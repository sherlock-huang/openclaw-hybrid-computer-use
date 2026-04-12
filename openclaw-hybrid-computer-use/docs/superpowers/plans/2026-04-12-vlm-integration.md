# VLM 集成实现计划 (v0.3.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** 添加 VLM（视觉语言模型）智能模式，让用户可以用自然语言指令控制浏览器/桌面，作为可选的第三层方案。

**Architecture:** VLMClient 封装多模态AI调用，VisionTaskPlanner 将自然语言转为 TaskSequence，复用现有 TaskExecutor 执行。

**Tech Stack:** Python 3.12, OpenAI/Anthropic API, Pillow (图像处理)

---

## 前置准备

- [ ] 获取 OpenAI API Key（或 Anthropic）
- [ ] 安装依赖: `pip install openai anthropic pillow`

---

## Task 1: VLMClient 封装

**Files:**
- Create: `src/vision/__init__.py`
- Create: `src/vision/llm_client.py`
- Test: `tests/test_vision_llm_client.py`

**目标:** 封装 GPT-4V / Claude 3 调用，支持图像输入

- [ ] **Step 1: 创建 VLMClient 基础结构**

创建 `src/vision/__init__.py`:
```python
"""视觉智能模块 - VLM 集成"""

from .llm_client import VLMClient
from .task_planner import VisionTaskPlanner

__all__ = ["VLMClient", "VisionTaskPlanner"]
```

创建 `src/vision/llm_client.py`:
```python
"""VLM 客户端 - 封装多模态 AI 调用"""

import base64
import logging
from typing import Optional, Dict, Any, List
from io import BytesIO
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class VLMClient:
    """视觉语言模型客户端"""
    
    SUPPORTED_PROVIDERS = {"openai", "anthropic"}
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 VLM 客户端
        
        Args:
            provider: "openai" 或 "anthropic"
            api_key: API 密钥，默认从环境变量读取
            model: 模型名称，默认使用 provider 的推荐模型
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的 provider: {provider}. 支持: {self.SUPPORTED_PROVIDERS}")
        
        self.provider = provider
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model or self._get_default_model()
        
        self._client = None
        self._init_client()
        
        logger.info(f"VLMClient 初始化: provider={provider}, model={self.model}")
    
    def _get_api_key_from_env(self) -> str:
        """从环境变量获取 API Key"""
        import os
        if self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("未设置 OPENAI_API_KEY 环境变量")
            return key
        elif self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("未设置 ANTHROPIC_API_KEY 环境变量")
            return key
    
    def _get_default_model(self) -> str:
        """获取默认模型"""
        if self.provider == "openai":
            return "gpt-4-vision-preview"
        elif self.provider == "anthropic":
            return "claude-3-sonnet-20240229"
    
    def _init_client(self):
        """初始化底层客户端"""
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
    
    def _encode_image(self, image: np.ndarray) -> str:
        """
        将 numpy 图像转为 base64 字符串
        
        Args:
            image: numpy 数组 (H, W, C)
            
        Returns:
            base64 编码的图像
        """
        # 转换为 PIL Image
        pil_image = Image.fromarray(image)
        
        # 压缩以节省 token
        max_size = (1024, 1024)
        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转为 base64
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_image
    
    def chat(self, messages: List[Dict], max_tokens: int = 1024) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表，支持文本和图像
            max_tokens: 最大返回 token 数
            
        Returns:
            AI 回复文本
        """
        if self.provider == "openai":
            return self._chat_openai(messages, max_tokens)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, max_tokens)
    
    def _chat_openai(self, messages: List[Dict], max_tokens: int) -> str:
        """OpenAI GPT-4V 调用"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.2  # 低温度，更确定性
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise
    
    def _chat_anthropic(self, messages: List[Dict], max_tokens: int) -> str:
        """Anthropic Claude 3 调用"""
        try:
            # 转换消息格式
            anthropic_messages = self._convert_to_anthropic_format(messages)
            
            response = self._client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                temperature=0.2
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            raise
    
    def _convert_to_anthropic_format(self, messages: List[Dict]) -> List[Dict]:
        """将 OpenAI 格式转为 Anthropic 格式"""
        # 简化处理，实际可能需要更复杂的转换
        return messages
    
    def analyze_screen(self, screenshot: np.ndarray, instruction: str, history: Optional[List] = None) -> Dict[str, Any]:
        """
        分析屏幕截图，返回操作建议
        
        Args:
            screenshot: 屏幕截图 (numpy 数组)
            instruction: 用户指令
            history: 历史操作记录
            
        Returns:
            解析后的决策字典
        """
        # 编码图像
        base64_image = self._encode_image(screenshot)
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt()
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"任务指令: {instruction}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
        
        # 调用 API
        response = self.chat(messages)
        
        # 解析响应
        return self._parse_response(response)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是 OpenClaw，一个智能桌面自动化助手。

你的任务是分析屏幕截图，帮助用户完成指定的任务。

可用操作：
1. click(x, y) 或 click(selector) - 点击元素
2. type(text) - 输入文字
3. scroll(amount) - 滚动页面（正数向下，负数向上）
4. wait(seconds) - 等待
5. screenshot() - 截图
6. finish() - 任务完成

返回格式必须是 JSON：
{
    "observation": "描述当前屏幕状态",
    "thought": "分析思考过程，为什么选择这个操作",
    "action": "click/type/scroll/wait/screenshot/finish",
    "target": "选择器如 #search-input，或坐标如 500,300",
    "value": "输入的文字（仅type操作）",
    "delay": 2.0,
    "is_task_complete": false
}

重要：
- 每次只执行一个操作
- 优先使用 ID 选择器，其次 class，最后坐标
- 操作后等待页面响应
- 任务完成时必须设置 is_task_complete: true"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应，提取 JSON"""
        import json
        import re
        
        # 尝试提取 JSON
        try:
            # 寻找 JSON 代码块
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response
            
            result = json.loads(json_str)
            
            # 验证必要字段
            required_fields = ["action", "target"]
            for field in required_fields:
                if field not in result:
                    result[field] = ""
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 失败: {e}")
            logger.error(f"原始响应: {response}")
            # 返回默认操作
            return {
                "observation": "解析失败",
                "thought": "AI 返回格式不正确",
                "action": "screenshot",
                "target": "",
                "value": "",
                "delay": 1.0,
                "is_task_complete": False
            }
```

- [ ] **Step 2: 添加依赖到 requirements.txt**

```
openai>=1.0.0
anthropic>=0.18.0
pillow>=10.0.0
```

- [ ] **Step 3: 创建测试**

创建 `tests/test_vision_llm_client.py`:
```python
"""VLMClient 测试"""

import pytest
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestVLMClient:
    """VLMClient 测试"""
    
    def test_client_creation(self):
        """测试创建 VLMClient（需要 API Key）"""
        import os
        
        # 如果没有 API Key，跳过测试
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("未设置 OPENAI_API_KEY")
        
        from src.vision.llm_client import VLMClient
        
        client = VLMClient(provider="openai")
        assert client.provider == "openai"
        assert client.model == "gpt-4-vision-preview"
    
    def test_encode_image(self):
        """测试图像编码"""
        from src.vision.llm_client import VLMClient
        
        client = VLMClient(provider="openai", api_key="fake-key")
        
        # 创建测试图像
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        base64_str = client._encode_image(image)
        
        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
    
    def test_parse_response_valid_json(self):
        """测试解析有效的 JSON 响应"""
        from src.vision.llm_client import VLMClient
        
        client = VLMClient(provider="openai", api_key="fake-key")
        
        response = '''{"action": "click", "target": "#btn", "delay": 2.0}'''
        result = client._parse_response(response)
        
        assert result["action"] == "click"
        assert result["target"] == "#btn"
    
    def test_parse_response_markdown_json(self):
        """测试解析 Markdown 格式的 JSON"""
        from src.vision.llm_client import VLMClient
        
        client = VLMClient(provider="openai", api_key="fake-key")
        
        response = '''```json
{"action": "type", "target": "#input", "value": "hello"}
```'''
        result = client._parse_response(response)
        
        assert result["action"] == "type"
        assert result["value"] == "hello"
```

- [ ] **Step 4: 提交**

```bash
git add src/vision/ tests/test_vision_llm_client.py requirements.txt
git commit -m "feat(vision): add VLMClient for GPT-4V/Claude integration"
```

---

## Task 2: VisionTaskPlanner

**Files:**
- Create: `src/vision/task_planner.py`
- Test: `tests/test_vision_task_planner.py`

**目标:** 将自然语言指令转为 TaskSequence

- [ ] **Step 1: 实现 VisionTaskPlanner**

创建 `src/vision/task_planner.py`:
```python
"""视觉任务规划器 - 将自然语言转为 TaskSequence"""

import logging
import time
from typing import Optional, List, Dict, Any
import numpy as np

from ..core.models import Task, TaskSequence, RecordingMode
from ..browser.controller import BrowserController
from ..browser.actions import BrowserActionHandler
from .llm_client import VLMClient

logger = logging.getLogger(__name__)


class VisionTaskPlanner:
    """视觉任务规划器"""
    
    def __init__(self, vlm_client: Optional[VLMClient] = None, max_steps: int = 20):
        """
        初始化任务规划器
        
        Args:
            vlm_client: VLM 客户端，默认创建新的
            max_steps: 最大执行步数
        """
        self.vlm = vlm_client or VLMClient()
        self.max_steps = max_steps
        self.history: List[Dict] = []
        
        # 浏览器控制
        self.browser_controller: Optional[BrowserController] = None
        self.browser_handler: Optional[BrowserActionHandler] = None
        
        logger.info(f"VisionTaskPlanner 初始化: max_steps={max_steps}")
    
    def execute_instruction(self, instruction: str, start_browser: bool = True) -> TaskSequence:
        """
        执行自然语言指令
        
        Args:
            instruction: 用户指令，如"在淘宝上搜索蓝牙耳机"
            start_browser: 是否自动启动浏览器
            
        Returns:
            执行的任务序列
        """
        logger.info(f"开始执行指令: {instruction}")
        
        tasks = []
        
        # 启动浏览器
        if start_browser:
            self._ensure_browser_running()
            tasks.append(Task("browser_launch", value="chromium", delay=2.0))
        
        # 主循环
        for step in range(self.max_steps):
            logger.info(f"Step {step + 1}/{self.max_steps}")
            
            # 截图
            screenshot = self._capture_screenshot()
            
            # VLM 决策
            decision = self.vlm.analyze_screen(screenshot, instruction, self.history)
            
            logger.info(f"VLM 决策: {decision}")
            
            # 检查是否完成
            if decision.get("is_task_complete") or decision.get("action") == "finish":
                logger.info("任务完成")
                break
            
            # 转换为 Task
            task = self._decision_to_task(decision)
            if task:
                tasks.append(task)
                
                # 执行操作
                self._execute_task(task)
                
                # 记录历史
                self.history.append({
                    "step": step,
                    "decision": decision,
                    "task": task.to_dict()
                })
            
            # 等待
            delay = decision.get("delay", 2.0)
            time.sleep(delay)
        
        # 关闭浏览器
        if self.browser_controller:
            tasks.append(Task("browser_close", delay=1.0))
            self.browser_controller.close()
        
        # 创建任务序列
        sequence = TaskSequence(
            name=f"VLM: {instruction[:50]}",
            tasks=tasks,
            max_retries=2
        )
        
        return sequence
    
    def _ensure_browser_running(self):
        """确保浏览器正在运行"""
        if not self.browser_controller or not self.browser_controller.is_running:
            self.browser_controller = BrowserController(
                browser_type="chromium",
                headless=False,
                user_data_dir="browser_data"
            )
            self.browser_controller.launch()
            self.browser_handler = BrowserActionHandler(self.browser_controller)
    
    def _capture_screenshot(self) -> np.ndarray:
        """捕获屏幕截图"""
        if self.browser_controller and self.browser_controller.is_running:
            # 浏览器页面截图
            from PIL import Image
            import io
            
            screenshot_bytes = self.browser_controller.page.screenshot()
            image = Image.open(io.BytesIO(screenshot_bytes))
            return np.array(image)
        else:
            # 桌面截图
            from ..perception.screen import ScreenCapture
            screen = ScreenCapture()
            return screen.capture()
    
    def _decision_to_task(self, decision: Dict[str, Any]) -> Optional[Task]:
        """将 VLM 决策转为 Task"""
        action = decision.get("action")
        target = decision.get("target", "")
        value = decision.get("value", "")
        delay = decision.get("delay", 2.0)
        
        if action == "click":
            return Task("browser_click" if self._is_browser_selector(target) else "click",
                       target=target, delay=delay)
        elif action == "type":
            return Task("browser_type" if self._is_browser_selector(target) else "type",
                       target=target, value=value, delay=delay)
        elif action == "scroll":
            return Task("browser_scroll", value=str(value), delay=delay)
        elif action == "wait":
            return Task("wait", delay=float(value) if value else delay)
        elif action == "screenshot":
            return Task("browser_screenshot", value=f"vlm_step_{len(self.history)}.png", delay=delay)
        
        return None
    
    def _is_browser_selector(self, target: str) -> bool:
        """判断是否为浏览器选择器"""
        if not target:
            return False
        # 浏览器选择器特征
        browser_patterns = ["#", ".", "[", "input", "button", "a", "div"]
        return any(pattern in target for pattern in browser_patterns)
    
    def _execute_task(self, task: Task):
        """执行单个任务"""
        if not self.browser_handler:
            return
        
        try:
            if task.action == "browser_click":
                self.browser_handler.click(task.target)
            elif task.action == "browser_type":
                self.browser_handler.type(task.target, task.value or "")
            elif task.action == "browser_scroll":
                amount = int(task.value) if task.value else 500
                self.browser_handler.scroll(amount)
            elif task.action == "browser_screenshot":
                self.browser_handler.screenshot(task.value)
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
```

- [ ] **Step 2: 提交**

```bash
git add src/vision/task_planner.py tests/test_vision_task_planner.py
git commit -m "feat(vision): add VisionTaskPlanner to convert natural language to tasks"
```

---

## Task 3: CLI 添加 vision 命令

**Files:**
- Modify: `src/__main__.py`

**目标:** 添加 `vision` 子命令

- [ ] **Step 1: 添加 cmd_vision 函数**

在 `src/__main__.py` 中添加：
```python
def cmd_vision(args):
    """VLM 智能模式命令"""
    from src.vision.task_planner import VisionTaskPlanner
    from src.core.models import TaskSequence
    import json
    
    print(f"🧠 VLM 智能模式")
    print(f"指令: {args.instruction}")
    print(f"模型: {args.provider}")
    print("-" * 50)
    
    try:
        # 创建规划器
        planner = VisionTaskPlanner(max_steps=args.max_steps)
        
        # 执行指令
        sequence = planner.execute_instruction(
            instruction=args.instruction,
            start_browser=not args.no_browser
        )
        
        print("-" * 50)
        print(f"✅ 任务完成！共 {len(sequence.tasks)} 步")
        
        # 保存结果
        if args.output:
            sequence.save_to_file(args.output)
            print(f"💾 已保存到: {args.output}")
        
        # 显示任务摘要
        print("\n📋 执行步骤:")
        for i, task in enumerate(sequence.tasks, 1):
            print(f"  {i}. {task.action}: {task.target or task.value}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
```

- [ ] **Step 2: 添加 argument parser**

```python
# vision 命令
vision_parser = subparsers.add_parser("vision", help="VLM 智能模式（自然语言指令）")
vision_parser.add_argument(
    "instruction",
    nargs="+",
    help="自然语言指令，如：'帮我在淘宝上搜索蓝牙耳机'"
)
vision_parser.add_argument(
    "--provider",
    choices=["openai", "anthropic"],
    default="openai",
    help="VLM 提供商 (默认: openai)"
)
vision_parser.add_argument(
    "--max-steps",
    type=int,
    default=20,
    help="最大执行步数 (默认: 20)"
)
vision_parser.add_argument(
    "--no-browser",
    action="store_true",
    help="不自动启动浏览器"
)
vision_parser.add_argument(
    "-o", "--output",
    help="保存任务文件的路径"
)
vision_parser.set_defaults(func=cmd_vision)
```

- [ ] **Step 3: 测试 CLI**

```bash
py -m src vision --help
```

- [ ] **Step 4: 提交**

```bash
git add src/__main__.py
git commit -m "feat(cli): add vision command for VLM natural language control"
```

---

## Task 4: 测试与示例

**Files:**
- Create: `examples/vision_task_example.py`
- Create: `docs/vision_usage.md`

- [ ] **Step 1: 创建示例脚本**

`examples/vision_task_example.py`:
```python
"""VLM 智能任务示例"""

import sys
sys.path.insert(0, '..')

from src.vision.task_planner import VisionTaskPlanner

# 创建规划器
planner = VisionTaskPlanner(max_steps=10)

# 执行指令
instruction = "在淘宝上搜索蓝牙耳机，按销量排序"
print(f"执行指令: {instruction}")

sequence = planner.execute_instruction(instruction)

print(f"\n生成任务序列: {sequence.name}")
print(f"共 {len(sequence.tasks)} 个步骤")
```

- [ ] **Step 2: 创建使用文档**

`docs/vision_usage.md`:
```markdown
# VLM 智能模式使用指南

## 简介

VLM (Vision Language Model) 模式让你可以用自然语言控制浏览器，
AI 会自动分析屏幕并执行操作。

## 使用前准备

1. 获取 OpenAI API Key
   - 访问 https://platform.openai.com/api-keys
   - 创建新的 API Key

2. 设置环境变量
   ```powershell
   $env:OPENAI_API_KEY = "your-api-key"
   ```

## 使用示例

### 基本用法

```bash
# 在淘宝上搜索商品
py -m src vision "帮我在淘宝上搜索蓝牙耳机"

# 带更多要求
py -m src vision "在淘宝上搜索蓝牙耳机，按销量排序，截图给我看前3个商品"

# 保存任务文件
py -m src vision "打开GitHub并搜索python项目" -o github_task.json
```

### Python API

```python
from src.vision.task_planner import VisionTaskPlanner

planner = VisionTaskPlanner()
sequence = planner.execute_instruction("在抖音上搜索美食视频")

# 保存生成的任务
sequence.save_to_file("douyin_task.json")
```

## 注意事项

- 每次操作都会截图给 AI 分析，有一定延迟
- API 调用会产生费用（GPT-4V 约 $0.01-0.02/次）
- 建议先在小任务上测试，再用于复杂场景
```

- [ ] **Step 3: 提交**

```bash
git add examples/vision_task_example.py docs/vision_usage.md
git commit -m "docs: add VLM vision mode usage examples and documentation"
```

---

## 完成清单

- [ ] Task 1: VLMClient 封装
- [ ] Task 2: VisionTaskPlanner
- [ ] Task 3: CLI 添加 vision 命令
- [ ] Task 4: 测试与示例

---

**需要 API Key 才能测试！**

如果没有 OpenAI/Anthropic API Key，可以先实现代码，后续再测试。

**Plan complete. Start execution?**
