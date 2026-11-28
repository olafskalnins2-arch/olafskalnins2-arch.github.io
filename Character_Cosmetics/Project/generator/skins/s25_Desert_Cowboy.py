from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '25', 'Desert_Cowboy', 'Rare', 0.32


def _vest_open(z):
    """half-angle (rad) of the vest's open front at height z"""
    return 0.2 + 0.4 * min(1.0, max(0.0, (z - 2.5) / 0.55))


def _noise(x, z, a=37.0, b=23.0, c=41.0, d=13.0):
    return 0.5 + 0.5 * np.sin(x * a + np.sin(z * b) * 2.0) * np.sin(z * c + x * d)


def _chap(name, side, bvh, z0, z1, off, a0, a1, ncol=15, nrows=13, group='Bottom', th=0.02):
    """Open leather chap: a partial leg tube (front + outer side only, open at the back / inner thigh), cast onto the
    jeans leg so it sits a fixed distance outside it. Weighted exactly like the trouser leg under it."""
    azs = list(np.linspace(a0, a1, ncol))
    D = [Vector((math.sin(a), -math.cos(a), 0)) for a in azs]
    zs = list(np.linspace(z0, z1, nrows))
    rows = []
    for z in zs:
        c = leg_point(side, z)
        ex = lambda j, p, z=z: 0.012 * max(0.0, 1.15 - z)
        rows.append(ray_ring(bvh, c, D, off, R=0.8, extra=ex, smooth=0))
    vv = [(z - z1) / (z0 - z1) for z in zs]
    pc = _grid_with_ij(name, rows, False, vv, [D] * len(rows), group)
    mid = rows[len(rows) // 2]
    pc.meta.update(kind='chap', zmin=z1, zmax=z0, circ=sum((mid[k] - mid[k - 1]).length for k in range(1, len(mid))), side=side)
    pc.meta.update(w_axis=W_AXIS, w_xmin=W_XMIN)
    if th: thicken(pc, th)
    pc.region = 'leg_' + side
    pc.rect_key = 'Chaps'
    return pc, rows


def _chap_fringe(name, side, edge, a_out, group='Bottom'):
    """Short leather strands along the chap's outer seam, angled outward / backward and drooping."""
    pc = Piece(name, group)
    d = Vector((math.sin(a_out), -math.cos(a_out), 0))
    for k in range(len(edge) - 1):
        for h in (0.0, 0.5):
            p = edge[k].lerp(edge[k + 1], h)
            q = edge[k].lerp(edge[k + 1], h + 0.32)
            o = d * 0.085 + Vector((0, 0, -0.03))
            ids = [pc.add_vert(p - d * 0.01), pc.add_vert(p + o), pc.add_vert(q + o), pc.add_vert(q - d * 0.01)]
            t = (q - p).cross(d)
            for i in ids: pc.hint[i] = t
            pc.add_face(ids, None, 'chap_l')
    orient_by_hint(pc)
    thicken(pc, 0.008)
    pc.region = 'leg_' + side
    pc.meta.update(w_axis=W_AXIS, w_xmin=W_XMIN)
    return pc


def _oval_disc(name, center, rx, rz, depth, col, n=20, group='Extras'):
    pc = prim_cyl(name, center, center + Vector((0, -depth, 0)), 1.0, n=n, col=col, group=group)
    s = rx
    pc.verts = [Vector((center.x + (p.x - center.x) * rx, p.y, center.z + (p.z - center.z) * rz)) for p in pc.verts]
    return pc


def build():
    pal = {'cream': '#efe3c8', 'cream_d': '#d9caa8', 'jeans': '#3d5a8a', 'jeans_l': '#5574a6', 'jeans_d': '#2c446d',
           'stitch': '#d9a24a', 'vest': '#8a5a34', 'vest_d': '#5e3b20', 'vest_l': '#a1704a', 'lace': '#d1ad79',
           'boot': '#7a4a25', 'boot_d': '#4a2b14', 'boot_st': '#d4a466', 'sole': '#2e1c10',
           'red': '#c94a3a', 'red_d': '#8f2c22', 'white': '#f6efe2', 'gold': '#d9b44a', 'gold_d': '#a07f24', 'gold_l': '#f0d47a',
           'silver': '#c3c7cc', 'silver_d': '#8d939b', 'chap': '#6a4225', 'chap_d': '#46291466'[:7], 'chap_l': '#8a5a34',
           'belt': '#4a2c16', 'belt_d': '#2e1a0c', 'rope': '#c9a66b', 'rope_d': '#9c7c46', 'pearl': '#f4efe6'}
    P = []

    # ---------- jeans (built first: everything else hangs over them) ----------
    pt = pants('Jeans', 2.22, 0.55, 0.04, hip_off=0.06, leg_extra=lambda z, a: 0.02 + 0.07 * max(0.0, 0.95 - z) / 0.4)

    def jpaint(U, V, m):
        img = P_solid(pal['jeans'])(U, V, m)
        z, az = zc(U, V, m)
        x = U * m.get('circ', 1.0)
        img = mix(img, 0.13 * (0.5 + 0.5 * np.sin((x + z) * 260)), pal['jeans_l'])          # twill
        img = mix(img, 0.10 * _noise(x * 3, z * 3), pal['jeans_d'])
        dash = (np.sin(z * 260) > -0.2).astype(float)
        if m.get('kind') == 'hip':
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 400) * dash, pal['stitch'])     # side seams
            fly = (np.abs(az - 0.1) < 0.006 + 0.0) | ((np.abs(az - 0.03) < 0.075) & (np.abs(z - 2.0) < 0.006))
            img = mix(img, fly.astype(float) * (z < 2.12) * dash, pal['stitch'])
            yk = 2.08 - 0.08 * (PI - np.abs(az)) / 1.2
            img = mix(img, aa((np.abs(z - yk) - 0.006) * 500) * (np.abs(az) > PI - 1.2) * dash, pal['stitch'])   # back yoke
            for sg in (-1, 1):   # back pocket tops
                c = sg * (PI - 0.55)
                img = mix(img, aa((np.abs(z - 1.99) - 0.005) * 500) * (np.abs(az - c) < 0.28), pal['stitch'])
        else:
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.007) * 400) * dash, pal['stitch'])     # leg seams
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.035)) * 500 - 2) * dash, pal['stitch'])     # hem stitch
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.01)) * 500 - 4), pal['jeans_d'])
        return img
    for p in pt: p.paint = jpaint
    P += pt

    # belt on the jeans hip + big oval gold buckle
    belt = band('Belt', 2.08, 2.21, 0.012, th=0.02, bvh=piece_bvh(pt[0]), group='Bottom')
    def bpaint(U, V, m):
        img = P_solid(pal['belt'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa(np.minimum(V - 0.1, 0.9 - V) * -200), pal['belt_d'])
        dash = (np.sin(U * 900) > 0).astype(float)
        img = mix(img, aa(np.abs(V - 0.2) * 300 - 1) * dash, pal['stitch'])
        img = mix(img, aa(np.abs(V - 0.8) * 300 - 1) * dash, pal['stitch'])
        return img
    belt.paint = bpaint; P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.145)), Vector((0, 1, 0)))
    bc = loc + Vector((0, -0.004, 0))
    buckle = [
        _oval_disc('Buckle', bc, 0.12, 0.088, 0.026, 'gold'),
        _oval_disc('BuckleInlay', bc + Vector((0, -0.024, 0)), 0.078, 0.052, 0.012, 'silver'),
    ]
    rim = [bc + Vector((math.cos(a) * 0.108, -0.03, math.sin(a) * 0.077)) for a in np.linspace(0, 2 * PI, 25)]
    buckle.append(tube_path('BuckleRope', rim, 0.009, 'gold_l', n=5, caps=False))
    # a little gold star on the silver inlay
    st = Piece('BuckleStar', 'Extras'); sc = bc + Vector((0, -0.037, 0))
    ring = [sc + Vector((math.cos(PI / 2 + k * PI / 5) * (0.038 if k % 2 == 0 else 0.016), 0, math.sin(PI / 2 + k * PI / 5) * (0.038 if k % 2 == 0 else 0.016))) for k in range(10)]
    ids = [st.add_vert(p, Vector((0, -1, 0))) for p in ring]; ci = st.add_vert(sc + Vector((0, -0.004, 0)), Vector((0, -1, 0)))
    for k in range(10): st.add_face([ids[k], ids[(k + 1) % 10], ci], None, 'gold')
    orient_by_hint(st); thicken(st, 0.006); st.rigid = True; buckle.append(st)
    for q in buckle: q.bone = 'LowerTorso'
    P += buckle

    # ---------- chaps over the jeans fronts ----------
    chaps = []
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        leg = pt[1] if s == 'L' else pt[2]
        jb = piece_bvh(pt[0], leg)
        a0, a1 = (-0.45, 1.85) if s == 'L' else (-1.85, 0.45)
        ch, rows = _chap('Chap_' + s, s, jb, 1.86, 0.76, 0.028, a0, a1)
        def cpaint(U, V, m):
            img = P_solid(pal['chap'])(U, V, m)
            z, az = zc(U, V, m)
            x = U * m.get('circ', 1.0)
            img = mix(img, 0.22 * _noise(x * 2.3, z * 2.1, 29, 17, 31, 11), '#5a3720')
            edge = np.minimum(U, 1 - U) * m.get('circ', 1.0)
            img = mix(img, aa((edge - 0.035) * 800), pal['chap_l'])                     # leather border
            img = mix(img, aa(np.abs(edge - 0.048) * 900 - 1) * (np.sin(z * 220) > 0), pal['lace'])   # stitching
            img = mix(img, aa((z - (m['zmax'] - 0.06)) * -600), pal['chap_l'])          # top band
            img = mix(img, aa(np.abs(z - (m['zmax'] - 0.075)) * 900 - 1) * (np.sin(x * 220) > 0), pal['lace'])
            return img
        ch.paint = cpaint
        P.append(ch); chaps.append(ch)
        edge = [r[-1] if s == 'L' else r[0] for r in rows[1:-1]]
        P.append(_chap_fringe('ChapFringe_' + s, s, edge, (a1 + 0.45) if s == 'L' else (a0 - 0.45)))
        # silver concho at the top of each chap (rigid, on the thigh)
        cb = piece_bvh(ch)
        az = 1.0 * sg
        d = Vector((math.sin(az), -math.cos(az), 0))
        lc = leg_point(s, 1.74)
        loc, nn = project(cb, lc + d * 0.8, -d)
        cn = prim_cyl('Concho_' + s, loc + nn * 0.004, loc + nn * 0.022, 0.045, n=10, col='silver', group='Bottom')
        cn.bone = ('Left' if s == 'L' else 'Right') + 'UpperLeg'; P.append(cn)

    # ---------- cream shirt (tucked into the jeans) ----------
    shirt = torso_shell('Shirt', 2.08, 0.035, nseg=32, th=0.015)
    def spaint(U, V, m):
        img = P_solid(pal['cream'])(U, V, m)
        z, az = zc(U, V, m)
        x = U * m.get('circ', 1.0)
        img = mix(img, 0.35 * aa(np.abs(np.sin(x * 40)) * 30 - 2), pal['cream_d'])   # faint pinstripe check
        img = mix(img, 0.25 * aa(np.abs(np.sin(z * 40)) * 30 - 2), pal['cream_d'])
        img = mix(img, aa((np.abs(az) - 0.035) * 400) * aa((0.025 - np.abs(az)) * -400) * 0, pal['cream_d'])
        img = mix(img, aa(np.abs(np.abs(az) - 0.04) * 500 - 1), pal['cream_d'])           # placket
        return img
    shirt.paint = spaint; P.append(shirt)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.9, 0.04, nseg=12, nrows=10, extra=lambda t, a: 0.01 + 0.012 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['cream'])(U, V, m), 0.3 * aa(np.abs(np.sin(U * 60)) * 30 - 2), pal['cream_d'])
        P.append(sl)
        P.append(sleeve('Cuff_' + s, s, 0.84, 0.97, 0.058, nseg=12, nrows=3, cap=False, col='cream', th=0.015))
    sb = piece_bvh(shirt)
    for i, z in enumerate((2.66, 2.48, 2.31)):
        loc, n = project(sb, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Snap{i}', loc, loc + n * 0.018, 0.027, n=8, col='pearl', group='Top'))

    # ---------- suede vest with fringe (hangs over shirt, jeans and belt) ----------
    nseg = 48
    WC = 4 * PI / nseg                                   # opening cut on a constant column, then warped to _vest_open(z)
    def vkeep(ij, f):
        j = ij[1]; az = azb(j + 0.5, nseg)
        zc_ = sum(vest.verts[i].z for i in f) / len(f)
        if abs(az) < WC: return False
        if zc_ < 2.24:                                   # fringe strands on the front panels only
            return j % 2 == 0 and 0.34 < abs(az) < 1.38
        return True
    zs = [2.04, 2.14, 2.24] + list(np.linspace(2.33, 2.95, 8))
    vest = torso_shell('Vest', 2.04, 0.07, nseg=nseg, zs=zs, extra=lambda z, a: 0.008, th=0, hang=2.3,
                       over=pt + [belt, shirt])
    full = piece_bvh(vest)
    for i, p in enumerate(vest.verts):                   # smooth azimuthal warp: straight-cut edge -> curved V opening
        az = math.atan2(p.x, -p.y); a = abs(az); sgn = 1 if az >= 0 else -1; w = _vest_open(p.z)
        a2 = w + (a - WC) * (PI - w) / (PI - WC) if a >= WC else a * w / WC
        d = Vector((math.sin(sgn * a2), -math.cos(sgn * a2), 0))
        h = full.ray_cast(Vector((0, 0, p.z)) + d * 2.0, -d, 2.0)
        vest.verts[i] = h[0] if h[0] is not None else Matrix.Rotation(-(sgn * a2 - az), 3, 'Z') @ p
    filter_faces(vest, vkeep)
    thicken(vest, 0.022)
    def vpaint(U, V, m):
        img = P_solid(pal['vest'])(U, V, m)
        z, az = zc(U, V, m)
        x = U * m.get('circ', 1.0)
        img = mix(img, 0.22 * _noise(x * 2, z * 2), pal['vest_d'])                    # suede mottling
        img = mix(img, 0.12 * _noise(x * 5, z * 5, 19, 7, 23, 5), pal['vest_l'])
        e = np.abs(az) - WC                                                            # (unwarped) distance from the edge
        img = mix(img, aa((e - 0.05) * 500) * (z > 2.24), pal['vest_d'])              # front binding
        img = mix(img, aa(np.abs(e - 0.075) * 600 - 1) * (np.sin(z * 160) > 0) * (z > 2.27), pal['lace'])
        img = mix(img, aa(np.abs(z - 2.265) * 500 - 6), pal['vest_d'])                 # hem binding
        img = mix(img, aa((z - 2.24) * 500), pal['vest_l'])                            # fringe strands
        # western yoke (back) and pocket welts (front)
        yk = 2.78 + 0.16 * np.clip((PI - np.abs(az)) / 0.9, 0, 1)
        img = mix(img, aa((yk - z) * 500) * (np.abs(az) > PI - 1.15) * 0.55, pal['vest_l'])
        img = mix(img, aa(np.abs(z - yk) * 600 - 1) * (np.abs(az) > PI - 1.15) * (np.sin(np.abs(az) * 160) > 0), pal['lace'])
        img = mix(img, aa(np.abs(z - 2.44) * 500 - 2.5) * (np.abs(np.abs(az) - 0.78) < 0.2), pal['vest_d'])
        img = mix(img, aa(np.abs(z - 2.76) * 500 - 2.5) * (np.abs(np.abs(az) - 0.72) < 0.12), pal['vest_d'])
        return img
    vest.paint = vpaint; P.append(vest)

    # ---------- red bandana: neck roll + front triangle + knot at the back ----------
    bn = collar('Bandana', 'stand', h=0.08, flare=0.07, col=None)
    def bandpaint(U, V, m):
        img = P_solid(pal['red'])(U, V, m)
        gx, gy = (U * 36) % 1 - 0.5, (V * 3 + 0.5 * (np.floor(U * 36) % 2)) % 1 - 0.5
        img = mix(img, aa((np.hypot(gx * 1.0, gy * 2.2) - 0.18) * 30), pal['white'])
        return img
    bn.paint = bandpaint; P.append(bn)
    def tri(s, t):
        w = 0.2 * (1 - t) + 0.012
        return Vector(((s - 0.5) * 2 * w, 0, 3.16 - t * 0.36))
    tr = surface_patch('BandanaTri', sb, tri, Vector((0, 1, 0)), 0.02, 5, 7, th=0.012)
    def tripaint(U, V, m):
        img = P_solid(pal['red'])(U, V, m)
        gx, gy = (U * 9) % 1 - 0.5, (V * 7 + 0.5 * (np.floor(U * 9) % 2)) % 1 - 0.5
        img = mix(img, aa((np.hypot(gx, gy * 1.3) - 0.2) * 40), pal['white'])
        img = mix(img, aa((np.hypot(gx, gy * 1.3) - 0.09) * 40), pal['red_d'])
        e = np.minimum(np.minimum(U, 1 - U), 1 - V) if False else np.minimum(U, 1 - U)
        img = mix(img, aa((e - 0.07) * 200), pal['white'])                            # white border
        img = mix(img, aa((e - 0.035) * 200), pal['red_d'])
        return img
    tr.paint = tripaint; tr.meta['rect'] = (128, 128); head_clear(tr, 0.03); P.append(tr)
    tb = piece_bvh(shirt, bn)
    loc, n = project(tb, Vector((0, 0, 3.2)), Vector((0, -1, 0)))
    kc = loc + n * 0.05
    knot = [prim_rbox('BandanaKnot', kc, (0.12, 0.08, 0.09), 'red_d', group='Top')]
    for sg in (-1, 1):
        pts = [kc + Vector((sg * 0.03, 0.02, -0.02)), kc + Vector((sg * 0.07, 0.035, -0.09)), kc + Vector((sg * 0.09, 0.04, -0.17))]
        knot.append(tube_path(f'BandanaTail{sg}', pts, 0.03, 'red', n=6, group='Top', rfn=lambda t: 0.035 * (1 - 0.5 * t)))
    for q in knot:
        head_clear(q, 0.03); body_clear(q, 0.02); q.rigid = True; q.bone = 'UpperTorso'
    P += knot

    # ---------- coiled lasso hanging on the belt (right hip, toward the back) ----------
    azl = -2.0
    dl = Vector((math.sin(azl), -math.cos(azl), 0)); tl = Vector((math.cos(azl), math.sin(azl), 0))
    S = piece_bvh(pt[0], pt[2], belt, chaps[1], vest)
    zc0, R0 = 2.0, 0.14
    need = 0.0
    for k in range(24):
        a = 2 * PI * k / 24
        for rr in (R0 + 0.04, R0, R0 * 0.5, 0.0):
            p = Vector((0, 0, zc0)) + Z * math.sin(a) * rr + tl * math.cos(a) * rr
            h = S.ray_cast(p + dl * 2.0, -dl, 2.0)
            if h[0] is not None: need = max(need, (h[0] - p).dot(dl))
    base = Vector((0, 0, zc0)) + dl * (need + 0.05)
    lasso = []
    for li, (dr, rr, dz, ph) in enumerate(((0.0, R0, 0.0, 0.0), (0.024, R0 - 0.012, -0.008, 0.6), (0.046, R0 + 0.01, 0.006, 1.3))):
        pts = []
        for k in range(23):
            a = 2 * PI * k / 22 + ph
            pts.append(base + dl * (dr + 0.006 * math.sin(3 * a)) + Z * (dz + math.sin(a) * rr) + tl * math.cos(a) * rr * 1.05)
        lasso.append(tube_path(f'LassoLoop{li}', pts, 0.02, 'rope' if li != 1 else 'rope_d', n=6, caps=False))
    # loose end hanging down + strap holding the coil to the belt
    e0 = base + dl * 0.03 + Z * (-R0) + tl * 0.04
    tail = [e0, e0 + Z * -0.08 + tl * 0.03 + dl * 0.01, e0 + Z * -0.17 + tl * 0.02 + dl * 0.015]
    lasso.append(tube_path('LassoEnd', tail, 0.02, 'rope', n=6))
    lb = piece_bvh(belt)
    bl, bnrm = project(lb, Vector((0, 0, 2.15)) + dl * 0.3, -dl)
    strap_c = (bl + base + dl * 0.023 + Z * R0) / 2 + Vector((0, 0, 0.0))
    strap_c = Vector((strap_c.x, strap_c.y, 2.15))
    ang = math.atan2(dl.x, -dl.y)
    lasso.append(prim_box('LassoStrap', strap_c, (0.06, (base + dl * 0.07 - bl).length + 0.02, 0.16), 'belt_d', rot=Matrix.Rotation(ang, 3, 'Z')))
    for q in lasso: q.bone = 'LowerTorso'
    P += lasso

    # ---------- cowboy boots with spurs ----------
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        bt = shoe('Boot_' + s, s, off=0.045, bulk=0.03, toe=0.08, sole_h=0.045, open_elev=50)
        def btpaint(U, V, m):
            img = P_solid(pal['boot'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, 0.15 * _noise(U * 9, z * 4), pal['boot_d'])
            wave = 0.5 + 0.025 * np.sin(az * 7)
            img = mix(img, aa(np.abs(z - wave) * 900 - 1.2) * (np.sin(az * 80) > -0.3), pal['boot_st'])    # decorative stitch
            img = mix(img, aa(np.abs(z - wave - 0.03) * 900 - 1.2) * (np.sin(az * 80) > -0.3), pal['boot_st'])
            toe = (np.abs(az) < 0.9) & (z < 0.43)
            img = mix(img, toe.astype(float) * 0.5, pal['boot_d'])                                         # toe cap
            heel = (np.abs(az) > PI - 1.0) & (z < m['sole_top'] + 0.05)
            img = mix(img, heel.astype(float), pal['sole'])
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            return img
        bt.paint = btpaint; P.append(bt)
        fb = piece_bvh(bt)
        back = max((p for p in bt.verts[:len(bt.verts) // 2] if 0.36 < p.z < 0.46), key=lambda p: p.y)
        foot = ('Left' if s == 'L' else 'Right') + 'Foot'
        sp = []
        # heel band around the back of the boot
        pts = []
        cxy = Vector((0.255 * sg, -0.08, 0.0))
        for a in np.linspace(PI / 2 + 0.25, 3 * PI / 2 - 0.25, 11):
            d = Vector((math.sin(a) * sg if False else math.sin(a), -math.cos(a), 0))
            l2, n2 = project(fb, Vector((cxy.x, cxy.y, 0.43)) + d * 0.6, -d)
            if l2 is None: continue
            pts.append(l2 + n2 * 0.014)
        sp.append(tube_path('SpurStrap_' + s, pts, 0.014, 'boot_d', n=5))
        hb = Vector((back.x, back.y, 0.42))
        l2, n2 = project(fb, hb + Vector((0, 0.6, 0)), Vector((0, -1, 0)))
        hb = l2 if l2 is not None else hb
        tip = hb + Vector((0, 0.13, -0.01))
        sp.append(prim_cyl('SpurShank_' + s, hb + Vector((0, 0.005, 0)), tip, 0.013, 0.01, n=6, col='silver'))
        sp.append(prim_cyl('SpurRowel_' + s, tip + Vector((-0.008, 0, 0)), tip + Vector((0.008, 0, 0)), 0.035, n=10, col='silver_d'))
        for k in range(8):
            a = 2 * PI * k / 8
            dd = Vector((0, math.cos(a), math.sin(a)))
            sp.append(prim_cone(f'SpurPoint_{s}{k}', tip + dd * 0.03, tip + dd * 0.08, 0.014, 'silver', n=4))
        for q in sp: q.bone = foot; q.group = 'Feet'
        P += sp
        # stacked cowboy heel under the back of the boot
        ys = [p.y for p in bt.verts if p.z < 0.33]
        ymax = max(ys)
        hl = prim_box('Heel_' + s, Vector((0.255 * sg, ymax - 0.07, 0.335)), (0.2, 0.15, 0.07), 'sole', group='Feet')
        hl.bone = foot; P.append(hl)
    return P, pal
