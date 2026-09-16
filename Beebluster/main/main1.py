import pygame
import random
import math
import sys
import mysql.connector
from datetime import datetime
import os
from playsound import playsound
import threading


# ---------------- Audio Setup ----------------
def play_background_music():
    """Play background music in a loop using playsound in a separate thread"""

    def play_music():
        try:
            while True:
                playsound('C:\\Users\HP\Downloads\game-minecraft-gaming-background-music-402451.mp3')
        except Exception as e:
            print(f"Error playing background music: {e}")

    # Start music in a separate thread to avoid blocking
    music_thread = threading.Thread(target=play_music, daemon=True)
    music_thread.start()
    print("Background music started!")


# ---------------- Database Setup ----------------
def init_database():
    """Initialize the database connection and create tables if they don't exist"""
    try:
        # Try different common MySQL configurations
        db_configs = [
            {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "bee_bluster_db"
            },
            {
                "host": "localhost",
                "user": "root",
                "password": "password",
                "database": "bee_bluster_db"
            },
            {
                "host": "localhost",
                "user": "root",
                "password": "root",
                "database": "bee_bluster_db"
            }
        ]

        db = None
        for config in db_configs:
            try:
                print(f"Trying database connection with user: {config['user']}")
                db = mysql.connector.connect(
                    host=config["host"],
                    user=config["user"],
                    password=config["password"],
                    database=config["database"]
                )
                if db.is_connected():
                    print("Database connected successfully!")
                    break
            except mysql.connector.Error as err:
                print(f"Connection failed: {err}")
                continue

        if db is None or not db.is_connected():
            print("All database connection attempts failed.")
            return None

        cursor = db.cursor()

        # Create database if it doesn't exist
        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS bee_bluster_db")
            cursor.execute("USE bee_bluster_db")
        except mysql.connector.Error as err:
            print(f"Database creation error: {err}")

        # Create scores table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    player_name VARCHAR(50) DEFAULT 'Player',
                    score INT NOT NULL,
                    level INT NOT NULL,
                    game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
            print("Database table created/verified successfully!")
        except mysql.connector.Error as err:
            print(f"Table creation error: {err}")
            db.rollback()

        return db

    except mysql.connector.Error as err:
        print(f"Database initialization error: {err}")
        print("Continuing without database functionality...")
        return None
    except Exception as e:
        print(f"Unexpected error during database initialization: {e}")
        return None


# Fallback file-based storage for when database is not available
SCORES_FILE = "game_scores.txt"


def save_score_to_file(score, level, player_name="Player"):
    """Save score to text file when database is not available"""
    try:
        with open(SCORES_FILE, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{player_name},{score},{level},{timestamp}\n")
        print(f"Score saved to file: {score} points at level {level}")
        return True
    except Exception as e:
        print(f"Error saving score to file: {e}")
        return False


def get_scores_from_file(limit=50):
    """Get scores from text file when database is not available"""
    try:
        if not os.path.exists(SCORES_FILE):
            return []

        scores = []
        with open(SCORES_FILE, "r") as f:
            lines = f.readlines()

        for line in lines[-limit:]:  # Get last 'limit' scores
            parts = line.strip().split(',')
            if len(parts) >= 4:
                name, score, level, date_str = parts[0], parts[1], parts[2], parts[3]
                try:
                    scores.append((name, int(score), int(level), datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")))
                except ValueError:
                    continue

        # Return in reverse chronological order (newest first)
        return sorted(scores, key=lambda x: x[3], reverse=True)[:limit]
    except Exception as e:
        print(f"Error reading scores from file: {e}")
        return []


def save_score(db, score, level, player_name="Player"):
    """Save score to database or file"""
    if db and db.is_connected():
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO scores (player_name, score, level) VALUES (%s, %s, %s)",
                (player_name, score, level)
            )
            db.commit()
            print(f"Score saved to database: {score} points at level {level}")
            return True
        except mysql.connector.Error as err:
            print(f"Error saving score to database: {err}")
            # Fallback to file
            return save_score_to_file(score, level, player_name)
    else:
        # Use file-based storage
        return save_score_to_file(score, level, player_name)


def get_all_scores(db, limit=50):
    """Retrieve all scores from database or file"""
    # Try database first
    if db and db.is_connected():
        try:
            cursor = db.cursor()
            cursor.execute(
                "SELECT player_name, score, level, game_date FROM scores ORDER BY game_date DESC LIMIT %s",
                (limit,)
            )
            scores = cursor.fetchall()
            print(f"Retrieved {len(scores)} scores from database")
            return scores
        except mysql.connector.Error as err:
            print(f"Error retrieving scores from database: {err}")

    # Fallback to file
    print("Using file-based scores storage")
    return get_scores_from_file(limit)


# Initialize database
db_connection = init_database()

pygame.init()

# ---------------- Screen Setup ----------------
WIDTH, HEIGHT = 1200, 650
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bee Bluster")

# ---------------- Assets ----------------
# Note: You'll need to have these image files in your project folder
try:
    background = pygame.image.load('img_2.png')
    playerImg = pygame.image.load('bee (2).png')
    enemyImg = pygame.image.load('dragonfly (1).png')
    chaserImg = pygame.image.load('mosquito.png')
    bulletImg = pygame.image.load('honeydrop.png')
    enemybulletImg = pygame.image.load('water.png')
    lifeImg = pygame.image.load('heart.png')
    powerImg = pygame.image.load('flower pink.png')
    title_image = pygame.image.load('img_17.png')
    print("All images loaded successfully!")
except pygame.error as e:
    print(f"Error loading images: {e}")
    print("Make sure all image files are in the correct directory")
    # Create placeholder surfaces to prevent crashes
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((0, 0, 100))
    playerImg = pygame.Surface((64, 64))
    playerImg.fill((255, 255, 0))
    enemyImg = pygame.Surface((64, 64))
    enemyImg.fill((255, 0, 0))
    chaserImg = pygame.Surface((64, 64))
    chaserImg.fill((0, 255, 0))
    bulletImg = pygame.Surface((10, 20))
    bulletImg.fill((0, 0, 255))
    enemybulletImg = pygame.Surface((10, 20))
    enemybulletImg.fill((255, 0, 255))
    lifeImg = pygame.Surface((30, 30))
    lifeImg.fill((255, 0, 0))
    powerImg = pygame.Surface((30, 30))
    powerImg.fill((0, 255, 255))
    title_image = pygame.Surface((WIDTH, HEIGHT))
    title_image.fill((100, 100, 200))

clock = pygame.time.Clock()

# ---------------- Game States ----------------
GAME_STATE_MENU = 0
GAME_STATE_LEVEL1 = 1
GAME_STATE_LEVEL2 = 2
GAME_STATE_SCORES = 3
current_game_state = GAME_STATE_MENU

# Global score variable to track final score
final_score = 0
current_level = 1


# ---------------- Scores Screen ----------------
def show_scores_screen():
    global current_game_state

    title_font = pygame.font.Font(None, 80)
    title_text = title_font.render("ALL SCORES", True, (255, 215, 0))

    back_font = pygame.font.Font(None, 50)
    back_text = back_font.render("BACK", True, (255, 255, 255))
    back_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 60)

    # Get all scores from database or file
    all_scores = get_all_scores(db_connection)

    waiting = True
    while waiting:
        screen.fill((0, 0, 0))

        # Title
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

        # Display all scores
        score_font = pygame.font.Font(None, 30)
        header_font = pygame.font.Font(None, 36)

        if all_scores:
            # Header
            header_text = header_font.render("Player - Score - Level - Date", True, (255, 255, 0))
            screen.blit(header_text, (WIDTH // 2 - header_text.get_width() // 2, 120))

            for i, score_data in enumerate(all_scores):
                if len(score_data) >= 4:
                    name, score, level, date = score_data
                    # Format date to be more readable
                    if hasattr(date, 'strftime'):
                        date_str = date.strftime("%Y-%m-%d %H:%M")
                    else:
                        date_str = str(date)

                    score_text = score_font.render(f"{name} - {score} - Level {level} - {date_str}", True,
                                                   (255, 255, 255))
                    screen.blit(score_text, (WIDTH // 2 - 250, 160 + i * 30))

                    # Show only first 15 scores to fit screen
                    if i >= 14:
                        more_text = score_font.render("... and more scores ...", True, (255, 255, 255))
                        screen.blit(more_text, (WIDTH // 2 - more_text.get_width() // 2, 160 + (i + 1) * 30))
                        break
                else:
                    # Handle case where score data is incomplete
                    error_text = score_font.render(f"Incomplete score data: {score_data}", True, (255, 0, 0))
                    screen.blit(error_text, (WIDTH // 2 - 250, 160 + i * 30))
        else:
            no_scores_text = header_font.render("No scores yet! Play the game to set records!", True, (255, 255, 255))
            screen.blit(no_scores_text, (WIDTH // 2 - no_scores_text.get_width() // 2, 300))

            # Show storage status
            storage_type = "Database" if db_connection and db_connection.is_connected() else "File"
            status_text = score_font.render(f"Storage: {storage_type}", True, (255, 255, 255))
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, 350))

        # Back button
        pygame.draw.rect(screen, (100, 100, 100), back_rect, border_radius=10)
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2,
                                back_rect.centery - back_text.get_height() // 2))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    waiting = False
                    current_game_state = GAME_STATE_MENU
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    waiting = False
                    current_game_state = GAME_STATE_MENU


# ---------------- Title Screen ----------------
def show_title_screen():
    global current_game_state

    title = pygame.transform.scale(title_image, (WIDTH, HEIGHT))
    title_font = pygame.font.Font(None, 80)
    title_text = title_font.render("BEE BLUSTER", True, (51, 102, 0))

    button_font = pygame.font.Font(None, 60)
    level1_text = button_font.render("LEVEL 1", True, (0, 0, 0))
    level2_text = button_font.render("LEVEL 2", True, (0, 0, 0))
    scores_text = button_font.render("SCORES", True, (0, 0, 0))

    level1_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 60)
    level2_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 60)
    scores_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 250, 200, 60)

    # Play background music when title screen appears
    play_background_music()

    waiting = True
    while waiting:
        screen.blit(title, (0, 0))

        # Title
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

        # Level buttons
        pygame.draw.rect(screen, (255, 255, 255), level1_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), level2_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), scores_rect, border_radius=10)

        screen.blit(level1_text, (level1_rect.centerx - level1_text.get_width() // 2,
                                  level1_rect.centery - level1_text.get_height() // 2))
        screen.blit(level2_text, (level2_rect.centerx - level2_text.get_width() // 2,
                                  level2_rect.centery - level2_text.get_height() // 2))
        screen.blit(scores_text, (scores_rect.centerx - scores_text.get_width() // 2,
                                  scores_rect.centery - scores_text.get_height() // 2))

        # Show storage status on title screen
        status_font = pygame.font.Font(None, 30)
        storage_type = "Database" if db_connection and db_connection.is_connected() else "File"
        status_text = status_font.render(f"Storage: {storage_type}", True, (255, 255, 255))
        screen.blit(status_text, (10, HEIGHT - 40))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if level1_rect.collidepoint(event.pos):
                    return GAME_STATE_LEVEL1
                if level2_rect.collidepoint(event.pos):
                    return GAME_STATE_LEVEL2
                if scores_rect.collidepoint(event.pos):
                    current_game_state = GAME_STATE_SCORES
                    waiting = False
                    return GAME_STATE_MENU
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return GAME_STATE_LEVEL1
                if event.key == pygame.K_2:
                    return GAME_STATE_LEVEL2
                if event.key == pygame.K_s:
                    current_game_state = GAME_STATE_SCORES
                    waiting = False
                    return GAME_STATE_MENU


# ---------------- Game Over Screen ----------------
def show_game_over_screen(score, level):
    global current_game_state, final_score, current_level

    final_score = score
    current_level = level

    # Save score to database or file
    save_score(db_connection, score, level)

    title_font = pygame.font.Font(None, 80)
    title_text = title_font.render("GAME OVER", True, (255, 0, 0))

    score_font = pygame.font.Font(None, 50)
    score_text = score_font.render(f"Final Score: {score}", True, (255, 255, 255))

    button_font = pygame.font.Font(None, 50)
    menu_text = button_font.render("MAIN MENU", True, (255, 255, 255))
    scores_text = button_font.render("VIEW SCORES", True, (255, 255, 255))

    menu_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60)
    scores_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 150, 300, 60)

    waiting = True
    while waiting:
        screen.fill((0, 0, 0))

        # Title and score
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 4 + 100))

        # Buttons
        pygame.draw.rect(screen, (100, 100, 100), menu_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 100), scores_rect, border_radius=10)

        screen.blit(menu_text, (menu_rect.centerx - menu_text.get_width() // 2,
                                menu_rect.centery - menu_text.get_height() // 2))
        screen.blit(scores_text, (scores_rect.centerx - scores_text.get_width() // 2,
                                  scores_rect.centery - scores_text.get_height() // 2))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_rect.collidepoint(event.pos):
                    waiting = False
                    current_game_state = GAME_STATE_MENU
                if scores_rect.collidepoint(event.pos):
                    waiting = False
                    current_game_state = GAME_STATE_SCORES
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    waiting = False
                    current_game_state = GAME_STATE_MENU
                if event.key == pygame.K_s:
                    waiting = False
                    current_game_state = GAME_STATE_SCORES


# ---------------- Level 1 ----------------
def run_level1_game():
    # Player
    playerX = 400
    playerY = HEIGHT - 100
    player_speed = 6
    playerX_change = 0
    playerY_change = 0

    # Bullets
    bullets = []
    bullet_speed = 8
    max_bullets = 8

    # Power-Up
    power_up = {
        "x": random.randint(50, WIDTH - 50),
        "y": 0,
        "speed": 4,
        "active": False
    }

    # Enemies
    num_enemies = 5
    num_chasers = 1
    enemies = []
    chasers = []

    def create_enemy():
        corner = random.choice([(0, 0), (WIDTH - 64, 0), (0, HEIGHT - 64), (WIDTH - 64, HEIGHT - 64)])
        return {
            "x": corner[0],
            "y": corner[1],
            "angle": random.uniform(0, 2 * math.pi),
            "radius": math.hypot(CENTER_X - corner[0], CENTER_Y - corner[1]),
            "spiraling": True
        }

    def create_chaser():
        return {
            "x": random.randint(0, WIDTH - 64),
            "y": random.randint(0, HEIGHT // 2),
            "speed": 2
        }

    for _ in range(num_enemies):
        enemies.append(create_enemy())
    for _ in range(num_chasers):
        chasers.append(create_chaser())

    # Enemy Bullets
    enemybullets = []
    enemy_bullet_speed = 3
    max_enemybullets = 4
    enemy_bullet_timer = 0
    enemy_bullet_cooldown = 100

    # Score & Lives
    score = 0
    lives = 3
    font = pygame.font.Font(None, 36)

    # ---------------- Helper functions ----------------
    def player(x, y):
        screen.blit(playerImg, (x, y))

    def enemy(x, y):
        screen.blit(enemyImg, (x, y))

    def chaser(x, y):
        screen.blit(chaserImg, (x, y))

    def bullet_fire(x, y):
        if len(bullets) < max_bullets:
            if power_up["active"]:
                bullets.append([x - 10, y])
                bullets.append([x + 18, y])
                bullets.append([x + 40, y])
            else:
                bullets.append([x + 18, y])

    def enemybullet_fire(x, y):
        if len(enemybullets) < max_enemybullets:
            enemybullets.append([x + 12, y])

    def is_collision(x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1) < 27

    def is_powerup_collision(x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1) < 30

    def draw_lives():
        for i in range(lives):
            screen.blit(lifeImg, (10 + i * 40, 10))

    def draw_score():
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH - 150, 10))

    # ---------------- Game Loop ----------------
    running = True
    while running:
        dt = clock.tick(60) / 20
        screen.blit(background, (0, 0))

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    playerX_change = -player_speed
                if event.key == pygame.K_RIGHT:
                    playerX_change = player_speed
                if event.key == pygame.K_UP:
                    playerY_change = -player_speed
                if event.key == pygame.K_DOWN:
                    playerY_change = player_speed
                if event.key == pygame.K_SPACE:
                    bullet_fire(playerX, playerY)
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                    playerX_change = 0
                if event.key in [pygame.K_UP, pygame.K_DOWN]:
                    playerY_change = 0

        # Update Player
        playerX = max(0, min(WIDTH - 64, playerX + playerX_change * dt))
        playerY = max(0, min(HEIGHT - 64, playerY + playerY_change * dt))

        # Update Bullets
        bullets = [[x, y - bullet_speed * dt] for x, y in bullets if y > 0]
        for x, y in bullets:
            screen.blit(bulletImg, (x, y))

        # Enemy Movement
        for enemy_obj in enemies:
            if enemy_obj["spiraling"]:
                dx = CENTER_X - enemy_obj["x"]
                dy = CENTER_Y - enemy_obj["y"]
                dist = math.hypot(dx, dy)
                if dist < 10:
                    enemy_obj["spiraling"] = False
                    enemy_obj["orbit_angle"] = random.uniform(0, 2 * math.pi)
                else:
                    step = 2 * dt
                    enemy_obj["x"] += dx / dist * step
                    enemy_obj["y"] += dy / dist * step
            else:
                enemy_obj["orbit_angle"] += 0.03 * dt
                enemy_obj["x"] = CENTER_X + 100 * math.cos(enemy_obj["orbit_angle"])
                enemy_obj["y"] = CENTER_Y + 100 * math.sin(enemy_obj["orbit_angle"])

        # Chaser Movement
        for chaser_obj in chasers:
            dx = playerX - chaser_obj["x"]
            dy = playerY - chaser_obj["y"]
            dist = math.hypot(dx, dy)
            if dist != 0:
                chaser_obj["x"] += chaser_obj["speed"] * dx / dist * dt
                chaser_obj["y"] += chaser_obj["speed"] * dy / dist * dt

        # Enemy Bullets
        enemy_bullet_timer += 1
        if enemy_bullet_timer >= enemy_bullet_cooldown and enemies:
            shooter = random.choice(enemies)
            enemybullet_fire(shooter["x"], shooter["y"])
            enemy_bullet_timer = 0

        new_enemybullets = []
        for x, y in enemybullets:
            if y < HEIGHT:
                if is_collision(playerX, playerY, x, y):
                    lives -= 1
                    if lives == 0:
                        show_game_over_screen(score, 1)
                        running = False
                    continue
                new_enemybullets.append([x, y + enemy_bullet_speed * dt])
        enemybullets = new_enemybullets
        for x, y in enemybullets:
            screen.blit(enemybulletImg, (x, y))

        # Enemy Hit
        new_enemies = []
        for enemy_obj in enemies:
            hit = False
            for bullet in bullets:
                if is_collision(bullet[0], bullet[1], enemy_obj["x"], enemy_obj["y"]):
                    score += 1
                    hit = True
                    break
            if hit:
                new_enemies.append(create_enemy())
            else:
                new_enemies.append(enemy_obj)
        enemies = new_enemies

        # Chaser Hit
        new_chasers = []
        for chaser_obj in chasers:
            hit = False
            for bullet in bullets:
                if is_collision(bullet[0], bullet[1], chaser_obj["x"], chaser_obj["y"]):
                    score += 2
                    hit = True
                    break
            if hit:
                new_chasers.append(create_chaser())
            else:
                new_chasers.append(chaser_obj)
        chasers = new_chasers

        # Chaser Collision with Player
        new_chasers = []
        for chaser_obj in chasers:
            if is_collision(playerX, playerY, chaser_obj["x"], chaser_obj["y"]):
                lives -= 1
                if lives == 0:
                    show_game_over_screen(score, 1)
                    running = False
                new_chasers.append(create_chaser())
            else:
                new_chasers.append(chaser_obj)
        chasers = new_chasers

        # Power Up
        power_up["y"] += power_up["speed"] * dt
        if power_up["y"] > HEIGHT:
            power_up["y"] = 0
            power_up["x"] = random.randint(50, WIDTH - 50)
        if is_powerup_collision(playerX, playerY, power_up["x"], power_up["y"]):
            power_up["active"] = True
            power_up["y"] = HEIGHT + 100
        screen.blit(powerImg, (power_up["x"], power_up["y"]))

        # Draw Everything
        player(playerX, playerY)
        for enemy_obj in enemies:
            enemy(enemy_obj["x"], enemy_obj["y"])
        for chaser_obj in chasers:
            chaser(chaser_obj["x"], chaser_obj["y"])
        draw_lives()
        draw_score()

        pygame.display.update()

    return GAME_STATE_MENU


# ---------------- Level 2 ----------------
def run_level2_game():
    # Two Players
    player1 = {
        "x": 300,
        "y": HEIGHT - 100,
        "speed": 7,
        "x_change": 0,
        "y_change": 0,
        "lives": 3,
        "bullets": [],
        "power_up": False
    }

    player2 = {
        "x": 500,
        "y": HEIGHT - 100,
        "speed": 7,
        "x_change": 0,
        "y_change": 0,
        "lives": 3,
        "bullets": [],
        "power_up": False
    }

    # Bullets
    bullet_speed = 10
    max_bullets_per_player = 6

    # Power-Up
    power_up = {
        "x": random.randint(50, WIDTH - 50),
        "y": 0,
        "speed": 5,
        "active": False
    }

    # Enemies - More enemies for level 2
    num_enemies = 8
    num_chasers = 3
    enemies = []
    chasers = []

    def create_enemy():
        corner = random.choice([(0, 0), (WIDTH - 64, 0), (0, HEIGHT - 64), (WIDTH - 64, HEIGHT - 64)])
        return {
            "x": corner[0],
            "y": corner[1],
            "angle": random.uniform(0, 2 * math.pi),
            "radius": math.hypot(CENTER_X - corner[0], CENTER_Y - corner[1]),
            "spiraling": True,
            "speed": random.uniform(1.5, 2.5)
        }

    def create_chaser():
        return {
            "x": random.randint(0, WIDTH - 64),
            "y": random.randint(0, HEIGHT // 2),
            "speed": random.uniform(2.5, 3.5)
        }

    for _ in range(num_enemies):
        enemies.append(create_enemy())
    for _ in range(num_chasers):
        chasers.append(create_chaser())

    # Enemy Bullets
    enemybullets = []
    enemy_bullet_speed = 4
    max_enemybullets = 6
    enemy_bullet_timer = 0
    enemy_bullet_cooldown = 70

    # Score
    score = 0
    font = pygame.font.Font(None, 36)

    # ---------------- Helper functions ----------------
    def draw_player(x, y):
        screen.blit(playerImg, (x, y))

    def enemy(x, y):
        screen.blit(enemyImg, (x, y))

    def chaser(x, y):
        screen.blit(chaserImg, (x, y))

    def bullet_fire(player, x, y):
        if len(player["bullets"]) < max_bullets_per_player:
            if player["power_up"]:
                player["bullets"].append([x - 10, y])
                player["bullets"].append([x + 18, y])
                player["bullets"].append([x + 40, y])
            else:
                player["bullets"].append([x + 18, y])

    def enemybullet_fire(x, y):
        if len(enemybullets) < max_enemybullets:
            enemybullets.append([x + 12, y])
            if random.random() < 0.3:
                enemybullets.append([x, y])
                enemybullets.append([x + 24, y])

    def is_collision(x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1) < 27

    def is_powerup_collision(x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1) < 30

    def draw_lives():
        # Player 1 lives
        for i in range(player1["lives"]):
            screen.blit(lifeImg, (10 + i * 40, 10))
        # Player 2 lives
        for i in range(player2["lives"]):
            screen.blit(lifeImg, (WIDTH - 150 + i * 40, 10))

    def draw_score():
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 10))

    # ---------------- Game Loop ----------------
    running = True
    while running:
        dt = clock.tick(60) / 20
        screen.blit(background, (0, 0))

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Player 1 controls (Arrow keys)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player1["x_change"] = -player1["speed"]
                if event.key == pygame.K_RIGHT:
                    player1["x_change"] = player1["speed"]
                if event.key == pygame.K_UP:
                    player1["y_change"] = -player1["speed"]
                if event.key == pygame.K_DOWN:
                    player1["y_change"] = player1["speed"]
                if event.key == pygame.K_SPACE:
                    bullet_fire(player1, player1["x"], player1["y"])

                # Player 2 controls (WASD)
                if event.key == pygame.K_a:
                    player2["x_change"] = -player2["speed"]
                if event.key == pygame.K_d:
                    player2["x_change"] = player2["speed"]
                if event.key == pygame.K_w:
                    player2["y_change"] = -player2["speed"]
                if event.key == pygame.K_s:
                    player2["y_change"] = player2["speed"]
                if event.key == pygame.K_f:
                    bullet_fire(player2, player2["x"], player2["y"])

                if event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.KEYUP:
                # Player 1
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                    player1["x_change"] = 0
                if event.key in [pygame.K_UP, pygame.K_DOWN]:
                    player1["y_change"] = 0

                # Player 2
                if event.key in [pygame.K_a, pygame.K_d]:
                    player2["x_change"] = 0
                if event.key in [pygame.K_w, pygame.K_s]:
                    player2["y_change"] = 0

        # Update Players
        player1["x"] = max(0, min(WIDTH - 64, player1["x"] + player1["x_change"] * dt))
        player1["y"] = max(0, min(HEIGHT - 64, player1["y"] + player1["y_change"] * dt))

        player2["x"] = max(0, min(WIDTH - 64, player2["x"] + player2["x_change"] * dt))
        player2["y"] = max(0, min(HEIGHT - 64, player2["y"] + player2["y_change"] * dt))

        # Update Bullets
        player1["bullets"] = [[x, y - bullet_speed * dt] for x, y in player1["bullets"] if y > 0]
        player2["bullets"] = [[x, y - bullet_speed * dt] for x, y in player2["bullets"] if y > 0]

        for x, y in player1["bullets"]:
            screen.blit(bulletImg, (x, y))
        for x, y in player2["bullets"]:
            screen.blit(bulletImg, (x, y))

        # Enemy Movement
        for enemy_obj in enemies:
            if enemy_obj["spiraling"]:
                dx = CENTER_X - enemy_obj["x"]
                dy = CENTER_Y - enemy_obj["y"]
                dist = math.hypot(dx, dy)
                if dist < 10:
                    enemy_obj["spiraling"] = False
                    enemy_obj["orbit_angle"] = random.uniform(0, 2 * math.pi)
                else:
                    step = enemy_obj["speed"] * dt
                    enemy_obj["x"] += dx / dist * step
                    enemy_obj["y"] += dy / dist * step
            else:
                enemy_obj["orbit_angle"] += 0.04 * dt
                enemy_obj["x"] = CENTER_X + 80 * math.cos(enemy_obj["orbit_angle"])
                enemy_obj["y"] = CENTER_Y + 80 * math.sin(enemy_obj["orbit_angle"])

        # Chaser Movement - Chase player 1 or 2 randomly
        for chaser_obj in chasers:
            target_player = random.choice([player1, player2])
            dx = target_player["x"] - chaser_obj["x"]
            dy = target_player["y"] - chaser_obj["y"]
            dist = math.hypot(dx, dy)
            if dist != 0:
                chaser_obj["x"] += chaser_obj["speed"] * dx / dist * dt
                chaser_obj["y"] += chaser_obj["speed"] * dy / dist * dt

        # Enemy Bullets
        enemy_bullet_timer += 1
        if enemy_bullet_timer >= enemy_bullet_cooldown and enemies:
            for enemy_obj in random.sample(enemies, min(2, len(enemies))):
                enemybullet_fire(enemy_obj["x"], enemy_obj["y"])
            enemy_bullet_timer = 0

        new_enemybullets = []
        for x, y in enemybullets:
            if y < HEIGHT:
                # Check collision with both players
                hit_player1 = is_collision(player1["x"], player1["y"], x, y)
                hit_player2 = is_collision(player2["x"], player2["y"], x, y)

                if hit_player1:
                    player1["lives"] -= 1
                    if player1["lives"] <= 0 and player2["lives"] <= 0:
                        show_game_over_screen(score, 2)
                        running = False
                    continue
                elif hit_player2:
                    player2["lives"] -= 1
                    if player1["lives"] <= 0 and player2["lives"] <= 0:
                        show_game_over_screen(score, 2)
                        running = False
                    continue
                else:
                    new_enemybullets.append([x, y + enemy_bullet_speed * dt])
        enemybullets = new_enemybullets
        for x, y in enemybullets:
            screen.blit(enemybulletImg, (x, y))

        # Enemy Hit by bullets
        new_enemies = []
        for enemy_obj in enemies:
            hit = False
            # Check player 1 bullets
            for bullet in player1["bullets"]:
                if is_collision(bullet[0], bullet[1], enemy_obj["x"], enemy_obj["y"]):
                    score += 2
                    hit = True
                    player1["bullets"].remove(bullet)
                    break
            # Check player 2 bullets
            if not hit:
                for bullet in player2["bullets"]:
                    if is_collision(bullet[0], bullet[1], enemy_obj["x"], enemy_obj["y"]):
                        score += 2
                        hit = True
                        player2["bullets"].remove(bullet)
                        break
            if hit:
                new_enemies.append(create_enemy())
            else:
                new_enemies.append(enemy_obj)
        enemies = new_enemies

        # Chaser Hit by bullets
        new_chasers = []
        for chaser_obj in chasers:
            hit = False
            # Check player 1 bullets
            for bullet in player1["bullets"]:
                if is_collision(bullet[0], bullet[1], chaser_obj["x"], chaser_obj["y"]):
                    score += 3
                    hit = True
                    player1["bullets"].remove(bullet)
                    break
            # Check player 2 bullets
            if not hit:
                for bullet in player2["bullets"]:
                    if is_collision(bullet[0], bullet[1], chaser_obj["x"], chaser_obj["y"]):
                        score += 3
                        hit = True
                        player2["bullets"].remove(bullet)
                        break
            if hit:
                new_chasers.append(create_chaser())
            else:
                new_chasers.append(chaser_obj)
        chasers = new_chasers

        # Chaser Collision with Players
        new_chasers = []
        for chaser_obj in chasers:
            hit_player1 = is_collision(player1["x"], player1["y"], chaser_obj["x"], chaser_obj["y"])
            hit_player2 = is_collision(player2["x"], player2["y"], chaser_obj["x"], chaser_obj["y"])

            if hit_player1:
                player1["lives"] -= 1
                if player1["lives"] <= 0 and player2["lives"] <= 0:
                    show_game_over_screen(score, 2)
                    running = False
                new_chasers.append(create_chaser())
            elif hit_player2:
                player2["lives"] -= 1
                if player1["lives"] <= 0 and player2["lives"] <= 0:
                    show_game_over_screen(score, 2)
                    running = False
                new_chasers.append(create_chaser())
            else:
                new_chasers.append(chaser_obj)
        chasers = new_chasers

        # Power Up
        if random.random() < 0.005:
            power_up["x"] = random.randint(50, WIDTH - 50)
            power_up["y"] = 0
            power_up["active"] = False

        power_up["y"] += power_up["speed"] * dt
        if power_up["y"] > HEIGHT:
            power_up["y"] = HEIGHT + 100

        if power_up["y"] < HEIGHT:
            screen.blit(powerImg, (power_up["x"], power_up["y"]))
            # Check collision with both players
            if is_powerup_collision(player1["x"], player1["y"], power_up["x"], power_up["y"]):
                player1["power_up"] = True
                power_up["y"] = HEIGHT + 100
            elif is_powerup_collision(player2["x"], player2["y"], power_up["x"], power_up["y"]):
                player2["power_up"] = True
                power_up["y"] = HEIGHT + 100

        # Draw Everything
        draw_player(player1["x"], player1["y"])
        draw_player(player2["x"], player2["y"])
        for enemy_obj in enemies:
            enemy(enemy_obj["x"], enemy_obj["y"])
        for chaser_obj in chasers:
            chaser(chaser_obj["x"], chaser_obj["y"])
        draw_lives()
        draw_score()

        pygame.display.update()

    return GAME_STATE_MENU


# ---------------- Main Game Loop ----------------
while True:
    if current_game_state == GAME_STATE_MENU:
        current_game_state = show_title_screen()

    elif current_game_state == GAME_STATE_LEVEL1:
        current_game_state = run_level1_game()

    elif current_game_state == GAME_STATE_LEVEL2:
        current_game_state = run_level2_game()

    elif current_game_state == GAME_STATE_SCORES:
        show_scores_screen()

# Close database connection when game ends
if db_connection and db_connection.is_connected():
    db_connection.close()
    print("Database connection closed.")
