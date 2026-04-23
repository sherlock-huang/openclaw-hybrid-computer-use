#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息 - 简化版

用法:
    python wechat_send_simple.py "联系人" "消息"
    python wechat_send_simple.py "文件传输助手" "Hello"
"""

import sys
import time

if len(sys.argv) < 3:
    print("用法: python wechat_send_simple.py \"联系人\" \"消息\"")
    print("示例: python wechat_send_simple.py \"文件传输助手\" \"Hello\"")
    sys.exit(1)

contact = sys.argv[1]
message = sys.argv[2]

print(f"准备发送消息给: {contact}")
print(f"消息内容: {message}")

# 导入依赖
try:
    import win32gui
    import win32con
    import win32api
    print("✓ Windows API 已加载")
except ImportError:
    print("✗ 请先安装 pywin32: pip install pywin32")
    sys.exit(1)

# 查找微信窗口
print("\n1. 查找微信窗口...")
wechat_hwnd = None

def callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            print(f"   找到: {title} (句柄: {hwnd})")
            return False
    return True

win32gui.EnumWindows(callback, None)

if not wechat_hwnd:
    print("✗ 未找到微信窗口，请确保微信已打开")
    sys.exit(1)

# 激活窗口
print("\n2. 激活微信窗口...")
if win32gui.IsIconic(wechat_hwnd):
    win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(wechat_hwnd)
time.sleep(0.5)

# 获取窗口位置
rect = win32gui.GetWindowRect(wechat_hwnd)
print(f"   窗口位置: {rect}")

# 点击搜索框（相对坐标）
print(f"\n3. 点击搜索框...")
search_x = rect[0] + 140
search_y = rect[1] + 40
win32api.SetCursorPos((search_x, search_y))
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.3)

# 输入联系人
print(f"   输入: {contact}")
for char in contact:
    win32api.keybd_event(ord(char), 0, 0, 0)
    win32api.keybd_event(ord(char), 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
time.sleep(0.5)

# 回车选择
print("   按回车选择...")
win32api.keybd_event(0x0D, 0, 0, 0)  # Enter down
win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)  # Enter up
time.sleep(1)

# 点击输入框
print(f"\n4. 点击输入框...")
input_x = rect[0] + 600
input_y = rect[1] + 800
win32api.SetCursorPos((input_x, input_y))
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.3)

# 输入消息
print(f"   输入: {message}")
for char in message:
    if ord(char) < 128:
        win32api.keybd_event(ord(char), 0, 0, 0)
        win32api.keybd_event(ord(char), 0, win32con.KEYEVENTF_KEYUP, 0)
    else:
        # 中文需要其他方式输入，这里简化处理
        print(f"   (跳过中文: {char})")
    time.sleep(0.05)

# 发送
print("\n5. 发送消息...")
win32api.keybd_event(0x0D, 0, 0, 0)
win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(0.3)

print("\n✓ 消息发送完成！")
print("(如果消息未发送，请检查微信窗口是否被其他窗口遮挡)")
