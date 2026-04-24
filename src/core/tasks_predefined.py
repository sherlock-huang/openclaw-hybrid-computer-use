"""预定义任务集合"""

from typing import Dict, List, Any
from .models import Task, TaskSequence
from .selectors_config import build_multi_selector, get_generic_selector
from ..utils.exceptions import NotFoundError


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
        raise NotFoundError(f"未知的预定义任务: {name}. 可用任务: {available}")
    
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


# ==================== 新增预置任务 ====================

def create_bilibili_search_task(keyword: str = "Python") -> TaskSequence:
    """
    B站搜索任务
    
    在Bilibili上搜索指定关键词的视频
    
    Args:
        keyword: 搜索关键词（如 "Python教程"）
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name=f"bilibili_search_{keyword}",
        tasks=[
            Task("browser_launch", value="chromium", delay=2.0),
            Task("browser_goto", value="https://www.bilibili.com", delay=5.0),
            Task("browser_click", target=".search-input, input[placeholder*='搜索'], .nav-search-input", delay=1.0),
            Task("browser_type", target=".search-input, input[placeholder*='搜索'], .nav-search-input", value=keyword, delay=0.5),
            Task("browser_press", value="Enter", delay=3.0),
            Task("browser_wait", target=".video-list-item, .card-list .card, .video-item", value="visible", delay=2.0),
            Task("browser_scroll", value="600", delay=1.0),
            Task("browser_screenshot", value=f"bilibili_search_{keyword}.png", delay=1.0),
        ],
        max_retries=2
    )


def create_weibo_hot_search_task() -> TaskSequence:
    """
    微博热搜查看任务
    
    打开微博并查看当前热搜榜单
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="weibo_hot_search",
        tasks=[
            Task("browser_launch", value="chromium", delay=2.0),
            Task("browser_goto", value="https://weibo.com/hot/search", delay=5.0),
            Task("browser_wait", target="[class*='hot'], [class*='rank'], .list", value="visible", delay=3.0),
            Task("browser_scroll", value="800", delay=1.0),
            Task("browser_screenshot", value="weibo_hot.png", delay=1.0),
        ],
        max_retries=2
    )


def create_zhihu_search_task(keyword: str = "人工智能") -> TaskSequence:
    """
    知乎搜索任务
    
    在知乎上搜索指定话题
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name=f"zhihu_search_{keyword}",
        tasks=[
            Task("browser_launch", value="chromium", delay=2.0),
            Task("browser_goto", value="https://www.zhihu.com", delay=5.0),
            Task("browser_click", target="input[placeholder*='搜索'], .SearchBar-input, #q", delay=1.0),
            Task("browser_type", target="input[placeholder*='搜索'], .SearchBar-input, #q", value=keyword, delay=0.5),
            Task("browser_press", value="Enter", delay=3.0),
            Task("browser_wait", target=".ContentItem, .SearchResult-Card, [class*='result']", value="visible", delay=2.0),
            Task("browser_scroll", value="500", delay=1.0),
            Task("browser_screenshot", value=f"zhihu_search_{keyword}.png", delay=1.0),
        ],
        max_retries=2
    )


def create_open_qq_task() -> TaskSequence:
    """
    打开QQ任务
    
    启动QQ应用程序
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_qq",
        tasks=[
            Task("launch", target="qq"),
            Task("wait", delay=3.0),
        ],
        max_retries=2
    )


def create_open_dingtalk_task() -> TaskSequence:
    """
    打开钉钉任务
    
    启动钉钉应用程序
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_dingtalk",
        tasks=[
            Task("launch", target="dingtalk"),
            Task("wait", delay=3.0),
        ],
        max_retries=2
    )


def create_screenshot_to_desktop_task(filename: str = "screenshot") -> TaskSequence:
    """
    截图保存到桌面任务
    
    截取当前屏幕并保存到桌面
    
    Args:
        filename: 保存的文件名（不含扩展名）
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name=f"screenshot_{filename}",
        tasks=[
            Task("hotkey", value="win+d", delay=1.0),
            Task("wait", delay=0.5),
            Task("hotkey", value="print", delay=0.5),
            Task("wait", delay=1.0),
        ],
        max_retries=1
    )


def create_new_text_file_task(filename: str = "新建文本", content: str = "") -> TaskSequence:
    """
    创建文本文件任务
    
    在桌面创建一个新的文本文件
    
    Args:
        filename: 文件名（不含扩展名）
        content: 文件内容
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name=f"new_text_file_{filename}",
        tasks=[
            Task("hotkey", value="win+d", delay=1.0),
            Task("right_click", target="960,540", delay=0.5),
            Task("click", target="新建", delay=0.3),
            Task("click", target="文本文档", delay=0.5),
            Task("type", value=filename),
            Task("press", value="enter", delay=0.5),
        ] + ([
            Task("type", value=content),
        ] if content else []) + [
            Task("hotkey", value="ctrl+s", delay=0.5),
        ],
        max_retries=2
    )


def create_open_cmd_task() -> TaskSequence:
    """
    打开命令提示符任务
    
    启动CMD命令提示符
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_cmd",
        tasks=[
            Task("hotkey", value="win+r", delay=0.5),
            Task("type", value="cmd"),
            Task("press", value="enter", delay=1.0),
        ],
        max_retries=2
    )


def create_system_info_task() -> TaskSequence:
    """
    查看系统信息任务
    
    打开系统设置查看基本信息
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="system_info",
        tasks=[
            Task("hotkey", value="win+i", delay=2.0),
            Task("wait", delay=1.0),
        ],
        max_retries=2
    )


# 更新任务注册表
PREDEFINED_TASKS.update({
    # 新增浏览器任务
    "bilibili_search": create_bilibili_search_task,
    "weibo_hot": create_weibo_hot_search_task,
    "zhihu_search": create_zhihu_search_task,
    # 新增桌面任务
    "open_qq": create_open_qq_task,
    "open_dingtalk": create_open_dingtalk_task,
    "screenshot_desktop": create_screenshot_to_desktop_task,
    "new_text_file": create_new_text_file_task,
    "open_cmd": create_open_cmd_task,
    "system_info": create_system_info_task,
})


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
        raise NotFoundError(f"未知的预定义任务: {name}. 可用任务: {available}")
    
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
            if ':' in line:
                param_name = line.split(':')[0].strip()
                param_desc = line.split(':')[1].strip() if ':' in line else ""
                # 只提取看起来像是参数的行
                if param_name and not param_name.startswith(('http', 'https', '如', '例如')):
                    params.append({"name": param_name, "description": param_desc})
    
    return {
        "name": name,
        "description": description,
        "full_doc": doc.strip(),
        "parameters": params
    }


def create_wechat_send_message_task(contact: str = "", message: str = "Hello") -> TaskSequence:
    """
    微信发送消息任务
    
    在微信桌面版中搜索指定联系人/群聊并发送消息。
    需要微信已登录且窗口可见。
    
    Args:
        contact: 联系人或群聊名称（如 "张三"、"工作群"）
        message: 要发送的消息内容
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name=f"wechat_send_{contact}",
        tasks=[
            Task("wechat_send", target=contact, value=message, delay=2.0),
        ],
        max_retries=1
    )


# 注册微信发送消息任务
PREDEFINED_TASKS["wechat_send"] = create_wechat_send_message_task

# ==================== Office 自动化任务 ====================

def create_excel_report_task(
    filepath: str = "report.xlsx",
    sheet_name: str = "Sheet1",
    headers: str = "Name,Value",
    data_json: str = "[[\"A\",1],[\"B\",2]]",
    chart_title: str = "Chart",
) -> TaskSequence:
    """
    创建 Excel 报告任务
    
    创建包含表头、数据和图表的 Excel 文件。
    
    Args:
        filepath: 输出文件路径
        sheet_name: 工作表名称
        headers: 表头，逗号分隔
        data_json: 数据，JSON 二维数组字符串
        chart_title: 图表标题
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="excel_report",
        tasks=[
            Task("excel_create", value=filepath, delay=0.5),
            Task("excel_write_cell", target=f"{sheet_name}!A1", value=headers.split(",")[0] if "," in headers else headers, delay=0.2),
            Task("excel_write_cell", target=f"{sheet_name}!B1", value=headers.split(",")[1] if "," in headers else "", delay=0.2),
            Task("excel_write_range", target="A2", value=data_json, delay=0.3),
            Task("excel_chart", value='{"type":"bar","data_range":"A1:B5","title":"' + chart_title + '"}', delay=0.5),
            Task("excel_save", value=filepath, delay=0.5),
        ],
        max_retries=1
    )


def create_excel_write_data_task(
    filepath: str = "data.xlsx",
    start_cell: str = "A1",
    data_json: str = "[[1,2],[3,4]]",
) -> TaskSequence:
    """
    写入 Excel 数据任务
    
    打开或创建 Excel 文件并写入二维数据。
    
    Args:
        filepath: Excel 文件路径
        start_cell: 起始单元格
        data_json: JSON 二维数组字符串
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="excel_write_data",
        tasks=[
            Task("excel_create", value=filepath, delay=0.5),
            Task("excel_write_range", target=start_cell, value=data_json, delay=0.3),
            Task("excel_save", value=filepath, delay=0.5),
        ],
        max_retries=1
    )


def create_word_document_task(
    filepath: str = "document.docx",
    title: str = "Document",
    paragraphs_json: str = '["Paragraph 1","Paragraph 2"]',
) -> TaskSequence:
    """
    创建 Word 文档任务
    
    创建包含标题和段落的 Word 文档。
    
    Args:
        filepath: 输出文件路径
        title: 文档标题
        paragraphs_json: 段落内容，JSON 字符串列表
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="word_document",
        tasks=[
            Task("word_create", value=filepath, delay=0.5),
            Task("word_heading", target="1", value=title, delay=0.2),
            Task("word_write", value=paragraphs_json, delay=0.3),
            Task("word_save", value=filepath, delay=0.5),
        ],
        max_retries=1
    )


def create_word_template_fill_task(
    template_path: str = "template.docx",
    output_path: str = "output.docx",
    mapping_json: str = '{"{{NAME}}":"张三","{{DATE}}":"2026-04-19"}',
) -> TaskSequence:
    """
    填充 Word 模板任务
    
    打开 Word 模板文件，批量替换占位符，保存为新文件。
    
    Args:
        template_path: 模板文件路径
        output_path: 输出文件路径
        mapping_json: 占位符映射，JSON 字典字符串
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="word_template_fill",
        tasks=[
            Task("word_open", value=template_path, delay=0.5),
            Task("word_fill", value=mapping_json, delay=0.3),
            Task("word_save", value=output_path, delay=0.5),
        ],
        max_retries=1
    )


# 注册 Office 自动化任务
PREDEFINED_TASKS.update({
    "excel_report": create_excel_report_task,
    "excel_write_data": create_excel_write_data_task,
    "word_document": create_word_document_task,
    "word_template_fill": create_word_template_fill_task,
})

# ==================== 通用工具任务 ====================

def create_file_copy_task(src: str = "", dst: str = "") -> TaskSequence:
    """
    复制文件任务
    
    Args:
        src: 源文件路径
        dst: 目标路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="file_copy",
        tasks=[
            Task("file_copy", target=src, value=dst, delay=0.3),
        ],
        max_retries=1
    )


def create_file_move_task(src: str = "", dst: str = "") -> TaskSequence:
    """
    移动文件任务
    
    Args:
        src: 源文件路径
        dst: 目标路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="file_move",
        tasks=[
            Task("file_move", target=src, value=dst, delay=0.3),
        ],
        max_retries=1
    )


def create_file_delete_task(path: str = "") -> TaskSequence:
    """
    删除文件或文件夹任务
    
    Args:
        path: 要删除的路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="file_delete",
        tasks=[
            Task("file_delete", target=path, delay=0.3),
        ],
        max_retries=1
    )


def create_folder_create_task(path: str = "") -> TaskSequence:
    """
    创建文件夹任务
    
    Args:
        path: 文件夹路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="folder_create",
        tasks=[
            Task("folder_create", target=path, delay=0.3),
        ],
        max_retries=1
    )


def create_shell_command_task(command: str = "echo Hello") -> TaskSequence:
    """
    执行 Shell 命令任务
    
    Args:
        command: 要执行的命令
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="shell_command",
        tasks=[
            Task("shell", value=command, delay=0.5),
        ],
        max_retries=1
    )


def create_system_lock_task() -> TaskSequence:
    """
    锁定屏幕任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="system_lock",
        tasks=[
            Task("system_lock", delay=0.5),
        ],
        max_retries=1
    )


def create_screenshot_save_task(filepath: str = "screenshot.png") -> TaskSequence:
    """
    截图保存任务
    
    Args:
        filepath: 保存路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="screenshot_save",
        tasks=[
            Task("screenshot_save", value=filepath, delay=0.5),
        ],
        max_retries=1
    )


def create_open_outlook_task() -> TaskSequence:
    """
    打开 Outlook 任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_outlook",
        tasks=[
            Task("launch", target="outlook", delay=3.0),
        ],
        max_retries=1
    )


def create_open_settings_task() -> TaskSequence:
    """
    打开系统设置任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_settings",
        tasks=[
            Task("launch", target="ms-settings:", delay=2.0),
        ],
        max_retries=1
    )


def create_open_task_manager_task() -> TaskSequence:
    """
    打开任务管理器任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="open_task_manager",
        tasks=[
            Task("hotkey", value="ctrl+shift+esc", delay=1.5),
        ],
        max_retries=1
    )


def create_copy_to_clipboard_task(text: str = "Hello") -> TaskSequence:
    """
    复制文本到剪贴板任务
    
    Args:
        text: 要复制的文本
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="copy_to_clipboard",
        tasks=[
            Task("clipboard_copy", value=text, delay=0.3),
        ],
        max_retries=1
    )


def create_browser_download_task(url: str = "") -> TaskSequence:
    """
    浏览器下载文件任务
    
    Args:
        url: 下载链接
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="browser_download",
        tasks=[
            Task("browser_launch", value="chromium", delay=2.0),
            Task("browser_goto", value=url, delay=5.0),
            Task("browser_wait", target="body", value="visible", delay=3.0),
        ],
        max_retries=1
    )


def create_excel_read_data_task(filepath: str = "data.xlsx", cell: str = "A1") -> TaskSequence:
    """
    读取 Excel 单元格任务
    
    Args:
        filepath: Excel 文件路径
        cell: 单元格地址
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="excel_read_data",
        tasks=[
            Task("excel_open", value=filepath, delay=0.5),
            Task("excel_read_cell", target=cell, delay=0.3),
        ],
        max_retries=1
    )


def create_word_open_read_task(filepath: str = "document.docx") -> TaskSequence:
    """
    打开 Word 文档任务
    
    Args:
        filepath: Word 文件路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="word_open_read",
        tasks=[
            Task("word_open", value=filepath, delay=0.5),
        ],
        max_retries=1
    )


def create_run_python_script_task(script_path: str = "") -> TaskSequence:
    """
    运行 Python 脚本任务
    
    Args:
        script_path: Python 脚本路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="run_python_script",
        tasks=[
            Task("shell", value=f"py {script_path}", delay=1.0),
        ],
        max_retries=1
    )


def create_shutdown_system_task() -> TaskSequence:
    """
    关机任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="shutdown_system",
        tasks=[
            Task("shell", value="shutdown /s /t 60", delay=0.5),
        ],
        max_retries=1
    )


def create_restart_system_task() -> TaskSequence:
    """
    重启任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="restart_system",
        tasks=[
            Task("shell", value="shutdown /r /t 60", delay=0.5),
        ],
        max_retries=1
    )


def create_project_folder_task(base_path: str = "./new_project") -> TaskSequence:
    """
    创建项目文件夹结构任务
    
    Args:
        base_path: 项目根目录
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="project_folder",
        tasks=[
            Task("folder_create", target=f"{base_path}/src", delay=0.2),
            Task("folder_create", target=f"{base_path}/docs", delay=0.2),
            Task("folder_create", target=f"{base_path}/tests", delay=0.2),
            Task("folder_create", target=f"{base_path}/assets", delay=0.2),
        ],
        max_retries=1
    )


def create_notepad_with_text_task(text: str = "Hello World", filename: str = "note") -> TaskSequence:
    """
    打开记事本并输入文本任务
    
    Args:
        text: 要输入的文本
        filename: 保存文件名
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="notepad_with_text",
        tasks=[
            Task("launch", target="notepad", delay=1.5),
            Task("type", value=text, delay=0.5),
            Task("hotkey", value="ctrl+s", delay=0.5),
            Task("type", value=filename, delay=0.3),
            Task("press", value="enter", delay=0.3),
        ],
        max_retries=2
    )


# 注册通用工具任务
PREDEFINED_TASKS.update({
    "file_copy": create_file_copy_task,
    "file_move": create_file_move_task,
    "file_delete": create_file_delete_task,
    "folder_create": create_folder_create_task,
    "shell_command": create_shell_command_task,
    "system_lock": create_system_lock_task,
    "screenshot_save": create_screenshot_save_task,
    "open_outlook": create_open_outlook_task,
    "open_settings": create_open_settings_task,
    "open_task_manager": create_open_task_manager_task,
    "copy_to_clipboard": create_copy_to_clipboard_task,
    "browser_download": create_browser_download_task,
    "excel_read_data": create_excel_read_data_task,
    "word_open_read": create_word_open_read_task,
    "run_python_script": create_run_python_script_task,
    "shutdown_system": create_shutdown_system_task,
    "restart_system": create_restart_system_task,
    "project_folder": create_project_folder_task,
    "notepad_with_text": create_notepad_with_text_task,
})

# ==================== 智能定位任务 ====================

def create_locate_and_click_image_task(template_path: str = "") -> TaskSequence:
    """
    定位图像并点击任务
    
    在屏幕上查找模板图像并点击。
    
    Args:
        template_path: 模板图像路径
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="locate_and_click_image",
        tasks=[
            Task("locate_image", target=template_path, delay=0.5),
            Task("click_relative", target="last_located", value="{}", delay=0.3),
        ],
        max_retries=2
    )


def create_locate_and_click_text_task(text: str = "") -> TaskSequence:
    """
    定位文字并点击任务
    
    通过 OCR 查找指定文字并点击。
    
    Args:
        text: 目标文字
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="locate_and_click_text",
        tasks=[
            Task("locate_text", target=text, delay=0.5),
            Task("click_relative", target="last_located", value="{}", delay=0.3),
        ],
        max_retries=2
    )


def create_wait_and_click_image_task(template_path: str = "", timeout: str = "10") -> TaskSequence:
    """
    等待图像出现并点击任务
    
    Args:
        template_path: 模板图像路径
        timeout: 等待超时（秒）
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="wait_and_click_image",
        tasks=[
            Task("wait_for_image", target=template_path, value=timeout, delay=0.5),
            Task("click_relative", target="last_located", value="{}", delay=0.3),
        ],
        max_retries=1
    )


def create_wait_and_click_text_task(text: str = "", timeout: str = "10") -> TaskSequence:
    """
    等待文字出现并点击任务
    
    Args:
        text: 目标文字
        timeout: 等待超时（秒）
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="wait_and_click_text",
        tasks=[
            Task("wait_for_text", target=text, value=timeout, delay=0.5),
            Task("click_relative", target="last_located", value="{}", delay=0.3),
        ],
        max_retries=1
    )


def create_click_below_text_task(reference: str = "", target: str = "", direction: str = "below") -> TaskSequence:
    """
    关系链定位点击任务
    
    基于参考文字找到目标文字并点击（如 "在'用户名'下方的输入框"）。
    
    Args:
        reference: 参考文字
        target: 目标文字
        direction: 相对方向 (below, above, left, right, nearest)
        
    Returns:
        任务序列
    """
    import json
    cfg = json.dumps({"target_text": target, "direction": direction})
    return TaskSequence(
        name="click_below_text",
        tasks=[
            Task("locate_relation", target=reference, value=cfg, delay=0.5),
            Task("click_relative", target="last_located", value="{}", delay=0.3),
        ],
        max_retries=2
    )


# 注册智能定位任务
PREDEFINED_TASKS.update({
    "locate_and_click_image": create_locate_and_click_image_task,
    "locate_and_click_text": create_locate_and_click_text_task,
    "wait_and_click_image": create_wait_and_click_image_task,
    "wait_and_click_text": create_wait_and_click_text_task,
    "click_below_text": create_click_below_text_task,
})

# ==================== 插件系统任务 ====================

def create_plugin_db_create_table_task(db_path: str = "data.db", table_sql: str = "") -> TaskSequence:
    """
    插件：创建数据库表任务
    
    使用 database 插件创建 SQLite 数据库和表。
    
    Args:
        db_path: 数据库文件路径
        table_sql: 建表 SQL 语句
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="plugin_db_create_table",
        tasks=[
            Task("plugin_invoke", target="database.connect", value=db_path, delay=0.3),
            Task("plugin_invoke", target="database.execute", value=table_sql, delay=0.3),
        ],
        max_retries=1
    )


def create_plugin_db_insert_task(db_path: str = "data.db", sql: str = "") -> TaskSequence:
    """
    插件：插入数据任务
    
    Args:
        db_path: 数据库文件路径
        sql: INSERT SQL 语句
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="plugin_db_insert",
        tasks=[
            Task("plugin_invoke", target="database.connect", value=db_path, delay=0.3),
            Task("plugin_invoke", target="database.execute", value=sql, delay=0.3),
        ],
        max_retries=1
    )


def create_plugin_db_query_task(db_path: str = "data.db", sql: str = "SELECT 1") -> TaskSequence:
    """
    插件：查询数据任务
    
    Args:
        db_path: 数据库文件路径
        sql: SELECT SQL 语句
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="plugin_db_query",
        tasks=[
            Task("plugin_invoke", target="database.connect", value=db_path, delay=0.3),
            Task("plugin_invoke", target="database.query", value=sql, delay=0.3),
        ],
        max_retries=1
    )


def create_plugin_api_get_task(url: str = "https://httpbin.org/get") -> TaskSequence:
    """
    插件：API GET 请求任务
    
    Args:
        url: 请求 URL
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="plugin_api_get",
        tasks=[
            Task("plugin_invoke", target="api.get", value=url, delay=1.0),
        ],
        max_retries=1
    )


def create_plugin_api_post_task(url: str = "https://httpbin.org/post", json_body: str = "{}") -> TaskSequence:
    """
    插件：API POST 请求任务
    
    Args:
        url: 请求 URL
        json_body: JSON 请求体
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="plugin_api_post",
        tasks=[
            Task("plugin_invoke", target="api.post", value=json_body, delay=1.0),
        ],
        max_retries=1
    )


def create_plugin_list_task() -> TaskSequence:
    """
    列出所有已加载插件任务
    
    Returns:
        任务序列
    """
    return TaskSequence(
        name="plugin_list",
        tasks=[
            Task("plugin_list", delay=0.5),
        ],
        max_retries=1
    )


# 注册插件系统任务
PREDEFINED_TASKS.update({
    "plugin_db_create_table": create_plugin_db_create_table_task,
    "plugin_db_insert": create_plugin_db_insert_task,
    "plugin_db_query": create_plugin_db_query_task,
    "plugin_api_get": create_plugin_api_get_task,
    "plugin_api_post": create_plugin_api_post_task,
    "plugin_list": create_plugin_list_task,
})

# ==================== 本地 VLM 任务 ====================

def create_local_vlm_analyze_task(instruction: str = "分析当前屏幕") -> TaskSequence:
    """
    本地 VLM 屏幕分析任务
    
    使用本地视觉语言模型分析屏幕截图并返回操作建议。
    需要已安装 transformers 和对应模型。
    
    Args:
        instruction: 用户指令
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="local_vlm_analyze",
        tasks=[
            Task("desktop_screenshot", delay=0.5),
            Task("vlm_analyze", target=instruction, value="local", delay=5.0),
        ],
        max_retries=1
    )


# 注册本地 VLM 任务
PREDEFINED_TASKS["local_vlm_analyze"] = create_local_vlm_analyze_task
