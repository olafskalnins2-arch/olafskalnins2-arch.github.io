from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '20', 'Splash_Painter', 'Common', 0.32

SPLAT = ('#e94f37', '#3b7dd8', '#f2c12e', '#4caf50')


def _splat_paint(base, seed, density=9.0, size=1.0, drips=True, hem=None, front=()):
    """White painter's cloth with colourful paint splats: wobbly blobs, satellite droplets and vertical drips."""
    def f(U, V, m):
        img = P_solid(base)(U, V, m)
        z0, az = zc(U, V, m)
        if hem is not None:
            img = hem(img, z0, az, V, m)
        pts, x, z, circ = scatter(U, V, m, density, seed, None)
        pts = list(pts) + [(0.5 * circ + fx, fz, fk) for fx, fz, fk in front]   # hand-placed splats (front of the bib)
        for px, pz, k in pts:
            k = int(k)
            if k % 5 == 0: continue                       # leave some cells clean
            col = SPLAT[k % 4]
            R = (0.022 + (k % 7) * 0.006) * size
            for off in (-circ, 0, circ):
                dx = x - (px + off); dz = z - pz
                if np.min(np.abs(dx)) > R * 3.5 or np.min(np.abs(dz)) > R * 6: continue
                r = np.sqrt(dx ** 2 + dz ** 2); th = np.arctan2(dz, dx)
                edge = R * (1 + 0.24 * np.sin(3 * th + k) + 0.12 * np.sin(7 * th + 2 * k))
                mask = aa((r - edge) * 900)
                for q in range(3):                        # flung droplets around the splat
                    ang = k * 1.7 + q * 2.1; d = R * (1.7 + 0.45 * q); sr = R * (0.24 - 0.05 * q)
                    mask = np.maximum(mask, aa((np.sqrt((dx - math.cos(ang) * d) ** 2 + (dz - math.sin(ang) * d) ** 2) - sr) * 900))
                if drips and k % 3 != 1:                  # paint running down
                    L = R * (1.4 + (k % 4) * 0.7); w = R * 0.2; cx = R * (0.25 * ((k % 3) - 1))
                    rect = np.maximum(np.abs(dx - cx) - w, np.maximum(dz, -L - dz))
                    mask = np.maximum(mask, aa(rect * 900))
                    mask = np.maximum(mask, aa((np.sqrt((dx - cx) ** 2 + (dz + L) ** 2) - w * 1.6) * 900))
                img = mix(img, mask, col)
        return img
    return f


def _strap(name, bvh, x0, w, lift, th, col):
    """Overall strap: front (on the bib) -> over the shoulder -> down the back (onto the back panel).
    Every row is projected onto the tee / bib from outside, so it lies on the cloth all the way."""
    cz = 2.92
    casts = [(Vector((0, -1, 0)), 2.84)]
    for ph in np.linspace(0.0, PI, 12):
        casts.append((Vector((0, -math.cos(ph), math.sin(ph))), None))
    casts += [(Vector((0, 1, 0)), z) for z in (2.82, 2.72, 2.62, 2.53)]
    rows = []; hints = []
    for d, z in casts:
        r = []; hh = []
        for s in (-0.5, -0.17, 0.17, 0.5):
            c = Vector((x0 + s * w, 0, cz if z is None else z))
            loc, n = project(bvh, c, -d, far=1.6)
            if loc is None:
                loc, n = c + d * 0.45, d
            r.append(loc + n * lift); hh.append(n)
        rows.append(r); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group='Top')
    head_clear(pc, 0.03)
    if th: thicken(pc, th)
    pc.region = 'torso'; pc.skirt = False
    return pc


def build():
    pal = {'white': '#f5f3ee', 'white_d': '#e2ded4', 'blue': '#3b7dd8', 'blue_d': '#2c62ae', 'grey': '#8a8f96', 'grey_d': '#6d7178',
           'sole': '#ecebe7', 'silver': '#c3c7cc', 'silver_d': '#8e9399', 'wood': '#c98a4b', 'bristle': '#3b2a1d',
           'red': '#e94f37', 'pblue': '#3b7dd8', 'yellow': '#f2c12e', 'green': '#4caf50'}
    P = []
    # ---- blue tee (tucked into the overalls)
    def tee_paint(U, V, m):
        img = P_solid(pal['blue'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((z - (m['zmax'] - 0.035)) * -600), pal['blue_d'])                    # ribbed neckline
        return mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.5, pal['blue_d'])   # side seams
    tee = torso_shell('Tee', 2.1, 0.03, nseg=32, th=0.015)
    tee.paint = tee_paint; P.append(tee)
    for s in 'LR':
        sl = sleeve('TeeSleeve_' + s, s, 0.0, 0.34, 0.04, extra=lambda t, a: 0.012 * t / 0.34)
        sl.paint = lambda U, V, m: mix(P_solid(pal['blue'])(U, V, m), aa((V - 0.88) * -400), pal['blue_d'])
        P.append(sl)

    # ---- white painter's overalls: trousers ...
    pt = pants('Overalls', 2.28, 0.52, 0.05, hip_off=0.055,
               leg_extra=lambda z, a: 0.03 + 0.015 * max(0, 1.2 - z), nseg=16)
    def seams(img, z, az, V, m):
        if m.get('kind') == 'leg':
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.6, pal['white_d'])   # side seams
        else:
            img = mix(img, aa((np.abs(az) - 0.006) * 400) * 0.6, pal['white_d'])                    # fly / centre seam
        return img
    for p, sd in zip(pt, (11, 23, 37)):
        p.paint = _splat_paint(pal['white'], sd, density=11.0, size=1.15, hem=seams)
    P += pt
    # ... + bib, waistband and back panel in one shell (cut with keep), sitting over the trouser top
    def bkeep(i, j, zc_, az):
        if zc_ < 2.31: return True                        # waistband all around
        if abs(az) < 0.78: return True                    # front bib
        return zc_ < 2.6 and abs(az) > PI - 0.66          # back panel
    zs = [2.16, 2.25, 2.34, 2.44, 2.54, 2.64, 2.74, 2.84, 2.93]
    bib = torso_shell('Bib', 2.16, 0.05, nseg=48, zs=zs, elevs=(), keep=bkeep, th=0.022, over=pt, over_gap=0.012)
    bib.skirt = False
    def bib_hem(img, z, az, V, m):
        img = mix(img, aa(np.abs(z - 2.34) * 600 - 1.2), pal['white_d'])                         # waistband seam
        return mix(img, aa((z - 2.895) * -600), pal['white_d'])                                    # bib top hem
    bib.paint = _splat_paint(pal['white'], 5, density=12.0, size=1.15, hem=bib_hem,
                             front=((-0.2, 2.74, 6), (-0.06, 2.47, 8), (0.21, 2.4, 13), (-0.25, 2.33, 3)))
    P.append(bib)
    tb = piece_bvh(tee)
    bb = piece_bvh(bib)
    for s, sg in (('L', 1), ('R', -1)):
        st = _strap('Strap_' + s, tb, 0.36 * sg, 0.12, 0.034, 0.02, 'white')
        st.paint = _splat_paint(pal['white'], 51 + sg, density=10.0, size=0.8, drips=False)
        st.meta.update(circ=0.12, zmin=2.5, zmax=3.3); st.rect_key = 'Strap'
        P.append(st)
        # strap buckle on the bib corner + button
        loc, n = project(bb, Vector((0.36 * sg, 0, 2.86)), Vector((0, 1, 0)))
        bk = prim_rbox('Buckle_' + s, loc + n * 0.05, (0.13, 0.035, 0.09), 'silver', bevel=0.015, group='Top')
        bk.bone = 'UpperTorso'; P.append(bk)
        P.append(prim_box('BuckleBar_' + s, loc + n * 0.07, (0.1, 0.012, 0.022), 'silver_d', group='Top'))
        P[-1].bone = 'UpperTorso'
        # side button on the waistband
        loc, n = project(bb, Vector((0.0, 0, 2.25)), Vector((-sg, 0.35, 0)).normalized())
        P.append(prim_cyl('SideButton_' + s, loc, loc + n * 0.022, 0.035, n=10, col='silver', group='Bottom'))
        P[-1].bone = 'LowerTorso'
    # chest pocket (character left) holding a paint brush
    pk = surface_patch('Pocket', bb, lambda s, t: Vector((0.06 + s * 0.22, 0, 2.48 + t * 0.24)), Vector((0, 1, 0)), 0.035, 5, 4,
                       col='white_d', th=0.04)
    pk.rigid = True; P.append(pk)
    loc, n = project(bb, Vector((0.17, 0, 2.74)), Vector((0, 1, 0)))
    base = loc + n * 0.022
    up = Vector((-0.12, 0, 1)).normalized()
    P.append(prim_cyl('BrushHandle', base - up * 0.2, base + up * 0.07, 0.02, n=8, col='wood', group='Top'))
    P.append(prim_cyl('BrushFerrule', base + up * 0.06, base + up * 0.13, 0.032, 0.03, n=10, col='silver', group='Top'))
    rot = Matrix.Rotation(math.atan2(-up.x, up.z), 3, 'Y')
    P.append(prim_rbox('BrushBristles', base + up * 0.17, (0.075, 0.035, 0.08), 'bristle', rot=rot, bevel=0.012, group='Top'))
    P.append(prim_rbox('BrushPaint', base + up * 0.205, (0.078, 0.038, 0.035), 'pblue', rot=rot, bevel=0.01, group='Top'))
    for q in P[-4:]: q.bone = 'UpperTorso'

    # ---- rolled trouser cuffs
    for s in 'LR':
        cf = leg_tube('Cuff_' + s, s, 0.66, 0.53, 0.125, nseg=16, nrows=3, th=0.02, col='white_d')
        P.append(cf)

    # ---- grey sneakers with paint dots
    def sneaker(U, V, m):
        img = P_solid(pal['grey'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.012)) * 600 - 3), pal['grey_d'])      # welt line
        for kz in (0.53, 0.575, 0.62):                                                         # laces
            img = mix(img, aa(np.abs(z - kz) * 600 - 3) * (np.abs(az) < 0.32), '#f4f4f2')
        img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])                             # white sole
        x, zz = phys(U, V, m)
        rng = np.random.default_rng(7)
        circ = m.get('circ', 1.0)
        for k in range(14):
            px = rng.uniform(0, circ); pz = rng.uniform(m['sole_top'] + 0.03, m['zmax'] - 0.04); R = rng.uniform(0.016, 0.026)
            for off in (-circ, 0, circ):
                img = mix(img, aa((np.sqrt((x - px - off) ** 2 + (zz - pz) ** 2) - R) * 900), SPLAT[k % 4])
        return img
    for s in 'LR':
        sh = shoe('Sneaker_' + s, s, off=0.04, bulk=0.03, toe=0.04, sole_h=0.06, open_elev=44)
        sh.paint = sneaker; P.append(sh)
    return P, pal
