from o02 import *

def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def RF_SLIT_TOP():
    import rigfix as _RF
    return _RF.DEFAULT_RAMPS.get('slit_top', 1.95)

def construction_hero():
    pal = {'grey': '#8d9096', 'grey_d': '#6f7277', 'orange': '#f47a1a', 'trim': '#5a3a22', 'beige': '#d6c49b', 'beige_d': '#b8a679',
           'brown': '#6a4326', 'brown_d': '#3e2614', 'silver': '#b9bcc0', 'boot': '#9ea2a6', 'boot_d': '#7b7f84', 'sole': '#2c3038',
           'wood': '#a0703c', 'metal': '#7d8288', 'red': '#c0392b', 'yellow': '#f2e01c'}
    P = []
    tee = torso_shell('Tee', 2.1, 0.03, nseg=32, th=0.015, col='grey'); P.append(tee)
    for s in 'LR':
        P.append(sleeve('TeeSleeve_' + s, s, 0.0, 0.2, 0.035, col='grey', extra=lambda t, a: 0.01))
    def vkeep(i, j, zc_, az):
        return not (zc_ > 2.78 and abs(az) < 0.05 + 0.4 * (zc_ - 2.78) / 0.4)
    pt = pants('Pants', 2.22, 0.5, 0.04, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.045 * max(0, 1.4 - z))
    vest = torso_shell('Vest', 2.05, 0.07, nseg=36, extra=lambda z, a: 0.01, keep=vkeep, th=0.022, hang=2.3, over=pt + [tee])
    def vpaint(U, V, m):
        img = P_solid(pal['orange'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(az) - 0.008) * 500) * (z < 2.8), pal['trim'])  # zipper
        img = reflective(img, z, 2.42, 2.53, pal['yellow'], pal['silver'])
        img = reflective(img, z, 2.16, 2.27, pal['yellow'], pal['silver'])
        # vertical braces front & back
        for c in (0.33, PI - 0.33):
            img = reflective(img, np.abs(az), c - 0.07, c + 0.07, pal['yellow'], pal['silver']) if c < 1 else img
        vert = np.abs(az)
        m1 = (z > 2.53)
        sub = P_solid(pal['orange'])(U, V, m)
        sub = reflective(sub, vert, 0.29, 0.43, pal['yellow'], pal['silver'])
        sub = reflective(sub, vert, PI - 0.43, PI - 0.29, pal['yellow'], pal['silver'])
        img = np.where(m1[..., None] & ((np.abs(vert - 0.36) < 0.075) | (np.abs(vert - (PI - 0.36)) < 0.075))[..., None], sub, img)
        return img
    vest.paint = vpaint
    # dark trim on the vest edges
    P.append(vest)
    def ppaint(U, V, m):
        img = P_solid(pal['beige'])(U, V, m); z, az = zc(U, V, m)
        return mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['beige_d'])
    for p in pt: p.paint = ppaint
    P += pt
    belt = band('ToolBelt', 2.0, 2.12, 0.012, th=0.02, bvh=piece_bvh(vest, *pt), hang=2.2); belt.group = 'Extras'   # straight, over the vest hem
    belt.paint = lambda U, V, m: mix(P_solid(pal['brown'])(U, V, m), aa(np.minimum(V - 0.12, 0.88 - V) * -200), pal['brown_d'])
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.06)), Vector((0, 1, 0)))
    P.append(prim_box('Buckle', loc + n * 0.015, (0.13, 0.03, 0.1), 'silver'))
    # pouches on hips
    for k, (az, w, h) in enumerate(((0.95, 0.2, 0.24), (-0.95, 0.2, 0.24), (1.6, 0.14, 0.18), (-1.6, 0.16, 0.2))):
        d = Vector((math.sin(az), -math.cos(az), 0))
        loc, n = project(bb, d * 1.5 + Vector((0, 0, 2.0)), -d)
        n = Vector((n.x, n.y, 0)).normalized()
        rot = Matrix(((n.y * -1, n.x, 0), (n.x, n.y, 0), (0, 0, 1))).transposed() if False else None
        ang = math.atan2(n.x, -n.y)
        R = Matrix.Rotation(ang, 3, 'Z')
        P.append(prim_rbox(f'Pouch{k}', loc + n * 0.06 + Vector((0, 0, -0.06)), (w, 0.1, h), 'brown', rot=R))
        P.append(prim_box(f'PouchFlap{k}', loc + n * 0.115 + Vector((0, 0, 0.02)), (w * 0.95, 0.015, 0.08), 'brown_d', rot=R))
    # hammer hanging at left hip (character left = +X)
    hx = Vector((0.56, -0.05, 1.98))
    P.append(prim_cyl('HammerHandle', hx + Vector((0, 0, 0.05)), hx + Vector((0.02, 0, -0.33)), 0.024, n=6, col='wood'))
    P.append(prim_box('HammerHead', hx + Vector((0, 0, 0.08)), (0.06, 0.2, 0.06), 'metal'))
    # screwdriver at right pouch
    for q in P[-2:]: q.bone = 'LowerTorso'
    sx = Vector((-0.55, -0.12, 2.1))
    P.append(prim_cyl('DriverGrip', sx, sx + Vector((0, 0, 0.1)), 0.025, n=6, col='red'))
    P.append(prim_cyl('DriverShaft', sx + Vector((0, 0, 0.1)), sx + Vector((0, 0, 0.2)), 0.009, n=5, col='metal'))
    for q in P[-2:]: q.bone = 'LowerTorso'
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.045, bulk=0.035, toe=0.03)
        sh.paint = lambda U, V, m: mix(P_solid(pal['boot'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), pal['sole'])
        P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 0.64, 0.47, 0.072, nseg=16, group='Feet', col='boot_d'))
        P.append(shaft)
    return P, pal

def chef():
    pal = {'white': '#f7f7f5', 'white_d': '#dcdcd8', 'btn': '#1c1c1c', 'black': '#161616', 'green': '#5a9a3a', 'green_d': '#3f7429', 'green_l': '#7cb556'}
    P = []
    pt = pants('Trousers', 2.15, 0.5, 0.04, hip_off=0.058, leg_extra=lambda z, a: 0.015 + 0.02 * max(0, 1.4 - z))
    jk = torso_shell('Jacket', 1.95, 0.055, nseg=32, extra=lambda z, a: 0.028 + 0.02 * max(0, 2.15 - z), th=0.022, hang=2.3, over=pt)
    def jp(U, V, m):
        img = P_solid(pal['white'])(U, V, m); z, az = zc(U, V, m)
        # double-breasted overlap edge (wearer's left panel over right)
        img = mix(img, aa((np.abs(az + 0.28) - 0.006) * 500) * (z < 3.05), pal['white_d'])
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.5, pal['white_d'])
        return img
    jk.paint = jp; P.append(jk)
    P.append(collar('Collar', 'stand', h=0.07, flare=0.02, open_front=0.08, col='white'))
    jb = piece_bvh(jk)
    for r, z in enumerate((2.86, 2.62, 2.38)):
        for c, x in enumerate((-0.12, 0.12)):
            loc, n = project(jb, Vector((x, 0, z)), Vector((0, 1, 0)))
            P.append(prim_cyl(f'Button{r}{c}', loc, loc + n * 0.022, 0.032, n=8, col='btn'))
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.97, 0.05, extra=lambda t, a: 0.01 + 0.01 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.abs(V - 0.9) * 400 - 1), pal['white_d']); P.append(sl)
    for p in pt: p.paint = lambda U, V, m: checker(U, V, m, 0.075, pal['white'], pal['black'])
    P += pt
    for s in 'LR':
        sh = shoe('Clog_' + s, s, off=0.045, bulk=0.035, toe=0.05, sole_h=0.07, open_elev=40)
        def cp(U, V, m):
            img = P_solid(pal['green'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['green_l'])
            # vent holes on the top
            x, zz = phys(U, V, m)
            holes = (np.hypot((x * 14) % 1 - 0.5, (zz * 14) % 1 - 0.5) < 0.22) & (V > 0.55)
            return mix(img, holes.astype(float), pal['green_d'])
        sh.paint = cp; P.append(sh)
        # heel strap
        sg = 1 if s == 'L' else -1
        c = Vector((0.255 * sg, 0.0, 0.42))
        pts = [Vector((0.255 * sg + 0.16 * math.cos(a), 0.05 + 0.2 * math.sin(a), 0.42)) for a in np.linspace(0.15, PI - 0.15, 7)]
        hs = tube_path('HeelStrap_' + s, pts, 0.025, 'green_d', n=6, group='Feet'); hs.rigid = True
        body_clear(hs, 0.02); P.append(hs)
    return P, pal

def firefighter():
    pal = {'red': '#c42a1e', 'red_d': '#9b1d14', 'dark': '#2b2b2e', 'dark_d': '#1b1b1d', 'yellow': '#f2e01c', 'silver': '#c3c6ca',
           'belt': '#3b1512', 'metal': '#b0b4ba', 'black': '#151515', 'sole': '#0a0a0a'}
    P = []
    pt = pants('Trousers', 2.22, 0.56, 0.05, hip_off=0.06, leg_extra=lambda z, a: 0.025 + 0.045 * max(0, 1.4 - z))
    jk = torso_shell('Jacket', 1.84, 0.075, nseg=32, extra=lambda z, a: 0.025 + 0.04 * max(0, 2.1 - z), th=0.025, hang=2.3, over=pt)
    def jp(U, V, m):
        img = P_solid(pal['red'])(U, V, m); z, az = zc(U, V, m)
        img = reflective(img, z, 2.70, 2.82, pal['yellow'], pal['silver'])
        img = reflective(img, z, 1.96, 2.08, pal['yellow'], pal['silver'])
        img = mix(img, aa(np.maximum(2.20 - z, z - 2.29) * 500), pal['belt'])
        img = mix(img, aa((np.abs(az) - 0.01) * 400), pal['red_d'])
        return img
    jk.paint = jp; P.append(jk)
    P.append(collar('Collar', 'stand', h=0.09, flare=0.03, open_front=0.12, col='red'))
    jb = piece_bvh(jk)
    for i, z in enumerate((2.97, 2.6, 2.245)):
        loc, n = project(jb, Vector((0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_box(f'ClaspBar{i}', loc + n * 0.02, (0.16, 0.03, 0.035), 'metal'))
        P.append(prim_box(f'ClaspHook{i}', loc + n * 0.03, (0.035, 0.035, 0.09), 'metal'))
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.96, 0.065, extra=lambda t, a: 0.012 + 0.02 * t)
        def spaint(U, V, m):
            img = P_solid(pal['red'])(U, V, m)
            img = reflective(img, V, 0.40, 0.48, pal['yellow'], pal['silver'])
            img = reflective(img, V, 0.74, 0.82, pal['yellow'], pal['silver'])
            return mix(img, aa((0.95 - V) * 400), pal['dark_d'])
        sl.paint = spaint; P.append(sl)
    def tp(U, V, m):
        img = P_solid(pal['dark'])(U, V, m); z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            img = reflective(img, z, 0.92, 1.0, pal['yellow'], pal['silver'])
            img = reflective(img, z, 0.78, 0.86, pal['yellow'], pal['silver'])
        return img
    for p in pt: p.paint = tp
    P += pt
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.05, bulk=0.04, toe=0.03, sole_h=0.07)
        sh.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), '#333333')
        P.append(sh)
        P.append(_shin(leg_tube('BootShaft_' + s, s, 0.66, 0.46, 0.078, nseg=16, group='Feet', col='black')))
    return P, pal

def pirate():
    pal = {'coat': '#8a5a2e', 'coat_d': '#6b4220', 'coat_l': '#9c6a3a', 'shirt': '#efe6cf', 'skin': SKIN, 'belt': '#5a3518',
           'gold': '#e0ad2a', 'gold_d': '#8a6414', 'red': '#b5302b', 'white': '#f3efe6', 'black': '#1a1a1c', 'sole': '#0c0c0c'}
    P = []
    sh = torso_shell('Shirt', 2.05, 0.035, nseg=32, th=0.015)
    def shp(U, V, m):
        img = P_solid(pal['shirt'])(U, V, m); z, az = zc(U, V, m)
        vz = 3.25 - z
        return mix(img, aa((np.abs(az) - np.clip(0.45 - vz * 0.9, 0, 1)) * 300) * (z > 2.82), pal['skin'])
    sh.paint = shp; P.append(sh)
    belt = band('Belt', 2.1, 2.24, 0.085, th=0.02)
    belt.paint = lambda U, V, m: mix(P_solid(pal['belt'])(U, V, m), aa(np.minimum(V - 0.1, 0.9 - V) * -200), '#3a2210')
    P.append(belt)
    loc, n = project(piece_bvh(belt), Vector((0, 0, 2.17)), Vector((0, 1, 0)))
    P.append(prim_box('BuckleL', loc + n * 0.02 + Vector((-0.07, 0, 0)), (0.035, 0.03, 0.17), 'gold'))
    P.append(prim_box('BuckleR', loc + n * 0.02 + Vector((0.07, 0, 0)), (0.035, 0.03, 0.17), 'gold'))
    P.append(prim_box('BuckleT', loc + n * 0.02 + Vector((0, 0, 0.07)), (0.175, 0.03, 0.035), 'gold'))
    P.append(prim_box('BuckleB', loc + n * 0.02 + Vector((0, 0, -0.07)), (0.175, 0.03, 0.035), 'gold'))
    P.append(prim_box('BucklePin', loc + n * 0.025, (0.09, 0.02, 0.025), 'gold_d'))
    # long open coat
    def ckeep(i, j, zc_, az):
        w = 0.42 if zc_ < 2.85 else 0.42 + (zc_ - 2.85) * 0.55
        return abs(az) > w
    pt = pants('Trousers', 2.2, 0.82, 0.045, hip_off=0.063, leg_extra=lambda z, a: 0.02 + 0.035 * max(0, 1.5 - z))
    coat = torso_shell('Coat', 1.12, 0.12, nseg=36, extra=lambda z, a: 0.01 + 0.09 * max(0, 2.05 - z), keep=ckeep, th=0.025, hang=2.3, over=pt + [belt])
    def cpaint(U, V, m):
        img = P_solid(pal['coat'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.5, pal['coat_d'])
        img = mix(img, aa((np.abs(az - PI) - 0.008) * 400) * (z < 1.8), pal['coat_d'])  # back vent
        img = mix(img, aa((np.abs(az + PI) - 0.008) * 400) * (z < 1.8), pal['coat_d'])
        return img
    coat.paint = cpaint; P.append(coat)
    cb = piece_bvh(coat)
    for sg in (-1, 1):
        def lap(s, t, sg=sg):
            z = 2.55 + t * 0.6
            w = 0.42 if z < 2.85 else 0.42 + (z - 2.85) * 0.55
            x0 = math.sin(w) * 0.56
            return Vector((sg * (x0 - 0.01 + s * (0.06 + 0.12 * t)), 0, z))
        P.append(surface_patch(f'Lapel{sg}', cb, lap, Vector((0, 1, 0)), 0.014, 4, 6, col='coat_l', th=0.015))
    P.append(collar('CoatCollar', 'fold', h=0.08, flare=0.08, open_front=0.5, col='coat_l', fold=0.1, lift=0.02))
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.93, 0.07, extra=lambda t, a: 0.015 + 0.02 * t)
        sl.paint = P_solid(pal['coat']); P.append(sl)
        P.append(sleeve('CoatCuff_' + s, s, 0.76, 0.95, 0.11, nrows=4, cap=False, col='coat_d', extra=lambda t, a: 0.03 * (t - 0.76) / 0.19))
    for p in pt: p.paint = lambda U, V, m: vstripes(U, V, m, 0.075, pal['white'], pal['red'])
    P += pt
    for s in 'LR':
        b = shoe('Boot_' + s, s, off=0.05, bulk=0.035, toe=0.03, sole_h=0.05)
        b.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), '#333333')
        P.append(b)
        P.append(_shin(leg_tube('BootShaft_' + s, s, 0.98, 0.46, 0.09, nseg=16, group='Feet', col='black', extra=lambda z, a: 0.01)))
        P.append(_shin(leg_tube('BootCuff_' + s, s, 1.06, 0.93, 0.13, nseg=16, nrows=3, group='Feet', col='black', extra=lambda z, a: 0.02 + 0.04 * (z - 0.93) / 0.13)))
    return P, pal

def wizard():
    pal = {'p': '#6b3fa0', 'p_d': '#53307f', 'p_l': '#8a5cc2', 'gold': '#f2c94c', 'shoe': '#6b3fa0', 'sash': '#53307f'}
    P = []
    def rkeep(i, j, zc_, az):
        return not (zc_ > 2.92 and abs(az) < 0.06 + 0.5 * (zc_ - 2.92) / 0.3)
    legs = [skin_leg(s, 1.9, 0.47) for s in 'LR']
    robe = torso_shell('Robe', 0.82, 0.06, nseg=40, extra=lambda z, a: 0.01 + 0.17 * max(0, 2.1 - z) ** 1.1, th=0.025, slits=RF_SLIT_TOP(), hang=2.3, over=legs)  # front/back slits (closed at rest)
    def rp(U, V, m):
        img = P_solid(pal['p'])(U, V, m); z, az = zc(U, V, m)
        pts, x, zz, circ = scatter(U, V, m, 6, 7, None)
        for px, pz, k in pts:
            if k % 4 == 0: img = moon(img, x, zz, circ, px, pz, 0.045, pal['gold'])
            else: img = star(img, x, zz, circ, px, pz, 0.045 + (k % 3) * 0.008, pal['gold'], rot=k * 0.1)
        img = mix(img, aa((z - (m['zmin'] + 0.07)) * 600), pal['p_l'])  # hem trim
        if m.get('kind') == 'torso':
            w = np.clip((z - 2.9) * 0.9, 0, 1)
            img = mix(img, aa((np.abs(az) - w - 0.05) * 300) * (z > 2.86), pal['p_l'])
            img = mix(img, aa((np.abs(az) - w) * 300) * (z > 2.9), SKIN)
        return img
    robe.paint = rp; P.append(robe)
    P.append(collar('Collar', 'stand', h=0.04, flare=0.04, open_front=0.5, col='p_l'))
    P += legs   # hidden under the robe at rest; covers the leg up to the hip when a slit opens
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.52, 0.06, extra=lambda t, a: 0.01 + 0.22 * max(0, t - 0.12) ** 1.4)
        sl.paint = lambda U, V, m: mix(rp(U, V, dict(m, zmin=0, zmax=0.8)), aa((0.9 - V) * 400), pal['p_l'])
        sl.weight = 'nearest'; P.append(sl)
    sash = band('Sash', 2.12, 2.27, 0.012, th=0.02, col='sash', bvh=piece_bvh(robe)); P.append(sash)   # fitted on the robe
    loc, n = project(piece_bvh(sash), Vector((0.0, 0, 2.2)), Vector((0, 1, 0)))
    P.append(prim_rbox('SashKnot', loc + n * 0.03, (0.12, 0.06, 0.11), 'p_d'))
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Shoe_' + s, s, off=0.04, bulk=0.02, toe=0.07, sole_h=0.03, open_elev=42, col='shoe')
        P.append(sh)
        tip = min(sh.verts, key=lambda p: p.y)
        tip = Vector((tip.x, tip.y + 0.03, 0.40))
        pts = []
        for k in range(14):
            f = k / 13
            ang = f * 1.6 * PI
            rad = 0.12 * (1 - 0.55 * f)
            cc = tip + Vector((0, -0.05, 0.12))
            pts.append(cc + Vector((0, -math.sin(ang) * rad, -math.cos(ang) * rad)))
        P.append(tube_path('Curl_' + s, pts, 0.06, 'shoe', n=7, group='Feet', rfn=lambda t: 0.065 * (1 - 0.8 * t)))
        P[-1].rigid = True
    return P, pal
