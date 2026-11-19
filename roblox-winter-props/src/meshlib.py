"""Tiny procedural mesh toolkit -> palette-textured GLB + OBJ for Roblox."""
import math, struct, json, zlib, os
import numpy as np

# ---------------------------------------------------------------- palette
PAL = {
    "snow": "#F3F6F9", "snow_shade": "#E3EAF1", "ice": "#C9E2EE", "pond": "#A8CBE0",
    "bark": "#A9673C", "wood": "#C38A52", "wood_end": "#F0DEC0", "ring": "#5E4E42",
    "rock": "#8E9DAA", "stone": "#A9AFBA", "lamp_green": "#3E6A4B", "gold": "#CDAA5E",
    "glass": "#FFE7AE", "pink": "#E8868B", "coral": "#EC8A80", "black": "#222428",
    "carrot": "#F0883A", "shovel_blue": "#4B8FDD", "handle": "#8A5A3A", "bird_blue": "#A8B9E4",
    "mint": "#A9DCC6", "axe_red": "#D9504A", "metal": "#9C9EA2", "cattail": "#9A5B3C",
    "reed": "#AEBD92", "dirt": "#A97A52", "rope": "#EEE2C2", "hole": "#1F2B45",
    "pebble": "#8F8F92", "white": "#FFFFFF", "split_wood": "#D8B482", "post": "#B97E4A",
}
KEYS = list(PAL)
PAL_COLS, SW = 8, 16
PAL_ROWS = (len(KEYS) + PAL_COLS - 1) // PAL_COLS


def uv_of(key):
    k = KEYS.index(key)
    c, r = k % PAL_COLS, k // PAL_COLS
    return ((c + 0.5) / PAL_COLS, (r + 0.5) / PAL_ROWS)


def palette_png():
    w, h = PAL_COLS * SW, PAL_ROWS * SW
    img = np.zeros((h, w, 3), np.uint8)
    for k, key in enumerate(KEYS):
        c, r = k % PAL_COLS, k // PAL_COLS
        hx = PAL[key].lstrip("#")
        img[r * SW:(r + 1) * SW, c * SW:(c + 1) * SW] = [int(hx[i:i + 2], 16) for i in (0, 2, 4)]
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- helpers
def _noise_fn(seed, n=7):
    rng = np.random.default_rng(abs(int(seed)))
    dirs = rng.normal(size=(n, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    ph = rng.uniform(0, 2 * math.pi, n)
    amp = rng.uniform(0.5, 1.0, n)

    def f(p, freq=1.0):
        p = np.atleast_2d(p)
        return (np.sin(freq * p @ dirs.T + ph) * amp).sum(1) / amp.sum()
    return f


def orient(V, F):
    V, F = np.asarray(V, float), np.asarray(F, int)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)).sum()
    if vol < 0:
        F = F[:, ::-1].copy()
    return V, F


def merge(*meshes):
    Vs, Fs, off = [], [], 0
    for V, F in meshes:
        Vs.append(V); Fs.append(F + off); off += len(V)
    return np.vstack(Vs), np.vstack(Fs)


def rotm(rx=0, ry=0, rz=0):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def xf(m, s=1.0, r=(0, 0, 0), t=(0, 0, 0)):
    V, F = m
    V = V * np.asarray(s, float)
    V = V @ rotm(*r).T + np.asarray(t, float)
    det = np.prod(np.broadcast_to(np.asarray(s, float), 3))
    if det < 0:
        F = F[:, ::-1]
    return V, F


def _fan(center_idx, ring, flip=False):
    n = len(ring)
    return [[center_idx, ring[j], ring[(j + 1) % n]] if not flip else
            [center_idx, ring[(j + 1) % n], ring[j]] for j in range(n)]


def _grid(rows, nu, closed=True):
    F = []
    for i in range(len(rows) - 1):
        for j in range(nu if closed else nu - 1):
            a, b = rows[i][j], rows[i][(j + 1) % nu]
            c, d = rows[i + 1][(j + 1) % nu], rows[i + 1][j]
            F += [[a, b, c], [a, c, d]]
    return F


# ---------------------------------------------------------------- primitives
def lathe(prof, seg=16, start=0.0, noise=0.0, seed=0, nfreq=1.0):
    """prof: list of (r, y) bottom->top. Closed with caps."""
    nf = _noise_fn(seed)
    V, rows = [], []
    for r, y in prof:
        row = []
        for j in range(seg):
            a = start + 2 * math.pi * j / seg
            rr = r
            if noise and r > 1e-6:
                rr = r * (1 + noise * nf(np.array([math.cos(a), y * 0.3, math.sin(a)]), nfreq)[0])
            row.append(len(V)); V.append([rr * math.cos(a), y, rr * math.sin(a)])
        rows.append(row)
    F = _grid(rows, seg)
    if prof[0][0] > 1e-6:
        V.append([0, prof[0][1], 0]); F += _fan(len(V) - 1, rows[0])
    if prof[-1][0] > 1e-6:
        V.append([0, prof[-1][1], 0]); F += _fan(len(V) - 1, rows[-1])
    return orient(V, F)


def cyl(r, h, seg=12, r2=None, start=0.0):
    return lathe([(r, 0), (r if r2 is None else r2, h)], seg, start)


def superq(rx, ry, rz, e1=1.0, e2=1.0, nu=16, nv=8, noise=0.0, seed=0, nfreq=1.5,
           yclip=None, sag=None):
    """Superellipsoid centred at origin. noise = radial displacement fraction."""
    nf = _noise_fn(seed)

    def sc(w, m):
        c, s = math.cos(w), math.sin(w)
        return math.copysign(abs(c) ** m, c), math.copysign(abs(s) ** m, s)
    V, rows = [], []
    for i in range(1, nv):
        th = -math.pi / 2 + math.pi * i / nv
        ct, st = sc(th, e1)
        row = []
        for j in range(nu):
            ph = -math.pi + 2 * math.pi * j / nu
            cp, sp = sc(ph, e2)
            p = np.array([rx * ct * cp, ry * st, rz * ct * sp])
            row.append(len(V)); V.append(p)
        rows.append(row)
    V.append(np.array([0, -ry, 0.])); bot = len(V) - 1
    V.append(np.array([0, ry, 0.])); top = len(V) - 1
    V = np.array(V)
    if noise:
        d = V / np.array([rx, ry, rz])
        V = V * (1 + noise * nf(d, nfreq))[:, None]
    if sag is not None:          # drip function on lower half: sag(angle)->amount
        for k, p in enumerate(V):
            if p[1] < 0:
                a = math.atan2(p[2] / rz, p[0] / rx)
                w = min(1.0, -p[1] / ry)
                V[k, 1] -= sag(a) * w
    if yclip is not None:
        V[:, 1] = np.maximum(V[:, 1], yclip)
    F = _grid(rows, nu) + _fan(bot, rows[0], True) + _fan(top, rows[-1])
    return orient(V, F)


def sphere(r, nu=14, nv=8, **kw):
    return superq(r, r, r, 1, 1, nu, nv, **kw)


def dome(rx, h, rz, nu=18, nv=5, noise=0.0, hnoise=0.0, seed=0, e=1.0, power=1.0):
    """Half-dome sitting on y=0 (closed bottom). noise wobbles the footprint."""
    nf = _noise_fn(seed)
    V, rows = [], []
    for i in range(nv):
        th = (math.pi / 2) * i / nv
        row = []
        for j in range(nu):
            a = 2 * math.pi * j / nu
            k = 1 + noise * nf(np.array([math.cos(a), 0, math.sin(a)]), 1.7)[0]
            c = abs(math.cos(th)) ** e
            y = h * math.sin(th) ** power
            y *= 1 + hnoise * nf(np.array([math.cos(a) * 2, 1.3, math.sin(a) * 2]), 2.3)[0] if i else 0
            row.append(len(V)); V.append([rx * k * c * math.cos(a), y, rz * k * c * math.sin(a)])
        rows.append(row)
    V.append([0, h, 0]); top = len(V) - 1
    V.append([0, 0, 0]); bot = len(V) - 1
    F = _grid(rows, nu) + _fan(top, rows[-1]) + _fan(bot, rows[0], True)
    return orient(V, F)


def box(sx, sy, sz):
    x, y, z = sx / 2, sy / 2, sz / 2
    V = [[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z], [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]]
    F = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4], [3, 6, 2], [3, 7, 6],
         [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5]]
    return orient(V, F)


def rbox(sx, sy, sz, e=0.25, nu=16, nv=8, **kw):
    return superq(sx / 2, sy / 2, sz / 2, e, e, nu, nv, **kw)


def torus(R, r, nu=20, nv=8, sx=1.0, sz=1.0, squash=1.0):
    V, rows = [], []
    for i in range(nv):
        b = 2 * math.pi * i / nv
        row = []
        for j in range(nu):
            a = 2 * math.pi * j / nu
            rr = R + r * math.cos(b)
            row.append(len(V)); V.append([rr * math.cos(a) * sx, r * math.sin(b) * squash, rr * math.sin(a) * sz])
        rows.append(row)
    rows.append(rows[0])
    F = _grid(rows, nu)
    return orient(V, F)


def catmull(pts, n=6):
    P = [np.asarray(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)


def tube(P, R, seg=8, caps=True, squash=1.0, closed=False, up_bias=0.0, round_end=False):
    """Sweep a circle along polyline P with radii R (scalar, list or callable(t))."""
    P = np.asarray(P, float)
    n = len(P)
    if callable(R):
        R = [R(i / (n - 1)) for i in range(n)]
    elif np.isscalar(R):
        R = [R] * n
    T = np.zeros_like(P)
    for i in range(n):
        if closed:
            T[i] = P[(i + 1) % n] - P[i - 1]
        else:
            T[i] = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    ref = np.array([0, 1, 0.]) if abs(T[0][1]) < 0.9 else np.array([1, 0, 0.])
    N = np.cross(T[0], ref); N /= np.linalg.norm(N)
    V, rows = [], []
    for i in range(n):
        if i:
            N = N - T[i] * (N @ T[i]); N /= np.linalg.norm(N)
        B = np.cross(T[i], N)
        row = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            off = R[i] * (math.cos(a) * N + math.sin(a) * B)
            off[1] *= squash
            off[1] += up_bias * R[i]
            row.append(len(V)); V.append(P[i] + off)
        rows.append(row)
    if closed:
        rows.append(rows[0])
    F = _grid(rows, seg)
    if caps and not closed:
        V.append(P[0]); F += _fan(len(V) - 1, rows[0])
        V.append(P[-1]); F += _fan(len(V) - 1, rows[-1])
    return orient(V, F)


def prism(poly, depth, axis="x"):
    """Extrude a convex 2D polygon (u,v) along axis, centred."""
    poly = np.asarray(poly, float)
    n = len(poly)
    V = []
    for s in (-depth / 2, depth / 2):
        for u, v in poly:
            V.append([s, v, u] if axis == "x" else [u, v, s])
    F = []
    for j in range(n):
        a, b = j, (j + 1) % n
        F += [[a, b, n + b], [a, n + b, n + a]]
    for j in range(1, n - 1):
        F += [[0, j + 1, j], [n, n + j, n + j + 1]]
    return orient(V, F)


# ---------------------------------------------------------------- model + export
class Model:
    def __init__(self, name):
        self.name, self.parts = name, []

    def add(self, mesh, color, smooth=40, node="Main"):
        V, F = mesh
        self.parts.append((node, color, np.asarray(V, float), np.asarray(F, int), smooth))
        return self

    def build(self):
        nodes = {}
        for node, color, V, F, ang in self.parts:
            uv = uv_of(color)
            a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
            fn = np.cross(b - a, c - a)
            area = np.linalg.norm(fn, axis=1)
            keep = area > 1e-9
            F, fn, area = F[keep], fn[keep], area[keep]
            fu = fn / area[:, None]
            # weld coincident positions so smoothing crosses seams
            key = np.round(V, 5)
            _, inv = np.unique(key, axis=0, return_inverse=True)
            inv = inv.ravel()
            Fw = inv[F]
            adj = {}
            for fi, tri in enumerate(Fw):
                for vi in tri:
                    adj.setdefault(vi, []).append(fi)
            cth = math.cos(math.radians(ang))
            out_p, out_n, idx, cache = [], [], [], {}
            for fi, tri in enumerate(F):
                for k in range(3):
                    vi = Fw[fi][k]
                    nb = adj[vi]
                    sel = [g for g in nb if fu[fi] @ fu[g] >= cth - 1e-6]
                    n = fn[sel].sum(0)
                    n /= (np.linalg.norm(n) or 1)
                    p = V[tri[k]]
                    kk = (tuple(np.round(p, 5)), tuple(np.round(n, 3)))
                    if kk not in cache:
                        cache[kk] = len(out_p); out_p.append(p); out_n.append(n)
                    idx.append(cache[kk])
            d = nodes.setdefault(node, {"P": [], "N": [], "UV": [], "I": []})
            off = len(d["P"])
            d["P"] += out_p; d["N"] += out_n; d["UV"] += [uv] * len(out_p)
            d["I"] += [i + off for i in idx]
        return nodes

    def tris(self):
        return sum(len(d["I"]) // 3 for d in self.build().values())


def export(model, outdir):
    nodes = model.build()
    # centre on X/Z, base at y=0
    allp = np.vstack([np.array(d["P"]) for d in nodes.values()])
    mn, mx = allp.min(0), allp.max(0)
    shift = np.array([-(mn[0] + mx[0]) / 2, -mn[1], -(mn[2] + mx[2]) / 2])
    png = palette_png()
    blob, views, accs, meshes, gnodes = b"", [], [], [], []

    def add_view(data, target=None):
        nonlocal blob
        while len(blob) % 4:
            blob += b"\x00"
        v = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}
        if target:
            v["target"] = target
        views.append(v); blob += data
        return len(views) - 1

    tri_total = 0
    for name, d in nodes.items():
        P = (np.array(d["P"]) + shift).astype(np.float32)
        N = np.array(d["N"], np.float32)
        UV = np.array(d["UV"], np.float32)
        I = np.array(d["I"], np.uint32)
        tri_total += len(I) // 3
        attrs = {}
        for key, arr, typ in (("POSITION", P, "VEC3"), ("NORMAL", N, "VEC3"), ("TEXCOORD_0", UV, "VEC2")):
            acc = {"bufferView": add_view(arr.tobytes(), 34962), "componentType": 5126,
                   "count": len(arr), "type": typ}
            if key == "POSITION":
                acc["min"], acc["max"] = P.min(0).tolist(), P.max(0).tolist()
            accs.append(acc); attrs[key] = len(accs) - 1
        accs.append({"bufferView": add_view(I.tobytes(), 34963), "componentType": 5125,
                     "count": len(I), "type": "SCALAR"})
        mat = 1 if name == "Glass" else 0
        meshes.append({"name": f"{model.name}_{name}", "primitives": [
            {"attributes": attrs, "indices": len(accs) - 1, "material": mat}]})
        gnodes.append({"name": name if len(nodes) > 1 else model.name, "mesh": len(meshes) - 1})
    img_view = add_view(png)
    while len(blob) % 4:
        blob += b"\x00"
    gltf = {
        "asset": {"version": "2.0", "generator": "winter-props meshlib"},
        "scene": 0, "scenes": [{"nodes": list(range(len(gnodes)))}],
        "nodes": gnodes, "meshes": meshes, "accessors": accs, "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
        "images": [{"bufferView": img_view, "mimeType": "image/png", "name": "WinterPalette"}],
        "samplers": [{"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}],
        "textures": [{"sampler": 0, "source": 0}],
        "materials": [
            {"name": "WinterPalette", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
             "metallicFactor": 0.0, "roughnessFactor": 0.75}},
            {"name": "LampGlass", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
             "metallicFactor": 0.0, "roughnessFactor": 0.3}, "emissiveFactor": [1.0, 0.85, 0.55]},
        ],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    glb = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob))
    glb += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(blob), 0x004E4942) + blob
    os.makedirs(f"{outdir}/glb", exist_ok=True)
    os.makedirs(f"{outdir}/obj", exist_ok=True)
    with open(f"{outdir}/glb/{model.name}.glb", "wb") as f:
        f.write(glb)
    # OBJ + MTL
    lines = [f"mtllib {model.name}.mtl"]
    vo = 0
    for name, d in nodes.items():
        P = np.array(d["P"]) + shift
        lines.append(f"o {name if len(nodes) > 1 else model.name}")
        lines += [f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}" for p in P]
        lines += [f"vt {u:.5f} {1 - v:.5f}" for u, v in d["UV"]]
        lines += [f"vn {n[0]:.4f} {n[1]:.4f} {n[2]:.4f}" for n in d["N"]]
        lines.append("usemtl " + ("LampGlass" if name == "Glass" else "WinterPalette"))
        I = d["I"]
        for t in range(0, len(I), 3):
            a, b, c = (I[t] + 1 + vo, I[t + 1] + 1 + vo, I[t + 2] + 1 + vo)
            lines.append(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}")
        vo += len(P)
    with open(f"{outdir}/obj/{model.name}.obj", "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(f"{outdir}/obj/{model.name}.mtl", "w") as f:
        f.write("newmtl WinterPalette\nKd 1 1 1\nmap_Kd WinterPalette.png\n\n"
                "newmtl LampGlass\nKd 1 1 1\nKe 1 0.85 0.55\nmap_Kd WinterPalette.png\n")
    with open(f"{outdir}/obj/WinterPalette.png", "wb") as f:
        f.write(png)
    with open(f"{outdir}/WinterPalette.png", "wb") as f:
        f.write(png)
    return tri_total, (mx - mn)
