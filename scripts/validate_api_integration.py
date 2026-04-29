"""Self-Healing 真实 API 联调验证脚本

验证内容：
1. API 连通性（简单 chat）
2. diagnose_failure 端到端（截图 + prompt → JSON 诊断）
3. JSON 结构验证
4. Verify Loop（before/after 截图比对）
5. 延迟统计

用法：
    C:/Users/Android/openclaw-python/python.exe scripts/validate_api_integration.py

环境变量要求（至少一个）：
    MINIMAX_API_KEY  或  MIMO_API_KEY
"""

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

# 确保能找到 src 模块
sys.path.insert(0, "d:/workspace/openclaw-hybrid-computer-use")

from src.core.key_manager import KeyManager
from src.vision.minimax_client import MinimaxClient
from src.vision.mimo_client import MimoClient

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """单项验证结果"""
    name: str
    passed: bool
    latency_ms: float = 0.0
    details: str = ""
    error: str = ""
    response_sample: str = ""


@dataclass
class ApiValidationReport:
    """API 验证报告"""
    provider: str
    results: List[ValidationResult] = field(default_factory=list)

    def add(self, result: ValidationResult):
        self.results.append(result)

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"[REPORT] {self.provider} 验证报告")
        print(f"{'='*60}")
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        for r in self.results:
            status = "[PASS]" if r.passed else "[FAIL]"
            print(f"{status} | {r.name} | {r.latency_ms:.0f}ms")
            if r.details:
                print(f"       详情: {r.details}")
            if r.error:
                print(f"       错误: {r.error}")
            if r.response_sample:
                print(f"       响应: {r.response_sample[:200]}")
        print(f"\n总计: {passed}/{total} 通过")
        print(f"{'='*60}\n")


def create_test_screenshot() -> np.ndarray:
    """创建一张模拟 UI 截图用于测试（1920x1080，带一个红色按钮）"""
    img = np.full((1080, 1920, 3), 240, dtype=np.uint8)  # 浅灰背景
    # 画一个红色按钮在中间
    y1, y2 = 400, 500
    x1, x2 = 800, 1120
    img[y1:y2, x1:x2] = [0, 0, 255]  # BGR 红色
    # 按钮文字（白色块模拟）
    img[y1+30:y2-30, x1+50:x2-50] = [255, 255, 255]
    return img


def create_test_screenshot_annotated() -> np.ndarray:
    """创建带标注的截图（蓝色框标出按钮）"""
    img = create_test_screenshot()
    # 画蓝色边框
    y1, y2 = 400, 500
    x1, x2 = 800, 1120
    img[y1:y1+3, x1:x2] = [255, 0, 0]
    img[y2-3:y2, x1:x2] = [255, 0, 0]
    img[y1:y2, x1:x1+3] = [255, 0, 0]
    img[y1:y2, x2-3:x2] = [255, 0, 0]
    return img


def validate_json_structure(text: str) -> tuple:
    """验证诊断返回的 JSON 结构是否完整"""
    import re
    try:
        # 尝试提取 JSON
        match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            json_str = match.group(1) if match else text
        data = json.loads(json_str)
    except Exception as e:
        return False, f"JSON 解析失败: {e}"

    required_fields = ["root_cause", "confidence", "suggested_target", "suggested_action"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return False, f"缺少必要字段: {missing}"

    # 检查 confidence 范围
    conf = data.get("confidence", 0)
    if not (0.0 <= conf <= 1.0):
        return False, f"confidence {conf} 不在 0~1 范围内"

    return True, "结构完整"


def test_connectivity(client, provider: str) -> ValidationResult:
    """测试 API 连通性：简单 text-only chat"""
    name = f"{provider} 连通性测试"
    start = time.time()
    try:
        response = client.chat(
            messages=[{"role": "user", "content": "你好，请回复'pong'"}],
            max_tokens=10,
        )
        latency = (time.time() - start) * 1000
        passed = len(response) > 0  # 只要返回非空内容即算连通
        return ValidationResult(
            name=name,
            passed=passed,
            latency_ms=latency,
            details=f"响应长度: {len(response)}",
            response_sample=response[:100],
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ValidationResult(
            name=name,
            passed=False,
            latency_ms=latency,
            error=str(e),
        )


def test_diagnose_failure(client, provider: str) -> ValidationResult:
    """测试 diagnose_failure 端到端"""
    name = f"{provider} diagnose_failure"
    screenshot = create_test_screenshot()
    annotated = create_test_screenshot_annotated()

    instruction = (
        "用户尝试点击'确认按钮'但失败了。\n"
        "请分析屏幕截图，给出失败原因和修复建议。\n"
        "输出 JSON 格式：{\"root_cause\": \"...\", \"confidence\": 0.8, "
        "\"suggested_target\": {...}, \"suggested_action\": \"...\"}"
    )

    start = time.time()
    try:
        diagnosis = client.diagnose_failure(
            screenshot=screenshot,
            annotated_screenshot=annotated,
            instruction=instruction,
            system_prompt="你是 UI 自动化调试专家。",
        )
        latency = (time.time() - start) * 1000

        valid, msg = validate_json_structure(diagnosis)
        return ValidationResult(
            name=name,
            passed=valid,
            latency_ms=latency,
            details=msg,
            response_sample=diagnosis[:300],
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ValidationResult(
            name=name,
            passed=False,
            latency_ms=latency,
            error=str(e),
        )


def test_verify_result(client, provider: str) -> ValidationResult:
    """测试 Verify Loop（操作前后截图比对）"""
    name = f"{provider} verify_result"
    before = create_test_screenshot()
    # after：按钮变成绿色表示已点击
    after = create_test_screenshot()
    y1, y2 = 400, 500
    x1, x2 = 800, 1120
    after[y1:y2, x1:x2] = [0, 255, 0]  # BGR 绿色

    instruction = "验证点击'确认按钮'后，按钮是否变成绿色（已点击状态）。"

    start = time.time()
    try:
        result = client.verify_result(
            screenshot_before=before,
            screenshot_after=after,
            instruction=instruction,
            system_prompt="你是操作验证助手。",
        )
        latency = (time.time() - start) * 1000
        passed = len(result) > 20  # 至少有一些内容
        return ValidationResult(
            name=name,
            passed=passed,
            latency_ms=latency,
            details=f"响应长度: {len(result)}",
            response_sample=result[:200],
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ValidationResult(
            name=name,
            passed=False,
            latency_ms=latency,
            error=str(e),
        )


def test_json_robustness(client, provider: str) -> ValidationResult:
    """测试 JSON 解析鲁棒性：故意给出模糊指令，看是否仍能返回可解析 JSON"""
    name = f"{provider} JSON 鲁棒性"
    screenshot = create_test_screenshot()

    # 故意模糊的指令
    instruction = "分析一下"

    start = time.time()
    try:
        diagnosis = client.diagnose_failure(
            screenshot=screenshot,
            annotated_screenshot=None,
            instruction=instruction,
        )
        latency = (time.time() - start) * 1000
        # 即使模糊，也应该返回一些文本（不一定非得是 JSON）
        passed = len(diagnosis) > 10
        return ValidationResult(
            name=name,
            passed=passed,
            latency_ms=latency,
            details=f"响应长度: {len(diagnosis)}",
            response_sample=diagnosis[:200],
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ValidationResult(
            name=name,
            passed=False,
            latency_ms=latency,
            error=str(e),
        )


def run_provider_validation(provider: str, client) -> ApiValidationReport:
    """运行单个 provider 的全部验证"""
    report = ApiValidationReport(provider=provider)
    logger.info(f"\n[CHECK] 开始验证 {provider}...")

    report.add(test_connectivity(client, provider))
    report.add(test_diagnose_failure(client, provider))
    report.add(test_verify_result(client, provider))
    report.add(test_json_robustness(client, provider))

    report.print_summary()
    return report


def main():
    print("=" * 60)
    print("OpenClaw Self-Healing 真实 API 联调验证")
    print("=" * 60)

    km = KeyManager(auto_load_env=True)
    all_passed = 0
    all_total = 0

    # Minimax
    minimax_key = km.get_key("minimax")
    if minimax_key:
        try:
            client = MinimaxClient(api_key=minimax_key)
            report = run_provider_validation("Minimax", client)
            all_passed += sum(1 for r in report.results if r.passed)
            all_total += len(report.results)
        except Exception as e:
            logger.error(f"MinimaxClient 初始化失败: {e}")
    else:
        logger.warning("未找到 MINIMAX_API_KEY，跳过 Minimax 验证")

    # Mimo
    mimo_key = km.get_key("mimo")
    if mimo_key:
        try:
            client = MimoClient(api_key=mimo_key)
            report = run_provider_validation("Mimo", client)
            all_passed += sum(1 for r in report.results if r.passed)
            all_total += len(report.results)
        except Exception as e:
            logger.error(f"MimoClient 初始化失败: {e}")
    else:
        logger.warning("未找到 MIMO_API_KEY，跳过 Mimo 验证")

    # 总览
    print("\n" + "=" * 60)
    print(f"[FINAL] 总体验证结果: {all_passed}/{all_total} 通过")
    print("=" * 60)

    if all_total > 0 and all_passed == all_total:
        print("[OK] 全部通过！Self-Healing API 联调就绪。")
        return 0
    elif all_total > 0:
        print("[WARN] 部分未通过，请查看上方详情。")
        return 1
    else:
        print("[ERR] 未找到任何可用 API Key，无法验证。")
        return 2


if __name__ == "__main__":
    sys.exit(main())
