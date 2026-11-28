from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '31', 'Jungle_Explorer', 'Rare', 0.32


def _shin31(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _strap(name, bvh, pts, w, lift=0.016, th=0.014, col=None, n=18, group='Top'):
    """Flat webbing strap lying on a torso garment: path points are snapped to the garment surface (nearest point),
    lifted along its normal and given width w. Weighted like the cloth under it (torso transfer, patch)."""
    pts = smooth_line(polyline_resample(pts, n), 2)
    hits = []
    for p in pts:   # cast from outside toward the torso axis: always lands on the OUTER shell
        c = Vector((0, 0, min(max(p.z, 2.3), 2.75)))
        dv = (p - c).normalized()
        loc, nor, fi, d = bvh.ray_cast(c + dv * 2.0, -dv, 2.0)
        if loc is None: loc, nor, fi, d = bvh.find_nearest(p)
        if nor.dot(dv) < 0: nor = -nor
        hits.append((loc, nor))
    rows = []; hints = []
    for i, (loc, nor) in enumerate(hits):
        t = hits[min(i + 1, n - 1)][0] - hits[max(i - 1, 0)][0]
        sd = t.cross(nor).normalized()
        rows.append([loc + nor * lift + sd * (k * w / 2) for k in (-1, 0, 1)]); hints.append([nor] * 3)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group)
    thicken(pc, th)
    pc.region = 'torso'; pc.skirt = False; pc.meta['patch'] = True; pc.rigid = True
    return pc


def _rot_from_normal(nor):
    nor = Vector((nor.x, nor.y, nor.z)).normalized()
    up = Vector((0, 0, 1)); up = (up - nor * up.dot(nor)).normalized()
    sd = up.cross(nor).normalized()
    return Matrix((sd, -nor, up)).transposed()     # local x -> side, local y -> into the surface, local z -> up


def build():
    pal = {'khaki': '#c8b27a', 'khaki_d': '#b49a62', 'khaki_dd': '#9a8150', 'pocket': '#bea86f',
           'boot': '#6b4428', 'boot_d': '#4f3019', 'sole': '#2a2320', 'lace': '#d8c79a',
           'green': '#3c6e47', 'green_d': '#2d5436', 'green_l': '#56885f',
           'sock': '#e8e2d0', 'sock_d': '#d3ccb6', 'btn': '#5a4630', 'brass': '#c49a3c',
           'black': '#1f1f22', 'lens': '#6fa3bf', 'leather': '#5a3a22', 'roll': '#b49a62', 'roll_d': '#8f7748',
           'metal': '#8d9488'}
    P = []

    # ---------------- shorts (built first: the shirt hangs over them) ----------------
    pt = pants('Shorts', 2.18, 1.42, 0.045, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.06 * max(0, (1.85 - z)), nseg=16)

    def shorts_paint(U, V, m):
        img = P_solid(pal['khaki_d'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['khaki_dd'])     # side seams
        if m.get('kind') == 'hip':
            img = mix(img, aa((np.abs(az) - 0.008) * 400) * 0.8, pal['khaki_dd'])                 # fly seam
        return img
    for p in pt: p.paint = shorts_paint
    P += pt
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        cf = leg_tube('ShortsCuff_' + s, s, 1.52, 1.40, 0.118, nrows=3, th=0.02, col='khaki_d')
        cf.meta.update(w_axis=W_AXIS, w_xmin=W_XMIN)       # deform exactly like the trouser leg under it
        P.append(cf)
        lb = piece_bvh(pt[1] if s == 'L' else pt[2])
        cp = surface_patch('Cargo_' + s, lb, lambda u, t, sg=sg: Vector((0, -0.11 + u * 0.22, 1.56 + t * 0.17)), Vector((-sg, 0, 0)),
                           0.012, 4, 4, col='khaki_dd', th=0.014, group='Bottom')
        cp.rigid = True; P.append(cp)
        cfl = surface_patch('CargoFlap_' + s, lb, lambda u, t, sg=sg: Vector((0, -0.12 + u * 0.24, 1.72 + t * 0.07)), Vector((-sg, 0, 0)),
                            0.028, 4, 2, col='khaki_d', th=0.014, group='Bottom')
        cfl.rigid = True; P.append(cfl)

    # ---------------- safari shirt (untucked, hangs over the shorts) ----------------
    shirt = torso_shell('Shirt', 1.95, 0.055, nseg=32, extra=lambda z, a: 0.025 + 0.04 * max(0, 2.2 - z), th=0.022, hang=2.3, over=pt)

    def shirt_paint(U, V, m):
        img = P_solid(pal['khaki'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(az) - 0.075) * 300) * 0.35, pal['khaki_d'])                     # placket band
        img = mix(img, aa(np.abs(np.abs(az) - 0.075) * 400 - 0.8), pal['khaki_dd'])              # placket stitching
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.6, pal['khaki_d'])   # side seams
        img = mix(img, aa(np.abs(z - 2.97) * 500 - 1.0) * (np.abs(az) > 2.0), pal['khaki_dd'])   # back yoke seam
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.05)) * 500 - 0.8), pal['khaki_dd'])          # hem stitching
        return img
    shirt.paint = shirt_paint; P.append(shirt)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.38, 0.05, extra=lambda t, a: 0.02 * t / 0.38)
        sl.paint = lambda U, V, m: mix(P_solid(pal['khaki'])(U, V, m), aa((V - 0.12) * -300) * 0.5, pal['khaki_d'])
        P.append(sl)
        P.append(sleeve('SleeveRoll_' + s, s, 0.33, 0.41, 0.088, nrows=3, cap=False, th=0.022, col='khaki_d', extra=lambda t, a: 0.008))
    P.append(collar('Collar', 'fold', h=0.07, flare=0.04, open_front=0.4, col='khaki', fold=0.09))
    sb = piece_bvh(shirt)

    # chest pockets with button flaps
    for sg in (-1, 1):
        pk = surface_patch(f'ChestPocket{sg}', sb, lambda u, t, sg=sg: Vector((sg * (0.19 + u * 0.17), 0, 2.56 + t * 0.22)), Vector((0, 1, 0)),
                           0.011, 5, 4, col='pocket', th=0.012)
        pk.rigid = True; P.append(pk)
        pf = surface_patch(f'ChestFlap{sg}', sb, lambda u, t, sg=sg: Vector((sg * (0.18 + u * 0.19), 0, 2.76 + t * 0.085)), Vector((0, 1, 0)),
                           0.027, 5, 2, col='khaki_d', th=0.012)
        pf.rigid = True; P.append(pf)
        loc, n = project(piece_bvh(pf), Vector((sg * 0.275, 0, 2.785)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'PocketBtn{sg}', loc, loc + n * 0.016, 0.022, n=8, col='btn', group='Top'))
    # placket buttons (the middle of the chest is covered by the binoculars)
    for i, z in enumerate((3.0, 2.82, 2.2, 2.06)):
        loc, n = project(sb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.018, 0.024, n=8, col='btn', group='Top'))

    # ---------------- backpack shoulder straps (green webbing) + epaulettes over them ----------------
    straps = []
    for sg in (-1, 1):
        path = [Vector((sg * 0.43, -0.45, 2.36)), Vector((sg * 0.42, -0.45, 2.6)), Vector((sg * 0.41, -0.45, 2.85)),
                Vector((sg * 0.41, -0.3, 3.08)), Vector((sg * 0.42, 0.0, 3.22)), Vector((sg * 0.39, 0.25, 3.12)),
                Vector((sg * 0.31, 0.42, 2.98)), Vector((sg * 0.25, 0.48, 2.86))]
        st = _strap(f'PackStrap{sg}', sb, path, 0.065, col='green_d', n=22)
        head_clear(st, 0.03)
        straps.append(st); P.append(st)
        # adjuster buckle + strap tail at the lower front end
        h = st.verts[1]; loc, nor, fi, d = sb.find_nearest(h)
        c = Vector((0, 0, 2.4)); nor = nor if nor.dot(loc - c) > 0 else -nor
        R = _rot_from_normal(nor)
        bk = prim_box(f'StrapBuckle{sg}', loc + nor * 0.035 + Vector((0, 0, 0.05)), (0.085, 0.022, 0.05), 'brass', rot=R, group='Top')
        bk.bone = 'UpperTorso'; P.append(bk)
    stb = piece_bvh(shirt, *straps)
    for sg in (-1, 1):
        ep = surface_patch(f'Epaulette{sg}', stb, lambda u, t, sg=sg: Vector((sg * (0.35 + u * 0.16), -0.07 + t * 0.14, 3.6)), Vector((0, 0, -1)),
                           0.014, 9, 3, col='khaki_dd', th=0.018)
        ep.rigid = True; head_clear(ep, 0.03); P.append(ep)
        loc, n = project(piece_bvh(ep), Vector((sg * 0.385, 0, 3.6)), Vector((0, 0, -1)))
        b = prim_cyl(f'EpauletteBtn{sg}', loc, loc + n * 0.016, 0.022, n=8, col='brass', group='Top')
        head_clear(b, 0.03); P.append(b)

    # ---------------- binoculars on a neck strap ----------------
    fy = min(project(sb, Vector((x, 0, z)), Vector((0, 1, 0)))[0].y for x in (-0.13, 0.0, 0.13) for z in (2.3, 2.42, 2.55))
    r = 0.056; by = fy - r - 0.012
    for sg in (-1, 1):
        x = sg * 0.07
        P.append(prim_cyl(f'BinoBarrel{sg}', Vector((x, by, 2.36)), Vector((x, by, 2.56)), r, n=12, col='green_d'))
        P.append(prim_cyl(f'BinoRubber{sg}', Vector((x, by, 2.30)), Vector((x, by, 2.38)), r + 0.008, n=12, col='black'))
        P.append(prim_cyl(f'BinoLens{sg}', Vector((x, by, 2.295)), Vector((x, by, 2.30)), r - 0.012, n=12, col='lens'))
        P.append(prim_cyl(f'BinoEyecup{sg}', Vector((x, by, 2.56)), Vector((x, by, 2.62)), 0.038, n=10, col='black'))
        P.append(prim_box(f'BinoLug{sg}', Vector((sg * 0.128, by + 0.01, 2.53)), (0.02, 0.03, 0.04), 'black'))
    P.append(prim_box('BinoBridge', Vector((0, by, 2.5)), (0.05, 0.06, 0.12), 'black'))
    P.append(prim_cyl('BinoFocus', Vector((-0.022, by - 0.005, 2.585)), Vector((0.022, by - 0.005, 2.585)), 0.022, n=10, col='green_l'))
    for p in P:
        if p.name.startswith('Bino'): p.bone = 'UpperTorso'; p.group = 'Top'
    for sg in (-1, 1):
        path = [Vector((sg * 0.115, -0.45, 2.5)), Vector((sg * 0.13, -0.45, 2.7)), Vector((sg * 0.145, -0.42, 2.88)),
                Vector((sg * 0.17, -0.34, 3.05)), Vector((sg * 0.19, -0.24, 3.14))]
        bs = _strap(f'BinoStrap{sg}', sb, path, 0.034, lift=0.012, th=0.012, col='leather', n=12)
        head_clear(bs, 0.03); P.append(bs)

    # ---------------- big canvas backpack + bedroll (rigid, UpperTorso) ----------------
    back = [p for p in shirt.verts[:shirt.meta['n_outer_verts']] if abs(p.x) < 0.36 and 2.22 < p.z < 3.04]
    yf = max(p.y for p in back) + 0.012
    for st in straps:
        yf = max(yf, max((p.y for p in st.verts if abs(p.x) < 0.36 and 2.22 < p.z < 3.04), default=yf) + 0.002)
    D = 0.34; yc = yf + D / 2; zc0, H = 2.62, 0.80
    pack = []
    pack.append(prim_rbox('Pack', Vector((0, yc, zc0)), (0.66, D, H), 'green'))
    pack.append(prim_rbox('PackLid', Vector((0, yc + 0.01, zc0 + H / 2 + 0.01)), (0.68, D + 0.04, 0.14), 'green_d'))
    pack.append(prim_rbox('PackPocket', Vector((0, yc + D / 2 + 0.04, 2.47)), (0.46, 0.11, 0.34), 'green_d'))
    pack.append(prim_box('PackPocketFlap', Vector((0, yc + D / 2 + 0.085, 2.62)), (0.48, 0.035, 0.1), 'green'))
    for sx in (-1, 1):
        pack.append(prim_box(f'PackBelt{sx}', Vector((sx * 0.13, yc + D / 2 + 0.105, 2.52)), (0.045, 0.012, 0.2), 'leather'))
        pack.append(prim_box(f'PackBuckle{sx}', Vector((sx * 0.13, yc + D / 2 + 0.11, 2.47)), (0.06, 0.012, 0.045), 'brass'))
        pack.append(prim_box(f'LidStrap{sx}', Vector((sx * 0.2, yc + D / 2 + 0.03, zc0 + H / 2 - 0.08)), (0.045, 0.012, 0.22), 'leather'))
    # canteen on the left side, side pocket on the right
    pack.append(prim_cyl('Canteen', Vector((0.325, yc, 2.48)), Vector((0.41, yc, 2.48)), 0.13, n=16, col='metal'))
    pack.append(prim_cyl('CanteenCover', Vector((0.33, yc, 2.48)), Vector((0.415, yc, 2.48)), 0.105, n=16, col='khaki_dd'))
    pack.append(prim_cyl('CanteenCap', Vector((0.37, yc, 2.6)), Vector((0.37, yc, 2.66)), 0.03, n=8, col='black'))
    pack.append(prim_rbox('SidePocket', Vector((-0.37, yc, 2.45)), (0.1, 0.22, 0.3), 'green_d'))
    # bedroll strapped on top of the lid
    rz = zc0 + H / 2 + 0.08 + 0.12
    pack.append(prim_cyl('Bedroll', Vector((-0.4, yc, rz)), Vector((0.4, yc, rz)), 0.12, n=16, col='sock'))
    for sx in (-1, 1):
        pack.append(prim_cyl(f'BedrollEnd{sx}', Vector((sx * 0.4, yc, rz)), Vector((sx * 0.405, yc, rz)), 0.09, n=14, col='sock_d'))
        pack.append(prim_cyl(f'BedrollCore{sx}', Vector((sx * 0.405, yc, rz)), Vector((sx * 0.41, yc, rz)), 0.045, n=10, col='green'))
        pack.append(prim_cyl(f'BedrollStripe{sx}', Vector((sx * 0.31 - 0.018, yc, rz)), Vector((sx * 0.31 + 0.018, yc, rz)), 0.123, n=16, col='green'))
        pack.append(prim_cyl(f'BedrollTie{sx}', Vector((sx * 0.17 - 0.025, yc, rz)), Vector((sx * 0.17 + 0.025, yc, rz)), 0.13, n=16, col='leather'))
    for p in pack:
        p.bone = 'UpperTorso'; p.group = 'Extras'; head_clear(p, 0.04)
    P += pack

    # ---------------- bare knees, knee-high socks, hiking boots ----------------
    def sock_paint(U, V, m):
        img = P_solid(pal['sock'])(U, V, m)
        z, az = zc(U, V, m)
        return mix(img, (0.5 + 0.5 * np.cos(az * 28)) * 0.35, pal['sock_d'])       # ribbing

    def cuff_paint(U, V, m):
        img = sock_paint(U, V, m)
        z, az = zc(U, V, m)
        for zz in (1.06, 1.1):
            img = mix(img, aa(np.abs(z - zz) * 500 - 5), pal['green'])
        return img

    def boot_paint(U, V, m):
        img = P_solid(pal['boot'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.03)) * 600 - 1.0), pal['boot_d'])   # welt stitching
        img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
        img = mix(img, aa((z - (m['sole_top'] - 0.03)) * 600), '#1a1513')                  # lug tread
        return img

    def shaft_paint(U, V, m):
        img = P_solid(pal['boot'])(U, V, m)
        z, az = zc(U, V, m)
        u = az / 0.26
        img = mix(img, aa((np.abs(u) - 1.0) * 60) * 0.7, pal['boot_d'])                    # tongue
        w = ((z / 0.06) % 1.0) * 2 - 1
        lace = aa((np.abs(np.abs(u) - np.abs(w)) - 0.16) * 40) * (np.abs(u) < 1.0)
        img = mix(img, lace, pal['lace'])
        for sx in (-1, 1):                                                                   # brass eyelets
            ey = np.hypot((az - sx * 0.3) * 0.5, ((z / 0.06 + 0.5) % 1.0 - 0.5) * 0.06)
            img = mix(img, aa((ey - 0.012) * 900), pal['brass'])
        return img

    for s in 'LR':
        P.append(skin_leg(s, 1.5, 0.95))
        sk = leg_tube('Sock_' + s, s, 1.08, 0.62, 0.03, nseg=16, th=0.012)
        sk.paint = sock_paint; sk.rect_key = 'Sock'; P.append(sk)
        sc = leg_tube('SockCuff_' + s, s, 1.14, 1.02, 0.052, nseg=16, nrows=3, th=0.016)
        sc.paint = cuff_paint; sc.rect_key = 'SockCuff'; P.append(sc)
        sh = shoe('Boot_' + s, s, off=0.05, bulk=0.035, toe=0.035, sole_h=0.065)
        sh.paint = boot_paint; sh.rect_key = 'Boot'; P.append(sh)
        shaft = _shin31(leg_tube('BootShaft_' + s, s, 0.76, 0.47, 0.08, nseg=16, group='Feet', extra=lambda z, a: 0.01))
        shaft.paint = shaft_paint; shaft.rect_key = 'BootShaft'; P.append(shaft)
        P.append(_shin31(leg_tube('BootCollar_' + s, s, 0.81, 0.72, 0.115, nseg=16, nrows=3, group='Feet', col='boot_d')))
    return P, pal
