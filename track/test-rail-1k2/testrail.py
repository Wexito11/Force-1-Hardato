# Тест-рейка 1:2 «Форс-1»: один рельс 480 мм с дефектами -> DXF + PDF
import sys, os
sys.path.insert(0, "/home/claude/force1")
import ezdxf
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Circle, Rectangle
from gost import *

L = 480.0          # длина рейки
J0, J1 = 234.0, 246.0   # стык: зазор 12 мм (1:2)
WEB_H = 80.0       # шейка + подошва (фанера 10, вертикально)
HEAD_W = 37.5      # ширина головки 1:2
TAB_B = (20.0, 6.0)     # нижние шипы в основание (фанера 6)
TAB_T = (30.0, 10.0)    # верхние шипы в нижний слой головки
SL = 0.4           # зазор под шип
WEAR = (80.0, 140.0)    # износ: вырезан верхний слой головки (провал 10 мм)
CRACKS = [((180, 4), (186, 33.5)), ((196, 6), (192, 31))]  # гравировка «трещин» на верхнем слое
CHIP = (400.0, 412.0, 9.0)   # скол кромки головки: x от-до, глубина
FISH = (180.0, 300.0, 20.0, 60.0)  # накладка (фанера 4): x от-до, y от-до на шейке
BOLTS = [195.0, 225.0, 255.0, 285.0]
HOLE_R = 2.15
BASE_W = 120.0
BOT_TABS = [30.0, 120.0, 200.0, 280.0, 360.0, 450.0]
TOP_TABS = [40.0, 190.0, 290.0, 430.0]


def web(x0, x1):
    """Шейка куска рельса: y=0 - верх основания, y=WEB_H - низ головки."""
    pts = [(x0, 0)]
    for t in [b for b in BOT_TABS if x0 < b < x1]:
        a, b = t - TAB_B[0] / 2, t + TAB_B[0] / 2
        pts += [(a, 0), (a, -TAB_B[1]), (b, -TAB_B[1]), (b, 0)]
    pts += [(x1, 0), (x1, WEB_H)]
    for t in sorted([b for b in TOP_TABS if x0 < b < x1], reverse=True):
        a, b = t - TAB_T[0] / 2, t + TAB_T[0] / 2
        pts += [(b, WEB_H), (b, WEB_H + TAB_T[1]), (a, WEB_H + TAB_T[1]), (a, WEB_H)]
    pts += [(x0, WEB_H)]
    holes = [(bx, 40.0, HOLE_R) for bx in BOLTS if x0 < bx < x1]
    return pts, holes


def head_lower(x0, x1):
    outer = [(x0, 0), (x1, 0), (x1, HEAD_W), (x0, HEAD_W)]
    slots = []
    for t in [b for b in TOP_TABS if x0 < b < x1]:
        a, b = t - TAB_T[0] / 2 - SL / 2, t + TAB_T[0] / 2 + SL / 2
        y0, y1 = HEAD_W / 2 - 5 - SL / 2, HEAD_W / 2 + 5 + SL / 2
        slots.append([(a, y0), (b, y0), (b, y1), (a, y1)])
    return outer, slots


def head_upper(x0, x1, chip=False):
    if chip:
        a, b, d = CHIP
        return [(x0, 0), (x1, 0), (x1, HEAD_W), (b, HEAD_W), (b, HEAD_W - d), (a, HEAD_W - d),
                (a, HEAD_W), (x0, HEAD_W)]
    return [(x0, 0), (x1, 0), (x1, HEAD_W), (x0, HEAD_W)]


def base():
    outer = [(0, 0), (L, 0), (L, BASE_W), (0, BASE_W)]
    slots = []
    for t in BOT_TABS:
        a, b = t - TAB_B[0] / 2 - SL / 2, t + TAB_B[0] / 2 + SL / 2
        y0, y1 = BASE_W / 2 - 5 - SL / 2, BASE_W / 2 + 5 + SL / 2
        slots.append([(a, y0), (b, y0), (b, y1), (a, y1)])
    return outer, slots


def fishplate():
    x0, x1, y0, y1 = FISH
    pts = [(0, 0), (x1 - x0, 0), (x1 - x0, y1 - y0), (0, y1 - y0)]
    return pts, [(bx - x0, 20.0, HOLE_R) for bx in BOLTS]


def sh(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def layout_10():
    """Фанера 10: 2 шейки, 2 нижних слоя головки, 3 куска верхнего слоя."""
    P = []  # (имя, контур, вырезы, отверстия, гравировка, метка)
    y = 8.0
    for name, (a, b) in (("Шейка 1", (0, J0)), ("Шейка 2", (J1, L))):
        pts, holes = web(a, b)
        dx = 4 - a + (0 if a == 0 else 250 - J1 + a - a)
        dx = 4 if a == 0 else 4 + J0 + 12 - J1
        P.append((name, sh(pts, dx, y + TAB_B[1]), [], [(x + dx, yy + y + TAB_B[1], r) for x, yy, r in holes],
                  [], (dx + (a + b) / 2, y + TAB_B[1] + 40)))
    y = 8 + TAB_B[1] + WEB_H + TAB_T[1] + 6        # 110
    for name, (a, b) in (("Головка низ 1", (0, J0)), ("Головка низ 2", (J1, L))):
        o, s = head_lower(a, b)
        dx = 4 if a == 0 else 4 + J0 + 12 - J1
        P.append((name, sh(o, dx, y), [sh(q, dx, y) for q in s], [], [], (dx + (a + b) / 2, y + HEAD_W / 2)))
    y += HEAD_W + 6                                # ~153
    pieces = [("Верх 1а", 0, WEAR[0], False), ("Верх 1б", WEAR[1], J0, False), ("Верх 2", J1, L, True)]
    xs = [4, 4 + WEAR[0] + 6, 4 + WEAR[0] + 6 + (J0 - WEAR[1]) + 6]
    # верх 2 (234) не влезает в ту же строку - следующая строка
    for (name, a, b, chip), dx0 in zip(pieces, xs):
        if name == "Верх 2":
            dx, yy = 4 - a, y + HEAD_W + 6
        else:
            dx, yy = dx0 - a, y
        o = head_upper(a, b, chip)
        eng = []
        if name == "Верх 1б":
            eng = [[(p[0] + dx, p[1] + yy) for p in c] for c in CRACKS]
        P.append((name, sh(o, dx, yy), [], [], eng, (dx + (a + b) / 2, yy + HEAD_W / 2)))
    return P


def layout_6():
    o, s = base()
    return [("Основание", sh(o, 4, 4), [sh(q, 4, 4) for q in s], [], [], (244, 25))]


def layout_4():
    P = []
    for i in range(2):
        pts, holes = fishplate()
        dx, dy = 4 + i * 126, 4
        P.append(("Накладка", sh(pts, dx, dy), [], [(x + dx, y + dy, r) for x, y, r in holes], [],
                  (dx + 60, dy + 32)))
    return P


def area(parts):
    import math
    def pa(p):
        return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2
    return sum(pa(o) - sum(pa(c) for c in cu) - sum(math.pi * r * r for *_, r in h)
               for _, o, cu, h, _, _ in parts) / 100


def to_dxf(path, parts):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.layers.add("CUT", color=1)
    doc.layers.add("ENGRAVE", color=5)
    doc.layers.add("FIELD_500x300", color=8, linetype="DASHED")
    m = doc.modelspace()
    m.add_lwpolyline([(0, 0), (500, 0), (500, 300), (0, 300)], close=True, dxfattribs={"layer": "FIELD_500x300"})
    for name, o, cuts, holes, eng, lab in parts:
        m.add_lwpolyline(o, close=True, dxfattribs={"layer": "CUT"})
        for c in cuts:
            m.add_lwpolyline(c, close=True, dxfattribs={"layer": "CUT"})
        for x, y, r in holes:
            m.add_circle((x, y), r, dxfattribs={"layer": "CUT"})
        for e in eng:
            m.add_lwpolyline(e, dxfattribs={"layer": "ENGRAVE", "const_width": 1.5})
        m.add_text(name, height=4, dxfattribs={"layer": "ENGRAVE"}).set_placement(
            lab, align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


def draw(ax, parts, ox, oy, s=1.0, size=3.0):
    for name, o, cuts, holes, eng, lab in parts:
        ax.add_patch(Polygon([(ox + x * s, oy + y * s) for x, y in o], closed=True, fill=False, lw=mm2pt(0.5)))
        for c in cuts:
            ax.add_patch(Polygon([(ox + x * s, oy + y * s) for x, y in c], closed=True, fill=False, lw=mm2pt(0.5)))
        for x, y, r in holes:
            ax.add_patch(Circle((ox + x * s, oy + y * s), r * s, fill=False, lw=mm2pt(0.5)))
        for e in eng:
            ax.plot([ox + x * s for x, _ in e], [oy + y * s for _, y in e], color="0.35", lw=mm2pt(1.5))
        text(ax, ox + lab[0] * s, oy + lab[1] * s, name, size)


def side_view(ax, ox, oy, s):
    """Вид сбоку собранной рейки с разметкой дефектов."""
    def R(x0, y0, w, h, **kw):
        ax.add_patch(Rectangle((ox + x0 * s, oy + y0 * s), w * s, h * s, fill=False, lw=mm2pt(0.5), **kw))
    R(0, -6, L, 6)                                  # основание
    for a, b in ((0, J0), (J1, L)):
        R(a, 0, b - a, WEB_H)
        R(a, WEB_H, b - a, 10)
    for a, b in ((0, WEAR[0]), (WEAR[1], J0), (J1, L)):
        R(a, WEB_H + 10, b - a, 10)
    x0, x1, y0, y1 = FISH
    R(x0, y0, x1 - x0, y1 - y0, ls="--")
    for i, bx in enumerate(BOLTS):
        ax.add_patch(Circle((ox + bx * s, oy + 40 * s), 3.5 * s, fill=(i != 2), color="0.3", lw=mm2pt(0.4)))
    ax.add_patch(Polygon([(ox + (330 + dx) * s, oy + (0 + dy) * s) for dx, dy in
                          [(-4, 0), (4, 0), (6, 3.5), (4, 7), (-4, 7), (-6, 3.5)]], closed=True, color="0.3"))
    marks = [(30, "1 эталон"), (110, "2 износ 10"), (190, "3 трещины"), (240, "4 стык 12,\nнет 1 болта"),
             (330, "5 мусор (гайка)"), (406, "6 скол 9")]
    for x, t in marks:
        line(ax, ox + x * s, oy + 104 * s, ox + x * s, oy + 122 * s, TN)
        text(ax, ox + x * s, oy + 132 * s, t, 3.0)
    text(ax, ox, oy + 152 * s, "Вид сбоку (М 1:2,5): рейка в сборе и дефекты", 3.5, ha="left")


if __name__ == "__main__":
    out = "/home/claude/force1/testrail/out"
    os.makedirs(out, exist_ok=True)
    A10, A6, A4 = layout_10(), layout_6(), layout_4()
    to_dxf(f"{out}/ТР_фанера10.dxf", A10)
    to_dxf(f"{out}/ТР_фанера6_основание.dxf", A6)
    to_dxf(f"{out}/ТР_фанера4_накладки.dxf", A4)
    print("фанера 10:", round(area(A10)), "см2; фанера 6:", round(area(A6)), "; фанера 4:", round(area(A4)))
    W, H = 420, 297
    with PdfPages(f"{out}/ФОРС1_Тест-рейка_1к2.pdf") as pdf:
        fig, ax = sheet(W, H)
        frame(ax, W, H, "ФОРС1.06.00.000", "Тест-рейка 1:2\nс дефектами", 1, 1, scale="1:2",
              material="Фанера 10, 6, 4 мм")
        side_view(ax, 40, 222, 0.4)
        draw(ax, A10, 35, 62, 0.5, 2.2)
        text(ax, 35, 220 - 5 + 0, "", 2)
        text(ax, 35, 57, "Фанера 10 - раскладка в поле 500×300 (М 1:2)", 3.2, ha="left")
        ax.add_patch(Rectangle((35, 62), 250, 150, fill=False, lw=mm2pt(0.3), ls=(0, (6, 3))))
        draw(ax, A6, 300, 190, 0.2, 1.8)
        text(ax, 300, 186, "Фанера 6 - основание (М 1:5)", 3.0, ha="left")
        draw(ax, A4, 300, 160, 0.4, 1.8)
        text(ax, 300, 156, "Фанера 4 - накладки, 2 шт. (М 1:2,5)", 3.0, ha="left")
        reqs = ["Технические требования",
                f"1. Фанера 10 - {area(A10):.0f} см²,\n    фанера 6 - {area(A6):.0f} см², фанера 4 - {area(A4):.0f} см².",
                "2. Головку и шейку склеить,\n    основание - на шипах.",
                "3. Трещины - гравировка (ENGRAVE).",
                "4. Накладки с двух сторон шейки,\n    3 болта M4×40, 4-е отверстие пустое.",
                "5. Верх головки не красить."]
        for i, r in enumerate(reqs):
            text(ax, 292, 140 - 8 * i, r, 2.4 if i else 3.0, ha="left")
        pdf.savefig(fig)
    print("ok")
