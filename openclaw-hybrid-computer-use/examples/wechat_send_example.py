#!/usr/bin/env python3
"""
微信发送消息示例

演示如何使用 OpenClaw 自动化微信桌面版发送消息。

使用前请确保：
1. 微信桌面版已安装并登录
2. 微信窗口未被最小化
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_helper import WeChatHelper
from claw_desktop import ComputerUseAgent


def example_1_basic_usage():
    """示例1: 基础用法 - 直接调用 WeChatHelper"""
    print("=" * 50)
    print("示例1: 使用 WeChatHelper 发送消息")
    print("=" * 50)
    
    helper = WeChatHelper()
    
    # 发送消息给指定联系人
    contact = "张三"  # 替换为实际联系人名称
    message = "Hello, this is a test message from OpenClaw!"
    
    print(f"准备发送消息给: {contact}")
    print(f"消息内容: {message}")
    
    success = helper.send_message_to_contact(contact, message)
    
    if success:
        print("✅ 消息发送成功！")
    else:
        print("❌ 消息发送失败，请检查微信是否已登录")


def example_2_predefined_task():
    """示例2: 使用预置任务"""
    print("\n" + "=" * 50)
    print("示例2: 使用预置任务发送消息")
    print("=" * 50)
    
    agent = ComputerUseAgent()
    
    # 使用预置任务
    result = agent.execute_task(
        "wechat_send",
        contact="工作群",
        message="大家好，这是一条自动化测试消息"
    )
    
    print(f"执行结果: {'成功' if result.success else '失败'}")
    print(f"耗时: {result.duration:.2f}秒")


def example_3_batch_send():
    """示例3: 批量发送消息"""
    print("\n" + "=" * 50)
    print("示例3: 批量发送消息")
    print("=" * 50)
    
    helper = WeChatHelper()
    
    # 定义要发送的消息列表
    messages = [
        ("张三", "早上好！今天的会议改到下午3点"),
        ("李四", "报告已提交，请查收"),
        ("工作群", "提醒大家下午有团队会议"),
    ]
    
    for contact, message in messages:
        print(f"\n发送给 {contact}: {message}")
        success = helper.send_message_to_contact(contact, message)
        
        if success:
            print("✅ 发送成功")
        else:
            print("❌ 发送失败")
        
        # 等待一段时间避免发送过快
        import time
        time.sleep(2)


def example_4_with_confirmation():
    """示例4: 带确认的发送"""
    print("\n" + "=" * 50)
    print("示例4: 带确认的发送")
    print("=" * 50)
    
    contact = input("请输入联系人名称: ")
    message = input("请输入消息内容: ")
    
    print(f"\n准备发送:")
    print(f"  联系人: {contact}")
    print(f"  消息: {message}")
    
    confirm = input("\n确认发送? (y/n): ")
    
    if confirm.lower() == 'y':
        helper = WeChatHelper()
        success = helper.send_message_to_contact(contact, message)
        
        if success:
            print("✅ 消息已发送")
        else:
            print("❌ 发送失败")
    else:
        print("已取消发送")


def main():
    """主函数 - 选择示例运行"""
    print("""
    OpenClaw 微信自动化示例
    ======================
    
    选择要运行的示例:
    1. 基础用法 (WeChatHelper)
    2. 预置任务 (ComputerUseAgent)
    3. 批量发送
    4. 带确认的发送
    5. 退出
    """)
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    if choice == '1':
        example_1_basic_usage()
    elif choice == '2':
        example_2_predefined_task()
    elif choice == '3':
        example_3_batch_send()
    elif choice == '4':
        example_4_with_confirmation()
    elif choice == '5':
        print("再见！")
        sys.exit(0)
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
