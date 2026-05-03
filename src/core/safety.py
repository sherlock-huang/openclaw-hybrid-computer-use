"""安全护栏模块 —— 敏感操作拦截与 PII 检测。

设计原则：
- 可复用：不仅用于 M4b 测试，也为未来 WeChat 安全操作预留扩展点。
- 可配置：黑名单和敏感词列表支持外部配置覆盖。
- 可审计：所有拦截和检测行为记录日志。
- 低误报：白名单机制避免阻塞无害的测试占位符。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 默认配置
# ---------------------------------------------------------------------------

DEFAULT_SENSITIVE_ACTIONS: Set[str] = {
    "wechat_send",
    "email_send",
    "email_read",
    "bank_transfer",
    "bank_query",
    "alipay_send",
    "wechat_pay",
}

DEFAULT_SENSITIVE_KEYWORDS: Set[str] = {
    "密码", "password", "passwd", "pwd",
    "验证码", "verification code", "captcha",
    "转账", "transfer", "汇款",
    "银行卡", "bank card", "credit card",
    "身份证", "id card",
    "密钥", "secret key", "api key", "token",
}

DEFAULT_PII_PATTERNS: List[tuple] = [
    ("phone_cn", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("idcard_cn", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("bankcard_cn", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
]

# 白名单：包含这些子串的文本不会被判定为敏感
DEFAULT_WHITELIST: Set[str] = {
    "test_", "example_", "demo_", "mock_",
    "hello", "world", "foo", "bar", "baz",
}


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class SafetyCheckResult:
    """安全检查结果。"""

    passed: bool
    reason: str = ""
    violated_rules: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SafetyGuard
# ---------------------------------------------------------------------------

class SafetyGuard:
    """安全护栏。

    职责：
    1. 拦截敏感 action（如 wechat_send）
    2. 检测文本中的 PII（手机号、身份证、银行卡号）
    3. 检测敏感关键词
    4. 提供可配置的规则集
    """

    def __init__(
        self,
        sensitive_actions: Optional[Set[str]] = None,
        sensitive_keywords: Optional[Set[str]] = None,
        pii_patterns: Optional[List[tuple]] = None,
        whitelist: Optional[Set[str]] = None,
    ):
        self.sensitive_actions = sensitive_actions or DEFAULT_SENSITIVE_ACTIONS.copy()
        self.sensitive_keywords = sensitive_keywords or DEFAULT_SENSITIVE_KEYWORDS.copy()
        self.pii_patterns = pii_patterns or DEFAULT_PII_PATTERNS.copy()
        self.whitelist = whitelist or DEFAULT_WHITELIST.copy()

    # ------------------------------------------------------------------
    # Action 拦截
    # ------------------------------------------------------------------

    def check_action(self, action: str) -> SafetyCheckResult:
        """检查 action 是否在敏感黑名单中。

        支持前缀匹配：email_* 会匹配 email_send、email_read 等。
        """
        if not action:
            return SafetyCheckResult(passed=False, reason="action is empty")

        # 精确匹配
        if action in self.sensitive_actions:
            logger.warning(f"[SafetyGuard] 敏感 action 被拦截: {action}")
            return SafetyCheckResult(
                passed=False,
                reason=f"Action '{action}' is in sensitive action blacklist",
                violated_rules=["sensitive_action"],
            )

        # 前缀匹配（如 email_*）
        for blocked in self.sensitive_actions:
            if blocked.endswith("_") and action.startswith(blocked):
                logger.warning(f"[SafetyGuard] 敏感 action 前缀被拦截: {action}")
                return SafetyCheckResult(
                    passed=False,
                    reason=f"Action '{action}' matches sensitive prefix '{blocked}'",
                    violated_rules=["sensitive_action_prefix"],
                )

        return SafetyCheckResult(passed=True)

    # ------------------------------------------------------------------
    # 文本检测
    # ------------------------------------------------------------------

    def check_text(self, text: str) -> SafetyCheckResult:
        """检查文本中是否包含 PII 或敏感关键词。

        先过白名单：如果文本包含白名单子串，跳过关键词检测（但仍检测 PII）。
        """
        if not text:
            return SafetyCheckResult(passed=True)

        violations: List[str] = []

        # PII 检测（白名单不免除 PII）
        for name, pattern in self.pii_patterns:
            if pattern.search(text):
                logger.warning(f"[SafetyGuard] 检测到 PII: {name}")
                violations.append(f"pii:{name}")

        # 敏感关键词检测（白名单可免除）
        if not self._is_whitelisted(text):
            lower = text.lower()
            for keyword in self.sensitive_keywords:
                if keyword.lower() in lower:
                    logger.warning(f"[SafetyGuard] 检测到敏感关键词: {keyword}")
                    violations.append(f"keyword:{keyword}")

        if violations:
            return SafetyCheckResult(
                passed=False,
                reason=f"Text contains sensitive content: {violations}",
                violated_rules=violations,
            )

        return SafetyCheckResult(passed=True)

    def _is_whitelisted(self, text: str) -> bool:
        """判断文本是否在白名单中。"""
        lower = text.lower()
        for w in self.whitelist:
            if w.lower() in lower:
                return True
        return False

    # ------------------------------------------------------------------
    # 批量检查（用于 Task）
    # ------------------------------------------------------------------

    def check_task(self, action: str, target: Optional[str] = None, value: Optional[str] = None) -> SafetyCheckResult:
        """对完整的 Task 进行安全检查。"""
        # Action 检查
        action_result = self.check_action(action)
        if not action_result.passed:
            return action_result

        # target / value 文本检查
        for field_name, field_value in [("target", target), ("value", value)]:
            if field_value:
                text_result = self.check_text(field_value)
                if not text_result.passed:
                    return SafetyCheckResult(
                        passed=False,
                        reason=f"[{field_name}] {text_result.reason}",
                        violated_rules=text_result.violated_rules,
                    )

        return SafetyCheckResult(passed=True)

    # ------------------------------------------------------------------
    # 未来扩展点（Owner 鲲鹏 要求的 WeChat 安全机制预留）
    # ------------------------------------------------------------------

    def confirm_recipient_identity(self, expected_contact: str, actual_contact: str) -> SafetyCheckResult:
        """收件人身份二次确认（预留接口）。

        未来 WeChat 操作时使用：比较预期联系人和实际检测到的联系人名称。
        """
        if expected_contact.strip() != actual_contact.strip():
            return SafetyCheckResult(
                passed=False,
                reason=f"Recipient mismatch: expected '{expected_contact}', got '{actual_contact}'",
                violated_rules=["recipient_mismatch"],
            )
        return SafetyCheckResult(passed=True)

    def privacy_warning(self, action: str, details: str) -> str:
        """生成隐私警告信息（预留接口）。

        未来 WeChat 操作前弹出确认对话框时使用。
        """
        return (
            f"【隐私警告】\n"
            f"即将执行敏感操作: {action}\n"
            f"详情: {details}\n"
            f"请确认收件人身份和操作内容无误后继续。"
        )
