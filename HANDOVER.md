# OpenClaw 项目交接文档

> **版本**: v0.3.1  
> **更新日期**: 2026-04-19  
> **GitHub**: https://github.com/sherlock-huang/openclaw-hybrid-computer-use  
> **交接人**: Agent (WeChat 自动化专项) → 后续接手 Agent

---

## 一、已完成功能

### 1.1 微信桌面自动化核心链路

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 微信窗口管理 | `src/utils/wechat_helper.py` | ✅ 稳定 | 窗口查找（多 fallback）、激活、状态检测 |
| OCR 联系人选择 | `src/utils/wechat_contact_selector.py` | ✅ 稳定 | 精确匹配 + 模糊匹配 + 冲突检测 |
| 安全发送器 | `src/utils/wechat_smart_sender.py` | ✅ 逻辑完备 | 8 步验证状态机，含审计日志 |
| 坐标映射 | `src/utils/adaptive_coords.py` | ✅ 稳定 | 比例坐标 + 模板匹配 fallback |
| 屏幕截图 | `src/perception/screen.py` | ✅ 稳定 | mss 优先，PIL fallback |
| OCR 识别 | `src/perception/ocr.py` | ✅ 稳定 | PaddleOCR 延迟加载，BGR→RGB |
| 审计日志 | `src/utils/wechat_audit_logger.py` | ✅ 稳定 | 每次发送决策链记录 |
| 窗口锁定 | `src/utils/window_lock_guard.py` | ✅ 稳定 | 防止发送过程中窗口被切换 |

### 1.2 任务学习引擎 v2

| 组件 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 坐标适配器 | `src/core/task_learning_engine.py` | ✅ 完成 | 录制回放坐标自适应 |
| 模式提取器 | `src/core/task_learning_engine.py` | ✅ 完成 | 多录制 LCS 公共子序列提取 |
| 任务推荐器 | `src/core/task_learning_engine.py` | ✅ 完成 | 基于窗口标题/操作历史推荐 |
| 单元测试 | `tests/test_task_learning_engine.py` | ✅ 18/18 通过 | 全部通过 |

### 1.3 关键稳定性修复（已验证）

1. **搜索框坐标**: 从相对比例 `AnchorPoint(0.15, 0.08)` 改为**固定偏移 `(wx+130, wy+50)`**，避开 failsafe 角落
2. **中文输入**: `search_contact` / `send_message_to_contact` 改用**剪贴板 `Ctrl+A` / `Ctrl+V` 粘贴**，替代 `pyautogui.typewrite`（中文输入不可靠）
3. **截图稳定性**: 安装 `mss` 替代 `PIL.ImageGrab`，解决 RDP 环境下间歇性 `screen grab failed`
4. **Fail-safe 处理**: 自动化环境设置 `pyautogui.FAILSAFE = False`
5. **窗口激活容错**: `SetForegroundWindow` 失败不再阻断；`EnumWindows` 失败时 fallback 到类名 `WeChatMainWndForPC`；支持恢复隐藏窗口 (`SW_SHOW`)

---

## 二、未完成 / 待测试功能

### 2.1 🔴 端到端发送未完全跑通

**问题**: `test_03_search_contact`（搜索联系人并 OCR 点击下拉历史）**已单独通过**，但完整的 `send_message_to_contact` 在 **Step 2: Contact validation** 步骤失败。

**失败位置** (`wechat_helper.py` 约第 661 行):
```python
result = self.validator.validate_chat_contact(self.window_handle, contact)
if not result.success:
    # ← 在此处失败，OCR 识别到空字符串或无关内容
```

**可能根因**（按优先级排序）:

| # | 根因假设 | 验证方法 |
|---|---------|---------|
| 1 | 剪贴板粘贴后未正确触发搜索下拉，Enter 回车进入了"全局搜索"而非目标聊天 | 查看 `logs/` 目录下的调试图 (`wechat_validate_contact_fail_*.png`) |
| 2 | OCR 验证区域坐标偏差：标题栏验证区域 `(rect[0]+280, rect[1], ww-280, 80)` 未覆盖到实际联系人名称 | 手动截图对比，调整 `title_region` / `header_region` 参数 |
| 3 | 微信版本差异：不同版本的标题栏高度/布局不同 | 确认当前微信版本，检查是否有 "置顶"、"群公告" 等 UI 元素干扰 |
| 4 | 点击下拉历史后，微信未进入聊天窗口，而是进入了联系人资料页 | 在 `search_contact` 返回 True 后增加状态检测 (`_detect_state`) |

**建议修复路径**:
1. 运行 `test_wechat_send.py` 中的 `test_03_search_contact`，成功后保存当时的调试图
2. 检查调试图中 `title_region` 和 `header_region` 是否确实覆盖了聊天窗口顶部标题
3. 如果标题栏确实没有联系人名称，说明点击后未进入聊天窗口——检查 `search_contact` 中点击的坐标是否正确（下拉历史的 OCR 坐标是否偏移）
4. 考虑增加 **"点击后等待聊天窗口加载"** 的轮询逻辑（当前只有固定 `time.sleep(0.8)`）

### 2.2 🟡 待完善功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| `validate_message_sent` 假阴性 | P1 | 中文 OCR 对聊天内容识别存在偏差，建议增加消息特征提取（如时间戳匹配）|
| 群聊验证 | P2 | `validate_group_chat_features` 已实现但未经充分测试 |
| 微信多开支持 | P3 | 当前只取第一个匹配的窗口句柄 |
| 消息图片/文件发送 | P3 | 当前仅支持文本消息 |
| 模板目录初始化 | P2 | `templates/wechat/` 下缺少实际模板图片，导致 `get_point_safe` 的模板匹配 fallback 失效 |

---

## 三、已知问题

### 3.1 运行环境问题

| 问题 | 影响 |  workaround |
|------|------|-------------|
| RDP 断开时图形会话停止 | 截图全黑 | 保持 RDP 连接，或使用 console session |
| Windows 控制台 GBK 编码 | emoji/中文输出报错 | 已移除测试脚本中的 emoji，使用纯 ASCII 提示 |
| PaddleOCR 首次加载 5-10s | 首次 `recognize()` 慢 | 延迟加载设计，可在导入时预加载 |
| `SetForegroundWindow` 偶发返回 error 0 | 窗口未真正前台化 | 已改为 warning 不阻断，后续截图可能受影响 |

### 3.2 代码层面问题

| 问题 | 位置 | 建议修复 |
|------|------|---------|
| `validate_message_sent` 中 `self.logger` 未定义 | `wechat_helper.py:226` | `WeChatOCRValidator` 缺少 `self.logger = logging.getLogger(...)` |
| `AdaptiveCoordinateMapper` 比例坐标鲁棒性不足 | `adaptive_coords.py` | 微信搜索框已改用固定偏移，比例坐标方案仅作 fallback |
| `send_wechat_message` 顶层函数缺少日志 | `wechat_helper.py:731` | 建议改用 `logger.info` 替代 `print` |

### 3.3 测试层面问题

| 问题 | 说明 |
|------|------|
| `test_wechat_send.py::test_04_send_message_interactive` | 需要 `-s` 参数运行（交互式输入），CI 环境会失败 |
| 部分测试依赖真实微信窗口 | `test_03_search_contact` 等需要微信运行且有指定联系人 |
| 测试用例在 mock 下通过，真实环境可能不同 | mock 测试中 `validate_chat_contact` 被 patch 为 `success=True`，掩盖了真实 OCR 问题 |

---

## 四、健壮性改进点

### 4.1 高优先级

1. **验证区域坐标动态校准**
   - 当前 `title_region = (rect[0]+280, rect[1], ww-280, 80)` 假设左侧列表宽 280px
   - 建议: 在 `WeChatHelper.__init__` 中增加一次 "校准截图"，OCR 识别左侧边界（"微信" 图标右侧即列表边界）

2. **点击后进入聊天窗口的确认**
   - `search_contact` 点击下拉历史后，增加轮询：每 200ms 检测一次 `_detect_state() == "chat"`，最多 3 秒
   - 如果超时不进入 chat 状态，返回 False，让上层重试

3. **OCR 验证容错增强**
   - `validate_chat_contact` 当前只扫描 title_region + header_region
   - 建议增加整个右侧聊天区域的扫描，提高容错

### 4.2 中优先级

4. **剪贴板内容污染防护**
   - 当前使用 `pyperclip.copy(contact)` 会覆盖用户剪贴板
   - 建议: 发送前保存剪贴板内容，发送后恢复（`pyperclip` 支持但有限制）

5. **微信状态机更健壮**
   - 当前 `_detect_state()` 只有 3 种状态
   - 建议增加: `contact_profile`（联系人资料页）、`mini_program`（小程序）、`browser`（内置浏览器）

6. **发送超时机制**
   - 当前 `send_message_to_contact` 没有总超时
   - 建议增加 `total_timeout` 参数，避免无限重试

### 4.3 低优先级

7. **模板图片生成工具**
   - `templates/wechat/` 目录为空
   - 建议写一个脚本：自动截取搜索框/输入框/发送按钮并保存为模板

8. **多分辨率适配**
   - 当前坐标基于 1920x1080 + 微信默认尺寸测试
   - 建议在高 DPI/缩放环境下测试

---

## 五、系统架构

### 5.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户入口层                             │
│  send_wechat_message()    send_wechat_message_safe()        │
│       (快速)                    (安全，推荐)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    WeChatSmartSender                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ SafetyLevel │ │ SendResult  │ │  8步验证状态机       │   │
│  │ STRICT      │ │ step_reached│ │  activate → search   │   │
│  │ NORMAL      │ │ error       │ │  → validate → type   │   │
│  └─────────────┘ └─────────────┘ │  → pre_check → send  │   │
│                                  │  → validate_message  │   │
│  附加: 敏感词检查 / 冷却期 / 审计日志 / 双人确认            │   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                     WeChatHelper                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │find_window  │ │ activate    │ │ search_contact      │   │
│  │(多fallback) │ │ (容错前台化) │ │ (OCR下拉/Enter)     │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │_detect_state│ │_ensure_chat │ │send_message_to_contact│  │
│  │(chat/search)│ │_state       │ │ (3策略重试)          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│  依赖: ScreenCapture, TextRecognizer, WeChatContactSelector │
│        AdaptiveCoordinateMapper, WeChatOCRValidator         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   感知层 (Perception)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ ScreenCapture   │  │ TextRecognizer  │  │TemplateMatcher│
│  │ mss (优先)      │  │ PaddleOCR       │  │ (OpenCV)    │ │
│  │ PIL (fallback)  │  │ 延迟加载        │  │             │ │
│  │ BGR 输出        │  │ BGR→RGB        │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 微信发送流程状态机

```
[开始]
  │
  ▼
[激活微信窗口] ──失败──→ [保存调试图] → 返回 FAIL
  │
  ▼
[导航到聊天列表] (Esc ×2 + 点击左侧图标)
  │
  ▼
[搜索联系人] ──失败──→ [清除搜索] → 重试 (最多3次)
  │  ├─ OCR 下拉框精确点击 (首选)
  │  └─ Enter fallback (可能进入全局搜索，需检测修复)
  │
  ▼
[验证聊天对象] ←────── 当前阻塞点！
  │  (OCR 扫描 title_region + header_region)
  │  ──失败──→ [状态检测] → [修复] → 重试
  │
  ▼
[点击输入框] (自适应坐标 + 模板匹配 fallback)
  │
  ▼
[粘贴消息] (剪贴板 Ctrl+V，中文可靠)
  │
  ▼
[发送前最终确认] (再次 OCR 验证聊天对象)
  │
  ▼
[按 Enter 发送]
  │
  ▼
[验证消息已发送] (OCR 扫描聊天区域右下角)
  │  ──失败──→ [保存调试图] → 返回 FAIL
  │
  ▼
[更新冷却期记录] → 返回 SUCCESS
```

### 5.3 任务学习引擎架构

```
TaskLearningEngine (统一入口)
  ├── CoordinateAdapter      # 录制坐标 → 当前屏幕坐标
  │     ├── 策略1: css_selector (浏览器)
  │     ├── 策略2: 相对窗口缩放
  │     └── 策略3: 原始坐标直接复用
  ├── PatternExtractor       # 多录制 → 公共操作模式
  │     └── LCS 最长公共子序列 (DP 实现)
  └── TaskRecommender        # 上下文 → 推荐任务
        ├── by_window: 窗口标题关键词匹配 + 成功率加权
        └── by_history: 操作前缀匹配
```

---

## 六、工具框架

### 6.1 核心依赖

```
Python 3.12.10 (Windows)
├── pyautogui >= 0.9.54      # 鼠标/键盘控制
├── pywin32 >= 306           # Windows API (EnumWindows, SetForegroundWindow)
├── mss >= 9.0.0             # 高性能截图 (RDP 稳定)
├── paddlepaddle == 2.6.2    # OCR 推理引擎
├── paddleocr == 2.7.3       # OCR 文字识别
├── numpy == 1.26.4          # 数值计算 (注意: paddle 对 numpy 2.x 不兼容)
├── opencv-python >= 4.8.0   # 图像处理/模板匹配
├── pyperclip                # 剪贴板操作 (中文输入)
└── pytest >= 7.0.0          # 测试框架
```

### 6.2 包导入映射

```python
# 项目根目录通过 junction 符号链接实现双路径导入
# claw_desktop → src
import claw_desktop.utils.wechat_helper   # 等价于
import src.utils.wechat_helper             # 两者均可
```

### 6.3 测试运行

```bash
# 运行全部测试
cd openclaw-hybrid-computer-use
pytest

# 运行微信相关测试（需要真实微信窗口）
pytest tests/test_wechat_send.py -s          # -s 保留 stdin 用于交互式测试
pytest tests/test_wechat_helper_retry.py      # mock 测试，无需微信
pytest tests/test_task_learning_engine.py     # 18个单元测试，全部通过

# 运行特定测试
pytest tests/test_wechat_send.py::TestWeChatHelper::test_03_search_contact -s
```

### 6.4 pytest 配置

```ini
# pytest.ini
cache_dir = temp/.pytest_cache
```

---

## 七、目录结构说明

```
openclaw-hybrid-computer-use/
├── src/                          # 主代码目录
│   ├── action/                   # 桌面操作 (鼠标/键盘/App管理/Office)
│   │   ├── mouse.py
│   │   ├── keyboard.py
│   │   ├── app_manager.py
│   │   └── office_automation.py
│   ├── browser/                  # 浏览器自动化 (Playwright)
│   │   ├── controller.py
│   │   └── actions.py
│   ├── core/                     # 核心引擎
│   │   ├── agent.py              # 主 Agent 协调器
│   │   ├── executor.py           # 任务执行器
│   │   ├── models.py             # 数据模型 (Task, RecordingEvent 等)
│   │   ├── recorder.py           # 操作录制器
│   │   ├── task_learner.py       # 任务学习器 v1 (历史成功率统计)
│   │   ├── task_learning_engine.py   # 任务学习引擎 v2 (坐标适配/LCS/推荐)
│   │   ├── tasks_predefined.py   # 预定义任务库 (18+ 任务)
│   │   └── config.py             # 全局配置
│   ├── perception/               # 感知层
│   │   ├── screen.py             # 截图管理 (mss + PIL fallback) ⭐
│   │   ├── ocr.py                # OCR 文字识别 (PaddleOCR) ⭐
│   │   ├── detector.py           # YOLO 目标检测
│   │   ├── template_matcher.py   # OpenCV 模板匹配
│   │   └── smart_locator.py      # 智能元素定位
│   ├── utils/                    # 工具类
│   │   ├── wechat_helper.py          # 微信核心助手 ⭐⭐⭐
│   │   ├── wechat_smart_sender.py    # 微信安全发送器 ⭐⭐⭐
│   │   ├── wechat_contact_selector.py # OCR 联系人选择器 ⭐⭐
│   │   ├── wechat_audit_logger.py    # 审计日志
│   │   ├── window_lock_guard.py      # 窗口稳定性守卫
│   │   ├── adaptive_coords.py        # 自适应坐标映射 ⭐
│   │   └── ...
│   ├── vision/                   # 视觉语言模型 (VLM) 集成
│   │   ├── llm_client.py         # GPT-4V / Claude API 客户端
│   │   ├── local_vlm.py          # 本地 Qwen-VL 支持
│   │   ├── task_planner.py       # 自然语言 → 任务计划
│   │   └── wechat_processor.py   # 微信场景 VLM 处理
│   └── plugins/                  # 插件系统
│       ├── base.py
│       └── loader.py
│
├── tests/                        # 测试目录 (184+ 测试用例)
│   ├── test_wechat_*.py          # 微信相关测试 ⭐
│   ├── test_task_learning_engine.py  # 任务学习引擎 v2 测试 (18 passed)
│   └── test_*.py                 # 其他模块测试
│
├── templates/                    # 模板文件
│   └── wechat/                   # 微信 UI 模板 (当前为空！)
│       ├── wechat_search_box.png
│       ├── wechat_input_box.png
│       └── wechat_send_button.png
│
├── logs/                         # 调试日志和截图
│   ├── wechat_validate_contact_fail_*.png   # 联系人验证失败截图
│   └── wechat_retry_final_*.png             # 最终重试调试图
│
├── recordings/                   # 操作录制存储
├── examples/                     # 示例脚本和预定义任务
├── docs/                         # 项目文档
├── scripts/                      # 工具脚本
├── requirements.txt              # 依赖列表
├── run.py                        # 主入口
└── HANDOVER.md                   # ← 本文件
```

> ⭐ 标记为微信自动化相关核心文件，接手 Agent 应优先阅读。

---

## 八、快速上手指南 (For Next Agent)

### 8.1 环境准备

```bash
# 1. 安装依赖
py -m pip install -r requirements.txt
# 特别注意 numpy 版本兼容性:
py -m pip install numpy==1.26.4 paddlepaddle==2.6.2 paddleocr==2.7.3

# 2. 确认 mss 已安装 (RDP 截图必需)
py -m pip install mss>=9.0.0

# 3. 运行测试验证环境
pytest tests/test_task_learning_engine.py -v   # 应全部通过
```

### 8.2 微信发送最小测试

```python
from src.utils.wechat_helper import send_wechat_message

# 快速发送（不经过安全验证层）
success = send_wechat_message("文件传输助手", "测试消息")

# 安全发送（推荐）
from src.utils.wechat_smart_sender import send_wechat_message_safe
result = send_wechat_message_safe(
    "文件传输助手", "测试消息",
    safety_level="strict",
    dry_run=True,          # 先dry-run测试
    require_confirm=False  # 跳过交互确认
)
print(result)
```

### 8.3 调试微信发送问题

```python
from src.utils.wechat_helper import WeChatHelper

helper = WeChatHelper()
helper.activate_wechat()

# 1. 先单独测试搜索
ok = helper.search_contact("文件传输助手", use_ocr_selector=True)
print(f"搜索: {ok}")

# 2. 检查当前状态
state = helper._detect_state()
print(f"状态: {state}")

# 3. 验证聊天对象
result = helper.validator.validate_chat_contact(
    helper.window_handle, "文件传输助手"
)
print(f"验证: {result}")
# 如果失败，检查 logs/ 目录下的调试图
```

---

## 九、Git 提交历史

```
7a3b9ee feat(wechat): improve navigation robustness, fix screen/ocr init, clipboard paste, mss support
ff01698 docs: add stability optimization documentation
6723fa3 feat(stability): add multi-selector config, enhanced executor, and task builder
```

当前代码已全部推送至 `origin/main`。

---

## 十、联系方式 / 上下文

- **项目根目录**: `C:\Users\openclaw-windows-2\kzy\workspace\openclaw-hybrid-computer-use`
- **GitHub**: https://github.com/sherlock-huang/openclaw-hybrid-computer-use
- **运行环境**: Windows Server (RDP 远程桌面), Python 3.12
- **微信版本**: 桌面版 WeChat (Windows)
- **关键时间戳**: PaddleOCR 首次加载约 5-10 秒，模型缓存到 `~/.paddleocr/whl/`

---

*本交接文档旨在帮助后续 Agent 快速理解项目状态、定位问题和继续开发。如有疑问，优先查看 `src/utils/wechat_helper.py` 和 `src/utils/wechat_smart_sender.py` 中的详细注释。*
