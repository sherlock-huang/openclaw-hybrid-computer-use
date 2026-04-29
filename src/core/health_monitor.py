"""API 健康监控与断路器

轻量级实现：无后台线程，在每次 diagnose 调用前检查状态。
- 连续失败达到阈值 → 标记为不可用，跳过该 tier
- 指数退避冷却 → 每隔一段时间允许再试一次
- 成功一次 → 立即恢复
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class TierHealth:
    """单个 tier 的健康记录"""
    tier: str
    state: HealthState = HealthState.HEALTHY
    consecutive_failures: int = 0
    last_check_time: float = 0.0
    next_probe_time: float = 0.0
    last_error: str = ""
    total_successes: int = 0
    total_failures: int = 0


class HealthMonitor:
    """断路器 + 健康监控"""

    def __init__(
        self,
        failure_threshold: int = 3,
        base_cooldown_sec: float = 30.0,
        max_cooldown_sec: float = 300.0,
        probe_timeout_sec: float = 10.0,
    ):
        self.failure_threshold = failure_threshold
        self.base_cooldown_sec = base_cooldown_sec
        self.max_cooldown_sec = max_cooldown_sec
        self.probe_timeout_sec = probe_timeout_sec
        self._health: Dict[str, TierHealth] = {}

    def _ensure(self, tier: str) -> TierHealth:
        if tier not in self._health:
            self._health[tier] = TierHealth(tier=tier)
        return self._health[tier]

    def record_success(self, tier: str) -> None:
        """记录一次成功调用"""
        h = self._ensure(tier)
        h.state = HealthState.HEALTHY
        h.consecutive_failures = 0
        h.last_check_time = time.time()
        h.next_probe_time = 0.0
        h.last_error = ""
        h.total_successes += 1
        logger.info(f"[HealthMonitor] {tier} 恢复 healthy")

    def record_failure(self, tier: str, error: str = "") -> None:
        """记录一次失败调用"""
        h = self._ensure(tier)
        h.consecutive_failures += 1
        h.last_check_time = time.time()
        h.last_error = error
        h.total_failures += 1

        if h.consecutive_failures >= self.failure_threshold:
            h.state = HealthState.UNHEALTHY
            cooldown = min(
                self.base_cooldown_sec * (2 ** (h.consecutive_failures - self.failure_threshold)),
                self.max_cooldown_sec,
            )
            h.next_probe_time = time.time() + cooldown
            logger.warning(
                f"[HealthMonitor] {tier} 连续失败 {h.consecutive_failures} 次，"
                f"标记为 unhealthy，冷却 {cooldown:.0f}s"
            )
        else:
            h.state = HealthState.DEGRADED
            logger.warning(
                f"[HealthMonitor] {tier} 失败 {h.consecutive_failures} 次，状态 degraded"
            )

    def should_attempt(self, tier: str) -> bool:
        """判断当前是否应该尝试调用该 tier"""
        h = self._ensure(tier)
        if h.state == HealthState.HEALTHY:
            return True
        if h.state == HealthState.DEGRADED:
            return True
        # UNHEALTHY: 只有过了冷却期才允许再试一次
        if time.time() >= h.next_probe_time:
            logger.info(f"[HealthMonitor] {tier} 冷却结束，允许探测")
            return True
        logger.info(
            f"[HealthMonitor] {tier} 仍在冷却中，"
            f"剩余 {h.next_probe_time - time.time():.0f}s"
        )
        return False

    def get_state(self, tier: str) -> HealthState:
        return self._ensure(tier).state

    def get_summary(self) -> Dict[str, dict]:
        """返回所有 tier 的健康摘要"""
        return {
            tier: {
                "state": h.state.value,
                "consecutive_failures": h.consecutive_failures,
                "total_successes": h.total_successes,
                "total_failures": h.total_failures,
                "last_error": h.last_error,
            }
            for tier, h in self._health.items()
        }

    def reset(self, tier: str) -> None:
        """手动重置某个 tier 的状态"""
        if tier in self._health:
            self._health[tier] = TierHealth(tier=tier)
            logger.info(f"[HealthMonitor] {tier} 状态已手动重置")
