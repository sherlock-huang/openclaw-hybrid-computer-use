#!/usr/bin/env python3
"""Test hotkey function only"""
import time
from pynput import keyboard

print("=" * 60)
print("TEST Hotkey Only")
print("=" * 60)

print("\nThis test will:")
print("1. Listen for Ctrl+R")
print("2. Show red indicator when triggered")
print("3. Exit after 10 seconds or when triggered twice")
print("\nPress Ctrl+R to start/stop recording simulation")
print("=" * 60)

recording = False
trigger_count = 0

def on_hotkey():
    global recording, trigger_count
    trigger_count += 1
    recording = not recording
    
    if recording:
        print(f"\n[{trigger_count}] START RECORDING (Red indicator should show)")
    else:
        print(f"\n[{trigger_count}] STOP RECORDING")
    
    if trigger_count >= 4:  # Start + Stop twice
        print("\nTriggered twice, exiting...")
        return False  # Stop listener

# Setup hotkey
hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+r'),
    on_hotkey
)

def on_press(key):
    hotkey.press(key)

def on_release(key):
    hotkey.release(key)

print("\nStarting listener...")
print("Waiting for Ctrl+R...")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join(timeout=10)  # Wait max 10 seconds

print("\n" + "=" * 60)
if trigger_count == 0:
    print("RESULT: No hotkey detected!")
    print("\nPossible solutions:")
    print("1. Run PowerShell as Administrator")
    print("2. Try a different hotkey combination")
    print("3. Check if Ctrl+R is used by other software")
else:
    print(f"RESULT: Hotkey worked! Triggered {trigger_count} times")
    print("\nThe recording function should work!")
print("=" * 60)
