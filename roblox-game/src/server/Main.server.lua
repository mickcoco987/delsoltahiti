-- Mini-jeu Ferrari 458 Catcher : des Ferrari tombent du ciel, les joueurs
-- les cliquent pour scorer. Rouge = +10, jaune = +25, bombe noire = -50.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")
local Lighting = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Events = ReplicatedStorage:WaitForChild("Events")
local scoreChanged = Events:WaitForChild("ScoreChanged")

-- --- decor minimal ---------------------------------------------------------

Lighting.Brightness = 2
Lighting.Ambient = Color3.fromRGB(80, 80, 90)
Lighting.OutdoorAmbient = Color3.fromRGB(140, 140, 160)

local function ensureBaseplate()
    if Workspace:FindFirstChild("Baseplate") then return end
    local base = Instance.new("Part")
    base.Name = "Baseplate"
    base.Anchored = true
    base.Size = Vector3.new(Config.ARENA_SIZE, 1, Config.ARENA_SIZE)
    base.Position = Vector3.new(0, 0, 0)
    base.Material = Enum.Material.Grass
    base.BrickColor = BrickColor.new("Dark green")
    base.TopSurface = Enum.SurfaceType.Smooth
    base.BottomSurface = Enum.SurfaceType.Smooth
    base.Parent = Workspace
end
ensureBaseplate()

-- --- score par joueur ------------------------------------------------------

local scores = {}

local function setScore(player, value)
    scores[player] = math.max(0, value)
    scoreChanged:FireClient(player, scores[player])
end

Players.PlayerAdded:Connect(function(player)
    setScore(player, 0)
end)
Players.PlayerRemoving:Connect(function(player)
    scores[player] = nil
end)

-- --- spawn d'une Ferrari ---------------------------------------------------

local function pickKind()
    local r = math.random()
    local cum = 0
    for _, kind in ipairs(Config.KINDS) do
        cum = cum + kind.weight
        if r <= cum then return kind end
    end
    return Config.KINDS[1]
end

local function spawnFerrari()
    local kind = pickKind()
    local part = Instance.new("Part")
    part.Name = "Ferrari_" .. kind.name
    part.Anchored = true
    part.Size = Vector3.new(6, 2, 12)
    part.Color = kind.color
    part.Material = Enum.Material.SmoothPlastic
    part.TopSurface = Enum.SurfaceType.Smooth
    part.BottomSurface = Enum.SurfaceType.Smooth

    local startPos = Vector3.new(
        math.random(-Config.ARENA_SIZE / 2 + 10, Config.ARENA_SIZE / 2 - 10),
        Config.SPAWN_HEIGHT,
        math.random(-Config.ARENA_SIZE / 2 + 10, Config.ARENA_SIZE / 2 - 10)
    )
    part.Position = startPos
    part.Parent = Workspace

    -- etiquette flottante au-dessus
    local bb = Instance.new("BillboardGui")
    bb.Size = UDim2.new(0, 140, 0, 40)
    bb.StudsOffset = Vector3.new(0, 3, 0)
    bb.AlwaysOnTop = true
    bb.Parent = part
    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(1, 0, 1, 0)
    label.BackgroundTransparency = 1
    label.Text = kind.label
    label.TextColor3 = kind.color
    label.TextStrokeTransparency = 0
    label.TextStrokeColor3 = Color3.new(0, 0, 0)
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.Parent = bb

    -- handler de clic (cote serveur)
    local detector = Instance.new("ClickDetector")
    detector.MaxActivationDistance = 300
    detector.Parent = part
    detector.MouseClick:Connect(function(player)
        if not part.Parent then return end
        setScore(player, (scores[player] or 0) + kind.points)
        part:Destroy()
    end)

    -- chute animee (TweenService = controle precis du timing)
    local endPos = Vector3.new(startPos.X, 1.5, startPos.Z)
    local tween = TweenService:Create(
        part,
        TweenInfo.new(Config.FALL_TIME, Enum.EasingStyle.Linear, Enum.EasingDirection.Out),
        { Position = endPos }
    )
    tween:Play()
    tween.Completed:Connect(function()
        if part.Parent then part:Destroy() end
    end)
end

-- --- boucle principale -----------------------------------------------------

task.spawn(function()
    while true do
        task.wait(Config.SPAWN_INTERVAL)
        pcall(spawnFerrari)
    end
end)

print("[Ferrari 458 Catcher] serveur pret. Bonne chasse.")
