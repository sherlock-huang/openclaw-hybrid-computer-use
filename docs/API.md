# API 文档

**版本**: v0.6.0  
**更新日期**: 2026-04-25

---

## 快速开始

```python
from claw_desktop import ComputerUseAgent

# 初始化
agent = ComputerUseAgent()

# 运行预定义任务
result = agent.execute_task("notepad_type", text="Hello World")

# 检查结果
print(f"成功: {result.success}")
print(f"耗时: {result.duration:.2f}s")
```

---

## 核心类

### ComputerUseAgent

主入口类，提供统一的操作接口。

#### 构造函数

```python
ComputerUseAgent(config: Optional[Config] = None)
```

**参数**:
- `config`: 配置对象，None则使用默认配置

#### 方法

##### execute

执行任务序列。

```python
def execute(sequence: TaskSequence) -> ExecutionResult
```

**参数**:
- `sequence`: 任务序列

**返回**: 执行结果

**示例**:
```python
from claw_desktop import Task, TaskSequence

sequence = TaskSequence("my_task", [
    Task("launch", target="notepad"),
    Task("wait", delay=1.0),
    Task("type", value="Hello"),
])

result = agent.execute(sequence)
```

##### execute_task

执行预定义任务。

```python
def execute_task(name: str, **kwargs) -> ExecutionResult
```

**参数**:
- `name`: 任务名称
- `**kwargs`: 任务参数

**返回**: 执行结果

**示例**:
```python
# 计算器加法
result = agent.execute_task("calculator_add", a=5, b=3)

# 记事本输入
result = agent.execute_task("notepad_type", text="Hello")
```

##### list_tasks

列出所有预定义任务。

```python
def list_tasks() -> List[Dict[str, str]]
```

**返回**: 任务列表，每个任务包含 `name` 和 `description`

**示例**:
```python
tasks = agent.list_tasks()
for task in tasks:
    print(f"{task['name']}: {task['description']}")
```

##### detect_screen

检测屏幕元素。

```python
def detect_screen() -> Dict[str, Any]
```

**返回**: 包含元素数量和元素列表的字典

**示例**:
```python
result = agent.detect_screen()
print(f"检测到 {result['element_count']} 个元素")
for elem in result['elements']:
    print(f"  - {elem['type']} @ {elem['center']}")
```

---

## 数据模型

### Task

原子任务定义。

```python
@dataclass
class Task:
    action: str          # 动作类型
    target: str = None   # 目标（元素ID、坐标、应用名）
    value: str = None    # 值（用于type等动作）
    delay: float = 1.0   # 执行后等待时间（秒）
```

**支持的动作**:

| 动作 | 描述 | 示例 |
|------|------|------|
| `launch` | 启动应用 | `Task("launch", target="notepad")` |
| `click` | 鼠标点击 | `Task("click", target="100,200")` |
| `double_click` | 双击 | `Task("double_click", target="button")` |
| `right_click` | 右键点击 | `Task("right_click", target="300,400")` |
| `type` | 输入文字 | `Task("type", value="Hello")` |
| `press` | 按下按键 | `Task("press", value="enter")` |
| `hotkey` | 组合键 | `Task("hotkey", value="ctrl+c")` |
| `scroll` | 滚动 | `Task("scroll", value="3")` |
| `wait` | 等待 | `Task("wait", delay=2.0)` |

### TaskSequence

任务序列。

```python
@dataclass
class TaskSequence:
    name: str            # 序列名称
    tasks: List[Task]    # 任务列表
    max_retries: int = 3 # 最大重试次数
```

### ExecutionResult

执行结果。

```python
@dataclass
class ExecutionResult:
    success: bool                # 是否成功
    completed_steps: int         # 完成步骤数
    duration: float             # 总耗时（秒）
    error: Optional[str] = None # 错误信息
    screenshots: List[np.ndarray] = []  # 执行过程截图
    logs: List[Dict] = []       # 执行日志
```

---

## 独立组件

### ScreenCapture

屏幕截图。

```python
from claw_desktop import ScreenCapture

capture = ScreenCapture()

# 全屏截图
image = capture.capture()

# 区域截图
image = capture.capture(region=(100, 100, 800, 600))  # x, y, w, h

# 保存截图
capture.save(image, "screenshot.png")
```

### ElementDetector

元素检测。

```python
from claw_desktop import ScreenCapture, ElementDetector

capture = ScreenCapture()
detector = ElementDetector()

# 截图并检测
image = capture.capture()
elements = detector.detect(image)

# 遍历检测结果
for elem in elements:
    print(f"{elem.id}: {elem.element_type.value} @ {elem.center}")
    print(f"  边界框: ({elem.bbox.x1}, {elem.bbox.y1}, {elem.bbox.x2}, {elem.bbox.y2})")
    print(f"  置信度: {elem.confidence:.2f}")

# 按类型筛选
buttons = detector.detect_by_type(image, ElementType.BUTTON)
```

### MouseController

鼠标控制。

```python
from claw_desktop import MouseController

mouse = MouseController()

# 获取当前位置
x, y = mouse.get_position()

# 移动鼠标（平滑动画）
mouse.move_to(500, 400, duration=0.5)

# 点击
mouse.click(500, 400)
mouse.double_click(500, 400)
mouse.right_click(500, 400)

# 滚动
mouse.scroll(3)      # 向上滚动
mouse.scroll(-3)     # 向下滚动

# 拖拽
mouse.move_to(100, 100)
pyautogui.mouseDown()
mouse.move_to(200, 200)
pyautogui.mouseUp()
```

### KeyboardController

键盘控制。

```python
from claw_desktop import KeyboardController

kb = KeyboardController()

# 输入文字
kb.type_text("Hello World")

# 按下按键
kb.press_key("enter")
kb.press_key("esc")

# 组合键
kb.hotkey("ctrl", "c")
kb.hotkey("ctrl", "v")
kb.hotkey("alt", "tab")

# 快捷操作
kb.select_all()  # Ctrl+A
kb.copy()        # Ctrl+C
kb.paste()       # Ctrl+V
```

### ApplicationManager

应用管理。

```python
from claw_desktop import ApplicationManager

app_mgr = ApplicationManager()

# 启动应用
app_mgr.launch("calculator")
app_mgr.launch("notepad")
app_mgr.launch("chrome")

# 检查是否运行
if app_mgr.is_running("notepad"):
    print("记事本正在运行")

# 注册自定义应用
app_mgr.register_app(
    name="myapp",
    linux_cmd="myapp-linux",
    mac_cmd="MyApp.app",
    win_cmd="myapp.exe"
)
```

---

## 预定义任务

### 计算器加法 (calculator_add)

打开计算器并执行加法。

```python
result = agent.execute_task("calculator_add", a=5, b=3)
```

**参数**:
- `a`: 第一个数字 (默认: 1)
- `b`: 第二个数字 (默认: 2)

### 记事本输入 (notepad_type)

打开记事本并输入文字。

```python
result = agent.execute_task("notepad_type", text="Hello World")
```

**参数**:
- `text`: 要输入的文字 (默认: "Hello World")

### Chrome搜索 (chrome_search)

打开Chrome并访问URL。

```python
result = agent.execute_task("chrome_search", url="openclaw.ai")
```

**参数**:
- `url`: 要访问的URL (默认: "openclaw.ai")

### 更多任务

```python
# 文件管理器导航
agent.execute_task("explorer_navigate", path="Desktop")

# 窗口切换
agent.execute_task("window_switch")

# 显示桌面
agent.execute_task("desktop_screenshot")

# 复制粘贴测试
agent.execute_task("text_copy_paste")

# 滚动测试
agent.execute_task("scroll_test")

# 右键菜单
agent.execute_task("right_click")

# 多应用切换
agent.execute_task("multi_app")
```

---

## 配置

### Config

配置对象。

```python
from claw_desktop.core.config import Config

config = Config()

# 修改配置
config.yolo_conf_threshold = 0.6
config.mouse_default_duration = 0.3
config.log_level = "DEBUG"

# 从环境变量加载
config = Config.from_env()

# 创建带配置的Agent
agent = ComputerUseAgent(config)
```

**配置项**:

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `yolo_model_path` | "models/yolov8n.pt" | YOLO模型路径 |
| `yolo_conf_threshold` | 0.5 | 检测置信度阈值 |
| `ocr_lang` | "ch" | OCR语言 |
| `mouse_default_duration` | 0.5 | 鼠标移动动画时长(秒) |
| `default_delay` | 1.0 | 默认等待时间(秒) |
| `max_retries` | 3 | 最大重试次数 |
| `log_level` | "INFO" | 日志级别 |
| `save_screenshots` | True | 是否保存截图 |

---

## 命令行接口 (CLI)

### 运行任务

```bash
# 列出预定义任务
python run.py run --list

# 运行任务
python run.py run notepad_type
python run.py run calculator_add a=5 b=3

# 带可视化
python run.py run notepad_type -v
```

### 检测屏幕

```bash
# 检测元素
python run.py detect

# 带可视化输出
python run.py detect -v -o elements.json
```

### 执行任务文件

```bash
python run.py execute examples/task_notepad.json
```

### 运行测试

```bash
# 基础测试
python run.py test

# 所有测试
python run.py test --all

# 特定类别
python run.py test --category basic predefined
```

### 性能基准测试

```bash
python run.py benchmark --save
```

---

## 可视化

### ExecutionVisualizer

执行过程可视化。

```python
from claw_desktop.utils.visualizer import ExecutionVisualizer

viz = ExecutionVisualizer(output_dir="output/viz")

# 可视化检测结果
path = viz.visualize_detection(image, elements)

# 可视化任务执行
path = viz.visualize_task_execution(
    image, task, elements, highlight_id="elem_001"
)

# 生成执行报告
path = viz.create_execution_report(result)
```

---

## 错误处理

### 常见错误

```python
from claw_desktop import ComputerUseAgent, Task, TaskSequence

agent = ComputerUseAgent()

# 任务可能失败，始终检查结果
result = agent.execute_task("some_task")

if not result.success:
    print(f"失败: {result.error}")
    print(f"完成步骤: {result.completed_steps}")
    
    # 查看截图
    for i, screenshot in enumerate(result.screenshots):
        print(f"步骤 {i+1} 截图: {screenshot.shape}")
```

### 异常捕获

```python
try:
    result = agent.execute(sequence)
except Exception as e:
    print(f"执行异常: {e}")
```

---

## 完整示例

```python
from claw_desktop import (
    ComputerUseAgent,
    Task,
    TaskSequence,
    ElementType,
)
from claw_desktop.utils.visualizer import ExecutionVisualizer

# 初始化
agent = ComputerUseAgent()
viz = ExecutionVisualizer()

# 创建自定义任务序列
sequence = TaskSequence("自动保存文档", [
    Task("launch", target="notepad"),
    Task("wait", delay=1.5),
    Task("type", value="这是自动生成的文档"),
    Task("hotkey", value="ctrl+s", delay=0.5),
    Task("type", value="auto_document.txt"),
    Task("press", value="enter"),
], max_retries=2)

# 执行
print("开始执行任务...")
result = agent.execute(sequence)

# 生成可视化报告
if result.screenshots:
    report_path = viz.create_execution_report(result)
    print(f"报告已保存: {report_path}")

# 输出结果
if result.success:
    print(f"✅ 任务完成！耗时: {result.duration:.2f}s")
else:
    print(f"❌ 任务失败: {result.error}")
```

---

**更多示例**: 参见 `examples/` 目录
