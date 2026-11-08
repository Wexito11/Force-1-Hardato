# Печатные детали телескопа и привода + упрощённая сборка робота
import cadquery as cq
import math
import params as P

def flange_bush(bore, body_d, out_len, in_len, setscrew=False):
    """Фланец Ø30x3 в плоскости XY, ось - Z. out_len - часть сквозь стенку (Z<0), in_len - внутрь (Z>3)."""
    f = cq.Workplane("XY").circle(P.FLANGE_D / 2).extrude(P.FLANGE_T)
    f = f.faces(">Z").workplane().pushPoints([(-P.PCD / 2, 0), (P.PCD / 2, 0)]).hole(3.3)
    b = cq.Workplane("XY").workplane(offset=P.FLANGE_T).circle(body_d / 2).extrude(in_len)
    s = f.union(b)
    if out_len > 0:
        s = s.union(cq.Workplane("XY").workplane(offset=-out_len).circle(body_d / 2).extrude(out_len))
    s = s.cut(cq.Workplane("XY").workplane(offset=-out_len - 1).circle(bore / 2).extrude(out_len + in_len + 10))
    if setscrew:   # радиальный M3 + карман под гайку
        z = P.FLANGE_T + in_len / 2
        s = s.cut(cq.Workplane("YZ").workplane(offset=0).center(0, z).circle(1.65).extrude(20))
        s = s.cut(cq.Workplane("XY").box(2.8, 6.0, 7.0).translate((bore / 2 + 2.6, 0, z)))
    return s

def bush_slide():   # B: Ø14 сквозь стенку 4 мм, внутрь 15, отверстие 10,4 (скольжение по трубе Ø10)
    return flange_bush(10.4, 14.0, P.T, P.BUSH_IN)

def bush_fix():     # A: тело Ø18 внутрь 17, отверстие 10,1, стопорный M3
    return flange_bush(10.1, 18.0, 0, P.FIX_LEN, setscrew=True)

def clamp_block():
    """Колодка ремня в A. Ось ремня - Y, верх канала на 2,5 мм ниже линии ремня."""
    h = P.BELT_Z - 2.5 - P.FLOOR          # ~26
    base = cq.Workplane("XY").box(50, 40, 4).translate((0, 0, 2))
    for dx in (-20, 20):
        for dy in (-8, 8):
            base = base.cut(cq.Workplane("XY").slot2D(10, 3.3, 90).extrude(10).translate((dx, dy, -2)))
    blk = cq.Workplane("XY").box(30, 35, h).translate((0, 0, h / 2))
    blk = blk.cut(cq.Workplane("XY").box(6.5, 40, 0.6).translate((0, 0, h - 0.3)))   # канал 6,5
    for dx in (-6.5, 6.5):
        blk = blk.cut(cq.Workplane("XY").circle(1.65).extrude(h + 2).translate((dx, 0, -1)))
        blk = blk.cut(cq.Workplane("XY").polygon(6, 6.4).extrude(3.2).translate((dx, 0, -0.1)))
    return base.union(blk)

def clamp_plate():
    p = cq.Workplane("XY").box(26, 30, 3).translate((0, 0, 1.5))
    for dx in (-6.5, 6.5):
        p = p.cut(cq.Workplane("XY").circle(1.65).extrude(5).translate((dx, 0, -1)))
    for i in range(-6, 7):   # зубья GT2 шаг 2 мм поперёк канала, высота 0,7
        p = p.union(cq.Workplane("XY").box(6.3, 1.0, 0.7).translate((0, i * 2.0, -0.35)))
    return p

def spring_arch(L=64.0, t=1.0, b=20.0):
    """Пружина-арка PETG: полоса b x t, проушины с отверстием Ø3,3 (ось вдоль ширины)."""
    s = cq.Workplane("XY").box(L, b, t)
    for sx in (-1, 1):
        eye = cq.Workplane("XZ").circle(3.5).extrude(b / 2, both=True).translate((sx * L / 2, 0, 0))
        eye = eye.cut(cq.Workplane("XZ").circle(1.65).extrude(b, both=True).translate((sx * L / 2, 0, 0)))
        s = s.union(eye)
    return s

def spring_bracket():
    """Кронштейн пружины на внутреннюю стенку: 2xM3 в стенку (Z 14 и 26), вилка с осью M3."""
    plate = cq.Workplane("XY").box(24, 4, 22).translate((0, 2, 20))
    plate = plate.cut(cq.Workplane("XZ").pushPoints([(0, 14), (0, 26)]).circle(1.65).extrude(-10))
    fork = cq.Workplane("XY").box(24, 8, 8).translate((0, 8, 6 + 4))
    fork = fork.cut(cq.Workplane("XY").box(21, 9, 9).translate((0, 9, 10)))   # прорезь под проушину
    fork = fork.cut(cq.Workplane("YZ").circle(1.65).extrude(30, both=True).translate((0, 8, 10)))
    return plate.union(cq.Workplane("XY").box(24, 12, 3).translate((0, 6, 6 + 1.5))).union(fork)

PARTS = {"Втулка_скользящая_B": (bush_slide, 2), "Втулка_фиксатор_A": (bush_fix, 2),
         "Колодка_ремня_A": (clamp_block, 1), "Планка_ремня_A": (clamp_plate, 1),
         "Пружина_арка": (spring_arch, 2), "Кронштейн_пружины": (spring_bracket, 4)}

if __name__ == "__main__":
    import os
    os.makedirs("out/3D/STL печать", exist_ok=True)
    tot = 0
    for n, (f, q) in PARTS.items():
        s = f()
        cq.exporters.export(s, f"out/3D/{n}.step")
        cq.exporters.export(s, f"out/3D/STL печать/{n}.stl", tolerance=0.02, angularTolerance=0.15)
        v = s.val().Volume() / 1000 * 1.27 * q
        bb = s.val().BoundingBox()
        tot += v
        print(f"{n}: x{q}, {bb.xlen:.1f}x{bb.ylen:.1f}x{bb.zlen:.1f}, {v:.1f} г (PETG 100%)")
    print("итого печать телескопа", round(tot, 1), "г")
