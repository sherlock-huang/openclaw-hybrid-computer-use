# 项目文件索引

> OpenClaw Computer-Use Agent 文件结构说明

---

## 📁 根目录文件

### 核心入口

| 文件 | 说明 | 用法 |
|------|------|------|
| `run.py` | 主 CLI 入口 | `python run.py --help` |
| `wechat_send.py` | 微信发送消息 | `py wechat_send.py "联系人" "消息"` |
| `wechat_voice_assistant.py` | 微信语音助手（自然语言） | `py wechat_voice_assistant.py "指令"` |

### 配置文档

| 文件 | 说明 |
|------|------|
| `README.md` | 项目主文档 |
| `PROJECT_STRUCTURE.md` | 项目结构说明 |
| `FILE_INDEX.md` | 本文件（文件索引） |
| `requirements.txt` | Python 依赖列表 |
| `.gitignore` | Git 忽略配置 |

---

## 📂 源代码目录 `src/`

### 核心模块 `src/core/`

| 文件 | 说明 |
|------|------|
| `agent.py` | 主 Agent 类 |
| `config.py` | 配置管理 |
| `executor.py` | 任务执行器 |
| `executor_enhanced.py` | 增强版执行器 |
| `models.py` | 数据模型 |
| `recorder.py` | 录制器 |
| `selectors_config.py` | 网站选择器配置 |
| `tasks_predefined.py` | 预置任务定义 |

### 桌面操作 `src/action/`

| 文件 | 说明 |
|------|------|
| `mouse.py` | 鼠标控制 |
| `keyboard.py` | 键盘控制 |
| `app_manager.py` | 应用管理 |

### 浏览器自动化 `src/browser/`

| 文件 | 说明 |
|------|------|
| `controller.py` | 浏览器控制器 |
| `actions.py` | 浏览器操作 |

### 图像识别 `src/perception/`

| 文件 | 说明 |
|------|------|
| `screen.py` | 屏幕截图 |
| `detector.py` | 元素检测 |
| `ocr.py` | 文字识别 |

### 录制功能 `src/recording/`

| 文件 | 说明 |
|------|------|
| `hybrid_recorder.py` | 混合录制器 |
| `browser_recorder.py` | 浏览器录制 |
| `window_detector.py` | 窗口检测 |

### 工具函数 `src/utils/`

| 文件 | 说明 |
|------|------|
| `logger.py` | 日志工具 |
| `visualizer.py` | 可视化 |
| `wechat_helper.py` | 微信辅助工具 |
| `task_builder.py` | 任务构建器 |
| `recording_overlay.py` | 录制悬浮窗 |
| `shortcut_listener.py` | 快捷键监听 |
| `image.py` | 图像处理 |

### VLM 智能模式 `src/vision/`

| 文件 | 说明 |
|------|------|
| `llm_client.py` | VLM 客户端 |
| `task_planner.py` | 任务规划器 |
| `prompts.py` | 提示词模板 |
| `wechat_processor.py` | 微信自然语言处理器 |

---

## 📂 测试目录 `tests/`

| 文件 | 说明 |
|------|------|
| `test_suite.py` | 测试套件 |
| `test_models.py` | 模型测试 |
| `test_executor.py` | 执行器测试 |
| `test_browser_*.py` | 浏览器相关测试 |
| `test_recorder*.py` | 录制相关测试 |
| `benchmark.py` | 性能基准测试 |

---

## 📂 脚本工具 `scripts/`

| 文件 | 说明 |
|------|------|
| `init-superpowers.ps1` | Superpowers 初始化 |
| `cleanup.py` | 清理脚本 |
| `wechat_send.bat` | 微信发送批处理 |
| `wechat_*.py` | 微信相关测试脚本 |
| `test_*.py` | 各种测试脚本 |

---

## 📂 示例目录 `examples/`

| 文件 | 说明 |
|------|------|
| `basic_usage.py` | 基础用法示例 |
| `predefined_tasks_demo.py` | 预置任务演示 |
| `vision_example.py` | VLM 模式示例 |
| `wechat_send_example.py` | 微信发送示例 |
| `*.json` | 示例任务文件 |

---

## 📂 文档目录 `docs/`

| 文件 | 说明 |
|------|------|
| `README.md` | 文档导航中心 |
| `QUICKSTART.md` | 快速入门指南 |
| `PREDEFINED_TASKS.md` | 预置任务参考 |
| `BROWSER_AUTOMATION.md` | 浏览器自动化 |
| `RECORDING.md` | 任务录制指南 |
| `vision_usage.md` | VLM 智能模式 |
| `WECHAT_TEST_GUIDE.md` | 微信功能测试指南 |
| `WECHAT_VOICE_ASSISTANT.md` | 微信语音助手文档 |
| `API.md` | API 参考 |
| `FAQ.md` | 常见问题 |
| `DEVELOPER_GUIDE.md` | 开发者指南 |
| `ARCHITECTURE.md` | 架构设计 |
| `ROADMAP.md` | 路线图 |

---

## 📂 数据目录（运行时生成）

| 目录 | 说明 | Git 忽略 |
|------|------|----------|
| `logs/` | 日志文件 | ✅ |
| `recordings/` | 录制任务 | ✅ |
| `browser_data/` | 浏览器数据 | ✅ |
| `models/` | AI 模型 | 部分 |

---

## 🚀 快速访问

### 常用命令

```bash
# 查看帮助
python run.py --help

# 列出预置任务
python run.py run --list

# 运行任务
python run.py run calculator a=5 b=3

# 微信发送消息
py wechat_send.py "联系人" "消息"

# 微信语音助手
py wechat_voice_assistant.py "给张三发消息说晚上好"
```

### 快速测试

```bash
# 运行测试
python run.py test --all

# 微信功能测试
py scripts/wechat_test_minimal.py
```

---

**最后更新**: 2026-04-11
