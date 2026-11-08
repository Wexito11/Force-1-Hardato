import cadquery as cq, math
import params as P, corpus as C, parts3d as Q
import cad as TRK, track as TT

def plate_xz(part, y0, sign):
    """Продольная стенка: (u,v) -> X=u-100, Z=v; толщина T от y0 в сторону sign."""
    n, o, cuts, holes, lab = part
    s = cq.Workplane("XZ").polyline([(u - 100, v) for u, v in o]).close().extrude(-P.T)
    for c in cuts:
        s = s.cut(cq.Workplane("XZ").polyline([(u - 100, v) for u, v in c]).close().extrude(-P.T - 2).translate((0, -1, 0)))
    for u, v, r in holes:
        s = s.cut(cq.Workplane("XZ").center(u - 100, v).circle(r).extrude(-P.T - 2).translate((0, -1, 0)))
    # сейчас Y 0..T
    return s.translate((0, y0 if sign > 0 else y0 - P.T, 0))

def plate_yz(part, ymin, x0):
    n, o, cuts, holes, lab = part
    s = cq.Workplane("YZ").polyline([(w + ymin, v) for w, v in o]).close().extrude(P.T)
    for c in cuts:
        s = s.cut(cq.Workplane("YZ").polyline([(w + ymin, v) for w, v in c]).close().extrude(P.T + 2).translate((-1, 0, 0)))
    for w, v, r in holes:
        s = s.cut(cq.Workplane("YZ").center(w + ymin, v).circle(r).extrude(P.T + 2).translate((-1, 0, 0)))
    return s.translate((x0, 0, 0))

def bottom_solid(part, sgn):
    n, o, cuts, holes, lab = part
    f = lambda x, y: (x - 100, sgn * (20 + y))
    s = cq.Workplane("XY").polyline([f(x, y) for x, y in o]).close().extrude(P.T)
    for c in cuts:
        s = s.cut(cq.Workplane("XY").polyline([f(x, y) for x, y in c]).close().extrude(P.T + 2).translate((0, 0, -1)))
    return s.translate((0, 0, P.FLOOR - P.T))

def wheel(drive):
    prof = [(0, 0), (P.WD / 2 + 5, 0), (P.WD / 2 + 5, P.FL), (P.WD / 2, P.FL), (P.WD / 2 - 0.75, P.WW), (0, P.WW)]
    w = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    return w   # ось - Z локально (реборда в z 0..5)

def module(m, dy=0.0):
    sgn = -1 if m == "A" else 1
    parts = C.module_parts(m)
    items = []
    wood, steel, pla, blk = (0.80, 0.66, 0.45), (0.72, 0.74, 0.78), (0.15, 0.55, 0.45), (0.12, 0.12, 0.12)
    yin, yout = sgn * P.Y_IN, sgn * P.Y_OUT
    items.append((plate_xz(parts[0], yin, sgn), wood))
    items.append((plate_xz(parts[1], yout, -sgn), wood))
    ymin = min(yin, yout)
    items.append((plate_yz(parts[2], ymin, -P.BL / 2), wood))
    items.append((plate_yz(parts[3], ymin, P.BL / 2 - P.T), wood))
    items.append((bottom_solid(parts[4], sgn), wood))
    # колёса: реборда на Y = +-90
    for x, drive in ((P.WB / 2, True), (-P.WB / 2, False)):
        w = wheel(drive)
        w = w.rotate((0, 0, 0), (1, 0, 0), -90 * sgn)       # ось вдоль Y, реборда к корпусу
        items.append((w.translate((x, sgn * P.Y_FL, P.AXLE_Z)), (0.25, 0.25, 0.28)))
    # JGA25-370 ведущий: от наружной стенки внутрь
    j = cq.Workplane("XZ").circle(12.4).extrude(52).translate((0, 0, 0))
    j = j.translate((P.WB / 2, 0, P.AXLE_Z)) if sgn > 0 else j.mirror("XZ").translate((P.WB / 2, 0, P.AXLE_Z))
    items.append((j.translate((0, sgn * (P.Y_OUT - P.T), 0)), steel))
    if m == "B":
        nema = cq.Workplane("XY").box(40, P.NEMA, P.NEMA).translate(((P.NEMA_X[0] + P.NEMA_X[1]) / 2, P.NEMA_YC, P.FLOOR + P.NEMA / 2))
        items.append((nema, blk))
        drum = cq.Workplane("YZ").circle(P.DRUM_D / 2).extrude(P.DRUM_X[1] - P.DRUM_X[0]).translate((P.DRUM_X[0], P.NEMA_YC, P.SHAFT_Z))
        items.append((drum, pla))
        for s in (-1, 1):
            b = Q.bush_slide().rotate((0, 0, 0), (1, 0, 0), -90).translate((s * P.TUBE_X, P.Y_IN + P.T, P.TUBE_Z))
            items.append((b, pla))
    else:
        for s in (-1, 1):
            b = Q.bush_fix().rotate((0, 0, 0), (1, 0, 0), 90).translate((s * P.TUBE_X, -(P.Y_IN + P.T), P.TUBE_Z))
            items.append((b, pla))
        cb = Q.clamp_block().translate((P.BELT_X, -49, P.FLOOR))
        items.append((cb, pla))
    return [(s.translate((0, dy, 0)), c) for s, c in items]

def robot(state=0.0):
    """state 0 - на рельсах (зазор 40), 1 - сжат (зазор 3)."""
    d = state * P.STROKE / 2
    items = module("A", d) + module("B", -d)
    alu = (0.82, 0.84, 0.88)
    for s in (-1, 1):
        t = cq.Workplane("XZ").circle(P.TUBE_D / 2).circle(P.TUBE_D / 2 - 1).extrude(-P.TUBE_L)
        items.append((t.translate((s * P.TUBE_X, P.TUBE_A_END + d, P.TUBE_Z)), alu))
    # ремень: от верха барабана (B) до колодки (A)
    y1, y2 = P.NEMA_YC - d, -49 + d
    belt = cq.Workplane("XY").box(6, y1 - y2, 1.4).translate((P.BELT_X, (y1 + y2) / 2, P.BELT_Z))
    items.append((belt, (0.1, 0.1, 0.1)))
    # пружины-арки между внутренними стенками
    gap = P.GAP0 - 2 * d
    chord = gap + 12
    L = 64.0
    h = math.sqrt(max(L * L / 4 - chord * chord / 4, 0)) * 0.9
    for s in (-1, 1):
        arch = cq.Workplane("YZ").polyline([(-chord / 2, 0), (0, h), (chord / 2, 0)]).offset2D(0.6).extrude(20)
        items.append((arch.translate((s * P.SPRING_X - 10, 0, 18)), (0.9, 0.5, 0.1)))
    return items

if __name__ == "__main__":
    a = cq.Assembly(name="FORS1_robot")
    for i, (s, c) in enumerate(robot(0)):
        a.add(s, name=f"p{i}", color=cq.Color(*c))
    a.save("out/3D/Робот_на_рельсах_упрощ.step")
    print("ok")
