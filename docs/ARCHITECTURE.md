# 技术架构设计

**文档版本**: v1.0  
**更新日期**: 2026-04-10

---

## 1. 架构概览

### 1.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Python API │  │    CLI       │  │  Test Suite  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│                  (TaskExecutor Engine)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Task Parser  │  │ State Manager│  │ Error Handler│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Perception  │    │    Action    │    │   Knowledge  │
│    Layer     │    │    Layer     │    │    Base      │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 1.2 核心设计原则

1. **模块化**: 每层可独立替换实现
2. **可观测**: 每个操作都有日志和截图记录
3. **容错性**: 失败自动重试，错误可追溯
4. **可扩展**: 新工具可通过统一接口接入

---

## 2. 感知层 (Perception Layer)

### 2.1 职责
- 获取屏幕状态 (截图)
- 识别可交互元素
- 提取文字信息

### 2.2 组件设计

#### ScreenCapture
```python
class ScreenCapture:
    """屏幕截图管理器"""
    
    def capture(self, region: Optional[Tuple] = None) -> np.ndarray:
        """
        截取屏幕
        
        Args:
            region: (x, y, w, h) 可选，None则全屏
        
        Returns:
            BGR格式的numpy数组
        """
        pass
    
    def save(self, image: np.ndarray, path: Path):
        """保存截图用于调试"""
        pass
```

#### ElementDetector
```python
class ElementDetector:
    """UI元素检测器 (基于YOLOv8)"""
    
    def __init__(self, model_path: str, conf_threshold: float = 0.5):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
    
    def detect(self, image: np.ndarray) -> List[UIElement]:
        """
        检测图像中的所有UI元素
        
        Args:
            image: BGR格式的numpy数组
        
        Returns:
            UIElement列表，按置信度排序
        """
        results = self.model(image, conf=self.conf_threshold)
        return self._parse_results(results)
    
    def detect_by_type(self, image: np.ndarray, 
                       element_type: str) -> List[UIElement]:
        """按类型筛选元素"""
        elements = self.detect(image)
        return [e for e in elements if e.element_type == element_type]
```

#### TextRecognizer
```python
class TextRecognizer:
    """文字识别器 (基于PaddleOCR)"""
    
    def __init__(self, lang: str = "ch"):
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)
    
    def recognize(self, image: np.ndarray) -> List[TextBox]:
        """
        识别图像中的所有文字
        
        Returns:
            TextBox列表，包含文字内容和位置
        """
        pass
    
    def find_text(self, image: np.ndarray, 
                  target: str) -> Optional[Tuple[int, int]]:
        """
        查找指定文字的位置
        
        Returns:
            文字中心点坐标 (x, y)，未找到返回None
        """
        pass
```

### 2.3 数据模型

```python
@dataclass
class UIElement:
    """UI元素"""
    id: str                      # 唯一ID (自动生成)
    bbox: BoundingBox            # 边界框
    element_type: ElementType    # 元素类型
    confidence: float           # 置信度 0-1
    text: Optional[str] = None  # 关联文字
    
    @property
    def center(self) -> Tuple[int, int]:
        """中心点坐标"""
        return (
            (self.bbox.x1 + self.bbox.x2) // 2,
            (self.bbox.y1 + self.bbox.y2) // 2
        )

@dataclass  
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1

class ElementType(Enum):
    BUTTON = "button"
    INPUT = "input"
    ICON = "icon"
    WINDOW = "window"
```

---

## 3. 行动层 (Action Layer)

### 3.1 职责
- 执行鼠标操作
- 执行键盘操作
- 管理应用程序

### 3.2 组件设计

#### MouseController
```python
class MouseController:
    """鼠标控制器 (基于PyAutoGUI)"""
    
    def __init__(self, smooth_move: bool = True):
        self.smooth_move = smooth_move
        pyautogui.FAILSAFE = True  # 鼠标移到角落终止
    
    def move(self, x: int, y: int, duration: float = 0.5):
        """移动鼠标到指定位置"""
        pyautogui.moveTo(x, y, duration=duration)
    
    def click(self, x: int, y: int, button: str = "left", 
              clicks: int = 1):
        """点击指定位置"""
        self.move(x, y)
        pyautogui.click(button=button, clicks=clicks)
    
    def scroll(self, amount: int, x: int = None, y: int = None):
        """滚动鼠标"""
        if x is not None and y is not None:
            self.move(x, y)
        pyautogui.scroll(amount)
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        return pyautogui.position()
```

#### KeyboardController
```python
class KeyboardController:
    """键盘控制器"""
    
    def type(self, text: str, interval: float = 0.01):
        """输入文字"""
        pyautogui.typewrite(text, interval=interval)
    
    def press(self, key: str):
        """按下并释放单个键"""
        pyautogui.press(key)
    
    def hotkey(self, *keys: str):
        """按下组合键"""
        pyautogui.hotkey(*keys)
    
    def hold(self, key: str):
        """按住某个键 (配合release使用)"""
        pyautogui.keyDown(key)
    
    def release(self, key: str):
        """释放某个键"""
        pyautogui.keyUp(key)
```

#### ApplicationManager
```python
class ApplicationManager:
    """应用管理器"""
    
    # MVP支持的应用映射
    APP_MAP = {
        "calculator": {
            "linux": "gnome-calculator",
            "darwin": "Calculator",  # macOS
            "win32": "calc.exe"
        },
        "notepad": {
            "linux": "gedit",
            "darwin": "TextEdit",
            "win32": "notepad.exe"
        },
        "chrome": {
            "linux": "google-chrome",
            "darwin": "Google Chrome",
            "win32": "chrome.exe"
        }
    }
    
    def launch(self, app_name: str) -> bool:
        """启动应用"""
        system = platform.system().lower()
        cmd = self.APP_MAP.get(app_name, {}).get(system)
        if cmd:
            subprocess.Popen(cmd, shell=True)
            return True
        return False
    
    def is_running(self, app_name: str) -> bool:
        """检查应用是否运行"""
        pass
    
    def activate_window(self, title_pattern: str) -> bool:
        """激活匹配标题的窗口"""
        pass
```

---

## 4. 协调层 (Orchestration Layer)

### 4.1 职责
- 解析任务
- 维护执行状态
- 协调感知层和行动层

### 4.2 TaskExecutor 设计

```python
class TaskExecutor:
    """任务执行引擎"""
    
    def __init__(self):
        self.screen = ScreenCapture()
        self.detector = ElementDetector()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.app_manager = ApplicationManager()
        self.state = ExecutionState()
        self.logger = logging.getLogger(__name__)
    
    def execute(self, sequence: TaskSequence) -> ExecutionResult:
        """
        执行任务序列
        
        执行流程:
        1. 初始化状态
        2. 对每个任务:
           a. 截图感知
           b. 解析目标
           c. 执行操作
           d. 验证结果
           e. 处理错误
        3. 返回结果
        """
        self.state.start(sequence)
        
        try:
            for i, task in enumerate(sequence.tasks):
                self.logger.info(f"Executing task {i+1}: {task.action}")
                
                # 执行前截图
                screenshot = self.screen.capture()
                self.state.add_screenshot(screenshot)
                
                # 执行任务
                success = self._execute_single_task(task, screenshot)
                
                if not success:
                    if not self._handle_failure(task, i):
                        return self.state.fail(f"Task {i+1} failed")
                
                # 等待
                time.sleep(task.delay)
            
            return self.state.complete()
            
        except Exception as e:
            self.logger.exception("Execution failed")
            return self.state.fail(str(e))
    
    def _execute_single_task(self, task: Task, 
                             screenshot: np.ndarray) -> bool:
        """执行单个任务"""
        
        if task.action == "launch":
            return self.app_manager.launch(task.target)
        
        elif task.action == "click":
            # 解析目标为坐标
            x, y = self._resolve_target(task.target, screenshot)
            self.mouse.click(x, y)
            return True
        
        elif task.action == "type":
            if task.target:
                x, y = self._resolve_target(task.target, screenshot)
                self.mouse.click(x, y)  # 先聚焦
            self.keyboard.type(task.value)
            return True
        
        elif task.action == "press":
            self.keyboard.press(task.value or task.target)
            return True
        
        elif task.action == "wait":
            time.sleep(task.delay)
            return True
        
        return False
    
    def _resolve_target(self, target: str, 
                        screenshot: np.ndarray) -> Tuple[int, int]:
        """
        解析目标为屏幕坐标
        
        target可以是:
        - 元素ID: "elem_001"
        - 坐标: "100,200"
        - 元素类型: "button"
        """
        # 解析坐标
        if "," in target:
            x, y = map(int, target.split(","))
            return x, y
        
        # 检测元素
        elements = self.detector.detect(screenshot)
        
        # 匹配元素ID或类型
        for elem in elements:
            if elem.id == target or elem.element_type == target:
                return elem.center
        
        raise ValueError(f"Target not found: {target}")
```

---

## 5. 状态管理

### 5.1 ExecutionState

```python
class ExecutionState:
    """执行状态管理"""
    
    def __init__(self):
        self.sequence: Optional[TaskSequence] = None
        self.current_step: int = 0
        self.screenshots: List[np.ndarray] = []
        self.logs: List[Dict] = []
        self.start_time: Optional[float] = None
        self.status: str = "idle"  # idle, running, success, failed
    
    def start(self, sequence: TaskSequence):
        """开始执行"""
        self.sequence = sequence
        self.current_step = 0
        self.start_time = time.time()
        self.status = "running"
    
    def add_screenshot(self, image: np.ndarray):
        """添加截图"""
        self.screenshots.append(image.copy())
    
    def log(self, action: str, details: Dict):
        """记录日志"""
        self.logs.append({
            "timestamp": time.time(),
            "action": action,
            "details": details
        })
    
    def complete(self) -> ExecutionResult:
        """标记完成"""
        self.status = "success"
        return ExecutionResult(
            success=True,
            completed_steps=self.current_step,
            duration=time.time() - self.start_time,
            screenshots=self.screenshots,
            logs=self.logs
        )
    
    def fail(self, error: str) -> ExecutionResult:
        """标记失败"""
        self.status = "failed"
        return ExecutionResult(
            success=False,
            error=error,
            completed_steps=self.current_step,
            duration=time.time() - self.start_time,
            screenshots=self.screenshots,
            logs=self.logs
        )
```

---

## 6. 错误处理策略

### 6.1 错误类型

| 错误类型 | 示例 | 处理策略 |
|----------|------|----------|
| 元素未找到 | 目标按钮不在屏幕 | 重试截图检测 |
| 操作超时 | 应用启动慢 | 增加等待时间 |
| 定位偏移 | 坐标点击未命中 | 扩大点击区域 |
| 权限问题 | 无法控制系统 | 提示用户授权 |

### 6.2 重试机制

```python
class RetryHandler:
    """重试处理器"""
    
    def __init__(self, max_retries: int = 3, 
                 delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay
    
    def execute_with_retry(self, fn: Callable, *args, **kwargs):
        """带重试的执行"""
        for attempt in range(self.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.delay * (attempt + 1))
```

---

## 7. 扩展点设计

### 7.1 新工具接入接口

```python
class BaseTool(ABC):
    """工具基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def execute(self, params: Dict) -> ToolResult:
        pass

# 示例: 浏览器工具
class BrowserTool(BaseTool):
    @property
    def name(self) -> str:
        return "browser"
    
    def execute(self, params: Dict) -> ToolResult:
        # 调用 agent-browser
        pass
```

### 7.2 插件机制

```python
class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: List[BaseTool] = []
    
    def register(self, tool: BaseTool):
        self.plugins.append(tool)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None
```

---

## 8. 性能考虑

### 8.1 优化策略

1. **模型优化**
   - 使用 YOLOv8n (轻量版)
   - 图片预处理：降采样到 640x640
   - CPU推理即可，无需GPU

2. **缓存机制**
   - 缓存最近一次的元素检测结果
   - 如果屏幕无变化，复用结果

3. **并发处理**
   - 截图和检测可并行
   - OCR延迟高，可异步处理

### 8.2 性能目标

| 操作 | 目标延迟 | 优化方案 |
|------|----------|----------|
| 截图 | < 500ms | mss库替代PIL |
| 元素检测 | < 2s | YOLOv8n + 降采样 |
| OCR | < 1s | 区域裁剪后识别 |
| 鼠标移动 | < 500ms | PyAutoGUI默认 |

---

**设计Agent**: 鲲鹏  
**实现Agent**: [待指定]  
**审核状态**: 待开发Agent确认
