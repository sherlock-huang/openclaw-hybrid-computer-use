# 项目结构说明

> OpenClaw Computer-Use Agent 项目目录结构

---

## 📁 目录概览

```
openclaw-computer-use/
├── docs/                   # 文档
├── examples/               # 示例代码和任务
├── models/                 # AI模型文件
├── recordings/             # 录制任务（用户生成）
├── scripts/                # 脚本工具
├── src/                    # 源代码
├── tests/                  # 测试代码
├── temp_backup/            # 临时备份（清理中）
├── logs/                   # 日志文件（.gitignore）
├── browser_data/           # 浏览器数据（.gitignore）
├── README.md               # 项目主文档
├── PROJECT_STRUCTURE.md    # 本文件
├── requirements.txt        # Python依赖
├── run.py                  # CLI入口
└── .gitignore              # Git忽略配置
```

---

## 📂 详细结构

### `docs/` - 文档

```
docs/
├── README.md               # 文档导航中心
├── QUICKSTART.md           # 快速入门
├── RECORDING.md            # 任务录制指南
├── BROWSER_AUTOMATION.md   # 浏览器自动化
├── PREDEFINED_TASKS.md     # 预置任务参考
├── vision_usage.md         # VLM智能模式
├── FAQ.md                  # 常见问题
├── DEVELOPER_GUIDE.md      # 开发者指南
├── ARCHITECTURE.md         # 架构设计
├── ROADMAP.md              # 路线图
├── API.md                  # API参考
├── MVP-RELEASE.md          # MVP发布说明
├── MVP-SPEC.md             # MVP规格
├── PHASE1_COMPLETION.md    # 阶段1完成报告
├── PHASE2_COMPLETION.md    # 阶段2完成报告
└── superpowers/            # Superpowers工作流文档
    ├── plans/              # 计划文档
    └── specs/              # 设计规格
```

### `src/` - 源代码

```
src/
├── __init__.py             # 包初始化
├── __main__.py             # 模块入口
├── action/                 # 行动层（鼠标、键盘、应用）
│   ├── __init__.py
│   ├── mouse.py            # 鼠标控制
│   ├── keyboard.py         # 键盘控制
│   └── app_manager.py      # 应用管理
├── browser/                # 浏览器自动化
│   ├── __init__.py
│   ├── controller.py       # 浏览器控制器
│   └── actions.py          # 浏览器操作
├── core/                   # 核心引擎
│   ├── __init__.py
│   ├── agent.py            # 主Agent类
│   ├── config.py           # 配置管理
│   ├── executor.py         # 任务执行器
│   ├── executor_enhanced.py# 增强版执行器
│   ├── models.py           # 数据模型
│   ├── recorder.py         # 录制器
│   ├── selectors_config.py # 选择器配置
│   └── tasks_predefined.py # 预置任务定义
├── perception/             # 感知层（截图、检测、OCR）
│   ├── __init__.py
│   ├── screen.py           # 屏幕截图
│   ├── detector.py         # 元素检测
│   └── ocr.py              # 文字识别
├── recording/              # 录制功能
│   ├── __init__.py
│   ├── hybrid_recorder.py  # 混合录制器
│   ├── browser_recorder.py # 浏览器录制
│   └── window_detector.py  # 窗口检测
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── logger.py           # 日志工具
│   ├── visualizer.py       # 可视化
│   ├── image.py            # 图像处理
│   ├── task_builder.py     # 任务构建器
│   ├── recording_overlay.py# 录制悬浮窗
│   └── shortcut_listener.py# 快捷键监听
└── vision/                 # VLM智能模式
    ├── __init__.py
    ├── llm_client.py       # VLM客户端
    ├── prompts.py          # 提示词模板
    └── task_planner.py     # 任务规划器
```

### `tests/` - 测试代码

```
tests/
├── __init__.py
├── test_suite.py           # 测试套件
├── test_models.py          # 模型测试
├── test_executor.py        # 执行器测试
├── test_executor_browser.py# 浏览器执行器测试
├── test_browser_actions.py # 浏览器操作测试
├── test_browser_controller.py # 浏览器控制器测试
├── test_browser_recorder.py # 浏览器录制测试
├── test_hybrid_recorder.py # 混合录制测试
├── test_recorder.py        # 录制器测试
├── test_recorder_integration.py # 录制集成测试
├── test_recording_overlay.py # 录制悬浮窗测试
├── test_screen.py          # 屏幕测试
├── test_mouse_keyboard.py  # 鼠标键盘测试
├── test_shortcut_listener.py # 快捷键测试
├── test_window_detector.py # 窗口检测测试
└── benchmark.py            # 性能基准测试
```

### `examples/` - 示例

```
examples/
├── README.md               # 示例说明
├── basic_usage.py          # 基础用法示例
├── predefined_tasks_demo.py # 预置任务演示
├── new_tasks_demo.py       # 新任务演示
├── vision_example.py       # VLM模式示例
├── browser_persistent_login.md # 持久登录示例
├── task_calculator.json    # 计算器任务示例
├── task_notepad.json       # 记事本任务示例
├── douyin_search.json      # 抖音搜索任务
├── simple_browser_test.json # 简单浏览器测试
├── recorded_example.json   # 录制示例
├── recorded_douyin_example.json # 抖音录制示例
└── saved_tasks/            # 保存的任务
    └── github_login_task.json
```

### `scripts/` - 脚本工具

```
scripts/
└── init-superpowers.ps1    # Superpowers初始化脚本
```

### `models/` - AI模型

```
models/
└── yolov8n.pt              # YOLOv8n模型（自动下载）
```

---

## 🔧 核心文件说明

### 入口文件

| 文件 | 说明 |
|------|------|
| `run.py` | CLI主入口，支持所有命令 |
| `src/__main__.py` | 模块入口，`python -m src` |

### 配置文件

| 文件 | 说明 |
|------|------|
| `requirements.txt` | Python依赖列表 |
| `.gitignore` | Git忽略配置 |

---

## 📊 代码统计

| 目录 | 文件数 | 代码行数(约) |
|------|--------|--------------|
| `src/` | 39 | ~5000 |
| `tests/` | 18 | ~2500 |
| `docs/` | 19 | ~35000(含) |
| `examples/` | 10+ | ~500 |
| `scripts/` | 13 | ~2000 |

---

## 🎯 开发规范

### 添加新功能

1. **核心功能** → `src/core/`
2. **浏览器功能** → `src/browser/`
3. **录制功能** → `src/recording/`
4. **工具函数** → `src/utils/`
5. **测试代码** → `tests/`
6. **使用示例** → `examples/`
7. **文档** → `docs/`

### 命名规范

- 模块名：`snake_case.py`
- 类名：`PascalCase`
- 函数名：`snake_case`
- 常量名：`UPPER_SNAKE_CASE`

---

## 🧹 清理规则

### 自动清理（.gitignore）

- `logs/` - 日志文件
- `browser_data/` - 浏览器数据
- `recordings/*.json` - 录制的任务
- `*.png`, `*.jpg` - 截图文件
- `__pycache__/` - Python缓存

### 手动清理

- `temp_backup/` - 临时备份文件
- 旧日志文件（保留最近3个）

---

**最后更新**: 2026-04-11
