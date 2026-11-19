# Winter Props (Roblox)

19 stylized snowy props, all under 5,000 tris (see `tri_counts.txt`). Preview: `preview.png`.

## Files
- `glb/*.glb` - use these (mesh + embedded palette texture in one file)
- `obj/*.obj` + `.mtl` + `WinterPalette.png` - fallback
- `src/` - Python generator (`python3 src/props.py` rebuilds everything, needs numpy)

## Import into Roblox Studio
1. Avatar tab / Home > **Import 3D**, pick a `.glb`.
2. Set the scale unit to **studs** (models are built 1 unit = 1 stud, snowman ~11 studs tall).
3. Each prop is one MeshPart with a small palette texture (one draw call). Base sits at y=0.
4. `SnowyLampPost` has a separate `Glass` part: set its Material to **Neon** and drop a PointLight in it.
5. Set `CollisionFidelity` to `Box`/`Hull` for decor you walk past, `PreciseConvexDecomposition` only where needed.
