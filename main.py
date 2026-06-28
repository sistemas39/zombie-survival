import pygame
import sys
import random
import math

from sprites import SpriteManager
from entities import Player, Zombie, Bala, ObjetoCaido, Particula
from weapons import get_default_weapons
from shop import Shop
from sonidos import GestorAudio
from fondo import generar_fondo
from mando import GestorMando
from touch_controls import TouchManager

pygame.init()

ANCHO = 960
ALTO  = 640
FPS   = 60

COLOR_FONDO  = (13, 13, 18)
COLOR_PANEL  = (28, 28, 38)
COLOR_TEXTO  = (235, 235, 255)
COLOR_ORO    = (255, 200, 7)
COLOR_ROJO   = (215, 20, 55)
COLOR_VERDE  = (50, 205, 80)
COLOR_GRIS   = (190, 190, 200)


class Juego:
    def __init__(self):
        # Detectar resolución del monitor para pantalla completa
        info = pygame.display.Info()
        self.pantalla_completa = False
        self.ancho_ventana = 960
        self.alto_ventana  = 640
        self.pantalla = pygame.display.set_mode(
            (self.ancho_ventana, self.alto_ventana),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("Supervivencia Zombie 2D")
        self.reloj = pygame.time.Clock()

        self.sm    = SpriteManager(scale=3)
        self.shop  = Shop(ANCHO, ALTO, self.sm)
        self.audio = GestorAudio()
        self.mando = GestorMando()   # soporte para mando Xbox/gamepad

        # Pre-renderizar el fondo una vez (mapa aleatorio)
        print("🏙️  Generando mapa...")
        self.fondo, self.tipo_mapa = generar_fondo(ANCHO, ALTO)

        # Estados: "MENU", "JUGANDO", "TIENDA", "FIN"
        self.estado = "MENU"
        self.shake  = 0.0
        self.banner_mapa_timer = 0  # cuánto tiempo se muestra el nombre del mapa
        # Opciones del menú
        self.skin_actual = 0
        self.dificultad  = 1  # 0: Fácil, 1: Normal, 2: Difícil
        self.menu_seleccion = 0  # 0: Personaje, 1: Dificultad, 2: Controles
        
        self.modo_tactil = False
        self.touch_manager = TouchManager(ANCHO, ALTO)

        # Orden fijo de armas para el scroll de la rueda y el hotbar
        self.orden_armas = ["pistola", "escopeta", "rifle", "metralleta"]

        self.reiniciar()
        self.audio.iniciar_musica()

    # ── Reinicio ────────────────────────────────────────────────────────────
    def reiniciar(self):
        # Generar nuevo mapa aleatorio en cada partida
        print("🏙️  Generando nuevo mapa...")
        self.fondo, self.tipo_mapa = generar_fondo(ANCHO, ALTO)
        self.banner_mapa_timer = 240  # ~4 segundos a 60 fps

        self.jugador   = Player(ANCHO // 2, ALTO // 2, self.sm, skin_index=self.skin_actual)
        self.zombies   = []
        self.balas     = []
        self.objetos   = []
        self.particulas = []

        self.armas = get_default_weapons()
        self.arma_activa = "pistola"

        self.oleada = 1
        self.zombies_por_spawnear = 0
        self.timer_spawn = 0.0
        self.cooldown_spawn = 1500
        self.intermision = True
        self.timer_oleada = 3000.0
        self.puntuacion = 0
        self.zombies_eliminados = 0

    # ── Bucle principal ─────────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            self.reloj.tick(FPS)
            tiempo = pygame.time.get_ticks()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    running = False

                # Plug/unplug de mando
                self.mando.manejar_evento(evento)

                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_F11:
                        self._toggle_pantalla_completa()
                    else:
                        self.manejar_tecla(evento, tiempo)

                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    self.manejar_clic(evento)

                if self.modo_tactil:
                    self.touch_manager.manejar_evento(evento)

                # ── Botones del mando ──
                elif evento.type == pygame.JOYBUTTONDOWN:
                    self._manejar_boton_mando(evento.button, tiempo)

                # ── D-pad ──
                elif evento.type == pygame.JOYHATMOTION:
                    hx, hy = evento.value
                    if self.estado == "JUGANDO":
                        if hx == 1:
                            self._scroll_arma(1)
                        elif hx == -1:
                            self._scroll_arma(-1)
                    elif self.estado == "TIENDA":
                        if hx == 1 or hy == -1:
                            self.shop.mando_navegar(1)
                        elif hx == -1 or hy == 1:
                            self.shop.mando_navegar(-1)
                    elif self.estado == "MENU":
                        if hy == 1:
                            self.menu_seleccion = (self.menu_seleccion - 1) % 3
                        elif hy == -1:
                            self.menu_seleccion = (self.menu_seleccion + 1) % 3
                        if hx == -1:
                            if self.menu_seleccion == 0:
                                self.skin_actual = (self.skin_actual - 1) % 3
                            elif self.menu_seleccion == 1:
                                self.dificultad = (self.dificultad - 1) % 3
                            else:
                                self.modo_tactil = not self.modo_tactil
                        elif hx == 1:
                            if self.menu_seleccion == 0:
                                self.skin_actual = (self.skin_actual + 1) % 3
                            elif self.menu_seleccion == 1:
                                self.dificultad = (self.dificultad + 1) % 3
                            else:
                                self.modo_tactil = not self.modo_tactil

            if self.estado == "JUGANDO":
                self.actualizar(tiempo)

            self.dibujar(tiempo)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _toggle_pantalla_completa(self):
        """Alterna entre ventana y pantalla completa (F11)."""
        self.pantalla_completa = not self.pantalla_completa
        if self.pantalla_completa:
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.pantalla = pygame.display.set_mode(
                (self.ancho_ventana, self.alto_ventana), pygame.RESIZABLE
            )

    # ── Eventos ─────────────────────────────────────────────────────────────
    def manejar_tecla(self, evento, tiempo):
        # M = silenciar / activar todo el audio
        if evento.key == pygame.K_m:
            self.audio.toggle_mute()
            return

        if self.estado == "MENU":
            if evento.key == pygame.K_SPACE or evento.key == pygame.K_RETURN:
                self.reiniciar()
                self.estado = "JUGANDO"
            elif evento.key == pygame.K_UP:
                self.menu_seleccion = (self.menu_seleccion - 1) % 3
            elif evento.key == pygame.K_DOWN:
                self.menu_seleccion = (self.menu_seleccion + 1) % 3
            elif evento.key == pygame.K_LEFT:
                if self.menu_seleccion == 0:
                    self.skin_actual = (self.skin_actual - 1) % 3
                elif self.menu_seleccion == 1:
                    self.dificultad = (self.dificultad - 1) % 3
                else:
                    self.modo_tactil = not self.modo_tactil
            elif evento.key == pygame.K_RIGHT:
                if self.menu_seleccion == 0:
                    self.skin_actual = (self.skin_actual + 1) % 3
                elif self.menu_seleccion == 1:
                    self.dificultad = (self.dificultad + 1) % 3
                else:
                    self.modo_tactil = not self.modo_tactil

        elif self.estado == "JUGANDO":
            if evento.key == pygame.K_1:
                self.cambiar_arma("pistola")
            elif evento.key == pygame.K_2:
                self.cambiar_arma("escopeta")
            elif evento.key == pygame.K_3:
                self.cambiar_arma("rifle")
            elif evento.key == pygame.K_4:
                self.cambiar_arma("metralleta")
            elif evento.key in (pygame.K_TAB, pygame.K_e, pygame.K_ESCAPE):
                self.estado = "TIENDA"
                self.audio.pausar_musica(True)
            # Nota: R ya no recarga — solo el power-up de munión recarga armas especiales

        elif self.estado == "TIENDA":
            if evento.key in (pygame.K_TAB, pygame.K_e, pygame.K_ESCAPE):
                self.estado = "JUGANDO"
                self.audio.pausar_musica(False)  # reanuda música al cerrar tienda

        elif self.estado == "FIN":
            if evento.key == pygame.K_SPACE or evento.key == pygame.K_RETURN:
                self.reiniciar()
                self.estado = "JUGANDO"
                self.audio.iniciar_musica()
            elif evento.key == pygame.K_ESCAPE:
                self.estado = "MENU"

    def manejar_clic(self, evento):
        if self.estado == "TIENDA" and evento.button == 1:
            if self.shop.handle_click(pygame.mouse.get_pos(), self.jugador, self.armas) == "CERRAR":
                self.estado = "JUGANDO"
                self.audio.pausar_musica(False)
        # Rueda del mouse: cambiar arma (fuera de tienda)
        elif self.estado == "JUGANDO":
            if evento.button == 4:   # scroll arriba
                self._scroll_arma(-1)
            elif evento.button == 5: # scroll abajo
                self._scroll_arma(1)

    def _scroll_arma(self, direccion):
        """Cicla entre armas desbloqueadas usando la rueda del mouse o D-pad."""
        disponibles = [k for k in self.orden_armas if self.armas[k].unlocked]
        if not disponibles:
            return
        try:
            idx = disponibles.index(self.arma_activa)
        except ValueError:
            idx = 0
        idx = (idx + direccion) % len(disponibles)
        self.arma_activa = disponibles[idx]
        self.mando.vibrar(0.0, 0.15, 60)   # toque corto al cambiar arma

    def _manejar_boton_mando(self, btn, tiempo):
        """Mapeo de botones Xbox al juego."""
        from mando import GestorMando as GM

        # A (0) — iniciar partida en menú / confirmar
        if btn == GM.BTN_A:
            if self.estado == "MENU":
                self.reiniciar()
                self.estado = "JUGANDO"
            elif self.estado == "FIN":
                self.reiniciar()
                self.estado = "JUGANDO"
            elif self.estado == "TIENDA":
                if self.shop.mando_confirmar(self.jugador, self.armas) == "CERRAR":
                    self.estado = "JUGANDO"
                    self.audio.pausar_musica(False)

        # B (1) — cerrar tienda o volver al menú
        elif btn == GM.BTN_B:
            if self.estado == "TIENDA":
                self.estado = "JUGANDO"
                self.audio.pausar_musica(False)
            elif self.estado == "FIN":
                self.estado = "MENU"

        # Start (7) — abrir/cerrar tienda durante la partida
        elif btn == GM.BTN_START:
            if self.estado == "JUGANDO":
                self.estado = "TIENDA"
                self.audio.pausar_musica(True)
            elif self.estado == "TIENDA":
                self.estado = "JUGANDO"
                self.audio.pausar_musica(False)

        # LB (4) — arma anterior
        elif btn == GM.BTN_LB and self.estado == "JUGANDO":
            self._scroll_arma(-1)

        # RB (5) — arma siguiente
        elif btn == GM.BTN_RB and self.estado == "JUGANDO":
            self._scroll_arma(1)
            
        # D-pad en caso de que lo detecte como botones (Linux xpad, btn 11-14)
        elif self.estado == "MENU":
            if btn == 11:  # D-pad Arriba
                self.menu_seleccion = (self.menu_seleccion - 1) % 3
            elif btn == 12:  # D-pad Abajo
                self.menu_seleccion = (self.menu_seleccion + 1) % 3
            elif btn == 13:  # D-pad Izquierda
                if self.menu_seleccion == 0:
                    self.skin_actual = (self.skin_actual - 1) % 3
                elif self.menu_seleccion == 1:
                    self.dificultad = (self.dificultad - 1) % 3
                else:
                    self.modo_tactil = not self.modo_tactil
            elif btn == 14:  # D-pad Derecha
                if self.menu_seleccion == 0:
                    self.skin_actual = (self.skin_actual + 1) % 3
                elif self.menu_seleccion == 1:
                    self.dificultad = (self.dificultad + 1) % 3
                else:
                    self.modo_tactil = not self.modo_tactil


    def cambiar_arma(self, clave):
        if self.armas[clave].unlocked:
            self.arma_activa = clave

    # ── Disparo ──────────────────────────────────────────────────────────────────────
    def disparar(self, tiempo):
        arma = self.armas[self.arma_activa]
        if tiempo - arma.last_shot_time < arma.fire_rate:
            return
        # Sin balas: NO recargar automáticamente
        # Solo el power-up de munión puede recargar armas especiales
        if arma.ammo_capacity != -1 and arma.current_ammo <= 0:
            return   # ¡bloqueado! el jugador debe recoger munión

        arma.last_shot_time = tiempo
        if arma.ammo_capacity != -1:
            arma.current_ammo -= 1

        # Shake
        if self.arma_activa == "escopeta":
            self.shake = min(14, self.shake + 9)
        elif self.arma_activa == "rifle":
            self.shake = min(6, self.shake + 3)
        else:
            self.shake = min(3, self.shake + 1.5)

        # 🔊 Sonido de disparo
        self.audio.reproducir(self.arma_activa, tiempo)

        angulo_base = self.jugador.dir_arma

        for _ in range(arma.bullets_per_shot):
            ang = angulo_base + random.uniform(-arma.spread, arma.spread)
            rad = math.radians(ang)
            sx = self.jugador.x + math.cos(rad) * 22
            sy = self.jugador.y - math.sin(rad) * 22
            daño_real = arma.damage * self.jugador.mult_daño  # aplicar buff de fuerza
            self.balas.append(Bala(sx, sy, ang, arma.bullet_speed, daño_real, self.sm))

        # Partícula casquillo
        ang_cas = angulo_base + 180 + random.uniform(-40, 40)
        rad_c = math.radians(ang_cas)
        self.particulas.append(Particula(
            self.jugador.x, self.jugador.y,
            math.cos(rad_c) * random.uniform(1.5, 3.0),
            -math.sin(rad_c) * random.uniform(1.5, 3.0),
            (218, 165, 32), 3, 18 + random.randint(0, 12)
        ))

    # ── Actualización ───────────────────────────────────────────────────────
    def actualizar(self, tiempo):
        teclas     = pygame.key.get_pressed()
        pos_raton  = pygame.mouse.get_pos()

        # Contador del banner de mapa
        if self.banner_mapa_timer > 0:
            self.banner_mapa_timer -= 1

        if self.modo_tactil:
            # Botón Tienda
            if self.touch_manager.btn_tienda.is_clicked:
                self.estado = "TIENDA"
                self.audio.pausar_musica(True)
                self.touch_manager.update()
                return
            # Botón Arma
            if self.touch_manager.btn_arma.is_clicked:
                self._scroll_arma(1)
                
            t_dx, t_dy = self.touch_manager.get_movimiento()
            t_ang = self.touch_manager.get_punteria() if self.touch_manager.j_der.active else None
            
            # Pasar input táctil al jugador como si fuera mando
            self.jugador.update(teclas, ANCHO, ALTO, tiempo, pos_raton,
                                joy_dx=t_dx, joy_dy=t_dy, joy_angulo=t_ang)
            
            # Disparo táctil (joystick derecho)
            if self.touch_manager.disparando():
                self.disparar(tiempo)
                
            self.touch_manager.update()
        else:
            # ── Entrada del mando / PC ──
            joy_dx, joy_dy = self.mando.get_movimiento()
            joy_angulo     = self.mando.get_punteria()
    
            self.jugador.update(teclas, ANCHO, ALTO, tiempo, pos_raton,
                                joy_dx=joy_dx, joy_dy=joy_dy, joy_angulo=joy_angulo)
    
            # Disparo: botón izquierdo del ratón  O  gatillo derecho (RT)
            if pygame.mouse.get_pressed()[0] or self.mando.disparando():
                self.disparar(tiempo)

        # ── Oleadas ──
        if self.intermision:
            self.timer_oleada -= 1000 / FPS
            if self.timer_oleada <= 0:
                self.intermision = False
                self.iniciar_oleada()
        else:
            if self.zombies_por_spawnear > 0:
                self.timer_spawn += 1000 / FPS
                if self.timer_spawn >= self.cooldown_spawn:
                    self.timer_spawn = 0
                    self.spawnear_zombie()
            if not self.zombies and self.zombies_por_spawnear == 0:
                self.intermision = True
                self.oleada += 1
                self.timer_oleada = 5000.0

        # ── Balas ──
        for b in self.balas[:]:
            if b.update():
                self.balas.remove(b)

        # ── Zombies ──
        for z in self.zombies[:]:
            z.update(self.jugador.x, self.jugador.y)
            if z.get_rect().colliderect(self.jugador.get_rect()):
                if self.jugador.recibir_daño(tiempo):
                    self.shake = 20
                    self.audio.reproducir("daño")   # 🔊 golpe al jugador
                    for _ in range(14):
                        self.particulas.append(Particula(
                            self.jugador.x, self.jugador.y,
                            random.uniform(-4, 4), random.uniform(-4, 4),
                            COLOR_ROJO, random.randint(4, 6), random.randint(28, 50)
                        ))
                    if self.jugador.vidas <= 0:
                        self.estado = "FIN"
                        self.audio.detener_musica()
                        self.audio.reproducir("game_over")

        # ── Objetos caídos ──
        for obj in self.objetos[:]:
            obj.update()
            dx = self.jugador.x - obj.x
            dy = self.jugador.y - obj.y
            dist = math.hypot(dx, dy)
            if dist < 110 and dist > 0:
                fuerza = (110 - dist) * 0.09
                obj.x += (dx / dist) * fuerza
                obj.y += (dy / dist) * fuerza
            if obj.get_rect().colliderect(self.jugador.get_rect()):
                recogido = True
                if obj.tipo == 'moneda':
                    self.jugador.monedas += obj.valor
                    self.audio.reproducir("moneda")
                    for _ in range(5):
                        self.particulas.append(Particula(
                            obj.x, obj.y,
                            random.uniform(-2, 2), random.uniform(-2, 2),
                            COLOR_ORO, 3, 14
                        ))
                elif obj.tipo == 'corazon' and self.jugador.vidas < self.jugador.max_vidas:
                    self.jugador.vidas += 1
                    self.audio.reproducir("corazon")
                    for _ in range(8):
                        self.particulas.append(Particula(
                            obj.x, obj.y,
                            random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5),
                            COLOR_ROJO, 4, 20
                        ))
                elif obj.tipo in ('escudo', 'velocidad', 'fuerza'):
                    self.jugador.aplicar_buff(obj.tipo, tiempo)
                    self.audio.reproducir("corazon")  # reutilizar sonido de pickup
                    col_buff = {'escudo': (80,170,255),'velocidad':(60,220,90),'fuerza':(255,60,60)}
                    c = col_buff.get(obj.tipo, (255,255,255))
                    for _ in range(10):
                        self.particulas.append(Particula(
                            obj.x, obj.y,
                            random.uniform(-3, 3), random.uniform(-3, 3),
                            c, 5, 25
                        ))
                elif obj.tipo == 'municion':
                    self.armas[self.arma_activa].reload()
                    self.audio.reproducir("moneda")
                    for _ in range(6):
                        self.particulas.append(Particula(
                            obj.x, obj.y,
                            random.uniform(-2, 2), random.uniform(-2, 2),
                            (255, 210, 40), 4, 18
                        ))
                else:
                    recogido = False
                if recogido:
                    self.objetos.remove(obj)

        # ── Colisión bala-zombie ──
        for b in self.balas[:]:
            br = b.get_rect()
            for z in self.zombies[:]:
                if br.colliderect(z.get_rect()):
                    color_sangre = (55, 150, 55) if z.tipo != 'tanque' else (140, 0, 0)
                    for _ in range(6):
                        self.particulas.append(Particula(
                            b.x, b.y,
                            random.uniform(-3, 3), random.uniform(-3, 3),
                            color_sangre, random.randint(3, 5), random.randint(12, 28)
                        ))
                    muerto = z.recibir_daño(b.daño, b.angulo, tiempo)
                    if b in self.balas:
                        self.balas.remove(b)
                    if muerto:
                        self.zombies.remove(z)
                        self.zombies_eliminados += 1
                        self.puntuacion += int(z.salud_max)
                        self.generar_drops(z)
                        self.audio.reproducir("zombie_muere")  # 🔊 muerte zombie
                        for _ in range(12):
                            self.particulas.append(Particula(
                                z.x, z.y,
                                random.uniform(-4, 4), random.uniform(-4, 4),
                                color_sangre, random.randint(4, 7), random.randint(25, 45)
                            ))
                    break

        # ── Partículas ──
        for p in self.particulas[:]:
            if p.update():
                self.particulas.remove(p)

        # ── Shake decay ──
        self.shake *= 0.88
        if self.shake < 0.2:
            self.shake = 0

    # ── Oleada ──────────────────────────────────────────────────────────────
    def iniciar_oleada(self):
        base_zombies = 6 + (self.oleada - 1) * 4
        mult_z = 0.7 if self.dificultad == 0 else (1.4 if self.dificultad == 2 else 1.0)
        self.zombies_por_spawnear = int(base_zombies * mult_z)
        
        base_cooldown = max(380, 1500 - (self.oleada - 1) * 90)
        mult_cd = 1.3 if self.dificultad == 0 else (0.7 if self.dificultad == 2 else 1.0)
        self.cooldown_spawn = base_cooldown * mult_cd
        
        self.timer_spawn = self.cooldown_spawn  # spawnea uno al instante
        self.audio.reproducir("oleada")  # 🔊 fanfarria de nueva oleada

    def spawnear_zombie(self):
        if self.zombies_por_spawnear <= 0:
            return
        self.zombies_por_spawnear -= 1
        lado = random.choice(["arriba", "abajo", "izq", "der"])
        margen = 50
        if lado == "arriba":
            x, y = random.randint(0, ANCHO), -margen
        elif lado == "abajo":
            x, y = random.randint(0, ANCHO), ALTO + margen
        elif lado == "izq":
            x, y = -margen, random.randint(0, ALTO)
        else:
            x, y = ANCHO + margen, random.randint(0, ALTO)

        tipo = "normal"
        if self.oleada >= 3:
            r = random.random()
            if r < 0.14:
                tipo = "tanque"
            elif r < 0.40:
                tipo = "rapido"
        elif self.oleada >= 2:
            if random.random() < 0.25:
                tipo = "rapido"

        self.zombies.append(Zombie(x, y, tipo, self.oleada, self.sm, self.dificultad))

    def generar_drops(self, zombie):
        """Drop table: munión ahora es la más común (arma sin recarga manual)."""
        r = random.random()
        # Corazón  Escudo  Velocidad  Fuerza  Munión   Moneda
        if r < zombie.prob_corazon:
            self.objetos.append(ObjetoCaido(zombie.x, zombie.y, 'corazon', 1, self.sm))
        elif r < zombie.prob_corazon + 0.07:
            self.objetos.append(ObjetoCaido(zombie.x, zombie.y, 'escudo', 0, self.sm))
        elif r < zombie.prob_corazon + 0.12:
            self.objetos.append(ObjetoCaido(zombie.x, zombie.y, 'velocidad', 0, self.sm))
        elif r < zombie.prob_corazon + 0.17:
            self.objetos.append(ObjetoCaido(zombie.x, zombie.y, 'fuerza', 0, self.sm))
        elif r < zombie.prob_corazon + 0.42:  # 25% de chance → antes 5%
            self.objetos.append(ObjetoCaido(zombie.x, zombie.y, 'municion', 0, self.sm))
        else:
            self.objetos.append(ObjetoCaido(zombie.x, zombie.y, 'moneda', zombie.monedas_drop, self.sm))

    # ── Dibujo ──────────────────────────────────────────────────────────────
    def dibujar(self, tiempo):
        ox = int(random.uniform(-self.shake, self.shake)) if self.shake > 0 else 0
        oy = int(random.uniform(-self.shake, self.shake)) if self.shake > 0 else 0

        self.pantalla.fill(COLOR_FONDO)
        juego_surf = pygame.Surface((ANCHO, ALTO))

        # Fondo post-apocalíptico (pre-renderizado)
        juego_surf.blit(self.fondo, (0, 0))

        # Objetos
        for obj in self.objetos:
            obj.draw(juego_surf)

        # Jugador
        self.jugador.draw(juego_surf, self.arma_activa)

        # Zombies
        for z in self.zombies:
            z.draw(juego_surf)

        # Balas
        for b in self.balas:
            b.draw(juego_surf)

        # Partículas
        for p in self.particulas:
            p.draw(juego_surf)

        self.pantalla.blit(juego_surf, (ox, oy))

        # HUD (sin shake)
        self.dibujar_hud(tiempo)

        # Pantallas de estado
        if self.estado == "MENU":
            self.dibujar_menu()
        elif self.estado == "JUGANDO":
            if self.modo_tactil:
                self.touch_manager.draw(self.pantalla)
        elif self.estado == "TIENDA":
            self.shop.draw(self.pantalla, self.jugador, self.armas, pygame.mouse.get_pos())
        elif self.estado == "FIN":
            self.dibujar_fin()

    # ── HUD ─────────────────────────────────────────────────────────────────
    def dibujar_hud(self, tiempo):
        f_med = pygame.font.Font(None, 28)
        f_peq = pygame.font.Font(None, 21)

        # Vidas (corazones)
        for i in range(self.jugador.max_vidas):
            if i < self.jugador.vidas:
                self.pantalla.blit(self.sm.heart, (15 + i * 36, 15))
            else:
                pygame.draw.rect(self.pantalla, (38, 38, 48),
                                 (15 + i*36 + 5, 20, 22, 22), border_radius=4)
                pygame.draw.rect(self.pantalla, (80, 80, 95),
                                 (15 + i*36 + 5, 20, 22, 22), 2, border_radius=4)

        # Oleada
        if self.intermision:
            t_seg = max(0, math.ceil(self.timer_oleada / 1000))
            txt_oleada = f"PRÓXIMA OLEADA: {t_seg}s"
            col_ol = COLOR_ORO
        else:
            txt_oleada = f"OLEADA {self.oleada}"
            col_ol = COLOR_TEXTO
        self.pantalla.blit(f_med.render(txt_oleada, True, col_ol), (210, 18))

        # Zombies restantes
        total_z = len(self.zombies) + self.zombies_por_spawnear
        self.pantalla.blit(f_med.render(f"Zombies: {total_z}", True, COLOR_TEXTO), (430, 18))

        # Puntuación
        txt_pts = f_med.render(f"Puntos: {self.puntuacion}", True, COLOR_TEXTO)
        self.pantalla.blit(txt_pts, (ANCHO - txt_pts.get_width() - 15, 18))

        # Panel inferior
        panel = pygame.Rect(12, ALTO - 78, 360, 65)
        pygame.draw.rect(self.pantalla, COLOR_PANEL, panel, border_radius=8)
        pygame.draw.rect(self.pantalla, (90, 90, 110), panel, 2, border_radius=8)

        self.pantalla.blit(f_med.render(f"Monedas: {self.jugador.monedas}", True, COLOR_ORO),
                           (24, ALTO - 70))

        arma = self.armas[self.arma_activa]
        sin_balas = (arma.ammo_capacity != -1 and arma.current_ammo <= 0)

        if sin_balas:
            ammo_str = "SIN BALAS"
            col_ammo = COLOR_ROJO
        else:
            ammo_str = "∞" if arma.ammo_capacity == -1 else f"{arma.current_ammo}/{arma.ammo_capacity}"
            col_ammo = COLOR_TEXTO

        self.pantalla.blit(f_med.render(f"{arma.name}: {ammo_str}", True, col_ammo),
                           (24, ALTO - 48))

        # Aviso pulsante si sin balas
        if sin_balas:
            if (pygame.time.get_ticks() // 350) % 2 == 0:
                f_alerta = pygame.font.Font(None, 22)
                aviso = f_alerta.render("(!!)  Recoge un power-up de MUNICION para recargar  (!!)", True, COLOR_ROJO)
                ax = ANCHO // 2 - aviso.get_width() // 2
                fondo_av = pygame.Surface((aviso.get_width() + 16, aviso.get_height() + 8), pygame.SRCALPHA)
                fondo_av.fill((40, 0, 0, 180))
                self.pantalla.blit(fondo_av, (ax - 8, ALTO - 115))
                self.pantalla.blit(aviso, (ax, ALTO - 111))

        icon_map = {
            "pistola":    self.sm.pistol,
            "escopeta":   self.sm.shotgun,
            "rifle":      self.sm.rifle,
            "metralleta": self.sm.metralleta,
        }
        icon = icon_map.get(self.arma_activa)
        if icon:
            self.pantalla.blit(icon, (260, ALTO - 72))

        # ── Hotbar estilo Minecraft (armas desbloqueadas, centro inferior) ──
        slot_size = 52
        slot_gap  = 6
        n_slots   = len(self.orden_armas)
        hotbar_w  = n_slots * slot_size + (n_slots - 1) * slot_gap
        hotbar_x  = ANCHO // 2 - hotbar_w // 2
        hotbar_y  = ALTO - slot_size - 10

        icon_map2 = {
            "pistola":    self.sm.pistol,
            "escopeta":   self.sm.shotgun,
            "rifle":      self.sm.rifle,
            "metralleta": self.sm.metralleta,
        }
        nombres_cortos = {"pistola": "Pistola", "escopeta": "Escopeta",
                          "rifle": "Rifle", "metralleta": "Mtrllta"}
        f_slot = pygame.font.Font(None, 17)
        f_num  = pygame.font.Font(None, 20)

        for i, clave in enumerate(self.orden_armas):
            sx = hotbar_x + i * (slot_size + slot_gap)
            sy = hotbar_y
            bloqueada  = not self.armas[clave].unlocked
            es_activa  = (clave == self.arma_activa)
            sin_bala_s = (self.armas[clave].ammo_capacity != -1 and
                          self.armas[clave].current_ammo <= 0)

            # Fondo del slot
            if es_activa:
                col_fondo = (55, 55, 75)
                col_borde = (255, 215, 50) if not sin_bala_s else COLOR_ROJO
                grosor_b  = 3
            elif bloqueada:
                col_fondo = (18, 18, 22)
                col_borde = (45, 45, 55)
                grosor_b  = 1
            else:
                col_fondo = (28, 28, 38)
                col_borde = (70, 70, 90)
                grosor_b  = 1

            pygame.draw.rect(self.pantalla, col_fondo,
                             (sx, sy, slot_size, slot_size), border_radius=6)
            pygame.draw.rect(self.pantalla, col_borde,
                             (sx, sy, slot_size, slot_size), grosor_b, border_radius=6)

            # Numero de tecla (esquina sup-izq)
            num_s = f_num.render(str(i + 1), True, (160, 160, 180))
            self.pantalla.blit(num_s, (sx + 4, sy + 4))

            if bloqueada:
                # Candado textual
                lock_s = f_slot.render("[LOCK]", True, (80, 80, 90))
                self.pantalla.blit(lock_s, (sx + slot_size // 2 - lock_s.get_width() // 2,
                                            sy + slot_size // 2 - 6))
            else:
                # Icono del arma escalado a 36x36
                icon = icon_map2.get(clave)
                if icon:
                    scaled = pygame.transform.scale(icon, (36, 36))
                    self.pantalla.blit(scaled, (sx + (slot_size - 36) // 2,
                                                sy + (slot_size - 36) // 2 - 2))

                # Nombre debajo del icono
                nom_s = f_slot.render(nombres_cortos[clave],
                                      True, (200, 195, 210) if not es_activa else (255, 230, 80))
                self.pantalla.blit(nom_s, (sx + slot_size // 2 - nom_s.get_width() // 2,
                                           sy + slot_size - 16))

                # Barra de munición en la parte inferior del slot
                if self.armas[clave].ammo_capacity != -1:
                    cap = self.armas[clave].ammo_capacity
                    cur = self.armas[clave].current_ammo
                    pct = max(0.0, cur / cap)
                    bar_w = slot_size - 10
                    bary  = sy + slot_size - 5
                    pygame.draw.rect(self.pantalla, (40, 10, 10),
                                     (sx + 5, bary, bar_w, 3), border_radius=1)
                    if cur > 0:
                        col_b = (50, 200, 60) if pct > 0.3 else (230, 120, 20)
                        pygame.draw.rect(self.pantalla, col_b,
                                         (sx + 5, bary, int(bar_w * pct), 3), border_radius=1)

            # Indicador seleccionado: pequeño triangulo abajo
            if es_activa:
                mid = sx + slot_size // 2
                pygame.draw.polygon(self.pantalla, (255, 215, 50) if not sin_bala_s else COLOR_ROJO,
                                    [(mid - 5, ALTO - 8), (mid + 5, ALTO - 8), (mid, ALTO - 2)])

        # Hint scroll (solo al inicio, 10 segundos)
        if tiempo < 10000:
            f_hint = pygame.font.Font(None, 18)
            hint = f_hint.render("Rueda del mouse para cambiar arma", True, (120, 120, 140))
            self.pantalla.blit(hint, hint.get_rect(center=(ANCHO // 2, ALTO - slot_size - 18)))

        # ── Indicadores de buff activos ──
        buff_x = 15
        buff_y = ALTO - 105
        f_buff = pygame.font.Font(None, 19)
        buffs = []
        j = self.jugador
        if j.escudo_activo:
            secs = max(0, int((j.escudo_dur - (tiempo - j.escudo_timer)) / 1000) + 1)
            buffs.append(("ESC", f"ESCUDO {secs}s", (80, 170, 255), (18, 25, 45), (60, 140, 230)))
        if j.boost_vel:
            secs = max(0, int((j.boost_vel_dur - (tiempo - j.boost_vel_timer)) / 1000) + 1)
            buffs.append(("VEL", f"VELOZ {secs}s",  (60, 220, 90),  (15, 35, 20),  (40, 180, 60)))
        if j.boost_fuerza:
            secs = max(0, int((j.boost_fuerza_dur - (tiempo - j.boost_fuerza_timer)) / 1000) + 1)
            buffs.append(("FUE", f"FUERZA {secs}s", (255, 75, 75),  (40, 12, 12),  (210, 30, 30)))
        for etiq_key, etiqueta, col_txt, col_bg, col_dot in buffs:
            bw = 96
            pygame.draw.rect(self.pantalla, col_bg,  (buff_x, buff_y, bw, 22), border_radius=5)
            pygame.draw.rect(self.pantalla, col_txt, (buff_x, buff_y, bw, 22), 2, border_radius=5)
            # Cuadrito de color en vez de emoji
            pygame.draw.rect(self.pantalla, col_dot, (buff_x + 4, buff_y + 5, 8, 12), border_radius=2)
            lbl_s = f_buff.render(etiqueta, True, col_txt)
            self.pantalla.blit(lbl_s, (buff_x + 16, buff_y + 4))
            buff_x += bw + 6

        # Banner inicio de oleada
        if self.intermision and self.timer_oleada > 1200:
            f_banner = pygame.font.Font(None, 50)
            banner = f_banner.render(f"PREPARACIÓN — OLEADA {self.oleada}", True, COLOR_ORO)
            bx = ANCHO // 2 - banner.get_width() // 2
            by = ALTO // 3
            cuadro = pygame.Rect(bx - 20, by - 12, banner.get_width() + 40, banner.get_height() + 24)
            pygame.draw.rect(self.pantalla, (18, 18, 22), cuadro, border_radius=10)
            pygame.draw.rect(self.pantalla, COLOR_ORO,   cuadro, 2, border_radius=10)
            self.pantalla.blit(banner, (bx, by))

        # Banner de nombre de mapa (aparece los primeros 4 segundos)
        if self.banner_mapa_timer > 0:
            from fondo import NOMBRES_MAPA
            nombre = NOMBRES_MAPA.get(self.tipo_mapa, self.tipo_mapa)
            alpha = min(255, self.banner_mapa_timer * 3)
            f_mapa = pygame.font.Font(None, 36)
            txt_mapa = f_mapa.render(f"[MAP]  {nombre.upper()}", True, (200, 220, 255))
            mx = ANCHO // 2 - txt_mapa.get_width() // 2
            my = ALTO // 2 - 90
            fondo_m = pygame.Surface((txt_mapa.get_width() + 28, txt_mapa.get_height() + 16), pygame.SRCALPHA)
            fondo_m.fill((10, 15, 30, min(200, alpha)))
            pygame.draw.rect(fondo_m, (80, 130, 200, min(200, alpha)),
                             (0, 0, fondo_m.get_width(), fondo_m.get_height()), 2, border_radius=8)
            self.pantalla.blit(fondo_m, (mx - 14, my - 8))
            s_txt = txt_mapa.copy()
            s_txt.set_alpha(alpha)
            self.pantalla.blit(s_txt, (mx, my))

        # Nombre del mapa en esquina superior derecha (siempre visible, chico)
        from fondo import NOMBRES_MAPA
        nombre_corto = NOMBRES_MAPA.get(self.tipo_mapa, self.tipo_mapa)
        f_mapita = pygame.font.Font(None, 19)
        lbl = f_mapita.render(f"[MAP] {nombre_corto}", True, (120, 140, 170))
        self.pantalla.blit(lbl, (ANCHO - lbl.get_width() - 12, 42))

        # Badge de estado del mando (esquina sup-der)
        f_ctrl_hud = pygame.font.Font(None, 18)
        if self.mando.conectado:
            nombre_m = self.mando.nombre[:22]  # truncar si es muy largo
            ctrl_txt = f_ctrl_hud.render(f"[CTRL] {nombre_m}", True, (60, 210, 90))
        else:
            ctrl_txt = f_ctrl_hud.render("[SIN MANDO]", True, (90, 90, 100))
        self.pantalla.blit(ctrl_txt, (ANCHO - ctrl_txt.get_width() - 12, 56))

    # ── Menú principal ──────────────────────────────────────────────────────
    def dibujar_menu(self):
        t     = pygame.time.get_ticks()
        ancho = self.pantalla.get_width()
        alto  = self.pantalla.get_height()
        cx    = ancho // 2

        # Fondo degradado oscuro (arriba más negro, abajo rojizo)
        bg = pygame.Surface((ancho, alto))
        for y in range(alto):
            frac = y / alto
            pygame.draw.line(bg, (int(6 + 18 * frac), int(2 + 6 * frac), int(8 + 16 * frac)),
                             (0, y), (ancho, y))
        self.pantalla.blit(bg, (0, 0))

        # Partículas de ceniza flotando
        rng_p = random.Random(42)
        for i in range(55):
            px = rng_p.randint(0, ancho)
            py = rng_p.randint(0, alto)
            vel = rng_p.uniform(0.3, 1.2)
            oy  = int((t * vel * 0.04 + i * 37) % alto)
            s = pygame.Surface((3, 3), pygame.SRCALPHA)
            s.fill((200, 190, 170, rng_p.randint(40, 120)))
            self.pantalla.blit(s, (px, (py + oy) % alto))

        # Goteos de sangre desde arriba
        rng_d = random.Random(7)
        for i in range(12):
            dx = rng_d.randint(40, ancho - 40)
            altura_max = rng_d.randint(30, 130)
            vel = rng_d.uniform(0.03, 0.08)
            drip_y = int((t * vel + i * 200) % (altura_max + 60))
            if drip_y < altura_max:
                pygame.draw.line(self.pantalla, (140, 8, 12), (dx, 0), (dx, drip_y), 2)
                pygame.draw.circle(self.pantalla, (160, 10, 14), (dx, drip_y), 4)

        # Siluetas de zombies caminando por el suelo
        n_z = 7
        for i in range(n_z):
            offset = (t * (0.04 + i * 0.008) + i * (ancho // n_z)) % (ancho + 80)
            zx = int(offset) - 40
            zy = alto - 95
            sz = pygame.Surface((32, 55), pygame.SRCALPHA)
            pygame.draw.ellipse(sz, (18, 30, 14, 200), (7, 0, 18, 18))
            pygame.draw.rect(sz,   (18, 30, 14, 200), (9, 17, 14, 22))
            arm_y = 28 + int(math.sin(t * 0.004 + i) * 4)
            pygame.draw.line(sz, (18, 30, 14, 200), (16, 22), (29, arm_y), 3)
            leg = int(math.sin(t * 0.006 + i * 1.3) * 6)
            pygame.draw.line(sz, (18, 30, 14, 200), (12, 38), (10 + leg, 55), 3)
            pygame.draw.line(sz, (18, 30, 14, 200), (20, 38), (22 - leg, 55), 3)
            if i % 2 == 0:
                sz = pygame.transform.flip(sz, True, False)
            self.pantalla.blit(sz, (zx, zy))

        # Suelo oscuro con charcos
        pygame.draw.rect(self.pantalla, (12, 8, 10), (0, alto - 42, ancho, 42))
        pygame.draw.line(self.pantalla, (80, 5, 10), (0, alto - 42), (ancho, alto - 42), 2)
        for i in range(8):
            bx = 60 + i * (ancho // 8) + random.Random(i + 100).randint(-20, 20)
            cs = pygame.Surface((60, 18), pygame.SRCALPHA)
            pygame.draw.ellipse(cs, (80, 5, 10, 100), (0, 0, 60, 18))
            self.pantalla.blit(cs, (bx - 30, alto - 36))

        # Panel central semitransparente
        pw = min(680, ancho - 40)
        ph = 520
        px_ = cx - pw // 2
        py_ = alto // 2 - ph // 2 + 10
        pan = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pan.fill((6, 4, 8, 200))
        pygame.draw.rect(pan, (130, 8, 14, 220), (0, 0, pw, ph), 3, border_radius=12)
        self.pantalla.blit(pan, (px_, py_))
        pygame.draw.rect(self.pantalla, (190, 10, 16),
                         (px_, py_, pw, 4), border_radius=2)

        # Título con sombra y glow pulsante
        f_tit = pygame.font.Font(None, 88)
        sombra = f_tit.render("SUPERVIVENCIA ZOMBIE", True, (80, 3, 6))
        self.pantalla.blit(sombra, sombra.get_rect(center=(cx + 3, py_ - 52)))
        titulo = f_tit.render("SUPERVIVENCIA ZOMBIE", True, (228, 16, 22))
        self.pantalla.blit(titulo, titulo.get_rect(center=(cx, py_ - 52)))
        f_sub = pygame.font.Font(None, 44)
        sub = f_sub.render("— 2D  PIXEL —", True, COLOR_ORO)
        self.pantalla.blit(sub, sub.get_rect(center=(cx, py_ - 8)))

        # Controles en dos columnas (dependen de si hay mando conectado)
        if self.mando.conectado:
            col_izq = [
                ((100, 200, 100), "Stick Izquierdo  ->  Mover"),
                ((100, 180, 255), "Stick Derecho  ->  Apuntar arma"),
                ((255, 80,  80),  "Gatillo RT  ->  Disparar"),
                ((255, 200,  50), "LB / RB  ->  Cambiar arma"),
            ]
            col_der = [
                ((200, 150, 255), "Boton Start  ->  Abrir Tienda"),
                ((180, 180, 180), "Boton M (teclado) -> Silenciar"),
                ((255, 210,  50), "Drop MUNICION  ->  Recargar"),
                ((100, 210, 255), "Boton A -> Confirmar / Iniciar"),
            ]
        else:
            col_izq = [
                ((100, 200, 100), "WASD / Flechas  ->  Mover"),
                ((100, 180, 255), "Raton  ->  Apuntar el arma"),
                ((255, 80,  80),  "Click izquierdo  ->  Disparar"),
                ((255, 200,  50), "1 / 2 / 3 / 4  ->  Cambiar arma"),
            ]
            col_der = [
                ((200, 150, 255), "TAB / E  ->  Abrir Tienda"),
                ((180, 180, 180), "M  ->  Silenciar audio"),
                ((255, 210,  50), "Drop MUNICION  ->  Recargar"),
                ((100, 210, 255), "F11  ->  Pantalla completa"),
            ]
        f_ctrl  = pygame.font.Font(None, 22)
        ctrl_y0 = py_ + 22
        col_w_c = pw // 2 - 24
        for col_x, lista in [(px_ + 12, col_izq), (px_ + pw // 2 + 12, col_der)]:
            for row, (dot_col, desc) in enumerate(lista):
                ry = ctrl_y0 + row * 38
                # Fondo de fila
                fila = pygame.Surface((col_w_c, 34), pygame.SRCALPHA)
                fila.fill((22, 10, 12, 180) if row % 2 == 0 else (12, 6, 8, 160))
                pygame.draw.rect(fila, (70, 12, 14, 140), (0, 0, col_w_c, 34), 1, border_radius=4)
                self.pantalla.blit(fila, (col_x, ry))
                # Cuadrito de color como indicador visual (sin emoji)
                pygame.draw.rect(self.pantalla, dot_col,
                                 (col_x + 6, ry + 9, 10, 14), border_radius=2)
                pygame.draw.rect(self.pantalla, (255, 255, 255),
                                 (col_x + 6, ry + 9, 10, 14), 1, border_radius=2)
                # Texto
                t_desc = f_ctrl.render(desc, True, (215, 210, 220))
                self.pantalla.blit(t_desc, (col_x + 22, ry + 8))

        # Separador superior a los selectores
        sep_y1 = py_ + 175
        pygame.draw.line(self.pantalla, (110, 10, 14),
                         (px_ + 20, sep_y1), (px_ + pw - 20, sep_y1), 1)

        # ── Selectores de Personaje y Dificultad ──
        f_sel = pygame.font.Font(None, 28)
        
        # Color del texto según selección
        col_skin = (255, 215, 50) if self.menu_seleccion == 0 else (200, 200, 200)
        col_dif  = (255, 215, 50) if self.menu_seleccion == 1 else (200, 200, 200)

        # Selector de Skin
        skin_nombres = ["1. Azul/Castaño", "2. Rojo/Rubio", "3. Táctico Ninja"]
        texto_skin = f"Personaje:  <  {skin_nombres[self.skin_actual]}  >"
        r_skin = f_sel.render(texto_skin, True, col_skin)
        self.pantalla.blit(r_skin, r_skin.get_rect(center=(cx, py_ + 195)))
        
        # Dibujar sprite del personaje seleccionado
        surf_skin = self.sm.player_skins[self.skin_actual][0]
        surf_skin_menu = pygame.transform.scale(surf_skin, (surf_skin.get_width()*2, surf_skin.get_height()*2))
        self.pantalla.blit(surf_skin_menu, surf_skin_menu.get_rect(center=(cx, py_ + 265)))

        # Selector de Dificultad
        dificultades = ["FÁCIL", "NORMAL", "DIFÍCIL"]
        base_cols_dif = [(100, 220, 100), (220, 220, 100), (255, 80, 80)]
        
        c_d = base_cols_dif[self.dificultad]
        if self.menu_seleccion != 1:
            c_d = (c_d[0]//2, c_d[1]//2, c_d[2]//2)

        texto_dif = f"Dificultad:  <  {dificultades[self.dificultad]}  >"
        r_dif = f_sel.render(texto_dif, True, c_d)
        
        # Selector de Controles
        modos_ctrl = ["TECLADO / MANDO", "TÁCTIL (MÓVIL)"]
        c_ctrl = (255, 215, 50) if self.menu_seleccion == 2 else (100, 100, 100)
        texto_ctrl = f"Controles:  <  {modos_ctrl[1 if self.modo_tactil else 0]}  >"
        r_ctrl = f_sel.render(texto_ctrl, True, c_ctrl)
        
        # Indicadores de selección manual a los lados
        if self.menu_seleccion == 0:
            pygame.draw.circle(self.pantalla, (255, 215, 50), (cx - 170, py_ + 195), 4)
            pygame.draw.circle(self.pantalla, (255, 215, 50), (cx + 170, py_ + 195), 4)
        elif self.menu_seleccion == 1:
            pygame.draw.circle(self.pantalla, (255, 215, 50), (cx - 150, py_ + 335), 4)
            pygame.draw.circle(self.pantalla, (255, 215, 50), (cx + 150, py_ + 335), 4)
        elif self.menu_seleccion == 2:
            pygame.draw.circle(self.pantalla, (255, 215, 50), (cx - 190, py_ + 380), 4)
            pygame.draw.circle(self.pantalla, (255, 215, 50), (cx + 190, py_ + 380), 4)

        self.pantalla.blit(r_dif, r_dif.get_rect(center=(cx, py_ + 335)))
        self.pantalla.blit(r_ctrl, r_ctrl.get_rect(center=(cx, py_ + 380)))

        f_hint = pygame.font.Font(None, 20)
        hint = f_hint.render("Usa las Flechas / D-pad para cambiar", True, (150, 150, 150))
        self.pantalla.blit(hint, hint.get_rect(center=(cx, py_ + 410)))

        # Separador inferior
        sep_y = py_ + ph - 82
        pygame.draw.line(self.pantalla, (110, 10, 14),
                         (px_ + 20, sep_y), (px_ + pw - 20, sep_y), 1)

        # Botón JUGAR pulsante con glow
        pulse = int(math.sin(t * 0.004) * 10)
        bw, bh = 290 + pulse, 52
        bx_ = cx - bw // 2
        by_ = sep_y + 14
        g_a = max(0, int(80 + math.sin(t * 0.004) * 60))
        glow_b = pygame.Surface((bw + 20, bh + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_b, (200, 15, 20, g_a),
                         (0, 0, bw + 20, bh + 20), border_radius=14)
        self.pantalla.blit(glow_b, (bx_ - 10, by_ - 10))
        pygame.draw.rect(self.pantalla, (165, 10, 15), (bx_, by_, bw, bh), border_radius=10)
        pygame.draw.rect(self.pantalla, (225, 22, 26), (bx_, by_, bw, bh), 3, border_radius=10)
        f_btn = pygame.font.Font(None, 36)
        btn_col = (255, 245, 245) if (t // 500) % 2 == 0 else (255, 195, 195)
        txt_play = ">> PRESIONA A" if self.mando.conectado else ">> PRESIONA ESPACIO"
        btn_txt = f_btn.render(txt_play, True, btn_col)
        self.pantalla.blit(btn_txt, btn_txt.get_rect(center=(cx, by_ + bh // 2)))

        # Pie de página
        f_pie = pygame.font.Font(None, 18)
        ver = f_pie.render(
            "v1.0  •  5 Mapas  •  4 Armas  •  Power-ups  •  F11 = Pantalla Completa",
            True, (80, 75, 90))
        self.pantalla.blit(ver, ver.get_rect(center=(cx, alto - 16)))

    # ── Pantalla de fin ─────────────────────────────────────────────────────
    def dibujar_fin(self):
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((30, 0, 0, 200))
        self.pantalla.blit(overlay, (0, 0))

        f_grande = pygame.font.Font(None, 82)
        f_med    = pygame.font.Font(None, 40)
        f_peq    = pygame.font.Font(None, 28)

        muerte = f_grande.render("HAS MUERTO", True, COLOR_ROJO)
        self.pantalla.blit(muerte, muerte.get_rect(center=(ANCHO // 2, ALTO // 3)))

        stats = [
            f"Oleada alcanzada: {self.oleada}",
            f"Zombies eliminados: {self.zombies_eliminados}",
            f"Puntuación final: {self.puntuacion}",
        ]
        for i, stat in enumerate(stats):
            txt = f_med.render(stat, True, COLOR_TEXTO)
            self.pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, ALTO // 2 + i * 40)))

        txt_restart = "A: Jugar de nuevo  |  B: Menú Principal" if self.mando.conectado else "ESPACIO: Jugar de nuevo  |  ESC: Menú Principal"
        reiniciar = f_peq.render(txt_restart, True, COLOR_ORO)
        self.pantalla.blit(reiniciar, reiniciar.get_rect(center=(ANCHO // 2, ALTO - 90)))


if __name__ == "__main__":
    juego = Juego()
    juego.run()
