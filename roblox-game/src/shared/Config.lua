-- Config partagee entre serveur et client.

local Config = {}

Config.ARENA_SIZE = 160         -- cote de l'arene (studs)
Config.SPAWN_HEIGHT = 90        -- hauteur depuis laquelle les Ferrari tombent
Config.SPAWN_INTERVAL = 1.4     -- secondes entre deux spawns
Config.FALL_TIME = 5            -- secondes pour qu'une Ferrari touche le sol

-- Types de cibles : poids = probabilite de spawn (cumul des poids = 1.0).
Config.KINDS = {
    {
        name = "Red",
        label = "Ferrari",
        color = Color3.fromRGB(220, 40, 40),
        points = 10,
        weight = 0.70,
    },
    {
        name = "Yellow",
        label = "Ferrari +",
        color = Color3.fromRGB(240, 200, 40),
        points = 25,
        weight = 0.20,
    },
    {
        name = "Bomb",
        label = "BOMBE !",
        color = Color3.fromRGB(20, 20, 20),
        points = -50,
        weight = 0.10,
    },
}

return Config
