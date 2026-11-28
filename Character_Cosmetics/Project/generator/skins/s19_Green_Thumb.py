from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '19', 'Green_Thumb', 'Common', 0.32

# Gardener: sage-green bib apron (neck loop, back ties with a bow, big leaf-print pocket with a trowel and a seed
# packet) over a tucked yellow tee, khaki shorts with rolled cuffs, skin-coloured legs and green rubber garden boots.

def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


AN = 96                                   # ring resolution of the cast apron shell
ASTEP = 2 * PI / AN
A_ZS = [1.60, 1.69, 1.78, 1.87, 1.96, 2.05, 2.14, 2.23, 2.32, 2.36, 2.41, 2.46, 2.51, 2.56, 2.61, 2.66, 2.75, 2.83, 2.95]
A_ELEVS = (18, 34, 46)                    # strap piece dome rows: straps (2 bands) + neck loop (top band)
SKIRT_W, BIB_W, STRAP_W0 = 18 * ASTEP, 10 * ASTEP, 8 * ASTEP   # half-widths (rad around the body axis)
A_COLS = 40                               # columns across the apron panel


def _w_of_z(z):
    """half-width of the apron at height z: skirt -> rounded armhole cut -> bib (works on arrays too)"""
    t = np.clip((np.asarray(z, float) - 2.36) / (2.66 - 2.36), 0, 1)
    return SKIRT_W - (SKIRT_W - BIB_W) * np.sin(t * PI / 2)


def _resample_panel(shell, nrows):
    """cut the front panel out of a full cast ring shell: every row gets A_COLS columns between -w(z) and +w(z),
    so the outline is a smooth curve instead of a stair of whole ring columns."""
    rows = []
    for i in range(nrows):
        ring = shell.verts[i * AN:(i + 1) * AN]
        z = sum(p.z for p in ring) / AN
        w = float(_w_of_z(z)); row = []
        for k in range(A_COLS + 1):
            az = -w + 2 * w * k / A_COLS
            f = (az + PI) / ASTEP; j0 = int(math.floor(f)); fr = f - j0
            row.append(ring[j0 % AN].lerp(ring[(j0 + 1) % AN], fr))
        rows.append(row)
    return rows


def _leaf(img, x, z, px, pz, L, W, ang, col, vein):
    ca, sa = math.cos(ang), math.sin(ang)
    dx = x - px; dz = z - pz
    a = dx * ca + dz * sa; b = -dx * sa + dz * ca
    t = np.clip(a / L, -1, 1)
    half = W * (1 - t ** 2) * (1 - 0.25 * t)
    d = np.maximum(np.abs(b) - half, np.abs(a) - L)
    img = mix(img, aa(d * 1400), col)
    img = mix(img, aa((np.abs(b) - 0.0025) * 1400) * (np.abs(a) < L * 0.85), vein)
    # stem
    img = mix(img, aa((np.abs(b) - 0.003) * 1400) * (a < -L) * (a > -L - 0.025), vein)
    return img


def build():
    pal = {'yellow': '#f2d34f', 'yellow_d': '#d6b636', 'khaki': '#c8b28a', 'khaki_d': '#a8936c', 'khaki_l': '#d6c39e',
           'boot': '#3f8f3a', 'boot_d': '#2f6e2b', 'boot_l': '#5aa952', 'sole': '#24461f',
           'apron': '#6f9e5a', 'apron_d': '#557f43', 'apron_l': '#86b571', 'pocket': '#7aa964',
           'leaf': '#3f6e33', 'leaf_l': '#a9d08a', 'wood': '#a5713e', 'wood_d': '#7d5228', 'metal': '#a7adb4',
           'packet': '#f4efe2', 'red': '#d9532f'}
    P = []

    # ---------------- shorts (lowest layer) ----------------
    pt = pants('Shorts', 2.2, 1.42, 0.045, hip_off=0.06, leg_extra=lambda z, a: 0.025 + 0.05 * max(0, 1.8 - z), nseg=16)

    def shorts_paint(U, V, m):
        img = P_solid(pal['khaki'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['khaki_d'])      # side seams
        if m.get('kind') == 'hip':
            img = mix(img, aa(np.abs(z - 2.135) * 500 - 1.2), pal['khaki_d'])                    # waistband seam
            img = mix(img, aa((np.abs(az) - 0.008) * 400) * (z < 2.12), pal['khaki_d'])           # fly / back seam
            img = mix(img, aa((np.abs(np.abs(az) - PI) - 0.008) * 400) * (z < 2.12), pal['khaki_d'])
        return img
    for p in pt: p.paint = shorts_paint
    P += pt
    for s in 'LR':
        cf = leg_tube('ShortsCuff_' + s, s, 1.53, 1.41, 0.125, nseg=16, nrows=3, th=0.02)
        cf.paint = lambda U, V, m: mix(P_solid(pal['khaki_l'])(U, V, m), aa(np.abs(V - 0.5) * 300 - 1.0), pal['khaki_d'])
        cf.rect_key = 'ShortsCuff'; P.append(cf)
        P.append(skin_leg(s, 1.5, 0.88))

    # ---------------- yellow tee (tucked into the shorts) ----------------
    tee = torso_shell('Tee', 2.08, 0.03, nseg=32, th=0.015, col='yellow')
    P.append(tee)
    for s in 'LR':
        sl = sleeve('TeeSleeve_' + s, s, 0.0, 0.32, 0.035, extra=lambda t, a: 0.012 + 0.025 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['yellow'])(U, V, m), aa((V - 0.14) * -300), pal['yellow_d'])
        P.append(sl)
    P.append(collar('TeeCollar', 'stand', h=0.035, flare=0.015, col='yellow_d', th=0.015))

    # ---------------- apron waist ties (back), under the apron's side edges ----------------
    tie = band('ApronTie', 2.19, 2.28, 0.012, nseg=48, th=0.018, col='apron_d', bvh=piece_bvh(tee, *pt),
               keep=lambda i, j, z, az: abs(az) > 0.98)
    P.append(tie)

    # ---------------- bib apron: smooth-outlined front panel + straps / neck loop ----------------
    full = torso_shell('ApronCast', A_ZS[0], 0.065, nseg=AN, zs=A_ZS, z_dome=A_ZS[-1], elevs=(),
                       extra=lambda z, a: 0.012 + 0.06 * max(0, 2.0 - z), th=0, hang=2.3, over=pt + [tee, tie])
    rows = _resample_panel(full, len(A_ZS))
    zr = [sum(p.z for p in r) / len(r) for r in rows]
    zmin, zmax = zr[0], zr[-1]
    apron = grid_piece('Apron', rows, closed=False, v_vals=[(z - zmin) / (zmax - zmin) for z in zr],
                       hints=[[Vector((p.x, p.y, 0)) for p in r] for r in rows], group='Top')
    apron.meta.update(zmin=zmin, zmax=zmax, circ=1.2, kind='torso')
    thicken(apron, 0.022)
    apron.region = 'torso'; apron.skirt = True; apron.rect_key = 'Apron'

    def apaint(U, V, m):
        img = P_solid(pal['apron'])(U, V, m)
        z, _ = zc(U, V, m)
        w = _w_of_z(z); r = 0.5
        az = -w + 2 * w * U
        d_side = np.minimum(U, 1 - U) * 2 * w * r
        d_top = np.where(np.abs(az) < STRAP_W0, zmax - z, 9.0)
        d = np.minimum(np.minimum(d_side, d_top), z - zmin)
        img = mix(img, aa((d - 0.028) * 700), pal['apron_d'])                     # bias binding around the edge
        dash = (np.sin((z + np.abs(az) * r) * 3 * 120) > 0).astype(float)
        img = mix(img, aa(np.abs(d - 0.045) * 1200 - 0.6) * dash * 0.7, pal['apron_l'])   # top-stitch
        return img
    apron.paint = apaint; P.append(apron)

    def skeep(i, j, zc_, az):
        a = abs(az)
        if i <= 2: return STRAP_W0 < a < BIB_W              # straps: sewn on the bib top, up the chest
        return a > STRAP_W0                                  # neck loop around the back of the neck
    strap = torso_shell('ApronStrap', 2.83, 0.075, nseg=AN, zs=[2.83, 2.95], z_dome=2.95, elevs=A_ELEVS,
                        keep=skeep, th=0.018, over=[tee], over_gap=0.05, col='apron_d')
    head_clear(strap, 0.05)
    P.append(strap)

    # ---------------- big front pocket with leaf print ----------------
    ab = piece_bvh(apron)
    PX0, PX1, PZ0, PZ1 = -0.31, 0.31, 1.73, 2.13
    pk = surface_patch('ApronPocket', ab, lambda s_, t: Vector((PX0 + s_ * (PX1 - PX0), 0, PZ0 + t * (PZ1 - PZ0))),
                       Vector((0, 1, 0)), 0.008, 12, 7, th=0.012)
    pw, ph = PX1 - PX0, PZ1 - PZ0
    leaves = [(0.08, 0.10, 0.05, 0.022, 0.6, 0), (0.17, 0.25, 0.045, 0.02, -0.5, 1), (0.26, 0.09, 0.04, 0.018, 1.9, 0),
              (0.36, 0.22, 0.05, 0.022, 0.3, 1), (0.47, 0.08, 0.045, 0.02, 2.5, 0), (0.53, 0.25, 0.04, 0.018, -0.9, 1),
              (0.04, 0.27, 0.035, 0.016, -1.2, 1), (0.30, 0.31, 0.03, 0.014, 0.9, 0), (0.56, 0.05, 0.03, 0.014, 0.2, 1)]

    def ppaint(U, V, m):
        x = U * pw; z = V * ph
        img = P_solid(pal['pocket'])(U, V, m)
        for px, pz, L, W, ang, c in leaves:
            img = _leaf(img, x, z, px, pz, L, W, ang, pal['leaf'] if c == 0 else pal['leaf_l'], pal['apron_d'])
        img = mix(img, aa((z - (ph - 0.035)) * -700), pal['apron_d'])            # hem band along the opening
        img = mix(img, aa(np.minimum(np.minimum(x, pw - x), z) * 700 - 6), pal['apron_d'])   # edge binding
        img = mix(img, aa((np.abs(x - pw / 2) - 0.004) * 900) * (z < ph - 0.035), pal['apron_d'])  # divider stitch
        return img
    pk.paint = ppaint; pk.meta['rect'] = (256, 160)
    pk.skirt = True                       # deforms exactly like the apron skirt it is sewn on
    P.append(pk)

    # trowel in the pocket (character's left), seed packet on the right
    loc, n = project(ab, Vector((0.15, 0, 2.1)), Vector((0, 1, 0)))
    ax = (Vector((0.14, 0, 1)) + n * 0.12).normalized()
    b0 = loc + n * 0.036
    P.append(prim_cyl('TrowelFerrule', b0 - ax * 0.03, b0 + ax * 0.06, 0.03, n=10, col='metal'))
    P.append(prim_cyl('TrowelHandle', b0 + ax * 0.06, b0 + ax * 0.28, 0.032, 0.026, n=10, col='wood'))
    P.append(prim_cyl('TrowelGrip', b0 + ax * 0.12, b0 + ax * 0.15, 0.035, n=10, col='wood_d'))
    P.append(prim_sphere('TrowelKnob', b0 + ax * 0.285, 0.034, 'wood_d', nl=4, seg=10))
    for q in P[-4:]: q.bone = 'LowerTorso'
    loc2, n2 = project(ab, Vector((-0.17, 0, 2.1)), Vector((0, 1, 0)))
    ang = math.atan2(n2.x, -n2.y)
    Rz = Matrix.Rotation(ang, 3, 'Z') @ Matrix.Rotation(-0.12, 3, 'Y')
    P.append(prim_box('SeedPacket', loc2 + n2 * 0.022 + Vector((0, 0, 0.05)), (0.13, 0.012, 0.15), 'packet', rot=Rz))
    P.append(prim_box('SeedPacketBand', loc2 + n2 * 0.03 + Vector((-0.006, 0, 0.085)), (0.12, 0.008, 0.045), 'red', rot=Rz))
    for q in P[-2:]: q.bone = 'LowerTorso'

    # bow at the back of the waist ties
    tb = piece_bvh(tie)
    bl, bn = project(tb, Vector((0, 0, 2.235)), Vector((0, -1, 0)))
    bc = bl + bn * 0.03
    P.append(prim_rbox('BowKnot', bc, (0.07, 0.05, 0.07), 'apron_d', bevel=0.015))
    for sg in (-1, 1):
        P.append(prim_rbox(f'BowLoop{sg}', bc + Vector((0.08 * sg, 0.0, 0.015)), (0.12, 0.035, 0.075), 'apron_d',
                           rot=Matrix.Rotation(0.35 * sg, 3, 'Y'), bevel=0.015))
        P.append(prim_box(f'BowTail{sg}', bc + Vector((0.045 * sg, 0.005, -0.12)), (0.045, 0.014, 0.2), 'apron_d',
                          rot=Matrix.Rotation(-0.22 * sg, 3, 'Y')))
    for q in P[-5:]: q.bone = 'LowerTorso'

    # ---------------- green rubber garden boots ----------------
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.05, bulk=0.035, toe=0.03, sole_h=0.06)

        def bp(U, V, m):
            img = P_solid(pal['boot'])(U, V, m)
            z, az = zc(U, V, m)
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            img = mix(img, aa(np.abs(z - m['sole_top'] - 0.025) * 600 - 1.5), pal['boot_d'])   # rubber trim line
            return img
        sh.paint = bp; P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 0.97, 0.46, 0.095, nseg=16, group='Feet',
                               extra=lambda z, a: 0.01 + 0.035 * max(0, z - 0.72)))
        shaft.paint = lambda U, V, m: mix(P_solid(pal['boot'])(U, V, m), (0.5 + 0.5 * np.cos(2 * PI * U * 2)) * 0.12, pal['boot_l'])
        P.append(shaft)
        P.append(_shin(leg_tube('BootRim_' + s, s, 1.0, 0.93, 0.145, nseg=16, nrows=3, group='Feet', col='boot_d', th=0.02)))
    return P, pal
