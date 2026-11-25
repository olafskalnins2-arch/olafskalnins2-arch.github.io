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
- NOT fixed (needs a shape decision, see ../CHECKLIST.md): the Wizard's knee/thigh pushes out of the closed robe in walk,
  spread and crouch; the Ghost's hands/feet stick out of the sheet in big poses. These are poke-through, not stretching:
  `wizard_robe_tradeoff.txt` / `ghost_sheet_tradeoff.txt` sweep every weight setting - each one that pulls the limbs
  back inside breaks the 1.5x limit (robe 2-4.5x webbing, ghost 2.5-14x). Weights alone can't do both.

Geometry proof (weights-only): every exported outfit has the same vertex positions, UVs, triangle count, embedded
texture and materials as its backup. The base character has the same 3512 vertex positions and materials, plus 4 cap
faces (+88 triangles) closing the open shoulder sockets.
