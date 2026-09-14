#!/usr/bin/env python3
"""
Watches GPIO3 for a button press and triggers a clean shutdown.
GPIO3 also has built-in wake-on-ground support: grounding it while the
Pi is fully halted powers it back on, so the same button does both jobs.

Runs as a systemd service (as root), so no sudo/password needed.
"""

from gpiozero import Button
from signal import pause
import subprocess

# GPIO3 (physical pin 5) has an internal pull-up already fitted on the
# board for the wake feature, so no external resistor is needed.
button = Button(3, pull_up=True, hold_time=2)


def shutdown():
    subprocess.run(["/sbin/shutdown", "-h", "now"])


# hold_time=2 avoids an accidental brief knock or vibration triggering
# a shutdown; the button must be held for 2 seconds.
button.when_held = shutdown

pause()
