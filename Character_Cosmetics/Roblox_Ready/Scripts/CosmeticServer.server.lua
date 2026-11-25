--!strict
-- CosmeticServer (Script) -> put in ServerScriptService next to CosmeticService.
-- Clients request an outfit with: ReplicatedStorage.EquipCosmetic:FireServer("08_Pirate")   ("" = unequip)
-- Server validates everything; the client never decides what gets equipped on its own.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CosmeticService = require(script.Parent:WaitForChild("CosmeticService"))

local remote = ReplicatedStorage:FindFirstChild("EquipCosmetic")
if not remote then
	remote = Instance.new("RemoteEvent")
	remote.Name = "EquipCosmetic"
	remote.Parent = ReplicatedStorage
end

local COOLDOWN = 0.5
local lastRequest: { [Player]: number } = {}

local function applyTo(player: Player, character: Model)
	local id = player:GetAttribute("CosmeticOutfit")
	if typeof(id) ~= "string" or id == "" then
		CosmeticService.Unequip(character)
		return
	end
	if character:WaitForChild(CosmeticService.BODY_NAME, 10) then
		CosmeticService.Equip(character, id)
	end
end

(remote :: RemoteEvent).OnServerEvent:Connect(function(player: Player, outfitId: unknown)
	if typeof(outfitId) ~= "string" or #outfitId > 40 then
		return
	end
	local now = os.clock()
	if (lastRequest[player] or 0) + COOLDOWN > now then
		return
	end
	lastRequest[player] = now
	if outfitId ~= "" and not CosmeticService.CanUse(player, outfitId) then
		return
	end
	player:SetAttribute("CosmeticOutfit", if outfitId == "" then nil else outfitId)
	local character = player.Character
	if character then
		applyTo(player, character)
	end
end)

Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(character)
		applyTo(player, character)
	end)
end)

Players.PlayerRemoving:Connect(function(player)
	lastRequest[player] = nil
end)
