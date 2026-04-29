"""Tests for health monitor and circuit breaker."""

import time

import pytest

from src.core.health_monitor import HealthMonitor, HealthState


class TestHealthMonitor:
    def test_initial_state_is_healthy(self):
        hm = HealthMonitor()
        assert hm.should_attempt("minimax") is True
        assert hm.get_state("minimax") == HealthState.HEALTHY

    def test_record_success(self):
        hm = HealthMonitor()
        hm.record_success("minimax")
        assert hm.get_state("minimax") == HealthState.HEALTHY
        summary = hm.get_summary()["minimax"]
        assert summary["total_successes"] == 1
        assert summary["consecutive_failures"] == 0

    def test_record_failure_degraded(self):
        hm = HealthMonitor(failure_threshold=3)
        hm.record_failure("minimax", error="timeout")
        assert hm.get_state("minimax") == HealthState.DEGRADED
        hm.record_failure("minimax", error="timeout")
        assert hm.get_state("minimax") == HealthState.DEGRADED
        summary = hm.get_summary()["minimax"]
        assert summary["consecutive_failures"] == 2
        assert summary["total_failures"] == 2
        assert "timeout" in summary["last_error"]

    def test_record_failure_unhealthy(self):
        hm = HealthMonitor(failure_threshold=3)
        hm.record_failure("minimax")
        hm.record_failure("minimax")
        hm.record_failure("minimax")
        assert hm.get_state("minimax") == HealthState.UNHEALTHY
        assert hm.should_attempt("minimax") is False

    def test_cooldown_allows_probe(self):
        hm = HealthMonitor(
            failure_threshold=1,
            base_cooldown_sec=0.05,
        )
        hm.record_failure("minimax")
        assert hm.should_attempt("minimax") is False
        time.sleep(0.06)
        assert hm.should_attempt("minimax") is True

    def test_success_resets_unhealthy(self):
        hm = HealthMonitor(failure_threshold=1, base_cooldown_sec=300)
        hm.record_failure("minimax")
        assert hm.get_state("minimax") == HealthState.UNHEALTHY
        hm.record_success("minimax")
        assert hm.get_state("minimax") == HealthState.HEALTHY
        assert hm.should_attempt("minimax") is True

    def test_exponential_backoff(self):
        hm = HealthMonitor(
            failure_threshold=1,
            base_cooldown_sec=0.1,
            max_cooldown_sec=1.0,
        )
        hm.record_failure("minimax")
        first_probe = hm._health["minimax"].next_probe_time
        time.sleep(0.11)
        hm.should_attempt("minimax")  # triggers probe allowance
        hm.record_failure("minimax")
        second_probe = hm._health["minimax"].next_probe_time
        assert second_probe - first_probe >= 0.1

    def test_reset(self):
        hm = HealthMonitor(failure_threshold=1)
        hm.record_failure("minimax")
        assert hm.get_state("minimax") == HealthState.UNHEALTHY
        hm.reset("minimax")
        assert hm.get_state("minimax") == HealthState.HEALTHY
        assert hm.should_attempt("minimax") is True

    def test_multiple_tiers_independent(self):
        hm = HealthMonitor(failure_threshold=1)
        hm.record_failure("minimax")
        hm.record_success("mimo")
        assert hm.get_state("minimax") == HealthState.UNHEALTHY
        assert hm.get_state("mimo") == HealthState.HEALTHY

    def test_summary_returns_all_tiers(self):
        hm = HealthMonitor()
        hm.record_failure("minimax")
        summary = hm.get_summary()
        assert "minimax" in summary
        assert summary["minimax"]["state"] == "degraded"
