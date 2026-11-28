from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '22', 'Mail_Carrier', 'Common', 0.32


def _cyl(az, z, r=0.5):
    return Vector((r * math.sin(az), -r * math.cos(az), z))


def _axis_proj(bvh, p):
    """project p onto the outermost surface of bvh, cast from outside toward the torso axis"""
    a = Vector((0, 0, min(max(p.z, 2.2), 2.75)))
    d = (p - a).normalized()
    h = bvh.ray_cast(a + d * 2.5, -d, 2.5)
    if h[0] is None: return p.copy(), d
    n = h[1] if h[1].dot(d) > 0 else -h[1]
    return h[0], n


def strap_piece(name, ctrl, bvh, w=0.09, lift=0.02, th=0.014, n=56, group='Top'):
    """crossbody strap lying on the garments (bvh): a 3-wide ribbon along the control path, thickened"""
    pts = smooth_line(polyline_resample(ctrl, n), 3)
    C = [_axis_proj(bvh, p) for p in pts]
    rows = []; hints = []
    for i, (c, nn) in enumerate(C):
        t = (C[min(i + 1, n - 1)][0] - C[max(i - 1, 0)][0]).normalized()
        b = t.cross(nn).normalized()
        row = []; hh = []
        for f in (-0.5, 0.0, 0.5):
            q, qn = (c, nn) if f == 0 else _axis_proj(bvh, c + b * w * f)
            row.append(q + qn * lift); hh.append(qn)
        rows.append(row); hints.append(hh)
    L = sum((rows[i][1] - rows[i - 1][1]).length for i in range(1, len(rows)))
    pc = grid_piece(name, rows, closed=False, hints=hints, group=group)
    thicken(pc, th)
    pc.meta['patch'] = True; pc.meta['length'] = L; pc.meta['rect'] = (32, 512)
    pc.region = 'torso'; pc.skirt = False
    return pc


def build():
    pal = {'blue': '#8ab6d6', 'blue_d': '#6f9cbd', 'blue_l': '#a3c7e0', 'navy': '#1f3a5f', 'navy_d': '#152a46',
           'navy_l': '#2c4c78', 'red': '#c8102e', 'black': '#111111', 'black_l': '#2a2a2c', 'sole': '#1c1c1e',
           'leather': '#7a5230', 'leather_d': '#5e3e22', 'leather_dd': '#3a2614', 'stitch': '#b08658',
           'white': '#f6f6f2', 'cream': '#efe3c4', 'paper': '#f4efe2', 'silver': '#b9bdc2', 'btn': '#eef2f6'}
    P = []

    # ---------------- navy shorts (built first: the shirt tucks inside) ----------------
    pt = pants('Shorts', 2.26, 1.38, 0.045, hip_off=0.072, leg_extra=lambda z, a: 0.02 + 0.05 * max(0, 1.85 - z), nseg=16)
    pt[1].rect_key = 'ShortsLegL'; pt[2].rect_key = 'ShortsLegR'

    def shorts_paint(U, V, m):
        img = P_solid(pal['navy'])(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            outer = PI / 2 if m.get('side') == 'L' else -PI / 2
            img = mix(img, aa((np.abs(az - outer) - 0.012) * 400), pal['red'])                    # red piping, outer seam
            img = mix(img, aa((np.abs(az + outer) - 0.006) * 400) * 0.7, pal['navy_d'])          # inner seam
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.06)) * 500 - 1.2), pal['navy_d'])         # hem stitch
        else:
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.012) * 400), pal['red'])          # piping continues up
            img = mix(img, aa((np.abs(az) - 0.008) * 400) * (z < 2.13), pal['navy_d'])           # fly
            for sg in (1, -1):                                                                     # slash pockets
                img = mix(img, aa(np.abs((az * sg - 0.95) - (z - 2.05) * 1.6) * 400 - 1.2) * (np.abs(z - 2.08) < 0.1), pal['navy_d'])
            for c in (PI - 0.55, -(PI - 0.55)):                                                    # back pockets
                inside = np.maximum(np.abs(az - c) - 0.24, np.abs(z - 2.06) - 0.07)
                img = mix(img, aa(np.abs(inside) * 500 - 1.2), pal['navy_d'])
        return img
    for p in pt: p.paint = shorts_paint
    P += pt

    # black belt fitted on the shorts' hip
    belt = band('Belt', 2.13, 2.235, 0.012, th=0.02, bvh=piece_bvh(pt[0]), group='Bottom')
    belt.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa(np.abs(np.abs(V - 0.5) - 0.36) * 300 - 1.0), pal['black_l'])
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.183)), Vector((0, 1, 0)))
    P.append(prim_box('Buckle', loc + n * 0.016, (0.13, 0.026, 0.1), 'silver', group='Bottom'))
    P.append(prim_box('BuckleBar', loc + n * 0.031, (0.07, 0.012, 0.05), 'black', group='Bottom'))
    for q in P[-2:]: q.bone = 'LowerTorso'

    # ---------------- light-blue short-sleeve shirt, tucked ----------------
    shirt = torso_shell('Shirt', 2.12, 0.035, nseg=32, extra=lambda z, a: 0.008, th=0.016)

    def shirt_paint(U, V, m):
        img = P_solid(pal['blue'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - 0.045) - 0.003) * 500), pal['blue_d'])               # placket edges
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 400) * 0.7, pal['blue_d'])         # side seams
        img = mix(img, aa(np.abs(z - 2.96) * 500 - 1.0) * (np.abs(az) > 2.0), pal['blue_d'])         # back yoke seam
        return img
    shirt.paint = shirt_paint; P.append(shirt)
    P.append(collar('Collar', 'fold', h=0.06, flare=0.015, open_front=0.3, col='blue', fold=0.065))
    sb = piece_bvh(shirt)
    for i, z in enumerate((2.98, 2.78, 2.36)):
        loc, n = project(sb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.016, 0.024, n=8, col='btn', group='Top'))
    # chest pocket (character's left) with flap and button
    pk = surface_patch('Pocket', sb, lambda s, t: Vector((0.16 + s * 0.2, 0, 2.6 + t * 0.2)), Vector((0, 1, 0)), 0.01, 4, 4, col='blue_d', th=0.012)
    pk.rigid = True; P.append(pk)
    pf = surface_patch('PocketFlap', sb, lambda s, t: Vector((0.15 + s * 0.22, 0, 2.77 + t * 0.07)), Vector((0, 1, 0)), 0.024, 4, 2, col='blue', th=0.012)
    pf.rigid = True; P.append(pf)
    loc, n = project(piece_bvh(pf), Vector((0.26, 0, 2.795)), Vector((0, 1, 0)))
    P.append(prim_cyl('PocketBtn', loc, loc + n * 0.012, 0.018, n=8, col='btn', group='Top'))

    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.36, 0.045, extra=lambda t, a: 0.02 * max(0, t) / 0.36)

        def sleeve_paint(U, V, m):
            img = P_solid(pal['blue'])(U, V, m)
            img = mix(img, aa((0.9 - V) * 400), pal['blue_l'])                                   # turned hem
            img = mix(img, aa(np.abs(V - 0.9) * 400 - 1.0), pal['navy'])                          # navy trim line
            return img
        sl.paint = sleeve_paint; P.append(sl)
        # navy shoulder patch on the outer upper sleeve (red border, white envelope emblem)
        sg = 1 if s == 'L' else -1
        cm, tg = arm_point(s, 0.17)
        out = Vector((sg, 0, 0)); out = (out - tg * out.dot(tg)).normalized()
        bvec = tg.cross(out).normalized()
        def ppos(u, t, s=s, bvec=bvec):
            c, _ = arm_point(s, 0.07 + t * 0.17)
            return c + bvec * (u - 0.5) * 0.2
        ap = surface_patch('ArmPatch_' + s, piece_bvh(sl), ppos, -out, 0.008, 5, 5, th=0.01)

        def patch_paint(U, V, m):
            img = P_solid(pal['navy'])(U, V, m)
            x, y = U - 0.5, V - 0.5
            box = np.maximum(np.abs(x), np.abs(y))
            img = mix(img, aa(np.abs(box - 0.40) * 300 - 1.5), pal['red'])                       # red border
            env = np.maximum(np.abs(x) / 0.26, np.abs(y) / 0.17)
            img = mix(img, aa((env - 1) * 60), pal['white'])                                       # envelope
            fl = np.abs(np.abs(x) * 0.8 - (y + 0.17)) * (y < 0.05)                                 # flap V
            img = mix(img, aa(fl * 300 - 1.0) * (env < 1), pal['navy'])
            return img
        ap.paint = patch_paint; ap.rect_key = 'ArmPatch'; ap.meta['rect'] = (64, 64)
        ap.rigid = True; ap.region = 'arm_' + s; P.append(ap)

    # ---------------- mail satchel on the left hip ----------------
    a = 0.85                                   # azimuth (front = 0, character's left = +pi/2)
    d = Vector((math.sin(a), -math.cos(a), 0)); tv = Vector((math.cos(a), math.sin(a), 0))
    R = Matrix.Rotation(a, 3, 'Z')             # -Y (bag front) -> d
    W_, D_, H_ = 0.46, 0.14, 0.36
    zc_ = 2.13
    hb = piece_bvh(pt[0], belt)
    loc, n = project(hb, d * 1.5 + Vector((0, 0, zc_)), -d)
    bc = Vector((loc.x, loc.y, zc_)) + d * (D_ / 2 - 0.02)
    bag = []
    bag.append(prim_rbox('Satchel', bc, (W_, D_, H_), 'leather', rot=R))
    top = bc + Vector((0, 0, H_ / 2))
    bag.append(prim_box('SatchelMouth', top + Vector((0, 0, -0.004)), (W_ * 0.86, D_ * 0.55, 0.012), 'leather_dd', rot=R))
    # envelopes peeking out of the top
    for k, (off, dz, tilt, w, h, col) in enumerate(((-0.1, 0.06, -0.12, 0.17, 0.15, 'white'), (0.0, 0.085, 0.06, 0.16, 0.15, 'cream'),
                                                     (0.1, 0.05, 0.16, 0.15, 0.13, 'paper'))):
        Re = Matrix.Rotation(tilt, 3, d) @ R
        ec = top + tv * off + d * (0.018 * (1 - k)) + Vector((0, 0, dz - h / 2))
        bag.append(prim_box(f'Envelope{k}', ec, (w, 0.008, h), col, rot=Re))
        if k == 1:   # red stamp
            sc = ec + Re @ Vector((w / 2 - 0.035, -0.006, h / 2 - 0.035))
            bag.append(prim_box('Stamp', sc, (0.035, 0.004, 0.035), 'red', rot=Re))
    # front flap with red mail badge and a strap + buckle
    ff = bc + d * (D_ / 2 + 0.002)
    bag.append(prim_box('SatchelFlap', ff + Vector((0, 0, H_ / 2 - 0.115)), (W_ * 1.02, 0.016, 0.23), 'leather_d', rot=R))
    bag.append(prim_box('FlapEdge', ff + d * 0.004 + Vector((0, 0, H_ / 2 - 0.232)), (W_ * 1.02, 0.014, 0.012), 'leather_dd', rot=R))
    bag.append(prim_cyl('Badge', ff + d * 0.008 + Vector((0, 0, H_ / 2 - 0.075)), ff + d * 0.02 + Vector((0, 0, H_ / 2 - 0.075)), 0.045, n=12, col='red'))
    bag.append(prim_box('BadgeEnv', ff + d * 0.022 + Vector((0, 0, H_ / 2 - 0.075)), (0.05, 0.004, 0.032), 'white', rot=R))
    bag.append(prim_box('FlapStrap', ff + d * 0.012 + Vector((0, 0, H_ / 2 - 0.215)), (0.045, 0.01, 0.13), 'leather_dd', rot=R))
    bag.append(prim_box('FlapBuckle', ff + d * 0.018 + Vector((0, 0, H_ / 2 - 0.235)), (0.065, 0.012, 0.045), 'silver', rot=R))
    tabs = []
    for k, sgn in enumerate((-1, 1)):   # strap tabs where the strap enters the bag (-1 inner end, +1 outer end)
        tp = top + tv * sgn * (W_ / 2 - 0.065) + d * (-D_ / 2 + 0.03)
        tabs.append(tp)
        bag.append(prim_box(f'StrapTab{k}', tp + Vector((0, 0, 0.005)), (0.075, 0.05, 0.09), 'leather_d', rot=R))
        bag.append(prim_box(f'StrapRivet{k}', tp + d * 0.026 + Vector((0, 0, 0.015)), (0.02, 0.01, 0.02), 'silver', rot=R))
    for q in bag: q.bone = 'LowerTorso'
    P += bag

    # crossbody strap: bag (inner end) -> up the chest -> over the right shoulder -> down the back -> bag (outer end)
    front = [tabs[0] - Vector((0, 0, 0.03)), tabs[0] + Vector((0, 0, 0.06))] + [_cyl(az, z) for az, z in ((0.3, 2.47), (0.0, 2.58), (-0.3, 2.72), (-0.6, 2.87), (-0.82, 2.98))]
    shoulder = [Vector(v) for v in ((-0.40, -0.22, 3.12), (-0.40, -0.1, 3.2), (-0.40, 0.02, 3.22), (-0.40, 0.14, 3.18), (-0.40, 0.25, 3.1))]
    back = [_cyl(az, z) for az, z in ((-(PI - 0.82), 2.98), (-(PI - 0.6), 2.86), (-(PI - 0.3), 2.74), (PI, 2.63), (PI - 0.35, 2.53),
                                      (PI - 0.75, 2.44), (PI - 1.15, 2.38), (1.65, 2.34))] + [tabs[1] + Vector((0, 0, 0.06)), tabs[1] - Vector((0, 0, 0.03))]
    st = strap_piece('Strap', front + shoulder + back, piece_bvh(shirt, pt[0], belt))

    def strap_paint(U, V, m):
        img = P_solid(pal['leather'])(U, V, m)
        img = mix(img, aa((0.44 - np.abs(U - 0.5)) * 60), pal['leather_d'])
        dash = ((V * m.get('length', 3.0) * 30) % 1) < 0.55
        img = mix(img, aa(np.abs(np.abs(U - 0.5) - 0.32) * 120 - 1.0) * dash, pal['stitch'])
        return img
    st.paint = strap_paint; P.append(st)

    # ---------------- legs: skin covers, white socks, black shoes ----------------
    for s in 'LR':
        P.append(skin_leg(s, 1.45, 0.47))
        sk = leg_tube('Sock_' + s, s, 0.80, 0.50, 0.034, nseg=16, th=0.012, group='Feet')

        def sock_paint(U, V, m):
            img = P_solid(pal['white'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa(np.maximum(0.715 - z, z - 0.745) * 500), pal['navy'])
            img = mix(img, aa(np.maximum(0.67 - z, z - 0.695) * 500), pal['red'])
            img = mix(img, aa((0.78 - z) * 500) * 0.35, '#d8d8d4')                               # ribbed top
            return img
        sk.paint = sock_paint; P.append(sk)
        sh = shoe('Shoe_' + s, s, off=0.045, bulk=0.012, toe=0.05, sole_h=0.045, open_elev=42)

        def shoe_paint(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            img = mix(img, aa(np.abs(z - m['sole_top']) * 600 - 1.0), pal['black_l'])           # welt line
            lace = (np.cos(az) > 0.93) & (z > m['sole_top'] + 0.09)
            img = mix(img, (lace & (((z * 40) % 1) < 0.4)).astype(float), '#3a3a3e')
            return img
        sh.paint = shoe_paint; P.append(sh)
    return P, pal
