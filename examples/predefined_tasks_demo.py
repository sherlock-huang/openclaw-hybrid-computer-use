#!/usr/bin/env python3
"""
预置任务演示脚本

展示如何使用 OpenClaw 的预置任务系统
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.tasks_predefined import (
    list_predefined_tasks,
    get_predefined_task,
    get_task_info,
    PREDEFINED_TASKS
)
from src.core.models import TaskSequence


def print_header(title: str) -> None:
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_list_tasks() -> None:
    """演示：列出所有可用任务"""
    print_header("1. 列出所有可用预置任务")
    
    tasks = list_predefined_tasks()
    
    # 分类显示任务
    browser_tasks = [t for t in tasks if t["name"] in [
        "github_login", "taobao_search", "jd_search", 
        "baidu_search", "douyin_search", "weather_check", "chrome_search"
    ]]
    desktop_tasks = [t for t in tasks if t["name"] in [
        "open_wechat", "desktop_cleanup", "calculator", "calculator_add",
        "notepad_type", "explorer_navigate", "window_switch", 
        "desktop_screenshot", "text_copy_paste", "scroll_test", 
        "right_click", "multi_app"
    ]]
    
    print(f"\n共 {len(tasks)} 个预置任务\n")
    
    print("🌐 浏览器任务:")
    for i, task in enumerate(browser_tasks, 1):
        print(f"   {i}. {task['name']:<20} - {task['description']}")
    
    print("\n💻 桌面任务:")
    for i, task in enumerate(desktop_tasks, 1):
        print(f"   {i}. {task['name']:<20} - {task['description']}")


def demo_get_task_info() -> None:
    """演示：获取任务详情"""
    print_header("2. 获取任务详细信息")
    
    example_tasks = ["github_login", "taobao_search", "calculator", "weather_check"]
    
    for task_name in example_tasks:
        info = get_task_info(task_name)
        print(f"\n📋 任务: {info['name']}")
        print(f"   描述: {info['description']}")
        if info['parameters']:
            print(f"   参数:")
            for param in info['parameters']:
                print(f"      - {param['name']}: {param['description']}")


def demo_create_task() -> None:
    """演示：创建特定任务"""
    print_header("3. 创建特定任务实例")
    
    # 创建百度搜索任务
    print("\n🔍 创建百度搜索任务...")
    baidu_task = get_predefined_task("baidu_search", keyword="Python编程")
    print(f"   任务名称: {baidu_task.name}")
    print(f"   任务数量: {len(baidu_task.tasks)}")
    print(f"   最大重试: {baidu_task.max_retries}")
    
    # 创建天气查询任务
    print("\n🌤️  创建天气查询任务...")
    weather_task = get_predefined_task("weather_check", city="上海")
    print(f"   任务名称: {weather_task.name}")
    print(f"   任务数量: {len(weather_task.tasks)}")
    
    # 创建计算器任务
    print("\n🧮 创建计算器任务...")
    calc_task = get_predefined_task("calculator", expression="12*34")
    print(f"   任务名称: {calc_task.name}")
    print(f"   任务数量: {len(calc_task.tasks)}")


def demo_task_details() -> None:
    """演示：显示任务详细步骤"""
    print_header("4. 查看任务详细步骤")
    
    task = get_predefined_task("taobao_search", keyword="iPhone")
    
    print(f"\n任务: {task.name}")
    print(f"步骤明细:")
    for i, step in enumerate(task.tasks, 1):
        action = step.action
        details = []
        if step.target:
            details.append(f"target={step.target}")
        if step.value:
            details.append(f"value={step.value}")
        if step.delay:
            details.append(f"delay={step.delay}")
        
        detail_str = ", ".join(details)
        print(f"   {i}. {action:<10} {detail_str}")


def demo_save_task() -> None:
    """演示：保存任务到文件"""
    print_header("5. 保存任务到文件")
    
    # 创建一个示例任务
    task = get_predefined_task("github_login", username="example", password="****")
    
    # 保存为JSON
    output_dir = Path(__file__).parent / "saved_tasks"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "github_login_task.json"
    
    # 转换为字典并保存
    task_dict = {
        "name": task.name,
        "max_retries": task.max_retries,
        "tasks": [
            {
                "action": t.action,
                "target": t.target,
                "value": t.value,
                "delay": t.delay
            }
            for t in task.tasks
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(task_dict, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 任务已保存到: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size} bytes")


def demo_category_stats() -> None:
    """演示：任务分类统计"""
    print_header("6. 任务分类统计")
    
    browser_keywords = ["github", "taobao", "jd", "baidu", "douyin", "weather", "chrome", "search"]
    desktop_keywords = ["wechat", "desktop", "calculator", "notepad", "explorer", "window", "text", "scroll", "click", "app"]
    
    browser_count = sum(1 for name in PREDEFINED_TASKS.keys() 
                       if any(kw in name for kw in browser_keywords))
    desktop_count = sum(1 for name in PREDEFINED_TASKS.keys() 
                       if any(kw in name for kw in desktop_keywords))
    
    print(f"\n📊 统计信息:")
    print(f"   浏览器相关任务: {browser_count} 个")
    print(f"   桌面相关任务:   {desktop_count} 个")
    print(f"   总计:           {len(PREDEFINED_TASKS)} 个")


def demo_task_usage_examples() -> None:
    """演示：任务使用示例"""
    print_header("7. 任务使用示例代码")
    
    examples = """
# 示例 1: 搜索商品
from src.core.tasks_predefined import get_predefined_task

task = get_predefined_task("jd_search", keyword="无线耳机")
executor.execute(task)

# 示例 2: 查看天气
task = get_predefined_task("weather_check", city="广州")
executor.execute(task)

# 示例 3: 打开微信
task = get_predefined_task("open_wechat")
executor.execute(task)

# 示例 4: 计算表达式
task = get_predefined_task("calculator", expression="100/4")
executor.execute(task)

# 示例 5: 列出所有可用任务
from src.core.tasks_predefined import list_predefined_tasks
tasks = list_predefined_tasks()
for task in tasks:
    print(f"{task['name']}: {task['description']}")
"""
    print(examples)


def main() -> None:
    """主函数"""
    print("\n" + "🚀 OpenClaw 预置任务演示".center(60, "="))
    
    try:
        demo_list_tasks()
        demo_get_task_info()
        demo_create_task()
        demo_task_details()
        demo_save_task()
        demo_category_stats()
        demo_task_usage_examples()
        
        print_header("演示完成")
        print("\n✨ 所有演示已完成！")
        print("\n提示: 可以使用以下命令运行此演示:")
        print(f"   python {Path(__file__).name}")
        
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
