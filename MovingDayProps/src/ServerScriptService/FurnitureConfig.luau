--!strict
-- FurnitureConfig (ModuleScript in ServerScriptService)
-- Per-model settings, keyed by the model name the GLB imports as.
-- Weight: how heavy it feels (slows the carrier). DoorAngle / FlipDoors / DrawerSlide / NoSpill: see MovableFurniture.

export type Entry = { Weight: number, DoorAngle: number?, FlipDoors: boolean?, DrawerSlide: number?, NoSpill: boolean? }

local C: { [string]: Entry } = {
	-- big appliances & furniture
	WasherW01 = { Weight = 120 },
	PianoP01 = { Weight = 150 },
	BedB01 = { Weight = 120 },
	SingleBedB03 = { Weight = 70 },
	SofaS01 = { Weight = 80 },
	StoveO01 = { Weight = 60 },
	DresserD01 = { Weight = 55 },
	SideboardS03 = { Weight = 60, DoorAngle = 90 }, -- middle doors share a hinge line
	CabinetC01 = { Weight = 50 },
	KegK01 = { Weight = 50 },
	BookshelfS05 = { Weight = 45 },
	KitchenCabinetK02 = { Weight = 40 },
	TVStandT04 = { Weight = 40 },
	ClockG01 = { Weight = 70 },
	ChestC04 = { Weight = 35 },
	ToiletW01 = { Weight = 35 },
	RadiatorR02 = { Weight = 60 },
	-- medium
	MonitorM01 = { Weight = 25 },
	CoffeeTableT02 = { Weight = 25 },
	NightstandN01 = { Weight = 20 },
	AmpA01 = { Weight = 20 },
	SewingMachineS04 = { Weight = 18 },
	MicrowaveM02 = { Weight = 15 },
	TypewriterT01 = { Weight = 15 },
	SuitcaseS02 = { Weight = 15 },
	MirrorStandM03 = { Weight = 15 },
	RockingChairC03 = { Weight = 15 },
	ChairC01 = { Weight = 12 },
	StepLadderL01 = { Weight = 12 },
	ToolboxT03 = { Weight = 12 },
	-- light
	GlobeE01 = { Weight = 10 },
	IroningBoardI01 = { Weight = 10 },
	VacuumV01 = { Weight = 10 },
	RadioR01 = { Weight = 8 },
	MovingBoxX01 = { Weight = 8 },
	BookStackB02 = { Weight = 6 },
	PictureFrameF01 = { Weight = 3 },
}

-- match names loosely: "WasherW01", "washer_w01", "WasherW01 (2)" all hit the same entry
local byKey: { [string]: Entry } = {}
local function key(name: string): string
	return (string.lower(name):gsub("%s*%(%d+%)$", ""):gsub("[^%w]", ""))
end
for name, entry in C do byKey[key(name)] = entry end

return {
	get = function(name: string): Entry? return byKey[key(name)] end,
	all = C,
}
