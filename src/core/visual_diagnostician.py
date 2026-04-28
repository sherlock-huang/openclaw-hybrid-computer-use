"""视觉诊断器 —— 融合推理引擎（Self-Healing Phase 2）

整合 YOLO + OCR 的结构化检测结果，结合三层模型做增强诊断。
核心流程：
  1. VisualContextBuilder: 截图 + YOLO + OCR → 标注图 + 结构化 JSON
  2. 语义优先级排序: 按与 target 的语义相似度对候选元素排序
  3. 三层模型诊断: Minimax → Mimo → GPT-5
  4. Verify Loop: 修复后截图验证
  5. Skill 沉淀: 成功后将经验写入 Skill 库
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

import cv2
import numpy as np

from .skill_manager import SkillManager, SkillEntry
from .model_tier_manager import ModelTierManager, TierResult
from .failure_analyzer import FailureType
from .models import Task
from ..vision.prompts import get_diagnosis_prompt, get_verify_prompt

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisReport:
    """诊断报告"""
    root_cause: str
    confidence: float
    target_presence: str           # found / found_similar / not_found / obscured
    suggested_target: Dict[str, Any]
    suggested_action: str
    reasoning: str
    fallback_strategy: str
    semantic_equivalents: List[str]
    tier_used: str


@dataclass
class VisualContext:
    """视觉上下文"""
    annotated_image: np.ndarray
    context_json: Dict[str, Any]
    top_candidates: List[Dict[str, Any]]


class VisualContextBuilder:
    """视觉上下文构建器：YOLO + OCR → 标注图 + 结构化数据"""

    def __init__(self, max_candidates: int = 15):
        self.max_candidates = max_candidates

    def build(
        self,
        screenshot: np.ndarray,
        target: str,
        yolo_elements: Optional[List] = None,
        ocr_texts: Optional[List] = None,
        last_click_pos: Optional[Tuple[int, int]] = None,
    ) -> VisualContext:
        """
        构建视觉上下文。

        Args:
            screenshot: 原始截图 (BGR)
            target: 用户要找的目标
            yolo_elements: YOLO 检测到的 UIElement 列表
            ocr_texts: OCR 检测到的 TextBox 列表
            last_click_pos: 上次尝试点击的位置（红色高亮）
        """
        annotated = screenshot.copy()
        h, w = screenshot.shape[:2]

        all_candidates = []

        # 绘制 YOLO 元素（蓝色框）
        if yolo_elements:
            for i, elem in enumerate(yolo_elements):
                x1, y1, x2, y2 = elem.bbox.x1, elem.bbox.y1, elem.bbox.x2, elem.bbox.y2
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)
                label = f"Y{i}:{elem.element_type}({elem.confidence:.2f})"
                cv2.putText(annotated, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                all_candidates.append({
                    "id": f"Y{i}",
                    "type": "yolo",
                    "element_type": elem.element_type,
                    "text": getattr(elem, "text", ""),
                    "bbox": [x1, y1, x2, y2],
                    "center": [int((x1+x2)/2), int((y1+y2)/2)],
                    "confidence": round(elem.confidence, 3),
                })

        # 绘制 OCR 文字（绿色框）
        if ocr_texts:
            for i, box in enumerate(ocr_texts):
                x1, y1, x2, y2 = box.bbox
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"O{i}:{box.text}({box.confidence:.2f})"
                cv2.putText(annotated, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                all_candidates.append({
                    "id": f"O{i}",
                    "type": "ocr",
                    "element_type": "text",
                    "text": box.text,
                    "bbox": [x1, y1, x2, y2],
                    "center": [int((x1+x2)/2), int((y1+y2)/2)],
                    "confidence": round(box.confidence, 3),
                })

        # 红色高亮上次点击位置
        if last_click_pos:
            cx, cy = last_click_pos
            cv2.circle(annotated, (cx, cy), 15, (0, 0, 255), 3)
            cv2.putText(annotated, "LAST_CLICK", (cx + 20, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # 语义优先级排序
        ranked = self._rank_by_semantic_relevance(target, all_candidates)
        top_candidates = ranked[:self.max_candidates]

        context_json = {
            "screen_size": [w, h],
            "target": target,
            "total_candidates": len(all_candidates),
            "top_candidates": top_candidates,
            "last_click_pos": last_click_pos,
        }

        return VisualContext(
            annotated_image=annotated,
            context_json=context_json,
            top_candidates=top_candidates,
        )

    def _rank_by_semantic_relevance(
        self, target: str, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """按与 target 的语义相似度排序候选元素"""
        target_lower = target.lower()

        def score(c):
            s = 0.0
            text = c.get("text", "").lower()
            elem_type = c.get("element_type", "").lower()

            # 文字完全包含 target
            if target_lower in text:
                s += 3.0
            # 文字部分匹配
            elif any(t in text for t in target_lower.split()):
                s += 1.5
            # 元素类型暗示（如 target 含"按钮"且 type 是 button）
            if "button" in elem_type and ("按钮" in target or "button" in target_lower):
                s += 1.0
            if "input" in elem_type and ("输入" in target or "input" in target_lower):
                s += 1.0
            # 置信度加权
            s += c.get("confidence", 0.0)
            return s

        candidates.sort(key=score, reverse=True)
        return candidates


class VisualDiagnostician:
    """视觉诊断器 —— 融合 YOLO/OCR + 三层模型的诊断引擎"""

    def __init__(
        self,
        model_tier_manager: Optional[ModelTierManager] = None,
        skill_manager: Optional[SkillManager] = None,
        context_builder: Optional[VisualContextBuilder] = None,
        config=None,
    ):
        self.tier_manager = model_tier_manager or ModelTierManager(config=config)
        self.skill_manager = skill_manager or SkillManager()
        self.context_builder = context_builder or VisualContextBuilder()
        self.config = config

    def diagnose(
        self,
        failure_type: FailureType,
        task: Task,
        screenshot: np.ndarray,
        yolo_elements: Optional[List] = None,
        ocr_texts: Optional[List] = None,
        last_click_pos: Optional[Tuple[int, int]] = None,
        execution_history: Optional[List] = None,
        error_message: str = "",
    ) -> Tuple[DiagnosisReport, TierResult]:
        """
        执行完整的视觉诊断流程。

        Returns:
            (DiagnosisReport, TierResult)
        """
        # Step 1: 构建视觉上下文
        visual_ctx = self.context_builder.build(
            screenshot=screenshot,
            target=task.target or "",
            yolo_elements=yolo_elements,
            ocr_texts=ocr_texts,
            last_click_pos=last_click_pos,
        )

        # Step 2: 构建诊断 prompt
        system_prompt = "你是 UI 自动化调试专家，擅长分析屏幕截图并给出精准的修复建议。"
        instruction = get_diagnosis_prompt(
            failure_type=failure_type.name,
            task=task,
            error_message=error_message,
            visual_context=visual_ctx.context_json,
            history=execution_history,
        )

        # Step 3: 三层模型诊断（从低到高）
        tier_result = self.tier_manager.diagnose_with_fallback(
            failure_type=failure_type.name,
            task_action=task.action,
            original_target=task.target or "",
            screenshot=screenshot,
            annotated_screenshot=visual_ctx.annotated_image,
            system_prompt=system_prompt,
            instruction=instruction,
        )

        # Step 4: 解析诊断报告
        report = self._parse_diagnosis(tier_result.diagnosis, tier_result.tier)
        return report, tier_result

    def verify(
        self,
        tier: str,
        screenshot_before: np.ndarray,
        screenshot_after: np.ndarray,
        task: Task,
        expected_effect: str = "",
    ) -> Dict[str, Any]:
        """
        Verify Loop：验证修复是否成功。
        """
        instruction = get_verify_prompt(
            task=task,
            expected_effect=expected_effect,
        )
        system_prompt = "你是操作验证助手，负责验证自动化操作是否成功执行。请比较两张截图并给出判断。"

        try:
            response = self.tier_manager.verify_with_tier(
                tier=tier,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                instruction=instruction,
                system_prompt=system_prompt,
            )
            parsed = self._try_parse_json(response)
            if parsed:
                return parsed
            # 文本推断
            success = "success" in response.lower() or "成功" in response
            return {
                "success": success,
                "observation": response[:500],
                "adjustment_needed": not success,
                "new_strategy": "",
            }
        except Exception as e:
            logger.warning(f"验证失败: {e}")
            return {"success": False, "observation": str(e), "adjustment_needed": True}

    def distill_skill(
        self,
        tier: str,
        failure_type: FailureType,
        task: Task,
        report: DiagnosisReport,
        successful_center: List[int],
        screen_context_hash: str,
    ) -> Optional[SkillEntry]:
        """成功后沉淀增量 skill"""
        return self.tier_manager.distill_skill(
            tier=tier,
            failure_type=failure_type.name,
            task_action=task.action,
            original_target=task.target or "",
            successful_strategy=report.suggested_action,
            successful_target=report.suggested_target.get("value", ""),
            successful_center=successful_center,
            screen_context_hash=screen_context_hash,
            vlm_diagnosis=report.reasoning,
            semantic_equivalents=report.semantic_equivalents,
        )

    def _parse_diagnosis(self, text: str, tier: str) -> DiagnosisReport:
        """解析 VLM 诊断文本为结构化报告"""
        parsed = self._try_parse_json(text)
        if not parsed:
            # 无法解析，返回默认报告
            return DiagnosisReport(
                root_cause="无法解析诊断结果",
                confidence=0.0,
                target_presence="unknown",
                suggested_target={},
                suggested_action="screenshot",
                reasoning=text[:500],
                fallback_strategy="人工干预",
                semantic_equivalents=[],
                tier_used=tier,
            )

        return DiagnosisReport(
            root_cause=parsed.get("root_cause", ""),
            confidence=parsed.get("confidence", 0.0),
            target_presence=parsed.get("target_presence", "unknown"),
            suggested_target=parsed.get("suggested_target", {}),
            suggested_action=parsed.get("suggested_action", "screenshot"),
            reasoning=parsed.get("reasoning", ""),
            fallback_strategy=parsed.get("fallback_strategy", ""),
            semantic_equivalents=parsed.get("semantic_equivalents", []),
            tier_used=tier,
        )

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        import re
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
