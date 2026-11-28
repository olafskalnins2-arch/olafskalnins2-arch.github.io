from o04 import *          # garments, pipeline, paints, o02/o03/o04 helpers
NUM, NAME, RARITY, MAXD = '28', 'Deep_Diver', 'Rare', 0.32


def _shin28(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _fin_blade(name, side, y0, y1, w0, w1, z0, half_th, curl, col, n=10, ns=9):
    """Flat fin blade: a flattened elliptic tube running forward (-Y) from y0 (under the foot pocket) to y1 (tip)."""
    sg = 1 if side == 'L' else -1
    cx = 0.255 * sg
    rows = []; hints = []; ctrs = []
    for k in range(ns):
        f = k / (ns - 1)
        y = y0 + (y1 - y0) * f
        w = w0 + (w1 - w0) * f ** 0.8
        zc_ = z0 + half_th + curl * f ** 2
        th = half_th * (1 - 0.45 * f)
        c = Vector((cx, y, zc_)); ctrs.append(c)
        ring = []; hh = []
        for j in range(n):
            a = 2 * PI * j / n
            ca, sa = math.cos(a), math.sin(a)
            # squarish (superellipse) section so the blade edge reads as a flat plate
            ex = math.copysign(abs(ca) ** 0.5, ca); ez = math.copysign(abs(sa) ** 0.7, sa)
            p = c + Vector((ex * w / 2, 0, ez * th))
            ring.append(p); hh.append(Vector((ca, 0, sa)))
        rows.append(ring); hints.append(hh)
    pc = grid_piece(name, rows, True, col=col, hints=hints, group='Feet', cap_start=ctrs[0] + Vector((0, 0.01, 0)),
                    cap_end=ctrs[-1] + Vector((0, -0.01, 0)))
    pc.rigid = True; pc.bone = ('Left' if side == 'L' else 'Right') + 'Foot'
    return pc, ctrs


def build():
    pal = {'navy': '#1d2b4f', 'navy_d': '#141f3a', 'navy_l': '#2a3c66', 'yellow': '#f3c623', 'yellow_d': '#c99f12',
           'lead': '#5a5f66', 'lead_d': '#43474d', 'black': '#111111', 'steel': '#b9bec5', 'glass': '#8fd3ec',
           'rubber': '#262626'}
    P = []

    # ---------------- wetsuit legs + hip (one silhouette) ----------------
    pt = pants('Wetsuit', 2.24, 0.55, 0.03, hip_off=0.046, leg_extra=lambda z, a: 0.006)

    def leg_paint(U, V, m):
        img = P_solid(pal['navy'])(U, V, m); z, az = zc(U, V, m)
        kind = m.get('kind')
        if kind == 'leg':
            c = PI / 2 if m.get('side') == 'L' else -PI / 2
            d = np.abs(np.remainder(az - c + PI, 2 * PI) - PI)
            img = mix(img, aa((d - 0.36) * 300), pal['yellow'])                 # outer side panel
            img = mix(img, aa(np.abs(d - 0.36) * 400 - 1.2), pal['black'])      # piping
            img = mix(img, aa(np.abs(z - 0.6) * 500 - 6), pal['black'])         # ankle seal
        else:
            d = np.abs(np.abs(az) - PI / 2)
            img = mix(img, aa((d - 0.32) * 300), pal['yellow'])
            img = mix(img, aa(np.abs(d - 0.32) * 400 - 1.2), pal['black'])
        return img
    for p in pt: p.paint = leg_paint

    # ---------------- wetsuit top (tight, tucked under the weight belt) ----------------
    suit = torso_shell('SuitTop', 2.1, 0.03, nseg=32, extra=lambda z, a: 0.004, th=0.02)

    def top_paint(U, V, m):
        img = P_solid(pal['navy'])(U, V, m); z, az = zc(U, V, m)
        d = np.abs(np.abs(az) - PI / 2)
        wdt = 0.32 + np.clip((z - 2.9) * 2.6, 0, 1.1)                         # side panel widening over the shoulder
        img = mix(img, aa((d - wdt) * 300), pal['yellow'])
        img = mix(img, aa(np.abs(d - wdt) * 400 - 1.2), pal['black'])
        # chest seam yoke
        img = mix(img, aa(np.abs(z - 2.9) * 500 - 1.2) * (d > wdt), pal['navy_l'])
        # back zipper with pull
        bz = np.abs(np.abs(az) - PI)
        img = mix(img, aa((bz - 0.018) * 400) * (z > 2.25), pal['black'])
        img = mix(img, aa((bz - 0.006) * 400) * (z > 2.25), pal['lead'])
        # harness straps (front and back) holding the twin tanks
        for c in (0.47, PI - 0.5):
            img = mix(img, aa((np.abs(np.abs(az) - c) - 0.065) * 400) * (z > 2.25), pal['black'])
        return img
    suit.paint = top_paint; P.append(suit)
    P.append(collar('NeckSeal', 'stand', h=0.05, flare=0.02, col='black', th=0.02))

    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.96, 0.03, extra=lambda t, a: 0.004)

        def sp(U, V, m):
            img = P_solid(pal['navy'])(U, V, m)
            img = mix(img, aa((V - 0.30) * 400), pal['yellow'])                  # shoulder panel
            img = mix(img, aa(np.abs(V - 0.30) * 400 - 1.2), pal['black'])
            img = mix(img, aa(np.abs(V - 0.52) * 400 - 1.0), pal['navy_l'])        # elbow seam
            img = mix(img, aa((0.93 - V) * 400), pal['black'])                    # wrist seal
            return img
        sl.paint = sp; P.append(sl)

    P += pt
    hip = pt[0]

    # knee pads
    for s in 'LR':
        lb = piece_bvh(pt[1] if s == 'L' else pt[2])
        sg = 1 if s == 'L' else -1
        kp = surface_patch('KneePad_' + s, lb, lambda u, t, sg=sg: Vector((sg * (0.15 + u * 0.2), 0, 1.07 + t * 0.22)),
                           Vector((0, 1, 0)), 0.012, 5, 5, col='black', th=0.025, group='Bottom')
        kp.rigid = True; kp.rect_key = 'KneePad'; P.append(kp)

    # ---------------- weight belt with lead blocks ----------------
    belt = band('WeightBelt', 2.08, 2.27, 0.014, th=0.022, bvh=piece_bvh(suit, hip), hang=2.38, group='Extras')
    belt.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa(np.minimum(V - 0.1, 0.9 - V) * -200), pal['rubber'])
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.175)), Vector((0, 1, 0)))
    P.append(prim_rbox('BeltBuckle', loc + n * 0.025, (0.2, 0.045, 0.15), 'steel', bevel=0.015))
    P.append(prim_box('BuckleBar', loc + n * 0.05, (0.13, 0.012, 0.03), 'lead_d'))
    for k, az in enumerate((0.55, -0.55, 1.0, -1.0, 2.15, -2.15)):
        d = Vector((math.sin(az), -math.cos(az), 0))
        l2, n2 = project(bb, d * 1.5 + Vector((0, 0, 2.175)), -d)
        n2 = Vector((n2.x, n2.y, 0)).normalized()
        R = Matrix.Rotation(math.atan2(n2.x, -n2.y), 3, 'Z')
        P.append(prim_rbox(f'LeadBlock{k}', l2 + n2 * 0.04, (0.15, 0.07, 0.15), 'lead', rot=R, bevel=0.012))
        P.append(prim_box(f'LeadKeeper{k}', l2 + n2 * 0.078, (0.04, 0.012, 0.165), 'black', rot=R))
    for q in P:
        if q.name.startswith(('BeltBuckle', 'BuckleBar', 'LeadBlock', 'LeadKeeper')): q.bone = 'LowerTorso'

    # ---------------- twin tanks on the back ----------------
    tb = piece_bvh(suit)
    bk, bn = project(tb, Vector((0, 0, 2.62)), Vector((0, -1, 0)))
    yb = bk.y + 0.02
    tank_parts = []
    tank_parts.append(prim_rbox('BackPlate', Vector((0, yb + 0.0, 2.62)), (0.5, 0.11, 0.8), 'black', bevel=0.03))
    tr, ty = 0.16, yb + 0.03 + 0.16
    for sg in (-1, 1):
        x = 0.172 * sg
        tank_parts.append(prim_cyl(f'Tank{sg}', Vector((x, ty, 2.36)), Vector((x, ty, 2.95)), tr, n=16, col='yellow', caps=False))
        tank_parts.append(prim_sphere(f'TankTop{sg}', Vector((x, ty, 2.95)), tr, 'yellow', nl=6, seg=16, scale=(1, 1, 0.75)))
        tank_parts.append(prim_sphere(f'TankBot{sg}', Vector((x, ty, 2.36)), tr, 'yellow', nl=6, seg=16, scale=(1, 1, 0.55)))
        for zb in (2.42, 2.82):
            tank_parts.append(prim_cyl(f'TankBand{sg}{zb}', Vector((x, ty, zb - 0.03)), Vector((x, ty, zb + 0.03)), tr + 0.012, n=16, col='lead'))
        tank_parts.append(prim_cyl(f'TankNeck{sg}', Vector((x, ty, 3.03)), Vector((x, ty, 3.1)), 0.04, n=8, col='steel'))
    # valve manifold + handwheels
    tank_parts.append(prim_cyl('Manifold', Vector((-0.24, ty, 3.12)), Vector((0.24, ty, 3.12)), 0.035, n=8, col='steel'))
    tank_parts.append(prim_cyl('IsoValve', Vector((0, ty, 3.12)), Vector((0, ty + 0.1, 3.12)), 0.03, n=8, col='steel'))
    tank_parts.append(prim_cyl('IsoWheel', Vector((0, ty + 0.1, 3.12)), Vector((0, ty + 0.13, 3.12)), 0.06, n=10, col='black'))
    for sg in (-1, 1):
        tank_parts.append(prim_cyl(f'ValveWheel{sg}', Vector((0.24 * sg, ty, 3.12)), Vector((0.28 * sg, ty, 3.12)), 0.06, n=10, col='black'))
    # first stage regulator on the right valve
    fs = Vector((-0.17, ty - 0.02, 3.2))
    tank_parts.append(prim_rbox('FirstStage', fs, (0.1, 0.1, 0.1), 'lead', bevel=0.02))
    for q in tank_parts:
        q.bone = 'UpperTorso'; head_clear(q, 0.04)
    P += tank_parts

    # ---------------- regulator hose over the right shoulder -> second stage on the chest ----------------
    up = B.bvh['torso_up']
    def shoulder_top(x, y):
        h = up.ray_cast(Vector((x, y, 4.2)), Vector((0, 0, -1)), 2.0)
        return h[0].z if h[0] else 3.2
    hp = [fs + Vector((0, 0, 0.04)), Vector((-0.24, ty - 0.08, 3.32))]
    for y in (0.28, 0.1, -0.08):
        hp.append(Vector((-0.36, y, shoulder_top(-0.36, y) + 0.07)))
    front = []
    for z in (2.98, 2.82, 2.68):
        l3, n3 = project(tb, Vector((-0.32, 0, z)), Vector((0, 1, 0)))
        front.append(l3 + n3 * 0.06)
    hp += front
    hp = smooth_line(polyline_resample(hp, 16), 2)
    hose = tube_path('RegHose', hp, 0.032, 'black', n=8, caps=True)
    head_clear(hose, 0.05); body_clear(hose, 0.045)
    hose.bone = 'UpperTorso'; P.append(hose)
    ss = hp[-1] + Vector((0, -0.04, -0.07))
    reg = [prim_rbox('Regulator', ss, (0.15, 0.12, 0.15), 'black', bevel=0.03),
           prim_cyl('PurgeBtn', ss + Vector((0, -0.06, 0)), ss + Vector((0, -0.085, 0)), 0.05, n=10, col='yellow'),
           prim_cyl('Mouthpiece', ss + Vector((0.06, -0.02, -0.01)), ss + Vector((0.12, -0.03, -0.01)), 0.035, n=8, col='rubber'),
           prim_box('Exhaust', ss + Vector((0, -0.02, -0.08)), (0.12, 0.08, 0.04), 'lead_d')]
    for q in reg: q.bone = 'UpperTorso'; body_clear(q, 0.03)
    P += reg

    # ---------------- dive mask hanging on the chest from its strap ----------------
    mloc, mn = project(tb, Vector((0.05, 0, 2.56)), Vector((0, 1, 0)))
    mc = mloc + mn * 0.055
    tilt = Matrix.Rotation(-0.25, 3, 'X')
    mask = [prim_rbox('MaskSkirt', mc, (0.46, 0.08, 0.25), 'black', rot=tilt, bevel=0.03),
            prim_rbox('MaskFrame', mc + tilt @ Vector((0, -0.04, 0.01)), (0.42, 0.03, 0.21), 'yellow', rot=tilt, bevel=0.015),
            prim_rbox('MaskLensL', mc + tilt @ Vector((0.09, -0.056, 0.015)), (0.155, 0.012, 0.14), 'glass', rot=tilt, bevel=0.01),
            prim_rbox('MaskLensR', mc + tilt @ Vector((-0.09, -0.056, 0.015)), (0.155, 0.012, 0.14), 'glass', rot=tilt, bevel=0.01),
            prim_rbox('MaskNose', mc + tilt @ Vector((0, -0.055, -0.095)), (0.1, 0.05, 0.08), 'black', rot=tilt, bevel=0.02)]
    # strap: mask sides -> up the chest -> round the back of the neck (outside the neck seal)
    sp = []
    for sg in (1, -1):
        side = [mc + Vector((0.23 * sg, 0.0, 0.0))]
        for x, z in ((0.24, 2.72), (0.27, 2.9), (0.3, 3.05)):
            l4, n4 = project(tb, Vector((x * sg + 0.02, 0, z)), Vector((0, 1, 0)))
            side.append(l4 + n4 * 0.03)
        if sg == -1: side = side[::-1]
        sp.append(side)
    ring = []
    for k in range(9):
        a = 0.85 + (2 * PI - 1.7) * k / 8          # from the front-left round the back to the front-right
        dv = Vector((math.sin(a), -math.cos(a), 0))
        r = 0.34
        ring.append(Vector((dv.x * r, dv.y * r, shoulder_top(dv.x * r, dv.y * r) + 0.03)))
    strap_pts = sp[0] + ring + sp[1]
    strap_pts = smooth_line(polyline_resample(strap_pts, 34), 2)
    strap = tube_path('MaskStrap', strap_pts, 0.018, 'black', n=6, caps=True)
    head_clear(strap, 0.04); body_clear(strap, 0.03)
    mask.append(strap)
    for q in mask: q.bone = 'UpperTorso'
    P += mask

    # ---------------- foot pockets + long yellow fins ----------------
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('FinPocket_' + s, s, off=0.072, bulk=0.03, toe=0.02, sole_h=0.04, open_elev=44)
        sh.paint = lambda U, V, m: mix(mix(P_solid(pal['yellow'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), pal['black']),
                                       aa(np.abs(zc(U, V, m)[0] - 0.56) * 500 - 5), pal['black'])
        P.append(sh)
        P.append(_shin28(leg_tube('AnkleSeal_' + s, s, 0.68, 0.54, 0.075, nseg=16, nrows=3, group='Feet', col='black',
                                  extra=lambda z, a: 0.01)))
        fy = min(p.y for p in sh.verts)
        blade, ctrs = _fin_blade('FinBlade_' + s, s, fy + 0.16, fy - 0.6, 0.28, 0.44, 0.306, 0.028, 0.03, 'yellow')
        blade.rect_key = 'FinBlade'; P.append(blade)
        # raised black side rails + tip bumper
        for e in (-1, 1):
            rp = []
            for k, c in enumerate(ctrs):
                f = k / (len(ctrs) - 1)
                w = 0.28 + (0.44 - 0.28) * f ** 0.8
                rp.append(c + Vector((e * (w / 2 - 0.015), 0, 0.016)))
            rail = tube_path(f'FinRail_{s}{e}', rp, 0.022, 'black', n=6, group='Feet', rfn=lambda t: 0.024 - 0.008 * t)
            rail.bone = blade.bone; P.append(rail)
        # vent channel stripes
        for e in (-1, 1):
            vp = [ctrs[k] + Vector((e * 0.07, 0, 0.018 - 0.006 * k / 8)) for k in range(3, len(ctrs) - 1)]
            vs = tube_path(f'FinVent_{s}{e}', vp, 0.012, 'yellow_d', n=5, group='Feet')
            vs.bone = blade.bone; P.append(vs)
        # heel strap with buckles
        pts = [Vector((0.255 * sg + 0.17 * math.cos(a), 0.0 + 0.17 * math.sin(a), 0.5)) for a in np.linspace(0.1, PI - 0.1, 9)]
        hs = tube_path('HeelStrap_' + s, pts, 0.028, 'black', n=6, group='Feet')
        body_clear(hs, 0.03); hs.bone = blade.bone; P.append(hs)

    # ---------------- dive knife on the right calf ----------------
    c = leg_point('R', 0.78)
    kx = c.x - 0.235
    knife = [prim_rbox('KnifeSheath', Vector((kx, c.y - 0.02, 0.78)), (0.05, 0.11, 0.3), 'black', bevel=0.02, group='Bottom'),
             prim_cyl('KnifeGrip', Vector((kx, c.y - 0.02, 0.93)), Vector((kx, c.y - 0.02, 1.03)), 0.032, n=8, col='yellow', group='Bottom'),
             prim_cyl('KnifePommel', Vector((kx, c.y - 0.02, 1.03)), Vector((kx, c.y - 0.02, 1.05)), 0.036, n=8, col='lead', group='Bottom')]
    for q in knife: q.bone = 'RightLowerLeg'
    P += knife
    for z0, z1 in ((0.9, 0.86), (0.7, 0.66)):
        P.append(_shin28(leg_tube(f'KnifeStrap{z0}_R', 'R', z0, z1, 0.06, nseg=16, nrows=2, group='Bottom', col='black',
                                  extra=lambda z, a: 0.06 * max(0.0, math.cos(a + PI / 2)) ** 2)))
    return P, pal
