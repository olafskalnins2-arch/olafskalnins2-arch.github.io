from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '27', 'Speed_Racer', 'Rare', 0.32

# ---------------------------------------------------------------- paint helpers (local)
def _box(x, z, cx, cz, hw, hh, k=420):
    """anti-aliased filled rectangle in physical units"""
    return aa(np.maximum(np.abs(x - cx) - hw, np.abs(z - cz) - hh) * k)

def _ell(x, z, cx, cz, rx, rz, k=420):
    return aa((np.sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2) - 1) * min(rx, rz) * k)

_SEG = {'a': (0, 1, 1), 'd': (0, -1, 1), 'g': (0, 0, 1), 'b': (1, 0.5, 0), 'c': (1, -0.5, 0), 'e': (-1, -0.5, 0), 'f': (-1, 0.5, 0)}
_ON = {'2': 'abged', '7': 'abc'}

def _digit(img, x, z, ch, cx, cz, w, h, t, col):
    """7-segment digit, w/h = width/height of the glyph, t = stroke"""
    for s in _ON[ch]:
        ox, oz, horiz = _SEG[s]
        px, pz = cx + ox * w / 2, cz + oz * h / 2
        if horiz: img = mix(img, _box(x, z, px, pz, w / 2 + t / 2, t / 2), col)
        else: img = mix(img, _box(x, z, px, pz, t / 2, h / 4 + t / 2), col)
    return img

def _wrap(a):
    return np.angle(np.exp(1j * a))

def build():
    pal = {'red': '#d7262e', 'red_d': '#a91b22', 'white': '#ffffff', 'black': '#111111', 'grey': '#2c2c2e',
           'metal': '#c9ccd1', 'sole': '#2a2a2a'}
    RED, WHITE, BLACK, RED_D = pal['red'], pal['white'], pal['black'], pal['red_d']
    P = []
    R_T = 0.47        # approx. torso radius -> physical units along the surface

    # ---------------- one-piece suit: legs + hip first (the top tucks into the hip, belt hides the seam)
    pt = pants('SuitPants', 2.24, 0.62, 0.045, hip_off=0.08, leg_extra=lambda z, a: 0.012)
    hip, legL, legR = pt
    legR.rect_key = 'SuitPantsLegR'   # mirrored stripes: each leg its own texture

    def suit_paint(U, V, m):
        img = P_solid(RED)(U, V, m); z, az = zc(U, V, m)
        x = az * R_T
        # side seams (subtle)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 400) * 0.6, RED_D)
        # twin racing stripes down the front
        for sg in (-1, 1):
            img = mix(img, aa((np.abs(az - sg * 0.28) - 0.068) * 420) * (z < 3.16), WHITE)
        if m.get('kind') == 'torso':
            # zipper
            img = mix(img, aa((np.abs(az) - 0.007) * 500) * (z > 2.3), BLACK)
            # sponsor patch, wearer's left chest: white plate, red chevron, black "lettering"
            cx, cz = 0.34, 2.74
            img = mix(img, _box(x, z, cx, cz, 0.105, 0.055), BLACK)
            img = mix(img, _box(x, z, cx, cz, 0.095, 0.045), WHITE)
            img = mix(img, _box(x, z, cx - 0.055, cz, 0.025, 0.03), RED)
            for k in range(2):
                img = mix(img, _box(x, z, cx + 0.03, cz + 0.016 - k * 0.032, 0.045, 0.008), BLACK)
            # sponsor patch, wearer's right chest: tyre-brand oval
            cx = -0.34
            img = mix(img, _ell(x, z, cx, cz, 0.11, 0.06), BLACK)
            img = mix(img, _ell(x, z, cx, cz, 0.085, 0.04), WHITE)
            img = mix(img, _ell(x, z, cx, cz, 0.06, 0.022), RED)
            img = mix(img, _box(x, z, cx, cz, 0.045, 0.004), WHITE)
            # small sponsor bar on the belly
            for sg in (-1, 1):
                img = mix(img, _box(x, z, sg * 0.30, 2.48, 0.08, 0.03), BLACK)
                img = mix(img, _box(x, z, sg * 0.30, 2.48, 0.07, 0.022), WHITE)
                img = mix(img, _box(x, z, sg * 0.30 - 0.035, 2.48, 0.022, 0.014), RED)
                img = mix(img, _box(x, z, sg * 0.30 + 0.025, 2.488, 0.035, 0.005), BLACK)
                img = mix(img, _box(x, z, sg * 0.30 + 0.025, 2.47, 0.035, 0.005), BLACK)
            # back: race number roundel "27" + sponsor bar across the shoulders
            xb = _wrap(az - PI) * R_T
            img = mix(img, _ell(xb, z, 0, 2.66, 0.2, 0.2), BLACK)
            img = mix(img, _ell(xb, z, 0, 2.66, 0.18, 0.18), WHITE)
            img = _digit(img, xb, z, '2', -0.055, 2.66, 0.07, 0.17, 0.028, BLACK)
            img = _digit(img, xb, z, '7', 0.055, 2.66, 0.07, 0.17, 0.028, BLACK)
            img = mix(img, _box(xb, z, 0, 2.97, 0.2, 0.035), WHITE)
            for k in range(5):
                img = mix(img, _box(xb, z, -0.15 + k * 0.075, 2.97, 0.026, 0.012), RED if k % 2 else BLACK)
        return img

    def leg_paint(U, V, m):
        img = P_solid(RED)(U, V, m); z, az = zc(U, V, m)
        sg = 1 if m.get('side') == 'L' else -1
        s = np.clip((1.95 - z) / 0.35, 0, 1)
        c = -sg * (0.28 + 0.14 * s); hw = 0.068 + 0.062 * s
        img = mix(img, aa((np.abs(az - c) - hw) * 420), WHITE)
        # outer-side seam
        img = mix(img, aa((np.abs(_wrap(az - sg * PI / 2)) - 0.012) * 400) * 0.6, RED_D)
        # sponsor patch on the outer thigh
        x = _wrap(az - sg * PI / 2) * 0.24
        img = mix(img, _box(x, z, 0, 1.52, 0.085, 0.07), BLACK)
        img = mix(img, _box(x, z, 0, 1.52, 0.075, 0.06), WHITE)
        img = mix(img, _box(x, z, 0, 1.55, 0.06, 0.012), RED)
        img = mix(img, _box(x, z, 0, 1.505, 0.06, 0.007), BLACK)
        img = mix(img, _box(x, z, -0.02, 1.48, 0.04, 0.006), BLACK)
        return img

    hip.paint = suit_paint
    legL.paint = leg_paint; legR.paint = leg_paint

    top = torso_shell('SuitTop', 2.08, 0.035, nseg=32, extra=lambda z, a: 0.01, th=0.02)
    top.paint = suit_paint
    P.append(top)
    P += pt

    # padded collar (black, white piping)
    col = collar('Collar', 'stand', h=0.09, flare=0.035, th=0.035)
    col.paint = lambda U, V, m: mix(mix(P_solid(BLACK)(U, V, m), aa((0.86 - V) * 300), WHITE), aa((0.8 - V) * 300) * aa((V - 0.84) * 300), RED)
    col.rect_key = 'Collar'
    P.append(col)
    tb = piece_bvh(top)
    loc, n = project(tb, Vector((0, 0, 3.04)), Vector((0, 1, 0)))
    zp = prim_rbox('ZipPull', loc + n * 0.02, (0.045, 0.03, 0.09), 'metal', bevel=0.01, group='Top')
    zp.bone = 'UpperTorso'; P.append(zp)

    # belt with checkered-flag trim (fitted over the suit top + the pants waist, straight ring)
    belt = torso_shell('Belt', 2.12, 0.012, nseg=32, zs=[2.12, 2.17, 2.22, 2.27, 2.33], elevs=(), th=0.025,
                       bvh=tb, hang=2.45, over=[hip, top], over_gap=0.014, group='Bottom')
    belt.skirt = False; belt.rect_key = 'Belt'
    def belt_paint(U, V, m):
        img = P_solid(BLACK)(U, V, m)
        z, az = zc(U, V, m)
        z0, z1 = m['zmin'] + 0.035, m['zmax'] - 0.035
        sq = (z1 - z0) / 2
        nu = 2 * int(round(m.get('circ', 3.0) / sq / 2))
        i = np.floor(U * nu).astype(int); j = np.floor((z - z0) / sq).astype(int)
        inside = (z > z0) & (z < z1)
        img = mix(img, (((i + j) % 2) == 0) * inside, WHITE)
        img = mix(img, aa(np.abs(z - z0) * 500 - 1.5) + aa(np.abs(z - z1) * 500 - 1.5), RED)
        return img
    belt.paint = belt_paint
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.225)), Vector((0, 1, 0)))
    P.append(prim_rbox('Buckle', loc + n * 0.025, (0.2, 0.05, 0.16), 'metal', bevel=0.015, group='Bottom'))
    P.append(prim_box('BuckleCenter', loc + n * 0.052, (0.12, 0.012, 0.08), 'black', group='Bottom'))

    # ---------------- sleeves (stripe down the outer side, sponsor patch on the upper arm)
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.9, 0.045, extra=lambda t, a: 0.01)
        def sp(U, V, m, sg=sg):
            img = P_solid(RED)(U, V, m); _, az = zc(U, V, m)
            t = m['vmin'] + V * (m['vmax'] - m['vmin'])
            out = _wrap(az + sg * PI / 2)
            img = mix(img, aa((np.abs(out) - 0.16) * 300) * (t > 0.04), WHITE)
            img = mix(img, aa((np.abs(out) - 0.05) * 300) * (t > 0.04), RED)
            x = az * 0.15
            img = mix(img, _box(x, t * 1.8, 0, 0.42, 0.065, 0.05), BLACK)
            img = mix(img, _box(x, t * 1.8, 0, 0.42, 0.055, 0.04), WHITE)
            img = mix(img, _box(x, t * 1.8, -0.02, 0.43, 0.025, 0.012), RED)
            img = mix(img, _box(x, t * 1.8, 0.0, 0.40, 0.045, 0.006), BLACK)
            return img
        sl.paint = sp; sl.rect_key = 'Sleeve_' + s
        P.append(sl)

        # glove: black, covers the wrist and the ball hand, closed at the fingertips
        gl = _glove('Glove_' + s, s, 0.86, 1.09, lambda t: 0.03 + 0.055 * (1 - _sstep2(0.9, 0.97, t)))
        gl.paint = P_solid(BLACK); P.append(gl)
        # checkered gauntlet cuff over the sleeve end / glove top
        cf = sleeve('GloveCuff_' + s, s, 0.83, 0.94, 0.115, nrows=4, cap=False, th=0.02,
                    extra=lambda t, a: 0.025 * (t - 0.83) / 0.11)
        def cpaint(U, V, m):
            img = P_solid(BLACK)(U, V, m)
            i = np.floor(U * 16).astype(int); j = np.floor((V - 0.12) / 0.38).astype(int)
            inside = (V > 0.12) & (V < 0.88)
            img = mix(img, (((i + j) % 2) == 0) * inside, WHITE)
            return img
        cf.paint = cpaint; cf.rect_key = 'GloveCuff'
        P.append(cf)
        # white knuckle pads on the back of the hand (outer side)
        gb = piece_bvh(gl)
        for k, y in enumerate((-0.085, -0.025, 0.035)):
            kp = surface_patch(f'Knuckle{s}{k}', gb, lambda u, t, y=y: Vector((1.04 * sg, y - 0.022 + u * 0.044, 1.13 + t * 0.1)),
                               Vector((-sg, 0, 0)), 0.006, 3, 3, col='white', th=0.022)
            kp.region = 'arm_' + s
            P.append(kp)

    # ---------------- racing boots
    for s in 'LR':
        b = shoe('Boot_' + s, s, off=0.045, bulk=0.025, toe=0.04, sole_h=0.05)
        def bp(U, V, m):
            img = P_solid(BLACK)(U, V, m); z, az = zc(U, V, m)
            st = m['sole_top']
            img = mix(img, aa((z - st) * 600), pal['sole'])
            img = mix(img, aa(np.abs(z - (st + 0.03)) * 600 - 3), WHITE)
            return img
        b.paint = bp; P.append(b)
        sh = _shin(leg_tube('BootShaft_' + s, s, 0.84, 0.47, 0.1, nseg=16, group='Feet', extra=lambda z, a: 0.005))
        sh.paint = lambda U, V, m: mix(P_solid(BLACK)(U, V, m), aa(np.abs(V - 0.93) * 300 - 3), WHITE)
        sh.rect_key = 'BootShaft'
        P.append(sh)
        P.append(_shin(leg_tube('BootStrap_' + s, s, 0.66, 0.59, 0.13, nseg=16, nrows=2, group='Feet', col='red', th=0.02)))
    return P, pal

def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def _sstep2(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def _glove(name, side, t0, t1, off_fn, nseg=14, nrows=10, group='Top', th=0.02):
    """sleeve-like tube from the forearm over the ball hand, closed with a cap at the fingertips"""
    bvh = B.bvh['arm_' + side]
    rows = []; hints = []; vv = []
    for t in np.linspace(t0, t1, nrows):
        c, tg = arm_point(side, t)
        dirs = tube_dirs_b(tg, nseg)
        ring = ray_ring(bvh, c, dirs, off_fn(t), R=0.7, smooth=1)
        if ring is None: break
        rows.append(ring); hints.append(dirs); vv.append(t)
    # rounded bottom of the ball hand: rays from the hand centre, tilted toward the fingertips
    hc, tg = arm_point(side, vv[-1])
    base = tube_dirs_b(tg, nseg); o = off_fn(vv[-1])
    for k, th_ in enumerate((68, 46, 24)):
        a = math.radians(th_)
        dirs = [(d * math.sin(a) + tg * math.cos(a)).normalized() for d in base]
        ring = ray_ring(bvh, hc, dirs, o, R=0.7, smooth=1)
        if ring is None: break
        rows.append(ring); hints.append(dirs); vv.append(vv[-1] + 0.02)
    h = bvh.ray_cast(hc + tg * 0.7, -tg, 0.7)
    tip = (h[0] + tg * o) if h[0] is not None else hc + tg * 0.2
    vmin, vmax = vv[0], vv[-1]
    pc = _grid_with_ij(name, rows, True, [(v - vmin) / (vmax - vmin) for v in vv], hints, group, None, cap_end=tip)
    pc.meta.update(kind='sleeve', circ=sum((rows[0][j] - rows[0][j - 1]).length for j in range(nseg)), t0=t0, t1=t1, vmin=vmin, vmax=vmax)
    if th: thicken(pc, th)
    pc.rect_key = name.replace('_L', '').replace('_R', '')
    pc.region = 'arm_' + side
    return pc
