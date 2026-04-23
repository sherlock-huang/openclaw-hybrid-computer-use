# 录制功能本地测试指南

## 快速开始

### 1. 环境检查

打开终端，在项目目录下执行：

```bash
# 检查 Python
python --version

# 检查 pip
pip --version

# 检查 pytest
python -m pytest --version
```

如果 pytest 未安装：
```bash
pip install pytest numpy pynput pillow opencv-python-headless
```

### 2. 诊断脚本

创建 `diagnose.py` 文件：

```python
#!/usr/bin/env python3
"""诊断脚本"""
import sys
import os

print("=" * 60)
print("🔍 环境诊断")
print("=" * 60)

# Python 版本
print(f"\n1. Python 版本: {sys.version}")

# 检查关键文件
print("\n2. 检查关键文件:")
files = ["src/__init__.py", "src/core/models.py", "tests/test_recorder.py"]
for f in files:
    exists = "✅" if os.path.exists(f) else "❌"
    print(f"   {exists} {f}")

# 检查依赖
print("\n3. 检查依赖:")
try:
    import pytest
    print(f"   ✅ pytest")
except ImportError:
    print("   ❌ pytest 未安装")

try:
    from pynput import keyboard, mouse
    print("   ✅ pynput")
except ImportError:
    print("   ❌ pynput 未安装")

# 尝试导入
print("\n4. 尝试导入项目模块:")
sys.path.insert(0, 'src')

try:
    from core.models import RecordingEvent
    print("   ✅ RecordingEvent 导入成功")
    
    # 测试创建对象
    event = RecordingEvent(action="click", timestamp=1.0, target="test")
    print(f"   ✅ 创建成功: {event.to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n诊断完成!")
```

运行：
```bash
python diagnose.py
```

---

## 测试步骤

### 测试 1：单元测试

```bash
# 运行测试
python -m pytest tests/test_recorder.py -v
```

**预期输出：**
```
tests/test_recorder.py::TestRecordingEvent::test_recording_event_creation PASSED
tests/test_recorder.py::TestRecordingEvent::test_recording_event_to_dict PASSED
tests/test_recorder.py::TestRecordingSession::test_session_creation PASSED
tests/test_recorder.py::TestRecordingSession::test_session_to_task_sequence PASSED
tests/test_recorder.py::TestTaskRecorder::test_recorder_lifecycle PASSED
tests/test_recorder.py::TestTaskRecorder::test_recorder_duplicate_start_raises PASSED

6 passed in 1.23s
```

**如果没有反应/卡住了：**
1. 检查 pytest 是否安装：`pip install pytest`
2. 检查是否有语法错误：`python -m py_compile tests/test_recorder.py`
3. 尝试直接运行测试：`python tests/test_recorder.py`

---

### 测试 2：直接运行测试代码

如果 pytest 不行，直接运行测试：

```python
# test_direct.py
import sys
sys.path.insert(0, 'src')

from core.models import RecordingEvent, RecordingSession
from datetime import datetime

print("测试 1: 创建 RecordingEvent")
event = RecordingEvent(
    action="click",
    timestamp=1.5,
    target="elem_001",
    position=(100, 200)
)
print(f"✅ 创建成功: {event.action} @ {event.position}")

print("\n测试 2: 序列化")
data = event.to_dict()
print(f"✅ to_dict(): {data}")

print("\n测试 3: 创建 RecordingSession")
session = RecordingSession(
    name="Test",
    start_time=datetime.now(),
    events=[event]
)
print(f"✅ 创建成功: {session.name}")

print("\n测试 4: 转换为 TaskSequence")
sequence = session.to_task_sequence()
print(f"✅ 转换成功: {len(sequence.tasks)} 个任务")
print(f"   任务 1: {sequence.tasks[0].action} -> {sequence.tasks[0].target}")

print("\n🎉 所有测试通过!")
```

运行：
```bash
python test_direct.py
```

---

### 测试 3：录制指示器

```python
# test_overlay.py
import sys
sys.path.insert(0, 'src')

from utils.recording_overlay import RecordingOverlay
import time

print("测试录制指示器...")
overlay = RecordingOverlay()

print("显示指示器（3秒）...")
overlay.show()
time.sleep(3)

print("隐藏指示器...")
overlay.hide()

print("✅ 测试完成!")
```

**注意：** 这会弹出一个红色窗口在屏幕右上角。

---

### 测试 4：完整录制流程

```python
# test_full_recording.py
import sys
sys.path.insert(0, 'src')

from core.recorder import TaskRecorder
import time

print("🎬 测试完整录制流程")
print("=" * 60)

recorder = TaskRecorder()

print("\n1. 开始录制...")
recorder.start_recording("测试会话")
print(f"   录制状态: {recorder.is_recording}")

print("\n2. 模拟操作...")
# 模拟点击
recorder._on_mouse_click(100, 200, None, True)
print("   ✅ 记录点击")

# 模拟输入
class MockKey:
    char = 'H'
recorder._on_key_press(MockKey())
print("   ✅ 记录输入 H")

class MockKey2:
    char = 'i'
recorder._on_key_press(MockKey2())
print("   ✅ 记录输入 i")

print("\n3. 停止录制...")
session = recorder.stop_recording()
print(f"   录制状态: {recorder.is_recording}")
print(f"   事件数量: {len(session.events)}")

print("\n4. 保存到文件...")
output_file = "test_recording.json"
session.save_to_file(output_file)
print(f"   ✅ 已保存到 {output_file}")

print("\n5. 读取并验证...")
import json
with open(output_file, 'r') as f:
    data = json.load(f)
print(f"   录制名称: {data['name']}")
print(f"   任务数量: {len(data['tasks'])}")
for i, task in enumerate(data['tasks']):
    print(f"   任务 {i+1}: {task}")

print("\n" + "=" * 60)
print("🎉 完整录制流程测试通过!")
```

运行：
```bash
python test_full_recording.py
```

---

## 常见问题

### 问题 1："No module named 'src'"

**解决：**
```bash
# 在项目根目录运行
python -m pytest tests/test_recorder.py

# 或者修改脚本开头
import sys
sys.path.insert(0, '.')
from src.core.models import RecordingEvent
```

### 问题 2："ImportError: cannot import name 'RecordingEvent'"

**解决：**
```bash
# 检查 models.py 是否存在
ls src/core/models.py

# 检查是否有语法错误
python -m py_compile src/core/models.py
```

### 问题 3：pytest 运行后没有输出

**解决：**
```bash
# 添加 verbose 模式
python -m pytest tests/test_recorder.py -v -s

# 或者捕获输出
python -m pytest tests/test_recorder.py -v --tb=short 2>&1 | tee test_output.txt
```

### 问题 4：pynput 导入失败

**解决：**
```bash
pip install pynput

# Windows 可能需要管理员权限
# 右键 PowerShell -> 以管理员身份运行
```

---

## 验证清单

- [ ] 诊断脚本运行成功
- [ ] 单元测试通过
- [ ] 直接测试脚本通过
- [ ] 录制指示器显示正常
- [ ] 完整录制流程成功
- [ ] JSON 文件正确生成
- [ ] 保存的文件可以重放

---

## 下一步

所有测试通过后，可以尝试：

```bash
# 1. 实际录制
python -m src record

# 2. 指定输出
python -m src record -o my_task.json

# 3. 重放
python -m src execute my_task.json
```
