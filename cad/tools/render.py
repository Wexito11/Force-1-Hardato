# Превью-рендеры моделей (matplotlib) -> PNG
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cadquery as cq
import cad

LIGHT = np.array([0.4, -0.5, 0.8]); LIGHT /= np.linalg.norm(LIGHT)


def mesh(shape, tol=0.3):
    v, f = shape.tessellate(tol, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in v])
    return v, np.array(f)


def add(ax, shape, rgb, tol=0.3):
    v, f = mesh(shape, tol)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    k = 0.45 + 0.55 * np.abs(n @ LIGHT)
    cols = np.clip(np.outer(k, rgb), 0, 1)
    pc = Poly3DCollection(tri, facecolors=cols, edgecolors="none", linewidths=0)
    ax.add_collection3d(pc)
    return v


def assy_items(a):
    out = []
    for name, (shape, loc, color) in [(c.name, (c.obj, c.loc, c.color)) for c in a.traverse() if False]:
        pass
    for child in a.children:
        sh = child.obj.val() if hasattr(child.obj, "val") else child.obj
        sh = sh.moved(child.loc)
        rgb = child.color.toTuple()[:3] if child.color else (0.7, 0.7, 0.7)
        out.append((sh, rgb))
    return out


def render(items, path, elev, azim, lims=None, size=(12, 7), title=None, tol=0.3):
    fig = plt.figure(figsize=size, dpi=150)
    ax = fig.add_subplot(111, projection="3d", computed_zorder=True)
    allv = []
    for sh, rgb in items:
        allv.append(add(ax, sh, rgb, tol))
    V = np.vstack(allv)
    lo, hi = (V.min(0), V.max(0)) if lims is None else lims
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(np.maximum(hi - lo, 1)), zoom=1.25)
    ax.view_init(elev, azim)
    ax.set_axis_off()
    if title:
        fig.suptitle(title, fontsize=13)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    tr = assy_items(cad.track_assembly())
    render(tr, "out/render_путь_общий.png", 28, -60, tol=0.5,
           title="Демо-путь «Форс-1»: 2 звена x 495 мм, колея 190, «вагон», препятствие")
    lims = (np.array([400, -160, 0]), np.array([620, 160, 60]))
    near = [(s, c) for s, c in tr if s.BoundingBox().xmin < 640 and s.BoundingBox().xmax > 380]
    render(near, "out/render_путь_стык.png", 30, -35, lims=lims, tol=0.2,
           title="Стык: зазор 6 мм, накладки, ослабленный болт (справа), мусор, RFID")
    parts = [(cad.socket().val(), (0.2, 0.6, 0.3)),
             (cad.wrench_arm().translate((0, 60, 0)).val(), (0.2, 0.6, 0.3)),
             (cad.jga25().translate((150, 60, 0)).val(), (0.7, 0.7, 0.72)),
             (cad.magnet_arm().translate((0, 130, 0)).val(), (0.9, 0.5, 0.15)),
             (cq.Workplane("XY").circle(12.5).extrude(20).translate((83, 130, -35)).val(), (0.5, 0.5, 0.55)),
             (cad.token_magazine().translate((40, 0, 0)).val(), (0.2, 0.4, 0.8)),
             (cad.token_slider().translate((40, -40, 0)).val(), (0.2, 0.4, 0.8)),
             (cad.token().translate((90, 0, 0)).val(), (0.95, 0.85, 0.1)),
             (cad.nozzle().translate((130, 0, 0)).val(), (0.8, 0.2, 0.2)),
             (cad.mg90s().translate((150, 130, 0)).val(), (0.15, 0.3, 0.7))]
    render(parts, "out/render_ремонтный_модуль.png", 30, -55, tol=0.1,
           title="Ремонтный модуль: гайковёрт, электромагнит, магазин меток, сопло")
    wh = assy_items(cad.weld_head_concept())
    render(wh, "out/render_сварка_концепт.png", 20, -50, tol=0.2,
           title="Концепт: позиционер сварочной головки на стыке")
    print("ok")
