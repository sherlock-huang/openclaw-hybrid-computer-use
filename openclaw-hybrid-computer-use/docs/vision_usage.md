# VLM 智能模式使用指南

## 简介

VLM (Vision Language Model) 模式让你可以用自然语言控制浏览器，
AI 会自动分析屏幕并执行操作。

## 使用前准备

### 1. 获取 API Key

**OpenAI (推荐):**
- 访问 https://platform.openai.com/api-keys
- 创建新的 API Key
- 设置环境变量:
  ```powershell
  $env:OPENAI_API_KEY = "sk-..."
  ```

**Anthropic (备选):**
- 访问 https://console.anthropic.com/
- 设置环境变量:
  ```powershell
  $env:ANTHROPIC_API_KEY = "sk-ant-..."
  ```

### 2. 安装依赖

```bash
pip install openai anthropic pillow
```

## 使用示例

### 命令行

```bash
# 在淘宝上搜索商品
py -m src vision "帮我在淘宝上搜索蓝牙耳机"

# 带更多要求
py -m src vision "在淘宝上搜索蓝牙耳机，按销量排序"

# 使用 Claude
py -m src vision "打开京东搜索手机" --provider anthropic

# 保存生成的任务
py -m src vision "登录GitHub创建新仓库" -o github_task.json
```

### Python API

```python
from src.vision import VisionTaskPlanner, VLMClient

# 创建 VLM 客户端
vlm = VLMClient(provider="openai")  # 或 "anthropic"

# 创建规划器
planner = VisionTaskPlanner(vlm_client=vlm, max_steps=15)

# 执行指令
sequence = planner.execute_instruction("在抖音上搜索美食视频")

# 保存结果
sequence.save_to_file("task.json")
```

## 注意事项

- **费用**: 每次操作都会调用 API，约 $0.01-0.02/次
- **延迟**: 每步需要等待 AI 分析和响应，约 2-5 秒
- **准确性**: VLM 可能误判界面元素，建议先在简单任务上测试
- **隐私**: 屏幕截图会发送给 AI 提供商，注意隐私安全

## 故障排除

**问题**: "未设置 OPENAI_API_KEY"
**解决**: 设置环境变量 `$env:OPENAI_API_KEY="your-key"`

**问题**: API 调用失败
**解决**: 检查网络连接，确认 API Key 有效，查看余额

**问题**: 任务执行失败
**解决**: 增加 `--max-steps`，或简化指令分步执行
