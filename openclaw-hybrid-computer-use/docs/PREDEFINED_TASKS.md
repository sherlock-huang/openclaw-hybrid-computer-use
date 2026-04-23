# 预置任务参考手册

> 28个开箱即用的自动化任务

---

## 📋 目录

- [桌面应用任务](#-桌面应用任务-18个)
- [浏览器任务](#-浏览器任务-10个)
- [任务参数速查](#-任务参数速查)
- [自定义参数](#-自定义参数)

---

## 🖥️ 桌面应用任务 (18个)

### 计算器 `calculator`

打开 Windows 计算器并执行运算。

```bash
# 加法
python run.py run calculator a=5 b=3 op=+

# 减法
python run.py run calculator a=10 b=4 op=-

# 乘法
python run.py run calculator a=6 b=7 op=*

# 除法
python run.py run calculator a=20 b=4 op=/
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `a` | 数字 | 1 | 第一个操作数 |
| `b` | 数字 | 2 | 第二个操作数 |
| `op` | 字符串 | + | 运算符: +, -, *, / |

---

### 记事本 `notepad`

打开记事本并输入文字。

```bash
python run.py run notepad text="Hello World!"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | 字符串 | "Hello World" | 要输入的文字 |

---

### 打开微信 `open_wechat`

启动微信桌面客户端。

```bash
python run.py run open_wechat
```

**注意：** 需要微信已安装在系统中。

---

### 微信发送消息 `wechat_send`

在微信桌面版中搜索指定联系人/群聊并发送消息。

#### 方式一：标准命令

```bash
python run.py run wechat_send contact="张三" message="晚上好！"
```

#### 方式二：一键发送脚本（推荐）

```bash
py wechat_send.py "张三" "晚上好！"
py wechat_send.py "File Transfer" "测试消息"
```

#### 方式三：自然语言控制 ⭐智能模式

```bash
# 进入交互模式
py wechat_voice_assistant.py

# Or use natural language directly
py wechat_voice_assistant.py "Send message to Zhang San saying good evening"
py wechat_voice_assistant.py "Tell Li Si about tomorrow's meeting"
py wechat_voice_assistant.py "Send received to work group"
```

支持的自然语言：
- `"给XXX发消息说XXX"`
- `"告诉XXX XXX"`
- `"通知XXX XXX"`
- `"跟XXX说 XXX"`

在已登录的微信桌面版中，搜索指定好友/群聊并发送消息。

```bash
# 发送给好友
python run.py run wechat_send contact="张三" message="晚上好！"

# 发送到群聊
python run.py run wechat_send contact="工作群" message="收到，马上处理"

# 发送后等待回复（用于自动化流程）
python run.py run wechat_send contact="客服" message="查询订单状态"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `contact` | 字符串 | 必填 | 联系人或群聊名称（需完全匹配） |
| `message` | 字符串 | "Hello" | 要发送的消息内容 |

**前提条件：**
1. 微信桌面版已安装并登录
2. 微信窗口未被最小化（可在后台）
3. 联系人名称需准确
4. 安装依赖: `py -m pip install pywin32 pyautogui`

**工作原理：**
1. 检测并激活微信窗口
2. 点击搜索框，输入联系人名称
3. 按回车选择第一个匹配结果
4. 在聊天窗口输入消息并发送

**注意事项：**
- 微信窗口会被带到前台
- 发送后会等待2秒确保消息送达
- 如果联系人不在列表中，会尝试搜索
- 目前仅支持 Windows 系统

---

### 打开 QQ `open_qq`

启动 QQ 桌面客户端。

```bash
python run.py run open_qq
```

---

### 打开钉钉 `open_dingtalk`

启动钉钉桌面客户端。

```bash
python run.py run open_dingtalk
```

---

### 文件管理器 `explorer`

打开 Windows 文件资源管理器。

```bash
# 打开桌面
python run.py run explorer path=Desktop

# 打开文档文件夹
python run.py run explorer path=Documents

# 打开下载文件夹
python run.py run explorer path=Downloads

# 打开指定路径
python run.py run explorer path="C:\Users\YourName\Pictures"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | 字符串 | "Desktop" | 目标路径：Desktop/Documents/Downloads 或完整路径 |

---

### 窗口切换 `window_switch`

演示 Alt+Tab 窗口切换。

```bash
python run.py run window_switch
```

---

### 桌面截图 `desktop_screenshot`

截取桌面并显示检测到的元素。

```bash
python run.py run desktop_screenshot
```

---

### 复制粘贴测试 `text_copy_paste`

测试剪贴板操作。

```bash
python run.py run text_copy_paste
```

---

### 滚动测试 `scroll_test`

测试页面滚动功能。

```bash
python run.py run scroll_test
```

---

### 右键菜单 `right_click`

测试右键点击和菜单。

```bash
python run.py run right_click
```

---

### 多应用切换 `multi_app`

在多个应用间切换的演示。

```bash
python run.py run multi_app
```

---

## 🌐 浏览器任务 (10个)

### GitHub 登录 `github_login`

自动登录 GitHub。

```bash
python run.py run github_login user=your_username pass=your_password
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user` | 字符串 | "" | GitHub 用户名或邮箱 |
| `pass` | 字符串 | "" | GitHub 密码 |

**注意：** 如果启用了 2FA，需要手动输入验证码。

---

### 淘宝搜索 `taobao_search`

在淘宝上搜索商品。

```bash
python run.py run taobao_search kw=手机
python run.py run taobao_search kw=蓝牙耳机
python run.py run taobao_search kw="MacBook Pro"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "手机" | 搜索关键词 |

---

### 京东搜索 `jd_search`

在京东上搜索商品。

```bash
python run.py run jd_search kw=电脑
python run.py run jd_search kw=iPhone
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "手机" | 搜索关键词 |

---

### 百度搜索 `baidu_search`

在百度上搜索。

```bash
python run.py run baidu_search kw=天气预报
python run.py run baidu_search kw="Python 教程"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "OpenClaw" | 搜索关键词 |

---

### 抖音搜索 `douyin_search`

在抖音上搜索视频。

```bash
python run.py run douyin_search kw=美食
python run.py run douyin_search kw=搞笑视频
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "美食" | 搜索关键词 |

---

### B站搜索 `bilibili_search`

在哔哩哔哩上搜索视频。

```bash
python run.py run bilibili_search kw=Python
python run.py run bilibili_search kw="原神攻略"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "Python" | 搜索关键词 |

---

### 微博热搜 `weibo_hot`

查看微博热搜榜。

```bash
python run.py run weibo_hot
```

此任务无需参数，自动打开微博热搜页面。

---

### 知乎搜索 `zhihu_search`

在知乎上搜索。

```bash
python run.py run zhihu_search kw=人工智能
python run.py run zhihu_search kw="如何学习编程"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "Python" | 搜索关键词 |

---

### 天气查询 `weather_check`

查询城市天气。

```bash
python run.py run weather_check city=北京
python run.py run weather_check city=上海
python run.py run weather_check city=广州
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `city` | 字符串 | "北京" | 城市名称 |

---

### Chrome 搜索 `chrome_search`

打开 Chrome 并搜索。

```bash
python run.py run chrome_search kw=openai.com
python run.py run chrome_search kw=github.com
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `kw` | 字符串 | "openai.com" | 要访问的网址或搜索词 |

---

## 📝 任务参数速查

### 参数类型说明

| 类型 | 示例 | 说明 |
|------|------|------|
| 数字 | `a=5`, `b=3` | 整数或小数 |
| 字符串 | `text="Hello"`, `kw=手机` | 文字内容，带空格需用引号 |
| 运算符 | `op=+`, `op=-` | +, -, *, / |

### 通用参数规则

```bash
# 基础用法
python run.py run <task_name>

# 带参数
python run.py run <task_name> param1=value1 param2=value2

# 带空格的字符串
python run.py run notepad text="Hello World"

# 查看帮助
python run.py run --list
```

---

## 🔧 自定义参数

### 在 Python 中使用

```python
from claw_desktop import ComputerUseAgent

agent = ComputerUseAgent()

# 计算器
result = agent.execute_task("calculator", a=10, b=5, op="*")

# 淘宝搜索
result = agent.execute_task("taobao_search", kw="笔记本电脑")

# 检查执行结果
if result.success:
    print(f"✅ 任务成功！耗时: {result.duration:.2f}s")
else:
    print(f"❌ 任务失败: {result.error}")
```

### 动态参数

```python
# 从用户输入获取参数
keyword = input("请输入搜索关键词: ")
agent.execute_task("baidu_search", kw=keyword)
```

### 批量执行

```python
keywords = ["手机", "电脑", "耳机", "键盘"]

for kw in keywords:
    print(f"搜索: {kw}")
    result = agent.execute_task("taobao_search", kw=kw)
    time.sleep(2)  # 避免请求过快
```

---

## ⚠️ 注意事项

### 浏览器任务

1. **分辨率**: 建议使用 1920x1080 分辨率
2. **网络**: 确保网络连接正常
3. **登录**: 部分任务可能需要先手动登录一次
4. **网站更新**: 如果网站改版，可能需要更新选择器

### 桌面任务

1. **应用安装**: 确保目标应用已安装
2. **权限**: Windows 上可能需要管理员权限
3. **窗口状态**: 确保没有其他窗口遮挡目标应用

---

## 🆕 添加新任务

想要添加自己的预置任务？查看 [开发者指南](DEVELOPER_GUIDE.md)。

---

**开始自动化吧！🚀**
