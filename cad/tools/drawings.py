# Чертежи деталей демо-пути под лазер: DXF (резка) + PDF (ГОСТ-рамка, 1:1)
import math
import ezdxf
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Circle, Rectangle
from gost import *
import track as T

OUT = "out"


# ---------------- DXF ----------------
def to_dxf(path, parts, frame_wh=(500, 300), title=""):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.layers.add("CUT", color=1)
    doc.layers.add("ENGRAVE", color=5)
    doc.layers.add("FIELD_500x300", color=8, linetype="DASHED")
    msp = doc.modelspace()
    if frame_wh:
        w, h = frame_wh
        msp.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True,
                           dxfattribs={"layer": "FIELD_500x300"})
    for name, outer, cuts, holes, lab in parts:
        msp.add_lwpolyline(outer, close=True, dxfattribs={"layer": "CUT"})
        for c in cuts:
            msp.add_lwpolyline(c, close=True, dxfattribs={"layer": "CUT"})
        for x, y, r in holes:
            msp.add_circle((x, y), r, dxfattribs={"layer": "CUT"})
        msp.add_text(name, height=4, dxfattribs={"layer": "ENGRAVE"}).set_placement(
            lab, align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)


# ---------------- PDF ----------------
def draw_parts(ax, parts, ox, oy, s=1.0, labels=True, lsize=3.5):
    for name, outer, cuts, holes, lab in parts:
        P = [(ox + x * s, oy + y * s) for x, y in outer]
        ax.add_patch(Polygon(P, closed=True, fill=False, lw=mm2pt(0.5)))
        for c in cuts:
            ax.add_patch(Polygon([(ox + x * s, oy + y * s) for x, y in c], closed=True,
                                 fill=False, lw=mm2pt(0.5)))
        for x, y, r in holes:
            ax.add_patch(Circle((ox + x * s, oy + y * s), r * s, fill=False, lw=mm2pt(0.5)))
        if labels:
            rot = 90 if (max(p[1] for p in outer) - min(p[1] for p in outer)) > 150 else 0
            text(ax, ox + lab[0] * s, oy + lab[1] * s, name, lsize, rotation=rot)


def field(ax, ox, oy, w=500, h=300, s=1.0):
    ax.add_patch(Rectangle((ox, oy), w * s, h * s, fill=False, lw=mm2pt(0.35), ls=(0, (6, 3))))
    dim_h(ax, ox, ox + w * s, oy - 12, f"{w}", oy)
    dim_v(ax, ox - 12, oy, oy + h * s, f"{h}", ox)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>,head_length=0.9,head_width=0.3",
                                lw=mm2pt(TN), color="black", shrinkA=0, shrinkB=0))


def dim_h(ax, x1, x2, y, s, yref=None, size=3.5):
    if yref is not None:
        for x in (x1, x2):
            line(ax, x, yref, x, y - 2 if y < yref else y + 2)
    line(ax, x1, y, x2, y)
    arrow(ax, (x1 + x2) / 2, y, x1, y)
    arrow(ax, (x1 + x2) / 2, y, x2, y)
    text(ax, (x1 + x2) / 2, y + 2.6, s, size)


def dim_v(ax, x, y1, y2, s, xref=None, size=3.5):
    if xref is not None:
        for y in (y1, y2):
            line(ax, xref, y, x - 2 if x < xref else x + 2, y)
    line(ax, x, y1, x, y2)
    arrow(ax, x, (y1 + y2) / 2, x, y1)
    arrow(ax, x, (y1 + y2) / 2, x, y2)
    text(ax, x - 2.6, (y1 + y2) / 2, s, size, rotation=90)


def tech_req(ax, x, y, lines, size=3.0):
    text(ax, x, y, "Технические требования", size + 0.5, ha="left")
    for i, l in enumerate(lines):
        text(ax, x, y - 6 * (i + 1), l, size, ha="left")


def sheet_layout(pdf, parts, title, des, mat, sheet_no, sheets, extra):
    W, H = 594, 420
    fig, ax = sheet(W, H)
    frame(ax, W, H, des, title, sheet_no, sheets, scale="1:1", material=mat)
    ox, oy = 45, 95
    field(ax, ox, oy)
    draw_parts(ax, parts, ox, oy)
    area = T.net_area(parts)
    tech_req(ax, 30, 75, extra + [
        f"Площадь деталей {area:.0f} см², поле 500 x 300 = 1500 см².",
        "Пунктир - граница рабочего поля лазера, не резать."])
    return fig, ax, ox, oy


def rail_detail(pdf, n, N):
    W, H = 420, 297
    fig, ax = sheet(W, H)
    frame(ax, W, H, "ФОРС1.05.00.003", "Рельс П1.\nШпала", n, N, scale="1:2",
          material="Фанера 10 мм")
    # Рельс П1, масштаб 1:1 на A3 не помещается целиком по длине (495) -> 1:1.5? даём 1:1.25
    s = 0.5
    ox, oy = 45, 215
    pts, holes = T.rail_outline(1, "П")
    draw_parts(ax, [("", pts, [], holes, (0, 0))], ox, oy, s, labels=False)
    text(ax, ox, oy + 50, "Рельс П1 (М 1:2). Л1 - то же без выреза; Л2, П2 - отверстия у начала", 3.2, ha="left")
    dim_h(ax, ox, ox + T.RAIL_L * s, oy - 24, "495", oy - T.TAB_H * s)
    dim_v(ax, ox - 8, oy, oy + T.RAIL_H * s, "40", ox)
    dim_v(ax, ox - 16, oy - T.TAB_H * s, oy + T.RAIL_H * s, "50", ox)
    a, b, d = T.WEAR
    dim_h(ax, ox + a * s, ox + b * s, oy + T.RAIL_H * s + 8, "40", oy + T.RAIL_H * s)
    dim_h(ax, ox, ox + a * s, oy + T.RAIL_H * s + 8, "140", oy + T.RAIL_H * s)
    text(ax, ox + (a + b) / 2 * s, oy + (T.RAIL_H - d) * s - 4, "глубина 3", 2.8)
    # шипы
    t0 = T.tie_x(0)
    dim_h(ax, ox, ox + t0 * s, oy - 14, "56", oy - T.TAB_H * s)
    dim_h(ax, ox + t0 * s, ox + T.tie_x(1) * s, oy - 14, "68", oy - T.TAB_H * s)
    text(ax, ox + 300 * s, oy - 9, "7 шипов 15 x 10 с шагом 68", 2.8, ha="left")
    # отверстия
    text(ax, ox + 470 * s, oy + 4, "2 отв. Ø4,3", 2.6)
    dim_h(ax, ox + 474 * s, ox + 495 * s, oy + T.RAIL_H * s + 8, "21", oy + T.RAIL_H * s)
    # Шпала (тип звена 1) 1:1
    ox2, oy2 = 40, 100
    pts, slots, uL, uR = T.tie_outline(0)
    draw_parts(ax, [("", pts, slots, [], (0, 0))], ox2, oy2, 1, labels=False)
    text(ax, ox2, oy2 + 45, "Шпала Ш1-Ш7 (М 1:1). Ш8-Ш14 - левый паз смещён наружу на 0,4-5,3 мм (см. DXF)",
         3.2, ha="left")
    dim_h(ax, ox2, ox2 + 280, oy2 - 14, "280", oy2)
    dim_v(ax, ox2 - 8, oy2, oy2 + 31, "31", ox2)
    dim_h(ax, ox2 + uL + 5.2, ox2 + uR - 5.2, oy2 + 38, "190 (колея)", oy2 + 31)
    dim_h(ax, ox2, ox2 + uL, oy2 - 6, "40", oy2)
    text(ax, ox2 + uR, oy2 + 15.5 - 12, "2 паза 10,4 x 15,4", 2.8)
    tech_req(ax, 30, 75, [
        "1. Изготовить лазерной резкой из фанеры 10 мм.",
        "2. Ширину пазов 10,4 подогнать по фактической толщине фанеры (натяг 0-0,2 мм).",
        "3. Шипы рельсов в пазы шпал не клеить - путь разборный.",
        "4. Неуказанные размеры - по DXF."])
    pdf.savefig(fig)


def small_sheet(pdf, n, N):
    W, H = 297, 210
    fig, ax = sheet(W, H)
    frame(ax, W, H, "ФОРС1.05.00.010", "Накладка стыка.\nПодкладка", n, N, scale="1:1",
          material="Фанера 3 мм / 4 мм")
    fp, sh = T.layout_small()
    draw_parts(ax, fp, 30, 125, labels=False)
    draw_parts(ax, sh, 30, 40, labels=False)
    dim_h(ax, 35, 95, 120, "60", 130)
    dim_v(ax, 27, 130, 150, "20", 35)
    dim_h(ax, 35, 66, 80, "31", 85)
    dim_v(ax, 27, 85, 115, "30", 35)
    dim_h(ax, 35, 41, 158, "6", 150)
    dim_h(ax, 41, 53, 158, "12", 150)
    text(ax, 30, 205 - 20, "Накладка - фанера 3 мм, 4 шт., 4 отв. Ø4,3 (шаг 12/24/12)", 3, ha="left")
    text(ax, 30, 205 - 27, "Подкладка - фанера 4 мм, 3 шт., 31 x 30 (перекос 4/190 = 1,2°)", 3, ha="left")
    text(ax, 30, 205 - 34, "Детали вставить в общую раскладку листов 3 мм и 4 мм.", 3, ha="left")
    pdf.savefig(fig)


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    A, B = T.layout_sheet_A(), T.layout_sheet_B()
    fp, sh = T.layout_small()
    to_dxf(f"{OUT}/ФОРС1_путь_фанера10_лист1.dxf", A)
    to_dxf(f"{OUT}/ФОРС1_путь_фанера10_лист2.dxf", B)
    to_dxf(f"{OUT}/ФОРС1_путь_накладки_фанера3.dxf", fp, frame_wh=None)
    to_dxf(f"{OUT}/ФОРС1_путь_подкладки_фанера4.dxf", sh, frame_wh=None)
    N = 4
    with PdfPages(f"{OUT}/ФОРС1_Чертежи_демо-пути.pdf") as pdf:
        fig, ax, ox, oy = sheet_layout(pdf, A, "Демо-путь.\nРаскладка, лист 1", "ФОРС1.05.00.001",
                                       "Фанера 10 мм", 1, N,
                                       ["1. Рельсы Л1, П1, Л2, П2 - 4 шт., опоры вагона - 4 шт.",
                                        "2. На П1 - вырез 40 x 3 мм (дефект «износ головки»)."])
        pdf.savefig(fig)
        fig, ax, ox, oy = sheet_layout(pdf, B, "Демо-путь.\nРаскладка, лист 2", "ФОРС1.05.00.002",
                                       "Фанера 10 мм", 2, N,
                                       ["1. Шпалы Ш1-Ш14, номер гравировать.",
                                        "2. Ш8-Ш14 - уширение колеи до 5,3 мм (дефект «колея»)."])
        pdf.savefig(fig)
        rail_detail(pdf, 3, N)
        small_sheet(pdf, 4, N)
    print("A", round(T.net_area(A)), "B", round(T.net_area(B)), "сумма", round(T.net_area(A) + T.net_area(B)))
