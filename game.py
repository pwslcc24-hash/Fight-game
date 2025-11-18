import sys
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 900, 500
FLOOR_Y = HEIGHT - 80
BG_COLOR = (18, 18, 40)
FPS = 60

GRAVITY = 0.8
JUMP_FORCE = 16
MOVE_SPEED = 6
KNOCKBACK_X = 10
KNOCKBACK_Y = 6
ATTACK_DURATION = 200  # milliseconds
ATTACK_COOLDOWN = 400
ATTACK_DAMAGE = 12


@dataclass
class Fighter:
    name: str
    color: tuple
    x: float
    y: float
    width: int
    height: int
    controls: dict
    facing: int = 1
    vx: float = 0
    vy: float = 0
    on_ground: bool = False
    attack_timer: int = 0
    cooldown_timer: int = 0
    attack_hit: bool = False
    health: int = 100

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def reset(self, start_pos):
        self.x, self.y = start_pos
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.attack_timer = 0
        self.cooldown_timer = 0
        self.attack_hit = False
        self.health = 100
        self.facing = 1


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def handle_input(fighter: Fighter, keys):
    move_left = keys[fighter.controls["left"]]
    move_right = keys[fighter.controls["right"]]

    fighter.vx = 0
    if move_left:
        fighter.vx = -MOVE_SPEED
        fighter.facing = -1
    if move_right:
        fighter.vx = MOVE_SPEED
        fighter.facing = 1

    if keys[fighter.controls["jump"]] and fighter.on_ground:
        fighter.vy = -JUMP_FORCE
        fighter.on_ground = False

    attack_pressed = keys[fighter.controls["attack"]]
    if attack_pressed and fighter.attack_timer <= 0 and fighter.cooldown_timer <= 0:
        fighter.attack_timer = ATTACK_DURATION
        fighter.cooldown_timer = ATTACK_COOLDOWN
        fighter.attack_hit = False


def apply_physics(fighter: Fighter, dt_ms):
    fighter.x += fighter.vx

    fighter.vy += GRAVITY
    fighter.y += fighter.vy

    if fighter.y + fighter.height >= FLOOR_Y:
        fighter.y = FLOOR_Y - fighter.height
        fighter.vy = 0
        fighter.on_ground = True
    else:
        fighter.on_ground = False

    fighter.x = clamp(fighter.x, 20, WIDTH - fighter.width - 20)

    fighter.attack_timer = max(0, fighter.attack_timer - dt_ms)
    fighter.cooldown_timer = max(0, fighter.cooldown_timer - dt_ms)
    if fighter.attack_timer == 0:
        fighter.attack_hit = False


def get_attack_rect(fighter: Fighter):
    if fighter.attack_timer <= 0:
        return None
    offset = 30
    attack_width = 50
    attack_height = fighter.height - 10
    if fighter.facing == 1:
        x = fighter.x + fighter.width + offset - attack_width
    else:
        x = fighter.x - offset
    y = fighter.y + 5
    return pygame.Rect(int(x), int(y), attack_width, attack_height)


def process_hit(attacker: Fighter, defender: Fighter):
    defender.health = max(0, defender.health - ATTACK_DAMAGE)
    defender.vx = KNOCKBACK_X * attacker.facing
    defender.vy = -KNOCKBACK_Y


def draw_health_bar(surface, fighter: Fighter, x, y, width, height):
    pygame.draw.rect(surface, (60, 60, 60), (x, y, width, height))
    ratio = fighter.health / 100
    inner_width = int(width * ratio)
    color = (220, 70, 70) if fighter.name == "Player 1" else (70, 160, 220)
    pygame.draw.rect(surface, color, (x, y, inner_width, height))


def reset_game(p1: Fighter, p2: Fighter):
    p1.reset((WIDTH * 0.25 - p1.width / 2, FLOOR_Y - p1.height))
    p2.reset((WIDTH * 0.75 - p2.width / 2, FLOOR_Y - p2.height))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Smash")
    clock = pygame.time.Clock()

    player1 = Fighter(
        name="Player 1",
        color=(240, 120, 120),
        x=WIDTH * 0.25,
        y=FLOOR_Y - 80,
        width=60,
        height=80,
        controls={
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "jump": pygame.K_UP,
            "attack": pygame.K_SPACE,
        },
    )

    player2 = Fighter(
        name="Player 2",
        color=(120, 170, 255),
        x=WIDTH * 0.75,
        y=FLOOR_Y - 80,
        width=60,
        height=80,
        controls={
            "left": pygame.K_a,
            "right": pygame.K_d,
            "jump": pygame.K_w,
            "attack": pygame.K_f,
        },
    )

    reset_game(player1, player2)

    font = pygame.font.SysFont("arial", 24)
    arena = pygame.Rect(50, FLOOR_Y + 10, WIDTH - 100, 20)

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        handle_input(player1, keys)
        handle_input(player2, keys)

        apply_physics(player1, dt_ms)
        apply_physics(player2, dt_ms)

        for attacker, defender in ((player1, player2), (player2, player1)):
            attack_rect = get_attack_rect(attacker)
            if attack_rect and not attacker.attack_hit:
                if attack_rect.colliderect(defender.rect):
                    attacker.attack_hit = True
                    process_hit(attacker, defender)

        if player1.health <= 0 or player2.health <= 0:
            pygame.time.delay(800)
            reset_game(player1, player2)

        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, (100, 100, 120), arena)

        pygame.draw.rect(screen, player1.color, player1.rect)
        pygame.draw.rect(screen, player2.color, player2.rect)

        for fighter in (player1, player2):
            attack_rect = get_attack_rect(fighter)
            if attack_rect:
                pygame.draw.rect(screen, (255, 230, 150), attack_rect)

        draw_health_bar(screen, player1, 50, 30, 300, 20)
        draw_health_bar(screen, player2, WIDTH - 350, 30, 300, 20)

        info = font.render("Arrow/WASD to move, Space/F to attack", True, (230, 230, 230))
        screen.blit(info, (WIDTH / 2 - info.get_width() / 2, 5))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
