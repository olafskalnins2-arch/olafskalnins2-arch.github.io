--!strict
-- FurnitureSetup (Script in ServerScriptService)
-- Finds every imported prop in Workspace (also ones spawned later), copies its settings
-- from FurnitureConfig onto the model as attributes and tags it "Movable".
-- MovableFurniture then turns it into a carryable physics object.

local CollectionService = game:GetService("CollectionService")
local Config = require(script.Parent:WaitForChild("FurnitureConfig"))

local function tryTag(inst: Instance)
	if not inst:IsA("Model") or CollectionService:HasTag(inst, "Movable") then return end
	local entry = Config.get(inst.Name)
	if not entry then return end
	for k, v in entry :: any do
		if inst:GetAttribute(k) == nil then inst:SetAttribute(k, v) end -- attributes you set by hand win
	end
	CollectionService:AddTag(inst, "Movable")
end

for _, d in workspace:GetDescendants() do tryTag(d) end
workspace.DescendantAdded:Connect(function(d)
	task.defer(tryTag, d) -- let a freshly cloned model finish parenting its children first
end)
