--!strict
-- MovableFurniture (Script in ServerScriptService)
-- Tag any furniture Model with "Movable".
--
-- Solid items (washer): one invisible box hitbox does all the collision.
-- Hollow items (cabinet): parts named "Col_..." become the real hitboxes (walls),
--   so stuff fits inside. A Col_ part inside a Model whose name contains "Door"
--   becomes a swinging door hitbox: the whole door hinges on its outer edge.
--   Same inside a Model whose name contains "Lid": it hinges on its back top edge
--   and lifts up (piano key cover, chest lid).
--   "Flap" in the name = hinges on its bottom edge and folds down (oven door).
--   "Drawer" in the name = slides straight out (attribute DrawerSlide sets how far, in studs).
--   A door/drawer may hold several Col_ parts (floor + walls, so stuff sits inside it):
--   "Col_<ModelName>" is the main one, the others are welded to it.
--   Put "HingeL" or "HingeR" in a door model's name to force which edge it hinges on
--   (needed when doors meet in pairs, e.g. a sideboard).
--
-- Physics extras:
--   * Tips over past 55 degrees -> every door, lid and drawer unlocks and swings / slides free.
--     Pressing F on one puts its motor back. Attribute NoSpill = true turns this off per item.
--   * Picking an item up welds whatever lies inside or on top of it, so contents travel with it.
--
-- Optional attributes on the Model:
--   Weight        (number, default 60)  heavier = slower carrier
--   HoldDistance  (number, default 1.5) gap between player and item while carrying
--   DoorAngle     (number, default 110) how far doors open, in degrees
--   FlipDoors     (bool)                set true if the doors swing inward

local CollectionService = game:GetService("CollectionService")
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local TAG = "Movable"
local BASE_SPEED = 16
local MIN_SPEED = 7

PhysicsService:RegisterCollisionGroup("Characters")
PhysicsService:RegisterCollisionGroup("CarriedItems")
PhysicsService:CollisionGroupSetCollidable("Characters", "CarriedItems", false)

type Door = {
	col: BasePart,
	hinge: HingeConstraint?, -- doors, lids, flaps
	slide: PrismaticConstraint?, -- drawers
	slideDist: number,
	subs: { BasePart }, -- extra hitboxes of the same door/drawer (drawer walls and floor)
	lock: WeldConstraint,
	closedOffset: CFrame, -- door hitbox relative to the item hitbox when shut
	prompt: ProximityPrompt,
	open: boolean,
}
type Item = {
	model: Model,
	hitbox: BasePart,
	colliders: { BasePart }, -- whatever actually collides
	doors: { Door },
	pickPrompt: ProximityPrompt,
	spilled: boolean, -- tipped over: doors and drawers are hanging free
}
type CarryState = { item: Item, parts: { Instance }, regrouped: { [BasePart]: string }, reenable: { ProximityPrompt } }

local items: { [Model]: Item } = {}
local carrying: { [Player]: CarryState } = {}
local carriedBy: { [Model]: Player } = {}

local function isCollider(p: Instance): boolean
	return p:IsA("BasePart") and string.find(p.Name, "Col_", 1, true) ~= nil
end

local OPENABLE = { "Door", "Lid", "Flap", "Drawer" }

local function doorModelOf(part: Instance, item: Model): Model?
	local a = part.Parent
	while a and a ~= item do
		if a:IsA("Model") then
			for _, key in OPENABLE do
				if string.find(a.Name, key, 1, true) then return a end
			end
		end
		a = a.Parent
	end
	return nil
end

local function setGroup(item: Item, group: string)
	for _, c in item.colliders do c.CollisionGroup = group end
	for _, d in item.doors do
		d.col.CollisionGroup = group
		for _, sc in d.subs do sc.CollisionGroup = group end
	end
end

-- doors --------------------------------------------------------------------

local function jointValue(door: Door): number
	if door.slide then return door.slide.CurrentPosition end
	return (door.hinge :: HingeConstraint).CurrentAngle
end

local function setTarget(door: Door, open: boolean)
	if door.slide then
		door.slide.TargetPosition = if open then door.slideDist else 0
	else
		local h = door.hinge :: HingeConstraint
		h.TargetAngle = if open then (if h.UpperAngle ~= 0 then h.UpperAngle else h.LowerAngle) else 0
	end
end

local function setActuator(door: Door, servo: boolean)
	local t = if servo then Enum.ActuatorType.Servo else Enum.ActuatorType.None
	if door.slide then door.slide.ActuatorType = t end
	if door.hinge then door.hinge.ActuatorType = t end
end

local function setDoor(door: Door, open: boolean)
	setActuator(door, true)
	door.open = open
	door.prompt.ActionText = if open then "Close" else "Open"
	if open then
		door.lock.Enabled = false
		setTarget(door, true)
	else
		setTarget(door, false)
		task.delay(0.6, function()
			local closeEnough = if door.slide then 0.05 else 5
			if not door.open and math.abs(jointValue(door)) < closeEnough then door.lock.Enabled = true end
		end)
	end
end

local function snapShut(item: Item, door: Door)
	setActuator(door, true)
	door.open = false
	door.prompt.ActionText = "Open"
	setTarget(door, false)
	door.col.CFrame = item.hitbox.CFrame * door.closedOffset
	door.lock.Enabled = true
end

-- the item-space horizontal axis this part sits furthest along (its "out" direction), as a unit vector
local function outwardOf(hitbox: BasePart, part: BasePart): Vector3
	local off = part.Position - hitbox.Position
	local r, l = hitbox.CFrame.RightVector, hitbox.CFrame.LookVector
	local dr, dl = off:Dot(r), off:Dot(l)
	if math.abs(dr) > math.abs(dl) then return r * (if dr >= 0 then 1 else -1) end
	return l * (if dl >= 0 then 1 else -1)
end

local function makeDoor(item: Model, hitbox: BasePart, col: BasePart, doorModel: Model, walls: { BasePart }, subs: { BasePart }): Door
	col.Massless = false
	col.CustomPhysicalProperties = PhysicalProperties.new(0.3, 0.5, 0.1)

	-- visible meshes ride on the door / drawer hitbox
	for _, d in doorModel:GetDescendants() do
		if d:IsA("BasePart") and d ~= col then
			local w = Instance.new("WeldConstraint"); w.Part0 = col; w.Part1 = d; w.Parent = col
		end
	end

	local cf, size = col.CFrame, col.Size
	local centre = hitbox.Position
	local name = doorModel.Name
	local hinge: HingeConstraint? = nil
	local slide: PrismaticConstraint? = nil
	local slideDist = 0

	if string.find(name, "Drawer", 1, true) then
		-- drawer: slides straight out of the front
		local out = outwardOf(hitbox, col)
		local depth = math.abs(cf:VectorToObjectSpace(out).X) * size.X + math.abs(cf:VectorToObjectSpace(out).Z) * size.Z
		slideDist = (item:GetAttribute("DrawerSlide") :: number?) or depth * 0.75
		local slideCF = CFrame.fromMatrix(col.Position, out, hitbox.CFrame.UpVector) -- attachment X axis = slide axis
		local a0 = Instance.new("Attachment"); a0.Name = "Slide0"; a0.Parent = hitbox; a0.WorldCFrame = slideCF
		local a1 = Instance.new("Attachment"); a1.Name = "Slide1"; a1.Parent = col; a1.WorldCFrame = slideCF
		local p = Instance.new("PrismaticConstraint")
		p.Attachment0 = a0; p.Attachment1 = a1
		p.ActuatorType = Enum.ActuatorType.Servo
		p.Speed = 4; p.ServoMaxForce = 1e5
		p.LimitsEnabled = true; p.LowerLimit = 0; p.UpperLimit = slideDist
		p.Parent = col
		slide = p
	else
		local longAxis: Vector3, halfLong: number, shortAxis: Vector3, halfShort: number
		if size.X >= size.Z then
			longAxis, halfLong, shortAxis, halfShort = cf.RightVector, size.X / 2, cf.LookVector, size.Z / 2
		else
			longAxis, halfLong, shortAxis, halfShort = cf.LookVector, size.Z / 2, cf.RightVector, size.X / 2
		end
		local axis: Vector3, hingePos: Vector3, sign: number, defaultAngle: number
		if string.find(name, "Lid", 1, true) then
			-- lid (key cover, chest lid): hinges along its long side, on the edge nearest the item centre, at the top
			axis = longAxis
			local towardCentre = if (col.Position - centre):Dot(shortAxis) >= 0 then -1 else 1
			hingePos = col.Position + shortAxis * towardCentre * halfShort + cf.UpVector * (size.Y / 2)
			local test = CFrame.fromAxisAngle(axis, math.rad(90)):VectorToWorldSpace(col.Position - hingePos)
			sign = if test:Dot(hitbox.CFrame.UpVector) > 0 then 1 else -1 -- opening lifts the free edge
			defaultAngle = 95
		elseif string.find(name, "Flap", 1, true) then
			-- flap (oven door): hinges along its bottom edge and folds down toward you
			axis = longAxis
			local out = outwardOf(hitbox, col)
			hingePos = col.Position - cf.UpVector * (size.Y / 2)
			local test = CFrame.fromAxisAngle(axis, math.rad(90)):VectorToWorldSpace(col.Position - hingePos)
			sign = if test:Dot(out) > 0 then 1 else -1
			defaultAngle = 85
		else
			-- door: hinges on the end of its long horizontal axis furthest from the item centre
			axis = cf.UpVector
			local side = if (col.Position - centre):Dot(longAxis) >= 0 then 1 else -1
			-- "HingeL" / "HingeR" in the name forces the hinge to the item's left / right edge of the door
			local right = hitbox.CFrame.RightVector
			if string.find(name, "HingeL", 1, true) then
				side = if longAxis:Dot(right) >= 0 then -1 else 1
			elseif string.find(name, "HingeR", 1, true) then
				side = if longAxis:Dot(right) >= 0 then 1 else -1
			end
			hingePos = col.Position + longAxis * side * halfLong
			local out = shortAxis * (if (col.Position - centre):Dot(shortAxis) >= 0 then 1 else -1)
			local test = CFrame.fromAxisAngle(axis, math.rad(90)):VectorToWorldSpace(col.Position - hingePos)
			sign = if test:Dot(out) > 0 then 1 else -1 -- opening swings outward
			defaultAngle = 110
		end
		if item:GetAttribute("FlipDoors") then sign = -sign end
		local angle = ((item:GetAttribute("DoorAngle") :: number?) or defaultAngle) * sign

		local perp = if math.abs(axis:Dot(cf.UpVector)) > 0.9 then longAxis else cf.UpVector
		local hingeCF = CFrame.fromMatrix(hingePos, axis, perp) -- attachment X axis = hinge axis
		local a0 = Instance.new("Attachment"); a0.Name = "DoorHinge0"; a0.Parent = hitbox; a0.WorldCFrame = hingeCF
		local a1 = Instance.new("Attachment"); a1.Name = "DoorHinge1"; a1.Parent = col; a1.WorldCFrame = hingeCF
		local h = Instance.new("HingeConstraint")
		h.Attachment0 = a0; h.Attachment1 = a1
		h.ActuatorType = Enum.ActuatorType.Servo
		h.AngularSpeed = 4
		h.ServoMaxTorque = 1e5
		h.LimitsEnabled = true
		h.LowerAngle = math.min(0, angle); h.UpperAngle = math.max(0, angle)
		h.Parent = col
		hinge = h
	end

	local lock = Instance.new("WeldConstraint"); lock.Name = "DoorLock"
	lock.Part0 = hitbox; lock.Part1 = col; lock.Parent = col

	-- must not fight its own item (walls, or the solid box hitbox)
	for _, part in { col, table.unpack(subs) } do
		local ncRoot = Instance.new("NoCollisionConstraint"); ncRoot.Part0 = part; ncRoot.Part1 = hitbox; ncRoot.Parent = col
		for _, wall in walls do
			local nc = Instance.new("NoCollisionConstraint"); nc.Part0 = part; nc.Part1 = wall; nc.Parent = col
		end
	end

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "Open"
	prompt.ObjectText = name
	prompt.KeyboardKeyCode = Enum.KeyCode.F
	prompt.GamepadKeyCode = Enum.KeyCode.ButtonY
	prompt.MaxActivationDistance = 7
	prompt.RequiresLineOfSight = false
	prompt.UIOffset = Vector2.new(0, 60)
	prompt.Parent = col

	return { col = col, hinge = hinge, slide = slide, slideDist = slideDist, subs = subs, lock = lock,
		closedOffset = hitbox.CFrame:ToObjectSpace(col.CFrame), prompt = prompt, open = false }
end

-- carrying -----------------------------------------------------------------

local function drop(player: Player)
	local state = carrying[player]
	if not state then return end
	carrying[player] = nil
	local item = state.item
	carriedBy[item.model] = nil
	player:SetAttribute("Carrying", nil)
	for _, inst in state.parts do inst:Destroy() end
	for part, group in state.regrouped do if part.Parent then part.CollisionGroup = group end end
	for _, pr in state.reenable do if pr.Parent then pr.Enabled = true end end

	if item.hitbox.Parent then
		setGroup(item, "Default")
		item.hitbox.AssemblyLinearVelocity = Vector3.zero
		pcall(function() item.hitbox:SetNetworkOwnershipAuto() end)
		item.pickPrompt.Enabled = true
		for _, d in item.doors do d.prompt.Enabled = true end
	end

	local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
	if humanoid then humanoid.WalkSpeed = BASE_SPEED end
end

local function pickUp(player: Player, item: Item)
	if carrying[player] or carriedBy[item.model] then return end
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not (root and humanoid and humanoid.Health > 0) then return end

	for _, d in item.doors do snapShut(item, d); d.prompt.Enabled = false end
	item.pickPrompt.Enabled = false -- nobody can steal it mid-carry

	local hitbox = item.hitbox
	local gap = (item.model:GetAttribute("HoldDistance") :: number?) or 1.5
	local a0 = Instance.new("Attachment"); a0.Name = "CarryItem"; a0.Parent = hitbox
	local a1 = Instance.new("Attachment"); a1.Name = "CarryHold"
	a1.CFrame = CFrame.new(0, 0.5, -(root.Size.Z / 2 + hitbox.Size.Z / 2 + gap)); a1.Parent = root

	local alignPos = Instance.new("AlignPosition")
	alignPos.Attachment0 = a0; alignPos.Attachment1 = a1
	alignPos.MaxForce = 1e6; alignPos.Responsiveness = 30
	alignPos.Parent = hitbox
	local alignRot = Instance.new("AlignOrientation")
	alignRot.Attachment0 = a0; alignRot.Attachment1 = a1
	alignRot.MaxTorque = 1e6; alignRot.Responsiveness = 30
	alignRot.Parent = hitbox

	setGroup(item, "CarriedItems")
	pcall(function() hitbox:SetNetworkOwner(player) end)

	local weight = (item.model:GetAttribute("Weight") :: number?) or 60
	humanoid.WalkSpeed = math.max(MIN_SPEED, BASE_SPEED - weight / 10)

	local state: CarryState = { item = item, parts = { a0, a1, alignPos, alignRot }, regrouped = {}, reenable = {} }

	-- whatever is lying inside (or on top of) the item gets welded on for the trip
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { item.model, character }
	local seen: { [BasePart]: boolean } = {}
	for _, p in workspace:GetPartBoundsInBox(hitbox.CFrame, hitbox.Size + Vector3.new(0, 0.5, 0), params) do
		local r = p.AssemblyRootPart
		if r and not r.Anchored and not seen[r] then
			seen[r] = true
			local owner = r:FindFirstAncestorOfClass("Model")
			local isCharacter = owner and owner:FindFirstChildOfClass("Humanoid") ~= nil
			-- only things whose centre is inside the item's footprint and above its bottom
			-- (never the furniture it is standing on)
			local rel = hitbox.CFrame:PointToObjectSpace(r.Position)
			local half = hitbox.Size / 2
			local inside = math.abs(rel.X) <= half.X and math.abs(rel.Z) <= half.Z and rel.Y > -half.Y + 0.05
			if inside and not isCharacter and not (owner and carriedBy[owner]) then
				local inner = owner and items[owner]
				if inner then -- a prop riding inside another prop can't be grabbed until it's set down
					inner.pickPrompt.Enabled = false
					table.insert(state.reenable, inner.pickPrompt)
				end
				local w = Instance.new("WeldConstraint"); w.Name = "CarriedContents"
				w.Part0 = hitbox; w.Part1 = r; w.Parent = hitbox
				table.insert(state.parts, w)
				for _, cp in r:GetConnectedParts(true) do
					if cp:IsA("BasePart") and not state.regrouped[cp] then
						state.regrouped[cp] = cp.CollisionGroup
						cp.CollisionGroup = "CarriedItems"
					end
				end
			end
		end
	end
	carrying[player] = state
	carriedBy[item.model] = player
	player:SetAttribute("Carrying", item.model.Name)
end

-- setup --------------------------------------------------------------------

local function setup(inst: Instance)
	if not inst:IsA("Model") or items[inst] then return end
	local model = inst

	-- invisible root: owns the mass, the prompt and every weld
	local cf, size = model:GetBoundingBox()
	local hitbox = Instance.new("Part")
	hitbox.Name = "Hitbox"
	hitbox.Size = size; hitbox.CFrame = cf
	hitbox.Transparency = 1; hitbox.Anchored = false
	local weight = (model:GetAttribute("Weight") :: number?) or 60
	hitbox.CustomPhysicalProperties = PhysicalProperties.new(math.clamp(weight / (size.X * size.Y * size.Z), 0.01, 100), 0.6, 0.1)
	hitbox.Parent = model

	local walls: { BasePart } = {}
	local doorParts: { [Model]: { BasePart } } = {}
	for _, d in model:GetDescendants() do
		if d ~= hitbox and isCollider(d) then
			local p = d :: BasePart
			p.Transparency = 1
			p.CanCollide = true; p.CanQuery = true; p.CanTouch = true
			p.Anchored = false
			if p:IsA("MeshPart") then p.CollisionFidelity = Enum.CollisionFidelity.Box end
			local dm = doorModelOf(p, model)
			if dm then
				doorParts[dm] = doorParts[dm] or {}
				table.insert(doorParts[dm], p)
			else
				p.Massless = true
				table.insert(walls, p)
			end
		end
	end
	-- a door/drawer can have several Col_ parts (a drawer's floor, walls, front): the one named
	-- "Col_<ModelName>" drives the hinge/slide, the rest ride along welded to it
	local doorCols: { [Model]: BasePart } = {}
	local doorSubs: { [Model]: { BasePart } } = {}
	for dm, list in doorParts do
		local main = list[1]
		for _, p in list do if p.Name == "Col_" .. dm.Name then main = p end end
		doorCols[dm] = main
		doorSubs[dm] = {}
		for _, p in list do if p ~= main then p.Massless = true; table.insert(doorSubs[dm], p) end end
	end
	local hollow = #walls > 0
	hitbox.CanCollide = not hollow

	-- visible meshes: no physics, welded to the root (door meshes get welded to their door in makeDoor)
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and d ~= hitbox and not isCollider(d) then
			d.Anchored = false
			d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			d.Massless = true
			if d:IsA("MeshPart") then d.CollisionFidelity = Enum.CollisionFidelity.Box end
			local dm = doorModelOf(d, model)
			if not (dm and doorCols[dm]) then
				local w = Instance.new("WeldConstraint"); w.Part0 = hitbox; w.Part1 = d; w.Parent = hitbox
			end
		end
	end
	for _, wall in walls do
		local w = Instance.new("WeldConstraint"); w.Part0 = hitbox; w.Part1 = wall; w.Parent = hitbox
	end
	model.PrimaryPart = hitbox

	local doors: { Door } = {}
	for dm, col in doorCols do table.insert(doors, makeDoor(model, hitbox, col, dm, walls, doorSubs[dm])) end
	for i = 1, #doors do -- doors meeting in the middle must not jam each other
		for j = i + 1, #doors do
			local nc = Instance.new("NoCollisionConstraint"); nc.Part0 = doors[i].col; nc.Part1 = doors[j].col; nc.Parent = doors[i].col
		end
	end

	local pick = Instance.new("ProximityPrompt")
	pick.ActionText = "Pick up"; pick.ObjectText = model.Name
	pick.HoldDuration = 0.3; pick.MaxActivationDistance = 8; pick.RequiresLineOfSight = false
	pick.Parent = hitbox

	local item: Item = { model = model, hitbox = hitbox, colliders = if hollow then walls else { hitbox }, doors = doors, pickPrompt = pick, spilled = false }
	items[model] = item

	pick.Triggered:Connect(function(player) pickUp(player, item) end)
	for _, door in doors do
		door.prompt.Triggered:Connect(function()
			if carriedBy[model] then return end
			setDoor(door, not door.open)
		end)
	end
	model.Destroying:Connect(function()
		local p = carriedBy[model]
		if p then drop(p) end
		items[model] = nil
	end)
end

-- tip-over: once an item leans past TIP_ANGLE its doors, lids and drawers let go and swing/slide freely
local TIP_COS = math.cos(math.rad(55))
task.spawn(function()
	while true do
		task.wait(0.25)
		for model, item in items do
			if #item.doors > 0 and not carriedBy[model] and item.hitbox.Parent and not model:GetAttribute("NoSpill") then
				local up = item.hitbox.CFrame.UpVector.Y
				if up < TIP_COS and not item.spilled then
					item.spilled = true
					for _, d in item.doors do
						d.open = true
						d.prompt.ActionText = "Close"
						d.lock.Enabled = false
						setActuator(d, false) -- free: gravity does the rest
					end
				elseif up > 0.9 and item.spilled then
					item.spilled = false -- stood back up; doors stay where they fell until someone closes them
				end
			end
		end
	end
end)

for _, m in CollectionService:GetTagged(TAG) do task.spawn(setup, m) end
CollectionService:GetInstanceAddedSignal(TAG):Connect(setup)

-- drop: the client fires this; the server only ever drops the caller's own item
local dropEvent = Instance.new("RemoteEvent")
dropEvent.Name = "DropCarriedItem"
dropEvent.Parent = ReplicatedStorage
dropEvent.OnServerEvent:Connect(function(player) drop(player) end)

local function onCharacter(player: Player, character: Model)
	drop(player)
	for _, d in character:GetDescendants() do
		if d:IsA("BasePart") then d.CollisionGroup = "Characters" end
	end
	character.DescendantAdded:Connect(function(d)
		if d:IsA("BasePart") then d.CollisionGroup = "Characters" end
	end)
	local humanoid = character:WaitForChild("Humanoid") :: Humanoid
	humanoid.Died:Connect(function() drop(player) end)
end

Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(c) onCharacter(player, c) end)
end)
Players.PlayerRemoving:Connect(drop)
