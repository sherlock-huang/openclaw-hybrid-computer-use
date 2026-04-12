"""CLI 入口"""

import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

from . import ComputerUseAgent, Task, TaskSequence
from .core.config import Config
from .perception.screen import ScreenCapture
from .perception.detector import ElementDetector
from .utils.image import draw_elements, save_debug_image


def cmd_detect(args):
    """检测屏幕元素命�?""
    print("正在检测屏幕元�?..")
    
    capture = ScreenCapture()
    detector = ElementDetector()
    
    image = capture.capture()
    elements = detector.detect(image)
    
    print(f"\n检测到 {len(elements)} 个元�?")
    for elem in elements:
        print(f"  [{elem.id}] {elem.element_type.value:8} @ ({elem.center[0]:4}, {elem.center[1]:4})  置信�?{elem.confidence:.2f}")
    
    if args.output:
        # 保存检测结�?
        output_data = {
            "count": len(elements),
            "elements": [e.to_dict() for e in elements]
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")
    
    if args.visualize:
        # 保存可视化图�?
        viz_path = Path(args.output).parent / "detection_visualization.png" if args.output else "detection_visualization.png"
        save_debug_image(image, viz_path, elements)
        print(f"可视化图像已保存�? {viz_path}")


def cmd_execute(args):
    """执行任务命令"""
    print(f"正在执行任务: {args.task_file}")
    
    # 加载任务文件
    with open(args.task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    
    # 解析任务
    tasks = [Task(**t) for t in task_data.get("tasks", [])]
    sequence = TaskSequence(
        name=task_data.get("name", "unnamed"),
        tasks=tasks,
        max_retries=task_data.get("max_retries", 3)
    )
    
    # 创建配置
    config = Config()
    if args.headless:
        config.browser_headless = True
        print("浏览器将以无头模式运�?)
    
    # 执行
    agent = ComputerUseAgent(config=config)
    result = agent.execute(sequence)
    
    print(f"\n执行结果: {'成功' if result.success else '失败'}")
    print(f"完成步骤: {result.completed_steps}/{len(tasks)}")
    print(f"耗时: {result.duration:.2f}�?)
    
    if result.error:
        print(f"错误: {result.error}")
    
    # 保存结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)


def cmd_run(args):
    """运行预定义任务命�?""
    print(f"运行预定义任�? {args.task_name}")
    
    agent = ComputerUseAgent()
    result = agent.execute_task(args.task_name, **args.params)
    
    print(f"\n执行结果: {'成功' if result.success else '失败'}")
    print(f"耗时: {result.duration:.2f}�?)
    
    if result.error:
        print(f"错误: {result.error}")


def cmd_browser_check(args):
    """检查浏览器安装状�?""
    try:
        from playwright.sync_api import sync_playwright
        
        print("检�?Playwright 浏览器安装状�?..")
        
        with sync_playwright() as p:
            for browser_type in ["chromium", "firefox", "webkit"]:
                try:
                    browser = getattr(p, browser_type).launch(headless=True)
                    browser.close()
                    print(f"  [OK] {browser_type}: 已安�?)
                except Exception as e:
                    print(f"  [FAIL] {browser_type}: 未安�?)
        
        print("\n安装浏览器命�?")
        print("  playwright install chromium")
        print("  playwright install firefox")
        print("  playwright install webkit")
        
    except ImportError:
        print("[FAIL] Playwright 未安�?)
        print("  运行: pip install playwright")


def cmd_vision(args):
    """VLM 智能模式命令"""
    from src.vision.task_planner import VisionTaskPlanner
    import time
    
    # 组合指令（支持多个单词）
    instruction = " ".join(args.instruction)
    
    print(f"🧠 VLM 智能模式")
    print(f"指令: {instruction}")
    print(f"提供�? {args.provider}")
    print("-" * 50)
    
    try:
        # 创建 VLM 客户�?
        from src.vision.llm_client import VLMClient
        vlm_client = VLMClient(provider=args.provider)
        
        # 创建规划�?
        planner = VisionTaskPlanner(
            vlm_client=vlm_client,
            max_steps=args.max_steps
        )
        
        # 执行指令
        sequence = planner.execute_instruction(
            instruction=instruction,
            start_browser=not args.no_browser
        )
        
        print("-" * 50)
        print(f"�?任务完成！共 {len(sequence.tasks)} �?)
        
        # 保存结果
        if args.output:
            sequence.save_to_file(args.output)
            print(f"💾 已保存到: {args.output}")
        
        # 显示任务摘要
        print("\n📋 执行步骤:")
        for i, task in enumerate(sequence.tasks[:10], 1):  # 最多显�?0�?
            target = task.target or task.value or ""
            print(f"  {i}. {task.action}: {target[:50]}")
        
        if len(sequence.tasks) > 10:
            print(f"  ... 还有 {len(sequence.tasks) - 10} �?)
        
    except Exception as e:
        print(f"�?执行失败: {e}")
        import traceback
        traceback.print_exc()


def cmd_record(args):
    """录制任务命令"""
    from .recording.hybrid_recorder import HybridRecorder
    from .core.models import RecordingMode
    import time
    
    # 解析模式
    mode_map = {
        "desktop": RecordingMode.DESKTOP,
        "browser": RecordingMode.BROWSER,
        "hybrid": RecordingMode.HYBRID,
    }
    mode = mode_map.get(args.mode, RecordingMode.HYBRID)
    
    # 创建录制�?
    recorder = HybridRecorder(mode=mode)
    
    try:
        recorder.start_recording()
        print(f"录制�?.. �?Ctrl+R 停止")
        
        # 等待停止
        while recorder.is_recording:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        if recorder.is_recording:
            session = recorder.stop_recording()
            
            # 保存文件
            output_path = args.output or f"recorded_{int(time.time())}.json"
            session.save_to_file(output_path)
            print(f"已保存到: {output_path}")


def main():
    """主入�?""
    parser = argparse.ArgumentParser(
        prog="claw-desktop",
        description="OpenClaw Computer-Use Agent"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # detect 命令
    detect_parser = subparsers.add_parser("detect", help="检测屏幕元�?)
    detect_parser.add_argument("-o", "--output", help="输出JSON文件路径")
    detect_parser.add_argument("-v", "--visualize", action="store_true", help="保存可视化图�?)
    
    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="执行任务文件")
    execute_parser.add_argument("task_file", help="任务JSON文件路径")
    execute_parser.add_argument("-o", "--output", help="输出结果文件路径")
    execute_parser.add_argument("--headless", action="store_true", 
                               help="浏览器无头模式（不显示界面）")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行预定义任�?)
    run_parser.add_argument("task_name", help="任务名称")
    run_parser.add_argument("--params", nargs="*", default=[], help="任务参数 (key=value)")
    
    # record 命令
    record_parser = subparsers.add_parser("record", help="录制桌面任务")
    record_parser.add_argument("-o", "--output", help="输出文件路径")
    record_parser.add_argument("--hotkey", default="<ctrl>+r", help="录制快捷�?(默认: <ctrl>+r)")
    record_parser.add_argument(
        "--mode", 
        choices=["desktop", "browser", "hybrid"],
        default="hybrid",
        help="录制模式: desktop(桌面), browser(浏览�?, hybrid(自动检�? 默认)"
    )
    
    # browser 命令
    browser_parser = subparsers.add_parser("browser", help="浏览器相关命�?)
    browser_parser.add_argument("command", choices=["check"], help="浏览器命�?)
    browser_parser.set_defaults(func=cmd_browser_check)
    
    # vision 命令
    vision_parser = subparsers.add_parser(
        "vision", 
        help="VLM 智能模式（自然语言控制�?
    )
    vision_parser.add_argument(
        "instruction",
        nargs="+",
        help="自然语言指令，例如：'帮我在淘宝上搜索蓝牙耳机'"
    )
    vision_parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "kimi", "kimi-coding"],
        default="openai",
        help="VLM 提供�?(默认: openai)"
    )
    vision_parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="最大执行步�?(默认: 20)"
    )
    vision_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动启动浏览器"
    )
    vision_parser.add_argument(
        "-o", "--output",
        help="保存任务文件的路�?
    )
    
    args = parser.parse_args()
    
    if args.command == "detect":
        cmd_detect(args)
    elif args.command == "execute":
        cmd_execute(args)
    elif args.command == "run":
        # 解析参数
        params = {}
        for p in args.params:
            if "=" in p:
                k, v = p.split("=", 1)
                params[k] = v
        args.params = params
        cmd_run(args)
    elif args.command == "record":
        cmd_record(args)
    elif args.command == "browser":
        args.func(args)
    elif args.command == "vision":
        cmd_vision(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
