#!/usr/bin/env python3
"""
VLM 智能任务示例

使用前请设置环境变量:
    $env:OPENAI_API_KEY = "your-api-key"
"""

import sys
sys.path.insert(0, '..')

from src.vision import VisionTaskPlanner, VLMClient


def main():
    # 检查 API Key
    import os
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("错误: 请设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 环境变量")
        print("例如: $env:OPENAI_API_KEY = 'sk-...'")
        sys.exit(1)
    
    # 创建 VLM 客户端
    print("正在初始化 VLM 客户端...")
    vlm = VLMClient()  # 默认使用 OpenAI
    
    # 创建规划器
    planner = VisionTaskPlanner(vlm_client=vlm, max_steps=10)
    
    # 执行指令
    instruction = "在淘宝上搜索蓝牙耳机"
    print(f"\n执行指令: {instruction}")
    print("-" * 50)
    
    try:
        sequence = planner.execute_instruction(instruction)
        
        print("-" * 50)
        print(f"✅ 任务完成！")
        print(f"生成了 {len(sequence.tasks)} 个步骤")
        
        # 保存
        output_file = "vision_task.json"
        sequence.save_to_file(output_file)
        print(f"💾 已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
