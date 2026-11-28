# Completion, Export & Rig Checklist

All numbers come from automated checks on the delivered files: `Rig_Check/check_rig_AFTER.txt` (rig check),
`Project/export_verification.json` (re-import of every GLB/FBX), `Project/build_report.json` (fit / coverage).

## Rig check (check_rig.py) - worst stretch / worst squash per pose, GLB file

Limits: every triangulated edge must stay between 0.5x and 1.5x of its rest length. "Before" = the original files in `_backup/`.

| Model | weights rules | walk | spread | arms up | arms down | crouch | before (passed) |
|---|---|---|---|---|---|---|---|
| character smooth v2 | PASS | 1.24 / 0.77 PASS | 1.27 / 0.75 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.49 / 0.50 PASS | 1/6 |
| 01 Classic Mover | PASS | 1.25 / 0.71 PASS | 1.40 / 0.65 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.46 / 0.50 PASS | 0/6 |
| 02 Chill Dude | PASS | 1.25 / 0.68 PASS | 1.44 / 0.62 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.47 / 0.50 PASS | 0/6 |
| 03 Raincoat | PASS | 1.25 / 0.74 PASS | 1.39 / 0.52 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.43 / 0.50 PASS | 0/6 |
| 04 Boss Mode | PASS | 1.25 / 0.74 PASS | 1.36 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.45 / 0.50 PASS | 0/6 |
| 05 Construction Hero | PASS | 1.25 / 0.74 PASS | 1.36 / 0.69 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.46 / 0.50 PASS | 0/6 |
| 06 Chef | PASS | 1.25 / 0.74 PASS | 1.36 / 0.54 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.44 / 0.50 PASS | 0/6 |
| 07 Firefighter | PASS | 1.25 / 0.72 PASS | 1.38 / 0.53 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.43 / 0.50 PASS | 0/6 |
| 08 Pirate | PASS | 1.25 / 0.74 PASS | 1.36 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.44 / 0.50 PASS | 0/6 |
| 09 Wizard | PASS | 1.50 / 0.50 PASS | 1.48 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.50 / 0.50 PASS | 0/6 |
| 10 Knight | PASS | 1.28 / 0.67 PASS | 1.50 / 0.53 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.47 / 0.50 PASS | 0/6 |
| 11 Astronaut | PASS | 1.28 / 0.61 PASS | 1.42 / 0.51 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.48 / 0.50 PASS | 0/6 |
| 12 Ghost | PASS | 1.42 / 0.71 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 3/6 |
| 13 Dinosaur | PASS | 1.27 / 0.73 PASS | 1.43 / 0.53 PASS | 1.00 / 1.00 PASS | 1.00 / 1.00 PASS | 1.48 / 0.51 PASS | 0/6 |

**All files (27 outfit GLB/FBX + CosmeticsRig + base character + .blend): 534/534 checks PASS after, 7/174 before.**

## Per outfit

| # | Outfit | Modeled | Textured | GLB | FBX | Tris (total / biggest mesh) | Rig check |
|---|---|---|---|---|---|---|---|
| 01 | Classic Mover | YES | YES | YES | YES | 9308 / 3816 | PASS 12/12 |
| 02 | Chill Dude | YES | YES | YES | YES | 7432 / 3372 | PASS 12/12 |
| 03 | Raincoat | YES | YES | YES | YES | 10048 / 5236 | PASS 12/12 |
| 04 | Boss Mode | YES | YES | YES | YES | 11696 / 6948 | PASS 12/12 |
| 05 | Construction Hero | YES | YES | YES | YES | 10340 / 4556 | PASS 12/12 |
| 06 | Chef | YES | YES | YES | YES | 8812 / 4024 | PASS 12/12 |
| 07 | Firefighter | YES | YES | YES | YES | 9164 / 4152 | PASS 12/12 |
| 08 | Pirate | YES | YES | YES | YES | 13636 / 8252 | PASS 12/12 |
| 09 | Wizard | YES | YES | YES | YES | 10600 / 6640 | PASS 12/12 |
| 10 | Knight | YES | YES | YES | YES | 11136 / 5248 | PASS 12/12 |
| 11 | Astronaut | YES | YES | YES | YES | 10696 / 4864 | PASS 12/12 |
| 12 | Ghost | YES | YES | YES | YES | 5720 / 5720 | PASS 12/12 |
| 13 | Dinosaur | YES | YES | YES | YES | 8844 / 2944 | PASS 12/12 |

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
  then a local repair pass fixes any edge that still fails a test pose. At the rig fix, geometry, UVs, textures and materials
  of every outfit were byte-for-byte the same as before; the later shape fix (section below) changed trousers and loose tops.

## New skins 14-43 (30 skins, 4 rarities)

Built from `Project/generator/skins/sNN_Name.py` (one module per skin, rules in `skins/SKIN_GUIDE.md`, concept sketch
`skins/concept_sketch.png`). No headwear on any skin (hats are separate items). Rarity is also in
`Roblox_Ready/Scripts/CosmeticService.lua` (`CosmeticService.RARITY`, `GetRarity`).

| # | Skin | Rarity | Rig (GLB+FBX) | walk | spread | crouch | Tris (total / biggest mesh) |
|---|---|---|---|---|---|---|---|
| 14 | Hoodie Hauler | Common | PASS 12/12 | 1.26 / 0.68 | 1.39 / 0.51 | 1.49 / 0.50 | 12048 / 5668 |
| 15 | Denim Overalls | Common | PASS 12/12 | 1.25 / 0.72 | 1.40 / 0.68 | 1.46 / 0.51 | 9828 / 4404 |
| 16 | Gym Buddy | Common | PASS 12/12 | 1.26 / 0.65 | 1.46 / 0.62 | 1.49 / 0.50 | 7564 / 3372 |
| 17 | Comfy Pajamas | Common | PASS 12/12 | 1.26 / 0.70 | 1.40 / 0.54 | 1.45 / 0.50 | 9780 / 4584 |
| 18 | Parcel Courier | Common | PASS 12/12 | 1.25 / 0.68 | 1.44 / 0.62 | 1.48 / 0.51 | 9720 / 3980 |
| 19 | Green Thumb | Common | PASS 12/12 | 1.27 / 0.65 | 1.50 / 0.63 | 1.49 / 0.50 | 13872 / 7440 |
| 20 | Splash Painter | Common | PASS 12/12 | 1.26 / 0.69 | 1.45 / 0.66 | 1.46 / 0.51 | 9756 / 4736 |
| 21 | Lumberjack | Common | PASS 12/12 | 1.25 / 0.74 | 1.36 / 0.69 | 1.44 / 0.51 | 10200 / 4876 |
| 22 | Mail Carrier | Common | PASS 12/12 | 1.26 / 0.70 | 1.44 / 0.57 | 1.47 / 0.51 | 10444 / 4160 |
| 23 | Barista | Common | PASS 12/12 | 1.50 / 0.51 | 1.49 / 0.51 | 1.50 / 0.50 | 12488 / 6568 |
| 24 | Shadow Ninja | Rare | PASS 12/12 | 1.30 / 0.74 | 1.39 / 0.50 | 1.48 / 0.50 | 13096 / 5348 |
| 25 | Desert Cowboy | Rare | PASS 12/12 | 1.30 / 0.74 | 1.37 / 0.62 | 1.48 / 0.50 | 15072 / 6368 |
| 26 | Surgeon | Rare | PASS 12/12 | 1.25 / 0.74 | 1.36 / 0.52 | 1.44 / 0.51 | 13436 / 7728 |
| 27 | Speed Racer | Rare | PASS 12/12 | 1.25 / 0.71 | 1.40 / 0.67 | 1.46 / 0.50 | 11752 / 5824 |
| 28 | Deep Diver | Rare | PASS 12/12 | 1.25 / 0.73 | 1.36 / 0.71 | 1.46 / 0.50 | 13988 / 3760 |
| 29 | Noir Detective | Rare | PASS 12/12 | 1.50 / 0.50 | 1.45 / 0.51 | 1.49 / 0.50 | 13392 / 8060 |
| 30 | Skater Kid | Rare | PASS 12/12 | 1.27 / 0.74 | 1.38 / 0.53 | 1.49 / 0.50 | 12392 / 4120 |
| 31 | Jungle Explorer | Rare | PASS 12/12 | 1.28 / 0.68 | 1.48 / 0.53 | 1.48 / 0.50 | 13360 / 5632 |
| 32 | Rock Star | Rare | PASS 12/12 | 1.25 / 0.73 | 1.38 / 0.70 | 1.46 / 0.50 | 14712 / 6924 |
| 33 | Samurai Warlord | Epic | PASS 12/12 | 1.48 / 0.53 | 1.40 / 0.50 | 1.48 / 0.50 | 17692 / 7764 |
| 34 | Frost Viking | Epic | PASS 12/12 | 1.25 / 0.74 | 1.36 / 0.53 | 1.44 / 0.50 | 18658 / 8306 |
| 35 | Sun Pharaoh | Epic | PASS 12/12 | 1.48 / 0.60 | 1.48 / 0.50 | 1.50 / 0.51 | 15936 / 7104 |
| 36 | Ice Mage | Epic | PASS 12/12 | 1.49 / 0.61 | 1.48 / 0.57 | 1.50 / 0.50 | 13632 / 8832 |
| 37 | Mecha Pilot | Epic | PASS 12/12 | 1.27 / 0.71 | 1.50 / 0.54 | 1.49 / 0.50 | 15260 / 7976 |
| 38 | Royal Guard | Epic | PASS 12/12 | 1.25 / 0.74 | 1.39 / 0.54 | 1.45 / 0.50 | 13212 / 8112 |
| 39 | Court Jester | Epic | PASS 12/12 | 1.25 / 0.74 | 1.38 / 0.51 | 1.50 / 0.50 | 16172 / 5856 |
| 40 | Dragon Knight | Legendary | PASS 12/12 | 1.50 / 0.54 | 1.47 / 0.51 | 1.49 / 0.50 | 21204 / 8452 |
| 41 | Seraph | Legendary | PASS 12/12 | 1.50 / 0.50 | 1.48 / 0.51 | 1.50 / 0.50 | 21952 / 9312 |
| 42 | Neon Ronin | Legendary | PASS 12/12 | 1.31 / 0.67 | 1.49 / 0.53 | 1.47 / 0.50 | 14792 / 6932 |
| 43 | Phoenix Emperor | Legendary | PASS 12/12 | 1.50 / 0.58 | 1.46 / 0.51 | 1.50 / 0.50 | 21296 / 8552 |

What each one is:

- **14 Hoodie Hauler** (Common): Heather-grey zip hoodie, untucked and hanging over charcoal joggers (cuffed at the ankle). Hood down on the back, red zip line + red drawstrings with tips, kangaroo pocket. White chunky sneakers with red laces.
- **15 Denim Overalls** (Common): Blue denim overalls: trousers + bib panel on the chest + two shoulder straps with brass buttons, worn over a yellow/white horizontally striped tee (short sleeves). Contrast orange stitching lines. Tan work boots.
- **16 Gym Buddy** (Common): Lime tank top (no sleeves, deep armholes) hanging over black athletic shorts with a white side stripe. White wristbands, orange running shoes, skin-colour leg covers below the shorts.
- **17 Comfy Pajamas** (Common): Light-blue button-up pajama shirt with white polka dots and a white piped collar, hanging over matching polka-dot pajama trousers. Fuzzy pink slippers with a little pom-pom on each.
- **18 Parcel Courier** (Common): Moving-day courier: brown polo shirt tucked into brown shorts with a black belt, yellow box-logo patch on the chest and yellow collar trim. Skin-colour leg covers, white crew socks, black sneakers. A small clipboard clipped to the belt.
- **19 Green Thumb** (Common): Gardener: sage-green bib apron with a big front pocket (trowel handle sticking out) over a yellow tee, khaki shorts, green rubber garden boots. Leaf print on the apron pocket.
- **20 Splash Painter** (Common): House painter: white painter's overalls covered in colourful paint splatters (red, blue, yellow, green drips) over a blue tee, grey sneakers with paint dots. Paint brush in a chest pocket.
- **21 Lumberjack** (Common): Red/black buffalo-check flannel shirt with rolled sleeves (forearms bare), hanging over blue jeans held by red suspenders, tall brown leather lace-up boots.
- **22 Mail Carrier** (Common): Light-blue short-sleeve shirt with navy shoulder patches, tucked into navy shorts, crossbody leather mail satchel resting on the hip (strap over one shoulder, envelopes peeking out), white socks, black shoes.
- **23 Barista** (Common): Black long-sleeve tee with pushed-up sleeves, tan canvas bib apron with leather neck strap and a coffee-bean logo on the pocket, dark jeans, white sneakers. Pen and small towel tucked in the apron.
- **24 Shadow Ninja** (Rare): Black ninja gi with wrap-front collar (visible overlap line), red sash belt with a knot and two hanging tails, loose dark trousers bound with criss-cross wraps on the shins, split-toe tabi boots. Red neck scarf with two long tails flowing behind, short sword (wakizashi) across the lower back, two shuriken on the belt.
- **25 Desert Cowboy** (Rare): Red bandana tied at the neck, brown suede vest with fringe over a cream shirt, jeans with a big oval gold belt buckle, brown leather chaps over the jeans fronts, cowboy boots with spurs, coiled lasso on the belt.
- **26 Surgeon** (Rare): Teal scrubs (V-neck top + trousers) under a long white lab coat that hangs open at the front over the trousers to the knee (lapels, chest pocket with pens, two hip pockets, back vent). Stethoscope around the neck, ID badge, white clogs.
- **27 Speed Racer** (Rare): One-piece red racing suit with two white racing stripes down the front and legs, sponsor patches (painted), padded collar, black gloves with white knuckle pads, black racing boots, checkered-flag trim on the cuffs and belt.
- **28 Deep Diver** (Rare): Navy full wetsuit with yellow panels down the sides and on the shoulders, weight belt with lead blocks, twin yellow air tanks with a valve on the back, dive mask hanging on the chest from its strap, regulator hose, long yellow fins on the feet.
- **29 Noir Detective** (Rare): Long double-breasted tan trench coat hanging to the knee over grey trousers (belted, buckle, epaulettes, popped collar, buttons), dark-red plaid scarf, polished brown shoes, magnifying glass in the belt.
- **30 Skater Kid** (Rare): Oversized white graphic tee (big teal/red flame logo) hanging over baggy grey cargo pants with side pockets, chunky red high-top skate shoes, chain wallet hanging from the belt loop, skateboard strapped on the back.
- **31 Jungle Explorer** (Rare): Khaki safari shirt with two flap chest pockets and epaulettes hanging over khaki shorts, big canvas backpack with a rolled bedroll on top, binoculars on a strap across the chest, knee-high socks and hiking boots.
- **32 Rock Star** (Rare): Black leather biker jacket (open, silver zips, studded shoulders) over a white tee with a pink lightning bolt, ripped black skinny jeans (painted rips), studded belt, black boots with buckles, pink electric guitar slung on the back.
- **33 Samurai Warlord** (Epic): Lacquered red armour: chest plate made of horizontal lames laced with gold cord, gold crest emblem on the chest, big flat shoulder plates (sode) on the upper arms, armoured throat guard collar, layered hanging tassets (kusazuri) over wide indigo hakama trousers, armoured shin guards, katana at the hip.
- **34 Frost Viking** (Epic): Mail tunic hanging over brown wool trousers with criss-cross leg wraps, thick white fur mantle around the shoulders, leather belt with a knotwork gold buckle, fur boots, round painted shield on the back, hand axe in the belt.
- **35 Sun Pharaoh** (Epic): White pleated linen kilt (shendyt) with a gold belt and a jewelled front panel, sheer white top, huge jewelled usekh collar (concentric gold / turquoise / lapis bands) over the shoulders, gold arm cuffs, gold sandals.
- **36 Ice Mage** (Epic): Floor-length ice-blue A-line robe with white fur trim at the hem and cuffs, snowflake pattern, frosted silver sash, wide bell sleeves, jagged ice-crystal spikes on both shoulders, white boots. Robe must use slit panels like the Wizard.
- **37 Mecha Pilot** (Epic): Bulky white armoured pilot suit with orange panels and glowing cyan lines, chest plate with a glowing round core, chunky shoulder and knee plates, armoured boots, compact jetpack with two thruster nozzles on the back.
- **38 Royal Guard** (Epic): Scarlet tunic hanging over black trousers with a red side stripe, two rows of gold buttons, white cross-belts with a brass plate, gold collar and cuff braid, gold epaulettes, white gloves, polished black boots.
- **39 Court Jester** (Epic): Harlequin diamond-pattern tunic (purple / gold) with a zig-zag pointed hem with a bell on each point, hanging over two-tone leggings (left leg purple, right leg gold), big white ruffled collar, curly toe shoes with bells.
- **40 Dragon Knight** (Legendary): Obsidian scale armour (scale pattern) with blood-red accents, dragon-head spiked pauldrons, red tabard panels hanging front and back over armoured legs, clawed gauntlets, big folded bat-like dragon wings on the back, spiked dragon tail.
- **41 Seraph** (Legendary): Radiant white A-line robe with gold trim and gold sash (slit panels like the Wizard), gold shoulder guards, gold arm bands, huge layered feathered angel wings spread behind, gold sandals.
- **42 Neon Ronin** (Legendary): Matte-black techwear samurai: angular armour plates with glowing neon cyan + magenta light strips, high neon-lined collar, layered tassets over hakama-cut trousers, energy katana with a glowing blade on the back.
- **43 Phoenix Emperor** (Legendary): Crimson imperial robe with gold flame pattern rising from the hem (A-line, slit panels), gold phoenix collar, gold bracers, a fan of fiery phoenix feathers / flame wings behind the shoulders (orange to yellow).

## Shape fix: smooth connections (geometry change)

- **Trousers (01-08, 11, 13):** the hip piece used to be a bulging dome that ended below the crotch with a flat cap, and
  the legs came out of it with a ledge and jagged rim flaps. Now the hip piece ends on the crotch line and each leg grows
  out of its bottom edge (same outline at the joint, rounding into the leg over 0.36 units): one smooth shape from waist
  to ankle. A small cap inside keeps the crotch covered when the legs spread.
- **Loose tops hang over the trousers (02 shirt, 03 coat, 04 jacket, 05 vest, 06 jacket, 07 jacket, 08 coat, 09 robe, 11 suit top, 13 onesie top):**
  they used to follow the body's round bottom, so hems tucked in under the belly, and below the crotch the rings
  collapsed into V-notches at front and back (the wizard pinch, the raincoat spike). Now they fall straight from the chest,
  flare by the same amount as before, and stay outside the trousers / belt with clearance.
- **09 Wizard:** robe is a clean A-line (no waist pinch, no notches), the sash sits on the robe instead of floating 0.1
  off the body. Slit panels kept; their thigh-follow ramps are longer (slit_blend / slit_blend_side 0.85 -> 1.1) because the
  robe now hangs further from the hips.
- **11 Astronaut:** belt refitted onto the suit top.
- **05 Construction Hero:** vest hangs straight over the trousers; tool belt slung straight under the vest hem.
- **10 Knight:** mail skirt and the three fauld lames hang (no notches / jagged rim at the crotch) and are layered:
  mail over the leg armour, each lame over the cuirass / the lame above, a clean stepped skirt. New hidden mail seat
  under the skirt closes the crotch (the grey body showed there in a wide leg spread).
- **13 Dinosaur:** onesie top hangs over the onesie legs instead of tucking under the belly (no crease at the waist).
- Weight rules unchanged. Trouser-leg weights are sampled toward the leg axis (see CLAUDE.md "Garment shape rules"), and
  the weight-repair pass may now reach loose coats out to |x| 0.85 at the hips. Not reshaped: 12 Ghost (one sheet, no joints).

- **Crotch panel (all trousers):** a thin centre panel in the trouser colour now fills the narrow slot between the two legs'
  inner faces, so no grey body line shows between the legs from the front or back.
- **10 Knight shoulder lames:** the lower pauldron lames no longer stretch across the chest and upper back (`dome(..., keep_out)`).
- **Skin tone:** skin-coloured leg covers use `o02.SKIN` #ed7c42, the arm tone as Roblox shows the body (it reads the colour
  factor as sRGB).

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
