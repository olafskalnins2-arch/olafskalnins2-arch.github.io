from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '32', 'Rock_Star', 'Rare', 0.32

# ---------------------------------------------------------------- local helpers (module-private)
def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def _sd_seg(x, z, a, b):
    """distance from (x, z) arrays to segment a-b (2D tuples)"""
    ax, az_ = a; bx, bz = b
    dx, dz = bx - ax, bz - az_
    L2 = dx * dx + dz * dz
    t = np.clip(((x - ax) * dx + (z - az_) * dz) / max(L2, 1e-12), 0, 1)
    return np.hypot(x - (ax + t * dx), z - (az_ + t * dz))

def _sd_poly(x, z, pts):
    """signed distance to a closed polygon (negative inside), even-odd rule"""
    d = None; inside = np.zeros(x.shape, bool)
    n = len(pts)
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        dd = _sd_seg(x, z, a, b)
        d = dd if d is None else np.minimum(d, dd)
        (x1, z1), (x2, z2) = a, b
        cond = ((z1 > z) != (z2 > z))
        xi = x1 + (z - z1) * (x2 - x1) / ((z2 - z1) if abs(z2 - z1) > 1e-12 else 1e-12)
        inside ^= cond & (x < xi)
    return np.where(inside, -d, d)

def _earclip(pts):
    """triangulate a simple CCW polygon (list of (u, v)) -> index triples"""
    idx = list(range(len(pts))); tris = []
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def inside(p, a, b, c):
        return cross(a, b, p) >= -1e-12 and cross(b, c, p) >= -1e-12 and cross(c, a, p) >= -1e-12
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1; n = len(idx)
        for k in range(n):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % n]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if cross(a, b, c) <= 1e-12: continue
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)): continue
            tris.append((i0, i1, i2)); idx.pop(k); break
        else:
            break
    if len(idx) == 3: tris.append(tuple(idx))
    return tris

def _slab(name, pts2, C, U, Vv, N, z0, z1, col, group='Extras'):
    """flat extruded outline (u, v) in the plane C + U*u + Vv*v, from N*z0 (back) to N*z1 (front)"""
    pc = Piece(name, group)
    n = len(pts2)
    fr = [pc.add_vert(C + U * u + Vv * v + N * z1) for u, v in pts2]
    bk = [pc.add_vert(C + U * u + Vv * v + N * z0) for u, v in pts2]
    for a, b, c in _earclip(pts2):
        pc.add_face((fr[a], fr[b], fr[c]), None, col)
        pc.add_face((bk[c], bk[b], bk[a]), None, col)
    for k in range(n):
        k2 = (k + 1) % n
        (u1, v1), (u2, v2) = pts2[k], pts2[k2]
        e = U * (u2 - u1) + Vv * (v2 - v1)
        out = e.cross(N)
        f = (fr[k], bk[k], bk[k2], fr[k2])
        if face_normal(pc.verts, f).dot(out) < 0: f = tuple(reversed(f))
        pc.add_face(f, None, col)
    pc.rigid = True; pc.bone = 'UpperTorso'
    return pc

def _wrap_patch(name, bvh, fn, lift, ns, nt, col=None, th=0.014, group='Top'):
    """patch lying on a torso garment; fn(s, t) -> (azimuth, z); cast horizontally toward the body axis"""
    rows = []; hints = []
    for i in range(nt):
        r = []; hh = []
        for j in range(ns):
            a, z = fn(j / (ns - 1), i / (nt - 1))
            d = Vector((math.sin(a), -math.cos(a), 0)); c = Vector((0, 0, z))
            h = bvh.ray_cast(c + d * 2.0, -d, 2.0)
            if h[0] is None: loc, n = c + d * 0.5, d
            else:
                loc, n = h[0], h[1]
                if n.dot(d) < 0: n = -n
            r.append(loc + n * lift); hh.append(n)
        rows.append(r); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group)
    if th: thicken(pc, th)
    pc.meta['patch'] = True
    return pc

def _merge(name, parts, group):
    pc = parts[0]; pc.name = name; pc.rect_key = name; pc.group = group
    for q in parts[1:]: pc.merge(q)
    return pc

def _proj_out(bvh, P, lift):
    """push a rough path point onto the outermost garment surface (cast toward the torso axis)"""
    A = Vector((0, 0, min(P.z, 2.8)))
    d = (P - A); d = d.normalized() if d.length > 1e-6 else Vector((0, -1, 0))
    h = bvh.ray_cast(A + d * 2.5, -d, 2.5)
    if h[0] is None: return P, d
    n = h[1]
    if n.dot(d) < 0: n = -n
    return h[0] + n * lift, n

def _ribbon(name, pts, nrms, w, h, group='Extras'):
    rows = []; hints = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        b = t.cross(nrms[i]).normalized(); n = b.cross(t).normalized()
        if n.dot(nrms[i]) < 0: n = -n
        ring = [p + b * w / 2 + n * h, p - b * w / 2 + n * h, p - b * w / 2, p + b * w / 2]
        mid = p + n * h / 2
        rows.append(ring); hints.append([q - mid for q in ring])
    pc = grid_piece(name, rows, True, hints=hints, group=group,
                    cap_start=pts[0] + nrms[0] * h / 2, cap_end=pts[-1] + nrms[-1] * h / 2,
                    v_vals=[i / (len(pts) - 1) for i in range(len(pts))])
    return pc


def build():
    pal = {'black': '#1b1b1d', 'black2': '#141416', 'black_l': '#242428', 'seam': '#0b0b0c', 'sheen': '#34343a',
           'white': '#f2f2f2', 'white_d': '#d9d9db', 'pink': '#e33b8f', 'pink_d': '#b52a6f', 'pink_l': '#f27bb5',
           'silver': '#c3c6ca', 'silver_d': '#8c9096', 'sole': '#2a2a2a', 'strap': '#2b2b30', 'fret': '#1e1a1c',
           'pickup': '#111113', 'inlay': '#f2f2f2'}
    P = []

    # ------------------------------------------------ ripped black skinny jeans
    pt = pants('Jeans', 2.24, 0.60, 0.03, hip_off=0.05, leg_extra=lambda z, a: 0.01, nseg=16)
    RIPS = {'L': [(0.15, 1.17, 0.075, 0.034), (-0.22, 1.63, 0.05, 0.024), (0.05, 1.42, 0.035, 0.016)],
            'R': [(0.18, 1.50, 0.065, 0.03), (-0.08, 1.09, 0.05, 0.022), (-0.15, 1.78, 0.04, 0.018)]}
    def jeans(U, V, m):
        img = P_solid(pal['black2'])(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            # soft fade on the front of the thigh, seams on both sides
            img = mix(img, 0.55 * np.exp(-(az / 0.55) ** 2) * np.clip((z - 0.9) / 0.7, 0, 1), '#25252a')
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.012) * 300), '#2c2c32')
            x = az * 0.19
            for cx, cz, w, h in RIPS.get(m.get('side', 'L'), []):
                cxu = cx * 0.19
                rr = np.sqrt(((x - cxu) / w) ** 2 + ((z - cz) / h) ** 2)
                rr = rr - 0.10 * np.sin((x - cxu) * 150 + cz * 7) - 0.07 * np.sin((x - cxu) * 330 + 1.3)
                img = mix(img, aa((rr - 1.35) * 25), '#55555c')          # frayed edge
                img = mix(img, aa((rr - 1.0) * 25), SKIN)                 # skin through the rip
                thr = np.abs(((z - cz) / 0.016) % 1.0 - 0.5)
                img = mix(img, aa((rr - 1.02) * 25) * (thr < 0.17), '#ececee')   # white threads across
        else:
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300), '#2c2c32')
            img = mix(img, aa((np.abs(az - 0.05) - 0.006) * 400) * (z < 2.16) * (z > 1.98), '#2c2c32')   # fly stitch
        return img
    for p in pt: p.paint = jeans
    P += pt

    # ------------------------------------------------ white tee (tucked) with a pink lightning bolt
    tee = torso_shell('Tee', 2.08, 0.028, nseg=32, th=0.015)
    BOLT = [(0.02, 0.27), (0.125, 0.27), (0.045, 0.06), (0.115, 0.06), (-0.075, -0.25), (-0.02, -0.02), (-0.09, -0.02)]
    def tee_paint(U, V, m):
        img = P_solid(pal['white'])(U, V, m)
        z, az = zc(U, V, m)
        x = az * 0.45
        sd = _sd_poly(x, z - 2.63, BOLT)
        img = mix(img, aa((sd - 0.012) * 500), pal['black'])      # outline
        img = mix(img, aa(sd * 500), pal['pink'])
        img = mix(img, aa((sd + 0.03) * 500) * np.clip((z - 2.63) * 6, 0, 1) * 0.5, pal['pink_l'])
        img = mix(img, aa((m['zmax'] - 0.05 - z) * 500), pal['white_d'])   # neck rib
        return img
    tee.paint = tee_paint; P.append(tee)

    # ------------------------------------------------ studded belt fitted on the jeans hip
    belt = band('Belt', 2.12, 2.23, 0.012, th=0.02, bvh=piece_bvh(pt[0])); belt.group = 'Bottom'
    belt.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa(np.minimum(V - 0.1, 0.9 - V) * -250), '#2c2c30')
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.175)), Vector((0, 1, 0)))
    bc = loc + n * 0.018
    bk = [prim_box('BuckleL', bc + Vector((-0.075, 0, 0)), (0.03, 0.03, 0.15), 'silver', group='Bottom'),
          prim_box('BuckleR', bc + Vector((0.075, 0, 0)), (0.03, 0.03, 0.15), 'silver', group='Bottom'),
          prim_box('BuckleT', bc + Vector((0, 0, 0.06)), (0.18, 0.03, 0.03), 'silver', group='Bottom'),
          prim_box('BuckleB', bc + Vector((0, 0, -0.06)), (0.18, 0.03, 0.03), 'silver', group='Bottom'),
          prim_box('BucklePin', bc + Vector((0, -0.006, 0)), (0.1, 0.02, 0.022), 'silver_d', group='Bottom')]
    buckle = _merge('Buckle', bk, 'Bottom'); buckle.bone = 'LowerTorso'; P.append(buckle)
    studs = []
    for a in (-0.31, -0.22, 0.22, 0.31):
        d = Vector((math.sin(a), -math.cos(a), 0))
        l2, n2 = project(bb, d * 1.5 + Vector((0, 0, 2.175)), -d)
        studs.append(prim_cone(f'BStud{a}', l2 - n2 * 0.004, l2 + n2 * 0.045, 0.03, 'silver', n=4, group='Bottom'))
    bs = _merge('BeltStuds', studs, 'Bottom'); bs.bone = 'LowerTorso'; P.append(bs)

    # ------------------------------------------------ black leather biker jacket (open front)
    E0 = 2 * PI / 48 * 3            # front edge of the cut (3 columns of 48 either side of the centre)
    def wv(z): return 0.38 + max(0.0, z - 2.7) * 0.85
    def jkeep(i, j, zc_, az): return abs(az) > wv(zc_)
    jex = lambda z, a: 0.014 + 0.025 * max(0, 2.2 - z)
    under = pt + [tee, belt]
    jk = torso_shell('Jacket', 1.97, 0.075, nseg=48, extra=jex, keep=jkeep, th=0.022, hang=2.3, over=under)
    jfull = torso_shell('JacketFull', 1.97, 0.075, nseg=48, extra=jex, th=0, hang=2.3, over=under)   # uncut: lapel support
    jfb = piece_bvh(jfull)
    def seg(x, z, a, b): return _sd_seg(x, z, a, b)
    def jpaint(U, V, m):
        img = P_solid(pal['black'])(U, V, m)
        z, az = zc(U, V, m); x = az * 0.5
        aaz = np.abs(az)
        img = mix(img, 0.55 * np.exp(-((aaz - 1.0) / 0.22) ** 2), pal['sheen'])        # leather sheen
        img = mix(img, 0.35 * np.exp(-((aaz - 2.45) / 0.25) ** 2), pal['sheen'])
        for c in (1.32, 2.2):                                                           # panel seams
            img = mix(img, aa((np.abs(aaz - c) - 0.006) * 400) * (z < 2.95), pal['seam'])
        img = mix(img, aa(np.abs(z - 2.95) * 500 - 1.5) * (aaz > 1.32), pal['seam'])    # yoke
        hem = m['zmin'] + 0.085
        img = mix(img, aa((z - hem) * 400), '#151517')                                  # waistband
        img = mix(img, aa(np.abs(z - hem) * 500 - 1.2), pal['seam'])
        # silver zip along both front edges
        zz = (aaz > E0 - 0.002) & (aaz < E0 + 0.05) & (z < 2.78)
        teeth = (np.floor(z / 0.016) % 2 == 0)
        img = mix(img, zz * 1.0, pal['silver'])
        img = mix(img, (zz & teeth & (aaz > E0 + 0.018) & (aaz < E0 + 0.032)) * 1.0, pal['silver_d'])
        # diagonal chest zip pocket (left) and slanted hip zip pockets
        dchest = seg(x, z, (0.31, 2.50), (0.5, 2.73)) * (az > 0)
        dchest = np.where(az > 0, dchest, 9)
        dhipL = seg(x, z, (0.31, 2.36), (0.45, 2.12)); dhipR = seg(x, z, (-0.31, 2.36), (-0.45, 2.12))
        for dd in (dchest, np.where(az > 0, dhipL, 9), np.where(az < 0, dhipR, 9)):
            img = mix(img, aa((dd - 0.011) * 500), pal['silver'])
            img = mix(img, aa((dd - 0.004) * 500) * (np.floor(z / 0.014) % 2 == 0), pal['silver_d'])
        return img
    jk.paint = jpaint; P.append(jk)
    jb = piece_bvh(jk)
    # wide lapels lying on the jacket next to the V (cover the stepped cut edge)
    lapels = []
    for sg in (-1, 1):
        def lap(s, t, sg=sg):
            z = 2.5 + t * 0.62
            inner = max(E0, wv(z) - 0.11)
            return sg * (inner + s * (0.05 + 0.42 * t ** 0.8)), z
        lp = _wrap_patch(f'Lapel{sg}', jfb, lap, 0.012, 5, 8, th=0.014)
        lp.paint = lambda U, V, m: mix(P_solid(pal['black_l'])(U, V, m), aa((np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V)) - 0.04) * 300), pal['seam'])
        lp.rect_key = 'Lapel'
        P.append(lp); lapels.append(lp)
    col = collar('Collar', 'fold', h=0.08, flare=0.08, open_front=0.55, col='black_l', fold=0.1, lift=0.02)
    P.append(col)
    # snap studs on the lapel tips + zip pulls
    lb = piece_bvh(*lapels)
    snaps = []
    for sg in (-1, 1):
        z = 3.0; a = sg * (max(E0, wv(z) - 0.11) + 0.05 + 0.42 * ((z - 2.5) / 0.62) ** 0.8 - 0.07)
        d = Vector((math.sin(a), -math.cos(a), 0))
        l2, n2 = project(lb, d * 1.5 + Vector((0, 0, z)), -d)
        if l2 is not None: snaps.append(prim_cyl(f'Snap{sg}', l2 - n2 * 0.004, l2 + n2 * 0.02, 0.026, n=8, col='silver', group='Top'))
        z = 2.62; a = sg * (E0 + 0.07)
        d = Vector((math.sin(a), -math.cos(a), 0))
        l2, n2 = project(lb, d * 1.5 + Vector((0, 0, z)), -d)
        if l2 is not None: snaps.append(prim_cyl(f'SnapB{sg}', l2 - n2 * 0.004, l2 + n2 * 0.02, 0.026, n=8, col='silver', group='Top'))
    sn = _merge('LapelSnaps', snaps, 'Top'); sn.bone = 'UpperTorso'; P.append(sn)
    pulls = []
    for nm, x, z in (('PullChest', 0.31, 2.50), ('PullHipL', 0.31, 2.36), ('PullHipR', -0.31, 2.36)):
        a = x / 0.5; d = Vector((math.sin(a), -math.cos(a), 0))
        l2, n2 = project(jb, d * 1.5 + Vector((0, 0, z)), -d)
        if l2 is None: continue
        pc = prim_box(nm, l2 + n2 * 0.012 + Vector((0, 0, -0.03)), (0.035, 0.02, 0.07), 'silver')
        pc.bone = 'UpperTorso' if z > 2.45 else 'LowerTorso'
        P.append(pc)
    # sleeves with quilted elbows and cuff zips
    sleeves = []
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.93, 0.06, extra=lambda t, a: 0.012 + 0.012 * t)
        def spaint(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            az = 2 * PI * (U - 0.5)
            img = mix(img, 0.45 * np.exp(-((np.abs(az) - 0.5) / 0.35) ** 2), pal['sheen'])
            for k in range(5):
                img = mix(img, aa(np.abs(V - (0.47 + k * 0.03)) * 600 - 1.0), pal['seam'])
            zipm = (np.abs(np.abs(az) - PI) < 0.16) & (V > 0.78)
            img = mix(img, zipm * 1.0, pal['silver'])
            img = mix(img, (zipm & (np.floor(V / 0.012) % 2 == 0) & (np.abs(np.abs(az) - PI) < 0.06)) * 1.0, pal['silver_d'])
            img = mix(img, aa((V - 0.95) * -400), '#151517')
            return img
        sl.paint = spaint; P.append(sl); sleeves.append(sl)

    # ------------------------------------------------ studded shoulders (pyramid studs, one bone each)
    for s, sl in zip('LR', sleeves):
        sg = 1 if s == 'L' else -1
        sb_ = piece_bvh(sl); tb_ = piece_bvh(jk, col)
        arm_st = []; tor_st = []
        for x in (0.40, 0.49, 0.58):
            for y in (-0.11, 0.0, 0.11):
                p0 = Vector((sg * x, y, 3.8))
                hs = sb_.ray_cast(p0, Vector((0, 0, -1)), 2.0)
                ht = tb_.ray_cast(p0, Vector((0, 0, -1)), 2.0)
                use_arm = hs[0] is not None and (ht[0] is None or hs[0].z >= ht[0].z)
                h = hs if use_arm else ht
                if h[0] is None: continue
                n = h[1] if h[1].z > 0 else -h[1]
                st = prim_cone(f'SStud{s}{x}{y}', h[0] - n * 0.004, h[0] + n * 0.05, 0.03, 'silver', n=4, group='Top')
                (arm_st if use_arm else tor_st).append(st)
        if arm_st:
            a = _merge('ShoulderStuds_' + s, arm_st, 'Top'); a.region = 'arm_' + s
            a.bone = ('Left' if s == 'L' else 'Right') + 'UpperArm'; P.append(a)
        if tor_st:
            t = _merge('ShoulderStudsT_' + s, tor_st, 'Top'); t.bone = 'UpperTorso'
            head_clear(t, 0.03); P.append(t)

    # ------------------------------------------------ black buckle boots
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Boot_' + s, s, off=0.045, bulk=0.035, toe=0.035, sole_h=0.065)
        def bpaint(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, 0.4 * np.exp(-((np.abs(az) - 0.6) / 0.4) ** 2), pal['sheen'])
            img = mix(img, aa(np.abs(z - m['sole_top'] - 0.03) * 600 - 1.0), '#3a3a40')    # welt stitch
            return mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
        sh.paint = bpaint; P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 0.86, 0.46, 0.08, nseg=16, group='Feet', extra=lambda z, a: 0.006))
        shaft.paint = lambda U, V, m: mix(mix(P_solid(pal['black'])(U, V, m), aa((0.92 - V) * 300), '#2c2c30'),
                                          0.35 * np.exp(-((np.abs(2 * PI * (U - 0.5)) - 0.5) / 0.35) ** 2), pal['sheen'])
        P.append(shaft)
        for k, (z0, z1) in enumerate(((0.80, 0.74), (0.64, 0.58))):
            stp = _shin(leg_tube(f'BootStrap{k}_' + s, s, z0, z1, 0.104, nseg=16, nrows=2, group='Feet', col='strap', th=0.015))
            P.append(stp)
            stb = piece_bvh(stp)
            d = Vector((sg, -0.25, 0)).normalized()
            c = leg_point(s, (z0 + z1) / 2)
            l2, n2 = project(stb, c + d * 1.0, -d)
            if l2 is None: continue
            n2 = Vector((n2.x, n2.y, 0)).normalized()
            Rm = Matrix.Rotation(math.atan2(n2.x, -n2.y), 3, 'Z')
            q = l2 + n2 * 0.014
            side = Rm @ Vector((1, 0, 0))
            parts = [prim_box(f'BkA{k}{s}', q + side * 0.04, (0.018, 0.022, 0.09), 'silver', rot=Rm, group='Feet'),
                     prim_box(f'BkB{k}{s}', q - side * 0.04, (0.018, 0.022, 0.09), 'silver', rot=Rm, group='Feet'),
                     prim_box(f'BkC{k}{s}', q + Vector((0, 0, 0.036)), (0.098, 0.022, 0.018), 'silver', rot=Rm, group='Feet'),
                     prim_box(f'BkD{k}{s}', q - Vector((0, 0, 0.036)), (0.098, 0.022, 0.018), 'silver', rot=Rm, group='Feet'),
                     prim_box(f'BkE{k}{s}', q, (0.05, 0.026, 0.012), 'silver_d', rot=Rm, group='Feet')]
            bkp = _merge(f'BootBuckle{k}_' + s, parts, 'Feet')
            bkp.bone = ('Left' if s == 'L' else 'Right') + 'LowerLeg'; bkp.region = 'shin_' + s
            P.append(bkp)

    # ------------------------------------------------ guitar strap (over the right shoulder, across the chest)
    Vg = Vector((-0.643, 0, 0.766)).normalized(); Ng = Vector((0, 1, 0)); Ug = Vg.cross(Ng).normalized()
    Cxz = Vector((0.30, 0, 2.30))
    S = 1.22                                              # guitar scale
    Ug = Ug * S; Vg = Vg * S
    horn = Cxz + Ug * (-0.17) + Vg * 0.29
    anchors = [Vector((horn.x, 0.5, horn.z)), Vector((-0.05, 0.45, 2.98)), Vector((-0.3, 0.32, 3.18)),
               Vector((-0.36, 0.12, 3.3)), Vector((-0.36, -0.08, 3.3)), Vector((-0.33, -0.3, 3.14)),
               Vector((-0.18, -0.48, 3.0)), Vector((0.05, -0.52, 2.93)), Vector((0.3, -0.45, 2.8)),
               Vector((0.5, -0.25, 2.62)), Vector((0.6, 0.05, 2.5)), Vector((0.5, 0.35, 2.45))]
    sbv = piece_bvh(jk, col, tee, *lapels, sn)
    path = smooth_line(polyline_resample(anchors, 44), 3)
    pts = []; nrms = []
    for p in path:
        q, n = _proj_out(sbv, p, 0.012)
        pts.append(q); nrms.append(n)
    for _ in range(2):                                    # smooth, then never sink back under the garments
        pts = smooth_line(pts, 1)
        pts2 = []
        for p, n in zip(pts, nrms):
            q, n2 = _proj_out(sbv, p, 0.012)
            A = Vector((0, 0, min(p.z, 2.8)))
            pts2.append(q if (q - A).length > (p - A).length else p)
        pts = pts2
    strap = _ribbon('GuitarStrap', pts, nrms, 0.085, 0.022)
    def strap_paint(U, V, m):
        img = P_solid(pal['strap'])(U, V, m)
        uu = (U % 0.25) / 0.25
        img = mix(img, ((np.abs(uu - 0.12) < 0.05) | (np.abs(uu - 0.88) < 0.05)) * (U < 0.25), pal['pink'])
        return img
    strap.paint = strap_paint
    head_clear(strap, 0.03)
    strap.rigid = True; strap.bone = 'UpperTorso'; P.append(strap)

    # ------------------------------------------------ pink electric guitar slung on the back
    BODY = [(0, -0.36), (0.14, -0.345), (0.25, -0.29), (0.31, -0.19), (0.315, -0.08), (0.28, 0.0), (0.24, 0.06),
            (0.25, 0.13), (0.24, 0.2), (0.2, 0.255), (0.16, 0.265), (0.12, 0.22), (0.08, 0.17), (0.0, 0.155),
            (-0.08, 0.17), (-0.12, 0.24), (-0.16, 0.31), (-0.21, 0.30), (-0.25, 0.24), (-0.26, 0.14), (-0.24, 0.06),
            (-0.28, 0.0), (-0.315, -0.08), (-0.31, -0.19), (-0.25, -0.29), (-0.14, -0.345)]
    GUARD = [(0.02, -0.25), (0.15, -0.27), (0.24, -0.2), (0.26, -0.08), (0.2, 0.02), (0.17, 0.12), (0.1, 0.13),
             (0.03, 0.12), (-0.05, 0.1), (-0.07, -0.02), (-0.03, -0.12)]
    HEAD = [(-0.048, 1.0), (0.048, 1.0), (0.075, 1.07), (0.072, 1.2), (0.03, 1.26), (-0.04, 1.25), (-0.072, 1.19), (-0.07, 1.07)]
    # back plane: clear of everything already on the back
    cb = piece_bvh(jk, col, tee, strap, *sleeves)
    samples = [Cxz + Ug * u + Vg * v for u, v in BODY] + [Cxz + Ug * u * 0.5 + Vg * v * 0.5 for u, v in BODY]
    samples += [Cxz + Ug * u + Vg * v for v in np.linspace(0.15, 1.26, 14) for u in (-0.07, 0.0, 0.07)]
    ymax = 0.45
    for s_ in samples:
        h = cb.ray_cast(Vector((s_.x, 3.0, s_.z)), Vector((0, -1, 0)), 4.0)
        if h[0] is not None: ymax = max(ymax, h[0].y)
    C = Vector((Cxz.x, ymax + 0.015, Cxz.z))
    G = []
    G.append(_slab('GuitarBody', BODY, C, Ug, Vg, Ng, 0.0, 0.1, 'pink'))
    G.append(_slab('GuitarGuard', GUARD, C, Ug, Vg, Ng, 0.1, 0.112, 'white'))
    G.append(_slab('GuitarHead', HEAD, C, Ug, Vg, Ng, 0.04, 0.085, 'pink'))
    Rg = Matrix((Ug, Vg, Ng)).transposed()
    def at(u, v, w): return C + Ug * u + Vg * v + Ng * w
    G.append(prim_box('GuitarNeck', at(0, 0.58, 0.067), (0.08, 0.86, 0.05), 'pink_d', rot=Rg))
    G.append(prim_box('Fretboard', at(0, 0.6, 0.103), (0.078, 0.82, 0.02), 'fret', rot=Rg))
    for k in range(12):
        v = 0.98 - 0.065 * k ** 0.92
        if v < 0.2: break
        G.append(prim_box(f'Fret{k}', at(0, v, 0.114), (0.078, 0.006, 0.006), 'silver', rot=Rg))
        if k in (2, 4, 6, 8):
            G.append(prim_box(f'Inlay{k}', at(0, v + 0.03, 0.114), (0.02, 0.02, 0.004), 'inlay', rot=Rg))
    G.append(prim_box('Nut', at(0, 1.0, 0.105), (0.08, 0.012, 0.025), 'white', rot=Rg))
    for k, v in enumerate((1.07, 1.13, 1.19)):
        for sgn in (-1, 1):
            G.append(prim_cyl(f'Peg{k}{sgn}', at(sgn * 0.07, v, 0.062), at(sgn * 0.115, v, 0.062), 0.013, n=6, col='silver'))
            G.append(prim_cyl(f'PegPost{k}{sgn}', at(sgn * 0.04, v, 0.085), at(sgn * 0.04, v, 0.11), 0.01, n=6, col='silver'))
    G.append(prim_box('PickupNeck', at(0, 0.07, 0.122), (0.16, 0.05, 0.022), 'pickup', rot=Rg))
    G.append(prim_box('PickupBridge', at(0, -0.06, 0.122), (0.16, 0.05, 0.022), 'pickup', rot=Rg))
    for k, v in enumerate((0.07, -0.06)):
        for kk in range(6):
            G.append(prim_box(f'Pole{k}{kk}', at(-0.055 + kk * 0.022, v, 0.134), (0.01, 0.01, 0.004), 'silver', rot=Rg))
    G.append(prim_box('Bridge', at(0, -0.17, 0.12), (0.15, 0.05, 0.022), 'silver', rot=Rg))
    G.append(prim_box('Tailpiece', at(0, -0.23, 0.115), (0.13, 0.025, 0.014), 'silver_d', rot=Rg))
    for k in range(6):                                    # strings
        u = -0.025 + k * 0.01
        G.append(prim_box(f'String{k}', at(u, 0.42, 0.117), (0.003, 1.17, 0.003), 'silver', rot=Rg))
    for k, (u, v) in enumerate(((0.17, -0.12), (0.21, -0.2), (0.12, -0.21))):
        G.append(prim_cyl(f'Knob{k}', at(u, v, 0.108), at(u, v, 0.14), 0.024, n=8, col='silver'))
    G.append(prim_box('Switch', at(-0.17, 0.18, 0.11), (0.012, 0.012, 0.05), 'silver', rot=Rg))
    G.append(prim_cyl('StrapPinT', at(-0.17, 0.3, 0.02), at(-0.17, 0.33, 0.02), 0.016, n=6, col='silver'))
    G.append(prim_cyl('StrapPinB', at(0, -0.36, 0.05), at(0, -0.39, 0.05), 0.016, n=6, col='silver'))
    for g in G: g.bone = 'UpperTorso'; g.group = 'Extras'
    head_clear(G[2], 0.03)
    # merge the small hardware into a few pieces (fewer objects); keep the coloured slabs separate
    hw = [g for g in G[3:]]
    by = {}
    for g in hw: by.setdefault(g.fcol[0], []).append(g)
    P += G[:3]
    for k, (c, lst) in enumerate(by.items()):
        m_ = _merge(f'GuitarHW{k}', lst, 'Extras'); m_.bone = 'UpperTorso'; P.append(m_)
    return P, pal
