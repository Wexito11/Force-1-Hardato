# Натурный образец: поперечная габаритная схема на пути 1520 (Р65, ж/б шпала), масштаб 1:10 на A3.
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon, Circle
from gost import sheet, frame, text, line, mm2pt, TH, TN

G = 1520.0          # колея по внутренним граням головок
B2B = 1440.0        # расстояние между внутренними гранями колёс колёсной пары
FLH, FLT = 28.0, 33.0   # гребень: высота, толщина
RAIL_H, HEAD_W, SOLE_W = 180.0, 75.0, 150.0   # Р65
PAD = 20.0          # подкладка + прокладка (прибл.)
TIE_H = 190.0       # шпала под рельсом (прибл.)
WD = 950.0          # колесо поезда
UGR = PAD + RAIL_H  # уровень головки рельса над верхом шпалы ~200
TR_LOW = 65.0       # низ необрессоренных частей подвижного состава над УГР (ГОСТ 9238)
CLR = 30.0          # запас
YW = B2B / 2 - 30   # робот в укрытии не дальше 690 от оси (30 до грани колеса поезда)


def draw(pdf):
    W, H = 420, 297
    fig, ax = sheet(W, H)
    frame(ax, W, H, "ФОРС1.00.00.000 ГЧ2", "Натурный образец.\nГабаритная схема", 1, 1, scale="1:10")
    s = 0.1
    ox, oy = 205, 120               # ось пути, верх шпалы
    X = lambda y: ox + y * s
    Z = lambda z: oy + z * s
    # шпала
    ax.add_patch(Rectangle((X(-1375), Z(-TIE_H)), 2750 * s, TIE_H * s, fc="#e0e0e0", ec="black", lw=mm2pt(TN)))
    text(ax, X(0), Z(-TIE_H / 2), "шпала ж/б 2750", 2.5)
    for sg in (-1, 1):
        yi = sg * G / 2
        yo = yi + sg * HEAD_W
        y0 = min(yi, yo)
        # подкладка, подошва, шейка, головка (упрощённо)
        ax.add_patch(Rectangle((X(y0 - 37.5 * sg * 0 + (-37.5 if sg > 0 else -37.5)) , Z(0)), 150 * s, PAD * s, fc="#999", ec="black", lw=mm2pt(TN)))
        yc = (yi + yo) / 2
        ax.add_patch(Rectangle((X(yc - SOLE_W / 2), Z(PAD)), SOLE_W * s, 12 * s, fc="#bbb", ec="black", lw=mm2pt(TN)))
        ax.add_patch(Rectangle((X(yc - 9), Z(PAD + 12)), 18 * s, (RAIL_H - 57) * s, fc="#bbb", ec="black", lw=mm2pt(TN)))
        ax.add_patch(Rectangle((X(yc - HEAD_W / 2), Z(UGR - 45)), HEAD_W * s, 45 * s, fc="#bbb", ec="black", lw=mm2pt(TN)))
        # колесо поезда: внутренняя грань на B2B/2, гребень внутри колеи
        yb = sg * B2B / 2
        yf = yb + sg * FLT
        ytr = yb + sg * 130
        ax.add_patch(Polygon([(X(yb), Z(UGR - FLH)), (X(yf), Z(UGR - FLH)), (X(yf), Z(UGR)), (X(ytr), Z(UGR)),
                              (X(ytr), Z(UGR + 300)), (X(yb), Z(UGR + 300))], closed=True, fc="#f3d9d9",
                             ec="#a33", lw=mm2pt(TN), hatch="///"))
    text(ax, X(-B2B / 2 - 60), Z(UGR + 330), "колесо поезда Ø950", 2.5)
    # УГР
    line(ax, X(-1500), Z(UGR), X(1500), Z(UGR), TN, ls="--")
    text(ax, X(1520), Z(UGR), "УГР", 2.5, ha="left")
    # зона укрытия
    zr = UGR + TR_LOW - CLR
    ax.add_patch(Rectangle((X(-YW), Z(0)), 2 * YW * s, zr * s, fc="#d6f0d6", ec="#2a7", lw=mm2pt(TH)))
    text(ax, X(0), Z(zr / 2 + 25), "ЗОНА УКРЫТИЯ РОБОТА", 3.5, color="#185")
    text(ax, X(0), Z(zr / 2 - 25), "ширина ≤ %d, высота ≤ %d над шпалой" % (2 * YW, zr), 2.8, color="#185")
    # размеры
    def dim(y1, y2, z, t):
        line(ax, X(y1), Z(z), X(y2), Z(z), TN)
        for y in (y1, y2):
            line(ax, X(y), Z(z) - 1.2, X(y), Z(z) + 1.2, TN)
        text(ax, (X(y1) + X(y2)) / 2, Z(z) + 2.2, t, 2.6)
    dim(-G / 2, G / 2, -TIE_H - 80, "1520 (колея)")
    dim(-B2B / 2, B2B / 2, UGR + 420, "1440 (между внутр. гранями колёс)")
    dim(-YW, YW, -TIE_H - 30, "%d" % (2 * YW))
    line(ax, X(-1300), Z(0), X(-1300), Z(UGR), TN)
    text(ax, X(-1300) - 1.5, Z(UGR / 2), "~%d" % UGR, 2.6, ha="right")
    # таблица
    rows = [("Параметр", "Натура", "Прототип 1:2", "Норма для 1:2"),
            ("Колея", "1520", "760", "760"),
            ("Рельс над шпалой (УГР)", "~200 (Р65 + подкладка)", "100", "100"),
            ("Внутр. грани колёс поезда", "1440", "-", "720"),
            ("Робот лёжа: высота над шпалой", "≤ 235 (УГР + 65 - 30)", "113 x 2 = 226", "≤ 117"),
            ("Робот лёжа: ширина", "≤ 1380", "680 (рейка 690)", "≤ 690"),
            ("Колёса робота в укрытии", "внутри зоны", "внутри зоны", "-")]
    cw = [62, 50, 50, 38]
    x0, y0 = 222, 280
    for i, r in enumerate(rows):
        x = x0
        for j, c in enumerate(r):
            text(ax, x + 1.2, y0 - i * 7, c, 2.4 if i else 2.6, ha="left")
            x += cw[j]
        line(ax, x0, y0 - i * 7 - 3.5, x0 + sum(cw), y0 - i * 7 - 3.5, TH if i == 0 else TN)
    tr = ["Требования к натурному образцу:",
          "1. В режиме укрытия робот ниже необрессоренных частей подвижного состава (65 мм над УГР по",
          "   ГОСТ 9238, запас 30 мм) и внутри внутренних граней колёс поезда (запас 30 мм на сторону).",
          "2. Колёса робота в укрытии убираются внутрь зоны (поворот на рычагах полозьев) или имеют Ø ≤ 140.",
          "3. Лидар утоплен в крышку модуля A, камера смотрит вверх через окно крышки.",
          "4. Части робота выше УГР в рабочем режиме сверять с нижним очертанием габарита ГОСТ 9238-2013.",
          "5. Прототип выполнен в масштабе 1:2 с теми же требованиями (лист ФОРС1.00.00.000 ГЧ1).",
          "Размеры Р65, ж/б шпалы и подкладки - номинальные, высота УГР над шпалой приблизительная."]
    for i, t in enumerate(tr):
        text(ax, 25, 60 - i * 5, t, 2.4, ha="left")
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    with PdfPages("out/ФОРС1_Натурный_габарит.pdf") as pdf:
        draw(pdf)
