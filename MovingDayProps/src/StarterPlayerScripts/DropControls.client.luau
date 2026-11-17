--!strict
-- DropControls (LocalScript in StarterPlayer > StarterPlayerScripts)
-- Q on keyboard, B on gamepad, an on-screen button on mobile. Only active while carrying.

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local dropEvent = ReplicatedStorage:WaitForChild("DropCarriedItem") :: RemoteEvent
local ACTION = "DropCarriedItem"

local function onAction(_: string, state: Enum.UserInputState)
	if state == Enum.UserInputState.Begin then dropEvent:FireServer() end
	return Enum.ContextActionResult.Sink
end

local function refresh()
	if player:GetAttribute("Carrying") then
		ContextActionService:BindAction(ACTION, onAction, true, Enum.KeyCode.Q, Enum.KeyCode.ButtonB)
		ContextActionService:SetTitle(ACTION, "Drop")
	else
		ContextActionService:UnbindAction(ACTION)
	end
end

player:GetAttributeChangedSignal("Carrying"):Connect(refresh)
refresh()
