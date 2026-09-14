#!/usr/bin/env python3
"""
Standalone test for the LED brightness/flicker behaviour, isolated from
the rest of the jukebox app. Same GPIO pin and logic as jukebox_main.py,
so if it looks right here it'll look right in the real thing.

Wiring for a bare test LED (no MOSFET needed for this):
GPIO12 -> LED anode (long leg) -> LED cathode (short leg) -> 330ohm resistor -> GND
"""

from gpiozero import PWMLED
import time

LED_PIN = 12
IDLE_BRIGHTNESS = 0.5
FULL_BRIGHTNESS = 1.0

led_strip = PWMLED(LED_PIN)


def flicker_then_brighten():
    flicker_pattern = [0.5, 0.9, 0.3, 1.0, 0.4, 0.85, 0.55, 1.0]
    for level in flicker_pattern:
        led_strip.value = level
        time.sleep(0.06)
    led_strip.value = FULL_BRIGHTNESS


print("LED test running.")
print("Press Enter to simulate a token insertion (flicker -> full brightness).")
print("Press Ctrl+C to quit.")

led_strip.value = IDLE_BRIGHTNESS
print(f"LED at idle brightness ({IDLE_BRIGHTNESS}).")

try:
    while True:
        input()
        print("Token inserted - flickering...")
        flicker_then_brighten()
        print("At full brightness. Press Enter again to reset to idle.")
        input()
        led_strip.value = IDLE_BRIGHTNESS
        print(f"Back to idle brightness ({IDLE_BRIGHTNESS}). Press Enter to test again.")
except KeyboardInterrupt:
    pass
finally:
    led_strip.off()
    print("\nLED off. Test finished.")
