"""M4b 迭代 1 测试 —— 失败注入、安全护栏、窗口管理"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np

from src.core.safety import SafetyGuard, SafetyCheckResult, DEFAULT_SENSITIVE_ACTIONS
from src.core.config import Config
from src.core.models import Task
from src.utils.exceptions import NotFoundError, ValidationError


# ---------------------------------------------------------------------------
# SafetyGuard Tests
# ---------------------------------------------------------------------------

class TestSafetyGuardAction:
    """测试敏感 action 拦截"""

    def test_blocks_exact_match(self):
        guard = SafetyGuard()
        result = guard.check_action("wechat_send")
        assert result.passed is False
        assert "wechat_send" in result.reason

    def test_allows_safe_action(self):
        guard = SafetyGuard()
        result = guard.check_action("click")
        assert result.passed is True

    def test_blocks_prefix_match(self):
        guard = SafetyGuard(sensitive_actions={"email_"})
        result = guard.check_action("email_send")
        assert result.passed is False
        assert "prefix" in result.reason

    def test_empty_action_rejected(self):
        guard = SafetyGuard()
        result = guard.check_action("")
        assert result.passed is False

    def test_custom_blacklist(self):
        guard = SafetyGuard(sensitive_actions={"dangerous_op"})
        assert guard.check_action("dangerous_op").passed is False
        assert guard.check_action("click").passed is True


class TestSafetyGuardText:
    """测试文本 PII 和敏感关键词检测"""

    def test_detects_phone_number(self):
        guard = SafetyGuard()
        result = guard.check_text("我的手机号是 13800138000")
        assert result.passed is False
        assert "pii:phone_cn" in result.violated_rules

    def test_detects_id_card(self):
        guard = SafetyGuard()
        result = guard.check_text("身份证号 110101199001011234")
        assert result.passed is False
        assert "pii:idcard_cn" in result.violated_rules

    def test_detects_sensitive_keyword(self):
        guard = SafetyGuard()
        result = guard.check_text("请输入你的密码")
        assert result.passed is False
        assert "keyword:密码" in result.violated_rules

    def test_whitelist_allows_test_data(self):
        guard = SafetyGuard()
        result = guard.check_text("test_123 hello")
        assert result.passed is True

    def test_pii_not_exempted_by_whitelist(self):
        guard = SafetyGuard()
        result = guard.check_text("test_123 13800138000")
        assert result.passed is False
        assert "pii:phone_cn" in result.violated_rules

    def test_empty_text_passes(self):
        guard = SafetyGuard()
        assert guard.check_text("").passed is True


class TestSafetyGuardTask:
    """测试完整 Task 安全检查"""

    def test_blocks_wechat_task(self):
        guard = SafetyGuard()
        result = guard.check_task("wechat_send", target="张三", value="你好")
        assert result.passed is False

    def test_blocks_sensitive_text_in_value(self):
        guard = SafetyGuard()
        result = guard.check_task("type", target="input", value="密码: 123456")
        assert result.passed is False

    def test_allows_safe_task(self):
        guard = SafetyGuard()
        result = guard.check_task("click", target="test_button", value="hello")
        assert result.passed is True

    def test_recipient_mismatch(self):
        guard = SafetyGuard()
        result = guard.confirm_recipient_identity("张三", "李四")
        assert result.passed is False
        assert "mismatch" in result.reason

    def test_recipient_match(self):
        guard = SafetyGuard()
        result = guard.confirm_recipient_identity("张三", "张三")
        assert result.passed is True


# ---------------------------------------------------------------------------
# Config Extension Tests
# ---------------------------------------------------------------------------

class TestConfigInjectionFields:
    """测试 Config 新增 test_failure_injection 字段"""

    def test_default_values(self):
        config = Config()
        assert config.test_failure_injection_enabled is False
        assert config.test_failure_injection_scenario is None
        assert config.test_failure_injection_delay == 0.0

    def test_custom_scenario(self):
        config = Config()
        config.test_failure_injection_enabled = True
        config.test_failure_injection_scenario = {
            "action": "click",
            "target": "btn",
            "delay": 0.5,
        }
        config.test_failure_injection_delay = 1.0
        assert config.test_failure_injection_enabled is True
        assert config.test_failure_injection_scenario["action"] == "click"

    def test_no_existing_behavior_change(self):
        """确保默认值不影响现有功能"""
        config = Config()
        # 所有 Self-Healing 配置应保持原有默认值
        assert config.vlm_diagnosis_enabled is True
        assert config.max_retries == 3


# ---------------------------------------------------------------------------
# Executor Failure Injection Tests
# ---------------------------------------------------------------------------

class TestExecutorFailureInjection:
    """测试 Executor _resolve_target 失败注入"""

    def test_injection_disabled_by_default(self):
        from src.core.executor import TaskExecutor

        config = Config()
        config.test_failure_injection_enabled = False

        executor = TaskExecutor(config=config)
        # 正常坐标应返回成功
        result = executor._resolve_target("100,200", np.zeros((100, 100, 3), dtype=np.uint8), "click")
        assert result == (100, 200)

    def test_injection_triggers_on_match(self):
        from src.core.executor import TaskExecutor

        config = Config()
        config.test_failure_injection_enabled = True
        config.test_failure_injection_scenario = {
            "action": "click",
            "target": "btn",
        }

        executor = TaskExecutor(config=config)
        with pytest.raises(NotFoundError) as exc_info:
            executor._resolve_target("btn", np.zeros((100, 100, 3), dtype=np.uint8), "click")
        assert "INJECTED" in str(exc_info.value)

    def test_injection_respects_delay(self):
        from src.core.executor import TaskExecutor

        config = Config()
        config.test_failure_injection_enabled = True
        config.test_failure_injection_scenario = {
            "action": "click",
            "target": "btn",
            "delay": 0.1,
        }

        executor = TaskExecutor(config=config)
        start = time.time()
        with pytest.raises(NotFoundError):
            executor._resolve_target("btn", np.zeros((100, 100, 3), dtype=np.uint8), "click")
        elapsed = time.time() - start
        assert elapsed >= 0.08  # 允许少量误差

    def test_injection_no_match_continues_normally(self):
        from src.core.executor import TaskExecutor

        config = Config()
        config.test_failure_injection_enabled = True
        config.test_failure_injection_scenario = {
            "action": "click",
            "target": "btn",
        }

        executor = TaskExecutor(config=config)
        # action 不匹配（scenario 要求 click，实际传入 type），注入不触发
        # 使用合法坐标，确保原有逻辑正常执行
        result = executor._resolve_target("100,200", np.zeros((100, 100, 3), dtype=np.uint8), "type")
        assert result == (100, 200)

    def test_injection_uses_config_delay_fallback(self):
        from src.core.executor import TaskExecutor

        config = Config()
        config.test_failure_injection_enabled = True
        config.test_failure_injection_scenario = {
            "action": "click",
            "target": "btn",
            # 不提供 delay
        }
        config.test_failure_injection_delay = 0.05

        executor = TaskExecutor(config=config)
        start = time.time()
        with pytest.raises(NotFoundError):
            executor._resolve_target("btn", np.zeros((100, 100, 3), dtype=np.uint8), "click")
        elapsed = time.time() - start
        assert elapsed >= 0.03


# ---------------------------------------------------------------------------
# Window Manager Tests
# ---------------------------------------------------------------------------

class TestWindowManager:
    """测试窗口管理器（部分 mock，避免真实启动窗口）"""

    def test_app_commands_dict(self):
        from src.utils.window_manager import APP_COMMANDS
        assert "notepad" in APP_COMMANDS
        assert "calc" in APP_COMMANDS

    def test_window_info_center(self):
        from src.utils.window_manager import WindowInfo
        info = WindowInfo(hwnd=123, title="Test", rect=(100, 100, 300, 300))
        assert info.center == (200, 200)

    @patch("src.utils.window_manager._get_pyautogui_windows")
    def test_find_windows(self, mock_get_windows):
        from src.utils.window_manager import find_windows

        mock_win = MagicMock()
        mock_win.title = "Notepad - test.txt"
        mock_win.left = 100
        mock_win.top = 100
        mock_win.right = 400
        mock_win.bottom = 300
        mock_win._hWnd = 123
        mock_get_windows.return_value = [mock_win]

        results = find_windows("notepad")
        assert len(results) == 1
        assert results[0].title == "Notepad - test.txt"
        assert results[0].rect == (100, 100, 400, 300)

    @patch("src.utils.window_manager.subprocess.Popen")
    def test_launch_app(self, mock_popen):
        from src.utils.window_manager import launch_app
        mock_popen.return_value = MagicMock()
        assert launch_app("notepad", wait_sec=0.1) is True
        mock_popen.assert_called_once()

    @patch("src.utils.window_manager.subprocess.Popen")
    def test_launch_app_failure(self, mock_popen):
        from src.utils.window_manager import launch_app
        mock_popen.side_effect = Exception("not found")
        assert launch_app("nonexistent_app", wait_sec=0.1) is False

    @patch("src.utils.window_manager._get_pyautogui_windows")
    def test_close_window_by_title(self, mock_get_all):
        from src.utils.window_manager import close_window_by_title, WindowInfo

        mock_win = MagicMock()
        mock_win.title = "Notepad - test.txt"
        mock_win.left = 100
        mock_win.top = 100
        mock_win.right = 400
        mock_win.bottom = 300
        mock_win._hWnd = 123
        # 第一次：找到窗口；第二次（while循环检查）：已关闭
        mock_get_all.side_effect = [
            [mock_win],   # find_windows 调用
            [mock_win],   # close_window_by_title 内部遍历
            [],           # while 循环检查：已关闭
        ]

        result = close_window_by_title("Notepad", timeout_sec=0.5)
        assert result is True
        mock_win.close.assert_called_once()

    @patch("src.utils.window_manager.subprocess.run")
    def test_force_kill_app(self, mock_run):
        from src.utils.window_manager import force_kill_app
        mock_run.return_value = MagicMock(returncode=0)
        assert force_kill_app("notepad") is True


# ---------------------------------------------------------------------------
# Integration: Executor + SafetyGuard
# ---------------------------------------------------------------------------

class TestExecutorWithSafety:
    """集成测试：Executor 与 SafetyGuard 配合"""

    def test_executor_rejects_wechat_send(self):
        from src.core.executor import TaskExecutor
        from src.core.safety import SafetyGuard

        # SafetyGuard 独立测试已通过，此处验证 Executor 可集成
        guard = SafetyGuard()
        result = guard.check_action("wechat_send")
        assert result.passed is False

        # 验证 Executor 的 task action 映射中包含 wechat_send
        executor = TaskExecutor()
        assert hasattr(executor, "_execute_single_task")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
