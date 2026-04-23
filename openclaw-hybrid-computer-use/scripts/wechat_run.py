#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息 - 使用 py 运行
"""

import sys
import os
import time

# 修复编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*50)
print("微信发送消息测试")
print("="*50)

# 检查 win32
print("\n检查 pywin32...")
try:
    import win32gui
    import win32con
    import win32api
    print("[OK] pywin32 已安装")
except ImportError:
    print("[ERROR] 缺少 pywin32 模块")
    print("\n正在安装 pywin32...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] pywin32 安装成功，请重新运行脚本")
    else:
        print("[ERROR] 安装失败:")
        print(result.stderr)
    input("\n按回车退出...")
    sys.exit(1)

# 获取参数
contact = sys.argv[1] if len(sys.argv) > 1 else "文件传输助手"
message = sys.argv[2] if len(sys.argv) > 2 else "测试消息 from OpenClaw"

print(f"\n联系人: {contact}")
print(f"消息: {message}")

# 查找微信
print("\n查找微信窗口...")
wechat_hwnd = None

def callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            print(f"[OK] 找到窗口: {title}")
            return False
    return True

win32gui.EnumWindows(callback, None)

if not wechat_hwnd:
    print("[ERROR] 未找到微信窗口")
    print("请确保微信已登录并打开")
    input("\n按回车退出...")
    sys.exit(1)

# 确认
confirm = input(f"\n发送给 {contact}? (y/n): ").strip().lower()
if confirm != 'y':
    print("取消")
    sys.exit(0)

# 发送
print("\n发送中...")

try:
    # 激活
    if win32gui.IsIconic(wechat_hwnd):
        win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(wechat_hwnd)
    time.sleep(0.5)
    
    rect = win32gui.GetWindowRect(wechat_hwnd)
    
    # 搜索框
    win32api.SetCursorPos((rect[0] + 140, rect[1] + 40))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)
    
    # 输入联系人 (使用 SendMessage)
    edit_hwnd = win32gui.FindWindowEx(wechat_hwnd, 0, "Edit", None)
    if edit_hwnd:
        win32gui.SendMessage(edit_hwnd, 0x000C, 0, contact)  # WM_SETTEXT
    else:
        # 备用：直接发送键盘消息
        for c in contact:
            win32api.keybd_event(ord(c.upper()), 0, 0, 0) if c.isalpha() else None
    
    time.sleep(0.5)
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(1)
    
    # 输入消息
    win32api.SetCursorPos((rect[0] + 600, rect[1] + 800))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)
    
    # 发送消息
    for c in message:
        if ord(c) < 128:
            win32api.keybd_event(ord(c), 0, 0, 0)
            win32api.keybd_event(ord(c), 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.02)
    
    time.sleep(0.3)
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    
    print("\n[OK] 发送完成!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

input("\n按回车退出...")
