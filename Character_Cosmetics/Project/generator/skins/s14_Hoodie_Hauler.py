from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers

NUM, NAME, RARITY, MAXD = '14', 'Hoodie_Hauler', 'Common', 0.32


def _heather(img, U, seed, light, dark, amt=0.35):
    '''fine heather speckle (deterministic)'''
    rng = np.random.default_rng(seed)
    nz = rng.random(U.shape)
    img = mix(img, (nz > 0.80) * amt, light)
    return mix(img, (nz < 0.16) * amt, dark)


def _ribs(img, coord, freq, col, amt=0.45):
    return mix(img, (0.5 + 0.5 * np.cos(coord * freq)) ** 2 * amt, col)


def _puffy_patch(name, bvh, fn, d, lift, ns, nt, col=None, th=0.02, group='Top'):
    '''surface patch whose lift varies over (s, t): a padded shape lying on a garment'''
    rows = []; hints = []
    for i in range(nt):
        r = []; hh = []
        for j in range(ns):
            s, t = j / (ns - 1), i / (nt - 1)
            p = fn(s, t)
            loc, n = project(bvh, p, d)
            if loc is None: loc, n = p, -d
            r.append(loc + n * lift(s, t)); hh.append(n)
        rows.append(r); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group)
    if th > 0: thicken(pc, th)
    return pc


def build():
    pal = {'grey': '#9aa0a6', 'grey_d': '#7f858b', 'grey_l': '#b4b9be', 'char': '#3a3d42', 'char_d': '#2b2d31',
           'char_l': '#4a4e54', 'white': '#f2f2f2', 'sole': '#d9dbde', 'sole_d': '#b9bcc0', 'red': '#d64541',
           'red_d': '#a8302d', 'tip': '#d8dadd', 'metal': '#c7cacf'}
    P = []

    # ---------------- joggers (built first: the hoodie hangs over them) ----------------
    def leg_x(z, a):
        thigh = 0.022 * min(1.0, max(0.0, (z - 0.95) / 0.45))          # roomy thigh
        blouse = 0.03 * math.exp(-((z - 0.86) / 0.12) ** 2)          # fabric bunching above the cuff
        return 0.018 + thigh + blouse
    pt = pants('Joggers', 2.2, 0.76, 0.045, hip_off=0.06, leg_extra=leg_x, nseg=16)

    def jog_paint(U, V, m):
        img = P_solid(pal['char'])(U, V, m)
        img = _heather(img, U, 41, pal['char_l'], pal['char_d'], 0.25)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['char_d'])   # side seams
        if m.get('kind') == 'hip':
            img = _ribs(mix(img, aa((2.08 - z) * 400), pal['char_d']), az, 90, pal['char'], 0.4)  # waistband
        return img
    for p in pt: p.paint = jog_paint
    P += pt

    # ribbed ankle cuffs: start hidden inside the bloused trouser hem, gather tight at the ankle
    for s in 'LR':
        cf = leg_tube('JogCuff_' + s, s, 0.84, 0.60, 0.05, nseg=16, nrows=4, th=0.02)
        def cuff_paint(U, V, m):
            img = P_solid(pal['char_d'])(U, V, m)
            z, az = zc(U, V, m)
            return _ribs(img, az, 64, pal['char'], 0.6)
        cf.paint = cuff_paint; cf.rect_key = 'JogCuff'
        P.append(cf)

    # ---------------- zip hoodie (untucked, hangs over the joggers) ----------------
    hood_y = lambda z, a: 0.022 + 0.03 * max(0.0, 2.12 - z)
    top = torso_shell('Hoodie', 1.86, 0.06, nseg=32, extra=hood_y, th=0.025, hang=2.3, over=pt)

    def hoodie_paint(U, V, m):
        img = P_solid(pal['grey'])(U, V, m)
        img = _heather(img, U, 14, pal['grey_l'], pal['grey_d'], 0.3)
        z, az = zc(U, V, m)
        zmin = m['zmin']
        rib = z < zmin + 0.11
        img = mix(img, rib * 1.0, pal['grey_d'])                                     # ribbed hem band
        img = _ribs(img, az, 110, pal['grey'], 0.5 * rib)
        img = mix(img, aa(np.abs(z - (zmin + 0.11)) * 600 - 1.0) * 0.6, '#6d7278')   # band seam
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.5, pal['grey_d'])   # side seams
        # raglan seams from the armpits to the neck (front and back)
        for c in (0.95, PI - 0.95):
            lim = c + (z - 2.75) * (0.55 if c < 1.5 else -0.55)
            img = mix(img, aa((np.abs(np.abs(az) - lim) - 0.006) * 300) * (z > 2.75) * 0.5, pal['grey_d'])
        # red zip: tape + darker teeth line
        img = mix(img, aa((np.abs(az) - 0.032) * 400), pal['red'])
        img = mix(img, aa((np.abs(az) - 0.009) * 400), pal['red_d'])
        return img
    top.paint = hoodie_paint; P.append(top)
    hb = piece_bvh(top)

    # sleeves: roomy, bloused over ribbed wrist cuffs
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.88, 0.05, extra=lambda t, a: 0.012 + 0.035 * min(1.0, t / 0.55) - 0.02 * min(1.0, max(0.0, (t - 0.74) / 0.14)))
        def sl_paint(U, V, m):
            img = P_solid(pal['grey'])(U, V, m)
            img = _heather(img, U, 7, pal['grey_l'], pal['grey_d'], 0.3)
            return mix(img, aa((np.abs(U - 0.5) - 0.002) * 600) * 0.35, pal['grey_d'])   # under-arm seam
        sl.paint = sl_paint; P.append(sl)
        wc = sleeve('WristCuff_' + s, s, 0.83, 0.975, 0.036, nrows=4, cap=False, th=0.018)
        wc.paint = lambda U, V, m: _ribs(P_solid(pal['grey_d'])(U, V, m), U * 2 * PI, 40, pal['grey'], 0.55)
        P.append(wc)

    # hood opening: a thick rolled rim around the neck, open at the front where the zip starts
    rim = collar('HoodRim', 'fold', h=0.075, flare=0.05, open_front=0.24, col='grey', fold=0.11, lift=0.0, th=0.02)
    P.append(rim)

    # hood lying DOWN on the upper back (rigid on UpperTorso)
    def hood_pt(s, t):
        W = 0.11 + 0.29 * math.sin(min(1.0, t * 1.15) * PI / 2) ** 0.8
        return Vector(((2 * s - 1) * W, 0, 2.52 + t * 0.62))
    def hood_lift(s, t):
        u = (2 * s - 1)
        prof = max(0.0, 1 - u * u) ** 0.6
        return 0.012 + 0.12 * prof * (0.35 + 0.65 * math.sin(min(1.0, t) * PI * 0.62) ) * min(1.0, t * 5 + 0.15)
    hood = _puffy_patch('HoodDown', hb, hood_pt, Vector((0, -1, 0)), hood_lift, 11, 9, th=0.02)
    def hood_paint(U, V, m):
        img = P_solid(pal['grey'])(U, V, m)
        img = _heather(img, U, 3, pal['grey_l'], pal['grey_d'], 0.3)
        img = mix(img, aa((np.abs(U - 0.5) - 0.004) * 500) * 0.6, pal['grey_d'])   # centre seam of the hood
        edge = np.minimum(np.minimum(U, 1 - U), V)
        img = mix(img, aa((edge - 0.07) * 300) * 0.7, pal['grey_d'])                # darker folded edge
        img = mix(img, aa(np.abs(edge - 0.1) * 500 - 0.8) * (np.sin((U + V) * 120) > 0) * 0.6, '#6d7278')  # edge stitching
        return img
    hood.paint = hood_paint
    head_clear(hood, 0.04)
    hood.rigid = True; hood.bone = 'UpperTorso'; P.append(hood)

    # red drawstrings with metal tips, lying on the chest beside the zip
    for sg in (-1, 1):
        pts = []
        for k in range(7):
            f = k / 6
            q = Vector((sg * (0.115 + 0.02 * f), 0, 3.12 - 0.40 * f))
            loc, n = project(hb, q, Vector((0, 1, 0)))
            pts.append(loc + n * 0.024)
        cord = tube_path(f'Drawstring{sg}', pts, 0.014, 'red', n=6, group='Top')
        cord.rigid = True; cord.bone = 'UpperTorso'; P.append(cord)
        end = pts[-1]; dvec = (pts[-1] - pts[-2]).normalized()
        tip = prim_cyl(f'DrawTip{sg}', end, end + dvec * 0.06, 0.019, 0.016, n=8, col='tip', group='Top')
        tip.bone = 'UpperTorso'; P.append(tip)
        # metal eyelet where the cord leaves the hood rim
        loc, n = project(hb, Vector((sg * 0.115, 0, 3.14)), Vector((0, 1, 0)))
        ey = prim_cyl(f'Eyelet{sg}', loc + n * 0.005, loc + n * 0.03, 0.026, n=8, col='metal', group='Top')
        ey.bone = 'UpperTorso'; P.append(ey)

    # zip slider + red pull tab at the top of the zip
    loc, n = project(hb, Vector((0, 0, 3.0)), Vector((0, 1, 0)))
    sl0 = loc + n * 0.02
    P.append(prim_rbox('ZipSlider', sl0, (0.05, 0.03, 0.07), 'metal', group='Top', bevel=0.01))
    P[-1].bone = 'UpperTorso'
    P.append(prim_rbox('ZipPull', sl0 + n * 0.02 + Vector((0, 0, -0.07)), (0.04, 0.018, 0.1), 'red', group='Top', bevel=0.01))
    P[-1].bone = 'UpperTorso'

    # kangaroo pocket, split by the zip: two halves with slanted hand openings on the outside
    for sg in (-1, 1):
        def kp(s, t, sg=sg):
            w = 0.29 - 0.11 * t
            return Vector((sg * (0.045 + s * w), 0, 2.0 + t * 0.36))
        pk = surface_patch(f'Pocket{sg}', hb, kp, Vector((0, 1, 0)), 0.01, 6, 5, th=0.012)
        def pk_paint(U, V, m):
            img = P_solid(pal['grey'])(U, V, m)
            img = _heather(img, U, 21, pal['grey_l'], pal['grey_d'], 0.3)
            img = mix(img, aa((0.86 - U) * 300), pal['grey_d'])                       # welted hand opening
            stitch = (np.sin(U * 90) > 0) * aa(np.abs(V - 0.07) * 500 - 1.0) + (np.sin(V * 60) > 0) * aa(np.abs(U - 0.05) * 500 - 1.0)
            img = mix(img, stitch * 0.7, '#6d7278')
            return img
        pk.paint = pk_paint; pk.rect_key = 'Pocket'
        pk.rigid = True; P.append(pk)

    # ---------------- chunky white sneakers with red laces ----------------
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Sneaker_' + s, s, off=0.05, bulk=0.05, toe=0.06, sole_h=0.09, open_elev=46)
        def sn_paint(U, V, m):
            img = P_solid(pal['white'])(U, V, m)
            z, az = zc(U, V, m)
            st = m['sole_top']
            img = mix(img, aa((z - st) * 600), pal['sole'])                          # chunky midsole
            img = mix(img, aa((z - (m['zmin'] + 0.025)) * 600), pal['sole_d'])       # outsole
            img = mix(img, aa(np.abs(z - st) * 600 - 1.5), pal['red'])                # thin red sole line
            img = mix(img, aa(np.abs(z - (st + 0.09)) * 500 - 0.8) * (np.cos(az) > 0.35) * 0.6, '#c9ccd0')   # toe-cap stitch
            return img
        sh.paint = sn_paint; P.append(sh)
        sb = piece_bvh(sh)
        foot_bone = 'LeftFoot' if s == 'L' else 'RightFoot'
        cx = 0.255 * sg
        def on_shoe(x, y, lift=0.014):
            loc, n = project(sb, Vector((x, y, 0.8)), Vector((0, 0, -1)))
            return loc + n * lift
        ys = (-0.245, -0.29, -0.335, -0.38)
        dx = 0.06
        k = 0
        for y in ys:                                  # straight bars
            pts = [on_shoe(cx + dx * f, y) for f in np.linspace(-1, 1, 5)]
            lc = tube_path(f'Lace_{s}{k}', pts, 0.018, 'red', n=6, group='Feet')
            lc.rigid = True; lc.bone = foot_bone; P.append(lc); k += 1
        for a, b in zip(ys, ys[1:]):                  # criss-cross between bars
            for d0 in (-1, 1):
                pts = [on_shoe(cx + dx * d0 * (1 - 2 * f), a + (b - a) * f, 0.022) for f in np.linspace(0, 1, 4)]
                lc = tube_path(f'Lace_{s}{k}', pts, 0.016, 'red', n=6, group='Feet')
                lc.rigid = True; lc.bone = foot_bone; P.append(lc); k += 1
        # bow on the top bar
        c0 = on_shoe(cx, ys[0], 0.03)
        for d0 in (-1, 1):
            loop = [c0 + Vector((d0 * 0.06 * math.sin(a), 0.03 * math.sin(2 * a) * 0.5, 0.035 * math.sin(a))) for a in np.linspace(0, PI, 7)]
            lc = tube_path(f'LaceBow_{s}{d0}', loop, 0.013, 'red', n=6, group='Feet')
            lc.rigid = True; lc.bone = foot_bone; P.append(lc)
            tail = [c0, c0 + Vector((d0 * 0.03, -0.03, -0.01)), c0 + Vector((d0 * 0.045, -0.06, -0.025))]
            tl = tube_path(f'LaceTail_{s}{d0}', [on_shoe(p.x, p.y, 0.022) if i else p for i, p in enumerate(tail)], 0.012, 'red', n=6, group='Feet')
            tl.rigid = True; tl.bone = foot_bone; P.append(tl)
        # red heel tab
        hl, hn = project(sb, Vector((cx, 0.3, 0.58)), Vector((0, -1, 0)))
        if hl is not None:
            ht = prim_rbox('HeelTab_' + s, hl + hn * 0.012, (0.07, 0.03, 0.09), 'red', group='Feet', bevel=0.01)
            ht.bone = foot_bone; P.append(ht)
    return P, pal
