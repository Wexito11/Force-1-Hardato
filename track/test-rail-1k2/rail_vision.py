#!/usr/bin/env python3
"""Форс-1: поиск дефектов головки рельса камерой (Raspberry Pi 5 + камера Pi).

Камера смотрит сверху на головку рельса, рельс идёт по кадру слева направо.
Ищет: трещину (тёмная полоса), скол/износ кромки (головка стала уже),
разрыв/стык (головка пропала по всей ширине), посторонний предмет (не дерево).

Запуск:
  python3 rail_vision.py --calib            # 1 раз над чистым участком: запомнить цвет и ширину
  python3 rail_vision.py                    # работа с камерой, дефекты в defects.csv + фото
  python3 rail_vision.py --image test.png   # проверка на картинке
"""
import argparse, csv, json, os, time
import cv2
import numpy as np

CFG = "rail_cfg.json"
DEF = {
    "roi": [0.0, 0.25, 1.0, 0.75],   # x0, y0, x1, y1 в долях кадра - полоса с головкой
    "wood_h": [5, 30],               # оттенок фанеры (HSV, 0-180)
    "wood_s_min": 50,                # насыщенность фанеры
    "width_px": None,                # ширина головки в пикселях (из калибровки)
    "crack_v": 70,                   # тёмнее этого - трещина/гравировка
    "chip_k": 0.80,                  # ширина < 80 % - скол/износ кромки
    "gap_k": 0.25,                   # ширина < 25 % - разрыв/стык
    "obj_area": 150,                 # мин. площадь постороннего предмета, px
    "crack_len": 0.5,                # трещина длиннее 50 % ширины головки
}


def load_cfg():
    c = dict(DEF)
    if os.path.exists(CFG):
        c.update(json.load(open(CFG)))
    return c


def crop(img, roi):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = roi
    return img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


def wood_mask(hsv, c):
    lo = np.array([c["wood_h"][0], c["wood_s_min"], 60])
    hi = np.array([c["wood_h"][1], 255, 255])
    m = cv2.inRange(hsv, lo, hi)
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))


def head_width(mask):
    """Ширина головки (px) в каждом столбце: от первого до последнего пикселя дерева."""
    w = np.zeros(mask.shape[1])
    for x in range(mask.shape[1]):
        ys = np.flatnonzero(mask[:, x])
        if ys.size:
            w[x] = ys[-1] - ys[0] + 1
    return w


def runs(flag, min_len):
    """Отрезки подряд идущих True длиной >= min_len -> [(x0, x1)]."""
    out, start = [], None
    for x, f in enumerate(np.append(flag, False)):
        if f and start is None:
            start = x
        elif not f and start is not None:
            if x - start >= min_len:
                out.append((start, x - 1))
            start = None
    return out


def calibrate(img, c):
    hsv = cv2.cvtColor(crop(img, c["roi"]), cv2.COLOR_BGR2HSV)
    # оттенок и насыщенность - по медиане яркой части кадра
    v = hsv[..., 2]
    sel = hsv[v > np.percentile(v, 40)]
    h_med, s_med = np.median(sel[:, 0]), np.median(sel[:, 1])
    c["wood_h"] = [int(max(0, h_med - 12)), int(min(179, h_med + 12))]
    c["wood_s_min"] = int(max(25, s_med * 0.5))
    c["width_px"] = float(np.median(head_width(wood_mask(hsv, c))))
    json.dump(c, open(CFG, "w"), indent=1)
    return c


def detect(img, c):
    roi = crop(img, c["roi"])
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    wood = wood_mask(hsv, c)
    W = c["width_px"] or float(np.median(head_width(wood)))
    w = head_width(wood)
    found = []
    # 1. разрыв / стык: головки почти нет по всей ширине
    for a, b in runs(w < c["gap_k"] * W, 3):
        found.append(("стык/разрыв", a, b))
    # 2. скол / износ кромки: головка заметно уже
    for a, b in runs((w >= c["gap_k"] * W) & (w < c["chip_k"] * W), 4):
        found.append(("скол/износ кромки", a, b))
    # 3. трещина: тёмная вытянутая полоса внутри головки
    ys = np.flatnonzero(wood.any(axis=1))
    if ys.size:
        band = np.zeros_like(wood)
        band[ys[0]:ys[-1] + 1] = 255
        dark = cv2.inRange(hsv[..., 2], 0, c["crack_v"]) & band
        dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(dark)
        for i in range(1, n):
            x, y, bw, bh, area = st[i]
            in_gap = any(x <= g1 and x + bw >= g0 for n_, g0, g1 in found if n_ == "стык/разрыв")
            if bh >= c["crack_len"] * W and bw < 0.6 * bh and not in_gap:
                found.append(("трещина", x, x + bw))
        # 4. посторонний предмет: не дерево и не тёмная трещина, внутри полосы головки
        other = cv2.bitwise_not(wood) & band & cv2.inRange(hsv[..., 2], c["crack_v"] + 1, 255)
        other = cv2.morphologyEx(other, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(other)
        for i in range(1, n):
            x, y, bw, bh, area = st[i]
            touches_edge = y <= ys[0] + 2 or y + bh >= ys[-1] - 2
            if area >= c["obj_area"] and not touches_edge:
                found.append(("посторонний предмет", x, x + bw))
    return found, roi


def draw(roi, found):
    out = roi.copy()
    for name, a, b in found:
        cv2.rectangle(out, (int(a), 2), (int(b), out.shape[0] - 3), (0, 0, 255), 2)
        cv2.putText(out, name.split("/")[0][:10], (int(a), 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    return out


def camera_frames():
    from picamera2 import Picamera2
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
    cam.start()
    time.sleep(1)
    while True:
        yield cam.capture_array()


def coord_reader(port):
    """Координата от ESP32 A по USB: строки вида 'X 1234' (мм). Без порта - None."""
    if not port:
        return lambda: None
    import serial
    s = serial.Serial(port, 115200, timeout=0)
    last = [None]
    def read():
        for line in s.read(s.in_waiting or 1).decode(errors="ignore").splitlines():
            if line.startswith("X "):
                last[0] = float(line[2:])
        return last[0]
    return read


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", action="store_true")
    ap.add_argument("--image")
    ap.add_argument("--port", help="например /dev/ttyUSB0")
    ap.add_argument("--px_mm", type=float, default=0, help="пикселей на мм вдоль рельса (0 - не считать)")
    a = ap.parse_args()
    c = load_cfg()
    frames = [cv2.imread(a.image)] if a.image else camera_frames()
    if a.calib:
        c = calibrate(next(iter(frames)), c)
        print("калибровка:", c)
        return
    coord = coord_reader(a.port)
    os.makedirs("defects", exist_ok=True)
    log = csv.writer(open("defects.csv", "a", newline=""))
    last = {}
    for frame in frames:
        found, roi = detect(frame, c)
        x_mm = coord()
        for name, x0, x1 in found:
            pos = x_mm if x_mm is not None else 0
            if a.px_mm and x_mm is not None:
                pos = x_mm + ((x0 + x1) / 2 - roi.shape[1] / 2) / a.px_mm
            key = (name, round(pos / 30))            # один дефект - одна запись на 30 мм
            if key in last and time.time() - last[key] < 5:
                continue
            last[key] = time.time()
            fn = f"defects/{int(time.time())}_{name.split('/')[0]}.jpg"
            cv2.imwrite(fn, draw(roi, found))
            log.writerow([time.strftime("%H:%M:%S"), name, round(pos), fn])
            print(f"ДЕФЕКТ: {name}, x = {pos:.0f} мм, фото {fn}")
        if a.image:
            cv2.imwrite("result.png", draw(roi, found))
            print("найдено:", [(n, int(x0), int(x1)) for n, x0, x1 in found] or "ничего")


if __name__ == "__main__":
    main()
