from o04 import *
NUM, NAME, RARITY, MAXD = '39', 'Court_Jester', 'Epic', 0.32

# ---- zig-zag hem: NP points around the tunic, a tip on the front / back centre line ----
NP = 10
ZTIP, ZVAL, ZT = 1.58, 1.80, 2.02          # point tips, valleys between them, top of the reshaped zone
HH = ZVAL - ZTIP                            # = half height of one harlequin diamond (hem points ARE the lower half-diamonds)
C_RUFF = Vector((0, 0, 2.95))


def _tri(s):                                # 0 on a point, 1 in a valley (s = az in point periods)
    return np.abs(np.mod(s + 0.5, 1.0) - 0.5) * 2


def _s(az): return az / (2 * PI / NP)


def _zh(az): return ZTIP + HH * _tri(_s(az))


def _remap(z, az):
    """original (hanging, straight-hemmed) z -> zig-zag hem z. Only ever moves rows UP (clearance stays)."""
    zh = _zh(az)
    return np.where(z < ZT, ZT - (ZT - z) * (ZT - zh) / (ZT - ZTIP), z)


def _zigzag(pc):
    n0 = pc.meta['n_outer_verts']
    orig = [v.copy() for v in pc.verts]
    for i, v in enumerate(orig):
        src = orig[i] if i < n0 else orig[i - n0]          # inner shell uses its outer twin's column
        if v.z >= ZT: continue
        az = math.atan2(src.x, -src.y)
        pc.verts[i] = Vector((v.x, v.y, float(_remap(np.array(v.z), np.array(az)))))
    pc.meta['zig'] = True
    return pc


def _harlequin(pal):
    w = 2 * PI * 0.52 / NP                   # physical width of one diamond (approx.)
    ga = math.hypot(2 / w, 1 / HH)
    def f(U, V, m):
        z0, az = zc(U, V, m)
        z = _remap(z0, az) if m.get('zig') else z0
        s = _s(az); v = (z - ZVAL) / HH
        a = 2 * s + v; b = 2 * s - v
        fa = np.floor((a + 1) / 2); fb = np.floor((b + 1) / 2)
        gold = (np.mod(fa + fb, 2) == 1)
        img = P_solid(pal['purple'])(U, V, m)
        # soft sheen inside every diamond (lighter towards its upper corner)
        la = (a + 1) / 2 - fa; lb = (b + 1) / 2 - fb          # 0..1 inside the cell
        sheen = np.clip(1 - np.abs(la - 0.5) - np.abs(lb - 0.5), 0, 1)
        img = mix(img, gold.astype(float), pal['gold'])
        img = mix(img, sheen * 0.18 * (~gold), pal['purple_l'])
        img = mix(img, sheen * 0.22 * gold, pal['gold_l'])
        # thin dark outline on every diamond edge
        da = np.abs((a + 1) / 2 - np.round((a + 1) / 2)) * 2
        db = np.abs((b + 1) / 2 - np.round((b + 1) / 2)) * 2
        d = np.minimum(da, db) / ga
        img = mix(img, aa((d - 0.004) * 170), pal['purple_d'])
        # white studs where four diamonds meet
        s1 = s - (np.floor(s) + 0.5); v1 = v - 2 * np.round(v / 2)
        s2 = s - np.round(s); v2 = v - (2 * np.round((v - 1) / 2) + 1)
        dd = np.minimum(np.hypot(s1 * w, v1 * HH), np.hypot(s2 * w, v2 * HH))
        img = mix(img, aa((dd - 0.02) * 170) * (z > ZVAL + 0.05), pal['white'])
        if m.get('zig'):
            # bell-gold piping along the pointed hem
            dh = (z - _zh(az)) * 0.6
            img = mix(img, aa((dh - 0.028) * 170) * (z < ZT), pal['bell'])
            img = mix(img, aa(np.abs(dh - 0.034) * 170 - 0.8) * (z < ZT), pal['purple_d'])
        return img
    return f


def _bell_paint(pal):
    def f(U, V, m):
        img = P_solid(pal['bell'])(U, V, m)
        img = mix(img, np.clip((V - 0.55) * 2.2, 0, 1) * 0.6, pal['bell_l'])        # highlight on top
        img = mix(img, np.clip((0.45 - V) * 2.0, 0, 1) * 0.5, pal['bell_d'])        # darker underside
        img = mix(img, aa(np.abs(V - 0.52) * 400 - 2), pal['bell_d'])               # seam ring
        du = np.minimum(np.mod(U, 0.5), 0.5 - np.mod(U, 0.5))                       # distance to the U=0 / U=0.5 meridians
        img = mix(img, aa((du - 0.025) * 400) * (V < 0.42), '#3a2a08')             # slit (front-back across the bottom)
        return img
    return f


def _bell(P, name, top, r, pal, bone, group='Extras'):
    """jingle bell hanging from `top`: stem, ball (painted slit / seam), clapper ball under the slit"""
    st = prim_cyl(name + 'Stem', top + Vector((0, 0, 0.008)), top - Vector((0, 0, 0.022)), r * 0.28, n=6, col='bell_d', group=group)
    c = top - Vector((0, 0, 0.018 + r * 0.92))
    bl = prim_sphere(name, c, r, None, nl=6, seg=10, group=group)
    bl.fcol = [None] * len(bl.faces); bl.paint = _bell_paint(pal); bl.rect_key = 'Bell'; bl.meta.update(rect=(128, 64))
    cl = prim_sphere(name + 'Clapper', c - Vector((0, 0, r * 0.78)), r * 0.28, 'bell_d', nl=4, seg=6, group=group)
    for q in (st, bl, cl):
        q.rigid = True; q.bone = bone; P.append(q)


def _cast_radii(c, dirs, layers, R=1.5):
    """outermost radius along every dir over several (bvh, gap) layers; misses filled from neighbours"""
    n = len(dirs); rad = []
    for d in dirs:
        best = None
        for bv, gap in layers:
            h = bv.ray_cast(c + d * R, -d, R)
            if h[0] is None: continue
            r = (h[0] - c).dot(d) + gap
            best = r if best is None else max(best, r)
        rad.append(best)
    if all(r is None for r in rad): return [0.5] * n
    r0 = list(rad)
    for j in range(n):
        if r0[j] is None:
            a = j; b = j
            while r0[a % n] is None: a -= 1
            while r0[b % n] is None: b += 1
            f = (j - a) / (b - a); rad[j] = r0[a % n] * (1 - f) + r0[b % n] * f
    for _ in range(3):                                          # grow-only smoothing (no dents)
        rad = [max(rad[j], (rad[j - 1] + 2 * rad[j] + rad[(j + 1) % n]) / 4) for j in range(n)]
    return rad


def _ruff(name, elevs, base_layers, flare, amp, waves, ph, pal, N=64, th=0.02, under=None, extra_base=None):
    D = hdirs_b(N)
    rows = []; hints = []; base = []
    for e in elevs:
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        r0 = _cast_radii(C_RUFF, dirs, base_layers)
        if extra_base: r0 = [r + extra_base(e) for r in r0]
        base.append(r0)
        ring = []
        for j, d in enumerate(dirs):
            az = azb(j, N)
            ring.append(C_RUFF + d * (r0[j] + flare(e) + amp(e) * math.sin(waves * az + ph)))
        rows.append(ring); hints.append(dirs)
    # scalloped outline: wave crests reach a little further out along the collar surface
    last, prev = rows[-1], rows[-2]
    for j in range(N):
        az = azb(j, N)
        t = (last[j] - prev[j]); t = t.normalized() if t.length > 1e-6 else Z
        last[j] = last[j] + t * 0.03 * (0.5 + 0.5 * math.sin(waves * az + ph))
    vv = [k / (len(elevs) - 1) for k in range(len(elevs))]
    pc = grid_piece(name, rows, closed=True, v_vals=vv, hints=hints, group='Extras')
    head_clear(pc, 0.035)
    if th: thicken(pc, th)
    head_clear(pc, 0.03)
    pc.region = 'torso'; pc.skirt = False
    pc.meta.update(rect=(512, 128), circ=4.0)
    def paint(U, V, m):
        az = 2 * PI * (U - 0.5)
        sw = np.sin(waves * az + ph)
        img = P_solid(pal['white'])(U, V, m)
        img = mix(img, (0.5 - 0.5 * sw) * np.clip(V * 1.4, 0, 1) * 0.75, pal['white_d'])     # pleat shadows
        img = mix(img, aa((0.9 - V) * 300), pal['bell'])                                    # gold piping on the edge
        return img
    pc.paint = paint
    return pc, base


def build():
    pal = {'purple': '#6b2fa0', 'purple_d': '#45186e', 'purple_l': '#8a4fc0', 'gold': '#e5b72b', 'gold_l': '#f3d36a',
           'gold_d': '#a8820f', 'white': '#fbfbf8', 'white_d': '#d9d4c8', 'bell': '#f2cf4a', 'bell_l': '#fbe9a0',
           'bell_d': '#9c7a14', 'sole': '#2e1247'}
    P = []
    # ---------------- two-tone leggings: left leg purple, right leg gold ----------------
    pt = pants('Hose', 2.2, 0.52, 0.03, hip_off=0.05,
               leg_extra=lambda z, a: 0.012 * min(1.0, max(0.0, (z - 0.52) / 0.25)))

    def hip_paint(U, V, m):
        z, az = zc(U, V, m)
        img = P_solid(pal['gold'])(U, V, m)
        img = mix(img, (az > 0).astype(float), pal['purple'])
        seam = np.minimum(np.abs(az), PI - np.abs(az))
        return mix(img, aa(seam * 300 - 1.2), pal['purple_d'])

    def leg_paint(col, other):
        def f(U, V, m):
            z, az = zc(U, V, m)
            img = P_solid(col)(U, V, m)
            r = m.get('circ', 1.2) / (2 * PI)
            dx = np.abs(az) * r
            for zc0, hw, hh in ((1.52, 0.07, 0.11), (1.2, 0.08, 0.12), (0.86, 0.065, 0.1)):   # counter-coloured diamonds down the front
                d = dx / hw + np.abs(z - zc0) / hh
                img = mix(img, aa((d - 1) * 14), other)
                img = mix(img, aa(np.abs(d - 1) * 14 - 0.6), pal['purple_d'])
            return img
        return f
    pt[0].paint = hip_paint
    pt[1].paint = leg_paint(pal['purple'], pal['gold']); pt[1].rect_key = 'HoseLegL'      # +X = character's left
    pt[2].paint = leg_paint(pal['gold'], pal['purple']); pt[2].rect_key = 'HoseLegR'
    P += pt

    # ---------------- harlequin tunic with a pointed (zig-zag) hem, hanging over the leggings ----------------
    tunic = torso_shell('Tunic', ZTIP, 0.05, nseg=4 * NP, extra=lambda z, a: 0.012 + 0.06 * max(0, 2.15 - z), th=0.025,
                        hang=2.3, over=pt)
    _zigzag(tunic)
    tunic.paint = _harlequin(pal); P.append(tunic)
    tb = piece_bvh(tunic)

    # ---------------- sleeves: purple with a gold dagged cuff and a white wrist ruffle ----------------
    sleeves = []
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.9, 0.05, extra=lambda t, a: 0.012 + 0.03 * t)
        def sp(U, V, m):
            img = P_solid(pal['purple'])(U, V, m)
            img = mix(img, np.clip(1 - np.abs(np.mod(U * 2, 1) - 0.5) * 2, 0, 1) * 0.12, pal['purple_l'])
            edge = 0.78 + 0.1 * _tri(U * 7)
            img = mix(img, aa((edge - V) * 300), pal['gold'])
            img = mix(img, aa(np.abs(V - edge) * 300 - 1.0), pal['purple_d'])
            return img
        sl.paint = sp; P.append(sl); sleeves.append(sl)
        rf = sleeve('WristRuff_' + s, s, 0.84, 0.98, 0.06, nseg=28, nrows=4, cap=False, th=0.015,
                    extra=lambda t, a: 0.05 + 0.085 * ((t - 0.84) / 0.14) ** 1.3 + 0.024 * ((t - 0.84) / 0.14) * math.sin(7 * a))
        def rp(U, V, m):
            az = 2 * PI * (U - 0.5)
            img = P_solid(pal['white'])(U, V, m)
            img = mix(img, (0.5 - 0.5 * np.sin(7 * az)) * V * 0.8, pal['white_d'])
            return mix(img, aa((0.88 - V) * 300), pal['bell'])
        rf.paint = rp; P.append(rf)

    # ---------------- big white ruffled collar: two pleated layers lying on the shoulders ----------------
    base_layers = [(piece_bvh(tunic, *sleeves), 0.035), (B.bvh['torso_up'], 0.1)]
    lo_elevs = [48, 40, 32, 24, 16, 8, 0, -6]
    fl_l = lambda e: 0.15 * max(0.0, (40 - min(e, 40)) / 46.0) ** 1.4
    am_l = lambda e: 0.055 * max(0.0, (48 - e) / 54.0) ** 1.2
    ruff_lo, base_lo = _ruff('RuffLower', lo_elevs, base_layers, fl_l, am_l, 16, 0.0, pal, th=0.02)
    P.append(ruff_lo)
    up_elevs = [48, 40, 32, 24, 16]
    fl_u = lambda e: fl_l(e) + am_l(e) + 0.025 + 0.012 + 0.045 * max(0.0, (40 - min(e, 40)) / 24.0) ** 1.5
    am_u = lambda e: 0.036 * max(0.0, (48 - e) / 32.0) ** 1.2
    ruff_up, _ = _ruff('RuffUpper', up_elevs, base_layers, fl_u, am_u, 16, PI, pal, N=64, th=0.018)
    ruff_up.rect_key = 'RuffUpper'; P.append(ruff_up)

    # ---------------- pompom buttons down the front ----------------
    for i, z in enumerate((2.80, 2.55, 2.30)):
        loc, n = project(tb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        pp = prim_sphere(f'Pompom{i}', loc + n * 0.032, 0.05, 'white', nl=5, seg=8, scale=(1, 0.75, 1), group='Top')
        pp.rigid = True; P.append(pp)

    # ---------------- jingle bells on every hem point ----------------
    N = 4 * NP
    for k in range(NP):
        tip = tunic.verts[4 * k]                                 # bottom row, tip column
        d = Vector((tip.x, tip.y, 0)).normalized()
        _bell(P, f'HemBell{k}', tip + d * 0.012, 0.05, pal, 'LowerTorso')

    # ---------------- curly-toe slippers with bells ----------------
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        foot = 'LeftFoot' if s == 'L' else 'RightFoot'
        sh = shoe('Slipper_' + s, s, off=0.055, bulk=0.02, toe=0.08, sole_h=0.03, open_elev=42)
        def shp(U, V, m):
            z, az = zc(U, V, m)
            img = P_solid(pal['purple'])(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            edge = 0.76 + 0.14 * _tri(U * 9)                     # gold dagged cuff round the opening
            img = mix(img, aa((edge - V) * 300), pal['gold'])
            img = mix(img, aa(np.abs(V - edge) * 300 - 1.0), pal['purple_d'])
            return img
        sh.paint = shp; P.append(sh)
        tip = min(sh.verts, key=lambda p: p.y)
        tip = Vector((tip.x, tip.y + 0.03, 0.40))
        cc = tip + Vector((0, -0.01, 0.15))   # curl starts inside the toe (no gap)
        pts = []
        for k in range(16):
            f = k / 15
            ang = f * 1.5 * PI
            rad = 0.13 * (1 - 0.5 * f)
            pts.append(cc + Vector((0, -math.sin(ang) * rad, -math.cos(ang) * rad)))
        cu = tube_path('Curl_' + s, pts, 0.06, None, n=8, group='Feet', rfn=lambda t: 0.068 * (1 - 0.72 * t))
        def cpaint(U, V, m):
            img = P_solid(pal['purple'])(U, V, m)
            band = np.mod(V * 6 + U, 1.0)
            img = mix(img, aa(np.abs(band - 0.5) * 60 - 8), pal['gold'])
            return img
        cu.fcol = [None] * len(cu.faces); cu.paint = cpaint; cu.rect_key = 'Curl'; cu.meta.update(rect=(64, 128))
        cu.rigid = True; cu.bone = foot; P.append(cu)
        # bell hanging from the curl's end, kept clear of the slipper's toe
        end = pts[-1]
        sb = piece_bvh(sh)
        h = sb.ray_cast(Vector((end.x, end.y, 1.0)), Vector((0, 0, -1)), 1.0)
        r = 0.045
        top = end - Vector((0, 0, 0.01))
        if h[0] is not None:
            need = h[0].z + 0.012 + 2 * r * 0.92 + 0.018 + r * 0.28
            if top.z < need: top = Vector((top.x, top.y, need))
        _bell(P, 'ToeBell' + s, top, r, pal, foot, group='Feet')
    return P, pal
