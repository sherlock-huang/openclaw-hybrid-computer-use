"""
ClawDesktop 基础使用示例

这个示例展示了如何使用 ComputerUseAgent 执行简单的桌面任务。
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_desktop import (
    ComputerUseAgent,
    Task,
    TaskSequence,
    ScreenCapture,
    ElementDetector,
)


def example_1_screen_capture():
    """示例1: 屏幕截图"""
    print("=" * 50)
    print("示例1: 屏幕截图")
    print("=" * 50)
    
    capture = ScreenCapture()
    
    # 截图
    print("正在截图...")
    image = capture.capture()
    print(f"截图成功: {image.shape}")
    
    # 保存截图
    capture.save(image, "output/screenshot.png")
    print("截图已保存到 output/screenshot.png")


def example_2_element_detection():
    """示例2: 元素检测"""
    print("\n" + "=" * 50)
    print("示例2: 元素检测")
    print("=" * 50)
    
    capture = ScreenCapture()
    detector = ElementDetector()
    
    # 截图
    print("正在截图...")
    image = capture.capture()
    
    # 检测元素
    print("正在检测元素...")
    elements = detector.detect(image)
    
    print(f"检测到 {len(elements)} 个元素:")
    for elem in elements[:5]:  # 只显示前5个
        print(f"  - {elem.id}: {elem.element_type.value} @ {elem.center}, 置信度={elem.confidence:.2f}")


def example_3_execute_task():
    """示例3: 执行任务序列"""
    print("\n" + "=" * 50)
    print("示例3: 执行任务序列")
    print("=" * 50)
    
    # 初始化 Agent
    agent = ComputerUseAgent()
    
    # 定义任务: 打开记事本并输入文字
    sequence = TaskSequence(
        name="打开记事本并输入",
        tasks=[
            Task("launch", target="notepad"),
            Task("wait", delay=1.5),
            Task("type", value="Hello from ClawDesktop!"),
        ]
    )
    
    print(f"执行任务: {sequence.name}")
    result = agent.execute(sequence)
    
    print(f"执行结果: {'成功' if result.success else '失败'}")
    print(f"耗时: {result.duration:.2f}秒")
    if result.error:
        print(f"错误: {result.error}")


def example_4_predefined_task():
    """示例4: 执行预定义任务"""
    print("\n" + "=" * 50)
    print("示例4: 执行预定义任务")
    print("=" * 50)
    
    agent = ComputerUseAgent()
    
    # 执行预定义的记事本任务
    print("执行预定义任务: notepad_type")
    result = agent.execute_task("notepad_type", text="这是预定义任务示例")
    
    print(f"执行结果: {'成功' if result.success else '失败'}")


if __name__ == "__main__":
    print("ClawDesktop 基础使用示例")
    print("=" * 50)
    
    try:
        # 运行示例 (根据需要取消注释)
        # example_1_screen_capture()
        # example_2_element_detection()
        # example_3_execute_task()
        # example_4_predefined_task()
        
        print("\n请根据需要取消注释相应的示例函数")
        print("注意: 运行控制示例时确保屏幕内容可以被操作")
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        import traceback
        traceback.print_exc()
