#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息 - 使用 pyautogui (更可靠)

需要先安装:
    py -m pip install pyautogui pywin32

用法:
    py wechat_pyautogui.py "联系人" "消息"
"""

import sys
import time

print("="*60)
print("微信发送消息 (pyautogui版本)")
print("="*60)

# 检查参数
contact = sys.argv[1] if len(sys.argv) > 1 else "文件传输助手"
message = sys.argv[2] if len(sys.argv) > 2 else "测试消息"

print(f"\n联系人: {contact}")
print(f"消息: {message}")

# 导入模块
print("\n导入模块...")
try:
    import win32gui
    import win32con
    import pyautogui
    pyautogui.FAILSAFE = True  # 鼠标移到角落终止
    pyautogui.PAUSE = 0.1
    print("  [OK] 模块导入成功")
except ImportError as e:
    print(f"  [ERROR] {e}")
    print("\n请安装依赖:")
    print("  py -m pip install pyautogui pywin32")
    input("按回车退出...")
    sys.exit(1)

# 查找微信
print("\n查找微信窗口...")
wechat_hwnd = None

def callback(hwnd, extra):
    global wechat_hwnd
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if "微信" in title or "WeChat" in title:
            wechat_hwnd = hwnd
            print(f"  [OK] 找到: {title}")
            return False
    return True

win32gui.EnumWindows(callback, None)

if not wechat_hwnd:
    print("  [ERROR] 未找到微信窗口")
    input("按回车退出...")
    sys.exit(1)

# 激活窗口
print("\n激活窗口...")
if win32gui.IsIconic(wechat_hwnd):
    win32gui.ShowWindow(wechat_hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(wechat_hwnd)
time.sleep(0.5)

# 获取窗口位置
rect = win32gui.GetWindowRect(wechat_hwnd)
print(f"  窗口位置: {rect}")

# 确认
confirm = input(f"\n发送给 {contact}: {message}? (y/n): ").strip().lower()
if confirm != 'y':
    print("取消")
    sys.exit(0)

print("\n开始发送...")

try:
    # 使用 pyautogui 操作
    
    # 1. 点击搜索框（相对窗口的固定位置）
    print("1. 点击搜索框...")
    search_x = rect[0] + 140
    search_y = rect[1] + 60
    pyautogui.click(search_x, search_y)
    time.sleep(0.3)
    
    # 2. 清空并输入联系人
    print("2. 输入联系人...")
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    pyautogui.typewrite(contact, interval=0.01)
    time.sleep(0.5)
    
    # 3. 回车选择
    print("3. 选择联系人...")
    pyautogui.press('enter')
    time.sleep(1.5)
    
    # 4. 点击输入框（窗口底部中间）
    print("4. 点击输入框...")
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    input_x = rect[0] + width // 2
    input_y = rect[1] + height - 120
    pyautogui.click(input_x, input_y)
    time.sleep(0.3)
    
    # 5. 输入消息
    print("5. 输入消息...")
    pyautogui.typewrite(message, interval=0.01)
    time.sleep(0.3)
    
    # 6. 发送
    print("6. 发送...")
    pyautogui.press('enter')
    time.sleep(0.5)
    
    print("\n[OK] 发送完成!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

input("\n按回车退出...")
