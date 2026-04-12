# 浏览器录制功能实现计划 (v0.2.1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** 扩展录制器支持浏览器操作录制，自动检测桌面/浏览器模式，生成可执行的混合任务序列。

**Architecture:** HybridRecorder 自动检测窗口类型，BrowserRecorder 通过 Playwright 获取 CSS 选择器，DesktopRecorder 保持现有坐标录制。

**Tech Stack:** Python 3.12, Playwright, pynput, pygetwindow

---

## 文件结构

```
src/
├── recording/
│   ├── __init__.py              # 导出 HybridRecorder, BrowserRecorder
│   ├── window_detector.py       # 窗口类型检测
│   ├── browser_recorder.py      # 浏览器录制器
│   └── hybrid_recorder.py       # 混合录制器
├── core/
│   └── models.py                # 添加 RecordingMode 枚举
└── __main__.py                  # 添加 --mode 参数

tests/
├── test_window_detector.py
├── test_browser_recorder.py
└── test_hybrid_recorder.py
```

---

## Task 1: 窗口检测器 (WindowDetector)

**Files:**
- Create: `src/recording/window_detector.py`
- Test: `tests/test_window_detector.py`

**目标:** 检测当前活动窗口是否为浏览器

- [ ] **Step 1: 编写失败测试**

创建 `tests/test_window_detector.py`：

```python
"""WindowDetector 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestWindowDetector:
    """WindowDetector 测试类"""
    
    def test_is_browser_window_chrome(self):
        """测试识别 Chrome 窗口"""
        from src.recording.window_detector import is_browser_window
        
        assert is_browser_window("抖音 - Google Chrome") is True
        assert is_browser_window("GitHub: Let's build from here - Chrome") is True
    
    def test_is_browser_window_edge(self):
        """测试识别 Edge 窗口"""
        from src.recording.window_detector import is_browser_window
        
        assert is_browser_window("Bing - Microsoft​ Edge") is True
    
    def test_is_browser_window_notepad(self):
        """测试识别非浏览器窗口"""
        from src.recording.window_detector import is_browser_window
        
        assert is_browser_window("无标题 - 记事本") is False
        assert is_browser_window("计算器") is False
    
    def test_get_active_window_title(self):
        """测试获取当前窗口标题"""
        from src.recording.window_detector import get_active_window_title
        
        title = get_active_window_title()
        assert isinstance(title, str)
        assert len(title) >= 0  # 可能为空，但不应该是 None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
py -m pytest tests/test_window_detector.py -v
```

Expected: FAIL (导入错误)

- [ ] **Step 3: 实现 WindowDetector**

创建 `src/recording/window_detector.py`：

```python
"""窗口检测器 - 检测当前活动窗口类型"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 浏览器窗口关键词
BROWSER_KEYWORDS = [
    "chrome", "谷歌浏览器", "chromium",
    "edge", "microsoft edge",
    "firefox", "火狐",
    "safari",
]


def get_active_window_title() -> Optional[str]:
    """
    获取当前活动窗口的标题
    
    Returns:
        窗口标题，如果获取失败返回 None
    """
    try:
        # Windows 平台
        import win32gui
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)
        return title
    except ImportError:
        logger.warning("win32gui 未安装，尝试使用 pygetwindow")
    
    try:
        import pygetwindow as gw
        window = gw.getActiveWindow()
        if window:
            return window.title
    except Exception as e:
        logger.error(f"获取窗口标题失败: {e}")
    
    return None


def is_browser_window(title: Optional[str]) -> bool:
    """
    判断窗口标题是否为浏览器
    
    Args:
        title: 窗口标题
        
    Returns:
        是否为浏览器窗口
    """
    if not title:
        return False
    
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in BROWSER_KEYWORDS)


def get_current_recording_mode() -> str:
    """
    获取当前应该使用的录制模式
    
    Returns:
        "browser" 或 "desktop"
    """
    title = get_active_window_title()
    mode = "browser" if is_browser_window(title) else "desktop"
    logger.debug(f"当前窗口: {title}, 模式: {mode}")
    return mode
```

- [ ] **Step 4: 安装依赖**

```bash
pip install pywin32 pygetwindow
```

添加到 `requirements.txt`：
```
pywin32>=306
pygetwindow>=0.0.9
```

- [ ] **Step 5: 运行测试确认通过**

```bash
py -m pytest tests/test_window_detector.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 6: 提交**

```bash
git add src/recording/ tests/test_window_detector.py requirements.txt
git commit -m "feat(recording): add WindowDetector to detect browser windows"
```

---

## Task 2: 数据模型扩展

**Files:**
- Modify: `src/core/models.py`

**目标:** 添加 RecordingMode 枚举和扩展 RecordingEvent

- [ ] **Step 1: 添加 RecordingMode 枚举**

在 `src/core/models.py` 中添加：

```python
from enum import Enum

class RecordingMode(Enum):
    """录制模式"""
    DESKTOP = "desktop"      # 桌面录制（坐标）
    BROWSER = "browser"      # 浏览器录制（选择器）
    HYBRID = "hybrid"        # 混合模式（自动检测）
```

- [ ] **Step 2: 扩展 RecordingEvent**

修改 `RecordingEvent` 类：

```python
@dataclass
class RecordingEvent:
    """录制的事件"""
    action: str
    timestamp: float
    target: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    value: Optional[str] = None
    element_type: Optional[str] = None
    recording_mode: RecordingMode = RecordingMode.DESKTOP  # 新增
    css_selector: Optional[str] = None  # 新增: CSS 选择器
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "action": self.action,
            "timestamp": self.timestamp,
            "target": self.target,
            "position": self.position,
            "value": self.value,
            "element_type": self.element_type,
            "recording_mode": self.recording_mode.value,
            "css_selector": self.css_selector,
        }
```

- [ ] **Step 3: 验证导入**

```bash
py -c "from src.core.models import RecordingMode, RecordingEvent; print('OK')"
```

Expected: "OK"

- [ ] **Step 4: 提交**

```bash
git add src/core/models.py
git commit -m "feat(models): add RecordingMode enum and extend RecordingEvent"
```

---

## Task 3: BrowserRecorder - 浏览器录制器

**Files:**
- Create: `src/recording/browser_recorder.py`
- Test: `tests/test_browser_recorder.py`

**目标:** 录制浏览器操作，获取 CSS 选择器

- [ ] **Step 1: 编写失败测试**

创建 `tests/test_browser_recorder.py`：

```python
"""BrowserRecorder 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBrowserRecorder:
    """BrowserRecorder 测试类"""
    
    def test_recorder_creation(self):
        """测试创建 BrowserRecorder"""
        from src.recording.browser_recorder import BrowserRecorder
        
        recorder = BrowserRecorder(user_data_dir="browser_data")
        
        assert recorder.user_data_dir == "browser_data"
        assert recorder.is_connected is False
    
    def test_connect_to_browser(self):
        """测试连接到浏览器"""
        from src.recording.browser_recorder import BrowserRecorder
        
        recorder = BrowserRecorder()
        
        # 先启动浏览器
        from src.browser.controller import BrowserController
        controller = BrowserController(user_data_dir="browser_data")
        controller.launch()
        
        # 尝试连接
        connected = recorder.connect()
        
        # 清理
        controller.close()
        
        # 连接可能成功也可能失败，取决于环境
        assert connected is True or connected is False
```

- [ ] **Step 2: 运行测试确认失败**

```bash
py -m pytest tests/test_browser_recorder.py -v
```

Expected: FAIL (导入错误)

- [ ] **Step 3: 实现 BrowserRecorder**

创建 `src/recording/browser_recorder.py`：

```python
"""浏览器录制器 - 录制网页操作"""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

from playwright.sync_api import sync_playwright

from ..browser.controller import BrowserController
from ..core.models import RecordingEvent, RecordingMode

logger = logging.getLogger(__name__)


class BrowserRecorder:
    """浏览器录制器"""
    
    def __init__(self, user_data_dir: str = "browser_data"):
        """
        初始化浏览器录制器
        
        Args:
            user_data_dir: 浏览器用户数据目录
        """
        self.user_data_dir = user_data_dir
        self._controller: Optional[BrowserController] = None
        self._playwright = None
        self._browser = None
        self._page = None
        self._last_event: Optional[Dict] = None
        
        logger.info(f"BrowserRecorder 初始化: user_data_dir={user_data_dir}")
    
    @property
    def is_connected(self) -> bool:
        """是否已连接到浏览器"""
        return self._page is not None and self._browser is not None
    
    def connect(self) -> bool:
        """
        连接到现有浏览器
        
        Returns:
            是否成功连接
        """
        try:
            # 方法1: 使用 BrowserController 启动浏览器
            self._controller = BrowserController(
                browser_type="chromium",
                headless=False,
                user_data_dir=self.user_data_dir
            )
            self._controller.launch()
            self._page = self._controller.page
            
            # 注入监听脚本
            self._inject_listeners()
            
            logger.info("BrowserRecorder 已连接到浏览器")
            return True
            
        except Exception as e:
            logger.error(f"连接浏览器失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self._controller:
            self._controller.close()
            self._controller = None
        self._page = None
        logger.info("BrowserRecorder 已断开连接")
    
    def _inject_listeners(self):
        """在页面中注入事件监听脚本"""
        if not self._page:
            return
        
        self._page.evaluate("""
            (function() {
                if (window.__browserRecorderInjected) return;
                window.__browserRecorderInjected = true;
                
                window.__lastBrowserEvent = null;
                
                // 获取元素选择器
                function getSelector(element) {
                    if (!element) return null;
                    
                    // 1. 尝试 ID
                    if (element.id) return '#' + element.id;
                    
                    // 2. 尝试 data-e2e 等测试属性
                    if (element.dataset.e2e) return `[data-e2e="${element.dataset.e2e}"]`;
                    if (element.dataset.testid) return `[data-testid="${element.dataset.testid}"]`;
                    
                    // 3. 尝试 class
                    if (element.className) {
                        const classes = element.className.split(' ').filter(c => c.length > 0);
                        if (classes.length > 0) return '.' + classes[0];
                    }
                    
                    // 4. 使用 tag name + nth-child
                    const tag = element.tagName.toLowerCase();
                    return tag;
                }
                
                // 监听点击事件
                document.addEventListener('click', function(e) {
                    window.__lastBrowserEvent = {
                        type: 'click',
                        selector: getSelector(e.target),
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now()
                    };
                }, true);
                
                // 监听输入事件
                document.addEventListener('input', function(e) {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                        window.__lastBrowserEvent = {
                            type: 'input',
                            selector: getSelector(e.target),
                            value: e.target.value,
                            timestamp: Date.now()
                        };
                    }
                }, true);
                
                console.log('BrowserRecorder: 事件监听已注入');
            })();
        """)
        
        logger.debug("事件监听脚本已注入")
    
    def get_last_event(self) -> Optional[RecordingEvent]:
        """
        获取最后一次浏览器事件
        
        Returns:
            RecordingEvent 或 None
        """
        if not self._page:
            return None
        
        try:
            event_data = self._page.evaluate("window.__lastBrowserEvent")
            
            if not event_data:
                return None
            
            # 转换为 RecordingEvent
            action_map = {
                'click': 'browser_click',
                'input': 'browser_type',
            }
            
            action = action_map.get(event_data['type'], event_data['type'])
            
            return RecordingEvent(
                action=action,
                timestamp=time.time(),
                target=event_data.get('selector'),
                position=(event_data.get('x', 0), event_data.get('y', 0)),
                value=event_data.get('value'),
                recording_mode=RecordingMode.BROWSER,
                css_selector=event_data.get('selector')
            )
            
        except Exception as e:
            logger.error(f"获取事件失败: {e}")
            return None
    
    def clear_last_event(self):
        """清除最后一个事件"""
        if self._page:
            self._page.evaluate("window.__lastBrowserEvent = null")
```

- [ ] **Step 4: 运行测试**

```bash
py -m pytest tests/test_browser_recorder.py -v
```

Expected: PASS (可能部分测试跳过)

- [ ] **Step 5: 提交**

```bash
git add src/recording/browser_recorder.py tests/test_browser_recorder.py
git commit -m "feat(recording): add BrowserRecorder for recording browser actions"
```

---

## Task 4: HybridRecorder - 混合录制器

**Files:**
- Create: `src/recording/hybrid_recorder.py`
- Create: `src/recording/__init__.py`
- Modify: `src/core/recorder.py` (可选，或保持独立)

**目标:** 主录制器，自动切换桌面/浏览器模式

- [ ] **Step 1: 创建 recording 模块初始化文件**

创建 `src/recording/__init__.py`：

```python
"""录制模块 - 支持桌面和浏览器操作录制"""

from .hybrid_recorder import HybridRecorder
from .browser_recorder import BrowserRecorder
from .window_detector import (
    get_active_window_title,
    is_browser_window,
    get_current_recording_mode
)

__all__ = [
    "HybridRecorder",
    "BrowserRecorder",
    "get_active_window_title",
    "is_browser_window",
    "get_current_recording_mode",
]
```

- [ ] **Step 2: 实现 HybridRecorder**

创建 `src/recording/hybrid_recorder.py`：

```python
"""混合录制器 - 自动检测并录制桌面或浏览器操作"""

import time
import logging
from typing import Optional, List
from datetime import datetime

from pynput import mouse, keyboard

from ..core.models import RecordingEvent, RecordingSession, RecordingMode
from ..utils.recording_overlay import RecordingOverlay
from .window_detector import get_current_recording_mode
from .browser_recorder import BrowserRecorder

logger = logging.getLogger(__name__)


class HybridRecorder:
    """混合录制器"""
    
    def __init__(self, mode: RecordingMode = RecordingMode.HYBRID, 
                 user_data_dir: str = "browser_data"):
        """
        初始化混合录制器
        
        Args:
            mode: 录制模式
            user_data_dir: 浏览器用户数据目录
        """
        self.mode = mode
        self.user_data_dir = user_data_dir
        
        self.is_recording = False
        self._session_name: Optional[str] = None
        self._start_time: Optional[float] = None
        self._events: List[RecordingEvent] = []
        
        # UI
        self._overlay = RecordingOverlay()
        
        # 监听器
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        
        # 浏览器录制器
        self._browser_recorder: Optional[BrowserRecorder] = None
        
        # 输入缓冲区
        self._input_buffer = ""
        self._last_input_time = 0.0
        
        logger.info(f"HybridRecorder 初始化: mode={mode.value}")
    
    def start_recording(self, name: Optional[str] = None):
        """开始录制"""
        if self.is_recording:
            raise RuntimeError("已经在录制中")
        
        self.is_recording = True
        self._session_name = name or f"录制任务 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self._start_time = time.time()
        self._events = []
        self._input_buffer = ""
        
        # 显示录制指示器
        self._overlay.show()
        
        # 启动浏览器录制器（如果是 BROWSER 或 HYBRID 模式）
        if self.mode in (RecordingMode.BROWSER, RecordingMode.HYBRID):
            self._browser_recorder = BrowserRecorder(self.user_data_dir)
            if self._browser_recorder.connect():
                logger.info("浏览器录制器已连接")
            else:
                logger.warning("浏览器录制器连接失败，将使用桌面录制")
        
        # 启动鼠标监听
        self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self._mouse_listener.start()
        
        # 启动键盘监听
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.start()
        
        logger.info(f"🎬 开始录制: {self._session_name} (模式: {self.mode.value})")
        print(f"🎬 开始录制... (模式: {self.mode.value}, 按 Ctrl+R 停止)")
    
    def stop_recording(self) -> RecordingSession:
        """停止录制"""
        if not self.is_recording:
            raise RuntimeError("未在录制中")
        
        # 处理剩余输入
        self._flush_input_buffer()
        
        self.is_recording = False
        
        # 停止监听器
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        # 断开浏览器录制器
        if self._browser_recorder:
            self._browser_recorder.disconnect()
            self._browser_recorder = None
        
        # 隐藏指示器
        self._overlay.hide()
        
        # 创建会话
        session = RecordingSession(
            name=self._session_name,
            start_time=datetime.fromtimestamp(self._start_time),
            events=self._events.copy()
        )
        
        logger.info(f"✅ 录制完成: {len(self._events)} 个事件")
        print(f"✅ 录制完成: {len(self._events)} 个事件")
        
        return session
    
    def _on_mouse_click(self, x, y, button, pressed):
        """鼠标点击回调"""
        if not pressed or not self.is_recording:
            return
        
        # 处理输入缓冲区
        self._flush_input_buffer()
        
        # 检测当前模式
        current_mode = self._detect_current_mode()
        
        if current_mode == RecordingMode.BROWSER and self._browser_recorder:
            # 尝试获取浏览器事件
            time.sleep(0.1)  # 等待 JavaScript 记录事件
            event = self._browser_recorder.get_last_event()
            
            if event and event.action == "browser_click":
                # 使用浏览器录制的事件
                event.timestamp = time.time() - self._start_time
                self._events.append(event)
                logger.info(f"🌐 浏览器点击: {event.css_selector}")
                self._browser_recorder.clear_last_event()
                return
        
        # 使用桌面录制
        from ..perception.screen import ScreenCapture
        from ..perception.detector import ElementDetector
        
        screen = ScreenCapture()
        detector = ElementDetector()
        
        try:
            screenshot = screen.capture()
            elements = detector.detect(screenshot)
            
            # 查找点击位置的元素
            target = None
            for elem in elements:
                if (elem.bbox.x1 <= x <= elem.bbox.x2 and 
                    elem.bbox.y1 <= y <= elem.bbox.y2):
                    target = elem.id
                    break
            
            event = RecordingEvent(
                action="click",
                timestamp=time.time() - self._start_time,
                target=target or f"{int(x)},{int(y)}",
                position=(int(x), int(y)),
                recording_mode=RecordingMode.DESKTOP
            )
            self._events.append(event)
            logger.info(f"🖱️ 桌面点击: ({x}, {y})")
            
        except Exception as e:
            logger.error(f"处理鼠标点击失败: {e}")
    
    def _on_key_press(self, key):
        """按键按下回调"""
        if not self.is_recording:
            return
        
        try:
            char = key.char
            self._input_buffer += char
            self._last_input_time = time.time()
        except AttributeError:
            # 特殊按键
            if key == keyboard.Key.enter:
                self._flush_input_buffer()
                event = RecordingEvent(
                    action="press",
                    timestamp=time.time() - self._start_time,
                    value="enter",
                    recording_mode=RecordingMode.DESKTOP
                )
                self._events.append(event)
    
    def _on_key_release(self, key):
        """按键释放回调"""
        pass
    
    def _flush_input_buffer(self):
        """将输入缓冲区中的内容保存为事件"""
        if self._input_buffer:
            event = RecordingEvent(
                action="type",
                timestamp=self._last_input_time - self._start_time,
                value=self._input_buffer,
                recording_mode=RecordingMode.DESKTOP
            )
            self._events.append(event)
            logger.debug(f"⌨️ 输入: {self._input_buffer}")
            self._input_buffer = ""
    
    def _detect_current_mode(self) -> RecordingMode:
        """检测当前录制模式"""
        if self.mode != RecordingMode.HYBRID:
            return self.mode
        
        # 自动检测
        mode_str = get_current_recording_mode()
        return RecordingMode.BROWSER if mode_str == "browser" else RecordingMode.DESKTOP
```

- [ ] **Step 3: 提交**

```bash
git add src/recording/
git commit -m "feat(recording): add HybridRecorder with automatic mode detection"
```

---

## Task 5: CLI 扩展

**Files:**
- Modify: `src/__main__.py`

**目标:** 添加 `--mode` 参数支持混合录制

- [ ] **Step 1: 修改 CLI**

修改 `src/__main__.py` 中的 `cmd_record` 函数：

```python
def cmd_record(args):
    """录制任务命令"""
    from src.recording.hybrid_recorder import HybridRecorder
    from src.core.models import RecordingMode
    
    # 解析模式
    mode_map = {
        "desktop": RecordingMode.DESKTOP,
        "browser": RecordingMode.BROWSER,
        "hybrid": RecordingMode.HYBRID,
    }
    mode = mode_map.get(args.mode, RecordingMode.HYBRID)
    
    # 创建录制器
    recorder = HybridRecorder(mode=mode)
    
    try:
        recorder.start_recording()
        print(f"录制中... 按 Ctrl+R 停止")
        
        # 等待停止
        import time
        while recorder.is_recording:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        if recorder.is_recording:
            session = recorder.stop_recording()
            
            # 保存文件
            output_path = args.output or f"recorded_{int(time.time())}.json"
            session.save_to_file(output_path)
            print(f"已保存到: {output_path}")
```

- [ ] **Step 2: 添加参数**

在 `record` subparser 中添加：

```python
record_parser.add_argument(
    "--mode", 
    choices=["desktop", "browser", "hybrid"],
    default="hybrid",
    help="录制模式: desktop(桌面), browser(浏览器), hybrid(自动检测, 默认)"
)
```

- [ ] **Step 3: 提交**

```bash
git add src/__main__.py
git commit -m "feat(cli): add --mode parameter for hybrid recording"
```

---

## Task 6: 集成测试与示例

**Files:**
- Create: `examples/recorded_douyin_example.json`
- Create: `tests/test_hybrid_recorder.py`

**目标:** 验证完整录制流程

- [ ] **Step 1: 创建集成测试**

创建 `tests/test_hybrid_recorder.py`：

```python
"""HybridRecorder 集成测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestHybridRecorder:
    """HybridRecorder 测试"""
    
    def test_recorder_creation(self):
        """测试创建 HybridRecorder"""
        from src.recording.hybrid_recorder import HybridRecorder
        from src.core.models import RecordingMode
        
        recorder = HybridRecorder(mode=RecordingMode.HYBRID)
        
        assert recorder.mode == RecordingMode.HYBRID
        assert recorder.is_recording is False
```

- [ ] **Step 2: 运行所有测试**

```bash
py -m pytest tests/test_recording*.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/ examples/
git commit -m "test: add integration tests for hybrid recording"
```

---

## 完成清单

- [ ] Task 1: WindowDetector 窗口检测器
- [ ] Task 2: 数据模型扩展
- [ ] Task 3: BrowserRecorder 浏览器录制器
- [ ] Task 4: HybridRecorder 混合录制器
- [ ] Task 5: CLI 扩展
- [ ] Task 6: 集成测试

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-12-browser-recording.md`.**

**Execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task

**2. Inline Execution** - Execute tasks in this session

**Which approach?**
