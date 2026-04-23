#!/usr/bin/env python3
"""不依赖 pytest 的测试脚本"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_recording_event():
    """测试 RecordingEvent"""
    print("测试 1: RecordingEvent...")
    from core.models import RecordingEvent
    
    event = RecordingEvent(
        action="click",
        timestamp=1.5,
        target="elem_001",
        position=(100, 200),
        element_type="button"
    )
    
    assert event.action == "click", f"期望 click, 得到 {event.action}"
    assert event.timestamp == 1.5
    assert event.target == "elem_001"
    print("   ✅ 通过")
    return True

def test_recording_event_to_dict():
    """测试序列化"""
    print("测试 2: to_dict()...")
    from core.models import RecordingEvent
    
    event = RecordingEvent(
        action="type",
        timestamp=2.0,
        value="Hello"
    )
    
    data = event.to_dict()
    assert data["action"] == "type"
    assert data["value"] == "Hello"
    print("   ✅ 通过")
    return True

def test_recording_session():
    """测试 RecordingSession"""
    print("测试 3: RecordingSession...")
    from core.models import RecordingEvent, RecordingSession
    from datetime import datetime
    
    events = [
        RecordingEvent(action="click", timestamp=0.5),
        RecordingEvent(action="type", timestamp=1.0, value="test")
    ]
    
    session = RecordingSession(
        name="Test",
        start_time=datetime.now(),
        events=events
    )
    
    assert session.name == "Test"
    assert len(session.events) == 2
    print("   ✅ 通过")
    return True

def test_to_task_sequence():
    """测试转换为 TaskSequence"""
    print("测试 4: to_task_sequence()...")
    from core.models import RecordingEvent, RecordingSession
    from datetime import datetime
    
    events = [
        RecordingEvent(action="click", timestamp=0.5, target="button_1"),
        RecordingEvent(action="type", timestamp=1.0, value="hello")
    ]
    
    session = RecordingSession(
        name="Test",
        start_time=datetime.now(),
        events=events
    )
    
    sequence = session.to_task_sequence()
    
    assert sequence.name == "Test"
    assert len(sequence.tasks) == 2
    assert sequence.tasks[0].action == "click"
    assert sequence.tasks[0].target == "button_1"
    assert sequence.tasks[1].action == "type"
    assert sequence.tasks[1].value == "hello"
    print("   ✅ 通过")
    return True

def test_save_to_file():
    """测试保存文件"""
    print("测试 5: save_to_file()...")
    from core.models import RecordingEvent, RecordingSession
    from datetime import datetime
    import json
    
    session = RecordingSession(
        name="SaveTest",
        start_time=datetime.now(),
        events=[RecordingEvent(action="click", timestamp=0.5, target="btn")]
    )
    
    test_file = "test_output.json"
    session.save_to_file(test_file)
    
    # 验证文件
    assert os.path.exists(test_file), "文件未创建"
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    assert data["name"] == "SaveTest"
    assert len(data["tasks"]) == 1
    
    # 清理
    os.remove(test_file)
    print("   ✅ 通过")
    return True

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("🧪 运行测试 (无需 pytest)")
    print("=" * 50)
    print()
    
    tests = [
        test_recording_event,
        test_recording_event_to_dict,
        test_recording_session,
        test_to_task_sequence,
        test_save_to_file,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            failed += 1
    
    print()
    print("=" * 50)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 50)
    
    if failed == 0:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("💡 有测试失败，请检查代码")
        return 1

if __name__ == "__main__":
    exit(run_all_tests())
