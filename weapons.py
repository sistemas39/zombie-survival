class Weapon:
    def __init__(self, name, damage, fire_rate, bullet_speed,
                 spread, bullets_per_shot, ammo_capacity, cost, unlocked, sprite_key):
        self.name             = name
        self.damage           = damage
        self.fire_rate        = fire_rate
        self.bullet_speed     = bullet_speed
        self.spread           = spread
        self.bullets_per_shot = bullets_per_shot
        self.ammo_capacity    = ammo_capacity
        self.current_ammo     = ammo_capacity
        self.cost             = cost
        self.unlocked         = unlocked
        self.sprite_key       = sprite_key
        self.last_shot_time   = 0

    def reload(self):
        if self.ammo_capacity != -1:
            self.current_ammo = self.ammo_capacity

    def upgrade_fire_rate(self, mult=0.85):
        self.fire_rate = max(45, int(self.fire_rate * mult))

    def upgrade_damage(self, mult=1.15):
        self.damage = round(self.damage * mult, 1)

    def upgrade_ammo(self, mult=1.3):
        if self.ammo_capacity != -1:
            # Añadir munición proporcional, mínimo 1 bala más
            extra = max(1, int(self.ammo_capacity * (mult - 1.0)))
            self.ammo_capacity += extra
            self.current_ammo += extra


def get_default_weapons():
    return {
        "pistola": Weapon(
            name="Pistola",
            damage=15.0,
            fire_rate=400,
            bullet_speed=12.0,
            spread=3.0,
            bullets_per_shot=1,
            ammo_capacity=-1,
            cost=0,
            unlocked=True,
            sprite_key="pistola",
        ),
        "escopeta": Weapon(
            name="Escopeta",
            damage=12.0,
            fire_rate=800,
            bullet_speed=9.0,
            spread=16.0,
            bullets_per_shot=6,
            ammo_capacity=8,
            cost=80,          # antes: 150
            unlocked=False,
            sprite_key="escopeta",
        ),
        "rifle": Weapon(
            name="Rifle de Asalto",
            damage=18.0,
            fire_rate=110,
            bullet_speed=15.0,
            spread=4.0,
            bullets_per_shot=1,
            ammo_capacity=30,
            cost=150,         # antes: 300
            unlocked=False,
            sprite_key="rifle",
        ),
        "metralleta": Weapon(
            name="Metralleta",
            damage=8.0,
            fire_rate=65,           # Disparo ultrarrápido
            bullet_speed=13.0,
            spread=8.0,
            bullets_per_shot=1,
            ammo_capacity=60,
            cost=220,         # antes: 450
            unlocked=False,
            sprite_key="metralleta",
        ),
    }
