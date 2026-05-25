from tkinter import *
import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from tkinter.ttk import Progressbar
import threading
import sys
import platform

if platform.system() == "Windows":
    import winsound

root = tk.Tk()
# rest_to edit
# ── Window ───────────────────────────────────────────────────────
WIN_WIDTH  = 1280
WIN_HEIGHT = 720
root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
root.resizable(False, False)

# ── Level configs ─────────────────────────────────────────────────
# Each key maps to a dict of gameplay parameters
LEVELS = {
    "Easy": {
        "label"              : "EASY",
        "color"              : "#2ecc71",   # green
        "enemy_count"        : 4,
        "enemy_speed"        : 1,
        "enemy_shoot_delay"  : 2500,        # ms between enemy salvos
        "enemy_bullet_speed" : 2,
        "player_speed"       : 9,
        "bullet_speed"       : 14,
        "gravity"            : 5,
        "jump_power"         : 20,
        "max_blood"          : 5,
        "max_lives"          : 3,
        "timer_seconds"      : 90,
        "score_to_win"       : 4,           # kill all enemies to win
        "shooting_distance"  : 280,
    },
    "Medium": {
        "label"              : "MEDIUM",
        "color"              : "#f39c12",   # orange
        "enemy_count"        : 7,
        "enemy_speed"        : 2,
        "enemy_shoot_delay"  : 1800,
        "enemy_bullet_speed" : 3,
        "player_speed"       : 8,
        "bullet_speed"       : 12,
        "gravity"            : 6,
        "jump_power"         : 18,
        "max_blood"          : 3,
        "max_lives"          : 3,
        "timer_seconds"      : 60,
        "score_to_win"       : 7,
        "shooting_distance"  : 350,
    },
    "Hard": {
        "label"              : "HARD",
        "color"              : "#e74c3c",   # red
        "enemy_count"        : 10,
        "enemy_speed"        : 3,
        "enemy_shoot_delay"  : 1000,
        "enemy_bullet_speed" : 5,
        "player_speed"       : 7,
        "bullet_speed"       : 11,
        "gravity"            : 7,
        "jump_power"         : 16,
        "max_blood"          : 3,
        "max_lives"          : 1,           # only one life!
        "timer_seconds"      : 45,
        "score_to_win"       : 10,
        "shooting_distance"  : 420,
    },
}

# ── Global game state ─────────────────────────────────────────────
scroll_offset   = 0
jump_count      = 0
score           = 0
enemy_direction = 1
enemy_step      = 0
player_bullets  = []
enemy_bullets   = []
keyPressed      = []
obstacles       = []
pol_pots        = []
is_jumping      = False
game_running    = False
current_lives   = 3
life            = 3

# ── Main menu canvas ──────────────────────────────────────────────
menu_frame  = tk.Frame(root, width=WIN_WIDTH, height=WIN_HEIGHT)
menu_frame.pack()
menu_canvas = tk.Canvas(menu_frame, width=WIN_WIDTH, height=WIN_HEIGHT)
menu_canvas.pack()

main_img = Image.open("img/main-screen.png").resize((WIN_WIDTH, WIN_HEIGHT))
imageTk_main = ImageTk.PhotoImage(main_img)
menu_canvas.create_image(0, 0, anchor="nw", image=imageTk_main)
menu_canvas.imageTk_main = imageTk_main


# ── Sound ─────────────────────────────────────────────────────────
def play_sound_loop():
    if platform.system() == "Windows":
        winsound.PlaySound('sound/dark-engine-logo-141942.wav',
                           winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC)

def play_shooting_sound():
    if platform.system() == "Windows":
        winsound.PlaySound("sound/9mm-pistol-shoot-short-reverb-7152.wav", winsound.SND_ASYNC)

threading.Thread(target=play_sound_loop, daemon=True).start()


# ════════════════════════════════════════════════════════════════
#  LEVEL SELECT SCREEN
# ════════════════════════════════════════════════════════════════
def show_level_select():
    """Opens the level-select window, called from Start button."""
    root.withdraw()
    ls = tk.Toplevel(root)
    ls.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
    ls.resizable(False, False)
    ls.title("Select Difficulty")

    # Background — reuse main screen image, slightly darkened
    bg_img = Image.open("img/main-screen.png").resize((WIN_WIDTH, WIN_HEIGHT))
    # Darken by blending with black
    dark = Image.new("RGB", bg_img.size, (0, 0, 0))
    bg_img = Image.blend(bg_img.convert("RGB"), dark, alpha=0.45)
    bg_tk = ImageTk.PhotoImage(bg_img)
    lc = tk.Canvas(ls, width=WIN_WIDTH, height=WIN_HEIGHT)
    lc.pack()
    lc.create_image(0, 0, anchor="nw", image=bg_tk)
    lc.bg_tk = bg_tk  # keep ref

    # Title
    lc.create_text(WIN_WIDTH // 2, 120,
                   text="SELECT DIFFICULTY",
                   font=("Arial", 48, "bold"),
                   fill="white")

    # Three difficulty buttons in a row
    btn_y    = WIN_HEIGHT // 2
    positions = {"Easy": WIN_WIDTH // 2 - 320,
                 "Medium": WIN_WIDTH // 2,
                 "Hard":   WIN_WIDTH // 2 + 320}

    def on_select(level_key):
        ls.destroy()
        start_loading(level_key)

    for key, cfg in LEVELS.items():
        bx = positions[key]

        # Card background
        lc.create_rectangle(bx - 120, btn_y - 110,
                            bx + 120, btn_y + 110,
                            fill="#1a1a2e", outline=cfg["color"], width=3)

        # Difficulty label
        lc.create_text(bx, btn_y - 75,
                       text=cfg["label"],
                       font=("Arial", 26, "bold"),
                       fill=cfg["color"])

        # Stats text
        stats = (
            f"Enemies : {cfg['enemy_count']}\n"
            f"Lives   : {cfg['max_lives']}\n"
            f"Health  : {cfg['max_blood']}\n"
            f"Time    : {cfg['timer_seconds']}s"
        )
        lc.create_text(bx, btn_y + 5,
                       text=stats,
                       font=("Courier", 13),
                       fill="white",
                       justify="left")

        # Select button
        tk.Button(ls, text=f"Play {cfg['label']}",
                  font=("Arial", 16, "bold"),
                  bg=cfg["color"], fg="white", border=4,
                  width=12,
                  command=lambda k=key: on_select(k)
                  ).place(x=bx - 80, y=btn_y + 75)

    # Back button
    def go_back():
        ls.destroy()
        root.deiconify()

    tk.Button(ls, text="← Back", font=("Arial", 16),
              bg="#555", fg="white",
              command=go_back).place(x=30, y=30)

    ls.focus_set()
    ls.mainloop()


# ════════════════════════════════════════════════════════════════
#  LOADING SCREEN
# ════════════════════════════════════════════════════════════════
def start_loading(level_key):
    loading_screen = tk.Toplevel(root)
    loading_screen.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
    loading_screen.title("Loading…")
    lframe = tk.Frame(loading_screen, width=WIN_WIDTH, height=WIN_HEIGHT)
    lframe.pack()
    lcanvas = tk.Canvas(lframe, width=WIN_WIDTH, height=WIN_HEIGHT)
    lcanvas.pack()

    img1   = Image.open("img/loadingscreen.png").resize((WIN_WIDTH, WIN_HEIGHT))
    imgTk  = ImageTk.PhotoImage(img1)
    lcanvas.create_image(0, 0, anchor="nw", image=imgTk)
    lcanvas.imgTk = imgTk

    # Show selected difficulty label on loading screen
    cfg = LEVELS[level_key]
    lcanvas.create_text(WIN_WIDTH // 2, 60,
                        text=f"Difficulty: {cfg['label']}",
                        font=("Arial", 28, "bold"),
                        fill=cfg["color"])

    pb = ttk.Progressbar(loading_screen, orient="horizontal",
                         length=400, mode="determinate")
    pb.place(x=(WIN_WIDTH - 400) // 2, y=WIN_HEIGHT - 120)

    def _do_loading():
        if pb['value'] >= pb['maximum']:
            start_game(loading_screen, level_key)
            return
        pb['value'] += 1
        root.after(15, _do_loading)

    _do_loading()


# ════════════════════════════════════════════════════════════════
#  MAIN GAME
# ════════════════════════════════════════════════════════════════
def start_game(loading_screen, level_key):
    global scroll_offset, jump_count, score
    global enemy_direction, enemy_step
    global player_bullets, enemy_bullets, keyPressed, obstacles, pol_pots
    global is_jumping, game_running
    global current_lives, life

    cfg = LEVELS[level_key]

    # ── Per-level constants (local, from cfg) ─────────────────────
    PLAYER_SPEED       = cfg["player_speed"]
    BULLET_SPEED       = cfg["bullet_speed"]
    GRAVITY_FORCE      = cfg["gravity"]
    JUMP_POWER         = cfg["jump_power"]
    ENEMY_BULLET_SPEED = cfg["enemy_bullet_speed"]
    SHOOT_DELAY        = cfg["enemy_shoot_delay"]
    SHOOTING_DISTANCE  = cfg["shooting_distance"]
    ENEMY_SPEED        = cfg["enemy_speed"]
    ENEMY_COUNT        = cfg["enemy_count"]
    MAX_BLOOD          = cfg["max_blood"]
    MAX_LIVES          = cfg["max_lives"]
    TIMER_SECS         = cfg["timer_seconds"]

    # ── Reset state ───────────────────────────────────────────────
    scroll_offset   = 0
    jump_count      = 0
    score           = 0
    enemy_direction = 1
    enemy_step      = 0
    player_bullets  = []
    enemy_bullets   = []
    keyPressed      = []
    obstacles       = []
    pol_pots        = []
    is_jumping      = False
    game_running    = True
    current_lives   = MAX_BLOOD
    life            = MAX_LIVES

    root.withdraw()
    loading_screen.withdraw()

    gw = tk.Toplevel()
    gw.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
    gw.resizable(False, False)
    gw.title(f"Pol Pot Game — {cfg['label']}")
    gw.protocol("WM_DELETE_WINDOW", lambda: _quit_game(gw))

    gframe = tk.Frame(gw, width=WIN_WIDTH, height=WIN_HEIGHT)
    gframe.pack()
    gc = tk.Canvas(gframe, width=WIN_WIDTH, height=WIN_HEIGHT, bg="black")
    gc.pack()

    # ── Background ────────────────────────────────────────────────
    bg_img = tk.PhotoImage(file="img/background-game.png")
    bg1 = gc.create_image(0,         0, image=bg_img, anchor="nw")
    bg2 = gc.create_image(WIN_WIDTH, 0, image=bg_img, anchor="nw")
    gc.bg_img = bg_img

    # ── Player ────────────────────────────────────────────────────
    walk_imgs = [tk.PhotoImage(file=f"img/Characters/player/Run/{i}.png")
                 for i in range(6)]
    gc.walk_imgs = walk_imgs

    GROUND_TOP     = WIN_HEIGHT - 220
    SPRITE_H       = 60
    SPRITE_W       = 24
    PLAYER_START_X = 150
    PLAYER_START_Y = GROUND_TOP - SPRITE_H

    player = gc.create_image(PLAYER_START_X, PLAYER_START_Y,
                             image=walk_imgs[0], anchor="s")

    # Ground
    gc.create_rectangle(0, GROUND_TOP, WIN_WIDTH * 10,
                        WIN_HEIGHT, fill="#5a3e1b", tags="wall")

    # ── HUD ───────────────────────────────────────────────────────
    # Difficulty badge (top-center)
    gc.create_rectangle(WIN_WIDTH // 2 - 80, 4,
                        WIN_WIDTH // 2 + 80, 34,
                        fill=cfg["color"], outline="")
    gc.create_text(WIN_WIDTH // 2, 19,
                   text=cfg["label"],
                   font=("Arial", 14, "bold"),
                   fill="white")

    style = tk.ttk.Style()
    style.theme_use('default')
    style.configure("Blood.Horizontal.TProgressbar", troughcolor='#333', background='red')
    style.configure("Empty.Horizontal.TProgressbar", troughcolor='#333', background='gray')

    progress_bar = Progressbar(gw, length=180, mode="determinate",
                               maximum=MAX_BLOOD,
                               style="Blood.Horizontal.TProgressbar")
    progress_bar.place(x=10, y=8)
    progress_bar["value"] = current_lives

    hfull  = ImageTk.PhotoImage(Image.open("img/heart_full.png").resize((36, 36)))
    hempty = ImageTk.PhotoImage(Image.open("img/heart_empty.png").resize((36, 36)))
    gc.hfull  = hfull   # keep reference — prevents garbage collection
    gc.hempty = hempty

    # Draw hearts directly on game canvas so they always refresh correctly
    HEART_X_START = 10
    HEART_Y       = 50
    HEART_GAP     = 40
    heart_items = []   # canvas item IDs
    for i in range(MAX_LIVES):
        hx = HEART_X_START + i * HEART_GAP
        item = gc.create_image(hx, HEART_Y, image=hfull, anchor="nw")
        heart_items.append(item)

    score_label = tk.Label(gw, text="Score: 0", font=("Arial", 18, "bold"),
                           bg="black", fg="white")
    score_label.place(x=WIN_WIDTH - 160, y=8)

    timer_label = tk.Label(gw, text="", font=("Arial", 18),
                           bg="black", fg="white")
    timer_label.place(x=WIN_WIDTH // 2 - 80, y=38)

    def _quit_game(window):
        global game_running
        game_running = False
        window.destroy()
        root.deiconify()

    tk.Button(gw, text='Menu', width=6, font=('Arial', 12),
              command=lambda: _quit_game(gw),
              bg='brown', fg='white').place(x=WIN_WIDTH - 70, y=WIN_HEIGHT - 44)

    # ── Platforms ─────────────────────────────────────────────────
    def create_obstacles():
        # More platforms on harder levels
        base_walls = [
            (180, 440, 320, 470, "white"),
            (400, 340, 540, 370, "white"),
            (600, 240, 740, 270, "white"),
            (750, 380, 860, 410, "red"),
            (900, 280, 1000,310, "white"),
            (1050,420,1180, 450, "white"),
        ]
        extra_hard = [
            (300, 180, 440, 210, "red"),
            (700, 160, 840, 190, "white"),
            (1100,260,1200, 290, "red"),
            (500, 480, 620, 510, "white"),
        ]
        walls_data = base_walls + (extra_hard if level_key == "Hard" else [])
        for x1, y1, x2, y2, color in walls_data:
            w = gc.create_rectangle(x1, y1, x2, y2, fill=color, tags="wall")
            obstacles.append(w)

    # ── Enemies ───────────────────────────────────────────────────
    enemy_img = tk.PhotoImage(file="img/Reverse characters/enemy/Run/0.png")
    gc.enemy_img = enemy_img

    # Enemy sprite half-height so feet sit on surface (same logic as player)
    ENEMY_SPRITE_H = 40

    def create_enemies():
        # Each entry = (foot_x, surface_y)
        # surface_y is the TOP of whatever surface the enemy stands on.
        # Enemy is placed with anchor="s" so cy = surface_y (feet on surface).

        GROUND = GROUND_TOP   # y=500 — the main ground surface

        # Platforms (x1,y1,x2,y2) from create_obstacles — pick mid-x, top-y
        # base platforms (all levels):
        #   (180,440,320,470)  mid=250, top=440
        #   (400,340,540,370)  mid=470, top=340
        #   (600,240,740,270)  mid=670, top=240
        #   (750,380,860,410)  mid=805, top=380
        #   (900,280,1000,310) mid=950, top=280
        #   (1050,420,1180,450)mid=1115,top=420

        # Positions per difficulty — (foot_x, surface_y)
        positions_easy = [
            (500,  GROUND),   # on ground, left area
            (720,  GROUND),   # on ground
            (950,  GROUND),   # on ground
            (250,  440),      # on platform 1
        ]

        positions_medium = [
            (500,  GROUND),
            (700,  GROUND),
            (950,  GROUND),
            (1150, GROUND),
            (250,  440),      # platform 1
            (470,  340),      # platform 2
            (805,  380),      # platform 4
        ]

        positions_hard = [
            (450,  GROUND),
            (620,  GROUND),
            (820,  GROUND),
            (1000, GROUND),
            (1200, GROUND),
            (250,  440),      # platform 1
            (470,  340),      # platform 2
            (670,  240),      # platform 3 (high)
            (805,  380),      # platform 4
            (950,  280),      # platform 5 (high)
        ]

        pos_map = {
            "Easy"  : positions_easy,
            "Medium": positions_medium,
            "Hard"  : positions_hard,
        }

        for (ex, surface_y) in pos_map[level_key][:ENEMY_COUNT]:
            # anchor="s" → cy is the feet of the sprite
            ey = surface_y  # feet on surface
            e  = gc.create_image(ex, ey, image=enemy_img,
                                 anchor="s", tags="enemy")
            pol_pots.append(e)

    # ── Enemy movement ────────────────────────────────────────────
    def move_enemies():
        global enemy_direction, enemy_step
        if not game_running:
            return
        for pol_pot in pol_pots:
            gc.move(pol_pot, enemy_direction * ENEMY_SPEED, 0)
        enemy_step += 1
        if enemy_step >= 60:
            enemy_direction *= -1
            enemy_step = 0
        gw.after(50, move_enemies)

    # ── Enemy shooting ────────────────────────────────────────────
    def enemy_shoot():
        if not game_running:
            return
        px, py = gc.coords(player)
        for pol_pot in pol_pots[:]:
            coords = gc.coords(pol_pot)
            if not coords:
                continue
            ex, ey = coords
            if abs(ex - px) <= SHOOTING_DISTANCE:
                dx = -1 if ex > px else 1
                b  = gc.create_oval(ex - 5, ey - 3, ex + 5, ey + 3, fill="orange")
                enemy_bullets.append((b, dx))
        gw.after(SHOOT_DELAY, enemy_shoot)

    def move_enemy_bullets():
        if not game_running:
            return
        to_remove = []
        px, py = gc.coords(player)
        for item in enemy_bullets[:]:
            b, dx = item
            gc.move(b, dx * ENEMY_BULLET_SPEED, 0)
            coords = gc.coords(b)
            if not coords:
                to_remove.append(item)
                continue
            bx1, by1, bx2, by2 = coords
            if bx2 < 0 or bx1 > WIN_WIDTH:
                gc.delete(b)
                to_remove.append(item)
                continue
            overlap = gc.find_overlapping(bx1, by1, bx2, by2)
            if player in overlap:
                gc.delete(b)
                to_remove.append(item)
                got_hit()
        for item in to_remove:
            if item in enemy_bullets:
                enemy_bullets.remove(item)
        gw.after(20, move_enemy_bullets)

    # ── Player input ──────────────────────────────────────────────
    def handle_key_press(event):
        global is_jumping, jump_count
        k = event.keysym
        if k == "Left"  and "Left"  not in keyPressed: keyPressed.append("Left")
        if k == "Right" and "Right" not in keyPressed: keyPressed.append("Right")
        if k == "Up" and not is_jumping:
            is_jumping = True
            jump_count = JUMP_POWER

    def handle_key_release(event):
        k = event.keysym
        if k == "Left"  and "Left"  in keyPressed: keyPressed.remove("Left")
        if k == "Right" and "Right" in keyPressed: keyPressed.remove("Right")

    def shoot(event):
        if not game_running:
            return
        x, y   = gc.coords(player)
        mid_y  = y - SPRITE_H
        b = gc.create_rectangle(x + 20, mid_y - 4, x + 36, mid_y + 4,
                                fill="red")
        player_bullets.append(b)
        play_shooting_sound()

    # ── Walk animation ────────────────────────────────────────────
    anim_frame = [0]
    def walk_animation():
        anim_frame[0] = (anim_frame[0] + 1) % len(walk_imgs)
        gc.itemconfig(player, image=walk_imgs[anim_frame[0]])

    # ── Collision helpers ─────────────────────────────────────────
    def check_movement(item, dx=0, dy=0):
        cx, cy  = gc.coords(item)   # anchor="s": cy = feet
        nx1 = cx + dx - SPRITE_W
        ny1 = cy + dy - SPRITE_H * 2
        nx2 = cx + dx + SPRITE_W
        ny2 = cy + dy
        for wall_id in gc.find_withtag("wall"):
            if wall_id in gc.find_overlapping(nx1, ny1, nx2, ny2):
                return False
        return True

    def apply_gravity():
        if check_movement(player, 0, GRAVITY_FORCE):
            gc.move(player, 0, GRAVITY_FORCE)

    # ── Background scroll ─────────────────────────────────────────
    def scroll_background(dx):
        gc.move(bg1, -dx // 4, 0)
        gc.move(bg2, -dx // 4, 0)
        b1x = gc.coords(bg1)[0]
        b2x = gc.coords(bg2)[0]
        if b1x <= -WIN_WIDTH: gc.coords(bg1, b2x + WIN_WIDTH, 0)
        if b2x <= -WIN_WIDTH: gc.coords(bg2, b1x + WIN_WIDTH, 0)
        if b1x >= WIN_WIDTH:  gc.coords(bg1, b2x - WIN_WIDTH, 0)
        if b2x >= WIN_WIDTH:  gc.coords(bg2, b1x - WIN_WIDTH, 0)

    def scroll_world(dx):
        global scroll_offset
        px, py = gc.coords(player)
        if dx > 0 and px >= WIN_WIDTH * 0.55:
            shift = -PLAYER_SPEED
            gc.move(player, shift, 0)
            for o in obstacles:              gc.move(o, shift, 0)
            for e in pol_pots:               gc.move(e, shift, 0)
            for b, d in enemy_bullets:       gc.move(b, shift, 0)
            scroll_offset += PLAYER_SPEED
            scroll_background(PLAYER_SPEED)
        elif dx < 0 and px <= WIN_WIDTH * 0.2:
            shift = PLAYER_SPEED
            gc.move(player, shift, 0)
            for o in obstacles:              gc.move(o, shift, 0)
            for e in pol_pots:               gc.move(e, shift, 0)
            for b, d in enemy_bullets:       gc.move(b, shift, 0)
            scroll_offset -= PLAYER_SPEED
            scroll_background(-PLAYER_SPEED)

    # ── Player bullets ────────────────────────────────────────────
    def move_player_bullets():
        for b in player_bullets[:]:
            gc.move(b, BULLET_SPEED, 0)
            coords = gc.coords(b)
            if not coords or coords[0] > WIN_WIDTH:
                gc.delete(b)
                if b in player_bullets: player_bullets.remove(b)

    def check_bullet_collision():
        for b in player_bullets[:]:
            coords = gc.coords(b)
            if not coords:
                if b in player_bullets: player_bullets.remove(b)
                continue
            overlap  = gc.find_overlapping(*coords)
            removed  = False
            for o in obstacles:
                if o in overlap:
                    gc.delete(b)
                    if b in player_bullets: player_bullets.remove(b)
                    removed = True
                    break
            if removed:
                continue
            for e in pol_pots[:]:
                if e in overlap:
                    gc.delete(e)
                    gc.delete(b)
                    if e in pol_pots:        pol_pots.remove(e)
                    if b in player_bullets:  player_bullets.remove(b)
                    increase_score()
                    break

    # ── Health / lives ────────────────────────────────────────────
    def update_blood():
        progress_bar["value"] = current_lives
        progress_bar["style"] = ("Blood.Horizontal.TProgressbar"
                                 if current_lives > 0 else "Empty.Horizontal.TProgressbar")

    def update_hearts():
        """Redraw all heart icons based on current_lives."""
        for i, item in enumerate(heart_items):
            gc.itemconfig(item, image=hfull if i < current_lives else hempty)

    def got_hit():
        global current_lives
        current_lives -= 1
        update_blood()
        update_hearts()
        if current_lives <= 0:
            lose_life_and_reset()

    def lose_life_and_reset():
        global life, current_lives
        life -= 1
        if life <= 0:
            game_over(won=False)
        else:
            current_lives = MAX_BLOOD
            update_blood()
            update_hearts()
            gc.coords(player, PLAYER_START_X, PLAYER_START_Y)

    # ── Score ─────────────────────────────────────────────────────
    def increase_score():
        global score
        score += 1
        score_label.config(text=f"Score: {score}")
        # Win condition: all enemies defeated
        if score >= cfg["score_to_win"] and len(pol_pots) == 0:
            game_over(won=True)

    # ── Game over / win screen ────────────────────────────────────
    def game_over(won=False):
        global game_running
        game_running = False

        gc.create_rectangle(0, 0, WIN_WIDTH, WIN_HEIGHT,
                            fill="black", stipple="gray50")

        if won:
            title_text  = "YOU WIN!"
            title_color = cfg["color"]
            sub_text    = f"All enemies defeated on {cfg['label']} mode!"
        else:
            title_text  = "GAME OVER"
            title_color = "red"
            sub_text    = f"Better luck next time on {cfg['label']} mode."

        gc.create_text(WIN_WIDTH // 2, WIN_HEIGHT // 2 - 80,
                       text=title_text,
                       fill=title_color,
                       font=("Arial", 72, "bold"))
        gc.create_text(WIN_WIDTH // 2, WIN_HEIGHT // 2,
                       text=sub_text,
                       fill="white",
                       font=("Arial", 22))
        gc.create_text(WIN_WIDTH // 2, WIN_HEIGHT // 2 + 50,
                       text=f"Final Score: {score}",
                       fill="yellow",
                       font=("Arial", 32, "bold"))

        btn_y = WIN_HEIGHT // 2 + 110
        tk.Button(gw, text="Try Again",
                  font=("Arial", 16, "bold"),
                  bg=cfg["color"], fg="white", width=10,
                  command=lambda: (gw.destroy(), root.deiconify(),
                                   start_loading(level_key))
                  ).place(x=WIN_WIDTH // 2 - 160, y=btn_y)

        tk.Button(gw, text="Change Level",
                  font=("Arial", 16, "bold"),
                  bg="#555", fg="white", width=12,
                  command=lambda: (gw.destroy(), root.deiconify(),
                                   show_level_select())
                  ).place(x=WIN_WIDTH // 2 + 20, y=btn_y)

    # ── Timer ─────────────────────────────────────────────────────
    def countdown(seconds):
        if not game_running:
            return
        if seconds >= 0:
            # Color warning when < 10 s
            color = "red" if seconds <= 10 else "white"
            timer_label.config(text=f"Time: {seconds}s", fg=color)
            gw.after(1000, countdown, seconds - 1)
        else:
            timer_label.config(text="Time's up!")
            game_over(won=False)

    # ── Main game loop ────────────────────────────────────────────
    def game_loop():
        global is_jumping, jump_count
        if not game_running:
            return
        dx = 0
        if "Left" in keyPressed:
            if check_movement(player, -PLAYER_SPEED, 0):
                gc.move(player, -PLAYER_SPEED, 0)
            dx = -PLAYER_SPEED
            walk_animation()
        elif "Right" in keyPressed:
            if check_movement(player, PLAYER_SPEED, 0):
                gc.move(player, PLAYER_SPEED, 0)
            dx = PLAYER_SPEED
            walk_animation()

        if is_jumping:
            if check_movement(player, 0, -GRAVITY_FORCE):
                gc.move(player, 0, -GRAVITY_FORCE)
            jump_count -= 1
            if jump_count <= 0:
                is_jumping = False
        else:
            apply_gravity()

        scroll_world(dx)
        move_player_bullets()
        check_bullet_collision()
        gw.after(20, game_loop)

    # ── Start ─────────────────────────────────────────────────────
    gc.bind_all("<KeyPress>",   handle_key_press)
    gc.bind_all("<KeyRelease>", handle_key_release)
    gc.bind_all("<space>",      shoot)
    gc.focus_set()

    create_obstacles()
    create_enemies()
    move_enemies()
    enemy_shoot()
    move_enemy_bullets()
    countdown(TIMER_SECS)
    game_loop()

    gw.mainloop()

# push code
# ════════════════════════════════════════════════════════════════
#  HELP SCREEN
# ════════════════════════════════════════════════════════════════
def show_help():
    root.withdraw()
    hw = tk.Toplevel(root)
    hw.title("Help")
    hw.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
    bg_img = Image.open("img/help-background.png").resize((WIN_WIDTH, WIN_HEIGHT))
    bg_tk  = ImageTk.PhotoImage(bg_img)
    hc = tk.Canvas(hw, width=WIN_WIDTH, height=WIN_HEIGHT)
    hc.pack()
    hc.create_image(0, 0, anchor="nw", image=bg_tk)
    hc.bg_tk = bg_tk

    # Controls info
    hc.create_text(WIN_WIDTH // 2, WIN_HEIGHT - 80,
                   text="← → Move    |    ↑ Jump    |    SPACE Shoot",
                   font=("Arial", 20), fill="white")

    def close_help():
        hw.destroy()
        root.deiconify()

    tk.Button(hw, text='Back', width=8, font=('Arial', 22),
              command=close_help, bg='#660000', fg="white").place(x=30, y=30)
    hw.focus_set()
    hw.mainloop()


def exit_program():
    sys.exit()


# ════════════════════════════════════════════════════════════════
#  MAIN MENU BUTTONS  (Start now goes to level select)
# ════════════════════════════════════════════════════════════════
btn_cfg = dict(width=14, font=('Arial', 26), bg='#660000', fg="white", border=6)

start_button = tk.Button(root, text='Start', command=show_level_select, **btn_cfg)
start_button.place(x=WIN_WIDTH // 2 - 140, y=WIN_HEIGHT // 2 - 60)

help_button = tk.Button(root, text='Help', command=show_help, **btn_cfg)
help_button.place(x=WIN_WIDTH // 2 - 140, y=WIN_HEIGHT // 2 + 30)

exit_button = tk.Button(root, text='Exit', command=exit_program, **btn_cfg)
exit_button.place(x=WIN_WIDTH // 2 - 140, y=WIN_HEIGHT // 2 + 120)

root.mainloop()