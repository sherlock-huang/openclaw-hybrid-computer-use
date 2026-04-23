#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最简单的微信测试"""

import sys
import os

print("开始测试...")
print(f"Python: {sys.version_info}")
print(f"平台: {sys.platform}")

# 检查 win32gui
try:
    import win32gui
    print("✓ win32gui 可用")
except ImportError:
    print("✗ win32gui 不可用，请运行: pip install pywin32")
    sys.exit(1)

# 检查微信窗口
print("\n查找微信窗口...")

def find_wechat():
    wechat_titles = ["微信", "WeChat"]
    found = []
    
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            for keyword in wechat_titles:
                if keyword in title:
                    extra.append((hwnd, title))
        return True
    
    win32gui.EnumWindows(callback, found)
    return found

windows = find_wechat()

if windows:
    print(f"找到 {len(windows)} 个微信窗口:")
    for handle, title in windows:
        print(f"  句柄: {handle}, 标题: {title}")
else:
    print("未找到微信窗口，请确保微信已登录并打开")
    sys.exit(1)

print("\n✓ 测试通过！微信窗口已找到")
print("\n现在可以尝试发送消息:")
print('  python wechat_send_simple.py "文件传输助手" "Hello"')
