# Участник 1 (08.11): полозья-параллелограммы с MG996R, лидар, камера на MG90S, TOF250, HW-511, RC522.
# Оси как в params.py: X вдоль пути, Y поперёк (A при -Y), Z от низа корпуса (= верх головки рельса).
import math
import cadquery as cq
import params as P
from assembly import robot

P.LINK = 58.0
PLA = (0.15, 0.55, 0.45)
WOOD = (0.80, 0.66, 0.45)
BLK = (0.12, 0.12, 0.12)
BLUE = (0.10, 0.25, 0.65)
ALU = (0.82, 0.84, 0.88)
PCB = (0.05, 0.45, 0.20)
SERVO_X = 113.0
LINK_Y = 77.0        # плоскость звеньев |Y|
SKID_YC = 83.0       # полоз фанера 6: |Y| 80..86


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl_between(p0, p1, r):
    v = cq.Vector(*p1) - cq.Vector(*p0)
    return cq.Workplane(cq.Plane(origin=p0, xDir=(v.y, -v.x, 0) if abs(v.z) < 0.99 * v.Length else (1, 0, 0),
                                 normal=v.normalized())).circle(r).extrude(v.Length)


def skid_geom(ang):
    a = math.radians(ang)
    dx, dz = -P.LINK * math.cos(a), P.LINK * math.sin(a)
    return dx, P.SERVO_Z + dz          # смещение полоза по X, высота оси шарнира полоза


def module_p1(m, ang):
    """Детали У1 для модуля m в системе модуля (знак Y по модулю)."""
    s = -1 if m == "A" else 1
    Y = lambda y: s * y
    items = []
    dx, zp = skid_geom(ang)
    for ex in (-1, 1):
        xs = ex * SERVO_X
        # кронштейн серво (печать) на торцевой стенке
        items.append((box(ex * 100 if ex > 0 else -103, ex * 103 if ex > 0 else -100,
                          *sorted((Y(28), Y(78))), 0, 46), PLA))
        # MG996R: вал вдоль Y, корпус 19,7 (X) x 42,9 (Y) x 40,7 (Z)
        items.append((box(xs - 9.85, xs + 9.85, *sorted((Y(P.SERVO_YC - 21.5), Y(P.SERVO_YC + 21.5))),
                          P.SERVO_Z - 10, P.SERVO_Z + 30.7), BLK))
        # качалка + звено (труба Ø6) + шарнир полоза
        items.append((cyl_between((xs, Y(74.5), P.SERVO_Z), (xs, Y(LINK_Y + 2), P.SERVO_Z), 9), (0.9, 0.9, 0.9)))
        items.append((cyl_between((xs, Y(LINK_Y), P.SERVO_Z), (xs + dx, Y(LINK_Y), zp), 3), ALU))
        items.append((cyl_between((xs + dx, Y(LINK_Y - 3), zp), (xs + dx, Y(SKID_YC + 3), zp), 1.6), ALU))
    # полоз: фанера 6, 240 x 12
    items.append((box(dx - P.SKID_L / 2, dx + P.SKID_L / 2, *sorted((Y(SKID_YC - 3), Y(SKID_YC + 3))),
                      zp - 6, zp + 6), WOOD))
    # TOF250 на кронштейне над головкой рельса (|Y| 95..105), между колёсами
    items.append((box(-10, 10, *sorted((Y(86), Y(104))), 40, 44), PLA))
    items.append((box(-10, 10, *sorted((Y(93.5), Y(106.5))), 35, 40), BLUE))
    # HW-511 вниз под дном
    items.append((box(-8, 8, *sorted((Y(36), Y(52))), -14, 0), PLA))
    items.append((box(-16, 16, *sorted((Y(37), Y(51))), -20, -14), PCB))
    if m == "A":
        lid = P.BH + P.LID
        # RPLIDAR C1 на крышке
        items.append((box(-43, 13, *sorted((Y(25), Y(81))), lid, lid + 4), PLA))
        items.append((box(-43, 13, *sorted((Y(25), Y(81))), lid + 4, lid + 26), BLK))
        items.append((cq.Workplane("XY").circle(26).extrude(19).translate((-15, Y(53), lid + 26)), (0.25, 0.25, 0.28)))
        # камера Pi на MG90S (наклон), крышка у переднего торца
        items.append((box(58, 81, *sorted((Y(47), Y(59))), lid, lid + 29), BLUE))
        items.append((box(64, 76, *sorted((Y(44), Y(62))), lid + 29, lid + 33), (0.9, 0.9, 0.9)))
        cam = box(-12.5, 12.5, -12, 12, 0, 5).rotate((0, 0, 0), (0, 1, 0), -35)
        items.append((cam.translate((72, Y(53), lid + 40)), PCB))
        items.append((cq.Workplane("XY").circle(4).extrude(6).rotate((0, 0, 0), (0, 1, 0), -35)
                      .translate((75, Y(53), lid + 44)), BLK))
    else:
        lid = P.BH + P.LID
        # RC522 под дном (до метки на шпале ~22 мм), XFW-001 и тумблер на крышке B
        for px in (-85, -35):
            for py in (32, 68):
                items.append((box(px - 2, px + 2, *sorted((Y(py - 2), Y(py + 2))), -16, 0), PLA))
        items.append((box(-90, -30, *sorted((Y(30), Y(70))), -18, -16), BLUE))
        items.append((box(-94, -46, *sorted((Y(38), Y(67))), lid, lid + 6), BLK))
        items.append((cq.Workplane("XY").circle(6).extrude(14).translate((-25, Y(53), lid)), (0.7, 0.1, 0.1)))
    return items


def robot_full(state=0.0, ang=P.ANG_UP):
    d = state * P.STROKE / 2
    items = list(robot(state))
    for m, dy in (("A", d), ("B", -d)):
        items += [(sh.translate((0, dy, 0)), c) for sh, c in module_p1(m, ang)]
    return items


def lowest(ang):
    dx, zp = skid_geom(ang)
    return zp - 6


if __name__ == "__main__":
    print("skid up bottom", lowest(P.ANG_UP), "down", lowest(P.ANG_DN), "dx up", skid_geom(P.ANG_UP)[0])
    print(len(robot_full()))
