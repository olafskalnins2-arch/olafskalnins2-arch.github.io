# Moving Day Props

37 low-poly furniture props for a Roblox moving game, plus the scripts that make them carryable physics objects.

```
MovingDayProps/
├─ models/                         37 .glb files, one per prop (file name = model name)
├─ src/
│  ├─ ServerScriptService/
│  │  ├─ MovableFurniture.server.luau   carrying, physics, doors/lids/drawers, tip-over
│  │  ├─ FurnitureSetup.server.luau     auto-tags imported props + sets their attributes
│  │  └─ FurnitureConfig.luau           ModuleScript: weight & settings per prop
│  └─ StarterPlayerScripts/
│     └─ DropControls.client.luau       Q / gamepad B / mobile button to drop
├─ default.project.json            Rojo project (optional)
└─ README.md
```

## 1. Put the scripts in your place

**Without Rojo (easiest):**

| File | Create in Studio as | Where |
|---|---|---|
| `MovableFurniture.server.luau` | **Script** named `MovableFurniture` | ServerScriptService |
| `FurnitureSetup.server.luau` | **Script** named `FurnitureSetup` | ServerScriptService |
| `FurnitureConfig.luau` | **ModuleScript** named `FurnitureConfig` | ServerScriptService (same parent as FurnitureSetup) |
| `DropControls.client.luau` | **LocalScript** named `DropControls` | StarterPlayer → StarterPlayerScripts |

Paste each file's contents into the matching script.

**With Rojo:** `rojo serve` in this folder and connect from the Rojo plugin. Scripts land in a `MovingDayProps` folder in ServerScriptService and StarterPlayerScripts.

## 2. Import the models

1. Studio → **Avatar** (or Home) tab → **Import 3D**.
2. Select all the files in `models/` (bulk import works).
3. Import settings: file units **Studs**, keep the hierarchy, **do not merge meshes**.
4. Put the imported models anywhere in **Workspace** (a `Furniture` folder is fine).

Keep the model and part names the importer gives them. The scripts rely on them:
- `Col_…` parts are the hitboxes (they turn invisible on Play).
- Child models with `Door`, `Lid`, `Flap` or `Drawer` in the name are the parts that open.
- `HingeL` / `HingeR` in a door's name picks which edge it hinges on.

That's it. On Play, `FurnitureSetup` recognises each prop by name, copies its weight from `FurnitureConfig`, and tags it `Movable`. To use a prop under another name, add it to `FurnitureConfig` or tag it `Movable` by hand.

## 3. What players can do

| Action | Input |
|---|---|
| Pick up | **E** (hold) on the prop |
| Drop | **Q** · gamepad **B** · on-screen button on mobile |
| Open / close a door, lid, drawer, oven door | **F** · gamepad **Y** |

## 4. Physics

- **One cheap collider per prop.** Solid props use a single invisible box. Hollow props (cabinets, chest, dresser, bookshelf…) use their `Col_` boxes as real walls, so things fit inside and sit on shelves.
- **Weight.** Each prop gets a density from its `Weight`. Heavier props slow the carrier down (walk speed 16 down to a minimum of 7).
- **Carrying.** The prop floats in front of the player (AlignPosition / AlignOrientation), still hits walls and doorframes, and never collides with characters. The carrier gets network ownership so it moves smoothly.
- **Contents ride along.** On pickup, everything lying inside or on top of the prop gets welded on for the trip, then released on drop.
- **Doors stay shut while carried.** Every door, lid and drawer snaps shut and locks on pickup.
- **Tip-over spill.** If a prop with opening parts leans more than **55°** (knocked over, dropped badly, falls off the truck), every door, lid and drawer unlocks and swings or slides **freely under gravity**. Pressing F on one gives it its motor back. Turn this off per prop with the attribute `NoSpill = true`.

## 5. Attributes (on the prop model)

| Attribute | Default | Meaning |
|---|---|---|
| `Weight` | 60 | How heavy it feels. Set by FurnitureConfig. |
| `HoldDistance` | 1.5 | Gap between the player and the prop while carrying. |
| `DoorAngle` | 110 (doors) · 95 (lids) · 85 (flaps) | How far things open, in degrees. |
| `FlipDoors` | false | Set true if doors/lids swing the wrong way. |
| `DrawerSlide` | 75% of drawer depth | How far drawers slide out, in studs. |
| `NoSpill` | false | Stops doors flying open when the prop tips over. |

Attributes you set by hand in Studio always win over FurnitureConfig.

## 6. The props

| Model | Tris | Opens | Weight |
|---|---|---|---|
| WasherW01 | 2,124 | – | 120 |
| CabinetC01 | 616 | 2 doors, hollow | 50 |
| PianoP01 | 356 | key cover (lid) | 150 |
| SofaS01 | 992 | – | 80 |
| ClockG01 | 482 | glass trunk door | 70 |
| RadioR01 | 508 | – | 8 |
| ChairC01 | 432 | – | 12 |
| GlobeE01 | 860 | – | 10 |
| AmpA01 | 666 | – | 20 |
| MonitorM01 | 620 | – | 25 |
| TypewriterT01 | 798 | – | 15 |
| KegK01 | 1,152 | – | 50 |
| SuitcaseS02 | 900 | – (locked) | 15 |
| BedB01 | 480 | – | 120 |
| KitchenCabinetK02 | 668 | 2 doors, hollow | 40 |
| SideboardS03 | 316 | 4 doors, hollow | 60 |
| CoffeeTableT02 | 420 | – | 25 |
| ToiletW01 | 820 | – | 35 |
| RadiatorR02 | 318 | – | 60 |
| BookStackB02 | 396 | – | 6 |
| PictureFrameF01 | 154 | – | 3 |
| MovingBoxX01 | 166 | – (locked) | 8 |
| IroningBoardI01 | 496 | – | 10 |
| StepLadderL01 | 252 | – | 12 |
| VacuumV01 | 600 | – | 10 |
| MicrowaveM02 | 896 | – (locked) | 15 |
| NightstandN01 | 680 | drawer + cupboard | 20 |
| ToolboxT03 | 860 | lid, hollow | 12 |
| SewingMachineS04 | 868 | – | 18 |
| MirrorStandM03 | 866 | – | 15 |
| RockingChairC03 | 808 | – | 15 |
| ChestC04 | 612 | lid, hollow | 35 |
| SingleBedB03 | 544 | – | 70 |
| TVStandT04 | 864 | 2 cupboards | 40 |
| BookshelfS05 | 252 | – (shelves hold stuff) | 45 |
| DresserD01 | 1,320 | 4 drawers | 55 |
| StoveO01 | 1,378 | oven door + drawer | 60 |

## 7. Studio tips

- Wood parts → Material **Wood**; fabric → **Fabric**; chrome/steel → **Metal**; glass panes → **Glass**, Transparency ≈ 0.7; glowing bits (radio dial, LEDs, amp lamp) → **Neon**.
- The globe and the picture frame each carry one tiny texture inside the GLB. If either imports plain white, re-import with textures enabled.

## 8. Not tested in Studio yet

These were built and checked in a 3D preview, not in Roblox. Most likely to need a tweak:
- **Hinge or slide direction.** If a door swings inward or a drawer slides into the furniture, set `FlipDoors = true` on that model and report the drawer one.
- **Importer naming.** If the importer renames the `Col_` parts or the `Door/Lid/Flap/Drawer` models, the hitboxes and opening parts won't be found.
