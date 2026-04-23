# 微信发送消息功能测试指南

> 测试微信桌面版自动发送消息功能

---

## 📋 测试前准备

### 1. 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 |
| Python | 3.9+ |
| 微信 | 桌面版，已登录 |

### 2. 安装依赖

```bash
pip install pywin32
```

### 3. 准备微信

- 确保微信桌面版已**登录**
- 微信窗口可以是**最小化**状态，但不能退出
- 准备一个测试联系人（推荐用"文件传输助手"）

---

## 🚀 快速测试（推荐）

### 步骤 1: 前置检查

```bash
python test_wechat_quick.py
```

预期输出：
```
==================================================
微信发送消息功能测试
==================================================
✅ 操作系统: Windows
✅ win32gui 模块: 可用

检查微信窗口...
✅ 微信窗口已找到 (句柄: 123456)
   窗口标题: (0, 0, 1920, 1080)

✅ 前置条件检查通过

使用 --send 参数发送测试消息:
  python test_wechat_quick.py --send -c "文件传输助手" -m "你的消息"
```

### 步骤 2: 发送测试消息

```bash
# 发送给文件传输助手（推荐，安全）
python test_wechat_quick.py --send

# 发送给指定联系人
python test_wechat_quick.py --send -c "张三" -m "晚上好！"
```

### 步骤 3: 完整功能测试

```bash
python test_wechat_quick.py --full
```

这将依次测试：
1. ✅ 查找窗口
2. ✅ 激活窗口
3. ✅ 搜索联系人
4. ✅ 发送消息

---

## 🧪 详细测试

### 运行单元测试

```bash
# 快速功能检查（无需微信）
python tests/test_wechat_send.py --mode quick

# 自动测试（需要微信）
python tests/test_wechat_send.py --mode auto

# 交互式测试
python tests/test_wechat_send.py --mode interactive
```

### 使用预置任务测试

```bash
# 查看是否包含 wechat_send 任务
python run.py run --list | findstr wechat

# 发送消息
python run.py run wechat_send contact="文件传输助手" message="测试消息"
```

### Python API 测试

```python
from claw_desktop import ComputerUseAgent

agent = ComputerUseAgent()

# 发送消息
result = agent.execute_task(
    "wechat_send",
    contact="文件传输助手",
    message="Hello from OpenClaw!"
)

print(f"发送结果: {'成功' if result.success else '失败'}")
print(f"耗时: {result.duration:.2f}秒")
```

---

## 🔍 故障排除

### 问题 1: "未找到微信窗口"

**原因：**
- 微信未运行
- 微信已退出
- 微信在后台托盘但未打开窗口

**解决：**
```bash
# 1. 确保微信已登录
# 2. 点击微信图标打开主窗口
# 3. 可以最小化，但不能退出
```

### 问题 2: "搜索联系人失败"

**原因：**
- 联系人名称不正确
- 联系人不在最近聊天记录中

**解决：**
```bash
# 使用"文件传输助手"测试（最安全）
python test_wechat_quick.py --send -c "文件传输助手"

# 确保联系人名称完全匹配
```

### 问题 3: "消息发送失败"

**原因：**
- 微信窗口被其他窗口遮挡
- 微信处于锁定状态
- 分辨率不匹配

**解决：**
```bash
# 1. 确保微信窗口可见
# 2. 解锁微信（如果有锁屏）
# 3. 使用标准分辨率 1920x1080
```

### 问题 4: "win32gui 不可用"

**解决：**
```bash
pip install pywin32
```

---

## 📊 测试检查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Windows 系统 | ⬜ | 仅支持 Windows |
| Python 3.9+ | ⬜ | 版本要求 |
| pywin32 安装 | ⬜ | `pip install pywin32` |
| 微信已登录 | ⬜ | 打开微信窗口 |
| 测试联系人 | ⬜ | 推荐使用"文件传输助手" |
| 分辨率适配 | ⬜ | 1920x1080 最佳 |

---

## 🎯 测试场景

### 场景 1: 发送给好友

```bash
python test_wechat_quick.py --send -c "张三" -m "晚上一起吃饭？"
```

### 场景 2: 发送到群聊

```bash
python test_wechat_quick.py --send -c "工作群" -m "收到，马上处理"
```

### 场景 3: 批量发送

```python
from src.utils.wechat_helper import WeChatHelper

helper = WeChatHelper()

messages = [
    ("张三", "早上好！"),
    ("李四", "报告已提交"),
    ("工作群", "下午有会议"),
]

for contact, message in messages:
    print(f"发送给 {contact}...")
    helper.send_message_to_contact(contact, message)
    time.sleep(2)  # 避免发送过快
```

---

## ⚠️ 注意事项

1. **测试安全**
   - 先用"文件传输助手"测试
   - 确认消息内容再发送
   - 避免群发敏感信息

2. **微信限制**
   - 不要频繁发送消息
   - 避免被判定为机器人
   - 建议间隔 2 秒以上

3. **隐私保护**
   - 测试脚本不会保存聊天记录
   - 仅在本地执行
   - 不会上传任何数据

---

## 🐛 调试信息

如果需要调试，可以启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.utils.wechat_helper import WeChatHelper

helper = WeChatHelper()
helper.send_message_to_contact("测试", "消息")
```

---

**开始测试吧！** 🚀

```bash
python test_wechat_quick.py
```
