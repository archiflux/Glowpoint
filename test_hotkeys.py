#!/usr/bin/env python3
"""Test script to check if pynput hotkeys work on your system."""
import sys
from pynput import keyboard
import time

print("=" * 60)
print("Glowpoint Hotkey Test")
print("=" * 60)
print()
print("This script tests if pynput can detect hotkeys on your system.")
print("This is especially important when using remote desktop connections.")
print()
print("Test 1: Simple key press detection")
print("-" * 60)
print("Press any key (or Ctrl+C to skip to hotkey test)...")
print()

key_pressed = False

def on_press(key):
    global key_pressed
    key_pressed = True
    try:
        print(f"✓ Key detected: {key.char}")
    except AttributeError:
        print(f"✓ Special key detected: {key}")

def on_release(key):
    if key == keyboard.Key.esc:
        return False

# Test basic keyboard detection
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# Wait for a key press
timeout = 10
start = time.time()
while not key_pressed and (time.time() - start) < timeout:
    time.sleep(0.1)

listener.stop()

if key_pressed:
    print("\n✓ SUCCESS: Basic keyboard detection works!")
else:
    print("\n✗ FAILED: No keyboard input detected within 10 seconds")
    print("  This may indicate an issue with pynput on your system.")

print()
print("Test 2: Global hotkey detection")
print("-" * 60)
print("Testing hotkey: Ctrl+Shift+B")
print("Press Ctrl+Shift+B within 15 seconds...")
print()

hotkey_pressed = False

def on_hotkey():
    global hotkey_pressed
    hotkey_pressed = True
    print("✓ HOTKEY DETECTED: Ctrl+Shift+B pressed!")

# Test global hotkey
hotkey = keyboard.GlobalHotKeys({
    '<ctrl>+<shift>+b': on_hotkey
})
hotkey.start()

# Wait for hotkey
timeout = 15
start = time.time()
while not hotkey_pressed and (time.time() - start) < timeout:
    time.sleep(0.1)

hotkey.stop()

print()
print("=" * 60)
print("Test Results")
print("=" * 60)

if key_pressed and hotkey_pressed:
    print("✓ ALL TESTS PASSED")
    print("  pynput is working correctly on your system!")
    print("  Glowpoint hotkeys should work.")
elif key_pressed and not hotkey_pressed:
    print("⚠ PARTIAL FAILURE")
    print("  Basic keyboard detection works, but global hotkeys don't.")
    print()
    print("  Possible causes:")
    print("  1. Remote Desktop interference (very common)")
    print("  2. Insufficient permissions (try running as admin/sudo)")
    print("  3. Wayland desktop environment (use X11)")
    print("  4. Conflicting global hotkey software")
    print()
    print("  Solutions:")
    print("  - Try running Glowpoint directly on the local machine")
    print("  - Use a different remote desktop solution (RDP, VNC)")
    print("  - Try different hotkey combinations")
elif not key_pressed:
    print("✗ COMPLETE FAILURE")
    print("  pynput cannot detect keyboard input at all.")
    print()
    print("  Possible causes:")
    print("  1. pynput not installed correctly: pip install pynput")
    print("  2. Missing system dependencies")
    print("  3. Remote desktop blocking all keyboard input")
    print()
    print("  Solution:")
    print("  - Run Glowpoint directly on the local machine")
else:
    print("? UNKNOWN STATE")

print()
print("For Glowpoint to work over remote desktop:")
print("- RDP (Remote Desktop Protocol) usually works")
print("- VNC often works")
print("- Google Remote Desktop may have issues with global hotkeys")
print("- TeamViewer usually works")
print()
print("Press Enter to exit...")
input()
