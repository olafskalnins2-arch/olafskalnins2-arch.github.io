"""Wizard robe: follow-field frontier (stretch vs poke-through). a(v) = min(cap, k*|x|) for skirt verts below the crotch."""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Roblox_Ready'))
import rigfix as RF
from lib import *; from pipeline import *
import check_rig as C, o03
from mathutils.bvhtree import BVHTree
load_body()
P = o03.wizard()[0]
B.pose_mats = {}   # no repair pass: raw trade-off
robe = next(p for p in P if p.name == 'Robe')
others = [p for p in P if p is not robe and not (p.rigid and not p.meta.get('patch'))]
W0 = np.array(rig_weights(robe))
Pn = np.array([v[:] for v in robe.verts])
lt = np.eye(15)[0]
WL = {s: np.array([RF.finalize((transfer(Vector(p), 'leg_' + s) * RF.mask_of(RF.LEG[s]))[None])[0] for p in Pn]) for s in 'LR'}
def mk(name, verts, faces, W):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    ob = bpy.data.objects.new('fr_' + name, me); bpy.context.scene.collection.objects.link(ob)
    for bn in BONES: ob.vertex_groups.new(name=bn)
    for vi, w in enumerate(W):
        for bi in np.nonzero(w)[0]: ob.vertex_groups[BONES[bi]].add([vi], float(w[bi]), 'REPLACE')
    m = ob.modifiers.new('A', 'ARMATURE'); m.object = B.arm; return ob
oth = [mk(p.name, p.verts, p.faces, np.array(rig_weights(p))) for p in others]
legs = [i for i in range(len(B.V)) if B.part[i] == 'torso' and 0.6 < B.V[i].z < 1.85]
def covered(objs):
    VV = []; FF = []
    for ob in objs:
        V = C.evaluated_coords(ob); F = [tuple(p.vertices) for p in ob.data.polygons]; o = len(VV); VV += V; FF += [tuple(i + o for i in f) for f in F]
    bvh = BVHTree.FromPolygons(VV, FF)
    dg = bpy.context.evaluated_depsgraph_get(); oe = B.obj.evaluated_get(dg); me = oe.to_mesh()
    cov = set(i for i in legs if bvh.ray_cast(me.vertices[i].co + me.vertices[i].normal * 0.002, me.vertices[i].normal, 1.0)[0] is not None)
    oe.to_mesh_clear(); return cov
rows = []
for cap, k in itertools.product((0.0, 0.3, 0.5, 0.7, 0.9), (1.0, 2.0, 4.0)):
    if cap == 0 and k > 1: continue
    W = W0.copy()
    for i, p in enumerate(Pn):
        if p[2] < 1.95 and abs(p[0]) > 0.02:
            s = 'L' if p[0] > 0 else 'R'
            kz = RF.sstep(1.95, 1.75, p[2]); a = min(cap, k * abs(p[0])) * kz
            W[i] = RF.finalize(((1 - a) * W0[i] + a * WL[s][i])[None])[0]
    for o in [o for o in bpy.data.objects if o.name == 'fr_Robe']: bpy.data.objects.remove(o)
    ob = mk('Robe', robe.verts, robe.faces, W)
    C.reset_pose(B.arm); bpy.context.view_layer.update(); r0 = C.evaluated_coords(ob); E = C.tri_edges(ob.data)
    c0 = covered([ob] + oth); out = {}
    for pose in ('walk', 'spread', 'crouch'):
        C.apply_pose(B.arm, C.POSES[pose]); co = C.evaluated_coords(ob); worst = 1; bad = 0
        for a_, b_ in E:
            l0 = (r0[a_] - r0[b_]).length
            if l0 < 1e-5: continue
            r = (co[a_] - co[b_]).length / l0; worst = max(worst, r, 1 / max(r, 1e-6)); bad += (r > 1.5 or r < 0.5)
        poke = len(c0 - covered([ob] + oth)) if pose != 'crouch' else '-'
        out[pose] = (round(worst, 2), bad, poke)
    C.reset_pose(B.arm)
    print(f'cap {cap} k {k}: ' + '  '.join(f'{p}: worst {v[0]} bad {v[1]} poke {v[2]}' for p, v in out.items()), flush=True)
