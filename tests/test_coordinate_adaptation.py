"""Tests for coordinate adaptation across screen resolutions."""

import pytest
import numpy as np

from src.core.models import RecordingEvent, RecordingSession, RecordingMode
from datetime import datetime


class TestRecordingEventResolution:
    def test_event_stores_resolution_and_normalized(self):
        event = RecordingEvent(
            action="click",
            timestamp=0.5,
            position=(960, 540),
            screen_resolution=(1920, 1080),
            normalized_position=(0.5, 0.5),
        )
        assert event.screen_resolution == (1920, 1080)
        assert event.normalized_position == (0.5, 0.5)

    def test_event_to_dict_includes_resolution(self):
        event = RecordingEvent(
            action="click",
            timestamp=1.0,
            position=(100, 200),
            screen_resolution=(1920, 1080),
            normalized_position=(0.0521, 0.1852),
        )
        d = event.to_dict()
        assert d["screen_resolution"] == (1920, 1080)
        assert d["normalized_position"] == (0.0521, 0.1852)


class TestRecordingSessionToTaskSequence:
    def test_task_sequence_with_resolution_format(self):
        events = [
            RecordingEvent(
                action="click",
                timestamp=0.0,
                position=(960, 540),
                screen_resolution=(1920, 1080),
                normalized_position=(0.5, 0.5),
            ),
        ]
        session = RecordingSession(
            name="test",
            start_time=datetime.now(),
            events=events,
            recorded_resolution=(1920, 1080),
        )
        seq = session.to_task_sequence()
        assert seq.tasks[0].target == "960,540@1920x1080"

    def test_task_sequence_without_resolution_fallback(self):
        events = [
            RecordingEvent(
                action="click",
                timestamp=0.0,
                position=(100, 200),
            ),
        ]
        session = RecordingSession(
            name="test",
            start_time=datetime.now(),
            events=events,
            recorded_resolution=None,
        )
        seq = session.to_task_sequence()
        assert seq.tasks[0].target == "100,200"

    def test_task_sequence_element_id_when_no_position(self):
        events = [
            RecordingEvent(
                action="click",
                timestamp=0.0,
                target="btn_ok",
            ),
        ]
        session = RecordingSession(
            name="test",
            start_time=datetime.now(),
            events=events,
        )
        seq = session.to_task_sequence()
        assert seq.tasks[0].target == "btn_ok"


class TestExecutorCoordinateScaling:
    def test_resolve_target_with_resolution_scaling(self, monkeypatch):
        from src.core.executor import TaskExecutor

        executor = TaskExecutor()
        # Mock _get_screen_size to return 2560x1440 (upscale from 1920x1080)
        monkeypatch.setattr(executor, "_get_screen_size", lambda: (2560, 1440))

        fake_screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
        # 960,540 @ 1920x1080 should scale to 1280,720 @ 2560x1440
        x, y = executor._resolve_target("960,540@1920x1080", fake_screenshot)
        assert x == 1280
        assert y == 720

    def test_resolve_target_same_resolution_no_scaling(self, monkeypatch):
        from src.core.executor import TaskExecutor

        executor = TaskExecutor()
        monkeypatch.setattr(executor, "_get_screen_size", lambda: (1920, 1080))

        fake_screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
        x, y = executor._resolve_target("100,200@1920x1080", fake_screenshot)
        assert x == 100
        assert y == 200

    def test_resolve_target_backward_compatible_plain_coords(self, monkeypatch):
        from src.core.executor import TaskExecutor

        executor = TaskExecutor()
        monkeypatch.setattr(executor, "_get_screen_size", lambda: (2560, 1440))

        fake_screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
        x, y = executor._resolve_target("300,400", fake_screenshot)
        assert x == 300
        assert y == 400

    def test_resolve_target_downscale(self, monkeypatch):
        from src.core.executor import TaskExecutor

        executor = TaskExecutor()
        # Downscale from 2560x1440 to 1920x1080
        monkeypatch.setattr(executor, "_get_screen_size", lambda: (1920, 1080))

        fake_screenshot = np.zeros((1440, 2560, 3), dtype=np.uint8)
        # 1280,720 @ 2560x1440 should scale to 960,540 @ 1920x1080
        x, y = executor._resolve_target("1280,720@2560x1440", fake_screenshot)
        assert x == 960
        assert y == 540

    def test_resolve_target_invalid_raises(self, monkeypatch):
        from src.core.executor import TaskExecutor
        from src.utils.exceptions import NotFoundError

        executor = TaskExecutor()
        monkeypatch.setattr(executor, "_get_screen_size", lambda: (1920, 1080))

        fake_screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
        with pytest.raises(NotFoundError):
            executor._resolve_target("not_a_target", fake_screenshot)
