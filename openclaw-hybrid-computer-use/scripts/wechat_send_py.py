#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息 - 使用 py 命令运行

用法:
    py wechat_send_py.py "联系人" "消息"
"""

import sys
import os
import time

print("="*50)
print("微信发送消息")
print("="*50)

# 检查参数
if len(sys.argv) < 3:
    print("\n用法: py wechat_send_py.py \"联系人\" \"消息\"")
    print("示例: py wechat_send_py.py \"文件传输助手\" \"Hello\"")
    print("\n使用默认测试参数...")
    contact = "文件传输助手"
    message = "测试消息 from OpenClaw"
else:
    contact = sys.argv[1]
    message = sys.argv[2]

print(f"\n联系人: {contact}")
print(f"消息: {message}")

# 导入 win32 模块
print("\n导入 Windows API...")
try:
    import win32gui
    import win32con
    import win32api
    print("✓ Windows API 加载成功")
except ImportError:
    print("✗ 缺少 pywin32")
    print("请运行: py -m pip install pywin32")
    input("\n按回车退出...")
    sys.exit(1)

# 查找微信窗口
print("\n查找微信窗口...")
wechat_hwnd = None

def find_callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            return False
    return True

win32gui.EnumWindows(find_callback, None)

if not wechat_hwnd:
    print("✗ 未找到微信窗口")
    print("请确保微信已登录并打开主窗口")
    input("\n按回车退出...")
    sys.exit(1)

print(f"✓ 找到微信窗口 (句柄: {wechat_hwnd})")

# 确认发送
confirm = input(f"\n发送给 {contact}: {message}\n确认? (y/n): ").strip().lower()
if confirm != 'y':
    print("已取消")
    sys.exit(0)

# 发送消息
print("\n开始发送...")

try:
    # 1. 激活窗口
    print("1. 激活窗口...")
    if win32gui.IsIconic(wechat_hwnd):
        win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(wechat_hwnd)
    time.sleep(0.5)
    
    # 2. 获取窗口位置
    rect = win32gui.GetWindowRect(wechat_hwnd)
    print(f"   窗口位置: {rect}")
    
    # 3. 点击搜索框
    print("2. 点击搜索框...")
    search_x = rect[0] + 140
    search_y = rect[1] + 40
    win32api.SetCursorPos((search_x, search_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)
    
    # 4. 清空并输入联系人
    print(f"3. 输入: {contact}")
    win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl
    win32api.keybd_event(0x41, 0, 0, 0)  # A
    win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)
    
    # 使用 PostMessage 发送中文
    for char in contact:
        win32gui.PostMessage(wechat_hwnd, 0x0102, ord(char), 0)
        time.sleep(0.05)
    time.sleep(0.5)
    
    # 5. 回车选择
    print("4. 选择联系人...")
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(1)
    
    # 6. 点击输入框
    print("5. 点击输入框...")
    input_x = rect[0] + 600
    input_y = rect[1] + 800
    win32api.SetCursorPos((input_x, input_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)
    
    # 7. 输入消息
    print(f"6. 输入消息...")
    for char in message:
        win32gui.PostMessage(wechat_hwnd, 0x0102, ord(char), 0)
        time.sleep(0.05)
    time.sleep(0.3)
    
    # 8. 发送
    print("7. 发送...")
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.5)
    
    print("\n" + "="*50)
    print("✓ 消息发送完成！")
    print("="*50)
    
except Exception as e:
    print(f"\n✗ 发送失败: {e}")
    import traceback
    traceback.print_exc()

input("\n按回车退出...")
