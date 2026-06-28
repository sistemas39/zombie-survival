import pygame

# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------
C = {
    '.': (0,   0,   0,   0  ),  # Transparente
    'k': (15,  15,  15,  255),  # Negro outline

    # Piel jugador
    'P': (255, 218, 168, 255),
    'p': (230, 185, 130, 255),
    'Q': (195, 145,  95, 255),

    # Ropa azul (jugador)
    'B': ( 55, 110, 200, 255),
    'b': ( 35,  75, 155, 255),
    'T': ( 90, 145, 230, 255),

    # Pantalón oscuro
    'N': ( 40,  40,  70, 255),
    'n': ( 25,  25,  50, 255),

    # Cabello marrón
    'M': (110,  65,  15, 255),
    'm': ( 75,  40,   5, 255),

    # Botas
    'X': ( 55,  30,   5, 255),

    # Colores extra para power-ups
    'S': ( 50, 150, 255, 255),  # Azul escudo
    's': ( 20, 100, 210, 255),  # Azul escudo sombra
    'W': (255, 255, 255, 255),  # Blanco
    'F': ( 60, 220,  90, 255),  # Verde velocidad
    'f': ( 30, 160,  60, 255),  # Verde velocidad sombra
    'L': (255,  60,  60, 255),  # Rojo fuerza
    'l': (190,  15,  15, 255),  # Rojo fuerza sombra
    'J': (255, 210,  40, 255),  # Amarillo municion
    'j': (190, 150,  15, 255),  # Amarillo municion sombra

    # Piel zombie (verde podrida)
    'Z': (120, 180, 100, 255),
    'z': ( 80, 130,  65, 255),
    'q': ( 50,  90,  40, 255),

    # Ropa zombie normal (verde oscura)
    'G': ( 45, 100,  50, 255),
    'g': ( 25,  65,  30, 255),

    # Zombie rápido (morado)
    'U': (110,  50, 170, 255),
    'u': ( 75,  25, 120, 255),

    # Zombie tanque (gris)
    'D': ( 80,  80,  85, 255),
    'd': ( 50,  50,  55, 255),

    # Sangre
    'R': (210,  20,  40, 255),
    'r': (140,   0,  15, 255),

    # Moneda
    'C': (255, 215,   0, 255),
    'c': (200, 160,   0, 255),
    'O': (240, 120,   0, 255),

    # Corazón
    'H': (245,  50,  75, 255),
    'h': (190,  15,  40, 255),
    'I': (255, 140, 160, 255),

    # Bala
    'Y': (255, 230,  60, 255),
    'y': (210, 170,  20, 255),
    'A': (190, 190, 200, 255),
    'a': (110, 110, 120, 255),
}

def make_surface(grid, scale=2):
    h = len(grid)
    w = max(len(row) for row in grid)
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            color = C.get(ch)
            if color and color[3] > 0:
                pygame.draw.rect(surf, color, (x*scale, y*scale, scale, scale))
    return surf

# ===========================================================================
#  SPRITES TOP-DOWN  (20x20, vistos desde arriba)
#  El personaje "mira hacia la derecha" → rotación en código apunta al ratón
#  Frame 0 = paso neutro / Frame 1 = paso alternado
# ===========================================================================

# ── Jugador ──────────────────────────────────────────────────────────────────
# Lectura: el sprite mira a la DERECHA.
# Cabeza arriba-centro, cuerpo debajo, piernas al fondo.
# ── Jugador (Skin 1: Azul/Castaño) ──────────────────────────────────────────
PLAYER_FRAMES = [
    [
        ".......MMMM.........",
        ".....MMMMMMMMM......",
        "....MmPPPPPPPMm.....",
        "...MmPPPPPPPPPMm....",
        "..kMPPQkPPPkQPPMk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPpppPPPPPPk...",
        "...kPPPPpPPPPPPk....",
        "....kkPPPPPPPkkk....",
        "....kBBBBBBBBBk.....",
        "...kBBBBBBBBBBBk....",
        "..kBBTBBBBBBBTBBk...",
        "..kBBBBBBBBBBBBBk...",
        "..kBBBBBBBBBBBBBk...",
        "..kBBBBBBBBBBBBBk...",
        "...kBBBBBBBBBBBk....",
        "..kNNNk.....kNNNk...",
        "..kNNNk.....kNNNk...",
        ".kXXXXk.....kXXXXk..",
    ],
    [
        ".......MMMM.........",
        ".....MMMMMMMMM......",
        "....MmPPPPPPPMm.....",
        "...MmPPPPPPPPPMm....",
        "..kMPPQkPPPkQPPMk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPpppPPPPPPk...",
        "...kPPPPpPPPPPPk....",
        "....kkPPPPPPPkkk....",
        "....kBBBBBBBBBk.....",
        "...kBBBBBBBBBBBk....",
        "..kBBTBBBBBBBTBBk...",
        "..kBBBBBBBBBBBBBk...",
        "..kBBBBBBBBBBBBBk...",
        "..kBBBBBBBBBBBBBk...",
        "...kBBBBBBBBBBBk....",
        "...kNNNk..kNNNk.....",
        "..kXXXXk..kXXXXk....",
        "..kXXXXk..kXXXXk....",
    ],
]

# ── Jugador (Skin 2: Rojo/Rubio) ─────────────────────────────────────────────
PLAYER_FRAMES_2 = [
    [
        ".......YYYY.........",
        ".....YYYYYYYYY......",
        "....YyPPPPPPPYy.....",
        "...YyPPPPPPPPPYy....",
        "..kYPPQkPPPkQPPYk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPpppPPPPPPk...",
        "...kPPPPpPPPPPPk....",
        "....kkPPPPPPPkkk....",
        "....krrrrrrrrrk.....",
        "...krrrrrrrrrrrk....",
        "..krrRrrrrrrrRrrk...",
        "..krrrrrrrrrrrrrk...",
        "..krrrrrrrrrrrrrk...",
        "..krrrrrrrrrrrrrk...",
        "...krrrrrrrrrrrk....",
        "..kNNNk.....kNNNk...",
        "..kNNNk.....kNNNk...",
        ".kXXXXk.....kXXXXk..",
    ],
    [
        ".......YYYY.........",
        ".....YYYYYYYYY......",
        "....YyPPPPPPPYy.....",
        "...YyPPPPPPPPPYy....",
        "..kYPPQkPPPkQPPYk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPpppPPPPPPk...",
        "...kPPPPpPPPPPPk....",
        "....kkPPPPPPPkkk....",
        "....krrrrrrrrrk.....",
        "...krrrrrrrrrrrk....",
        "..krrRrrrrrrrRrrk...",
        "..krrrrrrrrrrrrrk...",
        "..krrrrrrrrrrrrrk...",
        "..krrrrrrrrrrrrrk...",
        "...krrrrrrrrrrrk....",
        "...kNNNk..kNNNk.....",
        "..kXXXXk..kXXXXk....",
        "..kXXXXk..kXXXXk....",
    ],
]

# ── Jugador (Skin 3: Táctico/Negro) ──────────────────────────────────────────
PLAYER_FRAMES_3 = [
    [
        ".......nnnn.........",
        ".....nnnnnnnnn......",
        "....nnPPPPPPPnn.....",
        "...nnPPPPPPPPPnn....",
        "..knPPQkPPPkQPPnk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPpppPPPPPPk...",
        "...kPPPPpPPPPPPk....",
        "....kkPPPPPPPkkk....",
        "....knnnnnnnnnk.....",
        "...knnnnnnnnnnnk....",
        "..knnNnnnnnnnNnnk...",
        "..knnnnnnnnnnnnnk...",
        "..knnnnnnnnnnnnnk...",
        "..knnnnnnnnnnnnnk...",
        "...knnnnnnnnnnnk....",
        "..kNNNk.....kNNNk...",
        "..kNNNk.....kNNNk...",
        ".kXXXXk.....kXXXXk..",
    ],
    [
        ".......nnnn.........",
        ".....nnnnnnnnn......",
        "....nnPPPPPPPnn.....",
        "...nnPPPPPPPPPnn....",
        "..knPPQkPPPkQPPnk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPPPPPPPPPPk...",
        "..kPPPPpppPPPPPPk...",
        "...kPPPPpPPPPPPk....",
        "....kkPPPPPPPkkk....",
        "....knnnnnnnnnk.....",
        "...knnnnnnnnnnnk....",
        "..knnNnnnnnnnNnnk...",
        "..knnnnnnnnnnnnnk...",
        "..knnnnnnnnnnnnnk...",
        "..knnnnnnnnnnnnnk...",
        "...knnnnnnnnnnnk....",
        "...kNNNk..kNNNk.....",
        "..kXXXXk..kXXXXk....",
        "..kXXXXk..kXXXXk....",
    ],
]


# ── Pistola (sprite separado, apunta a la derecha) ────────────────────────
GUN_PISTOL = [
    "......",
    ".aaaa.",
    "aAAAA.",
    "aAAAA.",
    ".aaaa.",
    "......",
]

GUN_SHOTGUN = [
    "..mmmm..",
    ".mMMMM..",
    "mMMMMMaa",
    "mMMMMMAA",
    ".mMMMM..",
    "..mmmm..",
]

GUN_RIFLE = [
    "...mmmmm....",
    "..mMMMMMaaa.",
    ".mMMMMMMAAAA",
    ".mMMMMMMAAAA",
    "..mMMMMMaaa.",
    "...mmmmm....",
]

# ── Zombie normal (vista top-down, brazos extendidos hacia adelante) ────────
ZOMBIE_FRAMES = [
    [
        ".......qqqq.........",
        ".....qqZZZZZqq......",
        "....qZZZZZZZZZq.....",
        "...qZZZZZZZZZZZq....",
        "..kZZZkkkZZkkkZZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "..kZZZZzzzZZZZZZZk..",
        "...kZZZZzZZZZZZZk...",
        "....kkZZZZZZZkkkk...",
        "..kzzkGGGGGGGGGzzk..",  # brazos extendidos
        ".kzzZZGGGGGGGGGZZzzk.",
        "kzzZZZGGGGGGGGGZZZzzk",
        ".kzZZZGGGGGGGGGZZZzk.",
        "..kGGGGGGGGGGGGGGGk..",
        "..kGGGGGGGGGGGGGGGk..",
        "...kGGGGGGGGGGGGGk...",
        "..kGGGk.....kGGGk...",
        "..kGGGk.....kGGGk...",
        ".kXXXXk.....kXXXXk..",
    ],
    [
        ".......qqqq.........",
        ".....qqZZZZZqq......",
        "....qZZZZZZZZZq.....",
        "...qZZZZZZZZZZZq....",
        "..kZZZkkkZZkkkZZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "..kZZZZzzzZZZZZZZk..",
        "...kZZZZzZZZZZZZk...",
        "....kkZZZZZZZkkkk...",
        "..kzzkGGGGGGGGGzzk..",
        ".kzzZZGGGGGGGGGZZzzk.",
        "kzzZZZGGGGGGGGGZZZzzk",
        ".kzZZZGGGGGGGGGZZZzk.",
        "..kGGGGGGGGGGGGGGGk..",
        "..kGGGGGGGGGGGGGGGk..",
        "...kGGGGGGGGGGGGGk...",
        "...kGGGk..kGGGk.....",
        "..kXXXXk..kXXXXk....",
        "..kXXXXk..kXXXXk....",
    ],
]

# ── Zombie rápido (morado, más esbelto) ────────────────────────────────────
ZOMBIE_FAST_FRAMES = [
    [
        "......qqqq..........",
        "....qqZZZZZqq.......",
        "...qZZZZZZZZZq......",
        "..qZZZZZZZZZZZq.....",
        ".kZZZkkkZZkkkZZZk...",
        ".kZZZZZZZZZZZZZZk...",
        ".kZZZZZZZZZZZZZZk...",
        ".kZZZZzzzZZZZZZZk...",
        "..kZZZZzZZZZZZZk....",
        "...kkZZZZZZZkkkk....",
        ".kzzzzUUUUUUUzzzzk..",  # brazos muy extendidos (veloz)
        "kzzZZZUUUUUUUZZZzzk.",
        "kzZZZZUUUUUUUZZZZzk.",
        "kzzZZZUUUUUUUZZZzzk.",
        ".kUUUUUUUUUUUUUUUk..",
        ".kUUUUUUUUUUUUUUUk..",
        "..kUUUUUUUUUUUUUk...",
        "..kUUUk.....kUUUk...",
        "...kUUk......kUUk...",
        "..kXXXk......kXXXk..",
    ],
    [
        "......qqqq..........",
        "....qqZZZZZqq.......",
        "...qZZZZZZZZZq......",
        "..qZZZZZZZZZZZq.....",
        ".kZZZkkkZZkkkZZZk...",
        ".kZZZZZZZZZZZZZZk...",
        ".kZZZZZZZZZZZZZZk...",
        ".kZZZZzzzZZZZZZZk...",
        "..kZZZZzZZZZZZZk....",
        "...kkZZZZZZZkkkk....",
        ".kzzzzUUUUUUUzzzzk..",
        "kzzZZZUUUUUUUZZZzzk.",
        "kzZZZZUUUUUUUZZZZzk.",
        "kzzZZZUUUUUUUZZZzzk.",
        ".kUUUUUUUUUUUUUUUk..",
        ".kUUUUUUUUUUUUUUUk..",
        "..kUUUUUUUUUUUUUk...",
        "...kUUUk..kUUUk.....",
        "..kXXXXk..kXXXXk....",
        "..kXXXXk..kXXXXk....",
    ],
]

# ── Zombie tanque (ancho, gris) ─────────────────────────────────────────────
ZOMBIE_TANK_FRAMES = [
    [
        ".......qqqq.........",
        ".....qqZZZZZqq......",
        "....qZZZZZZZZZq.....",
        "...qZZZZZZZZZZZq....",
        "..kZZZkkkkZkkkkZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "..kZZRRZZZZZZRRZZk..",  # ojos rojos
        "..kZZZZZZZZZZZZZZk..",
        "...kZZZZzzzZZZZZZk...",
        "....kkZZZZZZZkkk....",
        "kzzzzDDDDDDDDDzzzzk.",  # brazos gruesos
        "kZZZZDDDDDDDDDZZZZk.",
        "kZZZZDDDDDDDDDZZZZk.",
        "kZZZZDDDDDDDDDZZZZk.",
        "kzzzzDDDDDDDDDzzzzk.",
        "..kDDDDDDDDDDDDDDk..",
        "..kDDDDDDDDDDDDDDk..",
        "...kDDDDDDDDDDDDk...",
        "..kDDDk.....kDDDk...",
        ".kXXXXXk...kXXXXXk..",
    ],
    [
        ".......qqqq.........",
        ".....qqZZZZZqq......",
        "....qZZZZZZZZZq.....",
        "...qZZZZZZZZZZZq....",
        "..kZZZkkkkZkkkkZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "..kZZRRZZZZZZRRZZk..",
        "..kZZZZZZZZZZZZZZk..",
        "...kZZZZzzzZZZZZZk...",
        "....kkZZZZZZZkkk....",
        "kzzzzDDDDDDDDDzzzzk.",
        "kZZZZDDDDDDDDDZZZZk.",
        "kZZZZDDDDDDDDDZZZZk.",
        "kZZZZDDDDDDDDDZZZZk.",
        "kzzzzDDDDDDDDDzzzzk.",
        "..kDDDDDDDDDDDDDDk..",
        "..kDDDDDDDDDDDDDDk..",
        "...kDDDDDDDDDDDDk...",
        "...kDDDk..kDDDk.....",
        ".kXXXXXk...kXXXXXk..",
    ],
]

# ── Moneda (16x16) ──────────────────────────────────────────────────────────
COIN_GRID = [
    "......OOoo......",
    "....OCCCCCOo....",
    "...OCCCCCCCCo...",
    "..OCCCkkkCCCCo..",
    ".OCCCkkkkkCCCCo.",
    ".OCCCkkkkkCCCCo.",
    "OCCCCkkkkkCCCCCo",
    "OCCCCkkkkkCCCCCo",
    "OCCCCkkkkkCCCCCo",
    ".OCCCkkkkkCCCCo.",
    ".OCCCkkkkkCCCCo.",
    "..OCCCkkkCCCCo..",
    "...OCCCCCCCCo...",
    "....OCCCCCOo....",
    "......OOoo......",
    "................",
]

# ── Corazón (16x16) ─────────────────────────────────────────────────────────
HEART_GRID = [
    "................",
    "..kHHkk.kHHkk...",
    ".kHHHHHkHHHHHk..",
    ".kIHHHHHHHHHHk..",
    ".kHHHHHHHHHHHk..",
    ".kHHHHHHHHHHHk..",
    "..kHHHHHHHHHk...",
    "...kHHHHHHHk....",
    "....kHHHHHk.....",
    ".....kHHHk......",
    "......kHk.......",
    ".......k........",
    "................",
    "................",
    "................",
    "................",
]

# ── Bala (8x8) ──────────────────────────────────────────────────────────────
BULLET_GRID = [
    "........",
    "..kYYk..",
    ".kYYYAk.",
    "kYYYYAAk",
    "kYYYYAAk",
    ".kyyyAk.",
    "..kaakk.",
    "........",
]

# ── Íconos de arma HUD (32x8) ───────────────────────────────────────────────
PISTOL_HUD = [
    "................................",
    "........aaaaaaaaaa..............",
    "......aaAAAAAAAAAAAAAa..........",
    "......aAAAAAAAAAAAAAAAAa........",
    "......aaAAAAAAAAAAAAAa..........",
    "........aaaaaaaaaa..............",
    "................................",
    "................................",
]

SHOTGUN_HUD = [
    "................................",
    "....mmmmmmmmaaaaaaaaaa..........",
    "...mMMMMMMMMAAAAAAAAAAAAAa......",
    "...mMMMMMMMMAAAAAAAAAAAAAAa.....",
    "...mMMMMMMMMAAAAAAAAAAAAAa......",
    "....mmmmmmmmaaaaaaaaaa..........",
    "................................",
    "................................",
]

RIFLE_HUD = [
    "................................",
    "....mmmmmmmmmmmaaaaaaaaaaaaa....",
    "...mMMMMMMMMMMMAAAAAAAAAAAAAAa..",
    "...mMMMMMMMMMMMAAAAAAAAAAAAAAAAa",
    "...mMMMMMMMMMMMAAAAAAAAAAAAAAa..",
    "....mmmmmmmmmmmaaaaaaaaaaaaa....",
    "................................",
    "................................",
]

# ── Metralleta (pistola manejada con ambas manos) ─────────────────────────
GUN_METRALLETA = [
    "......mm..",
    ".....mMmm.",
    "....mMMMMm",
    "...mMMMMMMm",
    "...mMMMMMMm",
    "....mMMMMm",
    ".....mMmm.",
    "......mm..",
]

# ── Metralleta HUD (32x8) ────────────────────────────────────────────────
METRALLETA_HUD = [
    "................................",
    "..mmmmmmmmmmmmaaaaaaaaaaaaaaaa..",
    ".mMMMMMMMMMMMAAAAAAAAAAAAAAAAAA.",
    ".mMMMMMMMMMMMAAAAAAAAAAAAAAAAAA.",
    ".mMMMmMMMMMMMAAAAAAAAAAAAAAAAAA.",
    "..mmmmmmmmmmmmaaaaaaaaaaaaaaaa..",
    "................................",
    "................................",
]

# ============================================================
#  ICONOS DE POWER-UPS (16x16)
# ============================================================

# Escudo (azul)
DROP_ESCUDO = [
    "....kSSSSSk.....",
    "...kSSSSSSSk....",
    "..kSSWWWWSSSSk..",
    "..kSSSSSSSSSk...",
    "..kSSWWSSSSSk...",
    "..kSSSSSSSSSk...",
    "...kSSSSSSSSk...",
    "....kSSSSSSk....",
    ".....kSSSSk.....",
    "......kSSk......",
    ".......kk.......",
    "................",
    "................",
    "................",
    "................",
    "................",
]

# Velocidad (rayo verde)
DROP_VELOCIDAD = [
    "........FFF.....",
    ".......FFFF.....",
    "......FFFFF.....",
    ".....FFFFFF.....",
    "....FFFFFFFF....",
    "....fffFFFFF....",
    ".....FFFF.......",
    "......FFF.......",
    ".......FF.......",
    "........F.......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

# Fuerza (estrella roja)
DROP_FUERZA = [
    "................",
    ".....LlLlL......",
    "....LLLLLLL.....",
    "...LLLLLLLLL....",
    "....LLLLLLL.....",
    "...LLLLLLLLL....",
    "....LLLLLLL.....",
    ".....LlLlL......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

# Munión (bala brillante)
DROP_MUNICION = [
    "....JJJJ.JJJ....",
    "...JJJJJJJJJj...",
    "...JJJJJJJJJj...",
    "...JJJJJJJJJj...",
    "...JJJJJJJJJj...",
    "...JJJJJJJJJj...",
    "....JJJJJJJj....",
    "....jjjjjjjj....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

# ===========================================================================
#  SpriteManager
# ===========================================================================
class SpriteManager:
    def __init__(self, scale=3):
        self.scale = scale

        # Jugador — tres skins (con dos frames de animación cada uno)
        self.player_skins = [
            [make_surface(f, scale) for f in PLAYER_FRAMES],
            [make_surface(f, scale) for f in PLAYER_FRAMES_2],
            [make_surface(f, scale) for f in PLAYER_FRAMES_3],
        ]

        # Armas separadas (se rotan independientemente)
        self.gun_pistol    = make_surface(GUN_PISTOL,    scale)
        self.gun_shotgun   = make_surface(GUN_SHOTGUN,   scale)
        self.gun_rifle     = make_surface(GUN_RIFLE,     scale)
        self.gun_metralleta = make_surface(GUN_METRALLETA, scale)

        # Zombies
        self.zombie_frames      = [make_surface(f, scale) for f in ZOMBIE_FRAMES]
        self.zombie_fast_frames = [make_surface(f, scale) for f in ZOMBIE_FAST_FRAMES]
        self.zombie_tank_frames = [make_surface(f, scale + 1) for f in ZOMBIE_TANK_FRAMES]

        # Items base
        self.coin   = make_surface(COIN_GRID,  scale - 1)
        self.heart  = make_surface(HEART_GRID, scale - 1)
        self.bullet = make_surface(BULLET_GRID, 2)

        # Power-up drops
        self.escudo    = make_surface(DROP_ESCUDO,    scale - 1)
        self.velocidad = make_surface(DROP_VELOCIDAD, scale - 1)
        self.fuerza    = make_surface(DROP_FUERZA,    scale - 1)
        self.municion  = make_surface(DROP_MUNICION,  scale - 1)

        # HUD
        self.pistol      = make_surface(PISTOL_HUD,      2)
        self.shotgun     = make_surface(SHOTGUN_HUD,     2)
        self.rifle       = make_surface(RIFLE_HUD,       2)
        self.metralleta  = make_surface(METRALLETA_HUD,  2)
