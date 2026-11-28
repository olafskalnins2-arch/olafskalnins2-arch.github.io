CHARACTER COSMETICS - 13 wearable outfits for your default character
=====================================================================

RIG FIX (weights) - READ THIS FIRST
-----------------------------------
All models were re-weighted so cloth no longer stretches like webbing between the legs, under the arms or at the
waist. Proof: Rig_Check/ (before/after renders + check tables, 7/174 checks passed before, 174/174 after).
- Base_Character/character_smooth_v2.glb  = YOUR base character with fixed weights (same name as your original).
  Your original weights were part of the problem, so re-import this one in Roblox Studio, or the outfits and the
  body will deform differently. Vertex positions are unchanged. The only mesh change: the 2 open shoulder sockets
  (and the 2 open arm ends) are capped with faces, so no hole opens when an arm moves.
- Every outfit GLB/FBX, CosmeticsRig.glb and the .blend were re-exported under the same names. Geometry, UVs,
  textures and materials are identical to before; only the skin weights changed. Exception (approved by you): the
  Wizard robe is cut into panels and its hidden leg covers are longer - see CHECKLIST.md.
- Originals are in _backup/ (MANIFEST.sha1 lists their checksums).
- Roblox_Ready/check_rig.py checks any model (see CLAUDE.md "Rigging rules" in the repo root). Run it before calling
  any new model done:  python3 Roblox_Ready/check_rig.py Roblox_Ready Base_Character Project

WHAT'S IN HERE
--------------
Project/
  Character_Cosmetics.blend    Blender project. Your untouched character + all 43 outfits, one collection
                               each, all parented to the SAME armature ("Character"). Textures are linked
                               from ../Textures (relative paths), so keep the folder structure.
  build_report.json            Per-outfit stats: pieces, meshes, triangles, coverage/poke-through tests.
  export_verification.json     Re-import check of every exported GLB/FBX (bones, joint positions, skin, UVs, textures).
  generator/                   The Blender-Python scripts that built everything. Re-run with:
                                 pip install bpy   (Blender 5.x as a Python module)
                                 CHARACTER_GLB=/path/character_smooth_v2.glb python3 generator/build_all.py /out/Character_Cosmetics
Roblox_Ready/
  00_Import_Helper/CosmeticsRig.glb   Your body + all 43 outfits on one shared skeleton. Use this as the Roblox
                                      template so every outfit is aligned to your rig. (Your body in here is a
                                      plain re-export, same geometry and weights. It's only a fitting
                                      reference for the script, not part of any cosmetic.)
  01_Classic_Mover/ ... 43_Phoenix_Emperor/  Each outfit on its own (14-43 are the 30 rarity skins):
      NN_Name.glb          skinned cosmetic (no body inside), texture embedded  <- recommended format
      NN_Name.fbx          same thing as FBX, texture embedded
      NN_Name_Albedo.png   the outfit's single 1024x1024 texture atlas
  Scripts/
      CosmeticService.lua        ModuleScript: Equip / Unequip / IsValid / CanUse
      CosmeticServer.server.lua  Script: secure RemoteEvent ("EquipCosmetic") + re-equip on respawn
Textures/      all 43 albedo atlases
Preview/       NN_Name.png = front, 3/4, back, walk pose, carry pose.  All_Outfits.png = overview.
CHECKLIST.md   completion + export status for every outfit, test results, known limitations.

HOW THE OUTFITS ARE BUILT
-------------------------
- Each outfit is real 3D geometry (shells with thickness, collars, pockets, buttons, belts, armor plates,
  boots, tails, spikes...) fitted by ray casting onto YOUR body mesh, then offset outward. Your character
  was never scaled, moved or edited.
- Skins 14-43 come in four rarities (Common, Rare, Epic, Legendary - see CHECKLIST.md and
  CosmeticService.RARITY). Each is one module in Project/generator/skins/; none has headwear (hats are separate).
- Loose tops (untucked shirts, jackets, coats, the robe, the space suit top) hang straight down from the chest and sit
  outside the trousers instead of tucking in under the belly. Trousers are one smooth shape from waist to ankle: the
  legs grow out of the hip piece's bottom edge, so there's no ledge or seam bulge at the crotch.
- Every outfit mesh is SKINNED to your exact 15 bones (LowerTorso, UpperTorso, Head, Left/Right
  UpperArm, LowerArm, Hand, UpperLeg, LowerLeg, Foot). Weights follow the "Rigging rules" in CLAUDE.md:
  transferred from the (fixed) body per region, no left/right mixing, max 4 influences, rigid parts on one bone.
- One material + one 1024px texture per outfit (Roblox MeshParts take one texture each).
- Each outfit is split into up to 5 meshes: _Top, _Bottom, _Feet, _Head, _Extras. That way no single
  MeshPart gets close to Roblox's triangle limit (the biggest is about 8.3k tris), and you can mix pieces.
- Units/orientation are identical to your GLB (Y-up, same scale). Import with the SAME settings you
  used for your character.

WHY NOT CLASSIC ACCESSORIES / LAYERED CLOTHING?
-----------------------------------------------
- Rigid Accessories (Handle + Attachment) can't bend at elbows and knees, so sleeves and trousers
  would crack apart at every joint. They're the wrong tool for full outfits on a skinned body.
- Layered Clothing (WrapLayer) needs inner and outer cage meshes built from Roblox's cage templates,
  plus a WrapTarget cage on your body. Your character is a custom single skinned mesh without those
  cages, and I couldn't author Roblox-template cages here.
- So the right fit for your rig is SKINNED MeshParts that share your bone names. They deform with
  your character's own bones, need no replacement character, and can be added or removed at runtime.

IMPORT + EQUIP IN ROBLOX STUDIO (recommended path)
--------------------------------------------------
1. Avatar tab / File > Import 3D > pick Roblox_Ready/00_Import_Helper/CosmeticsRig.glb.
   Use the same import settings as your character (same scale, rig import ON).
   You get a Model with a "Body" MeshPart, the bones, and MeshParts named like
   "08_Pirate_Top", "08_Pirate_Bottom", ...
2. Rename the model to CosmeticsRig and put it at ServerStorage > Cosmetics > CosmeticsRig
   (create the "Cosmetics" Folder).
3. Put Scripts/CosmeticService.lua (ModuleScript, name "CosmeticService") and
   Scripts/CosmeticServer.server.lua (Script) into ServerScriptService.
4. If your character's body MeshPart isn't called "Body", set CosmeticService.BODY_NAME.
5. Equip from the client (e.g. a shop button LocalScript):
       game.ReplicatedStorage:WaitForChild("EquipCosmetic"):FireServer("08_Pirate")
       game.ReplicatedStorage.EquipCosmetic:FireServer("")      -- unequip
   Or from server code:  CosmeticService.Equip(character, "13_Dinosaur") / CosmeticService.Unequip(character)
   The server checks type, length, whitelist and a cooldown, and has a CanUse() hook for
   ownership/gamepasses. The chosen outfit is stored on the player and re-applied on respawn.

What Equip does: clones that outfit's MeshParts from the template, deletes any Bones/joints inside
the clones, places them at the same offset from your live Body as in the template, welds them to
Body (massless, no collision/touch/query), and parents them next to Body in your character. They then
deform with your character's existing bones by name. Unequip just destroys them. The character
itself is never replaced.

FIRST TEST (do this once, it takes 2 minutes)
---------------------------------------------
I could NOT run Roblox Studio from where this was built. Everything is verified in Blender, but not in
Studio. So test once:
 a) Play Solo, equip "01_Classic_Mover", walk and jump. Sleeves and trousers should bend with the
    elbows and knees.
 b) If the outfit shows up but stays frozen in a T/rest pose while the body animates, the clone
    isn't finding your bones. Fix: parent the clones under the same instance that holds your
    character's Bone hierarchy (usually the root/Body part) instead of next to Body. That's the
    `part.Parent = container` line in CosmeticService.Equip.
 c) If an outfit appears offset, your character was imported with different settings than
    CosmeticsRig. Re-import CosmeticsRig with the exact same settings.

USING THE INDIVIDUAL OUTFIT FILES INSTEAD
-----------------------------------------
Every NN_Name.glb / .fbx works on its own: an armature identical to yours plus the skinned outfit
meshes, no body inside. Import one with the same settings as your character, then move its
MeshParts into your character the same way the script does (delete their Bones, weld to the body,
parent inside the character). The GLB is the safest choice because its joints are byte-for-byte your
original layout (pure translations, no rotations). The FBX is there for Blender/Maya/other tools.
Blender's FBX exporter can re-orient bone axes, so stick with the GLB for Roblox.

SWAPPING PIECES / EDITING
-------------------------
Open Project/Character_Cosmetics.blend. Each outfit is a collection (01_Classic_Mover, ...). Only
outfit 01 is visible by default; toggle the others in the outliner. Every mesh has an Armature
modifier pointing at "Character", so you can pose the rig to check deformation.

NOTES
-----
- Chill Dude, Wizard and Pirate include skin-colour leg covers or a painted V-neck because the
  references show orange skin where your actual body is grey. The leg covers are merged into each outfit's
  _Bottom mesh. Delete those faces in Blender (select linked, leg area) if you'd rather show the grey base layer.
- Ghost: hands poke through the sheet in big arm swings (see CHECKLIST.md). It's fully covered in idle.
- Wizard: the robe skirt is cut into panels (invisible standing still) so it opens like a slit robe when walking; legs
  never go through the cloth. Leg covers under it are skin-coloured up to the hips.
