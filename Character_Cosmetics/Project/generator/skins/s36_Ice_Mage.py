from o04 import *
NUM, NAME, RARITY, MAXD = '36', 'Ice_Mage', 'Epic', 0.7


from garments import _grid_with_ij, filter_faces


def _cap_dome(name, side, center, off, elevs, nseg=20, extra=None, group='Top', th=0.025, reach=-0.2):
    """shoulder cap: like o04.dome, but only the outer part (never spreads over the chest / back / neck)"""
    sg = 1 if side == 'L' else -1
    bv = side_bvh(side)
    D = hdirs_b(nseg); rows = []; hints = []; dirs_all = []
    for e in elevs:
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        ex = (lambda j, p, e=e: extra(e, azb(j, nseg))) if extra else None
        rows.append(ray_ring(bv, center, dirs, off, R=0.9, extra=ex, smooth=2)); hints.append(dirs); dirs_all.append(dirs)
    top = bv.ray_cast(center + Z * 0.9, -Z, 0.9)
    pc = _grid_with_ij(name, rows, True, [i / (len(rows) - 1) for i in range(len(rows))], hints, group, None,
                       cap_end=(top[0] + Z * off) if top[0] else center + Z * 0.3)
    M = len(rows)
    def keep(ij, f):
        i, j = ij
        if i >= M - 1: return True
        p = sum((pc.verts[k] for k in f), Vector()) / len(f)
        return (p.x - center.x) * sg > (reach if elevs[i] >= 20 else -0.02)
    filter_faces(pc, keep)
    if th: thicken(pc, th)
    return pc


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _flake_d(dx, dz, R, w):
    """signed distance-ish field of a 6-armed snowflake (arms + two pairs of side branches + hex centre)"""
    r = np.sqrt(dx ** 2 + dz ** 2)
    th = np.arctan2(dz, dx)
    a = np.mod(th + PI / 6, PI / 3) - PI / 6
    al = r * np.cos(a); v = np.abs(r * np.sin(a))
    d = np.where(al < R, v, np.sqrt((al - R) ** 2 + v ** 2))
    for b, L in ((0.5 * R, 0.34 * R), (0.76 * R, 0.2 * R)):
        u = al - b
        t = u * 0.5 + v * 0.866
        db = np.abs(u * 0.866 - v * 0.5)
        db = np.where((t >= 0) & (t <= L), db, 9.0)
        d = np.minimum(d, db)
    d = np.minimum(d, r - 2.2 * w)
    return d - w


def _flakes(img, z, az, rfn, pts, col, k=300):
    """pts: (az0, z0, R, rot). Distances measured on the surface: d_around = d_az * local radius."""
    for a0, z0, R, rot in pts:
        near = np.abs(z - z0) < R * 1.2
        if not near.any(): continue
        rr = rfn(z0)
        da = np.mod(az - a0 + PI, 2 * PI) - PI
        dx = da * rr; dz = z - z0
        if np.min(np.abs(dx)) > R * 1.3: continue
        c, s = math.cos(rot), math.sin(rot)
        d = _flake_d(dx * c - dz * s, dx * s + dz * c, R, R * 0.09)
        img = mix(img, aa(d * k) * near, col)
    return img


def _flake_pts(z0, z1, rfn, step, R0, R1, seed, skip=None):
    rng = np.random.default_rng(seed)
    out = []; row = 0
    z = z0
    while z < z1:
        rr = rfn(z); n = max(4, int(round(2 * PI * rr / step)))
        off = (row % 2) * 0.5
        for q in range(n):
            a = -PI + 2 * PI * (q + off + rng.uniform(-0.18, 0.18)) / n
            zz = z + rng.uniform(-0.03, 0.03)
            if skip and skip(a, zz): continue
            f = (z1 - zz) / (z1 - z0)
            out.append((a, zz, R0 + (R1 - R0) * f * rng.uniform(0.75, 1.0), rng.uniform(0, PI / 3)))
        z += step * 0.86; row += 1
    return out


def build():
    pal = {'ice': '#9fd3f2', 'ice_d': '#6fb6e0', 'ice_dd': '#4f97c6', 'white': '#ffffff', 'fur': '#f4f9fc', 'fur_d': '#d9e8f2',
           'silver': '#d8e3ea', 'silver_d': '#a9bccb', 'crystal': '#d8f1ff', 'crystal_d': '#a8dcf6', 'spike': '#7cc6ef', 'legging': '#e4f2fb',
           'sole': '#a9bccb'}
    P = []
    # ---- under layers: pale leggings (seen when the robe slits open) and white boots ----
    legs = [skin_leg(s, 1.9, 0.47) for s in 'LR']
    for p in legs: p.paint = P_solid(pal['legging'])
    shafts = []
    for s in 'LR':
        sh = _shin(leg_tube('BootShaft_' + s, s, 0.86, 0.47, 0.06, nseg=16, group='Feet', extra=lambda z, a: 0.006 + 0.03 * max(0, z - 0.7)))
        sh.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.abs(zc(U, V, m)[0] - 0.62) * 300 - 4), pal['ice_d'])
        shafts.append(sh)
    # ---- the robe: floor length A-line, front/back slit panels like the wizard ----
    def rex(z, a): return 0.01 + 0.17 * max(0, 2.1 - z) ** 1.1
    Z_HEM = 0.72
    robe = torso_shell('Robe', Z_HEM, 0.06, nseg=40, extra=rex, th=0.025, slits=RF_SLIT_TOP(), hang=2.3, over=legs + shafts)

    def rrad(z): return 0.5 + (rex(z, 0) if z < 2.3 else 0.03)
    robe_flakes = _flake_pts(0.9, 2.82, rrad, 0.34, 0.075, 0.045, 36,
                             skip=lambda a, z: (abs(a) < 0.3 and z < 2.95) or (2.05 < z < 2.36) or (abs(abs(a) - PI) < 0.42 and 2.25 < z < 2.95))
    panel_flakes = [(0.0, z, 0.05 + 0.025 * (1.95 - z) / 1.2, 0.0) for z in (0.98, 1.28, 1.58, 1.88)] + [(0.0, 2.62, 0.05, 0.0)]

    def rp(U, V, m):
        img = P_solid(pal['ice'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, np.clip((1.9 - z) / 1.2, 0, 1) * 0.55, pal['ice_d'])                     # deepens toward the hem
        img = mix(img, np.clip((z - 2.6) / 0.6, 0, 1) * 0.25, '#c3e4f7')                         # frosty shoulders
        if m.get('kind') == 'torso':
            pw = 0.16 + 0.08 * np.clip((2.2 - z) / 1.4, 0, 1)                                     # front panel widens to the hem
            fp = (np.abs(az) < pw) & (z < 3.0)
            img = mix(img, aa((np.abs(az) - pw) * 300) * (z < 3.0), pal['ice_d'])
            img = mix(img, aa(np.abs(np.abs(az) - pw) * 300 - 1.6) * (z < 3.0), pal['silver'])   # silver piping
            img = _flakes(img, z, az, rrad, panel_flakes, pal['white'])
            img = _flakes(img, z, az, rrad, [(PI, 2.6, 0.19, 0.0)], pal['silver'])               # big back snowflake
            img = _flakes(img, z, az, rrad, robe_flakes, pal['white'])
            img = mix(img, aa(np.abs(z - (m['zmin'] + 0.17)) * 300 - 1.6), pal['silver'])        # silver line above the fur
            img = mix(img, aa(np.abs(z - 3.02) * 300 - 1.6) * 0.9, pal['silver'])                 # neckline trim
        return img
    robe.paint = rp; robe.smooth_iters = 6; P.append(robe)
    P += legs + shafts
    # white fur hem: a thick ring with the SAME slit panels, sitting on the robe hem
    rb = robe
    def fur_paint(seed):
        def f(U, V, m):
            img = P_solid(pal['fur'])(U, V, m)
            x, zz = phys(U, V, m)
            n1 = np.sin(x * 61 + np.sin(zz * 47) * 2.1) * np.sin(zz * 53 + np.sin(x * 37 + seed) * 1.7)
            img = mix(img, np.clip(n1, 0, 1) * 0.55, pal['fur_d'])
            img = mix(img, np.clip(-n1 - 0.4, 0, 1) * 0.7, pal['white'])
            return img
        return f
    hem = torso_shell('HemFur', Z_HEM - 0.05, 0.06, nseg=40, zs=[Z_HEM - 0.05, Z_HEM + 0.04, Z_HEM + 0.13], elevs=(),
                      extra=rex, th=0.035, slits=RF_SLIT_TOP(), hang=Z_HEM + 0.131, over=[rb], over_gap=0.04)
    hem.paint = fur_paint(1.0); hem.rect_key = 'HemFur'; P.append(hem)
    # fur collar
    col = collar('FurCollar', 'stand', h=0.07, flare=0.07, col='fur', th=0.03)
    P.append(col)
    # ---- wide bell sleeves with fur cuffs ----
    def sex(t, a): return 0.012 + 0.26 * max(0, t - 0.3) ** 1.5
    sl_flakes = None
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.84, 0.06, extra=sex)
        def spaint(U, V, m):
            img = P_solid(pal['ice'])(U, V, m)
            img = mix(img, np.clip((V - 0.4) / 0.6, 0, 1) * 0.5, pal['ice_d'])
            m = dict(m, length=0.95)
            pts, X, Zz, circ = scatter(U, V, m, 10, 361, None)
            for px, pz, k in pts:
                R = 0.045 + (k % 3) * 0.008
                for o in (-circ, 0, circ):
                    dx = X - (px + o)
                    if np.min(np.abs(dx)) > R * 1.3: continue
                    img = mix(img, aa(_flake_d(dx, Zz - pz, R, R * 0.09) * 300), pal['white'])
            return img
        sl.paint = spaint; sl.weight = 'nearest'; P.append(sl)
        cf = sleeve('SleeveFur_' + s, s, 0.76, 0.86, 0.06, nrows=3, cap=False, extra=lambda t, a: sex(t, a) + 0.045, th=0.035)
        cf.paint = fur_paint(2.0); cf.rect_key = 'SleeveFur'; P.append(cf)
    # ---- frosted silver sash fitted on the robe, crystal snowflake buckle ----
    sash = band('Sash', 2.1, 2.3, 0.012, th=0.02, bvh=piece_bvh(robe))
    def sashp(U, V, m):
        img = P_solid(pal['silver'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, (0.5 + 0.5 * np.cos(az * 6)) * 0.25, '#f2f7fa')
        img = mix(img, aa(np.minimum(V - 0.1, 0.9 - V) * -300), pal['silver_d'])
        x, zz = phys(U, V, m)
        frost = np.sin(x * 90 + np.sin(zz * 70) * 3) * np.sin(zz * 110 + x * 13)
        return mix(img, np.clip(frost - 0.5, 0, 1) * 0.8, '#ffffff')
    sash.paint = sashp; P.append(sash)
    sb = piece_bvh(sash)
    loc, n = project(sb, Vector((0, 0, 2.2)), Vector((0, 1, 0)))
    bc = loc + n * 0.025
    P.append(prim_rbox('SashBuckle', bc, (0.22, 0.05, 0.22), 'silver_d'))
    f0 = bc + Vector((0, -0.03, 0))
    P.append(prim_rbox('BuckleInlay', f0, (0.17, 0.02, 0.17), 'ice_dd'))
    for k in range(3):
        R = Matrix.Rotation(k * PI / 3, 3, 'Y')
        P.append(prim_box(f'BuckleFlake{k}', f0 + Vector((0, -0.014, 0)), (0.15, 0.012, 0.022), 'crystal', rot=R))
    P.append(prim_sphere('BuckleGem', f0 + Vector((0, -0.022, 0)), 0.032, 'white', nl=4, seg=6, scale=(1, 0.6, 1)))
    # sash tie hanging on the wearer's left hip (short, stays above the slit tops)
    loc2, n2 = project(sb, Vector((0.33, 0, 2.2)), Vector((0, 1, 0)))
    tc = loc2 + n2 * 0.03
    P.append(prim_rbox('SashKnot', tc, (0.11, 0.06, 0.1), 'silver'))
    for k, (dx, ln) in enumerate(((-0.03, 0.2), (0.04, 0.17))):
        a = tc + Vector((dx, -0.005, -0.04)); b = a + Vector((dx * 0.6, -0.01, -ln))
        P.append(tube_path(f'SashTail{k}', [a, (a + b) / 2 + Vector((0, -0.01, 0)), b], 0.028, 'silver', n=6,
                           rfn=lambda t: 0.028 + 0.012 * t))
        P.append(prim_cone(f'SashTailCrystal{k}', b + Vector((0, 0, 0.01)), b + Vector((0, 0, -0.08)), 0.03, 'crystal', n=4))
    for q in P[-7:]: q.bone = 'LowerTorso'
    # ---- crystal brooch on the collar ----
    loc, n = project(piece_bvh(robe), Vector((0, 0, 2.95)), Vector((0, 1, 0)))
    gc = loc + n * 0.035
    P.append(prim_rbox('BroochMount', gc, (0.13, 0.04, 0.13), 'silver'))
    P.append(prim_cone('BroochGemA', gc + Vector((0, -0.02, 0)), gc + Vector((0, -0.02, 0.09)), 0.05, 'crystal', n=4))
    P.append(prim_cone('BroochGemB', gc + Vector((0, -0.02, 0)), gc + Vector((0, -0.02, -0.09)), 0.05, 'crystal_d', n=4))
    for q in P[-3:]: q.bone = 'UpperTorso'; head_clear(q, 0.03)
    # ---- frost pauldrons with jagged ice-crystal spikes ----
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        pc0 = Vector((0.58 * sg, 0.0, 2.86))
        pd = _cap_dome('FrostPauldron_' + s, s, pc0, 0.09, (-24, -8, 10, 30, 50, 70), extra=lambda e, a: 0.03 * max(0, (12 - e) / 36))
        def pdp(U, V, m):
            img = P_solid(pal['silver'])(U, V, m)
            img = mix(img, np.clip(1 - V * 1.4, 0, 1) * 0.6, pal['ice_d'])
            return mix(img, aa(np.abs(V - 0.14) * 300 - 1.5), pal['white'])
        pd.paint = pdp; pd.meta.update(circ=1.6); pd.rect_key = 'FrostPauldron'; pd.bone = 'UpperTorso'
        head_clear(pd, 0.03); P.append(pd)
        pb = piece_bvh(pd)
        spikes = ((0.0, 70, 0.44, 0.085), (-0.5, 50, 0.32, 0.07), (0.5, 47, 0.34, 0.072), (0.0, 32, 0.27, 0.062),
                  (-0.7, 22, 0.17, 0.05), (0.7, 24, 0.18, 0.05), (0.32, 60, 0.24, 0.055), (-0.3, 62, 0.22, 0.052))
        for k, (yaw, el, ln, r) in enumerate(spikes):
            e = math.radians(el)
            d = Vector((sg * math.cos(e) * math.cos(yaw), math.sin(yaw) * math.cos(e) * 0.9, math.sin(e))).normalized()
            loc, n = project(pb, pc0 + d * 1.0, -d)
            if loc is None or (loc - pc0).dot(d) < 0.05 or n.dot(d) < 0.3: continue
            tipd = (d * 0.6 + n * 0.4).normalized()
            base = loc - tipd * 0.04
            sp = prim_cone(f'IceSpike{s}{k}', base, base + tipd * (ln + 0.04), r, ('crystal', 'spike', 'crystal_d')[k % 3], n=5, flat=0.7)
            sp.bone = 'UpperTorso'; head_clear(sp, 0.03); P.append(sp)
    # ---- white boots ----
    for s in 'LR':
        b = shoe('Boot_' + s, s, off=0.05, bulk=0.035, toe=0.04, sole_h=0.05)
        def bp(U, V, m):
            img = P_solid(pal['white'])(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            return mix(img, aa(np.abs(z - (m['sole_top'] + 0.025)) * 300 - 2), pal['ice_d'])
        b.paint = bp; P.append(b)
        sg = 1 if s == 'L' else -1
        tip = min(b.verts, key=lambda p: p.y)
        g = Vector((0.255 * sg, tip.y + 0.06, 0.47))
        loc, n = project(piece_bvh(b), g, Vector((0, 1, 0.4)).normalized())
        if loc is not None:
            P.append(prim_cone(f'BootGem{s}', loc - n * 0.01, loc + n * 0.06, 0.035, 'crystal', n=4, group='Feet'))
    return P, pal
