"""
mando.py — Soporte para mando de Xbox (y cualquier gamepad SDL2-compatible).
Detecta automáticamente el primer mando conectado y provee una interfaz
limpia para movimiento, puntería, disparo y botones.

Mapeo estándar Xbox (SDL2 / pygame 2.x):
  Ejes:
    0  = Stick izquierdo X    (-1 izq, +1 der)
    1  = Stick izquierdo Y    (-1 arriba, +1 abajo)
    2  = Gatillo izquierdo LT (0.0 → 1.0)
    3  = Stick derecho X
    4  = Stick derecho Y
    5  = Gatillo derecho RT   (0.0 → 1.0)
  Botones:
    0  = A        1  = B        2  = X       3  = Y
    4  = LB       5  = RB       6  = Back    7  = Start
    8  = LS click 9  = RS click
  Hat 0 = D-pad (x, y)
"""
import pygame
import math


# Zona muerta del stick (evita drift)
DEADZONE = 0.18


class GestorMando:
    # ── Botones ──────────────────────────────────────────────────────────────
    BTN_A     = 0
    BTN_B     = 1
    BTN_X     = 2
    BTN_Y     = 3
    BTN_LB    = 4
    BTN_RB    = 5
    BTN_BACK  = 6
    BTN_START = 7

    def __init__(self):
        pygame.joystick.init()
        self.mando      = None
        self.conectado  = False
        self.nombre     = ""
        self._intentar_conectar()

    # ── Conexión ─────────────────────────────────────────────────────────────

    def _intentar_conectar(self):
        count = pygame.joystick.get_count()
        if count > 0:
            self.mando = pygame.joystick.Joystick(0)
            self.mando.init()
            self.conectado = True
            self.nombre    = self.mando.get_name()
            print(f"[MANDO] Conectado: {self.nombre}")
        else:
            self.conectado = False
            self.nombre    = ""

    def manejar_evento(self, evento):
        """Llama desde el loop principal para detectar plug/unplug."""
        if evento.type == pygame.JOYDEVICEADDED:
            self._intentar_conectar()
        elif evento.type == pygame.JOYDEVICEREMOVED:
            print("[MANDO] Desconectado")
            self.conectado = False
            self.mando     = None
            self.nombre    = ""

    # ── Lectura de ejes ───────────────────────────────────────────────────────

    def _eje(self, idx):
        """Lee un eje con zona muerta aplicada."""
        if not self.conectado:
            return 0.0
        try:
            v = self.mando.get_axis(idx)
            return 0.0 if abs(v) < DEADZONE else v
        except Exception:
            return 0.0

    def get_movimiento(self):
        """
        Devuelve (dx, dy) del stick izquierdo, cada uno en [-1, 1].
        Normalizado si el vector supera la magnitud 1.
        """
        x = self._eje(0)
        y = self._eje(1)
        mag = math.hypot(x, y)
        if mag > 1.0:
            x /= mag
            y /= mag
        return x, y

    def get_punteria(self):
        """
        Devuelve el ángulo (grados) del stick derecho hacia donde apunta,
        o None si el stick está en reposo.
        Eje 3 = Right X, Eje 4 = Right Y.
        """
        rx = self._eje(3)
        ry = self._eje(4)
        if rx == 0.0 and ry == 0.0:
            return None
        return math.degrees(math.atan2(-ry, rx))

    def get_rt(self):
        """Gatillo derecho (RT): 0.0 = suelto, 1.0 = fondo. Eje 5."""
        if not self.conectado:
            return 0.0
        try:
            v = self.mando.get_axis(5)
            # En algunos drivers RT va de -1 a +1; lo normalizamos a [0, 1]
            v = (v + 1.0) / 2.0 if v < 0 else v
            return v
        except Exception:
            return 0.0

    def disparando(self):
        """True si el gatillo derecho supera el umbral de disparo."""
        return self.get_rt() > 0.25

    # ── Botones ───────────────────────────────────────────────────────────────

    def boton(self, btn):
        """True si el botón indicado está presionado."""
        if not self.conectado:
            return False
        try:
            return bool(self.mando.get_button(btn))
        except Exception:
            return False

    def hat(self):
        """D-pad: (x, y) donde x∈{-1,0,1} y y∈{-1,0,1}."""
        if not self.conectado:
            return (0, 0)
        try:
            return self.mando.get_hat(0)
        except Exception:
            return (0, 0)

    # ── Vibración (si el hardware lo soporta) ─────────────────────────────────

    def vibrar(self, intensidad_baja=0.3, intensidad_alta=0.5, duracion_ms=120):
        """Rumble corto. Solo funciona en pygame 2.0+ con SDL2 rumble."""
        if not self.conectado:
            return
        try:
            self.mando.rumble(intensidad_baja, intensidad_alta, duracion_ms)
        except Exception:
            pass   # no todos los mandos soportan rumble
