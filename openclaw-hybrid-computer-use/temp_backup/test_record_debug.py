#!/usr/bin/env python3
"""Recording function debug script"""
import sys
import os
import time

print("=" * 60)
print("DEBUG Recording Function")
print("=" * 60)

# Check 1: Python path
print(f"\n[1/5] Python: {sys.executable}")
print(f"      Version: {sys.version[:20]}...")

# Check 2: Import pynput
try:
    from pynput import keyboard, mouse
    print("\n[2/5] OK pynput imported")
except Exception as e:
    print(f"\n[2/5] FAIL pynput import: {e}")
    sys.exit(1)

# Check 3: Import recording modules
try:
    sys.path.insert(0, 'src')
    from core.recorder import TaskRecorder
    from utils.shortcut_listener import ShortcutListener
    from utils.recording_overlay import RecordingOverlay
    print("\n[3/5] OK Recording modules imported")
except Exception as e:
    print(f"\n[3/5] FAIL Recording modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 4: Test shortcut listener
print("\n[4/5] Testing shortcut listener...")
print("      Press Ctrl+T to test (within 5 seconds)")

test_triggered = False

def test_callback():
    global test_triggered
    test_triggered = True
    print("      OK Shortcut triggered!")

listener = ShortcutListener(test_callback, "<ctrl>+t")
listener.start()

# Wait 5 seconds
for i in range(5):
    if test_triggered:
        break
    print(f"      Waiting... {5-i}s")
    time.sleep(1)

listener.stop()

if not test_triggered:
    print("      WARN No shortcut detected")
    print("      Possible reasons:")
    print("         - Did not press Ctrl+T")
    print("         - Need admin privileges")
    print("         - Shortcut occupied by other program")

# Check 5: Test recording overlay
print("\n[5/5] Testing recording overlay...")
print("      Will show red recording window for 3 seconds")

try:
    overlay = RecordingOverlay()
    overlay.show()
    print("      OK Recording overlay shown")
    time.sleep(3)
    overlay.hide()
    print("      OK Recording overlay closed")
except Exception as e:
    print(f"      FAIL Recording overlay: {e}")

print("\n" + "=" * 60)
print("Debug complete!")
print("=" * 60)

if test_triggered:
    print("\nOK Shortcut function works")
    print("\nNow run full recording:")
    print("  python -m src record")
else:
    print("\nWARN Shortcut not triggered, try:")
    print("  1. Run PowerShell as Administrator")
    print("  2. Change hotkey: python -m src record --hotkey '<ctrl>+<shift>+r>'")
    print("  3. Use CLI mode to start/stop recording")
