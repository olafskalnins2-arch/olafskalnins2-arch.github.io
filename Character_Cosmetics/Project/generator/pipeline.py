import os, json
from lib import *
from PIL import Image

ATLAS = 1024
PAL_H = 64

def hexc(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# ---------- paint helpers (numpy, return HxWx3 float 0..255) ----------
def P_solid(c):
    c = np.array(hexc(c) if isinstance(c, str) else c, float)
    return lambda U, V, m: np.broadcast_to(c, U.shape + (3,)).copy()

def mix(img, mask, c):
    c = np.array(hexc(c) if isinstance(c, str) else c, float)
    mask = np.clip(mask, 0, 1)[..., None]
    return img * (1 - mask) + c * mask

def aa(d, w=1.5):  # signed distance (px-ish) -> coverage
    return np.clip(0.5 - d / w, 0, 1)

def zc(U, V, m):  # physical coordinates: z, az (rad), x around (units)
    z = m.get('zmin', 0) + V * (m.get('zmax', 1) - m.get('zmin', 0))
    az = 2 * PI * (U - 0.5)
    return z, az

def pack(rects):
    """rects: dict key->(w,h). shelf pack into ATLAS x (ATLAS-PAL_H). returns key->(x,y,w,h)"""
    order = sorted(rects.items(), key=lambda kv: -kv[1][1])
    x = y = 0; sh = 0; out = {}
    for k, (w, h) in order:
        if x + w > ATLAS: x = 0; y += sh + 4; sh = 0
        out[k] = (x, y, w, h); x += w + 4; sh = max(sh, h)
    if y + sh > ATLAS - PAL_H:
        # scale down everything and retry
        return pack({k: (max(16, int(w * 0.75)), max(16, int(h * 0.75))) for k, (w, h) in rects.items()})
    return out

def p2(v, lo=32, hi=512):
    v = int(np.clip(v, lo, hi)); p = 1
    while p < v: p *= 2
    return p

def build_atlas(pieces, palette, out_png):
    img = np.zeros((ATLAS, ATLAS, 3), float); img[:] = 128
    rects = {}; owner = {}
    for pc in pieces:
        if pc.paint is None: continue
        if pc.rect_key not in rects:
            m = pc.meta
            if 'rect' in m: w, h = m['rect']
            else:
                circ = m.get('circ', 1.0)
                hh = (m.get('zmax', 1) - m.get('zmin', 0)) if 'zmax' in m else m.get('length', 0.6)
                w = p2(circ * 150, 64, 512); h = p2(abs(hh) * 170, 32, 512)
            rects[pc.rect_key] = (w, h); owner[pc.rect_key] = pc
    R = pack(rects)
    for k, (x, y, w, h) in R.items():
        pc = owner[k]
        U, V = np.meshgrid(np.linspace(0, 1, w), np.linspace(1, 0, h))
        tile = pc.paint(U, V, pc.meta)
        img[y:y + h, x:x + w] = tile
        # bleed 2px
        for d in (1, 2):
            if y - d >= 0: img[y - d, x:x + w] = tile[0]
            if y + h - 1 + d < ATLAS: img[y + h - 1 + d, x:x + w] = tile[-1]
            if x - d >= 0: img[y:y + h, x - d] = tile[:, 0]
            if x + w - 1 + d < ATLAS: img[y:y + h, x + w - 1 + d] = tile[:, -1]
    # palette
    cells = {}
    cs = 16; per_row = ATLAS // cs
    for i, (name, col) in enumerate(palette.items()):
        cx = (i % per_row) * cs; cy = ATLAS - PAL_H + (i // per_row) * cs
        img[cy:cy + cs, cx:cx + cs] = hexc(col) if isinstance(col, str) else col
        cells[name] = ((cx + cs / 2) / ATLAS, 1 - (cy + cs / 2) / ATLAS)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out_png)
    def uvmap(pc, uv, col):
        if col is not None: return cells[col]
        x, y, w, h = R[pc.rect_key]
        u, v = uv
        u = min(max(u, 0), 1); v = min(max(v, 0), 1)
        return ((x + 0.5 + u * (w - 1)) / ATLAS, 1 - (y + 0.5 + (1 - v) * (h - 1)) / ATLAS)
    return uvmap

# ---------- weights ----------
def weights_at(p):
    loc, nor, fi, dist = B.bvh['all'].find_nearest(p)
    t = B.all_tris[fi]
    a, b, c = (B.V[i] for i in t)
    # barycentric
    v0, v1, v2 = b - a, c - a, loc - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12: w = np.array([1 / 3] * 3)
    else:
        v = (d11 * d20 - d01 * d21) / den; ww = (d00 * d21 - d01 * d20) / den
        w = np.clip(np.array([1 - v - ww, v, ww]), 0, 1); w /= w.sum()
    return (B.W[list(t)] * w[:, None]).sum(0)

def weights_smooth(p, r=0.45, exclude_head=False, parts=None):
    acc = np.zeros(len(BONES)); tot = 0
    for co, i, d in B.kd.find_range(p, r):
        if exclude_head and B.part[i] == 'head': continue
        if parts is not None and B.part[i] not in parts: continue
        g = math.exp(-(d / (r * 0.5)) ** 2)
        acc += B.W[i] * g; tot += g
    if tot < 1e-9: return weights_at(p)
    return acc / tot

def limit4(w):
    w = np.array(w, float)
    idx = np.argsort(-w)[:4]
    o = np.zeros_like(w); o[idx] = w[idx]
    o[o < 0.01] = 0
    s = o.sum()
    return o / s if s > 0 else o

def piece_weights(pc):
    if callable(pc.weight):
        ws = [pc.weight(p) for p in pc.verts]
    elif pc.rigid:
        c = sum(pc.verts, Vector()) / len(pc.verts)
        w = weights_smooth(c, 0.2) if pc.weight == 'smooth' else weights_at(c)
        ws = [w] * len(pc.verts)
    elif pc.weight == 'smooth':
        ws = [weights_smooth(p) for p in pc.verts]
    else:
        ws = [weights_at(p) for p in pc.verts]
    return [limit4(w) for w in ws]

# ---------- blender objects ----------
def make_material(name, png):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(png); img.name = os.path.basename(png)
    tex.image = img
    tex.interpolation = 'Linear'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.75
    return mat

def build_objects(outfit_name, pieces, uvmap, mat, collection, smooth_angle=40, metal=False):
    groups = {}
    for pc in pieces: groups.setdefault(pc.group, []).append(pc)
    objs = []
    for g, pcs in groups.items():
        verts = []; faces = []; uvs = []; W = []
        sharp_faces = []
        for pc in pcs:
            o = len(verts)
            verts += [tuple(v) for v in pc.verts]
            W += pc.W
            for f, uv, col in zip(pc.faces, pc.fuv, pc.fcol):
                faces.append(tuple(i + o for i in f)); uvs.append([uvmap(pc, u, col) for u in uv])
                sharp_faces.append(pc.sharp)
        me = bpy.data.meshes.new(f'{outfit_name}_{g}')
        me.from_pydata(verts, [], faces)
        me.validate(clean_customdata=False)
        uvl = me.uv_layers.new(name='UVMap')
        k = 0
        for poly, uv in zip(me.polygons, uvs):
            for li, u in zip(poly.loop_indices, uv): uvl.data[li].uv = u
        me.materials.append(mat)
        for poly in me.polygons: poly.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        ob = bpy.data.objects.new(f'{outfit_name}_{g}', me)
        collection.objects.link(ob)
        for bn in BONES: ob.vertex_groups.new(name=bn)
        for vi, w in enumerate(W):
            for bi in np.nonzero(w)[0]:
                ob.vertex_groups[BONES[bi]].add([vi], float(w[bi]), 'REPLACE')
        ob.parent = B.arm
        mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = B.arm
        objs.append(ob)
    return objs

def finalize_pieces(pieces):
    for pc in pieces:
        pc.W = piece_weights(pc)

def skirt_weight(z_start=2.05, z_full=1.75, r=0.5):
    """nearest weights above z_start, blending to smooth torso/leg weights below (for coats, robes)."""
    def f(p):
        a = weights_at(p)
        if p.z >= z_start: return a
        b = weights_smooth(p, r, parts=('torso',))
        k = min(1.0, (z_start - p.z) / max(z_start - z_full, 1e-6))
        # keep lower-body skirts mostly attached to the pelvis
        lt = np.zeros(len(BONES)); lt[0] = 1.0
        b = b * 0.6 + lt * 0.4
        return a * (1 - k) + b * k
    return f


# =====================================================================================
#  Rig-safe garment weights (replaces piece_weights above). Rules: CLAUDE.md "Rigging rules".
# =====================================================================================
import rigfix as RF

def _bary_weights(tree_tris, p):
    tree, tris = tree_tris
    loc, nor, fi, dist = tree.find_nearest(p)
    t = tris[fi]
    a, b, c = (B.V[i] for i in t)
    v0, v1, v2 = b - a, c - a, loc - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-14: bw = np.array([1 / 3] * 3)
    else:
        v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
        bw = np.clip(np.array([1 - v - w, v, w]), 0, 1); bw /= bw.sum()
    return (B.W[list(t)] * bw[:, None]).sum(0), dist

def transfer(p, key):
    """nearest-face-interpolated weights from the (fixed) body, restricted to one body region"""
    return _bary_weights(B.wreg[key], p)[0]

def side_mask(x, eps=0.02):
    if x > eps: return RF.region_mask('garment_torso_side', 'L')
    if x < -eps: return RF.region_mask('garment_torso_side', 'R')
    return RF.region_mask('torso_center')

ONE = lambda name: np.eye(len(BONES))[BONES.index(name)]

def infer_region(pc):
    c = sum(pc.verts, Vector()) / len(pc.verts)
    best = None
    for key in ('torso', 'head', 'foot_L', 'foot_R'):
        d = B.wreg[key][0].find_nearest(c)[3]
        if best is None or d < best[0]: best = (d, key)
    if best[1] == 'torso' and c.z < 1.9 and abs(c.x) > 0.05:
        return 'leg_' + ('L' if c.x > 0 else 'R')   # patches on a thigh / knee belong to that leg
    return best[1]

def _norm(w):
    s = w.sum(); return w / s if s > 1e-12 else w

def rig_weights(pc):
    n = len(pc.verts)
    region = getattr(pc, 'region', None)
    bone = getattr(pc, 'bone', None)
    patch = pc.meta.get('patch', False)
    if bone:
        return np.tile(ONE(bone), (n, 1))
    if region == 'ghost':
        W = np.zeros((n, len(BONES)))
        for i, p in enumerate(pc.verts):
            h = RF.sstep(3.05, 3.5, p.z); u = RF.sstep(1.6, 2.9, p.z)
            W[i] = h * ONE('Head') + (1 - h) * (u * ONE('UpperTorso') + (1 - u) * ONE('LowerTorso'))
        return W
    if pc.rigid and not patch:
        # 100% on ONE bone: the bone that dominates the body where the part is attached
        allowed = [region] if region and region.startswith('arm') else ['torso', 'head', 'foot_L', 'foot_R']
        best = None
        for p in pc.verts:
            for key in allowed:
                w, d = _bary_weights(B.wreg[key], p)
                if best is None or d < best[0]: best = (d, w, p, key)
        d, w, p, key = best
        if key == 'torso': w = w * side_mask(p.x)
        if p.z > 1.9 and key == 'torso': w = w * RF.region_mask('torso_center') if w[[BONES.index('LowerTorso'), BONES.index('UpperTorso')]].sum() > 0 else w
        return np.tile(ONE(BONES[int(np.argmax(w))]), (n, 1))
    if region is None: region = infer_region(pc)
    W = np.zeros((n, len(BONES))); M = np.zeros_like(W)
    skirt = getattr(pc, 'skirt', not patch)   # only coat/robe/sheet shells get the pelvis-anchored hem rule
    lt = ONE('LowerTorso')
    for i, p in enumerate(pc.verts):
        if region.startswith('arm'):
            w = transfer(p, region); m = RF.region_mask('sleeve', region[-1])
        elif region.startswith('leg'):
            q = p
            if pc.meta.get('w_axis'):    # trouser legs: sample the thigh at the same height (halfway to the leg axis),
                c = leg_point(region[-1], p.z)   # not the torso bottom / steep crotch field the rim flares over
                q = c + (p - c) * pc.meta['w_axis']
            xm = pc.meta.get('w_xmin')
            if xm and abs(q.x) < xm: q = Vector((xm if region[-1] == 'L' else -xm, q.y, q.z))
            w = transfer(q, region); m = RF.region_mask('leg', region[-1])
        elif region.startswith('shin'):   # stiff boot shafts / cuffs / greaves: shin + foot only
            w = transfer(p, 'leg_' + region[-1]); m = RF.region_mask('foot', region[-1])
            if (w * m).sum() < 1e-6: w = m.copy()
        elif region.startswith('foot'):
            w = transfer(p, region); m = RF.region_mask('foot', region[-1])
        elif region == 'head':
            w = transfer(p, 'head'); m = RF.region_mask('head')
        else:  # torso garments
            pan = pc.meta.get('panel')
            m = side_mask(p.x) if not (pan is not None and pan[i] != 0) else RF.region_mask('garment_torso_side', 'L' if pan[i] > 0 else 'R')
            w = transfer(p, 'torso') * m
            if skirt and p.z < 1.95:
                # coat / robe / sheet hems below the crotch: anchored to the pelvis, gentle same-side leg follow
                k = RF.sstep(1.95, 1.75, p.z)
                if abs(p.x) > 0.02:
                    s = 'L' if p.x > 0 else 'R'
                    wl = transfer(p, 'leg_' + s) * RF.mask_of(RF.LEG[s])
                    a = RF.DEFAULT_RAMPS.get('skirt_cap', 0.3) * RF.sstep(0.05, RF.DEFAULT_RAMPS.get('skirt_x', 0.6), abs(p.x))
                    ws = a * _norm(wl) + (1 - a) * lt
                else:
                    ws = lt
                w = (1 - k) * _norm(w) + k * ws
            panel = pc.meta.get('panel')
            if panel is not None and panel[i] != 0:
                # slit robe panel: below the slit top it deforms like a (wide) trouser leg of its own side
                zt = pc.meta['slit_top']; s = 'L' if panel[i] > 0 else 'R'; back = abs(panel[i]) >= 2
                bk = 'slit_blend_side' if abs(panel[i]) == 3 else ('slit_blend_back' if back else 'slit_blend')
                b = RF.lstep(zt, zt - RF.DEFAULT_RAMPS.get(bk, RF.DEFAULT_RAMPS.get('slit_blend', 1.0)), p.z, 0.5)
                wl = ONE(RF.LEG[s][0])   # the whole panel hangs off its thigh, uniformly across its width (no shear)
                if back:   # back strips drape: inner strip follows less, outer (side) strip like the front
                    b *= RF.DEFAULT_RAMPS.get('slit_cap_back_side', 1.0) if abs(panel[i]) == 3 else RF.DEFAULT_RAMPS.get('slit_cap_back', 0.8)
                else:
                    b *= RF.DEFAULT_RAMPS.get('slit_cap', 1.0)
                w = (1 - b) * _norm(w) + b * _norm(wl)
        W[i] = _norm(w * m); M[i] = m
    # inner shell verts copy their outer twin (thickness rim edges never stretch)
    for a, b in pc.meta.get('pairs', []):
        W[b] = W[a]; M[b] = M[a]
    E = set()
    for f in pc.faces:
        for k in range(len(f)): E.add(tuple(sorted((f[k], f[(k + 1) % len(f)]))))
    # smooth ONLY in joint zones (waist, hips, knees, elbows, ankles, wrists) over the garment's own edges
    Pn = np.array([v[:] for v in pc.verts])
    W = RF.smooth(W, list(E), RF.joint_zone(Pn, None), iters=getattr(pc, 'smooth_iters', 0), M=M)
    for a, b in pc.meta.get('pairs', []): W[b] = W[a]
    G = RF.weld_groups(np.array([v[:] for v in pc.verts]), list(E), 0.012, coincident=None)   # never re-glue slits
    W, M = RF.weld_equalize(W, G, M)
    W = RF.finalize(W, M)
    W = RF.weld_equalize(W, G)
    for a, b in pc.meta.get('pairs', []): W[b] = W[a]
    # targeted repair: any edge (incl. BOTH diagonals of every quad - engines triangulate) that would still
    # stretch/squash past check_rig limits in any test pose gets its endpoint weights relaxed (weights only)
    TE = set(E)
    for f in pc.faces:
        if len(f) == 4:
            TE.add(tuple(sorted((f[0], f[2])))); TE.add(tuple(sorted((f[1], f[3]))))
    pm = list(getattr(B, 'pose_mats', {}).values())
    if pm:
        # loose torso garments (coats / robes hanging away from the body) may be repaired out to their full width
        hx = 0.85 if (region not in (None,) and not str(region).startswith('arm') and getattr(pc, 'skirt', False)) else 0.6
        zone = RF.joint_zone(Pn, None, dict(hip=0.7, knee=0.6, waist=0.3, hip_x=hx))
        tie = np.array(G)   # weld groups ...
        for a2, b2 in pc.meta.get('pairs', []): tie[b2] = tie[a2]   # ... and inner/outer shell twins move together
        # make tie a proper representative map (union of both relations)
        par = np.arange(len(tie))
        def fr(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for i2 in range(len(tie)):
            r1, r2 = fr(i2), fr(int(G[i2]))
            if r1 != r2: par[r1] = r2
        for a2, b2 in pc.meta.get('pairs', []):
            r1, r2 = fr(a2), fr(b2)
            if r1 != r2: par[r1] = r2
        tie = np.array([fr(i2) for i2 in range(len(tie))])
        for g in np.unique(tie):   # start with identical weights inside every tie group
            idx = np.where(tie == g)[0]
            if len(idx) > 1: W[idx] = W[idx[0]]
        allh = []
        for rnd in range(6):   # fix -> clean up (pair sync, prune, normalize) -> re-check, until stable
            W, hist = RF.relax_failing(Pn, sorted(TE), W, pm, M=M, zone=zone, tie=tie)
            for a, b in pc.meta.get('pairs', []): W[b] = W[a]
            W = RF.finalize(W, M)
            for a, b in pc.meta.get('pairs', []): W[b] = W[a]
            allh += hist
            _, h2 = RF.relax_failing(Pn, sorted(TE), W, pm, M=M, zone=zone, iters=1, tie=tie)
            allh.append(h2[0])
            if h2[0] == 0: break
        pc.meta['relax_hist'] = allh
    return W

def finalize_pieces(pieces):
    for pc in pieces:
        W = rig_weights(pc)
        pc.W = [w for w in RF.finalize(W)]


# ---------- coverage repair for thin skin-tight covers (weights only) ----------
def posed_body_bvhs():
    if getattr(B, 'posed_bvh', None) is None:
        from mathutils.bvhtree import BVHTree as _BT
        B.posed_bvh = {}
        for name, mats in B.pose_mats.items():
            Q = RF.lbs(B.P, B.W, mats)
            B.posed_bvh[name] = _BT.FromPolygons([Vector(q) for q in Q], [t for t in B.tris if B.part[t[0]] in ('torso', 'foot_L', 'foot_R')], all_triangles=True)  # legs: hands may legitimately touch them
    return B.posed_bvh

def cover_repair(pc, W, margin=0.004, iters=10):
    """For a thin cover: nudge weights of verts that sink into the posed body (any check pose) between their own
    allowed bones until they sit outside; a change is kept only if it reduces the sinking and keeps every incident
    edge inside the 0.5x-1.5x limits."""
    pm = getattr(B, 'pose_mats', {})
    if not pm: return W, []
    bv = posed_body_bvhs(); names = list(pm)
    Pn = np.array([v[:] for v in pc.verts]); Ph = np.c_[Pn, np.ones(len(Pn))]
    M = (W > 0).astype(float)
    side = pc.region[-1]; M[:] = RF.region_mask('leg', side)
    twin = {}
    for a, b in pc.meta.get('pairs', []): twin[a] = b
    E = set()
    for f in pc.faces:
        for k in range(len(f)): E.add(tuple(sorted((f[k], f[(k + 1) % len(f)]))))
        if len(f) == 4: E.add(tuple(sorted((f[0], f[2])))); E.add(tuple(sorted((f[1], f[3]))))
    inc = {}
    for a, b in E: inc.setdefault(a, []).append((a, b)); inc.setdefault(b, []).append((a, b))
    l0 = {e: np.linalg.norm(Pn[e[0]] - Pn[e[1]]) for e in E}
    def pos(i, w, n): return (np.einsum('b,bij,j->i', w, pm[n][:, :3, :], Ph[i]))
    def sinks(i, w):
        out = []
        for n in names:
            q = Vector(pos(i, w, n)); loc, nor, fi, d = bv[n].find_nearest(q)
            out.append(0.0 if loc is None else max(0.0, margin - (q - loc).dot(nor)))
        return np.array(out)
    def sink(i, w): return float(sinks(i, w).sum())
    def edges_ok(i, w):
        for a, b in inc.get(i, []):
            if l0[(a, b)] < 1e-5: continue
            j = b if a == i else a
            for n in names:
                r = np.linalg.norm(pos(i, w, n) - pos(j, W[j], n)) / l0[(a, b)]
                if r > 1.5 or r < 0.5: return False
        return True
    n0 = pc.meta.get('n_outer_verts', len(Pn)); hist = []
    for it in range(iters):
        bad = [i for i in range(n0) if sink(i, W[i]) > 0]
        hist.append(len(bad))
        if not bad: break
        for i in bad:
            base_v = sinks(i, W[i]); base = base_v.sum(); best = None
            bones = np.nonzero(M[i])[0]
            for a_ in bones:
                for b_ in bones:
                    if a_ == b_ or W[i, a_] <= 0: continue
                    for d in (0.05, 0.12, 0.25):
                        w = W[i].copy(); t = min(d, w[a_]); w[a_] -= t; w[b_] += t
                        w = RF.clean_row(w, M[i])
                        if w.sum() <= 0: continue
                        svv = sinks(i, w); sv = svv.sum()
                        if (svv <= base_v + 1e-7).all() and sv < base - 1e-6 and (best is None or sv < best[0]) and edges_ok(i, w): best = (sv, w)
            if best:
                W[i] = best[1]
                if i in twin: W[twin[i]] = best[1]
    return W, hist

_rig_weights_base = rig_weights
def rig_weights(pc):
    W = _rig_weights_base(pc)
    if getattr(pc, 'cover', False):
        W, h = cover_repair(pc, np.array(W))
        pc.meta['cover_hist'] = h
    return W
