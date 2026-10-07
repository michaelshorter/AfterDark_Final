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

## Building this on a new Pi from scratch

This is the full sequence, including everything that tripped us up the
first few times.

### 1. Flash the SD card

Use Raspberry Pi Imager:

- Device: Raspberry Pi 5
- OS: Raspberry Pi OS (64-bit), full desktop version (not Lite - VLC and
  the display need a desktop session)
- Advanced options (gear icon / Cmd+Shift+X before writing): set hostname
  to `jukebox`, username `jukebox`, a password you'll remember, configure
  Wi-Fi if needed, and enable SSH under Services

### 2. Boot it and set these three things before anything else

```bash
sudo raspi-config nonint do_boot_behaviour B4   # desktop autologin
sudo raspi-config nonint do_wayland W1           # switch to X11
sudo reboot
```

**Desktop autologin** is required or the autostart entry never fires.
**X11, not Wayland**, is required because the small-screen detection and
rotation both rely on `xrandr`, which Wayland doesn't support the same
way. Skipping this step is the most common reason the app doesn't appear
anywhere.

After rebooting, confirm:

```bash
echo $XDG_SESSION_TYPE
```

should print `x11`.

If a physical keyboard is attached and an on-screen keyboard keeps
popping up, disable it:

```bash
systemctl --user disable --now squeekboard
```

### 3. Clone the repo and run setup

```bash
git clone https://github.com/michaelshorter/AfterDark_Final.git ~/AfterDark2_DualScreen_v2
cd ~/AfterDark2_DualScreen_v2
bash setup.sh
```

This installs VLC, the Python virtual environment, and the autostart
entry. A `debconf`/`apt-listchanges` error partway through is harmless and
can be ignored - it's leftover noise from how `requirements.txt` was
originally generated, not a real dependency.

Afterwards, double check the autostart entry actually has the right path
(this has broken before after a fresh clone):

```bash
cat ~/.config/autostart/jukebox.desktop
```

The `Exec=` line should read
`/home/jukebox/AfterDark2_DualScreen_v2/run_jukebox.sh`. If it doesn't,
overwrite it directly:

```bash
cat > ~/.config/autostart/jukebox.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=AfterDark Jukebox
Exec=/home/jukebox/AfterDark2_DualScreen_v2/run_jukebox.sh
EOF
```

### 4. Install the shutdown button service

```bash
sudo cp jukebox-shutdown-button.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jukebox-shutdown-button
```

### A note on wooden tokens and the IR beam sensor

Thin wood (we used 2mm plywood) can be more transparent to the sensor's
infrared light than it looks to the eye, even held flat across the beam -
the receiver can still see enough IR passing through the wood grain to
read as "beam intact". A small spot of masking tape across the exact spot
where the beam crosses the token fixes this reliably. If tokens stop being
detected on a different wood type or thickness, this is the first thing
to check.

### 5. Wire up the hardware

- **Beam sensor** -> GPIO18 (physical pin 12). Double check against the
  physical pin, not just a count along a row - GPIO17 (pin 11) is an easy
  mix-up one pin over.
- **Shutdown button** -> GPIO3 (physical pin 5) and any GND pin. No
  resistor needed, GPIO3 has a built-in pull-up. Note: on the Pi 5 this
  only handles clean shutdown, not wake-from-off - GPIO3's wake feature
  from earlier Pi models doesn't work on the Pi 5. Powering back on just
  needs mains power restored (via a switch or smart plug), since the Pi 5
  always cold-boots when it senses power.
- **LED strip** -> via the MOSFET module's signal pin on GPIO12, VIN from
  a separate 5V/12V supply (matching your strip), GND shared with the Pi.
  The MOSFET module's own VCC pin isn't needed for basic switching on the
  Gravity-style module - signal and GND alone are enough.
- Give the LED strip's power supply its own mains socket if possible
  rather than sharing a strip with the Pi - a shared ground path between
  PWM switching and audio has caused an audible hum through the screen's
  HDMI audio before.

### 6. Verify GPIO pins aren't already claimed before testing

A stray test script left running in the background will block the real
app with a `GPIO busy` error. Before running `run_jukebox.sh`, check:

```bash
ps aux | grep python
```

Only `shutdown_button.py` should be running as its own service. Kill
anything else:

```bash
kill -9 <PID>
```

Always stop test scripts with **Ctrl+C**, not Ctrl+Z - Ctrl+Z suspends
the process rather than ending it, which leaves it holding the GPIO pin.

### 7. Test, then reboot to confirm autostart

```bash
cd ~/AfterDark2_DualScreen_v2
./run_jukebox.sh
```

Once that runs cleanly with the USB drive and screens connected, reboot
and confirm it starts itself with no manual commands:

```bash
sudo reboot
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
