# Completion, Export & Rig Checklist

All numbers come from automated checks on the delivered files: `Rig_Check/check_rig_AFTER.txt` (rig check),
`Project/export_verification.json` (re-import of every GLB/FBX), `Project/build_report.json` (fit / coverage).

## Rig check (check_rig.py) - worst stretch / worst squash per pose, GLB file

Limits: every triangulated edge must stay between 0.5x and 1.5x of its rest length. "Before" = the original files in `_backup/`.

| Model | weights rules | walk | spread | arms up | arms down | crouch | before (passed) |
|---|---|---|---|---|---|---|---|
| character smooth v2 | PASS | 1.24 / 0.77 PASS | 1.27 / 0.75 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.49 / 0.50 PASS | 1/6 |
| 01 Classic Mover | PASS | 1.26 / 0.66 PASS | 1.49 / 0.65 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.48 / 0.50 PASS | 0/6 |
| 02 Chill Dude | PASS | 1.32 / 0.68 PASS | 1.49 / 0.62 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.47 / 0.50 PASS | 0/6 |
| 03 Raincoat | PASS | 1.29 / 0.70 PASS | 1.47 / 0.67 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.46 / 0.50 PASS | 0/6 |
| 04 Boss Mode | PASS | 1.27 / 0.65 PASS | 1.50 / 0.70 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.48 / 0.50 PASS | 0/6 |
| 05 Construction Hero | PASS | 1.26 / 0.66 PASS | 1.49 / 0.69 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.47 / 0.50 PASS | 0/6 |
| 06 Chef | PASS | 1.26 / 0.66 PASS | 1.47 / 0.69 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.48 / 0.51 PASS | 0/6 |
| 07 Firefighter | PASS | 1.26 / 0.69 PASS | 1.49 / 0.59 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.49 / 0.51 PASS | 0/6 |
| 08 Pirate | PASS | 1.29 / 0.69 PASS | 1.49 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.48 / 0.50 PASS | 0/6 |
| 09 Wizard | PASS | 1.48 / 0.61 PASS | 1.48 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.49 / 0.51 PASS | 0/6 |
| 10 Knight | PASS | 1.28 / 0.67 PASS | 1.50 / 0.68 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.47 / 0.50 PASS | 0/6 |
| 11 Astronaut | PASS | 1.35 / 0.64 PASS | 1.50 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.50 / 0.51 PASS | 0/6 |
| 12 Ghost | PASS | 1.42 / 0.71 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 3/6 |
| 13 Dinosaur | PASS | 1.37 / 0.64 PASS | 1.50 / 0.59 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.50 / 0.50 PASS | 0/6 |

**All files (27 outfit GLB/FBX + CosmeticsRig + base character + .blend): 174/174 checks PASS after, 7/174 before.**

## Per outfit

| # | Outfit | Modeled | Textured | GLB | FBX | Tris (total / biggest mesh) | Rig check |
|---|---|---|---|---|---|---|---|
| 01 | Classic Mover | YES | YES | YES | YES | 9008 / 3668 | PASS 12/12 |
| 02 | Chill Dude | YES | YES | YES | YES | 7132 / 3340 | PASS 12/12 |
| 03 | Raincoat | YES | YES | YES | YES | 9620 / 5236 | PASS 12/12 |
| 04 | Boss Mode | YES | YES | YES | YES | 11268 / 6948 | PASS 12/12 |
| 05 | Construction Hero | YES | YES | YES | YES | 10040 / 4556 | PASS 12/12 |
| 06 | Chef | YES | YES | YES | YES | 8512 / 4024 | PASS 12/12 |
| 07 | Firefighter | YES | YES | YES | YES | 8864 / 4152 | PASS 12/12 |
| 08 | Pirate | YES | YES | YES | YES | 13336 / 8252 | PASS 12/12 |
| 09 | Wizard | YES | YES | YES | YES | 9472 / 6280 | PASS 12/12 |
| 10 | Knight | YES | YES | YES | YES | 10768 / 4736 | PASS 12/12 |
| 11 | Astronaut | YES | YES | YES | YES | 10396 / 4864 | PASS 12/12 |
| 12 | Ghost | YES | YES | YES | YES | 5720 / 5720 | PASS 12/12 |
| 13 | Dinosaur | YES | YES | YES | YES | 8672 / 2944 | PASS 12/12 |

## What each outfit contains

- **01_Classic_Mover**: Blue short-sleeve work shirt (collar, chest pocket, buttons), brown belt + buckle, beige cargo trousers with thigh pockets, brown work boots. Meshes: 01_Classic_Mover_Bottom, 01_Classic_Mover_Feet, 01_Classic_Mover_Top.
- **02_Chill_Dude**: Orange Hawaiian shirt with turquoise hibiscus print (untucked, open collar, buttons), turquoise shorts, flip-flops, skin-colour leg covers. Meshes: 02_Chill_Dude_Bottom, 02_Chill_Dude_Feet, 02_Chill_Dude_Top.
- **03_Raincoat**: Yellow raincoat (stand collar, hood folded down, drawstrings, 5 buttons, flap pockets), yellow trousers, tall yellow rain boots. Meshes: 03_Raincoat_Bottom, 03_Raincoat_Feet, 03_Raincoat_Top.
- **04_Boss_Mode**: Navy suit jacket with V opening + lapels + 2 buttons, white shirt + collar + cuffs, red tie with knot, navy trousers, black dress shoes. Meshes: 04_Boss_Mode_Bottom, 04_Boss_Mode_Extras, 04_Boss_Mode_Feet, 04_Boss_Mode_Top.
- **05_Construction_Hero**: Orange hi-vis vest with yellow/silver reflective stripes, grey undershirt, tool belt (pouches, buckle, hammer, screwdriver), beige trousers, grey work boots. Meshes: 05_Construction_Hero_Bottom, 05_Construction_Hero_Extras, 05_Construction_Hero_Feet, 05_Construction_Hero_Top.
- **06_Chef**: White double-breasted chef jacket (2x3 buttons, stand collar), black/white checkered trousers, green clogs with vents + heel strap. Meshes: 06_Chef_Bottom, 06_Chef_Extras, 06_Chef_Feet, 06_Chef_Top.
- **07_Firefighter**: Red jacket with yellow/silver reflective bands, dark belt band, metal clasps, stand collar, dark trousers with reflective bands, black boots. Meshes: 07_Firefighter_Bottom, 07_Firefighter_Extras, 07_Firefighter_Feet, 07_Firefighter_Top.
- **08_Pirate**: Long open brown coat (lapels, collar, big cuffs, back vent), beige V-neck shirt, brown belt + gold buckle, red/white striped trousers, tall black cuffed boots. Meshes: 08_Pirate_Bottom, 08_Pirate_Extras, 08_Pirate_Feet, 08_Pirate_Top.
- **09_Wizard**: Purple robe with gold stars + moons, light trim + V neckline, wide bell sleeves, purple sash + knot, curled purple shoes, skin-colour leg covers. Meshes: 09_Wizard_Bottom, 09_Wizard_Extras, 09_Wizard_Feet, 09_Wizard_Top.
- **10_Knight**: Steel cuirass, gorget, pauldrons + lames, couters, vambraces, layered faulds + mail skirt, cuisses, knee poleyns, greaves, sabatons. Meshes: 10_Knight_Bottom, 10_Knight_Feet, 10_Knight_Top.
- **11_Astronaut**: Bulky white suit, padded sleeves/legs, neck ring, harness straps, chest control panel, wide belt + pouches, backpack, knee pads, bulky boots. Meshes: 11_Astronaut_Bottom, 11_Astronaut_Extras, 11_Astronaut_Feet, 11_Astronaut_Top.
- **12_Ghost**: Full-body white sheet (bell shape, folds, wavy hem) with two dark oval eye holes. Meshes: 12_Ghost_Top.
- **13_Dinosaur**: Green onesie with light belly, hood with rim, spikes on hood + spine + tail, long spiked tail, puffy sleeves with claws, dino feet with claws. Meshes: 13_Dinosaur_Bottom, 13_Dinosaur_Extras, 13_Dinosaur_Feet, 13_Dinosaur_Head, 13_Dinosaur_Top.

## What changed in the rig fix (weights only, plus one mesh fix on the base body)

- **Base character**: the original weights had 2715 verts with junk weights < 0.01 (1307 of them leaking onto the
  opposite side), torso skin under the arms weighted to the upper arms (6.4x stretch with arms up), a hard
  left/right split at the crotch (2.2x tear in a leg spread) and knee/hip blends too tight for a crouch.
  New weights: clean joint ramps (waist, hips, knees, elbows, short ankle/wrist), centre line torso-only,
  hard shoulder seam, max 4 influences, >= 0.01, normalized. All 3512 vertex positions are unchanged.
- **Mesh fix (base body only):** the torso had two open shoulder sockets (and each arm an open end) stitched
  at the shoulder. With rig-safe weights those openings showed the hollow inside of the character when an arm moved,
  so the 4 holes were capped with faces: +4 faces (+88 triangles), no vertex moved or added.
- **Outfits**: weights re-transferred from the fixed body, region-locked (sleeve <- its arm, trouser leg <- its leg,
  boots <- foot/shin, shirt <- torso), left/right cleaned, rigid bits on one bone, inner/outer shell verts tied,
  then a local repair pass fixes any edge that still fails a test pose. Geometry, UVs, textures and materials of every
  outfit are byte-for-byte the same as before (checked; see Rig_Check/README.md).

## Known limitations (straight up)

- **09 Wizard robe - fixed with your OK (mesh change)**: weights alone can't keep legs inside a closed long robe without
  2-4x webbing (Rig_Check/wizard_robe_tradeoff.txt). So the robe skirt is cut into panels below the sash: front centre,
  back centre and both sides, plus one extra cut per side splitting each back panel into an inner and a side strip.
  The cuts duplicate vertices in place, so standing still the robe looks exactly the same. Each panel hangs off its own
  thigh (front + side strips fully, back inner strips 80%), so in walk / spread / crouch the slits open like a real slit robe
  and no leg goes through the cloth (measured: 0 leg-through-robe verts in all five poses). The hidden skin-colour leg
  covers now reach the hips (they were z 1.3), so legs seen through a slit are orange, not grey.
  Exact geometry change: the robe's outside surface is unchanged; 84 verts of its inside (backface) shell along the cut
  edges moved by <= 6.6 mm; the 2 leg covers are longer (641 old verts replaced by 1145 new ones, all under the robe).
- **12 Ghost - accepted as is (your call)**: one solid sheet, no cloth sim, passes every stretch check. Hands stick out in walk / arms up / crouch, feet in
  a wide spread. Proof: Rig_Check/ghost_sheet_tradeoff.txt - letting the sheet follow the arms costs 2.5-4.5x stretch in
  walk and 12-14x in arms up (the hands go above the sheet's head).
- **Soft knees/hips**: to keep an 80-degree crouch inside 0.5x-1.5x, the knee and hip blends are long, so thighs bend as a
  smooth curve (rubber-hose style) instead of a sharp hinge.
- **Thin margins**: the repair pass stops as soon as an edge is legal, so many results sit right at the limit (spread 1.49-1.50x, crouch squash 0.50x). They pass, but there is no headroom: a deeper crouch or wider spread than the test poses will exceed 1.5x somewhere.
- **Shoes** sit about 0.025 units below the feet (sole thickness).
- **Rendered**: all five check poses, front / side / back, before and after, for all 14 models (Rig_Check/).
- **Not tested inside Roblox Studio.** Everything is checked in Blender with the same linear blend skinning Roblox uses.
  Re-import the fixed base character (Base_Character/character_smooth_v2.glb) too, or your live character will keep its old weights.
