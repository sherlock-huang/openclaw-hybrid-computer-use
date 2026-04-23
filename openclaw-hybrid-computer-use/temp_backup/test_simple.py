#!/usr/bin/env python3
"""简化测试"""
import sys
sys.path.insert(0, 'src')

# 测试 1: 导入模型
try:
    from core.models import RecordingEvent, RecordingSession
    print("✅ 模型导入成功")
except Exception as e:
    print(f"❌ 模型导入失败: {e}")
    sys.exit(1)

# 测试 2: 创建事件
try:
    event = RecordingEvent(
        action="click",
        timestamp=1.0,
        target="elem_001",
        position=(100, 200)
    )
    print(f"✅ 创建事件: {event.action} @ {event.position}")
except Exception as e:
    print(f"❌ 创建事件失败: {e}")
    sys.exit(1)

# 测试 3: 序列化
try:
    data = event.to_dict()
    print(f"✅ 序列化: {data}")
except Exception as e:
    print(f"❌ 序列化失败: {e}")
    sys.exit(1)

# 测试 4: 创建会话
try:
    from datetime import datetime
    session = RecordingSession(
        name="Test",
        start_time=datetime.now(),
        events=[event]
    )
    print(f"✅ 创建会话: {session.name}")
except Exception as e:
    print(f"❌ 创建会话失败: {e}")
    sys.exit(1)

# 测试 5: 转换为 TaskSequence
try:
    sequence = session.to_task_sequence()
    print(f"✅ 转换为任务序列: {len(sequence.tasks)} 个任务")
except Exception as e:
    print(f"❌ 转换失败: {e}")
    sys.exit(1)

print("\n🎉 所有基本测试通过！")
