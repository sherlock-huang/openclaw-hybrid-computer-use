#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Safe Send - 终极安全发送入口

这是微信消息发送的**唯一推荐入口**。
采用 OCR 视觉验证 + 相似联系人冲突检测 + 发送前二次确认，
确保消息不会误发到其他人。

不支持录制模式，因为录制坐标无法验证聊天对象正确性。

Usage:
    # 严格模式发送（默认，最安全）
    py wechat_send.py "文件传输助手" "测试消息"

    # 仅测试验证流程，不真发送
    py wechat_send.py "文件传输助手" "测试消息" --dry-run

    # 标准模式（稍快但安全性略低）
    py wechat_send.py "文件传输助手" "测试消息" --safety-level normal

    # 跳过交互式确认（用于脚本自动化）
    py wechat_send.py "文件传输助手" "测试消息" --no-confirm
"""

import argparse
import sys

from src.utils.wechat_smart_sender import send_wechat_message_safe


def main():
    parser = argparse.ArgumentParser(
        description="微信安全发送工具 - 零误发保障",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
安全等级说明:
  strict (默认)
    - OCR 精确匹配联系人
    - 检测相似联系人冲突（如"张三" vs "张三-工作群"）
    - 发送前最终确认聊天对象
    - 发送后验证消息气泡
    - 敏感内容首次发送强制 dry-run
    - 窗口稳定性锁（发送中窗口被切换则停止）
    - 任何一步失败立即停止，绝不发送

  normal
    - OCR 精确选人 + 聊天对象验证 + 消息发送验证
    - 允许模糊匹配，不检测相似联系人冲突

交互式确认:
  默认情况下，按 Enter 前会要求你在命令行输入 y/n 确认。
  使用 --no-confirm 可跳过（仅推荐用于已知稳定的自动化脚本）。

示例:
  py wechat_send.py "文件传输助手" "Hello"
  py wechat_send.py "文件传输助手" "Hello" --dry-run
  py wechat_send.py "文件传输助手" "Hello" --no-confirm
        """
    )
    parser.add_argument("contact", help="联系人或群聊名称")
    parser.add_argument("message", help="要发送的消息内容")
    parser.add_argument(
        "--safety-level",
        choices=["strict", "normal"],
        default="strict",
        help="安全等级（默认 strict）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅执行验证流程，不实际发送消息"
    )
    confirm_group = parser.add_mutually_exclusive_group()
    confirm_group.add_argument(
        "--confirm",
        action="store_true",
        default=True,
        help="发送前要求用户确认（默认）"
    )
    confirm_group.add_argument(
        "--no-confirm",
        action="store_false",
        dest="confirm",
        help="跳过发送前用户确认（用于脚本自动化）"
    )
    
    args = parser.parse_args()
    
    result = send_wechat_message_safe(
        contact=args.contact,
        message=args.message,
        safety_level=args.safety_level,
        dry_run=args.dry_run,
        require_confirm=args.confirm
    )
    
    prefix = "[DRY-RUN] " if args.dry_run else ""
    
    if result.success:
        print(f"\n{prefix}✅ SUCCESS")
        print(f"   联系人: {result.contact}")
        print(f"   消息: {result.message}")
        print(f"   安全等级: {result.safety_level}")
        print(f"   最后步骤: {result.step_reached}")
        if result.warnings:
            print(f"   警告: {'; '.join(result.warnings)}")
        sys.exit(0)
    else:
        print(f"\n{prefix}❌ FAILED")
        print(f"   错误: {result.error}")
        print(f"   最后步骤: {result.step_reached}")
        if result.screenshot_path:
            print(f"   调试图: {result.screenshot_path}")
        if result.warnings:
            print(f"   警告: {'; '.join(result.warnings)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
