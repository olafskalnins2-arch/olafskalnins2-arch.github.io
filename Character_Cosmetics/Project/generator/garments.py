# Garment builders. All fitted to the imported default body via ray casting.
from lib import *
Z = Vector((0, 0, 1))

def hdirs_b(nseg):  # j=0 at back, j=n/2 front; az = -pi + 2pi j/n
    out = []
    for j in range(nseg):
        th = -PI + 2 * PI * j / nseg
        out.append(Vector((math.sin(th), -math.cos(th), 0)))
    return out

def azb(j, n): return -PI + 2 * PI * j / n

def tube_dirs_b(t, nseg, ref=Vector((0, -1, 0))):
    n, b = frame(t, ref)
    return [(n * math.cos(-PI + 2 * PI * j / nseg) + b * math.sin(-PI + 2 * PI * j / nseg)).normalized() for j in range(nseg)]

def _ring_len(r): return sum((r[j] - r[j - 1]).length for j in range(len(r)))

def filter_faces(pc, keep):
    F = []; U = []; C = []; IJ = []
    for f, uv, c, ij in zip(pc.faces, pc.fuv, pc.fcol, pc.meta['fij']):
        if keep(ij, f):
            F.append(f); U.append(uv); C.append(c); IJ.append(ij)
    pc.faces, pc.fuv, pc.fcol = F, U, C; pc.meta['fij'] = IJ
    # drop unused verts
    used = sorted(set(i for f in F for i in f)); m = {o: n for n, o in enumerate(used)}
    pc.verts = [pc.verts[i] for i in used]; pc.hint = [pc.hint[i] for i in used]
    pc.faces = [tuple(m[i] for i in f) for f in pc.faces]
    return pc

def _grid_with_ij(name, rows, closed, v_vals, hints, group, col=None, cap_start=None, cap_end=None):
    pc = grid_piece(name, rows, closed, v_vals=v_vals, hints=hints, group=group, col=col, cap_start=cap_start, cap_end=cap_end)
    M = len(rows); N = len(rows[0]); cols = N if closed else N - 1
    ij = [(i, j) for i in range(M - 1) for j in range(cols)]
    ij += [(-1, j) for j in range(cols)] if cap_start is not None else []
    ij += [(M - 1, j) for j in range(cols)] if cap_end is not None else []
    pc.meta['fij'] = ij
    return pc

def cut_slits(pc, N, z_s, sides=True):
    """Split the robe skirt below z_s into separate panels by duplicating vertices along cut columns (no position
    changes - it looks identical at rest). Front and back each keep a 2-face-wide centre tongue on the pelvis.
    Tags: +-1 front panel, +-3 back outer (side) strip, +-2 back inner strip (+ left, - right), 0 above the slit.
    Vertices on the cut centre line are duplicated; each copy belongs to the side of the panel it is attached to."""
    q = N // 4; e = N // 8
    def group(j):
        j %= N
        if N // 2 <= j <= N - 1:                                               # left half (cut exactly on the centre line)
            if not sides or j < 3 * q: return 1                               # front-left
            return 3 if j < 3 * q + e else 2                                   # back-left: outer (side) strip / inner strip
        if not sides or j >= q: return -1                                      # front-right
        return -3 if j >= q - e else -2                                        # back-right: outer strip / inner strip
    M = pc.meta['rows']
    dup = {}; tag = [0] * len(pc.verts); new_faces = []
    for (i, j), f in zip(pc.meta['fij'], pc.faces):
        g = group(j); nf = []
        for v in f:
            if v < M * N and pc.verts[v].z < z_s - 1e-6:
                c = v % N
                # vertex column c lies between face columns c-1 and c; if they belong to different groups, split
                gl, gr = group(c - 1), group(c)
                if gl != gr and g == gr:
                    key = (v, g)
                    if key not in dup:
                        dup[key] = len(pc.verts); pc.verts.append(pc.verts[v].copy()); pc.hint.append(pc.hint[v]); tag.append(g)
                    nf.append(dup[key]); continue
            nf.append(v)
        new_faces.append(tuple(nf))
    pc.faces = new_faces
    for (i, j), f in zip(pc.meta['fij'], pc.faces):
        g = group(j)
        if g:
            for v in f:
                if pc.verts[v].z < z_s - 1e-6: tag[v] = g
    pc.meta['panel'] = tag
    return pc

def torso_shell(name, z_bot, off, nseg=32, z_dome=2.95, elevs=(18, 34, 46, 54), nrows=None, zs=None,
                extra=None, bvh='torso', keep=None, group='Top', th=0.025, col=None, cap_bottom=False, smooth=2, slits=None):
    """Shell around torso from z_bot up to neck opening. extra(z, az)->radial add. keep(i,j,zc,az)->bool"""
    D = hdirs_b(nseg)
    if zs is None:
        nrows = nrows or max(3, int((z_dome - z_bot) / 0.09) + 1)
        zs = list(np.linspace(z_bot, z_dome, nrows))
    rows = []; hints = []; zrow = []
    for z in zs:
        ex = (lambda j, p, z=z: extra(z, azb(j, nseg))) if extra else None
        ring = ray_ring(B.bvh[bvh], Vector((0, 0, z)), D, off, R=1.8, extra=ex, smooth=smooth)
        rows.append(ring); hints.append(D); zrow.append(z)
    c = Vector((0, 0, z_dome))
    for e in elevs:
        e = math.radians(e)
        dirs = [(d * math.cos(e) + Z * math.sin(e)).normalized() for d in D]
        zz = None
        ex = (lambda j, p: extra(p.z, azb(j, nseg))) if extra else None
        ring = ray_ring(B.bvh['torso_up'], c, dirs, off, R=1.2, extra=ex, smooth=smooth)
        rows.append(ring); hints.append(dirs); zrow.append(sum(p.z for p in ring) / nseg)
    zmin, zmax = zrow[0], zrow[-1]
    vv = [(z - zmin) / (zmax - zmin) for z in zrow]
    cap = Vector((0, 0, zs[0] - 0.03)) if cap_bottom else None
    pc = _grid_with_ij(name, rows, True, vv, hints, group, col, cap_start=cap)
    pc.meta.update(zmin=zmin, zmax=zmax, circ=_ring_len(rows[len(rows) // 2]), nseg=nseg, kind='torso')
    if keep:
        filter_faces(pc, lambda ij, f: keep(ij[0], ij[1], sum(pc.verts[i].z for i in f) / len(f), azb(ij[1] + 0.5, nseg)))
    if slits: cut_slits(pc, nseg, slits)
    if th: thicken(pc, th)
    if slits:
        n0 = pc.meta['n_outer_verts']; t = pc.meta['panel']; pc.meta['panel'] = t + t[:n0] + [0] * (len(pc.verts) - n0 - len(t))
        pc.meta['slit_top'] = slits
    pc.region = 'torso'; pc.skirt = True
    return pc

def sleeve(name, side, t0, t1, off, nseg=14, nrows=None, extra=None, cap=True, group='Top', th=0.02, col=None, smooth=1):
    """extra(t, az) radial add."""
    nrows = nrows or max(3, int((t1 - t0) * 12) + 2)
    ts = list(np.linspace(t0, t1, nrows))
    rows = []; hints = []; vv = []
    bvh = B.bvh['arm_' + side]
    for t in ts:
        c, tg = arm_point(side, t)
        dirs = tube_dirs_b(tg, nseg)
        ex = (lambda j, p, t=t: extra(t, azb(j, nseg))) if extra else None
        ring = ray_ring(bvh, c, dirs, off, R=0.7, extra=ex, smooth=smooth)
        rows.append(ring); hints.append(dirs); vv.append(t)
    if cap and t0 <= 0.001:
        c, tg = arm_point(side, 0.0)
        base = tube_dirs_b(tg, nseg); capr = []; caph = []
        for e in (35, 62):
            e = math.radians(e)
            dirs = [(d * math.cos(e) - tg * math.sin(e)).normalized() for d in base]
            capr.append(ray_ring(bvh, c, dirs, off, R=0.7, smooth=smooth)); caph.append(dirs)
        rows = capr[::-1] + rows; hints = caph[::-1] + hints; vv = [-0.06, -0.03] + vv
        h = bvh.ray_cast(c - tg * 0.7, tg, 0.7)
        top = (h[0] - tg * off) if h[0] else c - tg * 0.15
        pc = _grid_with_ij(name, rows, True, vv, hints, group, col, cap_start=top)
    else:
        pc = _grid_with_ij(name, rows, True, vv, hints, group, col)
    pc.meta.update(kind='sleeve', circ=_ring_len(rows[-1]), t0=t0, t1=t1, vmin=vv[0], vmax=vv[-1])
    # normalise v into 0..1 for painting; keep t in meta
    vmin, vmax = vv[0], vv[-1]
    pc.fuv = [[(u, (v - vmin) / (vmax - vmin)) for u, v in uv] for uv in pc.fuv]
    if th: thicken(pc, th)
    pc.rect_key = name.replace('_L', '').replace('_R', '')
    pc.region = 'arm_' + side
    return pc

def leg_tube(name, side, z0, z1, off, nseg=16, nrows=None, extra=None, group='Bottom', th=0.02, col=None, bvh=None, smooth=2):
    """z0 top > z1 bottom"""
    nrows = nrows or max(3, int((z0 - z1) / 0.1) + 2)
    zs = list(np.linspace(z0, z1, nrows))
    rows = []; hints = []
    bv = B.bvh[bvh or ('leg_' + side)]
    for z in zs:
        c = leg_point(side, z)
        tg = (leg_point(side, z + 0.05) - leg_point(side, z - 0.05)); tg = tg.normalized() if tg.length > 1e-6 else Z
        dirs = tube_dirs_b(-tg, nseg) if False else hdirs_b(nseg)
        ex = (lambda j, p, z=z: extra(z, azb(j, nseg))) if extra else None
        ring = ray_ring(bv, c, dirs, off, R=0.8, extra=ex, smooth=smooth)
        rows.append(ring); hints.append(dirs)
    vv = [(z - z1) / (z0 - z1) for z in zs]
    pc = _grid_with_ij(name, rows, True, vv, hints, group, col)
    pc.meta.update(kind='leg', zmin=z1, zmax=z0, circ=_ring_len(rows[len(rows) // 2]), side=side)
    if th: thicken(pc, th)
    pc.region = 'leg_' + side
    pc.rect_key = name.replace('_L', '').replace('_R', '')
    return pc

def pants(prefix, z_waist, z_end, off, hip_off=None, extra=None, leg_extra=None, nseg=16, group='Bottom', th=0.02):
    hip_off = hip_off or off + 0.018
    hip = torso_shell(prefix + 'Hip', 1.86, hip_off, nseg=32, zs=list(np.linspace(1.86, z_waist, max(3, int((z_waist - 1.86) / 0.08) + 1))), elevs=(), extra=extra, group=group, th=th, cap_bottom=True)
    hip.meta['kind'] = 'hip'; hip.skirt = False
    L = leg_tube(prefix + 'Leg_L', 'L', 2.0, z_end, off, nseg=nseg, extra=leg_extra, group=group, th=th)
    R = leg_tube(prefix + 'Leg_R', 'R', 2.0, z_end, off, nseg=nseg, extra=(lambda z, a: leg_extra(z, -a)) if leg_extra else None, group=group, th=th)
    return [hip, L, R]

def shoe(name, side, off=0.035, sole_z=0.305, open_elev=48, nseg=20, extra=None, group='Feet', th=0.02, col=None, bvh=None,
         sole_h=0.06, bulk=0.0, toe=0.0):
    """Chunky flat-soled shoe fitted around the foot. extra(e, az, p) adds radial bulk for upper rows."""
    sg = 1 if side == 'L' else -1
    c = Vector((0.255 * sg, -0.08, 0.44))
    bv = B.bvh[bvh or ('footleg_' + side)]
    D = hdirs_b(nseg)
    elevs = [-20, -5, 10, 24, 37, open_elev]
    rows = []; hints = []
    for e in elevs:
        er = math.radians(e)
        dirs = [(d * math.cos(er) + Z * math.sin(er)).normalized() for d in D]
        ex = (lambda j, p, e=e: (extra(e, azb(j, nseg) * sg, p) if extra else 0) + bulk * max(0, 1 - max(e, 0) / 40)) 
        ring = ray_ring(bv, c, dirs, off, R=0.9, extra=ex, smooth=1)
        if ring is None: ring = [p + Z * 0.05 for p in rows[-1]]
        rows.append(ring); hints.append(dirs)
    # toe extension (front)
    if toe:
        for r in rows[:3]:
            for j, p in enumerate(r):
                f = max(0, -math.cos(azb(j, nseg) + PI) )  # front weight
                fy = max(0.0, math.cos(azb(j, nseg)))
                r[j] = p + Vector((0, -toe * fy ** 2, 0))
    # vertical sides down to a flat sole
    top = rows[0]
    lower = []
    for k, (sc, zz) in enumerate(((1.0, sole_z + sole_h), (1.0, sole_z + 0.012), (0.97, sole_z))):
        lower.append([Vector((c.x + (p.x - c.x) * sc, c.y + (p.y - c.y) * sc, min(zz, p.z))) for p in top])
    rows = lower[::-1] + rows; hints = [[(p - c) for p in r] for r in rows]
    for r in rows[:3]:
        pass
    vv = [p[0].z for p in rows]
    zmin, zmax = sole_z, max(p.z for r in rows for p in r)
    vv = [(sum(p.z for p in r) / len(r) - zmin) / (zmax - zmin) for r in rows]
    vv[0] = 0.0
    bot = Vector((c.x, c.y - toe * 0.4, sole_z))
    pc = _grid_with_ij(name, rows, True, vv, hints, group, col, cap_start=bot)
    pc.meta.update(kind='shoe', zmin=zmin, zmax=zmax, circ=_ring_len(rows[3]), sole_top=sole_z + sole_h)
    if th: thicken(pc, th)
    pc.region = 'foot_' + side
    pc.rect_key = name.replace('_L', '').replace('_R', '')
    return pc

def band(name, z0, z1, off, nseg=32, extra=None, group='Top', th=0.02, col=None, bvh='torso'):
    pc = torso_shell(name, z0, off, nseg=nseg, zs=[z0, (z0 + z1) / 2, z1], elevs=(), extra=extra, group=group, th=th, col=col, bvh=bvh)
    pc.rect_key = name
    return pc

def neck_ring_pts(pc_shell_top_z=3.2, r=0.27, n=24, z=3.2):
    return [Vector((r * math.sin(2 * PI * j / n), -r * math.cos(2 * PI * j / n), z)) for j in range(n)]

def collar(name, kind='stand', h=0.07, r0=None, flare=0.04, open_front=0.0, n=24, col=None, group='Top', z=None, fold=0.09, th=0.018, lift=0.0):
    """Collar around neck opening, built from the torso top. open_front: half-angle (rad) gap at front."""
    bv = B.bvh['torso_up']
    base = []; dirs = []
    angs = []
    for j in range(n + (1 if open_front else 0)):
        if open_front:
            a = open_front + (2 * PI - 2 * open_front) * j / n
        else:
            a = 2 * PI * j / n
        angs.append(a)
    for a in angs:
        d = Vector((math.sin(a), -math.cos(a), 0))
        # find torso top surface at radius ~0.26 from neck
        for rr in (0.25,):
            p = Vector((0, 0, 3.35)) + d * rr
            hh = bv.ray_cast(p, Vector((0, 0, -1)), 1.0)
            zt = hh[0].z if hh[0] else 3.18
        base.append(Vector((d.x * rr, d.y * rr, zt + 0.02 + lift))); dirs.append(d)
    rows = [[p - Z * 0.03 + dirs[k] * 0.01 for k, p in enumerate(base)], base,
            [p + Z * h + dirs[k] * flare for k, p in enumerate(base)]]
    if kind == 'fold':
        rows.append([p + Z * (h - fold) + dirs[k] * (flare + 0.07) for k, p in enumerate(base)])
    hints = [[d for d in dirs] for _ in rows]
    if kind == 'fold':
        hints[-1] = [d + Z for d in dirs]
    pc = _grid_with_ij(name, rows, closed=not open_front, v_vals=[i / (len(rows) - 1) for i in range(len(rows))], hints=hints, group=group, col=col)
    head_clear(pc, 0.025)
    if th: thicken(pc, th)
    pc.rigid = False; pc.region = 'torso'; pc.skirt = False
    return pc

def head_shell(name, off, open_deg=58, nphi=7, npsi=24, group='Head', col=None, th=0.03, zcut=None):
    """Hood-like shell around the head; opening is a cone around -Y (face)."""
    bv = B.bvh['head']
    c = HEAD_C
    phis = list(np.linspace(open_deg, 178, nphi))
    rows = []; hints = []
    for ph in phis:
        ph = math.radians(ph)
        dirs = []
        for k in range(npsi):
            ps = 2 * PI * k / npsi
            d = Vector((0, -1, 0)) * math.cos(ph) + (Vector((math.sin(ps), 0, math.cos(ps)))) * math.sin(ph)
            dirs.append(d.normalized())
        ring = ray_ring(bv, c, dirs, off, R=1.3, smooth=1)
        rows.append(ring); hints.append(dirs)
    pc = _grid_with_ij(name, rows, True, [i / (nphi - 1) for i in range(nphi)], hints, group, col, cap_end=c + Vector((0, 1, 0)) * (HEAD_R + off))
    pc.meta.update(kind='hood', circ=_ring_len(rows[-2]))
    pc.meta['rim'] = rows[0]
    if th: thicken(pc, th)
    pc.region = 'head'
    return pc
