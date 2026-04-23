# 微信语音助手 - 自然语言控制

> 用自然语言告诉 OpenClaw 发送微信消息

---

## 🚀 快速开始

### 安装依赖

```bash
py -m pip install pywin32 pyautogui
```

### 使用方法

#### 方式一：命令行直接输入

```bash
py wechat_voice_assistant.py "Send message to Zhang San saying good evening"
py wechat_voice_assistant.py "Tell Li Si about tomorrow's meeting"
py wechat_voice_assistant.py "Send received to work group"
```

#### 方式二：交互模式

```bash
py wechat_voice_assistant.py
```

然后直接输入自然语言指令：
```
📝 你想说什么: 给张三发消息说晚上好
🤔 解析中...

✅ 解析成功!
   联系人: 张三
   消息: 晚上好
   置信度: 90%

🚀 确认发送? (y/n): y

📤 正在发送...
✅ 消息已发送给 张三!
```

---

## 📝 支持的自然语言格式

| 说法示例 | 联系人 | 消息内容 |
|----------|--------|----------|
| 给张三发消息说晚上好 | 张三 | 晚上好 |
| 告诉李四明天开会 | 李四 | 明天开会 |
| 给工作群发收到 | 工作群 | 收到 |
| 发个消息给王五，内容是项目完成了 | 王五 | 项目完成了 |
| 通知技术群上线发布了 | 技术群 | 上线发布了 |
| 跟小明说晚上一起吃饭 | 小明 | 晚上一起吃饭 |
| 给文件传输助手发测试消息 | 文件传输助手 | 测试消息 |
| 告诉老板会议改期了 | 老板 | 会议改期了 |

---

## 🔧 工作原理

### 自然语言处理流程

```
用户输入: "给张三发消息说晚上好"
        ↓
[自然语言处理器]
        ↓
解析结果: contact="张三", message="晚上好"
        ↓
[微信发送模块]
        ↓
执行发送
```

### 支持的匹配模式

1. **给 [联系人] 发消息说 [内容]**
2. **告诉 [联系人] [内容]**
3. **通知 [联系人] [内容]**
4. **给 [联系人] 发 [内容]**
5. **发个消息给 [联系人]，内容是 [内容]**
6. **跟 [联系人] 说 [内容]**

---

## 💡 使用建议

### 推荐用法

- 联系人名称尽量准确（和微信显示名称一致）
- 消息内容不要太长（建议不超过100字）
- 首次使用先用"文件传输助手"测试

### 常见问题

**Q: 解析失败怎么办？**  
A: 尝试使用标准格式：`给XXX发消息说XXX`

**Q: 发送失败怎么办？**  
A: 检查微信是否已登录、窗口是否被最小化

**Q: 支持群发吗？**  
A: 目前需要逐个发送，暂不支持真正的群发功能

---

## 🐍 Python API

```python
from src.vision.wechat_processor import parse_wechat_command
from src.utils.wechat_helper import send_wechat_message

# 解析自然语言
contact, message = parse_wechat_command("给张三发消息说晚上好")

# 发送消息
send_wechat_message(contact, message)
```

---

## 🎯 完整示例

### 批量发送

```bash
py 微信语音助手.py "给张三发消息说项目完成了"
py 微信语音助手.py "给李四发消息说可以上线了"
py 微信语音助手.py "给老板发消息说报告已提交"
```

### 结合其他功能

```bash
# 先用 VLM 搜索信息
py -m src vision "在百度上搜索北京天气"

# 然后发给朋友
py 微信语音助手.py "给张三发消息说北京今天晴天"
```

---

开始用自然语言控制你的微信吧！🎉
