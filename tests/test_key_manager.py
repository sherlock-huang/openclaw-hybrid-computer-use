"""Tests for KeyManager."""

import pytest

from src.core.key_manager import KeyManager, ApiKey, KeyState, ProviderConfig


class TestKeyManager:
    def test_init_empty(self):
        km = KeyManager(auto_load_env=False)
        assert km.get_key("minimax") is None

    def test_register_and_get_key(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "sk-test-123")
        assert km.get_key("minimax") == "sk-test-123"

    def test_get_key_rotation(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "key-a")
        km.register_key("minimax", "key-b")
        # 轮询：第一次 a，第二次 b，第三次 a
        assert km.get_key("minimax") == "key-a"
        assert km.get_key("minimax") == "key-b"
        assert km.get_key("minimax") == "key-a"

    def test_duplicate_key_dedup(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "same")
        km.register_key("minimax", "same")
        assert len(km._keys["minimax"]) == 1

    def test_report_success(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "k1")
        km.report_result("minimax", "k1", success=True)
        summary = km.get_provider_summary("minimax")
        assert summary["keys"][0]["state"] == "healthy"
        assert summary["keys"][0]["success_rate"] == 1.0

    def test_report_failure_degraded(self):
        km = KeyManager(auto_load_env=False, providers={
            "minimax": ProviderConfig(name="minimax", failure_threshold=3),
        })
        km.register_key("minimax", "k1")
        km.report_result("minimax", "k1", success=False, error="timeout")
        km.report_result("minimax", "k1", success=False, error="timeout")
        summary = km.get_provider_summary("minimax")
        assert summary["keys"][0]["state"] == "degraded"
        assert summary["keys"][0]["consecutive_failures"] == 2

    def test_report_failure_exhausted(self):
        km = KeyManager(auto_load_env=False, providers={
            "minimax": ProviderConfig(name="minimax", failure_threshold=2),
        })
        km.register_key("minimax", "k1")
        km.report_result("minimax", "k1", success=False)
        km.report_result("minimax", "k1", success=False)
        summary = km.get_provider_summary("minimax")
        assert summary["keys"][0]["state"] == "exhausted"
        # exhausted key 不再被分配
        assert km.get_key("minimax") is None

    def test_rotation_skips_exhausted(self):
        km = KeyManager(auto_load_env=False, providers={
            "minimax": ProviderConfig(name="minimax", failure_threshold=1),
        })
        km.register_key("minimax", "bad")
        km.register_key("minimax", "good")
        km.report_result("minimax", "bad", success=False)
        # bad 被标记 exhausted，轮询应该直接返回 good
        assert km.get_key("minimax") == "good"
        assert km.get_key("minimax") == "good"

    def test_success_resets_exhausted(self):
        km = KeyManager(auto_load_env=False, providers={
            "minimax": ProviderConfig(name="minimax", failure_threshold=1),
        })
        km.register_key("minimax", "k1")
        km.report_result("minimax", "k1", success=False)
        assert km._keys["minimax"][0].state == KeyState.EXHAUSTED
        km.report_result("minimax", "k1", success=True)
        assert km._keys["minimax"][0].state == KeyState.HEALTHY

    def test_reset_provider(self):
        km = KeyManager(auto_load_env=False, providers={
            "minimax": ProviderConfig(name="minimax", failure_threshold=1),
        })
        km.register_key("minimax", "k1")
        km.report_result("minimax", "k1", success=False)
        assert km._keys["minimax"][0].state == KeyState.EXHAUSTED
        km.reset_provider("minimax")
        assert km._keys["minimax"][0].state == KeyState.HEALTHY

    def test_multi_provider_independent(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "mk")
        km.register_key("mimo", "mik")
        assert km.get_key("minimax") == "mk"
        assert km.get_key("mimo") == "mik"

    def test_summary_success_rate(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "k1")
        km.report_result("minimax", "k1", success=True)
        km.report_result("minimax", "k1", success=True)
        km.report_result("minimax", "k1", success=False)
        summary = km.get_provider_summary("minimax")
        assert summary["keys"][0]["success_rate"] == 0.67

    def test_all_summary(self):
        km = KeyManager(auto_load_env=False)
        km.register_key("minimax", "k1")
        km.register_key("mimo", "k2")
        all_summary = km.get_all_summary()
        assert "minimax" in all_summary
        assert "mimo" in all_summary
