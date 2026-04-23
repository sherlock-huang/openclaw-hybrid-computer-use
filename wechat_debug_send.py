#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送调试 - 带详细日志
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

try:
    import win32gui
    import win32con
    import pyautogui
except ImportError as e:
    print(f"Error: {e}")
    print("Install: py -m pip install pywin32 pyautogui")
    sys.exit(1)

# 查找微信
print("Step 1: Find WeChat window...")
wechat_hwnd = None

def callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            print(f"  Found: {title} (handle: {hwnd})")
            return False
    return True

win32gui.EnumWindows(callback, None)

if not wechat_hwnd:
    print("  Not found!")
    sys.exit(1)

# 激活
print("\nStep 2: Activate window...")
if win32gui.IsIconic(wechat_hwnd):
    win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(wechat_hwnd)
time.sleep(0.8)

# 获取窗口位置
rect = win32gui.GetWindowRect(wechat_hwnd)
width = rect[2] - rect[0]
height = rect[3] - rect[1]
print(f"  Window: {rect}, Size: {width}x{height}")

# 参数
contact = "文件传输助手"
message = "晚上好"

print(f"\nStep 3: Send to {contact}")

# 搜索联系人
print("\nStep 4: Open search (Ctrl+F)...")
pyautogui.keyDown('ctrl')
pyautogui.keyDown('f')
pyautogui.keyUp('f')
pyautogui.keyUp('ctrl')
time.sleep(0.5)

print("Step 5: Type contact name...")
pyautogui.hotkey('ctrl', 'a')
pyautogui.press('delete')
pyautogui.typewrite(contact, interval=0.01)
time.sleep(0.5)

print("Step 6: Press Enter to select...")
pyautogui.press('enter')
time.sleep(1.5)

# 点击输入框
print("\nStep 7: Click input box...")
input_x = rect[0] + width // 2
input_y = rect[1] + height - 120
print(f"  Click at: ({input_x}, {input_y})")
pyautogui.click(input_x, input_y)
time.sleep(0.3)

print("Step 8: Type message...")
print(f"  Message: {message}")
pyautogui.typewrite(message, interval=0.01)
time.sleep(0.3)

print("Step 9: Send...")
pyautogui.press('enter')
time.sleep(0.5)

print("\n" + "="*50)
print("Done! Check WeChat window.")
print("="*50)

input("\nPress Enter to exit...")
