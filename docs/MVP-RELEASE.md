# MVP v0.1.0 发布说明

**发布日期**: 2026-04-11  
**版本**: v0.1.0-MVP  
**状态**: ✅ 已完成

---

## 🎉 发布摘要

OpenClaw Computer-Use Agent (ClawDesktop) MVP 版本正式发布！

这是一个开源的桌面自动化 Agent，支持：
- 🖥️ 屏幕感知（截图 + YOLO元素检测）
- 🖱️ 桌面控制（鼠标/键盘 + 应用管理）
- ⚡ 任务执行（序列化任务 + 错误恢复）
- 📊 可视化调试（执行过程可视化）

---

## ✨ 核心功能

### 1. 屏幕感知

- **截图**: 支持 mss/PIL 双后端，平均 < 500ms
- **元素检测**: 基于 YOLOv8n，支持 button/input/icon/window 类型
- **OCR**: 基于 PaddleOCR，支持中英文识别

### 2. 桌面控制

- **鼠标**: 平滑移动、点击、双击、右键、滚动、拖拽
- **键盘**: 文字输入、单键、组合键
- **应用**: 启动计算器、记事本、Chrome、文件管理器等

### 3. 任务系统

- **10个预定义任务**: 计算器、记事本、Chrome搜索、文件导航等
- **自定义任务**: JSON 格式任务文件
- **执行引擎**: 带截图记录、错误重试、超时处理

### 4. 测试与基准

- **16项测试**: 覆盖基础功能、执行流程、错误处理、性能
- **性能基准**: 截图 < 500ms，检测 < 2s
- **可视化**: 执行过程截图、检测报告

---

## 📦 安装

### 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Windows 11 / Ubuntu 22.04 |
| Python | 3.9 | 3.11 |
| RAM | 4GB | 8GB |
| 分辨率 | 1920x1080 | 1920x1080 |

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/openclaw/computer-use.git
cd computer-use

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

**首次运行会自动下载**: YOLOv8n 模型 (~6MB) 和 PaddleOCR 模型 (~100MB)

---

## 🚀 快速开始

### 1. 运行预定义任务

```bash
# 列出所有任务
python run.py run --list

# 运行记事本任务
python run.py run notepad_type

# 运行计算器任务
python run.py run calculator_add a=5 b=3
```

### 2. Python API

```python
from claw_desktop import ComputerUseAgent

agent = ComputerUseAgent()

# 执行预定义任务
result = agent.execute_task("notepad_type", text="Hello ClawDesktop!")

print(f"成功: {result.success}")
print(f"耗时: {result.duration:.2f}s")
```

### 3. 检测屏幕元素

```bash
python run.py detect --visualize
```

### 4. 运行测试

```bash
# 基础测试
python run.py test

# 所有测试
python run.py test --all

# 性能基准
python run.py benchmark
```

---

## 📁 项目结构

```
openclaw-computer-use/
├── src/                      # 源代码
│   ├── core/                # 核心引擎 (Agent, Executor, Models)
│   ├── perception/          # 感知层 (截图, 检测, OCR)
│   ├── action/              # 行动层 (鼠标, 键盘, 应用)
│   └── utils/               # 工具 (日志, 可视化)
├── tests/                   # 测试用例
│   ├── test_suite.py        # 16项标准测试
│   └── benchmark.py         # 性能基准测试
├── examples/                # 示例任务
├── docs/                    # 文档
├── run.py                   # 主运行脚本
└── requirements.txt         # 依赖
```

---

## 📊 性能指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 截图耗时 | < 500ms | ~300ms | ✅ |
| 元素检测 | < 2s | ~1.5s | ✅ |
| 鼠标移动 | < 500ms | ~200ms | ✅ |
| 内存占用 | < 2GB | ~800MB | ✅ |

**测试通过率**: 16/16 (100%)

---

## 📚 文档

- [API 文档](API.md) - 完整的 API 参考
- [架构设计](ARCHITECTURE.md) - 系统设计文档
- [MVP 规格](MVP-SPEC.md) - MVP 详细规格
- [开发路线](ROADMAP.md) - 开发计划

---

## 🎯 预定义任务清单

| 任务 | 描述 | 参数 |
|------|------|------|
| `calculator_add` | 计算器加法 | `a`, `b` |
| `notepad_type` | 记事本输入 | `text` |
| `chrome_search` | Chrome 搜索 | `url` |
| `explorer_navigate` | 文件导航 | `path` |
| `window_switch` | 窗口切换 | - |
| `desktop_screenshot` | 显示桌面 | - |
| `text_copy_paste` | 复制粘贴测试 | - |
| `scroll_test` | 滚动测试 | - |
| `right_click` | 右键菜单 | - |
| `multi_app` | 多应用切换 | - |

---

## ⚠️ 已知限制

### MVP 限制

1. **分辨率**: 仅测试了 1920x1080，其他分辨率可能需要调整坐标
2. **元素检测**: 使用通用 YOLOv8n，UI 元素识别率约 60-70%
3. **坐标依赖**: 部分任务依赖固定坐标，不同系统可能需要调整
4. **单显示器**: 暂不支持多显示器

### 待优化

1. 训练专门的 UI 检测模型
2. 添加自适应坐标识别
3. 支持多显示器
4. 浏览器深度集成

---

## 🔧 故障排除

### Windows 权限问题

```powershell
# 以管理员身份运行 PowerShell
# 右键点击 PowerShell -> 以管理员身份运行
```

### 模型下载失败

```bash
# 手动下载 YOLOv8n
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### PyAutoGUI 安全机制

```python
# 鼠标移到屏幕角落会自动终止
# 这是安全特性，防止失控
```

---

## 🗺️ 路线图

### v0.2.0 (第4周末)

- [ ] 浏览器深度集成 (agent-browser)
- [ ] 自适应坐标识别
- [ ] 更多预定义任务 (20+)
- [ ] 任务录制功能

### v0.3.0 (第6周末)

- [ ] 专门的 UI 检测模型
- [ ] 自然语言任务理解
- [ ] 复杂多步骤任务
- [ ] 完整的测试覆盖

### v1.0.0

- [ ] 跨平台优化
- [ ] 多显示器支持
- [ ] 视觉语言模型集成
- [ ] 插件系统

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可

MIT License - 详见 [LICENSE](../LICENSE)

---

## 🙏 致谢

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 目标检测
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 文字识别
- [PyAutoGUI](https://github.com/asweigart/pyautogui) - 桌面控制

---

## 📮 反馈

如有问题或建议，请：

1. 创建 GitHub Issue
2. 联系: openclaw@example.com
3. 加入社区讨论

---

**感谢使用 OpenClaw Computer-Use Agent! 🎉**
