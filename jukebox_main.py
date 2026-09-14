import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import vlc
import pygame
import threading
import time
import json
from gpiozero import Button, PWMLED

# -----------------------------
# CONFIG
# -----------------------------
VIDEO_DIR     = "/media/jukebox/JUKEBOX/videos"
VALID_LETTERS = set("ABCDEFGHJKLMNQRSTUV")
VALID_NUMBERS = set("0123456789")
BEAM_PIN      = 18
LED_PIN       = 12  # PWM signal to the Gravity MOSFET module (GPIO18 and GPIO3 are already in use)
IDLE_BRIGHTNESS = 0.5
FULL_BRIGHTNESS = 1.0
FADE_DURATION = 3
FADE_STEPS    = 100
WINDOW_WIDTH  = 640
WINDOW_HEIGHT = 480
TOKEN_IMAGE   = "/media/jukebox/JUKEBOX/insert_token.png"
IDLE_IMAGE    = "/media/jukebox/JUKEBOX/make_selection.png"
STATE_FILE    = "/tmp/jukebox_state.json"
# -----------------------------

current_letter  = None
player          = None
fade_lock       = threading.Lock()
show_token_flag = threading.Event()
show_idle_flag  = threading.Event()

STATE_TOKEN   = "token"
STATE_IDLE    = "idle"
STATE_PLAYING = "playing"
state         = STATE_TOKEN

vlc_instance = vlc.Instance("--quiet", "--codec=avcodec,none", "--mouse-hide-timeout=0")
beam_sensor  = Button(BEAM_PIN, pull_up=True)
led_strip    = PWMLED(LED_PIN)

def flicker_then_brighten():
    """Quick flicker effect, then settle at full brightness."""
    def _run():
        flicker_pattern = [0.5, 0.9, 0.3, 1.0, 0.4, 0.85, 0.55, 1.0]
        for level in flicker_pattern:
            led_strip.value = level
            time.sleep(0.06)
        led_strip.value = FULL_BRIGHTNESS

    threading.Thread(target=_run, daemon=True).start()

def write_state(s, filename="", fade=1.0):
    """Write current state to shared file (kept for future dev/debug use)."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({"state": s, "file": filename, "fade": fade}, f)
    except Exception as e:
        print(f"State write error: {e}")

# -----------------------------
# PYGAME SETUP
# -----------------------------
pygame.init()
pygame.mouse.set_visible(False)

# If both screens are connected, the small screen is the second display (index 1).
# If only the small screen is plugged in, it becomes the only display (index 0).
num_displays = pygame.display.get_num_displays()
display_index = 1 if num_displays > 1 else 0

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.NOFRAME, display=display_index)
pygame.display.set_caption("AfterDark Jukebox")
wm_info = pygame.display.get_wm_info()

def load_surface(path, w, h):
    if os.path.exists(path):
        return pygame.transform.scale(pygame.image.load(path), (w, h))
    surf = pygame.Surface((w, h))
    surf.fill((0, 0, 0))
    return surf

token_surface = load_surface(TOKEN_IMAGE, WINDOW_WIDTH, WINDOW_HEIGHT)
idle_surface  = load_surface(IDLE_IMAGE,  WINDOW_WIDTH, WINDOW_HEIGHT)

def show_token():
    screen.blit(token_surface, (0, 0))
    pygame.display.flip()
    write_state(STATE_TOKEN)
    led_strip.value = IDLE_BRIGHTNESS

def show_idle():
    screen.blit(idle_surface, (0, 0))
    pygame.display.flip()
    write_state(STATE_IDLE)

pygame.mouse.set_visible(False)
pygame.event.pump()
show_token()
pygame.display.flip()

# -----------------------------
# FADE HELPER
# -----------------------------
def _set_video_level(p, frac):
    if p:
        p.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, frac)
        p.video_set_adjust_float(vlc.VideoAdjustOption.Contrast,   frac)
        p.video_set_adjust_float(vlc.VideoAdjustOption.Saturation, frac)
        p.audio_set_volume(int(frac * 100))

# -----------------------------
# FADE
# -----------------------------
def _fade(p, direction="out", block=False):
    def _run():
        with fade_lock:
            if not p:
                return
            delay = FADE_DURATION / FADE_STEPS
            rng = range(FADE_STEPS, -1, -1) if direction == "out" else range(FADE_STEPS + 1)
            for i in rng:
                frac = i / FADE_STEPS
                if not p.is_playing() and direction == "out":
                    break
                _set_video_level(p, frac)
                write_state(STATE_PLAYING, fade=frac)
                time.sleep(delay)
            if direction == "out":
                p.stop()
                show_idle_flag.set()
                print("Fade out complete, video stopped.")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    if block:
        t.join()

# -----------------------------
# VIDEO CONTROL
# -----------------------------
def play_video(filename):
    global player, state

    path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {filename}")
        return

    if player and player.is_playing():
        print("Video already playing, selection ignored.")
        return

    print(f"Playing: {filename}")
    state = STATE_PLAYING
    write_state(STATE_PLAYING, filename)

    media  = vlc_instance.media_new(path)
    player = vlc_instance.media_player_new()
    player.set_media(media)
    player.set_xwindow(wm_info["window"])
    player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)
    _set_video_level(player, 1.0)
    player.play()

def stop_video():
    global player, state
    if player:
        player.stop()
        player = None
    state = STATE_TOKEN
    show_token()

# -----------------------------
# IR BEAM
# -----------------------------
def on_beam_broken():
    global state
    if state == STATE_PLAYING:
        p = player
        threading.Thread(target=_fade, kwargs={"p": p, "direction": "out"}, daemon=True).start()
    elif state == STATE_TOKEN:
        state = STATE_IDLE
        show_idle_flag.set()
        flicker_then_brighten()
        print("Token inserted, showing selection screen.")
    else:
        print("Already on selection screen.")

beam_sensor.when_pressed = on_beam_broken

# -----------------------------
# MAIN LOOP
# -----------------------------
print("Waiting for token insertion...")
print("Press ESC to quit")

running = True
while running:
    pygame.mouse.set_visible(False)

    if show_idle_flag.is_set():
        show_idle()
        show_idle_flag.clear()
        state = STATE_IDLE

    if show_token_flag.is_set():
        show_token()
        show_token_flag.clear()
        state = STATE_TOKEN

    if player and player.get_state() == vlc.State.Ended:
        player.stop()
        player = None
        state = STATE_TOKEN
        show_token()
        print("Video ended, waiting for token.")

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            stop_video()
            break
        elif event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key).upper()
            if key_name == "ESCAPE":
                running = False
                stop_video()
                break
            if state == STATE_IDLE:
                if key_name in VALID_LETTERS:
                    current_letter = key_name
                    print(f"Letter selected: {current_letter}")
                elif key_name in VALID_NUMBERS and current_letter:
                    filename = f"{current_letter}{key_name}.mp4"
                    threading.Thread(target=play_video, args=(filename,), daemon=True).start()
                    current_letter = None

    time.sleep(0.1)

led_strip.off()
pygame.quit()
