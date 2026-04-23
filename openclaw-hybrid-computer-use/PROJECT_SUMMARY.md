# OpenClaw Computer-Use Agent - 项目完整总结

> 版本: v0.3.1 | 最后更新: 2026-04-11

---

## 📊 项目概况

**项目定位**: 开源桌面 + 浏览器自动化 Agent  
**核心目标**: 让 AI 能够控制计算机，执行桌面和浏览器任务  
**技术栈**: Python + PyAutoGUI + Playwright + YOLO + VLM

---

## 🎯 功能清单

### 1. 桌面自动化

| 功能 | 实现方式 | 状态 |
|------|----------|------|
| **鼠标控制** | PyAutoGUI | ✅ |
| **键盘控制** | PyAutoGUI | ✅ |
| **应用启动** | win32gui + subprocess | ✅ |
| **窗口管理** | win32gui | ✅ |
| **屏幕截图** | mss/PIL | ✅ |
| **元素检测** | YOLOv8n | ✅ |
| **OCR识别** | PaddleOCR | ✅ |

**实现细节**:
- `src/action/mouse.py` - 平滑移动、点击、滚动、拖拽
- `src/action/keyboard.py` - 文字输入、组合键
- `src/action/app_manager.py` - 启动计算器、记事本等
- `src/perception/` - 图像感知层

### 2. 浏览器自动化

| 功能 | 实现方式 | 状态 |
|------|----------|------|
| **浏览器控制** | Playwright | ✅ |
| **元素操作** | CSS Selector + XPath | ✅ |
| **持久登录** | user_data_dir | ✅ |
| **多标签页** | Playwright Context | ✅ |
| **页面导航** | goto/click/type | ✅ |

**实现细节**:
- `src/browser/controller.py` - 浏览器生命周期管理
- `src/browser/actions.py` - 浏览器操作封装
- 支持 Chromium/Firefox/WebKit
- 自动选择器降级（多重备选）

### 3. 任务系统

| 功能 | 实现方式 | 状态 |
|------|----------|------|
| **28个预置任务** | JSON + Python | ✅ |
| **任务录制** | pynput + 事件记录 | ✅ |
| **混合录制** | 桌面+浏览器自动切换 | ✅ |
| **任务回放** | 事件重放 | ✅ |
| **错误重试** | 指数退避 | ✅ |

**实现细节**:
- `src/core/tasks_predefined.py` - 预置任务定义
- `src/recording/hybrid_recorder.py` - 混合录制
- `src/core/executor_enhanced.py` - 增强版执行器

**预置任务列表**:
```
桌面任务(18): calculator, notepad, open_wechat, open_qq, 
              open_dingtalk, explorer, window_switch...
浏览器任务(10): github_login, taobao_search, jd_search, 
                baidu_search, douyin_search, bilibili_search...
```

### 4. VLM 智能模式

| 功能 | 实现方式 | 状态 |
|------|----------|------|
| **自然语言理解** | Kimi Coding API | ✅ |
| **屏幕分析** | 截图 + VLM | ✅ |
| **任务规划** | 多步决策 | ✅ |
| **自然语言转任务** | Prompt工程 | ✅ |

**实现细节**:
- `src/vision/llm_client.py` - VLM客户端
- `src/vision/task_planner.py` - 任务规划器
- `src/vision/wechat_processor.py` - 微信自然语言处理器
- 支持 Kimi Coding API (k2p5)

### 5. 微信自动发送（最新）

| 功能 | 实现方式 | 状态 |
|------|----------|------|
| **窗口检测** | win32gui | ✅ |
| **搜索联系人** | Ctrl+F + 剪贴板 | ✅ |
| **消息发送** | pyautogui + 剪贴板 | ✅ |
| **自然语言控制** | 正则匹配 | ✅ |

**实现细节**:
- `src/utils/wechat_helper.py` - 微信辅助类
- `wechat_send.py` - 直接发送
- `wechat_voice_assistant.py` - 自然语言控制

**支持的自然语言**:
- "给张三发消息说晚上好"
- "告诉李四明天开会"
- "给工作群发收到"

---

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│           User Interface            │
│  CLI (run.py) / Python API / VLM   │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│        Orchestration Layer          │
│      TaskExecutor / Planner         │
└─────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐
│Perception│  │ Action │  │Knowledge│
│  感知层  │  │ 行动层 │  │ 知识库  │
└────────┘  └────────┘  └────────┘
```

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **ComputerUseAgent** | `src/core/agent.py` | 主入口类 |
| **TaskExecutor** | `src/core/executor.py` | 任务执行引擎 |
| **ScreenCapture** | `src/perception/screen.py` | 屏幕截图 |
| **ElementDetector** | `src/perception/detector.py` | YOLO元素检测 |
| **MouseController** | `src/action/mouse.py` | 鼠标控制 |
| **KeyboardController** | `src/action/keyboard.py` | 键盘控制 |
| **BrowserController** | `src/browser/controller.py` | 浏览器控制 |
| **VLMClient** | `src/vision/llm_client.py` | VLM客户端 |

---

## 🔧 关键技术实现

### 1. 元素定位策略

**桌面元素**:
```python
# YOLO检测 + 坐标点击
elements = detector.detect(screenshot)
for elem in elements:
    if elem.element_type == target_type:
        mouse.click(*elem.center)
```

**浏览器元素**:
```python
# 多重选择器降级
selectors = "#q, input[placeholder*='搜索'], .search-input"
for selector in selectors.split(','):
    try:
        page.click(selector)
        break
    except:
        continue
```

### 2. 任务录制原理

```python
# 记录鼠标/键盘事件
@dataclass
class RecordedEvent:
    type: str          # mouse/keyboard
    action: str        # click/move/press
    position: tuple    # (x, y)
    timestamp: float

# 回放时重放事件
for event in recorded_events:
    if event.type == "mouse":
        pyautogui.click(*event.position)
    elif event.type == "keyboard":
        pyautogui.press(event.key)
```

### 3. VLM决策流程

```
1. 用户输入自然语言指令
2. 截取当前屏幕
3. VLM分析屏幕和目标
4. 返回结构化决策: {
     "action": "click/type/goto",
     "target": "selector/coordinates",
     "value": "text_for_typing"
   }
5. 执行操作
6. 循环直到任务完成
```

### 4. 微信发送原理

```python
# 1. 查找窗口
hwnd = win32gui.FindWindow(None, "微信")

# 2. 激活窗口
win32gui.SetForegroundWindow(hwnd)

# 3. 搜索联系人
pyautogui.keyDown('ctrl')
pyautogui.keyDown('f')
pyautogui.keyUp('f')
pyautogui.keyUp('ctrl')
pyperclip.copy("联系人")
pyautogui.hotkey('ctrl', 'v')
pyautogui.press('down')  # 选择结果
pyautogui.press('enter') # 确认

# 4. 发送消息
pyperclip.copy("消息内容")
pyautogui.hotkey('ctrl', 'v')
pyautogui.press('enter')
```

---

## 🚀 优化方向

### 1. 智能性优化

#### a. 元素定位智能化
| 现状 | 优化方向 | 实现方案 |
|------|----------|----------|
| 固定坐标/YOLO检测 | **自适应分辨率** | 根据屏幕分辨率动态计算坐标比例 |
| 单一选择器 | **智能选择器生成** | 使用多个属性生成健壮选择器 |
| 硬编码等待时间 | **智能等待** | 等待元素出现/可点击而非固定时间 |
| 无上下文理解 | **页面结构理解** | 使用DOM树分析元素关系 |

#### b. 微信发送智能化
| 现状 | 优化方向 | 实现方案 |
|------|----------|----------|
| 搜索选择 | **OCR识别列表** | 截图后OCR识别联系人列表 |
| 固定坐标 | **图像匹配定位** | 模板匹配找到输入框位置 |
| 无验证 | **发送结果验证** | 截图验证消息是否显示在聊天记录 |
| 单账号 | **多账号切换** | 维护多个微信窗口句柄 |

#### c. 任务规划智能化
| 现状 | 优化方向 | 实现方案 |
|------|----------|----------|
| 单步决策 | **多步规划** | VLM生成完整任务序列再执行 |
| 无记忆 | **上下文记忆** | 维护对话历史，支持多轮交互 |
| 固定提示词 | **动态提示词** | 根据页面类型加载不同提示词 |
| 无学习 | **任务学习** | 从成功案例学习最优执行路径 |

### 2. 稳定性优化

#### a. 错误处理增强
| 现状 | 优化方向 | 实现方案 |
|------|----------|----------|
| 简单重试 | **智能重试** | 根据错误类型选择重试策略 |
| 无回滚 | **失败回滚** | 失败时恢复到初始状态 |
| 无日志 | **详细日志** | 记录每个操作和截图 |
| 无监控 | **实时监控** | 检测页面卡住/加载失败 |

#### b. 容错机制
| 现状 | 优化方向 | 实现方案 |
|------|----------|----------|
| 单一选择器 | **多重备选** | 一个元素配置多个选择器 |
| 固定等待 | **动态等待** | 显式等待元素出现 |
| 无验证码处理 | **验证码识别** | 集成验证码识别服务 |
| 无弹窗处理 | **弹窗检测** | 检测并处理异常弹窗 |

#### c. 性能优化
| 现状 | 优化方向 | 实现方案 |
|------|----------|----------|
| 单线程 | **并发执行** | 并行处理多个任务 |
| 重复截图 | **缓存机制** | 屏幕无变化时复用结果 |
| 全屏检测 | **区域检测** | 只检测感兴趣区域 |
| 大模型调用 | **本地模型** | 部署本地轻量级VLM |

### 3. 功能扩展

#### a. 新功能
- [ ] Excel/Word 自动化
- [ ] 邮件客户端自动化
- [ ] 数据库操作
- [ ] API 调用集成
- [ ] 定时任务
- [ ] 任务调度器

#### b. 企业级特性
- [ ] 执行日志审计
- [ ] 权限控制
- [ ] 敏感信息脱敏
- [ ] 多用户支持
- [ ] 远程控制

---

## 📈 性能指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 截图耗时 | ~300ms | < 200ms |
| 元素检测 | ~1.5s | < 1s |
| 任务成功率 | ~70% | > 90% |
| VLM响应 | ~3s | < 2s |
| 内存占用 | ~800MB | < 500MB |

---

## 🎯 下一步重点

### 短期（1-2周）
1. 修复微信发送稳定性
2. 完善错误处理和日志
3. 增加更多预置任务

### 中期（1个月）
1. 实现智能元素定位
2. 添加任务学习功能
3. 支持更多桌面应用

### 长期（3个月）
1. 本地VLM部署
2. 企业级安全特性
3. 跨平台支持（Linux/macOS）

---

**总结**: 项目已具备桌面自动化、浏览器自动化、VLM智能控制三大核心能力，微信发送是首个社交应用自动化案例。下一步重点是提升稳定性和智能化水平。
