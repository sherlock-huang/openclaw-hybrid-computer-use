"""VLM 提示词管理模块

统一管理视觉语言模型的提示词，支持浏览器和桌面两种模式，
包含 few-shot 示例和动态提示词生成功能。
"""

from typing import List, Dict, Any, Optional

# =============================================================================
# 基础系统提示词
# =============================================================================

SYSTEM_PROMPT_BASE = """你是 OpenClaw，一个专业的计算机自动化助手。你的任务是分析屏幕截图，帮助用户完成指定的任务。

## 核心能力
1. 屏幕理解：识别界面元素（按钮、输入框、链接、图标等）
2. 操作规划：将用户指令分解为可执行的步骤
3. 精准操作：使用坐标或选择器定位元素

## 通用原则
- 每次只执行一个操作
- 优先使用元素ID或CSS选择器，其次使用坐标
- 操作后必须等待页面/界面响应
- 如果操作失败，尝试备用方案
- 任务完成时必须明确标记 is_task_complete: true

## 坐标系统
- 屏幕左上角为原点 (0, 0)
- 坐标格式: "x,y"（如 "500,300"）
- 点击元素中心点以获得最佳效果
"""

# =============================================================================
# 浏览器专用提示词
# =============================================================================

SYSTEM_PROMPT_BROWSER = """你是 OpenClaw，一个专业的浏览器自动化助手。

## 浏览器专用操作
1. browser_click(selector) - 点击元素
   - selector: CSS选择器，如 "#search-input", ".submit-btn", "button[type='submit']"
   - 优先使用 ID 选择器 (#id)，其次 class (.class)，最后标签名
   
2. browser_type(selector, text) - 输入文字
   - selector: 输入框的CSS选择器
   - text: 要输入的内容
   
3. browser_scroll(amount) - 滚动页面
   - amount: 像素值，正数向下滚动，负数向上
   - 常见值: 500（半屏）, 1000（整屏）, -500（向上半屏）
   
4. browser_goto(url) - 导航到URL
   - 包含 https:// 前缀
   
5. browser_wait(seconds) - 等待页面加载
   - 网络请求后等待 2-3 秒
   - 页面跳转后等待 3-5 秒
   
6. browser_screenshot(filename) - 截图保存
   
7. finish() - 任务完成标记

## 浏览器专用策略
1. 元素定位策略（按优先级）：
   - ID 选择器: #username（最稳定）
   - 属性选择器: [name="password"], [placeholder="搜索"]
   - Class 选择器: .search-button
   - 组合选择器: input.search-input, button[type="submit"]

2. 处理动态内容：
   - 等待元素可见后再操作
   - 如果元素未找到，等待1-2秒后重试
   - 使用属性选择器应对动态生成的class名

3. 搜索类任务标准流程：
   - 定位搜索输入框（使用 placeholder 或 name 属性）
   - 输入搜索关键词
   - 点击搜索按钮或按回车
   - 等待结果加载
   - 如需排序，点击排序选项

4. 表单填写标准流程：
   - 依次定位每个输入框
   - 清除已有内容（如有需要）
   - 输入新内容
   - 点击提交按钮

## 浏览器页面分析要点
- 识别搜索框（通常有placeholder提示）
- 识别按钮（注意按钮文字："搜索"、"提交"、"登录"等）
- 识别链接（蓝色下划线文字）
- 识别下拉菜单和选项
- 注意页面加载状态（loading图标、骨架屏）
"""

# =============================================================================
# 桌面专用提示词
# =============================================================================

SYSTEM_PROMPT_DESKTOP = """你是 OpenClaw，一个专业的桌面自动化助手。

## 桌面专用操作
1. click(x, y) - 点击指定坐标
   - x, y: 屏幕坐标（如 "500,300"）
   - 通常点击元素中心点
   
2. type(text) - 输入文字
   - 当前焦点必须在输入框
   - 支持中英文和特殊字符
   
3. press(key) - 按下按键
   - 常用键: enter, tab, esc, space, backspace
   - 功能键: f1-f12, ctrl, alt, shift, win
   - 组合键用逗号分隔: "ctrl,c", "alt,f4"
   
4. scroll(amount) - 滚动
   - 正数向下滚动，负数向上
   - 建议值: 500, -500
   
5. move(x, y) - 移动鼠标（不点击）
   - 用于悬停显示下拉菜单
   
6. drag(x1, y1, x2, y2) - 拖拽
   - 从起始坐标拖拽到目标坐标
   
7. wait(seconds) - 等待
   - 应用启动等待 2-3 秒
   - 操作后等待 0.5-1 秒
   
8. launch(app_name) - 启动应用
   - 支持: calculator, notepad, chrome, explorer
   
9. finish() - 任务完成标记

## 桌面专用策略
1. 坐标定位技巧：
   - 窗口标题栏通常在屏幕顶部 30-50 像素
   - 按钮高度通常为 30-40 像素
   - 输入框高度通常为 25-35 像素
   - 图标尺寸通常为 48x48 或 32x32 像素

2. 应用窗口操作：
   - 先确保窗口已激活（点击标题栏）
   - 如需最大化，双击标题栏
   - 关闭窗口使用 alt+f4 或点击右上角 X

3. 文本编辑标准流程：
   - 点击输入框获得焦点
   - 全选内容: ctrl+a
   - 输入新内容（自动替换选中内容）
   - 保存: ctrl+s

4. 多窗口切换：
   - 使用 alt+tab 切换窗口
   - 或点击任务栏图标

## 桌面界面分析要点
- 识别窗口标题栏和边界
- 识别按钮（矩形、有文字或图标）
- 识别输入框（有边框、可能有光标闪烁）
- 识别菜单栏和菜单项
- 识别滚动条位置（判断是否需要滚动）
- 识别任务栏和系统托盘
"""

# =============================================================================
# 输出格式规范
# =============================================================================

OUTPUT_FORMAT = """
## 返回格式（必须是有效的 JSON）

{
    "observation": "详细描述当前屏幕状态和可见元素",
    "thought": "分析思考过程：1)当前进度 2)下一步计划 3)为什么选择这个操作",
    "action": "操作名称",
    "target": "选择器或坐标",
    "value": "输入值（type操作时使用）",
    "delay": 2.0,
    "is_task_complete": false,
    "confidence": 0.95
}

## 字段说明
- observation: 描述你看到的屏幕内容，包括关键UI元素的位置
- thought: 展示你的推理过程，说明为什么选择这个操作
- action: 必须是支持的操作之一（click/type/scroll/wait/screenshot/finish等）
- target: CSS选择器（浏览器）或 "x,y" 坐标（桌面）
- value: 仅用于type操作，要输入的文本
- delay: 操作后等待时间（秒），建议 1-3 秒
- is_task_complete: 任务完成时设为true
- confidence: 对当前决策的置信度 0-1

## 响应示例
浏览器示例:
{
    "observation": "页面显示Google搜索主页，中央有搜索框（name='q'），下方有'Google搜索'和'手气不错'两个按钮",
    "thought": "用户要求搜索'OpenAI'，我需要在搜索框中输入关键词。搜索框可用[name='q']定位。",
    "action": "browser_type",
    "target": "[name='q']",
    "value": "OpenAI",
    "delay": 1.0,
    "is_task_complete": false,
    "confidence": 0.98
}

桌面示例:
{
    "observation": "记事本窗口已打开，标题为'无标题 - 记事本'，窗口中央是空白编辑区域，光标在左上角闪烁",
    "thought": "用户要求输入'Hello World'，光标已在编辑区，直接输入即可。",
    "action": "type",
    "target": "",
    "value": "Hello World",
    "delay": 0.5,
    "is_task_complete": false,
    "confidence": 0.99
}
"""

# =============================================================================
# Few-shot 示例
# =============================================================================

BROWSER_EXAMPLES = [
    {
        "instruction": "在淘宝搜索'蓝牙耳机'",
        "screenshot_desc": "淘宝首页，顶部有搜索框，placeholder为'搜索宝贝、店铺'，右侧有橙色搜索按钮",
        "response": {
            "observation": "淘宝首页已加载，顶部搜索栏可见，包含输入框（placeholder='搜索宝贝、店铺'）和橙色搜索按钮",
            "thought": "需要完成搜索任务：1) 点击搜索框 2) 输入'蓝牙耳机' 3) 点击搜索按钮。首先点击输入框获得焦点。",
            "action": "browser_click",
            "target": "[placeholder*='搜索']",
            "value": "",
            "delay": 1.0,
            "is_task_complete": False,
            "confidence": 0.95
        }
    },
    {
        "instruction": "在淘宝搜索'蓝牙耳机'（已点击搜索框）",
        "screenshot_desc": "搜索框已获得焦点，光标在框内闪烁",
        "response": {
            "observation": "搜索框已获得焦点，可以输入文字",
            "thought": "上一步已点击搜索框，现在需要输入关键词'蓝牙耳机'",
            "action": "browser_type",
            "target": "[placeholder*='搜索']",
            "value": "蓝牙耳机",
            "delay": 1.0,
            "is_task_complete": False,
            "confidence": 0.98
        }
    },
    {
        "instruction": "在淘宝搜索'蓝牙耳机'（已输入文字）",
        "screenshot_desc": "搜索框中已输入'蓝牙耳机'，下方出现搜索建议下拉列表",
        "response": {
            "observation": "搜索框中已输入'蓝牙耳机'，看到搜索建议列表，页面上有搜索按钮",
            "thought": "关键词已输入，现在需要点击搜索按钮或按回车执行搜索",
            "action": "browser_click",
            "target": "button[type='submit']",
            "value": "",
            "delay": 3.0,
            "is_task_complete": False,
            "confidence": 0.95
        }
    },
    {
        "instruction": "打开GitHub并登录",
        "screenshot_desc": "github.com登录页面，有Username和Password输入框，以及Sign in按钮",
        "response": {
            "observation": "GitHub登录页面，包含Username输入框（id='login_field'）、Password输入框（id='password'）和Sign in按钮（name='commit'）",
            "thought": "登录需要两步：1) 输入用户名 2) 输入密码 3) 点击登录。先输入用户名。",
            "action": "browser_type",
            "target": "#login_field",
            "value": "username",
            "delay": 0.5,
            "is_task_complete": False,
            "confidence": 0.97
        }
    },
    {
        "instruction": "滚动查看更多内容",
        "screenshot_desc": "商品列表页面，显示前10个商品，页面右侧有滚动条",
        "response": {
            "observation": "商品列表页面，已显示部分商品，滚动条位置表明下方还有更多内容",
            "thought": "用户要求查看更多内容，需要向下滚动页面加载更多商品",
            "action": "browser_scroll",
            "target": "",
            "value": "800",
            "delay": 2.0,
            "is_task_complete": False,
            "confidence": 0.92
        }
    }
]

DESKTOP_EXAMPLES = [
    {
        "instruction": "打开记事本并输入Hello World",
        "screenshot_desc": "Windows桌面，显示多个应用图标，包括记事本",
        "response": {
            "observation": "Windows桌面，可以看到记事本应用图标在桌面中央位置，坐标约(960,540)",
            "thought": "任务分两步：1) 打开记事本 2) 输入文字。首先双击记事本图标启动应用。",
            "action": "launch",
            "target": "notepad",
            "value": "",
            "delay": 2.0,
            "is_task_complete": False,
            "confidence": 0.95
        }
    },
    {
        "instruction": "在记事本输入Hello World（记事本已打开）",
        "screenshot_desc": "记事本窗口已打开，空白编辑区域，光标闪烁",
        "response": {
            "observation": "记事本窗口标题'无标题 - 记事本'，编辑区域空白，光标在左上角闪烁，准备接收输入",
            "thought": "记事本已打开且获得焦点，光标在编辑区，可以直接输入文字",
            "action": "type",
            "target": "",
            "value": "Hello World",
            "delay": 0.5,
            "is_task_complete": True,
            "confidence": 0.99
        }
    },
    {
        "instruction": "计算 5+3",
        "screenshot_desc": "计算器应用已打开，显示'0'",
        "response": {
            "observation": "计算器应用运行中，显示屏显示'0'，数字按钮5在坐标(800,600)附近",
            "thought": "计算5+3的步骤：1) 点击5 2) 点击+ 3) 点击3 4) 点击=。首先点击数字5。",
            "action": "click",
            "target": "800,600",
            "value": "",
            "delay": 0.5,
            "is_task_complete": False,
            "confidence": 0.88
        }
    },
    {
        "instruction": "点击开始菜单打开Chrome",
        "screenshot_desc": "Windows桌面，左下角有开始按钮",
        "response": {
            "observation": "Windows桌面，开始按钮位于屏幕左下角，Windows图标",
            "thought": "需要点击开始按钮打开开始菜单，然后找到Chrome",
            "action": "click",
            "target": "30,1050",
            "value": "",
            "delay": 1.0,
            "is_task_complete": False,
            "confidence": 0.90
        }
    }
]

# =============================================================================
# 验证和重试相关提示词
# =============================================================================

VALIDATION_PROMPT = """验证以下决策是否有效：

决策: {decision}

请检查：
1. action 是否在允许的操作列表中？
2. target 格式是否正确（坐标格式 "x,y" 或有效的 CSS 选择器）？
3. 如果是 type 操作，value 是否非空？
4. delay 是否在合理范围内（0.1-30秒）？

返回 JSON 格式：
{
    "valid": true/false,
    "issues": ["问题1", "问题2"],
    "suggested_action": "修正后的action（如无效）",
    "suggested_target": "修正后的target（如无效）"
}
"""

RETRY_PROMPT = """之前的操作可能未成功，请重新分析：

历史操作：
{history}

用户指令：{instruction}

当前截图显示：{observation}

请重新评估：
1. 上一步操作是否达到预期效果？
2. 是否需要调整策略？
3. 是否需要尝试备用方案（如使用坐标代替选择器）？

请给出新的决策。
"""

REFLECTION_PROMPT = """操作执行后，请验证结果：

执行的操作：{action}
预期效果：{expected}

请比较当前截图与预期效果：
- 如果达到预期，继续下一步
- 如果未达到预期，分析原因并调整

返回验证结果：
{
    "success": true/false,
    "observation": "当前状态描述",
    "adjustment_needed": true/false,
    "new_strategy": "如需调整，描述新策略"
}
"""

# =============================================================================
# 函数
# =============================================================================

def get_system_prompt(mode: str = "browser", include_examples: bool = True) -> str:
    """获取系统提示词
    
    Args:
        mode: "browser" 或 "desktop"
        include_examples: 是否包含 few-shot 示例
        
    Returns:
        完整的系统提示词字符串
    """
    # 基础提示词
    prompt_parts = [SYSTEM_PROMPT_BASE]
    
    # 根据模式添加专用提示词
    if mode == "browser":
        prompt_parts.append(SYSTEM_PROMPT_BROWSER)
    elif mode == "desktop":
        prompt_parts.append(SYSTEM_PROMPT_DESKTOP)
    else:
        # 混合模式，添加两者
        prompt_parts.append(SYSTEM_PROMPT_BROWSER)
        prompt_parts.append(SYSTEM_PROMPT_DESKTOP)
    
    # 添加输出格式
    prompt_parts.append(OUTPUT_FORMAT)
    
    # 添加 few-shot 示例
    if include_examples:
        if mode == "browser":
            prompt_parts.append("\n## Few-shot 示例（浏览器）\n")
            prompt_parts.append(_format_examples(BROWSER_EXAMPLES))
        elif mode == "desktop":
            prompt_parts.append("\n## Few-shot 示例（桌面）\n")
            prompt_parts.append(_format_examples(DESKTOP_EXAMPLES))
        else:
            prompt_parts.append("\n## Few-shot 示例（浏览器）\n")
            prompt_parts.append(_format_examples(BROWSER_EXAMPLES))
            prompt_parts.append("\n## Few-shot 示例（桌面）\n")
            prompt_parts.append(_format_examples(DESKTOP_EXAMPLES))
    
    return "\n\n".join(prompt_parts)


def get_few_shot_examples(mode: str = "browser", count: int = 3) -> List[Dict[str, Any]]:
    """获取 few-shot 示例
    
    Args:
        mode: "browser" 或 "desktop"
        count: 返回的示例数量
        
    Returns:
        示例列表
    """
    examples = BROWSER_EXAMPLES if mode == "browser" else DESKTOP_EXAMPLES
    return examples[:min(count, len(examples))]


def get_validation_prompt(decision: Dict[str, Any]) -> str:
    """获取验证提示词
    
    Args:
        decision: 决策字典
        
    Returns:
        验证提示词
    """
    import json
    return VALIDATION_PROMPT.format(decision=json.dumps(decision, ensure_ascii=False, indent=2))


def get_retry_prompt(history: List[Dict], instruction: str, observation: str) -> str:
    """获取重试提示词
    
    Args:
        history: 历史操作列表
        instruction: 用户指令
        observation: 当前观察
        
    Returns:
        重试提示词
    """
    import json
    return RETRY_PROMPT.format(
        history=json.dumps(history, ensure_ascii=False, indent=2),
        instruction=instruction,
        observation=observation
    )


def get_reflection_prompt(action: Dict[str, Any], expected: str) -> str:
    """获取反思提示词
    
    Args:
        action: 执行的操作
        expected: 预期效果
        
    Returns:
        反思提示词
    """
    import json
    return REFLECTION_PROMPT.format(
        action=json.dumps(action, ensure_ascii=False, indent=2),
        expected=expected
    )


def _format_examples(examples: List[Dict[str, Any]]) -> str:
    """格式化示例为字符串"""
    formatted = []
    for i, ex in enumerate(examples, 1):
        formatted.append(f"### 示例 {i}")
        formatted.append(f"指令: {ex['instruction']}")
        formatted.append(f"屏幕描述: {ex['screenshot_desc']}")
        formatted.append("响应:")
        import json
        formatted.append(json.dumps(ex['response'], ensure_ascii=False, indent=2))
        formatted.append("")
    return "\n".join(formatted)


# 允许的操作列表（用于验证）
VALID_ACTIONS_BROWSER = {
    "browser_click", "browser_type", "browser_scroll", 
    "browser_goto", "browser_wait", "browser_screenshot",
    "browser_clear", "browser_select", "browser_evaluate",
    "finish", "wait", "screenshot"
}

VALID_ACTIONS_DESKTOP = {
    "click", "type", "press", "scroll", "move", "drag",
    "wait", "launch", "screenshot", "finish"
}

VALID_ACTIONS_ALL = VALID_ACTIONS_BROWSER | VALID_ACTIONS_DESKTOP


def validate_decision(decision: Dict[str, Any], mode: str = "browser") -> tuple[bool, list[str]]:
    """验证决策是否有效
    
    Args:
        decision: 决策字典
        mode: "browser" 或 "desktop"
        
    Returns:
        (是否有效, 问题列表)
    """
    issues = []
    
    # 检查必要字段
    if "action" not in decision:
        issues.append("缺少 action 字段")
        return False, issues
    
    action = decision.get("action", "")
    target = decision.get("target", "")
    value = decision.get("value", "")
    delay = decision.get("delay", 1.0)
    
    # 检查 action 是否有效
    valid_actions = VALID_ACTIONS_BROWSER if mode == "browser" else VALID_ACTIONS_DESKTOP
    if action not in valid_actions and action not in VALID_ACTIONS_ALL:
        issues.append(f"无效的 action: {action}")
    
    # 检查 target 格式
    if action in ("click", "move"):
        if mode == "desktop":
            # 桌面模式需要坐标格式
            if target and not _is_valid_coordinate(target):
                issues.append(f"桌面模式下坐标格式不正确: {target}，应为 'x,y'")
        # 浏览器模式的选择器验证更宽松
    
    # 检查 type 操作是否有 value
    if action in ("type", "browser_type") and not value:
        issues.append("type 操作需要提供 value")
    
    # 检查 delay 范围
    if not isinstance(delay, (int, float)) or delay < 0 or delay > 60:
        issues.append(f"delay 值不合理: {delay}")
    
    # 检查 confidence
    confidence = decision.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1):
        issues.append(f"confidence 值应在 0-1 之间: {confidence}")
    
    return len(issues) == 0, issues


def _is_valid_coordinate(target: str) -> bool:
    """检查是否为有效的坐标格式 'x,y'"""
    if not target:
        return False
    parts = target.split(",")
    if len(parts) != 2:
        return False
    try:
        x, y = int(parts[0].strip()), int(parts[1].strip())
        return x >= 0 and y >= 0
    except ValueError:
        return False


def fix_decision(decision: Dict[str, Any], issues: List[str], mode: str = "browser") -> Dict[str, Any]:
    """尝试修复决策中的问题
    
    Args:
        decision: 原始决策
        issues: 问题列表
        mode: 操作模式
        
    Returns:
        修复后的决策
    """
    fixed = decision.copy()
    
    for issue in issues:
        # 修复无效的 action
        if "无效的 action" in issue:
            fixed["action"] = "screenshot"  # 默认使用 screenshot
            fixed["thought"] = fixed.get("thought", "") + " [自动修正: 使用 screenshot]"
        
        # 修复缺少的 target
        if "坐标格式不正确" in issue or "缺少 target" in issue:
            if mode == "desktop":
                fixed["target"] = "500,500"  # 屏幕中心
            else:
                fixed["target"] = "body"
        
        # 修复 type 操作缺少 value
        if "type 操作需要提供 value" in issue:
            fixed["value"] = ""  # 设置空字符串
        
        # 修复不合理的 delay
        if "delay 值不合理" in issue:
            fixed["delay"] = 2.0
        
        # 修复 confidence
        if "confidence 值" in issue:
            fixed["confidence"] = 0.5
    
    return fixed


# =============================================================================
# Self-Healing Phase 2: 诊断与验证 Prompt
# =============================================================================

def get_diagnosis_prompt(
    failure_type: str,
    task,
    error_message: str,
    visual_context: dict,
    history: list = None,
) -> str:
    """生成视觉诊断 prompt"""
    target = getattr(task, "target", "") or ""
    action = getattr(task, "action", "")
    value = getattr(task, "value", "") or ""

    history_text = ""
    if history:
        history_text = "\n## 执行历史\n" + "\n".join(
            f"- {i+1}. {h.get('action', '?')}(target={h.get('target', '?')})"
            for i, h in enumerate(history[-5:])
        )

    candidates_text = ""
    for c in visual_context.get("top_candidates", []):
        candidates_text += (
            f"- {c['id']} ({c['type']}): "
            f"type={c.get('element_type', '-')}, "
            f"text='{c.get('text', '-')}', "
            f"center={c['center']}, "
            f"confidence={c['confidence']}\n"
        )

    return f"""## 失败信息
- 任务: {action}(target={target}, value={value})
- 失败类型: {failure_type}
- 错误信息: {error_message}

## 屏幕检测到的候选元素（已按语义相关度排序）
{candidates_text or '未检测到候选元素'}

## 屏幕尺寸
{visual_context.get('screen_size', [1920, 1080])}
{history_text}

## 你的任务
1. 分析任务失败的根本原因（目标元素是否存在？位置是否变化？是否被遮挡？UI 是否重设计？）
2. 基于候选元素列表，推荐最可能的修复方案
3. 为目标生成语义等价描述（同义词、近义词、图标描述），用于备用搜索
4. 如果目标确实不存在，推荐最接近的替代元素

请严格返回 JSON 格式：
{{
    "root_cause": "根因描述",
    "confidence": 0.0-1.0,
    "target_presence": "found|found_similar|not_found|obscured",
    "suggested_target": {{
        "type": "coordinate|ocr_text|yolo_element",
        "value": "具体值",
        "center": [x, y]
    }},
    "suggested_action": "click|type|scroll|wait|...",
    "reasoning": "推理过程",
    "fallback_strategy": "如果推荐方案失败，备用策略是什么",
    "semantic_equivalents": ["等价描述1", "等价描述2", "..."]
}}
"""


def get_verify_prompt(task, expected_effect: str = "") -> str:
    """生成修复验证 prompt"""
    action = getattr(task, "action", "")
    target = getattr(task, "target", "") or ""
    return f"""## 操作信息
- 执行的操作: {action}(target={target})
- 预期效果: {expected_effect or '操作成功执行'}

## 验证任务
请比较"操作前截图"和"操作后截图"：
1. 操作是否达到预期效果？
2. 界面发生了什么变化？
3. 是否出现了新的问题（弹窗、错误提示等）？

请返回 JSON 格式：
{{
    "success": true/false,
    "observation": "当前状态描述",
    "adjustment_needed": true/false,
    "new_strategy": "如需调整，描述新策略"
}}
"""