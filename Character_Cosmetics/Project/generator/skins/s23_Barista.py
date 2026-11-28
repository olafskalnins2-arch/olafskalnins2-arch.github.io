from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03 (RF_SLIT_TOP), o04 helpers

NUM, NAME, RARITY, MAXD = '23', 'Barista', 'Common', 0.32


# ---------------------------------------------------------------- helpers (local to this skin)
def _ring_at(row, az, N):
    """point on a closed ring (ring index j <-> az = -pi + 2pi j/N) at a fractional azimuth"""
    f = (az + PI) / (2 * PI) * N
    j0 = int(math.floor(f)); t = f - j0
    return row[j0 % N].lerp(row[(j0 + 1) % N], t)


def _apron_hw(z):
    """half-angle (rad) of the apron at height z: wide skirt below the waist, tapered sides, narrow bib"""
    if z <= 2.28: return 1.28
    if z >= 2.56: return 0.50
    t = (z - 2.28) / 0.28; t = t * t * (3 - 2 * t)
    return 1.28 + (0.50 - 1.28) * t


def _apron(name, under, z_s, K=25, group='Top', th=0.02):
    """Front-only bib apron. Hung like a coat (torso_shell hang/over), then re-sampled as an open panel with clean
    curved edges. The skirt below z_s is split down the centre line (vertices duplicated in place) so each half
    hangs off its own thigh (rigfix panel rule), exactly like the wizard robe slits."""
    nseg = 48
    zs = [1.68, 1.77, 1.86, 1.95, 2.035, z_s, 2.2, 2.28, 2.35, 2.42, 2.49, 2.56, 2.65, 2.74, 2.83, 2.92, 3.02]
    full = torso_shell(name + 'Full', zs[0], 0.06, nseg=nseg, zs=zs, elevs=(), th=0,
                       extra=lambda z, a: 0.012 + 0.05 * max(0.0, 2.1 - z) * max(0.0, math.cos(a)),
                       hang=2.3, over=under, over_gap=0.035)
    M = len(zs)
    rows = [full.verts[i * nseg:(i + 1) * nseg] for i in range(M)]
    zmin, zmax = zs[0], zs[-1]
    pc = Piece(name, group)
    mid = (K - 1) // 2
    idx = []; idxL = {}; tag = []
    for i in range(M):
        hw = _apron_hw(zs[i]); r = []
        for j in range(K):
            az = -hw + 2 * hw * j / (K - 1)
            p = _ring_at(rows[i], az, nseg)
            h = Vector((math.sin(az), -math.cos(az), 0))
            r.append(pc.add_vert(p, h))
            cut = zs[i] < z_s - 1e-6
            tag.append(0 if not cut else (1 if j > mid else -1))
        idx.append(r)
        if zs[i] < z_s - 1e-6:            # duplicate the centre vertex: the copy belongs to the left panel
            p = pc.verts[r[mid]]
            idxL[i] = pc.add_vert(p.copy(), Vector((0, -1, 0))); tag.append(1)
    vv = [(z - zmin) / (zmax - zmin) for z in zs]
    for i in range(M - 1):
        for j in range(K - 1):
            a, b, c, d = idx[i][j], idx[i][j + 1], idx[i + 1][j + 1], idx[i + 1][j]
            if j >= mid:   # left half (+X): use the left copies on the centre column
                if j == mid:
                    a = idxL.get(i, a); d = idxL.get(i + 1, d)
            u0, u1 = j / (K - 1), (j + 1) / (K - 1)
            pc.add_face([a, b, c, d], [(u0, vv[i]), (u1, vv[i]), (u1, vv[i + 1]), (u0, vv[i + 1])], None)
    orient_by_hint(pc)
    pc.meta.update(rows=M, N=K, zmin=zmin, zmax=zmax, circ=1.0, kind='apron')
    thicken(pc, th)
    pc.meta['panel'] = tag + tag
    pc.meta['slit_top'] = z_s
    pc.region = 'torso'; pc.skirt = True
    return pc


def _tag_panel(pc, z_s):
    """make a patch on the apron skirt deform like the apron panel under it (same slit rule, same side)"""
    pc.meta['panel'] = [0 if p.z >= z_s - 1e-6 else (1 if p.x > 0 else -1) for p in pc.verts]
    pc.meta['slit_top'] = z_s
    pc.skirt = True; pc.region = 'torso'
    return pc


def _ribbon(name, pts, nrm, w, col, th, group='Extras'):
    rows = []; hints = []; n = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        s = t.cross(nrm[i]).normalized()
        rows.append([p - s * (w / 2), p + s * (w / 2)]); hints.append([nrm[i], nrm[i]])
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group)
    thicken(pc, th)
    return pc


def _snap(bv, pts, lift, center):
    out = []; nn = []
    for p in pts:
        loc, nor, fi, d = bv.find_nearest(p)
        if nor.dot(loc - center) < 0: nor = -nor
        out.append(loc + nor * lift); nn.append(nor)
    return out, nn


def _stitch(img, dist, along, col, px, gap=0.022, dash=0.03, alpha=0.9):
    """dashed stitch line where dist == gap (dist, along in units, px = pixels per unit)"""
    on = (np.mod(along / dash, 1.0) < 0.62).astype(float)
    return mix(img, aa(np.abs(dist - gap) * px - 0.9) * on * alpha, col)


# ---------------------------------------------------------------- the skin
def build():
    pal = {'black': '#202024', 'black_d': '#151518', 'black_l': '#2e2e34', 'jeans': '#2b3a55', 'jeans_d': '#1f2a3f',
           'jeans_l': '#3a4c6c', 'stitch_j': '#c99a4e', 'apron': '#b98b5e', 'apron_d': '#9a7048', 'apron_l': '#c99d72',
           'cream': '#efe3cc', 'thread': '#ead6b0', 'bean': '#4a2c17', 'leather': '#5e3a1f', 'leather_d': '#3f2612',
           'silver': '#c3c6ca', 'white': '#efefef', 'white_d': '#d6d6d6', 'sole': '#e2e2e2', 'grey': '#9aa0a6',
           'pen': '#f4f4f4', 'pen_cap': '#1b1b1f'}
    P = []
    z_s = RF_SLIT_TOP()

    # ---- dark jeans (built first: everything hangs over them)
    pt = pants('Jeans', 2.2, 0.52, 0.04, hip_off=0.06, leg_extra=lambda z, a: 0.018 + 0.012 * max(0, 1.3 - z), nseg=16)
    def jpaint(U, V, m):
        img = P_solid(pal['jeans'])(U, V, m)
        z, az = zc(U, V, m); x, _ = phys(U, V, m)
        tw = 0.5 + 0.5 * np.sin((x + z) * 2 * PI / 0.018)                 # denim twill
        img = mix(img, (tw > 0.75) * 0.22, pal['jeans_l'])
        img = mix(img, (tw < 0.2) * 0.18, pal['jeans_d'])
        if m.get('kind') == 'leg':
            for c in (PI / 2, -PI / 2):                                    # out-seam / in-seam with gold top-stitch
                img = mix(img, aa((np.abs(az - c) - 0.012) * 300) * 0.8, pal['jeans_d'])
                img = _stitch(img, np.abs(az - c) * 0.18, z, pal['stitch_j'], 700, gap=0.007, dash=0.025, alpha=0.8)
            img = mix(img, aa((z - (m['zmin'] + 0.05)) * 500) * 0.5, pal['jeans_d'])    # hem
            img = _stitch(img, z - m['zmin'], x, pal['stitch_j'], 700, gap=0.04, dash=0.025, alpha=0.8)
            # knee fade
            img = mix(img, np.clip(1 - np.abs(z - 1.1) / 0.14, 0, 1) * np.clip(np.cos(az), 0, 1) * 0.25, pal['jeans_l'])
        else:
            img = mix(img, aa(np.abs(z - 2.13) * 500 - 1) * 0.8, pal['jeans_d'])          # waistband seam
            img = _stitch(img, np.abs(az) * 0.4, z, pal['stitch_j'], 700, gap=0.04, dash=0.025, alpha=0.8 * (z > 2.0))  # fly
        return img
    for p in pt: p.paint = jpaint
    P += pt
    for s in 'LR':                                                          # rolled cuffs
        cf = leg_tube('JeansCuff_' + s, s, 0.72, 0.60, 0.10, nseg=16, nrows=3, th=0.02,
                      extra=lambda z, a: 0.006 * math.sin((z - 0.6) / 0.12 * PI))
        def cpaint(U, V, m):
            img = P_solid(pal['jeans_l'])(U, V, m); z, az = zc(U, V, m); x, _ = phys(U, V, m)
            img = mix(img, aa(np.abs(V - 0.5) * 120 - 1) * 0.5, pal['jeans'])
            return _stitch(img, np.abs(V - 0.85) * 0.12, x, pal['stitch_j'], 700, gap=0.0, dash=0.025, alpha=0.8)
        cf.paint = cpaint; cf.rect_key = 'JeansCuff'; P.append(cf)

    # ---- black long-sleeve tee, untucked: hangs over the jeans
    tee = torso_shell('Tee', 2.0, 0.03, nseg=32, extra=lambda z, a: 0.01 + 0.02 * max(0, 2.25 - z), th=0.018, hang=2.3, over=pt)
    def tpaint(U, V, m):
        img = P_solid(pal['black'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.7, pal['black_l'])    # side seams
        img = mix(img, aa((z - (m['zmin'] + 0.045)) * 500) * 0.8, pal['black_d'])                # hem band
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.045)) * 500 - 0.8) * 0.8, pal['black_l'])
        return img
    tee.paint = tpaint; P.append(tee)
    P.append(collar('Neckband', 'stand', h=0.035, flare=0.012, col='black_d', th=0.015))
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.64, 0.04, extra=lambda t, a: 0.012 + 0.012 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa((np.abs(U - 0.5) - 0.004) * 300) * 0.5, pal['black_l'])
        P.append(sl)
        # pushed-up sleeve: scrunched rolls just below the elbow
        pu = sleeve('SleevePush_' + s, s, 0.57, 0.71, 0.06, nrows=7, cap=False, th=0.02,
                    extra=lambda t, a: 0.012 + 0.014 * abs(math.sin((t - 0.57) / 0.14 * 2.5 * PI)))
        def ppaint(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            img = mix(img, (0.5 - 0.5 * np.cos(V * 5 * PI)) * 0.55, pal['black_l'])
            return mix(img, aa(np.abs(V - 0.2) * 200 - 1) * 0.6, pal['black_d'])
        pu.paint = ppaint; P.append(pu)

    # ---- apron ties: from the apron sides around the back (under the apron edges), bow at the back
    tie = band('ApronTie', 2.215, 2.275, 0.012, th=0.015, bvh=piece_bvh(tee), keep=lambda i, j, zc_, az: abs(az) > 1.12, group='Extras')
    tie.paint = lambda U, V, m: mix(P_solid(pal['apron'])(U, V, m), aa(np.minimum(V - 0.15, 0.85 - V) * -150) * 0.6, pal['apron_d'])
    P.append(tie)

    # ---- tan canvas bib apron
    ap = _apron('Apron', pt + [tee, tie], z_s)
    def apaint(U, V, m):
        img = P_solid(pal['apron'])(U, V, m)
        z = m['zmin'] + V * (m['zmax'] - m['zmin'])
        hwv = np.vectorize(_apron_hw)(z)
        width = 2 * hwv * 0.47
        x = (U - 0.5) * width
        tex = (np.sin(x * 2 * PI / 0.011) + np.sin(z * 2 * PI / 0.011))          # canvas weave
        img = mix(img, (tex > 1.3) * 0.16, pal['apron_d'])
        img = mix(img, (tex < -1.4) * 0.12, pal['apron_l'])
        side = np.minimum(U, 1 - U) * width
        img = mix(img, aa((side - 0.012) * 600) * 0.6, pal['apron_d'])                   # rolled side hem
        img = _stitch(img, side, z, pal['thread'], 650, gap=0.024)
        img = mix(img, aa((z - (m['zmin'] + 0.045)) * 600) * 0.55, pal['apron_d'])      # bottom hem
        img = _stitch(img, z - m['zmin'], x, pal['thread'], 650, gap=0.03)
        img = mix(img, aa((m['zmax'] - 0.04 - z) * 600) * 0.55, pal['apron_d'])         # bib top hem
        img = _stitch(img, m['zmax'] - z, x, pal['thread'], 650, gap=0.028)
        img = mix(img, aa(np.abs(z - 2.29) * 600 - 1.2) * 0.7, pal['apron_d'])          # waist seam
        img = _stitch(img, np.abs(z - 2.29), x, pal['thread'], 650, gap=0.014, alpha=0.7)
        return img
    ap.paint = apaint; ap.meta['rect'] = (512, 512); P.append(ap)
    ab = piece_bvh(ap)

    # bib pocket with the coffee-bean logo
    def bibpk(s, t): return Vector((-0.15 + s * 0.30, 0, 2.47 + t * 0.25))
    bp = surface_patch('BibPocket', ab, bibpk, Vector((0, 1, 0)), 0.012, 7, 6, th=0.012)
    def bppaint(U, V, m):
        img = P_solid(pal['apron_l'])(U, V, m)
        x = (U - 0.5) * 0.30; y = (V - 0.5) * 0.25; px = 800
        tex = np.sin(x * 2 * PI / 0.011) + np.sin(y * 2 * PI / 0.011)
        img = mix(img, (tex > 1.3) * 0.14, pal['apron'])
        edge = np.minimum(np.minimum(U * 0.30, (1 - U) * 0.30), (V * 0.25))
        img = _stitch(img, edge, x + y, pal['thread'], px, gap=0.016, dash=0.024)
        img = mix(img, aa(((1 - V) * 0.25 - 0.03) * px) * 0.6, pal['apron'])          # folded top hem
        img = _stitch(img, (1 - V) * 0.25, x, pal['thread'], px, gap=0.04, dash=0.024)
        # badge + coffee bean
        cx, cy = 0.0, -0.01
        r = np.hypot(x - cx, y - cy)
        img = mix(img, aa((r - 0.072) * px), pal['bean'])
        img = mix(img, aa((r - 0.062) * px), pal['cream'])
        ang = math.radians(35); ca, sa = math.cos(ang), math.sin(ang)
        bx = (x - cx) * ca + (y - cy) * sa; by = -(x - cx) * sa + (y - cy) * ca
        e = np.hypot(bx / 0.038, by / 0.027)
        img = mix(img, aa((e - 1) * 0.027 * px), pal['bean'])
        crease = by - 0.007 * np.sin(bx / 0.038 * PI)
        img = mix(img, aa((np.abs(crease) - 0.0035) * px) * (e < 0.82), pal['cream'])
        return img
    bp.paint = bppaint; bp.meta['rect'] = (240, 200); P.append(bp)

    # waist pockets, one per skirt panel (deform with their panel)
    for sg in (-1, 1):
        def wpk(s, t, sg=sg): return Vector((sg * (0.06 + s * 0.27), 0, 1.86 + t * 0.2))
        wp = surface_patch(f'WaistPocket{sg}', ab, wpk, Vector((0, 1, 0)), 0.01, 7, 5, th=0.012)
        def wppaint(U, V, m):
            img = P_solid(pal['apron_l'])(U, V, m)
            x = U * 0.27; y = V * 0.2; px = 800
            tex = np.sin(x * 2 * PI / 0.011) + np.sin(y * 2 * PI / 0.011)
            img = mix(img, (tex > 1.3) * 0.14, pal['apron'])
            edge = np.minimum(np.minimum(x, 0.27 - x), y)
            img = _stitch(img, edge, x + y, pal['thread'], px, gap=0.016, dash=0.024)
            img = mix(img, aa(((0.2 - y) - 0.03) * px) * 0.6, pal['apron'])
            img = _stitch(img, 0.2 - y, x, pal['thread'], px, gap=0.04, dash=0.024)
            img = _stitch(img, np.abs(x - 0.135), y, pal['thread'], px, gap=0.0, dash=0.024, alpha=0.8 * (y < 0.16))  # divider
            return img
        wp.paint = wppaint; wp.meta['rect'] = (220, 160); wp.rect_key = 'WaistPocket'
        _tag_panel(wp, z_s); P.append(wp)

    # small towel tucked into the right waist pocket, hanging over its front
    def twl(s, t): return Vector((-0.30 + s * 0.17, 0, 1.74 + t * 0.37))
    tw = surface_patch('Towel', ab, twl, Vector((0, 1, 0)), 0.03, 5, 7, th=0.016)
    def twpaint(U, V, m):
        img = P_solid(pal['white'])(U, V, m)
        x = U * 0.17; y = V * 0.37
        waf = (np.abs(np.mod(x / 0.016, 1) - 0.5) < 0.12) | (np.abs(np.mod(y / 0.016, 1) - 0.5) < 0.12)
        img = mix(img, waf * 0.25, pal['white_d'])
        for c in (0.06, 0.09):
            img = mix(img, aa((np.abs(y - c) - 0.008) * 700), pal['jeans'])
        img = mix(img, aa((y - 0.015) * 700) * (np.mod(x / 0.012, 1) < 0.5), pal['white_d'])   # fringe
        return img
    tw.paint = twpaint; tw.meta['rect'] = (96, 200); _tag_panel(tw, z_s); P.append(tw)
    def twf(s, t): return Vector((-0.305 + s * 0.18, 0, 2.06 + t * 0.08))
    tf = surface_patch('TowelFold', ab, twf, Vector((0, 1, 0)), 0.055, 5, 3, th=0.024, col='white')
    _tag_panel(tf, z_s); P.append(tf)

    # pen tucked in the bib pocket (wearer's left)
    lo, nlo = project(ab, Vector((0.095, 0, 2.62)), Vector((0, 1, 0)))
    hi, nhi = project(ab, Vector((0.095, 0, 2.80)), Vector((0, 1, 0)))
    p0 = lo + nlo * 0.024; p1 = hi + nhi * 0.024
    P.append(prim_cyl('PenBody', p0, p0.lerp(p1, 0.55), 0.016, n=8, col='pen'))
    P.append(prim_cyl('PenCap', p0.lerp(p1, 0.55), p1, 0.018, n=8, col='pen_cap'))
    P.append(prim_cone('PenTip', p1, p1 + (p1 - p0).normalized() * 0.03, 0.018, 'pen_cap', n=8))
    cl = p0.lerp(p1, 0.62) + nhi * 0.02
    P.append(prim_box('PenClip', cl + Vector((0, 0, -0.04)), (0.012, 0.008, 0.11), 'silver'))
    for q in P[-4:]: q.bone = 'UpperTorso'

    # ---- leather neck strap: from the bib corners up over the shoulders and round the back of the neck
    nb = P[[q.name for q in P].index('Neckband')]
    sb = piece_bvh(tee, nb, ap)
    G = [((0.17, 0, 2.95), (0, 1, 0)), ((0.19, 0, 3.07), (0, 1, 0)), ((0.24, -0.24, 3.15), (0, 0.6, -0.8)),
         ((0.31, -0.06, 3.15), (0, 0, -1)), ((0.31, 0.10, 3.15), (0, 0, -1)), ((0.24, 0.22, 3.1), (0, -0.6, -0.8)),
         ((0.12, 0, 3.04), (0, -1, 0)), ((0.0, 0, 3.02), (0, -1, 0))]
    G = G + [((-p[0], p[1], p[2]), d) for p, d in reversed(G[:-1])]
    guide = []
    for p, d in G:
        d = Vector(d).normalized(); loc, n = project(sb, Vector(p), d)
        guide.append(loc if loc is not None else Vector(p))
    path = smooth_line(polyline_resample(guide, 44), 3)
    path, nrm = _snap(sb, path, 0.022, Vector((0, 0.02, 2.7)))
    strap = _ribbon('NeckStrap', path, nrm, 0.065, None, 0.014)
    def stpaint(U, V, m):
        img = P_solid(pal['leather'])(U, V, m)
        img = mix(img, aa((np.minimum(U, 1 - U) - 0.12) * 60) * 0.5, pal['leather_d'])
        return img
    strap.paint = stpaint; strap.meta['rect'] = (32, 256)
    head_clear(strap, 0.04); strap.bone = 'UpperTorso'; P.append(strap)
    for k, (q, n) in enumerate(((path[0], nrm[0]), (path[-1], nrm[-1]))):          # rivets / grommets on the bib corners
        P.append(prim_cyl(f'Grommet{k}', q, q + n * 0.02, 0.032, n=10, col='silver'))
        P[-1].bone = 'UpperTorso'
    # adjuster buckle on the wearer's left strap
    bi = 7
    t = (path[bi + 1] - path[bi - 1]).normalized(); n = nrm[bi]; s = t.cross(n).normalized()
    R = Matrix((s, t, n)).transposed()
    P.append(prim_box('StrapBuckle', path[bi] + n * 0.012, (0.085, 0.05, 0.018), 'silver', rot=R))
    P[-1].bone = 'UpperTorso'

    # ---- bow at the back of the apron ties
    tb = piece_bvh(tie)
    loc, n = project(tb, Vector((0, 0, 2.245)), Vector((0, -1, 0)))
    P.append(prim_rbox('BowKnot', loc + n * 0.028, (0.075, 0.05, 0.065), 'apron_d'))
    for sg in (-1, 1):
        P.append(prim_sphere(f'BowLoop{sg}', loc + n * 0.03 + Vector((sg * 0.085, 0, 0.01)), 0.05, 'apron', nl=5, seg=10,
                             scale=(1.45, 0.42, 0.75)))
    tl_b = piece_bvh(tee, tie, *pt)
    for sg in (-1, 1):
        g = [Vector((sg * (0.02 + 0.06 * k / 5), 0.5, 2.22 - 0.2 * k / 5)) for k in range(6)]
        g, nn = _snap(tl_b, [project(tl_b, q, Vector((0, -1, 0)))[0] for q in g], 0.026, Vector((0, 0, 2.2)))
        P.append(_ribbon(f'BowTail{sg}', g, nn, 0.05, 'apron', 0.012))
    for q in P[-5:]: q.bone = 'LowerTorso'

    # ---- white sneakers
    for s in 'LR':
        sh = shoe('Sneaker_' + s, s, off=0.045, bulk=0.035, toe=0.05, sole_h=0.07, open_elev=44)
        def snk(U, V, m):
            img = P_solid(pal['white'])(U, V, m); z, az = zc(U, V, m)
            st = m['sole_top']
            img = mix(img, aa((z - st) * 600), pal['sole'])                               # sole
            img = mix(img, aa(np.abs(z - (st - 0.035)) * 600 - 1), pal['grey'])            # sole groove
            img = mix(img, aa(np.abs(z - st) * 600 - 0.8), pal['white_d'])
            img = mix(img, aa(np.abs(z - (st + 0.06)) * 600 - 0.8) * (np.cos(az) > 0.55), pal['white_d'])   # toe cap seam
            lace = (np.abs(az) < 0.32) & (z > st + 0.1)
            img = mix(img, lace * aa(np.abs(np.mod(z / 0.035, 1) - 0.5) * 30 - 6), pal['white_d'])   # laces
            img = mix(img, aa((np.abs(np.abs(az) - 0.36) - 0.01) * 300) * (z > st + 0.1), pal['grey'])  # eyelet rows
            img = mix(img, aa((np.abs(az) - (PI - 0.25)) * -300) * (z > st + 0.06), pal['jeans'])  # heel tab
            return img
        sh.paint = snk; P.append(sh)
    return P, pal
