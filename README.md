# OpenClaw Computer-Use Agent 🖥️🤖

**项目代号**: ClawDesktop
**版本**: v0.6.0 ✅
**更新日期**: 2026-04-25  

> 开源桌面 + 浏览器自动化 Agent，支持自然语言控制、任务录制、智能回放

---

## 🎉 最新功能 (v0.6.0)

| 版本 | 功能 | 描述 |
|------|------|------|
| v0.6.0 | **任务调度器** | 支持 interval / cron / at 三种定时调度模式，后台线程运行 |
| v0.6.0 | **批量任务执行** | 顺序/并行批量执行，支持 JSON 配置和 Markdown/HTML/JSON 报告 |
| v0.6.0 | **统一异常处理** | 完整的异常层级体系，结构化错误信息，自动截图保留现场 |
| v0.5.0 | **GUI 任务编辑器** | tkinter 可视化任务编排，支持执行日志和实时截图预览 |
| v0.4.0 | **Office 自动化** | Excel 读写、Word 模板填充，支持数据批量处理 |
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

### 方式四：批量任务 & 定时调度 (高级)

```bash
# 执行批量任务
python run.py batch examples/batch_demo.json

# 批量任务 dry-run（仅列出，不执行）
python run.py batch examples/batch_demo.json --dry-run

# 定时调度（每 3600 秒执行一次）
python run.py schedule examples/scheduler_demo.json --interval 3600

# Cron 调度（每天 9:00）
python run.py schedule examples/scheduler_demo.json --cron "0 9 * * *"

# 立即执行一次调度任务
python run.py schedule examples/scheduler_demo.json --once
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
| 📦 **批量任务执行** | 顺序/并行执行、JSON 配置、多格式报告 | ✅ |
| ⏰ **任务调度器** | interval / cron / at 三种定时模式 | ✅ |
| 🖥️ **GUI 任务编辑器** | tkinter 可视化编排、日志面板、截图预览 | ✅ |
| 📄 **Office 自动化** | Excel 读写、Word 模板填充 | ✅ |
| 🛡️ **统一异常处理** | 结构化错误体系、自动截图保留现场 | ✅ |

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
- [预置任务参考](docs/PREDEFINED_TASKS.md) - 64+ 预置任务详解

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

## 🎯 64+ 预置任务

### 桌面应用 (12个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `calculator` | 计算器运算 | `python run.py run calculator expr="1+2"` |
| `notepad` | 记事本操作 | `python run.py run notepad text="Hello"` |
| `open_wechat` | 打开微信 | `python run.py run open_wechat` |
| `open_qq` | 打开 QQ | `python run.py run open_qq` |
| `open_dingtalk` | 打开钉钉 | `python run.py run open_dingtalk` |
| `explorer` | 文件管理器 | `python run.py run explorer path=Desktop` |
| `open_cmd` | 打开命令行 | `python run.py run open_cmd` |
| `open_settings` | 打开系统设置 | `python run.py run open_settings` |
| `open_task_manager` | 打开任务管理器 | `python run.py run open_task_manager` |
| `system_lock` | 锁定屏幕 | `python run.py run system_lock` |
| `shutdown_system` | 关机 | `python run.py run shutdown_system` |
| `restart_system` | 重启 | `python run.py run restart_system` |

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

### Office 自动化 (6个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `excel_report` | Excel 报表生成 | `python run.py run excel_report filepath=report.xlsx` |
| `excel_write_data` | Excel 写入数据 | `python run.py run excel_write_data filepath=data.xlsx` |
| `excel_read_data` | Excel 读取数据 | `python run.py run excel_read_data filepath=data.xlsx cell=A1` |
| `word_document` | Word 创建文档 | `python run.py run word_document text="Hello"` |
| `word_template_fill` | Word 模板填充 | `python run.py run word_template_fill template=template.docx` |
| `word_open_read` | Word 读取文档 | `python run.py run word_open_read filepath=doc.docx` |

### 文件操作 (8个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `file_copy` | 复制文件 | `python run.py run file_copy src=a.txt dst=b.txt` |
| `file_move` | 移动文件 | `python run.py run file_move src=a.txt dst=folder/` |
| `file_delete` | 删除文件 | `python run.py run file_delete path=a.txt` |
| `folder_create` | 创建文件夹 | `python run.py run folder_create path=new_folder` |
| `project_folder` | 创建项目结构 | `python run.py run project_folder base_path=./myproject` |
| `new_text_file` | 新建文本文件 | `python run.py run new_text_file filename=note.txt content=Hello` |
| `browser_download` | 下载文件 | `python run.py run browser_download url=https://...` |
| `screenshot_save` | 截图保存 | `python run.py run screenshot_save filepath=shot.png` |

### 智能定位 (5个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `locate_and_click_image` | 图像定位点击 | `python run.py run locate_and_click_image template=btn.png` |
| `locate_and_click_text` | 文本定位点击 | `python run.py run locate_and_click_text text="确认"` |
| `wait_and_click_image` | 等待并点击图像 | `python run.py run wait_and_click_image template=btn.png` |
| `wait_and_click_text` | 等待并点击文本 | `python run.py run wait_and_click_text text="提交"` |
| `click_below_text` | 点击文本下方 | `python run.py run click_below_text reference="标题" target="按钮"` |

### 插件与扩展 (6个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `plugin_api_get` | API GET 请求 | `python run.py run plugin_api_get url=https://api.example.com` |
| `plugin_api_post` | API POST 请求 | `python run.py run plugin_api_post url=https://api.example.com` |
| `plugin_db_query` | 数据库查询 | `python run.py run plugin_db_query db_path=data.db` |
| `plugin_db_insert` | 数据库插入 | `python run.py run plugin_db_insert db_path=data.db` |
| `plugin_db_create_table` | 创建数据表 | `python run.py run plugin_db_create_table db_path=data.db` |
| `plugin_list` | 列出所有插件 | `python run.py run plugin_list` |

### 其他实用任务 (17个)

| 任务 | 描述 | 示例 |
|------|------|------|
| `shell_command` | 执行 Shell 命令 | `python run.py run shell_command command="echo Hello"` |
| `run_python_script` | 运行 Python 脚本 | `python run.py run run_python_script script_path=test.py` |
| `system_info` | 查看系统信息 | `python run.py run system_info` |
| `copy_to_clipboard` | 复制到剪贴板 | `python run.py run copy_to_clipboard text="Hello"` |
| `desktop_cleanup` | 桌面清理 | `python run.py run desktop_cleanup` |
| `desktop_screenshot` | 桌面截图 | `python run.py run desktop_screenshot` |
| `window_switch` | 窗口切换 | `python run.py run window_switch` |
| `scroll_test` | 滚动测试 | `python run.py run scroll_test` |
| `right_click` | 右键测试 | `python run.py run right_click` |
| `multi_app` | 多应用演示 | `python run.py run multi_app` |
| `text_copy_paste` | 复制粘贴 | `python run.py run text_copy_paste` |
| `wechat_send` | 微信发消息 | `python run.py run wechat_send contact=张三 msg=Hello` |
| `local_vlm_analyze` | 本地 VLM 分析 | `python run.py run local_vlm_analyze instruction="分析屏幕"` |

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

# ========== 批量任务 & 调度 ==========
python run.py batch examples/batch_demo.json  # 执行批量任务
python run.py batch examples/batch_demo.json --dry-run  # 仅预览
python run.py schedule examples/scheduler_demo.json --interval 3600  # 定时调度
python run.py schedule examples/scheduler_demo.json --once  # 立即执行一次

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

### v0.6.x (当前)
- [x] 任务调度器 (interval / cron / at)
- [x] 批量任务执行框架
- [x] 统一异常处理体系
- [x] GUI 任务编辑器增强
- [ ] 更多预置任务 (50+)
- [ ] 跨平台优化 (Linux/macOS)

### v0.7.0 (计划中)
- [ ] 任务学习引擎完善 (OCR 附近文本搜索)
- [ ] 插件系统扩展
- [ ] 多显示器支持

### v1.0.0 (规划中)
- [ ] 视觉语言模型本地部署
- [ ] 企业级安全特性
- [ ] 分布式任务执行

---

## 🤝 贡献与反馈

欢迎分享、引用与改进。

- 发现问题：欢迎提交 [Issue](https://github.com/sherlock-huang/openclaw-hybrid-computer-use/issues)
- 有改进建议：欢迎提交 [Pull Request](https://github.com/sherlock-huang/openclaw-hybrid-computer-use/pulls)

---

## 🔗 相关链接

- 主站博客：[https://kunpeng-ai.com](https://kunpeng-ai.com)
- GitHub 组织：[https://github.com/kunpeng-ai-research](https://github.com/kunpeng-ai-research)
- OpenClaw 官方：[https://openclaw.ai](https://openclaw.ai)

---

## 👤 维护与署名

- 维护者：**鲲鹏AI探索局**

---

## 📄 License

MIT License

---

**感谢使用 OpenClaw Computer-Use Agent! 🎉**
