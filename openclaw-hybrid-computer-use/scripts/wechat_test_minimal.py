#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# 设置编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*50)
print("微信功能最小化测试")
print("="*50)

# 步骤1: 检查 Python
print(f"\nPython: {sys.version_info.major}.{sys.version_info.minor}")
print(f"平台: {sys.platform}")

# 步骤2: 检查 win32gui
print("\n检查 win32gui...")
try:
    import win32gui
    import win32con
    print("✅ win32gui 可用")
except ImportError as e:
    print(f"❌ win32gui 不可用: {e}")
    print("\n请运行: pip install pywin32")
    input("按回车退出...")
    sys.exit(1)

# 步骤3: 查找微信窗口
print("\n查找微信窗口...")
wechat_hwnd = None

def enum_callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            print(f"  找到窗口: '{title}' (句柄: {hwnd})")
            return False
    return True

try:
    win32gui.EnumWindows(enum_callback, None)
except Exception as e:
    print(f"❌ 枚举窗口失败: {e}")
    input("按回车退出...")
    sys.exit(1)

if not wechat_hwnd:
    print("❌ 未找到微信窗口")
    print("请确保微信已登录并打开主窗口")
    input("按回车退出...")
    sys.exit(1)

print("\n" + "="*50)
print("✅ 测试通过！微信窗口已找到")
print("="*50)

# 询问是否发送测试消息
print("\n要发送测试消息吗？")
print("1. 发送给'文件传输助手'")
print("2. 输入自定义联系人和消息")
print("3. 退出")

choice = input("\n选择 (1/2/3): ").strip()

if choice == "1":
    contact = "文件传输助手"
    message = "测试消息 from OpenClaw"
elif choice == "2":
    contact = input("联系人名称: ").strip()
    message = input("消息内容: ").strip()
else:
    print("再见！")
    sys.exit(0)

if not contact or not message:
    print("联系人和消息不能为空")
    sys.exit(1)

print(f"\n准备发送:")
print(f"  联系人: {contact}")
print(f"  消息: {message}")

confirm = input("\n确认? (y/n): ").strip().lower()
if confirm != 'y':
    print("已取消")
    sys.exit(0)

# 发送消息
print("\n发送中...")

try:
    import win32api
    import time
    
    # 激活窗口
    print("1. 激活窗口...")
    if win32gui.IsIconic(wechat_hwnd):
        win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(wechat_hwnd)
    time.sleep(0.5)
    
    # 获取窗口位置
    rect = win32gui.GetWindowRect(wechat_hwnd)
    print(f"   窗口位置: {rect}")
    
    # 点击搜索框
    print("2. 点击搜索框...")
    search_x = rect[0] + 140
    search_y = rect[1] + 40
    win32api.SetCursorPos((search_x, search_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)
    
    # 输入联系人
    print(f"3. 输入联系人: {contact}")
    
    # 先清空搜索框 (Ctrl+A, Delete)
    win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl
    win32api.keybd_event(0x41, 0, 0, 0)  # A
    win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)
    
    win32api.keybd_event(0x2E, 0, 0, 0)  # Delete
    win32api.keybd_event(0x2E, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)
    
    # 输入联系人名称
    for char in contact:
        # 使用 SendMessage 发送中文
        win32gui.SendMessage(wechat_hwnd, 0x0102, ord(char), 0)
        time.sleep(0.05)
    time.sleep(0.5)
    
    # 回车选择
    print("4. 选择联系人...")
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(1)
    
    # 点击输入框
    print("5. 点击输入框...")
    input_x = rect[0] + 600
    input_y = rect[1] + 800
    win32api.SetCursorPos((input_x, input_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)
    
    # 输入消息
    print(f"6. 输入消息...")
    for char in message:
        win32gui.SendMessage(wechat_hwnd, 0x0102, ord(char), 0)
        time.sleep(0.05)
    time.sleep(0.3)
    
    # 发送
    print("7. 发送...")
    win32api.keybd_event(0x0D, 0, 0, 0)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.5)
    
    print("\n✅ 消息发送完成！")
    print("请检查微信窗口确认消息是否已发送")
    
except Exception as e:
    print(f"\n❌ 发送失败: {e}")
    import traceback
    traceback.print_exc()

print("\n按回车退出...")
input()
