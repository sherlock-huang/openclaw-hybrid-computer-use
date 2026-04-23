"""任务学习引擎 v2 演示

展示三个核心增强功能：
1. 坐标适配器 (CoordinateAdapter)
2. 模式提取器 (PatternExtractor)
3. 任务推荐器 (TaskRecommender)

运行方式:
    py examples/task_learning_demo.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import fix_windows_encoding
fix_windows_encoding()

import numpy as np
from src.core.models import RecordingEvent, RecordingSession, RecordingMode
from src.core.task_learning_engine import TaskLearningEngine
from src.core.task_learner import TaskPattern


def demo_coordinate_adapter():
    """演示 1: 坐标适配器 — 将录制坐标适配到当前屏幕"""
    print("=" * 60)
    print("演示 1: 坐标适配器 (CoordinateAdapter)")
    print("=" * 60)

    engine = TaskLearningEngine()

    # 模拟一个录制会话：用户在 1920x1080 屏幕上点击了 (500, 300)
    session = RecordingSession(
        name="登录流程录制",
        start_time=None,  # type: ignore
        events=[
            RecordingEvent(action="click", timestamp=0, position=(500, 300)),
            RecordingEvent(action="type", timestamp=1, position=(500, 300), value="username"),
            RecordingEvent(action="click", timestamp=2, position=(500, 400)),
            RecordingEvent(action="type", timestamp=3, position=(500, 400), value="password"),
            RecordingEvent(action="click", timestamp=4, position=(500, 500)),
        ],
    )

    # 模拟当前屏幕截图 (1080p)
    fake_screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # 适配录制到当前环境
    sequence = engine.adapt_recording(session, fake_screenshot)

    print(f"录制名称: {sequence.name}")
    print(f"任务数量: {len(sequence.tasks)}")
    for i, task in enumerate(sequence.tasks):
        print(f"  [{i+1}] {task.action:6s} -> target={task.target}, value={task.value!r}")

    # 演示浏览器模式：CSS 选择器优先
    browser_session = RecordingSession(
        name="浏览器录制",
        start_time=None,  # type: ignore
        events=[
            RecordingEvent(
                action="browser_click",
                timestamp=0,
                position=(100, 200),
                css_selector="#login-btn",
                recording_mode=RecordingMode.BROWSER,
            ),
        ],
    )
    browser_sequence = engine.adapt_recording(browser_session, fake_screenshot)
    print(f"\n浏览器模式适配: action={browser_sequence.tasks[0].action}, "
          f"保留原始坐标 ({browser_sequence.tasks[0].target})")
    print()


def demo_pattern_extractor():
    """演示 2: 模式提取器 — 从多个录制中提取通用模式"""
    print("=" * 60)
    print("演示 2: 模式提取器 (PatternExtractor)")
    print("=" * 60)

    engine = TaskLearningEngine()

    # 模拟 3 个用户在不同网站上的购买流程录制
    recordings = [
        RecordingSession(
            name="淘宝购买",
            start_time=None,  # type: ignore
            events=[
                RecordingEvent(action="open", timestamp=0),
                RecordingEvent(action="search", timestamp=1),
                RecordingEvent(action="click", timestamp=2),
                RecordingEvent(action="add_cart", timestamp=3),
                RecordingEvent(action="checkout", timestamp=4),
            ],
        ),
        RecordingSession(
            name="京东购买",
            start_time=None,  # type: ignore
            events=[
                RecordingEvent(action="open", timestamp=0),
                RecordingEvent(action="search", timestamp=1),
                RecordingEvent(action="filter", timestamp=2),
                RecordingEvent(action="click", timestamp=3),
                RecordingEvent(action="add_cart", timestamp=4),
                RecordingEvent(action="checkout", timestamp=5),
            ],
        ),
        RecordingSession(
            name="拼多多购买",
            start_time=None,  # type: ignore
            events=[
                RecordingEvent(action="open", timestamp=0),
                RecordingEvent(action="search", timestamp=1),
                RecordingEvent(action="click", timestamp=2),
                RecordingEvent(action="add_cart", timestamp=3),
                RecordingEvent(action="checkout", timestamp=4),
            ],
        ),
    ]

    pattern = engine.extract_pattern(recordings)
    if pattern:
        print(f"提取到通用模式: {pattern['pattern_name']}")
        print(f"  通用步骤: {' -> '.join(pattern['actions'])}")
        print(f"  覆盖度: {pattern['coverage']:.0%}")
        print(f"  来源录制数: {pattern['source_count']}")
        print(f"  置信度: {pattern['confidence']:.2f}")
    else:
        print("未提取到通用模式")

    # 查找相似录制
    similar = engine.extractor.find_similar_recordings(recordings[0], recordings)
    print(f"\n与「{recordings[0].name}」相似的录制: {[r.name for r in similar]}")
    print()


def demo_task_recommender():
    """演示 3: 任务推荐器 — 基于上下文推荐任务"""
    print("=" * 60)
    print("演示 3: 任务推荐器 (TaskRecommender)")
    print("=" * 60)

    # 使用隔离的学习器，避免演示受历史数据干扰
    import tempfile
    from src.core.task_learner import TaskLearner
    isolated = TaskLearner.__new__(TaskLearner)
    isolated.patterns = {}
    isolated.LEARN_FILE = __import__('pathlib').Path(tempfile.mktemp(suffix=".json"))
    engine = TaskLearningEngine(learner=isolated)

    # 手动注入一些学习到的模式（模拟历史数据）
    engine.learner.patterns["wechat:send_msg"] = TaskPattern(
        task_type="wechat_send",
        target_signature="send_msg",
        actions=[
            {"action": "open_wechat"},
            {"action": "search_contact"},
            {"action": "click_chat"},
            {"action": "type_message"},
            {"action": "click_send"},
        ],
        success_count=18,
        fail_count=2,
    )
    engine.learner.patterns["browser:search_taobao"] = TaskPattern(
        task_type="browser_search",
        target_signature="search_taobao",
        actions=[
            {"action": "launch_browser"},
            {"action": "goto_url"},
            {"action": "type_query"},
            {"action": "press_enter"},
        ],
        success_count=15,
        fail_count=5,
    )
    engine.learner.patterns["desktop:open_notepad"] = TaskPattern(
        task_type="app_launch",
        target_signature="open_notepad",
        actions=[
            {"action": "press_win"},
            {"action": "type_notepad"},
            {"action": "press_enter"},
        ],
        success_count=20,
        fail_count=0,
    )

    # 场景 A: 当前窗口是微信
    print("场景 A: 当前窗口「微信 - 文件传输助手」")
    recs = engine.recommend(window_title="微信 - 文件传输助手")
    print("  基于窗口的推荐:")
    for r in recs["by_window"]:
        print(f"    - {r['task_type']}({r['target']}): 匹配度={r['score']}, 成功率={r['success_rate']}")

    # 场景 B: 用户最近的操作历史
    print("\n场景 B: 最近操作历史 [open_wechat, search_contact]")
    recs = engine.recommend(recent_actions=["open_wechat", "search_contact"])
    print("  基于历史的推荐:")
    for r in recs["by_history"]:
        print(f"    - {r['task_type']}({r['target']}): 匹配度={r['score']}")
        if r.get("next_actions"):
            print(f"      建议下一步: {' -> '.join(r['next_actions'])}")

    # 场景 C: 综合推荐
    print("\n场景 C: 综合上下文 (窗口=微信, 历史=[open_wechat])")
    recs = engine.recommend(
        window_title="微信",
        recent_actions=["open_wechat"],
    )
    print(f"  窗口推荐数: {len(recs['by_window'])}")
    print(f"  历史推荐数: {len(recs['by_history'])}")
    print()


def demo_learn_from_recording():
    """演示 4: 从录制中学习并应用"""
    print("=" * 60)
    print("演示 4: 从录制中学习 (learn_from_recording)")
    print("=" * 60)

    engine = TaskLearningEngine()

    session = RecordingSession(
        name="自动填写表单",
        start_time=None,  # type: ignore
        events=[
            RecordingEvent(action="click", timestamp=0, position=(100, 100)),
            RecordingEvent(action="type", timestamp=1, position=(100, 100), value="张三"),
            RecordingEvent(action="click", timestamp=2, position=(100, 200)),
            RecordingEvent(action="type", timestamp=3, position=(100, 200), value="13800138000"),
            RecordingEvent(action="click", timestamp=4, position=(200, 400)),
        ],
    )

    # 学习一次成功执行
    engine.learn_from_recording(session, success=True, duration=5.0)

    # 查看学习结果
    pattern = engine.learner.suggest("recorded", "自动填写表单")
    print(f"学习到模式: {pattern.task_type} -> {pattern.target_signature}")
    print(f"  成功率: {pattern.success_rate:.0%}")
    print(f"  平均耗时: {pattern.avg_duration:.1f}s")
    print(f"  最佳延迟: {pattern.optimal_delay:.1f}s")
    print()


if __name__ == "__main__":
    print("\n🧠 OpenClaw 任务学习引擎 v2 演示\n")
    demo_coordinate_adapter()
    demo_pattern_extractor()
    demo_task_recommender()
    demo_learn_from_recording()
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)