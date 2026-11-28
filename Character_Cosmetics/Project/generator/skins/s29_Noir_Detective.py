from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03 (RF_SLIT_TOP), o04 helpers
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '29', 'Noir_Detective', 'Rare', 0.7


def _frac(x): return x - np.floor(x)


def plaid(sa, sb, pal):
    """dark-red tartan in the piece's own UV (sa, sb = physical size of the UV square)"""
    def f(U, V, m):
        a, b = U * sa, V * sb
        img = P_solid(pal['scarf'])(U, V, m)
        P = 0.15
        for c in (a, b):
            fr = _frac(c / P)
            img = mix(img, (np.abs(fr - 0.5) < 0.17).astype(float) * 0.42, pal['scarf_d'])     # wide dark bands
            img = mix(img, (np.abs(fr - 0.06) < 0.035).astype(float) * 0.75, pal['scarf_l'])   # thin tan line
            img = mix(img, (np.abs(fr - 0.5) < 0.03).astype(float) * 0.55, pal['scarf_k'])     # black pinstripe
        return img
    return f


def pop_collar(name, bvh, r0=0.36, h=0.21, flare=0.11, open_front=0.72, n=26, col=None, th=0.02):
    """popped (turned-up) coat collar standing on the coat's shoulders around the neck, open at the front"""
    angs = [open_front + (2 * PI - 2 * open_front) * j / n for j in range(n + 1)]
    base = []; dirs = []
    for a in angs:
        d = Vector((math.sin(a), -math.cos(a), 0))
        p = Vector((0, 0, 3.6)) + d * r0
        hh = bvh.ray_cast(p, Vector((0, 0, -1)), 1.2)
        zt = hh[0].z if hh[0] else 3.15
        base.append(Vector((d.x * r0, d.y * r0, zt + 0.012))); dirs.append(d)
    rows = [[p - Z * 0.04 - dirs[k] * 0.01 for k, p in enumerate(base)], base,
            [p + Z * h * 0.55 + dirs[k] * flare * 0.45 for k, p in enumerate(base)],
            [p + Z * h + dirs[k] * flare for k, p in enumerate(base)]]
    hints = [[d for d in dirs] for _ in rows]
    pc = _grid_with_ij(name, rows, closed=False, v_vals=[0, 0.2, 0.6, 1.0], hints=hints, group='Top', col=col)
    head_clear(pc, 0.03)
    if th: thicken(pc, th)
    pc.rigid = False; pc.region = 'torso'; pc.skirt = False
    return pc


def build():
    pal = {'tan': '#b89a6a', 'tan_d': '#9a7d50', 'tan_l': '#c9ad7e', 'tan_k': '#7c6240',
           'grey': '#3a3b40', 'grey_d': '#2b2c30', 'grey_l': '#4a4b52',
           'shoe': '#5a3a22', 'shoe_l': '#8a5e38', 'shoe_d': '#3a2414', 'sole': '#21160e',
           'scarf': '#7a2e2e', 'scarf_d': '#4e1a1c', 'scarf_l': '#c9a46a', 'scarf_k': '#1e1012',
           'btn': '#3b2716', 'brass': '#b08a3e', 'brass_d': '#7a5c22', 'wood': '#5b3519', 'glass': '#bfe0ea'}
    P = []
    # ---- grey trousers (under layer first)
    pt = pants('Trousers', 2.22, 0.5, 0.04, hip_off=0.052, leg_extra=lambda z, a: 0.015 + 0.02 * max(0, 1.4 - z))
    def tpaint(U, V, m):
        img = P_solid(pal['grey'])(U, V, m); z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            img = mix(img, aa((np.abs(az) - 0.008) * 400) * 0.8, pal['grey_l'])          # front crease
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.6, pal['grey_d'])
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.03)) * 500 - 1.0) * 0.7, pal['grey_d'])
        return img
    for p in pt: p.paint = tpaint
    P += pt

    # ---- long double-breasted trench coat, knee length, slit panels (closed at rest)
    def vkeep(i, j, zc_, az):
        return not (zc_ > 2.80 and abs(az) < 0.05 + 0.42 * (zc_ - 2.80) / 0.38)
    coat = torso_shell('Coat', 1.05, 0.07, nseg=40, extra=lambda z, a: 0.012 + 0.11 * max(0, 2.0 - z) ** 1.05,
                       keep=vkeep, th=0.025, slits=RF_SLIT_TOP(), hang=2.3, over=pt)
    def cpaint(U, V, m):
        img = P_solid(pal['tan'])(U, V, m); z, az = zc(U, V, m)
        # side seams + back centre seam / vent
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.5, pal['tan_d'])
        img = mix(img, aa((PI - np.abs(az) - 0.008) * 400) * (z < 2.3), pal['tan_d'])
        # double-breasted overlap edge (right panel over left) from the V down to the hem
        edge = 0.2 + 0.0 * z
        img = mix(img, aa((np.abs(az - edge) - 0.007) * 450) * (z < 2.82), pal['tan_k'])
        img = mix(img, aa((np.abs(az - edge - 0.03) - 0.003) * 450) * (z < 2.8) * 0.6, pal['tan_d'])   # stitch line
        # hem stitching
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.06)) * 500 - 0.8) * 0.7, pal['tan_d'])
        img = mix(img, aa((z - (m['zmin'] + 0.02)) * 500) * 0.35, pal['tan_k'])
        # slanted hip pocket flaps (both sides)
        for sg in (-1, 1):
            u = sg * az - 0.95
            zt = 1.92 + 0.1 * u
            inside = (np.abs(u) < 0.22) & (z < zt) & (z > zt - 0.09)
            img = mix(img, inside.astype(float) * 0.25, pal['tan_d'])
            img = mix(img, aa(np.abs(z - zt) * 500 - 0.8) * (np.abs(u) < 0.22), pal['tan_k'])
            img = mix(img, aa(np.abs(z - (zt - 0.09)) * 500 - 0.6) * (np.abs(u) < 0.22) * 0.8, pal['tan_k'])
        # storm (gun) flap on the right chest
        sf = (az < -0.12) & (az > -1.15) & (z > 2.72)
        img = mix(img, aa(np.abs(z - 2.72) * 500 - 0.8) * (az < -0.12) * (az > -1.15), pal['tan_k'])
        img = mix(img, sf.astype(float) * 0.12, pal['tan_l'])
        # back yoke (rain shield) across the shoulders
        by = (np.abs(az) > 1.9) & (z > 2.66)
        img = mix(img, by.astype(float) * 0.12, pal['tan_l'])
        img = mix(img, aa(np.abs(z - 2.66) * 500 - 0.8) * (np.abs(az) > 1.9), pal['tan_k'])
        return img
    coat.paint = cpaint; P.append(coat)
    cb = piece_bvh(coat)

    # lapels along the V
    for sg in (-1, 1):
        def lap(s, t, sg=sg):
            z = 2.81 + t * 0.36
            w = 0.05 + 0.42 * min(1, (z - 2.80) / 0.38)
            x0 = math.sin(w) * 0.52
            width = 0.05 + 0.15 * t ** 0.7
            return Vector((sg * (x0 - 0.012 + s * width), 0, z))
        lp = surface_patch(f'Lapel{sg}', cb, lap, Vector((0, 1, 0)), 0.012, 4, 7, col='tan_l', th=0.014)
        P.append(lp)
    # popped collar standing up behind the neck
    P.append(pop_collar('CoatCollar', cb, col='tan_l'))

    # double-breasted buttons: 2 x 3 above the belt
    for r, z in enumerate((2.36, 2.56, 2.76)):
        for c, x in enumerate((-0.2, 0.2)):
            loc, n = project(cb, Vector((x, 0, z)), Vector((0, 1, 0)))
            P.append(prim_cyl(f'Button{r}{c}', loc - n * 0.004, loc + n * 0.024, 0.033, n=10, col='btn', group='Top'))

    # epaulettes on the shoulders, each with a button near the collar
    for sg in (-1, 1):
        ep = surface_patch(f'Epaulette{sg}', cb, lambda s, t, sg=sg: Vector((sg * (0.34 + 0.18 * t), -0.055 + 0.11 * s, 3.8)),
                           Vector((0, 0, -1)), 0.012, 3, 5, col='tan_d', th=0.016)
        P.append(ep)
        loc, n = project(cb, Vector((sg * 0.37, 0, 3.8)), Vector((0, 0, -1)))
        b = prim_cyl(f'EpButton{sg}', loc + n * 0.02, loc + n * 0.042, 0.026, n=8, col='btn', group='Top')
        b.bone = 'UpperTorso'; P.append(b)

    # sleeves with buckled cuff straps
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.95, 0.06, extra=lambda t, a: 0.012 + 0.02 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['tan'])(U, V, m), aa((0.97 - V) * 400) * 0.6, pal['tan_d'])
        P.append(sl)
        st = sleeve('CuffStrap_' + s, s, 0.80, 0.865, 0.088, nrows=2, cap=False, col='tan_d', th=0.015, extra=lambda t, a: 0.02 * t)
        P.append(st)
        c, tg = arm_point(s, 0.832)
        loc, n = project(piece_bvh(st), c, Vector((-sg, 0, 0)))
        if loc is not None:
            bk = prim_box('CuffBuckle_' + s, loc + n * 0.012, (0.02, 0.07, 0.06), 'brass')
            bk.region = 'arm_' + s; bk.group = 'Top'; P.append(bk)

    # belt fitted on the coat + square buckle
    belt = band('Belt', 2.12, 2.25, 0.012, th=0.02, bvh=piece_bvh(coat), hang=2.35); belt.group = 'Extras'
    belt.paint = lambda U, V, m: mix(mix(P_solid(pal['tan_d'])(U, V, m), aa(np.minimum(V - 0.1, 0.9 - V) * -200), pal['tan_k']),
                                     aa(np.abs(np.minimum(np.abs(V - 0.2), np.abs(V - 0.8))) * 300 - 0.6) * 0.6, pal['tan_l'])
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.185)), Vector((0, 1, 0)))
    o = loc + n * 0.018
    for nm, d, sz in (('BuckleL', (-0.075, 0, 0), (0.03, 0.025, 0.17)), ('BuckleR', (0.075, 0, 0), (0.03, 0.025, 0.17)),
                      ('BuckleT', (0, 0, 0.07), (0.18, 0.025, 0.03)), ('BuckleB', (0, 0, -0.07), (0.18, 0.025, 0.03)),
                      ('BucklePin', (0, -0.004, 0), (0.025, 0.02, 0.13))):
        q = prim_box(nm, o + Vector(d), sz, 'brass' if nm != 'BucklePin' else 'brass_d'); q.bone = 'LowerTorso'; P.append(q)
    # belt tail tucked through the buckle
    q = prim_box('BeltTail', o + Vector((0.14, -0.006, 0)), (0.12, 0.014, 0.1), 'tan_d'); q.bone = 'LowerTorso'; P.append(q)

    # magnifying glass tucked in the belt on the character's left front
    az = 0.85
    d = Vector((math.sin(az), -math.cos(az), 0))
    bl, bn = project(bb, d * 1.5 + Vector((0, 0, 2.16)), -d)
    bn = Vector((bn.x, bn.y, 0)).normalized()
    cl, cn = project(cb, d * 1.5 + Vector((0, 0, 2.47)), -d)
    cn = Vector((cn.x, cn.y, 0)).normalized()
    tng = Z.cross(bn).normalized()
    h0 = bl + bn * 0.03 + Vector((0, 0, -0.1))
    h1 = bl + bn * 0.03 + Vector((0, 0, 0.13))
    lc = cl + cn * 0.05 + Vector((0, 0, 0.0))
    lc = Vector((lc.x, lc.y, h1.z + 0.03 + 0.1))
    mg = [prim_cyl('GlassHandle', h0, h1, 0.026, 0.022, n=8, col='wood'),
          prim_cyl('GlassFerrule', h1, h1 + Vector((0, 0, 0.04)), 0.03, n=8, col='brass')]
    ring = [lc + (tng * math.sin(2 * PI * k / 16) + Z * -math.cos(2 * PI * k / 16)) * 0.1 for k in range(17)]
    rg = tube_path('GlassRim', ring, 0.018, 'brass', n=6, caps=False); mg.append(rg)
    mg.append(prim_cyl('GlassLens', lc - cn * 0.007, lc + cn * 0.007, 0.092, n=16, col='glass'))
    for q in mg: q.bone = 'LowerTorso'; q.rigid = True; q.group = 'Extras'
    P += mg

    # dark-red plaid scarf: thick loop round the neck + fill in the coat's V
    loop = [Vector((math.sin(2 * PI * k / 20) * 0.29, -math.cos(2 * PI * k / 20) * 0.29 + 0.01, 3.22)) for k in range(21)]
    sc = tube_path('ScarfLoop', loop, 0.062, None, n=10, group='Top', caps=False)
    head_clear(sc, 0.02); body_clear(sc, 0.015)
    sc.paint = plaid(0.4, 1.8, pal); sc.bone = 'UpperTorso'; P.append(sc)
    bib = surface_patch('ScarfBib', B.bvh['torso'], lambda s, t: Vector((-0.24 + 0.48 * s, 0, 2.74 + 0.48 * t)),
                        Vector((0, 1, 0)), 0.03, 7, 7, th=0.012)
    head_clear(bib, 0.02)
    bib.paint = plaid(0.48, 0.48, pal); bib.bone = 'UpperTorso'; P.append(bib)
    # hanging scarf end over the left lapel
    tail = surface_patch('ScarfTail', piece_bvh(coat, *P[-1:]), lambda s, t: Vector((0.02 + 0.11 * s + 0.02 * t, 0, 3.08 - 0.5 * t)),
                         Vector((0, 1, 0)), 0.045, 4, 7, th=0.014)
    tail.paint = plaid(0.12, 0.5, pal); tail.bone = 'UpperTorso'; P.append(tail)

    # polished brown oxfords
    for s in 'LR':
        sh = shoe('Shoe_' + s, s, off=0.035, bulk=0.006, toe=0.07, sole_h=0.035, open_elev=40)
        def spaint(U, V, m):
            img = P_solid(pal['shoe'])(U, V, m); z, az = zc(U, V, m)
            img = mix(img, np.clip(np.cos(az), 0, 1) ** 3 * np.exp(-((V - 0.62) / 0.16) ** 2) * 0.7, pal['shoe_l'])   # toe shine
            img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.06)) * 500 - 0.6) * (np.cos(az) > 0.55), pal['shoe_d'])   # toe cap seam
            lace = (np.abs(az) < 0.28) & (V > 0.8)
            img = mix(img, lace.astype(float) * 0.8, pal['shoe_d'])
            img = mix(img, ((np.abs(_frac(z * 22) - 0.5) < 0.14) & (np.abs(az) < 0.22) & (V > 0.82)).astype(float), '#c8b08a')
            return mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
        sh.paint = spaint; P.append(sh)
    return P, pal
