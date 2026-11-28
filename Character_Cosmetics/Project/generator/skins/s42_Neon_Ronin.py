from o04 import *          # garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers (dome, _shin)
NUM, NAME, RARITY, MAXD = '42', 'Neon_Ronin', 'Legendary', 0.4

# ---------------------------------------------------------------- palette / neon helpers
CY, CY_HOT, CY_D = '#18e7f2', '#d2feff', '#0b7f88'
MG, MG_HOT, MG_D = '#ff2bd6', '#ffd0f4', '#8c1676'
BLK, BLK2, GUN, GUN_L, GUN_D = '#121216', '#24242c', '#4a4f58', '#7a818c', '#33373e'
K = 420.0   # anti-alias sharpness (1/units)


def _shin42(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def neon(img, dist, w, col, hot, glow=0.32, mask=1.0):
    """bright painted light strip: soft halo + saturated tube + hot white core. dist = distance from the line (units)"""
    img = mix(img, aa((dist - w * 2.8) * K * 0.6) * glow * mask, col)
    img = mix(img, aa((dist - w) * K) * mask, col)
    img = mix(img, aa((dist - w * 0.35) * K) * 0.85 * mask, hot)
    return img


def cyan(img, dist, w=0.007, mask=1.0): return neon(img, dist, w, CY, CY_HOT, mask=mask)
def magenta(img, dist, w=0.006, mask=1.0): return neon(img, dist, w, MG, MG_HOT, mask=mask)


def _seg(x, z, x0, z0, x1, z1):
    """distance from (x, z) arrays to the segment (x0, z0)-(x1, z1)"""
    dx, dz = x1 - x0, z1 - z0
    L2 = dx * dx + dz * dz
    t = np.clip(((x - x0) * dx + (z - z0) * dz) / L2, 0, 1)
    return np.hypot(x - (x0 + t * dx), z - (z0 + t * dz))


def _wrapd(a):
    return np.abs(np.remainder(a + PI, 2 * PI) - PI)


def _orient42(pc, f, want):
    n = face_normal(pc.verts, f)
    return tuple(reversed(f)) if n.dot(want) < 0 else tuple(f)


def plate42(name, origin, eu, ev, en, us, vtop, vbot, th, col, group='Extras'):
    """flat plate: for every u in us it spans v in [vbot(u), vtop(u)]; thickness th along en"""
    pc = Piece(name, group)
    T = []
    for u in us:
        row = []
        for v in (vtop(u), vbot(u)):
            p = origin + eu * u + ev * v
            row.append((pc.add_vert(p + en * th / 2), pc.add_vert(p - en * th / 2)))
        T.append(row)
    for k in range(len(us) - 1):
        (tf, tb), (bf, bb) = T[k]; (tf2, tb2), (bf2, bb2) = T[k + 1]
        pc.add_face(_orient42(pc, (tf, tf2, bf2, bf), en), None, col)
        pc.add_face(_orient42(pc, (tb, bb, bb2, tb2), -en), None, col)
        pc.add_face(_orient42(pc, (tf, tb, tb2, tf2), ev), None, col)
        pc.add_face(_orient42(pc, (bf, bf2, bb2, bb), -ev), None, col)
    for k, want in ((0, -eu), (len(us) - 1, eu)):
        (tf, tb), (bf, bb) = T[k]
        pc.add_face(_orient42(pc, (tf, bf, bb, tb), want), None, col)
    pc.rigid = True
    return pc


def build():
    pal = {'blk': BLK, 'blk2': BLK2, 'gun': GUN, 'gun_l': GUN_L, 'gun_d': GUN_D, 'cy': CY, 'cy_hot': CY_HOT,
           'mg': MG, 'mg_hot': MG_HOT, 'void': '#08080a'}
    P = []

    # ================================================================ hakama-cut trousers (wide, bloused into greaves)
    def hx(z, a):
        return 0.02 + 0.095 * max(0.0, math.sin(PI * min(1.0, max(0.0, (z - 1.0) / 0.95))))
    pt = pants('Hakama', 2.22, 0.6, 0.04, hip_off=0.065, leg_extra=hx, nseg=16)
    def hkp(U, V, m):
        img = P_solid('#17171c')(U, V, m); z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            for c in (0.45, 1.0, 2.1, 2.65):                 # deep hakama pleats (front and back)
                for sg in (1, -1):
                    img = mix(img, aa((np.abs(az - sg * c) - 0.012) * 250) * 0.8, '#09090c')
                    img = mix(img, aa((np.abs(az - sg * (c + 0.05)) - 0.008) * 250) * 0.5, BLK2)
            img = cyan(img, np.abs(np.abs(az) - PI / 2) * 0.24, 0.005)   # techwear piping down the outer / inner seam
        else:
            img = mix(img, aa((np.abs(az) - 0.01) * 300), '#09090c')
        return img
    for p in pt: p.paint = hkp
    P += pt

    # ================================================================ matte black do (cuirass jacket), hangs over the hakama
    do = torso_shell('Do', 1.98, 0.075, nseg=32, th=0.03, hang=2.3, over=pt,
                     extra=lambda z, a: 0.012 + 0.04 * max(0, 1 - abs(a) / 0.8) * max(0, min(1, (3.0 - z) / 0.3)) * max(0, min(1, (z - 2.3) / 0.2)))
    def dop(U, V, m):
        img = P_solid(BLK)(U, V, m); z, az = zc(U, V, m)
        x = az * 0.44
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300), BLK2)            # side seams
        # angular panel seams on the chest / back
        for sg in (1, -1):
            img = mix(img, aa((_seg(x, z, sg * 0.42, 3.05, sg * 0.62, 2.55) - 0.006) * K), BLK2)
            img = mix(img, aa((_seg(np.abs(_wrapd(az) - PI) * 0.44 * sg, z, sg * 0.25, 3.0, sg * 0.45, 2.5) - 0.006) * K), BLK2)
        # sternum light strip + glowing core node
        img = cyan(img, np.abs(x), 0.007, mask=(z > 2.5) * (z < 2.98))
        img = magenta(img, np.abs(np.hypot(x, (z - 2.47) * 1.0) - 0.028), 0.005)
        # flank circuit traces
        ax = np.abs(az)
        img = magenta(img, np.minimum(_seg(ax * 0.44, z, 1.2 * 0.44, 2.95, 1.2 * 0.44, 2.62), _seg(ax * 0.44, z, 1.2 * 0.44, 2.62, 1.45 * 0.44, 2.5)), 0.005)
        img = cyan(img, np.minimum(_seg(ax * 0.44, z, 1.85 * 0.44, 2.95, 1.85 * 0.44, 2.66), _seg(ax * 0.44, z, 1.85 * 0.44, 2.66, 1.65 * 0.44, 2.52)), 0.005)
        # twin spine strips down the back
        bx = (PI - _wrapd(az)) * 0.44
        img = cyan(img, np.abs(bx - 0.08), 0.006, mask=(z > 2.45) * (z < 3.02))
        img = magenta(img, np.abs(bx - 0.16), 0.004, mask=(z > 2.55) * (z < 2.95))
        img = magenta(img, np.abs(z - (m['zmin'] + 0.035)), 0.006)                         # hem light (seen through the tasset slits)
        return img
    do.paint = dop; do.sharp = False
    P.append(do)
    db = piece_bvh(do)

    # raised angular chest plates (projected onto the do)
    def cpp(U, V, m):
        w, h = 0.3, 0.44
        img = P_solid(BLK2)(U, V, m)
        e = np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h)
        img = mix(img, aa((e - 0.012) * K), GUN)                    # bevelled gunmetal rim
        img = mix(img, aa((e - 0.004) * K), GUN_D)
        img = cyan(img, np.abs(e - 0.026), 0.006)                   # inset neon outline
        img = magenta(img, _seg(U * w, V * h, 0.09, 0.08, 0.22, 0.08), 0.005)
        img = mix(img, aa((np.abs(V * h - 0.24) - 0.004) * K) * (e > 0.04), '#0c0c10')
        return img
    for sg in (1, -1):
        def fn(s, t, sg=sg):
            z = 2.5 + t * 0.44
            x0 = 0.075; x1 = 0.36 - 0.09 * (1 - t) - 0.05 * max(0, t - 0.8) / 0.2
            return Vector((sg * (x0 + s * (x1 - x0)), 0, z))
        cp = surface_patch(f'ChestPlate{sg}', db, fn, Vector((0, 1, 0)), 0.014, 6, 7, th=0.028)
        cp.paint = cpp; cp.rect_key = 'ChestPlate'; cp.meta['rect'] = (128, 128); cp.rigid = True; cp.sharp = True
        P.append(cp)

    # layered abdominal lames fitted on the do
    lames = []
    for k, (z0, z1) in enumerate(((2.26, 2.37), (2.36, 2.47))):
        lm = band(f'AbLame{k}', z0, z1, 0.012, bvh=db, th=0.022, extra=lambda z, a, z0=z0, z1=z1: 0.018 * (z1 - z) / (z1 - z0))
        def lp(U, V, m):
            img = P_solid('#1b1b21')(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa((V - 0.85) * -300), GUN)
            img = cyan(img, np.abs(V - 0.2) * 0.11, 0.006)
            return img
        lm.paint = lp; lm.rect_key = 'AbLame'; lm.sharp = True
        lames.append(lm)
    P += lames

    # ================================================================ kusazuri: 3 tiers of 6 split tassets over the hakama
    GAPS = PI / 3
    def tkeep(i, j, zc_, az):
        d = np.abs(az - np.round(az / GAPS) * GAPS)
        return d > 0.1
    def tp(U, V, m):
        img = P_solid(BLK)(U, V, m)
        az = 2 * PI * (U - 0.5)
        img = mix(img, np.clip(V, 0, 1) * 0.6, BLK2)
        dg = np.abs(az - np.round(az / GAPS) * GAPS)               # angle to the slit centre
        edge = (dg - 0.1309) * 0.56                                # distance to the panel side edge (units)
        img = mix(img, aa((edge - 0.008) * K), GUN_D)
        hz = V * 0.19
        img = mix(img, aa((hz - 0.007) * K), GUN)                  # gunmetal hem bead
        img = cyan(img, np.minimum(np.abs(edge - 0.024), np.abs(hz - 0.03)), 0.0065, mask=(hz > 0.016) * (edge > 0.012))
        cdist = (GAPS / 2 - np.abs(dg - GAPS / 2)) * 0.56          # distance from the panel centre line
        img = magenta(img, cdist, 0.005, mask=(V > 0.38) * (V < 0.72))
        # rivets near the top
        rv = np.hypot(np.abs(cdist - 0.075), (V - 0.84) * 0.19)
        img = mix(img, aa((rv - 0.011) * K), GUN_L)
        img = mix(img, aa((rv - 0.005) * K), GUN_D)
        return img
    legs_under = list(pt)
    under = [do] + lames
    tassets = []
    for k, (z0, z1, off) in enumerate(((2.02, 2.21, 0.1), (1.88, 2.07, 0.12), (1.74, 1.93, 0.14))):
        ts = torso_shell(f'Tasset{k}', z0, off, nseg=48, zs=[z0, (z0 + z1) / 2, z1], elevs=(), keep=tkeep,
                         extra=lambda z, a, z1=z1: 0.035 * (z1 - z) / 0.19, th=0.022, group='Bottom',
                         hang=z1 + 0.001, over=under + legs_under, over_gap=0.026)
        ts.paint = tp; ts.rect_key = 'Tasset'; ts.sharp = True
        P.append(ts); tassets.append(ts)
        under = under + [ts]

    # obi: gunmetal-edged black sash over the do + top tasset, magenta light core
    obi = band('Obi', 2.12, 2.3, 0.012, bvh=piece_bvh(do, tassets[0], *lames), th=0.025, hang=2.4)
    def obp(U, V, m):
        img = P_solid(BLK2)(U, V, m)
        img = mix(img, aa(np.minimum(V - 0.14, 0.86 - V) * 300), GUN)
        img = mix(img, aa(np.minimum(V - 0.06, 0.94 - V) * 300), GUN_D)
        img = magenta(img, np.abs(V - 0.5) * 0.18, 0.007)
        return img
    obi.paint = obp; obi.group = 'Bottom'
    P.append(obi)
    ob = piece_bvh(obi)
    # angular clasp: diamond gunmetal plate with a cyan reactor core
    loc, n = project(ob, Vector((0, 0, 2.21)), Vector((0, 1, 0)))
    n = Vector((n.x, n.y, 0)).normalized()
    Rq = Matrix.Rotation(PI / 4, 3, 'Y')
    cl = [prim_box('ObiClasp', loc + n * 0.02, (0.15, 0.04, 0.15), 'gun', rot=Rq),
          prim_box('ObiClaspRim', loc + n * 0.032, (0.115, 0.04, 0.115), 'gun_d', rot=Rq),
          prim_cyl('ObiCore', loc + n * 0.03, loc + n * 0.06, 0.04, n=6, col='cy'),
          prim_cyl('ObiCoreHot', loc + n * 0.05, loc + n * 0.064, 0.018, n=6, col='cy_hot')]
    for q in cl: q.bone = 'LowerTorso'; q.group = 'Bottom'
    P += cl

    # ================================================================ high neon-lined collar
    col_ = collar('Collar', 'stand', h=0.14, flare=0.2, open_front=0.36, th=0.025)
    def colp(U, V, m):
        img = P_solid(BLK)(U, V, m)
        img = mix(img, aa((V - 0.56) * 300), GUN)
        img = magenta(img, np.abs(V - 0.7) * 0.2, 0.004)
        img = cyan(img, np.abs(V - 0.93) * 0.2, 0.006)
        return img
    col_.paint = colp; col_.meta['rect'] = (256, 64)
    P.append(col_)
    n_row = (len(col_.verts) // 2) // 3
    top = col_.verts[2 * n_row:3 * n_row]
    nt = tube_path('CollarNeon', [p + (Vector((p.x, p.y, 0)).normalized() * 0.004) for p in top], 0.013, 'cy', n=6, group='Top', caps=True)
    head_clear(nt, 0.035); nt.bone = 'UpperTorso'
    P.append(nt)

    # ================================================================ arms: black sleeves, kote bracers
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        outer = -sg * PI / 2
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.95, 0.05, extra=lambda t, a: 0.01 + 0.012 * t)
        def slp(U, V, m, outer=outer):
            img = P_solid('#17171c')(U, V, m); az = 2 * PI * (U - 0.5)
            img = cyan(img, _wrapd(az - outer) * 0.13, 0.005, mask=(V < 0.62))
            img = mix(img, aa((np.abs(_wrapd(az - outer) - 0.35) - 0.01) * 200) * 0.6, BLK2)
            return img
        sl.paint = slp; sl.rect_key = 'Sleeve_' + s
        P.append(sl)
        kt = sleeve('Kote_' + s, s, 0.56, 0.95, 0.082, nrows=7, cap=False, th=0.02,
                    extra=lambda t, a, outer=outer: 0.004 + 0.02 * max(0, (t - 0.84) / 0.11)
                    + 0.012 * max(0, math.cos(a - outer)) ** 3)
        def ktp(U, V, m, outer=outer):
            img = P_solid(BLK)(U, V, m); az = 2 * PI * (U - 0.5)
            img = mix(img, V * 0.5, BLK2)
            ao = _wrapd(az - outer) * 0.15
            for vv in (0.3, 0.58):
                img = mix(img, aa((np.abs(V - vv) - 0.012) * 300), '#0c0c10')
            img = mix(img, aa((np.abs(ao - 0.06) - 0.003) * K), GUN)
            img = cyan(img, ao, 0.006, mask=(V > 0.06) * (V < 0.84))
            img = magenta(img, np.abs(V - 0.9) * 0.4, 0.006)
            img = mix(img, aa((V - 0.05) * 300) + aa((0.97 - V) * 300), GUN)
            return img
        kt.paint = ktp; kt.rect_key = 'Kote_' + s; kt.sharp = True
        P.append(kt)

    # ================================================================ o-sode: three overlapping rectangular lames per shoulder
    def sodep(U, V, m):
        img = P_solid(BLK)(U, V, m)
        img = mix(img, np.clip(V, 0, 1) * 0.55, BLK2)
        e = np.minimum(U, 1 - U) * 0.75
        img = mix(img, aa((V - 0.05) * 300) + aa((e - 0.01) * K), GUN)
        img = cyan(img, np.minimum(np.abs(V - 0.17) * 0.17, np.abs(e - 0.03) + (V < 0.17) * 1.0), 0.006)
        for c in (0.3, 0.5, 0.7):                            # odoshi lacing (glowing magenta)
            img = magenta(img, np.abs(U - c) * 0.75, 0.0045, mask=(V > 0.36) * (V < 0.8))
        return img
    sodes = []
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        ax_x = arm_point(s, 0.25)[0].x
        bv = side_bvh(s)
        phis = list(np.linspace(-1.2, 1.2, 11))
        R0 = []
        for ph in phis:
            d = Vector((sg * math.cos(ph), -math.sin(ph), 0))
            r = 0.2
            for z in np.linspace(2.4, 3.02, 10):
                c = Vector((ax_x, 0, z))
                h = bv.ray_cast(c + d * 1.0, -d, 1.0)
                if h[0] is not None: r = max(r, (h[0] - c).dot(d))
            R0.append(r)
        for _ in range(2):
            R0 = [max(R0[j], (R0[max(j - 1, 0)] + 2 * R0[j] + R0[min(j + 1, len(R0) - 1)]) / 4) for j in range(len(R0))]
        for k in range(3):
            zt = 3.02 - 0.14 * k; zb = zt - 0.21; off = 0.075 + 0.035 * k
            zs = [zb, (zb + zt) / 2, zt]
            rows = []; hints = []
            for z in zs:
                fl = 0.035 * (zt - z) / (zt - zb)
                row = []; hh = []
                for ph, r in zip(phis, R0):
                    d = Vector((sg * math.cos(ph), -math.sin(ph), 0))
                    row.append(Vector((ax_x, 0, z)) + d * (r + off + fl)); hh.append(d)
                rows.append(row); hints.append(hh)
            vv = [0.0, 0.42, 0.85]
            if k == 0:   # rolled top edge over the shoulder
                row = []; hh = []
                for ph, r in zip(phis, R0):
                    d = Vector((sg * math.cos(ph), -math.sin(ph), 0))
                    row.append(Vector((ax_x, 0, zt + 0.06)) + d * (r + off - 0.07)); hh.append((d + Z).normalized())
                rows.append(row); hints.append(hh); vv.append(1.0)
            else:
                vv = [0.0, 0.5, 1.0]
            sd = grid_piece(f'Sode{k}_' + s, rows, closed=False, v_vals=vv, hints=hints, group='Top')
            thicken(sd, 0.025)
            sd.paint = sodep; sd.rect_key = 'Sode'; sd.meta['rect'] = (128, 64)
            sd.bone = 'UpperTorso'; sd.sharp = True
            head_clear(sd, 0.03)
            P.append(sd); sodes.append(sd)

    # ================================================================ greaves (suneate) + armoured boots
    for s in 'LR':
        gr = _shin42(leg_tube('Suneate_' + s, s, 1.02, 0.5, 0.1, nseg=16, group='Feet', th=0.022,
                              extra=lambda z, a: 0.03 * max(0, math.cos(a)) ** 2 + 0.03 * max(0, (z - 0.92) / 0.1)))
        def grp(U, V, m):
            img = P_solid(BLK2)(U, V, m); z, az = zc(U, V, m)
            for c in (0.6, 1.2, 1.9, 2.5):
                for sg2 in (1, -1):
                    img = mix(img, aa((np.abs(az - sg2 * c) - 0.02) * 200), '#0e0e12')
            img = mix(img, aa((np.abs(np.abs(az) - 0.16) - 0.006) * 300), GUN)
            img = cyan(img, np.abs(az) * 0.16, 0.007, mask=(z > 0.56) * (z < 0.94))
            img = magenta(img, np.abs(z - 0.965), 0.006)
            img = mix(img, aa((z - 0.53) * 300), GUN)
            return img
        gr.paint = grp; gr.sharp = True
        P.append(gr)
        bt = shoe('Boot_' + s, s, off=0.05, bulk=0.035, toe=0.045, sole_h=0.06)
        def btp(U, V, m):
            img = P_solid(BLK)(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa((np.abs(az) - 0.5) * 200) * (z > m['sole_top'] + 0.02) * (z < m['sole_top'] + 0.12), BLK2)
            img = mix(img, aa((z - m['sole_top']) * 600), GUN_D)
            img = cyan(img, np.abs(z - (m['sole_top'] + 0.012)), 0.006)
            img = magenta(img, np.hypot(_wrapd(az - PI) * 0.15, z - (m['sole_top'] + 0.07)) - 0.012, 0.004)
            return img
        bt.paint = btp
        P.append(bt)

    # ================================================================ energy katana across the back
    cover = [do, obi, col_] + tassets + lames + sodes
    cb = piece_bvh(*cover)
    H = Vector((-0.34, 0, 3.17))          # tsuba (character's right shoulder)
    T = Vector((0.5, 0, 1.92))            # blade tip (character's left hip)
    def back_y(x, z):
        h = cb.ray_cast(Vector((x, 2.5, z)), Vector((0, -1, 0)), 3.0)
        return h[0].y if h[0] is not None else 0.0
    need = []
    for k in range(13):
        f = k / 12
        q = H.lerp(T, f)
        need.append((f, max(back_y(q.x + dx, q.z + dz) for dx in (-0.05, 0, 0.05) for dz in (-0.05, 0, 0.05)) + 0.06))
    y0 = max(nv for f, nv in need if f < 0.35); y1 = max(nv for f, nv in need if f > 0.65)
    lift = max(0.0, max(nv - (y0 + (y1 - y0) * f) for f, nv in need))
    H.y = y0 + lift; T.y = y1 + lift
    eu = (T - H).normalized(); Lb = (T - H).length
    en = Vector((0, 1, 0)); en = (en - en.dot(eu) * eu).normalized()
    ev = en.cross(eu).normalized()
    if ev.z < 0: ev = -ev                  # spine on the upper side
    kat = []
    us = list(np.linspace(0.05, Lb - 0.13, 8)) + [Lb - 0.09, Lb - 0.05, Lb - 0.02, Lb]
    def vtop(u):
        k0 = Lb - 0.13
        return 0.042 if u <= k0 else 0.042 - 0.08 * ((u - k0) / 0.13) ** 1.3
    kat.append(plate42('Blade', H, eu, ev, en, us, vtop, lambda u: -0.042, 0.016, 'cy'))
    kat.append(plate42('BladeCore', H, eu, ev, en, us[:-1], lambda u: min(0.011, vtop(u) - 0.012), lambda u: -0.016, 0.022, 'cy_hot'))
    at = lambda s_: H + eu * s_
    kat.append(prim_cyl('Habaki', at(0.0), at(0.06), 0.03, n=6, col='gun_l'))
    kat.append(prim_cyl('Emitter', at(0.02), at(0.045), 0.045, n=12, col='cy'))
    kat.append(prim_cyl('Tsuba', at(-0.02), at(0.012), 0.088, n=6, col='gun'))
    kat.append(prim_cyl('TsubaRing', at(-0.026), at(0.016), 0.062, n=6, col='mg'))
    kat.append(prim_cyl('Fuchi', at(-0.06), at(-0.02), 0.038, n=8, col='gun_l'))
    kat.append(prim_cyl('Tsuka', at(-0.38), at(-0.06), 0.034, r1=0.036, n=8, col='void'))
    for q in range(5):
        s0 = -0.09 - q * 0.058
        kat.append(prim_cyl(f'TsukaIto{q}', at(s0 - 0.018), at(s0), 0.04, n=8, col='mg'))
    kat.append(prim_cyl('Kashira', at(-0.42), at(-0.38), 0.042, r1=0.038, n=6, col='gun'))
    kat.append(prim_cyl('KashiraGem', at(-0.435), at(-0.415), 0.022, n=6, col='cy_hot'))
    # mag-lock clamps + struts down to the do
    for kk, f in enumerate((0.2, 0.62)):
        cpos = at(Lb * f)
        Rm = Matrix((eu, en, ev)).transposed()
        kat.append(prim_box(f'Clamp{kk}', cpos, (0.07, 0.05, 0.12), 'gun', rot=Rm))
        kat.append(prim_box(f'ClampLight{kk}', cpos + en * 0.026, (0.035, 0.01, 0.07), 'mg', rot=Rm))
        hb = cb.ray_cast(cpos, Vector((0, -1, 0)), 1.0)
        base = hb[0] if hb[0] is not None else cpos - en * 0.06
        mid = (base + cpos) / 2
        dd = (cpos - base).length + 0.03
        kat.append(prim_box(f'Strut{kk}', mid, (0.04, dd, 0.06), 'gun_d'))
    for q in kat:
        q.bone = 'UpperTorso'; q.group = 'Extras'
        head_clear(q, 0.03)
    P += kat
    return P, pal
