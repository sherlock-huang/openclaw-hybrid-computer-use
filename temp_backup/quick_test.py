#!/usr/bin/env python3
"""最简单的测试 - 直接复制到本地运行"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 50)
print("🚀 快速测试录制功能")
print("=" * 50)

try:
    print("\n1️⃣ 测试导入...")
    from core.models import RecordingEvent, RecordingSession
    print("   ✅ 模型导入成功")
    
    print("\n2️⃣ 创建事件...")
    event = RecordingEvent(
        action="click",
        timestamp=1.0,
        target="button_1",
        position=(100, 200)
    )
    print(f"   ✅ 事件: {event.action} @ {event.position}")
    
    print("\n3️⃣ 序列化...")
    data = event.to_dict()
    print(f"   ✅ JSON: {data}")
    
    print("\n4️⃣ 创建会话...")
    from datetime import datetime
    session = RecordingSession(
        name="测试录制",
        start_time=datetime.now(),
        events=[event]
    )
    print(f"   ✅ 会话: {session.name}")
    
    print("\n5️⃣ 转换为任务序列...")
    sequence = session.to_task_sequence()
    print(f"   ✅ 任务数: {len(sequence.tasks)}")
    print(f"   ✅ 任务: {sequence.tasks[0].action} -> {sequence.tasks[0].target}")
    
    print("\n6️⃣ 保存到文件...")
    session.save_to_file("test_output.json")
    print("   ✅ 已保存到 test_output.json")
    
    print("\n7️⃣ 验证文件...")
    import json
    with open("test_output.json", "r") as f:
        saved = json.load(f)
    print(f"   ✅ 文件内容: {saved['name']}")
    print(f"   ✅ 任务列表: {len(saved['tasks'])} 个任务")
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 50)
    print("💡 解决方法:")
    print("   1. 确保在项目根目录运行")
    print("   2. 确保已安装依赖: pip install -r requirements.txt")
    print("   3. 检查 src/core/models.py 是否存在")
    print("=" * 50)
