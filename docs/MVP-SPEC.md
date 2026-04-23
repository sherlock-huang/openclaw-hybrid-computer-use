# MVP 详细规格说明书

**文档版本**: v1.0  
**更新日期**: 2026-04-10  
**状态**: 待开发

---

## 1. 概述

### 1.1 文档目的

本文档定义 ClawDesktop MVP (最小可行产品) 的详细技术规格，供开发Agent实现参考。

### 1.2 范围界定

**MVP包含**:
- 屏幕截图与UI元素检测
- 基础鼠标/键盘操作
- 简单任务序列执行
- 错误检测与基础重试

**MVP不包含**:
- 自然语言理解
- 复杂任务规划
- 浏览器集成
- 多显示器支持

---

## 2. 功能规格

### 2.1 核心功能

#### F1: 屏幕感知

**F1.1 屏幕截图**
```python
def capture_screen() -> np.ndarray:
    """
    截取当前屏幕
    
    Returns:
        numpy array (H, W, 3) - BGR格式
    """
    pass
```

**验收标准**:
- 支持 1920x1080 分辨率
- 截图耗时 < 500ms
- 内存占用 < 100MB

**F1.2 元素检测**
```python
def detect_elements(image: np.ndarray) -> List[UIElement]:
    """
    检测屏幕中的可交互元素
    
    Returns:
        List[UIElement] - 检测到的元素列表
    """
    pass

@dataclass
class UIElement:
    id: str              # 唯一标识符 (e.g., "elem_001")
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    element_type: str    # "button", "input", "icon", "text"
    confidence: float    # 0.0 - 1.0
    text: str = ""       # OCR识别的文字 (可选)
```

**检测元素类型** (MVP只需支持):
- `button` - 按钮
- `input` - 输入框
- `icon` - 图标
- `window` - 窗口标题栏

**验收标准**:
- 检测准确率 ≥ 85% (在标准测试集上)
- 检测耗时 < 2秒
- 置信度阈值: 0.5

**F1.3 文字识别 (OCR)**
```python
def recognize_text(image: np.ndarray, bbox: Tuple) -> str:
    """
    识别指定区域的文字
    """
    pass
```

**验收标准**:
- 中英文识别准确率 ≥ 90%
- 耗时 < 500ms/区域

---

#### F2: 桌面控制

**F2.1 鼠标操作**
```python
class MouseController:
    def move_to(self, x: int, y: int, duration: float = 0.5):
        """平滑移动鼠标到指定坐标"""
        pass
    
    def click(self, x: int, y: int, button: str = "left"):
        """在指定坐标点击"""
        pass
    
    def double_click(self, x: int, y: int):
        """双击"""
        pass
    
    def right_click(self, x: int, y: int):
        """右键点击"""
        pass
    
    def scroll(self, clicks: int, x: int = None, y: int = None):
        """滚动 (正数向上, 负数向下)"""
        pass
```

**验收标准**:
- 定位精度: ±5像素
- 移动动画: 默认0.5秒平滑移动
- 支持 1920x1080 分辨率

**F2.2 键盘操作**
```python
class KeyboardController:
    def type_text(self, text: str, interval: float = 0.01):
        """输入文字"""
        pass
    
    def press_key(self, key: str):
        """按下单个键 (e.g., 'enter', 'esc', 'tab')"""
        pass
    
    def hotkey(self, *keys: str):
        """组合键 (e.g., hotkey('ctrl', 'c'))"""
        pass
```

**验收标准**:
- 支持所有常用键
- 中文输入正常
- 快捷键响应 < 100ms

**F2.3 应用管理**
```python
class AppManager:
    def launch(self, app_name: str) -> bool:
        """
        启动应用
        
        Args:
            app_name: "calculator", "notepad", "chrome" 等
        
        Returns:
            是否成功启动
        """
        pass
    
    def find_window(self, window_title: str = None) -> WindowInfo:
        """查找窗口"""
        pass
    
    def activate_window(self, window_id: str):
        """激活指定窗口"""
        pass
```

**MVP支持应用**:
- `calculator` - 计算器
- `notepad` - 记事本
- `chrome` - Chrome浏览器
- `explorer` - 文件资源管理器

---

#### F3: 任务执行

**F3.1 任务定义**
```python
@dataclass
class Task:
    """原子任务定义"""
    action: str          # "click", "type", "launch", "wait"
    target: str = None   # 元素ID或坐标或应用名
    value: str = None    # 输入值 (用于type)
    delay: float = 1.0   # 执行后等待时间

@dataclass
class TaskSequence:
    """任务序列"""
    name: str
    tasks: List[Task]
    max_retries: int = 3
```

**F3.2 执行引擎**
```python
class TaskExecutor:
    def execute(self, task_sequence: TaskSequence) -> ExecutionResult:
        """
        执行任务序列
        
        Returns:
            ExecutionResult 包含:
            - success: bool
            - completed_steps: int
            - error: str (如果失败)
            - screenshots: List[Path] (执行过程截图)
        """
        pass
```

**执行流程**:
```
1. 截取初始屏幕
2. 检测当前元素
3. 对每个任务:
   a. 解析目标 (元素ID → 坐标)
   b. 执行操作
   c. 等待指定时间
   d. 截取屏幕验证 (可选)
4. 返回执行结果
```

---

## 3. 技术实现

### 3.1 模型要求

**YOLO检测模型**:
```yaml
模型: YOLOv8n (轻量版)
输入尺寸: 640x640
类别数: 4 (button, input, icon, window)
置信度阈值: 0.5
NMS阈值: 0.45
```

**训练数据** (MVP可跳过训练，使用预训练):
- 方案A: 使用公开数据集 (RICO, ScreenQA)
- 方案B: 使用通用YOLOv8 + 简单规则过滤
- 方案C: 收集100张标注数据微调

**推荐**: 先尝试方案B，准确率不够再考虑方案C

### 3.2 依赖库

```txt
# requirements.txt
ultralytics>=8.0.0      # YOLOv8
pyautogui>=0.9.54       # 桌面控制
opencv-python>=4.8.0    # 图像处理
paddleocr>=2.7.0        # OCR文字识别
pillow>=10.0.0          # 图像处理
numpy>=1.24.0           # 数值计算
```

### 3.3 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| OS | Ubuntu 20.04 / macOS 12 | Ubuntu 22.04 |
| Python | 3.9 | 3.11 |
| RAM | 4GB | 8GB |
| GPU | 可选 (CPU推理) | GTX 1060 6GB |
| 分辨率 | 1920x1080 | 1920x1080 |

---

## 4. 测试规格

### 4.1 测试任务集

**T1: 计算器操作**
```python
task = TaskSequence("计算器加法", [
    Task("launch", target="calculator"),
    Task("wait", delay=1.0),
    Task("click", target="button_1"),  # 数字1
    Task("click", target="button_plus"),  # +
    Task("click", target="button_2"),  # 数字2
    Task("click", target="button_equals"),  # =
])
# 期望: 计算器显示 3
```

**T2: 记事本输入**
```python
task = TaskSequence("记事本打字", [
    Task("launch", target="notepad"),
    Task("wait", delay=1.0),
    Task("type", target="input_main", value="Hello World"),
])
# 期望: 记事本显示 Hello World
```

**T3: 打开Chrome并搜索**
```python
task = TaskSequence("Chrome搜索", [
    Task("launch", target="chrome"),
    Task("wait", delay=2.0),
    Task("click", target="address_bar"),
    Task("type", value="openclaw.ai"),
    Task("press", value="enter"),
])
# 期望: Chrome打开 openclaw.ai
```

### 4.2 测试通过标准

- 10个测试任务中 ≥8个成功
- 每个任务总耗时 < 10秒
- 无异常崩溃

---

## 5. 接口设计

### 5.1 Python API

```python
from claw_desktop import ComputerUseAgent

# 初始化
agent = ComputerUseAgent()

# 执行预定义任务
result = agent.execute_task("calculator_add", a=1, b=2)

# 执行原始任务序列
from claw_desktop import Task, TaskSequence

sequence = TaskSequence("自定义任务", [
    Task("launch", target="notepad"),
    Task("wait", delay=1),
    Task("type", value="Hello from ClawDesktop!"),
])
result = agent.execute(sequence)

print(result.success)  # True/False
print(result.message)  # 执行结果描述
```

### 5.2 CLI 接口

```bash
# 运行测试任务
python -m claw_desktop run tests/calculator_add.json

# 执行自定义脚本
python -m claw_desktop execute my_task.json --visualize

# 查看检测元素
python -m claw_desktop detect --output elements.json
```

---

## 6. 文件结构

```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── agent.py          # ComputerUseAgent 主类
│   ├── executor.py       # TaskExecutor 执行引擎
│   └── config.py         # 配置管理
├── perception/
│   ├── __init__.py
│   ├── detector.py       # YOLO元素检测
│   ├── ocr.py           # OCR文字识别
│   └── screen.py        # 屏幕截图
├── action/
│   ├── __init__.py
│   ├── mouse.py         # 鼠标控制
│   ├── keyboard.py      # 键盘控制
│   └── app_manager.py   # 应用管理
└── utils/
    ├── __init__.py
    ├── image.py         # 图像处理工具
    └── logger.py        # 日志
```

---

## 7. 开发检查清单

### Phase 1: 基础框架
- [ ] 项目结构初始化
- [ ] 依赖库安装脚本
- [ ] 屏幕截图功能
- [ ] 基础日志系统

### Phase 2: 感知层
- [ ] YOLO模型集成
- [ ] 元素检测实现
- [ ] 检测可视化功能
- [ ] OCR集成

### Phase 3: 行动层
- [ ] PyAutoGUI封装
- [ ] 鼠标控制
- [ ] 键盘控制
- [ ] 应用管理

### Phase 4: 执行引擎
- [ ] Task/TaskSequence定义
- [ ] 任务解析器
- [ ] 执行引擎
- [ ] 错误处理

### Phase 5: 测试
- [ ] 10个测试任务实现
- [ ] 测试报告生成
- [ ] 性能基准测试

---

## 8. 参考资源

- YOLOv8: https://docs.ultralytics.com/
- PyAutoGUI: https://pyautogui.readthedocs.io/
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- agent-browser: https://github.com/vercel-labs/agent-browser

---

**开发Agent注意**: 先实现核心功能，再优化细节。保持代码简洁，优先让测试通过。
