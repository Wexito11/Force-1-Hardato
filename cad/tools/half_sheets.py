# 1:2 - габаритная схема (поперечный разрез, 1:5) и раскладки под лазер (корпуса фанера 4, крышки оргстекло 3, полозья фанера 6)
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon
from gost import sheet, frame, text, line, mm2pt, TH, TN
import drawings as D, track as TR
import half as H

T = H.T
NSEG = 5


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def dedup(p):
    out = []
    for q in p:
        if not out or abs(out[-1][0] - q[0]) > 1e-6 or abs(out[-1][1] - q[1]) > 1e-6:
            out.append(q)
    if abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


SEG = H.BH / NSEG
SLOTS = (50.0, 150.0, 250.0)          # пазы под шипы дна вдоль длинной стенки (u)
SL = 30.2


def long_wall(name, holes, cuts):
    L, Hh = H.BL, H.BH
    pts = [(0, 0), (L, 0)]
    for k in range(NSEG):
        u = L if k % 2 == 0 else L - T
        pts += [(u, k * SEG), (u, (k + 1) * SEG)]
    pts += [(L, Hh), (0, Hh)]
    for k in reversed(range(NSEG)):
        u = 0 if k % 2 == 0 else T
        pts += [(u, (k + 1) * SEG), (u, k * SEG)]
    slots = [rect(c - SL / 2, T - 0.1, c + SL / 2, 2 * T + 0.1) for c in SLOTS]
    return (name, dedup(pts), slots + cuts, holes, (L / 2, Hh - 10))


def end_wall(name, holes, cuts=()):
    W, Hh = H.BW, H.BH
    pts = []
    for k in range(NSEG):
        w = W if k % 2 == 1 else W - T
        pts += [(w, k * SEG), (w, (k + 1) * SEG)]
    for k in reversed(range(NSEG)):
        w = 0 if k % 2 == 1 else T
        pts += [(w, (k + 1) * SEG), (w, k * SEG)]
    slots = [rect(W / 2 - SL / 2, T - 0.1, W / 2 + SL / 2, 2 * T + 0.1)]
    return (name, dedup(pts), slots + list(cuts), holes, (W / 2, Hh - 10))


def bottom(name, holes, cuts):
    """Дно (BL-2T) x (BW-2T) на высоте T..2T, шипы 30x4 в пазы стенок."""
    L, W = H.BL - 2 * T, H.BW - 2 * T
    pts = [(0, 0)]
    for c in SLOTS:
        c -= T
        pts += [(c - 15, 0), (c - 15, -T), (c + 15, -T), (c + 15, 0)]
    pts += [(L, 0), (L, W / 2 - 15), (L + T, W / 2 - 15), (L + T, W / 2 + 15), (L, W / 2 + 15), (L, W)]
    for c in reversed(SLOTS):
        c -= T
        pts += [(c + 15, W), (c + 15, W + T), (c - 15, W + T), (c - 15, W)]
    pts += [(0, W), (0, W / 2 + 15), (-T, W / 2 + 15), (-T, W / 2 - 15), (0, W / 2 - 15)]
    sh = lambda p: [(x + T, y + T) for x, y in p]
    return (name, sh(pts), [sh(c) for c in cuts], [(x + T, y + T, r) for x, y, r in holes], (L / 2 + T, W / 2 + T))


def parts(m):
    u = lambda X: X + H.BL / 2
    # внутренняя стенка
    if m == "A":
        cin = [rect(u(s * H.BEAM_X) - 10.5, H.BEAM_Z - 0.5, u(s * H.BEAM_X) + 10.5, H.BEAM_Z + 20.5) for s in (-1, 1)]
        cin += [rect(u(0) - 11, 41, u(0) + 11, 63)]                                  # Г-рейка
    else:
        cin = [rect(u(s * H.BEAM_X) - 8.5, H.BEAM_Z + 2, u(s * H.BEAM_X) + 8.5, H.BEAM_Z + 14) for s in (-1, 1)]
        c0 = u(0)
        cin += [[(c0 - 2, 3), (c0 + 42, 3), (c0 + 42, 45), (c0 + 28, 45), (c0 + 28, 58), (c0 + 12, 58), (c0 + 12, 63),
                 (c0 - 12, 63), (c0 - 12, 41), (c0 - 2, 41)]]                         # NEMA17, шкив, Г-рейка
    hin = [(u(s * H.BEAM_X) + d, H.BEAM_Z + 10, 1.65) for s in (-1, 1) for d in (-20, 20)]   # втулки/накладки профилей
    if m == "A":
        hin += [(u(129) + d, z, 1.65) for d in (-15, 15) for z in (9, 17)] + [(u(129), 30, 5.0)]        # кронштейн лидара + кабель
    inner = long_wall(f"{m}-1 стенка внутр.", hin, cin)
    # наружная стенка
    xd, xi = u(H.WB / 2), u(-H.WB / 2)
    hout = [(xd, H.AXLE, 4.2), (xd - 8.5, H.AXLE, 1.65), (xd + 8.5, H.AXLE, 1.65), (xi, H.AXLE, 2.15),
            (u(60) - 8, 30, 1.65), (u(60) + 8, 30, 1.65), (u(60), 52, 3.0)]               # TOF250
    cout = [rect(u(0) - 12, 41, u(0) + 12, 63)] if m == "B" else []                       # выход рейки в укрытии
    if m == "B":
        hout += [(u(-70), 28, 1.65), (u(-20), 28, 1.65)]                                      # RC522 (метка на головке рельса)
    if m == "A":
        hout += [(u(s * H.BEAM_X) + d, H.BEAM_Z + 10, 1.65) for s in (-1, 1) for d in (-8, 8)] + [(u(0) - 6, 52, 1.65), (u(0) + 6, 52, 1.65)]
    outer = long_wall(f"{m}-2 стенка наруж.", hout, cout)
    srv = [(H.BW - 53.5 + d, v, 1.65) for d in (-15, 15) for v in (10, 45)]
    e3 = end_wall(f"{m}-3 торец -X", srv + [(30, 52, 6.0)])
    e4h = srv + [(30, 52, 6.0)]
    e4 = end_wall(f"{m}-4 торец +X", e4h)
    bh = [(146 - 13, 36, 8.25), (146 + 13, 36, 8.25), (146 - 30, 36, 1.65), (146 + 30, 36, 1.65)]   # HC-SR04 вниз
    if m == "B":
        bh += [(36, 36, 1.65), (76, 36, 1.65)]                                             # 4x18650
    bot = bottom(f"{m}-5 дно", bh, [])
    return [inner, outer, e3, e4, bot]


def place(p, dx, dy, rot=False):
    n, o, c, h, lab = p
    if rot:
        f = lambda x, y: (y, -x)
        o = [f(*q) for q in o]; c = [[f(*q) for q in cc] for cc in c]; h = [(*f(x, y), r) for x, y, r in h]; lab = f(*lab)
        mx, my = min(q[0] for q in o), min(q[1] for q in o)
        o = [(x - mx, y - my) for x, y in o]; c = [[(x - mx, y - my) for x, y in cc] for cc in c]
        h = [(x - mx, y - my, r) for x, y, r in h]; lab = (lab[0] - mx, lab[1] - my)
    return (n, [(x + dx, y + dy) for x, y in o], [[(x + dx, y + dy) for x, y in cc] for cc in c],
            [(x + dx, y + dy, r) for x, y, r in h], (lab[0] + dx, lab[1] + dy))


def layouts():
    A, B = parts("A"), parts("B")
    s1 = [place(A[0], 5, 5), place(A[1], 5, 79), place(B[0], 5, 153), place(B[1], 5, 227),
          place(A[2], 313, 5), place(A[3], 313, 79), place(B[2], 313, 153), place(B[3], 313, 227)]
    s2 = [place(A[4], 8, 8), place(B[4], 8, 130)]
    lids = []
    for i, m in enumerate("AB"):
        hl = [(x, y, 1.65) for x in (8, 150, 292) for y in (8, 112)]
        cuts = []
        if m == "B":
            cuts = [rect(30, 37, 75.5, 63.5)]; hl += [(100, 50, 6.0)]                        # XFW-001, тумблер
        lids.append(place((f"{m}-6 крышка", rect(0, 0, 300, 120), cuts, hl, (220, 60)), 5, 5 + i * 128))
    # полозья фанера 6: подошва + 4 стойки
    a = math.radians(-42.45)
    half = H.SERVO_X + H.LINK * math.cos(a) + 8
    sk = []
    for i, m in enumerate("AB"):
        L = 2 * half
        o = rect(0, 0, L, 20)
        hh = [(8, 10, 1.65), (L - 8, 10, 1.65), (L / 2 - 60, 10, 1.65), (L / 2 + 60, 10, 1.65)]
        sk.append(place((f"П-{i + 1} подошва {m}", o, [], hh, (L / 2, 10)), 5, 5 + i * 26))
        for j in range(2):
            ph = H.POST + 20
            po = rect(0, 0, 14, ph)
            cut = [rect(7 - 1.65, ph - 26, 7 + 1.65, ph - 6)] if j == 1 else []          # паз шарнира 20 мм
            hp = [(7, 8, 1.65), (7, 30, 1.65)] + ([(7, ph - 7, 1.65)] if j == 0 else [])
            sk.append(place((f"С{j + 1}", po, cut, hp, (7, ph / 2 - 10)), 10 + (i * 2 + j) * 22, 70))
    return s1, s2, lids, sk


def section(pdf):
    W, Hh = 420, 297
    fig, ax = sheet(W, Hh)
    frame(ax, W, Hh, "ФОРС1.00.00.000 ГЧ1", "Робот 1:2 на пути 760.\nГабаритная схема", 1, 1, scale="1:5")
    s = 0.2
    def draw(oy, state, title):
        ox = 175
        X = lambda y: ox + y * s
        Z = lambda z: oy + z * s
        ax.add_patch(Rectangle((X(-H.TIE_L / 2), Z(-30)), H.TIE_L * s, 30 * s, fc="#e2e2e2", ec="black", lw=mm2pt(TN)))
        for sg in (-1, 1):
            yc = sg * (H.GAUGE / 2 + H.HEAD / 2)
            for (a, b, z0, z1) in ((37.5, 37.5, 0, 16), (4.5, 4.5, 16, 78), (H.HEAD / 2, H.HEAD / 2, 78, H.UGR)):
                ax.add_patch(Rectangle((X(yc - a), Z(z0)), 2 * a * s, (z1 - z0) * s, fc="#bbb", ec="black", lw=mm2pt(TN)))
        line(ax, X(-700), Z(H.UGR), X(700), Z(H.UGR), TN, ls="--")
        text(ax, X(705), Z(H.UGR), "УГР", 2.4, ha="left")
        if state == 0:
            z0, sh = H.Z_RAIL, 0
        else:
            z0, sh = H.Z_HIDE, H.STROKE
            for sg in (-1, 1):
                yb = sg * H.B2B / 2
                ax.add_patch(Polygon([(X(yb), Z(H.UGR - H.TR_FLH)), (X(yb + sg * H.TR_FLT), Z(H.UGR - H.TR_FLH)),
                                      (X(yb + sg * H.TR_FLT), Z(H.UGR)), (X(yb + sg * 70), Z(H.UGR)),
                                      (X(yb + sg * 70), Z(H.UGR + 150)), (X(yb), Z(H.UGR + 150))],
                                     closed=True, fc="#f3d9d9", ec="#a33", hatch="///", lw=mm2pt(TN)))
            ax.add_patch(Rectangle((X(-H.YMAX), Z(0)), 2 * H.YMAX * s, H.ZMAX * s, fill=False, ec="#2a7", lw=mm2pt(TH), ls="--"))
            text(ax, X(0), Z(H.UGR + 30), "зона укрытия: |Y| ≤ %d, Z ≤ %d" % (H.YMAX, H.ZMAX), 2.4, color="#185")
        for sg in (-1, 1):
            yi, yo = sg * (H.Y_IN - sh), sg * (H.Y_OUT - sh)
            ax.add_patch(Rectangle((X(min(yi, yo)), Z(z0)), H.BW * s, H.BH * s, fill=False, lw=mm2pt(TH)))
            ax.add_patch(Rectangle((X(min(yi, yo)), Z(z0 + H.BH)), H.BW * s, H.LID * s, fc="#cfe8f5", ec="black", lw=mm2pt(TN)))
            yf = sg * (H.Y_FLO - sh)
            ax.add_patch(Rectangle((X(min(yf, yf - sg * H.FLT)), Z(z0 + H.AXLE - H.FLD / 2)), H.FLT * s, H.FLD * s, fc="#555", ec="black", lw=mm2pt(TN)))
            ax.add_patch(Rectangle((X(min(yf, yf + sg * (H.WW - H.FLT))), Z(z0 + H.AXLE - H.WD / 2)), (H.WW - H.FLT) * s, H.WD * s, fc="#888", ec="black", lw=mm2pt(TN)))
        ax.add_patch(Rectangle((X(-(H.Y_IN - sh)), Z(z0 + H.BEAM_Z)), 2 * (H.Y_IN - sh) * s, 20 * s, fc="#ddd", ec="black", lw=mm2pt(TN)))
        text(ax, X(0), Z(z0 + H.BEAM_Z + 10), "П 20x20 / 15x10", 2.2)
        text(ax, X(-700), Z(H.UGR + (190 if state else 120)), title, 3.2, ha="left")
        return X, Z
    X, Z = draw(185, 0, "А-А. На рельсах (инспекция)")
    def dimh(y1, y2, z, t):
        line(ax, X(y1), Z(z), X(y2), Z(z), TN)
        for y in (y1, y2):
            line(ax, X(y), Z(z) - 1, X(y), Z(z) + 1, TN)
        text(ax, (X(y1) + X(y2)) / 2, Z(z) + 2, t, 2.4)
    dimh(-H.GAUGE / 2, H.GAUGE / 2, -50, "760 (колея)")
    dimh(-H.Y_IN, H.Y_IN, H.Z_RAIL + H.BH + 15, "502 (зазор)")
    X, Z = draw(75, 1, "Б-Б. Режим укрытия: колёсная пара поезда 1:2 (Ø475, 720 между гранями)")
    dimh(-(H.Y_FLO + H.WW - H.FLT - H.STROKE), H.Y_FLO + H.WW - H.FLT - H.STROKE, -50, "680 по колёсам ≤ 690")
    dimh(-H.B2B / 2, H.B2B / 2, H.UGR + 165, "720")
    rows = [("Проверка", "Норма 1:2", "Модель"),
            ("Высота в укрытии над шпалой", "≤ 85 (УГР 100 - 15)", "81 (стойки 84,5)"),
            ("Ширина в укрытии", "≤ 690 (720 - 2x15)", "680"),
            ("Рейка в укрытии |Y|", "≤ 345", "345"),
            ("Колёса над рельсом при переходе", "> 0", "10"),
            ("Момент MG996R, 0,8 кг на серво", "≤ 9,4 кг·см", "4,8"),
            ("Ход модуля / общий", "-", "80 / 160")]
    cw = [70, 48, 22]
    x0, y0 = 250, 280
    for i, r in enumerate(rows):
        x = x0
        for j, c in enumerate(r):
            text(ax, x + 1.2, y0 - i * 6.5, c, 2.4, ha="left")
            x += cw[j]
        line(ax, x0, y0 - i * 6.5 - 3.2, x0 + sum(cw), y0 - i * 6.5 - 3.2, TH if i == 0 else TN)
    tr = ["1. Путь 1:2 к Р65 на ж/б шпалах: колея 760, головка 37,5,",
          "   УГР 100 над шпалой (рельс 90 + подкладка 10).",
          "2. Колёсная пара поезда 1:2: 720 между внутр. гранями, гребень 14 x 16,5.",
          "   Ниже УГР в колее нет частей поезда, кроме гребней колёс.",
          "3. В укрытии робот ниже УГР на 15 и не ближе 15 к грани колеса поезда.",
          "4. Выше УГР в рабочем режиме - сверять с ГОСТ 9238-2013 (натурный образец)."]
    for i, t in enumerate(tr):
        text(ax, 25, 52 - i * 4.6, t, 2.3, ha="left")
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    import os
    os.makedirs("out/1к2/Лазер DXF", exist_ok=True)
    s1, s2, lids, sk = layouts()
    for nm, ps in (("s1", s1), ("s2", s2), ("lids", lids), ("sk", sk)):
        for p in ps:
            xs = [x for x, y in p[1]]; ys = [y for x, y in p[1]]
            assert min(xs) >= 0 and max(xs) <= 500 and min(ys) >= 0 and max(ys) <= 300, (nm, p[0], max(xs), max(ys))
    with PdfPages("out/1к2/ФОРС1_1к2_Габаритная_схема.pdf") as pdf:
        section(pdf)
    with PdfPages("out/1к2/ФОРС1_1к2_Чертежи_лазер.pdf") as pdf:
        for n, (ps, ttl, des, mat, extra) in enumerate([
                (s1, "Корпуса A, B: стенки", "ФОРС1.02.01.001", "Фанера 4 ГОСТ 3916.1-2018",
                 ["1. Стенки -1...-4 модулей A и B, шип-паз 14 мм.", "2. Пазы 30,2x4,2 - подогнать по факт. толщине."]),
                (s2, "Корпуса A, B: дно", "ФОРС1.02.01.002", "Фанера 4 ГОСТ 3916.1-2018", ["1. Дно -5 модулей A и B."]),
                (lids, "Крышки A, B", "ФОРС1.02.01.003", "Оргстекло 3 мм", ["1. Камера смотрит вверх через крышку A.", "2. B: XFW-001, тумблер Ø12."]),
                (sk, "Полозья: подошвы и стойки", "ФОРС1.01.02.001", "Фанера 6 ГОСТ 3916.1-2018",
                 ["1. Подошвы П-1, П-2; стойки С1 (шарнир Ø3,3), С2 (паз 20 - симметричные звенья).", "2. Стойки к подошве - 2 x M3 через уголок."])]):
            fig, ax, ox, oy = D.sheet_layout(pdf, ps, ttl, des, mat, n + 1, 4, extra)
            pdf.savefig(fig); plt.close(fig)
    D.to_dxf("out/1к2/Лазер DXF/ФОРС1_1к2_корпуса_фанера4_лист1.dxf", s1)
    D.to_dxf("out/1к2/Лазер DXF/ФОРС1_1к2_корпуса_фанера4_лист2.dxf", s2)
    D.to_dxf("out/1к2/Лазер DXF/ФОРС1_1к2_крышки_оргстекло3.dxf", lids)
    D.to_dxf("out/1к2/Лазер DXF/ФОРС1_1к2_полозья_фанера6.dxf", sk)
    print("areas cm2: walls", TR.net_area(s1), "bottoms", TR.net_area(s2), "lids", TR.net_area(lids), "skids", TR.net_area(sk))
