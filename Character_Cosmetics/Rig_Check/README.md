# Rig check - before / after

`before_after/NN_Name.jpg` - top row BEFORE (original files from `../_backup/`), bottom row AFTER (fixed files),
each in the **walk** and **legs spread wide** poses, front / side / back.
`before_after_all_poses/NN_Name.jpg` - left BEFORE, right AFTER, all five check poses (walk, spread, arms up, arms down,
crouch) x front / side / back. Every outfit is rendered on the base character (before: original body, after: fixed body).

`check_rig_BEFORE.txt` / `check_rig_AFTER.txt` - full output of `../Roblox_Ready/check_rig.py` on every model file
(all GLB + FBX, CosmeticsRig.glb, the base character, the .blend). **Before: 7/174 checks passed. After: 174/174.**

What the AFTER renders show (checked by eye, crotch / armpits / waist):
- No webbing between the legs on any trousers, boots, coats or the dino suit (before: solid sheets between the feet in
  the spread pose on Classic Mover, Raincoat, Construction Hero, Firefighter, Pirate, Knight, Astronaut, Dinosaur).
- No sleeve-to-torso webbing, no dark hole at the shoulder socket of the base body.
- Waist / belt line smooth in walk and spread.
- All five poses rendered and reviewed for all 14 models: no stretching / webbing anywhere.
- Wizard: fixed with an approved mesh change (robe cut into panels, invisible at rest; leg covers to the hips):
  no leg goes through the robe in any pose, no grey shows. `wizard_robe_tradeoff.txt` shows why weights alone couldn't.
- Ghost: hands/feet stick out of the sheet in big poses - accepted as is by you (`ghost_sheet_tradeoff.txt` shows every
  arm-follow setting breaks the 1.5x limit: 2.5-4.5x walk, 12-14x arms up).

Geometry proof: every exported outfit except the Wizard has the same vertex positions, UVs, triangle count, embedded
texture and materials as its backup (Wizard: see ../CHECKLIST.md for the exact approved change). The base character has the same 3512 vertex positions and materials, plus 4 cap
faces (+88 triangles) closing the open shoulder sockets.
