# 预置任务参考手册

> **65+** 个开箱即用的自动化任务

---

## 📋 目录

- [桌面应用任务](#-桌面应用任务)
- [浏览器任务](#-浏览器任务)
- [Office 自动化](#-office-自动化)
- [文件操作](#-文件操作)
- [智能定位](#-智能定位)
- [插件与扩展](#-插件与扩展)
- [其他实用任务](#-其他实用任务)
- [任务参数速查](#-任务参数速查)
- [自定义参数](#-自定义参数)
- [注意事项](#-注意事项)

---

## 🖥️ 桌面应用任务

| 任务 | 描述 | 参数 |
|------|------|------|
| `calculator` | 计算器（表达式模式） | `expression` |
| `calculator_add` | 计算器（两数相加） | `a`, `b` |
| `notepad_type` | 记事本输入文字 | `text` |
| `notepad_with_text` | 记事本输入并保存 | `text`, `filename` |
| `open_wechat` | 打开微信 | 无 |
| `open_qq` | 打开 QQ | 无 |
| `open_dingtalk` | 打开钉钉 | 无 |
| `open_outlook` | 打开 Outlook | 无 |
| `open_settings` | 打开系统设置 | 无 |
| `open_task_manager` | 打开任务管理器 | 无 |
| `open_cmd` | 打开命令行 | 无 |
| `explorer_navigate` | 文件资源管理器 | `path` |
| `window_switch` | 窗口切换演示 | 无 |
| `desktop_screenshot` | 桌面截图与检测 | 无 |
| `text_copy_paste` | 剪贴板复制粘贴测试 | 无 |
| `scroll_test` | 滚动测试 | 无 |
| `right_click` | 右键菜单测试 | 无 |
| `multi_app` | 多应用切换演示 | 无 |
| `desktop_cleanup` | 桌面清理 | 无 |
| `system_lock` | 锁定屏幕 | 无 |
| `shutdown_system` | 关机 | 无 |
| `restart_system` | 重启 | 无 |

---

### 计算器 `calculator`

使用表达式模式打开计算器并执行运算。

```bash
python run.py run calculator expression="1+2"
python run.py run calculator expression="sqrt(16)"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `expression` | 字符串 | "1+2" | 数学表达式 |

---

### 计算器（相加） `calculator_add`

打开计算器执行加法运算。

```bash
python run.py run calculator_add a=5 b=3
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `a` | 数字 | 1 | 第一个操作数 |
| `b` | 数字 | 2 | 第二个操作数 |

---

### 记事本 `notepad_type`

打开记事本并输入文字。

```bash
python run.py run notepad_type text="Hello World!"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | 字符串 | "Hello World" | 要输入的文字 |

---

### 记事本（保存） `notepad_with_text`

打开记事本输入文字并保存为文件。

```bash
python run.py run notepad_with_text text="会议记录" filename="note"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | 字符串 | "Hello World" | 要输入的文字 |
| `filename` | 字符串 | "note" | 保存的文件名（不含扩展名） |

---

### 打开微信 `open_wechat`

启动微信桌面客户端。

```bash
python run.py run open_wechat
```

**注意：** 需要微信已安装在系统中。

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

### 打开 Outlook `open_outlook`

启动 Outlook 桌面客户端。

```bash
python run.py run open_outlook
```

---

### 打开系统设置 `open_settings`

打开系统设置面板。

```bash
python run.py run open_settings
```

---

### 打开任务管理器 `open_task_manager`

打开任务管理器。

```bash
python run.py run open_task_manager
```

---

### 打开命令行 `open_cmd`

打开命令提示符（Windows）或终端。

```bash
python run.py run open_cmd
```

---

### 文件资源管理器 `explorer_navigate`

打开 Windows 文件资源管理器到指定路径。

```bash
# 打开桌面
python run.py run explorer_navigate path=Desktop

# 打开文档文件夹
python run.py run explorer_navigate path=Documents

# 打开指定路径
python run.py run explorer_navigate path="C:\\Users\\YourName\\Pictures"
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

### 桌面清理 `desktop_cleanup`

整理桌面文件到分类文件夹。

```bash
python run.py run desktop_cleanup
```

---

### 锁定屏幕 `system_lock`

锁定当前系统屏幕。

```bash
python run.py run system_lock
```

---

### 关机 `shutdown_system`

关闭计算机。

```bash
python run.py run shutdown_system
```

**警告：** 此任务会立即触发关机，请确保已保存所有工作。

---

### 重启 `restart_system`

重启计算机。

```bash
python run.py run restart_system
```

**警告：** 此任务会立即触发重启，请确保已保存所有工作。

---

## 🌐 浏览器任务

| 任务 | 描述 | 参数 |
|------|------|------|
| `github_login` | GitHub 登录 | `username`, `password` |
| `taobao_search` | 淘宝搜索 | `keyword` |
| `jd_search` | 京东搜索 | `keyword` |
| `baidu_search` | 百度搜索 | `keyword` |
| `douyin_search` | 抖音搜索 | `keyword` |
| `bilibili_search` | B站搜索 | `keyword` |
| `weibo_hot` | 微博热搜 | 无 |
| `weibo_hot_search` | 微博热搜（同 `weibo_hot`） | 无 |
| `zhihu_search` | 知乎搜索 | `keyword` |
| `weather_check` | 天气查询 | `city` |
| `chrome_search` | Chrome 搜索 | `url` |
| `browser_download` | 浏览器下载文件 | `url` |

---

### GitHub 登录 `github_login`

自动登录 GitHub。

```bash
python run.py run github_login username=your_username password=your_password
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `username` | 字符串 | "" | GitHub 用户名或邮箱 |
| `password` | 字符串 | "" | GitHub 密码 |

**注意：** 如果启用了 2FA，需要手动输入验证码。

---

### 淘宝搜索 `taobao_search`

在淘宝上搜索商品。

```bash
python run.py run taobao_search keyword=手机
python run.py run taobao_search keyword=蓝牙耳机
python run.py run taobao_search keyword="MacBook Pro"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | 字符串 | "手机" | 搜索关键词 |

---

### 京东搜索 `jd_search`

在京东上搜索商品。

```bash
python run.py run jd_search keyword=电脑
python run.py run jd_search keyword=iPhone
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | 字符串 | "笔记本电脑" | 搜索关键词 |

---

### 百度搜索 `baidu_search`

在百度上搜索。

```bash
python run.py run baidu_search keyword=天气预报
python run.py run baidu_search keyword="Python 教程"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | 字符串 | "OpenClaw AI" | 搜索关键词 |

---

### 抖音搜索 `douyin_search`

在抖音上搜索视频。

```bash
python run.py run douyin_search keyword=美食
python run.py run douyin_search keyword=搞笑视频
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | 字符串 | "科技" | 搜索关键词 |

---

### B站搜索 `bilibili_search`

在哔哩哔哩上搜索视频。

```bash
python run.py run bilibili_search keyword=Python
python run.py run bilibili_search keyword="原神攻略"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | 字符串 | "Python" | 搜索关键词 |

---

### 微博热搜 `weibo_hot`

查看微博热搜榜。

```bash
python run.py run weibo_hot
```

此任务无需参数，自动打开微博热搜页面。

> 别名：`weibo_hot_search`（效果相同）。

---

### 知乎搜索 `zhihu_search`

在知乎上搜索。

```bash
python run.py run zhihu_search keyword=人工智能
python run.py run zhihu_search keyword="如何学习编程"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | 字符串 | "人工智能" | 搜索关键词 |

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

打开 Chrome 并访问指定网址。

```bash
python run.py run chrome_search url=openclaw.ai
python run.py run chrome_search url=github.com
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | 字符串 | "openclaw.ai" | 要访问的网址或搜索词 |

---

### 浏览器下载 `browser_download`

使用浏览器下载指定 URL 的文件。

```bash
python run.py run browser_download url=https://example.com/file.zip
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | 字符串 | "" | 要下载的文件 URL |

---

## 📄 Office 自动化

| 任务 | 描述 | 参数 |
|------|------|------|
| `excel_report` | Excel 报表生成 | `filepath`, `sheet_name`, `headers`, `data_json`, `chart_title` |
| `excel_write_data` | Excel 写入数据 | `filepath`, `start_cell`, `data_json` |
| `excel_read_data` | Excel 读取数据 | `filepath`, `cell` |
| `word_document` | Word 创建文档 | `filepath`, `title`, `paragraphs_json` |
| `word_template_fill` | Word 模板填充 | `template_path`, `output_path`, `mapping_json` |
| `word_open_read` | Word 读取文档 | `filepath` |

---

### Excel 报表 `excel_report`

创建包含表头、数据和图表的 Excel 文件。

```bash
python run.py run excel_report filepath=report.xlsx sheet_name="Sheet1" headers="Name,Value" data_json="[[\"A\",1],[\"B\",2]]" chart_title="Chart"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filepath` | 字符串 | "report.xlsx" | 输出文件路径 |
| `sheet_name` | 字符串 | "Sheet1" | 工作表名称 |
| `headers` | 字符串 | "Name,Value" | 表头，逗号分隔 |
| `data_json` | 字符串 | `[["A",1],["B",2]]` | 数据，JSON 二维数组字符串 |
| `chart_title` | 字符串 | "Chart" | 图表标题 |

---

### Excel 写入数据 `excel_write_data`

打开或创建 Excel 文件并写入二维数据。

```bash
python run.py run excel_write_data filepath=data.xlsx start_cell=A1 data_json="[[1,2],[3,4]]"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filepath` | 字符串 | "data.xlsx" | Excel 文件路径 |
| `start_cell` | 字符串 | "A1" | 起始单元格 |
| `data_json` | 字符串 | `[[1,2],[3,4]]` | JSON 二维数组字符串 |

---

### Excel 读取数据 `excel_read_data`

读取 Excel 指定单元格的数据。

```bash
python run.py run excel_read_data filepath=data.xlsx cell=A1
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filepath` | 字符串 | "data.xlsx" | Excel 文件路径 |
| `cell` | 字符串 | "A1" | 单元格地址 |

---

### Word 创建文档 `word_document`

创建包含标题和段落的 Word 文档。

```bash
python run.py run word_document filepath=document.docx title="报告" paragraphs_json='["第一段","第二段"]'
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filepath` | 字符串 | "document.docx" | 输出文件路径 |
| `title` | 字符串 | "Document" | 文档标题 |
| `paragraphs_json` | 字符串 | `["Paragraph 1","Paragraph 2"]` | 段落内容，JSON 字符串列表 |

---

### Word 模板填充 `word_template_fill`

打开 Word 模板文件，批量替换占位符，保存为新文件。

```bash
python run.py run word_template_fill template_path=template.docx output_path=output.docx mapping_json='{"{{NAME}}":"张三","{{DATE}}":"2026-04-19"}'
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `template_path` | 字符串 | "template.docx" | 模板文件路径 |
| `output_path` | 字符串 | "output.docx" | 输出文件路径 |
| `mapping_json` | 字符串 | `{"{{NAME}}":"张三"...}` | 占位符映射，JSON 字典字符串 |

---

### Word 读取文档 `word_open_read`

打开 Word 文档并读取文本内容。

```bash
python run.py run word_open_read filepath=document.docx
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filepath` | 字符串 | "document.docx" | Word 文件路径 |

---

## 📁 文件操作

| 任务 | 描述 | 参数 |
|------|------|------|
| `file_copy` | 复制文件 | `src`, `dst` |
| `file_move` | 移动文件 | `src`, `dst` |
| `file_delete` | 删除文件 | `path` |
| `folder_create` | 创建文件夹 | `path` |
| `project_folder` | 创建项目结构 | `base_path` |
| `new_text_file` | 新建文本文件 | `filename`, `content` |
| `screenshot_save` | 截图保存 | `filepath` |
| `screenshot_desktop` | 截图保存到桌面 | `filename` |
| `screenshot_to_desktop` | 截图保存到桌面（同 `screenshot_desktop`） | `filename` |

---

### 复制文件 `file_copy`

复制文件到目标路径。

```bash
python run.py run file_copy src=a.txt dst=b.txt
python run.py run file_copy src=a.txt dst=backup/
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `src` | 字符串 | "" | 源文件路径 |
| `dst` | 字符串 | "" | 目标路径 |

---

### 移动文件 `file_move`

移动文件到目标路径。

```bash
python run.py run file_move src=a.txt dst=archive/
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `src` | 字符串 | "" | 源文件路径 |
| `dst` | 字符串 | "" | 目标路径 |

---

### 删除文件 `file_delete`

删除指定文件。

```bash
python run.py run file_delete path=old.txt
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | 字符串 | "" | 要删除的文件路径 |

---

### 创建文件夹 `folder_create`

创建指定文件夹。

```bash
python run.py run folder_create path=new_folder
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | 字符串 | "" | 文件夹路径 |

---

### 创建项目结构 `project_folder`

创建标准的项目文件夹结构。

```bash
python run.py run project_folder base_path=./myproject
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_path` | 字符串 | "./new_project" | 项目根目录路径 |

---

### 新建文本文件 `new_text_file`

创建文本文件并写入内容。

```bash
python run.py run new_text_file filename=note.txt content="Hello World"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filename` | 字符串 | "新建文本" | 文件名 |
| `content` | 字符串 | "" | 文件内容 |

---

### 截图保存 `screenshot_save`

截取屏幕并保存到指定路径。

```bash
python run.py run screenshot_save filepath=shot.png
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filepath` | 字符串 | "screenshot.png" | 保存路径 |

---

### 截图到桌面 `screenshot_desktop`

截取屏幕并保存到桌面。

```bash
python run.py run screenshot_desktop filename=my_screenshot
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filename` | 字符串 | "screenshot" | 文件名（不含扩展名） |

> 别名：`screenshot_to_desktop`（效果相同）。

---

## 🎯 智能定位

| 任务 | 描述 | 参数 |
|------|------|------|
| `locate_and_click_image` | 图像定位点击 | `template_path` |
| `locate_and_click_text` | 文本定位点击 | `text` |
| `wait_and_click_image` | 等待并点击图像 | `template_path`, `timeout` |
| `wait_and_click_text` | 等待并点击文本 | `text`, `timeout` |
| `click_below_text` | 点击文本下方元素 | `reference`, `target`, `direction` |

---

### 图像定位点击 `locate_and_click_image`

在屏幕上查找匹配图像并点击。

```bash
python run.py run locate_and_click_image template_path=btn.png
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `template_path` | 字符串 | "" | 模板图像路径 |

---

### 文本定位点击 `locate_and_click_text`

在屏幕上通过 OCR 查找指定文本并点击。

```bash
python run.py run locate_and_click_text text="确认"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | 字符串 | "" | 要点击的文本 |

---

### 等待并点击图像 `wait_and_click_image`

等待屏幕上出现匹配图像，然后点击。

```bash
python run.py run wait_and_click_image template_path=btn.png timeout=10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `template_path` | 字符串 | "" | 模板图像路径 |
| `timeout` | 字符串 | "10" | 最大等待时间（秒） |

---

### 等待并点击文本 `wait_and_click_text`

等待屏幕上出现指定文本，然后点击。

```bash
python run.py run wait_and_click_text text="提交" timeout=10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | 字符串 | "" | 要点击的文本 |
| `timeout` | 字符串 | "10" | 最大等待时间（秒） |

---

### 点击文本下方 `click_below_text`

查找参考文本，点击其下方的目标元素。

```bash
python run.py run click_below_text reference="标题" target="按钮" direction=below
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `reference` | 字符串 | "" | 参考文本 |
| `target` | 字符串 | "" | 目标文本 |
| `direction` | 字符串 | "below" | 相对方向：below / above / left / right |

---

## 🔌 插件与扩展

| 任务 | 描述 | 参数 |
|------|------|------|
| `plugin_api_get` | API GET 请求 | `url` |
| `plugin_api_post` | API POST 请求 | `url`, `json_body` |
| `plugin_db_query` | 数据库查询 | `db_path`, `sql` |
| `plugin_db_insert` | 数据库插入 | `db_path`, `sql` |
| `plugin_db_create_table` | 创建数据表 | `db_path`, `table_sql` |
| `plugin_list` | 列出所有插件 | 无 |

---

### API GET 请求 `plugin_api_get`

发送 HTTP GET 请求。

```bash
python run.py run plugin_api_get url=https://api.example.com/data
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | 字符串 | "https://httpbin.org/get" | 请求 URL |

---

### API POST 请求 `plugin_api_post`

发送 HTTP POST 请求。

```bash
python run.py run plugin_api_post url=https://api.example.com/data json_body='{"key":"value"}'
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | 字符串 | "https://httpbin.org/post" | 请求 URL |
| `json_body` | 字符串 | "{}" | JSON 请求体 |

---

### 数据库查询 `plugin_db_query`

执行 SQLite 查询语句。

```bash
python run.py run plugin_db_query db_path=data.db sql="SELECT * FROM users"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | 字符串 | "data.db" | 数据库文件路径 |
| `sql` | 字符串 | "SELECT 1" | SQL 查询语句 |

---

### 数据库插入 `plugin_db_insert`

执行 SQLite 插入/更新语句。

```bash
python run.py run plugin_db_insert db_path=data.db sql="INSERT INTO users VALUES (1, '张三')"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | 字符串 | "data.db" | 数据库文件路径 |
| `sql` | 字符串 | "" | SQL 插入/更新语句 |

---

### 创建数据表 `plugin_db_create_table`

创建 SQLite 数据表。

```bash
python run.py run plugin_db_create_table db_path=data.db table_sql="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | 字符串 | "data.db" | 数据库文件路径 |
| `table_sql` | 字符串 | "" | 建表 SQL 语句 |

---

### 列出插件 `plugin_list`

列出所有已安装的插件。

```bash
python run.py run plugin_list
```

---

## 🛠️ 其他实用任务

| 任务 | 描述 | 参数 |
|------|------|------|
| `shell_command` | 执行 Shell 命令 | `command` |
| `run_python_script` | 运行 Python 脚本 | `script_path` |
| `system_info` | 查看系统信息 | 无 |
| `copy_to_clipboard` | 复制到剪贴板 | `text` |
| `wechat_send` | 微信发消息 | `contact`, `message` |
| `local_vlm_analyze` | 本地 VLM 分析 | `instruction` |

---

### 执行 Shell 命令 `shell_command`

执行系统 Shell 命令。

```bash
python run.py run shell_command command="echo Hello"
python run.py run shell_command command="dir"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `command` | 字符串 | "echo Hello" | 要执行的命令 |

---

### 运行 Python 脚本 `run_python_script`

运行指定的 Python 脚本文件。

```bash
python run.py run run_python_script script_path=test.py
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `script_path` | 字符串 | "" | Python 脚本路径 |

---

### 查看系统信息 `system_info`

显示当前系统信息（CPU、内存、操作系统等）。

```bash
python run.py run system_info
```

---

### 复制到剪贴板 `copy_to_clipboard`

将指定文本复制到系统剪贴板。

```bash
python run.py run copy_to_clipboard text="Hello World"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | 字符串 | "Hello" | 要复制的文本 |

---

### 微信发消息 `wechat_send`

在已登录的微信桌面版中搜索指定联系人并发送消息。

```bash
# 标准命令
python run.py run wechat_send contact="张三" message="晚上好！"

# 发送到群聊
python run.py run wechat_send contact="工作群" message="收到，马上处理"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `contact` | 字符串 | "" | 联系人或群聊名称（需完全匹配） |
| `message` | 字符串 | "Hello" | 要发送的消息内容 |

**前提条件：**
1. 微信桌面版已安装并登录
2. 微信窗口未被最小化（可在后台）
3. 联系人名称需准确

**注意事项：**
- 微信窗口会被带到前台
- 发送后会等待 2 秒确保消息送达
- 目前仅支持 Windows 系统

---

### 本地 VLM 分析 `local_vlm_analyze`

使用本地视觉语言模型分析屏幕截图并返回操作建议。

```bash
python run.py run local_vlm_analyze instruction="分析当前屏幕"
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `instruction` | 字符串 | "分析当前屏幕" | 用户指令 |

**注意：** 需要已安装 transformers 和对应模型。

---

## 📝 任务参数速查

### 参数类型说明

| 类型 | 示例 | 说明 |
|------|------|------|
| 数字 | `a=5`, `b=3` | 整数或小数 |
| 字符串 | `text="Hello"`, `keyword=手机` | 文字内容，带空格需用引号 |
| JSON | `data_json="[[1,2]]"` | JSON 格式的字符串 |
| 路径 | `src=a.txt`, `path=folder/` | 文件或文件夹路径 |

### 通用参数规则

```bash
# 基础用法
python run.py run <task_name>

# 带参数
python run.py run <task_name> param1=value1 param2=value2

# 带空格的字符串
python run.py run notepad_type text="Hello World"

# 查看所有任务列表
python run.py run --list
```

---

## 🔧 自定义参数

### 在 Python 中使用

```python
from claw_desktop import ComputerUseAgent

agent = ComputerUseAgent()

# 计算器
result = agent.execute_task("calculator", expression="1+2")

# 淘宝搜索
result = agent.execute_task("taobao_search", keyword="笔记本电脑")

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
agent.execute_task("baidu_search", keyword=keyword)
```

### 批量执行

```python
keywords = ["手机", "电脑", "耳机", "键盘"]

for kw in keywords:
    print(f"搜索: {kw}")
    result = agent.execute_task("taobao_search", keyword=kw)
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

### Office 任务

1. **依赖**: 需要安装 `openpyxl` 和 `python-docx`
2. **路径**: 支持相对路径和绝对路径
3. **覆盖**: 如果文件已存在，可能会被覆盖

### 智能定位任务

1. **图像定位**: 模板图像应与屏幕显示比例一致
2. **OCR 识别**: 文本识别受字体、背景颜色影响
3. **超时**: 建议根据实际场景设置合理的超时时间

---

## 🆕 添加新任务

想要添加自己的预置任务？查看 [开发者指南](DEVELOPER_GUIDE.md)。

---

**开始自动化吧！🚀**
