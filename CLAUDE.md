# CLAUDE.md

Repo: GitHub Pages site + the Floppy Movers character cosmetics in `Character_Cosmetics/`.

- Base character (fixed weights): `Character_Cosmetics/Base_Character/character_smooth_v2.glb`
- Outfits: `Character_Cosmetics/Roblox_Ready/NN_Name/` (GLB + FBX + texture), all-in-one rig: `Roblox_Ready/00_Import_Helper/CosmeticsRig.glb`
- Blender project: `Character_Cosmetics/Project/Character_Cosmetics.blend`
- Generator scripts (rebuild everything, weight rules live in `rigfix.py`): `Character_Cosmetics/Project/generator/`
- Originals before the rig fix: `Character_Cosmetics/_backup/` (never overwrite; `MANIFEST.sha1` inside)

## Rigging rules

Every skinned mesh (body, clothing, accessories) on the 15-bone rig (LowerTorso, UpperTorso, Head,
Left/Right UpperArm, LowerArm, Hand, UpperLeg, LowerLeg, Foot) must follow these rules:

1. **No left/right mixing.** Left-side verts (x > 0 is the character's left) get ZERO weight on Right* bones and the
   reverse. Centre-line verts (|x| <= 0.02) get torso bones only. A separate limb piece (a trouser leg, a boot, a sleeve)
   belongs to its side as a whole, even where a bulky piece overlaps the centre line.
   Same for arms vs torso / other arm: arm verts get only their own arm's bones, torso verts get no arm bones
   (the shoulder is a hard seam; the torso's shoulder sockets are capped so nothing opens when an arm moves).
2. **Clean weights.** Max 4 influences per vertex, every weight >= 0.01 (smaller ones removed), weights normalized to 1.
3. **Clothing weights are transferred from the body mesh** (nearest face, interpolated), never auto weights, and only
   from the matching body region (sleeve <- that arm, trouser leg <- that leg, shoe <- that foot/shin, shirt <- torso).
   Then re-run the left/right cleanup. Coat / robe / sheet hems below the crotch stay mostly on LowerTorso with only a
   capped same-side leg follow (no webbing between the legs). Stiff boot shafts / cuffs / greaves use LowerLeg + Foot only.
4. **Rigid parts get 100% weight on ONE bone, no blending:** buttons, buckles, clasps, eyes, spikes, claws, studs,
   tools, backpacks, panels, pauldrons, tails, hoods that hang on the back.
5. **Smooth weights only across joints:** waist, hips, knees, elbows (plus short ankle / wrist ramps). Don't blur
   anything else. Thin clothing layers must match the body's weights exactly (no extra smoothing), or the body pokes through.
6. **Thick (double-sided) clothing:** inner-shell verts copy the weights of their outer twin, and verts joined by
   near-zero-length edges (< 0.012) or sitting at the same position get identical weights, so rims, stitched seams and
   degenerate edges never tear.

**`Character_Cosmetics/Roblox_Ready/check_rig.py` MUST pass before any new or changed model is called done.**
Run it on the exported files (not just the .blend):

    pip install bpy        # once (Blender as a Python module)
    python3 Character_Cosmetics/Roblox_Ready/check_rig.py Character_Cosmetics/Roblox_Ready Character_Cosmetics/Base_Character Character_Cosmetics/Project

It poses every model (walk, legs spread wide, arms up, arms down, crouch) and FAILS any triangulated edge stretching
> 1.5x or squashing < 0.5x, any vertex on both left and right limbs or on the wrong side, > 4 influences, weights < 0.01
or not normalized. It prints model | pose | worst stretch | worst squash | bad verts | PASS/FAIL and exits 1 on any FAIL.
Then render the model in walk + spread poses (front / side / back) and look at the crotch, armpits and waist yourself:
a PASS table with a broken-looking render is a FAIL.
