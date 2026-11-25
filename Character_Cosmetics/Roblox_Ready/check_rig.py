"""check_rig.py - automated skin-weight / deformation check for Floppy Movers character models.

MUST pass before any new model is called done.

Usage (Blender 4.x/5.x as a Python module: `pip install bpy`):
    python3 check_rig.py <file-or-folder> [...] [--poses walk,spread,arms_up,arms_down,crouch]
                         [--skip-mesh Body] [--json report.json]
or inside Blender:
    blender -b -P check_rig.py -- <file-or-folder> [...]

Accepts .glb / .gltf / .fbx / .blend. Folders are searched recursively (folders named _backup are skipped).

For every armature-deformed mesh in every file it checks:
  weights   - max 4 bone influences per vertex, every weight >= 0.01, weights sum to 1 (+-0.01),
              no vertex weighted to both Left* and Right* bones, and no vertex weighted to the other side's bones
              (side = the side of the separate mesh piece it belongs to; centre-line pieces: x > 0.02 left, < -0.02 right,
              in between: torso bones only)
  stretch   - poses the rig (walk, legs spread wide, arms up, arms down, crouch) and compares every
              edge of the TRIANGULATED mesh (incl. quad diagonals) posed vs rest: FAIL if any edge > 1.5x or < 0.5x
Prints: model | pose | worst stretch | worst squash | bad verts | PASS/FAIL.  Exit code 1 if anything fails.

Poses are defined as rotations about WORLD axes at each joint (character faces -Y, +X is the
character's left, +Z up), so they don't depend on how an importer orients bones.
"""
import sys, os, math, json, glob

import bpy
from mathutils import Matrix, Vector

STRETCH_MAX = 1.5
SQUASH_MIN = 0.5
MAX_INFLUENCES = 4
MIN_WEIGHT = 0.01

# (bone, world axis, degrees). Conventions (character faces -Y):
#   X-  swings a hanging limb forward      X+  bends a knee (shin back) / leans torso forward
#   Y-  moves a LEFT limb outward (+X)     Y+  moves a RIGHT limb outward (-X)
#   Z   turns head / torso
POSES = {
    'walk': [('LeftUpperArm', 'X', -40), ('RightUpperArm', 'X', 40), ('LeftLowerArm', 'X', -30), ('RightLowerArm', 'X', -20),
             ('LeftUpperLeg', 'X', -35), ('RightUpperLeg', 'X', 30), ('LeftLowerLeg', 'X', 35), ('RightLowerLeg', 'X', 10),
             ('Head', 'Z', 15), ('UpperTorso', 'Z', -8)],
    'spread': [('LeftUpperLeg', 'Y', -45), ('RightUpperLeg', 'Y', 45)],
    'arms_up': [('LeftUpperArm', 'Y', -150), ('RightUpperArm', 'Y', 150)],
    'arms_down': [('LeftUpperArm', 'Y', 12), ('RightUpperArm', 'Y', -12)],
    'crouch': [('LowerTorso', 'X', 15), ('LeftUpperLeg', 'X', -70), ('RightUpperLeg', 'X', -70),
               ('LeftLowerLeg', 'X', 80), ('RightLowerLeg', 'X', 80), ('LeftFoot', 'X', -10), ('RightFoot', 'X', -10),
               ('LeftUpperArm', 'X', -35), ('RightUpperArm', 'X', -35)],
}
AXES = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}


def side_of(name):
    n = name.lower()
    if n.startswith('left') or n.endswith('.l') or n.endswith('_l'): return 'L'
    if n.startswith('right') or n.endswith('.r') or n.endswith('_r'): return 'R'
    return None


def load(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.blend':
        bpy.ops.wm.open_mainfile(filepath=path)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=path)
        elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=path)
        else: raise ValueError(path)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' and m.object for m in o.modifiers)]
    return arms, meshes


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)


def apply_pose(arm, spec):
    """Rotate bones about world axes through their (posed) heads, parent first."""
    reset_pose(arm)
    bpy.context.view_layer.update()
    want = {}
    for b, ax, deg in spec: want.setdefault(b, []).append((ax, deg))
    aw = arm.matrix_world.to_3x3(); awi = aw.inverted()
    rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    cum = {}; head = {}

    def order(bone):
        yield bone
        for c in bone.children: yield from order(c)
    roots = [b for b in arm.data.bones if b.parent is None]
    for root in roots:
        for b in order(root):
            R = Matrix.Identity(3)
            for ax, deg in want.get(b.name, []):
                R = Matrix.Rotation(math.radians(deg), 3, awi @ AXES[ax]) @ R  # world axis -> armature space
            p = b.parent
            if p is None:
                cum[b.name] = R; head[b.name] = rest[b.name].translation.copy()
            else:
                cum[b.name] = cum[p.name] @ R
                head[b.name] = head[p.name] + cum[p.name] @ (rest[b.name].translation - rest[p.name].translation)
            hr = rest[b.name].translation
            M = Matrix.Translation(head[b.name]) @ cum[b.name].to_4x4() @ Matrix.Translation(-hr) @ rest[b.name]
            arm.pose.bones[b.name].matrix = M
            bpy.context.view_layer.update()


def evaluated_coords(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg); me = oe.to_mesh()
    co = [oe.matrix_world @ v.co for v in me.vertices]
    oe.to_mesh_clear()
    return co


def tri_edges(me):
    """edges of the TRIANGULATED mesh (what game engines render) - includes quad/ngon diagonals"""
    me.calc_loop_triangles()
    E = {tuple(sorted(e.vertices)) for e in me.edges}
    for t in me.loop_triangles:
        a, b, c = t.vertices
        E.update({tuple(sorted((a, b))), tuple(sorted((b, c))), tuple(sorted((a, c)))})
    return sorted(E)


def islands(me):
    par = list(range(len(me.vertices)))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    # exporters split vertices along UV seams / sharp edges: re-join verts sharing a position
    first = {}
    for v in me.vertices:
        k = tuple(round(c, 5) for c in v.co)
        if k in first:
            a, b = f(v.index), f(first[k])
            if a != b: par[a] = b
        else: first[k] = v.index
    return [f(i) for i in range(len(me.vertices))]


def weight_problems(ob, arm, side_eps=0.02, island_side=0.08):
    """Side rule: a separate mesh piece (island) whose centre is clearly left (x > 0.08) or right is that limb's piece -
    all its verts must avoid the other side's bones (bulky trouser legs may overlap the centre line). Pieces near the
    centre line (shirts, belts, hip shells) are judged per vertex: x > 0.02 no Right* bones, x < -0.02 no Left* bones."""
    bones = {b.name for b in arm.data.bones if b.use_deform}
    names = {g.index: g.name for g in ob.vertex_groups}
    mw = ob.matrix_world
    X = [(mw @ v.co).x for v in ob.data.vertices]
    isl = islands(ob.data); acc = {}
    for i, r in enumerate(isl):
        a = acc.setdefault(r, [0.0, 0]); a[0] += X[i]; a[1] += 1
    cx = {r: a[0] / a[1] for r, a in acc.items()}
    bad = {}
    for v in ob.data.vertices:
        ws = [(names[g.group], g.weight) for g in v.groups if names.get(g.group) in bones and g.weight > 0]
        why = []
        if len(ws) > MAX_INFLUENCES: why.append('>4 influences')
        if any(w < MIN_WEIGHT - 1e-6 for _, w in ws): why.append('weight<0.01')
        s = sum(w for _, w in ws)
        if abs(s - 1) > 0.01: why.append('not normalized (%.3f)' % s)
        sides = {side_of(n) for n, _ in ws} - {None}
        if len(sides) > 1: why.append('left+right bones')
        c = cx[isl[v.index]]
        own = 'L' if c > island_side else 'R' if c < -island_side else ('L' if X[v.index] > side_eps else 'R' if X[v.index] < -side_eps else 'C')
        if (own == 'L' and 'R' in sides) or (own == 'R' and 'L' in sides) or (own == 'C' and sides):
            why.append('wrong-side bones')
        if why: bad[v.index] = why
    return bad


def check_file(path, poses, skip):
    arms, meshes = load(path)
    meshes = [m for m in meshes if m.name not in skip]
    rows = []
    for ob in meshes:
        arm = next(m.object for m in ob.modifiers if m.type == 'ARMATURE' and m.object)
        reset_pose(arm); bpy.context.view_layer.update()
        rest = evaluated_coords(ob)
        edges = tri_edges(ob.data)
        rl = [(rest[a] - rest[b]).length for a, b in edges]
        wbad = weight_problems(ob, arm)
        kinds = {}
        for w in wbad.values():
            for k in w: kinds[k.split(' (')[0]] = kinds.get(k.split(' (')[0], 0) + 1
        rows.append(dict(model=os.path.basename(path), mesh=ob.name, pose='weights', worst=1.0, squash=1.0,
                         bad=len(wbad), detail=kinds, ok=not wbad))
        for pname in poses:
            apply_pose(arm, POSES[pname])
            co = evaluated_coords(ob)
            worst, squash, badv = 1.0, 1.0, set()
            for (a, b), l0 in zip(edges, rl):
                if l0 < 1e-5: continue
                r = (co[a] - co[b]).length / l0
                if r > worst: worst = r
                if r < squash: squash = r
                if r > STRETCH_MAX or r < SQUASH_MIN: badv.update((a, b))
            rows.append(dict(model=os.path.basename(path), mesh=ob.name, pose=pname, worst=round(worst, 3), squash=round(squash, 3),
                             bad=len(badv), ok=not badv))
        reset_pose(arm); bpy.context.view_layer.update()
    return rows


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    poses = list(POSES); skip = set(); out_json = None; paths = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--poses': poses = argv[i + 1].split(','); i += 2; continue
        if a == '--skip-mesh': skip.add(argv[i + 1]); i += 2; continue
        if a == '--json': out_json = argv[i + 1]; i += 2; continue
        paths.append(a); i += 1
    files = []
    for p in paths:
        if os.path.isdir(p):
            for f in sorted(glob.glob(os.path.join(p, '**', '*'), recursive=True)):
                if '_backup' in f.split(os.sep): continue
                if os.path.splitext(f)[1].lower() in ('.glb', '.gltf', '.fbx', '.blend'): files.append(f)
        else: files.append(p)
    all_rows = []
    for f in files:
        all_rows += check_file(f, poses, skip)
    # per model/pose summary (worst over meshes)
    summ = {}
    for r in all_rows:
        k = (r['model'], r['pose'])
        s = summ.setdefault(k, dict(worst=1.0, squash=1.0, bad=0, ok=True, meshes=[]))
        s['worst'] = max(s['worst'], r['worst']); s['squash'] = min(s['squash'], r['squash'])
        s['bad'] += r['bad']; s['ok'] &= r['ok']
        if not r['ok']: s['meshes'].append(r['mesh'])
    w = max([len(k[0]) for k in summ] + [5])
    print(f"{'model':<{w}} | {'pose':<9} | worst stretch | worst squash | bad verts | result")
    print('-' * (w + 66))
    fails = 0
    for (m, p), s in summ.items():
        res = 'PASS' if s['ok'] else 'FAIL'
        fails += not s['ok']
        extra = '' if s['ok'] else '  <- ' + ', '.join(sorted(set(s['meshes'])))[:80]
        print(f"{m:<{w}} | {p:<9} | {s['worst']:>13.3f} | {s['squash']:>12.3f} | {s['bad']:>9} | {res}{extra}")
    print(f"\n{len(summ) - fails}/{len(summ)} checks passed")
    if out_json: json.dump(all_rows, open(out_json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
