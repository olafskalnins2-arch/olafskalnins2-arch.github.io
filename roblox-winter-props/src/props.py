"""19 snowy props. Units: 1 = 1 stud. Run: python3 props.py"""
import math, sys, os
import numpy as np
from meshlib import *
from meshlib import _noise_fn

OUT = os.path.join(os.path.dirname(__file__), "..")
MAX_TRIS = 5000


def snow_strip(path, r, t0=0.1, t1=0.8, squash=0.55, lift=0.95, seg=8):
    n = len(path)
    a, b = int(t0 * (n - 1)), max(int(t1 * (n - 1)), int(t0 * (n - 1)) + 2)
    P = path[a:b + 1].copy()
    rr = r if np.isscalar(r) else np.asarray(r)[a:b + 1]
    rad = (lambda t: (rr if np.isscalar(rr) else np.interp(t, np.linspace(0, 1, len(rr)), rr)) * 1.2
           * (0.55 + 0.45 * math.sin(math.pi * t) ** 0.5))
    lifted = P + np.array([0, 1, 0]) * (np.asarray([rad(i / (len(P) - 1)) for i in range(len(P))])[:, None] * lift)
    return tube(lifted, rad, seg, squash=squash)


def snow_cap(rx, rz, th, pos, seed=0, drip=0.25, e2=0.35, rot=(0, 0, 0), nu=16, nv=8):
    nf = noise_cap = None
    import meshlib
    f = meshlib._noise_fn(seed)
    sag = lambda a: drip * max(0.0, f(np.array([math.cos(a) * 2, 0, math.sin(a) * 2]), 1.6)[0] + 0.25)
    return xf(superq(rx, th, rz, 0.55, e2, nu, nv, sag=sag, noise=0.04, seed=seed), r=rot, t=pos)


def rock(sx, sy, sz, pos, seed, rot=(0, 0, 0), nu=9, nv=6, e=0.5, noise=0.1):
    return xf(superq(sx / 2, sy / 2, sz / 2, e, e, nu, nv, noise=noise, seed=seed), r=rot, t=pos)


def log_x(m, length, r, pos, seed, seg=10, snow=True, rot=(0, 0, 0), stub=False):
    """Horizontal log along X centred at pos."""
    L = length / 2
    body = lathe([(r * 0.97, -L), (r, -L * 0.6), (r * 1.02, 0), (r, L * 0.6), (r * 0.97, L)], seg,
                 start=math.pi / seg, noise=0.035, seed=seed, nfreq=3)
    body = xf(uv_along(body, 1, -L, L, r), r=(0, 0, 90))
    parts = [(body, "bark_grain", 30)]
    for s in (1, -1):
        rc = r * 0.9
        cap = uv_cap(cyl(rc, 0.06, seg, start=math.pi / seg), 1, rc)
        cap = xf(cap, r=(0, 90 * (seed % 4), 0))          # vary ring/crack orientation per log
        cap = xf(cap, r=(0, 0, -90 * s), t=(s * (L - 0.015), 0, 0))
        parts.append((cap, "endgrain", 20))
    if stub:
        st = uv_along(cyl(r * 0.25, r * 1.1, 8), 1, 0, r * 1.1, r * 0.25)
        parts.append((xf(st, r=(-70, 0, 0), t=(L * 0.15, -r * 0.2, 0)), "bark_grain", 40))
        sc = uv_cap(cyl(r * 0.2, r * 1.1 + 0.03, 8), 1, r * 0.2)
        parts.append((xf(sc, r=(-70, 0, 0), t=(L * 0.15, -r * 0.2, 0)), "endgrain", 20))
    if snow:
        P = np.array([[-L * 0.95, r * 0.75, 0], [-L * 0.4, r * 0.82, 0], [0, r * 0.78, 0],
                      [L * 0.4, r * 0.84, 0], [L * 0.95, r * 0.76, 0]])
        P = catmull(P, 4)
        parts.append((tube(P, lambda t: r * (0.7 + 0.15 * math.sin(math.pi * t) ** 0.3), 12, squash=0.55), "snow", 60))
    for mesh, col, sm in parts:
        m.add(xf(mesh, r=rot, t=pos), col, sm)


# =================================================================== items
def tree():
    m = Model("SnowyBareTree")
    trunk = catmull([(0, 0, 0), (0.15, 4, 0), (-0.2, 8, 0), (0.1, 12, 0), (0.35, 16, 0.1)], 4)
    tr = lambda t: 0.32 + 0.95 * (1 - t) ** 1.3 + 0.55 * max(0, 1 - t * 7) ** 2
    m.add(tube(trunk, tr, 12), "bark", 50)
    branches = [
        ([(0, 6.3, 0), (-2.8, 7.3, 0.3), (-5.2, 8.6, 0.5), (-6.2, 11, 0.6), (-6.3, 13.3, 0.5)], 0.62, 0.26),
        ([(0, 6.9, 0), (2.4, 7.9, -0.3), (4.4, 9.8, -0.5), (5.6, 12.6, -0.6)], 0.55, 0.26),
        ([(4.6, 10.2, -0.5), (5.8, 10.1, -0.5), (6.8, 10.4, -0.5)], 0.24, 0.17),
        ([(0, 9.8, 0), (-1.5, 10.4, 0.9), (-2.9, 12.2, 1.1), (-3.4, 13.8, 1.1)], 0.42, 0.21),
        ([(0, 10.5, 0), (1.5, 11.1, -0.9), (2.6, 12.8, -1.0), (3.0, 14.3, -1.0)], 0.4, 0.21),
        ([(0, 8.4, 0), (0.5, 9.2, -2.0), (0.8, 11.4, -3.4), (1.0, 13.0, -3.7)], 0.45, 0.22),
        ([(0, 9.0, 0), (-0.3, 9.8, 2.1), (-0.5, 11.9, 3.3), (-0.6, 13.1, 3.5)], 0.42, 0.21),
    ]
    for i, (pts, r0, r1) in enumerate(branches):
        P = catmull(pts, 4)
        rf = lambda t, r0=r0, r1=r1: r0 + (r1 - r0) * t
        m.add(tube(P, rf, 8), "bark", 50)
        rr = [rf(k / (len(P) - 1)) for k in range(len(P))]
        lo, hi = (0.12, 0.7) if len(pts) > 3 else (0.0, 0.85)
        m.add(snow_strip(P, rr, lo, hi), "snow", 60)
    m.add(dome(3.6, 0.9, 3.2, 20, 4, noise=0.12, seed=3, e=0.6), "snow", 60)
    return m


def rock_pillar():
    m = Model("SnowyRockPillar")
    rocks = [((-0.9, 1.4, 0.1), (2.4, 2.8, 2.4)), ((1.3, 1.2, 0.2), (2.0, 2.4, 2.2)),
             ((-0.6, 3.9, 0.2), (3.6, 2.1, 2.7)), ((1.6, 3.6, -0.1), (2.0, 2.3, 2.1)),
             ((0.3, 5.9, 0.0), (2.9, 1.8, 2.5)), ((-1.8, 6.1, 0.1), (1.7, 1.4, 1.7)),
             ((1.9, 5.8, 0.2), (1.8, 1.6, 1.9)), ((0.4, 7.9, -0.1), (3.0, 1.8, 2.4))]
    for i, (c, s) in enumerate(rocks):
        m.add(rock(*s, c, seed=10 + i, e=0.35, noise=0.06, nu=10, nv=6), "rock", 25)
    for i in (2, 5, 6, 7, 1, 3):
        c, s = rocks[i]
        m.add(snow_cap(s[0] / 2 * 1.06, s[2] / 2 * 1.06, 0.32, (c[0], c[1] + s[1] / 2, c[2]), seed=i, drip=0.18), "snow", 60)
    m.add(dome(3.2, 1.0, 2.6, 22, 4, noise=0.15, hnoise=0.3, seed=5, e=0.7), "snow", 60)
    for i, (x, z) in enumerate([(-2.3, 1.2), (2.4, 0.9), (0.4, 2.0), (-1.8, -1.6)]):
        m.add(xf(dome(1.1, 0.8, 1.0, 12, 3, noise=0.1, seed=30 + i), t=(x, 0, z)), "snow", 60)
    return m


def stepping_path():
    m = Model("SnowSteppingStones")
    f = _noise_fn(4)
    slab = superq(3.2, 0.35, 8.0, 0.4, 0.6, 24, 6, noise=0.05, seed=4)
    V, F = slab
    V = V.copy(); V[:, 1] += 0.35
    m.add((V, F), "snow", 50)
    stones = [(-0.3, 5.6, 2.4, 1.5), (0.2, 3.1, 2.6, 1.6), (-0.2, 0.4, 2.8, 1.7), (0.3, -2.4, 3.0, 1.9), (0, -5.4, 3.4, 2.2)]
    for i, (x, z, w, d) in enumerate(stones):
        m.add(xf(superq(w / 2, 0.22, d / 2, 0.5, 0.45, 14, 4, noise=0.05, seed=40 + i), t=(x, 0.72, z)), "stone", 50)
        for s in (-1, 1):
            if (i + (s > 0)) % 2 == 0:
                m.add(xf(sphere(0.32, 8, 5, noise=0.2, seed=i), s=(1, 0.7, 1), t=(x + s * (w / 2 + 0.1), 0.75, z + 0.3 * s)), "snow", 70)
    return m


def icicle_ledge():
    m = Model("IcicleLedge")
    m.add(rbox(10, 1.2, 2.2, e=0.25, nu=20, nv=8, noise=0.02, seed=1), "snow", 50)
    rng = np.random.default_rng(7)
    xs = np.linspace(-4.3, 4.3, 10)
    for i, x in enumerate(xs):
        L = rng.uniform(1.4, 3.4)
        r = rng.uniform(0.28, 0.38)
        z = rng.uniform(-0.3, 0.3)
        prof = [(0.0, -L), (r * 0.35, -L + 0.12), (r * 0.6, -L * 0.6), (r * 0.85, -L * 0.25), (r, 0), (r, 0.3)]
        m.add(xf(lathe(prof, 8), t=(x + rng.uniform(-0.15, 0.15), -0.45, z)), "ice", 60)
    return m


def log():
    m = Model("SnowyLog")
    log_x(m, 9, 1.35, (0, 1.35, 0), seed=2, seg=11, stub=True)
    return m


def sled():
    m = Model("WoodenSled")
    for z in (-1.2, 1.2):
        run = catmull([(4.2, 0.18, z), (-2.5, 0.18, z), (-3.6, 0.35, z), (-4.1, 1.1, z), (-3.8, 2.0, z), (-3.2, 2.1, z)], 4)
        m.add(tube(run, 0.2, 6), "wood", 45)
        for x in (-1.6, 2.6):
            m.add(xf(box(0.4, 1.4, 0.35), t=(x, 0.95, z)), "wood", 20)
    for x in (-1.6, 2.6):
        m.add(xf(box(0.45, 0.3, 2.9), t=(x, 1.5, 0)), "wood", 20)
    for i, z in enumerate((-1.05, -0.35, 0.35, 1.05)):
        m.add(xf(rbox(6.2, 0.28, 0.62, e=0.2, nu=12, nv=4), t=(0.5, 1.78, z)), "wood", 35)
    m.add(xf(dome(1.5, 0.7, 1.15, 14, 4, noise=0.1, seed=2, e=0.5), t=(1.0, 1.9, 0)), "snow", 60)
    rope = catmull([(-3.2, 2.0, -1.2), (-3.5, 1.4, -0.7), (-3.9, 1.1, 0), (-3.5, 1.4, 0.7), (-3.2, 2.0, 1.2)], 4)
    m.add(tube(rope, 0.07, 5), "rope", 60)
    tail = catmull([(-3.9, 1.1, 0), (-4.5, 0.5, 0.2), (-5.2, 0.12, -0.3), (-5.8, 0.1, 0.4), (-6.0, 0.1, 1.0)], 4)
    m.add(tube(tail, 0.07, 5), "rope", 60)
    m.add(xf(sphere(0.16, 6, 4), t=(-3.9, 1.1, 0)), "rope", 60)
    return m


def frozen_pond():
    m = Model("FrozenPond")
    f = _noise_fn(9)
    loop = []
    for k in range(28):
        a = 2 * math.pi * k / 28
        rr = 1 + 0.06 * f(np.array([math.cos(a), 0, math.sin(a)]), 2.0)[0]
        loop.append([7.0 * rr * math.cos(a), 0.35, 5.0 * rr * math.sin(a)])
    m.add(tube(np.array(loop), 0.75, 8, closed=True, squash=0.6), "snow", 60)
    ice = []
    for k in range(28):
        ice.append((loop[k][0], loop[k][2]))
    V, F = superq(6.6, 0.18, 4.6, 0.5, 1.0, 28, 4)
    V = V.copy(); V[:, 1] += 0.18
    m.add((V, F), "pond", 30)
    for (x, z, ang, L) in [(-2.5, -1.2, 15, 2.2), (-1.2, -1.0, -25, 1.4), (2.6, 1.5, -10, 2.0), (3.6, 1.0, 50, 1.0), (-1.0, 2.0, 40, 1.2)]:
        m.add(xf(box(L, 0.04, 0.07), r=(0, ang, 0), t=(x, 0.37, z)), "white", 0)
    # cattails cluster
    cx, cz = 4.8, 3.6
    m.add(xf(dome(1.4, 0.45, 1.0, 12, 3, noise=0.1, seed=3), t=(cx, 0.2, cz)), "snow", 60)
    for i, (dx, dz, h, lean) in enumerate([(0, 0, 3.0, -6), (0.45, 0.2, 3.5, 4), (-0.4, 0.15, 2.6, -12)]):
        stem = xf(cyl(0.06, h, 6), r=(0, 0, lean), t=(cx + dx, 0.3, cz + dz))
        m.add(stem, "reed", 60)
        top = rotm(0, 0, lean) @ np.array([0, h, 0]) + np.array([cx + dx, 0.3, cz + dz])
        m.add(xf(superq(0.19, 0.55, 0.19, 0.7, 1, 8, 6), r=(0, 0, lean), t=top - rotm(0, 0, lean) @ np.array([0, 0.45, 0])), "cattail", 60)
        m.add(xf(cyl(0.03, 0.4, 4), r=(0, 0, lean), t=top), "reed", 60)
    for i, (dx, dz, h, a) in enumerate([(0.2, -0.2, 1.8, 20), (-0.3, -0.1, 1.5, -25), (0.1, 0.35, 1.6, 10)]):
        leaf = catmull([(0, 0, 0), (0.05 * a / 10, h * 0.6, 0), (0.12 * a / 10, h, 0)], 3)
        m.add(xf(tube(leaf, lambda t: 0.13 * (1 - t) + 0.01, 4, squash=1.0), s=(1, 1, 0.35), r=(0, 30 * i, 0), t=(cx + dx, 0.3, cz + dz)), "reed", 50)
    for i, (dx, dz, s) in enumerate([(-0.8, -0.4, 0.45), (0.8, -0.5, 0.35)]):
        m.add(rock(s * 2, s * 1.4, s * 1.8, (cx + dx, 0.45, cz + dz), seed=60 + i, nu=7, nv=5), "rock", 30)
    return m


def shovel():
    m = Model("SnowShovel")
    m.add(dome(2.6, 1.3, 2.2, 20, 5, noise=0.14, hnoise=0.2, seed=8, e=0.7), "snow", 60)
    parts = []
    # blade (local: blade bottom at y=0, facing +z), tilted later
    parts.append((xf(box(2.6, 2.4, 0.12), t=(0, 1.2, 0)), "shovel_blue", 20))
    for s in (-1, 1):
        parts.append((xf(box(0.12, 2.4, 0.7), t=(s * 1.26, 1.2, 0.35)), "shovel_blue", 20))
    parts.append((xf(box(2.6, 0.12, 0.7), t=(0, 0.06, 0.35)), "shovel_blue", 20))
    parts.append((xf(rbox(0.35, 2.2, 0.3, e=0.4, nu=8, nv=6), t=(0, 1.4, 0.1)), "shovel_blue", 40))
    parts.append((xf(cyl(0.28, 0.9, 10, r2=0.2), t=(0, 2.2, 0)), "shovel_blue", 40))
    parts.append((xf(cyl(0.17, 5.6, 10), t=(0, 2.9, 0)), "wood", 40))
    parts.append((xf(cyl(0.24, 0.7, 10), t=(0, 8.3, 0)), "handle", 40))
    D = catmull([(-0.15, 8.9, 0), (-0.75, 9.2, 0), (-0.85, 10.1, 0), (0, 10.25, 0), (0.85, 10.1, 0), (0.75, 9.2, 0), (0.15, 8.9, 0)], 3)
    parts.append((tube(D, 0.18, 8), "handle", 50))
    for mesh, col, sm in parts:
        m.add(xf(mesh, r=(-12, 15, 4), t=(0, 0.2, 0)), col, sm)
    return m


def birdhouse():
    m = Model("SnowyBirdhouse")
    m.add(cyl(0.45, 6.2, 12), "post", 40)
    m.add(xf(box(4.4, 0.35, 3.6), t=(0, 6.2, 0)), "bird_blue", 0)
    W, H, D = 3.4, 2.8, 2.8
    house = [(-W / 2, 0), (W / 2, 0), (W / 2, H), (0, H + 1.3), (-W / 2, H)]
    body = prism(house, D, axis="x")
    m.add(xf(body, r=(0, 90, 0), t=(0, 6.37, 0)), "bird_blue", 0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.add(xf(box(0.22, H, 0.22), t=(sx * (W / 2 + 0.02), 6.37 + H / 2, sz * (D / 2 + 0.02))), "white", 0)
    # roof slabs
    rl = math.hypot(W / 2, 1.3) + 0.6
    ang = math.degrees(math.atan2(1.3, W / 2))
    for s in (-1, 1):
        m.add(xf(box(rl, 0.25, D + 0.8), r=(0, 0, -s * ang), t=(s * (W / 4 + 0.15), 6.37 + H + 0.75, 0)), "bird_blue", 0)
    # snow on roof
    for s in (-1, 1):
        cap = snow_cap(rl / 2 + 0.05, (D + 1.1) / 2, 0.45, (0, 0, 0), seed=3 + s, drip=0.35, e2=0.25)
        m.add(xf(cap, r=(0, 0, -s * ang), t=(s * (W / 4 + 0.05), 6.37 + H + 1.25, 0)), "snow", 60)
    m.add(xf(sphere(0.8, 12, 6), s=(1.3, 0.55, 1.6), t=(0, 6.37 + H + 1.75, 0)), "snow", 60)
    # hole + perch on front (+z)
    fz = D / 2 + 0.01
    m.add(xf(cyl(0.5, 0.05, 14), r=(90, 0, 0), t=(0, 6.37 + 1.9, fz + 0.05)), "hole", 30)
    m.add(xf(torus(0.55, 0.1, 14, 6), r=(90, 0, 0), t=(0, 6.37 + 1.9, fz + 0.05)), "bird_blue", 50)
    m.add(xf(cyl(0.09, 0.6, 8), r=(90, 0, 0), t=(0, 6.37 + 1.0, fz + 0.6)), "pink", 40)
    m.add(xf(dome(0.9, 0.3, 0.6, 10, 3, seed=2), t=(1.3, 6.37, 1.3)), "snow", 60)
    return m


def lamp_post():
    m = Model("SnowyLampPost")
    m.add(xf(torus(1.25, 0.42, 20, 8, squash=0.75), t=(0, 0.32, 0)), "snow", 60)
    m.add(lathe([(1.05, 0), (1.0, 0.4), (0.75, 0.6), (0.55, 2.2), (0.6, 2.4), (0.6, 2.55), (0.32, 2.7)], 14), "lamp_green", 40)
    m.add(xf(cyl(0.3, 5.6, 12), t=(0, 2.6, 0)), "lamp_green", 40)
    m.add(xf(cyl(0.42, 0.3, 12), t=(0, 7.9, 0)), "lamp_green", 40)
    y0 = 8.2
    m.add(xf(lathe([(0.75, 0), (0.75, 0.2)], 4, start=math.pi / 4), t=(0, y0, 0)), "gold", 0)
    m.add(xf(lathe([(0.78, 0.2), (1.25, 2.0)], 4, start=math.pi / 4), t=(0, y0, 0)), "glass", 0, node="Glass")
    # frame corners + mid bars
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p0 = np.array([0.8 * math.cos(a), y0 + 0.2, 0.8 * math.sin(a)])
        p1 = np.array([1.29 * math.cos(a), y0 + 2.0, 1.29 * math.sin(a)])
        m.add(tube([p0, p1], 0.08, 5), "gold", 50)
    m.add(xf(lathe([(1.3, 0), (1.3, 0.2)], 4, start=math.pi / 4), t=(0, y0 + 2.0, 0)), "gold", 0)
    for k in range(4):
        a = k * math.pi / 2
        for frac in (0.5,):
            n = np.array([math.cos(a), 0, math.sin(a)])
            yb, yt = y0 + 0.2, y0 + 2.0
            p0 = n * (0.55 + 0.02) + np.array([0, yb, 0])
            p1 = n * (0.88 + 0.03) + np.array([0, yt, 0])
            m.add(tube([p0 + n * 0.02, p1 + n * 0.02], 0.05, 4), "gold", 50)
        mid = y0 + 1.1
        rr = (0.55 + 0.88) / 2 + 0.05
        t = np.array([-math.sin(a), 0, math.cos(a)])
        m.add(tube([n * rr - t * 0.85 + [0, mid, 0], n * rr + t * 0.85 + [0, mid, 0]], 0.05, 4), "gold", 50)
    m.add(xf(lathe([(1.55, 0), (1.55, 0.3), (0.5, 0.75), (0.0, 0.8)], 4, start=math.pi / 4), t=(0, y0 + 2.2, 0)), "lamp_green", 0)
    m.add(xf(snow_cap(1.15, 1.15, 0.65, (0, 0, 0), seed=4, drip=0.2, e2=0.6), t=(0, y0 + 3.05, 0)), "snow", 60)
    return m


def snowman():
    m = Model("Snowman")
    m.add(xf(sphere(2.6, 20, 12, yclip=-2.3), t=(0, 2.3, 0)), "snow", 60)
    m.add(xf(sphere(1.85, 18, 10), t=(0, 5.9, 0)), "snow", 60)
    m.add(xf(sphere(1.4, 18, 10), t=(0, 8.65, 0)), "snow", 60)
    m.add(xf(dome(1.38, 1.55, 1.38, 18, 5, e=0.9), t=(0, 9.35, 0)), "coral", 60)
    m.add(xf(torus(1.38, 0.35, 20, 8), t=(0, 9.45, 0)), "coral", 60)
    m.add(xf(sphere(0.32, 10, 6), t=(0, 10.95, 0)), "coral", 60)
    m.add(xf(torus(1.42, 0.38, 20, 8, squash=1.1), t=(0, 7.55, 0)), "pink", 60)
    m.add(xf(rbox(0.55, 2.0, 0.22, e=0.4, nu=8, nv=6), r=(-12, 0, 8), t=(0.95, 6.5, 1.55)), "pink", 50)
    for s in (-1, 1):
        m.add(xf(sphere(0.15, 8, 5), t=(s * 0.48, 8.95, 1.3)), "black", 60)
    m.add(xf(lathe([(0.17, 0), (0.0, 0.85)], 8), r=(90, 0, 0), t=(0, 8.6, 1.3)), "carrot", 50)
    for k in range(5):
        a = math.radians(-50 + k * 25)
        m.add(xf(sphere(0.085, 6, 4), t=(0.55 * math.sin(a), 8.25 - 0.17 * math.cos(a) + 0.0, 1.25)), "black", 60)
    for y in (6.4, 5.7, 5.0):
        m.add(xf(sphere(0.13, 8, 5), t=(0, y, math.sqrt(max(0, 1.85 ** 2 - (y - 5.9) ** 2)) - 0.03)), "black", 60)
    for s in (-1, 1):
        arm = [(s * 1.6, 6.4, 0), (s * 3.0, 7.0, 0), (s * 3.9, 7.7, 0)]
        m.add(tube(arm, lambda t: 0.16 - 0.06 * t, 6), "bark", 50)
        m.add(tube([(s * 3.0, 7.0, 0), (s * 3.3, 7.9, 0)], 0.09, 5), "bark", 50)
        m.add(tube([(s * 3.6, 7.45, 0), (s * 4.3, 7.4, 0)], 0.08, 5), "bark", 50)
    return m


def dirt_path():
    m = Model("SnowyDirtPath")
    m.add(xf(rbox(8, 0.9, 8, e=0.18, nu=16, nv=6, noise=0.01, seed=1), t=(0, 0.45, 0)), "dirt", 35)
    for s in (-1, 1):
        P = catmull([(s * 2.6, 0.95, -3.9), (s * 2.7, 1.0, -1.5), (s * 2.55, 1.0, 1.0), (s * 2.7, 0.95, 3.9)], 4)
        m.add(tube(P, lambda t: 1.25 + 0.15 * math.sin(t * 9), 10, squash=0.6), "snow", 60)
    rng = np.random.default_rng(3)
    for i in range(14):
        x, z, r = rng.uniform(-1.3, 1.3), rng.uniform(-3.5, 3.5), rng.uniform(0.08, 0.22)
        m.add(xf(sphere(r, 7, 4), s=(1.2, 0.5, 1), t=(x, 0.92, z)), "pebble", 60)
    return m


def stump_axe():
    m = Model("StumpWithAxe")
    m.add(uv_along(lathe([(2.4, 0), (2.05, 0.6), (1.85, 1.6), (1.8, 2.9), (1.75, 3.0)], 16, noise=0.04, seed=3, nfreq=4),
                   1, 0, 3.0, 2.0), "bark_grain", 30)
    m.add(xf(uv_cap(cyl(1.76, 0.08, 20), 1, 1.76), t=(0, 3.0, 0)), "endgrain", 10)
    # axe: head buried in the top
    axe = []
    axe.append((xf(box(1.5, 1.3, 0.35), t=(0, 0, 0)), "metal"))
    axe.append((xf(box(0.6, 1.0, 0.45), t=(0.95, 0.15, 0)), "metal"))
    axe.append((xf(cyl(0.17, 5.0, 10), r=(0, 0, -90), t=(0.9, 0.3, 0)), "axe_red"))
    axe.append((xf(sphere(0.22, 8, 5), s=(0.8, 1, 1), t=(5.85, 0.3, 0)), "axe_red"))
    for mesh, col in axe:
        m.add(xf(mesh, r=(0, 30, 28), t=(-0.2, 3.4, 0.0)), col, 30)
    for i, (x, z, a) in enumerate([(1.2, 2.0, 12), (1.9, 1.5, -10)]):
        pc = uv_along(prism([(-0.35, 0), (0.35, 0), (0.2, 2.0), (-0.3, 1.9)], 0.5, axis="z"), 1, 0, 2.0, 0.4)
        m.add(xf(pc, r=(-14, 25 + 10 * i, a), t=(x, 0.1, z)), "split_grain", 0)
    for i, (x, z, r) in enumerate([(-2.0, 0.8, 1.2), (1.8, -1.2, 1.3), (0.2, 2.3, 1.0), (-1.2, -2.0, 1.1)]):
        m.add(xf(dome(r, 0.75, r * 0.8, 12, 3, noise=0.12, seed=20 + i, e=0.6), t=(x, 0, z)), "snow", 60)
    return m


def log_pile():
    m = Model("SnowyLogPile")
    r = 1.05
    pos = [(-2.1, r), (0, r), (2.1, r), (-1.05, r + 1.8), (1.05, r + 1.8), (0, r + 3.6)]
    for i, (z, y) in enumerate(pos):
        log_x(m, 6.5, r, (z, y, 0), seed=50 + i, seg=10, snow=(i == 5), rot=(0, 90, 0))
    return m


def rock_pile():
    m = Model("SnowyRockPile")
    rocks = [((-1.6, 1.3, 0.2), (2.6, 2.6, 2.4)), ((1.7, 1.1, -0.3), (2.8, 2.2, 2.6)),
             ((0.0, 3.1, 0.0), (2.6, 2.4, 2.4)), ((0.9, 2.3, 1.3), (2.0, 1.9, 1.8)),
             ((-0.5, 0.8, 1.8), (1.8, 1.6, 1.6))]
    for i, (c, s) in enumerate(rocks):
        m.add(rock(*s, c, seed=70 + i, e=0.55, noise=0.08, nu=9, nv=7), "rock", 30)
        m.add(snow_cap(s[0] * 0.33, s[2] * 0.33, 0.28, (c[0], c[1] + s[1] * 0.46, c[2]), seed=i, drip=0.15, e2=0.7, nu=12, nv=6), "snow", 60)
    return m


def mailbox():
    m = Model("SnowyMailbox")
    m.add(xf(box(0.75, 4.2, 0.75), t=(0, 2.1, 0)), "post", 0)
    W, Hb = 2.2, 1.3
    prof = [(-W / 2, 0), (W / 2, 0)] + [(W / 2 * math.cos(a), Hb + W / 2 * math.sin(a)) for a in np.linspace(0, math.pi, 11)][::1]
    prof = [(-W / 2, 0), (W / 2, 0)] + [(W / 2 * math.cos(a), Hb + W / 2 * math.sin(a)) for a in np.linspace(0, math.pi, 11)]
    body = prism(prof, 3.6, axis="x")
    m.add(xf(body, t=(0, 4.2, 0)), "mint", 35)
    door = [(u * 1.06, v * 1.04 - 0.04) for u, v in prof]
    m.add(xf(prism(door, 0.18, axis="x"), t=(1.85, 4.2, 0)), "mint", 35)
    inner = [(u * 0.8, v * 0.82 + 0.15) for u, v in prof]
    m.add(xf(prism(inner, 0.08, axis="x"), t=(1.97, 4.2, 0)), "mint", 35)
    m.add(xf(rbox(0.18, 0.35, 0.22, e=0.4, nu=6, nv=4), t=(2.0, 5.35, 0.75)), "mint", 40)
    # flag on +z side
    m.add(xf(box(0.15, 1.5, 0.12), t=(0.5, 5.4, W / 2 + 0.12)), "pink", 0)
    m.add(xf(box(0.9, 0.55, 0.12), t=(0.82, 5.95, W / 2 + 0.12)), "pink", 0)
    m.add(xf(cyl(0.25, 0.14, 12), r=(90, 0, 0), t=(0.5, 4.75, W / 2 + 0.17)), "pink", 30)
    m.add(xf(snow_cap(1.8, 1.0, 0.55, (0, 0, 0), seed=6, drip=0.25, e2=0.45), t=(-0.1, 4.2 + Hb + W / 2 + 0.25, 0)), "snow", 60)
    return m


def snow_drift():
    m = Model("SnowDrift")
    nu, nv = 26, 7
    f = _noise_fn(12)
    V, rows = [], []
    for i in range(nv + 1):
        rr = 1 - i / nv
        row = []
        for j in range(nu):
            a = 2 * math.pi * j / nu
            x, z = 4.6 * rr * math.cos(a), 3.0 * rr * math.sin(a)
            base = 1 - rr ** 2.2
            ridge = 0.25 * math.sin(x * 1.6 + z * 0.6)
            y = 1.25 * base * (1 + ridge) * (1 + 0.25 * x / 4.6) if i else 0.0
            row.append(len(V)); V.append([x, y, z])
        rows.append(row)
    V.append([0, 0, 0]); bot = len(V) - 1
    F = []
    F += [[bot, rows[0][(j + 1) % nu], rows[0][j]] for j in range(nu)]
    for i in range(nv):
        for j in range(nu):
            a, b = rows[i][j], rows[i][(j + 1) % nu]
            c, d = rows[i + 1][(j + 1) % nu], rows[i + 1][j]
            if i == nv - 1:
                F.append([a, b, c])
            else:
                F += [[a, b, c], [a, c, d]]
    m.add(orient(V, F), "ice", 55)
    curl = catmull([(2.4, 1.2, -0.4), (3.4, 1.9, -0.2), (4.1, 2.0, 0.0), (4.3, 1.6, 0.1), (4.0, 1.4, 0.2)], 4)
    m.add(tube(curl, lambda t: 0.55 * (1 - t) + 0.35, 10, squash=0.75), "ice", 60)
    return m


def log_fence():
    m = Model("SnowyLogFence")
    for x in (-4.3, 4.3):
        m.add(xf(uv_along(lathe([(0.62, 0), (0.6, 2.5), (0.56, 5.4)], 12, noise=0.03, seed=int(x)), 1, 0, 5.4, 0.6), t=(x, 0, 0)), "wood_grain", 35)
        m.add(xf(uv_cap(cyl(0.54, 5.44, 12), 1, 0.54), t=(x, 0, 0)), "endgrain", 10)
        m.add(xf(snow_cap(0.6, 0.6, 0.22, (0, 0, 0), seed=2, drip=0.08, e2=1.0, nu=12, nv=6), t=(x, 5.45, 0)), "snow", 60)
    for y in (1.8, 4.0):
        L = 11.2
        rail = uv_along(lathe([(0.42, -L / 2), (0.45, 0), (0.42, L / 2)], 8, start=math.pi / 8, noise=0.03, seed=int(y * 3)), 1, -L / 2, L / 2, 0.45)
        m.add(xf(rail, r=(0, 0, 90), t=(0, y, 0.55)), "wood_grain", 35)
        for s in (-1, 1):
            m.add(xf(uv_cap(cyl(0.38, 0.05, 8, start=math.pi / 8), 1, 0.38), r=(0, 0, -90 * s), t=(s * L / 2, y, 0.55)), "endgrain", 10)
            m.add(xf(dome(0.25, 0.18, 0.25, 8, 2), t=(s * 5.2, y + 0.38, 0.55)), "snow", 60)
        P = catmull([(-3.7, y + 0.33, 0.55), (-1.5, y + 0.4, 0.55), (1.5, y + 0.36, 0.55), (3.7, y + 0.33, 0.55)], 4)
        m.add(tube(P, lambda t: 0.33 * (0.6 + 0.4 * math.sin(math.pi * t) ** 0.3), 10, squash=0.45), "snow", 60)
    return m


def boulder():
    m = Model("SnowyBoulder")
    m.add(xf(superq(3.0, 2.3, 2.7, 0.75, 0.75, 14, 9, noise=0.06, seed=91, yclip=-1.9), t=(0, 1.9, 0)), "rock", 32)
    m.add(snow_cap(2.85, 2.55, 0.85, (0, 3.75, 0), seed=5, drip=0.55, e2=0.8, nu=20, nv=10), "snow", 60)
    for i, (x, z, r) in enumerate([(-2.6, 1.6, 0.5), (-1.9, 2.3, 0.4), (2.5, 1.7, 0.42), (2.9, -0.5, 0.35), (-2.9, -0.8, 0.38), (0.9, 2.7, 0.3)]):
        m.add(rock(r * 2, r * 1.3, r * 1.7, (x, r * 0.55, z), seed=100 + i, nu=7, nv=5, e=0.8), "pebble" if i % 2 else "rock", 40)
    return m


ITEMS = [tree, rock_pillar, stepping_path, icicle_ledge, log, sled, frozen_pond, shovel, birdhouse,
         lamp_post, snowman, dirt_path, stump_axe, log_pile, rock_pile, mailbox, snow_drift, log_fence, boulder]

if __name__ == "__main__":
    only = sys.argv[1:]
    rows = []
    for fn in ITEMS:
        if only and fn.__name__ not in only:
            continue
        mdl = fn()
        t, size = export(mdl, OUT)
        flag = "OK" if t <= MAX_TRIS else "OVER!"
        rows.append((mdl.name, t, size))
        print(f"{mdl.name:22s} {t:5d} tris  size {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} studs  {flag}")
