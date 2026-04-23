"""
微信发送消息功能测试

测试前请确保：
1. 微信桌面版已安装并登录
2. 微信窗口可见或最小化在任务栏
3. 有已保存聊天记录的联系人
"""

import unittest
import sys
import os
import time
import io
import ctypes

# Windows UTF-8 编码修复
if sys.platform == "win32":
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)
    kernel32.SetConsoleOutputCP(65001)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_helper import WeChatHelper, WIN32_AVAILABLE
from src.utils.wechat_smart_sender import send_wechat_message_safe, SafetyLevel
from src.core.tasks_predefined import create_wechat_send_message_task, PREDEFINED_TASKS
from src.core.models import TaskSequence


@unittest.skipUnless(WIN32_AVAILABLE, "需要 Windows 系统和 win32gui")
class TestWeChatHelper(unittest.TestCase):
    """测试 WeChatHelper 类"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        print("\n" + "="*50)
        print("微信发送消息功能测试")
        print("="*50)
        print("⚠️  请确保微信已登录且窗口可见")
        print("="*50 + "\n")
        
        # 给用户3秒时间准备
        print("3秒后开始测试...")
        time.sleep(3)
    
    def test_01_find_wechat_window(self):
        """测试查找微信窗口"""
        print("\n[Test] 查找微信窗口...")
        
        helper = WeChatHelper()
        handle = helper.find_wechat_window()
        
        if handle:
            print(f"✅ 找到微信窗口，句柄: {handle}")
            self.assertIsNotNone(helper.window_rect)
            print(f"   窗口位置: {helper.window_rect}")
        else:
            print("❌ 未找到微信窗口，请确保微信已打开")
            self.skipTest("微信窗口未找到")
    
    def test_02_activate_wechat(self):
        """测试激活微信窗口"""
        print("\n[Test] 激活微信窗口...")
        
        helper = WeChatHelper()
        
        # 先找到窗口
        if not helper.find_wechat_window():
            self.skipTest("微信窗口未找到")
        
        # 激活窗口
        success = helper.activate_wechat()
        
        if success:
            print("✅ 微信窗口已激活")
            # 等待用户看到效果
            time.sleep(1)
        else:
            print("❌ 激活失败")
            self.fail("无法激活微信窗口")
    
    def test_03_search_contact(self):
        """测试搜索联系人"""
        print("\n[Test] 搜索联系人...")
        print("提示: 请确保有一个已保存的联系人/群聊")
        
        helper = WeChatHelper()
        
        # 测试搜索（使用"文件传输助手"作为安全测试目标）
        test_contact = "文件传输助手"
        print(f"搜索: {test_contact}")
        
        success = helper.search_contact(test_contact)
        
        if success:
            print(f"✅ 搜索并选择成功")
            time.sleep(1)
        else:
            print("❌ 搜索失败")
            self.fail("无法搜索联系人")
    
    def test_04_send_message_interactive(self):
        """交互式测试：发送消息给指定联系人"""
        print("\n" + "="*50)
        print("[Test] 发送消息测试（交互式）")
        print("="*50)
        
        # 询问用户联系人
        contact = input("\n请输入联系人/群聊名称（如'文件传输助手'）: ").strip()
        if not contact:
            contact = "文件传输助手"
            print(f"使用默认: {contact}")
        
        message = input("请输入测试消息（默认: 'Hello from OpenClaw!'）: ").strip()
        if not message:
            message = "Hello from OpenClaw!"
        
        print(f"\n准备发送:")
        print(f"  联系人: {contact}")
        print(f"  消息: {message}")
        
        confirm = input("\n确认发送? (y/n): ").strip().lower()
        
        if confirm != 'y':
            self.skipTest("用户取消测试")
        
        # 执行发送
        helper = WeChatHelper()
        success = helper.send_message_to_contact(contact, message)
        
        if success:
            print("✅ 消息发送成功！请检查微信")
            self.assertTrue(True)
        else:
            print("❌ 消息发送失败")
            self.fail("发送消息失败")
    
    def test_05_task_creation(self):
        """测试任务创建"""
        print("\n[Test] 创建预置任务...")
        
        task = create_wechat_send_message_task(
            contact="测试联系人",
            message="测试消息"
        )
        
        self.assertIsInstance(task, TaskSequence)
        self.assertEqual(task.name, "wechat_send_测试联系人")
        self.assertEqual(len(task.tasks), 1)
        self.assertEqual(task.tasks[0].action, "wechat_send")
        self.assertEqual(task.tasks[0].target, "测试联系人")
        self.assertEqual(task.tasks[0].value, "测试消息")
        
        print("✅ 任务创建成功")
        print(f"   任务名: {task.name}")
        print(f"   动作: {task.tasks[0].action}")
    
    def test_06_task_registered(self):
        """测试任务已注册到预置任务"""
        print("\n[Test] 检查预置任务注册...")
        
        self.assertIn("wechat_send", PREDEFINED_TASKS)
        print("✅ wechat_send 已注册到 PREDEFINED_TASKS")
        
        # 获取任务函数
        func = PREDEFINED_TASKS["wechat_send"]
        self.assertTrue(callable(func))
        print("✅ 任务函数可调用")


class TestWeChatSmartSender(unittest.TestCase):
    """测试 WeChatSmartSender 作为推荐入口"""
    
    def test_safety_level_values(self):
        """测试安全等级枚举"""
        self.assertEqual(SafetyLevel.STRICT.value, "strict")
        self.assertEqual(SafetyLevel.NORMAL.value, "normal")
    
    def test_send_wechat_message_safe_returns_result(self):
        """测试快速函数返回 SendResult"""
        from unittest.mock import patch, MagicMock
        with patch("src.utils.wechat_smart_sender.WeChatSmartSender") as MockSender:
            instance = MockSender.return_value
            instance.send.return_value = MagicMock(
                success=True, error="ok", step_reached="done",
                warnings=[], screenshot_path=None,
                contact="文件传输助手", message="测试",
                safety_level="strict", dry_run=False
            )
            result = send_wechat_message_safe("文件传输助手", "测试", safety_level="strict", dry_run=False)
            self.assertTrue(result.success)
            self.assertEqual(result.contact, "文件传输助手")
            MockSender.assert_called_once_with(safety_level=SafetyLevel.STRICT)


class TestWeChatHelperWithoutWin32(unittest.TestCase):
    """测试非 Windows 环境下的行为"""
    
    def test_no_win32_error(self):
        """测试无 win32gui 时的错误处理"""
        if WIN32_AVAILABLE:
            self.skipTest("当前有 win32gui")
        
        helper = WeChatHelper()
        result = helper.find_wechat_window()
        
        self.assertIsNone(result)
        print("✅ 无 win32gui 时正确返回 None")


def run_quick_test():
    """快速测试 - 无需交互"""
    print("\n" + "="*50)
    print("快速功能测试")
    print("="*50)
    
    # 1. 测试任务创建
    print("\n1. 测试任务创建...")
    task = create_wechat_send_message_task(contact="测试", message="Hello")
    print(f"   ✅ 任务创建: {task.name}")
    print(f"   动作: {task.tasks[0].action}")
    print(f"   目标: {task.tasks[0].target}")
    print(f"   值: {task.tasks[0].value}")
    
    # 2. 测试任务注册
    print("\n2. 测试任务注册...")
    if "wechat_send" in PREDEFINED_TASKS:
        print("   ✅ wechat_send 已注册")
    else:
        print("   ❌ wechat_send 未注册")
    
    # 3. 测试 WeChatHelper 初始化
    print("\n3. 测试 WeChatHelper 初始化...")
    try:
        helper = WeChatHelper()
        print("   ✅ WeChatHelper 初始化成功")
        
        if WIN32_AVAILABLE:
            print("   win32gui: 可用")
        else:
            print("   win32gui: 不可用")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
    
    print("\n" + "="*50)
    print("快速测试完成")
    print("="*50)


def run_interactive_test():
    """交互式测试"""
    suite = unittest.TestSuite()
    suite.addTest(TestWeChatHelper('test_04_send_message_interactive'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="微信发送消息功能测试")
    parser.add_argument(
        '--mode', 
        choices=['auto', 'interactive', 'quick'],
        default='quick',
        help='测试模式: auto=自动测试, interactive=交互式测试, quick=快速检查'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'quick':
        run_quick_test()
    elif args.mode == 'interactive':
        run_interactive_test()
    else:
        # 运行所有测试
        unittest.main(verbosity=2)
