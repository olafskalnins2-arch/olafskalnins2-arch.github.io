import bpy, math
from lib import *
from mathutils.bvhtree import BVHTree

def setup_scene(res=(560, 760), samples=24):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.78, 0.75, 0.70, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    for nm, en, rot in (('key', 3.2, (50, 0, -35)), ('fill', 1.0, (60, 0, 140))):
        ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en; ld.angle = 0.3
        lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
        lo.rotation_euler = tuple(math.radians(r) for r in rot)
    cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 5.0
    co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
    # fix body skin colours to the reference look (render only - file untouched)
    sc.render.film_transparent = False
    return co

def cam_to(co, ang, z=2.55, scale=5.0):
    a = math.radians(ang)
    co.location = (10 * math.sin(a), -10 * math.cos(a), z)
    co.rotation_euler = (math.radians(90), 0, a)
    co.data.ortho_scale = scale

def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

POSES = {
    'walk': {'LeftUpperArm': (40, 0, 0), 'RightUpperArm': (-40, 0, 0), 'LeftLowerArm': (30, 0, 0), 'RightLowerArm': (20, 0, 0),
             'LeftUpperLeg': (-35, 0, 0), 'RightUpperLeg': (30, 0, 0), 'LeftLowerLeg': (35, 0, 0), 'RightLowerLeg': (10, 0, 0),
             'Head': (0, 0, 15), 'UpperTorso': (0, 0, -8)},
    'carry': {'LeftUpperArm': (85, 0, -10), 'RightUpperArm': (85, 0, 10), 'LeftLowerArm': (25, 0, 0), 'RightLowerArm': (25, 0, 0),
              'LeftUpperLeg': (25, 0, 0), 'RightUpperLeg': (25, 0, 0), 'LeftLowerLeg': (-45, 0, 0), 'RightLowerLeg': (-45, 0, 0),
              'LowerTorso': (8, 0, 0)},
}

def set_pose(name):
    arm = B.arm
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
    if name:
        for bn, r in POSES[name].items():
            # bones point +Z; rotate around local X = pitch forward/back (forward arm swing = negative about X since front is -Y)
            arm.pose.bones[bn].rotation_euler = tuple(math.radians(-r[0] if i == 0 else r[i]) for i in range(3))
    bpy.context.view_layer.update()

def eval_mesh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg); me = oe.to_mesh()
    V = [oe.matrix_world @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return V, F

def penetration(objs, depth=0.006):
    """count outfit vertices inside the (evaluated) body surface."""
    BV, BF = eval_mesh(B.obj)
    bvh = BVHTree.FromPolygons(BV, BF)
    tot = 0; bad = 0; worst = 0
    for ob in objs:
        V, F = eval_mesh(ob)
        for p in V:
            loc, nor, fi, d = bvh.find_nearest(p)
            if loc is None: continue
            s = (p - loc).dot(nor)
            tot += 1
            if s < -depth:
                bad += 1; worst = max(worst, -s)
    return tot, bad, worst

REGIONS = {
    'torso': lambda p, part: part == 'torso' and p.z > 2.0,
    'hips_legs': lambda p, part: part == 'torso' and p.z <= 2.0 and p.z > 0.5,
    'upper_arms': lambda p, part: part.startswith('arm') and p.z > 2.25,
    'lower_arms': lambda p, part: part.startswith('arm') and 1.4 < p.z <= 2.25,
    'feet': lambda p, part: part.startswith('foot'),
    'head': lambda p, part: part == 'head',
}

def body_eval_normals():
    dg = bpy.context.evaluated_depsgraph_get()
    oe = B.obj.evaluated_get(dg); me = oe.to_mesh()
    V = [oe.matrix_world @ v.co for v in me.vertices]
    N = [(oe.matrix_world.to_3x3() @ v.normal).normalized() for v in me.vertices]
    oe.to_mesh_clear()
    return V, N

def covered_set(objs, maxd=2.0):
    BV, BN = body_eval_normals()
    VV = []; FF = []
    for ob in objs:
        V, F = eval_mesh(ob); o = len(VV); VV += V; FF += [tuple(i + o for i in f) for f in F]
    bvh = BVHTree.FromPolygons(VV, FF)
    cov = set()
    for i, (p, n) in enumerate(zip(BV, BN)):
        h = bvh.ray_cast(p + n * 0.002, n, maxd)
        if h[0] is not None: cov.add(i)
    return cov

def coverage_report(objs, maxd=0.32):
    set_pose(None)
    rest = covered_set(objs, maxd)
    reg = {}
    for k, f in REGIONS.items():
        idx = [i for i in range(len(B.V)) if f(B.V[i], B.part[i])]
        reg[k] = round(100 * sum(1 for i in idx if i in rest) / max(1, len(idx)), 1)
    out = {'rest_coverage_pct': reg, 'rest_covered_verts': len(rest)}
    for pose in ('walk', 'carry'):
        set_pose(pose)
        c = covered_set(objs, maxd)
        lost = len(rest - c)
        out[f'{pose}_pokethrough_verts'] = lost
        out[f'{pose}_pokethrough_pct'] = round(100 * lost / max(1, len(rest)), 2)
    set_pose(None)
    return out

def poke_detail(objs, pose, maxd=0.32):
    set_pose(None); rest = covered_set(objs, maxd)
    set_pose(pose); c = covered_set(objs, maxd); set_pose(None)
    lost = rest - c
    import collections
    cnt = collections.Counter(BONES[int(np.argmax(B.W[i]))] for i in lost)
    return dict(cnt)
