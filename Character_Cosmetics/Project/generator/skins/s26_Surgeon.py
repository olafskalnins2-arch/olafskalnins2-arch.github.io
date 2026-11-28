from o04 import *
NUM, NAME, RARITY, MAXD = '26', 'Surgeon', 'Rare', 0.7


def _rotz_to(n):
    """rotation about Z that turns local -Y (front face) towards the horizontal part of normal n"""
    return Matrix.Rotation(math.atan2(n.x, -n.y), 3, 'Z')


def build():
    pal = {'teal': '#2fa39a', 'teal_d': '#23807a', 'teal_l': '#46b8ae', 'white': '#f8f8f8', 'white_d': '#dde1e4',
           'white_p': '#eef0f2', 'clog': '#f4f4f4', 'clog_d': '#c9cdd1', 'sole': '#9aa0a6', 'steth': '#3a3d42',
           'silver': '#c4c8cd', 'black': '#18191b', 'blue': '#2c62c9', 'red': '#c8312a', 'photo': '#8aa6c4',
           'ink': '#4a4f56', 'card': '#ffffff'}
    P = []
    # ---- scrubs: trousers first, then the V-neck top hanging over them ----
    pt = pants('Scrubs', 2.2, 0.52, 0.04, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.03 * max(0, 1.4 - z))
    def ppaint(U, V, m):
        img = P_solid(pal['teal'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.007) * 300) * 0.7, pal['teal_d'])   # side seams
        if m.get('kind') == 'leg': img = mix(img, aa((z - (m['zmin'] + 0.05)) * 600), pal['teal_d'])  # hem
        return img
    for p in pt: p.paint = ppaint
    top = torso_shell('ScrubTop', 2.0, 0.045, nseg=32, extra=lambda z, a: 0.012, th=0.02, hang=2.3, over=pt)
    def tpaint(U, V, m):
        img = P_solid(pal['teal'])(U, V, m); z, az = zc(U, V, m)
        w = np.clip((z - 2.78) * 0.75, 0, 1)        # V-neck
        img = mix(img, aa((np.abs(az) - w - 0.06) * 300) * (z > 2.74), pal['teal_d'])
        img = mix(img, aa((np.abs(az) - w) * 300) * (z > 2.78), SKIN)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.007) * 300) * 0.7, pal['teal_d'])
        img = mix(img, aa((z - (m['zmin'] + 0.05)) * 600), pal['teal_d'])
        return img
    top.paint = tpaint; P.append(top)
    P += pt
    # ---- long white lab coat, open at the front, to the knee ----
    def ow(z): return 0.4 if z < 2.8 else 0.4 + (z - 2.8) * 0.5
    def ckeep(i, j, zc_, az): return abs(az) > ow(zc_)
    coat = torso_shell('LabCoat', 1.15, 0.11, nseg=36, extra=lambda z, a: 0.012 + 0.07 * max(0, 2.05 - z), keep=ckeep,
                       th=0.025, hang=2.3, over=pt + [top])
    def cpaint(U, V, m):
        img = P_solid(pal['white'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.6, pal['white_d'])          # side seams
        img = mix(img, aa((PI - np.abs(az) - 0.008) * 400) * (z < 1.78), pal['white_d'])               # back vent
        img = mix(img, aa(np.abs(z - 1.78) * 600 - 1) * (PI - np.abs(az) < 0.06), pal['white_d'])     # vent top stitch
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.06)) * 600 - 1) * 0.8, pal['white_d'])            # hem stitch
        img = mix(img, aa(np.abs(z - 2.22) * 600 - 1) * (PI - np.abs(az) < 0.45), pal['white_d'])     # back belt seam
        owz = np.where(z < 2.8, 0.4, 0.4 + (z - 2.8) * 0.5)
        img = mix(img, aa(np.abs(np.abs(az) - owz - 0.07) * 500 - 1) * (z < 2.44), pal['white_d'])     # front facing stitch
        return img
    coat.paint = cpaint; P.append(coat)
    cb = piece_bvh(coat)
    for sg in (-1, 1):   # lapels along the open front edge
        def lap(s, t, sg=sg):
            z = 2.42 + t * 0.72
            x0 = math.sin(ow(z)) * 0.55
            return Vector((sg * (x0 - 0.01 + s * (0.05 + 0.12 * t)), 0, z))
        P.append(surface_patch(f'Lapel{sg}', cb, lap, Vector((0, 1, 0)), 0.014, 4, 7, col='white_d', th=0.015))
    P.append(collar('CoatCollar', 'fold', h=0.08, flare=0.07, open_front=0.5, col='white', fold=0.1, lift=0.02))
    # chest pocket (wearer's left) with pens
    pk = surface_patch('ChestPocket', cb, lambda s, t: Vector((0.22 + s * 0.19, 0, 2.2 + t * 0.2)), Vector((0, 1, 0)), 0.01, 4, 4,
                       col='white_p', th=0.012)
    P.append(pk)
    P.append(surface_patch('ChestPocketHem', cb, lambda s, t: Vector((0.22 + s * 0.19, 0, 2.37 + t * 0.035)), Vector((0, 1, 0)),
                           0.024, 4, 2, col='white_d', th=0.008))
    for k, (x, col, h) in enumerate(((0.26, 'blue', 0.16), (0.31, 'red', 0.14), (0.365, 'silver', 0.17))):
        loc, n = project(cb, Vector((x, 0, 2.36)), Vector((0, 1, 0)))
        b = loc + n * 0.035
        P.append(prim_cyl(f'Pen{k}', b, b + Vector((0, 0, h)), 0.017, n=6, col=col))
        P.append(prim_box(f'PenClip{k}', b + n * 0.018 + Vector((0, 0, h - 0.05)), (0.012, 0.01, 0.07), 'silver' if col != 'silver' else 'ink'))
        if col == 'silver':
            P.append(prim_cyl(f'PenLightTip{k}', b + Vector((0, 0, h)), b + Vector((0, 0, h + 0.02)), 0.02, n=6, col='ink'))
    # hip pockets (follow the coat's hem rule)
    for sg in (-1, 1):
        hp = surface_patch(f'HipPocket{sg}', cb, lambda s, t, sg=sg: Vector((sg * (0.25 + s * 0.21), 0, 1.76 + t * 0.22)),
                           Vector((0, 1, 0)), 0.01, 4, 3, col='white_p', th=0.012)
        hp.skirt = True; P.append(hp)
        hh = surface_patch(f'HipPocketHem{sg}', cb, lambda s, t, sg=sg: Vector((sg * (0.25 + s * 0.21), 0, 1.94 + t * 0.04)),
                           Vector((0, 1, 0)), 0.024, 4, 2, col='white_d', th=0.008)
        hh.skirt = True; P.append(hh)
    # back half-belt with two buttons
    bt = surface_patch('BackTab', cb, lambda s, t: Vector((-0.3 + s * 0.6, 0, 2.18 + t * 0.08)), Vector((0, -1, 0)), 0.012, 6, 2,
                       col='white_p', th=0.012)
    P.append(bt)
    for sg in (-1, 1):
        loc, n = project(cb, Vector((0.22 * sg, 0, 2.22)), Vector((0, -1, 0)))
        P.append(prim_cyl(f'BackButton{sg}', loc + n * 0.02, loc + n * 0.04, 0.026, n=8, col='white_d'))
        P[-1].bone = 'UpperTorso'
    # coat sleeves
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.93, 0.065, extra=lambda t, a: 0.012 + 0.015 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.abs(V - 0.88) * 400 - 1), pal['white_d'])
        P.append(sl)
    # ---- ID badge (wearer's right chest) ----
    loc, n = project(cb, Vector((-0.31, 0, 2.3)), Vector((0, 1, 0)))
    n = Vector((n.x, n.y, 0)).normalized(); R = _rotz_to(n)
    c0 = loc + n * 0.02
    P.append(prim_box('BadgeCard', c0, (0.15, 0.012, 0.2), 'card', rot=R))
    P.append(prim_box('BadgeStripe', c0 + n * 0.008 + Vector((0, 0, 0.07)), (0.15, 0.006, 0.05), 'teal', rot=R))
    P.append(prim_box('BadgePhoto', c0 + n * 0.008 + R @ Vector((-0.035, 0, 0)) + Vector((0, 0, -0.005)), (0.05, 0.006, 0.065), 'photo', rot=R))
    for k, dz in enumerate((0.015, -0.015)):
        P.append(prim_box(f'BadgeText{k}', c0 + n * 0.008 + R @ Vector((0.035, 0, 0)) + Vector((0, 0, dz)), (0.055, 0.006, 0.012), 'ink', rot=R))
    P.append(prim_box('BadgeBar', c0 + n * 0.008 + Vector((0, 0, -0.07)), (0.11, 0.006, 0.014), 'ink', rot=R))
    P.append(prim_box('BadgeClip', c0 + n * 0.006 + Vector((0, 0, 0.115)), (0.04, 0.012, 0.05), 'silver', rot=R))
    for q in P[-7:]: q.bone = 'UpperTorso'
    # ---- stethoscope around the neck ----
    steth = []
    allb = piece_bvh(coat, top, P[[p.name for p in P].index('CoatCollar')], *[p for p in P if p.name.startswith('Lapel')])
    TR = 0.022
    loop = []
    for a in np.linspace(0.5, 2 * PI - 0.5, 17):
        d = Vector((math.sin(a), -math.cos(a), 0))
        q = d * 0.4
        h = allb.ray_cast(Vector((q.x, q.y, 3.8)), Vector((0, 0, -1)), 1.2)
        z = (h[0].z if h[0] else 3.22) + TR + 0.015
        loop.append(Vector((q.x, q.y, z)))
    # loop runs from front-left (a=0.5) around the back to front-right; add the hanging ends
    def hang_pts(sg, z_end):
        out = []
        for k in range(1, 7):
            f = k / 6
            z = 3.15 - (3.15 - z_end) * f
            x = sg * (0.2 - 0.08 * f)
            loc, nn = project(allb, Vector((x, 0, z)), Vector((0, 1, 0)))
            out.append(loc + nn * (TR + 0.012) if loc is not None else Vector((x, -0.45, z)))
        return out
    left = hang_pts(1, 2.58)       # chest piece side (wearer's left)
    right = hang_pts(-1, 2.7)      # ear tubes side
    pts = left[::-1] + loop + right
    pts = smooth_line(polyline_resample(pts, 40), 2)
    tb = tube_path('StethTube', pts, TR, 'steth', n=6); steth.append(tb)
    # chest piece
    e = pts[0]; loc, nn = project(allb, e + Vector((0, 0, -0.07)), Vector((0, 1, 0)))
    cp = loc + nn * 0.012
    steth.append(prim_cyl('StethStem', e, cp + nn * 0.03 + Vector((0, 0, 0.02)), 0.014, n=6, col='silver'))
    steth.append(prim_cyl('StethBell', cp, cp + nn * 0.045, 0.065, n=14, col='silver'))
    steth.append(prim_cyl('StethDiaphragm', cp + nn * 0.045, cp + nn * 0.052, 0.052, n=14, col='black'))
    # ear tubes: Y-junction with two silver tubes and black tips
    e = pts[-1]
    steth.append(prim_sphere('StethJoint', e, 0.03, 'silver', nl=4, seg=8))
    for sg in (-1, 1):
        a = e + Vector((0.055 * sg, 0, -0.06)); b = a + Vector((0.01 * sg, 0, -0.13))
        loc_a, na = project(allb, a, Vector((0, 1, 0))); loc_b, nb = project(allb, b, Vector((0, 1, 0)))
        a = loc_a + na * 0.03; b = loc_b + nb * 0.03
        steth.append(tube_path(f'StethEar{sg}', [e, a, b], 0.013, 'silver', n=6))
        steth.append(prim_sphere(f'StethTip{sg}', b + Vector((0, 0, -0.015)), 0.026, 'black', nl=4, seg=8))
    for q in steth:
        q.bone = 'UpperTorso'; q.rigid = True; head_clear(q, 0.03)
    P += steth
    # ---- white clogs ----
    for s in 'LR':
        sh = shoe('Clog_' + s, s, off=0.045, bulk=0.035, toe=0.05, sole_h=0.07, open_elev=40)
        def cpnt(U, V, m):
            img = P_solid(pal['clog'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            x, zz = phys(U, V, m)
            holes = (np.hypot((x * 14) % 1 - 0.5, (zz * 14) % 1 - 0.5) < 0.22) & (V > 0.55)
            return mix(img, holes.astype(float), pal['clog_d'])
        sh.paint = cpnt; P.append(sh)
        sg = 1 if s == 'L' else -1
        spts = [Vector((0.255 * sg + 0.16 * math.cos(a), 0.05 + 0.2 * math.sin(a), 0.42)) for a in np.linspace(0.15, PI - 0.15, 7)]
        hs = tube_path('HeelStrap_' + s, spts, 0.025, 'clog_d', n=6, group='Feet'); hs.rigid = True
        body_clear(hs, 0.02); P.append(hs)
    return P, pal
