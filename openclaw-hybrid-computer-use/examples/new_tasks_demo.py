#!/usr/bin/env python3
"""
新增预置任务演示

展示 v0.3.1 新增的 9 个预置任务
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.tasks_predefined import list_predefined_tasks, get_predefined_task


def main():
    print("=" * 60)
    print("🎉 OpenClaw v0.3.1 新增预置任务展示")
    print("=" * 60)
    
    # 获取所有任务
    all_tasks = list_predefined_tasks()
    
    # 分类展示
    browser_tasks = []
    desktop_tasks = []
    
    browser_keywords = ['github', 'taobao', 'jd', 'baidu', 'douyin', 'bilibili', 'weibo', 'zhihu', 'weather', 'chrome']
    
    for task in all_tasks:
        name = task['name']
        if any(kw in name for kw in browser_keywords):
            browser_tasks.append(task)
        else:
            desktop_tasks.append(task)
    
    print(f"\n📊 总计: {len(all_tasks)} 个预置任务")
    print(f"   - 浏览器任务: {len(browser_tasks)} 个")
    print(f"   - 桌面任务: {len(desktop_tasks)} 个")
    
    print("\n" + "=" * 60)
    print("🌐 浏览器任务")
    print("=" * 60)
    
    new_browser = ['bilibili_search', 'weibo_hot', 'zhihu_search']
    for task in browser_tasks:
        marker = "🆕 " if task['name'] in new_browser else "   "
        print(f"{marker}{task['name']}: {task['description']}")
    
    print("\n" + "=" * 60)
    print("🖥️ 桌面任务")
    print("=" * 60)
    
    new_desktop = ['open_qq', 'open_dingtalk', 'open_cmd', 'system_info', 'new_text_file', 'screenshot_desktop']
    for task in desktop_tasks:
        marker = "🆕 " if task['name'] in new_desktop else "   "
        print(f"{marker}{task['name']}: {task['description']}")
    
    print("\n" + "=" * 60)
    print("💡 使用示例")
    print("=" * 60)
    
    examples = [
        ("bilibili_search", {"keyword": "Python教程"}),
        ("weibo_hot", {}),
        ("zhihu_search", {"keyword": "人工智能"}),
        ("open_qq", {}),
        ("open_cmd", {}),
    ]
    
    for task_name, kwargs in examples:
        print(f"\n👉 {task_name}:")
        if kwargs:
            params = ', '.join([f'{k}="{v}"' for k, v in kwargs.items()])
            print(f"   py -m src run {task_name} {params}")
        else:
            print(f"   py -m src run {task_name}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
