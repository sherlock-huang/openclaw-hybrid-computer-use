# VLM 智能模式使用指南

> 使用自然语言控制浏览器，AI 自动分析屏幕并执行操作

---

## 📋 概述

VLM (Vision Language Model) 模式让你可以用**自然语言**描述任务，AI 会自动：
1. 分析当前屏幕截图
2. 理解界面元素
3. 规划操作步骤
4. 执行点击、输入等操作

**示例：**
```bash
py -m src vision "帮我在淘宝上搜索蓝牙耳机"
```

AI 会自动打开浏览器、访问淘宝、点击搜索框、输入关键词、点击搜索。

---

## 🚀 快速开始

### 步骤 1: 获取 API Key

**Kimi Coding API (推荐):**

1. 访问 [Kimi 开放平台](https://platform.kimi.com/)
2. 注册账号并创建 API Key
3. 复制你的 API Key

### 步骤 2: 设置环境变量

```bash
# Windows PowerShell
$env:KIMI_CODING_API_KEY = "your_api_key_here"

# Windows CMD
set KIMI_CODING_API_KEY=your_api_key_here

# Linux/macOS
export KIMI_CODING_API_KEY=your_api_key_here

# 永久设置（Windows 系统环境变量）
setx KIMI_CODING_API_KEY your_api_key_here
```

### 步骤 3: 验证配置

```bash
python -c "import os; print('API Key 已设置' if os.getenv('KIMI_CODING_API_KEY') else '未设置')"
```

### 步骤 4: 运行示例

```bash
py -m src vision "在百度上搜索今天天气"
```

---

## 📝 使用示例

### 命令行使用

```bash
# 基本搜索
py -m src vision "在淘宝上搜索手机"
py -m src vision "在京东搜索笔记本电脑"
py -m src vision "在B站搜索Python教程"

# 多步骤任务
py -m src vision "打开百度，搜索天气预报，查看北京的天气"

# 保存生成的任务
py -m src vision "在淘宝搜索耳机" -o headphone_search.json

# 设置最大步数
py -m src vision "在知乎搜索人工智能" --max-steps 20

# 使用特定浏览器
py -m src vision "在抖音搜索美食视频" --browser chromium
```

### Python API 使用

```python
from src.vision.llm_client import VLMClient
from src.vision.planner import VisionTaskPlanner

# 创建 VLM 客户端
vlm = VLMClient(
    provider="kimi-coding",  # 使用 Kimi Coding API
    api_key="your_api_key",  # 或从环境变量读取
    model="k2p5"             # 视觉语言模型
)

# 创建规划器
planner = VisionTaskPlanner(
    vlm_client=vlm,
    max_steps=15,
    headless=False  # 显示浏览器窗口
)

# 执行指令
sequence = planner.execute_instruction("在淘宝上搜索蓝牙耳机")

# 保存任务
sequence.save_to_file("taobao_headphone_search.json")

# 查看执行结果
print(f"任务名称: {sequence.name}")
print(f"步骤数: {len(sequence.tasks)}")
print(f"成功: {sequence.success}")
```

---

## 🎯 支持的网站

| 网站 | 示例指令 | 状态 |
|------|----------|------|
| **淘宝** | "在淘宝上搜索手机" | ✅ |
| **京东** | "在京东搜索电脑" | ✅ |
| **百度** | "在百度上搜索天气预报" | ✅ |
| **抖音** | "在抖音上搜索美食视频" | ✅ |
| **B站** | "在B站搜索Python教程" | ✅ |
| **微博** | "查看微博热搜" | ✅ |
| **知乎** | "在知乎搜索人工智能" | ✅ |
| **GitHub** | "在GitHub上搜索Python项目" | ✅ |

---

## 🔧 工作原理

### 执行流程

```
1. 接收自然语言指令
        ↓
2. 截取当前屏幕
        ↓
3. 发送给 VLM 分析
   ├─ 当前页面是什么？
   ├─ 目标元素在哪里？
   └─ 下一步应该做什么？
        ↓
4. VLM 返回操作决策
   ├─ 动作类型 (click/type/goto/...)
   ├─ 目标元素 (selector/coordinates)
   └─ 输入值 (text for typing)
        ↓
5. 执行操作
        ↓
6. 循环直到任务完成
```

### 决策格式

VLM 返回 JSON 格式的决策：

```json
{
  "action": "browser_click",
  "target": "#q",
  "value": null,
  "reasoning": "搜索框在页面右上角，ID为q"
}
```

---

## ⚠️ 注意事项

### 1. API 费用

- 每次操作调用一次 API
- 约 ¥0.01-0.05/次（取决于图像大小）
- 复杂任务可能需要 5-15 次调用

**节省费用建议：**
- 使用预置任务（免费）
- 录制常用任务并重复使用
- 简化指令，减少步骤

### 2. 响应延迟

- 每步需要 2-5 秒（API 调用 + 处理）
- 受网络状况影响
- 不适合实时性要求高的场景

### 3. 准确性

- VLM 可能误判界面元素
- 网站改版后可能失效
- 建议在重要操作前人工确认

### 4. 隐私安全

- 屏幕截图会发送给 AI 提供商
- 避免包含敏感信息的屏幕操作
- 本地任务录制更安全

---

## 🐛 故障排除

### 问题："未设置 KIMI_CODING_API_KEY"

**解决：**
```bash
# 设置环境变量
set KIMI_CODING_API_KEY=your_key

# 验证
python -c "import os; print(os.getenv('KIMI_CODING_API_KEY', '未设置'))"
```

### 问题：API 调用失败

**检查：**
1. API Key 是否正确
2. 网络连接是否正常
3. 账户余额是否充足
4. API 限流是否触发

### 问题：任务执行失败

**解决：**
```bash
# 增加最大步数
py -m src vision "复杂任务" --max-steps 30

# 简化指令，分步执行
py -m src vision "打开淘宝"
py -m src vision "在淘宝搜索手机"
```

### 问题：元素定位失败

**解决：**
1. 确保网站已完全加载
2. 尝试刷新页面
3. 手动检查选择器是否有效

---

## 💡 最佳实践

### 1. 指令清晰具体

```bash
# ✅ 好的指令
py -m src vision "在淘宝搜索框输入'手机'并点击搜索按钮"

# ❌ 避免模糊指令
py -m src vision "帮我买个手机"  # 太复杂，包含多个决策点
```

### 2. 分步执行复杂任务

```bash
# 而不是一次性执行
py -m src vision "打开京东，登录，搜索电脑，选择第一个，加入购物车"

# 分成多个步骤
py -m src vision "打开京东"
py -m src vision "在京东搜索电脑"
# 手动登录（如果需要验证码）
py -m src vision "选择第一个商品"
```

### 3. 保存成功任务

```bash
# 成功后保存，下次直接执行
py -m src vision "在淘宝搜索耳机" -o headphone_search.json

# 以后重复使用（免费）
python run.py execute headphone_search.json
```

### 4. 处理验证码

对于需要验证码的场景：
1. 使用预置任务先登录一次
2. 使用持久化浏览器保存登录状态
3. VLM 模式处理已登录后的操作

---

## 📊 性能优化

### 减少 API 调用次数

```python
# 限制最大步数
planner = VisionTaskPlanner(vlm_client=vlm, max_steps=10)

# 设置超时
planner = VisionTaskPlanner(vlm_client=vlm, timeout=30)
```

### 使用缓存

```python
# 相同的分析结果可以缓存
from src.vision.cache import AnalysisCache

cache = AnalysisCache()
result = cache.get_or_analyze(screenshot, instruction, vlm.analyze)
```

---

## 🔮 未来计划

| 功能 | 描述 | 预计版本 |
|------|------|----------|
| 本地模型 | 本地部署 VLM，无需 API | v0.5.0 |
| 任务学习 | 从成功执行中学习模式 | v0.4.0 |
| 多模态 | 支持语音指令输入 | v1.0.0 |
| 智能重试 | 失败后自动调整策略 | v0.4.0 |

---

**开始用自然语言控制你的计算机吧！🧠✨**
