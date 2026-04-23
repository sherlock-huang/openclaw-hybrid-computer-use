# 开发者指南

> 贡献代码、扩展功能、自定义任务

---

## 📋 目录

1. [项目结构](#-项目结构)
2. [开发环境设置](#-开发环境设置)
3. [代码规范](#-代码规范)
4. [添加预置任务](#-添加预置任务)
5. [扩展浏览器操作](#-扩展浏览器操作)
6. [测试指南](#-测试指南)
7. [提交贡献](#-提交贡献)

---

## 🏗️ 项目结构

```
openclaw-computer-use/
├── src/                          # 源代码
│   ├── __init__.py              # 包初始化（UTF-8修复）
│   ├── core/                    # 核心引擎
│   │   ├── agent.py             # 主Agent类
│   │   ├── executor.py          # 任务执行器
│   │   ├── executor_enhanced.py # 增强版执行器
│   │   ├── models.py            # 数据模型
│   │   ├── tasks_predefined.py  # 预置任务定义
│   │   └── selectors_config.py  # 选择器配置
│   ├── perception/              # 感知层
│   │   ├── screen.py            # 屏幕截图
│   │   ├── detector.py          # 元素检测
│   │   └── ocr.py               # 文字识别
│   ├── action/                  # 行动层
│   │   ├── mouse.py             # 鼠标控制
│   │   ├── keyboard.py          # 键盘控制
│   │   └── app_manager.py       # 应用管理
│   ├── browser/                 # 浏览器自动化
│   │   ├── controller.py        # 浏览器控制器
│   │   └── actions.py           # 浏览器操作
│   ├── vision/                  # VLM 智能模式
│   │   ├── llm_client.py        # VLM 客户端
│   │   ├── planner.py           # 任务规划器
│   │   └── prompts.py           # 提示词模板
│   └── utils/                   # 工具函数
│       ├── logger.py            # 日志工具
│       ├── visualizer.py        # 可视化
│       └── task_builder.py      # 任务构建器
├── tests/                        # 测试套件
│   ├── test_suite.py            # 标准测试
│   ├── test_predefined_tasks.py # 预置任务测试
│   └── benchmark.py             # 性能测试
├── docs/                         # 文档
├── examples/                     # 示例代码
├── recordings/                   # 录制文件（自动生成）
├── browser_data/                 # 浏览器数据（自动生成）
├── run.py                        # CLI 入口
└── requirements.txt              # 依赖
```

---

## 🔧 开发环境设置

### 1. 克隆仓库

```bash
git clone <repo-url>
cd openclaw-computer-use
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 安装开发依赖

```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8  # 开发工具
```

### 4. 安装 Playwright 浏览器

```bash
playwright install chromium
playwright install firefox
```

### 5. 验证安装

```bash
python run.py test --all
```

---

## 📝 代码规范

### Python 代码风格

遵循 PEP 8，使用 Black 格式化：

```bash
# 格式化代码
black src/ tests/

# 检查代码
flake8 src/ tests/
```

### 命名规范

| 类型 | 命名方式 | 示例 |
|------|----------|------|
| 类 | PascalCase | `TaskExecutor`, `BrowserController` |
| 函数/方法 | snake_case | `execute_task()`, `click_element()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_DELAY` |
| 私有 | _leading_underscore | `_internal_method()` |

### 文档字符串

所有公共类和方法必须有 docstring：

```python
def execute_task(self, task: Task, screenshot: np.ndarray) -> bool:
    """执行单个任务。
    
    Args:
        task: 要执行的任务
        screenshot: 当前屏幕截图
        
    Returns:
        执行是否成功
        
    Raises:
        TaskExecutionError: 执行失败时抛出
    """
    pass
```

### 类型注解

使用类型注解提高代码可读性：

```python
from typing import List, Optional, Dict, Any

def process_elements(
    elements: List[UIElement],
    filter_type: Optional[str] = None
) -> Dict[str, Any]:
    ...
```

---

## ➕ 添加预置任务

### 步骤 1: 创建任务工厂函数

在 `src/core/tasks_predefined.py` 中添加：

```python
def create_my_custom_task(param1: str = "default") -> TaskSequence:
    """创建自定义任务。
    
    Args:
        param1: 参数说明
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name="my_custom_task",
        tasks=[
            Task("launch", target="notepad"),
            Task("wait", delay=1.0),
            Task("type", value=param1),
            Task("press", value="enter"),
        ],
        max_retries=3
    )
```

### 步骤 2: 注册任务

在 `PREDEFINED_TASKS` 字典中注册：

```python
PREDEFINED_TASKS = {
    # 现有任务...
    "my_custom_task": create_my_custom_task,
}
```

### 步骤 3: 添加文档

更新 `docs/PREDEFINED_TASKS.md`：

```markdown
### 我的自定义任务 `my_custom_task`

描述你的任务功能。

```bash
python run.py run my_custom_task param1="Hello"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `param1` | 字符串 | "default" | 参数说明 |
```

### 步骤 4: 添加测试

在 `tests/test_predefined_tasks.py` 中添加：

```python
def test_my_custom_task(self):
    """测试自定义任务。"""
    task = create_my_custom_task(param1="test")
    self.assertEqual(task.name, "my_custom_task")
    self.assertEqual(len(task.tasks), 4)
```

---

## 🌐 扩展浏览器操作

### 添加新的浏览器操作

在 `src/browser/actions.py` 中添加：

```python
class BrowserActions:
    # 现有方法...
    
    def hover(self, selector: str) -> None:
        """鼠标悬停在元素上。
        
        Args:
            selector: CSS 选择器
        """
        self.page.hover(selector)
        self.logger.info(f"Hover on: {selector}")
    
    def select_option(self, selector: str, value: str) -> None:
        """选择下拉框选项。
        
        Args:
            selector: CSS 选择器
            value: 选项值
        """
        self.page.select_option(selector, value)
        self.logger.info(f"Selected {value} from {selector}")
```

### 在控制器中暴露

在 `src/browser/controller.py` 中添加：

```python
class BrowserController:
    # 现有方法...
    
    def hover(self, selector: str) -> None:
        """鼠标悬停。"""
        self._actions.hover(selector)
    
    def select_option(self, selector: str, value: str) -> None:
        """选择下拉框选项。"""
        self._actions.select_option(selector, value)
```

### 添加 CLI 支持

在 `run.py` 中添加命令：

```python
# 在 browser_parser 中添加
hover_parser = browser_subparsers.add_parser("hover", help="鼠标悬停")
hover_parser.add_argument("selector", help="CSS 选择器")

# 在命令处理中添加
elif browser_args.browser_command == "hover":
    controller.hover(browser_args.selector)
```

---

## 🧪 测试指南

### 运行测试

```bash
# 所有测试
python run.py test --all

# 特定类别
python run.py test --category basic
python run.py test --category predefined

# 使用 pytest
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=src --cov-report=html
```

### 编写测试

```python
import unittest
from src.core.models import Task, TaskSequence
from src.core.executor import TaskExecutor

class TestMyFeature(unittest.TestCase):
    """测试新功能。"""
    
    def setUp(self):
        """测试前准备。"""
        self.executor = TaskExecutor()
    
    def test_task_execution(self):
        """测试任务执行。"""
        task = Task("wait", delay=0.1)
        result = self.executor.execute(TaskSequence("test", [task]))
        self.assertTrue(result.success)
    
    def tearDown(self):
        """测试后清理。"""
        pass

if __name__ == "__main__":
    unittest.main()
```

### 测试规范

1. **独立性**: 每个测试独立运行
2. **可重复**: 多次运行结果一致
3. **快速**: 单个测试 < 5 秒
4. **覆盖率**: 核心代码覆盖 > 80%

---

## 📤 提交贡献

### 工作流程

1. **Fork 仓库**
   ```bash
   git clone https://github.com/your-username/openclaw-computer-use.git
   cd openclaw-computer-use
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/my-feature
   # 或
   git checkout -b fix/bug-description
   ```

3. **开发功能**
   - 编写代码
   - 添加测试
   - 更新文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new feature
   
   - 详细描述 1
   - 详细描述 2"
   ```

5. **推送分支**
   ```bash
   git push origin feature/my-feature
   ```

6. **创建 Pull Request**
   - 描述变更内容
   - 关联相关 Issue
   - 确保 CI 通过

### 提交信息规范

使用 [Conventional Commits](https://conventionalcommits.org/)：

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

示例：
```bash
git commit -m "feat: add support for custom selectors

- Add SelectorConfig class
- Support multiple fallback selectors
- Update all predefined tasks"
```

---

## 🔌 插件开发

### 创建插件

```python
from src.core.plugin import BasePlugin

class MyPlugin(BasePlugin):
    """自定义插件示例。"""
    
    @property
    def name(self) -> str:
        return "my_plugin"
    
    def initialize(self, config: dict) -> None:
        """初始化插件。"""
        self.config = config
    
    def execute(self, params: dict) -> dict:
        """执行插件功能。"""
        # 你的逻辑
        return {"status": "success", "data": ...}
```

### 注册插件

```python
from src.core.plugin import PluginManager

manager = PluginManager()
manager.register(MyPlugin())
```

---

## 📚 文档更新

修改代码后，同步更新：

1. **README.md**: 主要功能变更
2. **API.md**: 新增/修改的 API
3. **PREDEFINED_TASKS.md**: 新增任务
4. **CHANGELOG.md**: 版本变更记录

---

## 🐛 调试技巧

### 启用调试日志

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 使用断点

```python
import pdb; pdb.set_trace()
```

### 可视化调试

```python
from src.utils.visualizer import ExecutionVisualizer

viz = ExecutionVisualizer()
viz.visualize_detection(screenshot, elements)
```

---

## 📞 获取帮助

- 查看 [FAQ](FAQ.md)
- 提交 GitHub Issue
- 加入开发者社区

---

**感谢你的贡献！🎉**
