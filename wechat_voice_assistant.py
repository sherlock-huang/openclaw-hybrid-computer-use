#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Voice Assistant - 自然语言安全发送入口

这是微信自然语言控制的**唯一推荐入口**。
采用 OCR 视觉验证 + 相似联系人冲突检测 + 发送前二次确认，
确保消息不会误发到其他人。

不支持录制模式。

Usage:
    py wechat_voice_assistant.py "给张三发消息说晚上好"
    py wechat_voice_assistant.py "给文件传输助手发测试" --dry-run
    py wechat_voice_assistant.py "给张三发消息说晚上好" --no-confirm
"""

import argparse
import sys

from src.vision.wechat_processor import WeChatNaturalLanguageProcessor
from src.utils.wechat_smart_sender import send_wechat_message_safe


def main():
    parser = argparse.ArgumentParser(
        description="微信语音助手 - 自然语言安全发送",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
交互式确认说明:
  默认情况下，自然语言解析后会展示联系人+消息摘要，要求你输入 y/n 确认。
  如果解析置信度 < 0.8，无论是否设置 --no-confirm 都会强制要求确认。

示例:
  py wechat_voice_assistant.py "给张三发消息说晚上好"
  py wechat_voice_assistant.py "告诉李四明天开会"
  py wechat_voice_assistant.py "通知技术群上线发布了" --dry-run
        """
    )
    parser.add_argument("text", nargs="+", help="自然语言指令")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅执行验证流程，不实际发送消息"
    )
    parser.add_argument(
        "--safety-level",
        choices=["strict", "normal"],
        default="strict",
        help="安全等级（默认 strict）"
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
        help="跳过发送前用户确认（低置信度时仍会被强制要求）"
    )
    
    args = parser.parse_args()
    user_input = " ".join(args.text)
    
    # 解析自然语言
    processor = WeChatNaturalLanguageProcessor()
    parsed = processor.parse(user_input)
    
    if not parsed:
        print("\n❌ 解析失败")
        print("   请使用标准格式，例如：")
        print('   "给张三发消息说晚上好"')
        print('   "告诉李四明天开会"')
        sys.exit(1)
    
    print(f"\n📝 解析结果")
    print(f"   联系人: {parsed.contact}")
    print(f"   消息: {parsed.message}")
    print(f"   置信度: {parsed.confidence}")
    
    # 低置信度强制确认
    force_confirm = parsed.confidence < 0.8
    if force_confirm and not args.confirm:
        print("\n⚠️  解析置信度较低，已强制开启发送前确认")
    
    require_confirm = args.confirm or force_confirm
    confirm_summary = f"自然语言指令: {user_input}"
    
    result = send_wechat_message_safe(
        contact=parsed.contact,
        message=parsed.message,
        safety_level=args.safety_level,
        dry_run=args.dry_run,
        require_confirm=require_confirm,
        confirm_summary=confirm_summary
    )
    
    prefix = "[DRY-RUN] " if args.dry_run else ""
    
    if result.success:
        print(f"\n{prefix}✅ 发送成功")
        print(f"   联系人: {result.contact}")
        print(f"   消息: {result.message}")
        if result.warnings:
            print(f"   警告: {'; '.join(result.warnings)}")
        sys.exit(0)
    else:
        print(f"\n{prefix}❌ 发送失败")
        print(f"   错误: {result.error}")
        if result.screenshot_path:
            print(f"   调试图: {result.screenshot_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
