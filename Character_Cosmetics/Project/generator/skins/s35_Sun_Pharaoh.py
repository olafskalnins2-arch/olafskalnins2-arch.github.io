from o04 import *
from garments import _grid_with_ij
NUM, NAME, RARITY, MAXD = '35', 'Sun_Pharaoh', 'Epic', 0.32

# Sun Pharaoh: pleated linen shendyt (pleated under-kilt + shorter wrap layer with a curved hem), gold belt with an
# inlaid buckle plate and a jewelled front apron, sheer linen top with long sleeves, a huge usekh collar with
# concentric gold / turquoise / lapis bands and bead drops, a sun-disc pectoral, gold arm cuffs, anklets and sandals.


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def _az(p):
    return math.atan2(p.x, -p.y)          # 0 = front, +pi/2 = character left (+X)


def _pleat(pc, n, amp, z_full, z_top, skip_front=0.0):
    """Real accordion pleats: push every vertex (outer + inner shell alike) outward by a triangle wave in azimuth.
    Outward only, so the layer underneath is never hit. Fades out towards the waistband."""
    for i, p in enumerate(pc.verts):
        a = _az(p)
        f = abs(((a / (2 * PI) * n) % 1.0) - 0.5) * 2          # 1 on a ridge, 0 in a valley
        k = min(1.0, max(0.0, (z_top - p.z) / (z_top - z_full)))
        if skip_front: k *= min(1.0, max(0.0, (abs(a) - skip_front) / 0.25))
        h = Vector((p.x, p.y, 0))
        if h.length < 1e-6: continue
        pc.verts[i] = p + h.normalized() * (amp * f * k)


def _hem_warp(pc, z_top, z_bot, hem):
    """Re-space the hanging rows so the hem follows hem(az) (curved wrap edge) without stair steps."""
    for i, p in enumerate(pc.verts):
        if p.z < z_top:
            a = _az(p)
            pc.verts[i] = Vector((p.x, p.y, z_top - (z_top - p.z) * (z_top - hem(a)) / (z_top - z_bot)))


def build():
    pal = {'linen': '#f4efe2', 'linen_d': '#ddd5c2', 'linen_s': '#c9bfa9', 'gold': '#d9a72e', 'gold_l': '#f0c95a',
           'gold_d': '#a77a17', 'turq': '#2fb5a8', 'turq_d': '#1f8a80', 'lapis': '#2a6fb0', 'lapis_d': '#1c4c80',
           'skin': SKIN, 'sun': '#e8762b'}
    P = []
    sheer = '#f3e6d6'      # white linen with the skin faintly showing through

    # ---------------- lower layers: loincloth seat + bare legs ----------------
    seat = torso_shell('Loincloth', 1.95, 0.03, nseg=32, zs=list(np.linspace(1.95, 2.12, 4)), elevs=(), th=0.012,
                       col='linen_d', group='Bottom', cap_bottom=True, cap_dz=-0.03)
    seat.meta['kind'] = 'hip'; seat.skirt = False
    legs = [skin_leg(s, 1.9, 0.46) for s in 'LR']

    # ---------------- sheer top (tucked into the kilt) ----------------
    top = torso_shell('SheerTop', 2.1, 0.035, nseg=32, th=0.015, extra=lambda z, a: 0.006)

    def sheer_paint(U, V, m):
        img = P_solid(sheer)(U, V, m)
        z, az = zc(U, V, m)
        x = az * 0.45
        img = mix(img, (0.5 + 0.5 * np.cos(x * 2 * PI / 0.05)) * 0.18, pal['linen_d'])   # fine vertical pleats
        return img
    top.paint = sheer_paint
    P.append(top)
    for s in 'LR':
        sl = sleeve('SheerSleeve_' + s, s, 0.0, 0.84, 0.04, th=0.015, extra=lambda t, a: 0.006 + 0.02 * max(0, t - 0.45))

        def ssp(U, V, m):
            img = P_solid(sheer)(U, V, m)
            img = mix(img, (0.5 + 0.5 * np.cos(U * 2 * PI * 14)) * 0.18, pal['linen_d'])
            return img
        sl.paint = ssp
        P.append(sl)

    # ---------------- pleated under-kilt (hangs over seat + legs + tucked top) ----------------
    kz = list(np.linspace(1.45, 2.23, 10))
    kilt = torso_shell('Kilt', 1.45, 0.05, nseg=48, zs=kz, elevs=(), th=0.02, group='Bottom',
                       extra=lambda z, a: 0.02 + 0.12 * max(0, 2.05 - z),
                       hang=2.231, over=[seat, top] + legs, over_gap=0.026)
    _pleat(kilt, 24, 0.016, 1.9, 2.15)

    def kilt_paint(U, V, m):
        img = P_solid(pal['linen'])(U, V, m)
        z, az = zc(U, V, m)
        f = np.abs(((az / (2 * PI) * 24) % 1.0) - 0.5) * 2          # same wave as the geometry
        img = mix(img, (1 - f) ** 2 * 0.55 * np.clip((2.15 - z) / 0.25, 0, 1), pal['linen_s'])
        img = mix(img, aa((z - (m['zmin'] + 0.045)) * 600), pal['gold'])          # gold hem border
        img = mix(img, aa(np.abs(z - (m['zmin'] + 0.06)) * 600 - 2), pal['lapis'])
        return img
    kilt.paint = kilt_paint
    P.append(kilt)

    # ---------------- wrap layer: shorter, curved hem (low at the front, rising to the back) ----------------
    wz = list(np.linspace(1.6, 2.27, 8))
    wrap = torso_shell('KiltWrap', 1.6, 0.06, nseg=48, zs=wz, elevs=(), th=0.02, group='Bottom',
                       extra=lambda z, a: 0.025 + 0.12 * max(0, 2.05 - z),
                       hang=2.271, over=[kilt, seat, top] + legs, over_gap=0.026)
    _hem_warp(wrap, 2.16, 1.6, lambda a: 1.6 + 0.14 * (1 - math.cos(a)) / 2)

    def wrap_paint(U, V, m):
        img = P_solid(pal['linen'])(U, V, m)
        z, az = zc(U, V, m)
        # royal fan pleats: chevron lines running down and out from the centre front
        q = np.abs(az) * 0.5 + (2.2 - z) * 0.55
        w = np.abs(((q / 0.045) % 1.0) - 0.5)
        img = mix(img, aa((0.08 - w) * -60) * 0.7, pal['linen_d'])
        img = mix(img, aa((V - 0.075) * 600), pal['gold'])                      # gold border along the curved hem
        img = mix(img, aa(np.abs(V - 0.03) * 600 - 2), pal['turq'])
        return img
    wrap.paint = wrap_paint
    P.append(wrap)

    # ---------------- gold belt fitted on the wrap ----------------
    belt = band('Belt', 2.1, 2.24, 0.02, th=0.02, bvh=piece_bvh(wrap), hang=2.35)
    belt.group = 'Bottom'

    def belt_paint(U, V, m):
        img = P_solid(pal['gold'])(U, V, m)
        x, z = phys(U, V, m)
        k = np.floor(x / 0.06).astype(int)
        cell = np.abs(((x / 0.06) % 1.0) - 0.5)
        inner = (V > 0.25) & (V < 0.75) & (cell < 0.36)
        img = mix(img, inner.astype(float), pal['lapis'])
        img = mix(img, (inner & (k % 2 == 0)).astype(float), pal['turq'])
        img = mix(img, aa(np.abs(V - 0.12) * 300 - 3), pal['gold_l'])
        img = mix(img, aa(np.abs(V - 0.88) * 300 - 3), pal['gold_l'])
        return img
    belt.paint = belt_paint
    P.append(belt)
    bb = piece_bvh(belt)
    loc, n = project(bb, Vector((0, 0, 2.175)), Vector((0, 1, 0)))
    bk = prim_rbox('BeltPlate', loc + n * 0.02, (0.2, 0.04, 0.17), 'gold_l', group='Bottom'); bk.bone = 'LowerTorso'; P.append(bk)
    gm = prim_rbox('BeltGem', loc + n * 0.045, (0.11, 0.03, 0.09), 'lapis', group='Bottom'); gm.bone = 'LowerTorso'; P.append(gm)
    for sg in (-1, 1):
        g2 = prim_sphere(f'BeltStud{sg}', loc + n * 0.035 + Vector((0.075 * sg, 0, 0)), 0.022, 'turq', nl=4, seg=6, group='Bottom')
        g2.bone = 'LowerTorso'; P.append(g2)

    # ---------------- jewelled front apron hanging from the belt (rigid, on the pelvis) ----------------
    wb = piece_bvh(wrap)

    def apron_pt(s, t):
        w = 0.1 + 0.05 * t
        return Vector(((s - 0.5) * 2 * w, 0, 2.1 - t * 0.46))
    ap = surface_patch('Apron', wb, apron_pt, Vector((0, 1, 0)), 0.026, 5, 7, th=0.02, group='Bottom')
    ap.rigid = True; ap.bone = 'LowerTorso'; ap.meta['rect'] = (128, 256)

    def apron_paint(U, V, m):
        img = P_solid(pal['gold'])(U, V, m)
        u = U; v = V                       # v: 0 at the belt, 1 at the tip
        inner = (u > 0.1) & (u < 0.9) & (v > 0.05) & (v < 0.86)
        col = np.floor((u - 0.1) / 0.8 * 5).astype(int)
        img = mix(img, inner.astype(float), pal['lapis'])
        img = mix(img, (inner & (col % 2 == 1)).astype(float), pal['turq'])
        # horizontal gold bead dividers
        img = mix(img, (inner & (np.abs(((v - 0.05) / 0.09) % 1.0 - 0.5) > 0.4)).astype(float), pal['gold_l'])
        # vertical gold seams between the strips
        img = mix(img, (inner & (np.abs((((u - 0.1) / 0.8 * 5) % 1.0) - 0.5) > 0.44)).astype(float), pal['gold_d'])
        # bottom band: a row of little sun discs
        img = mix(img, ((v > 0.88) & (np.hypot(((u * 5) % 1.0 - 0.5) * 0.6, (v - 0.94) * 2.2) < 0.1)).astype(float), pal['sun'])
        return img
    ap.paint = apron_paint
    P.append(ap)
    tip_y = min(p.y for p in ap.verts)
    for k, x in enumerate(np.linspace(-0.12, 0.12, 5)):
        loc2, n2 = project(wb, Vector((x, 0, 1.63)), Vector((0, 1, 0)))
        if loc2 is None: continue
        bd = prim_sphere(f'ApronDrop{k}', loc2 + n2 * 0.04 + Vector((0, 0, -0.01)), 0.026, 'turq' if k % 2 else 'lapis',
                         nl=5, seg=6, scale=(1, 0.7, 1.5), group='Bottom')
        bd.bone = 'LowerTorso'; P.append(bd)

    P += [seat] + legs

    # ---------------- usekh collar: broad bib over chest, shoulders and back ----------------
    nseg = 48
    D = hdirs_b(nseg)
    c0 = Vector((0, 0, 2.95))
    e_neck = 57.0

    def e_edge(a):
        s2 = abs(math.sin(a)) ** 2.6
        back = (1 - math.cos(a)) / 2
        return -42.0 + 5.0 * back + 64.0 * s2
    svals = list(np.linspace(0, 1, 10))
    rows = []; hints = []
    for s in svals:
        dirs = []
        for j, d in enumerate(D):
            e = math.radians(e_neck + (e_edge(azb(j, nseg)) - e_neck) * s)
            dirs.append((d * math.cos(e) + Z * math.sin(e)).normalized())
        rows.append(ray_ring(B.bvh['torso_up'], c0, dirs, 0.075, R=1.2, smooth=2)); hints.append(dirs)
    us = _grid_with_ij('Usekh', rows, True, svals, hints, 'Top')
    us.meta.update(circ=_ring_len_(rows[5]), rect=(512, 128), kind='collar')
    head_clear(us, 0.035)
    thicken(us, 0.025)
    us.region = 'torso'; us.skirt = False

    def usekh_paint(U, V, m):
        s = V                                 # 0 at the neck, 1 at the outer edge
        x = U * m['circ']
        img = P_solid(pal['gold'])(U, V, m)
        bands = ((0.10, 0.24, 'turq'), (0.30, 0.44, 'lapis'), (0.50, 0.62, 'turq'), (0.68, 0.80, 'lapis'))
        for a, b, c in bands:
            img = mix(img, aa(np.maximum(a - s, s - b) * 900), pal[c])
            # beads: little gold dots threaded through each coloured band
            mid = (a + b) / 2
            sp = 0.045
            d = np.hypot(((x / sp) % 1.0 - 0.5) * sp, (s - mid) * 0.5)
            img = mix(img, aa((d - 0.009) * 2500) * 0.85, pal['gold_l'])
        # outer row of tear drops (alternating turquoise / lapis) with a gold rim
        sp = 0.06
        k = np.floor(x / sp).astype(int)
        dx = ((x / sp) % 1.0 - 0.5) * sp
        t = np.clip((s - 0.83) / 0.13, 0, 1)
        drop = (np.abs(dx) < 0.024 * np.sin(np.clip(t, 0, 1) * PI) ** 0.6) & (s > 0.83) & (s < 0.96)
        img = mix(img, drop.astype(float), pal['gold_d'])
        drop2 = (np.abs(dx) < 0.017 * np.sin(np.clip(t, 0, 1) * PI) ** 0.6) & (s > 0.845) & (s < 0.945)
        img = mix(img, (drop2 & (k % 2 == 0)).astype(float), pal['turq'])
        img = mix(img, (drop2 & (k % 2 == 1)).astype(float), pal['lapis'])
        img = mix(img, aa((s - 0.04) * 900), pal['gold_d'])
        img = mix(img, aa((0.975 - s) * 900), pal['gold_d'])
        return img
    us.paint = usekh_paint
    P.append(us)

    # bead drops hanging off the collar edge (front and back only, clear of the arms)
    ub = piece_bvh(us)
    edge = rows[-1]
    k = 0
    for j in range(nseg):
        a = azb(j, nseg)
        if 1.0 < abs(a) < 2.2 or j % 2: continue
        p = edge[j]
        d = Vector((p.x, p.y, 0)).normalized()
        loc3, n3 = project(ub, p + Vector((0, 0, 0.03)) + d * 0.5, -d)
        if loc3 is None: continue
        bd = prim_sphere(f'CollarDrop{k}', loc3 + n3 * 0.012 + Vector((0, 0, -0.045)), 0.03,
                         'turq' if k % 2 else 'lapis', nl=5, seg=6, scale=(1, 0.75, 1.45), group='Top')
        bd.bone = 'UpperTorso'; P.append(bd); k += 1

    # sun-disc pectoral hanging below the collar at the centre front
    tb = piece_bvh(top)
    loc, n = project(tb, Vector((0, 0, 2.5)), Vector((0, 1, 0)))
    pec = [prim_rbox('PectoralFrame', loc + n * 0.03, (0.26, 0.04, 0.2), 'gold'),
           prim_rbox('PectoralScarab', loc + n * 0.055 + Vector((0, 0, -0.025)), (0.11, 0.04, 0.12), 'lapis'),
           prim_cyl('PectoralSun', loc + n * 0.05 + Vector((0, 0, 0.06)), loc + n * 0.08 + Vector((0, 0, 0.06)), 0.042, n=12, col='sun'),
           prim_rbox('PectoralWingL', loc + n * 0.05 + Vector((0.085, 0, -0.01)), (0.06, 0.03, 0.1), 'turq'),
           prim_rbox('PectoralWingR', loc + n * 0.05 + Vector((-0.085, 0, -0.01)), (0.06, 0.03, 0.1), 'turq')]
    for q in pec: q.bone = 'UpperTorso'; q.group = 'Top'
    P += pec

    # ---------------- gold arm cuffs + armlets ----------------
    def cuff_paint(U, V, m):
        img = P_solid(pal['gold'])(U, V, m)
        img = mix(img, aa(np.abs(V - 0.5) * 400 - 30), pal['lapis'])
        img = mix(img, aa(np.abs(V - 0.5) * 400 - 12), pal['turq'])
        img = mix(img, aa(np.abs(V - 0.08) * 400 - 6), pal['gold_l'])
        img = mix(img, aa(np.abs(V - 0.92) * 400 - 6), pal['gold_l'])
        return img
    for s in 'LR':
        cf = sleeve('Cuff_' + s, s, 0.78, 0.94, 0.075, nrows=4, cap=False, th=0.025, extra=lambda t, a: 0.004)
        cf.paint = cuff_paint; cf.rect_key = 'Cuff'; P.append(cf)
        al = sleeve('Armlet_' + s, s, 0.25, 0.34, 0.075, nrows=3, cap=False, th=0.022)
        al.paint = cuff_paint; al.rect_key = 'Armlet'; P.append(al)

    # ---------------- gold sandals (bare feet showing between the straps) + anklets ----------------
    for s in 'LR':
        sh = shoe('Sandal_' + s, s, off=0.03, bulk=0.0, toe=0.03, sole_h=0.055, open_elev=50)

        def sandal_paint(U, V, m):
            img = P_solid(SKIN)(U, V, m)
            z, az = zc(U, V, m)
            st = m['sole_top']
            aaz = np.abs(az)
            # toe lines
            tl = (aaz < 0.55) & (z < st + 0.05) & (np.abs(((az / 0.18) % 1.0) - 0.5) > 0.44)
            img = mix(img, tl.astype(float) * 0.5, '#d98f63')
            # T-strap: centre strap up the instep + strap across the foot + heel strap
            img = mix(img, aa((aaz - 0.09) * 300) * (z > st), pal['gold'])
            img = mix(img, aa(np.abs(z - (st + 0.085)) * 600 - 9) * (aaz < 1.9), pal['gold'])
            img = mix(img, aa((np.abs(aaz - PI) - 0.12) * 300) * (z > st), pal['gold'])
            img = mix(img, aa(np.abs(z - (m['zmax'] - 0.03)) * 600 - 9), pal['gold'])
            img = mix(img, aa(np.hypot(aaz * 0.17, z - (st + 0.085)) * 600 - 9), pal['turq'])   # jewel on the instep
            # thick gold sole
            img = mix(img, aa((z - st) * 600), pal['gold_d'])
            img = mix(img, aa((z - (st - 0.02)) * 600), pal['gold'])
            return img
        sh.paint = sandal_paint
        P.append(sh)
        an = _shin(leg_tube('Anklet_' + s, s, 0.62, 0.56, 0.035, nseg=16, nrows=3, group='Feet', th=0.015))
        an.paint = lambda U, V, m: mix(P_solid(pal['gold'])(U, V, m), aa(np.abs(V - 0.5) * 400 - 10), pal['turq'])
        an.rect_key = 'Anklet'
        P.append(an)
    return P, pal


def _ring_len_(r):
    return sum((r[j] - r[j - 1]).length for j in range(len(r)))
