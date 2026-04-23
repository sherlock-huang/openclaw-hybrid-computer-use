"""任务学习记录管理 CLI"""

import argparse
import sys
import json
from pathlib import Path

from .task_learner import TaskLearner


def print_table(rows: list, headers: list):
    """简单表格打印"""
    if not rows:
        print("无数据")
        return
    
    # 计算每列最大宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 打印表头
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))
    
    # 打印数据行
    for row in rows:
        print(" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))


def cmd_stats(args):
    """显示所有任务统计"""
    learner = TaskLearner()
    stats = learner.get_stats()
    
    if not stats:
        print("暂无学习记录")
        return 0
    
    rows = []
    for s in stats:
        total = s["success_count"] + s["fail_count"]
        rows.append([
            s["task_type"],
            s["target"][:20],
            f"{s['success_rate']:.0%}",
            f"{s['success_count']}/{total}",
            f"{s['avg_duration']:.1f}s",
            f"{s['optimal_delay']:.1f}s",
            s["environment_key"],
        ])
    
    print_table(rows, ["Task Type", "Target", "Success Rate", "Success/Total", "Avg Duration", "Optimal Delay", "Environment"])
    print(f"\n总计 {len(stats)} 条学习记录")
    return 0


def cmd_top(args):
    """显示成功率最高的任务"""
    learner = TaskLearner()
    stats = learner.get_stats()
    stats.sort(key=lambda x: x["success_rate"], reverse=True)
    
    limit = args.n if hasattr(args, 'n') else 10
    top = stats[:limit]
    
    if not top:
        print("暂无学习记录")
        return 0
    
    rows = []
    for s in top:
        total = s["success_count"] + s["fail_count"]
        rows.append([
            s["task_type"],
            s["target"][:25],
            f"{s['success_rate']:.0%}",
            f"{s['success_count']}/{total}",
            f"{s['avg_duration']:.1f}s",
        ])
    
    print(f"Top {len(top)} 成功率最高的任务:")
    print_table(rows, ["Task Type", "Target", "Success Rate", "Success/Total", "Avg Duration"])
    return 0


def cmd_worst(args):
    """显示成功率最低的任务"""
    learner = TaskLearner()
    stats = learner.get_stats()
    stats.sort(key=lambda x: x["success_rate"])
    
    limit = args.n if hasattr(args, 'n') else 10
    worst = stats[:limit]
    
    if not worst:
        print("暂无学习记录")
        return 0
    
    rows = []
    for s in worst:
        total = s["success_count"] + s["fail_count"]
        rows.append([
            s["task_type"],
            s["target"][:25],
            f"{s['success_rate']:.0%}",
            f"{s['success_count']}/{total}",
            f"{s['avg_duration']:.1f}s",
        ])
    
    print(f"Top {len(worst)} 成功率最低的任务:")
    print_table(rows, ["Task Type", "Target", "Success Rate", "Success/Total", "Avg Duration"])
    return 0


def cmd_reset(args):
    """重置某个任务的学习记录"""
    learner = TaskLearner()
    success = learner.reset_pattern(args.task_type, args.target)
    if success:
        print(f"已重置学习记录: {args.task_type}:{args.target}")
        return 0
    else:
        print(f"未找到学习记录: {args.task_type}:{args.target}")
        return 1


def cmd_export(args):
    """导出学习记录"""
    learner = TaskLearner()
    success = learner.export(args.path)
    if success:
        print(f"已导出学习记录到: {args.path}")
        return 0
    else:
        print("导出失败")
        return 1


def main():
    parser = argparse.ArgumentParser(description="任务学习记录管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # stats
    subparsers.add_parser("stats", help="显示所有任务统计")
    
    # top
    top_parser = subparsers.add_parser("top", help="显示成功率最高的任务")
    top_parser.add_argument("-n", type=int, default=10, help="显示数量（默认10）")
    
    # worst
    worst_parser = subparsers.add_parser("worst", help="显示成功率最低的任务")
    worst_parser.add_argument("-n", type=int, default=10, help="显示数量（默认10）")
    
    # reset
    reset_parser = subparsers.add_parser("reset", help="重置某个任务的学习记录")
    reset_parser.add_argument("task_type", help="任务类型")
    reset_parser.add_argument("target", help="目标特征")
    
    # export
    export_parser = subparsers.add_parser("export", help="导出学习记录到 JSON")
    export_parser.add_argument("path", help="导出路径")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "stats": cmd_stats,
        "top": cmd_top,
        "worst": cmd_worst,
        "reset": cmd_reset,
        "export": cmd_export,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
