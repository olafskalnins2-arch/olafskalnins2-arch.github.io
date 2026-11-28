from o04 import *          # garments, pipeline, paints, o02/o03/o04 helpers (dome, _shin, metal_paint)
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '37', 'Mecha_Pilot', 'Epic', 0.32


def _shin37(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _angd(az, c):
    """angular distance between az and c (radians, wraps)"""
    return np.abs(np.remainder(az - c + PI, 2 * PI) - PI)


def _pdome(name, side, center, off, elevs, nseg=18, extra=None, th=0.03, inner_cut=0.0, cut_below=30, xmin=0.36, clear=None, gap=0.035, cap=True, xall=0.3, cast=None):
    '''o04.dome, but rows below `cut_below` degrees keep only the outer side of the shoulder (no flaps running
    across the chest / back toward the neck).'''
    sg = 1 if side == 'L' else -1
    bv = cast if cast is not None else side_bvh(side)                   # cast on the suit + sleeves: sits OVER them
    D = hdirs_b(nseg); rows = []; hints = []
    for e in elevs:
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        ex = (lambda j, p, e=e: extra(e, azb(j, nseg))) if extra else None
        rows.append(ray_ring(bv, center, dirs, off, R=0.9, extra=ex, smooth=2)); hints.append(dirs)
    top = bv.ray_cast(center + Z * 0.9, -Z, 0.9)
    pc = _grid_with_ij(name, rows, True, [i / (len(rows) - 1) for i in range(len(rows))], hints, 'Top', None,
                       cap_end=None if not cap else ((top[0] + Z * off) if top[0] else center + Z * 0.3))
    def keep(ij, f):
        i, j = ij
        if i < 0: return True
        if min(sg * pc.verts[v].x for v in f) < xall: return False      # stay off the neck / collar
        if elevs[min(i + 1, len(elevs) - 1)] >= cut_below: return True   # (i == last row: the top cap fan)
        if min(sg * pc.verts[v].x for v in f) < xmin: return False      # never across the chest / back
        return sg * math.sin(azb(j + 0.5, nseg)) > inner_cut
    filter_faces(pc, keep)
    if clear is not None:     # keep the plate outside the suit / sleeve layers (rays from the shoulder graze the neck side)
        for i, p in enumerate(pc.verts):
            loc, nor, fi, dist = clear.find_nearest(p)
            if loc is None: continue
            if (p - loc).dot(nor) < gap: pc.verts[i] = loc + nor * gap
    if th: thicken(pc, th)
    return pc


def build():
    pal = {'w': '#f2f2f0', 'w_d': '#d6d8da', 'or': '#ff7a1a', 'or_d': '#d95f0b', 'cy': '#18d6e6', 'cy_l': '#bff6fa',
           'dk': '#3c4148', 'dk_d': '#2a2e33', 'g': '#8a9098'}
    W, OR, CY, DK = pal['w'], pal['or'], pal['cy'], pal['dk']
    P = []

    # ---------------- suit legs + hip (one silhouette) ----------------
    pt = pants('SuitLegs', 2.16, 0.6, 0.075, hip_off=0.095, leg_extra=lambda z, a: 0.018 + 0.012 * max(0, 1.25 - z))

    def leg_paint(U, V, m):
        img = P_solid(W)(U, V, m); z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            c = PI / 2 if m.get('side') == 'L' else -PI / 2
            d = _angd(az, c)
            img = mix(img, aa((d - 0.42) * 300), OR)                       # outer orange side panel
            img = mix(img, aa((np.abs(d - 0.5) - 0.04) * 300), CY)            # glowing cyan piping beside it
            img = mix(img, aa(np.abs(z - 1.62) * 500 - 1.2), pal['w_d'])   # thigh seam
        else:
            d = np.abs(np.abs(az) - PI / 2)
            img = mix(img, aa((d - 0.42) * 300), OR)
            img = mix(img, aa((np.abs(d - 0.5) - 0.04) * 300), CY)
        return img
    for p in pt:
        p.paint = leg_paint; p.rect_key = p.name
    hip = pt[0]

    # ---------------- suit body (hangs over the hip) ----------------
    suit = torso_shell('Suit', 1.9, 0.095, nseg=32, extra=lambda z, a: 0.015, th=0.03, hang=2.3, over=pt)

    def suit_paint(U, V, m):
        img = P_solid(W)(U, V, m); z, az = zc(U, V, m)
        d = np.abs(np.abs(az) - PI / 2)
        wdt = 0.36 + 0 * z
        img = mix(img, aa((d - wdt) * 300) * (z < 2.95), OR)               # orange side panels (white under the shoulder plates)
        img = mix(img, aa((np.abs(d - wdt - 0.07) - 0.022) * 300) * (z < 2.95), CY)   # cyan glow line along the panel
        # back: orange spine panel with a cyan core line
        bz = np.abs(np.abs(az) - PI)
        img = mix(img, aa((bz - 0.16) * 300) * (z < 2.95), OR)
        img = mix(img, aa((bz - 0.025) * 300) * (z < 2.95), CY)
        # abdomen armour segments (front)
        fr = np.abs(az) < 0.75
        for L in (2.42, 2.53):
            img = mix(img, aa(np.abs(z - L) * 500 - 1.4) * fr, DK)
        img = mix(img, aa((np.abs(az) - 0.012) * 400) * (z < 2.6) * (z > 2.3), DK)
        # harness / jetpack straps over the shoulders (front and back)
        for c in (0.47, PI - 0.47):
            img = mix(img, aa((np.abs(np.abs(az) - c) - 0.06) * 400) * (z > 2.85), DK)
        # hem: dark band with a cyan line
        img = mix(img, aa((z - (m['zmin'] + 0.06)) * 600), DK)
        img = mix(img, aa((np.abs(z - (m['zmin'] + 0.085)) - 0.009) * 600), CY)
        return img
    suit.paint = suit_paint; P.append(suit)
    P.append(collar('NeckRing', 'stand', h=0.06, flare=0.05, col='dk', th=0.03))
    P += pt

    # ---------------- belt fitted on the suit ----------------
    belt = band('Belt', 2.17, 2.31, 0.016, th=0.025, bvh=piece_bvh(suit))

    def belt_paint(U, V, m):
        img = P_solid(DK)(U, V, m)
        img = mix(img, aa((np.abs(V - 0.5) - 0.07) * 300), CY)
        img = mix(img, aa(np.minimum(V - 0.1, 0.9 - V) * -200), pal['dk_d'])
        return img
    belt.paint = belt_paint; P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.24)), Vector((0, 1, 0)))
    bk = [prim_rbox('Buckle', loc + n * 0.03, (0.22, 0.06, 0.17), 'or', bevel=0.02),
          prim_box('BuckleLight', loc + n * 0.06, (0.12, 0.012, 0.06), 'cy')]
    for sg in (-1, 1):   # side utility pods
        d = Vector((sg * math.sin(1.05), -math.cos(1.05), 0))
        l2, n2 = project(bb, d * 1.5 + Vector((0, 0, 2.23)), -d)
        n2 = Vector((n2.x, n2.y, 0)).normalized()
        R = Matrix.Rotation(math.atan2(n2.x, -n2.y), 3, 'Z')
        bk.append(prim_rbox(f'BeltPod{sg}', l2 + n2 * 0.055 + Vector((0, 0, -0.02)), (0.16, 0.09, 0.19), 'w_d', rot=R, bevel=0.02))
        bk.append(prim_box(f'BeltPodLight{sg}', l2 + n2 * 0.102 + Vector((0, 0, 0.02)), (0.09, 0.01, 0.025), 'cy', rot=R))
    for q in bk: q.bone = 'LowerTorso'
    P += bk

    # ---------------- chest plate + glowing core ----------------
    sb = piece_bvh(suit)

    def plate_pt(s, t):
        z = 2.56 + t * 0.48
        hw = 0.25 + 0.12 * t                                            # wider at the top (pectoral plate)
        return Vector(((s - 0.5) * 2 * hw, 0, z))
    cp = surface_patch('ChestPlate', sb, plate_pt, Vector((0, 1, 0)), 0.02, 9, 7, th=0.045)

    def plate_paint(U, V, m):
        img = P_solid(W)(U, V, m)
        e = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
        img = mix(img, aa((e - 0.09) * 300), OR)                          # orange rim
        img = mix(img, aa((np.abs(e - 0.13) - 0.012) * 400), CY)              # cyan inset line
        img = mix(img, aa(np.abs(V - 0.82) * 400 - 1.0) * (e > 0.13), pal['w_d'])
        return img
    cp.paint = plate_paint; cp.meta['rect'] = (256, 256); cp.bone = 'UpperTorso'; P.append(cp)
    pb = piece_bvh(cp)
    loc, n = project(pb, Vector((0, 0, 2.77)), Vector((0, 1, 0)))
    n = Vector((n.x * 0.3, n.y, n.z)).normalized()                        # face out of the plate (chest leans back)
    core = [prim_cyl('CoreHousing', loc - n * 0.035, loc + n * 0.045, 0.145, 0.135, n=20, col='dk'),
            prim_cyl('CoreRing', loc + n * 0.045, loc + n * 0.06, 0.118, 0.112, n=20, col='or'),
            prim_cyl('CoreGlow', loc + n * 0.05, loc + n * 0.075, 0.095, 0.09, n=20, col='cy'),
            prim_cyl('CoreCenter', loc + n * 0.07, loc + n * 0.085, 0.045, 0.04, n=12, col='cy_l')]
    for k in range(4):   # housing bolts
        a = PI / 4 + k * PI / 2
        bp = loc + Vector((math.cos(a) * 0.128, 0, math.sin(a) * 0.128)) + n * 0.045
        core.append(prim_cyl(f'CoreBolt{k}', bp, bp + n * 0.012, 0.014, n=6, col='g'))
    for sg in (-1, 1):   # small status lights on the plate
        l3, n3 = project(pb, Vector((sg * 0.25, 0, 2.95)), Vector((0, 1, 0)))
        core.append(prim_box(f'PlateLight{sg}', l3 + n3 * 0.006, (0.08, 0.014, 0.03), 'cy'))
    for q in core: q.bone = 'UpperTorso'
    P += core

    # ---------------- arms ----------------
    def sleeve_paint(U, V, m):
        img = P_solid(W)(U, V, m)
        img = mix(img, aa(np.abs(V - 0.5) * 400 - 10), DK)               # elbow joint band
        img = mix(img, aa((np.abs(V - 0.28) - 0.01) * 400), CY)
        return img
    def vamb_paint(U, V, m):
        img = P_solid(W)(U, V, m); z, az = zc(U, V, m)
        d = np.abs(az)                                                     # 0 = front of the forearm
        img = mix(img, aa((np.abs(d - PI / 2) - 0.45) * 300), OR)
        img = mix(img, aa((np.abs(np.abs(d - PI / 2) - 0.52) - 0.04) * 300), CY)
        img = mix(img, aa((V - 0.08) * 400), DK)
        return img
    sleeves = []
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.95, 0.07, extra=lambda t, a: 0.015)
        sl.paint = sleeve_paint; P.append(sl); sleeves.append(sl)
        vb = sleeve('Vambrace_' + s, s, 0.6, 0.9, 0.11, cap=False, extra=lambda t, a: 0.012 + 0.035 * max(0, (t - 0.78) / 0.12))
        vb.paint = vamb_paint; vb.sharp = True; P.append(vb)
        P.append(sleeve('ElbowGuard_' + s, s, 0.45, 0.56, 0.1, nrows=3, cap=False, col='or',
                        extra=lambda t, a: 0.03 * max(0, math.cos(a + PI)) + 0.01))
        P.append(sleeve('WristCuff_' + s, s, 0.9, 0.98, 0.16, nrows=3, cap=False, col='dk'))
        P.append(sleeve('BicepBand_' + s, s, 0.3, 0.36, 0.1, nrows=2, cap=False, col='dk'))

    # ---------------- shoulder plates ----------------
    def pauldron_paint(U, V, m):
        img = P_solid(W)(U, V, m)
        img = mix(img, aa((V - 0.12) * 300), DK)                          # dark edge
        img = mix(img, aa((np.abs(V - 0.2) - 0.02) * 300), CY)               # glowing rim line
        img = mix(img, aa((0.5 - V) * 300), OR)                          # orange top panel
        img = mix(img, aa((np.abs(V - 0.47) - 0.022) * 300), CY)              # glow line round it
        return img
    clr = piece_bvh(suit, *sleeves)
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        pd = _pdome('ShoulderPlate_' + s, s, Vector((0.58 * sg, 0.0, 2.86)), 0.075, tuple(np.linspace(-32, 70, 12)), nseg=24,
                    extra=lambda e, a: 0.05 * max(0, (12 - e) / 44), th=0.035, cast=clr)
        pd.paint = pauldron_paint; pd.meta.update(circ=1.7); pd.rect_key = 'ShoulderPlate'; pd.bone = 'UpperTorso'
        head_clear(pd, 0.04); P.append(pd)
        pl = _pdome('ShoulderLame_' + s, s, Vector((0.58 * sg, 0.0, 2.86)), 0.1, (-40, -28, -16), nseg=24, extra=lambda e, a: 0.02, th=0.03, cap=False, cast=clr)
        pl.paint = lambda U, V, m: mix(P_solid(DK)(U, V, m), aa((np.abs(V - 0.45) - 0.07) * 300), CY)
        pl.rect_key = 'ShoulderLame'; pl.bone = 'UpperTorso'; P.append(pl)

    # ---------------- thigh + knee plates ----------------
    def knee_paint(U, V, m):
        img = P_solid(OR)(U, V, m)
        e = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
        img = mix(img, aa((e - 0.12) * 300), DK)
        r = np.hypot(U - 0.5, V - 0.5)
        img = mix(img, aa((r - 0.13) * 300), CY)
        img = mix(img, aa((r - 0.06) * 300), pal['cy_l'])
        return img
    def thigh_paint(U, V, m):
        img = P_solid(W)(U, V, m)
        e = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
        img = mix(img, aa((e - 0.08) * 300), OR)
        img = mix(img, aa((np.abs(U - 0.5) - 0.035) * 300) * (e > 0.08), CY)
        return img
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        lb = piece_bvh(pt[1] if s == 'L' else pt[2])
        tp = surface_patch('ThighPlate_' + s, lb, lambda u, t, sg=sg: Vector((sg * (0.13 + u * 0.24), 0, 1.38 + t * 0.34)),
                           Vector((0, 1, 0)), 0.015, 5, 5, th=0.03, group='Bottom')
        tp.paint = thigh_paint; tp.meta['rect'] = (128, 128); tp.rect_key = 'ThighPlate'; tp.rigid = True; P.append(tp)
        kp = surface_patch('KneePlate_' + s, lb, lambda u, t, sg=sg: Vector((sg * (0.12 + u * 0.26), 0, 1.03 + t * 0.29)),
                           Vector((0, 1, 0)), 0.03, 6, 6, th=0.05, group='Bottom')
        kp.paint = knee_paint; kp.meta['rect'] = (128, 128); kp.rect_key = 'KneePlate'; kp.rigid = True; P.append(kp)

    # ---------------- armoured boots ----------------
    def boot_paint(U, V, m):
        img = P_solid(OR)(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((z - m['sole_top']) * 600), DK)
        img = mix(img, aa((np.abs(z - m['sole_top'] - 0.025) - 0.01) * 600), CY)
        img = mix(img, aa(np.abs(z - 0.52) * 500 - 1.2) * (np.abs(az) < 0.9), pal['or_d'])
        return img
    def shaft_paint(U, V, m):
        img = P_solid(OR)(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((_angd(az, 0) - 0.55) * -300), W)                 # white shin guard on the front
        img = mix(img, aa((np.abs(_angd(az, 0) - 0.62) - 0.045) * 300), CY)
        for L in (0.6, 0.7):
            img = mix(img, aa(np.abs(z - L) * 500 - 1.0) * (_angd(az, 0) < 0.55), pal['w_d'])
        return img
    for s in 'LR':
        b = shoe('Boot_' + s, s, off=0.075, bulk=0.06, toe=0.05, sole_h=0.08)
        b.paint = boot_paint; P.append(b)
        sh = _shin37(leg_tube('BootShaft_' + s, s, 0.86, 0.46, 0.135, nseg=16, group='Feet', extra=lambda z, a: 0.01))
        sh.paint = shaft_paint; P.append(sh)
        P.append(_shin37(leg_tube('BootCuff_' + s, s, 0.9, 0.82, 0.17, nseg=16, nrows=2, group='Feet', col='dk')))

    # ---------------- compact jetpack ----------------
    loc, n = project(sb, Vector((0, 0, 2.66)), Vector((0, -1, 0)))
    yb = loc.y
    c = Vector((0, yb + 0.17, 2.66))
    jp = [prim_rbox('JetBody', c, (0.6, 0.3, 0.72), 'w', bevel=0.04),
          prim_rbox('JetPlate', Vector((0, yb + 0.03, 2.66)), (0.66, 0.08, 0.6), 'dk', bevel=0.02)]
    for sg in (-1, 1):
        jp.append(prim_rbox(f'JetSide{sg}', c + Vector((sg * 0.29, 0, 0)), (0.07, 0.26, 0.6), 'or', bevel=0.02))
        jp.append(prim_box(f'JetSideLine{sg}', c + Vector((sg * 0.33, 0, 0)), (0.012, 0.18, 0.44), 'cy'))
    jp.append(prim_rbox('JetCover', c + Vector((0, 0.15, 0.06)), (0.4, 0.04, 0.42), 'or', bevel=0.015))
    for k, dz in enumerate((0.17, 0.06, -0.05)):
        jp.append(prim_box(f'JetVent{k}', c + Vector((0, 0.175, dz)), (0.28, 0.012, 0.035), 'cy'))
    jp.append(prim_rbox('JetTop', c + Vector((0, 0.02, 0.38)), (0.44, 0.22, 0.08), 'dk', bevel=0.02))
    zb = c.z - 0.36
    for sg in (-1, 1):
        x = 0.17 * sg; yc = c.y + 0.02
        jp.append(prim_cyl(f'NozzleMount{sg}', Vector((x, yc, zb + 0.04)), Vector((x, yc, zb - 0.03)), 0.09, n=14, col='or'))
        jp.append(prim_cyl(f'Nozzle{sg}', Vector((x, yc, zb - 0.03)), Vector((x, yc, zb - 0.22)), 0.07, 0.105, n=14, col='dk', caps=False))
        jp.append(prim_cyl(f'NozzleRim{sg}', Vector((x, yc, zb - 0.2)), Vector((x, yc, zb - 0.235)), 0.113, n=14, col='g'))
        jp.append(prim_cyl(f'NozzleGlow{sg}', Vector((x, yc, zb - 0.12)), Vector((x, yc, zb - 0.215)), 0.06, 0.092, n=14, col='cy'))
    for q in jp:
        q.bone = 'UpperTorso'; head_clear(q, 0.04)
    P += jp
    return P, pal
