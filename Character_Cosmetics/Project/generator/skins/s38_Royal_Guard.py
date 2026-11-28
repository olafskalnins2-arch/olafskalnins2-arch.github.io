from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '38', 'Royal_Guard', 'Epic', 0.32


def _wrap(a): return (a + PI) % (2 * PI) - PI


def _sstep2(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def _glove(name, side, t0, t1, off_fn, nseg=14, nrows=10, group='Top', th=0.02):
    """sleeve-like tube from the forearm over the ball hand, closed with a cap at the fingertips"""
    bvh = B.bvh['arm_' + side]
    rows = []; hints = []; vv = []
    for t in np.linspace(t0, t1, nrows):
        c, tg = arm_point(side, t)
        dirs = tube_dirs_b(tg, nseg)
        ring = ray_ring(bvh, c, dirs, off_fn(t), R=0.7, smooth=1)
        if ring is None: break
        rows.append(ring); hints.append(dirs); vv.append(t)
    c, tg = arm_point(side, vv[-1])
    h = bvh.ray_cast(c + tg * 0.6, -tg, 0.6)
    tip = (h[0] + tg * off_fn(vv[-1])) if h[0] is not None else c + tg * 0.08
    vmin, vmax = vv[0], vv[-1]
    pc = _grid_with_ij(name, rows, True, [(v - vmin) / (vmax - vmin) for v in vv], hints, group, None, cap_end=tip)
    pc.meta.update(kind='sleeve', circ=sum((rows[0][j] - rows[0][j - 1]).length for j in range(nseg)), t0=t0, t1=t1, vmin=vmin, vmax=vmax)
    if th: thicken(pc, th)
    pc.rect_key = name.replace('_L', '').replace('_R', '')
    pc.region = 'arm_' + side
    return pc


def cross_strap(name, bvh, sg, width, lift, th, col, x_top=0.36, z_top=2.95, n_arc=7):
    """white cross-belt lying ON the tunic: from the hip (under the waist belt) up the front, over the shoulder
    (sg side) and down the back to the other hip. Every sample is projected onto `bvh` (tunic) and lifted."""
    # path in the front view (x, z), mirrored by sg; starts on top of the shoulder line
    xz = [(x_top, z_top), (x_top - 0.01, 2.86), (0.30, 2.76)]
    a, b = Vector((0.30, 2.76)), Vector((-0.355, 2.30))
    for k in range(1, 9):
        p = a.lerp(b, k / 8); xz.append((p.x, p.y))
    xz.append((-0.37, 2.235))                    # last bit runs straight down: square end tucked under the waist belt
    xz = [(sg * x, z) for x, z in xz]
    samples = []   # (origin, ray dir, across)
    def across_of(i, pts):
        p0 = Vector(pts[max(i - 1, 0)]); p1 = Vector(pts[min(i + 1, len(pts) - 1)])
        t = (p1 - p0).normalized(); ac = Vector((t.y, 0, -t.x))
        if ac.x * sg < 0: ac = -ac
        return ac
    for i in range(len(xz) - 1, 0, -1):          # back: from the hip up to the shoulder
        samples.append((Vector((xz[i][0], 0, xz[i][1])), Vector((0, -1, 0)), across_of(i, xz)))
    for k in range(n_arc):                       # over the shoulder (ray from behind -> from above -> from the front)
        th_ = PI - PI * k / (n_arc - 1)
        d = Vector((0, math.cos(th_), -math.sin(th_)))
        samples.append((Vector((sg * x_top, 0, z_top)), d, Vector((sg, 0, 0))))
    for i in range(1, len(xz)):                  # front: shoulder down to the other hip
        samples.append((Vector((xz[i][0], 0, xz[i][1])), Vector((0, 1, 0)), across_of(i, xz)))
    rows = []; hints = []
    for o, d, ac in samples:
        r = []; hh = []
        for f in (-0.5, 0.0, 0.5):
            loc, n = project(bvh, o + ac * width * f, d)
            if loc is None: loc, n = o + ac * width * f, -d
            r.append(loc + n * lift); hh.append(n)
        rows.append(r); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group='Top')
    head_clear(pc, 0.035)
    if th: thicken(pc, th)
    pc.meta['patch'] = True; pc.region = 'torso'; pc.skirt = False
    return pc


def build():
    pal = {'scarlet': '#c8102e', 'scarlet_d': '#97091f', 'scarlet_l': '#dc2a45',
           'black': '#111111', 'black_l': '#2b2b2e', 'black_d': '#070707',
           'gold': '#e8c35a', 'gold_d': '#a8812a', 'gold_l': '#f7e3a0',
           'white': '#f6f6f2', 'white_d': '#d6d6ce', 'brass': '#d9a93c', 'brass_d': '#8f6a1c',
           'sole': '#050505', 'shine': '#6a6a72'}
    P = []

    # ---------------- black trousers with a scarlet side stripe (under layer first)
    pt = pants('Trousers', 2.22, 0.50, 0.038, hip_off=0.056, leg_extra=lambda z, a: 0.016 + 0.018 * max(0, 1.45 - z))
    def tpaint(U, V, m):
        img = P_solid(pal['black'])(U, V, m); z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            sg = 1 if m.get('side') == 'L' else -1
            out = np.abs(_wrap(az - sg * PI / 2))
            img = mix(img, aa((out - 0.18) * 260), pal['scarlet'])                 # broad red stripe on the outer seam
            img = mix(img, aa((np.abs(az) - 0.006) * 400) * 0.7, pal['black_l'])  # pressed front crease
        return img
    for p in pt: p.paint = tpaint; p.rect_key = p.name
    P += pt

    # ---------------- scarlet tunic, hip length, hanging over the trousers
    tunic = torso_shell('Tunic', 1.84, 0.058, nseg=32, extra=lambda z, a: 0.014 + 0.035 * max(0, 2.12 - z),
                        th=0.022, hang=2.3, over=pt)
    def tunic_paint(U, V, m):
        img = P_solid(pal['scarlet'])(U, V, m); z, az = zc(U, V, m)
        zmin = m['zmin']
        # side seams + back seam
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.55, pal['scarlet_d'])
        img = mix(img, aa((PI - np.abs(az) - 0.006) * 300) * 0.55, pal['scarlet_d'])
        # front closure with white piping
        img = mix(img, aa((np.abs(az) - 0.007) * 400) * (z < 3.15), pal['white'])
        img = mix(img, aa((np.abs(az - 0.02) - 0.004) * 400) * (z < 3.15) * 0.6, pal['scarlet_d'])
        # white piped hem
        img = mix(img, aa((z - (zmin + 0.022)) * 500), pal['white'])
        img = mix(img, aa((z - (zmin + 0.008)) * 500), pal['scarlet_d'])
        # skirt flaps over the hips (front) with white piping
        for sg in (-1, 1):
            u = sg * az - 0.95
            box = np.maximum(np.abs(u) - 0.26, np.maximum(z - 2.06, 1.9 - z))
            img = mix(img, aa(box * 400) * 0.25, pal['scarlet_d'])
            img = mix(img, aa((np.abs(box) - 0.004) * 400), pal['white'])
        # back skirt pleats / vent flaps
        for c in (PI - 0.32, -(PI - 0.32)):
            img = mix(img, aa((np.abs(az - c) - 0.006) * 400) * (z < 2.12), pal['white'])
            img = mix(img, aa((np.abs(az - c) - 0.05) * 300) * (z < 2.12) * 0.18, pal['scarlet_d'])
        # chest fold shading under the arms
        img = mix(img, np.clip(np.abs(np.sin(az)) ** 6, 0, 1) * 0.12, pal['scarlet_d'])
        return img
    tunic.paint = tunic_paint; P.append(tunic)

    # ---------------- white cross-belts fitted on the tunic, crossing on the chest and on the back
    tb = piece_bvh(tunic)
    sA = cross_strap('CrossBelt_A', tb, 1, 0.11, 0.012, 0.014, 'white')
    sB = cross_strap('CrossBelt_B', tb, -1, 0.11, 0.036, 0.014, 'white')
    P += [sA, sB]
    straps_bv = piece_bvh(sB)
    # brass plate where the belts cross
    loc, n = project(straps_bv, Vector((0, 0, 2.549)), Vector((0, 1, 0)))
    pc0 = loc + n * 0.02
    plate = prim_rbox('BeltPlate', pc0, (0.15, 0.035, 0.19), 'brass'); plate.bone = 'UpperTorso'; P.append(plate)
    st = prim_cyl('PlateStar', pc0 + Vector((0, -0.012, 0)), pc0 + Vector((0, -0.03, 0)), 0.045, n=8, col='gold_l')
    st.bone = 'UpperTorso'; P.append(st)
    rim = prim_cyl('PlateBoss', pc0 + Vector((0, -0.025, 0)), pc0 + Vector((0, -0.038, 0)), 0.018, n=8, col='brass_d')
    rim.bone = 'UpperTorso'; P.append(rim)

    # ---------------- white waist belt fitted on the tunic + straps, brass buckle plate
    belt = band('Belt', 2.12, 2.27, 0.012, th=0.02, bvh=piece_bvh(tunic, sA, sB), hang=2.37)
    belt.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.minimum(V - 0.08, 0.92 - V) * -200) * 0.8, pal['white_d'])
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.195)), Vector((0, 1, 0)))
    o = loc + n * 0.018
    bk = prim_rbox('BeltBuckle', o, (0.2, 0.035, 0.15), 'brass'); bk.bone = 'LowerTorso'; P.append(bk)
    bk2 = prim_rbox('BuckleBoss', o + Vector((0, -0.018, 0)), (0.11, 0.02, 0.08), 'gold_l'); bk2.bone = 'LowerTorso'; P.append(bk2)

    # ---------------- two rows of gold buttons (kept clear of the cross-belts and the waist belt)
    for r, z in enumerate((3.02, 2.88, 2.55, 2.03, 1.96)):
        for c, x in enumerate((-0.15, 0.15)):
            loc, n = project(tb, Vector((x, 0, z)), Vector((0, 1, 0)))
            P.append(prim_cyl(f'Button{r}{c}', loc - n * 0.004, loc + n * 0.024, 0.03, n=10, col='gold', group='Top'))
    # buttons on the hip flaps
    for sg in (-1, 1):
        a = 0.95 * sg
        d = Vector((math.sin(a), -math.cos(a), 0))
        loc, n = project(tb, d * 0.0 + Vector((0, 0, 1.98)) + d * 1.5, -d)
        b = prim_cyl(f'FlapButton{sg}', loc - n * 0.004, loc + n * 0.022, 0.026, n=10, col='gold', group='Top')
        b.bone = 'LowerTorso'; P.append(b)

    # ---------------- gold braided stand collar
    col_ = collar('Collar', 'stand', h=0.09, flare=0.02, open_front=0.1, th=0.02)
    def braid(U, V, m):
        img = P_solid(pal['gold'])(U, V, m)
        k = (U * 60 + V * 3) % 1.0
        img = mix(img, aa((np.abs(k - 0.5) - 0.18) * 30) * 0.45, pal['gold_d'])
        img = mix(img, aa((np.abs(k - 0.2) - 0.06) * 30) * 0.5, pal['gold_l'])
        img = mix(img, aa(np.minimum(V - 0.12, 0.92 - V) * -200), pal['gold_d'])
        return img
    col_.paint = braid; P.append(col_)

    # ---------------- sleeves, gold cuff braid, white gloves
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.95, 0.055, extra=lambda t, a: 0.01 + 0.01 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['scarlet'])(U, V, m), aa(np.abs(V - 0.48) * 400 - 1) * 0.35, pal['scarlet_d'])
        sl.rect_key = 'Sleeve'; P.append(sl)
        cf = sleeve('Cuff_' + s, s, 0.82, 0.955, 0.1, nrows=4, cap=False, th=0.02, extra=lambda t, a: 0.012 * (t - 0.82) / 0.13)
        def cpaint(U, V, m):
            img = braid(U, V * 0.5 + 0.25, m)
            img = mix(img, aa(np.abs(V - 0.5) * 400 - 6), pal['scarlet'])        # scarlet band between two braids
            img = mix(img, aa(np.abs(V - 0.5) * 400 - 1.5), pal['white'])
            return img
        cf.paint = cpaint; cf.rect_key = 'Cuff'; P.append(cf)
        gl = _glove('Glove_' + s, s, 0.9, 1.3, lambda t: 0.034, nrows=13)
        gl.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.abs(V - 0.25) * 400 - 1) * 0.6, pal['white_d'])
        P.append(gl)

    # ---------------- gold epaulettes: shoulder board on top of the cross-belt, crescent pad + bullion fringe
    sleeves = [p for p in P if p.name.startswith('Sleeve_')]
    top_bv = piece_bvh(tunic, sA, sB, *sleeves)
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        bd = surface_patch(f'EpBoard{s}', top_bv, lambda u, t, sg=sg: Vector((sg * (0.28 + 0.22 * t), -0.075 + 0.15 * u, 3.9)),
                           Vector((0, 0, -1)), 0.014, 4, 5, th=0.018)
        bd.paint = braid; bd.rect_key = 'EpBoard'; bd.bone = 'UpperTorso'; P.append(bd)
        loc, n = project(top_bv, Vector((sg * 0.5, 0, 3.9)), Vector((0, 0, -1)))
        cz = loc.z + 0.03
        cr = prim_rbox(f'EpPad{s}', Vector((sg * 0.5, 0, cz)), (0.13, 0.3, 0.08), 'gold'); cr.bone = 'UpperTorso'; P.append(cr)
        loc2, _ = project(top_bv, Vector((sg * 0.29, 0, 3.9)), Vector((0, 0, -1)))
        btn = prim_cyl(f'EpButton{s}', loc2 + Vector((0, 0, 0.02)), loc2 + Vector((0, 0, 0.045)), 0.03, n=10, col='gold_l')
        btn.bone = 'UpperTorso'; P.append(btn)
        # bullion fringe hangs over the top of the sleeve and swings with the upper arm (rigid on it)
        slv = piece_bvh(*[p for p in sleeves if p.name.endswith(s)])
        for k, y in enumerate(np.linspace(-0.13, 0.13, 8)):
            pts = []
            for dz in (0.0, 0.06, 0.12, 0.18, 0.22):
                z = cz - 0.01 - dz
                h, _ = project(slv, Vector((sg * 0.62, y, z)), Vector((-sg, 0, 0)))
                x = max(0.56, (abs(h.x) + 0.035) if h is not None else 0.62)
                pts.append(Vector((sg * x, y * (1 + 0.2 * dz / 0.22), z)))
            f = tube_path(f'Fringe{s}{k}', pts, 0.019, 'gold_d' if k % 2 else 'gold', n=5, group='Top')
            f.rigid = True; f.region = 'arm_' + s; P.append(f)

    # ---------------- polished black boots
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.038, bulk=0.012, toe=0.06, sole_h=0.04, open_elev=42)
        def spaint(U, V, m):
            img = P_solid(pal['black'])(U, V, m); z, az = zc(U, V, m)
            img = mix(img, np.clip(np.cos(az), 0, 1) ** 4 * np.exp(-((V - 0.6) / 0.14) ** 2) * 0.8, pal['shine'])   # toe-cap shine
            img = mix(img, np.clip(np.cos(az), 0, 1) ** 8 * np.exp(-((V - 0.62) / 0.05) ** 2) * 0.7, '#b8b8c0')
            img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.05)) * 500 - 0.6) * (np.cos(az) > 0.5) * 0.7, pal['black_l'])
            img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.008)) * 500 - 0.6) * 0.6, pal['black_l'])   # welt stitch
            return mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
        sh.paint = spaint; sh.rect_key = 'Boot'; P.append(sh)
    return P, pal
