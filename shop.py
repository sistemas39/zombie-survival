import pygame


class Shop:
    def __init__(self, ancho, alto, sprite_manager):
        self.ancho = ancho
        self.alto  = alto
        self.sm    = sprite_manager

        self.w = 700
        self.h = 520
        self.x = (ancho - self.w) // 2
        self.y = (alto  - self.h) // 2

        self.nivel_cadencia  = 0
        self.nivel_danio     = 0
        self.nivel_municion  = 0
        self.nivel_velocidad = 0

        # Navegacion con mando (indice del boton seleccionado)
        self.sel = 0          # boton actualmente seleccionado por mando
        self.usar_mando = False

        # Colores
        self.C_BG    = (18,  18,  28, 245)
        self.C_BORDE = (255, 200,   7, 255)
        self.C_TEXTO = (235, 235, 255)
        self.C_BTN   = (38,  43,  60)
        self.C_HOVER = (55,  65,  90)
        self.C_SEL   = (40,  90, 150)   # seleccion por mando
        self.C_LOCK  = (22,  22,  30)
        self.C_ORO   = (255, 200,   7)
        self.C_ROJO  = (220,  25,  50)
        self.C_VERDE = (50,  200,  70)

        self.buttons = []

    # ─────────────────────────────────────────────────────────────────────────
    def draw(self, surface, jugador, armas, mouse_pos):
        # Detectar si el raton se mueve (para alternar entre mando y raton)
        if mouse_pos != getattr(self, "_last_mouse", mouse_pos):
            self.usar_mando = False
        self._last_mouse = mouse_pos

        # Overlay oscuro
        ov = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        ov.fill((6, 6, 12, 175))
        surface.blit(ov, (0, 0))

        # Caja de la tienda
        caja = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        caja.fill(self.C_BG)
        pygame.draw.rect(caja, self.C_BORDE, (0, 0, self.w, self.h), 4, border_radius=14)
        surface.blit(caja, (self.x, self.y))

        f_tit = pygame.font.Font(None, 38)
        f_med = pygame.font.Font(None, 24)
        f_peq = pygame.font.Font(None, 18)

        # Titulo (sin emoji)
        tit = f_tit.render("[ TIENDA DE MEJORAS ]", True, self.C_ORO)
        surface.blit(tit, tit.get_rect(center=(self.ancho // 2, self.y + 32)))

        # Monedas (sin emoji)
        m_txt = f_med.render(f"Monedas: {jugador.monedas}", True, self.C_ORO)
        surface.blit(m_txt, (self.x + self.w - m_txt.get_width() - 20, self.y + 18))

        sub = f_peq.render("Gasta monedas en armas y mejoras para sobrevivir mas.", True, (160, 160, 185))
        surface.blit(sub, sub.get_rect(center=(self.ancho // 2, self.y + 58)))

        # ── Definir botones ──────────────────────────────────────────────────
        self.buttons = []

        col_w   = 218
        col_h   = 64
        col_gap = 8
        row1_y = self.y + 78
        row2_y = row1_y + col_h + col_gap
        row3_y = row2_y + col_h + col_gap
        row4_y = row3_y + col_h + col_gap

        x1 = self.x + 10
        x2 = x1 + col_w + col_gap
        x3 = x2 + col_w + col_gap

        # ── Fila 1: Armas ────────────────────────────────────────────────────
        escopeta = armas["escopeta"]
        self._btn("comprar_escopeta", x1, row1_y, col_w, col_h,
                  "Desbloquear Escopeta" if not escopeta.unlocked else "[OK] Escopeta",
                  escopeta.cost if not escopeta.unlocked else 0,
                  not escopeta.unlocked,
                  "6 perdigones en abanico")

        rifle = armas["rifle"]
        self._btn("comprar_rifle", x2, row1_y, col_w, col_h,
                  "Desbloquear Rifle" if not rifle.unlocked else "[OK] Rifle",
                  rifle.cost if not rifle.unlocked else 0,
                  not rifle.unlocked,
                  "Auto, alta velocidad")

        metralleta = armas["metralleta"]
        self._btn("comprar_metralleta", x3, row1_y, col_w, col_h,
                  "Desbloquear Metralleta" if not metralleta.unlocked else "[OK] Metralleta",
                  metralleta.cost if not metralleta.unlocked else 0,
                  not metralleta.unlocked,
                  "60 balas, cadencia maxima")

        # ── Fila 2: Mejoras de armas ─────────────────────────────────────────
        costo_cad = int(50 * (1.4 ** self.nivel_cadencia))
        self._btn("mejorar_cadencia", x1, row2_y, col_w, col_h,
                  f"Cadencia Nv.{self.nivel_cadencia + 1}",
                  costo_cad, True,
                  "Dispara más rápido")

        costo_dmg = int(60 * (1.4 ** self.nivel_danio))
        self._btn("mejorar_danio", x2, row2_y, col_w, col_h,
                  f"Daño Nv.{self.nivel_danio + 1}",
                  costo_dmg, True,
                  "+15% daño (todas)")

        costo_mun = int(50 * (1.4 ** self.nivel_municion))
        self._btn("mejorar_municion", x3, row2_y, col_w, col_h,
                  f"Cargador Nv.{self.nivel_municion + 1}",
                  costo_mun, True,
                  "+30% cap. munición")

        # ── Fila 3: Jugador ───────────────────────────────────────────────────
        max_vel = jugador.speed_upgrades >= 5
        costo_vel = int(40 * (1.4 ** self.nivel_velocidad))
        self._btn("mejorar_velocidad", x1, row3_y, col_w + col_gap + col_w, col_h,
                  f"Velocidad Nv.{self.nivel_velocidad + 1}",
                  costo_vel, not max_vel,
                  "Te mueves mas rapido" if not max_vel else "NIVEL MAXIMO")

        max_h = jugador.max_vidas >= 5
        self._btn("max_vidas", x3, row3_y, col_w, col_h,
                  "Corazon Extra",
                  100, not max_h,
                  "+1 vida maxima" if not max_h else "MAXIMO ALCANZADO")

        # ── Fila 4: Curar y Cerrar ───────────────────────────────────────────
        curar_ok = jugador.vidas < jugador.max_vidas
        self._btn("curar", x1, row4_y, col_w + col_gap + col_w, col_h,
                  "Curar 1 Corazon",
                  25, curar_ok,
                  "Recupera una vida" if curar_ok else "VIDA COMPLETA")

        self._btn("cerrar_tienda", x3, row4_y, col_w, col_h,
                  "Cerrar Tienda",
                  0, True,
                  "Volver al juego")

        # Clamp indice de seleccion
        n = len(self.buttons)
        if n > 0:
            self.sel = self.sel % n

        # ── Renderizar botones ────────────────────────────────────────────────
        for i, btn in enumerate(self.buttons):
            rect  = pygame.Rect(btn["x"], btn["y"], btn["w"], btn["h"])
            hover_mouse = rect.collidepoint(mouse_pos) and btn["activo"] and not self.usar_mando
            sel_mando   = (i == self.sel) and self.usar_mando

            if not btn["activo"]:
                bg = self.C_LOCK
            elif sel_mando:
                bg = self.C_SEL
            elif hover_mouse:
                bg = self.C_HOVER
            else:
                bg = self.C_BTN

            pygame.draw.rect(surface, bg, rect, border_radius=7)

            # Borde: dorado si hover/sel, azul brillante si sel por mando
            if sel_mando:
                borde_c = (80, 180, 255)
            elif hover_mouse:
                borde_c = self.C_ORO
            else:
                borde_c = (85, 85, 100)
            pygame.draw.rect(surface, borde_c, rect, 2, border_radius=7)

            # Indicador triangular si es la seleccion del mando
            if sel_mando:
                mid_y = btn["y"] + btn["h"] // 2
                pygame.draw.polygon(surface, (80, 180, 255),
                                    [(btn["x"] - 10, mid_y - 6),
                                     (btn["x"] - 10, mid_y + 6),
                                     (btn["x"] - 2,  mid_y)])

            # Titulo
            col_tit = self.C_TEXTO if btn["activo"] else (105, 105, 115)
            t = f_med.render(btn["titulo"], True, col_tit)
            if t.get_width() > btn["w"] - 10:
                t = pygame.transform.scale(t, (btn["w"] - 10, t.get_height()))
            surface.blit(t, (btn["x"] + 8, btn["y"] + 10))

            # Descripcion
            d = f_peq.render(btn["desc"], True, (150, 150, 170) if btn["activo"] else (75, 75, 85))
            surface.blit(d, (btn["x"] + 8, btn["y"] + 34))

            # Costo
            if btn["costo"] > 0:
                col_c = self.C_ORO if jugador.monedas >= btn["costo"] else self.C_ROJO
                if not btn["activo"]:
                    col_c = (80, 80, 90)
                c_t = f_med.render(f"{btn['costo']} $", True, col_c)
                surface.blit(c_t, (btn["x"] + btn["w"] - c_t.get_width() - 8, btn["y"] + 10))

        # Instruccion inferior  —  cambia si hay mando activo
        if self.usar_mando:
            pie_str = "D-pad/Stick  Navegar  |  A  Comprar  |  B  Volver al juego"
        else:
            pie_str = "TAB / E / ESC  Volver al juego  |  Haz clic en un item para comprar"
        pie = f_med.render(pie_str, True, (130, 130, 155))
        surface.blit(pie, pie.get_rect(center=(self.ancho // 2, self.y + self.h - 20)))

    # ─────────────────────────────────────────────────────────────────────────
    def _btn(self, id, x, y, w, h, titulo, costo, activo, desc):
        self.buttons.append(dict(id=id, x=x, y=y, w=w, h=h,
                                  titulo=titulo, costo=costo,
                                  activo=activo, desc=desc))

    # ── Navegacion con mando ──────────────────────────────────────────────────
    def mando_navegar(self, direccion):
        """Mueve la seleccion del mando. direccion: +1 o -1."""
        self.usar_mando = True
        n = len(self.buttons)
        if n == 0:
            return
        # Buscar el proximo boton activo en la direccion dada
        for _ in range(n):
            self.sel = (self.sel + direccion) % n
            if self.buttons[self.sel]["activo"]:
                break

    def mando_confirmar(self, jugador, armas):
        """Compra el item actualmente seleccionado con el mando."""
        self.usar_mando = True
        if not self.buttons:
            return False
        btn = self.buttons[self.sel]
        if not btn["activo"]:
            return False
        return self._ejecutar_compra(btn, jugador, armas)

    # ── Click con raton ───────────────────────────────────────────────────────
    def handle_click(self, mouse_pos, jugador, armas):
        self.usar_mando = False
        for btn in self.buttons:
            rect = pygame.Rect(btn["x"], btn["y"], btn["w"], btn["h"])
            if rect.collidepoint(mouse_pos) and btn["activo"]:
                return self._ejecutar_compra(btn, jugador, armas)
        return False

    # ── Logica de compra comun ────────────────────────────────────────────────
    def _ejecutar_compra(self, btn, jugador, armas):
        if btn["id"] == "cerrar_tienda":
            return "CERRAR"
            
        if jugador.monedas < btn["costo"]:
            return False
            
        jugador.monedas -= btn["costo"]
        pid = btn["id"]
        
        if pid == "comprar_escopeta":
            armas["escopeta"].unlocked = True
        elif pid == "comprar_rifle":
            armas["rifle"].unlocked = True
        elif pid == "comprar_metralleta":
            armas["metralleta"].unlocked = True
        elif pid == "mejorar_cadencia":
            self.nivel_cadencia += 1
            for a in armas.values():
                a.upgrade_fire_rate()
        elif pid == "mejorar_danio":
            self.nivel_danio += 1
            for a in armas.values():
                a.upgrade_damage()
        elif pid == "mejorar_municion":
            self.nivel_municion += 1
            for a in armas.values():
                a.upgrade_ammo()
        elif pid == "mejorar_velocidad":
            self.nivel_velocidad += 1
            jugador.speed_upgrades += 1
            jugador.velocidad += 0.5
        elif pid == "max_vidas":
            jugador.max_vidas += 1
            jugador.vidas += 1
        elif pid == "curar":
            jugador.vidas += 1
        return True
