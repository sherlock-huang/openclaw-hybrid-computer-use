# VLM 集成设计文档 (v0.3.0)

**日期:** 2026-04-12  
**目标:** 让 Agent 能理解自然语言指令，通过视觉感知自动完成任务

---

## 1. 什么是 VLM？

**Vision Language Model** - 能同时处理图像和文本的多模态 AI

传统方式 vs VLM 方式：
- 传统：用户写 JSON 任务 → Agent 执行
- VLM：用户说"帮我在淘宝上搜蓝牙耳机" → AI 理解屏幕 → 自动执行

---

## 2. 核心架构

```
用户指令 → NaturalLanguageInterface → VisionTaskPlanner → ActionExecutor → 结果
                    ↓                        ↓
              解析意图                  VLM Client
                                         ↓
                                    截图 + 分析 + 决策
```

核心组件：
- **VLMClient** - 封装多模态 AI 调用
- **VisionTaskPlanner** - 任务规划与分解
- **ScreenAnalyzer** - 屏幕内容分析
- **VisionLoop** - 主循环：感知→决策→执行

---

## 3. 工作流程

```python
class VisionLoop:
    def run(self, instruction: str, max_steps: int = 20):
        for step in range(max_steps):
            # 1. 截图
            screenshot = screen.capture()
            
            # 2. VLM 决策
            decision = vlm.decide(instruction, screenshot, history)
            
            # 3. 检查完成
            if decision.action == "finish":
                return result
            
            # 4. 执行
            executor.execute(decision.action)
            
            # 5. 等待响应
            time.sleep(decision.delay)
```

---

## 4. VLM Prompt 示例

```
[System]
你是 OpenClaw，智能桌面自动化助手。

能力：
1. 分析屏幕截图，理解界面状态
2. 识别可交互元素（按钮、输入框等）
3. 规划并执行操作

操作规范：
- click(x, y) 或 click(selector)
- type(text)
- scroll(amount)
- wait(seconds)
- finish()

返回 JSON 格式：
{
    "observation": "当前屏幕状态",
    "thought": "思考过程",
    "action": "click/type/scroll/wait/finish",
    "target": "#search-input 或 500,300",
    "value": "输入值",
    "delay": 2.0
}
```

---

## 5. 使用示例

命令行：
```bash
py -m src vision "帮我在淘宝上搜索蓝牙耳机，按销量排序"
```

Python API：
```python
from src import OpenClawAgent
agent = OpenClawAgent(use_vision=True)
result = agent.execute_vision_task("在GitHub上创建新仓库")
```

---

## 6. 技术选型

| 模型 | 优点 | 缺点 | 成本/次 |
|------|------|------|---------|
| GPT-4V | 准确率高 | 需API | ~$0.40 |
| Claude 3 | 性价比高 | 需API | ~$0.18 |
| Qwen-VL | 开源本地 | 需GPU | 免费 |

推荐：开发用 GPT-4V，后期切开源模型

---

## 7. 实施计划

1. VLMClient 封装
2. VisionLoop 主循环
3. CLI 添加 vision 命令
4. 测试和优化 Prompt
