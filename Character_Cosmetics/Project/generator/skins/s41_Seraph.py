from o04 import *
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '41', 'Seraph', 'Legendary', 0.7

# Seraph: radiant white floor-length A-line robe (soft folds, slit panels like the wizard), gold embroidered trim, a
# sculpted gold hem band, gold sash with a winged medallion, gold collar + brooch, layered gold shoulder guards, gold
# arm bands and bracers, huge layered feathered angel wings spread behind (rigid on UpperTorso, clear of the arms),
# gold gladiator sandals with little ankle wings.

WHITE, CREAM, GOLD, GOLD_D, SHADOW = '#fbf8f0', '#efe9d8', '#e4b84a', '#c99a2e', '#d8c79a'
GOLD_L = '#f6dc8a'
PEARL = '#fffaf0'


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _az(p):
    return math.atan2(p.x, -p.y)          # 0 = front, +pi/2 = character left (+X)


def _sm(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


NF = 14   # robe folds around


def _folds(pc, z_top, z_full, amp):
    """soft vertical folds below the waist: outward-only radial push (never sinks into the layer below)"""
    for i, p in enumerate(pc.verts):
        if p.z >= z_top: continue
        k = _sm(z_top, z_full, p.z)
        h = Vector((p.x, p.y, 0))
        if h.length < 1e-6: continue
        f = 0.5 - 0.5 * math.cos(NF * _az(p))
        pc.verts[i] = p + h.normalized() * (amp * f * k)


def _open_dome(name, side, center, off, elevs, nseg=15, half=1.75, extra=None, th=0.022):
    """part of a shoulder dome that only covers the OUTER side of the shoulder (an arc of +-half rad around the
    outward direction, front to back) - a full ring would cut across the chest and back."""
    sg = 1 if side == 'L' else -1
    bv = side_bvh(side)
    ths = [sg * PI / 2 + half * (2 * j / (nseg - 1) - 1) for j in range(nseg)]
    D = [Vector((math.sin(t), -math.cos(t), 0)) for t in ths]
    rows = []; hints = []
    for e in elevs:
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        ex = (lambda j, p, e=e: extra(e, ths[j])) if extra else None
        rows.append(ray_ring(bv, center, dirs, off, R=0.9, extra=ex, smooth=0)); hints.append(dirs)
    pc = _grid_with_ij(name, rows, False, [i / (len(rows) - 1) for i in range(len(rows))], hints, 'Top')
    pc.meta.update(circ=1.6)
    thicken(pc, th)
    return pc


# ---------------- feathers ----------------
FEATHER_PROF = ([0.0, 0.14, 0.34, 0.55, 0.75, 0.9, 1.0], [0.38, 0.82, 1.0, 1.0, 0.9, 0.62, 0.14])
COVERT_PROF = ([0.0, 0.3, 0.62, 0.88, 1.0], [0.5, 0.95, 1.0, 0.72, 0.2])


def _feather(name, mapf, hint, root, ang, L, wd, layer, prof, paint, rkey, sgn=1, ridge=0.0055, th=0.005):
    """flat feather in the wing plane: root (s, h), direction ang (rad, in plane), mapped to 3D by mapf(s, h, l)"""
    d = (math.cos(ang), math.sin(ang)); q = (-math.sin(ang), math.cos(ang))
    ts, ws = prof
    rows = []
    for t, wf in zip(ts, ws):
        cs = root[0] + d[0] * L * t; ch = root[1] + d[1] * L * t
        hw = wd * 0.5 * wf
        row = []
        for k in (-1, 0, 1):
            l = layer + sgn * (ridge * (1 - 0.6 * t) if k == 0 else 0.0)
            row.append(mapf(cs + q[0] * hw * k, ch + q[1] * hw * k, l))
        rows.append(row)
    hv = hint * sgn
    pc = grid_piece(name, rows, closed=False, v_vals=list(ts), hints=[[hv] * 3 for _ in rows], group='Extras')
    thicken(pc, th)
    pc.rigid = True; pc.bone = 'UpperTorso'
    pc.paint = paint; pc.rect_key = rkey; pc.meta['rect'] = (64, 256)
    head_clear(pc, 0.03)
    return pc


def _fpaint(base, tip, shaft, edge=None, edge_from=0.55, shaft_col=None):
    def f(U, V, m):
        img = P_solid(tip)(U, V, m)
        img = mix(img, np.clip((0.5 - V) / 0.5, 0, 1) ** 1.3 * 0.9, base)        # warmer toward the root
        du = np.abs(U - 0.5)
        barbs = np.sin((du * 2.4 - V * 0.9) * 2 * PI * 7)                         # fine chevron barbs
        img = mix(img, np.clip(barbs - 0.55, 0, 1) * 0.55, shaft)
        img = mix(img, np.clip(du - 0.36, 0, 1) * 4.0 * 0.5, shaft)                # soft shading toward the vane edge
        img = mix(img, aa((du - 0.03 * (1 - 0.6 * V)) * 900), shaft_col or shaft)  # rachis (shaft)
        if edge:
            img = mix(img, aa((0.44 - du) * 700) * (V > edge_from), edge)
            img = mix(img, aa((V - 0.965) * -700) * 1.0, edge)                      # tip edge
        return img
    return f


def _wing(sg, P):
    """one huge spread wing; character left = +X (sg=+1)"""
    beta = math.radians(33)
    A = Vector((0.24 * sg, 0.52, 2.78))
    S = 1.1
    o = Vector((sg * math.cos(beta), math.sin(beta), 0))
    nb = Vector((-sg * math.sin(beta), math.cos(beta), 0))           # wing plane normal, pointing back
    tilt, curl = 0.22, 0.07

    def mapf(s, h, l):
        return A + o * (s * S) + Z * (h * S) + nb * (l + tilt * max(0.0, -h) * S - curl * (s * S) ** 2)

    s_ = 'L' if sg > 0 else 'R'
    # leading edge (the wing's arm): shoulder -> elbow -> wrist -> hand tip
    arm = [(0.0, 0.06), (0.22, 0.3), (0.48, 0.52), (0.74, 0.68), (0.97, 0.78), (1.17, 0.79), (1.36, 0.74)]
    def arm_at(g):
        L = [0.0]
        for a, b in zip(arm, arm[1:]): L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        x = g * L[-1]
        for i in range(len(arm) - 1):
            if x <= L[i + 1] or i == len(arm) - 2:
                f = (x - L[i]) / max(L[i + 1] - L[i], 1e-9)
                return (arm[i][0] + (arm[i + 1][0] - arm[i][0]) * f, arm[i][1] + (arm[i + 1][1] - arm[i][1]) * f)
    g_wrist = 0.68
    lerp = lambda a, b, f: a + (b - a) * f
    pw = _fpaint(SHADOW, WHITE, '#e6dcc0', edge=GOLD, edge_from=0.72, shaft_col=GOLD)     # gold-tipped primaries
    sw = _fpaint(SHADOW, WHITE, '#e6dcc0')
    gw = _fpaint(SHADOW, WHITE, '#e8dec4')
    lw = _fpaint(CREAM, WHITE, SHADOW, edge=GOLD_L, edge_from=0.5)
    vw = _fpaint(SHADOW, CREAM, '#e2d6b6')
    step = 0.0065
    # secondaries: hang from the arm between shoulder and wrist (inner first)
    n2 = 11
    for k in range(n2):
        f = k / (n2 - 1)
        r = arm_at(lerp(0.04, g_wrist - 0.02, f))
        ang = math.radians(lerp(-97, -63, f))
        L = lerp(0.74, 0.96, f ** 0.8)
        P.append(_feather(f'Sec{s_}{k}', mapf, nb, r, ang, L, 0.22, 0.012 + step * k, FEATHER_PROF, sw, 'FeatherSec'))
    # primaries: fan out from the hand (wrist -> tip), outermost pointing out and a little up
    n1 = 10
    Ls = [0.93, 1.02, 1.05, 1.03, 0.99, 0.95, 0.92, 0.89, 0.87, 0.86]
    for k in range(n1):
        f = k / (n1 - 1)                                  # 0 = tip, 1 = wrist
        r = arm_at(lerp(0.995, g_wrist + 0.02, f))
        ang = math.radians(lerp(16, -58, f))
        P.append(_feather(f'Pri{s_}{k}', mapf, nb, r, ang, Ls[k], 0.19, 0.012 + step * (n2 + 1 + (n1 - 1 - k)), FEATHER_PROF, pw, 'FeatherPri'))
    top = 0.012 + step * (n2 + n1 + 3)
    # greater coverts (back side): cover the roots of the flight feathers
    n3 = 12
    for k in range(n3):
        f = k / (n3 - 1)
        g = lerp(0.03, 0.97, f)
        r = arm_at(g); r = (r[0], r[1] - 0.02)
        ang = math.radians(lerp(-95, -64, f / g_wrist) if g < g_wrist else lerp(-62, -12, (g - g_wrist) / (1 - g_wrist)))
        L = lerp(0.42, 0.52, f)
        P.append(_feather(f'GCov{s_}{k}', mapf, nb, r, ang, L, 0.2, top + step * k, COVERT_PROF, gw, 'FeatherCov'))
    top2 = top + step * (n3 + 1)
    # lesser coverts (back side): small gold-edged feathers along the leading edge
    n4 = 10
    for k in range(n4):
        f = k / (n4 - 1)
        g = lerp(0.02, 0.92, f)
        r = arm_at(g); r = (r[0], r[1] + 0.03)
        ang = math.radians(lerp(-92, -66, f / g_wrist) if g < g_wrist else lerp(-62, -30, (g - g_wrist) / (1 - g_wrist)))
        P.append(_feather(f'LCov{s_}{k}', mapf, nb, r, ang, lerp(0.27, 0.3, f), 0.17, top2 + step * k, COVERT_PROF, lw, 'FeatherLes'))
    # under-wing coverts (front side, seen from the front)
    n5 = 10
    for k in range(n5):
        f = k / (n5 - 1)
        g = lerp(0.04, 0.95, f)
        r = arm_at(g); r = (r[0], r[1] - 0.01)
        ang = math.radians(lerp(-95, -64, f / g_wrist) if g < g_wrist else lerp(-62, -20, (g - g_wrist) / (1 - g_wrist)))
        P.append(_feather(f'VCov{s_}{k}', mapf, nb, r, ang, lerp(0.38, 0.46, f), 0.2, -0.012 - step * k, COVERT_PROF, vw, 'FeatherVen', sgn=-1))
    # the wing's arm: a soft white tube along the leading edge, rooted on the back mount
    pts = [mapf(s, h + 0.02, (top2 - 0.02) * 0.5) for s, h in arm]
    pts = smooth_line(polyline_resample(pts, 12), 2)
    rmax = (top2 + 0.03) * 0.5 + 0.02
    tb = tube_path(f'WingArm{s_}', pts, rmax, 'wing', n=8, group='Extras', rfn=lambda t: rmax * (1 - 0.55 * t) + 0.012)
    tb.rigid = True; tb.bone = 'UpperTorso'; head_clear(tb, 0.03); P.append(tb)
    return mapf


def build():
    pal = {'white': WHITE, 'cream': CREAM, 'gold': GOLD, 'gold_d': GOLD_D, 'gold_l': GOLD_L, 'shadow': SHADOW,
           'wing': '#f7f2e6', 'pearl': PEARL}
    P = []
    # ---------------- under layer: bare legs (seen when the slits open) ----------------
    legs = [skin_leg(s, 1.9, 0.47) for s in 'LR']

    # ---------------- the robe: floor-length A-line, slit panels like the wizard ----------------
    Z_HEM = 0.82

    def rex(z, a): return 0.01 + 0.17 * max(0, 2.1 - z) ** 1.1
    robe = torso_shell('Robe', Z_HEM, 0.06, nseg=40, extra=rex, th=0.025, slits=RF_SLIT_TOP(), hang=2.3, over=legs)

    EMB = [(sg * a, ln, sg * tl) for sg in (1, -1) for a, ln, tl in ((0.62, 0.62, 0.05), (1.3, 0.7, -0.04), (2.0, 0.66, 0.05), (2.72, 0.6, -0.04))]

    def rp(U, V, m):
        img = P_solid(WHITE)(U, V, m); z, az = zc(U, V, m)
        kf = np.clip((2.0 - z) / 0.8, 0, 1)
        img = mix(img, (0.5 + 0.5 * np.cos(NF * az)) * kf * 0.75, CREAM)                 # fold shading (valleys)
        img = mix(img, np.clip((z - 2.6) / 0.5, 0, 1) * 0.18, '#fffdf8')                  # radiant shoulders
        if m.get('kind') == 'torso':
            # front panel: double gold border lines + a column of gold diamonds
            pwid = 0.15 + 0.1 * np.clip((2.2 - z) / 1.4, 0, 1)
            fr = z < 3.02
            img = mix(img, aa((np.abs(az) - pwid) * 300) * fr * 0.55, CREAM)
            img = mix(img, aa(np.abs(np.abs(az) - pwid) * 300 - 2.2) * fr, GOLD)
            img = mix(img, aa(np.abs(np.abs(az) - pwid - 0.035) * 300 - 1.0) * fr, GOLD_D)
            per = 0.2
            zz = np.mod(z - 0.95, per) - per / 2
            dia = np.abs(az) / 0.07 + np.abs(zz) / 0.065
            img = mix(img, aa((dia - 1.0) * 6) * (z < 2.05) * (z > 0.98), GOLD)
            img = mix(img, aa((dia - 0.45) * 6) * (z < 2.05) * (z > 0.98), PEARL)
            # hem: wide gold band with a running scallop (feather) pattern
            z0 = m['zmin']
            img = mix(img, aa(np.maximum(z0 + 0.13 - z, z - (z0 + 0.26)) * 500), GOLD)
            sc = np.mod(az * 24 / (2 * PI), 1.0) - 0.5
            arc = np.hypot(sc * 0.18, (z - (z0 + 0.155)) * 1.0)
            img = mix(img, aa(np.abs(arc - 0.06) * 600 - 1.2) * (z > z0 + 0.135) * (z < z0 + 0.255), GOLD_D)
            img = mix(img, aa(np.abs(z - (z0 + 0.3)) * 400 - 1.4), GOLD)
            # embroidered gold feathers rising from the hem (sides and back; the front has the diamond column)
            for a0, ln, tl in EMB:
                zb = z0 + 0.34
                da = np.mod(az - a0 + PI, 2 * PI) - PI
                if not (np.abs(da) < 0.4).any(): continue
                x = da * (0.5 + rex(zb + ln * 0.5, 0))
                u = (z - zb) / ln
                xs = x - tl * np.clip(u, 0, 1) * ln
                ins = ((u > 0) & (u < 1)).astype(float)
                uc = np.clip(u, 0, 1)
                hw = 0.075 * np.sin(PI * uc) ** 0.6 * (1 - 0.35 * uc)
                img = mix(img, aa((np.abs(xs) - hw) * 180) * ins * 0.35, '#f4e6bf')
                img = mix(img, aa(np.abs(np.abs(xs) - hw) * 180 - 0.9) * ins, GOLD)
                img = mix(img, aa(np.abs(xs) * 180 - 0.7) * ins * (u < 0.97), GOLD_D)
                barbs = np.sin((np.abs(xs) - uc * ln * 0.5) * 2 * PI / 0.045)
                img = mix(img, np.clip(barbs - 0.55, 0, 1) * 2.0 * (np.abs(xs) < hw - 0.01) * ins * 0.6, GOLD)
            # scalloped yoke on the chest / back
            yz = 2.76 + 0.04 * np.abs(np.cos(az * 5))
            img = mix(img, aa((yz - z) * 300) * 0.35 * (z < 3.0), '#f4e6bf')
            img = mix(img, aa(np.abs(z - yz) * 300 - 1.6), GOLD)
            # neckline trim
            img = mix(img, aa(np.abs(z - 3.03) * 300 - 2.2), GOLD)
            img = mix(img, aa(np.abs(z - 2.96) * 300 - 1.0) * 0.9, GOLD_D)
        return img
    robe.paint = rp; P.append(robe)
    P += legs
    # sculpted gold hem band (same slit panels), sitting on the robe hem
    hem = torso_shell('HemBand', Z_HEM - 0.04, 0.06, nseg=40, zs=[Z_HEM - 0.04, Z_HEM + 0.03, Z_HEM + 0.1], elevs=(),
                      extra=rex, th=0.03, slits=RF_SLIT_TOP(), hang=Z_HEM + 0.101, over=[robe], over_gap=0.03, group='Bottom')
    def hemp(U, V, m):
        img = P_solid(GOLD)(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(V - 0.5) - 0.38) * -400), GOLD_D)
        sc = np.mod(az * 30 / (2 * PI), 1.0) - 0.5
        img = mix(img, aa((np.abs(sc) * 0.6 + np.abs(V - 0.5) * 0.35 - 0.1) * 600), GOLD_L)          # diamonds
        img = mix(img, aa((np.abs(sc) * 0.6 + np.abs(V - 0.5) * 0.35 - 0.045) * 600), PEARL)
        return img
    hem.paint = hemp; P.append(hem)

    # ---------------- gold collar + brooch ----------------
    col = collar('Collar', 'stand', h=0.06, flare=0.06, th=0.022)
    col.paint = metal_paint(base=GOLD, dark=GOLD_D, light=GOLD_L, lines=()); col.meta.update(circ=1.6, length=0.12)
    P.append(col)
    rb = piece_bvh(robe)
    loc, n = project(rb, Vector((0, 0, 2.9)), Vector((0, 1, 0)))
    bc = loc + n * 0.03
    P.append(prim_cyl('BroochDisc', bc - n * 0.02, bc + n * 0.02, 0.085, n=14, col='gold', group='Top'))
    P.append(prim_cyl('BroochRim', bc + n * 0.015, bc + n * 0.03, 0.06, n=14, col='gold_d', group='Top'))
    P.append(prim_sphere('BroochPearl', bc + n * 0.035, 0.038, 'pearl', nl=5, seg=8, group='Top'))
    for k in range(8):
        a = k * PI / 4
        dv = Vector((math.cos(a), 0, math.sin(a)))
        P.append(prim_cone(f'BroochRay{k}', bc + dv * 0.07 + n * 0.005, bc + dv * (0.13 if k % 2 == 0 else 0.105) + n * 0.005,
                           0.022, 'gold', n=4, flat=0.4, group='Top'))
    for q in P[-11:]: q.bone = 'UpperTorso'; head_clear(q, 0.03)

    # ---------------- bell sleeves, gold arm bands and bracers ----------------
    def sex(t, a): return 0.01 + 0.24 * max(0, t - 0.12) ** 1.4
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.55, 0.06, extra=sex)
        def sp(U, V, m):
            img = P_solid(WHITE)(U, V, m)
            img = mix(img, (0.5 + 0.5 * np.cos(U * 2 * PI * 6)) * np.clip((V - 0.45) / 0.5, 0, 1) * 0.6, CREAM)
            img = mix(img, aa((0.9 - V) * 500), GOLD)
            img = mix(img, aa(np.abs(V - 0.84) * 500 - 1.2), GOLD_D)
            return img
        sl.paint = sp; sl.weight = 'nearest'; P.append(sl)
        ab = sleeve('ArmBand_' + s, s, 0.3, 0.38, 0.06, nrows=3, cap=False, th=0.022, extra=lambda t, a: sex(t, a) + 0.028)
        def abp(U, V, m):
            img = P_solid(GOLD)(U, V, m)
            img = mix(img, aa((np.abs(V - 0.5) - 0.36) * -400), GOLD_D)
            sc = np.mod(U * 10, 1.0) - 0.5
            img = mix(img, aa((np.hypot(sc * 0.5, (V - 0.5) * 0.25) - 0.06) * 600), PEARL)
            return img
        ab.paint = abp; ab.rect_key = 'ArmBand'; P.append(ab)
        br = sleeve('Bracer_' + s, s, 0.72, 0.9, 0.032, nrows=4, cap=False, th=0.022,
                    extra=lambda t, a: 0.006 + 0.03 * max(0, (0.78 - t) / 0.06))
        def brp(U, V, m):
            img = P_solid(GOLD)(U, V, m)
            img = mix(img, (0.5 + 0.5 * np.cos(U * 2 * PI * 3)) * 0.35, GOLD_L)
            img = mix(img, aa((np.abs(V - 0.5) - 0.4) * -400), GOLD_D)
            # engraved feather chevrons
            sc = np.mod(U * 8, 1.0) - 0.5
            img = mix(img, aa(np.abs(np.abs(sc) * 0.7 - (V - 0.5) * 0.6 - 0.05) * 500 - 1) * (np.abs(V - 0.5) < 0.33), GOLD_D)
            return img
        br.paint = brp; br.rect_key = 'Bracer'; P.append(br)

    # ---------------- layered gold shoulder guards ----------------
    gold_m = metal_paint(base=GOLD, dark=GOLD_D, light=GOLD_L, lines=(0.2, 0.42))
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        c0 = Vector((0.58 * sg, 0.0, 2.86))
        pd = _open_dome('ShoulderGuard_' + s, s, c0, 0.1, (-26, -10, 8, 26, 44, 62, 78, 88), half=1.62, th=0.026, extra=lambda e, a: 0.06 * max(0, (12 - e) / 38))
        pd.paint = gold_m; pd.meta.update(circ=1.6); pd.rect_key = 'ShoulderGuard'; pd.bone = 'UpperTorso'
        head_clear(pd, 0.03); P.append(pd)
        for k, (off, el) in enumerate(((0.135, (-40, -27, -14)), (0.165, (-50, -40, -30)))):
            lm = _open_dome(f'GuardLame{k}_' + s, s, c0, off, el, extra=lambda e, a: 0.03)
            lm.paint = metal_paint(base=GOLD_D if k else GOLD, dark=GOLD_D, light=GOLD_L, lines=(0.5,))
            lm.rect_key = f'GuardLame{k}'; lm.bone = 'UpperTorso'; head_clear(lm, 0.03); P.append(lm)
        pb = piece_bvh(pd)
        d = Vector((sg * 0.75, -0.25, 0.6)).normalized()
        loc, n = project(pb, c0 + d * 1.0, -d)
        if loc is not None:
            P.append(prim_cyl(f'GuardBoss{s}', loc - n * 0.01, loc + n * 0.025, 0.06, n=12, col='gold_d'))
            P.append(prim_sphere(f'GuardPearl{s}', loc + n * 0.03, 0.035, 'pearl', nl=5, seg=8))
            for q in P[-2:]: q.bone = 'UpperTorso'; head_clear(q, 0.03)

    # ---------------- gold sash fitted on the robe, winged medallion, hanging tails ----------------
    sash = band('Sash', 2.1, 2.28, 0.012, th=0.02, bvh=piece_bvh(robe))
    def sashp(U, V, m):
        img = P_solid(GOLD)(U, V, m); z, az = zc(U, V, m)
        img = mix(img, (0.5 + 0.5 * np.cos(az * 16)) * 0.3, GOLD_L)
        img = mix(img, aa(np.minimum(V - 0.12, 0.88 - V) * -400), GOLD_D)
        return img
    sash.paint = sashp; P.append(sash)
    sb = piece_bvh(sash)
    loc, n = project(sb, Vector((0, 0, 2.19)), Vector((0, 1, 0)))
    mc = loc + n * 0.02
    nk = len(P)
    P.append(prim_cyl('Medallion', mc - n * 0.015, mc + n * 0.025, 0.1, n=16, col='gold_d'))
    P.append(prim_cyl('MedallionFace', mc + n * 0.02, mc + n * 0.035, 0.08, n=16, col='gold'))
    P.append(prim_sphere('MedallionPearl', mc + n * 0.04, 0.04, 'pearl', nl=5, seg=8))
    for sg in (-1, 1):   # little gold wings on the medallion
        for k, (dz, ln) in enumerate(((0.04, 0.17), (0.0, 0.14), (-0.04, 0.1))):
            b0 = mc + Vector((sg * 0.07, 0, dz)) + n * 0.01
            P.append(prim_cone(f'MedWing{sg}{k}', b0, b0 + Vector((sg * ln, 0, 0.03 - k * 0.02)), 0.03, 'gold' if k % 2 == 0 else 'gold_l', n=4, flat=0.35))
    loc2, n2 = project(sb, Vector((0.3, 0, 2.19)), Vector((0, 1, 0)))
    tc = loc2 + n2 * 0.03
    P.append(prim_rbox('SashKnot', tc, (0.11, 0.06, 0.1), 'gold'))
    for k, (dx, ln) in enumerate(((-0.03, 0.2), (0.04, 0.16))):
        a = tc + Vector((dx, -0.005, -0.04)); b = a + Vector((dx * 0.6, -0.012, -ln))
        P.append(tube_path(f'SashTail{k}', [a, (a + b) / 2 + Vector((0, -0.01, 0)), b], 0.026, 'gold', n=6,
                           rfn=lambda t: 0.024 + 0.012 * t))
        P.append(prim_cone(f'SashTassel{k}', b + Vector((0, 0, 0.01)), b + Vector((0, 0, -0.07)), 0.03, 'gold_d', n=6))
    for q in P[nk:]: q.bone = 'LowerTorso'; q.group = 'Bottom'

    # ---------------- huge layered feathered wings + gold back mount ----------------
    for sg in (1, -1):
        _wing(sg, P)
    tb = piece_bvh(robe)
    loc, n = project(tb, Vector((0, 0, 2.78)), Vector((0, -1, 0)))
    mp = loc + n * 0.05
    P.append(prim_rbox('WingMount', mp, (0.5, 0.12, 0.3), 'gold'))
    P.append(prim_rbox('WingMountInlay', mp + n * 0.05, (0.36, 0.04, 0.18), 'gold_d'))
    P.append(prim_sphere('WingMountPearl', mp + n * 0.08, 0.05, 'pearl', nl=5, seg=8))
    for q in P[-3:]: q.bone = 'UpperTorso'; head_clear(q, 0.03)

    # ---------------- gold gladiator sandals, anklets, little ankle wings ----------------
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sh = shoe('Sandal_' + s, s, off=0.03, bulk=0.0, toe=0.03, sole_h=0.055, open_elev=50)
        def sandal_paint(U, V, m):
            img = P_solid(SKIN)(U, V, m)
            z, az = zc(U, V, m)
            st = m['sole_top']; aaz = np.abs(az)
            tl = (aaz < 0.55) & (z < st + 0.05) & (np.abs(((az / 0.18) % 1.0) - 0.5) > 0.44)
            img = mix(img, tl.astype(float) * 0.5, '#d98f63')                              # toes
            img = mix(img, aa((aaz - 0.1) * 300) * (z > st), GOLD)                             # instep strap
            for zz in (0.07, 0.13, 0.19):
                img = mix(img, aa(np.abs(z - (st + zz)) * 600 - 8) * (aaz < 2.2), GOLD)        # cross straps
            img = mix(img, aa((np.abs(aaz - PI) - 0.13) * 300) * (z > st), GOLD)              # heel strap
            img = mix(img, aa(np.abs(z - (m['zmax'] - 0.03)) * 600 - 9), GOLD)
            img = mix(img, aa(np.hypot(aaz * 0.17, z - (st + 0.13)) * 600 - 8), PEARL)        # pearl on the instep
            img = mix(img, aa((z - st) * 600), GOLD_D)                                          # gold sole
            img = mix(img, aa((z - (st - 0.022)) * 600), GOLD)
            return img
        sh.paint = sandal_paint; P.append(sh)
        an = _shin(leg_tube('Anklet_' + s, s, 0.64, 0.57, 0.035, nseg=16, nrows=3, group='Feet', th=0.015))
        an.paint = lambda U, V, m: mix(P_solid(GOLD)(U, V, m), aa(np.abs(V - 0.5) * 400 - 12), GOLD_L)
        an.rect_key = 'Anklet'; P.append(an)
        ab = piece_bvh(an)
        loc, n = project(ab, Vector((sg * 0.6, 0.02, 0.605)), Vector((-sg, 0, 0)))
        if loc is not None:
            base = loc + n * 0.005
            for k, (dz, dy, ln) in enumerate(((0.05, 0.05, 0.15), (0.0, 0.06, 0.12), (-0.04, 0.05, 0.08))):
                b0 = base + Vector((0, 0, dz * 0.4))
                w = prim_cone(f'AnkleWing{s}{k}', b0, b0 + Vector((sg * 0.04, dy + 0.04, 0.05 + dz)) * (ln / 0.12), 0.028,
                              'gold' if k != 1 else 'gold_l', n=4, flat=0.35, group='Feet')
                w.bone = 'LeftLowerLeg' if s == 'L' else 'RightLowerLeg'; P.append(w)
    return P, pal
