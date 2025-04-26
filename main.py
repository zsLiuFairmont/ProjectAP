from cmu_graphics import *
import random, math

# Screen Setup 
app.width = 600
app.height = 800

# Game Variables
player_width, player_height = 50, 30
player = Rect(app.width//2, app.height - 40, player_width, player_height, fill='green')
player_speed = 10

bullets = []
enemies = []
player_health = 3
head_count = 0
survival_steps = 0    # counts frames for survival time
bullet_speed = 7
spawn_timer = 0
SPAWN_DELAY = 20

fire_cooldown = 0
fire_cooldown_max = 12

keys_held = set()
game_over = False

# Helper Functions
def drawStar(cx, cy, outerRadius, innerRadius, points, fill):
    coords = []
    angleStep = 360 / points
    for i in range(points):
        angle = math.radians(i * angleStep)
        r = outerRadius if i % 2 == 0 else innerRadius
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        coords.extend([x, y])
    drawPolygon(*coords, fill=fill)

def setEnemyVertices(enemy):
    w, h = enemy.width, enemy.height
    if enemy.shape == "rect":
        enemy.vertices = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
    elif enemy.shape == "triangle":
        enemy.vertices = [(0, -h/2), (w/2, h/2), (-w/2, h/2)]
    elif enemy.shape == "star":
        points = 10
        outerR = w/2
        innerR = w/4
        verts = []
        angleStep = 360 / points
        for i in range(points):
            angle = math.radians(i * angleStep)
            r = outerR if i % 2 == 0 else innerR
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            verts.append((x, y))
        enemy.vertices = verts

def drawEnemy(enemy):
    if enemy.shape == "circle":
        drawCircle(enemy.centerX, enemy.centerY, enemy.width / 2, fill=enemy.fill)
    elif enemy.shape in ["rect", "triangle", "star"]:
        verts = []
        angle = math.radians(enemy.angle)
        for (vx, vy) in enemy.vertices:
            x_rot = vx * math.cos(angle) - vy * math.sin(angle)
            y_rot = vx * math.sin(angle) + vy * math.cos(angle)
            verts.extend([x_rot + enemy.centerX, y_rot + enemy.centerY])
        if len(verts) >= 6:
            drawPolygon(*verts, fill=enemy.fill)
    else:
        drawShape(enemy)

# Game Functions
def move_player():
    if 'left' in keys_held and player.left > 0:
        player.centerX -= player_speed
    if 'right' in keys_held and player.right < app.width:
        player.centerX += player_speed
    if 'up' in keys_held and player.top > 0:
        player.centerY -= player_speed
    if 'down' in keys_held and player.bottom < app.height:
        player.centerY += player_speed

def shoot():
    bullet = Rect(player.centerX, player.top - 10, 10, 20, fill='yellow')
    bullet.exploded = False
    bullet.explosion_timer = 0
    bullets.append(bullet)

def update_bullets():
    for bullet in bullets[:]:
        if bullet.exploded:
            if bullet.explosion_timer > 0:
                bullet.explosion_timer -= 1
            else:
                bullet.width *= 0.9
                bullet.height *= 0.9
            if bullet.width < 1 or bullet.height < 1:
                bullets.remove(bullet)
        else:
            bullet.centerY -= bullet_speed
            if bullet.bottom < 0:
                bullets.remove(bullet)

def update_enemies():
    global player_health, game_over
    for enemy in enemies[:]:
        if enemy.hit:
            enemy.centerY += enemy.speed * 2
            enemy.width *= 0.98
            enemy.height *= 0.98
            enemy.angle = (enemy.angle + enemy.rotationSpeed) % 360
            if enemy.shape != "circle":
                setEnemyVertices(enemy)
            if enemy.width < 5 or enemy.height < 5 or enemy.top > app.height:
                enemies.remove(enemy)
        else:
            enemy.t += 0.1
            if enemy.pattern == "straight":
                enemy.centerY += enemy.speed
            elif enemy.pattern == "wavy":
                enemy.centerY += enemy.speed
                enemy.centerX = enemy.initialX + math.sin(enemy.t + enemy.phase) * enemy.amplitude
            elif enemy.pattern == "zigzag":
                enemy.centerY += enemy.speed
                enemy.centerX += enemy.horizSpeed * enemy.direction
                if enemy.left < 0 or enemy.right > app.width:
                    enemy.direction *= -1
            elif enemy.pattern == "spiral":
                enemy.t += 0.05
                enemy.centerY += enemy.speed
                enemy.centerX = enemy.initialX + enemy.t * enemy.factor * math.cos(enemy.t)
            elif enemy.pattern == "random":
                enemy.centerX += enemy.vx
                enemy.centerY += enemy.vy
                if enemy.left < 0 or enemy.right > app.width:
                    enemy.vx *= -1
                if enemy.top < 0 or enemy.bottom > app.height:
                    enemy.vy *= -1
            if enemy.hitsShape(player):
                player_health -= 1
                enemies.remove(enemy)
                if player_health <= 0:
                    game_over = True
        if enemy.top > app.height and enemy in enemies:
            enemies.remove(enemy)

def check_collisions():
    global head_count
    for bullet in bullets[:]:
        if bullet.exploded:
            continue
        for enemy in enemies:
            if not enemy.hit and bullet.hitsShape(enemy):
                enemy.hit = True
                enemy.fill = 'black'
                enemy.angle = 0
                enemy.rotationSpeed = 20
                bullet.exploded = True
                bullet.explosion_timer = 10
                head_count += 1
                break

def spawn_enemy():
    x = random.randint(40, app.width - 40)
    size = random.randint(30, 60)
    enemy = Rect(x, 20, size, size, fill='red')
    enemy.speed = random.uniform(3, 7)
    enemy.t = 0
    enemy.hit = False
    enemy.angle = 0
    enemy.rotationSpeed = 0
    enemy.pattern = random.choice(["straight", "wavy", "zigzag", "spiral", "random"])
    if enemy.pattern == "wavy":
        enemy.phase = random.uniform(0, 2*math.pi)
        enemy.amplitude = random.uniform(20, 80)
        enemy.initialX = enemy.centerX
    elif enemy.pattern == "zigzag":
        enemy.horizSpeed = random.uniform(1, 3)
        enemy.direction = random.choice([-1, 1])
    elif enemy.pattern == "spiral":
        enemy.initialX = enemy.centerX
        enemy.factor = random.uniform(1, 3)
    elif enemy.pattern == "random":
        enemy.vx = random.uniform(-3, 3)
        enemy.vy = random.uniform(1, 3)
    enemy.shape = random.choice(["rect", "circle", "triangle", "star"])
    if enemy.shape != "circle":
        setEnemyVertices(enemy)
    enemies.append(enemy)

# Event Handlers
def onKeyPress(key):
    global fire_cooldown, game_over
    if key == 'space' and not game_over and fire_cooldown <= 0:
        shoot()
        fire_cooldown = fire_cooldown_max
    elif key == 'r' and game_over:
        reset_game()
    keys_held.add(key)

def onKeyRelease(key):
    keys_held.discard(key)

def onMousePress(x, y):
    bx, by = app.width/2 - 80, app.height/2 + 80
    if game_over and bx < x < bx+160 and by < y < by+40:
        reset_game()

def onStep():
    global spawn_timer, fire_cooldown, survival_steps
    if game_over:
        return
    survival_steps += 1
    move_player()
    update_bullets()
    update_enemies()
    check_collisions()
    spawn_timer += 1
    if spawn_timer >= SPAWN_DELAY:
        spawn_enemy()
        spawn_timer = 0
    if fire_cooldown > 0:
        fire_cooldown -= 1

def onDraw():
    clear('black')
    for bullet in bullets:
        if bullet.exploded:
            drawStar(bullet.centerX, bullet.centerY,
                     bullet.width, bullet.width/2, 20, fill='orange')
        else:
            drawShape(bullet)
    for enemy in enemies:
        if enemy.shape == "circle":
            drawCircle(enemy.centerX, enemy.centerY,
                       enemy.width/2, fill=enemy.fill)
        else:
            drawEnemy(enemy)
    drawPlayerGraphic()

    # — HUD in red, left-aligned at x=20 so it's fully on-screen —
    seconds = survival_steps / 60
    drawLabel(f"Heads: {head_count}", 20, 20,
              size=20, fill='red', bold=True, align='left')
    drawLabel(f"Time: {seconds:.1f}s", 20, 50,
              size=20, fill='red', bold=True, align='left')

    if game_over:
        drawRect(0, 0, app.width, app.height,
                 fill='black', opacity=0.7)
        drawLabel("GAME OVER", app.width/2, app.height/2,
                  size=48, fill='red', bold=True)
        drawLabel("Press R to Restart",
                  app.width/2, app.height/2 + 50,
                  size=20, fill='red')
        button = Rect(app.width/2 - 80, app.height/2 + 80,
                      160, 40, fill='gray', roundness=10)
        drawLabel("Restart", app.width/2, app.height/2 + 100,
                  size=20, fill='red')

def drawPlayerGraphic():
    drawRect(player.left, player.top,
             player.width, player.height, fill='green')

def reset_game():
    global bullets, enemies, player_health
    global head_count, survival_steps
    global spawn_timer, fire_cooldown, game_over
    bullets.clear()
    enemies.clear()
    player_health = 3
    head_count = 0
    survival_steps = 0
    spawn_timer = 0
    fire_cooldown = 0
    game_over = False
    player.centerX = app.width//2
    player.centerY = app.height - 40

cmu_graphics.run()
