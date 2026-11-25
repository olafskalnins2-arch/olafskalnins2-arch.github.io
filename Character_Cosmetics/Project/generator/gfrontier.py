"""Ghost sheet: arm-follow frontier (stretch vs hand/leg poke-through)."""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Roblox_Ready'))
import rigfix as RF
from lib import *; from pipeline import *
import check_rig as C, o04
from mathutils.bvhtree import BVHTree
load_body(); B.pose_mats = {}
P = o04.ghost()[0]; sheet = P[0]; holes = P[1:]
W0 = np.array(rig_weights(sheet)); Pn = np.array([v[:] for v in sheet.verts])
WA = {}
for s in 'LR':
    WA[s] = np.array([RF.finalize((transfer(Vector(p), 'arm_' + s) * RF.mask_of(RF.ARM[s]))[None])[0] for p in Pn])
hand = {s: np.array(arm_point(s, 1.0)[0]) for s in 'LR'}
def mk(name, verts, faces, W):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    ob = bpy.data.objects.new('gf_' + name, me); bpy.context.scene.collection.objects.link(ob)
    for bn in BONES: ob.vertex_groups.new(name=bn)
    for vi, w in enumerate(W):
        for bi in np.nonzero(w)[0]: ob.vertex_groups[BONES[bi]].add([vi], float(w[bi]), 'REPLACE')
    m = ob.modifiers.new('A', 'ARMATURE'); m.object = B.arm; return ob
limbs = [i for i in range(len(B.V)) if B.part[i] in ('arm_L', 'arm_R') or (B.part[i] == 'torso' and B.V[i].z < 1.85) or B.part[i].startswith('foot')]
def covered(ob):
    V = C.evaluated_coords(ob); F = [tuple(p.vertices) for p in ob.data.polygons]; bvh = BVHTree.FromPolygons(V, F)
    dg = bpy.context.evaluated_depsgraph_get(); oe = B.obj.evaluated_get(dg); me = oe.to_mesh()
    cov = set(i for i in limbs if bvh.ray_cast(me.vertices[i].co + me.vertices[i].normal * 0.002, me.vertices[i].normal, 1.6)[0] is not None)
    oe.to_mesh_clear(); return cov
for cap, R in itertools.product((0.0, 0.5, 0.8, 1.0), (0.6, 1.2)):
    if cap == 0 and R > 0.6: continue
    W = W0.copy()
    for i, p in enumerate(Pn):
        if abs(p[0]) <= 0.02: continue
        s = 'L' if p[0] > 0 else 'R'
        d = np.linalg.norm(p - hand[s]); a = cap * max(0.0, 1 - d / R)
        if a > 0: W[i] = RF.finalize(((1 - a) * W0[i] + a * WA[s][i])[None])[0]
    for o in [o for o in bpy.data.objects if o.name.startswith('gf_')]: bpy.data.objects.remove(o)
    ob = mk('Sheet', sheet.verts, sheet.faces, W)
    C.reset_pose(B.arm); bpy.context.view_layer.update(); r0 = C.evaluated_coords(ob); E = C.tri_edges(ob.data); c0 = covered(ob)
    out = []
    for pose in ('walk', 'spread', 'arms_up', 'crouch'):
        C.apply_pose(B.arm, C.POSES[pose]); co = C.evaluated_coords(ob); worst = 1; bad = 0
        for a_, b_ in E:
            l0 = (r0[a_] - r0[b_]).length
            if l0 < 1e-5: continue
            r = (co[a_] - co[b_]).length / l0; worst = max(worst, r, 1 / max(r, 1e-6)); bad += (r > 1.5 or r < 0.5)
        out.append(f'{pose}: worst {worst:.2f} bad {bad} poke {len(c0 - covered(ob))}')
    C.reset_pose(B.arm)
    print(f'cap {cap} R {R}: ' + '  '.join(out), flush=True)
