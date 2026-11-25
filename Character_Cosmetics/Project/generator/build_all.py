import sys, os, json, time, shutil, importlib
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from pipeline import *
from viewer import *
import o01, o02, o03, o04

ROOT = sys.argv[-1]
OUTFITS = [
    ('01', 'Classic_Mover', o01.classic_mover, 0.32), ('02', 'Chill_Dude', o02.chill_dude, 0.32),
    ('03', 'Raincoat', o02.raincoat, 0.7), ('04', 'Boss_Mode', o02.boss_mode, 0.32),
    ('05', 'Construction_Hero', o03.construction_hero, 0.32), ('06', 'Chef', o03.chef, 0.32),
    ('07', 'Firefighter', o03.firefighter, 0.32), ('08', 'Pirate', o03.pirate, 0.7),
    ('09', 'Wizard', o03.wizard, 0.7), ('10', 'Knight', o04.knight, 0.32),
    ('11', 'Astronaut', o04.astronaut, 0.32), ('12', 'Ghost', o04.ghost, 1.6), ('13', 'Dinosaur', o04.dino, 0.32),
]
only = os.environ.get('ONLY')
for d in ('Project', 'Roblox_Ready', 'Textures', 'Preview'): os.makedirs(os.path.join(ROOT, d), exist_ok=True)
load_body()
co = setup_scene((600, 820), 24)
for m in B.obj.data.materials:  # preview only: show GLB colour factors the way Roblox shows them (sRGB)
    bc = m.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    bc.default_value = tuple((c ** 2.2) if i < 3 else c for i, c in enumerate(bc.default_value))
report = {}
allobjs = {}
for num, name, fn, maxd in OUTFITS:
    if only and num not in only.split(','): continue
    t0 = time.time()
    P, pal = fn()
    finalize_pieces(P)
    tex = os.path.join(ROOT, 'Textures', f'{num}_{name}_Albedo.png')
    uvmap = build_atlas(P, pal, tex)
    mat = make_material(f'{num}_{name}_Mat', tex)
    col = bpy.data.collections.new(f'{num}_{name}'); bpy.context.scene.collection.children.link(col)
    objs = build_objects(f'{num}_{name}', P, uvmap, mat, col)
    allobjs[num] = (name, col, objs)
    cov = coverage_report(objs, maxd)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    infl = max(sum(1 for g in v.groups if g.weight > 0) for o in objs for v in o.data.vertices)
    report[f'{num}_{name}'] = dict(pieces=len(P), meshes=[o.name for o in objs], triangles=tris, max_bone_influences=infl,
                                   texture=os.path.basename(tex), coverage=cov)
    print(num, name, 'tris', tris, cov, round(time.time() - t0, 1), 's', flush=True)

# ---------- exports ----------
def select_only(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = B.arm

for num, (name, col, objs) in allobjs.items():
    d = os.path.join(ROOT, 'Roblox_Ready', f'{num}_{name}'); os.makedirs(d, exist_ok=True)
    for o in bpy.data.objects: o.hide_set(False); o.hide_render = False
    set_pose(None)
    select_only([B.arm] + objs)
    bpy.ops.export_scene.gltf(filepath=os.path.join(d, f'{num}_{name}.glb'), export_format='GLB', use_selection=True,
                              export_animations=False, export_skins=True, export_apply=False, export_yup=True,
                              export_image_format='AUTO', export_texcoords=True, export_normals=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(d, f'{num}_{name}.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'},
                             add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True,
                             mesh_smooth_type='FACE', use_armature_deform_only=True, armature_nodetype='NULL')
    shutil.copy(os.path.join(ROOT, 'Textures', f'{num}_{name}_Albedo.png'), os.path.join(d, f'{num}_{name}_Albedo.png'))

# ---------- previews ----------
def show_only(num):
    for k, (n, c, objs) in allobjs.items():
        for o in objs: o.hide_render = (k != num); o.hide_set(k != num)

sheets = []
for num, (name, col, objs) in allobjs.items():
    show_only(num)
    paths = []
    for i, (ang, pose) in enumerate([(0, None), (35, None), (180, None), (30, 'walk'), (30, 'carry')]):
        set_pose(pose); cam_to(co, ang)
        p = os.path.join(ROOT, 'Preview', f'_tmp_{num}_{i}.png'); render(p); paths.append(p)
    set_pose(None)
    ims = [Image.open(p) for p in paths]
    W, H = ims[0].size
    sheet = Image.new('RGB', (W * len(ims), H + 60), ims[0].getpixel((5, 5)))
    for k, im in enumerate(ims): sheet.paste(im, (k * W, 60))
    from PIL import ImageDraw, ImageFont
    dr = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    except Exception: font = small = None
    dr.text((20, 12), f'{num}  {name.replace("_", " ")}', fill=(40, 40, 40), font=font)
    for k, lab in enumerate(['front', '3/4', 'back', 'walk pose', 'carry pose']):
        dr.text((k * W + W // 2 - 50, H + 20), lab, fill=(90, 90, 90), font=small)
    sheet.save(os.path.join(ROOT, 'Preview', f'{num}_{name}.png'))
    ims[0].save(os.path.join(ROOT, 'Preview', f'{num}_{name}_front.png'))
    for p in paths: os.remove(p)
    sheets.append((num, name, os.path.join(ROOT, 'Preview', f'{num}_{name}_front.png')))

# contact sheet
if len(sheets) == 13:
    from PIL import ImageDraw, ImageFont
    ims = [Image.open(p) for _, _, p in sheets]
    W, H = ims[0].size; cols = 7
    sw, sh = W // 2, H // 2
    bg = ims[0].getpixel((5, 5)); sheet = Image.new('RGB', (cols * sw, 2 * (sh + 40)), bg)
    dr = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except Exception: font = None
    for k, ((num, name, _), im) in enumerate(zip(sheets, ims)):
        r, c = divmod(k, cols)
        if r == 1: c += 0.5
        x = int(c * sw); y = r * (sh + 40)
        sheet.paste(im.resize((sw, sh)), (x, y))
        dr.text((x + 10, y + sh + 8), f'{num} {name.replace("_", " ")}', fill=(40, 40, 40), font=font)
    sheet.save(os.path.join(ROOT, 'Preview', 'All_Outfits.png'))

# ---------- import helper: your body + all outfits on the one shared skeleton ----------
if len(allobjs) == 13:
    for o in bpy.data.objects: o.hide_set(False); o.hide_render = False
    set_pose(None)
    alls = [o for _, (_, _, objs) in allobjs.items() for o in objs]
    d = os.path.join(ROOT, 'Roblox_Ready', '00_Import_Helper'); os.makedirs(d, exist_ok=True)
    # restore the body's original material colours for export (preview tweak undone)
    for m in B.obj.data.materials:
        bc = m.node_tree.nodes['Principled BSDF'].inputs['Base Color']
        bc.default_value = tuple((c ** (1 / 2.2)) if i < 3 else c for i, c in enumerate(bc.default_value))
    select_only([B.arm, B.obj] + alls)
    bpy.ops.export_scene.gltf(filepath=os.path.join(d, 'CosmeticsRig.glb'), export_format='GLB', use_selection=True,
                              export_animations=False, export_skins=True, export_apply=False, export_yup=True)
    for m in B.obj.data.materials:
        bc = m.node_tree.nodes['Principled BSDF'].inputs['Base Color']
        bc.default_value = tuple((c ** 2.2) if i < 3 else c for i, c in enumerate(bc.default_value))

# ---------- blender project ----------
for k, (n, c, objs) in allobjs.items():
    for o in objs: o.hide_render = (k != '01'); o.hide_set(k != '01')
bpy.ops.file.pack_all() if False else None
blend = os.path.join(ROOT, 'Project', 'Character_Cosmetics.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_mainfile()
json.dump(report, open(os.path.join(ROOT, 'Project', 'build_report.json'), 'w'), indent=1)
print('DONE')
