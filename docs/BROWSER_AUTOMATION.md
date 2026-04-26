# 浏览器自动化指南

> Playwright 集成，支持持久登录、多标签页、智能元素定位

---

## 📋 目录

1. [快速开始](#-快速开始)
2. [CLI 命令](#-cli-命令)
3. [Python API](#-python-api)
4. [元素定位策略](#-元素定位策略)
5. [持久化登录](#-持久化登录)
6. [高级功能](#-高级功能)

---

## 🚀 快速开始

### 启动浏览器

```bash
# 启动 Chromium（默认）
python run.py browser launch

# 启动 Firefox
python run.py browser launch --type firefox

# 启动 WebKit
python run.py browser launch --type webkit
```

### 访问网页

```bash
python run.py browser goto https://www.taobao.com
```

### 基本操作示例

```bash
# 在淘宝上搜索商品
python run.py browser goto https://www.taobao.com
python run.py browser click '#q'                    # 点击搜索框
python run.py browser type '#q' '手机'              # 输入关键词
python run.py browser click '.btn-search'           # 点击搜索按钮
```

---

## 🛠️ CLI 命令

### 浏览器控制

```bash
# 启动浏览器
python run.py browser launch [--type chromium|firefox|webkit] [--headless]

# 访问 URL
python run.py browser goto <url>

# 点击元素
python run.py browser click <selector>

# 输入文字
python run.py browser type <selector> <text>

# 等待元素
python run.py browser wait <selector> [--timeout 10]

# 获取元素文本
python run.py browser text <selector>

# 执行 JavaScript
python run.py browser eval <script>

# 截图
python run.py browser screenshot [output.png]

# 滚动页面
python run.py browser scroll <pixels>

# 返回上一页
python run.py browser back

# 关闭浏览器
python run.py browser close
```

### 完整示例：淘宝搜索

```bash
# 一步完成
python run.py run taobao_search keyword=手机

# 或使用底层命令
python run.py browser launch
python run.py browser goto https://www.taobao.com
python run.py browser click '#q'
python run.py browser type '#q' '手机'
python run.py browser click '.btn-search'
python run.py browser screenshot taobao_result.png
python run.py browser close
```

---

## 🐍 Python API

### 基础用法

```python
from src.browser.controller import BrowserController

# 启动浏览器
with BrowserController(browser_type="chromium", headless=False) as browser:
    # 访问网页
    browser.goto("https://www.taobao.com")
    
    # 点击元素
    browser.click("#q")  # 搜索框
    
    # 输入文字
    browser.type("#q", "手机")
    
    # 点击搜索按钮
    browser.click(".btn-search")
    
    # 等待页面加载
    browser.wait_for_selector(".item", timeout=10)
    
    # 截图
    browser.screenshot("result.png")
```

### 高级用法

```python
from src.browser.controller import BrowserController
from src.browser.actions import BrowserActions

# 持久化登录（保存 cookies）
with BrowserController(
    browser_type="chromium",
    user_data_dir="browser_data"  # 保存用户数据
) as browser:
    
    actions = BrowserActions(browser.page)
    
    # 访问淘宝（已登录状态）
    browser.goto("https://www.taobao.com")
    
    # 获取所有商品标题
    items = browser.page.query_selector_all(".item .title")
    for item in items[:5]:
        title = item.inner_text()
        print(f"商品: {title}")
    
    # 执行复杂的 JavaScript
    result = browser.page.evaluate("""
        () => {
            return {
                url: window.location.href,
                title: document.title,
                items: Array.from(document.querySelectorAll('.item')).length
            }
        }
    """)
    print(f"页面信息: {result}")
```

---

## 🎯 元素定位策略

### CSS 选择器

```python
# ID 选择器
browser.click("#username")

# Class 选择器
browser.click(".btn-primary")

# 属性选择器
browser.click("[data-testid='submit']")

# 层级选择器
browser.click(".search-box input")

# 多重选择器（智能降级）
browser.click("#q, input[placeholder*='搜索'], .search-input")
```

### XPath（备用）

```python
# 当 CSS 选择器不够用时，可以使用 XPath
page.click("xpath=//button[contains(text(), '提交')]")
```

### 文本内容

```python
# 点击包含特定文字的按钮
page.click("text=登录")
page.click("text='立即购买'")
```

### 智能选择器配置

项目内置了常用网站的选择器配置：

```python
from src.core.selectors_config import get_selector

# 获取淘宝搜索框的多个备选选择器
selector = get_selector("taobao", "search_input")
# 返回: "#q, input[placeholder*='搜索'], .search-combobox-input"

browser.click(selector)  # 自动尝试所有备选
```

**支持的网站：**
- 淘宝 (taobao)
- 京东 (jd)
- 抖音 (douyin)
- B站 (bilibili)
- 百度 (baidu)
- 微博 (weibo)
- 知乎 (zhihu)
- GitHub (github)

---

## 💾 持久化登录

### 什么是持久化登录？

- 保存浏览器 cookies、localStorage、sessionStorage
- 下次启动时自动恢复登录状态
- 无需重复扫码或输入密码

### 使用方法

```python
from src.browser.controller import BrowserController

# 指定用户数据目录
with BrowserController(user_data_dir="browser_data") as browser:
    # 第一次：手动登录
    browser.goto("https://login.taobao.com")
    # ... 扫码或密码登录 ...
    
    # 关闭后，登录状态已保存

# 第二次：自动保持登录状态
with BrowserController(user_data_dir="browser_data") as browser:
    browser.goto("https://www.taobao.com")
    # 已登录状态，直接看到个人中心
```

### 多账号管理

```python
# 账号 A
with BrowserController(user_data_dir="browser_data/user_a") as browser:
    browser.goto("https://taobao.com")

# 账号 B
with BrowserController(user_data_dir="browser_data/user_b") as browser:
    browser.goto("https://taobao.com")
```

---

## 🚀 高级功能

### 多标签页管理

```python
with BrowserController() as browser:
    # 打开第一个标签页
    browser.goto("https://taobao.com")
    
    # 打开新标签页
    new_page = browser.context.new_page()
    new_page.goto("https://jd.com")
    
    # 在多个标签页间切换
    pages = browser.context.pages
    for page in pages:
        print(f"页面标题: {page.title()}")
```

### 无头模式

```python
# 不显示浏览器窗口（适合服务器/CI）
with BrowserController(headless=True) as browser:
    browser.goto("https://example.com")
    browser.screenshot("result.png")
```

### 等待策略

```python
# 等待元素出现
browser.wait_for_selector(".item", timeout=10)

# 等待元素可见
browser.wait_for_selector(".item", state="visible", timeout=10)

# 等待元素隐藏
browser.wait_for_selector(".loading", state="hidden", timeout=10)

# 等待网络空闲
browser.page.wait_for_load_state("networkidle")
```

### 表单处理

```python
# 清空并输入
browser.page.fill("#username", "myuser")  # 自动清空原有内容

# 选择下拉框
browser.page.select_option("#province", "北京")

# 勾选复选框
browser.page.check("#agreement")

# 取消勾选
browser.page.uncheck("#subscribe")
```

### 文件上传/下载

```python
# 上传文件
browser.page.set_input_files("#upload", "path/to/file.jpg")

# 下载文件
with browser.page.expect_download() as download_info:
    browser.click("#download-btn")
download = download_info.value
download.save_as("/path/to/save.zip")
```

### 拦截请求

```python
# 拦截图片请求以加速加载
def handle_route(route, request):
    if request.resource_type == "image":
        route.abort()
    else:
        route.continue_()

browser.page.route("**/*", handle_route)
browser.goto("https://example.com")  # 不会加载图片
```

---

## 🐛 故障排除

### 问题：元素找不到

```python
# 检查选择器是否正确
# 使用浏览器开发者工具 (F12) 验证

# 等待元素加载
browser.wait_for_selector(".item", timeout=10)

# 使用多重选择器
browser.click("#q, .search-input, input[name='q']")
```

### 问题：点击被拦截

```python
# 有些元素被其他元素覆盖，尝试强制点击
browser.page.click(".btn", force=True)

# 或者先滚动到视图中
browser.page.locator(".btn").scroll_into_view_if_needed()
browser.click(".btn")
```

### 问题：页面加载超时

```python
# 增加超时时间
browser.goto("https://example.com", timeout=60000)  # 60秒

# 或者等待特定状态
browser.page.wait_for_load_state("domcontentloaded")
```

---

## 📊 性能优化

### 1. 复用浏览器实例

```python
# 不好的做法：每次操作都启动新浏览器
for url in urls:
    with BrowserController() as browser:  # 慢！
        browser.goto(url)

# 好的做法：复用浏览器
with BrowserController() as browser:
    for url in urls:
        browser.goto(url)
```

### 2. 拦截不必要的资源

```python
# 拦截图片、CSS、字体等
browser.page.route("**/*.{png,jpg,jpeg,gif,css,woff2}", 
                   lambda route: route.abort())
```

### 3. 并行处理

```python
import asyncio

async def process_page(browser, url):
    page = await browser.context.new_page()
    await page.goto(url)
    # ... 处理 ...
    await page.close()

# 并行打开多个页面
await asyncio.gather(
    process_page(browser, "https://site1.com"),
    process_page(browser, "https://site2.com"),
    process_page(browser, "https://site3.com"),
)
```

---

**开始浏览器自动化之旅吧！🌐**
