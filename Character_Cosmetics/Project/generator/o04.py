from o03 import *
from garments import _grid_with_ij
from mathutils.bvhtree import BVHTree

def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def side_bvh(side):
    key = 'shoulder_' + side
    if key not in B.bvh:
        tris = [t for t in B.tris if (B.part[t[0]] == 'arm_' + side) or (B.part[t[0]] == 'torso' and min(B.V[i].z for i in t) > 2.35)]
        B.bvh[key] = BVHTree.FromPolygons(B.V, tris, all_triangles=True)
    return B.bvh[key]

def dome(name, side, center, off, elevs, nseg=18, extra=None, group='Top', th=0.025, col=None):
    bv = side_bvh(side)
    D = hdirs_b(nseg); rows = []; hints = []
    for e in elevs:
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        ex = (lambda j, p, e=e: extra(e, azb(j, nseg))) if extra else None
        rows.append(ray_ring(bv, center, dirs, off, R=0.9, extra=ex, smooth=2)); hints.append(dirs)
    top = bv.ray_cast(center + Z * 0.9, -Z, 0.9)
    pc = _grid_with_ij(name, rows, True, [i / (len(rows) - 1) for i in range(len(rows))], hints, group, col,
                       cap_end=(top[0] + Z * off) if top[0] else center + Z * 0.3)
    if th: thicken(pc, th)
    return pc

def metal_paint(base='#9ea5ad', dark='#5f656d', light='#d3d8de', lines=()):
    def f(U, V, m):
        img = P_solid(base)(U, V, m)
        z, az = zc(U, V, m) if 'zmax' in m else (V, 2 * PI * (U - 0.5))
        img = mix(img, (0.5 + 0.5 * np.cos(az * 3)) * 0.45, light)
        img = mix(img, (0.5 - 0.5 * np.cos(az * 3)) * 0.25, dark)
        for L in lines:
            img = mix(img, aa(np.abs(z - L) * 500 - 1.0), dark)
        return img
    return f

def knight():
    pal = {'steel': '#b9bec5', 'steel_d': '#80868e', 'steel_l': '#d7dbe0', 'leather': '#5a3b22', 'rivet': '#8d939b', 'mail': '#6f747b'}
    P = []
    cu = torso_shell('Cuirass', 2.2, 0.085, nseg=32, extra=lambda z, a: 0.012 + 0.05 * max(0, 1 - abs(a) / 0.7) * max(0, min(1, (3.0 - z) / 0.3)) * max(0, min(1, (z - 2.25) / 0.2)), th=0.03)
    cu.paint = metal_paint(lines=(2.32, 2.62)); cu.sharp = True; P.append(cu)
    P.append(collar('Gorget', 'stand', h=0.05, flare=0.05, col='steel_d'))
    for k, (z0, z1, off) in enumerate(((2.06, 2.26, 0.105), (1.92, 2.11, 0.125), (1.78, 1.97, 0.145))):
        fd = torso_shell(f'Fauld{k}', z0, off, nseg=32, zs=[z0, z1], elevs=(), extra=lambda z, a, z1=z1: 0.03 * (z1 - z) / 0.2, th=0.02, group='Bottom')
        fd.paint = metal_paint(lines=(z0 + 0.012,)); P.append(fd)
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        pd = dome('Pauldron_' + s, s, Vector((0.58 * sg, 0.0, 2.86)), 0.07, (-30, -12, 8, 28, 48, 68), extra=lambda e, a: 0.04 * max(0, (10 - e) / 40))
        pd.paint = metal_paint(lines=(0.18, 0.4)); pd.meta.update(circ=1.6); pd.rect_key = 'Pauldron'; pd.bone = 'UpperTorso'; P.append(pd)
        pd2 = dome('PauldronLame_' + s, s, Vector((0.58 * sg, 0.0, 2.86)), 0.11, (-42, -26, -12), extra=lambda e, a: 0.03)
        pd2.paint = metal_paint(); pd2.rect_key = 'Lame'; pd2.bone = 'UpperTorso'; P.append(pd2)
        vb = sleeve('Vambrace_' + s, s, 0.52, 0.95, 0.045, cap=False, extra=lambda t, a: 0.015 + 0.05 * max(0, 1 - (t - 0.52) / 0.12) + 0.04 * max(0, (t - 0.86) / 0.09))
        vb.paint = metal_paint(lines=(0.2, 0.8)); vb.sharp = True; P.append(vb)
        P.append(sleeve('VambraceStrap_' + s, s, 0.70, 0.74, 0.07, nrows=2, cap=False, col='leather'))
        P.append(sleeve('Couter_' + s, s, 0.44, 0.54, 0.06, nrows=3, cap=False, col='steel_d', extra=lambda t, a: 0.03 * max(0, math.cos(a + PI)) + 0.01))
        cuis = leg_tube('Cuisse_' + s, s, 1.95, 1.3, 0.05, extra=lambda z, a: 0.015)
        cuis.paint = metal_paint(lines=(1.5, 1.7)); P.append(cuis)
        knee = leg_tube('Poleyn_' + s, s, 1.36, 1.05, 0.08, nrows=5, extra=lambda z, a: 0.06 * max(0, math.cos(a)) * math.sin(PI * (z - 1.05) / 0.31))
        knee.paint = metal_paint(base='#c4c9cf', lines=(1.2,)); P.append(knee)
        gr = _shin(leg_tube('Greave_' + s, s, 1.1, 0.52, 0.05, extra=lambda z, a: 0.012 + 0.03 * max(0, (0.65 - z) / 0.13)))
        gr.paint = metal_paint(lines=(0.7, 0.95)); P.append(gr)
        sb = shoe('Sabaton_' + s, s, off=0.05, bulk=0.03, toe=0.06, sole_h=0.04)
        def sp(U, V, m):
            img = metal_paint()(U, V, m); z, az = zc(U, V, m)
            for L in (0.4, 0.45, 0.5): img = mix(img, aa(np.abs(z - L) * 600 - 1) * (np.cos(az) > 0.2), pal['steel_d'])
            return mix(img, aa((z - m['sole_top']) * 600), '#3d3f43')
        sb.paint = sp; P.append(sb)
    # mail skirt underneath faulds
    ms = torso_shell('MailSkirt', 1.82, 0.06, nseg=32, zs=[1.82, 2.0, 2.15], elevs=(), th=0.015, col='mail', group='Bottom')
    P.append(ms)
    for s in 'LR':
        P.append(leg_tube('MailLeg_' + s, s, 1.98, 1.28, 0.035, col='mail', th=0.012))
    return P, pal

def astronaut():
    pal = {'w': '#f2f2f0', 'w_d': '#d9dadb', 'g': '#9aa0a8', 'g_d': '#6c727a', 'dark': '#3c4148', 'red': '#d23b2f', 'blue': '#3a8de0',
           'screen': '#5a6068', 'dial': '#e8e8e8'}
    P = []
    pt = pants('SuitPants', 2.12, 0.62, 0.09, hip_off=0.095, leg_extra=lambda z, a: 0.02 + 0.02 * abs(math.sin(z * 6)))
    tor = torso_shell('Suit', 1.86, 0.1, nseg=32, extra=lambda z, a: 0.02, th=0.03, hang=2.3, over=pt)
    def tp(U, V, m):
        img = P_solid(pal['w'])(U, V, m); z, az = zc(U, V, m)
        # harness straps over shoulders (front & back), chest strap
        for c in (0.42, PI - 0.42):
            img = mix(img, aa((np.abs(np.abs(az) - c) - 0.055) * 400) * (z > 2.3), pal['g'])
        img = mix(img, aa(np.abs(z - 2.38) * 500 - 18), pal['g'])
        img = mix(img, aa((np.abs(az) - 0.01) * 400) * (z < 2.3), pal['w_d'])
        return img
    tor.paint = tp; P.append(tor)
    P.append(collar('NeckRing', 'stand', h=0.05, flare=0.05, col='g', th=0.03))
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.93, 0.085, extra=lambda t, a: 0.02 + 0.022 * abs(math.sin(t * PI * 4.5)))
        sl.paint = lambda U, V, m: mix(mix(P_solid(pal['w'])(U, V, m), aa(np.abs(V - 0.5) * 400 - 8), pal['g']), aa(np.abs(V - 0.04) * 400 - 6), pal['g'])
        P.append(sl)
        P.append(sleeve('WristRing_' + s, s, 0.9, 0.98, 0.115, nrows=3, cap=False, col='g'))
    for p in pt: p.paint = P_solid(pal['w'])
    P += pt
    for s in 'LR':
        lb = piece_bvh(pt[1] if s == 'L' else pt[2])
        sg = 1 if s == 'L' else -1
        kp = surface_patch('KneePad_' + s, lb, lambda u, t, sg=sg: Vector((sg * (0.13 + u * 0.24), 0, 1.06 + t * 0.26)), Vector((0, 1, 0)), 0.02, 5, 5, col='g_d', th=0.04, group='Bottom')
        kp.rigid = True; P.append(kp)
        b = shoe('Boot_' + s, s, off=0.07, bulk=0.06, toe=0.03, sole_h=0.07)
        b.paint = lambda U, V, m: mix(P_solid(pal['w'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), pal['g_d'])
        P.append(b)
        P.append(_shin(leg_tube('BootShaft_' + s, s, 0.8, 0.46, 0.13, nseg=16, group='Feet', col='w', extra=lambda z, a: 0.01)))
        P.append(_shin(leg_tube('BootRing_' + s, s, 0.84, 0.76, 0.16, nseg=16, nrows=2, group='Feet', col='g')))
    belt = band('Belt', 2.02, 2.2, 0.02, th=0.025, col='g', bvh=piece_bvh(tor)); P.append(belt)   # fitted on the suit
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.11)), Vector((0, 1, 0)))
    P.append(prim_rbox('BeltBuckle', loc + n * 0.03, (0.22, 0.06, 0.15), 'g_d'))
    for sg in (-1, 1):
        l2, n2 = project(bb, Vector((0.3 * sg, 0, 2.08)), Vector((0, 1, 0)))
        P.append(prim_rbox(f'BeltPouch{sg}', l2 + n2 * 0.06, (0.16, 0.1, 0.18), 'w_d'))
    tb = piece_bvh(tor)
    loc, n = project(tb, Vector((0, 0, 2.72)), Vector((0, 1, 0)))
    pc0 = loc + n * 0.045
    P.append(prim_rbox('ChestPanel', pc0, (0.44, 0.08, 0.32), 'g'))
    f = pc0 + Vector((0, -0.045, 0))
    P.append(prim_cyl('Gauge', f + Vector((-0.1, 0, 0.06)), f + Vector((-0.1, -0.02, 0.06)), 0.065, n=12, col='dial'))
    P.append(prim_box('GaugeNeedle', f + Vector((-0.1, -0.025, 0.07)), (0.07, 0.006, 0.01), 'dark', rot=Matrix.Rotation(0.6, 3, 'Y')))
    P.append(prim_cyl('Dial', f + Vector((0.1, 0, 0.07)), f + Vector((0.1, -0.025, 0.07)), 0.05, n=10, col='dial'))
    P.append(prim_box('DialMark', f + Vector((0.1, -0.03, 0.09)), (0.01, 0.006, 0.04), 'dark'))
    P.append(prim_box('Screen', f + Vector((-0.08, -0.005, -0.08)), (0.16, 0.02, 0.09), 'screen'))
    P.append(prim_box('BtnBlue', f + Vector((0.11, -0.01, -0.05)), (0.05, 0.025, 0.035), 'blue'))
    P.append(prim_box('BtnRed', f + Vector((0.11, -0.01, -0.1)), (0.05, 0.025, 0.035), 'red'))
    # backpack
    loc, n = project(tb, Vector((0, 0, 2.68)), Vector((0, -1, 0)))
    P.append(prim_rbox('Backpack', loc + Vector((0, 0.2, 0.05)), (0.72, 0.36, 0.92), 'w_d'))
    P.append(prim_box('BackpackVent', loc + Vector((0, 0.385, 0.25)), (0.4, 0.02, 0.12), 'g'))
    P.append(prim_box('BackpackVent2', loc + Vector((0, 0.385, -0.15)), (0.4, 0.02, 0.12), 'g'))
    for k in P[-3:]: k.bone = 'UpperTorso'
    return P, pal

def weights_at_parts(p, parts):
    co, i, d = min(((co, i, d) for co, i, d in B.kd.find_range(p, 1.5) if B.part[i] in parts), key=lambda x: x[2])
    return B.W[i]

def ghost():
    pal = {'sheet': '#f4f4f2', 'hole': '#4a2512', 'hole_rim': '#d8d8d4'}
    nseg = 40
    D = hdirs_b(nseg)
    allb = B.bvh['all']
    def need(c, dirs):
        out = []
        for d in dirs:
            h = allb.ray_cast(c + d * 2.2, -d, 2.2)
            out.append((h[0] - c).dot(d) if h[0] else 0.0)
        return out
    rows = []; zrow = []
    hc = Vector((0, 0, 4.0))
    for e in (84, 70, 55, 40, 25, 10):
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        nd = need(hc, dirs)
        base = 0.86
        r = [max(base, n + 0.07) for n in nd]
        for _ in range(3): r = [max(r[j], (r[j - 1] + r[j] + r[(j + 1) % nseg]) / 3) for j in range(nseg)]
        rows.append([hc + dirs[j] * r[j] for j in range(nseg)]); zrow.append(None)
    # body part: smooth bell envelope that clears every body point (arms/hands included)
    zs = list(np.arange(3.9, 0.36, -0.13)) + [0.36]
    needs = [need(Vector((0, 0, z)), D) for z in zs]
    nmax = [max(n) for n in needs]
    slope = 0.22
    prof = []
    for a, z in enumerate(zs):
        r = 0.86
        for b, z2 in enumerate(zs):
            if z2 >= z: r = max(r, nmax[b] + 0.1)
            else: r = max(r, nmax[b] + 0.1 - slope * (z - z2))
        prof.append(r)
    for a, z in enumerate(zs):
        t = max(0, (3.6 - z) / 3.2)
        ring = []
        for j, d in enumerate(D):
            az = azb(j, nseg)
            fold = 0.05 * t * (0.5 + 0.5 * math.sin(9 * az + 0.7))
            rr = max(prof[a] + fold, needs[a][j] + 0.08)
            zz = z + (0.06 * math.sin(9 * az + 0.7) if z < 0.4 else 0)
            ring.append(Vector((d.x * rr, d.y * rr, zz)))
        rows.append(ring)
    toph = allb.ray_cast(hc + Z * 2, -Z, 2)
    topz = (toph[0].z + 0.07) if toph[0] else hc.z + 0.86
    pc = _grid_with_ij('Sheet', rows, True, None, [[(p - Vector((0, 0, p.z))) + Z * 0.3 for p in r] for r in rows], 'Top', 'sheet',
                       cap_start=Vector((0, 0, max(topz, rows[0][0].z + 0.02))))
    def gw(p):
        w = np.zeros(len(BONES))
        hz = 3.45; lz = 3.0
        if p.z >= hz: w[2] = 1.0
        elif p.z > lz:
            f = (p.z - lz) / (hz - lz); w[2] = f; w[1] = 1 - f
        else:
            f = min(1, max(0, (p.z - 2.0) / 1.0)); w[1] = f * 0.85; w[0] = 1 - f * 0.85
        # let the sheet bulge with the arms / legs underneath so they never poke through
        for parts, rad, kmax in ((('arm_L', 'arm_R'), 0.7, 0.6), (('torso',), 0.5, 0.0)):
            if kmax == 0: continue
            best = min(((co - p).length for co, i, d in B.kd.find_range(p, rad) if B.part[i] in parts), default=None)
            if best is None: continue
            k = kmax * max(0.0, 1 - best / rad)
            wa = weights_smooth(p, 0.5, parts=parts)
            w = w * (1 - k) + wa * k
        if p.z < 1.3:
            best = min(((co - p).length for co, i, d in B.kd.find_range(p, 0.6) if B.part[i] == 'torso' and B.V[i].z < 1.3), default=None)
            if best is not None:
                k = 0.7 * max(0.0, 1 - best / 0.6)
                w = w * (1 - k) + weights_smooth(p, 0.6, parts=('torso', 'foot_L', 'foot_R')) * k
        return w
    pc.weight = gw; pc.region = 'ghost'
    thicken(pc, 0.025)
    P = [pc]
    sb = piece_bvh(pc)
    for sg in (-1, 1):
        def ov(s, t, sg=sg):
            a = 2 * PI * s
            return Vector((sg * 0.24 + math.cos(a) * 0.11 * t, 0, 4.12 + math.sin(a) * 0.17 * t))
        hole = surface_patch(f'EyeHole{sg}', sb, ov, Vector((0, 1, 0)), 0.012, 16, 3, col='hole', th=0.0, group='Top')
        hole.bone = 'Head'
        P.append(hole)
    return P, pal

def dino():
    pal = {'g': '#3fa535', 'g_d': '#2f8428', 'belly': '#bfe57a', 'or': '#f08a24', 'red': '#e0472b', 'claw': '#f4f1e8'}
    P = []
    bc = (0.0, 2.48); ba, bz = 0.62, 0.5
    def gp(U, V, m):
        img = P_solid(pal['g'])(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'torso':
            d = np.sqrt((az / ba) ** 2 + ((z - bc[1]) / bz) ** 2)
            img = mix(img, aa((d - 1) * 120), pal['belly'])
        return img
    tor = torso_shell('Onesie', 1.88, 0.07, nseg=32, extra=lambda z, a: 0.015, th=0.025)
    tor.paint = gp; P.append(tor)
    pt = pants('OnesieLegs', 2.12, 0.5, 0.065, hip_off=0.11, leg_extra=lambda z, a: 0.025 + 0.02 * max(0, 1.2 - z))
    for p in pt: p.paint = P_solid(pal['g'])
    P += pt
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.40, 0.07, extra=lambda t, a: 0.02 + 0.07 * math.sin(min(1, t / 0.4) * PI * 0.85))
        sl.paint = P_solid(pal['g']); P.append(sl)
        c, tg = arm_point(s, 0.40)
        nfr, bfr = frame(tg, Vector((0, -1, 0)))
        for k, a in enumerate((-0.6, 0.0, 0.6)):
            dirv = (nfr * math.cos(a) + bfr * math.sin(a) * 0.6).normalized()
            base = c + dirv * 0.13 + tg * 0.01
            P.append(prim_cone(f'Claw{s}{k}', base, base + tg * 0.09 + dirv * 0.05, 0.03, 'claw', n=5)); P[-1].region = 'arm_' + s
    hood = head_shell('Hood', 0.075, open_deg=57, nphi=8, npsi=26)
    hood.paint = P_solid(pal['g']); hood.weight = lambda p: weights_at(p) if p.z > 3.35 else weights_smooth(p, 0.3)
    P.append(hood)
    rim = hood.meta['rim']
    rp = [HEAD_C + (p - HEAD_C) * 1.0 for p in rim] + [rim[0]]
    rt = tube_path('HoodRim', rp, 0.05, 'g_d', n=6, group='Head', caps=False)
    rt.region = 'head'; P.append(rt)
    # spikes: over the hood top/back and down the spine
    hb = piece_bvh(hood)
    k = 0
    for ph in (78, 102, 126, 150):
        phr = math.radians(ph)
        d = Vector((0, -math.cos(phr), math.sin(phr)))
        loc, n = project(hb, HEAD_C + d * 1.6, -d)
        size = 0.16 if ph < 140 else 0.13
        P.append(prim_cone(f'Spike{k}', loc - n * 0.03, loc + n * size * 1.6, size * 0.55, 'or' if k % 2 else 'red', n=4, flat=0.35, group='Head'))
        P[-1].weight = lambda p: weights_at(Vector((0, 0, 4.4))); k += 1
    tb = piece_bvh(tor)
    for z in (3.0, 2.72, 2.44):
        loc, n = project(tb, Vector((0, 0, z)), Vector((0, -1, 0)))
        P.append(prim_cone(f'Spike{k}', loc - n * 0.02, loc + n * 0.2, 0.1, 'or' if k % 2 else 'red', n=4, flat=0.35)); k += 1
    # tail
    tail_pts = [Vector(p) for p in ((0, 0.36, 2.12), (0, 0.62, 1.85), (0.03, 0.9, 1.45), (0.12, 1.08, 1.0), (0.3, 1.12, 0.62), (0.5, 1.0, 0.45))]
    tail_pts = smooth_line(polyline_resample(tail_pts, 12), 2)
    tl = tube_path('Tail', tail_pts, 0.2, 'g', n=10, group='Extras', rfn=lambda t: 0.21 * (1 - t) ** 0.9 + 0.02)
    tl.bone = 'LowerTorso'; P.append(tl)
    for i in range(1, 10, 2):
        p = tail_pts[i]; tg = (tail_pts[i + 1] - tail_pts[i - 1]).normalized()
        up = (Z - Z.dot(tg) * tg).normalized()
        r = 0.21 * (1 - i / 11) ** 0.9 + 0.02
        P.append(prim_cone(f'TailSpike{i}', p + up * (r * 0.7), p + up * (r + 0.1), 0.06 * (1 - i / 14), 'or' if i % 4 == 1 else 'red', n=4, flat=0.35, group='Extras'))
        P[-1].bone = 'LowerTorso'
    for s in 'LR':
        ft = shoe('DinoFoot_' + s, s, off=0.07, bulk=0.07, toe=0.07, sole_h=0.04, open_elev=44)
        ft.paint = P_solid(pal['g']); P.append(ft)
        sg = 1 if s == 'L' else -1
        front = min(ft.verts, key=lambda p: p.y)
        for kk, dx in enumerate((-0.1, 0.0, 0.1)):
            base = Vector((0.255 * sg + dx, front.y + 0.04, 0.34))
            P.append(prim_cone(f'ToeClaw{s}{kk}', base, base + Vector((dx * 0.3, -0.1, -0.015)), 0.032, 'claw', n=5, group='Feet'))
    return P, pal
