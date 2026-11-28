from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03 (RF_SLIT_TOP), o04 helpers (dome)
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '34', 'Frost_Viking', 'Epic', 0.32


def _shin34(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _frac(x): return x - np.floor(x)


# ---------------------------------------------------------------- paints
def mail_paint(pal, sx, sz, z0=0.0, trim=None):
    """riveted mail: staggered rows of small rings (physical size sx around x sz along)"""
    def f(U, V, m):
        x, z = U * sx, z0 + V * sz
        img = P_solid(pal['mail'])(U, V, m)
        s = 0.052
        k = np.floor(z / (s * 0.75))
        fx = _frac(x / s + 0.5 * (k % 2)); fz = _frac(z / (s * 0.75))
        d = np.hypot(fx - 0.5, (fz - 0.5) * 0.75)
        ring = np.clip(1 - np.abs(d - 0.3) / 0.11, 0, 1)
        img = mix(img, (d < 0.17).astype(float) * 0.55, pal['mail_d'])
        img = mix(img, ring * (0.2 + 0.25 * (fz > 0.5)), pal['mail_l'])
        img = mix(img, np.clip((0.5 - fz) * 2, 0, 1) * (d > 0.38) * 0.35, pal['mail_d'])
        if trim:
            for zz, w, c in trim(m):
                img = mix(img, aa((np.abs(z - zz) - w) * 500), pal[c])
        return img
    return f


def fur_paint(base, dark, light, sx, sz, seed=0.0, shag=None):
    """thick fluffy fur: soft clumps + fine strands running down"""
    def f(U, V, m):
        x, z = U * sx, V * sz
        img = P_solid(base)(U, V, m)
        n = (np.sin(x * 61 + np.sin(z * 23 + seed) * 1.7) * 0.5 + np.sin(x * 137 + z * 11 + seed * 3) * 0.3
             + np.sin(z * 47 + x * 29 + seed) * 0.2)
        c = np.sin(x * 21 + 3 * np.sin(z * 9 + seed)) * np.sin(z * 26 + 2 * np.sin(x * 13 + seed))
        img = mix(img, np.clip(-n, 0, 1) * 0.35, dark)
        img = mix(img, np.clip(n, 0, 1) * 0.45, light)
        img = mix(img, np.clip(c - 0.45, 0, 1) * 1.1, dark)
        img = mix(img, np.clip(-c - 0.55, 0, 1) * 1.2, light)
        if shag is not None:   # darker tufty edge band at V=shag (hem)
            e = shag + 0.04 * np.sin(x * 70) + 0.03 * np.sin(x * 23)
            img = mix(img, np.clip((e - V) * 25, 0, 1) * 0.35, dark)
        return img
    return f


def wool_paint(pal, sx, sz, z0=0.0, base='wool'):
    def f(U, V, m):
        x, z = U * sx, z0 + V * sz
        img = P_solid(pal[base])(U, V, m)
        tw = 0.5 + 0.5 * np.sin((x + z) * 2 * PI / 0.035)
        img = mix(img, tw * 0.22, pal['wool_d'])
        h = np.sin(x * 53 + np.sin(z * 17) * 2) * np.sin(z * 41 + x * 7)
        img = mix(img, np.clip(h, 0, 1) * 0.18, pal['wool_l'])
        return img
    return f


def leather_paint(pal, col='leather'):
    def f(U, V, m):
        img = P_solid(pal[col])(U, V, m)
        h = np.sin(U * 90 + np.sin(V * 30) * 2) * np.sin(V * 70 + U * 15)
        return mix(img, np.clip(h, 0, 1) * 0.2, pal['leather_l'])
    return f


# ---------------------------------------------------------------- geometry helpers
def _orient(pc, f, want):
    n = face_normal(pc.verts, f)
    return tuple(reversed(f)) if n.dot(want) < 0 else tuple(f)


def blade_piece(name, origin, eu, ev, en, us, vtop, vbot, th, col, group='Extras'):
    """flat plate whose outline is column-monotone: for every u in us it spans v in [vbot(u), vtop(u)]; thickness th along en"""
    pc = Piece(name, group)
    T = []; Bt = []
    for u in us:
        row = []
        for v in (vtop(u), vbot(u)):
            p = origin + eu * u + ev * v
            row.append((pc.add_vert(p + en * th / 2), pc.add_vert(p - en * th / 2)))
        T.append(row)
    c = origin + eu * (sum(us) / len(us))
    for k in range(len(us) - 1):
        (tf, tb), (bf, bb) = T[k]; (tf2, tb2), (bf2, bb2) = T[k + 1]
        pc.add_face(_orient(pc, (tf, tf2, bf2, bf), en), None, col)
        pc.add_face(_orient(pc, (tb, bb, bb2, tb2), -en), None, col)
        pc.add_face(_orient(pc, (tf, tb, tb2, tf2), ev), None, col)
        pc.add_face(_orient(pc, (bf, bf2, bb2, bb), -ev), None, col)
    for k, want in ((0, -eu), (len(us) - 1, eu)):
        (tf, tb), (bf, bb) = T[k]
        pc.add_face(_orient(pc, (tf, bf, bb, tb), want), None, col)
    pc.rigid = True
    return pc


def disc_piece(name, center, ex, ey, en, radii, nseg, group='Extras', col=None, bulge=0.0):
    """flat round disc facing en (polar grid, u = angle, v = radius / R), slightly domed by bulge"""
    R = radii[-1]
    rows = []; hints = []
    for r in radii:
        q = 1 - (r / R) ** 2
        rows.append([center + (ex * math.cos(2 * PI * j / nseg) + ey * math.sin(2 * PI * j / nseg)) * r + en * bulge * q
                     for j in range(nseg)])
        hints.append([en] * nseg)
    pc = grid_piece(name, rows, True, v_vals=[r / R for r in radii], hints=hints, group=group, col=col,
                    cap_start=center + en * bulge)
    pc.rigid = True
    return pc


def trefoil(c, eu, ev, en, size, depth, n=72):
    pts = []
    for k in range(n + 1):
        t = 2 * PI * k / n
        x = math.sin(t) + 2 * math.sin(2 * t); y = math.cos(t) - 2 * math.cos(2 * t); zz = -math.sin(3 * t)
        pts.append(c + eu * x * size + ev * y * size + en * zz * depth)
    return pts


# ---------------------------------------------------------------- build
def build():
    pal = {'mail': '#6d7680', 'mail_d': '#3a3f46', 'mail_l': '#98a1ab',
           'wool': '#5a4632', 'wool_d': '#43331f', 'wool_l': '#6f5a43', 'wrap': '#7d6a52',
           'fur': '#e9e4d6', 'fur_d': '#bdb5a2', 'fur_l': '#fbf8f0', 'boot': '#d9d4c8',
           'leather': '#4a3020', 'leather_d': '#2e1d12', 'leather_l': '#6a4a32',
           'gold': '#c9a24a', 'gold_d': '#8a6a28', 'gold_l': '#e8cc7a',
           'red': '#b03a2e', 'red_d': '#7e2820', 'cream': '#e9dcc0', 'iron': '#4b4f55', 'iron_l': '#7a8088',
           'wood': '#7a5332', 'wood_d': '#553820', 'sole': '#2a1d14'}
    P = []

    # ---- brown wool trousers (under layer first)
    pt = pants('Trousers', 2.22, 0.55, 0.04, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.015 * max(0, 1.4 - z))
    for p in pt:
        p.paint = wool_paint(pal, p.meta.get('circ', 3.0), p.meta['zmax'] - p.meta['zmin'], p.meta['zmin'])
    P += pt

    # ---- criss-cross leg wraps (wool puttees with leather thongs), shin
    wraps = []
    for s in 'LR':
        lw = leg_tube('LegWrap_' + s, s, 1.26, 0.74, 0.092, nseg=16, th=0.015, extra=lambda z, a: 0.004)
        circ = lw.meta['circ']
        def wp(U, V, m, circ=circ):
            x, z = U * circ, 0.74 + V * 0.52
            img = P_solid(pal['wrap'])(U, V, m)
            # spiral wool bands
            sp = _frac(z / 0.055 + x / circ)
            img = mix(img, aa((np.abs(sp - 0.02) - 0.03) * 60), pal['wool_d'])
            img = mix(img, np.clip(1 - np.abs(sp - 0.5) * 4, 0, 1) * 0.2, pal['wool_l'])
            # crossing leather thongs (two opposite helices -> X's front and back)
            Pp = circ / 2
            for sgn in (1, -1):
                u = _frac(x / Pp + sgn * z / 0.2)
                d = np.abs(u - 0.5) * Pp
                img = mix(img, aa((d - 0.026) * 700), pal['leather_d'])
                img = mix(img, aa((np.abs(d - 0.008) - 0.004) * 700) * 0.7, pal['leather_l'])
            # tie bands top and bottom
            img = mix(img, aa((np.abs(z - 1.23) - 0.022) * 600), pal['leather_d'])
            img = mix(img, aa((np.abs(z - 0.79) - 0.018) * 600), pal['leather'])
            return img
        lw.paint = wp; wraps.append(lw)
    P += wraps

    # ---- fur boots
    boot_fur = fur_paint(pal['boot'], pal['fur_d'], pal['fur_l'], 1.4, 0.45, seed=2.0)
    for s in 'LR':
        sh = shoe('FurBoot_' + s, s, off=0.06, bulk=0.055, toe=0.03, sole_h=0.05, open_elev=46)
        def bp(U, V, m):
            img = boot_fur(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.015)) * 600 - 6), pal['leather'])     # welt strap
            return mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
        sh.paint = bp; P.append(sh)
        shaft = _shin34(leg_tube('BootShaft_' + s, s, 0.86, 0.47, 0.13, nseg=16, group='Feet', th=0.02,
                                 extra=lambda z, a: 0.012 + 0.01 * math.sin(a * 5)))
        def shp(U, V, m):
            img = boot_fur(U, V, m); z = 0.47 + V * 0.39
            img = mix(img, aa((np.abs(z - 0.62) - 0.02) * 600), pal['leather'])                     # leather tie
            return img
        shaft.paint = shp; P.append(shaft)
        cuff = _shin34(leg_tube('BootCuff_' + s, s, 0.93, 0.8, 0.165, nseg=16, nrows=3, group='Feet', th=0.02,
                                extra=lambda z, a: 0.018 + 0.012 * math.sin(a * 7) + 0.03 * (z - 0.8) / 0.13))
        cuff.paint = fur_paint(pal['fur'], pal['fur_d'], pal['fur_l'], 1.6, 0.15, seed=5.0); P.append(cuff)

    # ---- mail tunic: hangs over the trousers, flares a little, knee-high-ish hem
    tun = torso_shell('MailTunic', 1.64, 0.06, nseg=32, extra=lambda z, a: 0.014 + 0.085 * max(0, 2.05 - z),
                      th=0.025, hang=2.3, over=pt)
    zmn, zmx = tun.meta['zmin'], tun.meta['zmax']
    mp = mail_paint(pal, tun.meta['circ'], zmx - zmn, zmn,
                    trim=lambda m: ((zmn + 0.035, 0.03, 'leather'), (zmn + 0.075, 0.006, 'gold')))
    def tp(U, V, m):
        img = mp(U, V, m); z, az = zc(U, V, m)
        # leather baldric (carries the shield): a tilted ring around the chest
        zb = 2.46 + 0.2 * np.sin(az)
        img = mix(img, aa((np.abs(z - zb) - 0.04) * 500), pal['leather'])
        img = mix(img, aa((np.abs(np.abs(z - zb) - 0.028) - 0.003) * 600) * 0.7, pal['leather_l'])
        # side slit seams (leather binding)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.012) * 400) * (z < 1.95), pal['leather'])
        return img
    tun.paint = tp; P.append(tun)

    # ---- sleeves: wool undersleeve to the wrist, mail half-sleeve, leather bracers
    for s in 'LR':
        us = sleeve('UnderSleeve_' + s, s, 0.0, 0.95, 0.04, nseg=12, extra=lambda t, a: 0.008 + 0.012 * t)
        us.paint = wool_paint(pal, us.meta['circ'], 1.2); P.append(us)
        ms = sleeve('MailSleeve_' + s, s, 0.0, 0.46, 0.075, nseg=14, extra=lambda t, a: 0.01 + 0.03 * max(0, t - 0.25))
        ms.paint = mail_paint(pal, ms.meta['circ'], 0.6, trim=lambda m: ((0.03, 0.028, 'leather'), (0.07, 0.005, 'gold')))
        P.append(ms)
        br = sleeve('Bracer_' + s, s, 0.62, 0.93, 0.07, nrows=5, nseg=12, cap=False, th=0.02,
                    extra=lambda t, a: 0.006 + 0.02 * (t - 0.62) / 0.31)
        def brp(U, V, m):
            img = leather_paint(pal)(U, V, m)
            for vv in (0.1, 0.9):
                img = mix(img, aa((np.abs(V - vv) - 0.035) * 300), pal['gold'])
            # knot diamond row on the outside
            dv = np.abs(_frac(U * 6) - 0.5) * 2 + np.abs(V - 0.5) * 3.2
            img = mix(img, aa((np.abs(dv - 0.55) - 0.08) * 120), pal['gold_d'])
            return img
        br.paint = brp; P.append(br)

    # ---- belt fitted on the tunic (straight ring)
    belt = band('Belt', 2.1, 2.24, 0.012, th=0.022, bvh=piece_bvh(tun), hang=2.34); belt.group = 'Extras'
    bcirc = belt.meta['circ']
    def beltp(U, V, m):
        img = leather_paint(pal)(U, V, m)
        img = mix(img, aa(np.minimum(V - 0.1, 0.9 - V) * -200), pal['leather_d'])
        st = (np.abs(np.abs(V - 0.5) - 0.3) < 0.03) & (_frac(U * bcirc / 0.03) < 0.55)
        img = mix(img, st.astype(float) * 0.8, pal['leather_l'])
        x = U * bcirc
        d = np.hypot((_frac(x / 0.16) - 0.5) * 0.16, (V - 0.5) * 0.14)
        img = mix(img, aa((d - 0.014) * 900), pal['gold'])
        img = mix(img, aa((d - 0.006) * 900) * 0.6, pal['gold_l'])
        return img
    belt.paint = beltp; P.append(belt)
    bb = piece_bvh(belt)

    # ---- knotwork gold buckle: round plate + raised trefoil knot + rim
    loc, n = project(bb, Vector((0, 0, 2.17)), Vector((0, 1, 0)))
    n = Vector((n.x, n.y, 0)).normalized()
    eu = Vector((1, 0, 0)); ev = Vector((0, 0, 1))
    c0 = loc + n * 0.008
    bk = [prim_cyl('BucklePlate', c0, c0 + n * 0.03, 0.115, n=24, col='gold_d')]
    rim = [c0 + n * 0.032 + (eu * math.cos(2 * PI * k / 24) + ev * math.sin(2 * PI * k / 24)) * 0.105 for k in range(25)]
    bk.append(tube_path('BuckleRim', rim, 0.013, 'gold', n=6, caps=False))
    kn = trefoil(c0 + n * 0.042, eu, ev, n, 0.026, 0.006)
    bk.append(tube_path('BuckleKnot', kn, 0.0115, 'gold_l', n=6, caps=False))
    bk.append(prim_sphere('BuckleBoss', c0 + n * 0.045, 0.02, 'gold', nl=4, seg=8))
    bk.append(prim_box('BeltTail', loc + n * 0.012 + Vector((0.19, 0, -0.005)), (0.14, 0.016, 0.1), 'leather_d'))
    for q in bk: q.rigid = True; q.bone = 'LowerTorso'; q.group = 'Extras'
    P += bk

    # ---- hand axe hooked in the belt on the character's right front hip
    az = -0.85
    d = Vector((math.sin(az), -math.cos(az), 0))
    bl, bn = project(bb, d * 1.5 + Vector((0, 0, 2.17)), -d)
    bn = Vector((bn.x, bn.y, 0)).normalized()
    tng = Z.cross(bn).normalized()            # points toward the front centre
    hb = bl + bn * 0.045
    h_top = hb + Z * 0.2; h_bot = hb + Z * -0.5 + bn * 0.05
    ax = [prim_cyl('AxeHandle', h_bot, h_top, 0.024, 0.026, n=8, col='wood'),
          prim_cyl('AxeGrip', h_bot + (h_top - h_bot) * 0.03, h_bot + (h_top - h_bot) * 0.3, 0.029, n=8, col='leather'),
          prim_cyl('AxeKnob', h_bot - (h_top - h_bot).normalized() * 0.02, h_bot + (h_top - h_bot).normalized() * 0.02, 0.034, n=8, col='iron'),
          prim_cyl('AxeFrog', hb - Z * 0.045 - bn * 0.01, hb + Z * 0.045 - bn * 0.01, 0.042, n=10, col='leather_d')]
    sock = h_top - Z * 0.05
    ax.append(prim_rbox('AxeSocket', sock, (0.07, 0.07, 0.12), 'iron', rot=Matrix((tng, bn, Z)).transposed(), bevel=0.01))
    ax.append(blade_piece('AxeBlade', sock, tng, Z, bn, [0.02, 0.08, 0.14, 0.2, 0.25, 0.27],
                          lambda u: 0.04 + 0.08 * (u / 0.27) ** 2,
                          lambda u: -0.04 - 0.19 * (u / 0.27) ** 1.7, 0.024, 'iron_l'))
    ax.append(blade_piece('AxeEdge', sock, tng, Z, bn, [0.26, 0.285],
                          lambda u: 0.125, lambda u: -0.235, 0.012, 'mail_l'))
    ax.append(blade_piece('AxePoll', sock, -tng, Z, bn, [0.02, 0.06], lambda u: 0.03, lambda u: -0.03, 0.04, 'iron'))
    for q in ax: q.rigid = True; q.bone = 'LowerTorso'; q.group = 'Extras'
    P += ax

    # ---- thick white fur mantle around the shoulders (over the tunic)
    mzs = [2.5, 2.6, 2.7, 2.8, 2.9]
    man = torso_shell('FurMantle', 2.5, 0.075, nseg=32, zs=mzs, elevs=(18, 34, 46),
                      extra=lambda z, a: 0.06 + 0.035 * max(0, (2.72 - z) / 0.22) + 0.012 * math.sin(a * 11) * max(0, (2.62 - z) / 0.12),
                      th=0.035, over=[tun], over_gap=0.035)
    head_clear(man, 0.03)
    man.paint = fur_paint(pal['fur'], pal['fur_d'], pal['fur_l'], man.meta['circ'], man.meta['zmax'] - man.meta['zmin'], seed=1.0, shag=0.12)
    P.append(man)
    mb = piece_bvh(man)
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        fd = dome('FurShoulder_' + s, s, Vector((0.6 * sg, 0.0, 2.84)), 0.15, (-34, -16, 4, 24, 46, 68), nseg=18,
                  extra=lambda e, a: 0.03 * max(0, (5 - e) / 40) + 0.01 * math.sin(a * 9), th=0.03)
        fd.paint = fur_paint(pal['fur'], pal['fur_d'], pal['fur_l'], 1.6, 0.5, seed=3.0 + sg, shag=0.15)
        fd.meta.update(circ=1.6); fd.rect_key = 'FurShoulder'; fd.bone = 'UpperTorso'
        head_clear(fd, 0.03)
        P.append(fd)
    # fur roll around the neck, resting on the mantle
    ring = []
    for k in range(25):
        a = 2 * PI * k / 24
        dd = Vector((math.sin(a), -math.cos(a), 0))
        p = Vector((0, 0, 3.7)) + Vector((dd.x * 0.44, dd.y * 0.39, 0))
        h = mb.ray_cast(p, Vector((0, 0, -1)), 1.5)
        zt = h[0].z if h[0] else 3.15
        ring.append(Vector((dd.x * 0.44, dd.y * 0.39, zt + 0.03)))
    roll = tube_path('FurRoll', ring, 0.085, None, n=10, group='Top', caps=False)
    head_clear(roll, 0.03)
    roll.paint = fur_paint(pal['fur'], pal['fur_d'], pal['fur_l'], 0.6, 2.3, seed=7.0)
    roll.meta['rect'] = (128, 256); roll.bone = 'UpperTorso'; P.append(roll)
    # gold brooches pinning the mantle at the front, joined by a chain
    br = []
    pts = []
    for sg in (-1, 1):
        l2, n2 = project(mb, Vector((0.2 * sg, 0, 2.7)), Vector((0, 1, 0)))
        br.append(prim_cyl(f'Brooch{sg}', l2 - n2 * 0.01, l2 + n2 * 0.03, 0.065, n=14, col='gold'))
        br.append(prim_sphere(f'BroochGem{sg}', l2 + n2 * 0.035, 0.028, 'red', nl=4, seg=8))
        rr = [l2 + n2 * 0.034 + Vector((math.cos(2 * PI * k / 14), 0, math.sin(2 * PI * k / 14))) * 0.05 for k in range(15)]
        br.append(tube_path(f'BroochRing{sg}', rr, 0.008, 'gold_d', n=5, caps=False))
        pts.append(l2 + n2 * 0.03)
    a0, a1 = pts
    chain = [a0 + (a1 - a0) * (k / 8) + Vector((0, -0.02, -0.07 * math.sin(PI * k / 8))) for k in range(9)]
    br.append(tube_path('BroochChain', chain, 0.012, 'gold', n=5))
    for q in br: q.rigid = True; q.bone = 'UpperTorso'; q.group = 'Top'
    P += br

    # ---- round painted shield on the back
    cover = [tun, man, belt, roll] + [p for p in P if p.name.startswith('FurShoulder_')]
    ymax = 0.0
    for pc in cover:
        for v in pc.verts:
            if abs(v.x) < 0.5 and 2.0 < v.z < 3.15: ymax = max(ymax, v.y)
    R = 0.5
    sc = Vector((0, ymax + 0.075, 2.58))
    en = Vector((0, 1, 0)); ex = Vector((1, 0, 0)); ey = Vector((0, 0, 1))
    radii = [0.08, 0.14, 0.2, 0.26, 0.32, 0.38, 0.44, 0.47, R]
    sh = disc_piece('Shield', sc, ex, ey, en, radii, 32, bulge=0.03)
    thicken(sh, 0.035)
    sh.meta['rect'] = (512, 128)
    def shieldp(U, V, m):
        img = P_solid(pal['red'])(U, V, m)
        w = _frac(U * 4 + V * 0.55)                     # 4 curved cream swirl arms
        img = mix(img, aa((np.abs(w - 0.25) - 0.12) * 120) * (V > 0.2), pal['cream'])
        img = mix(img, aa((np.abs(np.abs(w - 0.25) - 0.12) - 0.01) * 200) * (V > 0.2), pal['red_d'])
        # plank lines (wood grain showing through) and weathering
        g = np.sin(U * 2 * PI * 9) * 0.5 + 0.5
        img = mix(img, np.clip(np.sin(V * 40 + np.sin(U * 60) * 1.5), 0, 1) * 0.08, pal['red_d'])
        img = mix(img, aa((np.abs(V - 0.22) - 0.02) * 300), pal['gold_d'])
        img = mix(img, aa((V - 0.9) * -300), pal['leather'])
        return img
    sh.paint = shieldp
    sp = [sh]
    boss_c = sc + en * 0.03
    sp.append(prim_sphere('ShieldBoss', boss_c, 0.1, 'gold', nl=6, seg=14, scale=(1, 0.65, 1)))
    sp.append(prim_cyl('ShieldBossRim', boss_c - en * 0.01, boss_c + en * 0.015, 0.125, n=16, col='gold_d'))
    rimp = [sc + (ex * math.cos(2 * PI * k / 40) + ey * math.sin(2 * PI * k / 40)) * R - en * 0.017 for k in range(41)]
    sp.append(tube_path('ShieldRim', rimp, 0.026, 'iron', n=6, caps=False))
    for k in range(8):
        a = 2 * PI * (k + 0.5) / 8
        p = sc + (ex * math.cos(a) + ey * math.sin(a)) * (R - 0.055) + en * 0.006
        sp.append(prim_sphere(f'ShieldRivet{k}', p, 0.02, 'gold_l', nl=3, seg=6, scale=(1, 0.6, 1)))
    # shield strap on the back: from the baldric up behind the shield
    for q in sp: q.rigid = True; q.bone = 'UpperTorso'; q.group = 'Extras'
    P += sp
    return P, pal
