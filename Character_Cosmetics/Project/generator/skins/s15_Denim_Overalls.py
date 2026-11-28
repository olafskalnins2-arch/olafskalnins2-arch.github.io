from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '15', 'Denim_Overalls', 'Common', 0.32

ORANGE = '#f08a24'


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _stitch(img, dist, along, col=ORANGE, w=2.2, period=0.045, duty=0.62):
    """dashed contrast stitch: dist = signed distance to the seam line (units), along = coordinate along it (units)"""
    m = aa(np.abs(dist) * 500 - w) * (np.mod(along / period, 1.0) < duty)
    return mix(img, m, col)


def _line(img, dist, col, w=1.5):
    return mix(img, aa(np.abs(dist) * 500 - w), col)


def _strap(name, sg, bv, width=0.11, lift=0.014, th=0.016, group='Bottom'):
    """Overall shoulder strap: a ribbon laid over the garments (front on the bib, over the shoulder top, down the back).
    Each row is cast onto the garment surface (and never closer than 0.045 to the body)."""
    body = B.bvh['torso']
    samp = []   # (x centre, ray origin, ray dir)
    fz = [2.66, 2.72, 2.78]
    for k, z in enumerate(fz):
        x = 0.20 + 0.03 * k / (len(fz) - 1)
        samp.append((x, Vector((0, -2.0, z)), Vector((0, 1, 0))))
    zc0 = 2.85
    for k in range(13):
        a = math.radians(15 * k)
        d = Vector((0, -math.cos(a), math.sin(a)))
        x = 0.24 + 0.10 * min(1, a / (PI / 2)) if a <= PI / 2 else 0.34 - 0.06 * (a - PI / 2) / (PI / 2)
        samp.append((x, Vector((0, 0, zc0)) + d * 1.6, -d))
    bz = list(np.linspace(2.78, 2.22, 8))
    for k, z in enumerate(bz):
        x = 0.28 - 0.08 * k / (len(bz) - 1)
        samp.append((x, Vector((0, 2.0, z)), Vector((0, -1, 0))))
    rows = []; hints = []
    for x, o, d in samp:
        r = []; hh = []
        for off in (-width / 2, 0.0, width / 2):
            oo = o + Vector((sg * (x + off), 0, 0))
            best = None
            h = bv.ray_cast(oo, d, 4.0)
            if h[0] is not None:
                n = h[1] if h[1].dot(d) < 0 else -h[1]
                best = (h[0] + n * lift, n)
            hb = body.ray_cast(oo, d, 4.0)
            if hb[0] is not None:
                nb = hb[1] if hb[1].dot(d) < 0 else -hb[1]
                cand = hb[0] + nb * 0.05
                if best is None or (cand - oo).dot(d) < (best[0] - oo).dot(d): best = (cand, nb)
            if best is None: best = (oo + d * 1.5, -d)
            r.append(best[0]); hh.append(best[1])
        rows.append(r); hints.append(hh)
    # light smoothing along the strap (keeps it a clean band over the bib edge / shoulder)
    for _ in range(2):
        nr = [rows[0]]
        for i in range(1, len(rows) - 1):
            nr.append([rows[i][j] * 0.5 + (rows[i - 1][j] + rows[i + 1][j]) * 0.25 for j in range(3)])
        nr.append(rows[-1]); rows = nr
    # never below the surface after smoothing
    for i, r in enumerate(rows):
        for j, p in enumerate(r):
            x, o, d = samp[i]
            h = bv.ray_cast(p - d * 0.3, d, 0.6)
            if h[0] is not None:
                n = h[1] if h[1].dot(d) < 0 else -h[1]
                s = (p - h[0]).dot(n)
                if s < lift * 0.8: r[j] = p + n * (lift * 0.8 - s)
    pc = grid_piece(name, rows, closed=False, hints=hints, group=group)
    head_clear(pc, 0.04)
    thicken(pc, th)
    pc.region = 'torso'; pc.skirt = False; pc.meta['patch'] = True
    pc.meta['rect'] = (32, 512); pc.rect_key = 'Strap'
    return pc, rows


def build():
    pal = {'denim': '#3b6ea5', 'denim_d': '#2c5582', 'yellow': '#f4c542', 'white': '#ffffff', 'boot': '#a0703c',
           'boot_d': '#7d5328', 'sole': '#3d2a18', 'brass': '#d9a441', 'brass_d': '#a87a26', 'orange': ORANGE}
    P = []

    # ---------------- striped tee (tucked into the overalls) ----------------
    STP = 0.15
    def stripes_z(img, z):
        f = np.mod(z / STP, 1.0)
        return mix(img, aa((np.minimum(f, 1 - f) * STP - STP * 0.22) * 500), pal['white'])   # white bands, yellow between
    def tee_paint(U, V, m):
        img = P_solid(pal['yellow'])(U, V, m); z, az = zc(U, V, m)
        return stripes_z(img, z)
    tee = torso_shell('Tee', 2.1, 0.03, nseg=32, th=0.015)
    tee.paint = tee_paint; P.append(tee)
    for s in 'LR':
        sl = sleeve('TeeSleeve_' + s, s, 0.0, 0.33, 0.035, extra=lambda t, a: 0.012 + 0.012 * t / 0.33)
        def sp(U, V, m):
            img = P_solid(pal['yellow'])(U, V, m)
            t = m['vmin'] + V * (m['vmax'] - m['vmin'])
            return stripes_z(img, t * 2.0)
        sl.paint = sp; P.append(sl)
        P.append(sleeve('SleeveHem_' + s, s, 0.30, 0.345, 0.065, nrows=3, cap=False, th=0.015, col='yellow',
                        extra=lambda t, a: 0.012))
    P.append(collar('Collar', 'stand', h=0.045, flare=0.015, col='yellow'))

    # ---------------- overalls: trousers + bib + straps ----------------
    pt = pants('Overalls', 2.3, 0.55, 0.045, hip_off=0.065, leg_extra=lambda z, a: 0.02 + 0.04 * max(0, 1.4 - z), nseg=16)
    def denim(U, V, m):
        img = P_solid(pal['denim'])(U, V, m); z, az = zc(U, V, m)
        kind = m.get('kind')
        if kind == 'hip':
            r = 0.52; x = az * r
            # waistband
            img = mix(img, aa(np.maximum(2.2 - z, z - 2.31) * 500), pal['denim_d'])
            img = _stitch(img, z - 2.215, x); img = _stitch(img, z - 2.285, x)
            # side seams + fly J-stitch
            for c in (PI / 2, -PI / 2):
                img = _stitch(img, (az - c) * r - 0.012, z); img = _stitch(img, (az - c) * r + 0.012, z)
            fly = (z > 2.02) & (z < 2.2)
            img = mix(img, aa(np.abs((az - 0.17) * r) * 500 - 2.2) * fly * (np.mod(z / 0.045, 1) < 0.62), ORANGE)
            img = mix(img, aa(np.abs((az) * r) * 500 - 1.2) * (z < 2.2), pal['denim_d'])
            # front pocket openings (slanted)
            for sgn in (1, -1):
                d = (sgn * az * r - (0.30 + (2.2 - z) * 0.55))
                img = _stitch(img, d, z, w=2.0)
                img = mix(img, aa(np.abs(d + 0.012) * 500 - 1.2) * (z > 2.05) * (z < 2.2), pal['denim_d'])
            # back patch pockets
            for sgn in (1, -1):
                bx = (sgn * az - (PI - 0.5)) * r      # pocket centre at |az| = PI - 0.5
                inside = (np.abs(bx) < 0.12) & (z > 1.98) & (z < 2.18)
                dbox = np.maximum(np.abs(bx) - 0.12, np.maximum(1.98 - z, z - 2.18))
                img = mix(img, inside.astype(float) * 0.35, pal['denim_d'])
                img = mix(img, aa(np.abs(dbox) * 500 - 1.0), pal['denim_d'])
                img = _stitch(img, np.where(inside, dbox + 0.014, 1.0), bx + z, w=2.0)
        elif kind == 'leg':
            for c in (PI / 2, -PI / 2):   # outer / inner seams (double contrast stitch)
                img = mix(img, aa(np.abs((az - c) * 0.18) * 500 - 1.2), pal['denim_d'])
                img = _stitch(img, (az - c) * 0.18 - 0.014, z); img = _stitch(img, (az - c) * 0.18 + 0.014, z)
        return img
    for p in pt: p.paint = denim
    hip = pt[0]
    bib = torso_shell('Bib', 2.3, 0.065, nseg=32, zs=list(np.linspace(2.3, 2.9, 8)), elevs=(),
                      keep=lambda i, j, zc_, az: abs(az) < 0.55, th=0.02, group='Bottom')
    bib.skirt = False
    AZE = 2 * PI * 3 / 32   # bib edge azimuth
    def bib_paint(U, V, m):
        img = P_solid(pal['denim'])(U, V, m); z, az = zc(U, V, m)
        r = 0.48; x = az * r; zt = m['zmax']
        img = mix(img, aa(np.abs(z - (zt - 0.006)) * 500 - 2.0), pal['denim_d'])                       # top hem
        img = mix(img, aa(np.abs((np.abs(az) - AZE) * r + 0.006) * 500 - 2.0), pal['denim_d'])          # side hems
        img = _stitch(img, np.where(z < zt - 0.03 + 0.004, (np.abs(az) - AZE) * r + 0.03, 1.0), z)       # side stitch
        img = _stitch(img, np.where(np.abs(az) * r < AZE * r - 0.03 + 0.004, z - (zt - 0.03), 1.0), x)  # top stitch
        img = _stitch(img, np.where(z < zt - 0.05, (np.abs(az) - AZE) * r + 0.05, 1.0), z)
        return img
    bib.paint = bib_paint
    P += pt
    P.append(bib)
    bbv = piece_bvh(bib)
    # bib pocket with a pencil slot, contrast stitched
    def pk_paint(U, V, m):
        img = P_solid(pal['denim_d'])(U, V, m)
        w, h = 0.28, 0.22
        x = U * w; z = V * h
        d = np.minimum(np.minimum(x, w - x), np.minimum(z, h - z))
        img = _stitch(img, np.where(z < h - 0.02, d - 0.018, 1.0), x + z, w=2.0)
        img = _stitch(img, np.where(z < h - 0.03, x - w * 0.7, 1.0), z, w=2.0)
        img = mix(img, aa(np.abs(z - (h - 0.03)) * 500 - 2.0), pal['denim'])
        img = _stitch(img, z - (h - 0.05), x, w=2.0)
        return img
    pk = surface_patch('BibPocket', bbv, lambda s, t: Vector((-0.14 + s * 0.28, 0, 2.5 + t * 0.22)), Vector((0, 1, 0)),
                       0.008, 6, 5, th=0.012, group='Bottom')
    pk.paint = pk_paint; pk.meta['rect'] = (64, 64); P.append(pk)

    # shoulder straps
    gar = piece_bvh(bib, tee, hip)
    def strap_paint(U, V, m):
        img = P_solid(pal['denim'])(U, V, m)
        L = 1.7; z = V * L; x = U * 0.11
        img = mix(img, aa(np.minimum(x, 0.11 - x) * 500 - 2.0) , pal['denim_d'])
        img = _stitch(img, x - 0.022, z); img = _stitch(img, x - 0.088, z)
        return img
    for s, sg in (('L', 1), ('R', -1)):
        st, rows = _strap('Strap_' + s, sg, gar)
        st.paint = strap_paint; P.append(st)
        sbv = piece_bvh(st)
        # brass clasp + button where the strap hooks onto the bib corner
        loc, n = project(sbv, Vector((sg * 0.205, 0, 2.79)), Vector((0, 1, 0)))
        if loc is not None:
            cl = prim_rbox('Clasp_' + s, loc + n * 0.02, (0.15, 0.035, 0.15), 'brass', bevel=0.02); cl.bone = 'UpperTorso'
            P.append(cl)
            b0 = loc + n * 0.036
            bt = prim_cyl('ClaspButton_' + s, b0, b0 + n * 0.022, 0.035, n=10, col='brass_d'); bt.bone = 'UpperTorso'
            P.append(bt)
        # strap end at the back waistband: brass button
        loc, n = project(sbv, Vector((sg * 0.2, 0, 2.25)), Vector((0, -1, 0)))
        if loc is not None:
            bb = prim_cyl('BackButton_' + s, loc + n * 0.005, loc + n * 0.03, 0.035, n=10, col='brass'); bb.bone = 'LowerTorso'
            P.append(bb)
        # side-opening buttons on the hips
        loc, n = project(piece_bvh(hip), Vector((sg * 0.0, -0.05, 2.2)) + Vector((sg * 0.6, 0, 0)), Vector((-sg, 0, 0)))
        if loc is not None:
            hb = prim_cyl('HipButton_' + s, loc, loc + n * 0.025, 0.035, n=10, col='brass'); hb.bone = 'LowerTorso'
            P.append(hb)

    # rolled cuffs at the trouser hems
    for s in 'LR':
        cf = leg_tube('Cuff_' + s, s, 0.68, 0.53, 0.13, nseg=16, nrows=3, th=0.02)
        def cpaint(U, V, m):
            img = P_solid(pal['denim_d'])(U, V, m); z, az = zc(U, V, m); x = U * m.get('circ', 1.4)
            img = _stitch(img, z - 0.655, x); img = _stitch(img, z - 0.555, x)
            return img
        cf.paint = cpaint; P.append(cf)

    # ---------------- tan work boots ----------------
    def boot_paint(U, V, m):
        img = P_solid(pal['boot'])(U, V, m); z, az = zc(U, V, m)
        st = m['sole_top']
        front = np.cos(az)
        img = mix(img, aa((z - (st + 0.075)) * 500) * aa((0.55 - front) * 60), pal['boot_d'])          # toe cap
        img = mix(img, aa((z - st) * 600), pal['sole'])                                                # sole
        img = mix(img, aa(np.abs(z - (st - 0.02)) * 600 - 1.2), '#5a3d22')                             # sole tread line
        img = _stitch(img, z - (st + 0.014), U * 1.6, col='#f2d48a', w=1.6, period=0.035)                 # welt stitch
        lace = (np.abs(az) < 0.32) & (z > st + 0.12)
        img = mix(img, lace.astype(float) * 0.5, pal['boot_d'])
        ll = np.mod((z - st) / 0.04, 1.0)
        img = mix(img, lace * aa((np.abs(ll - 0.5) - 0.12) * 40), '#3d2a18')                            # laces
        return img
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.045, bulk=0.035, toe=0.035, sole_h=0.07)
        sh.paint = boot_paint; P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 0.66, 0.47, 0.068, nseg=16, group='Feet'))
        shaft.paint = lambda U, V, m: mix(P_solid(pal['boot'])(U, V, m), aa((0.86 - V) * 300), pal['boot_d'])
        P.append(shaft)
    return P, pal
