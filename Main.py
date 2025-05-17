import pygame, sys, math, random

pygame.init()
screen = pygame.display.set_mode((1200, 700))
pygame.display.set_caption("Zombie Shooter - Scrolling Camera")
clock = pygame.time.Clock()
font = pygame.font.SysFont('comicsansms', 30)

WORLD_WIDTH = 3000
WORLD_HEIGHT = 2000
SCREEN_WIDTH = screen.get_width()
SCREEN_HEIGHT = screen.get_height()

grass_image = pygame.image.load("grass.png").convert()
tree_image = pygame.image.load("finaltree.png").convert_alpha()
tree_image = pygame.transform.scale(tree_image, (120, 150))  # Adjust size as needed

rock_image = pygame.image.load("finalrock.png").convert_alpha()
rock_image = pygame.transform.scale(rock_image, (100, 70))  # Adjust size as needed

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

class Player:
    def __init__(self):
        self.world_x = WORLD_WIDTH // 2
        self.world_y = WORLD_HEIGHT // 2
        self.speed = 5
        self.angle = 0
        self.size = 40
        self.health = 100
        original_image = pygame.image.load("survivor-move_rifle_0.png").convert_alpha()
        self.image = pygame.transform.scale(original_image, (60, 60))
        self.rotated_image = self.image

    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= self.speed
        if keys[pygame.K_s]: dy += self.speed
        if keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_d]: dx += self.speed

        new_rect = pygame.Rect(
            self.world_x + dx - self.size // 2,
            self.world_y + dy - self.size // 2,
            self.size,
            self.size
        )

        if not check_collision(new_rect):
            self.world_x += dx
            self.world_y += dy

    def update_angle(self, mouse_pos, camera_x, camera_y):
        dx = (mouse_pos[0] + camera_x) - self.world_x
        dy = (mouse_pos[1] + camera_y) - self.world_y
        self.angle = math.atan2(dy, dx)

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        angle_degrees = -math.degrees(self.angle)
        self.rotated_image = pygame.transform.rotate(self.image, angle_degrees)
        rect = self.rotated_image.get_rect(center=(screen_x, screen_y))
        screen.blit(self.rotated_image, rect.topleft)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0

class Bullet:
    def __init__(self, x, y, angle):
        self.world_x = x
        self.world_y = y
        self.angle = angle
        self.speed = 12
        self.size = 6
        self.spawn_time = pygame.time.get_ticks()

    def move(self):
        self.world_x += self.speed * math.cos(self.angle)
        self.world_y += self.speed * math.sin(self.angle)

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), self.size)

    def off_world(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        return (screen_x < -self.size or screen_x > SCREEN_WIDTH + self.size or
                screen_y < -self.size or screen_y > SCREEN_HEIGHT + self.size)

    def rect(self):
        return pygame.Rect(self.world_x - self.size, self.world_y - self.size, self.size * 2, self.size * 2)

    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time > 5000

class Enemy:
    def __init__(self):
        margin = 100
        self.world_x = random.randint(margin, WORLD_WIDTH - margin)
        self.world_y = random.randint(margin, WORLD_HEIGHT - margin)
        self.size = 30
        self.speed = 1.5
        self.angle = 0
        enemy_image = pygame.image.load("skeleton-attack_0.png").convert_alpha()
        self.image = pygame.transform.scale(enemy_image, (60,60))
        self.rotated_image = self.image

    def move_toward(self, player):
        dx = player.world_x - self.world_x
        dy = player.world_y - self.world_y
        angle = math.atan2(dy, dx)
        move_x = self.speed * math.cos(angle)
        move_y = self.speed * math.sin(angle)

        new_rect = pygame.Rect(self.world_x + move_x - self.size // 2,
                               self.world_y + move_y - self.size // 2,
                               self.size, self.size)
        if not check_collision(new_rect):
            self.world_x += move_x
            self.world_y += move_y
        else:
            for angle_offset in [math.pi/6, -math.pi/6, math.pi/3, -math.pi/3]:
                new_angle = angle + angle_offset
                alt_move_x = self.speed * math.cos(new_angle)
                alt_move_y = self.speed * math.sin(new_angle)
                alt_rect = pygame.Rect(self.world_x + alt_move_x - self.size // 2,
                                       self.world_y + alt_move_y - self.size // 2,
                                       self.size, self.size)
                if not check_collision(alt_rect):
                    self.world_x += alt_move_x
                    self.world_y += alt_move_y
                    break

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        angle_degrees = -math.degrees(self.angle)
        self.rotated_image = pygame.transform.rotate(self.image, angle_degrees)
        rect = self.rotated_image.get_rect(center=(screen_x, screen_y))
        screen.blit(self.rotated_image, rect.topleft)

    def rect(self):
        return pygame.Rect(self.world_x - self.size//2, self.world_y - self.size//2, self.size, self.size)

class EnvironmentObject:
    def __init__(self, image, x, y, collision_rect=None, is_tree=False):
        self.image = image
        self.world_x = x
        self.world_y = y
        self.rect = self.image.get_rect(center=(x, y))
        self.collision_rect = collision_rect
        self.is_tree = is_tree

    def draw(self, camera_x, camera_y, debug=False):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        screen.blit(self.image, (screen_x - self.rect.width // 2, screen_y - self.rect.height // 2))

        if debug and self.collision_rect:
            hitbox_screen = pygame.Rect(
                screen_x + self.collision_rect.x,
                screen_y + self.collision_rect.y,
                self.collision_rect.width,
                self.collision_rect.height
            )
            pygame.draw.rect(screen, RED, hitbox_screen, 2)

def check_collision(new_rect):
    for obj in environment_objects:
        if obj.collision_rect:
            obj_rect = pygame.Rect(
                obj.world_x + obj.collision_rect.x,
                obj.world_y + obj.collision_rect.y,
                obj.collision_rect.width,
                obj.collision_rect.height
            )
            if new_rect.colliderect(obj_rect):
                return True
    return False

player = Player()
bullets = []
enemies = [Enemy() for _ in range(5)]
score = 0
wave = 1
wave_start_time = pygame.time.get_ticks()
wave_delay = 5000
next_wave_triggered = False
environment_objects = []

for _ in range(30):  # Trees
    x = random.randint(100, WORLD_WIDTH - 100)
    y = random.randint(100, WORLD_HEIGHT - 100)
    trunk_rect = pygame.Rect(-10, 30, 20, 40)
    environment_objects.append(EnvironmentObject(tree_image, x, y, trunk_rect, is_tree=True))

for _ in range(20):  # Rocks
    x = random.randint(100, WORLD_WIDTH - 100)
    y = random.randint(100, WORLD_HEIGHT - 100)
    rock_rect = pygame.Rect(-50, -30, 100, 70)
    environment_objects.append(EnvironmentObject(rock_image, x, y, rock_rect))

while True:
    clock.tick(60)
    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = (mouse_x + player.world_x - SCREEN_WIDTH // 2) - player.world_x
            dy = (mouse_y + player.world_y - SCREEN_HEIGHT // 2) - player.world_y
            angle = math.atan2(dy, dx)
            offset = 30
            bx = player.world_x + math.cos(angle) * offset
            by = player.world_y + math.sin(angle) * offset
            bullets.append(Bullet(bx, by, angle))
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            wave += 1
            enemies = [Enemy() for _ in range(5 + wave * 2)]
            wave_start_time = pygame.time.get_ticks()
            next_wave_triggered = True

    player.move(keys)
    camera_x = player.world_x - SCREEN_WIDTH // 2
    camera_y = player.world_y - SCREEN_HEIGHT // 2
    player.update_angle(mouse_pos, camera_x, camera_y)

    tile_w, tile_h = grass_image.get_width(), grass_image.get_height()
    start_x = camera_x // tile_w * tile_w
    start_y = camera_y // tile_h * tile_h
    for x in range(start_x, camera_x + SCREEN_WIDTH, tile_w):
        for y in range(start_y, camera_y + SCREEN_HEIGHT, tile_h):
            screen.blit(grass_image, (x - camera_x, y - camera_y))

    for obj in environment_objects:
        if not obj.is_tree:
            obj.draw(camera_x, camera_y)
        elif obj.world_y < player.world_y:
            obj.draw(camera_x, camera_y)

    player.draw(camera_x, camera_y)
    for enemy in enemies:
        enemy.draw(camera_x, camera_y)

    for obj in environment_objects:
        if obj.is_tree and obj.world_y >= player.world_y:
            obj.draw(camera_x, camera_y)

    for bullet in bullets[:]:
        bullet.move()
        if bullet.off_world(camera_x, camera_y) or bullet.is_expired():
            bullets.remove(bullet)
            continue
        bullet.draw(camera_x, camera_y)
        for enemy in enemies[:]:
            if bullet.rect().colliderect(enemy.rect()):
                enemies.remove(enemy)
                if bullet in bullets:
                    bullets.remove(bullet)
                score += 10
                break

    for enemy in enemies[:]:
        enemy.move_toward(player)
        if enemy.rect().colliderect(pygame.Rect(player.world_x - player.size // 2,
                                                player.world_y - player.size // 2,
                                                player.size, player.size)):
            player.take_damage(10)
            enemies.remove(enemy)

    for enemy in enemies:
        sx, sy = enemy.world_x - camera_x, enemy.world_y - camera_y
        if sx < 0 or sx > SCREEN_WIDTH or sy < 0 or sy > SCREEN_HEIGHT:
            ix = max(10, min(sx, SCREEN_WIDTH - 10))
            iy = max(10, min(sy, SCREEN_HEIGHT - 10))
            pygame.draw.circle(screen, RED, (int(ix), int(iy)), 5)

    if len(enemies) == 0:
        if not next_wave_triggered:
            wave_start_time = pygame.time.get_ticks()
            next_wave_triggered = True
        elif pygame.time.get_ticks() - wave_start_time >= wave_delay:
            wave += 1
            enemies = [Enemy() for _ in range(5 + wave * 2)]
            next_wave_triggered = False

    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font.render(f"Wave: {wave}", True, WHITE), (20, 60))
    screen.blit(font.render(f"Health: {player.health}", True, BLUE), (20, 100))

    if player.health <= 0:
        screen.fill((0, 0, 0))
        game_over = font.render("Game Over!", True, WHITE)
        screen.blit(game_over, (SCREEN_WIDTH // 2 - game_over.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.update()
        pygame.time.wait(2000)
        sys.exit()

    minimap_w, minimap_h = 200, 140
    mini = pygame.Surface((minimap_w, minimap_h))
    mini.fill((40, 40, 40))
    pygame.draw.rect(mini, WHITE, (0, 0, minimap_w, minimap_h), 2)
    scale_x = minimap_w / WORLD_WIDTH
    scale_y = minimap_h / WORLD_HEIGHT
    for enemy in enemies:
        mx, my = int(enemy.world_x * scale_x), int(enemy.world_y * scale_y)
        pygame.draw.circle(mini, GREEN, (mx, my), 3)
    px, py = int(player.world_x * scale_x), int(player.world_y * scale_y)
    pygame.draw.circle(mini, BLUE, (px, py), 4)
    screen.blit(mini, (SCREEN_WIDTH - minimap_w - 10, 10))

    pygame.display.update()
