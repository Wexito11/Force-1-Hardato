import math
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon, Circle
from gost import *
import drawings as D
import track as TR
import params as P
import corpus as C

DES = "ФОРС1.02.00.000"

def R(ax, x, y, w, h, lw=TH, ls="-", fc="none", hatch=None):
    ax.add_patch(Rectangle((x, y), w, h, fill=fc != "none", facecolor=fc, edgecolor="black",
                           lw=mm2pt(lw), ls=ls, hatch=hatch))

def section(ax, ox, oy, s, state, title):
    """Поперечный разрез (Y-Z). ox,oy - точка (Y=0, Z=0 верх головки). state 0/1."""
    d = state * P.STROKE / 2
    zoff = 0 if state == 0 else -(TR.RAIL_H)      # в укрытии робот на шпалах
    X = lambda y: ox + y * s
    Z = lambda z: oy + z * s
    # шпала и рельсы
    R(ax, X(-140), Z(-TR.RAIL_H - TR.TIE_T), 280 * s, TR.TIE_T * s, TN, fc="#e8e8e8")
    for sg in (-1, 1):
        y0 = sg * (P.GAUGE / 2) if sg > 0 else -(P.GAUGE / 2 + P.RAIL_T)
        R(ax, X(y0), Z(-TR.RAIL_H), P.RAIL_T * s, TR.RAIL_H * s, TN, fc="#d9c3a5")
    for sg, dy in ((-1, d), (1, -d)):
        yin, yout = sg * P.Y_IN + dy, sg * P.Y_OUT + dy
        y0 = min(yin, yout)
        R(ax, X(y0), Z(zoff), P.BW * s, P.BH * s, TH)
        R(ax, X(y0), Z(zoff + P.BH), P.BW * s, P.LID * s, TN, fc="#cfe8f5")
        # колесо: реборда Ø60 x5, обод Ø50 x15
        yf = sg * P.Y_FL + dy
        yfl = yf if sg > 0 else yf - P.FL
        ytr = yf + sg * P.FL if sg > 0 else yf - P.WW
        R(ax, X(yfl), Z(zoff + P.AXLE_Z - 30), P.FL * s, 60 * s, TN, fc="#555555")
        R(ax, X(ytr), Z(zoff), (P.WW - P.FL) * s, P.WD * s, TN, fc="#777777")
        # труба
    for sg in (1,):
        pass
    ya, yb = P.TUBE_A_END + d, P.TUBE_B_END + d
    R(ax, X(ya), Z(zoff + P.TUBE_Z - 5), (yb - ya) * s, 10 * s, TN, fc="#b8c2cc")
    # ремень
    line(ax, X(-49 + d), Z(zoff + P.BELT_Z), X(P.NEMA_YC - d), Z(zoff + P.BELT_Z), 0.6)
    ax.add_patch(Circle((X(P.NEMA_YC - d), Z(zoff + P.SHAFT_Z)), P.DRUM_D / 2 * s, fill=False, lw=mm2pt(TN)))
    text(ax, X(0), Z(zoff + P.BH + 22), title, 3.5)
    return X, Z, d, zoff

def sheet_gabarit(pdf):
    W, H = 420, 297
    fig, ax = sheet(W, H)
    frame(ax, W, H, DES + " ГЧ", "Габаритная схема\nтелескопа и корпусов", 1, 3, scale="1:2", material="")
    s = 0.5
    X, Z, d, zo = section(ax, 120, 175, s, 0, "А-А. На рельсах (А4988 откл., пружины разводят)")
    D.dim_h(ax, X(-P.GAUGE / 2), X(P.GAUGE / 2), Z(-58), "190 (колея)", Z(-40))
    D.dim_h(ax, X(-P.Y_FL - P.WW), X(P.Y_FL + P.WW), Z(-72), "220 по колёсам", Z(0))
    D.dim_h(ax, X(-P.Y_IN), X(P.Y_IN), Z(P.BH + 8), "40", Z(P.BH))
    D.dim_h(ax, X(P.Y_IN), X(P.Y_OUT), Z(P.BH + 8), "66", Z(P.BH))
    D.dim_v(ax, X(-P.Y_FL - P.WW - 12), Z(0), Z(P.BH), "80", X(-P.Y_OUT))
    D.dim_v(ax, X(P.Y_FL + P.WW + 10), Z(0), Z(P.TUBE_Z), "65", X(P.Y_OUT))
    X2, Z2, d2, zo2 = section(ax, 120, 72, s, 1, "Б-Б. Укрытие: сжат на 37 мм, на шпалах")
    D.dim_h(ax, X2(-P.Y_FL - P.WW + d2), X2(P.Y_FL + P.WW - d2), Z2(-30), "183 < 190", Z2(-40))
    D.tech_req(ax, 235, 270, [
        "1. Колея 190, головка рельса 10. Реборда 5 мм упирается в внутр. грань рельса.",
        "2. Колесо Ø50, ширина 20 (реборда 5 + обод 15). Зазор колесо-стенка 4.",
        "3. Корпус 66 x 200 x 80, фанера 4 мм, крышка оргстекло 3 мм.",
        "4. Зазор между модулями: 40 на рельсах, 3 в сжатом. Ход телескопа 37.",
        "5. В сжатом: ширина по колёсам 183, до рельсов по 3,5 с каждой стороны.",
        "6. Трубы Ø10x1 L=86, 2 шт., X = ±55, Z = 65 от низа корпуса.",
        "7. В A трубы зажаты втулками-фиксаторами, в B скользят во втулках.",
        "8. NEMA17 в B: вал вдоль X, барабан Ø15, ремень GT2 Z = 38,7.",
        "9. Колодка ремня в A на дне, пазы 3,3x10 - натяжка и ноль колеи.",
        "10. Пружины-арки PETG 64x20x1 (2 шт.), X = ±82: ~8 Н каждая.",
        "11. Лежащий робот: верх крышки 93 над столом (с лидаром 134).",
        "    Низ перекладин «вагона» поднять до >= 155.",
    ], size=2.8)
    pdf.savefig(fig); plt.close(fig)

def wall_view(ax, part, ox, oy, s=1.0):
    D.draw_parts(ax, [part], ox, oy, s, labels=False)

def sheet_interface(pdf):
    W, H = 420, 297
    fig, ax = sheet(W, H)
    frame(ax, W, H, DES + " ИЛ", "Интерфейсный лист:\nвнутренние стенки A и B", 2, 3, scale="1:1",
          material="Фанера 4 ГОСТ 3916.1-2018")
    A, B = C.module_parts("A"), C.module_parts("B")
    for k, (part, oy, t) in enumerate(((A[0], 190, "A-1 (вид из зазора)"), (B[0], 80, "B-1 (вид из зазора)"))):
        ox = 40
        wall_view(ax, part, ox, oy)
        text(ax, ox + 100, oy + 88, t, 3.5)
        u = lambda X: ox + X + 100
        D.dim_h(ax, u(-P.TUBE_X), u(P.TUBE_X), oy - 10, "110", oy + P.TUBE_Z)
        D.dim_h(ax, u(0), u(P.BELT_X), oy + 86 - 4, "24,5", oy + P.BELT_Z) if False else None
        D.dim_v(ax, ox + 212, oy, oy + P.TUBE_Z, "65", ox + 200)
        D.dim_v(ax, ox + 224, oy, oy + P.BELT_Z, "38,7", ox + 200)
        D.dim_v(ax, ox + 236, oy, oy + P.BH, "80", ox + 200)
        d = "Ø10,4" if part[0].startswith("A") else "Ø14,4"
        text(ax, u(P.TUBE_X), oy + P.TUBE_Z + 11, f"{d}, 2 отв. Ø3,3 на ±11", 2.5)
        text(ax, u(P.BELT_X), oy + P.BELT_Z + 8, "паз ремня 12x7, X=%s" % str(P.BELT_X).replace(".", ","), 2.5)
        text(ax, u(P.SPRING_X) - 4, oy + 34, "2xØ3,3 пружина", 2.5)
    D.tech_req(ax, 290, 270, [
        "Начало X - середина корпуса, +X - к ведущему колесу.",
        "Высоты - от нижней кромки стенки.",
        "",
        "Наружная стенка (A-2, B-2):",
        " ведущее колесо X=+80, Z=25: Ø8,4 +",
        "   2 отв. Ø3,3 через 17 (JGA25-370);",
        " холостое X=-80, Z=25: Ø4,3 (ось M4).",
        "Торцевые стенки: Ø12 под провода.",
        "Дно A: 4 паза 3,3x10 под колодку,",
        "   X = 4,5 и 44,5; |Y| = 41 и 57.",
        "Дно: шип-паз 20x4, пазы в стенках",
        "   на высоте 6-10 мм.",
        "Отверстия под платы и датчики -",
        "   по компоновке Участника 1.",
    ], size=2.8)
    pdf.savefig(fig); plt.close(fig)

def sheet_parts(pdf):
    W, H = 420, 297
    fig, ax = sheet(W, H)
    frame(ax, W, H, DES + " СП", "Телескоп и привод:\nдетали и материалы", 3, 3, material="")
    rows = [("Поз.", "Наименование", "Кол.", "Материал / технология", "Примечание"),
            ("1", "Труба Ø10x1, L=86", "2", "Алюм. труба Ø10 (Прил. 1), резка", "172 мм из 500"),
            ("2", "Втулка скользящая B", "2", "Печать PETG", "отв. 10,4; Ø14 сквозь стенку"),
            ("3", "Втулка-фиксатор A", "2", "Печать PETG", "отв. 10,1; стопор M3"),
            ("4", "Колодка ремня A", "1", "Печать PETG, 30%", "канал 6,5; гайки M3 снизу"),
            ("5", "Планка ремня A", "1", "Печать PETG", "зубья GT2 шаг 2"),
            ("6", "Пружина-арка", "2", "Печать PETG 100%", "64x20x1, ~8 Н"),
            ("7", "Кронштейн пружины", "4", "Печать PETG", "ось M3"),
            ("8", "Барабан Ø15 на NEMA17", "1", "Печать (модель У1)", "магнит AS5600 в торце"),
            ("9", "Ремень GT2", "1", "Прил. 1", "~200 мм из 1 м"),
            ("10", "Шаговый NEMA17 + A4988", "1", "Прил. 1", "0,74 об. на ход"),
            ("11", "Энкодер AS5600", "1", "Прил. 1", "0,0115 мм/отсчёт"),
            ("12", "Винт M3x12 + гайка", "16", "Прил. 1", "втулки, планка, кронштейны"),
            ("13", "Винт M3x10 + гайка", "8", "Прил. 1", "колодка к дну, кронштейны"),
            ("14", "Винт M3x20 + гайка", "4", "Прил. 1", "оси пружин")]
    cw = [12, 62, 12, 70, 62]
    x0, y0 = 30, 270
    for i, r in enumerate(rows):
        x = x0
        for j, c in enumerate(r):
            text(ax, x + 1.5, y0 - i * 8, c, 3 if i else 3.2, ha="left")
            x += cw[j]
        line(ax, x0, y0 - i * 8 - 4, x0 + sum(cw), y0 - i * 8 - 4, TN if i else TH)
    D.tech_req(ax, 30, 140, [
        "Расчёт привода: барабан Ø15 - 47,1 мм/об; ход 37 = 0,79 об = 157 шагов (2510 микрошагов 1/16).",
        "Усилие: NEMA17 0,40 Н·м / 7,5 мм = 53 Н удержание; нужно пружины 2x8 + трение ~5 = 21 Н.",
        "AS5600: 4096 отсч./об -> 0,0115 мм; реальная точность колеи ±0,2 мм (люфт, ремень); порог 2 мм.",
        "Пружина-арка: эйлерова сила F = π²EI/L², E(PETG) = 2 ГПа, I = 20·1³/12 -> 8 Н, почти постоянна по ходу.",
        "Посадка труб: алюминий Ø10 реальный 9,9-10,0; отв. втулок печатать 10,4 / 10,1, при туге - развернуть сверлом.",
        "Печать телескопа ~83 г при 100 % (колодка 30 % - ~55 г). Лимит 800 г - общий с У1 и У4.",
        "Жгут W1 (7 жил) - внутри трубы X=-55, петля запаса 50 мм в B.",
    ], size=2.8)
    pdf.savefig(fig); plt.close(fig)

def laser_pdf(path):
    s1, s2 = C.layouts()
    _, shims = TR.layout_small()
    shims = [C.place(p, 80, 0) for p in shims]
    s2 = s2 + shims
    lids = C.lid_parts()
    with PdfPages(path) as pdf:
        for n, (parts, mat, extra) in enumerate([
                (s1, "Фанера 4 ГОСТ 3916.1-2018", ["1. Корпуса A и B: стенки -1..-4, дно -5.",
                                                    "2. Пазы 20,2x4,2 - подогнать по факт. толщине фанеры."]),
                (s2, "Фанера 4 ГОСТ 3916.1-2018", ["1. B-4 - торцевая стенка B; подкладки демо-пути (У4) - 3 шт."]),
                (lids, "Оргстекло 3 мм", ["1. Крышки A-6, B-6; отв. Ø3,3 - к печатным уголкам.",
                                          "2. Лидар, камера, XFW-001, тумблер - по компоновке У1."])]):
            fig, ax, ox, oy = D.sheet_layout(pdf, parts, "Корпуса модулей.\nРаскладка, лист %d" % (n + 1),
                                             "ФОРС1.02.01.00%d" % (n + 1), mat, n + 1, 3, extra)
            pdf.savefig(fig); plt.close(fig)
        D.to_dxf("out/Лазер DXF/ФОРС1_корпуса_фанера4_лист1.dxf", s1)
        D.to_dxf("out/Лазер DXF/ФОРС1_корпуса_фанера4_лист2.dxf", s2)
        D.to_dxf("out/Лазер DXF/ФОРС1_крышки_оргстекло3.dxf", lids)
    return TR.net_area(s1), TR.net_area(s2), TR.net_area(lids)

if __name__ == "__main__":
    import os
    os.makedirs("out/Лазер DXF", exist_ok=True)
    with PdfPages("out/ФОРС1_Телескоп_габариты_интерфейс.pdf") as pdf:
        sheet_gabarit(pdf); sheet_interface(pdf); sheet_parts(pdf)
    print(laser_pdf("out/ФОРС1_Чертежи_корпусов_лазер.pdf"))
