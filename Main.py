import pygame, sys, math, random

pygame.init()
screen = pygame.display.set_mode((1200, 700))#screen width and screen height
pygame.display.set_caption("Zombie Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont('comicsansms', 30)


#map size
WORLD_WIDTH = 3000
WORLD_HEIGHT = 2000
SCREEN_WIDTH = screen.get_width()
SCREEN_HEIGHT = screen.get_height()

#importing grass and tree
grass_image = pygame.image.load("grass.png").convert()
tree_image = pygame.image.load("finaltree.png").convert_alpha()
tree_image = pygame.transform.scale(tree_image, (120, 150))

#importing rocks
rock_image = pygame.image.load("finalrock.png").convert_alpha()
rock_image = pygame.transform.scale(rock_image, (100, 70))

#sound for gun and sound for zombies
shoot_sound = pygame.mixer.Sound("shoot.ogg")
zombie_move_sound = pygame.mixer.Sound("zombie_move.wav")

#ammo box
ammo_box_image = pygame.image.load("ammo_box.png").convert_alpha()
ammo_box_image = pygame.transform.scale(ammo_box_image, (60,60))
ammo_box_pos = (500,300)

#image of player
original_image = pygame.image.load("survivor-move_rifle_0.png").convert_alpha()

#health machine to increase health
hp_box_image = pygame.image.load("hp_box.png").convert_alpha()
hp_box_image = pygame.transform.scale(hp_box_image, (110, 130))
hp_box_pos = (800, 600)


#random colours if needed
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
        self.max_health = 100
        self.image = pygame.transform.scale(original_image, (60, 60))
        self.rotated_image = self.image
        self.mag_capacity = 30
        self.bullets_in_mag = self.mag_capacity
        self.reserve_ammo = 240
        self.is_reloading = False
        self.reload_start_time = 0
        self.reload_duration = 1500

    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= self.speed
        if keys[pygame.K_s]: dy += self.speed
        if keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_d]: dx += self.speed

        new_x = self.world_x + dx
        new_y = self.world_y + dy


        half_size = self.size // 2
        new_x = max(half_size, min(WORLD_WIDTH - half_size, new_x))
        new_y = max(half_size, min(WORLD_HEIGHT - half_size, new_y))

        new_rect = pygame.Rect(new_x - half_size,
                               new_y - half_size,
                               self.size, self.size)

        if not check_collision(new_rect):
            self.world_x = new_x
            self.world_y = new_y

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

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def reload(self):
        if self.bullets_in_mag < self.mag_capacity and self.reserve_ammo > 0:
            self.is_reloading = True
            self.reload_start_time = pygame.time.get_ticks()

    def update_reload(self):
        if self.is_reloading:
            if pygame.time.get_ticks() - self.reload_start_time >= self.reload_duration:
                needed = self.mag_capacity - self.bullets_in_mag
                to_reload = min(needed, self.reserve_ammo)
                self.bullets_in_mag += to_reload
                self.reserve_ammo -= to_reload
                self.is_reloading = False

    def is_player_near_ammo_box(player_rect, ammo_box_rect, distance=100):
        player_center = player_rect.center
        ammo_center = ammo_box_rect.center
        dx = player_center[0] - ammo_center[0]
        dy = player_center[1] - ammo_center[1]
        return (dx * dx + dy * dy) <= (distance * distance)


class Bullet:
    def __init__(self, x, y, angle):
        self.world_x = x
        self.world_y = y
        self.angle = angle
        self.speed = 40
        self.size = 5
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
        self.speed = 3
        self.angle = 0
        enemy_image = pygame.image.load("skeleton-attack_0.png").convert_alpha()
        self.image = pygame.transform.scale(enemy_image, (60,60))
        self.rotated_image = self.image
        self.move_sound_cooldown = 0

    def move_toward(self, player):
        dx = player.world_x - self.world_x
        dy = player.world_y - self.world_y
        angle = math.atan2(dy, dx)
        self.angle = angle  # <-- THIS LINE FIXES THE FACING DIRECTION

        move_x = self.speed * math.cos(angle)
        move_y = self.speed * math.sin(angle)

        new_rect = pygame.Rect(self.world_x + move_x - self.size // 2,
                               self.world_y + move_y - self.size // 2,
                               self.size, self.size)

        if not check_collision(new_rect):
            self.world_x += move_x
            self.world_y += move_y
        else:
            for angle_offset in [math.pi / 6, -math.pi / 6, math.pi / 3, -math.pi / 3]:
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

    def play_zombie_sound(self, player):
        current_time = pygame.time.get_ticks()
        if current_time < self.move_sound_cooldown:
            return  # still cooling down, skip playing sound

        max_hearing_distance = 500
        dx = self.world_x - player.world_x
        dy = self.world_y - player.world_y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < max_hearing_distance:
            volume = max(0.0, 0.5 - distance / max_hearing_distance)
            zombie_move_sound.set_volume(volume)
            zombie_move_sound.play()
            self.move_sound_cooldown = current_time + 2000

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

class Boss:
    def __init__(self):
        self.world_x = random.randint(200, WORLD_WIDTH - 200)
        self.world_y = random.randint(200, WORLD_HEIGHT - 200)
        self.size = 80
        self.health = 300
        self.speed = 1.2
        self.angle = 0
        boss_image = pygame.image.load("boss.png").convert_alpha()  # Use your boss image
        self.image = pygame.transform.scale(boss_image, (100, 100))
        self.rotated_image = self.image

    def move_toward(self, player):
        dx = player.world_x - self.world_x
        dy = player.world_y - self.world_y
        self.angle = math.atan2(dy, dx)
        move_x = self.speed * math.cos(self.angle)
        move_y = self.speed * math.sin(self.angle)
        new_rect = pygame.Rect(self.world_x + move_x - self.size // 2,
                               self.world_y + move_y - self.size // 2,
                               self.size, self.size)
        if not check_collision(new_rect):
            self.world_x += move_x
            self.world_y += move_y

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        angle_degrees = -math.degrees(self.angle)
        self.rotated_image = pygame.transform.rotate(self.image, angle_degrees)
        rect = self.rotated_image.get_rect(center=(screen_x, screen_y))
        screen.blit(self.rotated_image, rect.topleft)
        # Draw health bar
        health_bar_width = 60
        pygame.draw.rect(screen, RED, (screen_x - 30, screen_y - 60, health_bar_width, 8))
        pygame.draw.rect(screen, GREEN, (screen_x - 30, screen_y - 60, int(health_bar_width * self.health / 300), 8))

    def rect(self):
        return pygame.Rect(self.world_x - self.size // 2, self.world_y - self.size // 2, self.size, self.size)

class AmmoBox:
    def __init__(self, image, x, y):
        margin = 100
        self.image = image
        self.world_x = random.randint(margin, WORLD_WIDTH - margin)
        self.world_y = random.randint(margin, WORLD_HEIGHT - margin)
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        screen.blit(self.image, (screen_x - self.rect.width // 2, screen_y - self.rect.height // 2))

    def get_rect(self):
        # For collision / proximity detection
        return pygame.Rect(self.world_x - self.rect.width // 2,
                           self.world_y - self.rect.height // 2,
                           self.rect.width, self.rect.height)

class HPBox:
    def __init__(self, image, x, y):
        margin = 100
        self.image = image
        self.world_x = random.randint(margin, WORLD_WIDTH - margin)
        self.world_y = random.randint(margin, WORLD_HEIGHT - margin)
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        screen.blit(self.image, (screen_x - self.rect.width // 2, screen_y - self.rect.height // 2))

    def get_rect(self):
        return pygame.Rect(self.world_x - self.rect.width // 2,
                           self.world_y - self.rect.height // 2,
                           self.rect.width, self.rect.height)

#checks if a given rectangle collides with any environment objects
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

#some data/information for main loop
player = Player()
bullets = []
enemies = [Enemy() for _ in range(5)]
score = 0
wave = 1
wave_start_time = pygame.time.get_ticks()
wave_delay = 5000 #5 seconds
next_wave_triggered = False
environment_objects = []
boss = None

#Creates ammo and health boxes and gets the health box’s rectangle.
ammo_box = AmmoBox(ammo_box_image, *ammo_box_pos)
hp_box = HPBox(hp_box_image, *hp_box_pos)
hp_box_rect = hp_box.get_rect()

#spawns trees
for _ in range(30):
    x = random.randint(100, WORLD_WIDTH - 100)
    y = random.randint(100, WORLD_HEIGHT - 100)
    trunk_rect = pygame.Rect(-10, 30, 20, 40)
    environment_objects.append(EnvironmentObject(tree_image, x, y, trunk_rect, is_tree=True))

#spawns rocks
for _ in range(20):
    x = random.randint(100, WORLD_WIDTH - 100)
    y = random.randint(100, WORLD_HEIGHT - 100)
    rock_rect = pygame.Rect(-50, -30, 100, 70)
    environment_objects.append(EnvironmentObject(rock_image, x, y, rock_rect))

# Check if the player is within proximity pixels of the ammo box rect
def is_player_near_ammo_box(player_rect, ammo_box_rect, proximity=50):
    distance = player_rect.centerx - ammo_box_rect.centerx, player_rect.centery - ammo_box_rect.centery
    dist_squared = distance[0]**2 + distance[1]**2
    return dist_squared <= proximity**2

# Check if the player is within proximity pixels of the health box rect
def is_player_near_hp_box(player_rect, hp_box_rect, proximity=50):
    distance = player_rect.centerx - hp_box_rect.centerx, player_rect.centery - hp_box_rect.centery
    dist_squared = distance[0]**2 + distance[1]**2
    return dist_squared <= proximity**2

# Game loop
while True:
    clock.tick(60)
    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    player.update_reload()

    # Get player,ammo box and health box rects for proximity and interaction
    player_rect = pygame.Rect(
        player.world_x - player.size // 2,
        player.world_y - player.size // 2,
        player.size,
        player.size
    )
    ammo_box_rect = pygame.Rect(
        ammo_box.world_x - 10,
        ammo_box.world_y - 10,
        20,
        20
    )
    hp_box_rect = pygame.Rect(
        hp_box.world_x - 10,
        hp_box.world_y - 10,
        20,
        20
    )
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not player.is_reloading:
            if player.bullets_in_mag > 0:
                dx = (mouse_pos[0] + player.world_x - SCREEN_WIDTH // 2) - player.world_x
                dy = (mouse_pos[1] + player.world_y - SCREEN_HEIGHT // 2) - player.world_y
                angle = math.atan2(dy, dx)
                offset = 30
                bx = player.world_x + math.cos(angle) * offset
                by = player.world_y + math.sin(angle) * offset
                bullets.append(Bullet(bx, by, angle))
                player.bullets_in_mag -= 1
                shoot_sound.play()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                wave += 1
                enemies = [Enemy() for _ in range(5 + wave * 2)]
                wave_start_time = pygame.time.get_ticks()
                next_wave_triggered = True

            if event.key == pygame.K_r:
                player.reload()

            if event.key == pygame.K_f:
                if is_player_near_ammo_box(player_rect, ammo_box_rect):
                    ammo_to_add = 100
                    cost = 200
                    max_reserve = 240
                    if player.reserve_ammo < max_reserve and score >= cost:
                        added_ammo = min(ammo_to_add, max_reserve - player.reserve_ammo)
                        player.reserve_ammo += added_ammo
                        score -= cost
                elif is_player_near_hp_box(player_rect, hp_box_rect):
                    cost = 500
                    if score >= cost:
                        player.health = min(player.health + 100, player.max_health + 100)
                        player.max_health += 100
                        score -= cost

    # Movement and camera logic
    player.move(keys)
    camera_x = player.world_x - SCREEN_WIDTH // 2
    camera_y = player.world_y - SCREEN_HEIGHT // 2
    player.update_angle(mouse_pos, camera_x, camera_y)

    # Draw ground
    tile_w, tile_h = grass_image.get_width(), grass_image.get_height()
    start_x = camera_x // tile_w * tile_w
    start_y = camera_y // tile_h * tile_h
    for x in range(start_x, camera_x + SCREEN_WIDTH, tile_w):
        for y in range(start_y, camera_y + SCREEN_HEIGHT, tile_h):
            screen.blit(grass_image, (x - camera_x, y - camera_y))

    # Environment
    for obj in environment_objects:
        if not obj.is_tree:
            obj.draw(camera_x, camera_y)
    for obj in environment_objects:
        if obj.is_tree and obj.world_y < player.world_y:
            obj.draw(camera_x, camera_y)

    ammo_box.draw(camera_x, camera_y)
    hp_box.draw(camera_x, camera_y)
    player.draw(camera_x, camera_y)

    # Ammo box location indicator
    pygame.draw.circle(screen, (255, 105, 180), (ammo_box.world_x - camera_x, ammo_box.world_y - camera_y), 1)

    for enemy in enemies:
        enemy.draw(camera_x, camera_y)
    if boss:
        boss.draw(camera_x, camera_y)

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

        if boss and bullet.rect().colliderect(boss.rect()):
            boss.health -= 20
            if bullet in bullets:
                bullets.remove(bullet)
            if boss.health <= 0:
                score += 100
                boss = None

    # Enemy attacks
    for enemy in enemies[:]:
        enemy.move_toward(player)
        enemy.play_zombie_sound(player)
        if enemy.rect().colliderect(player_rect):
            player.take_damage(10)
            enemies.remove(enemy)

    if boss:
        boss.move_toward(player)
        if boss.rect().colliderect(player_rect):
            player.take_damage(25)

    # Out-of-screen enemy indicators
    for enemy in enemies:
        sx, sy = enemy.world_x - camera_x, enemy.world_y - camera_y
        if sx < 0 or sx > SCREEN_WIDTH or sy < 0 or sy > SCREEN_HEIGHT:
            ix = max(10, min(sx, SCREEN_WIDTH - 10))
            iy = max(10, min(sy, SCREEN_HEIGHT - 10))
            pygame.draw.circle(screen, RED, (int(ix), int(iy)), 5)

    # Wave logic
    if len(enemies) == 0 and boss is None:
        if not next_wave_triggered:
            wave_start_time = pygame.time.get_ticks()
            next_wave_triggered = True
        elif pygame.time.get_ticks() - wave_start_time >= wave_delay:
            wave += 1
            enemies = [Enemy() for _ in range(5 + wave * 2)]
            if wave % 5 == 0:
                boss = Boss()
            next_wave_triggered = False

    # Game over screen
    if player.health <= 0:
        screen.fill((0, 0, 0))
        game_over = font.render("Game Over!", True, WHITE)
        screen.blit(game_over, (SCREEN_WIDTH // 2 - game_over.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.update()
        pygame.time.wait(2000)
        sys.exit()


    # Minimap
    minimap_w, minimap_h = 200, 140
    mini = pygame.Surface((minimap_w, minimap_h))
    mini.fill((40, 40, 40))
    pygame.draw.rect(mini, WHITE, (0, 0, minimap_w, minimap_h), 2)
    scale_x = minimap_w / WORLD_WIDTH
    scale_y = minimap_h / WORLD_HEIGHT
    for enemy in enemies:
        mx, my = int(enemy.world_x * scale_x), int(enemy.world_y * scale_y)
        pygame.draw.circle(mini, GREEN, (mx, my), 3)
    if boss:
        mx, my = int(boss.world_x * scale_x), int(boss.world_y * scale_y)
        pygame.draw.circle(mini, RED, (mx, my), 5)
    px, py = int(player.world_x * scale_x), int(player.world_y * scale_y)
    pygame.draw.circle(mini, BLUE, (px, py), 4)
    screen.blit(mini, (SCREEN_WIDTH - minimap_w - 10, 10))

    # World boundary
    pygame.draw.rect(
        screen,
        (0, 0, 0),
        pygame.Rect(-camera_x, -camera_y, WORLD_WIDTH, WORLD_HEIGHT),
        5
    )
    # Create a dark overlay
    dark_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dark_surface.fill((0, 0, 0, 150))  # Semi-transparent black

    # Flashlight
    flashlight_radius = 600
    cone_angle = math.pi / 3  # 60 degrees
    num_rays = 60
    ray_step = cone_angle / num_rays

    # flashlight center on screen
    px = SCREEN_WIDTH // 2
    py = SCREEN_HEIGHT // 2

    # Create flashlight cone
    flashlight_points = [(px, py)]
    start_angle = player.angle - cone_angle / 2
    for i in range(num_rays + 1):
        angle = start_angle + i * ray_step
        x = px + flashlight_radius * math.cos(angle)
        y = py + flashlight_radius * math.sin(angle)
        flashlight_points.append((x, y))

    # Cut out the flashlight cone (polygonal beam)
    pygame.draw.polygon(dark_surface, (0, 0, 0, 0), flashlight_points)

    # Apply dark overlay with hole for flashlight
    screen.blit(dark_surface, (0, 0))

    #UI
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font.render(f"Wave: {wave}", True, WHITE), (20, 60))
    screen.blit(font.render(f"Health: {player.health}", True, BLUE), (20, 100))
    screen.blit(font.render(f"Ammo: {player.bullets_in_mag} / {player.reserve_ammo}", True, ORANGE), (20, 140))

    info_text = font.render("200 points for 100 bullets, press F to buy", True, (255, 255, 255))
    if is_player_near_ammo_box(player_rect, ammo_box_rect):
        screen.blit(info_text, (ammo_box_rect.x - camera_x - 40, ammo_box_rect.y - camera_y - 30))
    elif is_player_near_hp_box(player_rect, hp_box_rect):
        info_text = font.render("500 points for +100 HP, press F to buy", True, (255, 255, 255))
        screen.blit(info_text, (hp_box_rect.x - camera_x - 40, hp_box_rect.y - camera_y - 30))

    # Minimap
    minimap_w, minimap_h = 200, 140
    mini = pygame.Surface((minimap_w, minimap_h))
    mini.fill((40, 40, 40))
    pygame.draw.rect(mini, WHITE, (0, 0, minimap_w, minimap_h), 2)
    scale_x = minimap_w / WORLD_WIDTH
    scale_y = minimap_h / WORLD_HEIGHT
    for enemy in enemies:
        mx, my = int(enemy.world_x * scale_x), int(enemy.world_y * scale_y)
        pygame.draw.circle(mini, GREEN, (mx, my), 3)
    if boss:
        mx, my = int(boss.world_x * scale_x), int(boss.world_y * scale_y)
        pygame.draw.circle(mini, RED, (mx, my), 5)
    px, py = int(player.world_x * scale_x), int(player.world_y * scale_y)
    pygame.draw.circle(mini, BLUE, (px, py), 4)
    screen.blit(mini, (SCREEN_WIDTH - minimap_w - 10, 10))

    pygame.display.update()

