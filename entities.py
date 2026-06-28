import pygame
import math
import random

# ──────────────────────────────────────────────────────────────────────────
#  JUGADOR
# ──────────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, x, y, sprite_manager, skin_index=0):
        self.x = x
        self.y = y
        self.sm = sprite_manager
        self.skin_index = skin_index

        sample = self.sm.player_skins[self.skin_index][0]
        self.w, self.h = sample.get_size()

        # Estadísticas
        self.vidas     = 3
        self.max_vidas = 3
        self.velocidad = 4.0
        self.monedas   = 0
        self.speed_upgrades = 0

        # Multiplicador de daño (se usa al crear balas)
        self.mult_daño = 1.0

        # Invulnerabilidad normal
        self.invulnerable    = False
        self.invul_duracion  = 1000
        self.invul_timer     = 0

        # ── Buffs temporales ──
        # Escudo (bloquea siguiente daño, dura 5s)
        self.escudo_activo  = False
        self.escudo_timer   = 0
        self.escudo_dur     = 5000
        self.escudo_ticks   = 0   # para animación del escudo

        # Velocidad extra (dura 6s)
        self.boost_vel      = False
        self.boost_vel_timer = 0
        self.boost_vel_dur  = 6000
        self.boost_vel_extra = 2.5

        # Fuerza (daño x1.7 durante 6s)
        self.boost_fuerza      = False
        self.boost_fuerza_timer = 0
        self.boost_fuerza_dur   = 6000

        # Animación de caminata
        self.anim_frame    = 0
        self.anim_timer    = 0
        self.anim_velocidad = 8
        self.caminando     = False

        # Dirección visual: solo flip izq/der — nunca boca abajo
        self.mirando_izq = False   # True = flip horizontal
        self.dir_arma    = 0.0     # ángulo del arma hacia el ratón

        # Bob
        self.bob_timer  = 0.0
        self.bob_offset = 0.0

        # Flash invulnerabilidad
        self.flash_tick = 0

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def recibir_daño(self, tiempo_actual):
        # Escudo bloquea el daño
        if self.escudo_activo:
            self.escudo_activo = False
            return False
        if not self.invulnerable:
            self.vidas -= 1
            self.invulnerable = True
            self.invul_timer = tiempo_actual
            return True
        return False

    def aplicar_buff(self, tipo, tiempo_actual):
        """Aplica un power-up recogido."""
        if tipo == 'escudo':
            self.escudo_activo  = True
            self.escudo_timer   = tiempo_actual
        elif tipo == 'velocidad':
            self.boost_vel      = True
            self.boost_vel_timer = tiempo_actual
        elif tipo == 'fuerza':
            self.boost_fuerza      = True
            self.boost_fuerza_timer = tiempo_actual
            self.mult_daño = 1.7

    def _actualizar_buffs(self, tiempo_actual):
        if self.escudo_activo:
            self.escudo_ticks += 1
            if tiempo_actual - self.escudo_timer > self.escudo_dur:
                self.escudo_activo = False
        if self.boost_vel:
            if tiempo_actual - self.boost_vel_timer > self.boost_vel_dur:
                self.boost_vel = False
        if self.boost_fuerza:
            if tiempo_actual - self.boost_fuerza_timer > self.boost_fuerza_dur:
                self.boost_fuerza = False
                self.mult_daño = 1.0

    def get_velocidad_real(self):
        extra = self.boost_vel_extra if self.boost_vel else 0.0
        return self.velocidad + extra

    def update(self, teclas, ancho, alto, tiempo_actual, pos_raton,
                joy_dx=0.0, joy_dy=0.0, joy_angulo=None):
        # Buffs
        self._actualizar_buffs(tiempo_actual)

        # ── Movimiento: teclado + stick izquierdo (se suman) ──
        dx, dy = 0.0, 0.0
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:  dx -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]: dx += 1
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:    dy -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:  dy += 1

        # Stick izquierdo del mando (suma al teclado)
        dx += joy_dx
        dy += joy_dy

        # Normalizar si supera magnitud 1
        mag = math.hypot(dx, dy)
        if mag > 1.0:
            dx /= mag
            dy /= mag

        self.caminando = (abs(dx) > 0.05 or abs(dy) > 0.05)

        # Actualizar dirección de flip basada en el movimiento horizontal
        if abs(dx) > 0.05:
            self.mirando_izq = dx < 0

        vel = self.get_velocidad_real()
        self.x += dx * vel
        self.y += dy * vel

        # Límites de pantalla
        margen = 30
        self.x = max(margen, min(ancho - margen, self.x))
        self.y = max(margen, min(alto - margen, self.y))

        # ── Dirección del arma ──
        if joy_angulo is not None:
            # Stick derecho del mando sobreescribe la punteria
            self.dir_arma = joy_angulo
            rad = math.radians(joy_angulo)
            self.mirando_izq = math.cos(rad) < 0
        else:
            # Ratón
            rx, ry = pos_raton
            self.dir_arma = math.degrees(math.atan2(-(ry - self.y), rx - self.x))
            if not self.caminando:
                self.mirando_izq = (rx < self.x)

        # ── Animación de caminata ──
        if self.caminando:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_velocidad:
                self.anim_timer = 0
                self.anim_frame = 1 - self.anim_frame
            self.bob_timer += 0.3
            self.bob_offset = math.sin(self.bob_timer) * 2.5
        else:
            self.bob_offset *= 0.7
            self.anim_frame = 0

        # ── Invulnerabilidad ──
        if self.invulnerable:
            self.flash_tick += 1
            if tiempo_actual - self.invul_timer > self.invul_duracion:
                self.invulnerable = False
                self.flash_tick = 0

    def draw(self, superficie, arma_key):
        cx, cy = int(self.x), int(self.y + self.bob_offset)

        # ── Aura de escudo (anillo azul pulsante) ──
        if self.escudo_activo:
            radio = 36 + int(math.sin(self.escudo_ticks * 0.15) * 4)
            s_surf = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s_surf, (60, 160, 255, 80), (radio + 2, radio + 2), radio)
            pygame.draw.circle(s_surf, (100, 200, 255, 180), (radio + 2, radio + 2), radio, 3)
            superficie.blit(s_surf, (cx - radio - 2, cy - radio - 2))

        # ── Aura de fuerza (anillo rojo) ──
        if self.boost_fuerza:
            radio = 32
            s_surf = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
            a = 60 + int(math.sin(pygame.time.get_ticks() * 0.01) * 40)
            pygame.draw.circle(s_surf, (255, 50, 50, max(0, min(255, a))), (radio, radio), radio, 4)
            superficie.blit(s_surf, (cx - radio, cy - radio))

        # ── Rastro verde si velocidad activa ──
        if self.boost_vel and self.caminando:
            s_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(s_surf, (60, 220, 90, 70), (14, 14), 14)
            superficie.blit(s_surf, (cx - 14, cy - 14))

        # ── Cuerpo: flip horizontal, SIN rotación (nunca boca abajo) ──
        frame = self.sm.player_skins[self.skin_index][self.anim_frame]
        # Flip horizontal según la dirección
        frame_draw = pygame.transform.flip(frame, self.mirando_izq, False)
        cuerpo_rect = frame_draw.get_rect(center=(cx, cy))

        if self.invulnerable and (self.flash_tick // 4) % 2 == 1:
            pass
        else:
            superficie.blit(frame_draw, cuerpo_rect.topleft)

        # ── Arma (sigue al ratón con ángulo completo) ──
        gun_map = {
            "pistola":    self.sm.gun_pistol,
            "escopeta":   self.sm.gun_shotgun,
            "rifle":      self.sm.gun_rifle,
            "metralleta": self.sm.gun_metralleta,
        }
        gun_sprite = gun_map.get(arma_key, self.sm.gun_pistol)
        # Flip el arma también si apunta a la izquierda, para que no aparezca espejada
        if self.mirando_izq:
            gun_sprite = pygame.transform.flip(gun_sprite, True, False)
        gun_rot    = pygame.transform.rotate(gun_sprite, self.dir_arma)

        rad = math.radians(self.dir_arma)
        gun_x = cx + math.cos(rad) * 20
        gun_y = cy - math.sin(rad) * 20
        gun_rect = gun_rot.get_rect(center=(gun_x, gun_y))

        if not (self.invulnerable and (self.flash_tick // 4) % 2 == 1):
            superficie.blit(gun_rot, gun_rect.topleft)


# ──────────────────────────────────────────────────────────────────────────
#  ZOMBIE
# ──────────────────────────────────────────────────────────────────────────
class Zombie:
    def __init__(self, x, y, tipo, oleada, sprite_manager, dificultad=1):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.sm = sprite_manager

        mult_oleada = 1.0 + (oleada - 1) * 0.12
        mult_dif    = 0.7 if dificultad == 0 else (1.4 if dificultad == 2 else 1.0)
        drop_mult   = 1.5 if dificultad == 0 else (0.6 if dificultad == 2 else 1.0)

        if tipo == "normal":
            self.frames = self.sm.zombie_frames
            self.salud_max = 30.0 * mult_oleada * mult_dif
            self.velocidad = random.uniform(1.3, 1.9) * mult_dif
            self.monedas_drop = int(random.randint(8, 18) * drop_mult)
            self.prob_corazon = 0.05 * drop_mult
        elif tipo == "rapido":
            self.frames = self.sm.zombie_fast_frames
            self.salud_max = 15.0 * mult_oleada * mult_dif
            self.velocidad = random.uniform(2.6, 3.4) * mult_dif
            self.monedas_drop = int(random.randint(15, 28) * drop_mult)
            self.prob_corazon = 0.04 * drop_mult
        elif tipo == "tanque":
            self.frames = self.sm.zombie_tank_frames
            self.salud_max = 110.0 * mult_oleada * mult_dif
            self.velocidad = random.uniform(0.8, 1.1) * mult_dif
            self.monedas_drop = int(random.randint(40, 75) * drop_mult)
            self.prob_corazon = 0.18 * drop_mult


        self.salud = self.salud_max
        sample = self.frames[0]
        self.w, self.h = sample.get_size()

        # Animación
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_velocidad = 10

        # Dirección suavizada
        self.dir_actual = 0.0

        # Dirección para flip: izquierda o derecha según el movimiento
        self.mirando_izq = True   # por defecto apunta al jugador
        self.kb_dx = 0.0
        self.kb_dy = 0.0

        # Flash de daño
        self.flash_timer = 0

        # Bob
        self.bob_timer = random.uniform(0, 100)
        self.bob_offset = 0.0

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self, px, py):
        # Flash
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Vector hacia el jugador
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            ndx = dx / dist
            ndy = dy / dist
        else:
            ndx, ndy = 0.0, 0.0

        # Dirección suave para flip: izq si el jugador está a la izquierda
        self.mirando_izq = (px < self.x)

        # Mover
        self.x += ndx * self.velocidad + self.kb_dx
        self.y += ndy * self.velocidad + self.kb_dy
        self.kb_dx *= 0.82
        self.kb_dy *= 0.82

        # Animación
        self.anim_timer += 1
        if self.anim_timer >= self.anim_velocidad:
            self.anim_timer = 0
            self.anim_frame = 1 - self.anim_frame

        # Bob
        self.bob_timer += 0.25
        self.bob_offset = math.sin(self.bob_timer) * 2.0

    def aplicar_knockback(self, angulo, cantidad):
        rad = math.radians(angulo)
        self.kb_dx += math.cos(rad) * cantidad
        self.kb_dy -= math.sin(rad) * cantidad

    def recibir_daño(self, cantidad, angulo, tiempo_actual):
        self.salud -= cantidad
        self.flash_timer = 6
        self.aplicar_knockback(angulo, cantidad * 0.12)
        return self.salud <= 0

    def draw(self, superficie):
        frame = self.frames[self.anim_frame]
        # Flip horizontal según dirección al jugador — sin rotar, nunca boca abajo
        frame_draw = pygame.transform.flip(frame, self.mirando_izq, False)
        rect = frame_draw.get_rect(center=(self.x, self.y + self.bob_offset))

        if self.flash_timer > 0:
            # Flash blanco al recibir daño
            tintado = frame_draw.copy()
            tintado.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
            superficie.blit(tintado, rect.topleft)
        else:
            superficie.blit(frame_draw, rect.topleft)

        # Barra de salud (solo si está dañado)
        if self.salud < self.salud_max:
            bw = max(self.w, 32)
            bh = 5
            pct = max(0.0, self.salud / self.salud_max)
            bx = self.x - bw // 2
            by = self.y - self.h // 2 - 10
            pygame.draw.rect(superficie, (100, 0, 0),   (bx, by, bw, bh), border_radius=2)
            pygame.draw.rect(superficie, (50, 210, 60), (bx, by, int(bw * pct), bh), border_radius=2)


# ──────────────────────────────────────────────────────────────────────────
#  BALA
# ──────────────────────────────────────────────────────────────────────────
class Bala:
    def __init__(self, x, y, angulo, velocidad, daño, sprite_manager):
        self.x = x
        self.y = y
        self.angulo = angulo
        self.daño = daño
        rad = math.radians(angulo)
        self.dx =  math.cos(rad) * velocidad
        self.dy = -math.sin(rad) * velocidad
        self.imagen = pygame.transform.rotate(sprite_manager.bullet, angulo)
        self.w = self.imagen.get_width()
        self.h = self.imagen.get_height()
        self.dist_max = 650
        self.dist = 0.0

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dist += math.hypot(self.dx, self.dy)
        return self.dist >= self.dist_max

    def draw(self, superficie):
        superficie.blit(self.imagen, (self.x - self.w // 2, self.y - self.h // 2))


# ──────────────────────────────────────────────────────────────────────────
#  OBJETO CAÍDO (moneda / corazón)
# ──────────────────────────────────────────────────────────────────────────
class ObjetoCaido:
    """
    Tipos: 'moneda', 'corazon', 'escudo', 'velocidad', 'fuerza', 'municion'
    """
    _ICON_MAP = {
        'moneda':    'coin',
        'corazon':   'heart',
        'escudo':    'escudo',
        'velocidad': 'velocidad',
        'fuerza':    'fuerza',
        'municion':  'municion',
    }
    # Color del texto de etiqueta que aparece encima del item
    _LABEL = {
        'escudo':    ("ESCUDO",    (80,  170, 255)),
        'velocidad': ("VELOZ",     (60,  220,  90)),
        'fuerza':    ("FUERZA",    (255,  60,  60)),
        'municion':  ("MUNI",      (255, 210,  40)),
    }

    def __init__(self, x, y, tipo, valor, sprite_manager):
        self.x     = x
        self.y     = y
        self.tipo  = tipo
        self.valor = valor    # monedas/vidas a dar; 0 para buffs
        attr = self._ICON_MAP.get(tipo, 'coin')
        self.imagen = getattr(sprite_manager, attr)
        self.w, self.h = self.imagen.get_size()
        self.float_timer = random.uniform(0, 100)
        self.float_offset = 0.0
        self._font = None  # se inicializa en draw

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self):
        self.float_timer += 0.07
        self.float_offset = math.sin(self.float_timer) * 4

    def draw(self, superficie):
        # Sombra
        sombra = pygame.Rect(self.x - 6, self.y + self.h // 2 - 2, 12, 4)
        pygame.draw.ellipse(superficie, (0, 0, 0, 80), sombra)
        # Item
        superficie.blit(self.imagen,
                        (self.x - self.w // 2,
                         self.y - self.h // 2 + self.float_offset))
        # Etiqueta para power-ups
        if self.tipo in self._LABEL:
            if self._font is None:
                self._font = pygame.font.Font(None, 16)
            txt, col = self._LABEL[self.tipo]
            lbl = self._font.render(txt, True, col)
            superficie.blit(lbl, (self.x - lbl.get_width() // 2,
                                  self.y - self.h // 2 - 14 + self.float_offset))


# ──────────────────────────────────────────────────────────────────────────
#  PARTÍCULA
# ──────────────────────────────────────────────────────────────────────────
class Particula:
    def __init__(self, x, y, dx, dy, color, tamaño, vida):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.color = color
        self.tamaño = tamaño
        self.vida_max = vida
        self.vida = vida

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dx *= 0.92
        self.dy *= 0.92
        self.vida -= 1
        return self.vida <= 0

    def draw(self, superficie):
        alpha = int((self.vida / self.vida_max) * 255)
        if alpha <= 0:
            return
        s = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
        r, g, b = self.color[:3]
        s.fill((r, g, b, alpha))
        superficie.blit(s, (self.x - self.tamaño // 2, self.y - self.tamaño // 2))
