# «Форс-1» в масштабе 1:2 (08.11, У1). Оси: X вдоль пути, Y поперёк (A при -Y), Z от верха шпалы.
import math
import cadquery as cq

# ---- путь 1:2 (натура / 2) ----
GAUGE = 760.0                 # колея по внутренним граням головок
HEAD = 37.5                   # ширина головки
UGR = 100.0                   # уровень головки над шпалой (Р65 90 + подкладка 10)
B2B = 720.0                   # внутренние грани колёс поезда
TR_FLH, TR_FLT, TR_WD = 14.0, 16.5, 475.0
TIE_L, TIE_W, TIE_H, TIE_P = 1375.0, 135.0, 95.0, 272.0
CLR_Z, CLR_Y = 15.0, 15.0     # запас до УГР и до грани колеса поезда
ZMAX = UGR - CLR_Z            # 85 - потолок укрытия
YMAX = B2B / 2 - CLR_Y        # 345

# ---- робот ----
T = 4.0                        # фанера корпуса
BL, BW, BH, LID = 300.0, 120.0, 66.0, 3.0
WD, FLD, WW, FLT = 50.0, 66.0, 45.0, 5.0     # колесо: обод Ø50, реборда Ø66 (8 мм), ширина 45 (обод 40)
HUB = 4.0
Y_FLO = GAUGE / 2                    # наружная грань реборды = внутр. грань рельса (380)
Y_OUT = Y_FLO - FLT - HUB            # наружная стенка корпуса 371
Y_IN = Y_OUT - BW                    # внутренняя стенка 251
STROKE = 80.0                        # ход каждого модуля внутрь (общий 160)
WB = 240.0                           # база колёс X = +-120
AXLE = 36.0                          # ось колеса над низом корпуса
Z_RAIL = UGR + WD / 2 - AXLE         # низ корпуса на рельсах = 85
Z_HIDE = 12.0                        # низ корпуса в укрытии (на поднятых полозьях)
# телескоп: П-профиль 20x20x1,5 (в A) + прямоугольный 15x10x1,5 (в B) скользит внутри
BEAM_X, BEAM_Z = 90.0, 44.0          # X = +-110, Z от низа корпуса
BEAM_L = 440.0
RACK_L = 632.0                       # Г-профиль-рейка: от наружной стенки A; в укрытии конец на |Y| 345
# полозья: симметричные звенья L=60 (+-45 град), серво снаружи торцов
SERVO_X, SERVO_Z, LINK = BL / 2 + 11, 20.0, 60.0
POST = 72.5                          # высота стойки полоза до шарнира
SKID_Y = Y_OUT - 10                  # плоскость полоза |Y|


def hidden_ok():
    wheel_out = Y_FLO + WW - FLT - STROKE   # обод снаружи: 380+40-80
    return dict(wheel_out=wheel_out, ymax=YMAX, top=Z_HIDE + BH + LID, zmax=ZMAX,
                gap_rails=2 * Y_IN, gap_hidden=2 * (Y_IN - STROKE),
                beam_A_end=-(Y_OUT - T) + BEAM_L, beam_A_end_hidden=-(Y_OUT - T) + BEAM_L + STROKE,
                B_inner_hidden=Y_IN - STROKE, rack_end_rails=-(Y_OUT - T) + RACK_L, rack_end_hidden=-(Y_OUT - T) + RACK_L + STROKE + 0 * STROKE,
                rack_end_abs_hidden=-(Y_OUT - T) + STROKE + RACK_L)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl_y(x, y0, y1, z, r):
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))


def wheel(x, s, z_axle):
    """Колесо: реборда к корпусу. s - знак стороны."""
    yi = s * (Y_FLO - FLT)
    fl = cyl_y(x, min(yi, yi + s * FLT), max(yi, yi + s * FLT), z_axle, FLD / 2)
    y1 = yi + s * FLT
    tr = cyl_y(x, min(y1, y1 + s * (WW - FLT)), max(y1, y1 + s * (WW - FLT)), z_axle, WD / 2)
    return fl.union(tr)


WOOD, PLA, BLK, ALU, GLASS = (0.80, 0.66, 0.45), (0.15, 0.55, 0.45), (0.13, 0.13, 0.13), (0.82, 0.84, 0.88), (0.75, 0.88, 0.95)
PCB, BLUE, DARK = (0.05, 0.45, 0.2), (0.1, 0.25, 0.65), (0.25, 0.25, 0.28)


def module(m, z0, shift, ang_deg):
    """z0 - низ корпуса над шпалой; shift - смещение внутрь (0..STROKE); ang - угол звеньев полоза."""
    s = -1 if m == "A" else 1
    dy = -s * shift
    Y = lambda y: s * y + dy
    yy = lambda a, b: tuple(sorted((Y(a), Y(b))))
    it = []
    # корпус
    it.append((box(-BL / 2, BL / 2, *yy(Y_IN, Y_OUT), z0, z0 + T), WOOD))
    for a, b in ((Y_IN, Y_IN + T), (Y_OUT - T, Y_OUT)):
        it.append((box(-BL / 2, BL / 2, *yy(a, b), z0, z0 + BH), WOOD))
    for x in (-BL / 2, BL / 2 - T):
        it.append((box(x, x + T, *yy(Y_IN, Y_OUT), z0, z0 + BH), WOOD))
    it.append((box(-BL / 2, BL / 2, *yy(Y_IN, Y_OUT), z0 + BH, z0 + BH + LID), GLASS))
    # колёса + JGA25 (ведущее +X)
    for x in (WB / 2, -WB / 2):
        it.append((wheel(x, s, z0 + AXLE).translate((0, dy, 0)), DARK))
    it.append((cyl_y(WB / 2, *yy(Y_OUT - T - 55, Y_OUT - T), z0 + AXLE, 12.5), ALU))
    # полозья: стойки + звенья + подошва
    a = math.radians(ang_deg)
    zp = z0 + SERVO_Z + LINK * math.sin(a)
    for ex in (-1, 1):
        xs = ex * SERVO_X
        xp = xs + ex * LINK * math.cos(a)
        it.append((box(xs - 10, xs + 10, *yy(Y_OUT - 75, Y_OUT - 32), z0 + SERVO_Z - 10, z0 + SERVO_Z + 30.7), BLK))
        it.append((box(ex * BL / 2 if ex > 0 else -BL / 2 - 3, ex * BL / 2 + 3 if ex > 0 else -BL / 2, *yy(Y_OUT - 80, Y_OUT - 27), z0, z0 + 50), PLA))
        p0, p1 = (xs, Y(SKID_Y - 4), z0 + SERVO_Z), (xp, Y(SKID_Y - 4), zp)
        v = cq.Vector(*p1) - cq.Vector(*p0)
        it.append((cq.Workplane(cq.Plane(origin=p0, xDir=(0, 1, 0), normal=v.normalized())).circle(3).extrude(v.Length), ALU))
        it.append((box(xp - 6, xp + 6, *yy(SKID_Y, SKID_Y + 6), zp - POST, zp + 6), WOOD))
    xl = SERVO_X + LINK * math.cos(a) + 8
    it.append((box(-xl, xl, *yy(SKID_Y, SKID_Y + 6), zp - POST - 6, zp - POST + 6), WOOD))
    # датчики
    it.append((box(50, 70, *yy(Y_OUT, Y_FLO + 25), z0 + 45, z0 + 49), PLA))
    it.append((box(50, 70, *yy(Y_FLO + 12, Y_FLO + 25), z0 + 40, z0 + 45), BLUE))       # TOF250 над головкой
    it.append((box(-22.5, 22.5, *yy(Y_IN + 30, Y_IN + 50), z0 + T, z0 + T + 3), PCB))  # HC-SR04 (шпалы)
    for xx in (-13, 13):
        it.append((cq.Workplane("XY").circle(8).extrude(10 + T).translate((xx, Y(Y_IN + 40), z0 - 10)), (0.75, 0.75, 0.75)))
    if m == "A":
        # лидар RPLIDAR C1 на кронштейне у внутренней стенки, в зазоре между модулями, рядом с П-профилем (+X)
        # луч ~52 над низом корпуса: на рельсах 141 над шпалой (41 над УГР), в укрытии верх 76 < 85
        LX0, LX1 = 108.0, 163.0
        it.append((box(LX0, BL / 2, *yy(Y_IN - 4, Y_IN), z0 + 6, z0 + 21), PLA))                     # пластина на стенке
        it.append((box(LX0, BL / 2, *yy(Y_IN - 62, Y_IN - 4), z0 + 17, z0 + 21), PLA))              # полка
        it.append((box(LX0, LX1, *yy(Y_IN - 61, Y_IN - 6), z0 + 21, z0 + 44), BLK))                  # корпус лидара
        it.append((cq.Workplane("XY").circle(26).extrude(20).translate(((LX0 + LX1) / 2, Y(Y_IN - 33.5), z0 + 44)), DARK))
        # камера на MG90S под крышкой (смотрит вверх через крышку)
        it.append((box(35, 60, *yy(Y_IN + 40, Y_IN + 65), z0 + BH - 12, z0 + BH - 2), PCB))
        # Pi 5, PCA9685, XH-M400 x2, ESP A, L298N - габариты
        for (x0, x1, a0, a1, h0, h1, c) in [(-120, -35, Y_IN + 8, Y_IN + 64, 8, 28, PCB), (-20, 42, Y_IN + 8, Y_IN + 33, 8, 22, BLUE),
                                            (-120, -60, Y_IN + 70, Y_OUT - 8, 8, 30, BLUE), (-50, 5, Y_IN + 70, Y_OUT - 8, 8, 21, PCB),
                                            (55, 98, Y_IN + 8, Y_IN + 51, 8, 35, (0.7, 0.1, 0.1))]:
            it.append((box(x0, x1, *yy(a0, a1), z0 + h0, z0 + h1), c))
    else:
        it.append((box(-130, -50, *yy(Y_IN + 20, Y_IN + 61), z0 + T, z0 + T + 40), BLUE))      # 4x18650 2x2
        it.append((box(-2, 40.3, *yy(Y_IN - 15, Y_IN + 27.3), z0 + T, z0 + T + 40), BLK))       # NEMA17, вал вверх
        it.append((cq.Workplane("XY").circle(8).extrude(10).translate((19, Y(Y_IN + 6), z0 + T + 42)), (0.85, 0.85, 0.85)))  # шкив
        it.append((box(-75, -15, *yy(Y_OUT - 9, Y_OUT - 5), z0 + 8, z0 + 48), BLUE))            # RC522 у наруж. стенки (метка на головке)
        for (x0, x1, a0, a1, h0, h1, c) in [(-40, 15, Y_IN + 80, Y_OUT - 12, 8, 21, PCB), (40, 83, Y_IN + 70, Y_OUT - 8, 8, 35, (0.7, 0.1, 0.1))]:
            it.append((box(x0, x1, *yy(a0, a1), z0 + h0, z0 + h1), c))
    return it


def telescope(z0, shift):
    it = []
    ya0 = -(Y_OUT - T) + shift       # конец П-профиля в A (у наружной стенки)
    yb0 = (Y_OUT - T) - shift
    for ex in (-1, 1):
        x = ex * BEAM_X
        it.append((box(x - 10, x + 10, ya0, ya0 + BEAM_L, z0 + BEAM_Z, z0 + BEAM_Z + 20), ALU))       # П 20x20
        it.append((box(x - 7.5, x + 7.5, yb0 - BEAM_L, yb0, z0 + BEAM_Z + 3, z0 + BEAM_Z + 13), (0.6, 0.62, 0.66)))  # 15x10
    # рейка: Г-профиль 20x20, закреплён в A, ремень GT2 зубьями к шкиву NEMA17 (B)
    yr0 = -(Y_OUT - T) + shift
    it.append((box(-10, 10, yr0, yr0 + RACK_L, z0 + 42, z0 + 44), ALU))
    it.append((box(8, 10, yr0, yr0 + RACK_L, z0 + 42, z0 + 62), ALU))
    it.append((box(10, 11.4, yr0 + RACK_L - 190, yr0 + RACK_L, z0 + 46, z0 + 56), BLK))
    return it


def robot(state, ang):
    """state 0 - на рельсах, 1 - укрытие (сжат и опущен), 2 - на рельсах, полозья опущены, сжат."""
    if state == 0:
        z0, sh = Z_RAIL, 0.0
    elif state == 2:
        z0, sh = Z_RAIL + 10, STROKE
    else:
        z0, sh = Z_HIDE, STROKE
    return module("A", z0, sh, ang) + module("B", z0, sh, ang) + telescope(z0, sh)


def track(x0=-700, x1=700, wagon=False):
    it = []
    n0 = math.ceil(x0 / TIE_P)
    for k in range(n0, int(x1 // TIE_P) + 1):
        x = k * TIE_P
        n = 14
        for j in range(n):
            ya, yb = -TIE_L / 2 + j * TIE_L / n, -TIE_L / 2 + (j + 1) * TIE_L / n
            it.append((box(x - TIE_W / 2, x + TIE_W / 2, ya, yb, -TIE_H, 0), (0.62, 0.62, 0.6)))
    xs = [x0 + k * 100 for k in range(int((x1 - x0) // 100) + 1)]
    for s in (-1, 1):
        yi = s * GAUGE / 2
        yc = yi + s * HEAD / 2
        for xa in xs[:-1]:
            xb = xa + 100
            it.append((box(xa, xb, yc - 37.5, yc + 37.5, 0, 10), (0.35, 0.35, 0.35)))      # подкладка
            it.append((box(xa, xb, yc - 37.5, yc + 37.5, 10, 16), (0.45, 0.42, 0.4)))       # подошва
            it.append((box(xa, xb, yc - 4.5, yc + 4.5, 16, 78), (0.45, 0.42, 0.4)))         # шейка
            it.append((box(xa, xb, yc - HEAD / 2, yc + HEAD / 2, 78, UGR), (0.55, 0.52, 0.5)))   # головка
    if wagon:   # колёсная пара поезда над укрывшимся роботом (1:2)
        for s in (-1, 1):
            yb = s * B2B / 2
            it.append((cyl_y(0, *sorted((yb, yb + s * 70)), UGR + TR_WD / 2, TR_WD / 2), (0.55, 0.15, 0.15)))
            it.append((cyl_y(0, *sorted((yb, yb + s * TR_FLT)), UGR + TR_WD / 2, TR_WD / 2 + TR_FLH), (0.55, 0.15, 0.15)))
        it.append((cyl_y(0, -B2B / 2, B2B / 2, UGR + TR_WD / 2, 70), (0.4, 0.1, 0.1)))
    return it


if __name__ == "__main__":
    print(hidden_ok())
    print("rails: body bottom", Z_RAIL, "top", Z_RAIL + BH + LID)
    a_up = math.degrees(math.asin((Z_HIDE * 0 - 10 + POST - SERVO_Z) / LINK))
    print("skid raised angle", a_up)
