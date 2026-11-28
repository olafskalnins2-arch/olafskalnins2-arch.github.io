from o04 import *          # garments, pipeline, paints, o02/o03/o04 helpers (dome, metal_paint, RF_SLIT_TOP)
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '40', 'Dragon_Knight', 'Legendary', 0.32

OBS, OBS_L, OBS_D = '#24222b', '#3a3644', '#131217'
RED, RED_D = '#d3262e', '#8c1018'
BONE, BONE_D = '#e8dcc0', '#b3a27c'
EMBER = '#ff6a1f'
SHEEN = '#5d5870'


def _shin40(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


# ------------------------------------------------------------------ paints
def _scale_field(x, z, w):
    """overlapping fish scales (rows overlap the row below). returns e (0 at the scale's edge .. 1 at its centre),
    s (vertical position inside the scale, -1 bottom .. 1 top) and the row index"""
    r = w / 2; h = r
    k0 = np.floor(z / h).astype(int)
    E = np.full(x.shape, -1.0); S = np.zeros(x.shape); K = np.zeros(x.shape, int)
    for dk in (0, 1, 2):
        k = k0 - dk
        off = 0.5 * w * (k % 2)
        xc = np.round((x - off) / w) * w + off
        zc_ = k * h + r
        d = np.hypot(x - xc, z - zc_)
        ins = (d < r) & (E < 0)
        E = np.where(ins, 1 - d / r, E); S = np.where(ins, (z - zc_) / r, S); K = np.where(ins, k, K)
    return np.where(E < 0, 0.0, E), S, K


def scale_img(x, z, w, base=OBS, glow=0.16):
    E, S, K = _scale_field(x, z, w)
    img = P_solid(base)(x, z, {})
    img = mix(img, np.clip(0.75 - E * 1.5, 0, 1), '#575170')           # lighter rim on the free (lower) edge
    img = mix(img, np.clip((S - 0.1) * 1.4, 0, 1) * 0.55, OBS_D)        # shadow under the overlapping row above
    img = mix(img, E ** 2 * glow, RED_D)                                 # deep red glint in each scale
    img = mix(img, np.clip(1.3 - E / 0.09, 0, 1), '#0b0a0e')             # crisp outline
    return img


def scale_paint(w=0.11, base=OBS, glow=0.16):
    def f(U, V, m):
        x, z = phys(U, V, m)
        circ = m.get('circ', 1.0); n = max(2, int(round(circ / w)))
        return scale_img(x, z, circ / n, base, glow)
    return f


def trim(img, coord, c, width, col=RED_D, line=EMBER, lw=1.1, k=500):
    """band of `col` centred on coord==c (half width `width`) with a thin glowing line in the middle"""
    img = mix(img, aa((np.abs(coord - c) - width) * k), col)
    if line: img = mix(img, aa(np.abs(coord - c) * k - lw), line)
    return img


def plate_paint(red_v=(), ember=True, base=OBS_L, rings=()):
    """obsidian plate: lobed sheen around, blood-red bands at V positions (with an ember line)"""
    def f(U, V, m):
        az = 2 * PI * (U - 0.5)
        img = P_solid(base)(U, V, m)
        img = mix(img, (0.5 + 0.5 * np.cos(az * 3)) * 0.45, SHEEN)
        img = mix(img, (0.5 - 0.5 * np.cos(az * 3)) * 0.45, OBS_D)
        for v, wdt in red_v:
            img = trim(img, V, v, wdt, RED_D, EMBER if ember else None, k=400)
        for v in rings:
            img = mix(img, aa(np.abs(V - v) * 400 - 1.0), OBS_D)
        return img
    return f


def eye_emblem(img, X, Y, cx, cy, s, ring=True):
    """dragon eye: bone ring, ember almond iris, black slit pupil (X, Y physical units)"""
    dx, dy = X - cx, Y - cy
    r = np.hypot(dx, dy)
    if ring:
        img = mix(img, aa((r - 1.0 * s) * 900), OBS)
        img = mix(img, aa(np.abs(r - 0.93 * s) * 900 - 2.2), BONE)
    a, b = 0.66 * s, 0.3 * s
    R = (a * a + b * b) / (2 * b)
    alm = np.maximum(np.hypot(dx, dy - (b - R)), np.hypot(dx, dy + (b - R))) - R
    img = mix(img, aa((alm - 0.06 * s) * 900), BONE)
    img = mix(img, aa(alm * 900), RED)
    img = mix(img, aa((alm + 0.1 * s) * 900) * np.clip(1 - r / (0.6 * s), 0, 1) * 1.4, EMBER)
    pup = np.hypot(dx / (0.09 * s), dy / (0.33 * s)) - 1
    img = mix(img, aa(pup * 40), OBS_D)
    return img


# ------------------------------------------------------------------ helpers
def _gauntlet(name, side, t0, t1, off_fn, nseg=14, nrows=9, group='Top', th=0.02):
    """armoured glove: tube from the forearm over the ball hand, closed with a cap at the fingertips"""
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
    pc.meta.update(kind='sleeve', circ=sum((rows[0][j] - rows[0][j - 1]).length for j in range(nseg)), t0=t0, t1=t1)
    if th: thicken(pc, th)
    pc.rect_key = name.replace('_L', '').replace('_R', '')
    pc.region = 'arm_' + side
    return pc


def _rot(fwd, up=Vector((0, 0, 1))):
    """rotation whose local -Y points along fwd and local +Z roughly up"""
    fwd = fwd.normalized()
    right = fwd.cross(up).normalized()
    up2 = right.cross(fwd).normalized()
    return Matrix((right, -fwd, up2)).transposed(), right, up2


def _poly_at(pts, t):
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (b - a).length)
    s = t * L[-1]
    for i in range(len(pts) - 1):
        if s <= L[i + 1] or i == len(pts) - 2:
            f = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
            return pts[i].lerp(pts[i + 1], min(max(f, 0), 1))


def membrane(name, sa, sb, nr=8, nc=6, depth=0.36, billow=0.07, t0=0.06):
    """bat-wing membrane between two bone spokes that start at the wing wrist; scalloped trailing edge"""
    rows = []
    for i in range(nr + 1):
        t = t0 + (1 - t0) * i / nr
        row = []
        for k in range(nc + 1):
            c = k / nc
            tm = t * (1 - depth * math.sin(PI * c))
            p = _poly_at(sa, tm).lerp(_poly_at(sb, tm), c)
            p = p + Vector((0, 1, 0)) * billow * math.sin(PI * c) * math.sin(PI * min(1, t * 1.2))
            row.append(p)
        rows.append(row)
    hints = [[Vector((0, 1, 0))] * (nc + 1) for _ in rows]
    pc = grid_piece(name, rows, closed=False, hints=hints, group='Extras')
    thicken(pc, 0.018)
    pc.meta['rect'] = (128, 128); pc.rect_key = 'WingMembrane'
    return pc


def flap(name, a0, a1, zb, zt, over, tag, ctr_u0, paint_fn):
    """one hanging tabard panel (a strip of a draped torso shell between azimuths a0..a1). It hangs off its own thigh
    below the slit top like a slit robe panel (rule 6); the centre-line verts belong to this panel's side."""
    nseg = 64
    zs = list(np.linspace(zb, zt, max(4, int((zt - zb) / 0.075) + 1)))
    pc = torso_shell(name, zb, 0.03, nseg=nseg, zs=zs, elevs=(), keep=lambda i, j, zc_, az: a0 < az < a1,
                     extra=lambda z, a: 0.01 + 0.025 * max(0.0, (1.9 - z) / 0.8), th=0.018, group='Bottom',
                     hang=zt + 0.001, over=over, over_gap=0.03)
    pc.meta['panel'] = [tag] * len(pc.verts)
    pc.meta['slit_top'] = RF_SLIT_TOP()
    us = [u for uv in pc.fuv for (u, v) in uv]; u0, u1 = min(us), max(us)
    pc.fuv = [[((u - u0) / (u1 - u0), v) for (u, v) in uv] for uv in pc.fuv]
    pc.meta['rect'] = (64, 256); pc.meta['ctr_u0'] = ctr_u0
    pc.paint = paint_fn
    return pc


# ------------------------------------------------------------------ build
def build():
    pal = {'obs': OBS, 'obs_l': OBS_L, 'obs_d': OBS_D, 'red': RED, 'red_d': RED_D, 'bone': BONE, 'bone_d': BONE_D,
           'ember': EMBER, 'sheen': SHEEN}
    P = []

    # ---------------- scale leggings (one silhouette with the hip) ----------------
    pt = pants('Leggings', 2.18, 0.48, 0.04, hip_off=0.06, leg_extra=lambda z, a: 0.012)
    for p in pt: p.paint = scale_paint(0.09, OBS, 0.1)
    pt[0].meta['rect'] = (256, 64)
    P += pt
    for s, lp in (('L', pt[1]), ('R', pt[2])):
        B.bvh['s40_trouser_' + s] = piece_bvh(lp)

    # ---------------- leg armour fitted on the leggings ----------------
    legs_armour = []
    for s in 'LR':
        cu = leg_tube('Cuisse_' + s, s, 1.76, 1.3, 0.035, nseg=16, extra=lambda z, a: 0.008, bvh='s40_trouser_' + s, th=0.022)
        cu.meta.update(w_axis=W_AXIS, w_xmin=W_XMIN)       # same weight sampling as the trouser leg under it
        cu.paint = plate_paint(red_v=((0.12, 0.05),), rings=(0.6,)); cu.meta['rect'] = (128, 128); cu.rect_key = 'Cuisse'
        cu.sharp = True
        legs_armour.append(cu)
        kn = leg_tube('Poleyn_' + s, s, 1.38, 1.04, 0.07, nseg=16, nrows=5, bvh='s40_trouser_' + s, th=0.022,
                      extra=lambda z, a: 0.012 + 0.06 * max(0, math.cos(a)) * math.sin(PI * min(1, max(0, (z - 1.04) / 0.34))))
        kn.paint = plate_paint(red_v=((0.5, 0.09),)); kn.meta['rect'] = (64, 64); kn.rect_key = 'Poleyn'
        legs_armour.append(kn)
        gr = _shin40(leg_tube('Greave_' + s, s, 1.1, 0.54, 0.035, nseg=16, bvh='s40_trouser_' + s, group='Feet', th=0.022,
                              extra=lambda z, a: 0.012 + 0.045 * max(0, (0.68 - z) / 0.14) + 0.02 * max(0, math.cos(a)) ** 4))
        gr.paint = plate_paint(red_v=((0.1, 0.04), (0.9, 0.03)), rings=(0.55,)); gr.meta['rect'] = (128, 128); gr.rect_key = 'Greave'
        gr.sharp = True
        P.append(gr)
    P += legs_armour
    # knee spikes
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        kb = piece_bvh(next(p for p in legs_armour if p.name == 'Poleyn_' + s))
        loc, n = project(kb, Vector((0.25 * sg, 0, 1.22)), Vector((0, 1, 0)))
        sp = prim_cone('KneeSpike_' + s, loc - n * 0.02, loc + n * 0.13 + Vector((0, 0, 0.03)), 0.04, 'bone', n=6, group='Bottom')
        P.append(sp)

    # ---------------- sabatons with dragon toe claws ----------------
    def sab_paint(U, V, m):
        img = plate_paint()(U, V, m); z, az = zc(U, V, m)
        for L in (0.42, 0.47, 0.52):
            img = mix(img, aa(np.abs(z - L) * 600 - 1) * (np.cos(az) > 0.25), OBS_D)
        img = trim(img, z, m['sole_top'] + 0.03, 0.012, RED_D, EMBER, k=600)
        return mix(img, aa((z - m['sole_top']) * 600), OBS_D)
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sb = shoe('Sabaton_' + s, s, off=0.05, bulk=0.035, toe=0.08, sole_h=0.05)
        sb.paint = sab_paint; sb.meta['rect'] = (128, 64); sb.rect_key = 'Sabaton'; P.append(sb)
        front = min(sb.verts, key=lambda p: p.y)
        for kk, dx in enumerate((-0.09, 0.0, 0.09)):
            base = Vector((0.255 * sg + dx, front.y + 0.06, 0.37))
            P.append(prim_cone(f'ToeClaw{s}{kk}', base, base + Vector((dx * 0.35, -0.12, -0.04)), 0.032, 'bone', n=6, group='Feet'))

    # ---------------- scale hauberk (hangs over the hip, cuisse tops) ----------------
    hb = torso_shell('Hauberk', 1.84, 0.085, nseg=32, extra=lambda z, a: 0.012 + 0.03 * max(0, (2.1 - z) / 0.26), th=0.03,
                     hang=2.3, over=pt + legs_armour)

    def hb_paint(U, V, m):
        x, z = phys(U, V, m); az = 2 * PI * (U - 0.5)
        circ = m['circ']; n = int(round(circ / 0.14))
        img = scale_img(x, z, circ / n)
        img = trim(img, z, m['zmin'] + 0.05, 0.035, RED_D, EMBER, k=600)              # hem band
        img = mix(img, aa((z - (m['zmin'] + 0.012)) * 600), OBS_D)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.02) * 300) * (z < 2.95), RED_D)
        img = mix(img, aa((z - (m['zmax'] - 0.05)) * -600), RED_D)                     # neckline band
        return img
    hb.paint = hb_paint; hb.meta['rect'] = (512, 256); P.append(hb)
    hbv = piece_bvh(hb)
    P.append(collar('Gorget', 'stand', h=0.07, flare=0.06, col='red_d', th=0.025))

    # ---------------- tabard: chest panel + four hanging panels ----------------
    def chest_pt(s_, t):
        z = 2.14 + t * 0.86
        hw = 0.25 - 0.06 * t
        return Vector(((s_ - 0.5) * 2 * hw, 0, z))
    cp = surface_patch('TabardChest', hbv, chest_pt, Vector((0, 1, 0)), 0.014, 7, 10, th=0.014)

    def cp_paint(U, V, m):
        X = (U - 0.5) * 0.44; Y = V * 0.86
        img = P_solid(RED)(U, V, m)
        img = mix(img, (0.5 - 0.5 * np.cos(U * 2 * PI * 2)) * 0.18, RED_D)
        e = np.minimum(U, 1 - U)
        img = mix(img, aa((e - 0.1) * 500), BONE)
        img = mix(img, aa(np.abs(e - 0.14) * 500 - 1.0), EMBER)
        img = mix(img, aa(((1 - V) - 0.04) * 500), BONE)
        img = eye_emblem(img, X, Y, 0.0, 0.56, 0.14)
        # flame tongues rising from the belt
        for cx in (-0.09, 0.0, 0.09):
            hgt = 0.16 if cx == 0 else 0.11
            fl = np.abs(X - cx) - 0.035 * np.clip(1 - (Y - 0.04) / hgt, 0, 1)
            img = mix(img, aa(fl * 900) * (Y > 0.03), EMBER)
        return img
    cp.paint = cp_paint; cp.meta['rect'] = (128, 256); P.append(cp)

    def flap_paint_fn(front):
        def f(U, V, m):
            X = U if m['ctr_u0'] else 1 - U               # 0 on the centre line .. 1 on the outer edge
            img = P_solid(RED)(U, V, m)
            img = mix(img, (0.5 - 0.5 * np.cos(X * 2 * PI * 1.5)) * 0.25, RED_D)
            img = mix(img, aa((1 - X - 0.16) * 300), BONE)                     # bone trim on the outer edge
            img = mix(img, aa(np.abs(1 - X - 0.21) * 300 - 1.0), EMBER)
            zig = 0.085 + 0.04 * np.abs(((X * 3) % 1) - 0.5) * 2              # dagged hem band
            img = mix(img, aa((V - zig) * 500), BONE)
            img = mix(img, aa(np.abs(V - zig - 0.025) * 500 - 1.2), EMBER)
            img = mix(img, aa((V - 0.03) * 500), RED_D)
            for v0 in ((0.42, 0.6) if front else (0.5,)):                     # downward chevrons across the pair
                img = mix(img, aa((np.abs(V - (v0 + 0.18 * X)) - 0.022) * 500) * (X < 0.84), OBS)
                img = mix(img, aa(np.abs(V - (v0 + 0.18 * X)) * 500 - 1.0) * (X < 0.84), EMBER)
            if front: img = mix(img, aa(X * 300 - 0.8), RED_D)                  # seam on the centre line
            else:
                img = mix(img, aa((X - 0.16) * 300), BONE)                     # back panels: trim on both edges
                img = mix(img, aa(np.abs(X - 0.21) * 300 - 1.0), EMBER)
            return img
        return f
    under = [hb] + legs_armour + pt
    flaps = [flap('TabardFront_L', 0.0, 0.5, 1.12, 2.22, under, 1, True, flap_paint_fn(True)),
             flap('TabardFront_R', -0.5, 0.0, 1.12, 2.22, under, -1, False, flap_paint_fn(True)),
             flap('TabardBack_L', PI - 0.64, PI - 0.27, 1.2, 2.22, under, 2, False, flap_paint_fn(False)),
             flap('TabardBack_R', -PI + 0.27, -PI + 0.64, 1.2, 2.22, under, -2, True, flap_paint_fn(False))]
    P += flaps

    # ---------------- belt over hauberk, chest panel and flap tops ----------------
    belt = band('Belt', 2.1, 2.26, 0.012, th=0.025, bvh=piece_bvh(hb, cp, *flaps), hang=2.36)

    def belt_paint(U, V, m):
        img = P_solid(OBS_D)(U, V, m)
        img = mix(img, aa(np.minimum(V - 0.14, 0.86 - V) * -300), RED_D)
        img = mix(img, aa(np.abs(V - 0.5) * 400 - 1.0) * (np.sin(U * 2 * PI * 60) > 0), OBS_L)
        return img
    belt.paint = belt_paint; belt.meta['rect'] = (256, 32); P.append(belt)
    bbv = piece_bvh(belt)
    loc, n = project(bbv, Vector((0, 0, 2.18)), Vector((0, 1, 0)))
    bk = [prim_rbox('BuckleSkull', loc + n * 0.04, (0.2, 0.07, 0.17), 'bone', bevel=0.02),
          prim_rbox('BuckleSnout', loc + n * 0.08 + Vector((0, 0, -0.04)), (0.12, 0.05, 0.08), 'bone_d', bevel=0.015)]
    for sx in (-1, 1):
        bk.append(prim_sphere(f'BuckleEye{sx}', loc + n * 0.078 + Vector((0.045 * sx, 0, 0.03)), 0.022, 'ember', nl=4, seg=8))
        bk.append(prim_cone(f'BuckleHorn{sx}', loc + n * 0.04 + Vector((0.08 * sx, 0, 0.06)),
                            loc + n * 0.02 + Vector((0.16 * sx, 0, 0.16)), 0.025, 'bone', n=6))
    for sx in (-1, 1):   # studs
        for k in range(3):
            d = Vector((sx * math.sin(0.55 + k * 0.42), -math.cos(0.55 + k * 0.42), 0))
            l2, n2 = project(bbv, d * 1.5 + Vector((0, 0, 2.18)), -d)
            if l2 is not None: bk.append(prim_cone(f'BeltStud{sx}{k}', l2 - n2 * 0.005, l2 + n2 * 0.04, 0.022, 'bone', n=6))
    for q in bk: q.bone = 'LowerTorso'
    P += bk

    # ---------------- arms: scale sleeves, red couters, spiked vambraces, clawed gauntlets ----------------
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.93, 0.05, extra=lambda t, a: 0.01)
        sl.paint = scale_paint(0.09, OBS, 0.14); sl.meta['length'] = 1.9; sl.meta['rect'] = (128, 256); P.append(sl)
        P.append(sleeve('Couter_' + s, s, 0.42, 0.55, 0.085, nrows=4, cap=False, col='red_d',
                        extra=lambda t, a: 0.035 * max(0, math.cos(a + PI)) + 0.01))
        vb = sleeve('Vambrace_' + s, s, 0.56, 0.9, 0.08, cap=False,
                    extra=lambda t, a: 0.012 + 0.045 * max(0, (t - 0.76) / 0.14))
        vb.paint = plate_paint(red_v=((0.9, 0.05), (0.08, 0.03)), rings=(0.45,)); vb.meta['rect'] = (128, 128); vb.sharp = True
        P.append(vb)
        vbb = piece_bvh(vb)
        for k, t in enumerate((0.66, 0.79)):
            c, tg = arm_point(s, t)
            out = Vector((sg, 0.35, 0)); out = (out - tg * out.dot(tg)).normalized()
            l2, n2 = project(vbb, c + out * 0.6, -out)
            if l2 is None: continue
            sp = prim_cone(f'VambSpike{s}{k}', l2 - out * 0.02, l2 + out * 0.15 + tg * 0.06, 0.035, 'bone', n=6, group='Top')
            sp.region = 'arm_' + s; P.append(sp)
        gl = _gauntlet('Gauntlet_' + s, s, 0.87, 1.15, lambda t: 0.035)
        gl.paint = plate_paint(red_v=((0.12, 0.05),), rings=(0.55, 0.75)); gl.meta['rect'] = (64, 64); gl.rect_key = 'Gauntlet'
        P.append(gl)
        gb = piece_bvh(gl)
        c, tg = arm_point(s, 1.08)
        nf, bf = frame(tg, Vector((0, -1, 0)))
        for k, a in enumerate((-1.25, -0.42, 0.42, 1.25)):
            dirv = (nf * math.cos(a) + bf * math.sin(a)).normalized()
            l2, n2 = project(gb, c + dirv * 0.6, -dirv)
            if l2 is None: continue
            cl = prim_cone(f'Claw{s}{k}', l2 - dirv * 0.01, l2 + tg * 0.17 + dirv * 0.05, 0.03, 'bone', n=6, group='Top')
            cl.region = 'arm_' + s; P.append(cl)
        P.append(sleeve('CuffRing_' + s, s, 0.86, 0.9, 0.17, nrows=2, cap=False, col='red'))

    # ---------------- dragon-head spiked pauldrons ----------------
    def pd_paint(U, V, m):
        img = plate_paint()(U, V, m)
        img = trim(img, V, 0.1, 0.06, RED_D, EMBER, k=400)
        az = 2 * PI * (U - 0.5)
        img = mix(img, aa(np.abs(np.sin(az * 4)) * 60 - 1.0) * (V > 0.3), OBS_D)      # radial ridges
        return img
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        C = Vector((0.58 * sg, 0.0, 2.86))
        pd = dome('Pauldron_' + s, s, C, 0.08, (-32, -14, 6, 26, 46, 68), extra=lambda e, a: 0.05 * max(0, (10 - e) / 42), th=0.03)
        pd.paint = pd_paint; pd.meta['rect'] = (128, 128); pd.rect_key = 'Pauldron'; pd.bone = 'UpperTorso'
        head_clear(pd, 0.04); P.append(pd)
        lm = dome('PauldronLame_' + s, s, C, 0.125, (-44, -30, -18), extra=lambda e, a: 0.035, th=0, col='red_d')
        filter_faces(lm, lambda ij, f, lm=lm, sg=sg: all(sg * lm.verts[i].x > 0.4 for i in f))   # outer skirt only
        thicken(lm, 0.025)
        lm.bone = 'UpperTorso'; P.append(lm)
        pb = piece_bvh(pd)
        parts = []
        # spikes along the top ridge
        for k, (yy, ln) in enumerate(((-0.05, 0.2), (0.18, 0.24), (0.4, 0.18))):
            d = Vector((sg * 0.62, yy, 0.78)).normalized()
            l2, n2 = project(pb, C + d * 1.2, -d)
            parts.append(prim_cone(f'PauldSpike{s}{k}', l2 - n2 * 0.03, l2 + (n2 + d).normalized() * ln, 0.05, 'bone', n=6))
        # dragon head on the front of the pauldron
        d = Vector((sg * 0.55, -0.62, 0.45)).normalized()
        l2, n2 = project(pb, C + d * 1.2, -d)
        fwd = Vector((sg * 0.32, -1, -0.18)).normalized()
        R, right, up = _rot(fwd)
        S0 = l2 + n2 * 0.075
        K = 1.3
        parts += [prim_rbox(f'DragonSkull{s}', S0, (0.19 * K, 0.2 * K, 0.15 * K), 'obs_l', rot=R, bevel=0.03),
                  prim_rbox(f'DragonSnout{s}', S0 + fwd * 0.15 * K, (0.13 * K, 0.17 * K, 0.075 * K), 'obs_l', rot=R, bevel=0.02),
                  prim_rbox(f'DragonJaw{s}', S0 + (fwd * 0.12 - up * 0.075) * K, (0.11 * K, 0.15 * K, 0.04 * K), 'obs', rot=R, bevel=0.015),
                  prim_rbox(f'DragonMaw{s}', S0 + (fwd * 0.12 - up * 0.045) * K, (0.09 * K, 0.13 * K, 0.03 * K), 'ember', rot=R, bevel=0.01)]
        for sx in (-1, 1):
            parts.append(prim_sphere(f'DragonEye{s}{sx}', S0 + (fwd * 0.06 + up * 0.05 + right * 0.08 * sx) * K, 0.03, 'ember', nl=4, seg=8))
            hb0 = S0 + (up * 0.06 + right * 0.06 * sx - fwd * 0.03) * K
            parts.append(prim_cone(f'DragonHorn{s}{sx}', hb0, hb0 + (-fwd * 0.22 + up * 0.12 + right * 0.05 * sx) * K, 0.04, 'bone', n=6))
            tb0 = S0 + (fwd * 0.21 - up * 0.04 + right * 0.035 * sx) * K
            parts.append(prim_cone(f'DragonFang{s}{sx}', tb0, tb0 - up * 0.09, 0.018, 'bone', n=5))
        parts.append(prim_cone(f'DragonCrest{s}', S0 + up * 0.08 * K, S0 + (up * 0.17 - fwd * 0.12) * K, 0.04, 'red', n=4, flat=0.35))
        for q in parts:
            q.bone = 'UpperTorso'; head_clear(q, 0.04)
        P += parts

    # ---------------- folded bat-like dragon wings (rigid, UpperTorso) ----------------
    def mem_paint(U, V, m):
        img = P_solid(RED_D)(U, V, m)
        img = mix(img, np.clip(1 - V * 1.6, 0, 1) * 0.75, '#3a0710')           # dark near the wrist
        img = mix(img, np.clip((V - 0.55) * 2, 0, 1) * 0.35, RED)               # brighter toward the trailing edge
        img = mix(img, aa(np.minimum(U, 1 - U) * 200 - 1.5) * 0.8, OBS_D)        # shadow along the bones
        for u0 in (0.33, 0.66):                                                 # veins
            vu = u0 + 0.06 * np.sin(V * 7 + u0 * 9)
            img = mix(img, aa(np.abs(U - vu) * 300 - 0.8) * (V > 0.12) * 0.7, '#4a0a12')
        img = mix(img, aa((1 - V) * 300 - 2.5), EMBER)                           # ember rim on the scalloped edge
        return img
    wing = []
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        l2, _ = project(hbv, Vector((0.2 * sg, 0, 2.95)), Vector((0, -1, 0)))
        A = Vector((0.2 * sg, l2.y + 0.04, 2.95))
        E = Vector((0.6 * sg, 0.95, 3.55)); Wr = Vector((1.1 * sg, 1.02, 4.18))
        tips = [Vector((1.86 * sg, 1.08, 3.45)), Vector((1.7 * sg, 1.18, 2.55)), Vector((1.38 * sg, 1.22, 2.02))]
        fingers = []
        for tp in tips:
            mid = Wr.lerp(tp, 0.5) + Vector((0.0, 0.07, 0.0)) + (tp - Wr).cross(Vector((0, 1, 0))).normalized() * 0.04 * sg
            fingers.append([Wr, mid, tp])
        arm = [Wr, E, A]
        wing.append(membrane(f'WingMem{s}0', arm, fingers[2]))
        wing.append(membrane(f'WingMem{s}1', fingers[2], fingers[1], nc=4))
        wing.append(membrane(f'WingMem{s}2', fingers[1], fingers[0], nc=4))
        for mm in wing[-3:]: mm.paint = mem_paint
        apts = smooth_line(polyline_resample([A - Vector((0, 0.06, 0)), A, E, Wr], 12), 1)
        wing.append(tube_path(f'WingArm{s}', apts, 0.06, 'obs_l', n=8, rfn=lambda t: 0.075 - 0.03 * t))
        for k, fp in enumerate(fingers):
            fp2 = smooth_line(polyline_resample(fp, 8), 1)
            wing.append(tube_path(f'WingFinger{s}{k}', fp2, 0.03, 'obs_l', n=6, rfn=lambda t: 0.036 - 0.02 * t))
            tg = (fp2[-1] - fp2[-2]).normalized()
            wing.append(prim_cone(f'WingTipClaw{s}{k}', fp2[-1] - tg * 0.02, fp2[-1] + tg * 0.11, 0.022, 'bone', n=5))
        wing.append(prim_sphere(f'WingWrist{s}', Wr, 0.075, 'obs', nl=5, seg=10))
        wing.append(prim_sphere(f'WingElbow{s}', E, 0.07, 'obs', nl=5, seg=10))
        wing.append(prim_cone(f'WingThumb{s}', Wr + Vector((0, 0, 0.04)), Wr + Vector((0.06 * sg, -0.04, 0.26)), 0.04, 'bone', n=6))
        wing.append(prim_cone(f'WingElbowSpike{s}', E, E + Vector((0.05 * sg, 0.2, 0.1)), 0.035, 'bone', n=6))
    # wing mount on the upper back
    l2, n2 = project(hbv, Vector((0, 0, 2.92)), Vector((0, -1, 0)))
    mc = Vector((0, l2.y + 0.05, 2.92))
    wing += [prim_rbox('WingMount', mc, (0.56, 0.12, 0.42), 'obs_l', bevel=0.03),
             prim_rbox('WingMountRim', mc + Vector((0, 0.01, 0)), (0.6, 0.09, 0.46), 'red_d', bevel=0.03),
             prim_sphere('WingMountGem', mc + Vector((0, 0.065, 0)), 0.07, 'red', nl=5, seg=10, scale=(1, 0.6, 1.2))]
    for k, dz in enumerate((0.13, -0.13)):
        wing.append(prim_cone(f'MountSpike{k}', mc + Vector((0, 0.05, dz)), mc + Vector((0, 0.18, dz + 0.04)), 0.03, 'bone', n=6))
    for q in wing:
        q.bone = 'UpperTorso'; head_clear(q, 0.04)
    P += wing

    # ---------------- spiked dragon tail (rigid, LowerTorso) ----------------
    l2, _ = project(hbv, Vector((0, 0, 2.02)), Vector((0, -1, 0)))
    yr = l2.y
    tail_pts = [Vector(p) for p in ((0, yr - 0.12, 2.04), (0, yr + 0.2, 1.97), (0.02, 1.02, 1.72), (0.08, 1.28, 1.32),
                                    (0.22, 1.42, 0.92), (0.45, 1.4, 0.6), (0.72, 1.22, 0.45), (0.92, 0.98, 0.42))]
    tail_pts = smooth_line(polyline_resample(tail_pts, 16), 2)
    rf = lambda t: 0.14 * (1 - t) ** 0.85 + 0.025
    tl = tube_path('Tail', tail_pts, 0.14, None, n=10, rfn=rf)
    tl.meta.update(circ=0.88, length=2.9, rect=(128, 256))

    def tail_paint(U, V, m):
        x, z = phys(U, V, m)
        img = scale_img(x, z, 0.88 / 9)
        img = mix(img, np.clip((V - 0.45) * 1.6, 0, 1) * 0.55, RED_D)
        return img
    tl.paint = tail_paint
    tail = [tl]
    for i in range(1, 15):
        p = tail_pts[i]; tg = (tail_pts[i + 1] - tail_pts[i - 1]).normalized()
        up = (Vector((0, 0.35, 1)) - Vector((0, 0.35, 1)).dot(tg) * tg).normalized()
        r = rf(i / 15)
        big = i % 2 == 1
        ln = (0.16 if big else 0.09) * (1 - i / 22)
        tail.append(prim_cone(f'TailSpike{i}', p + up * (r * 0.6), p + up * (r + ln) - tg * 0.04, (0.055 if big else 0.035) * (1 - i / 24),
                              'bone' if big else 'red', n=4, flat=0.35))
    tg = (tail_pts[-1] - tail_pts[-2]).normalized()
    tail.append(prim_cone('TailBlade', tail_pts[-1] - tg * 0.03, tail_pts[-1] + tg * 0.28, 0.13, 'red', n=4, flat=0.3))
    tail.append(prim_cone('TailBladeEdge', tail_pts[-1] - tg * 0.05, tail_pts[-1] + tg * 0.2, 0.09, 'bone', n=4, flat=0.45))
    for q in tail:
        q.bone = 'LowerTorso'
    P += tail
    return P, pal
