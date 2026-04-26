# 常见问题解答 (FAQ)

> 使用 OpenClaw Computer-Use Agent 时的常见问题

---

## 📋 目录

- [安装问题](#-安装问题)
- [运行时问题](#-运行时问题)
- [浏览器自动化](#-浏览器自动化)
- [任务录制](#-任务录制)
- [VLM 模式](#-vlm-模式)
- [性能优化](#-性能优化)
- [其他问题](#-其他问题)

---

## 🔧 安装问题

### Q: 安装依赖时失败怎么办？

**A:** 尝试以下步骤：

```bash
# 1. 升级 pip
pip install --upgrade pip

# 2. 使用国内镜像（中国大陆）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 单独安装失败的包
pip install ultralytics
pip install paddleocr
pip install playwright

# 4. 安装 Playwright 浏览器
playwright install chromium
```

### Q: Windows 上提示"不是内部或外部命令"？

**A:** 
1. 确保 Python 已添加到系统 PATH
2. 使用 `py` 代替 `python`：
   ```bash
   py run.py test
   ```

### Q: 模型下载很慢或失败？

**A:**
```bash
# 手动下载 YOLOv8n
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# PaddleOCR 模型会自动下载，如果失败可以：
# 1. 设置代理
set HTTP_PROXY=http://127.0.0.1:7890
# 2. 或手动从官网下载模型放到 ~/.paddleocr/ 目录
```

---

## 🚀 运行时问题

### Q: 提示"RuntimeError: main thread is not in main loop"？

**A:** 这是 tkinter 的线程警告，不影响功能。如果看到界面问题：
1. 确保从主线程启动录制
2. 避免在多线程环境中使用 GUI 功能

### Q: Windows 中文显示乱码？

**A:** 已自动修复。如果仍有问题，手动设置：

```powershell
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# 或者在运行命令前
set PYTHONIOENCODING=utf-8
python run.py test
```

### Q: PyAutoGUI 安全机制导致任务中断？

**A:** PyAutoGUI 会在鼠标移动到屏幕四个角落时终止程序（安全特性）。

**解决方法：**
1. 执行任务时避免将鼠标移到角落
2. 如需禁用（不推荐）：
   ```python
   import pyautogui
   pyautogui.FAILSAFE = False
   ```

### Q: 元素检测找不到目标？

**A:**
1. **检查分辨率**：项目针对 1920x1080 优化
2. **等待时间**：增加 delay 参数
3. **使用坐标**：临时使用固定坐标
4. **更新模型**：考虑训练专门的 UI 检测模型

```python
# 增加等待时间
task = Task("click", target="button", delay=2.0)
```

---

## 🌐 浏览器自动化

### Q: 浏览器启动失败？

**A:**

```bash
# 1. 确保 Playwright 浏览器已安装
playwright install chromium

# 2. 检查权限（Windows）
# 以管理员身份运行 PowerShell

# 3. 清理用户数据目录
rmdir /s browser_data
# 然后重新运行
```

### Q: 元素点击失败？

**A:**

```python
# 方法 1: 使用多重选择器（推荐）
browser.click("#q, input[placeholder*='搜索'], .search-input")

# 方法 2: 等待元素加载
browser.wait_for_selector(".btn", timeout=10)
browser.click(".btn")

# 方法 3: 强制点击
browser.page.click(".btn", force=True)

# 方法 4: 先滚动到视图中
browser.page.locator(".btn").scroll_into_view_if_needed()
browser.click(".btn")
```

### Q: 如何保持登录状态？

**A:** 使用持久化上下文：

```python
from src.browser.controller import BrowserController

with BrowserController(user_data_dir="browser_data") as browser:
    browser.goto("https://taobao.com")
    # 第一次手动登录，之后自动保持
```

### Q: 网站改版后选择器失效？

**A:** 更新 `src/core/selectors_config.py`：

```python
SELECTOR_CONFIG = {
    "taobao": {
        # 添加新的备选选择器
        "search_input": "#q, .new-search-class, input[type='search']",
    }
}
```

---

## 🎬 任务录制

### Q: 录制快捷键无效？

**A:**
1. 检查是否有其他软件占用了 `Ctrl+R` 快捷键
2. 确保录制窗口在最前端
3. 尝试以管理员身份运行

### Q: 回放时坐标不准确？

**A:**
1. **分辨率一致**：确保回放时屏幕分辨率与录制时相同
2. **缩放设置**：检查 Windows 显示缩放是否为 100%
3. **使用选择器**：优先使用 CSS 选择器而非坐标

### Q: 浏览器操作录制的选择器不对？

**A:** 某些动态网站的选择器会变化。编辑录制文件：

```json
{
  "action": "browser_click",
  "target": "#dynamic-id-12345, .static-class, button[type='submit']"
}
```

---

## 🧠 VLM 模式

### Q: 提示"未设置 KIMI_CODING_API_KEY"？

**A:**

```bash
# Windows
set KIMI_CODING_API_KEY=your_api_key

# Linux/macOS
export KIMI_CODING_API_KEY=your_api_key

# 验证
python -c "import os; print(os.getenv('KIMI_CODING_API_KEY'))"
```

### Q: API 调用超时？

**A:** 某些图像分析可能需要较长时间：
1. 检查网络连接
2. 使用较小的截图区域
3. 增加超时设置（修改 `src/vision/llm_client.py` 中的 timeout）

### Q: VLM 分析结果不准确？

**A:**
1. **简化指令**：使用更清晰的描述
2. **分步执行**：将复杂任务拆分为多个简单任务
3. **检查截图**：确保屏幕内容清晰可见
4. **调整提示词**：参考 `src/vision/prompts.py` 优化

```bash
# 好的指令
py -m src vision "在淘宝搜索框输入'手机'并点击搜索按钮"

# 避免过于复杂的指令
py -m src vision "帮我买一部手机"  # 太复杂，可能失败
```

### Q: 如何降低 API 调用成本？

**A:**
1. 使用预置任务代替 VLM 模式（免费）
2. 录制常用任务并重复使用
3. 减少 max_steps 参数
4. 使用本地模型（v0.5.0+ 已支持 Qwen2-VL）

---

## ⚡ 性能优化

### Q: 任务执行太慢？

**A:**

```python
# 1. 减少延迟
task = Task("click", target="btn", delay=0.5)  # 默认 1.0

# 2. 使用无头浏览器
with BrowserController(headless=True) as browser:
    # 更快但看不到界面
    
# 3. 拦截不必要的资源
browser.page.route("**/*.{png,jpg,css}", 
                   lambda route: route.abort())
```

### Q: 内存占用过高？

**A:**
1. 及时关闭浏览器实例
2. 限制截图保存数量
3. 使用轻量级模型（YOLOv8n）

```python
# 使用上下文管理器确保资源释放
with BrowserController() as browser:
    # 使用浏览器
    pass  # 自动关闭
```

### Q: 如何提高元素检测速度？

**A:**
1. 使用降采样：`config.yolo_input_size = 320`
2. 降低置信度阈值：`config.yolo_conf_threshold = 0.3`
3. 缓存检测结果

---

## 🐛 其他问题

### Q: 如何调试任务执行？

**A:**

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看执行截图
result = agent.execute_task("calculator")
for i, screenshot in enumerate(result.screenshots):
    print(f"步骤 {i+1}: {screenshot.shape}")

# 保存可视化结果
from claw_desktop.utils.visualizer import ExecutionVisualizer
viz = ExecutionVisualizer()
viz.create_execution_report(result)
```

### Q: 如何贡献代码？

**A:** 查看 [开发者指南](DEVELOPER_GUIDE.md)。基本流程：
1. Fork 仓库
2. 创建特性分支
3. 提交更改
4. 创建 Pull Request

### Q: 在哪里获取帮助？

**A:**
1. 查看本文档和 [API 文档](API.md)
2. 运行 `python run.py test` 检查安装
3. 查看 `examples/` 目录的示例代码
4. 提交 GitHub Issue

---

## 📞 提交问题

如果以上方法无法解决你的问题：

1. **收集信息**：
   - 操作系统版本
   - Python 版本 (`python --version`)
   - 错误日志

2. **复现步骤**：
   - 最小复现代码
   - 预期行为
   - 实际行为

3. **提交 Issue**：
   - 标题：[Bug] 简短描述
   - 内容：环境 + 复现步骤 + 错误信息

---

**希望这份 FAQ 能解决你的问题！🎉**
