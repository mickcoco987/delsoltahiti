-- HUD client : affiche le score en haut a gauche + une bande d'instruction
-- en bas. Le score est tenu cote serveur ; on le recoit via RemoteEvent.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Events = ReplicatedStorage:WaitForChild("Events")
local scoreChanged = Events:WaitForChild("ScoreChanged")
local player = Players.LocalPlayer

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "FerrariCatcherHUD"
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

-- --- carte "Score" en haut a gauche ----------------------------------------

local scoreFrame = Instance.new("Frame")
scoreFrame.Size = UDim2.new(0, 280, 0, 78)
scoreFrame.Position = UDim2.new(0, 20, 0, 20)
scoreFrame.BackgroundColor3 = Color3.fromRGB(20, 18, 16)
scoreFrame.BackgroundTransparency = 0.18
scoreFrame.BorderSizePixel = 0
scoreFrame.Parent = screenGui

local frameCorner = Instance.new("UICorner")
frameCorner.CornerRadius = UDim.new(0, 12)
frameCorner.Parent = scoreFrame

-- bandeau rouge a gauche
local stripe = Instance.new("Frame")
stripe.Size = UDim2.new(0, 4, 1, 0)
stripe.Position = UDim2.new(0, 0, 0, 0)
stripe.BackgroundColor3 = Color3.fromRGB(255, 40, 0)
stripe.BorderSizePixel = 0
stripe.Parent = scoreFrame
local stripeCorner = Instance.new("UICorner")
stripeCorner.CornerRadius = UDim.new(0, 12)
stripeCorner.Parent = stripe

local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, -20, 0, 22)
title.Position = UDim2.new(0, 18, 0, 10)
title.BackgroundTransparency = 1
title.Font = Enum.Font.Gotham
title.TextColor3 = Color3.fromRGB(180, 170, 160)
title.TextSize = 14
title.TextXAlignment = Enum.TextXAlignment.Left
title.Text = "SCORE"
title.Parent = scoreFrame

local scoreLabel = Instance.new("TextLabel")
scoreLabel.Size = UDim2.new(1, -20, 0, 40)
scoreLabel.Position = UDim2.new(0, 18, 0, 30)
scoreLabel.BackgroundTransparency = 1
scoreLabel.Font = Enum.Font.GothamBold
scoreLabel.TextColor3 = Color3.fromRGB(255, 245, 235)
scoreLabel.TextSize = 36
scoreLabel.TextXAlignment = Enum.TextXAlignment.Left
scoreLabel.Text = "0"
scoreLabel.Parent = scoreFrame

-- --- bandeau d'instructions en bas -----------------------------------------

local hint = Instance.new("TextLabel")
hint.Size = UDim2.new(0, 720, 0, 40)
hint.Position = UDim2.new(0.5, -360, 1, -60)
hint.BackgroundColor3 = Color3.fromRGB(20, 18, 16)
hint.BackgroundTransparency = 0.35
hint.BorderSizePixel = 0
hint.Font = Enum.Font.Gotham
hint.TextColor3 = Color3.fromRGB(245, 240, 230)
hint.TextStrokeTransparency = 0.5
hint.TextSize = 16
hint.Text = "Clique les Ferrari rouges (+10) et jaunes (+25). Évite les bombes noires (-50) !"
hint.Parent = screenGui

local hintCorner = Instance.new("UICorner")
hintCorner.CornerRadius = UDim.new(0, 8)
hintCorner.Parent = hint

-- --- mise a jour du score --------------------------------------------------

scoreChanged.OnClientEvent:Connect(function(value)
    scoreLabel.Text = tostring(value)
end)
