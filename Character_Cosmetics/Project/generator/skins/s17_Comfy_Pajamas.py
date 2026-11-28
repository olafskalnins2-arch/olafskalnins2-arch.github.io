from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '17', 'Comfy_Pajamas', 'Common', 0.32


def _dots(base, dot, sp=0.13, r=0.024, length=None):
    """Staggered polka dots in physical units, seamless around the circumference."""
    def f(U, V, m):
        mm = dict(m, length=length) if length else m
        img = P_solid(base)(U, V, mm)
        x, z = phys(U, V, mm)
        circ = mm.get('circ', 1.0)
        n = max(4, int(round(circ / sp)))
        sx = circ / n
        row = np.floor(z / sp)
        xo = x / sx + 0.5 * (row % 2)
        dx = (xo - np.floor(xo) - 0.5) * sx
        dz = (z / sp - row - 0.5) * sp
        return mix(img, aa((np.sqrt(dx * dx + dz * dz) - r) * 900), dot)
    return f


def build():
    pal = {'blue': '#8fc1e8', 'blue_d': '#74a8d2', 'white': '#ffffff', 'pink': '#f6a5c0', 'pink_d': '#e48aa8',
           'pink_l': '#fbc9da', 'sole': '#e9c7d3', 'btn': '#ffffff'}
    P = []
    dots = _dots(pal['blue'], pal['white'])

    # ---- trousers first (loose, slightly flared, white piped cuffs)
    pt = pants('PJPants', 2.2, 0.56, 0.05, hip_off=0.065,
               leg_extra=lambda z, a: 0.025 + 0.03 * max(0, 1.3 - z))
    def ppaint(U, V, m):
        img = dots(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.045)) * 600 - 2.0), pal['white'])   # cuff piping
            img = mix(img, aa(np.abs(np.abs(az) - PI / 2) * 300 - 1.0) * 0.5, pal['blue_d'])   # side seam
        return img
    for p in pt: p.paint = ppaint
    P += pt

    # ---- untucked button-up shirt hanging over the trousers
    shirt = torso_shell('PJShirt', 1.96, 0.055, nseg=32, extra=lambda z, a: 0.03 + 0.04 * max(0, 2.2 - z),
                        th=0.022, hang=2.3, over=pt)
    def spaint(U, V, m):
        img = dots(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(az - 0.03) - 0.12) * 300), pal['blue'])                 # plain placket
        img = mix(img, aa((np.abs(az - 0.165) - 0.022) * 300), pal['white'])              # placket piping
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.035)) * 600 - 2.0), pal['white'])     # hem piping
        img = mix(img, aa(np.abs(np.abs(az) - PI / 2) * 300 - 1.0) * 0.5, pal['blue_d'])   # side seams
        return img
    shirt.paint = spaint; P.append(shirt)

    for s in 'LR':
        sl = sleeve('PJSleeve_' + s, s, 0.0, 0.93, 0.055, extra=lambda t, a: 0.012 + 0.02 * t)
        # true sleeve dimensions so the dots stay round (meta circ is the wrist ring, length defaults to 0.6)
        N = sl.meta['N']; nr = sl.meta['n_outer_verts'] // N
        rings = [sl.verts[i * N:(i + 1) * N] for i in range(nr)]
        sl.meta['circ'] = sum(sum((r[j] - r[j - 1]).length for j in range(N)) for r in rings) / nr
        cen = [sum(r, Vector()) / N for r in rings]
        sl.meta['length'] = sum((cen[i + 1] - cen[i]).length for i in range(nr - 1))
        sl.meta['rect'] = (256, 256)
        def slp(U, V, m):
            img = _dots(pal['blue'], pal['white'])(U, V, m)
            img = mix(img, aa(np.abs(V - 0.955) * 500 - 2.5), pal['white'])                # cuff piping
            return img
        sl.paint = slp; P.append(sl)

    # ---- flat pyjama collar lying on the shirt's shoulders, pointed tips at the front, white piped edge
    sb = piece_bvh(shirt)
    C0 = Vector((0, 0, 2.95)); na, nt, gap = 30, 5, 0.24
    rows = []; hints = []
    for i in range(nt):
        r = []; hh = []
        for j in range(na):
            a = gap + (2 * PI - 2 * gap) * j / (na - 1)
            fa = min(a, 2 * PI - a)
            e_out = 38 - 30 * max(0.0, 1 - (fa - gap) / 0.75) ** 1.5
            e = math.radians(57 + (e_out - 57) * i / (nt - 1))
            d = Vector((math.sin(a), -math.cos(a), 0)) * math.cos(e) + Z * math.sin(e)
            loc, n = project(sb, C0 + d * 1.2, -d)
            if loc is None: loc, n = C0 + d * 0.5, d
            r.append(loc + n * 0.014); hh.append(n)
        rows.append(r); hints.append(hh)
    col_ = grid_piece('PJCollar', rows, closed=False, hints=hints, group='Top')
    head_clear(col_, 0.03)
    thicken(col_, 0.014)
    col_.meta['patch'] = True; col_.region = 'torso'; col_.skirt = False
    col_.meta['rect'] = (512, 64)
    def cpaint(U, V, m):
        img = P_solid(pal['blue'])(U, V, m)
        img = mix(img, aa((0.80 - V) * 300), pal['white'])
        img = mix(img, aa((np.minimum(U, 1 - U) - 0.022) * 1500), pal['white'])
        return img
    col_.paint = cpaint
    P.append(col_)

    for i, z in enumerate((2.93, 2.69, 2.45, 2.21, 2.0)):
        loc, n = project(sb, Vector((0.012, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.02, 0.03, n=10, col='btn', group='Top'))

    # chest pocket on the character's left (+X) with a white piped top edge
    pk = surface_patch('Pocket', sb, lambda s, t: Vector((0.16 + s * 0.2, 0, 2.55 + t * 0.2)), Vector((0, 1, 0)),
                       0.01, 4, 4, th=0.012)
    pk.paint = lambda U, V, m: mix(P_solid(pal['blue'])(U, V, m), aa((0.84 - V) * 300), pal['white'])
    pk.rigid = True; P.append(pk)

    # ---- fuzzy pink slippers with a pom-pom
    def fuzz(U, V, m):
        img = P_solid(pal['pink'])(U, V, m)
        z, az = zc(U, V, m)
        nz = (np.sin(U * 517.0 + V * 91.0) * np.sin(V * 433.0 - U * 77.0) + np.sin(U * 1213.0 + V * 1531.0)) * 0.5
        img = mix(img, np.clip(nz, 0, 1) * 0.45, pal['pink_l'])
        img = mix(img, np.clip(-nz, 0, 1) * 0.35, pal['pink_d'])
        img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
        return img
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Slipper_' + s, s, off=0.055, bulk=0.05, toe=0.04, sole_h=0.045, open_elev=42)
        sh.paint = fuzz; P.append(sh)
        nseg = 20
        top = [sh.verts[8 * nseg + j].copy() for j in range(nseg)]
        cc = sum(top, Vector()) / nseg
        ring = [cc + (p - cc) * 1.04 + Vector((0, 0, 0.005)) for p in top]
        cuff = tube_path('SlipperCuff_' + s, ring + [ring[0]], 0.032, 'pink_l', n=6, group='Feet', caps=False)
        cuff.region = 'foot_' + s; cuff.rect_key = 'SlipperCuff'
        cuff.paint = (lambda U, V, m: mix(P_solid(pal['pink_l'])(U, V, m),
                                                           np.clip(np.sin(U * 900.0) * np.sin(V * 300.0), 0, 1) * 0.4, pal['pink']))
        P.append(cuff)
        sbv = piece_bvh(sh)
        loc, n = project(sbv, Vector((0.255 * sg, -0.25, 0.9)), Vector((0, 0, -1)))
        pom = prim_sphere('PomPom_' + s, loc + Vector((0, -0.01, 0.065)), 0.095, 'pink_l', nl=7, seg=12, group='Feet')
        P.append(pom)
    return P, pal
