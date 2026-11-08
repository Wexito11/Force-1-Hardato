# ГОСТ-подобная рамка и основная надпись (ГОСТ 2.104, форма 1, упрощённо) на matplotlib, единицы - мм
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch, Circle

matplotlib.rcParams["font.family"] = "DejaVu Sans"
FONT = dict(fontstyle="italic")
TH = 0.7   # основная линия, мм
TN = 0.3   # тонкая


def mm2pt(w):
    return w / 25.4 * 72


def sheet(W, H):
    fig = plt.figure(figsize=(W / 25.4, H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def line(ax, x1, y1, x2, y2, w=TN, **kw):
    ax.plot([x1, x2], [y1, y2], color="black", lw=mm2pt(w), solid_capstyle="butt", **kw)


def text(ax, x, y, s, size=3.5, ha="center", va="center", **kw):
    # size - высота шрифта в мм
    ax.text(x, y, s, fontsize=mm2pt(size) / 0.72, ha=ha, va=va, **FONT, **kw)


def frame(ax, W, H, designation, name, sheet_no=1, sheets=1, scale="", mass="",
          material="", developer="Гутьеррес", org="МГТУ им. Н.Э. Баумана\nкоманда «Форс-1»"):
    # внешняя тонкая граница листа и рамка 20/5/5/5
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, lw=mm2pt(TN)))
    ax.add_patch(Rectangle((20, 5), W - 25, H - 10, fill=False, lw=mm2pt(TH)))
    # основная надпись 185 x 55 в правом нижнем углу
    x0, y0 = W - 5 - 185, 5
    ax.add_patch(Rectangle((x0, y0), 185, 55, fill=False, lw=mm2pt(TH)))
    cols = [7, 10, 23, 15, 10]
    xs = [x0]
    for c in cols:
        xs.append(xs[-1] + c)
    # левая часть: 11 строк по 5 мм
    for i in range(1, 11):
        line(ax, x0, y0 + 5 * i, x0 + 65, y0 + 5 * i, TH if i in (5, 6) else TN)
    for xv in xs[1:-1]:
        line(ax, xv, y0 + 25, xv, y0 + 55, TH)
    line(ax, xs[1], y0, xs[1], y0 + 25, TN)  # граница подписей внизу
    for xv in (xs[3], xs[4]):
        line(ax, xv, y0, xv, y0 + 25, TH)
    line(ax, x0 + 65, y0, x0 + 65, y0 + 55, TH)
    hdr = ["Изм.", "Лист", "№ докум.", "Подп.", "Дата"]
    for i, h in enumerate(hdr):
        text(ax, (xs[i] + xs[i + 1]) / 2, y0 + 27.5, h, 2.2)
    roles = ["Разраб.", "Пров.", "Т.контр.", "Н.контр.", "Утв."]
    for i, r in enumerate(roles):
        yy = y0 + 22.5 - 5 * i
        text(ax, x0 + 1, yy, r, 2.2, ha="left")
    text(ax, xs[2] + 1, y0 + 22.5, developer, 2.2, ha="left")
    # правая часть
    xr = x0 + 65
    line(ax, xr, y0 + 40, x0 + 185, y0 + 40, TH)
    text(ax, xr + 60, y0 + 47.5, designation, 5)
    line(ax, xr + 70, y0, xr + 70, y0 + 40, TH)
    text(ax, xr + 35, y0 + 27, name, 3.5, wrap=True)
    line(ax, xr, y0 + 15, xr + 70, y0 + 15, TH)
    text(ax, xr + 35, y0 + 7.5, material, 3.0)
    xa = xr + 70
    line(ax, xa, y0 + 35, xa + 50, y0 + 35, TH)
    line(ax, xa, y0 + 20, xa + 50, y0 + 20, TH)
    line(ax, xa, y0 + 15, xa + 50, y0 + 15, TH)
    for xv in (xa + 17, xa + 34):
        line(ax, xv, y0 + 20, xv, y0 + 40, TH)
    text(ax, xa + 8.5, y0 + 37.5, "Лит.", 2.2)
    text(ax, xa + 25.5, y0 + 37.5, "Масса", 2.2)
    text(ax, xa + 42, y0 + 37.5, "Масштаб", 2.2)
    text(ax, xa + 8.5, y0 + 27.5, "У", 3.5)
    text(ax, xa + 25.5, y0 + 27.5, mass, 3.0)
    text(ax, xa + 42, y0 + 27.5, scale, 3.5)
    line(ax, xa + 25, y0 + 15, xa + 25, y0 + 20, TN)
    text(ax, xa + 1, y0 + 17.5, f"Лист {sheet_no}", 2.2, ha="left")
    text(ax, xa + 26, y0 + 17.5, f"Листов {sheets}", 2.2, ha="left")
    text(ax, xa + 25, y0 + 7.5, org, 2.5)
    return x0, y0
