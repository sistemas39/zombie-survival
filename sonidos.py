"""
sonidos.py  —  Generación procedural de audio para Supervivencia Zombie 2D
Todos los sonidos se sintetizan con numpy; no se requieren archivos externos.
"""

import pygame
import numpy as np
import math
import random

TASA = 44100   # Hz
CANALES = 1    # mono

# ---------------------------------------------------------------------------
# Utilidades de síntesis
# ---------------------------------------------------------------------------
def _normalizar(arr, vol=0.85):
    maximo = np.max(np.abs(arr))
    if maximo > 0:
        arr = arr / maximo * vol
    return arr

def _envolvente(frames, ataque=0.01, decaimiento=0.08, sustain=0.6, release=0.15):
    """Curva ADSR → array de factores float."""
    env = np.ones(frames, dtype=np.float32)
    a = int(frames * ataque)
    d = int(frames * decaimiento)
    r = int(frames * release)
    s = frames - a - d - r

    if a > 0: env[:a]         = np.linspace(0, 1, a)
    if d > 0: env[a:a+d]      = np.linspace(1, sustain, d)
    if s > 0: env[a+d:a+d+s]  = sustain
    if r > 0: env[a+d+s:]     = np.linspace(sustain, 0, r)
    return env

def _hacer_sonido(arr_float):
    """Convierte float[-1,1] a int16 estéreo y crea Sound."""
    arr = np.clip(arr_float, -1, 1)
    estereo = np.column_stack([arr, arr])
    pcm = (estereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(pcm)

def _seno(freq, frames):
    t = np.arange(frames, dtype=np.float32) / TASA
    return np.sin(2 * np.pi * freq * t)

def _cuadrada(freq, frames):
    return np.sign(_seno(freq, frames))

def _sierra(freq, frames):
    t = np.arange(frames, dtype=np.float32) / TASA
    return 2 * (t * freq - np.floor(t * freq + 0.5))

def _ruido(frames):
    return np.random.uniform(-1, 1, frames).astype(np.float32)

# ---------------------------------------------------------------------------
# Efectos de sonido individuales
# ---------------------------------------------------------------------------

def _sfx_pistola():
    frames = int(TASA * 0.18)
    # Mezcla de ruido filtrado + tono decayente
    ruido = _ruido(frames)
    tono  = _seno(180, frames) * np.exp(-np.arange(frames) / (TASA * 0.04))
    raw   = ruido * 0.7 + tono * 0.5
    env   = _envolvente(frames, 0.002, 0.05, 0.0, 0.3)
    return _hacer_sonido(_normalizar(raw * env, 0.80))

def _sfx_escopeta():
    frames = int(TASA * 0.30)
    ruido  = _ruido(frames)
    sub    = _seno(80, frames) * np.exp(-np.arange(frames) / (TASA * 0.06))
    raw    = ruido * 0.75 + sub * 0.6
    env    = _envolvente(frames, 0.002, 0.08, 0.0, 0.3)
    return _hacer_sonido(_normalizar(raw * env, 0.90))

def _sfx_rifle():
    frames = int(TASA * 0.10)
    ruido  = _ruido(frames)
    tono   = _seno(280, frames) * np.exp(-np.arange(frames) / (TASA * 0.02))
    raw    = ruido * 0.65 + tono * 0.45
    env    = _envolvente(frames, 0.001, 0.03, 0.0, 0.2)
    return _hacer_sonido(_normalizar(raw * env, 0.70))

def _sfx_zombie_muere():
    frames = int(TASA * 0.45)
    t      = np.arange(frames, dtype=np.float32) / TASA
    # Gruñido descendente
    freq_env = 200 * np.exp(-t * 4)
    raw    = np.sin(2 * np.pi * freq_env * t)
    raw   += _ruido(frames) * 0.3
    env    = _envolvente(frames, 0.01, 0.05, 0.5, 0.3)
    return _hacer_sonido(_normalizar(raw * env, 0.75))

def _sfx_daño_jugador():
    frames = int(TASA * 0.25)
    t      = np.arange(frames, dtype=np.float32) / TASA
    # Tono grave distorsionado
    raw    = np.sin(2 * np.pi * 130 * t) + _ruido(frames) * 0.4
    raw    = np.clip(raw * 3, -1, 1)   # saturación para dar impacto
    env    = _envolvente(frames, 0.005, 0.07, 0.2, 0.4)
    return _hacer_sonido(_normalizar(raw * env, 0.85))

def _sfx_moneda():
    frames = int(TASA * 0.20)
    # Ding brillante: seno + armónico
    raw    = _seno(1200, frames) * 0.6 + _seno(2400, frames) * 0.3
    env    = _envolvente(frames, 0.005, 0.03, 0.2, 0.6)
    return _hacer_sonido(_normalizar(raw * env, 0.65))

def _sfx_corazon():
    frames = int(TASA * 0.40)
    # Campana suave con dos tonos armoniosos
    raw    = (_seno(523, frames) * 0.5 +   # Do5
              _seno(659, frames) * 0.35 +  # Mi5
              _seno(784, frames) * 0.25)   # Sol5
    env    = _envolvente(frames, 0.01, 0.05, 0.4, 0.5)
    return _hacer_sonido(_normalizar(raw * env, 0.70))

def _sfx_oleada():
    """Fanfarria corta de "oleada comienza"."""
    frames = int(TASA * 0.55)
    notas  = [220, 277, 330, 440]   # La, Do#, Mi, La (acorde menor)
    raw    = np.zeros(frames, dtype=np.float32)
    seg    = frames // len(notas)
    for i, hz in enumerate(notas):
        ini = i * seg
        fin = ini + seg
        raw[ini:fin] = _seno(hz, seg) * 0.6 + _seno(hz * 2, seg) * 0.2
    env = _envolvente(frames, 0.02, 0.10, 0.6, 0.20)
    return _hacer_sonido(_normalizar(raw * env, 0.70))

def _sfx_game_over():
    """Melodía triste descendente."""
    notas  = [440, 370, 330, 277, 220]   # descendente cromático
    dur_n  = 0.30
    raw    = np.array([], dtype=np.float32)
    for hz in notas:
        f = int(TASA * dur_n)
        seg = _seno(hz, f) * 0.55 + _seno(hz * 0.5, f) * 0.25
        env = _envolvente(f, 0.02, 0.05, 0.7, 0.25)
        raw = np.concatenate([raw, seg * env])
    return _hacer_sonido(_normalizar(raw, 0.75))

# ---------------------------------------------------------------------------
# Música de fondo — bucle de ~4 segundos
# ---------------------------------------------------------------------------
def _generar_musica_fondo():
    """
    Genera un bucle de música spooky:
    - Bajo pulsante (onda cuadrada grave)
    - Drone ambiental (ondas senoidales desfasadas)
    - Golpes de batería simples
    """
    bpm    = 100
    beat   = 60.0 / bpm
    compas = beat * 4        # 4 beats por compás
    loops  = 2               # 2 compases → ~4.8 s
    total  = int(TASA * compas * loops)
    mezcla = np.zeros(total, dtype=np.float32)

    # ── Bajo pulsante ──
    patron_bajo = [110, 0, 110, 0, 82, 0, 110, 0]   # notas (0 = silencio)
    paso        = int(TASA * beat / 2)               # corchea
    for rep in range(loops * 4):
        nota = patron_bajo[rep % len(patron_bajo)]
        if nota == 0: continue
        ini = rep * paso
        fin = min(ini + paso, total)
        f   = fin - ini
        t   = np.arange(f, dtype=np.float32) / TASA
        sig = _cuadrada(nota, f) * 0.30
        env = np.exp(-t * 5)   # decaimiento rápido
        mezcla[ini:fin] += sig * env

    # ── Drone ambiental ──
    t_all = np.arange(total, dtype=np.float32) / TASA
    drone  = (_seno(55, total) * 0.18 +
              _seno(55.3, total) * 0.12 +   # ligero desfase → chorus
              _seno(82.4, total) * 0.10)
    mezcla += drone

    # ── Batería simple: kick + hi-hat ──
    durk = int(TASA * 0.12)
    durh = int(TASA * 0.05)
    kicks = [0, beat * 2]
    hats  = [beat * 0.5, beat * 1.5, beat * 2.5, beat * 3.5]

    for rep in range(loops * 4):
        for k in kicks:
            pos = int((rep / 4 * compas + k) * TASA)
            if pos + durk > total: continue
            t_k = np.arange(durk, dtype=np.float32) / TASA
            kick = _seno(80, durk) * np.exp(-t_k * 40) * 0.45
            mezcla[pos:pos + durk] += kick
        for h in hats:
            pos = int((rep / 4 * compas + h) * TASA)
            if pos + durh > total: continue
            hat = _ruido(durh) * np.exp(-np.arange(durh, dtype=np.float32) * 80 / TASA) * 0.18
            mezcla[pos:pos + durh] += hat

    # ── Melodía espeluznante (arpeggio menor) ──
    escala = [220, 261, 277, 311, 329]  # La menor pentatónica
    for rep in range(loops * 8):
        nota = escala[rep % len(escala)]
        ini  = int(rep * compas / 8 * TASA)
        dur  = int(TASA * 0.28)
        fin  = min(ini + dur, total)
        f    = fin - ini
        if f <= 0: continue
        t_m  = np.arange(f, dtype=np.float32) / TASA
        mel  = _seno(nota, f) * 0.15 + _seno(nota * 2, f) * 0.07
        env  = np.exp(-t_m * 6)
        mezcla[ini:fin] += mel * env

    # Normalizar y convertir a estéreo int16
    mezcla = np.clip(_normalizar(mezcla, 0.80), -1, 1)
    estereo = np.column_stack([mezcla, mezcla])
    pcm = (estereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(pcm)

# ---------------------------------------------------------------------------
# GestorAudio — singleton que maneja todo el audio del juego
# ---------------------------------------------------------------------------
class GestorAudio:
    def __init__(self):
        pygame.mixer.pre_init(TASA, -16, 2, 512)
        if not pygame.mixer.get_init():
            pygame.mixer.init(TASA, -16, 2, 512)
        pygame.mixer.set_num_channels(24)

        print("🎵 Generando efectos de sonido...")
        self.sfx = {
            "pistola":      _sfx_pistola(),
            "escopeta":     _sfx_escopeta(),
            "rifle":        _sfx_rifle(),
            "metralleta":   _sfx_rifle(),       # mismo banco que rifle, pitch natural
            "zombie_muere": _sfx_zombie_muere(),
            "daño":         _sfx_daño_jugador(),
            "moneda":       _sfx_moneda(),
            "corazon":      _sfx_corazon(),
            "oleada":       _sfx_oleada(),
            "game_over":    _sfx_game_over(),
        }

        # Volúmenes
        volumen = {
            "pistola": 0.55, "escopeta": 0.65, "rifle": 0.50,
            "metralleta": 0.45,
            "zombie_muere": 0.60, "daño": 0.75,
            "moneda": 0.55, "corazon": 0.65,
            "oleada": 0.70, "game_over": 0.80,
        }
        for k, s in self.sfx.items():
            s.set_volume(volumen.get(k, 0.60))

        print("🎵 Generando música de fondo...")
        self.musica = _generar_musica_fondo()
        self.musica.set_volume(0.35)

        self.musica_canal = None
        self.activo = True

        # Limitar frecuencia de SFX de disparo
        self._ultimo_disparo_sfx = 0

    def reproducir(self, nombre, tiempo_actual=None):
        if not self.activo:
            return
        # Throttle de disparos para no saturar canales
        if nombre in ("pistola", "rifle"):
            if tiempo_actual and tiempo_actual - self._ultimo_disparo_sfx < 80:
                return
            self._ultimo_disparo_sfx = tiempo_actual or 0

        sfx = self.sfx.get(nombre)
        if sfx:
            sfx.play()

    def iniciar_musica(self):
        if not self.activo:
            return
        self.musica_canal = self.musica.play(loops=-1)  # bucle infinito

    def detener_musica(self):
        if self.musica_canal:
            self.musica_canal.stop()

    def pausar_musica(self, pausar: bool):
        if self.musica_canal:
            if pausar:
                self.musica_canal.pause()
            else:
                self.musica_canal.unpause()

    def toggle_mute(self):
        self.activo = not self.activo
        if self.activo:
            self.iniciar_musica()
        else:
            pygame.mixer.pause()
