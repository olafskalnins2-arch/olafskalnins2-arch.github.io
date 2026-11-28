--!strict
-- CosmeticService (ModuleScript) -> put in ServerScriptService
-- Equips the skinned cosmetic MeshParts onto a character that uses the same 15-bone rig
-- (LowerTorso, UpperTorso, Head, Left/Right UpperArm/LowerArm/Hand, Left/Right UpperLeg/LowerLeg/Foot).
--
-- Expects: ServerStorage.Cosmetics.CosmeticsRig  (Roblox_Ready/00_Import_Helper/CosmeticsRig.glb imported as a Model)
-- The outfit MeshParts are cloned into the live character next to its body MeshPart, so their skinning
-- resolves to the character's own bones by name and they animate with the character. Nothing on the
-- character is replaced, resized or modified.

local ServerStorage = game:GetService("ServerStorage")

local CosmeticService = {}

-- Name of the skinned body MeshPart inside your character model. Change if yours differs.
CosmeticService.BODY_NAME = "Body"
local ATTR = "CosmeticOutfit"

CosmeticService.OUTFITS = {
	"01_Classic_Mover", "02_Chill_Dude", "03_Raincoat", "04_Boss_Mode", "05_Construction_Hero",
	"06_Chef", "07_Firefighter", "08_Pirate", "09_Wizard", "10_Knight", "11_Astronaut", "12_Ghost", "13_Dinosaur",
	"14_Hoodie_Hauler", "15_Denim_Overalls", "16_Gym_Buddy", "17_Comfy_Pajamas", "18_Parcel_Courier",
	"19_Green_Thumb", "20_Splash_Painter", "21_Lumberjack", "22_Mail_Carrier", "23_Barista",
	"24_Shadow_Ninja", "25_Desert_Cowboy", "26_Surgeon", "27_Speed_Racer", "28_Deep_Diver",
	"29_Noir_Detective", "30_Skater_Kid", "31_Jungle_Explorer", "32_Rock_Star", "33_Samurai_Warlord",
	"34_Frost_Viking", "35_Sun_Pharaoh", "36_Ice_Mage", "37_Mecha_Pilot", "38_Royal_Guard",
	"39_Court_Jester", "40_Dragon_Knight", "41_Seraph", "42_Neon_Ronin", "43_Phoenix_Emperor",
}

-- Rarity of each skin: "Common" < "Rare" < "Epic" < "Legendary". The first 13 are the original set ("Original").
CosmeticService.RARITY = {
	["14_Hoodie_Hauler"] = "Common",
	["15_Denim_Overalls"] = "Common",
	["16_Gym_Buddy"] = "Common",
	["17_Comfy_Pajamas"] = "Common",
	["18_Parcel_Courier"] = "Common",
	["19_Green_Thumb"] = "Common",
	["20_Splash_Painter"] = "Common",
	["21_Lumberjack"] = "Common",
	["22_Mail_Carrier"] = "Common",
	["23_Barista"] = "Common",
	["24_Shadow_Ninja"] = "Rare",
	["25_Desert_Cowboy"] = "Rare",
	["26_Surgeon"] = "Rare",
	["27_Speed_Racer"] = "Rare",
	["28_Deep_Diver"] = "Rare",
	["29_Noir_Detective"] = "Rare",
	["30_Skater_Kid"] = "Rare",
	["31_Jungle_Explorer"] = "Rare",
	["32_Rock_Star"] = "Rare",
	["33_Samurai_Warlord"] = "Epic",
	["34_Frost_Viking"] = "Epic",
	["35_Sun_Pharaoh"] = "Epic",
	["36_Ice_Mage"] = "Epic",
	["37_Mecha_Pilot"] = "Epic",
	["38_Royal_Guard"] = "Epic",
	["39_Court_Jester"] = "Epic",
	["40_Dragon_Knight"] = "Legendary",
	["41_Seraph"] = "Legendary",
	["42_Neon_Ronin"] = "Legendary",
	["43_Phoenix_Emperor"] = "Legendary",
}
for _, id in CosmeticService.OUTFITS do
	if CosmeticService.RARITY[id] == nil then CosmeticService.RARITY[id] = "Original" end
end

function CosmeticService.GetRarity(outfitId: string): string?
	return CosmeticService.RARITY[outfitId]
end

local VALID: { [string]: boolean } = {}
for _, id in CosmeticService.OUTFITS do
	VALID[id] = true
end

function CosmeticService.IsValid(outfitId: string): boolean
	return VALID[outfitId] == true
end

-- Hook for ownership / gamepass / currency checks. Default: everyone owns everything.
function CosmeticService.CanUse(_player: Player, outfitId: string): boolean
	return VALID[outfitId] == true
end

local function getTemplate(): (Model?, BasePart?)
	local folder = ServerStorage:FindFirstChild("Cosmetics")
	local rig = folder and folder:FindFirstChild("CosmeticsRig")
	if not (rig and rig:IsA("Model")) then
		warn("[CosmeticService] ServerStorage.Cosmetics.CosmeticsRig is missing")
		return nil, nil
	end
	local body = rig:FindFirstChild(CosmeticService.BODY_NAME, true)
	if not (body and body:IsA("BasePart")) then
		warn("[CosmeticService] CosmeticsRig has no '" .. CosmeticService.BODY_NAME .. "' part")
		return nil, nil
	end
	return rig, body
end

function CosmeticService.GetEquipped(character: Model): string?
	local v = character:GetAttribute(ATTR)
	return if typeof(v) == "string" then v else nil
end

function CosmeticService.Unequip(character: Model)
	for _, d in character:GetDescendants() do
		if d:IsA("MeshPart") and d:GetAttribute(ATTR) ~= nil then
			d:Destroy()
		end
	end
	character:SetAttribute(ATTR, nil)
end

function CosmeticService.Equip(character: Model, outfitId: string): boolean
	if not VALID[outfitId] then
		return false
	end
	local liveBody = character:FindFirstChild(CosmeticService.BODY_NAME, true)
	if not (liveBody and liveBody:IsA("BasePart")) then
		warn("[CosmeticService] character has no '" .. CosmeticService.BODY_NAME .. "' part")
		return false
	end
	local rig, templateBody = getTemplate()
	if not (rig and templateBody) then
		return false
	end
	CosmeticService.Unequip(character)

	local container = liveBody.Parent :: Instance
	local count = 0
	for _, src in rig:GetDescendants() do
		if src:IsA("MeshPart") and string.sub(src.Name, 1, #outfitId + 1) == outfitId .. "_" then
			local part = src:Clone()
			-- drop anything that would bind the clone to the template instead of the live rig
			for _, d in part:GetDescendants() do
				if d:IsA("Bone") or d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("Constraint") then
					d:Destroy()
				end
			end
			part.Anchored = false
			part.CanCollide = false
			part.CanTouch = false
			part.CanQuery = false
			part.Massless = true
			-- same rest-space offset from the body as in the template (both were exported on one skeleton)
			part.CFrame = liveBody.CFrame * templateBody.CFrame:ToObjectSpace(src.CFrame)
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = liveBody
			weld.Part1 = part
			weld.Parent = part
			part:SetAttribute(ATTR, outfitId)
			part.Parent = container
			count += 1
		end
	end
	if count == 0 then
		warn("[CosmeticService] no MeshParts found for " .. outfitId)
		return false
	end
	character:SetAttribute(ATTR, outfitId)
	return true
end

return CosmeticService
