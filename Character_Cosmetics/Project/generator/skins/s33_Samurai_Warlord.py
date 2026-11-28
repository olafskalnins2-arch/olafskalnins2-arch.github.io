from o04 import *
import rigfix as _RF33

NUM, NAME, RARITY, MAXD = '33', 'Samurai_Warlord', 'Epic', 0.32

PAL33 = {'red': '#b3202a', 'red_d': '#7d121b', 'red_l': '#d5454c', 'black': '#1c1c20', 'black_l': '#3a3a42',
         'indigo': '#1f2a44', 'indigo_d': '#141b2e', 'indigo_l': '#33426a', 'gold': '#d9b44a', 'gold_d': '#9c7a24',
         'leather': '#2a1c14', 'leather_l': '#4a3324', 'sole': '#111113', 'steel': '#c9ced6'}


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def _np_ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- paints
def _lacquer(img, f, base_l, base_d):
    """glossy lacquer shading along f (0 bottom .. 1 top of a plate)"""
    img = mix(img, np.clip(1 - np.abs(f - 0.62) / 0.22, 0, 1) * 0.45, base_l)
    img = mix(img, np.clip((0.25 - f) / 0.25, 0, 1) * 0.35, base_d)
    return img


def _cord_pairs(img, x, xs, gap, w, col, mask=1.0):
    """vertical gold cord pairs (sugake odoshi) at x positions xs (units)"""
    for c in xs:
        for o in (-gap, gap):
            img = mix(img, aa((np.abs(x - (c + o)) - w) * 900) * mask, col)
    return img


def _do_paint(LB):
    pal = PAL33

    def f(U, V, m):
        z, az = zc(U, V, m)
        img = P_solid(pal['red'])(U, V, m)
        x = az * 0.52                                     # approx units around the body
        top = LB[-1]
        lam = z < top
        k = np.clip(np.floor((z - LB[0]) / (LB[1] - LB[0])), 0, len(LB) - 2)
        fr = np.clip((z - (LB[0] + k * (LB[1] - LB[0]))) / (LB[1] - LB[0]), 0, 1)
        img = _lacquer(img, fr, pal['red_l'], pal['red_d'])
        # shadow under the step of the lame above + dark lacquer rim at each lame bottom
        img = mix(img, aa((0.88 - fr) * 300) * 0.55 * lam, pal['red_d'])
        img = mix(img, aa((fr - 0.06) * 300) * lam, pal['black'])
        # gold lacing pairs, columns every ~0.2 units (aligned on the front centre)
        step = 0.2
        xm = (x + step / 2) % step - step / 2
        for o in (-0.028, 0.028):
            img = mix(img, aa((np.abs(xm - o) - 0.009) * 900) * lam * (fr > 0.06), pal['gold'])
        # lacing holes at the lame bottoms
        img = mix(img, aa((np.hypot((np.abs(xm) - 0.028) * 1.0, (fr - 0.14) * (LB[1] - LB[0])) - 0.008) * 900) * lam, pal['black'])
        # breast plate (munaita) + shoulder straps: black lacquer, gold rims, gold rivets
        bp = z >= top
        img = mix(img, bp.astype(float), pal['black'])
        img = mix(img, aa(np.abs(z - (top + 0.02)) * 600 - 3) * bp, pal['gold'])
        rv = (np.hypot(((x + 0.06) % 0.12) - 0.06, z - (top + 0.065)) < 0.013)
        img = mix(img, rv.astype(float) * bp, pal['gold'])
        img = mix(img, aa((np.abs(z - (top + 0.065)) - 0.025) * 600) * 0.25 * bp, pal['black_l'])
        return img
    return f


def _kz_paint(bottom=False):
    pal = PAL33

    def f(U, V, m):
        z, az = zc(U, V, m)
        img = P_solid(pal['red'])(U, V, m)
        img = _lacquer(img, V, pal['red_l'], pal['red_d'])
        r = 0.7
        x = az * r
        pw = PI / 4 * r                                    # panel width (units)
        xp = (x % pw)                                      # position inside its panel
        # panel edges (separate hanging plates)
        img = mix(img, aa((np.minimum(xp, pw - xp) - 0.006) * 900), pal['black'])
        # top rim: black lacquer edge + horizontal gold cord
        img = mix(img, aa((0.86 - V) * 260), pal['black'])
        img = mix(img, aa((np.abs(V - 0.79) - 0.035) * 260), pal['gold'])
        # vertical lacing pairs, 3 per panel
        xs = [pw * (i + 0.5) / 3 for i in range(3)]
        img = _cord_pairs(img, xp, xs, 0.022, 0.008, pal['gold'], mask=(V < 0.76) * (V > 0.04))
        # bottom rim
        img = mix(img, aa((V - 0.045) * 300), pal['black'])
        if bottom:   # hishinui: gold cross knots along the lowest lame
            for c in xs:
                dx = xp - c; dz = (V - 0.3) * 0.22
                arm1 = np.abs(dx - dz) / 1.414; arm2 = np.abs(dx + dz) / 1.414
                inside = (np.abs(dx) < 0.04) * (np.abs(dz) < 0.04)
                img = mix(img, aa((np.minimum(arm1, arm2) - 0.008) * 900) * inside, pal['gold'])
        return img
    return f


def _sode_paint(U, V, m):
    pal = PAL33
    img = P_solid(pal['red'])(U, V, m)
    img = _lacquer(img, V, pal['red_l'], pal['red_d'])
    x = U * m['width']
    img = mix(img, aa((0.86 - V) * 260), pal['black'])
    img = mix(img, aa((np.abs(V - 0.79) - 0.035) * 260), pal['gold'])
    xs = [m['width'] * c for c in (0.2, 0.5, 0.8)]
    img = _cord_pairs(img, x, xs, 0.022, 0.008, pal['gold'], mask=(V < 0.76) * (V > 0.04))
    img = mix(img, aa((V - 0.05) * 300), pal['black'])
    img = mix(img, aa((np.minimum(U, 1 - U) * m['width'] - 0.012) * 900), pal['black'])
    return img


def _kanmuri_paint(U, V, m):
    pal = PAL33
    img = P_solid(pal['black'])(U, V, m)
    img = mix(img, aa((np.minimum(V, 1 - V) - 0.16) * 300), pal['gold'])
    x = U * m['width']
    for c in (0.15, 0.5, 0.85):
        img = mix(img, aa((np.hypot(x - c * m['width'], (V - 0.5) * 0.08) - 0.014) * 900), pal['gold'])
    return img


def _kote_paint(U, V, m):
    pal = PAL33
    img = P_solid(pal['indigo'])(U, V, m)
    circ = m.get('circ', 1.0)
    x = U * circ; L = 0.95
    y = V * L
    # chain mail (kusari) on the upper arm: small dark rings on a lattice
    gx = (x % 0.05) - 0.025; gy = (y % 0.05) - 0.025
    ring = np.abs(np.hypot(gx, gy) - 0.014)
    img = mix(img, aa((ring - 0.004) * 900) * (V < 0.5), pal['black_l'])
    # forearm splints (shino): black lacquer bars with gold edges
    fa = (V > 0.53) * (V < 0.9)
    n = 6; pw = circ / n
    xp = x % pw - pw / 2
    bar = np.abs(xp) < pw * 0.3
    img = mix(img, (bar * fa).astype(float), pal['black'])
    img = mix(img, aa((np.abs(np.abs(xp) - pw * 0.3) - 0.006) * 900) * fa, pal['gold'])
    img = mix(img, aa((np.abs(V - 0.53) - 0.006) * 400), pal['gold'])
    img = mix(img, aa((np.abs(V - 0.9) - 0.006) * 400), pal['gold'])
    return img


def _hakama_paint(U, V, m):
    pal = PAL33
    z, az = zc(U, V, m)
    img = P_solid(pal['indigo'])(U, V, m)
    circ = m.get('circ', 1.0)
    n = 14
    q = (U * n) % 1.0
    img = mix(img, (0.5 + 0.5 * np.cos(q * 2 * PI)) * 0.35, pal['indigo_l'])
    img = mix(img, aa((np.minimum(q, 1 - q) * circ / n - 0.004) * 900) * 0.8, pal['indigo_d'])
    return img


def _suneate_paint(U, V, m):
    pal = PAL33
    z, az = zc(U, V, m)
    img = P_solid(pal['red'])(U, V, m)
    front = np.abs(az) < 2.0
    # splints over the front, cloth (indigo) behind the calf
    img = mix(img, (~front).astype(float), pal['indigo'])
    sp = np.abs(((az + 2.0) / 0.8) % 1 - 0.5)
    img = mix(img, (1 - 2 * sp) ** 2 * 0.55 * front, pal['red_l'])
    img = mix(img, (2 * sp) ** 3 * 0.5 * front, pal['red_d'])
    sd = (0.5 - sp) * 0.8 * 0.3                         # distance to the splint seam (units)
    img = mix(img, aa((sd - 0.006) * 900) * front, pal['black'])
    # gold rims, leather ties
    img = mix(img, aa((m['zmax'] - 0.035 - z) * 600), pal['gold'])
    img = mix(img, aa((z - (m['zmin'] + 0.03)) * 600), pal['gold'])
    for zz in (0.62, 0.9):
        img = mix(img, aa((np.abs(z - zz) - 0.012) * 600), pal['leather'])
    return img


def _shoe_paint(U, V, m):
    pal = PAL33
    z, az = zc(U, V, m)
    img = P_solid(pal['leather'])(U, V, m)
    img = mix(img, aa((np.abs(z - (m['sole_top'] + 0.05)) - 0.006) * 600), pal['leather_l'])
    img = mix(img, aa((np.abs(az) - 0.025) * 300) * (z < m['sole_top'] + 0.12), pal['sole'])   # split toe (tabi)
    return mix(img, aa((z - m['sole_top']) * 600), pal['sole'])


def _crest_paint(U, V, m):
    pal = PAL33
    r = V * m['R']; th = U * 2 * PI
    img = P_solid(pal['gold'])(U, V, m)
    n = 16
    p = (th * n / (2 * PI)) % 1.0
    rt = m['R'] * (0.7 + 0.1 * np.sin(PI * p))
    img = mix(img, aa((r - rt) * 900), pal['black'])                                  # black ring outside the petals
    img = mix(img, aa((np.minimum(p, 1 - p) * 2 * PI * r / n - 0.0035) * 900) * (r > m['R'] * 0.26) * (r < rt), pal['gold_d'])
    img = mix(img, aa((np.abs(r - rt) - 0.004) * 900), pal['gold_d'])
    img = mix(img, aa((np.abs(r - m['R'] * 0.26) - 0.004) * 900), pal['gold_d'])
    return img


def _obi_paint(U, V, m):
    pal = PAL33
    img = P_solid(pal['leather'])(U, V, m)
    img = mix(img, aa((np.minimum(V, 1 - V) - 0.14) * 300), pal['gold'])
    img = mix(img, aa((np.abs(((U * 40) % 1) - 0.5) - 0.18) * 30) * (np.abs(V - 0.5) < 0.22) * 0.35, pal['leather_l'])
    return img


def _collar_paint(U, V, m):
    pal = PAL33
    img = P_solid(pal['black'])(U, V, m)
    img = mix(img, aa((0.8 - V) * 300), pal['gold'])
    img = mix(img, aa((np.abs(V - 0.45) - 0.08) * 300), pal['red'])
    return img


def _bib_paint(U, V, m):
    pal = PAL33
    img = P_solid(pal['red'])(U, V, m)
    k = np.floor(V * 3); fr = V * 3 - k
    img = _lacquer(img, 1 - fr, pal['red_l'], pal['red_d'])
    img = mix(img, aa((fr - 0.12) * 300), pal['black'])
    x = U * m['width']
    img = _cord_pairs(img, x, [m['width'] * c for c in (0.2, 0.4, 0.6, 0.8)], 0.018, 0.007, pal['gold'], mask=fr > 0.12)
    img = mix(img, aa((np.minimum(U, 1 - U) * m['width'] - 0.012) * 900), pal['gold'])
    return img


# ---------------------------------------------------------------- geometry helpers
def _strip(name, rows, hints, group='Top', th=0.018, col=None):
    pc = grid_piece(name, rows, closed=False, hints=hints, group=group, col=col,
                    v_vals=[i / (len(rows) - 1) for i in range(len(rows))])
    if th: thicken(pc, th)
    return pc


def _panelize(pc, nseg, npan=8):
    """Cut a (not yet thickened, cap-less) torso_shell ring into npan separate hanging plates (vertices duplicated at
    the cuts, identical at rest) and tag each plate with its side like cut_slits does (front/side +-1, back-side +-3,
    back-inner +-2), so each plate hangs off its own thigh."""
    per = nseg // npan
    nv = []; nh = []; tags = []; faces = []; key = {}
    for (i, j), f in zip(pc.meta['fij'], pc.faces):
        g = (j // per) % npan
        azc = -PI + (g + 0.5) * 2 * PI / npan
        s = 1 if azc > 0 else -1
        t = 1 if abs(azc) < PI / 2 else (3 if abs(azc) < 3 * PI / 4 else 2)
        out = []
        for v in f:
            k = (v, g)
            if k not in key:
                key[k] = len(nv); nv.append(pc.verts[v].copy()); nh.append(pc.hint[v]); tags.append(s * t)
            out.append(key[k])
        faces.append(tuple(out))
    pc.verts = nv; pc.hint = nh; pc.faces = faces
    return tags


def kusazuri_lame(name, z0, z1, off, under, legs, paint, rect_key, th=0.02):
    nseg = 48
    pc = torso_shell(name, z0, off, nseg=nseg, zs=[z0, (z0 + z1) / 2, z1], elevs=(),
                     extra=lambda z, a, z1=z1, z0=z0: 0.022 * (z1 - z) / (z1 - z0), th=0, group='Bottom',
                     hang=z1 + 0.001, over=under + legs, over_gap=0.026)
    tags = _panelize(pc, nseg)
    thicken(pc, th)
    pc.meta['panel'] = tags + tags
    pc.meta['slit_top'] = RF_SLIT_TOP()
    pc.meta['rect'] = (512, 64)
    pc.paint = paint; pc.rect_key = rect_key
    pc.region = 'torso'; pc.skirt = True
    return pc


def build():
    pal = dict(PAL33)
    P = []
    # ---------------- hakama (wide indigo trousers, gathered into the shin guards)
    def hk(z, a):
        bul = 0.12 * _ss(1.92, 1.4, z) * (1 - _ss(1.16, 1.0, z))
        return 0.02 + bul * (0.5 + 0.5 * math.sin(a))
    pt = pants('Hakama', 2.1, 0.78, 0.05, hip_off=0.07, leg_extra=hk)
    for p in pt: p.paint = _hakama_paint
    # ---------------- do (lamellar chest armour: real stepped lames)
    LB = [2.12, 2.24, 2.36, 2.48, 2.60, 2.72, 2.84]
    S = 0.02
    def do_ext(z, a):
        e = 0.0
        if z < LB[-1] - 1e-6:
            k = min(len(LB) - 2, max(0, int((z - LB[0] + 1e-6) // (LB[1] - LB[0]))))
            fr = (z - LB[k]) / (LB[k + 1] - LB[k] - 0.007)
            e = S * (1 - min(1.0, max(0.0, fr)))
        else:
            e = S * max(0.0, 1 - (z - LB[-1]) / 0.1)
        bul = 0.035 * max(0.0, math.cos(a)) ** 2 * _ss(2.2, 2.5, z) * (1 - _ss(2.85, 3.05, z))
        return 0.004 + e + bul
    zs = []
    for k in range(len(LB) - 1):
        zs += [LB[k], LB[k] + 0.06, LB[k + 1] - 0.007]
    zs += [LB[-1], 2.9, 2.95]
    do = torso_shell('Do', LB[0], 0.085, nseg=36, zs=zs, extra=do_ext, th=0.03)
    do.paint = _do_paint(LB); do.meta['rect'] = (512, 256); P.append(do)
    # ---------------- kusazuri: four stacked hanging lames, each cut into 8 plates
    legs = list(pt)
    under = [do]
    lames = []
    spec = ((2.00, 2.24, 0.10), (1.83, 2.06, 0.12), (1.66, 1.89, 0.14), (1.49, 1.72, 0.16))
    for k, (z0, z1, off) in enumerate(spec):
        last = k == len(spec) - 1
        lm = kusazuri_lame(f'Kusazuri{k}', z0, z1, off, under, legs, _kz_paint(last), 'KusazuriB' if last else 'Kusazuri')
        P.append(lm); lames.append(lm); under = under + [lm]
    P += pt
    # ---------------- obi (leather sash) over the do bottom + top lame
    obi = band('Obi', 2.12, 2.22, 0.012, th=0.02, bvh=piece_bvh(do, lames[0]), hang=2.32, group='Bottom')
    obi.paint = _obi_paint; obi.meta['rect'] = (512, 32); P.append(obi)
    ob = piece_bvh(obi)
    loc, n = project(ob, Vector((0, 0, 2.17)), Vector((0, 1, 0)))
    knot = prim_rbox('ObiKnot', loc + n * 0.03, (0.13, 0.06, 0.1), 'leather_l', group='Bottom'); knot.bone = 'LowerTorso'; P.append(knot)
    # ---------------- throat guard (nodowa): stand collar + crescent lamellar bib
    col = collar('Nodowa', 'stand', h=0.08, flare=0.07, th=0.02)
    col.paint = _collar_paint; col.meta['rect'] = (256, 64); P.append(col)
    db = piece_bvh(do)
    bw = 0.62
    def bib(s, t):
        w = (0.31 - 0.1 * t)
        sag = 0.06 * (1 - (2 * s - 1) ** 2)
        return Vector(((s - 0.5) * 2 * w, 0, 3.12 - t * (0.15 + sag)))
    bb = surface_patch('NodowaBib', db, bib, Vector((0, 1, 0)), 0.014, 9, 4, th=0.016)
    head_clear(bb, 0.035)
    bb.paint = _bib_paint; bb.meta['width'] = bw; bb.meta['rect'] = (256, 64); bb.bone = 'UpperTorso'; P.append(bb)
    # ---------------- crest emblem (gold chrysanthemum mon) on the chest
    loc, n = project(db, Vector((0, 0, 2.6)), Vector((0, 1, 0)))
    a1 = Vector((1, 0, 0)); a1 = (a1 - n * a1.dot(n)).normalized(); a2 = n.cross(a1)
    CR = 0.15; NS = 32
    radii = [0.02, 0.05, 0.08, 0.105, 0.125, CR]
    lift = 0.0
    for r in (CR, CR * 0.6):
        for j in range(16):
            th_ = 2 * PI * j / 16
            q = loc + (a1 * math.cos(th_) + a2 * math.sin(th_)) * r
            h = db.ray_cast(q + n * 1.0, -n, 2.0)
            if h[0] is not None: lift = max(lift, (h[0] - q).dot(n))
    C0 = loc + n * (lift + 0.035)
    rows = [[C0 + (a1 * math.cos(2 * PI * j / NS) + a2 * math.sin(2 * PI * j / NS)) * r for j in range(NS)] for r in radii]
    crest = grid_piece('Crest', rows, True, v_vals=[r / CR for r in radii], hints=[[n] * NS for _ in rows], group='Extras', cap_start=C0)
    thicken(crest, 0.02)
    crest.paint = _crest_paint; crest.meta.update(R=CR, rect=(256, 64)); crest.bone = 'UpperTorso'; P.append(crest)
    rim = [C0 - n * 0.008 + (a1 * math.cos(2 * PI * j / 24) + a2 * math.sin(2 * PI * j / 24)) * (CR + 0.004) for j in range(25)]
    cr = tube_path('CrestRim', rim, 0.018, 'gold', n=6, caps=False); cr.bone = 'UpperTorso'; P.append(cr)
    # ---------------- agemaki (gold cord bow knot) on the back
    loc, n = project(db, Vector((0, 0, 2.66)), Vector((0, -1, 0)))
    kc = loc + n * 0.045
    ag = prim_rbox('Agemaki', kc, (0.09, 0.07, 0.09), 'gold'); ag.bone = 'UpperTorso'; P.append(ag)
    def onback(x, z, lift):
        l2, n2 = project(db, Vector((x, 0, z)), Vector((0, -1, 0)))
        return l2 + n2 * lift
    for sg in (-1, 1):
        pts = [onback(sg * (0.03 + 0.14 * math.sin(a) ** 0.8 * (1 if a < PI else 1)), 2.66 + 0.08 * math.sin(2 * a), 0.04)
               for a in np.linspace(0.15, PI - 0.15, 9)]
        pts = [kc] + pts + [kc]
        ag.merge(tube_path(f'AgemakiLoop{sg}', pts, 0.016, 'gold', n=6))
        tp = [onback(sg * (0.03 + 0.05 * f), 2.62 - 0.32 * f, 0.05 + 0.02 * f) for f in np.linspace(0, 1, 7)]
        ag.merge(tube_path(f'AgemakiTassel{sg}', tp, 0.02, 'gold', n=6, rfn=lambda f: 0.014 + 0.03 * f ** 3))
    # ---------------- arms: kote (armoured sleeves), elbow plates, gold cuffs, sode (big shoulder plates)
    kotes = {}
    for s in 'LR':
        k = sleeve('Kote_' + s, s, 0.0, 0.95, 0.05, extra=lambda t, a: 0.012 + 0.012 * math.sin(min(1, t / 0.5) * PI))
        k.paint = _kote_paint; k.meta['rect'] = (256, 256); P.append(k); kotes[s] = k
        P.append(sleeve('Hiji_' + s, s, 0.45, 0.55, 0.075, nrows=3, cap=False, col='black',
                        extra=lambda t, a: 0.03 * max(0, math.cos(a + PI)) + 0.01))
        P.append(sleeve('Cuff_' + s, s, 0.89, 0.97, 0.085, nrows=3, cap=False, col='gold'))
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        A, _ = arm_point(s, 0.03)
        _, tg = arm_point(s, 0.22)
        nn = Vector((sg, 0, 0)); nn = (nn - tg * nn.dot(tg)).normalized()
        bv = tg.cross(nn).normalized()
        D = 0.3
        Ltot = 0.74
        need = 0.0
        for q in kotes[s].verts + do.verts:
            d = (q - A).dot(tg)
            if -0.06 < d < Ltot + 0.06:
                rq = (q - A) - tg * d
                if rq.dot(nn) > -0.02: need = max(need, (rq + nn * D).length)
        R0 = need + 0.035 + 0.018
        print('S33 sode', s, 'need', round(need, 3), 'R0', round(R0, 3))
        nl = 6; hl = 0.15; st = (Ltot - hl) / (nl - 1)
        sode = None
        for k in range(nl):
            d0 = k * st; d1 = d0 + hl
            R = R0 + k * 0.02
            rows = []; hints = []
            for dd in np.linspace(d1, d0, 3):                # bottom row first
                fl = (dd - d0) / hl                            # 0 top .. 1 bottom of this lame (dd grows downward)
                w = 0.27 + 0.06 * (dd / Ltot)
                Rr = R + 0.012 * fl
                ph = w / Rr
                c = A + tg * dd - nn * D
                rows.append([c + (nn * math.cos(p) + bv * math.sin(p)) * Rr for p in np.linspace(-ph, ph, 9)])
                hints.append([nn * math.cos(p) + bv * math.sin(p) for p in np.linspace(-ph, ph, 9)])
            lm = _strip(f'Sode{k}_' + s, rows, hints)
            sode = lm if sode is None else sode.merge(lm)
        sode.name = 'Sode_' + s
        sode.paint = _sode_paint; sode.rect_key = 'Sode'; sode.meta = {'width': 0.6, 'rect': (128, 64)}
        sode.bone = ('Left' if s == 'L' else 'Right') + 'UpperArm'; P.append(sode)
        # kanmuri-ita: black top bar with gold rims + a gold cord up to the shoulder
        rows = []; hints = []
        Rk = R0 - 0.004
        for dd in (0.045, -0.045):
            ph = 0.29 / Rk; c = A + tg * dd - nn * D
            rows.append([c + (nn * math.cos(p) + bv * math.sin(p)) * Rk for p in np.linspace(-ph, ph, 9)])
            hints.append([nn * math.cos(p) + bv * math.sin(p) for p in np.linspace(-ph, ph, 9)])
        km = _strip('Kanmuri_' + s, rows, hints, th=0.03)
        km.paint = _kanmuri_paint; km.rect_key = 'Kanmuri'; km.meta = {'width': 0.6, 'rect': (128, 32)}
        km.bone = sode.bone; P.append(km)
    # ---------------- shin guards (suneate) + tabi boots
    for s in 'LR':
        sn = _shin(leg_tube('Suneate_' + s, s, 0.99, 0.5, 0.115, nseg=16, group='Feet', extra=lambda z, a: 0.012 * max(0, math.cos(a))))
        sn.paint = _suneate_paint; sn.meta['rect'] = (128, 128); P.append(sn)
        sh = shoe('Tabi_' + s, s, off=0.045, bulk=0.025, toe=0.03, sole_h=0.04)
        sh.paint = _shoe_paint; P.append(sh)
    # ---------------- tachi-style katana hung from the obi on the left hip
    allb = piece_bvh(*[p for p in P if p.group in ('Bottom', 'Top') and not p.name.startswith(('Kote', 'Hiji', 'Cuff', 'Sode', 'Kanmuri'))])
    F = Vector((0.0, -0.5, 2.06)); Bk = Vector((0.0, 0.78, 1.62))
    rs = 0.032
    xneed = 0.0
    for f in np.linspace(0, 1, 15):
        q = F.lerp(Bk, f)
        h = allb.ray_cast(Vector((2.0, q.y, q.z)), Vector((-1, 0, 0)), 3.0)
        if h[0] is not None: xneed = max(xneed, h[0].x + rs + 0.015)
    F.x = xneed; Bk.x = xneed
    print('S33 xneed', round(xneed, 3), [round(max(v.x for v in l.verts), 3) for l in lames])
    armb = B.bvh['arm_L']
    for f in np.linspace(0, 1, 7):
        q = F.lerp(Bk, f)
        h = armb.ray_cast(Vector((0.2, q.y, q.z)), Vector((1, 0, 0)), 2.0)
        print('S33 katana', [round(c, 3) for c in q], 'arm inner x', None if h[0] is None else round(h[0].x, 3))
    ax = (Bk - F).normalized()
    up = (Z - ax * Z.dot(ax)).normalized()
    saya_pts = [F.lerp(Bk, f) + up * (0.05 * math.sin(PI * f) - 0.0) for f in np.linspace(0, 1, 9)]
    kat = tube_path('Saya', saya_pts, rs, 'black', n=8)
    parts = [kat]
    parts.append(prim_cyl('Koiguchi', F - ax * 0.005, F + ax * 0.05, rs + 0.01, n=8, col='gold'))
    parts.append(prim_cyl('Kojiri', Bk - ax * 0.08, Bk + ax * 0.01, rs + 0.008, rs * 0.7, n=8, col='gold'))
    for f in (0.18, 0.42):
        c = F.lerp(Bk, f) + up * (0.05 * math.sin(PI * f))
        parts.append(prim_cyl(f'SayaBand{f}', c - ax * 0.03, c + ax * 0.03, rs + 0.012, n=8, col='gold'))
    tsu = F - ax * 0.012
    parts.append(prim_cyl('Tsuba', tsu - ax * 0.012, tsu + ax * 0.012, 0.085, n=12, col='gold'))
    hilt_dir = (-ax + up * 0.12).normalized()
    h0 = tsu - ax * 0.012; h1 = h0 + hilt_dir * 0.34
    parts.append(prim_cyl('Tsuka', h0, h1, 0.034, 0.03, n=8, col='black_l'))
    for k in range(5):     # diamond hilt wrap bumps
        c = h0.lerp(h1, 0.12 + 0.18 * k)
        parts.append(prim_cyl(f'Ito{k}', c - hilt_dir * 0.02, c + hilt_dir * 0.02, 0.039, n=4, col='leather'))
    parts.append(prim_cyl('Kashira', h1, h1 + hilt_dir * 0.035, 0.036, 0.026, n=8, col='gold'))
    # hanging cords (ashi) from the obi to the scabbard
    for f in (0.18, 0.42):
        c = F.lerp(Bk, f) + up * (0.05 * math.sin(PI * f))
        top, nt = project(ob, Vector((0, c.y, 2.15)), Vector((-1, 0, 0)))
        if top is None: continue
        mid = (top + c) / 2 + Vector((0.02, 0, 0))
        parts.append(tube_path(f'Ashi{f}', [top + nt * 0.005, mid, c + up * rs], 0.014, 'gold', n=5))
    for p in parts[1:]: kat.merge(p)
    kat.name = 'Katana'; kat.group = 'Extras'; kat.bone = 'LowerTorso'; kat.rigid = True
    P.append(kat)
    return P, pal
