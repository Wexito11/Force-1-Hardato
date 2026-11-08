# Схема алгоритма «Форс-1» по ГОСТ 19.701-90 (3 листа A4) -> PDF
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch, Circle
from gost import *

W, H = 210, 297
A = 14      # высота символа
B = 56      # ширина символа
FS = 2.2    # шрифт в символах


def proc(ax, x, y, s, w=B, h=A):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, lw=mm2pt(TH)))
    text(ax, x, y, s, FS)


def pred(ax, x, y, s, w=B, h=A):
    proc(ax, x, y, s, w, h)
    for dx in (-w / 2 + 3, w / 2 - 3):
        line(ax, x + dx, y - h / 2, x + dx, y + h / 2, TH)


def term(ax, x, y, s, w=B, h=10):
    ax.add_patch(FancyBboxPatch((x - w / 2 + h / 2, y - h / 2), w - h, h,
                                boxstyle=f"round,pad=0,rounding_size={h/2}",
                                mutation_aspect=1, fill=False, lw=mm2pt(TH)))
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle=f"round,pad=0,rounding_size={h/2}",
                                fill=False, lw=mm2pt(TH)))
    text(ax, x, y, s, FS)


def term(ax, x, y, s, w=B, h=10):
    r = h / 2
    import numpy as np
    t = np.linspace(-np.pi / 2, np.pi / 2, 30)
    xr = x + w / 2 - r + r * np.cos(t)
    yr = y + r * np.sin(t)
    xl = x - w / 2 + r - r * np.cos(t)
    yl = y - r * np.sin(t)
    xs = list(xr) + list(xl) + [xr[0]]
    ys = list(yr) + list(yl) + [yr[0]]
    ax.plot(xs, ys, color="black", lw=mm2pt(TH))
    text(ax, x, y, s, FS)


def data(ax, x, y, s, w=B, h=A, k=5):
    ax.add_patch(Polygon([(x - w / 2 + k, y + h / 2), (x + w / 2, y + h / 2),
                          (x + w / 2 - k, y - h / 2), (x - w / 2, y - h / 2)],
                         closed=True, fill=False, lw=mm2pt(TH)))
    text(ax, x, y, s, FS)


def dec(ax, x, y, s, w=B, h=20):
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                         closed=True, fill=False, lw=mm2pt(TH)))
    text(ax, x, y, s, FS - 0.2)


def conn(ax, x, y, s, r=3):
    ax.add_patch(Circle((x, y), r, fill=False, lw=mm2pt(TH)))
    text(ax, x, y, s, 2.8)


def path(ax, pts, arrow=False):
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        line(ax, x1, y1, x2, y2, TN + 0.15)
    if arrow:
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.25",
                                    lw=mm2pt(TN + 0.15), color="black",
                                    shrinkA=0, shrinkB=0))


def lab(ax, x, y, s, ha="left"):
    text(ax, x, y, s, 2.4, ha=ha)


def page1(pdf):
    fig, ax = sheet(W, H)
    frame(ax, W, H, "ФОРС1.01.00 СА", "Робот-путеобходчик\n«Форс-1».\nСхема алгоритма",
          1, 3, material="Основной цикл")
    X, XR = 95, 165
    ys = dict(t1=282, p2=263, d3=244, r4=223, r5=200, p6=178, r7=156, r8=133, r9=110, p10=89, t11=72)
    term(ax, X, ys["t1"], "Начало")
    proc(ax, X, ys["p2"], "Самопроверка датчиков,\nобнуление энкодера,\nполозья вверх, A4988 откл.")
    data(ax, X, ys["d3"], "Команда оператора (Wi-Fi)\nили вибрация рельса (MPU)")
    dec(ax, X, ys["r4"], "Укрытие или\nвибрация?")
    dec(ax, X, ys["r5"], "Команда\n«Старт»?")
    proc(ax, X, ys["p6"], "Движение. Опрос датчиков,\nкоордината: энкодер + RFID")
    dec(ax, X, ys["r7"], "Лидар:\nпрепятствие < 30 см?")
    dec(ax, X, ys["r8"], "Превышен\nпорог дефекта?")
    dec(ax, X, ys["r9"], "Конец\nучастка?")
    proc(ax, X, ys["p10"], "Отчёт на веб-страницу:\nграфик колеи, дефекты")
    term(ax, X, ys["t11"], "Конец")
    # вертикаль основного потока
    seq = [("t1", 5, 7), ("p2", 7, 7), ("d3", 7, 10), ("r4", 10, 10), ("r5", 10, 7),
           ("p6", 7, 10), ("r7", 10, 10), ("r8", 10, 10), ("r9", 10, 7), ("p10", 7, 5)]
    keys = list(ys)
    for (k, _, hb), k2 in zip(seq, keys[1:]):
        ht = {"t1": 5, "p2": 7, "d3": 7, "r4": 10, "r5": 10, "p6": 7, "r7": 10,
              "r8": 10, "r9": 10, "p10": 7, "t11": 5}
        path(ax, [(X, ys[k] - ht[k]), (X, ys[k2] + ht[k2])])
    lab(ax, X + 1.5, ys["r4"] - 12.5, "нет")
    lab(ax, X + 1.5, ys["r5"] - 12.5, "да")
    lab(ax, X + 1.5, ys["r7"] - 12.5, "нет")
    lab(ax, X + 1.5, ys["r8"] - 12.5, "нет")
    lab(ax, X + 1.5, ys["r9"] - 12.5, "да")
    # укрытие
    pred(ax, XR, ys["r4"], "Режим укрытия\n(лист 2)", w=44)
    path(ax, [(X + B/2, ys["r4"]), (XR - 22, ys["r4"])])
    lab(ax, X + B/2 + 1, ys["r4"] + 2, "да")
    path(ax, [(XR, ys["r4"] + 7), (XR, ys["d3"]), (X + B/2, ys["d3"])], arrow=True)
    # старт: нет -> к ожиданию
    path(ax, [(X - B/2, ys["r5"]), (32, ys["r5"]), (32, ys["d3"]), (X - B/2, ys["d3"])], arrow=True)
    lab(ax, X - B/2 - 1, ys["r5"] + 2, "нет", ha="right")
    # препятствие
    proc(ax, XR, ys["r7"], "Стоп, ожидание\nсвободного пути", w=44)
    path(ax, [(X + B/2, ys["r7"]), (XR - 22, ys["r7"])])
    lab(ax, X + B/2 + 1, ys["r7"] + 2, "да")
    path(ax, [(XR + 22, ys["r7"]), (194, ys["r7"])], arrow=True)
    conn(ax, 197, ys["r7"], "1")
    # дефект
    proc(ax, XR, ys["r8"], "Стоп. Запись: тип,\nкоордината, фото", w=44)
    path(ax, [(X + B/2, ys["r8"]), (XR - 22, ys["r8"])])
    lab(ax, X + B/2 + 1, ys["r8"] + 2, "да")
    proc(ax, XR, ys["r9"], "Обслуживание: метка,\nмагнит или подтяжка\nболта", w=44, h=16)
    path(ax, [(XR, ys["r8"] - 7), (XR, ys["r9"] + 8)])
    path(ax, [(XR, ys["r9"] - 8), (XR, 95)], arrow=True)
    conn(ax, XR, 92, "1")
    # конец участка: нет
    path(ax, [(X - B/2, ys["r9"]), (35, ys["r9"])], arrow=True)
    conn(ax, 32, ys["r9"], "1")
    lab(ax, X - B/2 - 1, ys["r9"] + 2, "нет", ha="right")
    # вход соединителя 1 в P6
    conn(ax, 45, ys["p6"], "1")
    path(ax, [(48, ys["p6"]), (X - B/2, ys["p6"])], arrow=True)
    text(ax, 25, 64, "Пороги дефектов - лист 3.", 2.4, ha="left")
    pdf.savefig(fig)


def page2(pdf):
    fig, ax = sheet(W, H)
    frame(ax, W, H, "ФОРС1.01.00 СА", "Робот-путеобходчик\n«Форс-1».\nСхема алгоритма",
          2, 3, material="Режим укрытия")
    X1, X2 = 68, 150
    c1 = [("t", 282, "Режим укрытия"),
          ("p", 263, "Стоп. Лидар-стоп\nотключён"),
          ("p", 244, "Полозья модуля A вниз"),
          ("p", 225, "Полозья модуля B вниз"),
          ("p", 206, "A4988 вкл., NEMA17\nнаматывает ремень"),
          ("r", 185, "Ход по AS5600\n≥ 160 мм?"),
          ("p", 164, "Полозья вверх:\nсначала A, затем B"),
          ("p", 145, "Робот лежит на шпалах,\nкамера (MG90S) вверх"),
          ("p", 126, "Съёмка ходовой части,\nзапись кадров"),
          ("r", 105, "Команда\n«поезд ушёл»?")]
    draw_col(ax, X1, c1)
    # петли
    path(ax, [(X1 - B/2, 185), (32, 185), (32, 206), (X1 - B/2, 206)], arrow=True)
    lab(ax, X1 - B/2 - 1, 187, "нет", ha="right")
    lab(ax, X1 + 1.5, 185 - 12.5, "да")
    path(ax, [(X1 - B/2, 105), (32, 105), (32, 126), (X1 - B/2, 126)], arrow=True)
    lab(ax, X1 - B/2 - 1, 107, "нет", ha="right")
    lab(ax, X1 + 1.5, 105 - 12.5, "да")
    path(ax, [(X1, 95), (X1, 88)], arrow=True)
    conn(ax, X1, 85, "2")
    c2 = [("c", 282, "2"),
          ("p", 263, "Полозья вниз:\nсначала A, затем B"),
          ("p", 244, "NEMA17 разводит модули,\nзатем A4988 откл."),
          ("r", 223, "Реборды прижаты?\n(AS5600 стабилен 1 с)"),
          ("p", 202, "Полозья вверх:\nсначала A, затем B"),
          ("p", 183, "Лидар-стоп включён"),
          ("t", 164, "Возврат (лист 1, ввод)")]
    draw_col(ax, X2, c2)
    path(ax, [(X2 + B/2, 223), (198, 223), (198, 244), (X2 + B/2, 244)], arrow=True)
    lab(ax, X2 + B/2 + 1, 225, "нет")
    lab(ax, X2 + 1.5, 223 - 12.5, "да")
    text(ax, 110, 135, "Примечания:", 2.6, ha="left")
    notes = ["1. Полозья опускаются и поднимаются по очереди,",
             "    чтобы ограничить пиковый ток линии 6 В",
             "    (4 x MG996R).",
             "2. В режиме укрытия лидар-стоп отключён:",
             "    поезд над роботом не должен",
             "    блокировать алгоритм.",
             "3. Вибрация рельса (MPU-9250) проверяется",
             "    только на стоянке, иначе ложные",
             "    срабатывания от собственного хода."]
    for i, n in enumerate(notes):
        text(ax, 110, 129 - 4.2 * i, n, 2.3, ha="left")
    pdf.savefig(fig)


def draw_col(ax, X, items):
    hh = {"t": 5, "p": 7, "r": 10, "c": 3}
    for kind, y, s in items:
        {"t": term, "p": proc, "r": dec, "c": conn}[kind](ax, X, y, s)
    for (k1, y1, _), (k2, y2, _) in zip(items[:-1], items[1:]):
        path(ax, [(X, y1 - hh[k1]), (X, y2 + hh[k2])])


def page3(pdf):
    fig, ax = sheet(W, H)
    frame(ax, W, H, "ФОРС1.01.00 СА", "Робот-путеобходчик\n«Форс-1».\nСхема алгоритма",
          3, 3, material="Состояния и пороги")
    text(ax, 115, 285, "Таблица 1 - Состояния и переходы", 3, ha="center")
    rows = [("Код", "Состояние", "Действие", "Переход"),
            ("S0", "Инициализация", "самопроверка, обнуление", "OK → S1"),
            ("S1", "Ожидание", "стоит, слушает команды и MPU", "старт → S2; укрытие → S7"),
            ("S2", "Езда и измерения", "опрос датчиков, координата", "порог → S3; лидар → S6;\nконец → S5"),
            ("S3", "Дефект", "стоп, запись, фото", "→ S4"),
            ("S4", "Обслуживание", "метка / магнит / болт", "готово или тайм-аут → S2"),
            ("S5", "Отчёт", "данные на веб-страницу", "→ S1"),
            ("S6", "Препятствие", "стоп, ждать > 30 см", "чисто → S2"),
            ("S7", "Полозья вниз", "A, затем B", "→ S8"),
            ("S8", "Сжатие телескопа", "NEMA17 до хода 160 мм (AS5600)", "→ S9"),
            ("S9", "Полозья вверх", "робот на шпалах", "→ S10"),
            ("S10", "Осмотр поезда", "камера снизу, лидар-стоп откл.", "«поезд ушёл» → S11"),
            ("S11", "Возврат", "в обратном порядке", "→ S1")]
    cw = [12, 37, 59, 62]
    table(ax, 25, 278, rows, cw, rh=8.5)
    text(ax, 115, 158, "Таблица 2 - Пороги дефектов (прототип 1:2)", 3, ha="center")
    rows2 = [("Параметр", "Датчик", "Порог", "Действие"),
             ("Ширина колеи", "AS5600 (телескоп)", "|Δ| > 8 мм (колея 760)", "запись, метка"),
             ("Перекос", "MPU-9250", "крен > 0,8°", "запись, метка"),
             ("Износ головки", "TOF250 вниз", "d - d0 > 8 мм", "запись, метка"),
             ("Стык", "TOF250 + энкодер,\nкамера", "провал > 12 мм", "фото болтов,\nподтяжка"),
             ("Шпалы", "HC-SR04 вниз + энкодер", "шаг вне 272 ± 40 мм", "запись"),
             ("Мусор", "камера", "металл на пути", "электромагнит"),
             ("Препятствие", "RPLIDAR C1", "< 30 см", "стоп")]
    table(ax, 25, 151, rows2, [36, 44, 45, 45], rh=9)
    pdf.savefig(fig)


def table(ax, x0, y0, rows, cw, rh):
    xs = [x0]
    for c in cw:
        xs.append(xs[-1] + c)
    n = len(rows)
    for i in range(n + 1):
        line(ax, x0, y0 - i * rh, xs[-1], y0 - i * rh, TH if i in (0, 1, n) else TN)
    for xv in xs:
        line(ax, xv, y0, xv, y0 - n * rh, TH)
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            text(ax, xs[j] + 1.5, y0 - (i + 0.5) * rh, c, 2.4, ha="left")


if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    with PdfPages("out/ФОРС1_Схема_алгоритма.pdf") as pdf:
        page1(pdf)
        page2(pdf)
        page3(pdf)
    print("ok")
