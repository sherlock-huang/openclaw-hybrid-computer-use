# OpenClaw Computer-Use Agent 🖥️🤖

**项目代号**: ClawDesktop  
**版本**: v0.3.1 ✅  
**更新日期**: 2026-04-11  

> 开源桌面 + 浏览器自动化 Agent，支持自然语言控制、任务录制、智能回放

---

## 🎉 最新功能 (v0.3.1)

| 版本 | 功能 | 描述 |
|------|------|------|
| v0.3.1 | **稳定性优化** | 多重选择器降级、智能重试机制、28个预置任务 |
| v0.3.0 | **VLM 智能模式** | 用自然语言控制浏览器，AI 自动分析屏幕执行操作 |
| v0.2.1 | **任务录制** | 按 `Ctrl+R` 录制操作，支持桌面+浏览器混合录制 |
| v0.2.0 | **浏览器自动化** | Playwright 集成，10+ 浏览器操作 |
| v0.1.0 | **桌面自动化** | YOLO 元素检测、鼠标键盘控制、10个预置任务 |

---

## 🚀 三种使用方式

### 方式一：任务录制 (最简单)

```bash
# 录制你的操作
python run.py record

# 录制时按 Ctrl+R 开始，Ctrl+Shift+R 停止
# 自动生成任务文件，可随时回放

# 回放录制的任务
python run.py execute recordings/my_task.json
```

### 方式二：预置任务 (最稳定)

```bash
# 查看所有预置任务
python run.py run --list

# 桌面任务
python run.py run calculator a=5 b=3           # 计算器
python run.py run notepad text="Hello"         # 记事本
python run.py run open_wechat                             # 打开微信
py wechat_send.py "张三" "晚上好！"                        # 微信发消息
py wechat_voice_assistant.py "给张三发消息说晚上好"          # 自然语言控制微信

# 浏览器任务
python run.py run github_login user=xxx        # GitHub登录
python run.py run taobao_search kw=手机        # 淘宝搜索
python run.py run douyin_search kw=美食        # 抖音搜索
python run.py run bilibili_search kw=Python    # B站搜索
```

### 方式三：自然语言 (最智能)

```bash
# 需要设置 KIMI_CODING_API_KEY
set KIMI_CODING_API_KEY=your_api_key

# 用自然语言控制
py -m src vision "帮我在淘宝上搜索蓝牙耳机"
py -m src vision "在B站搜索Python教程视频"
py -m src vision "打开京东搜索手机并查看第一个商品"
```

---

## 📦 安装

### 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| Python | 3.9 | 3.11+ |
| RAM | 4GB | 8GB |
| 分辨率 | 1920x1080 | 1920x1080 |

### 安装步骤

```bash
# 1. 克隆仓库
git clone <repo-url>
cd openclaw-computer-use

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install -r requirements.txt

# 4. (可选) 配置 API Key 用于 VLM 模式
set KIMI_CODING_API_KEY=your_api_key  # Windows
export KIMI_CODING_API_KEY=your_api_key  # Linux/macOS
```

---

## ✨ 核心功能

| 功能模块 | 特性 | 状态 |
|----------|------|------|
| 📸 **屏幕感知** | 截图、YOLOv8 元素检测、OCR 文字识别 | ✅ |
| 🖱️ **桌面控制** | 鼠标、键盘、应用启动、窗口管理 | ✅ |
| 🌐 **浏览器自动化** | Playwright 集成、持久登录、元素操作 | ✅ |
| 🎬 **任务录制** | 桌面+浏览器混合录制、自动回放 | ✅ |
| 🧠 **VLM 智能** | Kimi Coding API、自然语言理解 | ✅ |
| ⚡ **稳定性优化** | 多重选择器、智能重试、降级机制 | ✅ |

---

## 📂 项目结构

```
openclaw-computer-use/
├── docs/                   # 完整文档
├── examples/               # 示例代码和任务
├── models/                 # AI模型
├── recordings/             # 录制任务（用户生成）
├── scripts/                # 脚本工具
├── src/                    # 源代码
├── tests/                  # 测试代码
├── run.py                  # CLI入口
└── requirements.txt        # 依赖
```

详细结构见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 📚 文档导航

### 入门教程
- [快速入门指南](docs/QUICKSTART.md) - 5分钟上手
- [任务录制指南](docs/RECORDING.md) - 如何录制和回放操作
- [预置任务参考](docs/PREDEFINED_TASKS.md) - 28个预置任务详解

### 进阶使用
- [浏览器自动化](docs/BROWSER_AUTOMATION.md) - 浏览器操作详解
- [VLM 智能模式](docs/vision_usage.md) - 自然语言控制
- [API 参考](docs/API.md) - Python API 完整文档

### 开发文档
- [项目结构](PROJECT_STRUCTURE.md) - 目录结构说明
- [架构设计](docs/ARCHITECTURE.md) - 系统架构说明
- [开发者指南](docs/DEVELOPER_GUIDE.md) - 贡献代码指南
- [FAQ](docs/FAQ.md) - 常见问题解答

---

## 🎯 28个预置任务

### 桌面应用 (18个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `calculator` | 计算器运算 | `python run.py run calculator a=5 b=3 op=+` |
| `notepad` | 记事本操作 | `python run.py run notepad text="Hello"` |
| `open_wechat` | 打开微信 | `python run.py run open_wechat` |
| `open_qq` | 打开 QQ | `python run.py run open_qq` |
| `open_dingtalk` | 打开钉钉 | `python run.py run open_dingtalk` |
| `explorer` | 文件管理器 | `python run.py run explorer path=Desktop` |

### 浏览器任务 (10个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `github_login` | GitHub 登录 | `python run.py run github_login user=xxx pass=xxx` |
| `taobao_search` | 淘宝搜索 | `python run.py run taobao_search kw=手机` |
| `jd_search` | 京东搜索 | `python run.py run jd_search kw=电脑` |
| `baidu_search` | 百度搜索 | `python run.py run baidu_search kw=天气` |
| `douyin_search` | 抖音搜索 | `python run.py run douyin_search kw=美食` |
| `bilibili_search` | B站搜索 | `python run.py run bilibili_search kw=Python` |
| `weibo_hot` | 微博热搜 | `python run.py run weibo_hot` |
| `zhihu_search` | 知乎搜索 | `python run.py run zhihu_search kw=AI` |
| `weather_check` | 天气查询 | `python run.py run weather_check city=北京` |
| `chrome_search` | Chrome 搜索 | `python run.py run chrome_search kw=openai` |

---

## 🛠️ CLI 命令速查

```bash
# ========== 任务执行 ==========
python run.py run --list                      # 列出所有预置任务
python run.py run calculator a=5 b=3          # 运行任务（带参数）
python run.py run notepad text="Hello World"

# ========== 任务录制 ==========
python run.py record                          # 开始录制
# Ctrl+R: 开始录制  Ctrl+Shift+R: 停止录制
python run.py execute recordings/task.json    # 回放任务

# ========== 屏幕检测 ==========
python run.py detect                          # 检测屏幕元素
python run.py detect --visualize              # 可视化检测结果

# ========== 浏览器 ==========
python run.py browser launch                  # 启动浏览器
python run.py browser goto https://www.example.com

# ========== 测试 ==========
python run.py test                            # 运行基础测试
python run.py test --all                      # 运行所有测试
python run.py benchmark                       # 性能测试

# ========== VLM 模式 ==========
py -m src vision "在淘宝上搜索手机"             # 自然语言控制
py -m src vision "在京东搜索电脑" -o task.json  # 保存任务文件
```

---

## 🐍 Python API

```python
from claw_desktop import ComputerUseAgent

# 初始化
agent = ComputerUseAgent()

# 执行预置任务
result = agent.execute_task("notepad", text="Hello World!")
print(f"成功: {result.success}, 耗时: {result.duration:.2f}s")

# 浏览器自动化
from src.browser.controller import BrowserController

with BrowserController() as browser:
    browser.goto("https://www.taobao.com")
    browser.click("#q")  # 搜索框
    browser.type("手机")
    browser.click(".btn-search")
```

---

## 📊 性能指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 截图耗时 | < 500ms | ~300ms | ✅ |
| 元素检测 | < 2s | ~1.5s | ✅ |
| 鼠标移动 | < 500ms | ~200ms | ✅ |
| 内存占用 | < 2GB | ~800MB | ✅ |
| 浏览器启动 | < 5s | ~3s | ✅ |
| VLM 分析 | < 5s | ~3s | ✅ |

---

## 🗺️ 路线图

### v0.4.0 (计划中)
- [ ] Excel/Word 自动化
- [ ] 更多预置任务 (50+)
- [ ] 插件系统
- [ ] 跨平台优化

### v1.0.0 (规划中)
- [ ] 多显示器支持
- [ ] 视觉语言模型本地部署
- [ ] 图形化界面
- [ ] 企业级安全特性

---

## 🤝 贡献

欢迎贡献！请查看 [开发者指南](docs/DEVELOPER_GUIDE.md)。

---

## 📄 许可

MIT License

---

**感谢使用 OpenClaw Computer-Use Agent! 🎉**
