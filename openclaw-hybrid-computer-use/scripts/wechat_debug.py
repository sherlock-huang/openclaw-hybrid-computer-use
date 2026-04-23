#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息 - 调试版本
"""

import sys
import os
import time
import traceback

# 修复编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*60)
print("微信发送消息 - 调试模式")
print("="*60)

# 导入模块
print("\n[1] 导入模块...")
try:
    import win32gui
    import win32con
    import win32api
    print("  [OK] Windows API")
except ImportError as e:
    print(f"  [ERROR] {e}")
    input("按回车退出...")
    sys.exit(1)

# 查找微信
print("\n[2] 查找微信窗口...")
wechat_hwnd = None

def enum_callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            print(f"  [OK] 找到: {title} (句柄: {hwnd})")
            return False
    return True

win32gui.EnumWindows(enum_callback, None)

if not wechat_hwnd:
    print("  [ERROR] 未找到微信窗口")
    input("按回车退出...")
    sys.exit(1)

# 获取窗口信息
print("\n[3] 窗口信息...")
rect = win32gui.GetWindowRect(wechat_hwnd)
width = rect[2] - rect[0]
height = rect[3] - rect[1]
print(f"  位置: ({rect[0]}, {rect[1]}) - ({rect[2]}, {rect[3]})")
print(f"  大小: {width} x {height}")

contact = "文件传输助手"
message = "测试消息123"

print(f"\n[4] 准备发送")
print(f"  联系人: {contact}")
print(f"  消息: {message}")

confirm = input("\n开始发送? (y/n): ").strip().lower()
if confirm != 'y':
    print("取消")
    sys.exit(0)

print("\n" + "="*60)
print("开始执行")
print("="*60)

try:
    # 1. 激活窗口
    print("\n[步骤1] 激活窗口...")
    if win32gui.IsIconic(wechat_hwnd):
        win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(wechat_hwnd)
    print("  窗口已激活")
    time.sleep(0.8)
    
    # 2. 点击搜索框
    print("\n[步骤2] 点击搜索框...")
    search_x = rect[0] + 150
    search_y = rect[1] + 40
    print(f"  点击坐标: ({search_x}, {search_y})")
    win32api.SetCursorPos((search_x, search_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    
    # 3. 全选删除
    print("\n[步骤3] 清空搜索框...")
    win32api.keybd_event(0x11, 0, 0, 0)
    win32api.keybd_event(0x41, 0, 0, 0)
    win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)
    win32api.keybd_event(0x2E, 0, 0, 0)
    win32api.keybd_event(0x2E, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)
    
    # 4. 输入联系人
    print(f"\n[步骤4] 输入联系人: {contact}")
    for char in contact:
        win32gui.PostMessage(wechat_hwnd, 0x0102, ord(char), 0)
        time.sleep(0.05)
    print("  输入完成")
    time.sleep(0.8)
    
    # 5. 回车选择
    print("\n[步骤5] 按回车选择...")
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(1.5)
    
    # 6. 点击输入框
    print("\n[步骤6] 点击消息输入框...")
    input_x = rect[0] + int(width * 0.6)
    input_y = rect[1] + height - 100
    print(f"  点击坐标: ({input_x}, {input_y})")
    win32api.SetCursorPos((input_x, input_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    
    # 7. 输入消息
    print(f"\n[步骤7] 输入消息: {message}")
    for char in message:
        if ord(char) < 128:
            win32api.keybd_event(ord(char), 0, 0, 0)
            win32api.keybd_event(ord(char), 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            win32gui.PostMessage(wechat_hwnd, 0x0102, ord(char), 0)
        time.sleep(0.03)
    print("  输入完成")
    time.sleep(0.5)
    
    # 8. 发送
    print("\n[步骤8] 按回车发送...")
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.5)
    
    print("\n" + "="*60)
    print("[OK] 执行完成!")
    print("="*60)
    print("\n请检查微信窗口，看消息是否已发送")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    traceback.print_exc()

input("\n按回车退出...")
