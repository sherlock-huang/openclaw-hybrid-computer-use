# 浏览器集成实现计划 (v0.2.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 OpenClaw Desktop Agent 添加浏览器自动化能力，支持 Playwright 控制浏览器，并与现有桌面自动化混合使用。

**Architecture:** 双模式架构 - `BrowserController` 管理浏览器生命周期，`BrowserActionHandler` 封装 Playwright 操作，`MixedModeExecutor` 自动切换桌面/浏览器模式。

**Tech Stack:** Python 3.12, Playwright 1.40+, pytest

---

## 文件结构

```
src/
├── browser/
│   ├── __init__.py              # 导出 BrowserController, BrowserActionHandler
│   ├── controller.py            # 浏览器生命周期管理
│   ├── actions.py               # 浏览器操作封装
│   └── executor.py              # 浏览器任务执行器
├── core/
│   ├── models.py                # 扩展 Task action 类型
│   └── executor.py              # 集成 browser actions
└── __main__.py                  # 添加浏览器相关 CLI 命令

tests/
├── test_browser_controller.py   # BrowserController 测试
├── test_browser_actions.py      # BrowserActionHandler 测试
└── test_mixed_executor.py       # 混合模式测试

examples/
└── douyin_search.json           # 抖音搜索示例任务
```

---

## 前置依赖

### Task 0: 安装 Playwright

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 添加 Playwright 依赖到 requirements.txt**

```
playwright>=1.40.0
```

- [ ] **Step 2: 提交依赖更新**

```bash
git add requirements.txt
git commit -m "deps: add playwright for browser automation"
```

---

## Task 1: 核心数据模型扩展

**Files:**
- Modify: `src/core/models.py`
- Test: `tests/test_models.py` (新建或修改)

**目标:** 扩展 Task 模型支持浏览器 action 类型

- [ ] **Step 1: 添加浏览器 action 常量到 models.py**

在 `src/core/models.py` 顶部添加：

```python
# 浏览器相关 actions
BROWSER_ACTIONS = {
    "browser_launch",
    "browser_close", 
    "browser_goto",
    "browser_click",
    "browser_type",
    "browser_clear",
    "browser_select",
    "browser_wait",
    "browser_scroll",
    "browser_screenshot",
    "browser_evaluate",
}

def is_browser_action(action: str) -> bool:
    """判断是否为浏览器 action"""
    return action.startswith("browser_")
```

- [ ] **Step 2: 验证导入正常**

```bash
py -c "from src.core.models import is_browser_action, BROWSER_ACTIONS; print('OK')"
```

Expected: 输出 "OK"

- [ ] **Step 3: 添加测试**

创建/修改 `tests/test_models.py`：

```python
def test_is_browser_action():
    from src.core.models import is_browser_action
    
    assert is_browser_action("browser_click") is True
    assert is_browser_action("browser_type") is True
    assert is_browser_action("click") is False
    assert is_browser_action("type") is False
```

- [ ] **Step 4: 运行测试**

```bash
py -m pytest tests/test_models.py::test_is_browser_action -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/core/models.py tests/test_models.py
git commit -m "feat(models): add browser action types and is_browser_action helper"
```

---

## Task 2: BrowserController - 浏览器生命周期管理

**Files:**
- Create: `src/browser/__init__.py`
- Create: `src/browser/controller.py`
- Test: `tests/test_browser_controller.py`

**目标:** 创建浏览器控制器，封装 Playwright 浏览器管理

- [ ] **Step 1: 创建 src/browser/__init__.py**

```python
"""浏览器自动化模块"""

from .controller import BrowserController
from .actions import BrowserActionHandler

__all__ = ["BrowserController", "BrowserActionHandler"]
```

- [ ] **Step 2: 编写失败测试 - BrowserController 基础功能**

创建 `tests/test_browser_controller.py`：

```python
"""BrowserController 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBrowserController:
    """BrowserController 测试类"""
    
    def test_controller_creation(self):
        """测试创建 BrowserController"""
        from src.browser.controller import BrowserController
        
        controller = BrowserController(browser_type="chromium", headless=True)
        
        assert controller.browser_type == "chromium"
        assert controller.headless is True
        assert controller.is_running is False
    
    def test_controller_launch_and_close(self):
        """测试启动和关闭浏览器"""
        from src.browser.controller import BrowserController
        
        controller = BrowserController(headless=True)
        
        # 启动前状态
        assert controller.is_running is False
        
        # 启动
        controller.launch()
        assert controller.is_running is True
        assert controller.page is not None
        
        # 关闭
        controller.close()
        assert controller.is_running is False
```

- [ ] **Step 3: 运行测试确认失败**

```bash
py -m pytest tests/test_browser_controller.py -v
```

Expected: FAIL (BrowserController 不存在)

- [ ] **Step 4: 实现 BrowserController**

创建 `src/browser/controller.py`：

```python
"""浏览器控制器 - 管理浏览器生命周期"""

import logging
from typing import Optional, Any
from playwright.sync_api import sync_playwright, Page, Browser

logger = logging.getLogger(__name__)


class BrowserController:
    """浏览器控制器"""
    
    SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
    
    def __init__(self, browser_type: str = "chromium", headless: bool = False):
        """
        初始化浏览器控制器
        
        Args:
            browser_type: 浏览器类型 ("chromium" | "firefox" | "webkit")
            headless: 是否无头模式
            
        Raises:
            ValueError: 不支持的浏览器类型
        """
        if browser_type not in self.SUPPORTED_BROWSERS:
            raise ValueError(f"不支持的浏览器类型: {browser_type}. "
                           f"支持: {self.SUPPORTED_BROWSERS}")
        
        self.browser_type = browser_type
        self.headless = headless
        
        self._playwright: Optional[Any] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        
        logger.info(f"BrowserController 初始化: {browser_type}, headless={headless}")
    
    @property
    def is_running(self) -> bool:
        """浏览器是否正在运行"""
        return self._browser is not None and self._page is not None
    
    @property
    def page(self) -> Optional[Page]:
        """获取当前页面"""
        return self._page
    
    def launch(self) -> None:
        """启动浏览器"""
        if self.is_running:
            logger.warning("浏览器已在运行")
            return
        
        try:
            self._playwright = sync_playwright().start()
            
            # 获取浏览器启动器
            browser_launcher = getattr(self._playwright, self.browser_type)
            
            # 启动浏览器
            self._browser = browser_launcher.launch(headless=self.headless)
            
            # 创建新页面
            self._page = self._browser.new_page()
            
            # 设置默认视口
            self._page.set_viewport_size({"width": 1920, "height": 1080})
            
            logger.info(f"浏览器启动成功: {self.browser_type}")
            
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            self.close()
            raise
    
    def close(self) -> None:
        """关闭浏览器"""
        logger.info("关闭浏览器...")
        
        if self._page:
            try:
                self._page.close()
            except Exception as e:
                logger.debug(f"关闭页面时出错: {e}")
            finally:
                self._page = None
        
        if self._browser:
            try:
                self._browser.close()
            except Exception as e:
                logger.debug(f"关闭浏览器时出错: {e}")
            finally:
                self._browser = None
        
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.debug(f"停止 playwright 时出错: {e}")
            finally:
                self._playwright = None
        
        logger.info("浏览器已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.launch()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
```

- [ ] **Step 5: 运行测试确认通过**

```bash
py -m pytest tests/test_browser_controller.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 6: 提交**

```bash
git add src/browser/ tests/test_browser_controller.py
git commit -m "feat(browser): add BrowserController for browser lifecycle management"
```

---

## Task 3: BrowserActionHandler - 浏览器操作封装

**Files:**
- Create: `src/browser/actions.py`
- Test: `tests/test_browser_actions.py`

**目标:** 封装所有浏览器操作（点击、输入、导航等）

- [ ] **Step 1: 编写失败测试**

创建 `tests/test_browser_actions.py`：

```python
"""BrowserActionHandler 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBrowserActionHandler:
    """BrowserActionHandler 测试类"""
    
    @pytest.fixture
    def handler(self):
        """创建测试用的 handler"""
        from src.browser.controller import BrowserController
        from src.browser.actions import BrowserActionHandler
        
        controller = BrowserController(headless=True)
        controller.launch()
        
        handler = BrowserActionHandler(controller)
        yield handler
        
        controller.close()
    
    def test_goto(self, handler):
        """测试导航到 URL"""
        handler.goto("https://example.com")
        
        # 验证页面标题
        assert "Example Domain" in handler.controller.page.title()
    
    def test_click(self, handler):
        """测试点击元素"""
        handler.goto("https://example.com")
        
        # 点击 "More information..." 链接
        handler.click("a")
        
        # 验证页面已跳转
        assert "iana.org" in handler.controller.page.url
    
    def test_type(self, handler):
        """测试输入文字"""
        # 使用 httpbin 测试表单
        handler.goto("https://httpbin.org/forms/post")
        
        handler.type("input[name='custname']", "Test User")
        
        # 获取输入的值
        value = handler.controller.page.input_value("input[name='custname']")
        assert value == "Test User"
    
    def test_scroll(self, handler):
        """测试滚动页面"""
        handler.goto("https://example.com")
        
        # 滚动 500 像素
        handler.scroll(500)
        
        # 验证滚动位置
        scroll_y = handler.controller.page.evaluate("() => window.scrollY")
        assert scroll_y == 500
    
    def test_screenshot(self, handler, tmp_path):
        """测试截图"""
        handler.goto("https://example.com")
        
        screenshot_path = tmp_path / "test.png"
        data = handler.screenshot(str(screenshot_path))
        
        # 验证文件已创建
        assert screenshot_path.exists()
        # 验证返回了字节数据
        assert data is not None
        assert len(data) > 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
py -m pytest tests/test_browser_actions.py -v
```

Expected: FAIL (导入错误)

- [ ] **Step 3: 实现 BrowserActionHandler**

创建 `src/browser/actions.py`：

```python
"""浏览器操作处理器 - 封装 Playwright 操作"""

import logging
import time
from typing import Optional, Dict, Any, Union
from pathlib import Path

from .controller import BrowserController

logger = logging.getLogger(__name__)


class BrowserActionHandler:
    """浏览器操作处理器"""
    
    def __init__(self, controller: BrowserController):
        """
        初始化操作处理器
        
        Args:
            controller: 浏览器控制器实例
        """
        self.controller = controller
        logger.info("BrowserActionHandler 初始化完成")
    
    def _get_page(self):
        """获取当前页面，确保浏览器已启动"""
        if not self.controller.is_running:
            raise RuntimeError("浏览器未启动，请先调用 browser_launch")
        return self.controller.page
    
    def goto(self, url: str, timeout: int = 30) -> None:
        """
        导航到 URL
        
        Args:
            url: 目标 URL
            timeout: 加载超时时间（秒）
        """
        page = self._get_page()
        logger.info(f"导航到: {url}")
        
        try:
            page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            logger.info(f"页面加载完成: {page.title()}")
        except Exception as e:
            logger.error(f"页面加载失败: {e}")
            raise
    
    def click(self, selector: str, options: Optional[Dict] = None) -> None:
        """
        点击元素
        
        Args:
            selector: CSS 选择器或 XPath
            options: {
                timeout: 等待超时（秒，默认30）
                force: 是否强制点击（默认False）
                button: 鼠标按钮（"left"|"right"|"middle"，默认"left"）
            }
        """
        page = self._get_page()
        opts = options or {}
        
        timeout = opts.get("timeout", 30) * 1000
        force = opts.get("force", False)
        button = opts.get("button", "left")
        
        logger.info(f"点击元素: {selector}")
        
        try:
            page.click(
                selector,
                timeout=timeout,
                force=force,
                button=button
            )
            logger.debug(f"点击成功: {selector}")
        except Exception as e:
            logger.error(f"点击失败 {selector}: {e}")
            raise
    
    def type(self, selector: str, text: str, options: Optional[Dict] = None) -> None:
        """
        输入文字
        
        Args:
            selector: CSS 选择器
            text: 要输入的文字
            options: {
                timeout: 等待超时（秒，默认30）
                clear_first: 是否先清空（默认True）
                delay: 每个字符输入延迟（毫秒，默认0）
            }
        """
        page = self._get_page()
        opts = options or {}
        
        timeout = opts.get("timeout", 30) * 1000
        clear_first = opts.get("clear_first", True)
        delay = opts.get("delay", 0)
        
        logger.info(f"在 {selector} 输入文字: {text}")
        
        try:
            if clear_first:
                page.fill(selector, text, timeout=timeout)
            else:
                page.type(selector, text, timeout=timeout, delay=delay)
            logger.debug(f"输入完成: {selector}")
        except Exception as e:
            logger.error(f"输入失败 {selector}: {e}")
            raise
    
    def clear(self, selector: str, timeout: int = 30) -> None:
        """
        清空输入框
        
        Args:
            selector: CSS 选择器
            timeout: 等待超时（秒）
        """
        page = self._get_page()
        logger.info(f"清空输入框: {selector}")
        
        try:
            page.fill(selector, "", timeout=timeout * 1000)
        except Exception as e:
            logger.error(f"清空失败 {selector}: {e}")
            raise
    
    def select(self, selector: str, value: str, timeout: int = 30) -> None:
        """
        选择下拉框选项
        
        Args:
            selector: CSS 选择器
            value: 选项值
            timeout: 等待超时（秒）
        """
        page = self._get_page()
        logger.info(f"选择 {selector}: {value}")
        
        try:
            page.select_option(selector, value, timeout=timeout * 1000)
        except Exception as e:
            logger.error(f"选择失败 {selector}: {e}")
            raise
    
    def wait_for(self, selector: str, state: str = "visible", timeout: int = 30) -> None:
        """
        等待元素状态
        
        Args:
            selector: CSS 选择器
            state: 等待状态 ("visible" | "hidden" | "attached" | "detached")
            timeout: 超时时间（秒）
        """
        page = self._get_page()
        logger.info(f"等待元素 {selector} 状态: {state}")
        
        valid_states = ["visible", "hidden", "attached", "detached"]
        if state not in valid_states:
            raise ValueError(f"无效的状态: {state}. 支持: {valid_states}")
        
        try:
            page.wait_for_selector(selector, state=state, timeout=timeout * 1000)
            logger.debug(f"元素 {selector} 已 {state}")
        except Exception as e:
            logger.error(f"等待元素失败 {selector}: {e}")
            raise
    
    def scroll(self, amount: int, direction: str = "vertical") -> None:
        """
        滚动页面
        
        Args:
            amount: 滚动像素（正数向下/向右，负数向上/向左）
            direction: 滚动方向 ("vertical" | "horizontal")
        """
        page = self._get_page()
        logger.info(f"滚动页面: {direction} {amount}px")
        
        try:
            if direction == "vertical":
                page.evaluate(f"() => window.scrollBy(0, {amount})")
            elif direction == "horizontal":
                page.evaluate(f"() => window.scrollBy({amount}, 0)")
            else:
                raise ValueError(f"无效的滚动方向: {direction}")
            
            # 等待滚动完成
            time.sleep(0.5)
            logger.debug(f"滚动完成")
        except Exception as e:
            logger.error(f"滚动失败: {e}")
            raise
    
    def screenshot(self, path: Optional[str] = None) -> bytes:
        """
        截图
        
        Args:
            path: 保存路径（可选）
            
        Returns:
            截图字节数据
        """
        page = self._get_page()
        logger.info("截图...")
        
        try:
            screenshot_bytes = page.screenshot(path=path, full_page=True)
            logger.info(f"截图完成{' 保存到: ' + path if path else ''}")
            return screenshot_bytes
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise
    
    def evaluate(self, script: str) -> Any:
        """
        执行 JavaScript
        
        Args:
            script: JavaScript 代码
            
        Returns:
            脚本执行结果
        """
        page = self._get_page()
        logger.info(f"执行脚本: {script[:50]}...")
        
        try:
            result = page.evaluate(script)
            return result
        except Exception as e:
            logger.error(f"脚本执行失败: {e}")
            raise
```

- [ ] **Step 4: 运行测试确认通过**

```bash
py -m pytest tests/test_browser_actions.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: 提交**

```bash
git add src/browser/actions.py tests/test_browser_actions.py
git commit -m "feat(browser): add BrowserActionHandler with click, type, scroll, screenshot"
```

---

## Task 4: 集成到 TaskExecutor

**Files:**
- Modify: `src/core/executor.py`
- Test: `tests/test_executor_browser.py`

**目标:** 扩展 TaskExecutor 支持浏览器 action

- [ ] **Step 1: 编写集成测试**

创建 `tests/test_executor_browser.py`：

```python
"""TaskExecutor 浏览器集成测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestExecutorBrowserActions:
    """测试 TaskExecutor 执行浏览器任务"""
    
    def test_execute_browser_launch_and_goto(self):
        """测试执行 browser_launch 和 browser_goto"""
        from src.core.executor import TaskExecutor
        from src.core.models import Task, TaskSequence
        
        executor = TaskExecutor()
        
        sequence = TaskSequence(
            name="浏览器测试",
            tasks=[
                Task("browser_launch", value="chromium", delay=2.0),
                Task("browser_goto", value="https://example.com", delay=2.0),
                Task("browser_close", delay=1.0),
            ]
        )
        
        result = executor.execute(sequence)
        
        assert result.success is True
        assert result.completed_steps == 3
    
    def test_execute_browser_click_and_type(self):
        """测试执行浏览器点击和输入"""
        from src.core.executor import TaskExecutor
        from src.core.models import Task, TaskSequence
        
        executor = TaskExecutor()
        
        sequence = TaskSequence(
            name="浏览器交互测试",
            tasks=[
                Task("browser_launch", value="chromium", delay=2.0),
                Task("browser_goto", value="https://httpbin.org/forms/post", delay=3.0),
                Task("browser_type", target="input[name='custname']", value="Test", delay=0.5),
                Task("browser_click", target="input[type='submit']", delay=2.0),
                Task("browser_close", delay=1.0),
            ]
        )
        
        result = executor.execute(sequence)
        
        assert result.success is True
```

- [ ] **Step 2: 运行测试确认失败**

```bash
py -m pytest tests/test_executor_browser.py -v
```

Expected: FAIL (browser actions 未实现)

- [ ] **Step 3: 扩展 TaskExecutor**

修改 `src/core/executor.py`，在 `TaskExecutor` 类中添加浏览器支持：

在 `__init__` 方法中添加：

```python
from ..browser.controller import BrowserController
from ..browser.actions import BrowserActionHandler

# 在 __init__ 中添加：
self.browser_controller: Optional[BrowserController] = None
self.browser_handler: Optional[BrowserActionHandler] = None
```

在 `_execute_single_task` 方法中添加 browser actions：

```python
# 在方法开头添加 browser action 处理
if task.action == "browser_launch":
    browser_type = task.value or "chromium"
    self.browser_controller = BrowserController(
        browser_type=browser_type,
        headless=self.config.browser_headless
    )
    self.browser_controller.launch()
    self.browser_handler = BrowserActionHandler(self.browser_controller)
    return True

elif task.action == "browser_close":
    if self.browser_controller:
        self.browser_controller.close()
        self.browser_controller = None
        self.browser_handler = None
    return True

elif task.action == "browser_goto":
    if not task.value:
        raise ValueError("browser_goto requires value (URL)")
    self.browser_handler.goto(task.value)
    return True

elif task.action == "browser_click":
    if not task.target:
        raise ValueError("browser_click requires target (selector)")
    self.browser_handler.click(task.target)
    return True

elif task.action == "browser_type":
    if not task.target:
        raise ValueError("browser_type requires target (selector)")
    self.browser_handler.type(task.target, task.value or "")
    return True

elif task.action == "browser_clear":
    if not task.target:
        raise ValueError("browser_clear requires target (selector)")
    self.browser_handler.clear(task.target)
    return True

elif task.action == "browser_wait":
    if not task.target:
        raise ValueError("browser_wait requires target (selector)")
    state = task.value or "visible"
    self.browser_handler.wait_for(task.target, state=state)
    return True

elif task.action == "browser_scroll":
    amount = int(task.value) if task.value else 500
    self.browser_handler.scroll(amount)
    return True

elif task.action == "browser_screenshot":
    path = task.value
    self.browser_handler.screenshot(path)
    return True

elif task.action == "browser_evaluate":
    if not task.value:
        raise ValueError("browser_evaluate requires value (JavaScript)")
    self.browser_handler.evaluate(task.value)
    return True

# 原有的 desktop actions 继续处理...
```

在 `execute` 方法结尾添加清理：

```python
finally:
    # 确保浏览器关闭
    if self.browser_controller and self.browser_controller.is_running:
        self.browser_controller.close()
```

- [ ] **Step 4: 添加配置项**

修改 `src/core/config.py`，添加浏览器配置：

```python
class Config:
    """配置类"""
    
    def __init__(self):
        # 现有配置...
        
        # 浏览器配置
        self.browser_headless = False  # 是否无头模式
        self.browser_default_type = "chromium"  # 默认浏览器
        self.browser_timeout = 30  # 默认超时（秒）
```

- [ ] **Step 5: 运行测试确认通过**

```bash
py -m pytest tests/test_executor_browser.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 6: 提交**

```bash
git add src/core/executor.py src/core/config.py tests/test_executor_browser.py
git commit -m "feat(executor): integrate browser actions into TaskExecutor"
```

---

## Task 5: 抖音搜索示例任务

**Files:**
- Create: `examples/douyin_search.json`

**目标:** 创建可运行的抖音搜索示例

- [ ] **Step 1: 创建示例任务文件**

创建 `examples/douyin_search.json`：

```json
{
  "name": "抖音搜索UP主",
  "description": "在抖音网页版搜索指定UP主并查看视频列表",
  "version": "1.0",
  "author": "OpenClaw",
  "tasks": [
    {
      "action": "browser_launch",
      "value": "chromium",
      "delay": 2.0,
      "description": "启动 Chromium 浏览器"
    },
    {
      "action": "browser_goto",
      "value": "https://www.douyin.com",
      "delay": 5.0,
      "description": "访问抖音网页版"
    },
    {
      "action": "browser_click",
      "target": "[data-e2e='search-icon']",
      "delay": 1.0,
      "description": "点击搜索图标"
    },
    {
      "action": "browser_type",
      "target": "[data-e2e='search-input']",
      "value": "李子柒",
      "delay": 0.5,
      "description": "输入UP主名称（可替换）"
    },
    {
      "action": "browser_click",
      "target": "[data-e2e='search-button']",
      "delay": 3.0,
      "description": "点击搜索按钮"
    },
    {
      "action": "browser_wait",
      "target": ".video-item, [data-e2e='user-card']",
      "value": "visible",
      "delay": 2.0,
      "description": "等待搜索结果加载"
    },
    {
      "action": "browser_scroll",
      "value": "800",
      "delay": 1.0,
      "description": "向下滚动查看更多内容"
    },
    {
      "action": "browser_screenshot",
      "value": "douyin_search_result.png",
      "delay": 1.0,
      "description": "截图保存结果"
    },
    {
      "action": "browser_close",
      "delay": 1.0,
      "description": "关闭浏览器"
    }
  ],
  "max_retries": 2
}
```

- [ ] **Step 2: 验证 JSON 格式**

```bash
py -c "import json; json.load(open('examples/douyin_search.json')); print('JSON valid')"
```

Expected: "JSON valid"

- [ ] **Step 3: 创建 README 说明**

创建 `examples/README.md`：

```markdown
# 示例任务

## 抖音搜索 (douyin_search.json)

在抖音网页版搜索UP主并查看视频。

### 使用方法

1. 确保已登录抖音网页版（cookies 会保留）
2. 运行任务：
   ```bash
   py -m src execute examples/douyin_search.json
   ```

### 自定义搜索

编辑 `douyin_search.json`，修改第 4 个任务的 `value`：

```json
{
  "action": "browser_type",
  "target": "[data-e2e='search-input']",
  "value": "你想搜索的UP主名称"
}
```

### 注意事项

- 抖音网站结构可能变化，如果失败请检查选择器
- 首次运行需要登录抖音账号
- 截图保存在当前目录
```

- [ ] **Step 4: 提交**

```bash
git add examples/
git commit -m "feat(examples): add douyin search example task"
```

---

## Task 6: 更新 CLI 支持

**Files:**
- Modify: `src/__main__.py`

**目标:** 添加浏览器相关 CLI 命令和选项

- [ ] **Step 1: 添加浏览器检查命令**

在 `src/__main__.py` 中添加：

```python
def cmd_browser_check(args):
    """检查浏览器安装状态"""
    try:
        from playwright.sync_api import sync_playwright
        
        print("检查 Playwright 浏览器安装状态...")
        
        with sync_playwright() as p:
            for browser_type in ["chromium", "firefox", "webkit"]:
                try:
                    browser = getattr(p, browser_type).launch(headless=True)
                    browser.close()
                    print(f"  ✓ {browser_type}: 已安装")
                except Exception as e:
                    print(f"  ✗ {browser_type}: 未安装 ({e})")
        
        print("\n安装浏览器命令:")
        print("  playwright install chromium")
        print("  playwright install firefox")
        print("  playwright install webkit")
        
    except ImportError:
        print("✗ Playwright 未安装")
        print("  运行: pip install playwright")

# 在 subparsers 中添加
browser_parser = subparsers.add_parser("browser", help="浏览器相关命令")
browser_parser.add_argument("command", choices=["check"], help="浏览器命令")
browser_parser.set_defaults(func=cmd_browser_check)
```

- [ ] **Step 2: 添加执行选项**

修改 `cmd_execute`，添加 headless 选项：

```python
def cmd_execute(args):
    """执行任务"""
    from src.core.executor import TaskExecutor
    from src.core.config import Config
    
    config = Config()
    if args.headless:
        config.browser_headless = True
    
    executor = TaskExecutor(config=config)
    # ... 其余代码

# 添加参数
execute_parser.add_argument("--headless", action="store_true", 
                           help="浏览器无头模式")
```

- [ ] **Step 3: 测试 CLI**

```bash
py -m src browser check
```

Expected: 显示浏览器安装状态

- [ ] **Step 4: 提交**

```bash
git add src/__main__.py
git commit -m "feat(cli): add browser check command and headless option"
```

---

## Task 7: 最终验证

**目标:** 运行所有测试，确保功能完整

- [ ] **Step 1: 运行浏览器模块测试**

```bash
py -m pytest tests/test_browser_*.py -v
```

Expected: 所有测试 PASS

- [ ] **Step 2: 运行所有测试**

```bash
py -m pytest tests/ -v --tb=short
```

Expected: 全部 PASS

- [ ] **Step 3: 验证示例任务格式**

```bash
py -m src validate examples/douyin_search.json
```

（如果 validate 命令不存在，则仅检查 JSON 格式）

- [ ] **Step 4: 创建集成测试脚本**

创建 `test_integration.py`：

```python
"""集成测试 - 验证浏览器功能"""
import sys
sys.path.insert(0, '.')

from src.core.executor import TaskExecutor
from src.core.models import Task, TaskSequence

print("=" * 50)
print("浏览器集成测试")
print("=" * 50)

# 测试 1: 启动和关闭
print("\n[Test 1] 浏览器启动和关闭...")
executor = TaskExecutor()
sequence = TaskSequence(
    name="基础测试",
    tasks=[
        Task("browser_launch", value="chromium", delay=2.0),
        Task("browser_goto", value="https://example.com", delay=2.0),
        Task("browser_close", delay=1.0),
    ]
)
result = executor.execute(sequence)
assert result.success, f"测试失败: {result.error}"
print("✓ 通过")

print("\n" + "=" * 50)
print("所有测试通过！")
print("=" * 50)
```

- [ ] **Step 5: 运行集成测试**

```bash
py test_integration.py
```

Expected: "所有测试通过！"

- [ ] **Step 6: 清理并提交**

```bash
Remove-Item test_integration.py
git add -A
git commit -m "test: add integration tests for browser automation"
```

---

## 完成清单

- [ ] Task 0: 安装 Playwright 依赖
- [ ] Task 1: 核心数据模型扩展
- [ ] Task 2: BrowserController 实现
- [ ] Task 3: BrowserActionHandler 实现
- [ ] Task 4: 集成到 TaskExecutor
- [ ] Task 5: 抖音搜索示例任务
- [ ] Task 6: 更新 CLI 支持
- [ ] Task 7: 最终验证

---

## 执行方式选择

**Plan complete and saved to `docs/superpowers/plans/2026-04-12-browser-integration.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review

**Which approach?**
