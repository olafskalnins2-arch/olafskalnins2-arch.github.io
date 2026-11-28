from o04 import *
NUM, NAME, RARITY, MAXD = '43', 'Phoenix_Emperor', 'Legendary', 0.7


# ---------------------------------------------------------------- helpers (local to this skin)
def _hash(k, s=0.0):
    return (math.sin(k * 12.9898 + s * 78.233) * 43758.5453) % 1.0


def _flame_h(az, n, hmin, hmax, seed, z=None, wob=0.0):
    """height field of n flame tongues around the circumference (az in rad). Returns (height, local u in -1..1)."""
    a = az
    if z is not None and wob:
        a = az + wob * np.sin(z * 11.0 + az * 3.0 + seed)          # flickering, wavy tongues
    q = (a + PI) / (2 * PI) * n
    k = np.floor(q)
    u = (q - k) * 2 - 1                                             # -1..1 across one tongue
    hk = hmin + (hmax - hmin) * ((np.sin(k * 12.9898 + seed * 78.233) * 43758.5453) % 1.0)
    prof = np.clip(1 - np.abs(u), 0, 1) ** 1.6                      # pointed tongue
    return hk * prof, u


def _flames(img, z, az, z0, n, hmin, hmax, seed, cols, wob=0.07):
    """layered flame tongues rising from z0: gold outline, orange body, yellow core."""
    h, u = _flame_h(az, n, hmin, hmax, seed, z, wob)
    d = (z - z0) - h
    img = mix(img, aa(d * 300), cols[0])
    img = mix(img, aa((d + 0.035 + 0.25 * h) * 300) * (h > 0.08), cols[1])
    img = mix(img, aa((d + 0.07 + 0.5 * h) * 300) * (h > 0.15), cols[2])
    return img


def flame_feather(name, root, d, L, W, phase=0.0, curl=0.12, n=9, ncol=4, th=0.022, rect='Feather', group='Extras'):
    """flat flame-shaped feather blade (rigid). root: base point, d: direction along the feather (roughly in a plane
    facing backwards), L length, W max half-width. The tip flickers sideways like a flame."""
    d = d.normalized()
    s = Vector((0, 1, 0)).cross(d)
    if s.length < 1e-4: s = Vector((1, 0, 0))
    s.normalize()
    nrm = d.cross(s).normalized()
    if nrm.y < 0: nrm = -nrm; s = -s                        # outer face looks backwards
    rows = []; hints = []; vv = []
    for i in range(n + 1):
        t = i / n
        c = root + d * (L * t) + s * (curl * L * math.sin(PI * t * 1.3 + phase) * t) + nrm * (0.08 * L * t * t)
        w = W * (0.45 + 0.55 * math.sin(PI * min(1.0, t * 1.15)) ** 0.7) * (1 - t) ** 0.55
        w = max(w, 0.008)
        row = []
        for k in range(ncol + 1):
            u = -1 + 2 * k / ncol
            row.append(c + s * (w * u) + nrm * (0.25 * w * (1 - u * u)))
        rows.append(row); hints.append([nrm] * (ncol + 1)); vv.append(t)
    pc = grid_piece(name, rows, closed=False, v_vals=vv, hints=hints, group=group)
    thicken(pc, th)
    pc.rect_key = rect; pc.rigid = True; pc.bone = 'UpperTorso'
    return pc


def _grad(stops):
    """paint along V through colour stops [(v, '#hex'), ...] with a light centre vein across U."""
    def f(U, V, m):
        img = P_solid(stops[0][1])(U, V, m)
        for (v0, c0), (v1, c1) in zip(stops, stops[1:]):
            img = mix(img, np.clip((V - v0) / max(1e-6, v1 - v0), 0, 1), c1)
        vein = aa((np.abs(U - 0.5) - 0.03) * 400) * (V < 0.8)
        img = mix(img, vein * 0.6, '#fff1b0')
        img = mix(img, aa((0.47 - np.abs(U - 0.5)) * 300) * 0.35, '#7a0c15')   # darker rims
        return img
    return f


def build():
    pal = {'crim': '#b3121f', 'crim_d': '#7a0c15', 'crim_l': '#cf2a2f', 'gold': '#e0ad2a', 'gold_d': '#a8791a', 'gold_l': '#f5d26a',
           'fl_o': '#ff5a1f', 'fl_y': '#ffb21a', 'fl_l': '#ffd84a', 'ruby': '#d0102a', 'ruby_d': '#8e0a1c', 'trous': '#5e0a12',
           'sole': '#7a5410'}
    P = []
    FL = (pal['gold'], pal['fl_o'], pal['fl_l'])

    # ---- under layers: dark crimson trousers (seen when the slits open) ----
    legs = pants('Trousers', 2.15, 0.5, 0.03, hip_off=0.05, leg_extra=lambda z, a: 0.01)
    for p in legs: p.paint = P_solid(pal['trous'])

    # ---- the imperial robe: floor length A-line, front/back slit panels like the wizard ----
    def rex(z, a): return 0.012 + 0.18 * max(0, 2.12 - z) ** 1.1
    Z_HEM = 0.74
    robe = torso_shell('Robe', Z_HEM, 0.06, nseg=40, extra=rex, th=0.025, slits=RF_SLIT_TOP(), hang=2.3, over=legs)
    zmin_robe = robe.meta['zmin']

    def rrad(z): return 0.5 + (rex(z, 0) if z < 2.3 else 0.03)

    def rp(U, V, m):
        img = P_solid(pal['crim'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, np.clip((2.0 - z) / 1.3, 0, 1) * 0.55, pal['crim_d'])                   # deepens toward the hem
        img = mix(img, np.clip((z - 2.5) / 0.6, 0, 1) * 0.25, pal['crim_l'])
        if m.get('kind') == 'torso':
            # imperial brocade: tone-on-tone diamond lattice with tiny gold studs (fades out above the flames)
            gx = (az + PI) / (2 * PI) * 30; gz = z / 0.2
            la = np.minimum(np.abs(np.mod(gx + gz, 1.0) - 0.5), np.abs(np.mod(gx - gz, 1.0) - 0.5))
            img = mix(img, aa((0.5 - la) * 60 - 26) * 0.55 * (z > 1.0), pal['crim_d'])
            cx = np.mod(gx, 1.0) - 0.5; cz = np.mod(gz + 0.5, 1.0) - 0.5
            dot = np.sqrt((cx * 2 * PI * 0.52 / 30) ** 2 + (cz * 0.2) ** 2)
            img = mix(img, aa((dot - 0.012) * 900) * (z > 1.0), pal['gold'])
            # imperial front panel with double gold piping
            pw = 0.15 + 0.1 * np.clip((2.3 - z) / 1.5, 0, 1)
            img = mix(img, aa((np.abs(az) - pw) * 300) * (z < 3.0), pal['crim_d'])
            for o in (0.0, 0.035):
                img = mix(img, aa(np.abs(np.abs(az) - pw - o) * 300 - 1.4) * (z < 3.0), pal['gold'])
            # gold phoenix-tail chevrons down the front panel
            for zc0 in (2.85, 2.65, 1.75, 1.45, 1.15):
                ch = (z - zc0) - np.abs(az) * 0.9
                img = mix(img, aa(np.abs(ch) * 300 - 1.6) * (np.abs(az) < pw - 0.03), pal['gold'])
            # big flames rising from the hem (gold outline, orange body, yellow core) + low secondary licks
            img = _flames(img, z, az, zmin_robe + 0.12, 16, 0.25, 0.75, 1.7, FL)
            img = _flames(img, z, az + PI / 16, zmin_robe + 0.12, 16, 0.12, 0.32, 4.1, FL)
            img = mix(img, aa(np.abs(z - (zmin_robe + 0.13)) * 300 - 1.5), pal['gold_l'])
            img = mix(img, aa(np.abs(z - 3.03) * 300 - 1.6) * 0.9, pal['gold'])                  # neckline trim
            img = mix(img, aa(np.abs(z - 2.36) * 300 - 1.2), pal['gold_d'])                      # above the sash
        return img
    robe.paint = rp; P.append(robe)
    P += legs

    # gold hem band with the SAME slit panels, sitting on the robe hem
    hem = torso_shell('HemBand', Z_HEM - 0.04, 0.06, nseg=40, zs=[Z_HEM - 0.04, Z_HEM + 0.04, Z_HEM + 0.11], elevs=(),
                      extra=rex, th=0.03, slits=RF_SLIT_TOP(), hang=Z_HEM + 0.111, over=[robe], over_gap=0.035)
    def hemp(U, V, m):
        img = P_solid(pal['gold'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, (0.5 + 0.5 * np.cos(az * 40)) * 0.3, pal['gold_l'])
        img = mix(img, aa(np.minimum(V - 0.12, 0.88 - V) * -300), pal['gold_d'])
        # ruby lozenges
        q = np.mod((az + PI) / (2 * PI) * 20, 1.0) - 0.5
        img = mix(img, aa((np.abs(q) * 0.33 + np.abs(V - 0.5) * 0.5 - 0.12) * 300), pal['ruby'])
        return img
    hem.paint = hemp; hem.rect_key = 'HemBand'; P.append(hem)

    # ---- bell sleeves with flame tongues and gold cuffs ----
    def sex(t, a): return 0.012 + 0.2 * max(0, t - 0.22) ** 1.3
    T_SL = 0.62
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, T_SL, 0.06, extra=sex)
        def spaint(U, V, m):
            img = P_solid(pal['crim'])(U, V, m)
            img = mix(img, np.clip((V - 0.3) / 0.7, 0, 1) * 0.5, pal['crim_d'])
            az = 2 * PI * (U - 0.5)
            h, u = _flame_h(az, 9, 0.18, 0.45, 2.3, V, 0.15)
            d = (1.0 - V) - h
            img = mix(img, aa(d * 120), pal['gold'])
            img = mix(img, aa((d + 0.04 + 0.25 * h) * 120) * (h > 0.08), pal['fl_o'])
            img = mix(img, aa((d + 0.08 + 0.5 * h) * 120) * (h > 0.15), pal['fl_l'])
            return img
        sl.paint = spaint; sl.weight = 'nearest'; P.append(sl)
        cf = sleeve('SleeveCuff_' + s, s, T_SL - 0.06, T_SL + 0.01, 0.06, nrows=3, cap=False,
                    extra=lambda t, a: sex(t, a) + 0.03, th=0.03)
        cf.paint = lambda U, V, m: mix(P_solid(pal['gold'])(U, V, m), aa(np.abs(V - 0.5) * 300 - 6), pal['gold_d'])
        cf.rect_key = 'SleeveCuff'; P.append(cf)
        # gold bracers on the forearm (below the bell sleeve)
        br = sleeve('Bracer_' + s, s, 0.6, 0.95, 0.05, nrows=7, cap=False,
                    extra=lambda t, a: 0.012 + 0.025 * max(0, (t - 0.85) / 0.1), th=0.025)
        def brp(U, V, m):
            img = P_solid(pal['gold'])(U, V, m)
            az = 2 * PI * (U - 0.5)
            img = mix(img, (0.5 + 0.5 * np.cos(az * 3)) * 0.4, pal['gold_l'])
            img = mix(img, (0.5 - 0.5 * np.cos(az * 3)) * 0.25, pal['gold_d'])
            for L in (0.08, 0.92):
                img = mix(img, aa(np.abs(V - L) * 300 - 2), pal['gold_d'])
            # engraved flame
            h, u = _flame_h(az, 6, 0.3, 0.6, 5.0, V, 0.12)
            d = (0.88 - V) - h
            img = mix(img, aa(np.abs(d) * 200 - 1.5) * (V < 0.88), pal['ruby_d'])
            return img
        br.paint = brp; br.rect_key = 'Bracer'; br.sharp = True; P.append(br)
        c, tg = arm_point(s, 0.78)
        nfr, bfr = frame(tg, Vector((0, -1, 0)))
        bb = piece_bvh(br)
        for k, dv in enumerate((-nfr, Vector((1 if s == 'L' else -1, 0, 0)))):
            dv = (dv - tg * dv.dot(tg)).normalized()
            loc, n = project(bb, c + dv * 0.5, -dv)
            if loc is None: continue
            g = prim_sphere(f'BracerGem{s}{k}', loc + n * 0.012, 0.04, 'ruby', nl=4, seg=8, scale=(1, 1, 1))
            g.region = 'arm_' + s; P.append(g)
            mnt = prim_cyl(f'BracerMount{s}{k}', loc - n * 0.01, loc + n * 0.015, 0.058, n=10, col='gold_d')
            mnt.region = 'arm_' + s; P.append(mnt)

    # ---- gold phoenix collar: stand collar + a ruff of small gold feathers around the back and sides ----
    col = collar('PhoenixCollar', 'stand', h=0.09, flare=0.08, th=0.03)
    def colp(U, V, m):
        img = P_solid(pal['gold'])(U, V, m)
        # feather scale pattern
        q = np.mod(U * 24, 1.0) - 0.5
        sc = np.sqrt(q ** 2 + (np.mod(V * 2 + 0.5 * (np.floor(U * 24) % 2), 1.0) - 0.9) ** 2)
        img = mix(img, aa((np.abs(sc - 0.45) - 0.05) * 60), pal['gold_d'])
        return mix(img, aa((0.85 - V) * -300), pal['gold_l'])
    col.paint = colp; P.append(col)
    for k in range(11):
        az = math.radians(62 + (360 - 124) * k / 10)
        e = math.radians(24 + 6 * math.sin(k * 1.7))
        dh = Vector((math.sin(az), -math.cos(az), 0))
        root = Vector((0, 0, 3.22)) + dh * 0.28
        d = dh * math.cos(e) + Vector((0, 0, math.sin(e)))
        ff = flame_feather(f'CollarFeather{k}', root, d, 0.27 + 0.04 * (k % 2), 0.06, phase=k * 0.9, curl=0.08, n=6, ncol=2,
                           th=0.02, rect='CollarFeather')
        ff.paint = _grad([(0.0, pal['gold_d']), (0.45, pal['gold']), (1.0, pal['fl_l'])])
        head_clear(ff, 0.035); P.append(ff)
    # ruby pendant on the front of the collar
    rb = piece_bvh(robe)
    loc, n = project(rb, Vector((0, 0, 2.98)), Vector((0, 1, 0)))
    pc0 = loc + n * 0.03
    P.append(prim_cyl('PendantMount', loc - n * 0.01, loc + n * 0.03, 0.1, n=14, col='gold'))
    P.append(prim_sphere('PendantGem', pc0 + n * 0.01, 0.06, 'ruby', nl=5, seg=10, scale=(1, 0.6, 1.2)))
    for k in range(5):
        a = -PI / 2 + (k - 2) * 0.55
        dv = Vector((math.cos(a), 0, math.sin(a)))
        b0 = pc0 + dv * 0.08
        P.append(prim_cone(f'PendantRay{k}', b0, b0 + dv * 0.1 + n * 0.0, 0.028, 'fl_y' if k % 2 else 'gold', n=4, flat=0.5))
    for q in P[-7:]: q.bone = 'UpperTorso'; head_clear(q, 0.03)

    # ---- gold sash fitted on the robe, phoenix sun buckle, short tails on the left hip ----
    sash = band('Sash', 2.12, 2.32, 0.012, th=0.02, bvh=piece_bvh(robe))
    def sashp(U, V, m):
        img = P_solid(pal['gold'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, (0.5 + 0.5 * np.cos(az * 6)) * 0.3, pal['gold_l'])
        img = mix(img, aa(np.minimum(V - 0.12, 0.88 - V) * -300), pal['gold_d'])
        q = np.mod((az + PI) / (2 * PI) * 28, 1.0)
        zig = np.abs(V - 0.5 - 0.18 * (np.abs(q - 0.5) * 2 - 0.5))
        img = mix(img, aa(zig * 300 - 2), pal['crim'])
        return img
    sash.paint = sashp; P.append(sash)
    sb = piece_bvh(sash)
    loc, n = project(sb, Vector((0, 0, 2.22)), Vector((0, 1, 0)))
    bc = loc + n * 0.025
    nb = len(P)
    P.append(prim_cyl('SashBuckle', loc - n * 0.005, loc + n * 0.045, 0.14, n=16, col='gold_d'))
    P.append(prim_cyl('SashBuckleFace', loc + n * 0.04, loc + n * 0.055, 0.115, n=16, col='gold'))
    P.append(prim_sphere('SashGem', loc + n * 0.065, 0.05, 'ruby', nl=5, seg=10, scale=(1, 0.55, 1)))
    for k in range(8):
        a = 2 * PI * k / 8 + PI / 8
        dv = Vector((math.cos(a), 0, math.sin(a)))
        b0 = loc + n * 0.03 + dv * 0.13
        P.append(prim_cone(f'BuckleRay{k}', b0, b0 + dv * (0.1 if k % 2 else 0.07), 0.035, 'fl_o' if k % 2 else 'fl_y', n=4, flat=0.45))
    loc2, n2 = project(sb, Vector((0.36, 0, 2.22)), Vector((0, 1, 0)))
    tc = loc2 + n2 * 0.03
    P.append(prim_rbox('SashKnot', tc, (0.12, 0.07, 0.11), 'gold'))
    for k, (dx, ln) in enumerate(((-0.03, 0.17), (0.04, 0.14))):
        a = tc + Vector((dx, -0.01, -0.04)); b = a + Vector((dx * 0.6, -0.012, -ln))
        P.append(tube_path(f'SashTail{k}', [a, (a + b) / 2 + Vector((0, -0.01, 0)), b], 0.028, 'gold', n=6,
                           rfn=lambda t: 0.028 + 0.012 * t))
        P.append(prim_cone(f'SashTailFlame{k}', b + Vector((0, 0, 0.01)), b + Vector((0, -0.01, -0.09)), 0.034, 'fl_o', n=5, flat=0.6))
    for q in P[nb:]: q.bone = 'LowerTorso'

    # ---- phoenix wings: a fan of rigid flame feathers behind the shoulders (UpperTorso) ----
    loc, n = project(rb, Vector((0, 0, 2.8)), Vector((0, -1, 0)))
    mc = loc + Vector((0, 0.02, 0))
    nm = len(P)
    P.append(prim_cyl('WingMount', mc - Vector((0, 0.03, 0)), mc + Vector((0, 0.07, 0)), 0.2, n=16, col='gold_d'))
    P.append(prim_cyl('WingMountFace', mc + Vector((0, 0.065, 0)), mc + Vector((0, 0.085, 0)), 0.16, n=16, col='gold'))
    P.append(prim_sphere('WingGem', mc + Vector((0, 0.1, 0)), 0.07, 'ruby', nl=5, seg=10, scale=(1, 0.55, 1)))
    for q in P[nm:]: q.bone = 'UpperTorso'
    grad_long = _grad([(0.0, pal['crim']), (0.18, pal['fl_o']), (0.62, pal['fl_y']), (1.0, pal['fl_l'])])
    grad_mid = _grad([(0.0, pal['fl_o']), (0.5, pal['fl_y']), (1.0, '#fff0a0')])
    grad_short = _grad([(0.0, pal['gold_d']), (0.35, pal['gold']), (1.0, pal['fl_l'])])
    layers = (   # (angles from horizontal, length, half width, y offset, paint, rect)
        ((6, 20, 34, 48, 62, 76), (1.6, 1.85, 1.95, 1.9, 1.72, 1.48), 0.15, 0.00, grad_long, 'FeatherLong'),
        ((13, 27, 41, 55, 69), (1.25, 1.42, 1.48, 1.38, 1.2), 0.13, 0.05, grad_mid, 'FeatherMid'),
        ((20, 36, 52, 68), (0.82, 0.9, 0.9, 0.82), 0.1, 0.10, grad_short, 'FeatherShort'),
    )
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        for li, (angs, lens, w, yo, paint, rect) in enumerate(layers):
            for k, (th_, L) in enumerate(zip(angs, lens)):
                t = math.radians(th_)
                d = Vector((sg * math.cos(t), 0.2, math.sin(t)))
                root = mc + Vector((sg * 0.06, 0.04 + yo, 0.04))
                ff = flame_feather(f'Wing{s}{li}{k}', root, d, L, w, phase=k * 1.3 + li, curl=0.1 * sg, rect=rect)
                ff.paint = paint
                head_clear(ff, 0.04)
                P.append(ff)

    # ---- gold slippers with curled flame toes ----
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Slipper_' + s, s, off=0.045, bulk=0.025, toe=0.06, sole_h=0.04, open_elev=44)
        def shp(U, V, m):
            img = P_solid(pal['gold'])(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            img = mix(img, aa(np.abs(z - (m['sole_top'] + 0.03)) * 300 - 2), pal['crim'])
            return img
        sh.paint = shp; P.append(sh)
        tip = min(sh.verts, key=lambda p: p.y)
        tip = Vector((tip.x, tip.y + 0.04, 0.40))
        pts = []
        for k in range(10):
            f = k / 9
            ang = f * 1.4 * PI
            rad = 0.08 * (1 - 0.5 * f)
            cc = tip + Vector((0, -0.03, 0.08))
            pts.append(cc + Vector((0, -math.sin(ang) * rad, -math.cos(ang) * rad)))
        cu = tube_path('ToeCurl_' + s, pts, 0.045, 'gold', n=7, group='Feet', rfn=lambda t: 0.048 * (1 - 0.8 * t))
        cu.rigid = True; P.append(cu)
        loc, n = project(piece_bvh(sh), Vector((0.255 * sg, tip.y + 0.12, 0.5)), Vector((0, 1, 0.5)).normalized())
        if loc is not None:
            P.append(prim_sphere(f'SlipperGem{s}', loc + n * 0.01, 0.035, 'ruby', nl=4, seg=8, group='Feet', scale=(1, 0.6, 1)))
    return P, pal
