from garments import *
import zlib
from paints import *
SKIN = '#ed7c42'

def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def skin_leg(side, z0, z1, off=0.012):
    '''skin-coloured leg cover so uncovered legs match the orange reference look (body legs are grey).'''
    pc = leg_tube('SkinLeg_' + side, side, z0, z1, off, nseg=16, th=0.008, group='Bottom', smooth=0)
    pc.paint = P_solid(SKIN); pc.rect_key = 'SkinLeg'; pc.cover = True   # thin cover: coverage repair keeps it outside the body
    return pc

def flip_flop(side, pal):
    sg = 1 if side == 'L' else -1
    c = Vector((0.255 * sg, -0.09, 0.40))
    D = hdirs_b(20)
    ring = ray_ring(B.bvh['foot_' + side], c, D, 0.035, R=0.8, smooth=2)
    out = [Vector((p.x, p.y, 0.0)) for p in ring]
    rows = [[Vector((p.x * 0.97 + c.x * 0.03, p.y * 0.97 + c.y * 0.03, 0.288)) for p in out],
            [Vector((p.x, p.y, 0.30)) for p in out], [Vector((p.x, p.y, 0.322)) for p in out],
            [Vector((p.x * 0.97 + c.x * 0.03, p.y * 0.97 + c.y * 0.03, 0.327)) for p in out]]
    pc = grid_piece('FlipSole_' + side, rows, True, col='sole', hints=[[q - c for q in r] for r in rows], group='Feet',
                    cap_start=Vector((c.x, c.y, 0.288)), cap_end=Vector((c.x, c.y, 0.327)))
    for i, p in enumerate(pc.verts):
        if abs(p.z - 0.30) < 0.001 or abs(p.z - 0.288) < 0.001: pass
    # colour the top layer differently
    pc.fcol = ['sole_top' if all(pc.verts[i].z > 0.31 for i in f) else 'sole' for f in pc.faces]
    pc.rigid = True
    P = [pc]
    # straps: toe post -> over foot -> sides
    fb = B.bvh['foot_' + side]
    def onfoot(x, y, lift=0.022):
        loc, n = project(fb, Vector((x, y, 0.62)), Vector((0, 0, -1)))
        if loc is None: return Vector((x, y, 0.34))
        return loc + n * lift
    post = Vector((c.x - 0.03 * sg, -0.29, 0.34))
    for s2 in (-1, 1):
        pts = []
        for k in range(7):
            f = k / 6
            x = post.x + s2 * f * 0.15
            y = post.y + f * 0.17
            pts.append(onfoot(x, y))
        pts[0] = post + Vector((0, 0, 0.02))
        tp = tube_path(f'Strap_{side}{s2}', pts, 0.022, 'strap', n=6, group='Feet')
        tp.rigid = True; P.append(tp)
    P.append(prim_cyl('ToePost_' + side, Vector((post.x, post.y, 0.32)), Vector((post.x, post.y, 0.37)), 0.018, col='strap', group='Feet'))
    return P

def chill_dude():
    pal = {'orange': '#f08a2a', 'teal': '#2fc2bc', 'teal_d': '#1d9e98', 'shorts': '#27b3a6', 'shorts_d': '#1b8c82',
           'sole': '#5b5f63', 'sole_top': '#8a8f93', 'strap': '#3b3f44', 'btn': '#f4e8d0', 'leaf': '#3ab7a5'}
    P = []
    def hawaii(U, V, m):
        img = P_solid(pal['orange'])(U, V, m)
        pts, x, z, circ = scatter(U, V, m, 7, zlib.crc32(m.get('kind', 'x').encode()) % 999, None)  # deterministic (hash() is salted per run)
        rng = np.random.default_rng(3)
        for px, pz, k in pts:
            R = 0.075 + (k % 5) * 0.01
            if k % 3 == 0:  # leaf
                img = star(img, x, z, circ, px + 0.05, pz - 0.05, R * 0.7, pal['teal_d'], rot=k)
            img = flower(img, x, z, circ, px, pz, R, pal['teal'], pal['orange'] if k % 2 else '#f6c46a', rot=k * 0.37)
        return img
    shirt = torso_shell('Shirt', 1.98, 0.05, nseg=32, extra=lambda z, a: 0.03 + 0.05 * max(0, 2.25 - z), th=0.02)
    shirt.paint = hawaii; P.append(shirt)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.36, 0.05, extra=lambda t, a: 0.03 * t / 0.36)
        sl.paint = hawaii; P.append(sl)
    P.append(collar('Collar', 'fold', h=0.06, flare=0.04, open_front=0.42, col='orange', fold=0.085))
    bv = piece_bvh(shirt)
    for i, z in enumerate((2.86, 2.62, 2.38, 2.14)):
        loc, n = project(bv, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.018, 0.026, n=8, col='btn', group='Top'))
    pt = pants('Shorts', 2.15, 1.40, 0.045, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.06 * max(0, (1.85 - z)), nseg=16)
    def shorts(U, V, m):
        img = P_solid(pal['shorts'])(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'leg': img = mix(img, aa(np.abs(z - 1.47) * 500 - 1.5), pal['shorts_d'])
        else: img = mix(img, aa(np.abs(z - 2.18) * 500 - 1.5), pal['shorts_d'])
        return img
    for p in pt: p.paint = shorts
    P += pt
    for s in 'LR':
        P += flip_flop(s, pal)
        P.append(skin_leg(s, 1.5, 0.47))
    return P, pal

def raincoat():
    pal = {'y': '#f5d915', 'y_d': '#d9bb0a', 'y_l': '#fbe85a', 'cord': '#f7f3e0', 'sole': '#c9a908', 'btn': '#e6c510'}
    P = []
    coat = torso_shell('Coat', 1.62, 0.07, nseg=32, extra=lambda z, a: 0.01 + 0.10 * max(0, 2.05 - z), th=0.025)
    def ypaint(U, V, m):
        img = P_solid(pal['y'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(az) - 0.012) * 400), pal['y_d'])  # placket seam
        img = mix(img, aa((np.abs(az) - 0.07) * -400) * aa(np.abs(az) - 0.1) * 0, pal['y_d'])
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.5, pal['y_d'])
        return img
    coat.paint = ypaint; P.append(coat)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.97, 0.055, extra=lambda t, a: 0.01 + 0.03 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['y'])(U, V, m), aa(np.abs(V - 0.86) * 400 - 1), pal['y_d'])
        P.append(sl)
    P.append(collar('Collar', 'stand', h=0.07, flare=0.05, col='y'))
    # hood (down, folded behind the neck)
    hood = prim_sphere('Hood', Vector((0, 0.34, 3.26)), 0.30, 'y', nl=7, seg=14, scale=(1.35, 0.75, 0.62), group='Top')
    hood.rigid = False
    head_clear(hood, 0.035); body_clear(hood, 0.03)
    hood.bone = 'UpperTorso'; P.append(hood)
    hrim = prim_sphere('HoodRim', Vector((0, 0.3, 3.38)), 0.26, 'y_d', nl=5, seg=14, scale=(1.4, 0.6, 0.25), group='Top')
    hrim.rigid = False; head_clear(hrim, 0.04); body_clear(hrim, 0.035); hrim.bone = 'UpperTorso'; P.append(hrim)
    bv = piece_bvh(coat)
    # drawstrings
    for sg in (-1, 1):
        top, n = project(bv, Vector((0.11 * sg, 0, 3.08)), Vector((0, 1, 0)))
        pts = [top + n * 0.02 + Vector((0.01 * sg * k, -0.004 * k, -0.07 * k)) for k in range(5)]
        P.append(tube_path(f'Cord{sg}', pts, 0.014, 'cord', n=5, group='Top'))
        P[-1].rigid = True
        P.append(prim_sphere(f'CordEnd{sg}', pts[-1] + Vector((0, 0, -0.03)), 0.028, 'cord', nl=4, seg=6, scale=(1, 1, 1.4), group='Top'))
    for i, z in enumerate((2.92, 2.66, 2.40, 2.14, 1.88)):
        loc, n = project(bv, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.022, 0.032, n=8, col='btn', group='Top'))
    for sg in (-1, 1):
        pk = surface_patch(f'Pocket{sg}', bv, lambda s, t, sg=sg: Vector((sg * (0.14 + s * 0.24), 0, 2.02 + t * 0.2)), Vector((0, 1, 0)), 0.01, 5, 4, col='y_l', th=0.012)
        pk.rigid = True; P.append(pk)
        pf = surface_patch(f'PocketFlap{sg}', bv, lambda s, t, sg=sg: Vector((sg * (0.12 + s * 0.28), 0, 2.2 + t * 0.07)), Vector((0, 1, 0)), 0.03, 5, 2, col='y', th=0.014)
        pf.rigid = True; P.append(pf)
    pt = pants('Pants', 2.2, 0.80, 0.05, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.02 * max(0, 1.3 - z))
    for p in pt: p.paint = P_solid(pal['y'])
    P += pt
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.05, bulk=0.03, toe=0.02)
        sh.paint = lambda U, V, m: mix(P_solid(pal['y'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), pal['sole'])
        P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 0.86, 0.46, 0.10, nseg=16, group='Feet', extra=lambda z, a: 0.01 + 0.02 * (z - 0.46)))
        shaft.paint = lambda U, V, m: mix(P_solid(pal['y'])(U, V, m), aa((0.93 - V) * 300), pal['y_d'])
        P.append(shaft)
    return P, pal

def boss_mode():
    pal = {'navy': '#1f2b45', 'navy_d': '#151e32', 'navy_l': '#2a3a5c', 'white': '#f4f4f2', 'red': '#b3121f', 'red_d': '#8c0d17',
           'black': '#111113', 'sole': '#050505', 'btn': '#0b0f1a'}
    P = []
    shirt = torso_shell('Shirt', 2.1, 0.035, nseg=32, th=0.015, col='white')
    P.append(shirt)
    P.append(collar('ShirtCollar', 'stand', h=0.05, flare=0.02, open_front=0.2, col='white'))
    sb = piece_bvh(shirt)
    # tie
    def tie_pt(s, t):
        w = 0.045 + 0.035 * t
        tipdrop = 0.06 * (1 - abs(s - 0.5) * 2) * (t > 0.85) * (t - 0.85) / 0.15
        return Vector(((s - 0.5) * 2 * w, 0, 3.07 - t * 0.66 - tipdrop))
    tie = surface_patch('Tie', sb, tie_pt, Vector((0, 1, 0)), 0.012, 3, 9, col='red', th=0.015)
    P.append(tie)
    loc, n = project(sb, Vector((0, 0, 3.1)), Vector((0, 1, 0)))
    P.append(prim_rbox('TieKnot', loc + n * 0.035, (0.11, 0.06, 0.09), 'red_d', group='Top'))
    # jacket with V opening
    def vkeep(i, j, zc_, az):
        if zc_ > 2.46:
            w = 0.05 + 0.42 * min(1, (zc_ - 2.46) / 0.62)
            return abs(az) > w
        return True
    jk = torso_shell('Jacket', 1.86, 0.075, nseg=36, extra=lambda z, a: 0.01 + 0.03 * max(0, 2.1 - z), keep=vkeep, th=0.022)
    def jpaint(U, V, m):
        img = P_solid(pal['navy'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.6, pal['navy_d'])
        img = mix(img, aa((np.abs(az) - 0.012) * 400) * (z < 2.46), pal['navy_d'])
        # hip pocket slits
        img = mix(img, aa(np.abs(z - 2.05) * 600 - 1.2) * (np.abs(np.abs(az) - 0.75) < 0.25), pal['navy_d'])
        img = mix(img, aa(np.abs(z - 2.78) * 600 - 1.2) * (np.abs(az - 0.72) < 0.14), pal['navy_d'])
        return img
    jk.paint = jpaint; P.append(jk)
    jb = piece_bvh(jk)
    # lapels: lie on the jacket next to the V edge
    for sg in (-1, 1):
        def lap(s, t, sg=sg):
            z = 2.47 + t * 0.66
            w = 0.05 + 0.42 * min(1, (z - 2.46) / 0.62)
            x0 = math.sin(w) * 0.5
            width = 0.04 + 0.13 * t ** 0.7
            return Vector((sg * (x0 - 0.01 + s * width), 0, z))
        lp = surface_patch(f'Lapel{sg}', jb, lap, Vector((0, 1, 0)), 0.012, 4, 7, col='navy_l', th=0.014)
        P.append(lp)
    for i, z in enumerate((2.40, 2.24)):
        loc, n = project(jb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.02, 0.03, n=8, col='btn'))
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.93, 0.055, extra=lambda t, a: 0.012 + 0.01 * t)
        sl.paint = lambda U, V, m: P_solid(pal['navy'])(U, V, m); P.append(sl)
        cf = sleeve('Cuff_' + s, s, 0.86, 0.985, 0.05, nrows=4, cap=False, col='white', th=0.015)
        P.append(cf)
    pt = pants('Trousers', 2.25, 0.50, 0.035, hip_off=0.055, leg_extra=lambda z, a: 0.015 + 0.02 * max(0, 1.5 - z))
    def tpaint(U, V, m):
        img = P_solid(pal['navy'])(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'leg': img = mix(img, aa((np.abs(az) - 0.01) * 400) * 0.7, pal['navy_l'])
        return img
    for p in pt: p.paint = tpaint
    P += pt
    for s in 'LR':
        sh = shoe('Shoe_' + s, s, off=0.035, bulk=0.005, toe=0.06, sole_h=0.035, open_elev=40)
        sh.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), '#2a2a2a')
        P.append(sh)
    return P, pal
