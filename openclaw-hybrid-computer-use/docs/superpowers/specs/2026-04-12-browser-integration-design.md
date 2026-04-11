# 浏览器集成设计文档 (v0.2.0)

**日期:** 2026-04-12  
**作者:** OpenClaw Team  
**状态:** 待实现  
**关联技能:** superpowers:writing-plans

---

## 1. 目标与背景

### 1.1 目标
为 OpenClaw Desktop Agent 添加浏览器自动化能力，使其能够：
- 控制浏览器执行网页操作（点击、输入、导航、滚动）
- 与现有桌面自动化无缝集成（混合模式）
- 支持录制网页操作并回放

### 1.2 背景
当前系统仅支持桌面应用自动化（点击坐标、键盘输入）。用户需要自动化网页任务，如：
- 抖音网页版搜索UP主
- 自动登录网站
- 网页数据抓取

### 1.3 成功标准
- [ ] 可通过 JSON 任务序列控制浏览器
- [ ] 支持 Playwright 的所有主流浏览器（Chromium、Firefox、WebKit）
- [ ] 浏览器操作与桌面操作可在同一任务序列中混合使用
- [ ] 提供抖音搜索示例任务

---

## 2. 架构设计

### 2.1 双模式架构

```
┌─────────────────────────────────────────────────────────────┐
│                     TaskExecutor                            │
│                     (任务执行引擎)                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐        ┌──────────────────────────┐  │
│  │  DesktopMode     │        │      BrowserMode         │  │
│  │  (现有)          │        │      (新增)              │  │
│  │                  │        │                          │  │
│  │  ScreenCapture   │        │   BrowserController      │  │
│  │  ElementDetector │        │   ├─ PlaywrightWrapper   │  │
│  │  MouseController │        │   ├─ PageManager         │  │
│  │  KeyboardControl │        │   └─ ActionHandler       │  │
│  └──────────────────┘        └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 文件路径 | 职责 |
|------|----------|------|
| `BrowserController` | `src/browser/controller.py` | 浏览器生命周期管理（启动、关闭、页面管理） |
| `BrowserActionHandler` | `src/browser/actions.py` | 浏览器操作封装（点击、输入、导航等） |
| `BrowserTaskExecutor` | `src/browser/executor.py` | 浏览器专用任务执行器 |
| `MixedModeExecutor` | `src/core/mixed_executor.py` | 混合模式协调器（自动切换桌面/浏览器） |

---

## 3. 数据模型扩展

### 3.1 新增 Task Action 类型

```python
# src/core/models.py
BROWSER_ACTIONS = {
    "browser_launch",     # 启动浏览器
    "browser_close",      # 关闭浏览器
    "browser_goto",       # 访问URL
    "browser_click",      # 点击元素（CSS/XPath selector）
    "browser_type",       # 输入文字
    "browser_clear",      # 清空输入框
    "browser_select",     # 选择下拉框
    "browser_wait",       # 等待元素
    "browser_scroll",     # 滚动页面
    "browser_screenshot", # 页面截图
    "browser_evaluate",   # 执行 JavaScript
}
```

### 3.2 Task 结构示例

```json
{
  "name": "抖音搜索UP主",
  "tasks": [
    {"action": "browser_launch", "value": "chromium", "delay": 2.0},
    {"action": "browser_goto", "value": "https://www.douyin.com", "delay": 3.0},
    {"action": "browser_click", "target": "[data-e2e='search-icon']", "delay": 1.0},
    {"action": "browser_type", "target": "[data-e2e='search-input']", "value": "UP主名称", "delay": 0.5},
    {"action": "browser_click", "target": "[data-e2e='search-button']", "delay": 2.0},
    {"action": "browser_scroll", "value": "1000", "delay": 1.0},
    {"action": "browser_screenshot", "value": "search_result.png", "delay": 0.5},
    {"action": "browser_close", "delay": 1.0}
  ]
}
```

---

## 4. 接口设计

### 4.1 BrowserController 接口

```python
class BrowserController:
    """浏览器控制器 - 管理浏览器生命周期"""
    
    def __init__(self, browser_type: str = "chromium", headless: bool = False):
        """
        Args:
            browser_type: "chromium" | "firefox" | "webkit"
            headless: 是否无头模式
        """
    
    def launch(self) -> None:
        """启动浏览器"""
    
    def close(self) -> None:
        """关闭浏览器"""
    
    def new_page(self, viewport: Optional[Dict] = None) -> Page:
        """创建新页面/标签页"""
    
    def get_page(self, index: int = 0) -> Page:
        """获取指定页面"""
    
    def current_page(self) -> Page:
        """获取当前活动页面"""
```

### 4.2 BrowserActionHandler 接口

```python
class BrowserActionHandler:
    """浏览器操作处理器"""
    
    def __init__(self, controller: BrowserController):
        self.controller = controller
    
    def goto(self, url: str) -> None:
        """导航到URL"""
    
    def click(self, selector: str, options: Optional[Dict] = None) -> None:
        """
        点击元素
        
        Args:
            selector: CSS 选择器或 XPath
            options: {timeout, force, click_count, button}
        """
    
    def type(self, selector: str, text: str, options: Optional[Dict] = None) -> None:
        """
        输入文字
        
        Args:
            selector: CSS 选择器
            text: 要输入的文字
            options: {timeout, clear_first, delay}
        """
    
    def scroll(self, amount: int, direction: str = "vertical") -> None:
        """
        滚动页面
        
        Args:
            amount: 滚动像素（正数向下，负数向上）
            direction: "vertical" | "horizontal"
        """
    
    def wait_for(self, selector: str, state: str = "visible", timeout: int = 30) -> None:
        """
        等待元素状态
        
        Args:
            selector: CSS 选择器
            state: "visible" | "hidden" | "attached" | "detached"
            timeout: 超时时间（秒）
        """
    
    def screenshot(self, path: Optional[str] = None) -> bytes:
        """截图，返回图片字节或保存到文件"""
    
    def evaluate(self, script: str) -> Any:
        """执行 JavaScript 并返回结果"""
```

---

## 5. 混合模式设计

### 5.1 自动模式检测

```python
class MixedModeExecutor:
    """混合模式执行器 - 自动切换桌面/浏览器模式"""
    
    def __init__(self):
        self.desktop_executor = TaskExecutor()
        self.browser_executor = BrowserTaskExecutor()
    
    def execute(self, sequence: TaskSequence) -> ExecutionResult:
        for task in sequence.tasks:
            if self._is_browser_action(task.action):
                self.browser_executor.execute(task)
            else:
                self.desktop_executor.execute(task)
    
    def _is_browser_action(self, action: str) -> bool:
        return action.startswith("browser_")
```

### 5.2 模式切换示例

```json
{
  "name": "混合任务示例",
  "tasks": [
    {"action": "browser_launch"},
    {"action": "browser_goto", "value": "https://example.com"},
    {"action": "click", "target": "500,300"},        // ← 桌面模式：屏幕点击
    {"action": "browser_type", "target": "#input", "value": "text"},  // ← 浏览器模式
    {"action": "hotkey", "value": "alt+tab"},       // ← 桌面模式：切换窗口
    {"action": "browser_close"}
  ]
}
```

---

## 6. 依赖与安装

### 6.1 Python 依赖

```
playwright>=1.40.0
```

### 6.2 浏览器安装

```bash
# 安装 Playwright 浏览器
playwright install chromium
playwright install firefox
```

---

## 7. 错误处理

### 7.1 常见错误

| 错误类型 | 处理方式 |
|----------|----------|
| 元素未找到 | 重试3次，每次延迟1秒，失败后截图 |
| 页面加载超时 | 超时30秒后报错，保存当前HTML |
| 浏览器启动失败 | 检查安装，提示运行 `playwright install` |
| 选择器无效 | 立即报错，提示检查选择器语法 |

### 7.2 截图调试

所有浏览器错误自动触发截图，保存到 `logs/browser_errors/`。

---

## 8. 测试策略

### 8.1 单元测试

```python
# tests/test_browser_controller.py
def test_browser_launch_and_close():
    controller = BrowserController(headless=True)
    controller.launch()
    assert controller.is_running
    controller.close()
    assert not controller.is_running

def test_goto_and_click():
    controller = BrowserController(headless=True)
    controller.launch()
    handler = BrowserActionHandler(controller)
    handler.goto("https://example.com")
    handler.click("h1")
    controller.close()
```

### 8.2 集成测试

- 测试完整任务序列执行
- 测试混合模式切换
- 测试错误重试机制

---

## 9. 示例任务

### 9.1 抖音搜索UP主

```json
{
  "name": "抖音搜索UP主",
  "description": "在抖音网页版搜索指定UP主并查看视频",
  "tasks": [
    {"action": "browser_launch", "value": "chromium", "delay": 2.0},
    {"action": "browser_goto", "value": "https://www.douyin.com", "delay": 5.0},
    {"action": "browser_click", "target": "[data-e2e='search-icon']", "delay": 1.0},
    {"action": "browser_type", "target": "[data-e2e='search-input']", "value": "{{up主名称}}", "delay": 0.5},
    {"action": "browser_click", "target": "[data-e2e='search-button']", "delay": 3.0},
    {"action": "browser_wait", "target": ".video-item", "value": "visible", "delay": 2.0},
    {"action": "browser_click", "target": ".video-item:first-child", "delay": 2.0},
    {"action": "browser_scroll", "value": "800", "delay": 1.0},
    {"action": "browser_screenshot", "value": "douyin_result.png", "delay": 0.5},
    {"action": "browser_close", "delay": 1.0}
  ]
}
```

---

## 10. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 抖音网站结构变化 | 高 | 中 | 使用 data-e2e 属性，定期更新选择器 |
| Playwright 安装复杂 | 中 | 低 | 提供详细安装文档，检测未安装时提示 |
| 浏览器资源占用 | 中 | 低 | 支持 headless 模式，自动清理进程 |
| 混合模式逻辑复杂 | 低 | 中 | 清晰的 action 命名前缀区分模式 |

---

## 11. 后续扩展

### 11.1 v0.2.1 计划
- [ ] 录制浏览器操作（扩展现有录制器）
- [ ] 智能选择器推荐（基于页面结构）
- [ ] 浏览器操作视频录制

### 11.2 v0.3.0 计划
- [ ] 视觉语言模型（VLM）集成
- [ ] 自然语言描述生成浏览器任务
- [ ] 自动处理动态加载内容

---

## 12. 审查清单

- [x] 架构设计清晰，组件职责明确
- [x] 接口定义完整，包含参数和返回值
- [x] 数据模型扩展向后兼容
- [x] 错误处理策略完备
- [x] 测试策略覆盖核心功能
- [x] 示例任务具有实际价值
- [x] 风险评估和缓解措施

---

## 13. 审批

**设计审查通过后将进入 writing-plans 阶段，创建详细实现计划。**

---

*文档版本: 1.0*  
*创建时间: 2026-04-12*  
*最后更新: 2026-04-12*
