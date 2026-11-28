from o04 import *
NUM, NAME, RARITY, MAXD = '30', 'Skater_Kid', 'Rare', 0.32

# ---------------------------------------------------------------- helpers (local to this skin)
def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

_TONGUES = ((-0.64, 0.60, 0.30, -0.30), (-0.32, 0.84, 0.30, -0.16), (0.02, 1.0, 0.33, 0.12),
            (0.36, 0.80, 0.30, 0.22), (0.68, 0.56, 0.28, 0.30))

def _flame_d(X, Z, cx, z0, W, H):
    """signed distance-ish (units, <0 inside) of a 5-tongue flame: base centre (cx, z0), half width W, height H"""
    u = (X - cx) / W; v = (Z - z0) / H
    d = (np.sqrt((u / 0.86) ** 2 + ((v - 0.2) / 0.25) ** 2) - 1) * 0.25 * H          # round base blob
    for uk, hk, wk, lean in _TONGUES:
        t = v / hk
        tc = np.clip(t, 0, 1)
        prof = wk * (1 - tc) ** 0.75
        dk = (np.abs(u - uk - lean * tc ** 2) - prof) * W
        dk = np.where(t > 1, np.maximum((t - 1) * hk * H, np.abs(u - uk - lean) * W), dk)
        dk = np.where(t < 0.1, np.maximum(dk, 0.02), dk)
        d = np.minimum(d, dk)
    return d

def _flame(img, X, Z, cx, z0, W, H, pal, px=170.0, outline=True):
    if outline: img = mix(img, aa((_flame_d(X, Z, cx, z0, W, H) - 0.014) * px), pal['ink'])
    img = mix(img, aa(_flame_d(X, Z, cx, z0, W, H) * px), pal['red'])
    img = mix(img, aa(_flame_d(X, Z, cx, z0 + 0.03 * H / 0.6, W * 0.62, H * 0.7) * px), pal['teal'])
    img = mix(img, aa(_flame_d(X, Z, cx, z0 + 0.05 * H / 0.6, W * 0.3, H * 0.4) * px), pal['white'])
    return img

def _strap_over_shoulder(name, xc, bv, width=0.08, lift=0.02, phis=None):
    """flat strap in the plane x = xc running from the chest front over the shoulder down the back, laid on bv"""
    phis = phis or list(np.linspace(-22, 228, 26))
    c = Vector((xc, 0.0, 2.78))
    rows = []; hints = []
    for ph in phis:
        r = math.radians(ph)
        d = Vector((0, -math.cos(r), math.sin(r)))
        row = []; hh = []
        for dx in (-width / 2, 0.0, width / 2):
            o = c + Vector((dx, 0, 0))
            loc, n = project(bv, o + d * 1.6, -d)
            if loc is None: loc, n = o + d * 0.5, d
            row.append(loc + d * lift); hh.append(d)
        rows.append(row); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col='strap', hints=hints, group='Top')
    thicken(pc, 0.014)
    pc.region = 'torso'; pc.skirt = False; pc.meta['patch'] = True
    return pc, rows

def _link(name, a, b, perp, half, wid, r, col):
    m = (a + b) / 2; e = (b - a).normalized()
    pts = [m + e * math.cos(t) * half + perp * math.sin(t) * wid for t in np.linspace(0, 2 * PI, 11)]
    return tube_path(name, pts, r, col, n=4, group='Extras', caps=False)


def build():
    pal = {'white': '#f2f2f2', 'white_d': '#d6d9dc', 'grey': '#5e6b7a', 'grey_d': '#4a5562', 'grey_l': '#73808f',
           'red': '#e23b3b', 'red_d': '#b82a2a', 'teal': '#22b8cf', 'teal_d': '#178a9c', 'ink': '#1d2a33',
           'strap': '#202327', 'silver': '#c3c8ce', 'chain': '#b5bac1', 'wallet': '#2a2d33', 'sole': '#f2f2f2',
           'wheel': '#22b8cf', 'grip': '#1b1c1f', 'maple': '#d9b483'}
    P = []

    # ---------------------------------------------------------------- baggy cargo pants (lower layer first)
    pt = pants('Cargo', 2.2, 0.72, 0.06, hip_off=0.07, leg_extra=lambda z, a: 0.035 + 0.055 * max(0, 1.55 - z), nseg=16)
    def ppaint(U, V, m):
        img = P_solid(pal['grey'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['grey_d'])        # side seams
        if m.get('kind') == 'leg':
            img = mix(img, aa((z - (m['zmin'] + 0.06)) * 500), pal['grey_d'])                      # hem band
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.075)) * 600 - 1.0), pal['grey_l'])
            img = mix(img, aa(np.abs(z - 1.08) * 600 - 1.2) * (np.cos(az) > 0.55), pal['grey_d'])  # knee seam
            img = mix(img, aa(np.abs(z - 1.18) * 600 - 1.0) * (np.cos(az) > 0.6), pal['grey_l'])
        return img
    for p in pt: p.paint = ppaint
    P += pt
    for s, sg in (('L', 1), ('R', -1)):
        lb = piece_bvh(pt[1] if s == 'L' else pt[2])
        bone = 'LeftUpperLeg' if s == 'L' else 'RightUpperLeg'
        cp = surface_patch('CargoPocket_' + s, lb, lambda u, t, sg=sg: Vector((0, -0.13 + u * 0.26, 1.1 + t * 0.28)), Vector((-sg, 0, 0)), 0.012, 5, 5, col='grey_d', th=0.016, group='Bottom')
        cp.rigid = True; P.append(cp)
        cf = surface_patch('CargoFlap_' + s, lb, lambda u, t, sg=sg: Vector((0, -0.145 + u * 0.29, 1.36 + t * 0.09)), Vector((-sg, 0, 0)), 0.032, 5, 2, col='grey_l', th=0.016, group='Bottom')
        cf.rigid = True; P.append(cf)
        loc, n = project(lb, Vector((0, 0.0, 1.39)), Vector((-sg, 0, 0)))
        sn = prim_cyl('CargoSnap_' + s, loc + n * 0.03, loc + n * 0.06, 0.026, n=8, col='teal')
        sn.bone = bone; P.append(sn)

    # ---------------------------------------------------------------- chain wallet (right hip, rigid on the right thigh)
    hipR = piece_bvh(pt[0], pt[2])
    def on_leg(az, z, gap):
        c = leg_point('R', min(z, 1.9)); d = Vector((math.sin(az), -math.cos(az), 0))
        loc, n = project(hipR, Vector((c.x, c.y, z)) + d * 1.2, -d)
        if loc is None: loc = Vector((c.x, c.y, z)) + d * 0.3
        return loc + d * gap, d
    path = []
    for t in np.linspace(0, 1, 40):
        az = -0.8 - 1.95 * t
        z = 1.95 + (1.9 - 1.95) * t - 0.42 * math.sin(PI * t)
        path.append(on_leg(az, z, 0.04)[0])
    path = polyline_resample(path, 22)
    chain = None
    for k in range(len(path) - 1):
        a, b = path[k], path[k + 1]
        e = (b - a).normalized()
        nrm = Vector((a.x - leg_point('R', a.z).x, a.y - leg_point('R', a.z).y, 0)).normalized()
        perp = (nrm - e * nrm.dot(e)).normalized()
        if k % 2: perp = e.cross(perp).normalized()
        lk = _link(f'Link{k}', a - e * 0.012, b + e * 0.012, perp, None or ((b - a).length / 2 + 0.012), 0.022, 0.0085, 'chain')
        chain = lk if chain is None else chain.merge(lk)
    chain.name = 'WalletChain'; chain.rect_key = 'WalletChain'; chain.rigid = True; chain.bone = 'RightUpperLeg'
    P.append(chain)
    wl, wn = on_leg(-2.85, 1.8, 0.0)
    wallet = prim_rbox('Wallet', wl + wn * 0.012, (0.17, 0.05, 0.22), 'wallet', rot=Matrix.Rotation(math.atan2(wn.x, -wn.y) - PI, 3, 'Z'), group='Extras')
    wallet.bone = 'RightUpperLeg'; P.append(wallet)
    stripe = prim_box('WalletStitch', wl + wn * 0.04 + Vector((0, 0, 0.06)), (0.15, 0.012, 0.025), 'red', rot=Matrix.Rotation(math.atan2(wn.x, -wn.y) - PI, 3, 'Z'), group='Extras')
    stripe.bone = 'RightUpperLeg'; P.append(stripe)
    ring = _link('ChainRing', path[-1] + Vector((0, 0, -0.03)), path[-1] + Vector((0, 0, 0.03)), wn, 0.035, 0.035, 0.01, 'silver')
    ring.rigid = True; ring.bone = 'RightUpperLeg'; P.append(ring)

    # ---------------------------------------------------------------- oversized graphic tee (hangs over the pants)
    tee = torso_shell('Tee', 1.9, 0.06, nseg=32, extra=lambda z, a: 0.035 + 0.025 * max(0, 2.3 - z), th=0.022, hang=2.3,
                      over=pt + [chain, wallet, ring])
    def teep(U, V, m):
        img = P_solid(pal['white'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.6, pal['white_d'])       # side seams
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.06)) * 600 - 1.0), pal['white_d'])            # hem stitch
        X = az * 0.52
        img = _flame(img, X, z, 0.0, 2.2, 0.3, 0.66, pal)                                           # big chest logo
        # little teal flame tag on the hem (wearer's left)
        img = mix(img, aa((np.maximum(np.abs(az - 0.75) - 0.06, np.abs(z - (m['zmin'] + 0.12)) - 0.035)) * 500), pal['teal'])
        return img
    tee.paint = teep; P.append(tee)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.42, 0.06, extra=lambda t, a: 0.03 + 0.07 * t / 0.42)
        def slp(U, V, m):
            img = P_solid(pal['white'])(U, V, m)
            img = mix(img, aa(np.maximum(0.80 - V, V - 0.87) * 400), pal['teal'])
            img = mix(img, aa(np.maximum(0.90 - V, V - 0.93) * 400), pal['red'])
            return img
        sl.paint = slp; P.append(sl)
    col = collar('Collar', 'stand', h=0.035, flare=0.03, col='red', th=0.018)
    P.append(col)

    # ---------------------------------------------------------------- shoulder straps holding the board
    tb = piece_bvh(tee, col)
    straps = []
    for sg in (-1, 1):
        st, rows = _strap_over_shoulder(f'Strap{sg}', sg * 0.335, tb)
        P.append(st); straps.append(st)
        f0 = rows[0][1]
        bk = prim_rbox(f'StrapClip{sg}', f0 + Vector((0, -0.02, -0.02)), (0.1, 0.035, 0.08), 'teal', group='Top')
        bk.bone = 'UpperTorso'; P.append(bk)

    # ---------------------------------------------------------------- skateboard on the back (rigid, UpperTorso)
    Lb, Wb, Tb = 1.16, 0.42, 0.034
    zc0 = 2.7
    allb = piece_bvh(tee, col, *straps)
    def deck_rows(y0):
        rows = []; hints = []; ss = list(np.linspace(-Lb / 2 + 0.004, Lb / 2 - 0.004, 19))
        for s in ss:
            e = abs(s) - (Lb / 2 - Wb / 2)
            hw = Wb / 2 * math.sqrt(max(0.0, 1 - (e / (Wb / 2)) ** 2)) if e > 0 else Wb / 2
            hw = max(hw, 0.03)
            kick = -0.07 * max(0.0, (abs(s) - (Lb / 2 - 0.25)) / 0.25) ** 1.8
            c = Vector((0, y0 + kick, zc0 + s))
            ring = []; hh = []
            for j in range(12):
                a = 2 * PI * j / 12 + PI / 12
                sp = lambda v, p=0.3: math.copysign(abs(v) ** p, v)
                ring.append(c + Vector((-hw * sp(math.cos(a)), Tb / 2 * sp(math.sin(a)), 0)))
                hh.append(Vector((-math.cos(a), math.sin(a), 0)))
            rows.append(ring); hints.append(hh)
        return rows, hints, ss
    rows, hints, ss = deck_rows(0.0)
    need = -9.0
    for r in rows:
        for p in r:
            h = allb.ray_cast(Vector((p.x, 2.0, p.z)), Vector((0, -1, 0)), 3.0)
            hb = B.bvh['all'].ray_cast(Vector((p.x, 2.0, p.z)), Vector((0, -1, 0)), 3.0)
            yy = max(h[0].y if h[0] else -9, hb[0].y if hb[0] else -9)
            need = max(need, yy + 0.02 - p.y)
    y0 = need
    rows, hints, ss = deck_rows(y0)
    vv = [(s + Lb / 2) / Lb for s in ss]
    deck = grid_piece('Deck', rows, True, v_vals=vv, hints=hints, group='Extras',
                      cap_start=Vector((0, rows[0][0].y * 0 + sum(p.y for p in rows[0]) / 12, zc0 - Lb / 2)),
                      cap_end=Vector((0, sum(p.y for p in rows[-1]) / 12, zc0 + Lb / 2)))
    deck.meta['rect'] = (128, 320)
    def deckp(U, V, m):
        img = P_solid(pal['red'])(U, V, m)
        sa = np.sin(2 * PI * U + PI / 12)
        ca = np.cos(2 * PI * U + PI / 12)
        X = -np.sign(ca) * np.abs(ca) ** 0.3 * Wb / 2      # across the deck
        Zl = V * Lb
        img = _flame(img, X, Zl, 0.0, 0.05, 0.19, 0.62, pal, px=240.0, outline=False)
        r = np.sqrt(X ** 2 + (Zl - 0.93) ** 2)
        img = mix(img, aa((r - 0.075) * 300), pal['white'])
        img = mix(img, aa((np.abs(r - 0.05) - 0.012) * 300), pal['teal'])
        img = mix(img, aa((sa - 0.3) * 40), pal['maple'])   # edges
        img = mix(img, aa((sa + 0.3) * 40), pal['grip'])    # grip tape side (faces the back)
        return img
    deck.paint = deckp; deck.rigid = True; deck.bone = 'UpperTorso'
    P.append(deck)
    yo = y0 + Tb / 2                                         # deck outer (wheel side) face
    hw_ = []
    trucks = None
    for k, s in enumerate((-Lb / 2 + 0.24, Lb / 2 - 0.24)):
        z = zc0 + s
        parts = [prim_box(f'Base{k}', Vector((0, yo + 0.012, z)), (0.13, 0.024, 0.1), 'silver'),
                 prim_box(f'King{k}', Vector((0, yo + 0.04, z)), (0.06, 0.04, 0.06), 'silver'),
                 prim_cyl(f'Hanger{k}', Vector((-0.2, yo + 0.065, z)), Vector((0.2, yo + 0.065, z)), 0.022, n=8, col='silver')]
        for sx in (-1, 1):
            parts.append(prim_cyl(f'Wheel{k}{sx}', Vector((sx * 0.155, yo + 0.065, z)), Vector((sx * 0.215, yo + 0.065, z)), 0.056, n=12, col='wheel'))
            parts.append(prim_cyl(f'Hub{k}{sx}', Vector((sx * 0.214, yo + 0.065, z)), Vector((sx * 0.222, yo + 0.065, z)), 0.026, n=8, col='white'))
        for q in parts:
            trucks = q if trucks is None else trucks.merge(q)
    trucks.name = 'Trucks'; trucks.rect_key = 'Trucks'; trucks.rigid = True; trucks.bone = 'UpperTorso'
    P.append(trucks)
    # board straps: across the deck face (between the trucks), down to the shoulder straps
    for k, zb in enumerate((zc0 + 0.13, zc0 - 0.25)):
        pts = []
        for x in np.linspace(-0.37, 0.37, 15):
            if abs(x) <= Wb / 2 + 0.005:
                y = yo + 0.012
            else:
                h = allb.ray_cast(Vector((x, 2.0, zb)), Vector((0, -1, 0)), 3.0)
                ys = (h[0].y + 0.012) if h[0] else yo
                f = min(1.0, (abs(x) - Wb / 2) / 0.12)
                y = (yo + 0.012) * (1 - f) + ys * f
            pts.append(Vector((x, y, zb)))
        rws = [[p + Vector((0, 0, -0.04)) for p in pts], [p + Vector((0, 0, 0.04)) for p in pts]]
        band_ = grid_piece(f'BoardStrap{k}', [list(r) for r in zip(*rws)], closed=False, col='strap',
                           hints=[[Vector((0, 1, 0))] * 2 for _ in pts], group='Extras')
        thicken(band_, 0.012)
        band_.rigid = True; band_.bone = 'UpperTorso'; P.append(band_)
        bp = prim_rbox(f'BoardBuckle{k}', Vector((0.12, yo + 0.03, zb)), (0.08, 0.03, 0.1), 'teal')
        bp.bone = 'UpperTorso'; P.append(bp)
    for q in (deck, trucks): head_clear(q, 0.04)

    # ---------------------------------------------------------------- chunky red high-tops
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Shoe_' + s, s, off=0.05, bulk=0.045, toe=0.05, sole_h=0.08, open_elev=44)
        def shp(U, V, m):
            img = P_solid(pal['red'])(U, V, m); z, az = zc(U, V, m)
            st = m['sole_top']
            img = mix(img, aa((z - st) * 600), pal['white'])
            img = mix(img, aa(np.abs(z - (st - 0.03)) * 600 - 1.4), pal['teal'])
            img = mix(img, aa(np.maximum(z - st - 0.07, (0.72 - np.cos(az)) * 0.4) * 600), pal['white'])   # toe cap
            img = mix(img, aa(np.abs(z - (st + 0.075)) * 600 - 0.8) * (np.cos(az) > 0.72), pal['red_d'])
            return img
        sh.paint = shp; P.append(sh)
        ht = _shin(leg_tube('HighTop_' + s, s, 0.84, 0.47, 0.082, nseg=16, group='Feet', extra=lambda z, a: 0.006))
        az0 = sg * PI / 2
        def htp(U, V, m, az0=az0):
            img = P_solid(pal['red'])(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa((np.abs(az) - 0.22) * 300), pal['red_d'])                              # tongue
            for zz in np.arange(0.53, 0.80, 0.06):
                img = mix(img, aa(np.abs(z - zz) * 600 - 1.6) * aa((np.abs(az) - 0.2) * 300), pal['white'])   # laces
            img = mix(img, aa((m['zmax'] - 0.035 - z) * 600), pal['white'])                          # padded rim
            dx = (az - az0) * 0.25; r = np.sqrt(dx ** 2 + (z - 0.64) ** 2)
            img = mix(img, aa((r - 0.07) * 600), pal['white'])                                        # ankle patch
            th_ = np.arctan2(z - 0.64, dx); k = 0.5 + 0.5 * np.cos(5 * th_ - PI / 2)
            img = mix(img, aa((r - 0.055 * (0.45 + 0.55 * k ** 3)) * 600), pal['teal'])
            return img
        ht.paint = htp; ht.rect_key = 'HighTop_' + s; P.append(ht)
    return P, pal
