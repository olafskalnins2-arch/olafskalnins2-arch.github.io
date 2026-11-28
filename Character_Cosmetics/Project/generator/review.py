# Review sheet for one outfit worn on the base body (what a person sees in game).
#   python3 review.py OUT.png BODY.glb OUTFIT.glb
# Row 1: front / side / back / 3-4 (rest pose)      Row 2: hip side / hip 3-4 / from below / hip front (close-ups)
# Row 3: walk front / walk side / spread front / spread low-back (crotch) / crouch
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Roblox_Ready'))
import check_rig as C
from PIL import Image, ImageDraw

out, body, glb = sys.argv[1:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
for o in list(bpy.data.objects):
    if o.name == 'Icosphere': bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.78, 0.75, 0.70, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
for nm, en, rot in (('key', 3.2, (50, 0, -35)), ('fill', 1.0, (60, 0, 140)), ('under', 0.8, (200, 0, 20))):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en; ld.angle = 0.3
    lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo); lo.rotation_euler = tuple(math.radians(r) for r in rot)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co); sc.camera = co
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']

def shot(path, pose, az, el, zc, scale, res):
    for a in arms:
        if pose: C.apply_pose(a, C.POSES[pose])
        else: C.reset_pose(a)
    bpy.context.view_layer.update()
    a_, e_ = math.radians(az), math.radians(el)
    d = Vector((math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_)))
    co.location = Vector((0, 0, zc)) + d * 14; co.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); cd.ortho_scale = scale
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    return Image.open(path).convert('RGB')

rows = [
    [(None, 0, 0, 2.5, 5.6), (None, 90, 0, 2.5, 5.6), (None, 180, 0, 2.5, 5.6), (None, 35, 0, 2.5, 5.6)],
    [(None, 90, 0, 1.9, 2.4), (None, 40, -20, 1.9, 2.4), (None, 20, -55, 1.9, 2.6), (None, 0, 0, 1.9, 2.4)],
    [('walk', 0, 0, 2.4, 5.4), ('walk', 90, 0, 2.4, 5.4), ('spread', 0, 0, 2.2, 4.6), ('spread', 180, -25, 1.9, 3.0), ('crouch', 60, 0, 2.2, 5.0)],
]
labels = [['front', 'side', 'back', '3/4'], ['hip side', 'hip 3/4', 'from below', 'hip front'],
          ['walk', 'walk side', 'spread', 'spread low back', 'crouch']]
TW, TH = 300, 400
sheet = Image.new('RGB', (TW * 5, TH * 3), (200, 196, 190)); dr = ImageDraw.Draw(sheet)
tmp = out + '.tile.png'
for r, row in enumerate(rows):
    for c, (pose, az, el, zc, s) in enumerate(row):
        sheet.paste(shot(tmp, pose, az, el, zc, s, (TW, TH)), (c * TW, r * TH))
        dr.text((c * TW + 6, r * TH + 4), labels[r][c], fill=(0, 0, 0))
dr.text((TW * 4 + 6, 8), os.path.basename(glb), fill=(0, 0, 0))
os.remove(tmp)
sheet.save(out)
print('review saved', out)
