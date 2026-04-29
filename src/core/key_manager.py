"""API Key 统一管理与轮询

解决多 provider Key 分散、无余额预警、无失败率统计的问题。
- 集中存储：支持环境变量自动加载 + 代码注册
- 多 Key 轮询：单个 provider 可配置多把 Key，自动切换
- 健康追踪：记录每把 Key 的成功/失败/调用次数
- 自动降级：连续失败达到阈值后标记 exhausted，跳过该 Key
- 余额查询：支持调用 provider 余额 API（如可用）
"""

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable

import requests

logger = logging.getLogger(__name__)


class KeyState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    EXHAUSTED = "exhausted"


@dataclass
class ApiKey:
    """单把 API Key 的状态记录"""
    value: str
    provider: str
    state: KeyState = KeyState.HEALTHY
    consecutive_failures: int = 0
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0
    last_used: float = 0.0
    last_error: str = ""
    # 可选：余额信息（单位：元 或 token）
    balance: Optional[float] = None
    balance_checked_at: Optional[float] = None


@dataclass
class ProviderConfig:
    """单个 provider 的配置"""
    name: str
    env_vars: List[str] = field(default_factory=list)
    # 余额查询端点（如果有）
    balance_url: Optional[str] = None
    # 余额解析函数：response json -> float
    balance_parser: Optional[Callable[[Dict], Optional[float]]] = None
    # 连续失败多少次标记 exhausted
    failure_threshold: int = 3


class KeyManager:
    """API Key 统一管理者"""

    # 预置 provider 配置
    DEFAULT_PROVIDERS = {
        "minimax": ProviderConfig(
            name="minimax",
            env_vars=["MINIMAX_API_KEY"],
            failure_threshold=3,
        ),
        "mimo": ProviderConfig(
            name="mimo",
            env_vars=["MIMO_API_KEY"],
            failure_threshold=3,
        ),
        "openai": ProviderConfig(
            name="openai",
            env_vars=["OPENAI_API_KEY"],
            failure_threshold=3,
        ),
        "anthropic": ProviderConfig(
            name="anthropic",
            env_vars=["ANTHROPIC_API_KEY"],
            failure_threshold=3,
        ),
        "kimi": ProviderConfig(
            name="kimi",
            env_vars=["KIMI_API_KEY", "KIMI_CODING_API_KEY"],
            failure_threshold=3,
        ),
    }

    def __init__(
        self,
        providers: Optional[Dict[str, ProviderConfig]] = None,
        auto_load_env: bool = True,
    ):
        self.providers = providers or self.DEFAULT_PROVIDERS.copy()
        self._keys: Dict[str, List[ApiKey]] = {}
        self._key_index: Dict[str, int] = {}  # 当前轮询索引

        if auto_load_env:
            self._load_from_env()

    def _load_from_env(self):
        """从环境变量自动加载 Key"""
        for provider_name, cfg in self.providers.items():
            for env_var in cfg.env_vars:
                key_value = os.getenv(env_var)
                if key_value:
                    self.register_key(provider_name, key_value, source=env_var)
                    logger.info(f"KeyManager 从环境变量加载 {provider_name}: {env_var}")

    def register_key(
        self,
        provider: str,
        key_value: str,
        source: str = "manual",
    ) -> ApiKey:
        """手动注册一把 Key"""
        if provider not in self._keys:
            self._keys[provider] = []
            self._key_index[provider] = 0

        # 去重：相同 key 不再重复添加
        for existing in self._keys[provider]:
            if existing.value == key_value:
                logger.debug(f"KeyManager {provider} Key 已存在，跳过")
                return existing

        key = ApiKey(value=key_value, provider=provider)
        self._keys[provider].append(key)
        logger.info(f"KeyManager 注册 {provider} Key (来源: {source})")
        return key

    def get_key(self, provider: str) -> Optional[str]:
        """
        获取当前 provider 的活跃 Key。
        轮询策略：跳过 exhausted 的 Key，在 healthy + degraded 之间轮询。
        """
        keys = self._keys.get(provider, [])
        if not keys:
            logger.warning(f"KeyManager {provider} 未注册任何 Key")
            return None

        cfg = self.providers.get(provider)
        threshold = cfg.failure_threshold if cfg else 3

        # 从当前索引开始，找第一个非 exhausted 的 Key
        start_idx = self._key_index.get(provider, 0)
        for offset in range(len(keys)):
            idx = (start_idx + offset) % len(keys)
            key = keys[idx]
            if key.state != KeyState.EXHAUSTED:
                # 更新轮询索引到下一个位置
                self._key_index[provider] = (idx + 1) % len(keys)
                key.last_used = time.time()
                key.total_calls += 1
                logger.debug(f"KeyManager 分配 {provider} Key (idx={idx}, state={key.state.value})")
                return key.value

        # 所有 Key 都 exhausted
        logger.error(f"KeyManager {provider} 所有 Key 已耗尽")
        return None

    def report_result(self, provider: str, key_value: str, success: bool, error: str = ""):
        """报告某把 Key 的调用结果，更新状态"""
        keys = self._keys.get(provider, [])
        for key in keys:
            if key.value == key_value:
                if success:
                    key.consecutive_failures = 0
                    key.total_successes += 1
                    if key.state in (KeyState.DEGRADED, KeyState.EXHAUSTED):
                        key.state = KeyState.HEALTHY
                        logger.info(f"KeyManager {provider} Key 恢复 healthy")
                else:
                    key.consecutive_failures += 1
                    key.total_failures += 1
                    key.last_error = error
                    cfg = self.providers.get(provider)
                    threshold = cfg.failure_threshold if cfg else 3
                    if key.consecutive_failures >= threshold:
                        key.state = KeyState.EXHAUSTED
                        logger.warning(
                            f"KeyManager {provider} Key 连续失败 {key.consecutive_failures} 次，"
                            f"标记为 exhausted"
                        )
                    else:
                        key.state = KeyState.DEGRADED
                        logger.warning(
                            f"KeyManager {provider} Key 失败 {key.consecutive_failures} 次，"
                            f"状态 degraded"
                        )
                return
        logger.warning(f"KeyManager 未找到 {provider} 的 Key 用于报告结果")

    def get_provider_summary(self, provider: str) -> Optional[Dict]:
        """获取单个 provider 的 Key 状态摘要"""
        keys = self._keys.get(provider, [])
        if not keys:
            return None
        return {
            "provider": provider,
            "total_keys": len(keys),
            "healthy": sum(1 for k in keys if k.state == KeyState.HEALTHY),
            "degraded": sum(1 for k in keys if k.state == KeyState.DEGRADED),
            "exhausted": sum(1 for k in keys if k.state == KeyState.EXHAUSTED),
            "keys": [
                {
                    "state": k.state.value,
                    "total_calls": k.total_calls,
                    "success_rate": round(k.total_successes / max(k.total_successes + k.total_failures, 1), 2),
                    "consecutive_failures": k.consecutive_failures,
                    "last_error": k.last_error,
                    "balance": k.balance,
                }
                for k in keys
            ],
        }

    def get_all_summary(self) -> Dict[str, Dict]:
        """获取所有 provider 的摘要"""
        return {
            provider: summary
            for provider in self._keys
            if (summary := self.get_provider_summary(provider))
        }

    def reset_key(self, provider: str, key_value: str):
        """手动重置某把 Key 的状态"""
        for key in self._keys.get(provider, []):
            if key.value == key_value:
                key.state = KeyState.HEALTHY
                key.consecutive_failures = 0
                key.last_error = ""
                logger.info(f"KeyManager {provider} Key 已手动重置")
                return

    def reset_provider(self, provider: str):
        """手动重置 provider 下所有 Key"""
        for key in self._keys.get(provider, []):
            key.state = KeyState.HEALTHY
            key.consecutive_failures = 0
            key.last_error = ""
        logger.info(f"KeyManager {provider} 所有 Key 已手动重置")

    def check_balance(self, provider: str) -> Optional[float]:
        """
        查询 provider 余额（如果配置了余额 API）。
        返回余额数值，或 None（不支持/查询失败）。
        """
        cfg = self.providers.get(provider)
        if not cfg or not cfg.balance_url or not cfg.balance_parser:
            logger.debug(f"KeyManager {provider} 未配置余额查询")
            return None

        key_value = self.get_key(provider)
        if not key_value:
            return None

        try:
            resp = requests.get(
                cfg.balance_url,
                headers={"Authorization": f"Bearer {key_value}"},
                timeout=10,
            )
            resp.raise_for_status()
            balance = cfg.balance_parser(resp.json())
            # 更新所有该 provider Key 的余额（假设共享账户）
            for key in self._keys.get(provider, []):
                key.balance = balance
                key.balance_checked_at = time.time()
            logger.info(f"KeyManager {provider} 余额查询成功: {balance}")
            return balance
        except Exception as e:
            logger.warning(f"KeyManager {provider} 余额查询失败: {e}")
            return None
