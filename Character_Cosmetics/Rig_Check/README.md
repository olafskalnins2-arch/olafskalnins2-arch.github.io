# Rig check - before / after

`before_after/NN_Name.jpg` - top row BEFORE (original files from `../_backup/`), bottom row AFTER (fixed files),
each in the **walk** and **legs spread wide** poses, front / side / back. Every outfit is rendered on the base character
(before: original body, after: fixed body).

`check_rig_BEFORE.txt` / `check_rig_AFTER.txt` - full output of `../Roblox_Ready/check_rig.py` on every model file
(all GLB + FBX, CosmeticsRig.glb, the base character, the .blend). **Before: 7/174 checks passed. After: 174/174.**

What the AFTER renders show (checked by eye, crotch / armpits / waist):
- No webbing between the legs on any trousers, boots, coats or the dino suit (before: solid sheets between the feet in
  the spread pose on Classic Mover, Raincoat, Construction Hero, Firefighter, Pirate, Knight, Astronaut, Dinosaur).
- No sleeve-to-torso webbing, no dark hole at the shoulder socket of the base body.
- Waist / belt line smooth in walk and spread.
- Still visible (known, see ../CHECKLIST.md): the Wizard's knee/shin pushes out of the robe front in a big stride or
  leg spread; the Ghost's hands/feet poke out of the sheet in big poses.

Not rendered (checked by script only): arms up, arms down, crouch.

Geometry proof (weights-only): every exported outfit has the same vertex positions, UVs, triangle count, embedded
texture and materials as its backup. The base character has the same 3512 vertex positions and materials, plus 4 cap
faces (+88 triangles) closing the open shoulder sockets.
