from o04 import *
NUM, NAME, RARITY, MAXD = '24', 'Shadow_Ninja', 'Rare', 0.4

# ---------------------------------------------------------------- local helpers (no shared-file edits)
def _shin24(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def _ribbon(name, pts, w0, w1, col, th=0.016, group='Extras', bone='UpperTorso', side_ref=Vector((1, 0, 0)),
            out_ref=Vector((0, -1, 0)), twist=None):
    """flat cloth strip (scarf / sash tail) along pts, rigid on one bone"""
    pts = [Vector(p) for p in pts]; M = len(pts)
    rows = []; hints = []
    for i, p in enumerate(pts):
        f = i / (M - 1)
        t = (pts[min(i + 1, M - 1)] - pts[max(i - 1, 0)]).normalized()
        s = side_ref - side_ref.dot(t) * t
        s = s.normalized() if s.length > 1e-6 else Vector((1, 0, 0))
        if twist: s = Matrix.Rotation(twist(f), 3, t) @ s
        n = t.cross(s).normalized()
        if n.dot(out_ref) < 0: n = -n
        w = (w0 + (w1 - w0) * f) / 2
        rows.append([p - s * w, p + s * w]); hints.append([n, n])
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group)
    thicken(pc, th)
    pc.rigid = True; pc.bone = bone
    return pc

def _shuriken(name, center, normal, R=0.095, r=0.03, th=0.014, rot=0.0, col='steel', bone='LowerTorso'):
    n = normal.normalized()
    a, b = frame(n, Vector((0, 0, 1)))
    pts = []
    for k in range(8):
        ang = rot + PI * k / 4
        rr = R if k % 2 == 0 else r
        # blades slightly hooked: inner points rotated a bit
        if k % 2: ang += 0.18
        pts.append(center + (a * math.cos(ang) + b * math.sin(ang)) * rr)
    pc = Piece(name, 'Extras')
    top = [pc.add_vert(p + n * th / 2, n) for p in pts]; bot = [pc.add_vert(p - n * th / 2, -n) for p in pts]
    ct = pc.add_vert(center + n * th / 2, n); cb = pc.add_vert(center - n * th / 2, -n)
    for k in range(8):
        k2 = (k + 1) % 8
        pc.add_face([top[k], top[k2], ct], None, col)
        pc.add_face([bot[k2], bot[k], cb], None, col)
        pc.add_face([top[k2], top[k], bot[k], bot[k2]], None, col)
    orient_each(pc, center)
    pc.rigid = True; pc.bone = bone
    return pc

def _wrap_img(img, x, z, circ, strap, edge, n=3, slope=0.9, w=0.026):
    """criss-cross binding straps (seamless around the tube: period = circ / n)"""
    P = circ / n
    for sgn in (1, -1):
        d = np.abs(((x + sgn * slope * z) / P + 0.5) % 1.0 - 0.5) * P
        img = mix(img, aa((d - w - 0.007) * 700), edge)
        img = mix(img, aa((d - w) * 700), strap)
    return img

def _tabi_split(sh, side, xs, depth=0.055, width=0.022):
    """push a groove into the toe between the big toe and the other toes (split-toe tabi)"""
    n0 = sh.meta['n_outer_verts']; st = sh.meta['sole_top']
    bv = B.bvh['footleg_' + side]
    ymin = min(p.y for p in sh.verts[:n0])
    for i in range(n0):
        p = sh.verts[i]
        if p.z < st + 0.004 or p.z > 0.6: continue
        f = math.exp(-((p.x - xs) / width) ** 2) * min(1.0, max(0.0, (ymin + 0.13 - p.y) / 0.07))
        dm = depth * f
        if dm < 1e-4: continue
        for _ in range(12):
            q = p + Vector((0, dm, 0))
            loc, nor, fi, dist = bv.find_nearest(q)
            if loc is None or ((q - loc).dot(nor) > 0.02): break
            dm *= 0.7
        mv = Vector((0, dm, 0))
        sh.verts[i] = p + mv; sh.verts[i + n0] = sh.verts[i + n0] + mv
    return sh


def build():
    pal = {'black': '#1a1a1f', 'char': '#2b2b33', 'char_l': '#474752', 'red': '#c0262d', 'red_d': '#8e1a20',
           'steel': '#b9bec5', 'steel_d': '#7d838b', 'lacquer': '#101014', 'sole': '#3b3b43', 'mail': '#5c6068',
           'dark': '#0c0c0f'}
    P = []

    # ---------------------------------------------------------------- loose trousers (charcoal), bloused above the wraps
    def lx(z, a):
        return 0.008 + 0.065 * max(0.0, math.sin(PI * min(1.0, max(0.0, (z - 0.98) / 0.85)))) + 0.012 * max(0.0, min(1.0, (1.8 - z) / 0.4)) * (z > 1.4)
    pt = pants('Hakama', 2.2, 0.64, 0.035, hip_off=0.07, leg_extra=lx, nseg=16)
    def ppaint(U, V, m):
        img = P_solid(pal['char'])(U, V, m); z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, '#222229')
            # soft fold lines of the bloused leg
            for c in (0.6, -0.7, 2.4):
                img = mix(img, aa((np.abs(az - c) - 0.01) * 200) * 0.35 * (z > 1.05) * (z < 1.8), '#232329')
        return img
    for p in pt: p.paint = ppaint

    # ---------------------------------------------------------------- black gi jacket (hangs over the trousers)
    gi = torso_shell('Gi', 1.76, 0.06, nseg=32, extra=lambda z, a: 0.015 + 0.05 * max(0, 2.1 - z), th=0.025, hang=2.3, over=pt)
    def gipaint(U, V, m):
        img = P_solid(pal['black'])(U, V, m); z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 300) * 0.8, pal['char'])        # side seams
        img = mix(img, aa((np.abs(az + 0.69) - 0.007) * 400) * (z < 2.12), pal['char_l'])        # left panel edge (over the right)
        img = mix(img, aa((z - (m['zmin'] + 0.06)) * 600), pal['char'])                           # hem band
        # red clan crest between the shoulder blades
        dx = np.remainder(az, 2 * PI) - PI; dx = dx * 0.5; dz = z - 2.66
        r = np.sqrt(dx ** 2 + dz ** 2); th = np.arctan2(dz, dx)
        img = mix(img, aa((np.abs(r - 0.115) - 0.011) * 500), pal['red'])
        edge = 0.095 * (0.22 + 0.78 * (0.5 + 0.5 * np.cos(4 * th + 0.785)) ** 3)
        img = mix(img, aa((r - edge) * 500), pal['red'])
        img = mix(img, aa((r - 0.016) * 500), pal['black'])
        return img
    gi.paint = gipaint
    P.append(gi)
    P += pt
    gb = piece_bvh(gi)

    # wrap-front collar: chain-mail undershirt in the V, right panel band under the left panel band
    zt = 3.12; x0 = 0.15; k = 0.53
    eL = lambda z: x0 - k * (zt - z)          # left panel edge (crosses to the right hip)
    eR = lambda z: -x0 + k * (zt - z)
    zx = zt - x0 / k                           # crossing point
    zlo = zx - 0.02
    def vfn(s, t):
        z = zlo + t * (zt + 0.02 - zlo)
        a, b = eR(z) - 0.03, eL(z) + 0.03
        return Vector((a + s * (b - a), 0, z))
    mail = surface_patch('MailV', gb, vfn, Vector((0, 1, 0)), 0.005, 7, 6, th=0.005)
    def mpaint(U, V, m):
        z = zlo + V * (zt + 0.02 - zlo)
        a = -x0 + k * (zt - z) - 0.03; b = x0 - k * (zt - z) + 0.03
        x = a + U * (b - a)
        img = P_solid('#1f1f25')(U, V, m)
        c = 0.03
        row = np.floor(z / c); xx = x / c + 0.5 * (row % 2)
        dx = (xx - np.floor(xx) - 0.5) * c; dz = (z / c - row - 0.5) * c
        rr = np.sqrt(dx ** 2 + dz ** 2)
        img = mix(img, aa((np.abs(rr - 0.0105) - 0.0035) * 1500), pal['mail'])
        img = mix(img, aa((np.abs(rr - 0.0105) - 0.0012) * 1500) * (dz > 0), '#8a8f97')
        return img
    mail.paint = mpaint; mail.meta['rect'] = (256, 128); P.append(mail)
    cw = 0.085
    bandR = surface_patch('CollarBandR', gb, lambda s, t: Vector((eR(zt - t * (zt - (zx - 0.03))) - cw * s, 0, zt - t * (zt - (zx - 0.03)))),
                          Vector((0, 1, 0)), 0.014, 3, 6, col='char', th=0.008)
    P.append(bandR)
    bandL = surface_patch('CollarBandL', gb, lambda s, t: Vector((eL(zt - t * (zt - 2.2)) + cw * s, 0, zt - t * (zt - 2.2))),
                          Vector((0, 1, 0)), 0.026, 3, 12, col='char', th=0.01)
    P.append(bandL)

    # sleeves + forearm bindings
    for s in 'LR':
        sl = sleeve('GiSleeve_' + s, s, 0.0, 0.62, 0.055, extra=lambda t, a: 0.015 + 0.06 * t / 0.62)
        sl.paint = lambda U, V, m: mix(P_solid(pal['black'])(U, V, m), aa((0.93 - V) * 400), pal['char'])
        P.append(sl)
        aw = sleeve('ArmWrap_' + s, s, 0.55, 0.96, 0.035, nseg=14, cap=False, extra=lambda t, a: 0.006 + 0.012 * max(0, (0.66 - t) / 0.11))
        L = sum((arm_point(s, 0.55 + 0.41 * (q + 1) / 20)[0] - arm_point(s, 0.55 + 0.41 * q / 20)[0]).length for q in range(20))
        aw.meta['length'] = L
        def awp(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            x, z = phys(U, V, m)
            img = mix(img, aa(np.abs(((z / 0.045) % 1.0) - 0.5) * 8 - 3.2) * 0.5, '#26262d')
            img = _wrap_img(img, x, z, m['circ'], pal['char_l'], pal['dark'], n=2, slope=0.8, w=0.02)
            img = mix(img, aa((np.minimum(V, 1 - V) - 0.06) * 300), pal['char'])
            return img
        aw.paint = awp; aw.rect_key = 'ArmWrap'
        P.append(aw)

    # ---------------------------------------------------------------- red sash with knot + two hanging tails
    sash = band('Sash', 2.08, 2.30, 0.03, bvh=gb, th=0.03, hang=2.4)
    def spaint(U, V, m):
        img = P_solid(pal['red'])(U, V, m); z, az = zc(U, V, m)
        for c in (0.36, 0.66): img = mix(img, aa(np.abs(V - c) * 300 - 0.6) * 0.8, pal['red_d'])
        img = mix(img, aa(np.minimum(V - 0.06, 0.94 - V) * -300), pal['red_d'])
        return img
    sash.paint = spaint; P.append(sash)
    sb = piece_bvh(sash)
    loc, n = project(sb, Vector((0.16, 0, 2.19)), Vector((0, 1, 0)))
    ang = math.atan2(n.x, -n.y); Rk = Matrix.Rotation(ang, 3, 'Z')
    kc = loc + n * 0.05
    P.append(prim_rbox('SashKnot', kc, (0.15, 0.09, 0.13), 'red_d', rot=Rk))
    tg = Rk @ Vector((1, 0, 0))
    for sg in (-1, 1):
        P.append(prim_rbox(f'SashLoop{sg}', kc + tg * (0.085 * sg) + n * -0.012 + Vector((0, 0, 0.012)), (0.09, 0.06, 0.1), 'red',
                           rot=Rk @ Matrix.Rotation(-0.35 * sg, 3, 'Y')))
    for k_, (xa, xb, zb, w0, w1) in enumerate(((0.14, 0.07, 1.70, 0.075, 0.065), (0.19, 0.28, 1.75, 0.07, 0.06))):
        pts = []
        for q in range(9):
            f = q / 8
            z = 2.13 - f * (2.13 - zb); x = xa + (xb - xa) * f + 0.012 * math.sin(f * PI * 2 + k_)
            lo, nn = project(gb, Vector((x, 0, max(z, 1.82))), Vector((0, 1, 0)))
            pts.append(Vector((lo.x, lo.y, z)) + nn * 0.062 + Vector((0, -0.01 * max(0, 1.82 - z) / 0.1, 0)))
        P.append(_ribbon(f'SashTail{k_}', pts, w0, w1, 'red', th=0.014, bone='LowerTorso', group='Extras'))
    for p in P[-5:]: p.bone = "LowerTorso"   # knot, loops, tails

    # two shuriken tucked in the sash (wearer's right front / side)
    for k_, (az, z, rot) in enumerate(((-0.62, 2.2, 0.3), (-1.02, 2.17, 0.9))):
        d = Vector((math.sin(az), -math.cos(az), 0))
        lo, nn = project(sb, d * 1.6 + Vector((0, 0, z)), -d)
        c = lo + nn * 0.012
        P.append(_shuriken(f'Shuriken{k_}', c, nn, rot=rot))
        P.append(prim_cyl(f'ShurikenHole{k_}', c - nn * 0.012, c + nn * 0.012, 0.016, n=8, col='dark'))
        P[-1].bone = 'LowerTorso'

    # ---------------------------------------------------------------- wakizashi across the lower back (tucked in the sash)
    H = Vector((-0.63, 0, 2.38)); T = Vector((0.6, 0, 2.07))
    back = piece_bvh(gi, sash); yb = 0.0
    for q in range(25):
        p = H.lerp(T, q / 24)
        for dz in (-0.045, 0.0, 0.045):
            lo, nn = project(back, Vector((p.x, 0, p.z + dz)), Vector((0, -1, 0)))
            if lo is not None: yb = max(yb, lo.y + 0.05)
    H.y = yb; T.y = yb
    dv = (T - H).normalized(); Ls = (T - H).length
    at = lambda s: H + dv * s
    sw = []
    sw.append(prim_cyl('Kashira', at(0.0), at(0.035), 0.034, r1=0.037, n=10, col='steel'))
    sw.append(prim_cyl('Tsuka', at(0.035), at(0.29), 0.034, r1=0.036, n=10, col='black'))
    for q in range(5):
        s0 = 0.06 + q * 0.047
        sw.append(prim_cyl(f'TsukaIto{q}', at(s0), at(s0 + 0.022), 0.039, n=10, col='red'))
    sw.append(prim_cyl('Fuchi', at(0.29), at(0.315), 0.041, n=10, col='steel'))
    sw.append(prim_cyl('Tsuba', at(0.315), at(0.335), 0.085, n=14, col='steel_d'))
    sw.append(prim_cyl('Koiguchi', at(0.335), at(0.375), 0.043, n=10, col='steel'))
    sw.append(prim_cyl('Saya', at(0.375), at(Ls - 0.035), 0.041, r1=0.036, n=10, col='lacquer'))
    sw.append(prim_cyl('Sageo', at(0.43), at(0.47), 0.046, n=10, col='red'))
    sw.append(prim_cyl('Kojiri', at(Ls - 0.035), at(Ls), 0.036, r1=0.03, n=10, col='steel'))
    for p in sw: p.bone = 'LowerTorso'; p.group = 'Extras'
    P += sw

    # ---------------------------------------------------------------- red neck scarf + knot + two long tails behind
    scarf = collar('Scarf', 'fold', h=0.12, flare=0.08, fold=0.13, col='red', th=0.04)
    P.append(scarf)
    lo, nn = project(piece_bvh(scarf), Vector((0, 0, 3.24)), Vector((0, -1, 0)))
    K = lo + nn * 0.04
    kn = prim_rbox('ScarfKnot', K, (0.17, 0.1, 0.13), 'red_d', group='Extras')
    head_clear(kn, 0.03); kn.bone = 'UpperTorso'; P.append(kn)
    for sg in (-1, 1):
        ctrl = [K + Vector((0.04 * sg, 0.03, -0.04)), K + Vector((0.10 * sg, 0.15, -0.13)), K + Vector((0.15 * sg, 0.28, -0.30)),
                K + Vector((0.20 * sg, 0.38, -0.50)), K + Vector((0.24 * sg, 0.45, -0.70)), K + Vector((0.28 * sg, 0.50, -0.88))]
        pts = smooth_line(polyline_resample(ctrl, 14), 2)
        pts = [p + Vector((0.025 * sg * math.sin(i / 13 * PI * 2.2), 0, 0)) for i, p in enumerate(pts)]
        tl = _ribbon(f'ScarfTail{sg}', pts, 0.18, 0.13, 'red', th=0.018, bone='UpperTorso', group='Extras',
                     out_ref=Vector((0, 0.6, 1)), twist=lambda f, sg=sg: 0.3 * sg * math.sin(f * PI * 1.3))
        head_clear(tl, 0.03); P.append(tl)

    # ---------------------------------------------------------------- shin wraps + split-toe tabi
    for s in 'LR':
        sg = 1 if s == 'L' else -1
        wr = _shin24(leg_tube('ShinWrap_' + s, s, 1.04, 0.56, 0.074, nseg=16, group='Feet',
                              extra=lambda z, a: 0.002 + 0.016 * max(0, (z - 0.88) / 0.16) - 0.008 * max(0, (0.66 - z) / 0.1)))
        def wp(U, V, m):
            img = P_solid(pal['black'])(U, V, m)
            x, z = phys(U, V, m)
            img = mix(img, aa(np.abs(((z / 0.05) % 1.0) - 0.5) * 8 - 3.2) * 0.5, '#26262d')
            img = _wrap_img(img, x, z, m['circ'], pal['char_l'], pal['dark'], n=3, slope=0.9, w=0.024)
            img = mix(img, aa((np.minimum(V, 1 - V) - 0.05) * 300), pal['char'])
            return img
        wr.paint = wp; wr.rect_key = 'ShinWrap'
        P.append(wr)
        sh = shoe('Tabi_' + s, s, off=0.035, bulk=0.02, toe=0.05, sole_h=0.04, open_elev=50, nseg=32)
        xs = 0.255 * sg - 0.055 * sg
        _tabi_split(sh, s, xs)
        azs = math.atan2(xs - 0.255 * sg, 0.28)
        def tp(U, V, m, azs=azs):
            img = P_solid(pal['black'])(U, V, m); z, az = zc(U, V, m)
            img = mix(img, aa((np.abs(az - azs) - 0.02) * 300) * (z > m['sole_top']) * (z < 0.5), pal['dark'])
            img = mix(img, aa((z - m['sole_top']) * 600), pal['sole'])
            return img
        sh.paint = tp; sh.rect_key = 'Tabi_' + s
        P.append(sh)
        # split toe: big-toe lobe + four-toe lobe on the toe cap, a crease between them
        n0 = sh.meta['n_outer_verts']; st = sh.meta['sole_top']
        ymin = min(p.y for p in sh.verts[:n0])
        for nm, cx, rx, ry, rz in (('BigToe', xs - 0.048 * sg, 0.042, 0.06, 0.05), ('Toes', xs + 0.075 * sg, 0.07, 0.06, 0.045)):
            c = Vector((cx, ymin + ry * 0.92, st + rz * 0.9))
            lb = prim_sphere(f'Tabi{nm}_' + s, c, 1.0, 'black', nl=6, seg=12, scale=(rx, ry, rz), group='Feet')
            lb.bone = ('LeftFoot' if s == 'L' else 'RightFoot'); P.append(lb)
    return P, pal
