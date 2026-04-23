#!/usr/bin/env python3
"""
任务稳定性优化测试

演示优化后的任务执行器功能
"""

import sys
sys.path.insert(0, '.')

from src.core.selectors_config import build_multi_selector, get_selectors
from src.utils.task_builder import TaskBuilder, create_stable_task
from src.core.models import Task


def test_selectors_config():
    """测试选择器配置"""
    print("=" * 60)
    print("🔧 选择器配置测试")
    print("=" * 60)
    
    sites = ["taobao", "jd", "douyin", "bilibili"]
    elements = ["search_input", "search_button"]
    
    for site in sites:
        print(f"\n📍 {site.upper()}")
        for element in elements:
            selectors = get_selectors(site, element)
            if selectors:
                multi_selector = build_multi_selector(site, element)
                print(f"  {element}: {multi_selector[:80]}...")


def test_task_builder():
    """测试任务构建器"""
    print("\n" + "=" * 60)
    print("🔨 任务构建器测试")
    print("=" * 60)
    
    # 测试搜索任务构建
    print("\n1. 构建淘宝搜索任务...")
    from src.core.selectors_config import get_selectors
    
    task = TaskBuilder.build_search_task(
        site_name="taobao",
        url="https://www.taobao.com",
        search_input_selectors=get_selectors("taobao", "search_input"),
        search_button_selectors=get_selectors("taobao", "search_button"),
        keyword="iPhone 15",
        wait_for_selectors=get_selectors("taobao", "product_item"),
        scroll=True
    )
    
    print(f"   ✅ 任务创建: {task.name}")
    print(f"   步骤数: {len(task.tasks)}")
    print(f"   重试次数: {task.max_retries}")
    print("\n   执行步骤:")
    for i, t in enumerate(task.tasks[:5], 1):
        target = t.target or ""
        print(f"     {i}. {t.action}: {target[:50]}{'...' if len(target) > 50 else ''}")
    if len(task.tasks) > 5:
        print(f"     ... 还有 {len(task.tasks) - 5} 步")


def test_stable_task():
    """测试稳定任务创建"""
    print("\n" + "=" * 60)
    print("🛡️ 稳定任务创建测试")
    print("=" * 60)
    
    print("\n2. 创建带备选选择器的任务...")
    task = create_stable_task(
        action="browser_click",
        target="#search-input",
        fallback_targets=[
            "input[placeholder*='搜索']",
            ".search-input",
            "input[type='text']"
        ],
        delay=1.0
    )
    
    print(f"   ✅ 任务创建: {task.action}")
    print(f"   目标选择器: {task.target}")
    print(f"   延迟: {task.delay}s")


def test_enhanced_executor():
    """测试增强版执行器"""
    print("\n" + "=" * 60)
    print("⚡ 增强版执行器测试")
    print("=" * 60)
    
    try:
        from src.core.task_executor_enhanced import EnhancedTaskExecutor
        
        print("\n3. 初始化增强版执行器...")
        executor = EnhancedTaskExecutor()
        print(f"   ✅ 执行器初始化成功")
        print(f"   最大重试: {executor.max_retries}")
        print(f"   重试延迟: {executor.retry_delay}s")
        print(f"   选择器降级: {'启用' if executor.selector_fallback else '禁用'}")
        
        # 测试多重选择器解析
        print("\n4. 测试多重选择器解析...")
        test_cases = [
            "#id1, .class2, [attr3]",
            "selector1 | selector2 | selector3",
            "single-selector"
        ]
        for case in test_cases:
            result = executor._parse_multi_selectors(case)
            print(f"   '{case}' -> {len(result)} 个选择器")
            
    except ImportError as e:
        print(f"   ⚠️ 模块导入失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 OpenClaw 任务稳定性优化测试")
    print("=" * 60)
    
    test_selectors_config()
    test_task_builder()
    test_stable_task()
    test_enhanced_executor()
    
    print("\n" + "=" * 60)
    print("✅ 优化测试完成!")
    print("=" * 60)
    print("\n📋 优化内容:")
    print("  1. 多重选择器配置 - 提高元素定位成功率")
    print("  2. 智能重试机制 - 自动尝试备选方案")
    print("  3. 任务构建器 - 简化任务创建流程")
    print("  4. 前置检查 - 提前发现环境问题")


if __name__ == "__main__":
    main()
