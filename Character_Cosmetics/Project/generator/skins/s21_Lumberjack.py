from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '21', 'Lumberjack', 'Common', 0.32


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _band(c, K=9.0):
    """soft 0/1 square wave (1 on even cells) from a cell coordinate c - seamless, anti-aliased"""
    return np.clip(0.5 + np.sin(PI * c) * K, 0, 1)


def buffalo(x_cells, z_cells, pal, shade=0.0):
    """red / black buffalo check: black where both bands cross, dark red where one band crosses"""
    a = _band(x_cells); b = _band(z_cells)
    img = P_solid(pal['red'])(x_cells, z_cells, {})
    img = mix(img, np.maximum(a, b) * (1 - a * b), pal['red_d'])
    img = mix(img, a * b, pal['black'])
    # fine woven texture (subtle thread lines)
    th = 0.5 + 0.5 * np.sin(2 * PI * x_cells * 4) * np.sin(2 * PI * z_cells * 4)
    img = mix(img, th * 0.10, pal['black'])
    if shade: img = mix(img, np.full(x_cells.shape, shade), pal['black'])
    return img


def strap(name, samples, w, bvh, lift, th=0.012, col=None, group='Top'):
    """flat strap draped on a garment: samples = [(origin, ray_dir, across, lift_scale)] along the path.
    Every point across the strap is ray-cast onto bvh and lifted along the hit normal."""
    rows = []; hints = []
    for O, d, a, ls in samples:
        r = []; hh = []
        for t in (-0.5, 0.0, 0.5):
            loc, n = project(bvh, O + a * (w * t), d)
            if loc is None:
                print('STRAP MISS', name, tuple(O)); loc, n = project(B.bvh['torso_up'], O + a * (w * t), d); loc = loc + n * 0.08
            r.append(loc + n * lift * ls); hh.append(n)
        rows.append(r); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group,
                    v_vals=[i / (len(rows) - 1) for i in range(len(rows))])
    thicken(pc, th)
    pc.meta['patch'] = True; pc.region = 'torso'; pc.skirt = False
    return pc


def build():
    pal = {'red': '#b3261e', 'red_d': '#5e1712', 'black': '#1c1c1c', 'jeans': '#3d5a8a', 'jeans_d': '#2c4369',
           'jeans_l': '#5874a3', 'stitch': '#c99a3e', 'boot': '#6b4428', 'boot_d': '#4a2e1a', 'sole': '#2a1f17',
           'lace': '#d9c39a', 'metal': '#b9bcc0', 'btn': '#efe6d2', 'susp': '#b3261e', 'susp_d': '#7d1913'}
    P = []
    CHK = 0.14   # check size (units)

    # ---------------- jeans (lower layer first) ----------------
    jx = lambda z, a: 0.022 + 0.05 * min(1.0, max(0.0, (1.45 - z) / 0.5))      # slight boot-cut flare over the boots
    pt = pants('Jeans', 2.2, 0.95, 0.04, hip_off=0.06, leg_extra=jx, nseg=16)

    def jpaint(U, V, m):
        img = P_solid(pal['jeans'])(U, V, m)
        z, az = zc(U, V, m)
        rng = np.random.default_rng(21)
        img = img + (rng.random(U.shape)[..., None] - 0.5) * 10               # denim grain
        if m.get('kind') == 'leg':
            img = mix(img, 0.28 * np.cos(az).clip(0, 1) ** 3 * np.exp(-((z - 1.4) / 0.25) ** 2), pal['jeans_l'])  # thigh fade
            for c in (PI / 2, -PI / 2):                                              # out-seam + inseam, gold stitching
                img = mix(img, aa((np.abs(az - c) - 0.012) * 300), pal['jeans_d'])
                dash = (np.sin(z * 2 * PI / 0.035) > 0)
                img = mix(img, aa((np.abs(az - c - 0.035) - 0.007) * 300) * dash, pal['stitch'])
        else:
            img = mix(img, aa((np.abs(az) - 0.01) * 300) * (z < 2.15), pal['jeans_d'])   # fly
            img = mix(img, aa((z - 2.12) * -400), pal['jeans_d'])                   # waistband
        return np.clip(img, 0, 255)
    for p in pt: p.paint = jpaint
    P += pt
    for s in 'LR':   # rolled-up cuffs (lighter inside denim)
        cf = leg_tube('JeanCuff_' + s, s, 1.05, 0.94, 0.04 + jx(0.95, 0) + 0.035, nseg=16, nrows=3, th=0.02, group='Bottom')
        cf.paint = lambda U, V, m: mix(mix(P_solid(pal['jeans_l'])(U, V, m), aa(np.abs(V - 0.5) * 300 - 3), pal['jeans']),
                                       aa(np.minimum(V, 1 - V) * 300 - 1.5) , pal['jeans_d'])
        P.append(cf)

    # ---------------- flannel shirt (untucked, hangs over the jeans) ----------------
    shirt = torso_shell('Flannel', 1.98, 0.05, nseg=32, extra=lambda z, a: 0.018 + 0.035 * max(0, 2.25 - z), th=0.02,
                        hang=2.3, over=pt)

    def spaint(U, V, m):
        z, az = zc(U, V, m)
        n = max(2, int(round(m['circ'] / CHK)) // 2 * 2)
        img = buffalo(U * n + 0.5, (z - 2.0) / CHK, pal)
        img = mix(img, aa((np.abs(az) - 0.045) * 300) * 0.35, pal['black'])           # placket edges
        img = mix(img, aa((np.abs(np.abs(az) - 0.045) - 0.004) * 400) * 0.6, pal['black'])
        img = mix(img, aa((z - 2.005) * 300) * 0.5, pal['black'])                    # hem stitch shadow
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.4, pal['black'])   # side seams
        return img
    shirt.paint = spaint; P.append(shirt)
    sb = piece_bvh(shirt)

    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.44, 0.05, extra=lambda t, a: 0.015 + 0.02 * t)
        def slp(U, V, m):
            n = max(2, int(round(m['circ'] / CHK)) // 2 * 2)
            return buffalo(U * n + 0.5, V * 0.44 * 1.35 / CHK, pal)
        sl.paint = slp; P.append(sl)
        # rolled cuff: thick roll of the same flannel just above the bare forearm
        cf = sleeve('RollCuff_' + s, s, 0.38, 0.47, 0.085, nrows=4, cap=False, th=0.025, extra=lambda t, a: 0.012)
        def cfp(U, V, m):
            n = max(2, int(round(m['circ'] / CHK)) // 2 * 2)
            img = buffalo(U * n, V * 0.6, pal, shade=0.12)
            img = mix(img, aa(np.abs(V - 0.5) * 120 - 2) * 0.5, pal['black'])      # fold line between the rolls
            return img
        cf.paint = cfp; P.append(cf)

    col = collar('Collar', 'fold', h=0.06, flare=0.03, open_front=0.30, fold=0.08)
    col.paint = lambda U, V, m: buffalo(U * 10, V * 1.2 + 0.3, pal); P.append(col)

    for i, z in enumerate((2.93, 2.70, 2.47, 2.24, 2.04)):     # pearl snap buttons down the placket
        loc, n = project(sb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.02, 0.026, n=8, col='btn', group='Top'))

    # ---------------- red suspenders (X at the back) ----------------
    XS, ZA, ZX, ZB, W = 0.27, 2.80, 2.43, 2.07, 0.085
    for s, sg in (('L', 1), ('R', -1)):
        x = XS * sg
        smp = []
        for z in np.linspace(ZB, ZA, 13):                                          # front, straight down
            smp.append((Vector((x, -1.5, z)), Vector((0, 1, 0)), Vector((1, 0, 0)), 1.0))
        for ph in np.linspace(-75, 75, 11):                                        # over the shoulder
            u = Vector((0, math.sin(math.radians(ph)), math.cos(math.radians(ph))))
            smp.append((Vector((x, 0, ZA)) + u * 1.5, -u, Vector((1, 0, 0)), 1.0))
        k = XS / (ZA - ZX)
        def back(zs, sg=sg, s=s, up=0.0):
            out = []
            for z in zs:                                                           # back: crossing in an X
                xb = sg * XS * (z - ZX) / (ZA - ZX)
                a = Vector((1, 0, -k * sg)).normalized()
                ls = 1.0 + (1.2 * math.exp(-((z - ZX) / 0.12) ** 2) if s == 'R' else 0.0)   # right strap rides over the left one
                out.append((Vector((xb, 1.5, z)), Vector((0, -1, 0)), a, ls + up))
            return out
        def stp(U, V, m):
            img = P_solid(pal['susp'])(U, V, m)
            img = mix(img, aa((np.minimum(U, 1 - U) - 0.12) * 200), pal['susp_d'])  # edge stitching
            return img
        # split at the X crossing (centre line): the part beyond it is its own piece on the other side of the torso
        # (it starts a hair above the crossing and lies a hair higher, so the joint is closed but never coincident)
        for part, sm in (('', smp + back(np.linspace(ZA, ZX, 7))), ('Low', back(np.linspace(ZX + 0.012, ZB, 7), up=0.3))):
            st = strap('Suspender' + part + '_' + s, sm, W, sb, 0.012, th=0.01)
            st.paint = stp; st.rect_key = 'Suspender'; P.append(st)
        for zz, yd, xx in ((ZB + 0.035, 1, x), (ZB + 0.035, -1, -x)):             # metal clips at the strap ends
            loc, n = project(sb, Vector((xx, 0, zz)), Vector((0, yd, 0)))
            cl = prim_box(f'Clip_{s}{"F" if yd > 0 else "B"}', loc + n * 0.032, (0.10, 0.025, 0.075), 'metal', group='Top')
            cl.bone = 'LowerTorso'; P.append(cl)

    # ---------------- tall brown leather lace-up boots ----------------
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.045, bulk=0.035, toe=0.03, sole_h=0.07)
        def bpaint(U, V, m):
            img = P_solid(pal['boot'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            img = mix(img, aa(np.abs(z - m['sole_top'] - 0.025) * 600 - 1) * 0.8, pal['boot_d'])   # welt stitch
            return img
        sh.paint = bpaint; P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 1.07, 0.46, 0.065, nseg=16, group='Feet',
                               extra=lambda z, a: 0.008 * max(0.0, math.cos(a)) + 0.014 * min(1.0, max(0.0, (0.76 - z) / 0.28))))
        def shp(U, V, m):
            img = P_solid(pal['boot'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa((z - 1.02) * -500), pal['boot_d'])                   # padded top collar
            uw = 0.30                                                              # lacing area (front)
            img = mix(img, aa((np.abs(az) - uw) * 200) * 0.55, pal['boot_d'])      # tongue
            u = np.clip(az / uw, -1, 1); v = z / 0.075
            for sgn in (1, -1):
                dist = np.abs(((v + sgn * (u + 1) / 2 + 0.5) % 1.0) - 0.5)          # criss-cross laces
                img = mix(img, aa((dist - 0.09) * 19) * (np.abs(az) < uw) * (z < 0.98), pal['lace'])
            for sgn in (1, -1):                                                    # metal hooks on both lace edges
                dv = ((v + 0.0) % 1.0) - 0.5
                img = mix(img, aa((np.sqrt((dv * 0.075 * 300) ** 2 + ((az - sgn * uw) * 0.28 * 300) ** 2) - 4)) * (z < 0.98), pal['metal'])
            return img
        shaft.paint = shp; P.append(shaft)
    return P, pal
