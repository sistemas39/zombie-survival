"""
fondo.py — Generación procedural de mapas post-apocalípticos (top-down).
5 mapas distintos; cada partida elige uno aleatoriamente (o por seed).
Se pre-renderiza una vez al inicio para no afectar el rendimiento.
"""
import pygame
import random
import math


# ============================================================
#  UTILIDADES INTERNAS
# ============================================================

def _ruido_base(surf, ancho, alto, color_base, variacion=8, cant=3500):
    """Rellena la superficie con ruido granular sutil encima de un color base."""
    r0, g0, b0 = color_base
    surf.fill(color_base)
    for _ in range(cant):
        x = random.randint(0, ancho - 1)
        y = random.randint(0, alto - 1)
        v = random.randint(-variacion, variacion)
        surf.set_at((x, y), (
            max(0, min(255, r0 + v)),
            max(0, min(255, g0 + v)),
            max(0, min(255, b0 + v)),
        ))


def _grieta(surf, cx, cy, pasos=6, color=(20, 20, 22), grosor=1):
    """Dibuja una grieta fractal desde (cx, cy)."""
    for _ in range(pasos):
        dx = random.randint(-16, 16)
        dy = random.randint(-16, 16)
        pygame.draw.line(surf, color, (cx, cy), (cx + dx, cy + dy), grosor)
        cx += dx // 2
        cy += dy // 2


def _charco(surf, x, y, rx=18, ry=11, color=(80, 5, 10, 100)):
    s = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, color, (0, 0, rx * 2, ry * 2))
    surf.blit(s, (x - rx, y - ry))


def _escombro(surf, x, y, w, h, color, angulo=0):
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    tmp.fill(color)
    # Borde oscuro para volumen
    pygame.draw.rect(tmp, (max(0, color[0] - 20), max(0, color[1] - 20), max(0, color[2] - 20)), (0, 0, w, h), 1)
    rot = pygame.transform.rotate(tmp, angulo)
    surf.blit(rot, (x - rot.get_width() // 2, y - rot.get_height() // 2))


def _coche(surf, cx, cy, ang, carroceria=(55, 55, 62)):
    tmp = pygame.Surface((64, 32), pygame.SRCALPHA)
    pygame.draw.rect(tmp, carroceria, (0, 0, 64, 32), border_radius=4)
    pygame.draw.rect(tmp, (12, 12, 14), (0, 0, 64, 32), 2, border_radius=4)
    # Parabrisas roto
    pygame.draw.rect(tmp, (28, 30, 38), (10, 5, 20, 12))
    pygame.draw.line(tmp, (12, 12, 14), (10, 5), (22, 17), 1)
    pygame.draw.line(tmp, (12, 12, 14), (24, 5), (14, 15), 1)
    # Capó — tono algo más claro
    pygame.draw.rect(tmp, (max(0, carroceria[0] - 10), max(0, carroceria[1] - 10), max(0, carroceria[2] - 8)),
                     (34, 6, 22, 20), border_radius=2)
    # Ruedas
    for wx, wy in [(2, 2), (50, 2), (2, 22), (50, 22)]:
        pygame.draw.ellipse(tmp, (16, 16, 18), (wx, wy, 12, 8))
    # Mancha aceite
    oil = pygame.Surface((52, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(oil, (10, 10, 10, 80), (0, 0, 52, 18))
    surf.blit(oil, (cx + 6, cy + 28))
    rot = pygame.transform.rotate(tmp, ang)
    surf.blit(rot, (cx - rot.get_width() // 2, cy - rot.get_height() // 2))


def _arbol(surf, x, y, radio=22, color_tronco=(55, 35, 12), color_copa=(30, 90, 25)):
    """Árbol top-down: tronco pequeño + copa circular con variación."""
    # Copa (círculo verde oscuro)
    s = pygame.Surface((radio * 2 + 8, radio * 2 + 8), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color_copa, 240), (radio + 4, radio + 4), radio)
    # Sombra interior
    pygame.draw.circle(s, (max(0, color_copa[0] - 15), max(0, color_copa[1] - 20), max(0, color_copa[2] - 10), 180),
                       (radio + 4, radio + 6), radio - 6)
    # Brillo
    pygame.draw.circle(s, (min(255, color_copa[0] + 30), min(255, color_copa[1] + 40), min(255, color_copa[2] + 15), 120),
                       (radio, radio), radio // 3)
    surf.blit(s, (x - radio - 4, y - radio - 4))
    # Tronco
    pygame.draw.circle(surf, color_tronco, (x, y), 5)
    pygame.draw.circle(surf, (35, 20, 5), (x, y), 5, 2)


def _barril(surf, x, y, color=(60, 90, 55)):
    """Barril metálico top-down."""
    pygame.draw.circle(surf, color, (x, y), 10)
    pygame.draw.circle(surf, (max(0, color[0] - 20), max(0, color[1] - 20), max(0, color[2] - 20)), (x, y), 10, 2)
    pygame.draw.line(surf, (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30)),
                     (x - 8, y - 4), (x + 8, y - 4), 2)
    pygame.draw.line(surf, (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30)),
                     (x - 8, y + 4), (x + 8, y + 4), 2)


def _roca(surf, x, y, tamaño=14, color=(75, 72, 65)):
    pts = []
    for i in range(7):
        ang = math.radians(i * (360 / 7) + random.uniform(-15, 15))
        r = tamaño + random.randint(-4, 4)
        pts.append((x + int(math.cos(ang) * r), y + int(math.sin(ang) * r)))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, (max(0, color[0] - 25), max(0, color[1] - 25), max(0, color[2] - 25)), pts, 2)
    # Línea de luz
    pygame.draw.line(surf, (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)),
                     (x - tamaño // 3, y - tamaño // 3), (x + tamaño // 4, y - tamaño // 4), 1)


def _caja(surf, x, y, w=22, h=20, color=(100, 70, 30), ang=0):
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    tmp.fill(color)
    # Cruz de madera
    sombra = (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30))
    pygame.draw.line(tmp, sombra, (0, h // 2), (w, h // 2), 2)
    pygame.draw.line(tmp, sombra, (w // 2, 0), (w // 2, h), 2)
    pygame.draw.rect(tmp, sombra, (0, 0, w, h), 2)
    rot = pygame.transform.rotate(tmp, ang)
    surf.blit(rot, (x - rot.get_width() // 2, y - rot.get_height() // 2))


# ============================================================
#  MAPA 1 — CIUDAD EN RUINAS (original mejorado)
# ============================================================

def _mapa_ciudad(ancho, alto):
    surf = pygame.Surface((ancho, alto))
    _ruido_base(surf, ancho, alto, (30, 30, 34), variacion=7)

    # Aceras
    gris = (58, 58, 65)
    for r in [pygame.Rect(0, 0, ancho, 30), pygame.Rect(0, alto - 30, ancho, 30),
              pygame.Rect(0, 0, 30, alto), pygame.Rect(ancho - 30, 0, 30, alto)]:
        pygame.draw.rect(surf, gris, r)
        pygame.draw.rect(surf, (42, 42, 48), r, 2)

    # Carriles centrales
    amarillo = (175, 150, 20)
    for x in range(0, ancho, 85):
        pygame.draw.rect(surf, amarillo, (x, alto // 2 - 2, 55, 5))
    for y in range(0, alto, 85):
        pygame.draw.rect(surf, amarillo, (ancho // 2 - 2, y, 5, 55))
    # Carriles secundarios
    for frac in [1/3, 2/3]:
        pygame.draw.line(surf, (65, 65, 70), (0, int(alto * frac)), (ancho, int(alto * frac)), 2)
        pygame.draw.line(surf, (65, 65, 70), (int(ancho * frac), 0), (int(ancho * frac), alto), 2)

    # Edificios en esquinas/bordes — más oscuros y con contorno visible
    edificios = [
        (0, 0, 165, 135), (ancho - 165, 0, 165, 135),
        (0, alto - 135, 165, 135), (ancho - 165, alto - 135, 165, 135),
        (295, 0, 130, 85), (570, 0, 130, 85),
        (295, alto - 85, 130, 85), (570, alto - 85, 130, 85),
    ]
    colores_ed = [(28, 32, 40), (35, 28, 28), (30, 35, 30), (40, 32, 25)]
    for bx, by, bw, bh in edificios:
        c = random.choice(colores_ed)
        pygame.draw.rect(surf, c, (bx, by, bw, bh))
        # Ventanas
        for wy in range(by + 14, by + bh - 8, 20):
            for wx in range(bx + 12, bx + bw - 8, 20):
                wc = (62, 52, 18) if random.random() < 0.15 else (18, 18, 22)
                pygame.draw.rect(surf, wc, (wx, wy, 10, 8))
                pygame.draw.rect(surf, (10, 10, 12), (wx, wy, 10, 8), 1)
        # Grietas en fachada
        for _ in range(random.randint(4, 9)):
            _grieta(surf, random.randint(bx, bx + bw - 1), random.randint(by, by + bh - 1),
                    color=(12, 12, 14))
        pygame.draw.rect(surf, (10, 10, 12), (bx, by, bw, bh), 3)

    # Charcos de sangre
    for _ in range(18):
        _charco(surf, random.randint(60, ancho - 60), random.randint(60, alto - 60),
                random.randint(10, 30), random.randint(6, 18))

    # Escombros de asfalto y ladrillos
    for _ in range(60):
        ex, ey = random.randint(30, ancho - 30), random.randint(30, alto - 30)
        c = random.randint(32, 58)
        _escombro(surf, ex, ey, random.randint(5, 20), random.randint(4, 12),
                  (c, c - 3, max(0, c - 8)), random.uniform(0, 90))

    # Grietas en asfalto
    for _ in range(40):
        _grieta(surf, random.randint(40, ancho - 40), random.randint(40, alto - 40),
                pasos=random.randint(4, 10))

    # Coches abandonados
    coches = [
        (170, 45, 5, (58, 52, 48)), (720, 62, 18, (42, 52, 48)),
        (130, alto - 75, -8, (55, 45, 38)), (670, alto - 88, 7, (48, 55, 45)),
        (ancho // 2 - 65, 40, 0, (50, 50, 60)),
    ]
    for cx, cy, ang, col in coches:
        _coche(surf, cx, cy, ang, col)

    # Barriles oxidados
    for bx, by in [(210, 80), (760, 100), (180, alto - 90), (700, alto - 80)]:
        _barril(surf, bx, by, (80, 45, 20))

    return surf


# ============================================================
#  MAPA 2 — BOSQUE OSCURO
# ============================================================

def _mapa_bosque(ancho, alto):
    surf = pygame.Surface((ancho, alto))
    # Base: tierra oscura
    _ruido_base(surf, ancho, alto, (28, 38, 22), variacion=10, cant=4000)

    # Parches de hierba con distinción clara
    for _ in range(120):
        gx = random.randint(0, ancho - 1)
        gy = random.randint(0, alto - 1)
        gr = random.randint(4, 22)
        gc = random.randint(28, 55)
        s = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (max(0, gc - 10), gc + random.randint(0, 20), max(0, gc - 15), 130), (gr, gr), gr)
        surf.blit(s, (gx - gr, gy - gr))

    # Caminos de tierra
    pygame.draw.line(surf, (48, 36, 20), (0, alto // 2), (ancho, alto // 2), 60)
    pygame.draw.line(surf, (48, 36, 20), (ancho // 2, 0), (ancho // 2, alto), 60)
    # Bordes del camino (líneas de hierba aplastada)
    for off in [-30, 30]:
        pygame.draw.line(surf, (35, 48, 22), (0, alto // 2 + off), (ancho, alto // 2 + off), 2)
        pygame.draw.line(surf, (35, 48, 22), (ancho // 2 + off, 0), (ancho // 2 + off, alto), 2)
    # Textura de tierra en camino
    for _ in range(200):
        px = random.randint(0, ancho - 1)
        py = random.randint(int(alto * 0.35), int(alto * 0.65))
        v = random.randint(-5, 5)
        surf.set_at((px, py), (48 + v, 36 + v, 20 + v))
    for _ in range(200):
        px = random.randint(int(ancho * 0.35), int(ancho * 0.65))
        py = random.randint(0, alto - 1)
        v = random.randint(-5, 5)
        surf.set_at((px, py), (48 + v, 36 + v, 20 + v))

    # Árboles (MUCHOS, bien visibles, verde oscuro)
    zonas_arboles = []
    # Zona izquierda y derecha
    for _ in range(35):
        tx = random.choice([random.randint(0, ancho // 2 - 80), random.randint(ancho // 2 + 80, ancho)])
        ty = random.randint(0, alto)
        radio = random.randint(18, 30)
        zonas_arboles.append((tx, ty, radio))
    # Esquinas con árboles densos
    for _ in range(25):
        qx = random.choice([random.randint(0, 180), random.randint(ancho - 180, ancho)])
        qy = random.choice([random.randint(0, 160), random.randint(alto - 160, alto)])
        zonas_arboles.append((qx, qy, random.randint(20, 32)))

    # Primero sombras de copas
    for tx, ty, radio in zonas_arboles:
        s = pygame.Surface((radio * 2 + 10, radio * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 0, 0, 60), (radio + 8, radio + 8), radio)
        surf.blit(s, (tx - radio - 2, ty - radio + 4))

    # Luego copas
    for tx, ty, radio in zonas_arboles:
        verde = (25 + random.randint(0, 20), 70 + random.randint(0, 35), 18 + random.randint(0, 15))
        _arbol(surf, tx, ty, radio, color_copa=verde)

    # Charcos de barro / agua estancada
    for _ in range(12):
        _charco(surf, random.randint(60, ancho - 60), random.randint(60, alto - 60),
                random.randint(12, 35), random.randint(8, 20), (30, 50, 70, 120))

    # Rocas
    for _ in range(30):
        _roca(surf, random.randint(30, ancho - 30), random.randint(30, alto - 30),
              random.randint(8, 18), (68, 65, 55))

    # Sangre sobre tierra
    for _ in range(10):
        _charco(surf, random.randint(60, ancho - 60), random.randint(60, alto - 60),
                random.randint(8, 22), random.randint(5, 14), (85, 5, 8, 100))

    return surf


# ============================================================
#  MAPA 3 — ALMACÉN ABANDONADO
# ============================================================

def _mapa_almacen(ancho, alto):
    surf = pygame.Surface((ancho, alto))
    # Suelo de concreto rayado
    _ruido_base(surf, ancho, alto, (38, 38, 42), variacion=5, cant=2500)

    # Líneas amarillas de seguridad industrial (muy visibles)
    amarillo = (210, 175, 0)
    negro = (20, 20, 22)
    # Franjas de seguridad en bordes
    for i in range(0, ancho, 40):
        if (i // 40) % 2 == 0:
            pygame.draw.rect(surf, amarillo, (i, 0, 20, 18))
            pygame.draw.rect(surf, amarillo, (i, alto - 18, 20, 18))
    for i in range(0, alto, 40):
        if (i // 40) % 2 == 0:
            pygame.draw.rect(surf, amarillo, (0, i, 18, 20))
            pygame.draw.rect(surf, amarillo, (ancho - 18, i, 18, 20))
    # Borde negro
    pygame.draw.rect(surf, negro, (0, 0, ancho, alto), 3)

    # Estantes / paredes internas (rectángulos oscuros marcados)
    estantes = [
        (60, 60, 180, 22), (60, 110, 180, 22),
        (ancho - 240, 60, 180, 22), (ancho - 240, 110, 180, 22),
        (60, alto - 82, 180, 22), (60, alto - 132, 180, 22),
        (ancho - 240, alto - 82, 180, 22), (ancho - 240, alto - 132, 180, 22),
        # Estantes centrales horizontales
        (280, 160, 22, 130), (ancho - 302, 160, 22, 130),
        (280, alto - 290, 22, 130), (ancho - 302, alto - 290, 22, 130),
    ]
    for ex, ey, ew, eh in estantes:
        pygame.draw.rect(surf, (25, 25, 28), (ex, ey, ew, eh))
        pygame.draw.rect(surf, (60, 55, 40), (ex, ey, ew, eh), 3)  # borde amarronado visible

    # Cajas apiladas (MUY distintas, madera clara con cruz)
    posiciones_cajas = [
        (90, 85), (115, 85), (90, 115),
        (ancho - 120, 85), (ancho - 95, 85), (ancho - 120, 115),
        (90, alto - 110), (115, alto - 110),
        (ancho - 120, alto - 110), (ancho - 95, alto - 110),
        (ancho // 2 - 50, alto // 2 - 30), (ancho // 2 + 30, alto // 2 - 30),
        (ancho // 2 - 50, alto // 2 + 30), (ancho // 2 + 30, alto // 2 + 30),
    ]
    for cx, cy in posiciones_cajas:
        col = (105 + random.randint(-10, 10), 72 + random.randint(-10, 10), 28 + random.randint(-5, 5))
        _caja(surf, cx, cy, random.randint(18, 26), random.randint(16, 24), col, random.uniform(-8, 8))

    # Barriles metálicos (verde/azul industrial)
    for bx, by, col in [
        (220, 80, (45, 80, 55)), (240, 80, (50, 75, 50)),
        (ancho - 260, 80, (45, 60, 85)), (ancho - 240, 80, (50, 65, 80)),
        (220, alto - 100, (80, 45, 30)), (ancho - 260, alto - 100, (80, 45, 30)),
        (ancho // 2 - 20, 55, (60, 80, 50)), (ancho // 2 + 20, 55, (60, 80, 50)),
    ]:
        _barril(surf, bx, by, col)

    # Grietas en concreto
    for _ in range(25):
        _grieta(surf, random.randint(30, ancho - 30), random.randint(30, alto - 30),
                pasos=random.randint(3, 7), color=(28, 28, 30))

    # Manchas de aceite (círculos oscuros sobre suelo)
    for _ in range(8):
        ox, oy = random.randint(60, ancho - 60), random.randint(60, alto - 60)
        s = pygame.Surface((60, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (10, 10, 14, 140), (0, 0, 60, 28))
        surf.blit(s, (ox - 30, oy - 14))

    # Sangre
    for _ in range(12):
        _charco(surf, random.randint(60, ancho - 60), random.randint(60, alto - 60),
                random.randint(8, 25), random.randint(5, 14))

    return surf


# ============================================================
#  MAPA 4 — DESIERTO POST-NUCLEAR
# ============================================================

def _mapa_desierto(ancho, alto):
    surf = pygame.Surface((ancho, alto))
    _ruido_base(surf, ancho, alto, (110, 85, 48), variacion=14, cant=5000)

    # Dunas: manchas de arena más clara
    for _ in range(80):
        dx = random.randint(0, ancho)
        dy = random.randint(0, alto)
        dr = random.randint(20, 70)
        s = pygame.Surface((dr * 2, dr * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (130 + random.randint(-10, 20), 100 + random.randint(-10, 15),
                                55 + random.randint(-8, 8), 80), (0, 0, dr * 2, dr * 2))
        surf.blit(s, (dx - dr, dy - dr))

    # Grietas áridas (muy visibles, más oscuras)
    for _ in range(50):
        _grieta(surf, random.randint(20, ancho - 20), random.randint(20, alto - 20),
                pasos=random.randint(5, 12), color=(75, 55, 25), grosor=1)

    # Ruinas de muros (rectángulos de adobe/piedra MUY distintos)
    muros = [
        (0, 0, 140, 110), (ancho - 140, 0, 140, 110),
        (0, alto - 110, 140, 110), (ancho - 140, alto - 110, 140, 110),
        (300, 0, 100, 55), (560, 0, 100, 55),
        (300, alto - 55, 100, 55), (560, alto - 55, 100, 55),
    ]
    for mx, my, mw, mh in muros:
        c = random.randint(85, 105)
        pygame.draw.rect(surf, (c, c - 15, c - 28), (mx, my, mw, mh))
        # Bloques de adobe
        for row in range(my, my + mh, 14):
            for col in range(mx + (row // 14 % 2) * 8, mx + mw, 22):
                pygame.draw.rect(surf, (c - 12, c - 25, c - 40),
                                 (col, row, 20, 12), 1)
        pygame.draw.rect(surf, (65, 45, 20), (mx, my, mw, mh), 3)

    # Rocas grandes (muy distintas sobre arena)
    for _ in range(22):
        _roca(surf, random.randint(30, ancho - 30), random.randint(30, alto - 30),
              random.randint(10, 25), (88, 80, 68))

    # Restos de vehículos (coches oxidados, color naranja-óxido)
    coches_des = [
        (200, 50, 10, (90, 50, 20)), (720, 55, -5, (85, 55, 18)),
        (160, alto - 70, 0, (95, 48, 15)), (700, alto - 80, 15, (80, 52, 20)),
    ]
    for cx, cy, ang, col in coches_des:
        _coche(surf, cx, cy, ang, col)

    # Barras y chatarra (barriles oxidados)
    for bx, by in [(260, 75), (690, 75), (260, alto - 90), (690, alto - 90),
                   (ancho // 2, 50), (ancho // 2, alto - 60)]:
        _barril(surf, bx, by, (90, 40, 15))

    # Sangre seca (más oscura, casi negra sobre arena)
    for _ in range(14):
        _charco(surf, random.randint(60, ancho - 60), random.randint(60, alto - 60),
                random.randint(8, 25), random.randint(5, 14), (55, 3, 5, 130))

    # Huesos / restos
    for _ in range(10):
        bx, by = random.randint(60, ancho - 60), random.randint(60, alto - 60)
        pygame.draw.line(surf, (200, 188, 155), (bx - 8, by), (bx + 8, by), 2)
        pygame.draw.line(surf, (200, 188, 155), (bx, by - 8), (bx, by + 8), 2)

    return surf


# ============================================================
#  MAPA 5 — BASE MILITAR
# ============================================================

def _mapa_militar(ancho, alto):
    surf = pygame.Surface((ancho, alto))
    _ruido_base(surf, ancho, alto, (35, 42, 30), variacion=8, cant=3000)

    # Suelo de grava militar (punteado oscuro)
    for _ in range(1500):
        px = random.randint(0, ancho - 1)
        py = random.randint(0, alto - 1)
        surf.set_at((px, py), (28, 34, 22))

    # Asfalto de base (calles internas más claras)
    pygame.draw.rect(surf, (42, 48, 36), (ancho // 2 - 35, 0, 70, alto))
    pygame.draw.rect(surf, (42, 48, 36), (0, alto // 2 - 35, ancho, 70))
    # Bordes de calle con línea blanca militar
    blanco_m = (160, 165, 140)
    for off in [-35, 35]:
        for x in range(0, ancho, 60):
            pygame.draw.rect(surf, blanco_m, (x, alto // 2 + off - 2, 38, 4))
        for y in range(0, alto, 60):
            pygame.draw.rect(surf, blanco_m, (ancho // 2 + off - 2, y, 4, 38))

    # Búnkers / bunkers (edificios sólidos militares)
    bunkers = [
        (0, 0, 170, 140), (ancho - 170, 0, 170, 140),
        (0, alto - 140, 170, 140), (ancho - 170, alto - 140, 170, 140),
        (310, 0, 120, 70), (530, 0, 120, 70),
        (310, alto - 70, 120, 70), (530, alto - 70, 120, 70),
    ]
    for bx, by, bw, bh in bunkers:
        c = random.randint(38, 52)
        pygame.draw.rect(surf, (c, c + 4, c - 5), (bx, by, bw, bh))
        # Detalles: ranuras de ventilación
        for ry in range(by + 10, by + bh - 8, 16):
            for rx in range(bx + 10, bx + bw - 8, 14):
                pygame.draw.rect(surf, (20, 24, 16), (rx, ry, 8, 4))
        # Refuerzos de concreto (líneas horizontales)
        for ry in range(by + 20, by + bh, 28):
            pygame.draw.line(surf, (max(0, c - 15), max(0, c - 12), max(0, c - 18)),
                             (bx, ry), (bx + bw, ry), 2)
        pygame.draw.rect(surf, (18, 22, 14), (bx, by, bw, bh), 4)

    # Sacos de arena / barricadas (MUY visibles — beige sobre verde)
    saco_cols = [(165, 148, 110), (150, 135, 100)]
    barricadas = [
        (170, 50), (200, 50), (170, 68),
        (ancho - 200, 50), (ancho - 170, 50), (ancho - 200, 68),
        (170, alto - 68), (200, alto - 68), (170, alto - 50),
        (ancho - 200, alto - 68), (ancho - 170, alto - 68),
    ]
    for bx, by in barricadas:
        col = random.choice(saco_cols)
        tmp = pygame.Surface((28, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, col, (0, 0, 28, 16))
        pygame.draw.ellipse(tmp, (max(0, col[0] - 30), max(0, col[1] - 30), max(0, col[2] - 30)),
                            (0, 0, 28, 16), 2)
        pygame.draw.line(tmp, (max(0, col[0] - 20), max(0, col[1] - 20), max(0, col[2] - 20)),
                         (4, 8), (24, 8), 1)
        surf.blit(tmp, (bx - 14, by - 8))

    # Vehículos militares (verde oliva)
    coches_mil = [
        (190, 55, 0, (42, 60, 28)), (720, 58, -10, (45, 62, 30)),
        (180, alto - 78, 5, (40, 58, 26)), (710, alto - 82, 12, (44, 60, 28)),
        (ancho // 2 - 50, 44, 0, (38, 55, 24)),
    ]
    for cx, cy, ang, col in coches_mil:
        _coche(surf, cx, cy, ang, col)

    # Barriles de combustible (verde militar)
    for bx, by in [(240, 80), (260, 80), (ancho - 260, 80), (ancho - 240, 80),
                   (240, alto - 100), (ancho - 260, alto - 100)]:
        _barril(surf, bx, by, (35, 58, 28))

    # Grietas y desgaste
    for _ in range(30):
        _grieta(surf, random.randint(30, ancho - 30), random.randint(30, alto - 30),
                pasos=random.randint(3, 7), color=(25, 30, 18))

    # Sangre
    for _ in range(16):
        _charco(surf, random.randint(60, ancho - 60), random.randint(60, alto - 60),
                random.randint(8, 26), random.randint(5, 16))

    # Señales militares en suelo
    for sx, sy in [(ancho // 2 - 15, 18), (ancho // 2 + 15, alto - 22)]:
        for i in range(4):
            c = (175, 45, 0) if i % 2 == 0 else (220, 195, 0)
            pygame.draw.rect(surf, c, (sx + i * 10, sy, 8, 7))

    return surf


# ============================================================
#  ENTRADA PÚBLICA
# ============================================================

MAPAS = {
    "ciudad":   _mapa_ciudad,
    "bosque":   _mapa_bosque,
    "almacen":  _mapa_almacen,
    "desierto": _mapa_desierto,
    "militar":  _mapa_militar,
}

NOMBRES_MAPA = {
    "ciudad":   "Ciudad en Ruinas",
    "bosque":   "Bosque Oscuro",
    "almacen":  "Almacén Abandonado",
    "desierto": "Desierto Nuclear",
    "militar":  "Base Militar",
}


def generar_fondo(ancho, alto, tipo=None, seed=None):
    """
    Genera y devuelve una Surface con el fondo del mapa.
    tipo: 'ciudad' | 'bosque' | 'almacen' | 'desierto' | 'militar' | None (aleatorio)
    """
    if tipo is None:
        tipo = random.choice(list(MAPAS.keys()))
    if seed is not None:
        random.seed(seed)
    else:
        random.seed(random.randint(0, 99999))

    print(f"🗺️  Mapa: {NOMBRES_MAPA.get(tipo, tipo)}")
    surf = MAPAS[tipo](ancho, alto)
    return surf, tipo
