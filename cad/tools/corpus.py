# Корпуса модулей A и B под лазер: фанера 4 мм, шип-паз. Детали в формате drawings.py:
# (имя, контур, вырезы-полилинии, отверстия (x,y,r), точка подписи)
import params as P
import drawings as D
import track as TR
from matplotlib.backends.backend_pdf import PdfPages
from gost import *

T = P.T
SEG = P.BH / 5          # 5 шипов по высоте угла
SL, SH = 20.2, T + 0.2  # паз под шип дна
K = 0.0                 # учёт реза лазера - подобрать на пробе


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def long_wall(holes, cuts, name):
    """Продольная стенка 200x80: u = X+100, v = Z. Шипы на торцах - сегменты 0,2,4."""
    L, H = P.BL, P.BH
    pts = [(0, 0), (L, 0)]
    for k in range(5):
        u = L if k % 2 == 0 else L - T
        pts += [(u, k * SEG), (u, (k + 1) * SEG)]
    pts += [(L, H), (0, H)]
    for k in reversed(range(5)):
        u = 0 if k % 2 == 0 else T
        pts += [(u, (k + 1) * SEG), (u, k * SEG)]
    pts = dedup(pts)
    slots = [rect(c - SL / 2, P.FLOOR - T - 0.1, c + SL / 2, P.FLOOR + 0.1) for c in (40, 100, 160)]
    return (name, pts, slots + cuts, holes, (L / 2, 50))


def end_wall(name):
    W, H = P.BW, P.BH
    pts = []
    for k in range(5):           # правый край снизу вверх
        w = W if k % 2 == 1 else W - T
        pts += [(w, k * SEG), (w, (k + 1) * SEG)]
    for k in reversed(range(5)):  # левый край сверху вниз
        w = 0 if k % 2 == 1 else T
        pts += [(w, (k + 1) * SEG), (w, k * SEG)]
    pts = dedup(pts)
    slots = [rect(W / 2 - SL / 2, P.FLOOR - T - 0.1, W / 2 + SL / 2, P.FLOOR + 0.1)]
    srv = [(W / 2 + dx, v, 1.65) for dx in (-15, 15) for v in (8, 40)]   # кронштейн MG996R полоза (У1)
    return (name, pts, slots, [(W / 2, 62, 6.0)] + srv, (W / 2, 50))   # Ø12 - проход проводов/USB


def bottom(name, holes, cuts):
    """Дно 192x58 с шипами 20x4 в пазы стенок. x = X+100 (от внутр. грани торца +4), y = поперёк."""
    L, W = P.BL - 2 * T, P.BW - 2 * T
    pts = [(0, 0)]
    for c in (36, 96, 156):      # нижний длинный край, шипы наружу
        pts += [(c - 10, 0), (c - 10, -T), (c + 10, -T), (c + 10, 0)]
    pts += [(L, 0), (L, W / 2 - 10), (L + T, W / 2 - 10), (L + T, W / 2 + 10), (L, W / 2 + 10), (L, W)]
    for c in (156, 96, 36):
        pts += [(c + 10, W), (c + 10, W + T), (c - 10, W + T), (c - 10, W)]
    pts += [(0, W), (0, W / 2 + 10), (-T, W / 2 + 10), (-T, W / 2 - 10), (0, W / 2 - 10)]
    sh = lambda p: [(x + T, y + T) for x, y in p]   # сдвиг в положительные координаты
    return (name, sh(pts), [sh(c) for c in cuts], [(x + T, y + T, r) for x, y, r in holes], (L / 2 + T, W / 2 + T + 12))


def dedup(p):
    out = []
    for q in p:
        if not out or (abs(out[-1][0] - q[0]) > 1e-6 or abs(out[-1][1] - q[1]) > 1e-6):
            out.append(q)
    if abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def module_parts(m):
    """m = 'A' или 'B'. Внутренняя стенка смотрит в зазор."""
    u = lambda X: X + P.BL / 2
    belt = rect(u(P.BELT_X) - 6, P.BELT_Z - 3.5, u(P.BELT_X) + 6, P.BELT_Z + 3.5)   # паз ремня 12x7
    tube_r = (10.4 if m == "A" else 14.4) / 2
    h_in = []
    for s in (-1, 1):
        x = u(s * P.TUBE_X)
        h_in += [(x, P.TUBE_Z, tube_r), (x - P.PCD / 2, P.TUBE_Z, 1.65), (x + P.PCD / 2, P.TUBE_Z, 1.65)]
        xs = u(s * P.SPRING_X)
        h_in += [(xs, 14, 1.65), (xs, 26, 1.65)]          # кронштейн пружины-арки
    inner = long_wall(h_in, [belt], f"{m}-1 стенка внутр.")
    # наружная: ведущее колесо +X (JGA25-370: вал Ø8 + 2xM3 через 17), холостое -X (ось M4)
    xd, xi = u(P.WB / 2), u(-P.WB / 2)
    h_out = [(xd, P.AXLE_Z, 4.2), (xd - 8.5, P.AXLE_Z, 1.65), (xd + 8.5, P.AXLE_Z, 1.65),
             (xi, P.AXLE_Z, 2.15)]
    h_out += [(u(-8), 34, 1.65), (u(8), 34, 1.65), (u(0), 52, 3.0)]   # кронштейн TOF250 + провод (У1)
    outer = long_wall(h_out, [], f"{m}-2 стенка наруж.")
    e1, e2 = end_wall(f"{m}-3"), end_wall(f"{m}-4")
    # дно: зажим ремня (только A) - 4 паза 3,3x10 вдоль Y; Ø4 - винты стоек плат по месту
    cuts, holes = [], []
    if m == "A":
        # в системе дна: x = X + 96, y = расстояние от внутренней стенки (внутр. грань) = |Y| - 24
        cx = P.BELT_X + 96
        for dx in (-20, 20):
            for yc in (17, 33):    # центры пазов: зона Y -41..-57 под колодкой
                cuts.append(rect(cx + dx - 1.65, yc - 5, cx + dx + 1.65, yc + 5))
    else:
        nx = (P.NEMA_X[0] + P.NEMA_X[1]) / 2 + 96
        pass
    holes += [(92, 20, 1.65), (100, 20, 1.65), (96, 5, 3.0)]          # кронштейн HW-511 + провод (У1)
    if m == "B":
        holes += [(x, y, 1.65) for x in (11, 61) for y in (8, 44)]      # стойки RC522
        holes += [(36, 3.5, 3.0)]                                        # провод RC522
        holes += [(13.5, 36, 1.65), (63.5, 36, 1.65)]                    # держатель 4x18650 (2x2)
    bot = bottom(f"{m}-5 дно", holes, cuts)
    return [inner, outer, e1, e2, bot]


def place(part, dx, dy):
    n, o, c, h, lab = part
    return (n, [(x + dx, y + dy) for x, y in o], [[(x + dx, y + dy) for x, y in cc] for cc in c],
            [(x + dx, y + dy, r) for x, y, r in h], (lab[0] + dx, lab[1] + dy))


def layouts():
    A, B = module_parts("A"), module_parts("B")
    s1 = [place(A[0], 5, 5), place(A[1], 210, 5), place(B[0], 5, 92), place(B[1], 210, 92),
          place(A[2], 420, 5), place(A[3], 420, 92), place(B[2], 420, 179),
          place(A[4], 9, 183), place(B[4], 214, 183)]
    s2 = [place(B[3], 5, 5)]
    return s1, s2


def lid_parts():
    lids = []
    for i, m in enumerate("AB"):
        h = [(6, 6, 1.65), (194, 6, 1.65), (6, 60, 1.65), (194, 60, 1.65)]
        cuts = []
        if m == "A":   # лидар (переходник 4xM3, кабель Ø12), камера на MG90S, шлейф
            h += [(x, y, 1.65) for x in (65, 105) for y in (13, 53)] + [(85, 33, 6.0)]
            h += [(155.75, 33, 1.1), (183.25, 33, 1.1)]
            cuts += [rect(158, 26.75, 181, 39.25), rect(160, 45, 178, 48)]
        else:          # XFW-001 (вырез 45,5x26,5) и тумблер Ø12
            cuts += [rect(9, 19.75, 54.5, 46.25)]
            h += [(75, 33, 6.0)]
        lids.append(place((f"{m}-6 крышка", rect(0, 0, 200, 66), cuts, h, (120 if m == "A" else 130, 15)), 5, 5 + i * 72))
    return lids


if __name__ == "__main__":
    s1, s2 = layouts()
    for p in s1 + s2:
        xs = [x for x, y in p[1]]; ys = [y for x, y in p[1]]
        assert min(xs) >= 0 and max(xs) <= 500 and min(ys) >= 0 and max(ys) <= 300, p[0]
    print("S1 area", TR.net_area(s1), "S2", TR.net_area(s2), "lid", TR.net_area(lid_parts()))
