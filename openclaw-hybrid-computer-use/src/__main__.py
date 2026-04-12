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
    """检测屏幕元素命令"""
    print("正在检测屏幕元素...")
    
    capture = ScreenCapture()
    detector = ElementDetector()
    
    image = capture.capture()
    elements = detector.detect(image)
    
    print(f"\n检测到 {len(elements)} 个元素:")
    for elem in elements:
        print(f"  [{elem.id}] {elem.element_type.value:8} @ ({elem.center[0]:4}, {elem.center[1]:4})  置信度={elem.confidence:.2f}")
    
    if args.output:
        # 保存检测结果
        output_data = {
            "count": len(elements),
            "elements": [e.to_dict() for e in elements]
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")
    
    if args.visualize:
        # 保存可视化图像
        viz_path = Path(args.output).parent / "detection_visualization.png" if args.output else "detection_visualization.png"
        save_debug_image(image, viz_path, elements)
        print(f"可视化图像已保存到: {viz_path}")


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
        print("浏览器将以无头模式运行")
    
    # 执行
    agent = ComputerUseAgent(config=config)
    result = agent.execute(sequence)
    
    print(f"\n执行结果: {'成功' if result.success else '失败'}")
    print(f"完成步骤: {result.completed_steps}/{len(tasks)}")
    print(f"耗时: {result.duration:.2f}秒")
    
    if result.error:
        print(f"错误: {result.error}")
    
    # 保存结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)


def cmd_run(args):
    """运行预定义任务命令"""
    print(f"运行预定义任务: {args.task_name}")
    
    agent = ComputerUseAgent()
    result = agent.execute_task(args.task_name, **args.params)
    
    print(f"\n执行结果: {'成功' if result.success else '失败'}")
    print(f"耗时: {result.duration:.2f}秒")
    
    if result.error:
        print(f"错误: {result.error}")


def cmd_browser_check(args):
    """检查浏览器安装状态"""
    try:
        from playwright.sync_api import sync_playwright
        
        print("检查 Playwright 浏览器安装状态...")
        
        with sync_playwright() as p:
            for browser_type in ["chromium", "firefox", "webkit"]:
                try:
                    browser = getattr(p, browser_type).launch(headless=True)
                    browser.close()
                    print(f"  [OK] {browser_type}: 已安装")
                except Exception as e:
                    print(f"  [FAIL] {browser_type}: 未安装")
        
        print("\n安装浏览器命令:")
        print("  playwright install chromium")
        print("  playwright install firefox")
        print("  playwright install webkit")
        
    except ImportError:
        print("[FAIL] Playwright 未安装")
        print("  运行: pip install playwright")


def cmd_record(args):
    """录制任务命令"""
    from .core.recorder import TaskRecorder
    from .utils.shortcut_listener import ShortcutListener
    
    recorder = TaskRecorder()
    
    def toggle_recording():
        if recorder.is_recording:
            try:
                session = recorder.stop_recording()
                # 保存
                output = args.output or f"recorded_{datetime.now():%Y%m%d_%H%M%S}.json"
                session.save_to_file(output)
                print(f"💾 已保存: {output}")
            except Exception as e:
                print(f"❌ 保存失败: {e}")
        else:
            try:
                recorder.start_recording()
            except Exception as e:
                print(f"❌ 开始录制失败: {e}")
    
    # 设置快捷键监听
    listener = ShortcutListener(toggle_recording, args.hotkey)
    listener.start()
    
    print(f"🎙️  任务录制器")
    print(f"   快捷键: {args.hotkey}")
    print(f"   按 {args.hotkey} 开始/停止录制")
    print(f"   按 Ctrl+C 退出\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        if recorder.is_recording:
            recorder.stop_recording()
        print("\n👋 已退出")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="claw-desktop",
        description="OpenClaw Computer-Use Agent"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # detect 命令
    detect_parser = subparsers.add_parser("detect", help="检测屏幕元素")
    detect_parser.add_argument("-o", "--output", help="输出JSON文件路径")
    detect_parser.add_argument("-v", "--visualize", action="store_true", help="保存可视化图像")
    
    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="执行任务文件")
    execute_parser.add_argument("task_file", help="任务JSON文件路径")
    execute_parser.add_argument("-o", "--output", help="输出结果文件路径")
    execute_parser.add_argument("--headless", action="store_true", 
                               help="浏览器无头模式（不显示界面）")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行预定义任务")
    run_parser.add_argument("task_name", help="任务名称")
    run_parser.add_argument("--params", nargs="*", default=[], help="任务参数 (key=value)")
    
    # record 命令
    record_parser = subparsers.add_parser("record", help="录制桌面任务")
    record_parser.add_argument("-o", "--output", help="输出文件路径")
    record_parser.add_argument("--hotkey", default="<ctrl>+r", help="录制快捷键 (默认: <ctrl>+r)")
    
    # browser 命令
    browser_parser = subparsers.add_parser("browser", help="浏览器相关命令")
    browser_parser.add_argument("command", choices=["check"], help="浏览器命令")
    browser_parser.set_defaults(func=cmd_browser_check)
    
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
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
