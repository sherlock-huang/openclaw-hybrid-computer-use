#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息 - 最简单版本
使用键盘快捷键操作，不依赖坐标
"""

import sys
import time

print("="*60)
print("微信发送消息 (快捷键版本)")
print("="*60)

contact = sys.argv[1] if len(sys.argv) > 1 else "文件传输助手"
message = sys.argv[2] if len(sys.argv) > 2 else "Hello"

print(f"\n联系人: {contact}")
print(f"消息: {message}")

try:
    import win32gui
    import win32con
    import win32api
except ImportError:
    print("\n请先安装 pywin32:")
    print("  py -m pip install pywin32")
    input("按回车退出...")
    sys.exit(1)

# 查找并激活微信
print("\n查找微信窗口...")
wechat_hwnd = None

def callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            return False
    return True

win32gui.EnumWindows(callback, None)

if not wechat_hwnd:
    print("未找到微信窗口")
    sys.exit(1)

print(f"找到微信窗口 (句柄: {wechat_hwnd})")

if win32gui.IsIconic(wechat_hwnd):
    win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(wechat_hwnd)
time.sleep(0.5)

# 使用 Ctrl+F 打开搜索
print("\n使用 Ctrl+F 打开搜索...")
win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl
win32api.keybd_event(0x46, 0, 0, 0)  # F
win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)
win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(0.5)

# 输入联系人
print(f"输入联系人: {contact}")
for char in contact:
    win32gui.PostMessage(wechat_hwnd, 0x0102, ord(char), 0)
    time.sleep(0.05)
time.sleep(0.5)

# 回车选择
print("按回车选择...")
win32api.keybd_event(0x0D, 0, 0, 0)
win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(1)

# 输入消息
print(f"输入消息: {message}")
for char in message:
    win32gui.PostMessage(wechat_hwnd, 0x0102, ord(char), 0)
    time.sleep(0.03)
time.sleep(0.3)

# 发送
print("发送...")
win32api.keybd_event(0x0D, 0, 0, 0)
win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)

print("\n[OK] 完成!")
input("\n按回车退出...")
