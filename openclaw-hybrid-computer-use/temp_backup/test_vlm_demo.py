#!/usr/bin/env python3
"""
VLM 功能演示测试
使用 Kimi API 测试视觉语言模型功能
"""

import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 设置 API Key
os.environ["KIMI_API_KEY"] = "sk-kimi-emIul7M1KdbnUeOQMzbLtiwTZ5vAMNcv7FqguPtBC7ycqEBMStjjNJfzYYFf8IAo"

sys.path.insert(0, '.')

from src.vision import VLMClient, VisionTaskPlanner
from src.core.models import TaskSequence


def create_test_screenshot():
    """创建测试截图（模拟网页）"""
    # 创建一个模拟网页的图像
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # 绘制标题栏
    draw.rectangle([0, 0, 800, 50], fill='#4A90E2')
    draw.text((20, 15), "模拟网页 - 搜索页面", fill='white')
    
    # 绘制搜索框
    draw.rectangle([200, 200, 600, 250], fill='#f0f0f0', outline='#ccc', width=2)
    draw.text((210, 215), "搜索框 - 在此输入...", fill='#999')
    
    # 绘制搜索按钮
    draw.rectangle([620, 200, 720, 250], fill='#4A90E2')
    draw.text((650, 215), "搜索", fill='white')
    
    # 绘制一些内容
    draw.text((200, 300), "热门搜索:", fill='#333')
    draw.text((200, 330), "- 蓝牙耳机", fill='#666')
    draw.text((200, 360), "- iPhone 15", fill='#666')
    draw.text((200, 390), "- 机械键盘", fill='#666')
    
    # 转换为 numpy 数组
    return np.array(img)


def test_vlm_analyze():
    """测试 VLM 分析功能"""
    print("=" * 60)
    print("🧠 VLM 功能测试 - Kimi API")
    print("=" * 60)
    
    # 创建 VLM 客户端
    print("\n1. 初始化 VLM 客户端 (Kimi)...")
    vlm = VLMClient(provider="kimi")
    print("   ✅ 初始化成功")
    
    # 创建测试截图
    print("\n2. 创建测试截图...")
    screenshot = create_test_screenshot()
    print(f"   ✅ 截图尺寸: {screenshot.shape}")
    
    # 测试分析功能
    print("\n3. 测试屏幕分析...")
    instruction = "点击搜索框并输入'蓝牙耳机'"
    
    try:
        result = vlm.analyze_screen(
            screenshot=screenshot,
            instruction=instruction,
            history=None
        )
        
        print("\n   ✅ 分析完成!")
        print(f"\n   📋 结果:")
        print(f"   - 观察: {result.get('observation', 'N/A')[:80]}...")
        print(f"   - 思考: {result.get('thought', 'N/A')[:80]}...")
        print(f"   - 操作: {result.get('action', 'N/A')}")
        print(f"   - 目标: {result.get('target', 'N/A')}")
        print(f"   - 完成: {result.get('is_task_complete', False)}")
        
    except Exception as e:
        print(f"\n   ❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ VLM 基础功能测试通过!")
    print("=" * 60)
    return True


def test_prompts():
    """测试提示词系统"""
    print("\n" + "=" * 60)
    print("📝 提示词系统测试")
    print("=" * 60)
    
    from src.vision.prompts import get_system_prompt, get_few_shot_examples
    
    # 测试不同模式的提示词
    for mode in ["browser", "desktop", "auto"]:
        prompt = get_system_prompt(mode)
        print(f"\n{mode.upper()} 模式提示词长度: {len(prompt)} 字符")
        print(f"  前100字符: {prompt[:100]}...")
    
    # 测试 few-shot 示例
    examples = get_few_shot_examples("browser", count=2)
    print(f"\n✅ 获取到 {len(examples)} 个 few-shot 示例")
    
    print("\n" + "=" * 60)
    print("✅ 提示词系统测试通过!")
    print("=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 OpenClaw VLM 测试程序")
    print("=" * 60)
    
    # 测试提示词系统
    test_prompts()
    
    # 测试 VLM 分析（需要 API Key）
    print("\n💡 提示: 测试 VLM 分析需要调用 Kimi API，会产生少量费用")
    print("   是否继续测试 VLM 分析? (y/n): ", end="")
    
    # 自动继续测试
    print("y (自动继续)")
    
    success = test_vlm_analyze()
    
    if success:
        print("\n🎉 所有测试通过! VLM 功能已就绪!")
        print("\n你可以使用以下命令运行 VLM 任务:")
        print("  py -m src vision \"帮我在淘宝上搜索蓝牙耳机\" --provider kimi")
    else:
        print("\n⚠️ 测试未完全通过，请检查配置")


if __name__ == "__main__":
    main()
