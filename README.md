# AfterDark Jukebox

A token-operated video jukebox running on a Raspberry Pi 5. A beam sensor detects
when a token is inserted, the user selects a video by pressing a letter then a
number on a keyboard, and the video plays full screen. An LED strip dims and
brightens in sync with the state of the jukebox.

The app runs on a single small screen. A second, larger screen can stay
connected for development without the app appearing on it.

## Files

- `jukebox_main.py` - the main application. Handles the display, video
  playback, beam sensor, and LED strip.
- `run_jukebox.sh` - waits for the USB drive holding the videos, then starts
  the app. This is what runs automatically on boot.
- `setup.sh` - one-off setup script. Installs VLC, the Python environment,
  and the autostart entry.
- `requirements.txt` - Python packages needed by the app.
- `shutdown_button.py` - watches a GPIO pin for a held button press and
  triggers a clean shutdown.
- `jukebox-shutdown-button.service` - systemd service that runs
  `shutdown_button.py` at boot, as root, so no password is needed.
- `led_test.py` - standalone script for testing the LED brightness and
  flicker behaviour without running the full app.

## First-time setup

```bash
git clone git@github.com:michaelshorter/AfterDark_Final.git ~/AfterDark2_DualScreen_v2
cd ~/AfterDark2_DualScreen_v2
bash setup.sh
```

This installs everything needed and sets the app to start automatically
on boot, once desktop autologin is enabled
(`sudo raspi-config` -> System Options -> Boot / Auto Login -> Desktop
Autologin).

To install the shutdown button service:

```bash
sudo cp jukebox-shutdown-button.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jukebox-shutdown-button
```

## Changing the config variables

All the settings that are likely to need changing sit together at the top
of `jukebox_main.py`, under `# CONFIG`. Edit the value and restart the app
for it to take effect.

| Variable | What it does | Notes |
|---|---|---|
| `VIDEO_DIR` | Folder on the USB drive where video files live | Videos must be named `<letter><number>.mp4`, e.g. `A3.mp4`, matching a valid letter and number below |
| `VALID_LETTERS` | Letters the user can select | Add or remove letters here if you change how many rows of videos you have |
| `VALID_NUMBERS` | Numbers the user can select | Same idea, for columns |
| `BEAM_PIN` | GPIO pin the IR beam sensor is wired to | Currently GPIO18 |
| `LED_PIN` | GPIO pin sending the PWM signal to the LED strip's MOSFET module | Currently GPIO12. Don't reuse GPIO18 (beam sensor) or GPIO3 (shutdown button) |
| `IDLE_BRIGHTNESS` | LED brightness while waiting for a token, from 0.0 to 1.0 | Currently 0.5 (half brightness) |
| `FULL_BRIGHTNESS` | LED brightness once a token is inserted | Currently 1.0 (full) |
| `FADE_DURATION` | How long a video's picture and sound take to fade out, in seconds, when the beam is broken mid-playback | Currently 3 |
| `FADE_STEPS` | How many steps the fade is broken into | Higher is smoother but not usually worth changing |
| `WINDOW_WIDTH` / `WINDOW_HEIGHT` | Resolution of the screen the app displays on | Currently 640x480, matching the small screen. Change this if you fit a different screen |
| `TOKEN_IMAGE` | Image shown while waiting for a token | Full path on the USB drive |
| `IDLE_IMAGE` | Image shown once a token is inserted, before a video is chosen | Full path on the USB drive |
| `STATE_FILE` | Where the current state is written as JSON | Kept for future dev/debug use, safe to leave alone |

## The LED flicker effect

When a token is inserted, `flicker_then_brighten()` runs through a short
sequence of brightness levels before settling at `FULL_BRIGHTNESS`. The
pattern itself is a list near the top of the function:

```python
flicker_pattern = [0.5, 0.9, 0.3, 1.0, 0.4, 0.85, 0.55, 1.0]
```

Add, remove, or reorder numbers in that list to change the flicker feel.
Each step holds for 0.06 seconds, set in the `time.sleep(0.06)` line just
below it. Slow the whole effect down by raising that number, or speed it up
by lowering it.

To test changes to the flicker without running the full app, use
`led_test.py`:

```bash
python3 led_test.py
```

## Small screen only, large screen for development

The app auto-detects how many screens are connected at startup. With two
screens connected, it opens on the second one (the small screen). With only
the small screen connected, it opens on that one, since it's the only
option. This is handled near the top of the file, just after
`pygame.init()`, and shouldn't normally need changing.

## Powering on and off

Hold the shutdown button (wired to GPIO3) for 2 seconds to shut down
cleanly. Once the activity LED has stopped blinking, it's safe to cut power
at the wall or smart plug. Restoring power boots the Pi straight back up.
