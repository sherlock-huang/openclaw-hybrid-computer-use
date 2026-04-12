# OpenClaw Computer-Use Agent

**项目代号**: ClawDesktop  
**版本**: v0.2.0 ✅  
**创建时间**: 2026-04-10  
**设计**: 鲲鹏 (OpenClaw Agent)  

---

## 🎉 v0.2.0 新功能

✅ **VLM 智能模式** - 用自然语言控制浏览器，AI 自动分析屏幕执行操作  
✅ **任务录制** - 按 `Ctrl+R` 录制桌面操作，自动生成可重放的任务文件  
✅ **MVP v0.1.0** - 10个预定义任务、16项测试、完整文档

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd openclaw-computer-use

# 安装依赖
pip install -r requirements.txt
```

### 运行示例

```bash
# 列出预定义任务
python run.py run --list

# 运行记事本任务
python run.py run notepad_type

# 运行计算器任务
python run.py run calculator_add a=5 b=3

# 检测屏幕元素
python run.py detect --visualize

# 录制任务（新功能！）
python run.py record

# 运行测试
python run.py test --all
```

### Python API

```python
from claw_desktop import ComputerUseAgent

agent = ComputerUseAgent()

# 执行预定义任务
result = agent.execute_task("notepad_type", text="Hello World!")

print(f"成功: {result.success}")
print(f"耗时: {result.duration:.2f}s")
```

---

## ✨ 核心功能

| 功能 | 描述 | 状态 |
|------|------|------|
| 📸 屏幕截图 | mss/PIL 双后端 | ✅ |
| 🔍 元素检测 | YOLOv8n 检测 UI 元素 | ✅ |
| 📝 OCR | PaddleOCR 文字识别 | ✅ |
| 🖱️ 鼠标控制 | 移动、点击、滚动、拖拽 | ✅ |
| ⌨️ 键盘控制 | 输入、组合键、快捷键 | ✅ |
| 📱 应用管理 | 启动计算器、记事本等 | ✅ |
| ⚡ 任务执行 | 序列化任务、错误恢复 | ✅ |
| 📊 可视化 | 执行过程截图、报告 | ✅ |
| 🧠 VLM 智能 | 自然语言控制浏览器 | ✅ |

---

## 📦 项目结构

```
openclaw-computer-use/
├── src/                     # 源代码 (~1800 行)
│   ├── core/               # 核心引擎
│   ├── perception/         # 感知层
│   ├── action/             # 行动层
│   └── utils/              # 工具函数
├── tests/                  # 测试套件
│   ├── test_suite.py       # 16项标准测试
│   └── benchmark.py        # 性能基准
├── examples/               # 示例任务
├── docs/                   # 文档
│   ├── API.md             # API文档
│   ├── MVP-RELEASE.md     # 发布说明
│   └── ...
├── run.py                  # 主运行脚本
└── requirements.txt        # 依赖
```

---

## 📊 性能指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 截图耗时 | < 500ms | ~300ms | ✅ |
| 元素检测 | < 2s | ~1.5s | ✅ |
| 鼠标移动 | < 500ms | ~200ms | ✅ |
| 内存占用 | < 2GB | ~800MB | ✅ |
| 测试通过 | 16项 | 16项 | ✅ |

---

## 🎯 预定义任务 (10个)

```python
# 计算器加法
agent.execute_task("calculator_add", a=5, b=3)

# 记事本输入
agent.execute_task("notepad_type", text="Hello")

# Chrome 搜索
agent.execute_task("chrome_search", url="openclaw.ai")

# 文件导航
agent.execute_task("explorer_navigate", path="Desktop")

# 更多: window_switch, desktop_screenshot, text_copy_paste, 
#       scroll_test, right_click, multi_app
```

---

## 📚 文档

- [API 文档](docs/API.md) - 完整的 API 参考
- [VLM 使用指南](docs/vision_usage.md) - 智能模式使用说明
- [发布说明](docs/MVP-RELEASE.md) - MVP 发布详情
- [架构设计](docs/ARCHITECTURE.md) - 系统设计
- [MVP 规格](docs/MVP-SPEC.md) - 详细规格
- [开发路线](docs/ROADMAP.md) - 未来计划

---

## 🛠️ CLI 命令

```bash
# 任务相关
python run.py run --list                    # 列出任务
python run.py run notepad_type              # 运行任务
python run.py run calculator_add a=5 b=3   # 带参数

# 检测
python run.py detect --visualize            # 检测屏幕元素

# 测试
python run.py test                          # 基础测试
python run.py test --all                    # 全部测试
python run.py benchmark                     # 性能测试

# 执行任务文件
python run.py execute examples/task.json
```

---

## 🗺️ 路线图

### v0.2.0 (第4周末)
- [ ] 浏览器深度集成
- [ ] 自适应坐标识别
- [ ] 更多预定义任务 (20+)

### v0.3.0 (第6周末)
- [ ] 专门的 UI 检测模型
- [ ] 自然语言任务理解
- [ ] 复杂多步骤任务

### v0.2.0 VLM 智能模式
自然语言控制浏览器，支持 OpenAI 和 Anthropic：
```bash
py -m src vision "在抖音上搜索美食视频"
```

### v1.0.0
- [ ] 跨平台优化
- [ ] 多显示器支持
- [ ] 视觉语言模型集成

---

## 🎯 项目背景

### 问题定义

当前 OpenClaw 在 Computer-Use 领域存在明显短板：

1. **浏览器限制**: 原生 `browser` 工具只能处理网页，无法操作桌面应用
2. **缺乏视觉感知**: 无法"看见"屏幕内容，只能依赖结构化数据
3. **工具割裂**: agent-browser、PyAutoGUI、YOLO 各自独立，没有统一协调

### 市场机会

- OpenAI Computer-Use: 闭源、API调用成本高、数据隐私风险
- Fara-7B: 仅支持网页，无法操作本地应用
- 开源桌面自动化: 多为脚本工具，缺乏 AI Agent 的智能规划能力

**空白市场**: 一个真正开源、可本地部署、支持完整桌面+网页的 Computer-Use Agent

### 项目愿景

打造 OpenClaw 生态中最强大的 Computer-Use 能力，让用户可以用自然语言控制整个计算机：

> "打开Excel，把销售数据图表复制到PPT第二页，然后保存到桌面"

---

## 📝 变更记录

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| 2026-04-11 | v0.1.0 | MVP完成: 10个任务、16项测试、API文档 | 开发Agent |
| 2026-04-10 | v0.0.1 | 项目创建，MVP方案设计 | 鲲鹏 |

---

## 📄 许可

MIT License

---

**感谢使用 OpenClaw Computer-Use Agent! 🎉**
