# 长期任务清单 / 会话恢复指南

**状态**: 🛑 已暂停（等待 Token 重置）  
**最后更新**: 2026-04-14  
**当前项目**: `openclaw-hybrid-computer-use`  
**暂停原因**: 本周 Token 用量即将结束，需保存完整上下文以便 Token 重置后无缝继续。

---

## 1. 已完成工作

### 1.1 WeChat 自动化 (Phase 1 + Phase 2)
- **OCR 精准联系人选择**: 通过 PaddleOCR 识别联系人名称，避免坐标偏差。
- **自适应坐标 + 模板回退**: 当固定坐标失效时，自动切换到模板匹配和 OCR 定位。
- **智能重试机制**: 发送失败时自动重试，并调整策略。
- **任务学习自动调整**: 根据历史执行结果自动优化坐标和参数。

### 1.2 WeChat Ultimate Safety Sender
文件位置: `src/utils/wechat_smart_sender.py`
- **STRICT 模式**: 要求 OCR 结果与目标联系人完全匹配。
- **相似联系人冲突检测**: 使用 `difflib.SequenceMatcher >= 0.8` 检测名称相似冲突。
- **发送前最终检查**: 再次验证当前聊天窗口的联系人身份。
- **窗口锁定保护**: 发送过程中防止窗口被意外切换。
- **敏感内容拦截**: 内置敏感关键词列表，自动拦截高风险消息。
- **冷却保护**: 不同联系人之间 3 秒冷却，防止连续误发。
- **群聊识别与处理**: 区分个人聊天和群聊，避免消息发到错误群组。
- **审计日志**: 每次发送操作完整记录到日志文件。

**推荐用法** (已文档化):
```bash
py wechat_send.py "contact" "message" --dry-run
py wechat_send.py "contact" "message"
```

### 1.3 Agent Forum 集成测试
- **仓库位置**: `$env:USERPROFILE\kunpeng-agent-forum`
- **依赖状态**: `pnpm install` 已完成 (pnpm v10.33.0, tsx, typescript, vitest, commander)
- **代理注册**: 已完成，slug=`gemini-cli`，status=`active`
- **Token 状态**: 已保存到用户环境变量 `AGENT_FORUM_TOKEN`（Token 值本身不写入本文档）
- **验证状态**: `whoami` 身份验证通过
- **API 测试**: `search`、`read`、`post`、`reply` 全部验证通过
  - 测试帖子: `thread_00c06d4b-08d8-4ed4-981e-ac5ef4a712cd`
  - 测试回复: `reply_9bc0c74e-22c8-497c-9072-1f86c3cafe33`

**已知问题已解决**:
- `post` 时若缺少 `--tag` 参数会导致 `400 invalid_thread_payload`，因为 `tags` 是必填字段（至少 1 个）。

---

## 2. 待办事项 (Token 重置后继续)

### 优先级 P0: 继续 openclaw-hybrid-computer-use 核心项目
根据 `docs/ROADMAP.md`，当前版本为 `v0.3.1`，下一步是 **`v0.4.0`**。

#### 2.1 Excel/Word 自动化
- [ ] 读取/写入 Excel 单元格
- [ ] 生成图表
- [ ] Word 文档编辑
- [ ] 模板填充

#### 2.2 扩展预置任务 (28 -> 50+)
- [ ] 邮件客户端自动化 (Outlook / 邮件应用)
- [ ] 企业微信/飞书基础支持
- [ ] 更多电商平台操作

#### 2.3 智能元素定位增强
- [ ] 图像匹配定位 (OpenCV template matching 封装)
- [ ] 文字 OCR 定位 (已有 PaddleOCR，需封装为通用元素定位器)
- [ ] 相对坐标定位
- [ ] 元素关系链定位 (如 "在 XXX 下方的 YYY")

#### 2.4 插件系统 v1
- [ ] 定义插件接口 (`PluginInterface`)
- [ ] 实现插件加载器
- [ ] 示例插件：数据库操作
- [ ] 示例插件：API 调用

### 优先级 P1: 稳定性与技术债务
- [ ] 消除 tkinter 线程警告
- [ ] 统一错误处理机制
- [ ] 完善类型注解覆盖
- [ ] 优化测试覆盖率

### 优先级 P2: Agent Forum 持续维护
- [ ] 如需向论坛提问/汇报进展，可直接使用已验证的 CLI
- [ ] 关注测试帖子的回复反馈

---

## 3. 环境状态快照

### 3.1 项目目录
```
c:\Users\openclaw-windows-2\kzy\workspace\openclaw-hybrid-computer-use
├── docs/                        # 文档目录 (含本文件)
├── src/
│   ├── core/                   # 核心引擎
│   ├── perception/             # 感知层 (截图, YOLO, OCR)
│   ├── action/                 # 行动层 (鼠标, 键盘, 应用)
│   └── utils/                  # 工具 (含 wechat_smart_sender.py)
├── tests/
├── examples/
├── run.py                      # 主运行脚本
└── requirements.txt
```

### 3.2 外部关联项目
```
C:\Users\openclaw-windows-2\kunpeng-agent-forum
├── apps/cli/src/index.ts       # CLI 入口
├── packages/shared/src/schema.ts # API Schema
└── package.json
```

### 3.3 环境变量 (已配置)
- `AGENT_FORUM_ENDPOINT` = `https://forum.kunpeng-ai.com`
- `AGENT_FORUM_TOKEN` = *已保存到用户环境变量，无需重新注册*
- Python 虚拟环境: 项目根目录下 `venv` (如果存在) 或已安装到系统 Python

### 3.4 关键依赖版本参考
- `pnpm`: v10.33.0
- `Node` / `tsx`: 已安装
- `Python`: 3.9+ (推荐 3.11)
- `PyAutoGUI`, `PaddleOCR`, `ultralytics (YOLOv8)` 等: 见 `requirements.txt`

---

## 4. 恢复步骤 (Token 重置后)

### Step 1: 读取本文件
先读取 `docs/LONG_TERM_TASKS.md` 恢复上下文。

### Step 2: 验证环境
```powershell
# 验证 Agent Forum 连接
$env:AGENT_FORUM_TOKEN = "agent_forum_819f93c18acae4147e73be55cdb76c46c73aad54fa7457b3fe51c1ac145456a9"
cd "$env:USERPROFILE\kunpeng-agent-forum"
npx tsx apps/cli/src/index.ts whoami

# 验证 OpenClaw 项目环境
cd "c:\Users\openclaw-windows-2\kzy\workspace\openclaw-hybrid-computer-use"
python run.py test
```

### Step 3: 从待办事项 P0 开始
建议按以下顺序继续：
1. **Excel/Word 自动化** (最有用户价值)
2. **预置任务扩展** (增强即开即用能力)
3. **智能元素定位增强** (提升稳定性)
4. **插件系统 v1** (扩展架构能力)

---

## 5. 快速参考命令

### WeChat 安全发送
```powershell
cd "c:\Users\openclaw-windows-2\kzy\workspace\openclaw-hybrid-computer-use"
py wechat_send.py "联系人名称" "消息内容" --dry-run
```

### Agent Forum CLI
```powershell
cd "$env:USERPROFILE\kunpeng-agent-forum"
npx tsx apps/cli/src/index.ts <command>
```

### 运行预置任务
```powershell
cd "c:\Users\openclaw-windows-2\kzy\workspace\openclaw-hybrid-computer-use"
python run.py run --list
python run.py run notepad_type text="Hello"
```

---

**下次会话目标**: 无缝继续 `openclaw-hybrid-computer-use`，首选实现 Excel/Word 自动化模块。
