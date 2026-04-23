"""任务构建工具 - 帮助构建稳定的任务序列"""

from typing import List, Optional
from ..core.models import Task, TaskSequence


class TaskBuilder:
    """任务构建器"""
    
    @staticmethod
    def build_browser_task(
        name: str,
        url: str,
        steps: List[Task],
        max_retries: int = 3
    ) -> TaskSequence:
        """
        构建浏览器任务
        
        Args:
            name: 任务名称
            url: 目标URL
            steps: 操作步骤列表
            max_retries: 最大重试次数
            
        Returns:
            任务序列
        """
        base_tasks = [
            Task("browser_launch", value="chromium", delay=2.0),
            Task("browser_goto", value=url, delay=5.0),
        ]
        
        # 添加用户步骤
        base_tasks.extend(steps)
        
        # 添加关闭浏览器（可选）
        # base_tasks.append(Task("browser_close", delay=1.0))
        
        return TaskSequence(
            name=name,
            tasks=base_tasks,
            max_retries=max_retries
        )
    
    @staticmethod
    def build_search_task(
        site_name: str,
        url: str,
        search_input_selectors: List[str],
        search_button_selectors: List[str],
        keyword: str,
        wait_for_selectors: Optional[List[str]] = None,
        scroll: bool = True
    ) -> TaskSequence:
        """
        构建搜索任务模板
        
        Args:
            site_name: 网站名称
            url: 网站URL
            search_input_selectors: 搜索框选择器列表（按优先级）
            search_button_selectors: 搜索按钮选择器列表
            keyword: 搜索关键词
            wait_for_selectors: 等待加载的选择器
            scroll: 是否滚动页面
            
        Returns:
            任务序列
        """
        # 构建多重选择器字符串
        input_selector = ", ".join(search_input_selectors) if search_input_selectors else "input[type='text']"
        button_selector = ", ".join(search_button_selectors) if search_button_selectors else "button[type='submit']"
        wait_selector = ", ".join(wait_for_selectors) if wait_for_selectors else "body"
        
        steps = [
            Task("browser_click", target=input_selector, delay=1.0),
            Task("browser_type", target=input_selector, value=keyword, delay=0.5),
            Task("browser_click", target=button_selector, delay=3.0),
            Task("browser_wait", target=wait_selector, value="visible", delay=2.0),
        ]
        
        if scroll:
            steps.append(Task("browser_scroll", value="600", delay=1.0))
        
        steps.append(Task("browser_screenshot", value=f"{site_name}_search_{keyword}.png", delay=1.0))
        
        return TaskBuilder.build_browser_task(
            name=f"{site_name}_search_{keyword}",
            url=url,
            steps=steps,
            max_retries=3
        )
    
    @staticmethod
    def build_desktop_app_task(
        app_name: str,
        launch_target: str,
        wait_time: float = 3.0
    ) -> TaskSequence:
        """
        构建桌面应用启动任务
        
        Args:
            app_name: 应用名称
            launch_target: 启动目标
            wait_time: 等待时间
            
        Returns:
            任务序列
        """
        return TaskSequence(
            name=f"open_{app_name}",
            tasks=[
                Task("launch", target=launch_target),
                Task("wait", delay=wait_time),
            ],
            max_retries=2
        )


class RetryDecorator:
    """重试装饰器工具"""
    
    @staticmethod
    def with_retry(task: Task, max_attempts: int = 3) -> List[Task]:
        """
        为任务添加重试机制
        
        通过复制任务多次来实现重试效果
        
        Args:
            task: 原始任务
            max_attempts: 最大尝试次数
            
        Returns:
            任务列表
        """
        tasks = []
        for i in range(max_attempts):
            # 复制任务，但添加更长的延迟（指数退避）
            delay = task.delay * (1.5 ** i)
            tasks.append(Task(
                action=task.action,
                target=task.target,
                value=task.value,
                delay=delay
            ))
        return tasks


def create_stable_task(
    action: str,
    target: str,
    value: str = "",
    delay: float = 1.0,
    fallback_targets: Optional[List[str]] = None
) -> Task:
    """
    创建稳定的任务（带备选目标）
    
    Args:
        action: 动作类型
        target: 主要目标
        value: 值
        delay: 延迟
        fallback_targets: 备选目标列表
        
    Returns:
        任务
    """
    # 构建多重选择器
    if fallback_targets:
        all_targets = [target] + fallback_targets
        target = ", ".join(all_targets)
    
    return Task(
        action=action,
        target=target,
        value=value,
        delay=delay
    )
