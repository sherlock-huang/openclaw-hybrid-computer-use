#!/usr/bin/env python3
"""
实际 VLM 测试 - 带详细输出
"""

import os
import sys
import time

# 设置 API Key
os.environ["KIMI_CODING_API_KEY"] = "sk-kimi-YKpr73Pj0ztqa35rNmnan8wA45wXmBCwvgg3CB7A07iertrbi3SOMIbSfwHy3JYw"

sys.path.insert(0, '.')

from src.vision import VLMClient, VisionTaskPlanner
from src.core.models import Task


def main():
    print("=" * 60)
    print("🧠 VLM 实际测试")
    print("=" * 60)
    
    # 创建 VLM 客户端
    print("\n1. 初始化 VLM 客户端...")
    vlm = VLMClient(provider='kimi-coding')
    print("   ✅ 客户端就绪")
    
    # 创建规划器（更多步骤）
    print("\n2. 创建任务规划器...")
    planner = VisionTaskPlanner(vlm_client=vlm, max_steps=10)
    print("   ✅ 规划器就绪")
    
    # 执行指令
    instruction = "Open browser and visit example.com"
    print(f"\n3. 执行指令: {instruction}")
    print("-" * 60)
    
    try:
        # 手动执行以观察过程
        print("\n🚀 启动浏览器...")
        planner._ensure_browser_running()
        print("   ✅ 浏览器已启动")
        
        # 等待页面加载
        time.sleep(3)
        
        # 访问 example.com
        print("\n🌐 访问 example.com...")
        planner.browser_handler.goto("https://example.com")
        print("   ✅ 页面加载完成")
        
        # 等待
        time.sleep(2)
        
        # 截图
        print("\n📸 截图...")
        planner.browser_handler.screenshot("vlm_test_example.png")
        print("   ✅ 截图已保存: vlm_test_example.png")
        
        # 使用 VLM 分析
        print("\n🧠 使用 VLM 分析页面...")
        screenshot = planner._capture_screenshot()
        print(f"   截图尺寸: {screenshot.shape}")
        
        result = vlm.analyze_screen(
            screenshot=screenshot,
            instruction="What do you see on this page? Describe the main elements.",
            history=[]
        )
        
        print("\n   📋 VLM 分析结果:")
        print(f"   - 观察: {result.get('observation', 'N/A')[:100]}...")
        print(f"   - 思考: {result.get('thought', 'N/A')[:100]}...")
        print(f"   - 建议操作: {result.get('action', 'N/A')}")
        
        # 关闭浏览器
        print("\n🔒 关闭浏览器...")
        planner.browser_controller.close()
        print("   ✅ 浏览器已关闭")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)
        print("\n生成的文件:")
        print("  - vlm_test_example.png")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
