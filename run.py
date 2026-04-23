#!/usr/bin/env python3
"""
OpenClaw Computer-Use Agent 运行脚本

便捷的命令行入口，用于运行测试、任务和基准测试。
"""

import argparse
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def cmd_test(args):
    """运行测试"""
    import subprocess
    
    if args.category:
        # 运行特定类别的测试
        from tests.test_suite import run_test_suite
        run_test_suite(args.category)
    elif args.all:
        # 运行所有测试
        subprocess.run(["python", "-m", "pytest", "tests/", "-v", "--tb=short"])
    else:
        # 运行基础测试
        subprocess.run(["python", "-m", "pytest", "tests/test_suite.py::TestBasicFunctionality", "-v"])


def cmd_run(args):
    """运行任务"""
    from claw_desktop import ComputerUseAgent
    
    agent = ComputerUseAgent()
    
    if args.list:
        # 列出所有预定义任务
        tasks = agent.list_tasks()
        print("\n📋 预定义任务列表:")
        print("-" * 50)
        for task in tasks:
            print(f"  • {task['name']:20} - {task['description']}")
        print()
        return
    
    if args.task:
        # 运行指定任务
        print(f"\n🚀 运行任务: {args.task}")
        print("-" * 50)
        
        # 解析参数
        kwargs = {}
        if args.params:
            for param in args.params:
                if "=" in param:
                    k, v = param.split("=", 1)
                    # 尝试转换为数字
                    try:
                        v = int(v)
                    except ValueError:
                        try:
                            v = float(v)
                        except ValueError:
                            pass
                    kwargs[k] = v
        
        result = agent.execute_task(args.task, **kwargs)
        
        print("\n📊 执行结果:")
        print(f"  状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"  完成步骤: {result.completed_steps}")
        print(f"  耗时: {result.duration:.2f}s")
        
        if result.error:
            print(f"  错误: {result.error}")
        
        if args.visualize and result.screenshots:
            from claw_desktop.utils.visualizer import ExecutionVisualizer
            viz = ExecutionVisualizer()
            report_path = viz.create_execution_report(result)
            print(f"  可视化报告: {report_path}")


def cmd_benchmark(args):
    """运行基准测试"""
    from tests.benchmark import BenchmarkSuite
    
    suite = BenchmarkSuite()
    suite.run_all()
    suite.print_report()
    
    if args.save:
        suite.save_report()


def cmd_detect(args):
    """检测屏幕元素"""
    from claw_desktop import ScreenCapture, ElementDetector
    from claw_desktop.utils.visualizer import ExecutionVisualizer
    
    print("\n🔍 检测屏幕元素...")
    print("-" * 50)
    
    capture = ScreenCapture()
    detector = ElementDetector()
    
    image = capture.capture()
    elements = detector.detect(image)
    
    print(f"\n检测到 {len(elements)} 个元素:")
    for elem in elements[:10]:  # 只显示前10个
        print(f"  [{elem.id}] {elem.element_type.value:8} "
              f"@ ({elem.center[0]:4}, {elem.center[1]:4}) "
              f"置信度={elem.confidence:.2f}")
    
    if len(elements) > 10:
        print(f"  ... 还有 {len(elements) - 10} 个元素")
    
    if args.visualize:
        viz = ExecutionVisualizer()
        path = viz.visualize_detection(image, elements)
        print(f"\n📸 可视化图像已保存: {path}")
    
    if args.output:
        import json
        data = {
            "count": len(elements),
            "elements": [e.to_dict() for e in elements]
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n📄 结果已保存: {args.output}")


def cmd_execute(args):
    """执行任务文件"""
    import json
    from claw_desktop import ComputerUseAgent, Task, TaskSequence
    
    print(f"\n📂 加载任务文件: {args.file}")
    print("-" * 50)
    
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 解析任务
    tasks = [Task(**t) for t in data.get("tasks", [])]
    sequence = TaskSequence(
        name=data.get("name", "unnamed"),
        tasks=tasks,
        max_retries=data.get("max_retries", 3)
    )
    
    print(f"任务名称: {sequence.name}")
    print(f"任务数: {len(tasks)}")
    
    agent = ComputerUseAgent()
    result = agent.execute(sequence)
    
    print("\n📊 执行结果:")
    print(f"  状态: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"  耗时: {result.duration:.2f}s")


def main():
    """主入口"""
    import claw_desktop
    claw_desktop.fix_windows_encoding()

    parser = argparse.ArgumentParser(
        prog="run.py",
        description="OpenClaw Computer-Use Agent 运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行基础测试
  python run.py test
  
  # 运行所有测试
  python run.py test --all
  
  # 列出预定义任务
  python run.py run --list
  
  # 运行记事本任务
  python run.py run notepad_type
  
  # 运行计算器任务并传递参数
  python run.py run calculator_add a=5 b=3
  
  # 检测屏幕元素
  python run.py detect --visualize
  
  # 运行基准测试
  python run.py benchmark
  
  # 执行任务文件
  python run.py execute examples/task_notepad.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # test 命令
    test_parser = subparsers.add_parser("test", help="运行测试")
    test_parser.add_argument("--all", action="store_true", help="运行所有测试")
    test_parser.add_argument("--category", nargs="+", 
                            choices=["basic", "predefined", "execution", "error_handling", "performance"],
                            help="运行特定类别的测试")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行预定义任务")
    run_parser.add_argument("task", nargs="?", help="任务名称")
    run_parser.add_argument("--list", action="store_true", help="列出所有任务")
    run_parser.add_argument("--params", nargs="*", help="任务参数 (key=value)")
    run_parser.add_argument("-v", "--visualize", action="store_true", help="生成可视化报告")
    
    # benchmark 命令
    benchmark_parser = subparsers.add_parser("benchmark", help="运行性能基准测试")
    benchmark_parser.add_argument("--save", action="store_true", help="保存报告")
    
    # detect 命令
    detect_parser = subparsers.add_parser("detect", help="检测屏幕元素")
    detect_parser.add_argument("-v", "--visualize", action="store_true", help="保存可视化图像")
    detect_parser.add_argument("-o", "--output", help="输出JSON文件路径")
    
    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="执行任务文件")
    execute_parser.add_argument("file", help="任务JSON文件路径")
    
    args = parser.parse_args()
    
    if args.command == "test":
        cmd_test(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "detect":
        cmd_detect(args)
    elif args.command == "execute":
        cmd_execute(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

