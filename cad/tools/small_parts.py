# «Форс-1» 1:2 - мелкие печатные детали. Запуск: python small_parts.py -> out/STL/*.stl и *.step
# Все размеры - параметры вверху. Перед печатью сверить с реальными деталями из набора (штангенциркуль).
import os
import cadquery as cq

OUT = "out/STL"
os.makedirs(OUT, exist_ok=True)
M3 = 3.4            # отверстие под винт M3 (свободное)
M3_TAP = 2.6        # под винт M3 в пластик (нарезает сам)

# ---------- 1. Кронштейн MG996R на торец корпуса (4 шт.) ----------
# Серво 40,7 x 19,7 x 42,9; фланец 54,5 x 20, отверстия 49 x 10. Крепление к торцу: 4 x M3 по 30 x 35 (как в DXF торцов).
SERVO_L, SERVO_W, SERVO_H = 40.7, 19.7, 42.9
SERVO_HOLES_X, SERVO_HOLES_Y = 49.0, 10.0
WALL_HOLES_X, WALL_HOLES_Y = 30.0, 35.0

def servo_bracket():
    t = 4.0
    plate = cq.Workplane("XY").box(60, 48, t).faces(">Z").workplane().pushPoints(
        [(x, y) for x in (-WALL_HOLES_X / 2, WALL_HOLES_X / 2) for y in (-WALL_HOLES_Y / 2, WALL_HOLES_Y / 2)]).hole(M3)
    # полка под фланец серво, перпендикулярно пластине
    shelf = (cq.Workplane("XZ").box(60, 26, t).translate((0, -24 + t / 2, 13 + t / 2))
             .faces(">Y").workplane().pushPoints([(x, 0) for x in (-SERVO_HOLES_X / 2, SERVO_HOLES_X / 2)]).hole(M3)
             .cut(cq.Workplane("XZ").box(SERVO_L + 0.6, SERVO_W + 0.6, 10).translate((0, -24, 13))))
    rib = cq.Workplane("XY").box(t, 26, 26).translate((-28, -11, 13)) .union(cq.Workplane("XY").box(t, 26, 26).translate((28, -11, 13)))
    return plate.union(shelf).union(rib)

# ---------- 2. Наконечник звена полозьев (8 шт.) ----------
# Звено - труба Ø6 x 1 мм, длина 60 между осями. Наконечник: гильза под трубу + ушко под ось M3.
def link_end():
    sleeve = cq.Workplane("XY").circle(5).extrude(14).faces(">Z").workplane().hole(6.2, 10)
    lug = (cq.Workplane("XZ").center(0, 20).circle(5).extrude(4, both=True)
           .union(cq.Workplane("XZ").center(0, 17).rect(10, 6).extrude(4, both=True)))
    lug = lug.cut(cq.Workplane("XZ").center(0, 20).circle(M3 / 2).extrude(10, both=True))
    return sleeve.union(lug)

# ---------- 3. Вкладыш телескопа (4 шт.) ----------
# П-профиль 20x20x1,5 (внутри 17 x 18,5), внутри скользит прямоугольный 15x10x1,5. Вкладыш - втулка 17 x 18 x 30 с окном 15,3 x 10,3.
P_IN_W, P_IN_H = 17.0, 18.5
R_W, R_H = 15.0, 10.0
def telescope_insert():
    body = cq.Workplane("XY").box(P_IN_W - 0.2, P_IN_H - 0.5, 30)
    return body.cut(cq.Workplane("XY").box(R_W + 0.3, R_H + 0.3, 40)).edges("|Z").chamfer(0.6)

# ---------- 4. Площадка лидара RPLIDAR C1 (1 шт.) ----------
# 58 x 58 x 2, 4 x M3 по 48 x 48 (стойки от дна, см. DXF дна A), отверстия под крепёж C1 (сверить с даташитом: 4 x M2.5 ~ 35 x 35).
def lidar_plate():
    p = cq.Workplane("XY").box(58, 58, 2).faces(">Z").workplane()
    p = p.pushPoints([(x, y) for x in (-24, 24) for y in (-24, 24)]).hole(M3)
    p = p.faces(">Z").workplane().pushPoints([(x, y) for x in (-17.5, 17.5) for y in (-17.5, 17.5)]).hole(2.7)
    return p.faces(">Z").workplane().hole(12)   # кабель

# ---------- 5. Кронштейн TOF250 на наружную стенку (2 шт.) ----------
# Плата TOF250 ~ 28 x 14 (сверить!), смотрит вниз на головку рельса. Крепление к стенке 2 x M3 по 16 (DXF наружных стенок, Z=30).
def tof_bracket():
    t = 3.0
    wall = cq.Workplane("XY").box(30, t, 24).faces(">Y").workplane().pushPoints([(-8, 0), (8, 0)]).hole(M3)
    arm = cq.Workplane("XY").box(30, 40, t).translate((0, 20 - t / 2 + 1.5, 12 - t / 2))
    arm = arm.faces(">Z").workplane().pushPoints([(-10, 24), (10, 24)]).hole(2.7)   # под плату TOF250 (сверить шаг)
    arm = arm.faces(">Z").workplane().center(0, 24).rect(16, 10).cutThruAll()       # окно под оптику
    return wall.union(arm)

# ---------- 6. Стойка HC-SR04 под дно (2 шт.) ----------
# Плата 45,5 x 20,5; излучатели Ø16 выходят в отверстия дна (DXF: 2 x Ø16,5 по 26). Стойка держит плату на 4 мм под дном.
def sonar_standoff():
    frame = cq.Workplane("XY").box(52, 26, 6).cut(cq.Workplane("XY").box(46, 21, 10))
    return frame.faces(">Z").workplane().pushPoints([(-30, 0), (30, 0)]).hole(M3)

# ---------- 7. Прижимной ролик ремня GT2 (1 шт.) ----------
def belt_roller():
    return cq.Workplane("XY").circle(7.5).extrude(10).faces(">Z").workplane().hole(3.2).edges().chamfer(0.5)

# ---------- 8. Колодка зажима ремня на Г-рейке (1 шт.) ----------
def belt_clamp():
    return (cq.Workplane("XY").box(24, 12, 6).faces(">Z").workplane().pushPoints([(-8, 0), (8, 0)]).hole(M3)
            .faces("<Z").workplane().rect(24, 6.5).cutBlind(-2))   # канавка под ремень 6 мм

# ---------- 9. Держатель AS5600 над шкивом (2 шт.: телескоп и гайковёрт) ----------
def as5600_holder():
    base = cq.Workplane("XY").box(30, 20, 3).faces(">Z").workplane().pushPoints([(-11, 0), (11, 0)]).hole(M3)
    post = cq.Workplane("XY").box(6, 20, 25).translate((-12, 0, 14))
    top = cq.Workplane("XY").box(30, 20, 3).translate((0, 0, 25.5)).faces(">Z").workplane().pushPoints([(4, -6), (4, 6)]).hole(2.7)
    return base.union(post).union(top)

PARTS = {"Кронштейн_MG996R_торец": servo_bracket, "Наконечник_звена_Ø6": link_end, "Вкладыш_телескопа": telescope_insert,
         "Площадка_лидара_C1": lidar_plate, "Кронштейн_TOF250": tof_bracket, "Стойка_HC-SR04": sonar_standoff,
         "Ролик_ремня_GT2": belt_roller, "Колодка_ремня": belt_clamp, "Держатель_AS5600": as5600_holder}

if __name__ == "__main__":
    total = 0
    for name, fn in PARTS.items():
        s = fn()
        v = s.val().Volume() / 1000.0
        total += v
        cq.exporters.export(s, f"{OUT}/{name}.stl")
        cq.exporters.export(s, f"{OUT}/{name}.step")
        print(f"{name}: {v:.1f} см³")
    print(f"итого {total:.1f} см³ (x1 каждой), при 100 % PLA ~{total * 1.24:.0f} г")
