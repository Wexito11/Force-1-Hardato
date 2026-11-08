# Софт-рендер с z-буфером: ортографическая камера, плоское затенение, сглаживание 2x
import numpy as np
from PIL import Image, ImageFilter

KEY = np.array([0.45, -0.55, 0.70]); KEY /= np.linalg.norm(KEY)
FILL = np.array([-0.5, 0.4, 0.35]); FILL /= np.linalg.norm(FILL)


def mesh(shape, tol):
    v, f = shape.tessellate(tol, 0.25)
    return np.array([(p.x, p.y, p.z) for p in v], float), np.array(f, int)


def cam(elev, azim):
    e, a = np.radians(elev), np.radians(azim)
    # направление взгляда (из камеры к сцене), как в matplotlib view_init
    d = -np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    up = np.array([0, 0, 1.0])
    r = np.cross(d, up); r /= np.linalg.norm(r)
    u = np.cross(r, d)
    return r, u, d


def render(items, path, elev, azim, tol=0.5, W=1800, H=1100, ss=2, margin=0.05, bg=(255, 255, 255), lims=None):
    r, u, d = cam(elev, azim)
    tris, cols = [], []
    for sh, rgb in items:
        v, f = mesh(sh, tol)
        t = v[f]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        nn = np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        n = n / nn
        # двусторонние грани: нормаль к камере
        flip = (n @ d) > 0
        n[flip] *= -1
        k = 0.32 + 0.52 * np.clip(n @ KEY, 0, 1) + 0.16 * np.clip(n @ FILL, 0, 1) + 0.08 * np.clip(n[:, 2], 0, 1)
        c = np.clip(np.outer(k, np.array(rgb)), 0, 1)
        tris.append(t); cols.append(c)
    T = np.vstack(tris); C = np.vstack(cols)
    # проекция
    P = np.stack([T @ r, T @ u, T @ d], axis=-1)  # x, y, depth
    if lims is not None:
        allp = P.reshape(-1, 3)
        keep = np.ones(len(T), bool)
        for i, (lo, hi) in enumerate(zip(lims[0], lims[1])):
            keep &= (T[:, :, i].max(1) >= lo) & (T[:, :, i].min(1) <= hi)
        P, C = P[keep], C[keep]
    xs, ys = P[:, :, 0], P[:, :, 1]
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = W * ss, H * ss
    sx = (w * (1 - 2 * margin)) / (x1 - x0); sy = (h * (1 - 2 * margin)) / (y1 - y0)
    s = min(sx, sy)
    ox = (w - s * (x1 - x0)) / 2; oy = (h - s * (y1 - y0)) / 2
    X = (xs - x0) * s + ox; Y = h - ((ys - y0) * s + oy); Z = P[:, :, 2]
    img = np.ones((h, w, 3)) * (np.array(bg) / 255.0)
    zb = np.full((h, w), np.inf)
    # растеризация: по порядку убывания размера bbox не нужно, z-буфер решает
    for i in range(len(X)):
        xa, ya = X[i], Y[i]
        bx0, bx1 = int(max(np.floor(xa.min()), 0)), int(min(np.ceil(xa.max()), w - 1))
        by0, by1 = int(max(np.floor(ya.min()), 0)), int(min(np.ceil(ya.max()), h - 1))
        if bx1 < bx0 or by1 < by0:
            continue
        gx, gy = np.meshgrid(np.arange(bx0, bx1 + 1) + 0.5, np.arange(by0, by1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = (xa[0], ya[0]), (xa[1], ya[1]), (xa[2], ya[2])
        det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(det) < 1e-9:
            continue
        l1 = ((bx - gx) * (cy - gy) - (cx - gx) * (by - gy)) / det
        l2 = ((cx - gx) * (ay - gy) - (ax - gx) * (cy - gy)) / det
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not inside.any():
            continue
        z = l1 * Z[i, 0] + l2 * Z[i, 1] + l3 * Z[i, 2]
        sub = zb[by0:by1 + 1, bx0:bx1 + 1]
        upd = inside & (z < sub)
        sub[upd] = z[upd]
        img[by0:by1 + 1, bx0:bx1 + 1][upd] = C[i]
    out = Image.fromarray((img * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    out.save(path)
    return out
