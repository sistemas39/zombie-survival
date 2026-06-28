import pygame
import math

class VirtualJoystick:
    def __init__(self, cx, cy, radius):
        self.cx = cx
        self.cy = cy
        self.base_radius = radius
        self.knob_radius = radius // 2
        
        self.active = False
        self.touch_id = None
        
        self.knob_x = cx
        self.knob_y = cy
        
        # Valores de salida
        self.dx = 0.0
        self.dy = 0.0
        self.angle = 0.0
        
    def procesar_toque_down(self, tid, tx, ty):
        if self.active: return False
        # Si presiona dentro o cerca del área de la base
        dist = math.hypot(tx - self.cx, ty - self.cy)
        if dist <= self.base_radius * 1.5:  # Margen extra
            self.active = True
            self.touch_id = tid
            self.update_pos(tx, ty)
            return True
        return False
        
    def procesar_toque_motion(self, tid, tx, ty):
        if self.active and self.touch_id == tid:
            self.update_pos(tx, ty)
            return True
        return False
        
    def procesar_toque_up(self, tid):
        if self.active and self.touch_id == tid:
            self.active = False
            self.touch_id = None
            self.knob_x = self.cx
            self.knob_y = self.cy
            self.dx = 0.0
            self.dy = 0.0
            return True
        return False
        
    def update_pos(self, tx, ty):
        # Calcular vector
        vx = tx - self.cx
        vy = ty - self.cy
        dist = math.hypot(vx, vy)
        
        # Clamp al borde de la base
        if dist > self.base_radius:
            vx = (vx / dist) * self.base_radius
            vy = (vy / dist) * self.base_radius
            
        self.knob_x = self.cx + vx
        self.knob_y = self.cy + vy
        
        # Normalizar dx, dy [-1, 1]
        self.dx = vx / self.base_radius
        self.dy = vy / self.base_radius
        self.angle = math.degrees(math.atan2(-self.dy, self.dx))
        
    def draw(self, surface):
        # Base (transparente oscura)
        pygame.draw.circle(surface, (50, 50, 50, 100), (self.cx, self.cy), self.base_radius)
        pygame.draw.circle(surface, (150, 150, 150, 150), (self.cx, self.cy), self.base_radius, 2)
        # Knob
        color_knob = (200, 200, 200, 200) if self.active else (150, 150, 150, 150)
        pygame.draw.circle(surface, color_knob, (int(self.knob_x), int(self.knob_y)), self.knob_radius)

class TouchButton:
    def __init__(self, rect, texto, color=(100, 100, 100)):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.color = color
        self.active = False
        self.touch_id = None
        self.is_clicked = False
        
    def update(self):
        self.is_clicked = False
        
    def procesar_toque_down(self, tid, tx, ty):
        if self.active: return False
        if self.rect.collidepoint(tx, ty):
            self.active = True
            self.touch_id = tid
            return True
        return False
        
    def procesar_toque_up(self, tid, tx, ty):
        if self.active and self.touch_id == tid:
            self.active = False
            self.touch_id = None
            if self.rect.collidepoint(tx, ty):
                self.is_clicked = True
            return True
        return False
        
    def draw(self, surface, font):
        c = (min(255, self.color[0]+50), min(255, self.color[1]+50), min(255, self.color[2]+50), 200) if self.active else (*self.color, 150)
        pygame.draw.rect(surface, c, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200,200,200, 180), self.rect, 2, border_radius=8)
        
        txt = font.render(self.texto, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=self.rect.center))

class TouchManager:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        
        j_radius = int(alto * 0.15)
        
        # Izquierdo (Mover)
        self.j_izq = VirtualJoystick(j_radius + 40, alto - j_radius - 40, j_radius)
        # Derecho (Apuntar / Disparar)
        self.j_der = VirtualJoystick(ancho - j_radius - 40, alto - j_radius - 40, j_radius)
        
        # Botones
        self.btn_tienda = TouchButton((ancho - 140, 20, 120, 50), "TIENDA", (60, 60, 180))
        self.btn_arma = TouchButton((ancho - j_radius*2 - 100, alto - 80, 80, 60), "ARMA", (180, 120, 40))
        
        self.font = pygame.font.Font(None, 24)
        
    def update(self):
        self.btn_tienda.update()
        self.btn_arma.update()
        
    def manejar_evento(self, evento):
        # Mapeo de FINGER (Touch) y MOUSE (simulación en PC)
        if evento.type == pygame.FINGERDOWN:
            tx = evento.x * self.ancho
            ty = evento.y * self.alto
            self._handle_down(evento.finger_id, tx, ty)
        elif evento.type == pygame.FINGERMOTION:
            tx = evento.x * self.ancho
            ty = evento.y * self.alto
            self._handle_motion(evento.finger_id, tx, ty)
        elif evento.type == pygame.FINGERUP:
            tx = evento.x * self.ancho
            ty = evento.y * self.alto
            self._handle_up(evento.finger_id, tx, ty)
            
        # Simulación táctil con ratón para poder probar en PC
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._handle_down(-1, evento.pos[0], evento.pos[1])
        elif evento.type == pygame.MOUSEMOTION and (evento.buttons[0] or self.j_izq.touch_id == -1 or self.j_der.touch_id == -1):
            self._handle_motion(-1, evento.pos[0], evento.pos[1])
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self._handle_up(-1, evento.pos[0], evento.pos[1])

    def _handle_down(self, tid, tx, ty):
        if self.btn_tienda.procesar_toque_down(tid, tx, ty): return
        if self.btn_arma.procesar_toque_down(tid, tx, ty): return
        if self.j_izq.procesar_toque_down(tid, tx, ty): return
        if self.j_der.procesar_toque_down(tid, tx, ty): return

    def _handle_motion(self, tid, tx, ty):
        self.j_izq.procesar_toque_motion(tid, tx, ty)
        self.j_der.procesar_toque_motion(tid, tx, ty)

    def _handle_up(self, tid, tx, ty):
        self.btn_tienda.procesar_toque_up(tid, tx, ty)
        self.btn_arma.procesar_toque_up(tid, tx, ty)
        self.j_izq.procesar_toque_up(tid)
        self.j_der.procesar_toque_up(tid)

    def draw(self, surface):
        # Es necesario crear una capa semitransparente para los controles táctiles
        # pygame soporta alfa en superficies, pero los primitivos con alfa directo a veces fallan.
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        
        self.j_izq.draw(overlay)
        self.j_der.draw(overlay)
        self.btn_tienda.draw(overlay, self.font)
        self.btn_arma.draw(overlay, self.font)
        
        surface.blit(overlay, (0, 0))

    # ---- Getters de input ----
    def get_movimiento(self):
        return self.j_izq.dx, self.j_izq.dy
        
    def get_punteria(self):
        return self.j_der.angle
        
    def disparando(self):
        # Si está estirando el joystick derecho más de 10% de su tamaño
        return self.j_der.active and math.hypot(self.j_der.dx, self.j_der.dy) > 0.1
