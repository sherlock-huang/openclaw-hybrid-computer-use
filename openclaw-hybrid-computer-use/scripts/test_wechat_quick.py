#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信发送消息快速测试脚本

使用方法:
    python test_wechat_quick.py                    # 快速功能检查
    python test_wechat_quick.py --send             # 发送测试消息
    python test_wechat_quick.py --contact 张三     # 发送给指定联系人
"""

import sys
import os
import time
import traceback

# 设置 stdout 编码为 utf-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 50)
print("微信发送消息功能测试")
print("=" * 50)
print(f"Python: {sys.version}")
print(f"平台: {sys.platform}")

# 导入依赖
print("\n[1/4] 检查依赖...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.utils.wechat_helper import WeChatHelper, WIN32_AVAILABLE
    print("✅ 依赖导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    traceback.print_exc()
    print("\n请确保已安装依赖:")
    print("  pip install pywin32")
    input("\n按回车键退出...")
    sys.exit(1)

# 检查操作系统
print("\n[2/4] 检查系统...")
if sys.platform != "win32":
    print("❌ 此功能仅支持 Windows 系统")
    input("\n按回车键退出...")
    sys.exit(1)
print("✅ Windows 系统")

# 检查 win32gui
if not WIN32_AVAILABLE:
    print("❌ 缺少 win32gui 模块")
    print("请运行: pip install pywin32")
    input("\n按回车键退出...")
    sys.exit(1)
print("✅ win32gui 模块可用")

# 检查微信窗口
print("\n[3/4] 检查微信窗口...")
try:
    helper = WeChatHelper()
    handle = helper.find_wechat_window()
    
    if handle:
        print(f"✅ 找到微信窗口 (句柄: {handle})")
    else:
        print("❌ 未找到微信窗口")
        print("请确保:")
        print("  1. 微信桌面版已安装")
        print("  2. 微信已登录")
        print("  3. 微信窗口已打开（可以最小化）")
        input("\n按回车键退出...")
        sys.exit(1)
except Exception as e:
    print(f"❌ 检查失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

# 解析命令行参数
print("\n[4/4] 解析参数...")
import argparse

parser = argparse.ArgumentParser(description="微信发送消息测试")
parser.add_argument('--send', '-s', action='store_true', help='发送消息')
parser.add_argument('--contact', '-c', default='文件传输助手', help='联系人')
parser.add_argument('--message', '-m', default='Hello from OpenClaw! [测试消息]', help='消息内容')
parser.add_argument('--full', '-f', action='store_true', help='完整测试')

args = parser.parse_args()

print(f"   联系人: {args.contact}")
print(f"   消息: {args.message}")

# 执行发送
if args.send or args.full:
    print("\n" + "=" * 50)
    print("准备发送消息")
    print("=" * 50)
    
    confirm = input(f"\n发送给 {args.contact}: {args.message}\n\n确认? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print("\n发送中...")
        try:
            success = helper.send_message_to_contact(args.contact, args.message)
            if success:
                print("✅ 消息发送成功！请检查微信")
            else:
                print("❌ 消息发送失败")
        except Exception as e:
            print(f"❌ 发送异常: {e}")
            traceback.print_exc()
    else:
        print("已取消")
else:
    print("\n" + "=" * 50)
    print("✅ 前置检查通过！")
    print("=" * 50)
    print("\n使用 --send 参数发送消息:")
    print(f'  python test_wechat_quick.py --send -c "{args.contact}" -m "{args.message}"')

print("\n按回车键退出...")
input()
