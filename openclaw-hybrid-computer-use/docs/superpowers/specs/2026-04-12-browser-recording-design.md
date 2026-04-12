# 浏览器录制功能设计文档 (v0.2.1)

**日期:** 2026-04-12  
**作者:** OpenClaw Team  
**状态:** 待实现  
**关联技能:** superpowers:writing-plans

---

## 1. 目标与背景

### 1.1 目标
扩展任务录制器，使其能够：
- 检测用户是否在浏览器中操作
- 如果是浏览器：记录 CSS 选择器而非屏幕坐标
- 如果是桌面应用：保持现有坐标录制方式
- 生成可直接回放的混合任务序列

### 1.2 背景
当前录制器只能记录桌面坐标（如 "500,300"），这种方式：
- ✅ 适用于桌面应用
- ❌ 不适用于网页（页面缩放、响应式布局会导致坐标失效）

浏览器需要使用 CSS 选择器（如 "#search-input"），更稳定可靠。

### 1.3 成功标准
- [ ] 用户在浏览器中点击，记录为 `browser_click` + CSS 选择器
- [ ] 用户在桌面应用中点击，记录为 `click` + 坐标
- [ ] 自动生成可执行的混合任务 JSON
- [ ] 提供录制示例：录制一次抖音搜索，自动生成分毫不差的任务文件

---

## 2. 架构设计

### 2.1 混合录制架构

```
┌─────────────────────────────────────────────────────────────┐
│                    HybridRecorder                           │
│                    (混合录制器)                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐        ┌──────────────────────────┐  │
│  │  DesktopRecorder │        │    BrowserRecorder       │  │
│  │  (现有)          │        │    (新增)                │  │
│  │                  │        │                          │  │
│  │  pynput 监听     │        │   连接现有浏览器          │  │
│  │  屏幕坐标        │◄──────►│   Playwright 获取选择器   │  │
│  └──────────────────┘        └──────────────────────────┘  │
│           ▲                            ▲                    │
│           │                            │                    │
│           └───────────┬────────────────┘                    │
│                       ▼                                     │
│              ┌─────────────────┐                           │
│              │  窗口检测器      │                           │
│              │  - 获取当前窗口  │                           │
│              │  - 判断浏览器   │                           │
│              └─────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 文件路径 | 职责 |
|------|----------|------|
| `HybridRecorder` | `src/recording/hybrid_recorder.py` | 主录制器，自动切换模式 |
| `BrowserRecorder` | `src/recording/browser_recorder.py` | 浏览器操作录制 |
| `WindowDetector` | `src/recording/window_detector.py` | 检测当前活动窗口类型 |
| `RecordingMode` | `src/core/models.py` | 录制模式枚举 |

---

## 3. 关键流程

### 3.1 鼠标点击处理流程

```
用户点击
    │
    ▼
┌─────────────┐
│ 获取当前窗口 │
└─────────────┘
    │
    ├── 是浏览器窗口？ ──Yes──► 使用 BrowserRecorder
    │                              - 通过 Playwright 获取元素选择器
    │                              - 记录 browser_click + selector
    │
    └── No ──► 使用 DesktopRecorder
                   - 记录屏幕坐标
                   - 记录 click + "x,y"
```

### 3.2 BrowserRecorder 工作原理

```python
# 1. 连接到已存在的浏览器（使用相同的 user_data_dir）
controller = BrowserController(user_data_dir="browser_data")
controller.launch()

# 2. 在页面中注入 JavaScript 监听点击事件
page.evaluate("""
    window.lastClickedElement = null;
    document.addEventListener('click', function(e) {
        window.lastClickedElement = e.target;
    }, true);
""")

# 3. 当检测到点击时，获取元素选择器
selector = page.evaluate("""
    function getSelector(element) {
        // 生成唯一选择器的算法
        if (element.id) return '#' + element.id;
        if (element.className) return '.' + element.className.split(' ')[0];
        return element.tagName.toLowerCase();
    }
    getSelector(window.lastClickedElement);
""")

# 4. 记录事件
recording_event = RecordingEvent(
    action="browser_click",
    target=selector,
    position=(x, y)  # 作为备选
)
```

---

## 4. 数据模型扩展

### 4.1 新增录制模式枚举

```python
# src/core/models.py
from enum import Enum

class RecordingMode(Enum):
    """录制模式"""
    DESKTOP = "desktop"      # 桌面录制（坐标）
    BROWSER = "browser"      # 浏览器录制（选择器）
    HYBRID = "hybrid"        # 混合模式（自动检测）
```

### 4.2 RecordingEvent 扩展

```python
@dataclass
class RecordingEvent:
    action: str                    # "click", "type", "browser_click", ...
    timestamp: float
    target: Optional[str] = None   # 元素ID、坐标或CSS选择器
    position: Optional[Tuple[int, int]] = None  # 坐标 (x, y)
    value: Optional[str] = None    # 输入值
    element_type: Optional[str] = None  # 元素类型
    recording_mode: RecordingMode = RecordingMode.DESKTOP  # 录制模式
    
    # 浏览器特有
    css_selector: Optional[str] = None  # CSS 选择器
    xpath: Optional[str] = None         # XPath（备选）
```

---

## 5. 接口设计

### 5.1 HybridRecorder 接口

```python
class HybridRecorder:
    """混合录制器 - 自动检测并录制桌面或浏览器操作"""
    
    def __init__(self, mode: RecordingMode = RecordingMode.HYBRID):
        """
        Args:
            mode: 录制模式
                - HYBRID: 自动检测（推荐）
                - DESKTOP: 只录制桌面
                - BROWSER: 只录制浏览器
        """
    
    def start_recording(self, name: Optional[str] = None):
        """开始录制"""
    
    def stop_recording(self) -> RecordingSession:
        """停止录制并返回会话"""
    
    def _detect_current_mode(self) -> RecordingMode:
        """检测当前应该使用哪种录制模式"""
        # 获取当前活动窗口
        # 如果是浏览器窗口 -> 返回 BROWSER
        # 否则 -> 返回 DESKTOP
```

### 5.2 BrowserRecorder 接口

```python
class BrowserRecorder:
    """浏览器录制器 - 录制网页操作"""
    
    def __init__(self, user_data_dir: str = "browser_data"):
        """
        Args:
            user_data_dir: 浏览器用户数据目录
        """
    
    def connect(self) -> bool:
        """
        连接到现有浏览器
        
        Returns:
            是否成功连接
        """
    
    def inject_listeners(self):
        """在页面中注入事件监听脚本"""
    
    def get_last_click_selector(self) -> Optional[str]:
        """获取最后一次点击的元素选择器"""
    
    def get_last_input_selector(self) -> Optional[str]:
        """获取最后一次输入的元素选择器"""
```

---

## 6. 使用示例

### 6.1 命令行使用

```bash
# 启动混合录制（自动检测）
py -m src record --mode hybrid -o my_task.json

# 只录制浏览器
py -m src record --mode browser -o browser_task.json

# 只录制桌面
py -m src record --mode desktop -o desktop_task.json
```

### 6.2 录制流程示例

```
1. 用户运行: py -m src record --mode hybrid

2. 用户打开浏览器，访问抖音
   [检测] 当前窗口是浏览器 -> 使用 BrowserRecorder
   
3. 用户点击搜索框
   [记录] action="browser_click", target="#search-input", css_selector="#search-input"
   
4. 用户输入 "李子柒"
   [记录] action="browser_type", target="#search-input", value="李子柒"
   
5. 用户按 Enter
   [记录] action="browser_press", value="Enter"
   
6. 用户滚动页面
   [记录] action="browser_scroll", value="500"
   
7. 用户停止录制 (Ctrl+R)
   [生成] my_task.json
```

### 6.3 生成的任务文件示例

```json
{
  "name": "录制任务 2026-04-12 18:30:00",
  "recorded_at": "2026-04-12T18:30:00",
  "mode": "hybrid",
  "tasks": [
    {
      "action": "browser_launch",
      "value": "chromium",
      "delay": 2.0,
      "_metadata": {
        "recorded_position": [100, 100],
        "css_selector": null
      }
    },
    {
      "action": "browser_click",
      "target": "#search-input",
      "delay": 0.5,
      "_metadata": {
        "recorded_position": [800, 200],
        "css_selector": "#search-input"
      }
    },
    {
      "action": "browser_type",
      "target": "#search-input",
      "value": "李子柒",
      "delay": 0.5
    },
    {
      "action": "browser_scroll",
      "value": "500",
      "delay": 1.0
    }
  ]
}
```

---

## 7. 技术难点与解决方案

### 7.1 难点1：检测当前窗口是否为浏览器

**方案**: 使用 `pygetwindow` 或 `pywin32` 获取窗口标题
- Chrome: 标题包含 "Chrome" 或 "谷歌浏览器"
- Edge: 标题包含 "Edge"
- Firefox: 标题包含 "Firefox"

```python
def is_browser_window(title: str) -> bool:
    browser_keywords = ["Chrome", "Edge", "Firefox", "Safari", " chromium"]
    return any(keyword.lower() in title.lower() for keyword in browser_keywords)
```

### 7.2 难点2：连接到已存在的浏览器

**方案**: Playwright 的 `connect_over_cdp`
```python
browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
```

或者启动时指定端口：
```python
chromium.launch(args=["--remote-debugging-port=9222"])
```

### 7.3 难点3：生成稳定的选择器

**方案**: 优先使用 ID，其次 class，最后 XPath
```javascript
function getStableSelector(element) {
    // 1. 尝试 ID
    if (element.id) return '#' + element.id;
    
    // 2. 尝试 data-* 属性
    if (element.dataset.e2e) return `[data-e2e="${element.dataset.e2e}"]`;
    
    // 3. 尝试 class
    if (element.className) {
        const classes = element.className.split(' ').filter(c => c.length > 0);
        if (classes.length > 0) return '.' + classes[0];
    }
    
    // 4. 使用 XPath
    return getXPath(element);
}
```

---

## 8. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 无法连接到已存在的浏览器 | 中 | 高 | 提供备用方案：启动新浏览器 |
| 生成的选择器不稳定 | 中 | 中 | 多策略生成，记录备选选择器 |
| 检测窗口类型不准确 | 低 | 中 | 提供手动切换模式的热键 |
| 录制和回放不一致 | 中 | 高 | 录制时截图，回放时对比 |

---

## 9. 审查清单

- [x] 架构设计清晰，混合模式可行
- [x] 接口定义完整
- [x] 技术难点有解决方案
- [x] 使用示例具体
- [x] 风险评估全面

---

## 10. 审批

**设计审查通过后将进入 writing-plans 阶段。**

---

*文档版本: 1.0*  
*创建时间: 2026-04-12*
