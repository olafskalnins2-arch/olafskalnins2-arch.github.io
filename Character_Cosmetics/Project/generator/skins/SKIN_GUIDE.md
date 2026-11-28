# Building a Floppy Movers skin (read all of it before writing code)

You build ONE outfit as Python code that the existing generator turns into a rigged, textured Roblox GLB/FBX.
The repo rules in `/home/user/olafskalnins2-arch.github.io/CLAUDE.md` (Rigging rules + Garment shape rules) apply. Read it.

## Files

- Your module: `Character_Cosmetics/Project/generator/skins/sNN_Name.py` (exactly the number + name you were given).
- **Write ONLY your own module.** Never edit `garments.py`, `lib.py`, `pipeline.py`, `rigfix.py`, `build_all.py`, `o0*.py`,
  `review.py`, other skins, or anything else. 30 agents work in parallel: an edit to a shared file breaks everyone. If you
  need a helper, define it inside your module. If you think a shared function has a bug, say so in your report.
- **No git** (no commit, no push, no checkout, no stash). The lead integrates everything.
- Study first: `o01.py`..`o04.py` (the 13 original outfits, already fixed with the rules below), `garments.py` (`torso_shell`,
  `drape`, `pants`, `trouser_leg`, `sleeve`, `leg_tube`, `shoe`, `band`, `collar`, `head_shell`), `lib.py` (primitives),
  `paints.py` (texture helpers). Good references: o03.wizard (robe + slits + sash on robe), o03.pirate (open coat over
  trousers + belt), o02.raincoat (coat over pants, hood), o04.knight (layered hanging plates), o04.dino (hood, tail, spikes),
  o04.astronaut (backpack, chest panel, belt fitted on the suit).

## Module template

```python
from o04 import *          # pulls in everything: garments, pipeline, paints, o02 (skin_leg, SKIN), o03, o04 helpers
NUM, NAME, RARITY, MAXD = '14', 'Hoodie_Hauler', 'Common', 0.32    # MAXD 0.7 for long coats/robes
def build():
    pal = {'grey': '#9aa0a6', ...}           # named colours; a piece with col='grey' gets that flat colour
    P = []
    pt = pants('Joggers', 2.2, 0.5, 0.045, hip_off=0.06, leg_extra=lambda z, a: 0.02)   # build the LOWER layers first
    for p in pt: p.paint = P_solid(pal['char'])
    top = torso_shell('Hoodie', 1.95, 0.06, nseg=32, extra=lambda z, a: 0.015, th=0.025, hang=2.3, over=pt)
    ...
    return P, pal
```

## Coordinates (Blender space, Z up, units = body units)

- Front of the character is **-Y**, back +Y, character's left is **+X**. Feet bottom z~0.33, crotch z 1.93, waist ~2.2-2.3,
  chest 2.3-2.9 (front/back radius 0.41, side radius 0.5), neck/collar ~3.2, head centre `HEAD_C`=(0,-0.012,4.029) radius
  `HEAD_R`=0.786 (huge round head; the EYES are on the front of the head around z 3.9-4.35 - never cover them).
- Legs: cylinders r 0.17 around x=+-0.25 below z 1.9 (`leg_point(side, z)`). Arms hang down the sides
  (`arm_point(side, t)`, t 0 = shoulder .. 1 = wrist). Feet/shoes around z 0.33-0.6.
- Torso below z 2.2 is the ROUND bottom of a capsule (it curves in to the crotch). This is why loose tops must hang.

## NO HEADWEAR

Hats are sold separately, so skins have **nothing on or around the head**: no hats, caps, helmets, crowns, halos,
headbands, masks, hoods worn up, nemes, headsets, horns. Nothing above the collar (z > ~3.35) except a collar itself
and wings / back props that rise behind the shoulders. Never use group 'Head' or bone 'Head'. A hood lying DOWN on the
back (o02.raincoat) is fine.

## Pieces and how they are rigged (pipeline.rig_weights)

- `group` = which exported mesh: 'Top', 'Bottom', 'Feet', 'Head', 'Extras'. **Each group must stay <= 10,000 triangles**
  (build_one.sh prints the counts). Keep nseg/nrows reasonable.
- Torso garments (`torso_shell`, `band`, `collar`, `surface_patch` on the torso): weights from the torso, side-masked.
- `sleeve(...)` -> region 'arm_L/R'. `leg_tube` / `trouser_leg` -> 'leg_L/R'. `shoe` -> 'foot_L/R'. `_shin(leg_tube(...))`
  (define `_shin` like o03 does: `pc.region = 'shin_' + pc.region[-1]`) for stiff boot shafts / greaves.
- Rigid parts (buttons, buckles, tools, tanks, backpacks, guitars, swords, wings, shields, spikes): set `pc.rigid = True`
  AND `pc.bone = 'UpperTorso' | 'LowerTorso'` (one bone, 100%). Back items -> 'UpperTorso'. Belt-hung items -> 'LowerTorso'.
  Anything near the head (high collars, shoulder spikes, wings): `head_clear(pc, 0.03)` so it never sinks into the head.
  Wings / capes / tails must stay clear of the arms and legs at rest (arms hang at x ~ +-0.6..0.75).
- A piece needs EITHER `col='palette_key'` (flat colour) OR `pc.paint = fn(U, V, m) -> image` (see paints.py, `P_solid`,
  `mix`, `aa`, `zc`, `scatter`, `star`, `checker`, `vstripes`, `reflective`). Pieces sharing `rect_key` share one texture
  region - give pieces with different paint different names / rect_keys.
- Thin skin-coloured leg covers for bare legs: `skin_leg(side, z0, z1)` (from o02) - bare body legs are GREY, so any
  outfit that shows legs (shorts, kilts, short skirts) needs them. Bare arms are already skin coloured. `SKIN` (o02, #ed7c42) is the
  skin tone as Roblox shows the body (it reads the colour factor as sRGB) - use it, do not override it.

## The shape rules (these were real mistakes - do NOT repeat them)

1. **Trousers: always `pants(prefix, z_waist, z_end, off, hip_off=..., leg_extra=...)`.** Never build your own hip dome +
   separate leg tubes: that made a bulging "diaper" with a ledge and jagged flaps at the hip-to-leg joint. `pants()` gives
   one smooth silhouette and covers the crotch. Shorts: same call with z_end ~1.3-1.45 (+ `skin_leg` below).
2. **Any loose top whose hem is free (untucked shirt, hoodie, jacket, coat, tunic, robe, apron body, tabard shell, vest)
   must hang:** `torso_shell(..., hang=2.3, over=<everything under it: pants pieces, belts, undershirt>)`. Without `hang`
   the shell follows the body's round bottom: hems tuck in under the belly and V-notches appear at the crotch front/back
   (that was the wizard "weird curves" and the raincoat spike). Build the under-layers FIRST so you can pass them in `over`.
   A tucked shirt (under a belt / inside the trousers) does not hang: end it at z>=2.1 and let the pants hip cover it.
3. **Belts, sashes, bands that sit on a loose piece are fitted ON that piece:** `band(name, z0, z1, 0.012,
   bvh=piece_bvh(coat), th=0.02)` (add `hang=z1+0.1` if it should be a straight ring). Never fit them to the body with a
   big offset (it floats / sinks through the coat).
4. **Long robes / dresses / coats below the knee over both legs**: `slits=RF_SLIT_TOP()` like the wizard robe (panels that
   open when the legs move), `MAXD=0.7`. Open-front long coats (pirate) don't need slits.
5. **Layered hanging plates / skirts (tassets, faulds, kilts, tabard flaps):** `torso_shell(..., zs=[z0, z1], elevs=(),
   hang=z1 + 0.001, over=<layer below + leg pieces>, over_gap=0.026)` so they never notch at the crotch and stack cleanly.
   If nothing covers the crotch under a skirt, add a hidden seat like o04.knight's `MailHip` (or just use `pants`).
6. **Clearance**: every layer sits OUTSIDE the layer under it (`over=` does it for torso shells; for leg tubes use a bigger
   offset than the trousers, e.g. boots shafts / greaves off >= trouser off + 0.03). Nothing may poke through at rest.
7. **No floating bits**: patches/pockets/buttons are projected onto their garment with `piece_bvh(garment)` + `project` /
   `surface_patch` (see o01 pocket/buttons). Rigid props touch what they hang from.
8. Do NOT change `rigfix.DEFAULT_RAMPS` or any global.

## Rarity = how cool / detailed

- Common: everyday outfit, 4-8 pieces, clean colours, 1-2 small details (pocket, logo patch, laces).
- Rare: themed costume, 8-16 pieces, props and patterns.
- Epic: elaborate, 15-30 pieces, layered armour/fabric, strong patterns, a signature accessory.
- Legendary: spectacular silhouette (wings / tails / glowing lines / big collars), richest texture work, 25+ pieces.
  Still: every rule above, rig check pass, <= 10k tris per mesh group.

## Build / check / look loop (always through the scripts - they queue on 4 shared CPU slots)

    W=/tmp/claude-0/-home-user/9bb9dc67-9944-5637-bd0d-2d9c3a8d60c6/scratchpad/skinwork
    $W/build_one.sh NN          # builds ONLY your skin, prints coverage, rig table, tris per mesh, review sheet path

- Never run Blender/bpy (`python3` importing bpy, build_all.py, check_rig.py, review.py) directly - only via
  `$W/build_one.sh` or `$W/slot.sh <cmd>` (the box has 4 cores / 15 GB for 30 agents).
- Done means ALL of:
  1. `12/12 checks passed` for your GLB + FBX (stretch 0.5x..1.5x in walk/spread/arms up/arms down/crouch, weight rules).
     If an edge fails, fix the SHAPE first (less flare near hips, more clearance, slits for long skirts, rigid bone for
     props); see how o03/o04 handled it.
  2. Every mesh group <= 10,000 tris.
  3. You LOOKED at `$W/out/NN/review.png` (Read the image) and it is clean: front/side/back/3-4, hip close-ups, from below,
     walk, spread, crouch. Check: no ledge or gap at hip/leg, crotch covered in "spread low back", hems hang outside the
     trousers, no tucking/notches, nothing pokes through, eyes visible, props attached, colours match the brief.
     A PASS table with an ugly render is a FAIL. Iterate until it looks good (2-6 iterations is normal).

## Report (your final message)

`NN Name | Rarity | rig X/12 | tris per group | pieces | one-line description of what you built | any problems/limits`.
