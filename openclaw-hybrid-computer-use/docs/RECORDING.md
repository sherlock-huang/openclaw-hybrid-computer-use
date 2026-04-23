# 任务录制指南

> 记录你的操作，生成可重放的自动化任务

---

## 📋 概述

任务录制功能让你可以：
- ✅ 记录鼠标点击、移动、拖拽
- ✅ 记录键盘输入
- ✅ 记录浏览器操作（自动识别 CSS 选择器）
- ✅ 生成 JSON 任务文件
- ✅ 随时回放录制的任务

---

## 🚀 快速开始

### 1. 启动录制

```bash
python run.py record
```

会显示一个绿色的悬浮窗，表示录制器已就绪：

```
┌──────────────────────┐
│  🎬 Claw Recorder    │
│  Ready               │
│  Ctrl+R: Start       │
│  Ctrl+Shift+R: Stop  │
└──────────────────────┘
```

### 2. 控制录制

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + R` | 开始录制 |
| `Ctrl + Shift + R` | 停止录制 |

### 3. 回放任务

```bash
# 录制文件自动保存在 recordings/ 目录
python run.py execute recordings/task_20260411_120000.json
```

---

## 📝 录制示例

### 示例 1：记事本操作

**录制步骤：**
1. 运行 `python run.py record`
2. 按 `Ctrl+R` 开始录制
3. 按 `Win+R`，输入 `notepad`，回车
4. 在记事本中输入 "Hello World"
5. 按 `Ctrl+Shift+R` 停止录制

**回放：**
```bash
python run.py execute recordings/notepad_demo_xxx.json
```

### 示例 2：浏览器操作

**录制步骤：**
1. 运行 `python run.py record`
2. 按 `Ctrl+R` 开始录制
3. 打开 Chrome
4. 访问 `https://www.baidu.com`
5. 点击搜索框
6. 输入 "天气"
7. 点击搜索按钮
8. 按 `Ctrl+Shift+R` 停止录制

**特点：**
- 浏览器内的点击自动记录为 CSS 选择器（如 `#kw`, `#su`）
- 即使页面布局变化，也能正确回放

---

## 🔧 高级录制

### 混合录制

支持同时录制 **桌面** 和 **浏览器** 操作：

```
录制流程示例：
1. 打开微信桌面应用（桌面操作）
2. 切换到 Chrome 浏览器（桌面操作）
3. 在淘宝上搜索商品（浏览器操作）
4. 复制商品标题（浏览器操作）
5. 粘贴到微信（桌面操作）
```

录制器会自动检测当前窗口类型，使用合适的记录方式。

### 录制浏览器多标签页

1. 打开 Chrome 浏览器
2. 开始录制
3. 在多个标签页之间切换
4. 录制器会自动记录每个标签页的 URL 和操作

### 带滚动的页面操作

对于需要滚动的页面：
1. 正常录制滚动操作
2. 录制器会记录滚动位置和方向
3. 回放时自动执行相同滚动

---

## 📄 录制文件格式

录制的任务保存为 JSON 文件：

```json
{
  "name": "task_20260411_120000",
  "description": "Recorded task",
  "created_at": "2026-04-11T12:00:00",
  "tasks": [
    {
      "action": "launch",
      "target": "notepad",
      "delay": 1.0
    },
    {
      "action": "click",
      "target": "100,200",
      "delay": 0.5
    },
    {
      "action": "type",
      "value": "Hello World",
      "delay": 0.5
    }
  ]
}
```

### 浏览器任务示例

```json
{
  "name": "baidu_search",
  "tasks": [
    {
      "action": "browser_launch",
      "value": "chromium",
      "delay": 2.0
    },
    {
      "action": "browser_goto",
      "value": "https://www.baidu.com",
      "delay": 2.0
    },
    {
      "action": "browser_click",
      "target": "#kw",
      "delay": 0.5
    },
    {
      "action": "browser_type",
      "target": "#kw",
      "value": "天气",
      "delay": 0.5
    },
    {
      "action": "browser_click",
      "target": "#su",
      "delay": 2.0
    }
  ]
}
```

---

## 🛠️ 手动编辑录制文件

可以用任何文本编辑器修改录制的任务：

### 修改延迟时间

```json
// 原来的 0.5 秒等待改为 2 秒
{
  "action": "browser_goto",
  "value": "https://example.com",
  "delay": 2.0  // 修改这里
}
```

### 修改输入内容

```json
// 修改搜索关键词
{
  "action": "browser_type",
  "target": "#kw",
  "value": "新的搜索词",  // 修改这里
  "delay": 0.5
}
```

### 添加选择器备选

```json
// 添加多个备选选择器
{
  "action": "browser_click",
  "target": "#q, input[placeholder*='搜索'], .search-input",
  "delay": 0.5
}
```

---

## ⚠️ 注意事项

### 1. 分辨率一致

- 录制和回放时屏幕分辨率应保持一致
- 不同分辨率可能导致坐标偏移

### 2. 应用状态

- 确保回放时应用处于初始状态
- 例如：录制时记事本是新打开的，回放前也应关闭再打开

### 3. 浏览器选择器

- CSS 选择器基于录制时的页面结构
- 网站改版后可能需要更新选择器

### 4. 时间敏感操作

- 网络加载、动画等时间因素可能影响回放
- 可适当增加 `delay` 值

---

## 🐛 故障排除

### 问题：录制没有反应

**检查：**
1. 是否有权限访问桌面
2. 是否以管理员身份运行（Windows）
3. 快捷键是否与其他软件冲突

### 问题：回放时找不到元素

**解决：**
1. 检查目标应用是否打开
2. 更新 JSON 文件中的选择器
3. 增加 `delay` 等待时间

### 问题：坐标点击不准确

**解决：**
1. 确保回放时分辨率与录制时一致
2. 尝试使用元素检测代替固定坐标
3. 添加多重选择器备选

---

## 📊 最佳实践

### 1. 命名规范

```bash
# 录制后重命名文件
mv recordings/task_20260411_120000.json recordings/baidu_weather_search.json
```

### 2. 模块化任务

将复杂任务拆分为多个小任务：

```bash
# 登录任务
recordings/login_taobao.json

# 搜索任务
recordings/search_iphone.json

# 组合执行
python run.py execute recordings/login_taobao.json
python run.py execute recordings/search_iphone.json
```

### 3. 添加注释

编辑 JSON 文件添加注释字段：

```json
{
  "name": "taobao_search",
  "description": "淘宝搜索商品，适用于日常购物场景",
  "author": "user",
  "version": "1.0"
}
```

---

## 🎯 示例任务库

```bash
recordings/
├── desktop/
│   ├── open_notepad_write.json
│   ├── calculator_add.json
│   └── wechat_send_msg.json
└── browser/
    ├── baidu_search.json
    ├── taobao_search.json
    ├── jd_search.json
    └── github_login.json
```

---

**开始录制你的第一个任务吧！🎬**
