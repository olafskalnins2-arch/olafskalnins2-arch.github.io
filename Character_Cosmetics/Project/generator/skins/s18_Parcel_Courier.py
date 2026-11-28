from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '18', 'Parcel_Courier', 'Common', 0.32


def build():
    pal = {'brown': '#6b4a2b', 'brown_d': '#5a3d22', 'brown_dd': '#47301a', 'seam': '#4f3520', 'yellow': '#f2b632',
           'yellow_d': '#c98f1c', 'black': '#222222', 'black_d': '#151515', 'white': '#f4f4f2', 'white_d': '#d9d9d6',
           'silver': '#b4b8bd', 'board': '#a87a46', 'paper': '#f7f5ee', 'ink': '#7d8794', 'btn': '#e9d9b8', 'skin': '#f7b88b'}
    P = []

    # ---- shorts first (the tucked polo sits inside the hip shell) ----
    pt = pants('Shorts', 2.22, 1.36, 0.045, hip_off=0.066, leg_extra=lambda z, a: 0.02 + 0.05 * max(0, 1.85 - z), nseg=16)
    def shorts_paint(U, V, m):
        img = P_solid(pal['brown_d'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['seam'])          # side seams
        if m.get('kind') == 'leg':
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.06)) * 500 - 1.5), pal['seam'])               # hem stitch
        else:
            img = mix(img, aa((np.abs(az) - 0.008) * 400) * (z < 2.16), pal['seam'])                  # fly
            # back pockets
            for c in (PI - 0.55, -(PI - 0.55)):
                inside = np.maximum(np.abs(az - c) - 0.24, np.abs(z - 2.08) - 0.07)
                img = mix(img, aa(np.abs(inside) * 500 - 1.2), pal['seam'])
            # front slash pockets
            for sg in (1, -1):
                img = mix(img, aa(np.abs((az * sg - 0.95) - (z - 2.05) * 1.6) * 400 - 1.2) * (np.abs(z - 2.08) < 0.1), pal['seam'])
        return img
    for p in pt: p.paint = shorts_paint
    P += pt

    # ---- tucked polo shirt ----
    shirt = torso_shell('Polo', 2.12, 0.035, nseg=32, extra=lambda z, a: 0.008, th=0.016)
    def polo_paint(U, V, m):
        img = P_solid(pal['brown'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 400) * 0.7, pal['brown_d'])        # side seams
        # button placket at the throat
        pk = (z > 2.74) & (z < 3.3)
        img = mix(img, aa((np.abs(np.abs(az) - 0.075) - 0.003) * 500) * pk, pal['brown_d'])
        img = mix(img, aa(np.abs(z - 2.74) * 500 - 1.0) * (np.abs(az) < 0.078), pal['brown_d'])
        return img
    shirt.paint = polo_paint; P.append(shirt)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.36, 0.045, extra=lambda t, a: 0.02 * t / 0.36)
        def sleeve_paint(U, V, m):
            img = P_solid(pal['brown'])(U, V, m)
            img = mix(img, aa((0.86 - V) * 400), pal['brown_d'])                                     # ribbed cuff
            img = mix(img, aa(np.abs(V - 0.93) * 400 - 3), pal['yellow'])                           # tipping stripe
            return img
        sl.paint = sleeve_paint; P.append(sl)
    # polo collar with yellow tipping
    col = collar('Collar', 'fold', h=0.06, flare=0.03, open_front=0.22, fold=0.085)
    def collar_paint(U, V, m):
        img = P_solid(pal['brown'])(U, V, m)
        img = mix(img, aa((0.86 - V) * 300), pal['yellow'])
        img = mix(img, aa(np.abs(V - 0.93) * 300 - 1.0), pal['brown'])
        return img
    col.paint = collar_paint; col.meta['rect'] = (256, 64); P.append(col)
    sb = piece_bvh(shirt)
    for i, z in enumerate((3.08, 2.88)):
        loc, n = project(sb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.018, 0.024, n=8, col='btn', group='Top'))
    # yellow box-logo patch on the left chest
    logo = surface_patch('LogoPatch', sb, lambda s, t: Vector((0.15 + s * 0.22, 0, 2.56 + t * 0.22)), Vector((0, 1, 0)),
                         0.008, 5, 5, th=0.01)
    def logo_paint(U, V, m):
        img = P_solid(pal['yellow'])(U, V, m)
        x, y = U - 0.5, V - 0.5
        img = mix(img, aa(np.abs(np.maximum(np.abs(x), np.abs(y)) - 0.42) * 300 - 1.2), pal['yellow_d'])   # stitched rim
        # isometric parcel: top rhombus + two side faces
        top = (np.abs(x) / 0.26 + np.abs(y - 0.12) / 0.13) < 1
        body = (np.abs(x) < 0.26) & (y < 0.12) & (y > -0.27 + 0.13 * (1 - np.abs(x) / 0.26)) & ~top
        left = body & (x < 0)
        img = mix(img, top.astype(float), pal['board'])
        img = mix(img, left.astype(float), pal['brown_d'])
        img = mix(img, (body & ~left).astype(float), pal['brown_dd'])
        tape = (np.abs(x - (y - 0.12) * 0.0) < 0.035) & (top | body)
        img = mix(img, tape.astype(float) * 0.85, pal['yellow'])
        return img
    logo.paint = logo_paint; logo.meta['rect'] = (128, 128); P.append(logo)

    # ---- black belt on the shorts ----
    belt = band('Belt', 2.08, 2.2, 0.012, th=0.02, bvh=piece_bvh(pt[0])); belt.group = 'Bottom'
    belt.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa(np.minimum(V - 0.12, 0.88 - V) * -200), pal['black_d'])
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.14)), Vector((0, 1, 0)))
    P.append(prim_box('Buckle', loc + n * 0.012, (0.15, 0.025, 0.11), 'silver', group='Bottom'))
    P.append(prim_box('BuckleBar', loc + n * 0.026, (0.11, 0.012, 0.025), 'black_d', group='Bottom'))
    for q in P[-2:]: q.rigid = True; q.bone = 'LowerTorso'
    # belt loops
    for k, az in enumerate((0.55, -0.55, 1.45, -1.45, PI - 0.4, -(PI - 0.4))):
        d = Vector((math.sin(az), -math.cos(az), 0))
        l2, n2 = project(bb, d * 1.5 + Vector((0, 0, 2.14)), -d)
        if l2 is None: continue
        ang = math.atan2(n2.x, -n2.y)
        P.append(prim_box(f'BeltLoop{k}', l2 + n2 * 0.006, (0.04, 0.014, 0.15), 'brown_d', rot=Matrix.Rotation(ang, 3, 'Z'), group='Bottom'))
        P[-1].rigid = True; P[-1].bone = 'LowerTorso'

    # ---- small clipboard clipped to the belt (wearer's right front hip) ----
    az = -0.78
    d = Vector((math.sin(az), -math.cos(az), 0))
    l3, n3 = project(bb, d * 1.5 + Vector((0, 0, 2.12)), -d)
    n3 = Vector((n3.x, n3.y, 0)).normalized()
    R = Matrix.Rotation(math.atan2(n3.x, -n3.y), 3, 'Z')
    tilt = R @ Matrix.Rotation(-0.06, 3, 'X')            # bottom swings out a touch
    up = tilt @ Vector((0, 0, 1))
    c0 = l3 + n3 * 0.032
    bc = c0 - up * 0.14
    cb = []
    cb.append(prim_box('ClipBoard', bc, (0.22, 0.02, 0.3), 'board', rot=tilt, group='Extras'))
    fwd = tilt @ Vector((0, -1, 0))
    cb.append(prim_box('ClipPaper', bc + fwd * 0.012 - up * 0.015, (0.19, 0.006, 0.25), 'paper', rot=tilt, group='Extras'))
    for k in range(4):
        cb.append(prim_box(f'ClipLine{k}', bc + fwd * 0.0155 + up * (0.04 - k * 0.045), (0.12 - 0.02 * (k == 3), 0.003, 0.012), 'ink', rot=tilt, group='Extras'))
    cb.append(prim_box('ClipTick', bc + fwd * 0.0155 + up * 0.04 + (tilt @ Vector((0.075, 0, 0))), (0.022, 0.003, 0.022), 'yellow', rot=tilt, group='Extras'))
    cb.append(prim_rbox('ClipClamp', c0 - up * 0.005 + fwd * 0.012, (0.11, 0.03, 0.05), 'silver', rot=tilt, group='Extras', bevel=0.01))
    cb.append(prim_box('ClipHook', c0 + up * 0.035 - fwd * 0.006, (0.05, 0.012, 0.11), 'silver', rot=tilt, group='Extras'))
    for q in cb: q.rigid = True; q.bone = 'LowerTorso'
    P += cb

    # ---- legs: skin covers, white crew socks, black sneakers ----
    for s in 'LR':
        lg = skin_leg(s, 1.5, 0.47)
        lg.paint = P_solid(pal['skin']); P.append(lg)   # o02.SKIN is the linear factor; this is the arms' real sRGB tone
        sk = leg_tube('Sock_' + s, s, 0.80, 0.48, 0.032, nseg=16, group='Feet', th=0.012)
        def sock_paint(U, V, m):
            img = P_solid(pal['white'])(U, V, m)
            x, z = phys(U, V, m)
            rib = (0.5 + 0.5 * np.cos(x * 2 * PI / 0.035)) * (z > 0.68) * 0.35
            img = mix(img, rib, pal['white_d'])
            img = mix(img, aa(np.abs(z - 0.66) * 500 - 1.2), pal['white_d'])
            return img
        sk.paint = sock_paint; P.append(sk)
        sh = shoe('Sneaker_' + s, s, off=0.045, bulk=0.025, toe=0.04, sole_h=0.055, open_elev=44)
        def sneaker_paint(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            z, az = zc(U, V, m)
            st = m['sole_top']
            img = mix(img, aa((z - st) * 600), pal['white'])                       # white midsole
            img = mix(img, aa((z - (st - 0.035)) * 600), '#3a3a3a')               # dark outsole
            img = mix(img, aa(np.abs(z - (st + 0.02)) * 600 - 0.8), pal['black_d'])  # welt stitch
            return img
        sh.paint = sneaker_paint; P.append(sh)
        # laces across the top of the foot
        sg = 1 if s == 'L' else -1
        fb = piece_bvh(sh)
        for k in range(3):
            y = -0.2 + k * 0.06
            pts = []
            for f in np.linspace(-1, 1, 5):
                q = Vector((0.255 * sg + f * 0.06, y, 0.9))
                loc, nn = project(fb, q, Vector((0, 0, -1)))
                if loc is None: break
                pts.append(loc + nn * 0.008)
            if len(pts) == 5:
                lc = tube_path(f'Lace_{s}{k}', pts, 0.011, 'white', n=4, group='Feet')
                lc.rigid = True; lc.region = 'foot_' + s; P.append(lc)
    return P, pal
