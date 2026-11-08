# 3D: демо-путь и ремонтный модуль «Форс-1» (CadQuery) -> STEP/STL
import math, os
import cadquery as cq
import track as T

OUT = "out/3d"
os.makedirs(OUT, exist_ok=True)


def box(dx, dy, dz, x=0, y=0, z=0):
    """Параллелепипед с углом в (x,y,z)."""
    return cq.Workplane("XY").box(dx, dy, dz, centered=False).translate((x, y, z))


def cyl_y(d, L, x, y, z):
    return cq.Workplane("XZ").circle(d / 2).extrude(L / 2, both=True).translate((x, y, z))


def rail_solid(sec, side):
    pts, holes = T.rail_outline(sec, side)
    s = cq.Workplane("XZ").polyline(pts).close().extrude(T.RAIL_T / 2, both=True)
    for hx, hy, r in holes:
        s = s.cut(cq.Workplane("XZ").center(hx, hy).circle(r).extrude(20, both=True))
    x_off = 0 if sec == 1 else T.SEC2
    yc = T.GAUGE / 2 + T.RAIL_T / 2
    s = s.translate((x_off, 0, T.TIE_T))
    if side == "П":
        return s.translate((0, yc, 0))
    s = s.translate((0, -yc, 0))
    if sec == 2:  # уширение: поворот вокруг начала звена 2
        ang = math.degrees(math.atan2(T.WIDEN_MAX, T.RAIL_L))
        s = s.rotate((T.SEC2, -yc, 0), (T.SEC2, -yc, 1), -ang)
    return s


def tie_solid(k):
    pts, slots, uL, uR = T.tie_outline(k)
    s = box(T.TIE_W, T.TIE_L, T.TIE_T, T.tie_x(k) - T.TIE_W / 2, -T.TIE_L / 2, 0)
    for sl in slots:
        (u1, v1), _, (u2, v2), _ = sl
        s = s.cut(box(v2 - v1, u2 - u1, T.TIE_T + 2, T.tie_x(k) - T.TIE_W / 2 + v1,
                      -T.TIE_L / 2 + u1, -1))
    return s


def hex_nut(x, y, z, axis="Y", af=7.0, h=3.2):
    d = af / math.cos(math.radians(30))
    if axis == "Y":
        return cq.Workplane("XZ").polygon(6, d).circle(2.1).extrude(h / 2, both=True).translate((x, y, z))
    return cq.Workplane("XY").polygon(6, d).circle(2.1).extrude(h).translate((x, y, z))


def track_assembly():
    a = cq.Assembly(name="demo_track")
    wood = cq.Color(0.80, 0.65, 0.45)
    dark = cq.Color(0.25, 0.25, 0.28)
    steel = cq.Color(0.7, 0.7, 0.72)
    for k in range(T.NT):
        if k == T.MISSING_TIE:
            continue
        t = tie_solid(k)
        if k in T.SHIM_TIES:
            ang = math.degrees(math.atan2(4.0, T.TIE_L - 15))
            t = t.rotate((0, T.TIE_L / 2, 0), (1, T.TIE_L / 2, 0), -ang)
            a.add(box(31, 30, 4, T.tie_x(k) - 15.5, -T.TIE_L / 2, -4), name=f"shim_{k+1}",
                  color=cq.Color(0.9, 0.8, 0.6))
        a.add(t, name=f"tie_{k+1}", color=wood)
    for sec in (1, 2):
        for side in ("Л", "П"):
            a.add(rail_solid(sec, side), name=f"rail_{'L' if side=='Л' else 'R'}{sec}",
                  color=cq.Color(0.55, 0.40, 0.28))
    # накладки и болты на стыке
    yc = T.GAUGE / 2 + T.RAIL_T / 2
    zb = T.TIE_T + T.HOLE_Y
    for sgn in (-1, 1):
        for face in (-1, 1):
            yy = sgn * yc + face * (T.RAIL_T / 2 + 1.5)
            a.add(box(60, 3, 20, T.RAIL_L + T.GAP / 2 - 30, yy - 1.5, T.TIE_T + 10),
                  name=f"plate_{sgn}_{face}", color=cq.Color(0.85, 0.75, 0.55))
        for hx in (474, 486, 510, 522):
            loose = (sgn == 1 and hx == 510)
            a.add(cyl_y(4, 26 + (4 if loose else 0), hx, sgn * yc, zb), name=f"bolt_{sgn}_{hx}", color=steel)
            ynut = sgn * yc - sgn * (T.RAIL_T / 2 + 3 + 1.6 + (3 if loose else 0))
            a.add(hex_nut(hx, ynut, zb), name=f"nut_{sgn}_{hx}", color=steel)
    # мусор (гайка M3) на шпале 9
    a.add(hex_nut(T.tie_x(8), 0, T.TIE_T, axis="Z", af=5.5, h=2.4), name="debris", color=steel)
    # RFID-метки
    for k in (0, 7):
        a.add(cq.Workplane("XY").circle(12).extrude(1).translate((T.tie_x(k), 0, T.TIE_T)),
              name=f"rfid_{k}", color=cq.Color(0.2, 0.4, 0.8))
    # «вагон»: 4 опоры (фанера) + стойки 15x10 + перекладины Г 20x20
    for xb in (330.0, 470.0):
        for sy in (-1, 1):
            a.add(box(60, 60, 10, xb - 30, sy * 175 - 30, 0), name=f"foot_{xb}_{sy}", color=wood)
            a.add(box(10, 15, 150, xb - 5, sy * 175 - 7.5, 0), name=f"leg_{xb}_{sy}",
                  color=cq.Color(0.75, 0.77, 0.8))
        g = (cq.Workplane("XZ").polyline([(0, 0), (20, 0), (20, 1.5), (1.5, 1.5), (1.5, 20), (0, 20)])
             .close().extrude(200, both=True))
        a.add(g.translate((xb + 5, 0, 130)), name=f"wagon_bar_{xb}", color=cq.Color(0.75, 0.77, 0.8))
    # препятствие
    a.add(box(60, 120, 80, 1060, -60, 0), name="obstacle", color=dark)
    return a


# ---------------- ремонтный модуль ----------------
def socket():
    """Торцевая головка под ключ 7 (M4), посадка на D-вал Ø4 мотора JGA25-370."""
    d_hex = 7.25 / math.cos(math.radians(30))
    s = cq.Workplane("XY").circle(8).extrude(22)
    s = s.cut(cq.Workplane("XY").polygon(6, d_hex).extrude(6))            # гнездо под гайку
    s = s.cut(cq.Workplane("XY").circle(2.4).extrude(10))                  # под выступ болта
    shaft = cq.Workplane("XY").circle(2.05).extrude(30).cut(box(5, 5, 30, -2.5, 1.55, 0))  # D-профиль
    s = s.cut(shaft.translate((0, 0, 10)))
    s = s.cut(cq.Workplane("YZ").circle(1.4).extrude(10).translate((0, 0, 16)))  # под винт M3 (саморез)
    s = s.faces(">Z").edges().chamfer(0.5)
    return s


def mg90s():
    b = box(22.8, 12.2, 22.7, -11.4, -6.1, 0)
    b = b.union(box(32.2, 12.2, 2.5, -16.1, -6.1, 15.9))
    b = b.union(cq.Workplane("XY").circle(2.3).extrude(4).translate((-11.4 + 6.1, 0, 22.7)))
    return b


def jga25():
    g = cq.Workplane("XZ").circle(12.5).extrude(21)                 # редуктор
    m = cq.Workplane("XZ").circle(12.2).extrude(31).translate((0, -21, 0))
    m = cq.Workplane("XZ").circle(12.2).extrude(31)
    m = m.translate((0, 21, 0))
    sh = cq.Workplane("XZ").circle(2).extrude(9.5).translate((0, -9.5, 0))
    return g.union(m).union(sh)


def wrench_arm():
    """Рычаг гайковёрта на MG90S: хомут Ø25 под JGA25-370, гибкая змейка - поджатие головки."""
    L = 60.0
    arm = box(L, 4, 12, 0, -2, -6)
    # змейка (податливость ~2-3 мм): поперечные пропилы с разных сторон
    for i, x in enumerate((22, 27, 32, 37)):
        z0 = -6 if i % 2 == 0 else -3.5
        arm = arm.cut(box(1.2, 6, 9.5, x, -3, z0))
    ring = cq.Workplane("XZ").circle(15.5).circle(12.6).extrude(6, both=True).translate((L + 13, 0, 0))
    ring = ring.cut(box(4, 14, 3, L + 13 - 2, -7, 12))                  # разрез хомута
    ear = box(10, 12, 4, L + 13 - 5, -6, 14.5).cut(
        cq.Workplane("XZ").circle(1.6).extrude(10, both=True).translate((L + 13, 0, 16.5)))
    hub = cq.Workplane("XZ").circle(6).extrude(2, both=True).cut(
        cq.Workplane("XZ").circle(1.2).extrude(5, both=True))
    for dx in (-4, 4):
        hub = hub.cut(cq.Workplane("XZ").circle(0.8).extrude(5, both=True).translate((0, 0, dx)))
    return arm.union(ring).union(ear).union(hub)


def magnet_arm():
    """Рычаг электромагнита BR-P25/11 на MG90S."""
    L = 70.0
    arm = box(L, 4, 10, 0, -2, -5)
    cup = cq.Workplane("XY").circle(15).circle(12.8).extrude(10).translate((L + 13, 0, -15))
    top = cq.Workplane("XY").circle(15).extrude(2.5).translate((L + 13, 0, -5)).cut(
        cq.Workplane("XY").circle(2.2).extrude(5).translate((L + 13, 0, -6)))
    link = box(13, 4, 10, L, -2, -5)
    hub = cq.Workplane("XZ").circle(6).extrude(2, both=True).cut(cq.Workplane("XZ").circle(1.2).extrude(5, both=True))
    return arm.union(cup).union(top).union(link).union(hub)


def token_magazine():
    """Магазин фишек-меток Ø20 x 3 (8 шт.), выдача заслонкой на MG90S."""
    body = box(26, 26, 40, -13, -13, 0)
    body = body.cut(cq.Workplane("XY").circle(10.5).extrude(45).translate((0, 0, 3.6)))
    body = body.cut(box(26, 22, 3.6, -13, -11, 0))                       # канал заслонки
    body = body.cut(cq.Workplane("XY").circle(10.5).extrude(5).translate((0, 0, -1)))
    window = box(30, 4, 30, -15, -15, 8)                                  # смотровое окно
    body = body.cut(box(6, 30, 28, -3, -15, 8))
    for x in (-9, 9):
        body = body.union(box(6, 4, 10, x - 3, 13, 26)).cut(
            cq.Workplane("XZ").circle(1.6).extrude(5, both=True).translate((x, 15, 31)))
    return body


def token_slider():
    s = box(48, 21.6, 3.2, -24, -10.8, 0)
    s = s.cut(cq.Workplane("XY").circle(10.4).extrude(5).translate((-12, 0, -1)))
    s = s.cut(cq.Workplane("XY").circle(1.0).extrude(5).translate((20, 0, -1)))
    return s


def token():
    return cq.Workplane("XY").circle(10).extrude(3).faces(">Z").workplane().text("Д", 8, -0.8, kind="bold")


def nozzle():
    """Сопло помпы маркировки: хомут на трубку + конус Ø1,2."""
    plate = box(30, 20, 3, -15, -10, 0)
    for x in (-10, 10):
        plate = plate.cut(cq.Workplane("XY").circle(1.6).extrude(5).translate((x, 0, -1)))
    boss = cq.Workplane("XY").circle(5).extrude(10).translate((0, 0, 3))
    cone = cq.Workplane("XY").circle(5).workplane(offset=12).circle(1.5).loft().translate((0, 0, -12))
    n = plate.union(boss).union(cone)
    n = n.cut(cq.Workplane("XY").circle(3.1).extrude(9).translate((0, 0, 5)))   # под трубку Ø6
    n = n.cut(cq.Workplane("XY").circle(0.6).extrude(30).translate((0, 0, -13)))
    return n


def weld_head_concept():
    a = cq.Assembly(name="weld_head_concept")
    grey = cq.Color(0.6, 0.62, 0.65)
    for y in (-15, 15):
        a.add(cq.Workplane("YZ").circle(3).extrude(160).translate((0, y, 0)), name=f"guide_{y}", color=grey)
    car = box(40, 46, 22, 60, -23, -11)
    for y in (-15, 15):
        car = car.cut(cq.Workplane("YZ").circle(3.3).extrude(50).translate((55, y, 0)))
    a.add(car, name="carriage", color=cq.Color(0.9, 0.5, 0.15))
    head = cq.Workplane("XY").circle(11).extrude(45).translate((80, 0, -56))
    tip = cq.Workplane("XY").circle(11).workplane(offset=18).circle(3).loft().translate((80, 0, -74))
    tip = cq.Workplane("XY").add(tip.val()).mirror("XY", basePointVector=(0, 0, -65))
    a.add(head, name="weld_head", color=cq.Color(0.85, 0.2, 0.2))
    a.add(cq.Workplane("XY").circle(11).workplane(offset=-16).circle(3).loft()
          .translate((80, 0, -56)), name="weld_tip", color=cq.Color(0.3, 0.3, 0.3))
    a.add(box(42.3, 42.3, 40, 165, -21, -21), name="nema17", color=cq.Color(0.15, 0.15, 0.15))
    a.add(box(160, 2, 6, 0, 25, -3), name="gt2_belt", color=cq.Color(0.1, 0.1, 0.1))
    a.add(box(10, 60, 50, -10, -30, -25), name="end_plate", color=grey)
    return a


def repair_assembly():
    """Гайковёрт у ослабленного болта (x=510, правый рельс) - показ работы в сборке пути."""
    a = cq.Assembly(name="repair_demo")
    yc = T.GAUGE / 2 + T.RAIL_T / 2
    zb = T.TIE_T + T.HOLE_Y
    ynut_face = yc - (T.RAIL_T / 2 + 3 + 3.2 + 3)
    # головка смотрит наружу (к рельсу, +Y), ось Y
    sk = socket().rotate((0, 0, 0), (1, 0, 0), -90).translate((510, ynut_face - 22 + 22, zb))
    sk = socket().rotate((0, 0, 0), (1, 0, 0), 90)       # ось +Z -> -Y
    sk = sk.rotate((0, 0, 0), (0, 0, 1), 180).translate((510, ynut_face + 1, zb))
    a.add(sk, name="socket", color=cq.Color(0.2, 0.6, 0.3))
    a.add(jga25().translate((510, ynut_face - 22 - 9.5 + 9.5, zb)).translate((0, -9.5, 0)),
          name="jga25_370", color=cq.Color(0.7, 0.7, 0.72))
    arm = wrench_arm().rotate((0, 0, 0), (0, 1, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
    a.add(arm, name="wrench_arm_raw", color=cq.Color(0.2, 0.6, 0.3))
    return a


if __name__ == "__main__":
    parts = {
        "Головка_гайковерта": socket(),
        "Рычаг_гайковерта": wrench_arm(),
        "Рычаг_электромагнита": magnet_arm(),
        "Магазин_фишек": token_magazine(),
        "Заслонка_магазина": token_slider(),
        "Фишка_метка": token(),
        "Сопло_помпы": nozzle(),
    }
    PLA = 1.24e-3  # г/мм3
    total = 0
    for name, p in parts.items():
        cq.exporters.export(p, f"{OUT}/{name}.step")
        cq.exporters.export(p, f"{OUT}/{name}.stl", tolerance=0.05, angularTolerance=0.2)
        v = p.val().Volume()
        n = 8 if name == "Фишка_метка" else 1
        g = v * PLA * n
        total += g
        print(f"{name:24s} V={v/1000:6.1f} см3  x{n}  ~{g:5.1f} г (100% заполнение)")
    print("Итого печать ремонтного модуля (100%):", round(total), "г")
    tr = track_assembly()
    tr.save(f"{OUT}/Демо-путь_сборка.step")
    weld_head_concept().save(f"{OUT}/Сварочная_головка_концепт.step")
    cq.exporters.export(jga25(), f"{OUT}/_JGA25-370_габарит.step")
    cq.exporters.export(mg90s(), f"{OUT}/_MG90S_габарит.step")
    print("ok")
