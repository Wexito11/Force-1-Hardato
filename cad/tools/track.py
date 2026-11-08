# Геометрия демо-пути «Форс-1» (мм). Используется для DXF, PDF-чертежей и 3D.
import math

GAUGE = 190.0          # колея по внутренним граням головок
RAIL_T = 10.0          # толщина рельса = фанера 10 мм
RAIL_L = 495.0         # длина куска рельса (поле лазера 500)
RAIL_H = 40.0          # высота рельса над шпалой
TAB_W, TAB_H = 15.0, 10.0
GAP = 6.0              # зазор в стыке
PITCH = 68.0
X0 = 56.0              # первая шпала
NT = 14                # шпал
TIE_L, TIE_W, TIE_T = 280.0, 31.0, 10.0
SLOT_X, SLOT_Y = 10.4, 15.4     # паз под шип (подогнать под фактическую толщину фанеры)
WIDEN_MAX = 6.0        # уширение колеи к концу 2-го звена
SEC2 = RAIL_L + GAP    # начало 2-го звена = 501
WEAR = (140.0, 180.0, 3.0)      # вырез «износ головки» на рельсе П1: от, до, глубина
JOINT_HOLES = [RAIL_L - 9, RAIL_L - 21]   # отверстия под накладки (звено 1, локально)
HOLE_D = 4.3
HOLE_Y = 20.0
MISSING_TIE = 10       # индекс шпалы, которую убирают на демо (x = 736)
SHIM_TIES = [11, 12, 13]   # под левые концы - подкладки 4 мм (перекос)


def tie_x(k):
    return X0 + PITCH * k


def widen(x):
    return 0.0 if x < SEC2 else WIDEN_MAX * (x - SEC2) / RAIL_L


def rail_outline(section, side):
    """Контур рельса в локальных координатах: x вдоль, y=0 - верх шпалы."""
    x_off = 0.0 if section == 1 else SEC2
    tabs = [tie_x(k) - x_off for k in range(NT)
            if 0 <= tie_x(k) - x_off <= RAIL_L]
    pts = [(0, 0)]
    for t in sorted(tabs):
        a, b = t - TAB_W / 2, t + TAB_W / 2
        pts += [(a, 0), (a, -TAB_H), (b, -TAB_H), (b, 0)]
    pts += [(RAIL_L, 0), (RAIL_L, RAIL_H)]
    if section == 1 and side == "П":
        a, b, d = WEAR
        pts += [(b, RAIL_H), (b, RAIL_H - d), (a, RAIL_H - d), (a, RAIL_H)]
    pts += [(0, RAIL_H)]
    holes = JOINT_HOLES if section == 1 else [RAIL_L - h for h in JOINT_HOLES]
    return pts, [(hx, HOLE_Y, HOLE_D / 2) for hx in holes]


def tie_outline(k):
    """Шпала в координатах (u поперёк пути 0..280, v вдоль 0..31). Левый рельс - у u=40."""
    pts = [(0, 0), (TIE_L, 0), (TIE_L, TIE_W), (0, TIE_W)]
    c = TIE_L / 2
    uL = c - (GAUGE / 2 + RAIL_T / 2) - widen(tie_x(k))
    uR = c + (GAUGE / 2 + RAIL_T / 2)
    slots = []
    for u in (uL, uR):
        slots.append([(u - SLOT_X / 2, TIE_W / 2 - SLOT_Y / 2), (u + SLOT_X / 2, TIE_W / 2 - SLOT_Y / 2),
                      (u + SLOT_X / 2, TIE_W / 2 + SLOT_Y / 2), (u - SLOT_X / 2, TIE_W / 2 + SLOT_Y / 2)])
    return pts, slots, uL, uR


FOOT = 60.0
PROF = (15.4, 10.4)   # паз под прямоугольный профиль 15x10


def foot_outline():
    pts = [(0, 0), (FOOT, 0), (FOOT, FOOT), (0, FOOT)]
    a, b = PROF
    slot = [((FOOT - a) / 2, (FOOT - b) / 2), ((FOOT + a) / 2, (FOOT - b) / 2),
            ((FOOT + a) / 2, (FOOT + b) / 2), ((FOOT - a) / 2, (FOOT + b) / 2)]
    return pts, [slot]


def fishplate_outline():
    pts = [(0, 0), (60, 0), (60, 20), (0, 20)]
    return pts, [(x, 10, HOLE_D / 2) for x in (6, 18, 42, 54)]


def shim_outline():
    return [(0, 0), (31, 0), (31, 30), (0, 30)]


def poly_area(p):
    return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2


def transform(pts, dx, dy, rot=False):
    if rot:  # поворот на 90° (u,v) -> (v,u)
        return [(dx + y, dy + x) for x, y in pts]
    return [(dx + x, dy + y) for x, y in pts]


def layout_sheet_A():
    """10 мм, лист 1: 4 рельса + 4 опоры вагона. Возвращает список (имя, контур, вырезы-полигоны, отверстия-круги)."""
    parts = []
    y = 3.0
    for i, (sec, side) in enumerate([(1, "Л"), (1, "П"), (2, "Л"), (2, "П")]):
        pts, holes = rail_outline(sec, side)
        dx, dy = 2.5, y + TAB_H
        parts.append((f"Рельс {side}{sec}", transform(pts, dx, dy), [],
                      [(dx + hx, dy + hy, r) for hx, hy, r in holes], (dx + 250, dy + 20)))
        y += RAIL_H + TAB_H + 3
    for i in range(4):
        pts, slots = foot_outline()
        dx, dy = 10 + i * (FOOT + 6), 225.0
        parts.append((f"Опора {i+1}", transform(pts, dx, dy), [transform(s, dx, dy) for s in slots], [],
                      (dx + 30, dy + 52)))
    return parts


def layout_sheet_B():
    parts = []
    for k in range(NT):
        pts, slots, _, _ = tie_outline(k)
        dx, dy = 20 + k * (TIE_W + 2.5), 10.0
        parts.append((f"Ш{k+1}", transform(pts, dx, dy, rot=True),
                      [transform(s, dx, dy, rot=True) for s in slots], [], (dx + 15.5, dy + 140)))
    return parts


def layout_small():
    parts = []
    for i in range(4):
        pts, holes = fishplate_outline()
        dx, dy = 5 + i * 66, 5
        parts.append(("Накладка", transform(pts, dx, dy), [], [(dx + x, dy + y, r) for x, y, r in holes],
                      (dx + 30, dy + 28)))
    shims = []
    for i in range(3):
        dx, dy = 5 + i * 37, 45
        shims.append(("Подкладка", transform(shim_outline(), dx, dy), [], [], (dx + 15.5, dy + 38)))
    return parts, shims


def net_area(parts):
    s = 0
    for name, outer, cut, holes, _ in parts:
        s += poly_area(outer) - sum(poly_area(c) for c in cut) - sum(math.pi * r * r for *_, r in holes)
    return s / 100.0  # см²


if __name__ == "__main__":
    A, B = layout_sheet_A(), layout_sheet_B()
    print("Лист A, см2:", round(net_area(A)), " Лист B, см2:", round(net_area(B)))
    for k in range(NT):
        print(k + 1, tie_x(k), round(widen(tie_x(k)), 2))
