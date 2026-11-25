# Core fitting + mesh toolkit for building cosmetics around the default character.
import bpy, math, os, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

GLB = __import__('os').environ.get('CHARACTER_GLB', 'character_smooth_v2.glb')
BONES = ['LowerTorso','UpperTorso','Head','LeftUpperArm','LeftLowerArm','LeftHand','RightUpperArm',
         'RightLowerArm','RightHand','LeftUpperLeg','LeftLowerLeg','LeftFoot','RightUpperLeg','RightLowerLeg','RightFoot']
PI = math.pi
HEAD_C = Vector((0, -0.012, 4.029)); HEAD_R = 0.786

class Body:
    pass
B = Body()

def pose_matrices(arm):
    """skinning matrices (pose @ rest^-1, armature space) for every check_rig pose"""
    import importlib, sys as _s
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, '..', '..', 'Roblox_Ready'), os.path.join(here, '..', '..', 'Roblox_Ready')):
        if os.path.exists(os.path.join(cand, 'check_rig.py')): _s.path.insert(0, os.path.abspath(cand)); break
    import check_rig as C
    out = {}
    for name, spec in C.POSES.items():
        C.apply_pose(arm, spec)
        out[name] = np.array([np.array(arm.pose.bones[b].matrix @ arm.data.bones[b].matrix_local.inverted()) for b in BONES])
    C.reset_pose(arm); bpy.context.view_layer.update()
    return out

def cap_shoulder_holes(me):
    """The base mesh has OPEN shoulder seams: the torso has a socket hole and each arm an open end, stitched at
    coincident verts. With rig-safe (hard) shoulder weights those openings show the hollow inside when an arm moves.
    Fill every open boundary loop around the shoulders with faces (no vertex is moved or added). Returns #loops filled."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    bnd = [e for e in bm.edges if e.is_boundary]
    seen = set(); loops = []
    for e in bnd:
        if e in seen: continue
        stack = [e]; comp = []
        while stack:
            x = stack.pop()
            if x in seen: continue
            seen.add(x); comp.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: stack.append(y)
        loops.append(comp)
    filled = 0
    for comp in loops:
        vs = {v for e in comp for v in e.verts}
        c = sum((v.co for v in vs), Vector()) / len(vs)
        if not (c.z > 2.5 and 0.25 < abs(c.x) < 0.75 and c.z < 3.3): continue
        if any(sum(1 for y in v.link_edges if y.is_boundary) != 2 for v in vs): continue   # only simple closed loops
        # walk the loop in order
        start = comp[0].verts[0]; order = [start]; prev = None; cur = start
        while True:
            nxt = [y.other_vert(cur) for y in cur.link_edges if y.is_boundary and y.other_vert(cur) is not prev]
            if not nxt or nxt[0] is start: break
            prev, cur = cur, nxt[0]; order.append(cur)
        if len(order) != len(vs): continue
        adj = next(f for e in comp for f in e.link_faces)
        # orient the cap opposite to the loop direction used by the neighbouring face (consistent winding)
        e0 = comp[0]; a, b = e0.verts
        fl = list(adj.verts); ia, ib = fl.index(a), fl.index(b)
        forward = (ib - ia) % len(fl) == 1      # neighbour walks a->b, so the cap must walk b->a
        oa, ob = order.index(a), order.index(b)
        if ((ob - oa) % len(order) == 1) == forward: order.reverse()
        f = bm.faces.new(order); f.material_index = adj.material_index; f.smooth = False   # flat: no dark smooth-normal blending
        filled += 1
    bm.normal_update()
    bm.to_mesh(me); bm.free(); me.update()
    return filled

def shoulder_sockets(me, P, part):
    """rim vertices of the torso's open shoulder sockets (where each arm is stitched in)"""
    import collections
    cnt = collections.Counter()
    for p in me.polygons:
        for k in p.edge_keys: cnt[k] += 1
    rim = sorted(set(i for k, c in cnt.items() if c == 1 for i in k if part[i] == 'torso' and P[i, 2] > 2.5 and abs(P[i, 0]) > 0.2))
    return {'L': P[[i for i in rim if P[i, 0] > 0]], 'R': P[[i for i in rim if P[i, 0] < 0]]}

def load_body():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB)
    ico = bpy.data.objects.get('Icosphere')
    if ico: bpy.data.objects.remove(ico)
    body = bpy.data.objects['Body']; arm = bpy.data.objects['Character']
    me = body.data; me.calc_loop_triangles()
    B.obj, B.arm = body, arm
    B.V = [v.co.copy() for v in me.vertices]
    B.P = np.array([v.co[:] for v in me.vertices])
    gi = {g.index: g.name for g in body.vertex_groups}
    W = np.zeros((len(B.V), len(BONES)))
    for v in me.vertices:
        for g in v.groups: W[v.index, BONES.index(gi[g.group])] = g.weight
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    B.W_original = W
    B.tris = [tuple(t.vertices) for t in me.loop_triangles]
    # loose parts
    par = list(range(len(B.V)))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    root = np.array([f(i) for i in range(len(B.V))])
    lab = {}
    for r in set(root):
        idx = np.where(root == r)[0]
        dom = np.bincount(W[idx].argmax(1), minlength=15)
        name = BONES[dom.argmax()]; pts = B.P[idx]
        if name in ('UpperTorso', 'LowerTorso') and len(idx) > 1000: k = 'torso'
        elif 'Arm' in name or 'Hand' in name: k = 'arm_L' if pts[:, 0].mean() > 0 else 'arm_R'
        elif 'Foot' in name or 'Leg' in name: k = 'foot_L' if pts[:, 0].mean() > 0 else 'foot_R'
        elif pts[:, 2].max() < 3.45: k = 'neck'
        else: k = 'head'
        lab[r] = k
    B.part = np.array([lab[r] for r in root])
    # ---- fixed body weights (rigfix rules): analytic joint ramps per body part + weld-equalised tiny edges ----
    import rigfix as RF
    B.sockets = shoulder_sockets(me, B.P, B.part)
    Wf = np.zeros_like(W)
    for k in set(B.part):
        idx = np.where(B.part == k)[0]
        reg, side = (k.split('_') + [None])[:2]
        Wf[idx] = RF.analytic_weights(B.P[idx], reg, side)   # hard shoulder seam (sockets get capped below)
    edges_b = [tuple(e.vertices) for e in me.edges]
    G = RF.weld_groups(B.P, edges_b, 0.012)
    # keep the shoulder seam hard: a group may not mix torso and arm verts (re-split by part)
    G = np.array([hash((int(g), str(B.part[i]) if str(B.part[i]).startswith('arm') or B.part[i] == 'torso' else '')) % (2 ** 62) for i, g in enumerate(G)])
    Wf = RF.weld_equalize(Wf, G); Wf = RF.finalize(Wf); Wf = RF.weld_equalize(Wf, G)
    # targeted repair of any edge that still fails the check_rig poses (numpy LBS, weights only)
    Mb = np.zeros_like(Wf)
    for k in set(B.part):
        idx = np.where(B.part == k)[0]; reg, side = (k.split('_') + [None])[:2]
        if reg == 'torso':
            for i in idx:
                x = B.P[i, 0]
                Mb[i] = RF.region_mask('torso_center') if abs(x) <= 0.02 else RF.region_mask('torso_side', 'L' if x > 0 else 'R')
                if abs(x) > 0.02 and abs(x) <= 0.2: Mb[i] = RF.region_mask('garment_torso_side', 'L' if x > 0 else 'R')
        else:
            Mb[idx] = RF.region_mask(reg, side) if reg in ('arm', 'foot') else RF.region_mask(reg)
    B.pose_mats = pose_matrices(arm)
    Wf, hist = RF.relax_failing(B.P, edges_b, Wf, list(B.pose_mats.values()), M=Mb, zone=RF.joint_zone(B.P, None, dict(hip=0.7, knee=0.6)))
    Wf = RF.weld_equalize(Wf, G); Wf = RF.finalize(Wf, Mb); Wf = RF.weld_equalize(Wf, G)
    B.relax_hist = hist
    B.W = Wf
    # close the open shoulder sockets on the exported body only - AFTER all fitting BVHs/weights are built from the
    # original surface, so no garment shape changes (caps add faces, never vertices)
    B.caps = cap_shoulder_holes(body.data)
    for g in list(body.vertex_groups): body.vertex_groups.remove(g)
    for bn in BONES: body.vertex_groups.new(name=bn)
    for i, w in enumerate(Wf):
        for bi in np.nonzero(w)[0]: body.vertex_groups[BONES[bi]].add([i], float(w[bi]), 'REPLACE')
    def bvh(filt):
        tris = [t for t in B.tris if filt(t)]
        return BVHTree.FromPolygons(B.V, tris, all_triangles=True), tris
    pt = B.part
    B.bvh = {}
    # weight-transfer regions (tri lists kept for barycentric interpolation)
    B.wreg = {}
    def wreg(key, filt):
        tree, tris = bvh(filt); B.wreg[key] = (tree, tris)
    wreg('torso', lambda t: pt[t[0]] == 'torso')
    wreg('head', lambda t: pt[t[0]] == 'head')
    for s, sg in (('L', 1), ('R', -1)):
        wreg('arm_' + s, lambda t, s=s: pt[t[0]] == 'arm_' + s)
        wreg('leg_' + s, lambda t, sg=sg: pt[t[0]] == 'torso' and all(B.V[i].x * sg >= -1e-4 for i in t) and max(B.V[i].z for i in t) < 2.35)
        wreg('foot_' + s, lambda t, s=s, sg=sg: pt[t[0]] == 'foot_' + s or (pt[t[0]] == 'torso' and all(B.V[i].x * sg > 0 for i in t) and max(B.V[i].z for i in t) < 0.8))
    B.bvh['all'], B.all_tris = bvh(lambda t: True)
    B.bvh['torso'], _ = bvh(lambda t: pt[t[0]] == 'torso')
    B.bvh['torso_up'], _ = bvh(lambda t: pt[t[0]] == 'torso' and min(B.V[i].z for i in t) > 1.86)
    for s, sg in (('L', 1), ('R', -1)):
        B.bvh['leg_' + s], _ = bvh(lambda t, sg=sg: pt[t[0]] == 'torso' and all(B.V[i].x * sg > -0.02 for i in t) and max(B.V[i].z for i in t) < 2.12)
        B.bvh['arm_' + s], _ = bvh(lambda t, s=s: pt[t[0]] == 'arm_' + s)
        B.bvh['foot_' + s], _ = bvh(lambda t, s=s: pt[t[0]] == 'foot_' + s)
        B.bvh['footleg_' + s], _ = bvh(lambda t, s=s, sg=sg: pt[t[0]] == 'foot_' + s or (pt[t[0]] == 'torso' and all(B.V[i].x * sg > 0 for i in t) and max(B.V[i].z for i in t) < 0.75))
    B.bvh['head'], _ = bvh(lambda t: pt[t[0]] == 'head')
    B.bvh['headneck'], _ = bvh(lambda t: pt[t[0]] in ('head', 'neck'))
    B.bvh['upper'], _ = bvh(lambda t: pt[t[0]] in ('torso','arm_L','arm_R','head','neck') and min(B.V[i].z for i in t) > 1.7)
    B.kd = KDTree(len(B.V))
    for i, v in enumerate(B.V): B.kd.insert(v, i)
    B.kd.balance()
    # joints (Blender space)
    J = {}
    for b in arm.data.bones: J[b.name] = (arm.matrix_world @ b.head_local).copy()
    B.J = J
    return B

# ---------------- centerlines ----------------
def polyline_resample(pts, n):
    pts = [Vector(p) for p in pts]
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (b - a).length)
    out = []
    for k in range(n):
        s = L[-1] * k / (n - 1)
        i = max(0, min(len(pts) - 2, np.searchsorted(L, s) - 1))
        t = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
        out.append(pts[i].lerp(pts[i + 1], t))
    return out

def smooth_line(pts, it=2):
    pts = [p.copy() for p in pts]
    for _ in range(it):
        pts = [pts[0]] + [(pts[i - 1] + pts[i] * 2 + pts[i + 1]) / 4 for i in range(1, len(pts) - 1)] + [pts[-1]]
    return pts

def arm_line(side):
    s = 'Left' if side == 'L' else 'Right'; sg = 1 if side == 'L' else -1
    J = B.J
    top = Vector((0.5 * sg, 0.0, 3.06))
    pts = [top, J[s + 'UpperArm'], J[s + 'LowerArm'], J[s + 'Hand'], Vector((1.04 * sg, -0.045, 1.02))]
    return pts

def arm_point(side, t):
    """t in [0,1] along shoulder-top(0) .. wrist(1). returns point, tangent"""
    pts = arm_line(side)[:4]
    dense = smooth_line(polyline_resample(pts, 60), 6)
    L = np.cumsum([0] + [(b - a).length for a, b in zip(dense, dense[1:])]); L /= L[-1]
    i = int(np.clip(np.searchsorted(L, t) - 1, 0, len(dense) - 2))
    f = (t - L[i]) / max(L[i + 1] - L[i], 1e-9)
    p = dense[i].lerp(dense[i + 1], f)
    tg = (dense[min(i + 2, len(dense) - 1)] - dense[max(i - 1, 0)]).normalized()
    return p, tg

def leg_point(side, z):
    s = 'Left' if side == 'L' else 'Right'; J = B.J
    pts = [J[s + 'UpperLeg'] + Vector((0, 0, 0.2)), J[s + 'UpperLeg'], J[s + 'LowerLeg'], J[s + 'Foot']]
    # linear in z
    for a, b in zip(pts, pts[1:]):
        if b.z <= z <= a.z:
            f = (a.z - z) / (a.z - b.z); return a.lerp(b, f)
    return pts[-1] if z < pts[-1].z else pts[0]

# ---------------- ray rings ----------------
def ray_ring(bvh, center, dirs, off, R=1.6, extra=None, fill=True, minr=0.0, smooth=1):
    """Outermost hit along each dir (cast inward from far), pushed out by off."""
    pts = []
    for j, d in enumerate(dirs):
        h = bvh.ray_cast(center + d * R, -d, R)
        if h[0] is None: pts.append(None); continue
        loc, nor = h[0], h[1]
        if nor.dot(d) < 0: nor = -nor
        o = off(j, loc) if callable(off) else off
        p = loc + (nor + d).normalized() * o
        pts.append(p)
    n = len(dirs)
    rad = [None if p is None else (p - center).dot(dirs[j]) for j, p in enumerate(pts)]
    if all(r is None for r in rad): return None
    if fill:
        r0 = list(rad); rad = list(rad)
        for j in range(n):
            if r0[j] is None:
                a = j; b = j
                while r0[a % n] is None: a -= 1
                while r0[b % n] is None: b += 1
                f = (j - a) / (b - a)
                rad[j] = r0[a % n] * (1 - f) + r0[b % n] * f
        pts = [center + dirs[j] * rad[j] if pts[j] is None else pts[j] for j in range(n)]
    # smoothing: only grow (never shrink -> no new clipping)
    for _ in range(smooth):
        r = [(pts[j] - center).dot(dirs[j]) for j in range(n)]
        r2 = [max(r[j], (r[j - 1] + 2 * r[j] + r[(j + 1) % n]) / 4) for j in range(n)]
        pts = [pts[j] + dirs[j] * (r2[j] - r[j]) for j in range(n)]
    out = []
    for j in range(n):
        p = pts[j]
        r = (p - center).dot(dirs[j])
        if r < minr: p = p + dirs[j] * (minr - r)
        if extra: p = p + dirs[j] * extra(j, p)
        out.append(p)
    return out

def frame(t, ref=Vector((0, -1, 0))):
    n = (ref - ref.dot(t) * t)
    if n.length < 1e-4: n = Vector((1, 0, 0)) - t * t.x
    n.normalize(); b = t.cross(n)
    return n, b

def circle_dirs(t, nseg, ref=Vector((0, -1, 0))):
    n, b = frame(t, ref)
    # j=0 front, increasing towards +X (character's left) for horizontal rings
    return [(n * math.cos(2 * PI * j / nseg) + b * math.sin(2 * PI * j / nseg)).normalized() for j in range(nseg)]

def hdirs(nseg):
    return [Vector((math.sin(2 * PI * j / nseg), -math.cos(2 * PI * j / nseg), 0)) for j in range(nseg)]

def az_of(j, nseg):  # radians, 0 = front, +pi/2 = character left (+X)
    a = 2 * PI * j / nseg
    return a if a <= PI else a - 2 * PI

# ---------------- Piece ----------------
class Piece:
    def __init__(self, name, group='Top'):
        self.name = name; self.group = group
        self.verts = []; self.faces = []; self.fuv = []; self.fcol = []
        self.paint = None; self.rect = None; self.rect_key = name
        self.weight = 'nearest'; self.rigid = False; self.meta = {}
        self.hint = []  # outward hint per vertex
        self.sharp = False
    def add_vert(self, p, hint=None):
        self.verts.append(Vector(p)); self.hint.append(hint); return len(self.verts) - 1
    def add_face(self, idx, uvs=None, col=None):
        self.faces.append(tuple(idx)); self.fuv.append(uvs or [(0.5, 0.5)] * len(idx)); self.fcol.append(col)
    def merge(self, other):
        o = len(self.verts)
        self.verts += other.verts; self.hint += other.hint
        self.faces += [tuple(i + o for i in f) for f in other.faces]
        self.fuv += other.fuv; self.fcol += other.fcol
        return self

def face_normal(P, f):
    n = Vector()
    for k in range(len(f)):
        a, b = P[f[k]], P[f[(k + 1) % len(f)]]
        n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))

def orient_by_hint(pc):
    s = 0
    for f in pc.faces:
        n = face_normal(pc.verts, f)
        for i in f:
            if pc.hint[i] is not None: s += n.dot(pc.hint[i])
    if s < 0:
        pc.faces = [tuple(reversed(f)) for f in pc.faces]
        pc.fuv = [list(reversed(u)) for u in pc.fuv]

def grid_piece(name, rows, closed=True, v_vals=None, col=None, hint_center=None, hints=None, group='Top', cap_start=None, cap_end=None, u_range=(0, 1)):
    """rows: list of rings (list of Vector). u = j/n, v from v_vals (default row index). hints: outward vectors per row/j."""
    pc = Piece(name, group)
    M = len(rows); N = len(rows[0])
    if v_vals is None: v_vals = [i / (M - 1) for i in range(M)]
    idx = []
    for i, r in enumerate(rows):
        idx.append([pc.add_vert(p, hints[i][j] if hints else ((p - hint_center) if hint_center is not None else None)) for j, p in enumerate(r)])
    cols = N if closed else N - 1
    den = N if closed else N - 1
    u0, u1 = u_range
    U = lambda j: u0 + (u1 - u0) * j / den
    for i in range(M - 1):
        for j in range(cols):
            j2 = (j + 1) % N
            uj2 = U(j + 1)
            pc.add_face([idx[i][j], idx[i][j2], idx[i + 1][j2], idx[i + 1][j]],
                        [(U(j), v_vals[i]), (uj2, v_vals[i]), (uj2, v_vals[i + 1]), (U(j), v_vals[i + 1])], col)
    for cap, i in ((cap_start, 0), (cap_end, M - 1)):
        if cap is not None:
            c = pc.add_vert(cap, (cap - sum(rows[i], Vector()) / N) if True else None)
            for j in range(cols):
                j2 = (j + 1) % N
                pc.add_face([idx[i][j], idx[i][j2], c], [(U(j), v_vals[i]), (U(j + 1), v_vals[i]), ((U(j) + U(j + 1)) / 2, v_vals[i])], col)
    orient_by_hint(pc)
    pc.meta['rows'] = M; pc.meta['N'] = N
    return pc

def vertex_normals(pc):
    vn = [Vector() for _ in pc.verts]
    for f in pc.faces:
        n = face_normal(pc.verts, f)
        for i in f: vn[i] += n
    return [n.normalized() if n.length > 1e-9 else Vector((0, 0, 1)) for n in vn]

def thicken(pc, th, rim_col='same'):
    """Make double sided with thickness th (inwards). Adds rim faces on boundary edges."""
    vn = vertex_normals(pc)
    n0 = len(pc.verts)
    pc.meta['n_outer_faces'] = len(pc.faces); pc.meta['n_outer_verts'] = n0
    pc.meta['pairs'] = pc.meta.get('pairs', []) + [(i, i + n0) for i in range(n0)]
    for i in range(n0):
        pc.verts.append(pc.verts[i] - vn[i] * th); pc.hint.append(None)
    F = list(pc.faces); UV = list(pc.fuv); C = list(pc.fcol)
    for f, uv, c in zip(F, UV, C):
        pc.faces.append(tuple(i + n0 for i in reversed(f))); pc.fuv.append(list(reversed(uv))); pc.fcol.append(c)
    ec = {}
    for fi, f in enumerate(F):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            key = (min(a, b), max(a, b))
            ec.setdefault(key, []).append((fi, k, a, b))
    for key, lst in ec.items():
        if len(lst) == 1:
            fi, k, a, b = lst[0]
            ua, ub = UV[fi][k], UV[fi][(k + 1) % len(F[fi])]
            col = C[fi] if rim_col == 'same' else rim_col
            pc.faces.append((b, a, a + n0, b + n0)); pc.fuv.append([ub, ua, ua, ub]); pc.fcol.append(col)
    return pc

def transform_piece(pc, M):
    pc.verts = [M @ v for v in pc.verts]; return pc

# ---------------- primitives ----------------
def prim_cyl(name, p0, p1, r0, r1=None, n=8, col='black', caps=True, group='Extras'):
    r1 = r0 if r1 is None else r1
    t = (p1 - p0).normalized(); a, b = frame(t, Vector((0, -1, 0.01)) if abs(t.y) < 0.9 else Vector((1, 0, 0)))
    rows = []
    for p, r in ((p0, r0), (p1, r1)):
        rows.append([p + (a * math.cos(2 * PI * j / n) + b * math.sin(2 * PI * j / n)) * r for j in range(n)])
    pc = grid_piece(name, rows, closed=True, col=col, hint_center=None,
                    hints=[[(rows[i][j] - (p0 if i == 0 else p1)) for j in range(n)] for i in range(2)], group=group,
                    cap_start=p0 if caps else None, cap_end=p1 if caps and r1 > 1e-5 else None)
    pc.rigid = True
    return pc

def prim_box(name, center, size, col, rot=None, group='Extras', bevel=0.0):
    sx, sy, sz = [s / 2 for s in size]
    P = [Vector((x, y, z)) for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)]
    if bevel > 0:
        return prim_rbox(name, center, size, col, rot, group, bevel)
    R = rot or Matrix.Identity(3)
    pc = Piece(name, group)
    for p in P: pc.add_vert(Vector(center) + R @ p, R @ p)
    for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        pc.add_face(f, None, col)
    orient_each(pc, Vector(center))
    pc.rigid = True
    return pc

def prim_rbox(name, center, size, col, rot=None, group='Extras', bevel=0.02, seg=8):
    """rounded box as a superellipsoid-ish lat-long"""
    R = rot or Matrix.Identity(3)
    sx, sy, sz = [s / 2 for s in size]
    rows = []
    nl = 7
    for i in range(nl):
        e = -PI / 2 + PI * i / (nl - 1)
        ring = []
        for j in range(seg):
            a = 2 * PI * j / seg + PI / seg
            def sg(v, p=0.35): return math.copysign(abs(v) ** p, v)
            x = sg(math.cos(e)) * sg(math.sin(a)) * sx
            y = -sg(math.cos(e)) * sg(math.cos(a)) * sy
            z = sg(math.sin(e)) * sz
            ring.append(Vector(center) + R @ Vector((x, y, z)))
        rows.append(ring)
    rows = rows[1:-1]
    pc = grid_piece(name, rows, True, col=col, hint_center=Vector(center), group=group,
                    cap_start=Vector(center) + R @ Vector((0, 0, -sz)), cap_end=Vector(center) + R @ Vector((0, 0, sz)))
    pc.rigid = True
    return pc

def orient_each(pc, c):
    F = []
    for f, uv in zip(pc.faces, pc.fuv):
        n = face_normal(pc.verts, f)
        fc = sum((pc.verts[i] for i in f), Vector()) / len(f)
        if n.dot(fc - c) < 0: F.append((tuple(reversed(f)), list(reversed(uv))))
        else: F.append((f, uv))
    pc.faces = [a for a, b in F]; pc.fuv = [b for a, b in F]

def prim_sphere(name, c, r, col, nl=6, seg=10, scale=(1, 1, 1), group='Extras', rot=None):
    R = rot or Matrix.Identity(3)
    rows = []
    for i in range(1, nl):
        e = -PI / 2 + PI * i / nl
        rows.append([Vector(c) + R @ Vector((math.cos(e) * math.sin(2 * PI * j / seg) * r * scale[0], -math.cos(e) * math.cos(2 * PI * j / seg) * r * scale[1], math.sin(e) * r * scale[2])) for j in range(seg)])
    pc = grid_piece(name, rows, True, col=col, hint_center=Vector(c), group=group,
                    cap_start=Vector(c) + R @ Vector((0, 0, -r * scale[2])), cap_end=Vector(c) + R @ Vector((0, 0, r * scale[2])))
    pc.rigid = True
    return pc

def prim_cone(name, base, tip, r, col, n=6, group='Extras', flat=1.0):
    t = (tip - base).normalized(); a, b = frame(t, Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0)))
    ring = [base + (a * math.cos(2 * PI * j / n) * flat + b * math.sin(2 * PI * j / n)) * r for j in range(n)]
    pc = Piece(name, group)
    ids = [pc.add_vert(p) for p in ring]; ti = pc.add_vert(tip); bi = pc.add_vert(base)
    for j in range(n):
        pc.add_face([ids[j], ids[(j + 1) % n], ti], None, col)
        pc.add_face([ids[(j + 1) % n], ids[j], bi], None, col)
    orient_each(pc, base + (tip - base) * 0.3)
    pc.rigid = True
    return pc

def tube_path(name, pts, radius, col, n=6, group='Extras', caps=True, rfn=None):
    pts = [Vector(p) for p in pts]
    rows = []; hints = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a, b = frame(t, Vector((0, -1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0)))
        r = rfn(i / (len(pts) - 1)) if rfn else radius
        ring = [p + (a * math.cos(2 * PI * j / n) + b * math.sin(2 * PI * j / n)) * r for j in range(n)]
        rows.append(ring); hints.append([q - p for q in ring])
    pc = grid_piece(name, rows, True, col=col, hints=hints, group=group,
                    cap_start=pts[0] if caps else None, cap_end=pts[-1] if caps else None,
                    v_vals=[i / (len(pts) - 1) for i in range(len(pts))])
    return pc

# ------------- surface projection helpers -------------
def piece_bvh(*pcs):
    V = []; F = []
    for pc in pcs:
        o = len(V); V += pc.verts; F += [tuple(i + o for i in f) for f in pc.faces]
    return BVHTree.FromPolygons(V, F)

def project(bvh, p, d, far=3.0):
    """cast from p - d*far along d; return first hit loc, normal (normal facing against d)"""
    h = bvh.ray_cast(p - d * far, d, far * 2)
    if h[0] is None: return None, None
    n = h[1]
    if n.dot(d) > 0: n = -n
    return h[0], n

def surface_patch(name, bvh, fn, d, lift, ns=6, nt=6, col=None, th=0.02, group='Top', paint_uv=False):
    """fn(s,t)->Vector point (in space, projected along d onto bvh)."""
    rows = []; hints = []
    for i in range(nt):
        r = []; hh = []
        for j in range(ns):
            p = fn(j / (ns - 1), i / (nt - 1))
            loc, n = project(bvh, p, d)
            if loc is None: loc, n = p, -d
            r.append(loc + n * lift); hh.append(n)
        rows.append(r); hints.append(hh)
    pc = grid_piece(name, rows, closed=False, col=col, hints=hints, group=group)
    if th > 0: thicken(pc, th)
    pc.meta['patch'] = True   # surface patches (pockets, lapels, pads, tie) deform with the cloth under them
    return pc

def body_clear(pc, gap=0.012, bvh_key='all', idx=None):
    """push vertices that are inside/too close to body outward along body normal"""
    bvh = B.bvh[bvh_key]; moved = 0
    rng = range(len(pc.verts)) if idx is None else idx
    for i in rng:
        p = pc.verts[i]
        loc, nor, fi, dist = bvh.find_nearest(p)
        if loc is None: continue
        s = (p - loc).dot(nor)
        if s < gap:
            pc.verts[i] = loc + nor * gap if s < 0 or True else p
            moved += 1
    return moved

def head_clear(pc, gap=0.03):
    m = 0
    for i, p in enumerate(pc.verts):
        d = p - HEAD_C
        if d.length < HEAD_R + gap:
            pc.verts[i] = HEAD_C + d.normalized() * (HEAD_R + gap); m += 1
    return m
