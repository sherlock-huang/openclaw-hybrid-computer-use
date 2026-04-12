"""预定义任务集合"""

from typing import Dict, List, Any
from .models import Task, TaskSequence


# ==================== 浏览器任务 ====================

def create_github_login_task(username: str = "", password: str = "") -> TaskSequence:
    """
    GitHub 登录任务
    
    在浏览器中打开 GitHub 登录页面并自动填写用户名和密码
    
    Args:
        username: GitHub 用户名
        password: GitHub 密码
        
    Returns:
        任务序列
    """
    tasks = [
        Task("launch", target="chrome"),
        Task("wait", delay=2.0),
        Task("click", target="address_bar", delay=0.5),
        Task("type", value="https://github.com/login"),
        Task("press", value="enter"),
        Task("wait", delay=3.0),
    ]
    
    if username:
        tasks.extend([
            Task("click", target="login_field", delay=0.5),
            Task("type", value=username),
        ])
    
    if password:
        tasks.extend([
            Task("click", target="password_field", delay=0.5),
            Task("type", value=password),
        ])
    
    return TaskSequence(
        name="github_login",
        tasks=tasks,
        max_retries=2
    )


def create_taobao_search_task(keyword: str = "手机") -> TaskSequence:
    """
    淘宝搜索任务
    
    在浏览器中打开淘宝并搜索指定关键词
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="taobao_search",
        tasks=[
            Task("launch", target="chrome"),
            Task("wait", delay=2.0),
            Task("click", target="address_bar", delay=0.5),
            Task("type", value="https://www.taobao.com"),
            Task("press", value="enter"),
            Task("wait", delay=3.0),
            Task("click", target="search_box", delay=0.5),
            Task("type", value=keyword),
            Task("press", value="enter"),
        ],
        max_retries=2
    )


def create_jd_search_task(keyword: str = "笔记本电脑") -> TaskSequence:
    """
    京东搜索任务
    
    在浏览器中打开京东并搜索指定关键词
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="jd_search",
        tasks=[
            Task("launch", target="chrome"),
            Task("wait", delay=2.0),
            Task("click", target="address_bar", delay=0.5),
            Task("type", value="https://www.jd.com"),
            Task("press", value="enter"),
            Task("wait", delay=3.0),
            Task("click", target="search_box", delay=0.5),
            Task("type", value=keyword),
            Task("press", value="enter"),
        ],
        max_retries=2
    )


def create_baidu_search_task(keyword: str = "OpenClaw AI") -> TaskSequence:
    """
    百度搜索任务
    
    在浏览器中打开百度并搜索指定关键词
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="baidu_search",
        tasks=[
            Task("launch", target="chrome"),
            Task("wait", delay=2.0),
            Task("click", target="address_bar", delay=0.5),
            Task("type", value="https://www.baidu.com"),
            Task("press", value="enter"),
            Task("wait", delay=2.0),
            Task("click", target="search_input", delay=0.5),
            Task("type", value=keyword),
            Task("press", value="enter"),
        ],
        max_retries=2
    )


def create_douyin_search_task(keyword: str = "科技") -> TaskSequence:
    """
    抖音搜索任务
    
    在浏览器中打开抖音并搜索指定关键词
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="douyin_search",
        tasks=[
            Task("launch", target="chrome"),
            Task("wait", delay=2.0),
            Task("click", target="address_bar", delay=0.5),
            Task("type", value="https://www.douyin.com"),
            Task("press", value="enter"),
            Task("wait", delay=4.0),
            Task("click", target="search_box", delay=0.5),
            Task("type", value=keyword),
            Task("press", value="enter"),
        ],
        max_retries=2
    )


def create_weather_check_task(city: str = "北京") -> TaskSequence:
    """
    查看天气任务
    
    在浏览器中搜索指定城市的天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="weather_check",
        tasks=[
            Task("launch", target="chrome"),
            Task("wait", delay=2.0),
            Task("click", target="address_bar", delay=0.5),
            Task("type", value=f"https://www.baidu.com/s?wd={city}天气"),
            Task("press", value="enter"),
            Task("wait", delay=3.0),
        ],
        max_retries=2
    )


# ==================== 桌面任务 ====================

def create_open_wechat_task() -> TaskSequence:
    """
    打开微信任务
    
    启动微信应用程序
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_wechat",
        tasks=[
            Task("launch", target="wechat"),
            Task("wait", delay=3.0),
        ],
        max_retries=2
    )


def create_desktop_cleanup_task() -> TaskSequence:
    """
    桌面整理任务
    
    创建新文件夹并将桌面文件整理到该文件夹中
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="desktop_cleanup",
        tasks=[
            Task("hotkey", value="win+d", delay=1.0),  # 显示桌面
            Task("right_click", target="empty_area", delay=0.5),  # 右键空白处
            Task("click", target="new_folder", delay=0.5),  # 新建文件夹
            Task("type", value="桌面整理"),  # 命名文件夹
            Task("press", value="enter", delay=0.5),
            # 选择多个文件并拖动到文件夹中
            Task("drag", target="file1", value="folder", delay=0.5),
        ],
        max_retries=2
    )


def create_calculator_task(expression: str = "1+2") -> TaskSequence:
    """
    计算器任务（支持表达式）
    
    打开计算器并计算数学表达式
    
    Args:
        expression: 数学表达式（如 "12*34"）
        
    Returns:
        任务序列
    """
    tasks = [
        Task("launch", target="calculator"),
        Task("wait", delay=1.5),
    ]
    
    # 将表达式转换为计算器操作
    for char in expression:
        if char.isdigit():
            tasks.append(Task("click", target=f"button_{char}", delay=0.3))
        elif char in ['+', '-', '*', '/']:
            operator_map = {'+': 'button_plus', '-': 'button_minus', 
                          '*': 'button_multiply', '/': 'button_divide'}
            tasks.append(Task("click", target=operator_map.get(char, 'button'), delay=0.3))
        elif char == '.':
            tasks.append(Task("click", target="button_decimal", delay=0.3))
    
    tasks.append(Task("click", target="button_equals"))
    
    return TaskSequence(
        name="calculator",
        tasks=tasks,
        max_retries=2
    )


# ==================== 原有预定义任务 ====================

def create_calculator_add_task(a: int = 1, b: int = 2) -> TaskSequence:
    """
    创建计算器加法任务
    
    Args:
        a: 第一个数字
        b: 第二个数字
        
    Returns:
        任务序列
    """
    # 注意：实际使用时需要根据计算器UI调整坐标
    # 这里使用相对位置作为示例
    return TaskSequence(
        name=f"calculator_{a}+{b}",
        tasks=[
            Task("launch", target="calculator"),
            Task("wait", delay=1.5),
            # 输入第一个数字
            *[Task("click", target="button", delay=0.3) for _ in str(a)],
            # 点击加号
            Task("click", target="button_plus", delay=0.3),
            # 输入第二个数字
            *[Task("click", target="button", delay=0.3) for _ in str(b)],
            # 点击等于
            Task("click", target="button_equals"),
        ],
        max_retries=2
    )


def create_notepad_type_task(text: str = "Hello World") -> TaskSequence:
    """
    创建记事本输入任务
    
    Args:
        text: 要输入的文字
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="notepad_type",
        tasks=[
            Task("launch", target="notepad"),
            Task("wait", delay=1.5),
            Task("type", value=text),
        ],
        max_retries=2
    )


def create_chrome_search_task(url: str = "openclaw.ai") -> TaskSequence:
    """
    创建Chrome搜索任务
    
    Args:
        url: 要访问的URL
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="chrome_search",
        tasks=[
            Task("launch", target="chrome"),
            Task("wait", delay=2.0),
            Task("click", target="input", delay=0.5),  # 地址栏
            Task("type", value=url),
            Task("press", value="enter"),
        ],
        max_retries=2
    )


def create_explorer_navigate_task(path: str = "Desktop") -> TaskSequence:
    """
    创建文件资源管理器导航任务
    
    Args:
        path: 要导航到的路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="explorer_navigate",
        tasks=[
            Task("launch", target="explorer"),
            Task("wait", delay=1.5),
            Task("hotkey", value="ctrl+l", delay=0.3),  # 聚焦地址栏
            Task("type", value=path),
            Task("press", value="enter"),
        ],
        max_retries=2
    )


def create_window_switch_task() -> TaskSequence:
    """
    创建窗口切换任务
    
    使用 Alt+Tab 切换窗口
    """
    return TaskSequence(
        name="window_switch",
        tasks=[
            Task("hotkey", value="alt+tab"),
            Task("wait", delay=0.5),
        ],
        max_retries=1
    )


def create_desktop_screenshot_task() -> TaskSequence:
    """
    创建桌面截图任务
    
    最小化所有窗口并截图
    """
    return TaskSequence(
        name="desktop_screenshot",
        tasks=[
            Task("hotkey", value="win+d", delay=1.0),  # 显示桌面
            Task("wait", delay=0.5),
        ],
        max_retries=1
    )


def create_text_copy_paste_task() -> TaskSequence:
    """
    创建复制粘贴任务
    
    在记事本中输入文字并复制粘贴
    """
    return TaskSequence(
        name="text_copy_paste",
        tasks=[
            Task("launch", target="notepad"),
            Task("wait", delay=1.5),
            Task("type", value="Hello ClawDesktop!"),
            Task("hotkey", value="ctrl+a", delay=0.3),  # 全选
            Task("hotkey", value="ctrl+c", delay=0.3),  # 复制
            Task("press", value="end", delay=0.3),      # 移到末尾
            Task("press", value="return", delay=0.3),   # 换行
            Task("hotkey", value="ctrl+v"),             # 粘贴
        ],
        max_retries=2
    )


def create_scroll_test_task() -> TaskSequence:
    """
    创建滚动测试任务
    
    打开记事本，输入多行文字，然后滚动
    """
    text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    return TaskSequence(
        name="scroll_test",
        tasks=[
            Task("launch", target="notepad"),
            Task("wait", delay=1.5),
            Task("type", value=text),
            Task("scroll", value="3", delay=0.5),   # 向上滚动
            Task("scroll", value="-3", delay=0.5),  # 向下滚动
        ],
        max_retries=2
    )


def create_right_click_task() -> TaskSequence:
    """
    创建右键菜单任务
    
    在桌面右键点击
    """
    return TaskSequence(
        name="right_click",
        tasks=[
            Task("hotkey", value="win+d", delay=1.0),  # 显示桌面
            Task("right_click", target="960,540", delay=0.5),  # 屏幕中心右键
            Task("press", value="esc", delay=0.3),     # 关闭菜单
        ],
        max_retries=2
    )


def create_multi_app_task() -> TaskSequence:
    """
    创建多应用切换任务
    
    打开计算器和记事本，然后切换
    """
    return TaskSequence(
        name="multi_app",
        tasks=[
            Task("launch", target="calculator"),
            Task("wait", delay=1.0),
            Task("launch", target="notepad"),
            Task("wait", delay=1.0),
            Task("hotkey", value="alt+tab", delay=0.5),  # 切换回计算器
            Task("hotkey", value="alt+tab", delay=0.5),  # 切换回记事本
        ],
        max_retries=2
    )


# 预定义任务注册表
PREDEFINED_TASKS: Dict[str, callable] = {
    # 浏览器任务
    "github_login": create_github_login_task,
    "taobao_search": create_taobao_search_task,
    "jd_search": create_jd_search_task,
    "baidu_search": create_baidu_search_task,
    "douyin_search": create_douyin_search_task,
    "weather_check": create_weather_check_task,
    # 桌面任务
    "open_wechat": create_open_wechat_task,
    "desktop_cleanup": create_desktop_cleanup_task,
    "calculator": create_calculator_task,
    # 原有任务
    "calculator_add": create_calculator_add_task,
    "notepad_type": create_notepad_type_task,
    "chrome_search": create_chrome_search_task,
    "explorer_navigate": create_explorer_navigate_task,
    "window_switch": create_window_switch_task,
    "desktop_screenshot": create_desktop_screenshot_task,
    "text_copy_paste": create_text_copy_paste_task,
    "scroll_test": create_scroll_test_task,
    "right_click": create_right_click_task,
    "multi_app": create_multi_app_task,
}


def get_predefined_task(name: str, **kwargs) -> TaskSequence:
    """
    获取预定义任务
    
    Args:
        name: 任务名称
        **kwargs: 任务参数
        
    Returns:
        任务序列
        
    Raises:
        ValueError: 如果任务不存在
    """
    if name not in PREDEFINED_TASKS:
        available = ", ".join(PREDEFINED_TASKS.keys())
        raise ValueError(f"未知的预定义任务: {name}. 可用任务: {available}")
    
    return PREDEFINED_TASKS[name](**kwargs)


def list_predefined_tasks() -> List[Dict[str, Any]]:
    """
    列出所有预定义任务
    
    Returns:
        任务信息列表
    """
    return [
        {"name": name, "description": func.__doc__.strip().split('\n')[0] if func.__doc__ else ""}
        for name, func in PREDEFINED_TASKS.items()
    ]


def get_task_info(name: str) -> Dict[str, Any]:
    """
    获取任务的详细信息
    
    Args:
        name: 任务名称
        
    Returns:
        任务信息字典
        
    Raises:
        ValueError: 如果任务不存在
    """
    if name not in PREDEFINED_TASKS:
        available = ", ".join(PREDEFINED_TASKS.keys())
        raise ValueError(f"未知的预定义任务: {name}. 可用任务: {available}")
    
    func = PREDEFINED_TASKS[name]
    doc = func.__doc__ or ""
    
    # 解析文档字符串获取参数信息
    lines = doc.strip().split('\n')
    description = lines[0] if lines else ""
    
    # 尝试从文档中提取参数
    params = []
    in_args = False
    for line in lines:
        if "Args:" in line:
            in_args = True
            continue
        if in_args:
            if line.strip() and not line.startswith(' '):
                break
            if ':' in line and line.strip().startswith((
                'username', 'password', 'keyword', 'city', 'expression', 
                'a:', 'b:', 'text:', 'url:', 'path:'
            )):
                param_name = line.split(':')[0].strip()
                param_desc = line.split(':')[1].strip() if ':' in line else ""
                params.append({"name": param_name, "description": param_desc})
    
    return {
        "name": name,
        "description": description,
        "full_doc": doc.strip(),
        "parameters": params
    }
