# 快速入门指南

> 5分钟上手 OpenClaw Computer-Use Agent

---

## 📋 目录

1. [安装](#-安装) (2分钟)
2. [第一种方式：预置任务](#-第一种方式预置任务) (2分钟)
3. [第二种方式：任务录制](#-第二种方式任务录制) (3分钟)
4. [第三种方式：自然语言](#-第三种方式自然语言) (2分钟)

---

## 🔧 安装

### 步骤 1: 克隆仓库

```bash
git clone <repo-url>
cd openclaw-computer-use
```

### 步骤 2: 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

> **首次运行**会自动下载 YOLOv8n 模型 (~6MB) 和 PaddleOCR 模型 (~100MB)

### 步骤 4: 验证安装

```bash
python run.py test
```

看到 `✅ 所有测试通过!` 表示安装成功！

---

## 🚀 第一种方式：预置任务

最简单稳定的自动化方式，28个常用任务开箱即用。

### 查看所有任务

```bash
python run.py run --list
```

### 桌面任务示例

**1. 计算器**
```bash
# 计算 5 + 3
python run.py run calculator a=5 b=3 op=+

# 计算 10 - 4
python run.py run calculator a=10 b=4 op=-
```

**2. 记事本**
```bash
# 打开记事本并输入文字
python run.py run notepad text="Hello OpenClaw!"
```

**3. 打开常用应用**
```bash
python run.py run open_wechat     # 打开微信
python run.py run open_qq         # 打开 QQ
python run.py run open_dingtalk   # 打开钉钉
```

### 浏览器任务示例

**1. 淘宝搜索**
```bash
python run.py run taobao_search kw=手机
```

**2. 百度搜索**
```bash
python run.py run baidu_search kw=今天天气怎么样
```

**3. B站搜索**
```bash
python run.py run bilibili_search kw=Python教程
```

---

## 🎬 第二种方式：任务录制

录制你的操作，自动生成可重放的任务。

### 开始录制

```bash
python run.py record
```

### 录制控制

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + R` | 开始录制 |
| `Ctrl + Shift + R` | 停止录制 |

### 录制示例

1. **启动录制**
   ```bash
   python run.py record
   # 显示绿色悬浮窗表示就绪
   ```

2. **按 Ctrl+R 开始录制**
   - 打开计算器
   - 点击按钮输入 5 + 3
   - 查看结果

3. **按 Ctrl+Shift+R 停止录制**
   - 自动保存到 `recordings/calculator_demo_YYYYMMDD_HHMMSS.json`

4. **回放任务**
   ```bash
   python run.py execute recordings/calculator_demo_xxx.json
   ```

### 混合录制

支持同时录制 **桌面操作** 和 **浏览器操作**：

1. 录制时启动浏览器
2. 浏览器内的点击、输入会被记录为 CSS 选择器
3. 桌面应用操作会记录为坐标或图像识别

---

## 🧠 第三种方式：自然语言

用自然语言描述任务，AI 自动分析并执行。

### 准备 API Key

1. 获取 Kimi Coding API Key:
   - 访问 [Kimi 开放平台](https://platform.kimi.com/)
   - 创建 API Key

2. 设置环境变量:
   ```bash
   # Windows
   set KIMI_CODING_API_KEY=your_api_key
   
   # Linux/macOS
   export KIMI_CODING_API_KEY=your_api_key
   ```

### 使用示例

```bash
# 淘宝购物
py -m src vision "帮我在淘宝上搜索蓝牙耳机，筛选销量最高的"

# 信息查询
py -m src vision "在百度上搜索今天的北京天气"

# 视频观看
py -m src vision "在B站搜索Python入门教程，打开第一个视频"

# 保存生成的任务
py -m src vision "在京东搜索手机" -o jd_search_task.json
```

### 工作原理

1. **截图** - 截取当前屏幕
2. **分析** - VLM 分析界面和目标
3. **决策** - AI 决定下一步操作
4. **执行** - 自动执行点击、输入等
5. **循环** - 重复直到任务完成

---

## 🎯 下一步

| 想做什么 | 查看文档 |
|----------|----------|
| 了解更多预置任务 | [预置任务参考](PREDEFINED_TASKS.md) |
| 学习浏览器自动化 | [浏览器自动化指南](BROWSER_AUTOMATION.md) |
| 使用 Python API | [API 文档](API.md) |
| 自定义任务 | [开发者指南](DEVELOPER_GUIDE.md) |
| 解决问题 | [FAQ](FAQ.md) |

---

## ⚡ 快速命令卡

```bash
# 预置任务
python run.py run --list                              # 列出任务
python run.py run calculator a=5 b=3                  # 计算器
python run.py run taobao_search kw=手机               # 淘宝搜索

# 录制
python run.py record                                  # 开始录制
# Ctrl+R: 开始  Ctrl+Shift+R: 停止
python run.py execute recordings/task.json            # 回放

# VLM 模式
py -m src vision "在淘宝上搜索手机"                    # 自然语言

# 测试
python run.py test                                    # 运行测试
```

---

**祝你使用愉快！遇到问题请查看 [FAQ](FAQ.md) 🎉**
