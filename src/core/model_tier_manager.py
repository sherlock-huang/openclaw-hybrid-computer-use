"""三层模型管理器

从低到高的模型储备：
  L1: Minimax M2.7  — 主力诊断（快、便宜）
  L2: 小米 Mimo      — 深度诊断（中等成本）
  L3: GPT-5/4V       — 最强兜底（高成本）

执行成功后，高层模型总结增量经验 → Skill → 传给低层模型学习。
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import numpy as np

from .skill_manager import SkillManager, SkillEntry
from ..vision.minimax_client import MinimaxClient
from ..vision.mimo_client import MimoClient
from ..vision.llm_client import VLMClient
from ..vision.local_vlm_client import LocalVLMClient
from ..utils.exceptions import ConfigError

logger = logging.getLogger(__name__)


@dataclass
class TierResult:
    """单层模型执行结果"""
    tier: str
    success: bool
    diagnosis: str
    parsed_diagnosis: Optional[Dict[str, Any]]
    latency_ms: float
    error: Optional[str] = None


class ModelTierManager:
    """四层模型管理器（含本地离线兜底）"""

    TIER_ORDER = ["minimax", "mimo", "gpt5", "local"]

    def __init__(
        self,
        skill_manager: Optional[SkillManager] = None,
        minimax_client: Optional[MinimaxClient] = None,
        mimo_client: Optional[MimoClient] = None,
        gpt5_client: Optional[VLMClient] = None,
        local_client: Optional[LocalVLMClient] = None,
        config=None,
    ):
        self.skill_manager = skill_manager or SkillManager()
        self.minimax = minimax_client
        self.mimo = mimo_client
        self.gpt5 = gpt5_client
        self.local = local_client
        self.config = config
        self._clients: Dict[str, Any] = {}
        self._init_clients()

    def _init_clients(self):
        """延迟初始化客户端"""
        if self.minimax is None:
            try:
                self.minimax = MinimaxClient()
                self._clients["minimax"] = self.minimax
                logger.info("MinimaxClient 初始化成功")
            except ConfigError as e:
                logger.warning(f"MinimaxClient 初始化失败: {e}")
        else:
            self._clients["minimax"] = self.minimax

        if self.mimo is None:
            try:
                self.mimo = MimoClient()
                self._clients["mimo"] = self.mimo
                logger.info("MimoClient 初始化成功")
            except ConfigError as e:
                logger.warning(f"MimoClient 初始化失败: {e}")
        else:
            self._clients["mimo"] = self.mimo

        if self.gpt5 is None:
            try:
                self.gpt5 = VLMClient(provider="openai", model="gpt-4o")
                self._clients["gpt5"] = self.gpt5
                logger.info("GPT-5/4V Client 初始化成功")
            except ConfigError as e:
                logger.warning(f"GPT-5/4V Client 初始化失败: {e}")
        else:
            self._clients["gpt5"] = self.gpt5

        # 本地 VLM 离线兜底（延迟加载，不在这里初始化模型权重）
        if self.local is None:
            try:
                local_cfg = {}
                if self.config:
                    local_cfg = {
                        "model_name": self.config.local_vlm_model,
                        "device": self.config.local_vlm_device,
                        "cache_dir": self.config.local_vlm_cache_dir,
                        "load_in_4bit": self.config.local_vlm_load_in_4bit,
                        "load_in_8bit": self.config.local_vlm_load_in_8bit,
                        "max_tokens": self.config.local_vlm_max_tokens,
                        "temperature": self.config.local_vlm_temperature,
                    }
                self.local = LocalVLMClient(**local_cfg)
                self._clients["local"] = self.local
                logger.info("LocalVLMClient 初始化成功（模型权重延迟加载）")
            except Exception as e:
                logger.warning(f"LocalVLMClient 初始化失败: {e}")
        else:
            self._clients["local"] = self.local

    def diagnose_with_fallback(
        self,
        failure_type: str,
        task_action: str,
        original_target: str,
        screenshot: np.ndarray,
        annotated_screenshot: Optional[np.ndarray],
        system_prompt: str,
        instruction: str,
    ) -> TierResult:
        """
        从低到高尝试三层模型诊断。

        返回第一个成功的 TierResult，或者最后一个失败的 TierResult。
        """
        last_result = None

        for tier in self.TIER_ORDER:
            client = self._clients.get(tier)
            if client is None:
                logger.warning(f"{tier} 客户端未初始化，跳过")
                continue

            start = time.time()
            try:
                logger.info(f"尝试 {tier} 诊断...")
                if hasattr(client, "diagnose_failure"):
                    diagnosis = client.diagnose_failure(
                        screenshot=screenshot,
                        annotated_screenshot=annotated_screenshot,
                        instruction=instruction,
                        system_prompt=system_prompt,
                    )
                else:
                    # 回退到 VLMClient.analyze_screen
                    diagnosis_dict = client.analyze_screen(
                        screenshot=screenshot,
                        instruction=instruction,
                    )
                    diagnosis = json.dumps(diagnosis_dict, ensure_ascii=False)

                latency = (time.time() - start) * 1000
                parsed = self._try_parse_json(diagnosis)

                # 判断诊断是否"理想"（有实际修复建议）
                is_ideal = self._is_ideal_diagnosis(parsed)

                result = TierResult(
                    tier=tier,
                    success=is_ideal,
                    diagnosis=diagnosis,
                    parsed_diagnosis=parsed,
                    latency_ms=latency,
                )
                last_result = result

                if is_ideal:
                    logger.info(f"{tier} 诊断理想，返回结果")
                    return result
                else:
                    logger.info(f"{tier} 诊断不理想，升级到下一层")

            except Exception as e:
                latency = (time.time() - start) * 1000
                last_result = TierResult(
                    tier=tier,
                    success=False,
                    diagnosis="",
                    parsed_diagnosis=None,
                    latency_ms=latency,
                    error=str(e),
                )
                logger.warning(f"{tier} 诊断异常: {e}")

        # 所有层级都失败，返回最后一个结果
        return last_result or TierResult(
            tier="none", success=False, diagnosis="", parsed_diagnosis=None, latency_ms=0,
            error="所有模型层级都不可用",
        )

    def verify_with_tier(
        self,
        tier: str,
        screenshot_before: np.ndarray,
        screenshot_after: np.ndarray,
        instruction: str,
        system_prompt: str,
    ) -> str:
        """使用指定层级的模型验证修复结果"""
        client = self._clients.get(tier)
        if client is None:
            raise RuntimeError(f"{tier} 客户端未初始化")

        if hasattr(client, "verify_result"):
            return client.verify_result(
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                instruction=instruction,
                system_prompt=system_prompt,
            )
        else:
            # 回退：用 analyze_screen 分析 after 截图
            result = client.analyze_screen(
                screenshot=screenshot_after,
                instruction=instruction,
            )
            return json.dumps(result, ensure_ascii=False)

    def distill_skill(
        self,
        tier: str,
        failure_type: str,
        task_action: str,
        original_target: str,
        successful_strategy: str,
        successful_target: str,
        successful_center: List[int],
        screen_context_hash: str,
        vlm_diagnosis: str,
        semantic_equivalents: List[str] = None,
    ) -> SkillEntry:
        """
        高层模型成功后，总结增量 skill 沉淀到 SkillManager。
        低层模型下次同类型任务时会优先使用。
        """
        entry = self.skill_manager.add_skill(
            failure_type=failure_type,
            task_action=task_action,
            original_target=original_target,
            semantic_equivalents=semantic_equivalents or [],
            successful_strategy=successful_strategy,
            successful_target=successful_target,
            successful_center=successful_center,
            screen_context_hash=screen_context_hash,
            recovery_success=True,
            vlm_diagnosis=vlm_diagnosis,
            created_by_tier=tier,
        )
        logger.info(f"Skill 蒸馏完成: {entry.id} (来源: {tier})")
        return entry

    def _is_ideal_diagnosis(self, parsed: Optional[Dict[str, Any]]) -> bool:
        """判断诊断结果是否"理想"（有实际修复建议）"""
        if not parsed:
            return False
        # 关键字段存在且有意义
        has_suggestion = bool(
            parsed.get("suggested_target")
            or parsed.get("root_cause")
            or parsed.get("action")
        )
        confidence = parsed.get("confidence", 0.0)
        return has_suggestion and confidence > 0.5

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        import json, re
        try:
            match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except Exception:
            return None

    def get_available_tiers(self) -> List[str]:
        """获取当前可用的模型层级"""
        return [t for t in self.TIER_ORDER if t in self._clients]
