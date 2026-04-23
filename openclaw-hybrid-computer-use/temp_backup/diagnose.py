#!/usr/bin/env python3
"""诊断脚本"""
import sys
import os

print("=" * 60)
print("🔍 环境诊断")
print("=" * 60)

# 1. Python 版本
print(f"\n1. Python 版本: {sys.version}")

# 2. 当前目录
print(f"\n2. 当前目录: {os.getcwd()}")

# 3. 检查文件是否存在
print("\n3. 检查关键文件:")
files_to_check = [
    "src/__init__.py",
    "src/core/__init__.py",
    "src/core/models.py",
    "tests/test_recorder.py",
    "requirements.txt"
]

for f in files_to_check:
    exists = "✅" if os.path.exists(f) else "❌"
    print(f"   {exists} {f}")

# 4. 检查依赖
print("\n4. 检查依赖:")
try:
    import pytest
    print(f"   ✅ pytest {pytest.__version__}")
except ImportError:
    print("   ❌ pytest 未安装")

try:
    import numpy
    print(f"   ✅ numpy {numpy.__version__}")
except ImportError:
    print("   ❌ numpy 未安装")

try:
    from pynput import keyboard, mouse
    print("   ✅ pynput")
except ImportError:
    print("   ❌ pynput 未安装")

# 5. 尝试导入项目模块
print("\n5. 尝试导入项目模块:")
sys.path.insert(0, 'src')

try:
    from core.models import RecordingEvent
    print("   ✅ RecordingEvent 导入成功")
except Exception as e:
    print(f"   ❌ RecordingEvent 导入失败: {e}")

try:
    from utils.recording_overlay import RecordingOverlay
    print("   ✅ RecordingOverlay 导入成功")
except Exception as e:
    print(f"   ❌ RecordingOverlay 导入失败: {e}")

try:
    from utils.shortcut_listener import ShortcutListener
    print("   ✅ ShortcutListener 导入成功")
except Exception as e:
    print(f"   ❌ ShortcutListener 导入失败: {e}")

try:
    from core.recorder import TaskRecorder
    print("   ✅ TaskRecorder 导入成功")
except Exception as e:
    print(f"   ❌ TaskRecorder 导入失败: {e}")

# 6. 测试创建对象
print("\n6. 测试创建对象:")
try:
    from core.models import RecordingEvent, RecordingSession
    from datetime import datetime
    
    event = RecordingEvent(
        action="click",
        timestamp=1.0,
        target="elem_001",
        position=(100, 200)
    )
    print(f"   ✅ RecordingEvent 创建成功: {event.action}")
    
    data = event.to_dict()
    print(f"   ✅ to_dict() 成功: {data}")
    
    session = RecordingSession(
        name="test",
        start_time=datetime.now(),
        events=[event]
    )
    print(f"   ✅ RecordingSession 创建成功: {session.name}")
    
    sequence = session.to_task_sequence()
    print(f"   ✅ to_task_sequence() 成功: {len(sequence.tasks)} 个任务")
    
except Exception as e:
    print(f"   ❌ 创建对象失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
