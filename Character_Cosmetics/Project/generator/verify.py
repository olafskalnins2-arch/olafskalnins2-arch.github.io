# Verify every exported file: re-import, check skeleton == original, skin data, textures.
import sys, os, json, struct, glob
import bpy
ROOT = sys.argv[-1]
ORIG = __import__('os').environ.get('CHARACTER_GLB', 'character_smooth_v2.glb')
def gj(p):
    d = open(p, 'rb').read(); L = struct.unpack('<I', d[12:16])[0]; return json.loads(d[20:20 + L])
oj = gj(ORIG)
onodes = {n['name']: n for n in oj['nodes']}
bones = [oj['nodes'][i]['name'] for i in oj['skins'][0]['joints']]
def world(nodes, name):
    by = {n['name']: n for n in nodes}; par = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []): par[nodes[c]['name']] = n['name']
    t = [0, 0, 0]; k = name
    while k:
        tr = by[k].get('translation', [0, 0, 0]); t = [a + b for a, b in zip(t, tr)]; k = par.get(k)
    return t
res = {}
for f in sorted(glob.glob(os.path.join(ROOT, 'Roblox_Ready', '*', '*.glb'))):
    j = gj(f); name = os.path.basename(f)
    r = {}
    jn = [j['nodes'][i]['name'] for i in j['skins'][0]['joints']]
    r['same_15_bones'] = sorted(jn) == sorted(bones)
    err = max(max(abs(a - b) for a, b in zip(world(j['nodes'], b), world(oj['nodes'], b))) for b in bones)
    r['max_joint_pos_error'] = float(f'{err:.2e}')
    rots = [n.get('rotation', [0, 0, 0, 1]) for n in j['nodes'] if n['name'] in bones]
    r['max_joint_rot_dev'] = float(f"{max(max(abs(q[0]), abs(q[1]), abs(q[2]), abs(1 - q[3])) for q in rots):.1e}")
    meshes = [n['name'] for n in j['nodes'] if 'mesh' in n]
    r['meshes'] = meshes
    r['contains_body'] = 'Body' in meshes
    attrs = set(k for m in j['meshes'] for p in m['primitives'] for k in p['attributes'])
    r['has_uv_joints_weights'] = all(a in attrs for a in ('TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0'))
    r['embedded_images'] = len(j.get('images', []))
    r['materials_per_outfit'] = len(j.get('materials', []))
    # re-import in Blender
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    ms = [o for o in bpy.data.objects if o.type == 'MESH' and not (o.name.startswith('Icosphere') and not o.modifiers)]  # importer's bone-shape helper
    r['reimport_ok'] = len(arms) == 1 and len(ms) == len(meshes) and all(any(m.type == 'ARMATURE' for m in o.modifiers) for o in ms)
    tris = 0
    for o in ms:
        o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
    r['triangles'] = tris
    r['max_tris_single_mesh'] = max(len(o.data.loop_triangles) for o in ms)
    res[name] = r
for f in sorted(glob.glob(os.path.join(ROOT, 'Roblox_Ready', '*', '*.fbx'))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    ms = [o for o in bpy.data.objects if o.type == 'MESH']
    bn = sorted(b.name for b in arms[0].data.bones) if arms else []
    imgs = [i for i in bpy.data.images if i.has_data or i.packed_file or os.path.exists(bpy.path.abspath(i.filepath))]
    # joint positions
    err = 0
    if arms:
        A = arms[0]
        for b in A.data.bones:
            wp = A.matrix_world @ b.head_local
            o = world(oj['nodes'], b.name)  # gltf Y-up -> blender Z-up
            err = max(err, abs(wp.x - o[0]), abs(wp.y + o[2]), abs(wp.z - o[1]))
    res[os.path.basename(f)] = dict(reimport_ok=len(arms) == 1 and len(ms) >= 1, same_15_bones=bn == sorted(bones),
                                    max_joint_pos_error=float(f'{err:.2e}'), meshes=[o.name for o in ms], textures_found=len(imgs) > 0,
                                    vertex_groups_ok=all(len(o.vertex_groups) >= 1 for o in ms))
json.dump(res, open(os.path.join(ROOT, 'Project', 'export_verification.json'), 'w'), indent=1)
bad = {k: v for k, v in res.items() if not (v.get('reimport_ok') and v.get('same_15_bones') and v.get('max_joint_pos_error', 1) < 1e-3)}
print('FILES', len(res), 'PROBLEMS', json.dumps(bad, indent=1))
