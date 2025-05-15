import pygame, sys, math, random

pygame.init()
screen = pygame.display.set_mode((1200, 700))
pygame.display.set_caption("Zombie Shooter - Scrolling Camera")
clock = pygame.time.Clock()
font = pygame.font.SysFont('comicsansms', 30)

# World and screen sizes
WORLD_WIDTH = 3000
WORLD_HEIGHT = 2000
SCREEN_WIDTH = screen.get_width()
SCREEN_HEIGHT = screen.get_height()

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

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
        if keys[pygame.K_w]: self.world_y -= self.speed
        if keys[pygame.K_s]: self.world_y += self.speed
        if keys[pygame.K_a]: self.world_x -= self.speed
        if keys[pygame.K_d]: self.world_x += self.speed

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
            self.health = 0  # Player health can't go below zero

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
        # Bullet expires after 5000 ms (5 seconds)
        current_time = pygame.time.get_ticks()
        return current_time - self.spawn_time > 5000

class Enemy:
    def __init__(self):
        margin = 100
        self.world_x = random.randint(margin, WORLD_WIDTH - margin)
        self.world_y = random.randint(margin, WORLD_HEIGHT - margin)
        self.size = 30
        self.speed = 1.5

    def move_toward(self, player):
        dx = player.world_x - self.world_x
        dy = player.world_y - self.world_y
        angle = math.atan2(dy, dx)
        self.world_x += self.speed * math.cos(angle)
        self.world_y += self.speed * math.sin(angle)

    def draw(self, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        pygame.draw.rect(screen, GREEN, (screen_x - self.size//2, screen_y - self.size//2, self.size, self.size))

    def rect(self):
        return pygame.Rect(self.world_x - self.size//2, self.world_y - self.size//2, self.size, self.size)

# Game setup
player = Player()
bullets = []
enemies = [Enemy() for _ in range(5)]
score = 0
wave = 1
wave_start_time = pygame.time.get_ticks()  # Start time for wave change
wave_delay = 1000  # 1 second delay between waves
next_wave_triggered = False  # Whether the player manually triggered the next wave

# Main game loop
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

            # Bullet spawn offset from center
            offset_distance = 30  # adjust this for how far in front of player bullet appears
            bullet_start_x = player.world_x + math.cos(angle) * offset_distance
            bullet_start_y = player.world_y + math.sin(angle) * offset_distance

            bullets.append(Bullet(bullet_start_x, bullet_start_y, angle))

        # Check for 'T' key press to manually trigger the next wave
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            # Manually trigger the next wave if 'T' is pressed
            wave += 1
            enemies = [Enemy() for _ in range(5 + wave * 2)]  # Increase the number of enemies as wave increases
            wave_start_time = pygame.time.get_ticks()  # Reset wave start time
            next_wave_triggered = True

    player.move(keys)
    camera_x = player.world_x - SCREEN_WIDTH // 2
    camera_y = player.world_y - SCREEN_HEIGHT // 2
    player.update_angle(mouse_pos, camera_x, camera_y)

    screen.fill((20, 20, 20))  # Background

    # Draw player
    player.draw(camera_x, camera_y)

    # Draw and update bullets
    for bullet in bullets[:]:
        bullet.move()

        # Remove bullet if it's off-screen or expired
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

    # Move and draw enemies
    for enemy in enemies:
        enemy.move_toward(player)
        enemy.draw(camera_x, camera_y)

        # Check for collision with player
        if enemy.rect().colliderect(pygame.Rect(player.world_x - player.size // 2, player.world_y - player.size // 2, player.size, player.size)):
            player.take_damage(10)  # Player takes damage when an enemy collides with them
            enemies.remove(enemy)

    # Draw off-screen indicators for enemies (Red Dots)
    for enemy in enemies:
        enemy_screen_x = enemy.world_x - camera_x
        enemy_screen_y = enemy.world_y - camera_y

        # If the enemy is off-screen, show an indicator
        if enemy_screen_x < 0 or enemy_screen_x > SCREEN_WIDTH or enemy_screen_y < 0 or enemy_screen_y > SCREEN_HEIGHT:
            # Determine which edge to display the indicator on
            if enemy_screen_x < 0:
                indicator_x = 10
            elif enemy_screen_x > SCREEN_WIDTH:
                indicator_x = SCREEN_WIDTH - 10
            else:
                indicator_x = enemy_screen_x

            if enemy_screen_y < 0:
                indicator_y = 10
            elif enemy_screen_y > SCREEN_HEIGHT:
                indicator_y = SCREEN_HEIGHT - 10
            else:
                indicator_y = enemy_screen_y

            # Draw small red circle at the edge pointing to the enemy
            pygame.draw.circle(screen, RED, (indicator_x, indicator_y), 5)

    # Automatically trigger next wave when all enemies are defeated
    if len(enemies) == 0 and not next_wave_triggered:
        wave += 1
        enemies = [Enemy() for _ in range(5 + wave * 2)]  # Increase the number of enemies as wave increases
        wave_start_time = pygame.time.get_ticks()  # Reset wave start time
        next_wave_triggered = True  # Mark that the next wave has been triggered

    # UI
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font.render(f"Wave: {wave}", True, WHITE), (20, 60))
    screen.blit(font.render(f"Health: {player.health}", True, BLUE), (20, 100))

    # Check for game over
    if player.health <= 0:
        screen.fill((0, 0, 0))  # Game over screen
        game_over_text = font.render("Game Over!", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.update()
        pygame.time.wait(2000)  # Wait for 2 seconds before closing
        sys.exit()

    pygame.display.update()
