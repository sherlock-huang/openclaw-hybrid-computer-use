"""
微信发送审计日志器

记录每次发送的完整决策路径，便于事后追责和故障分析。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from dataclasses import asdict

logger = logging.getLogger(__name__)


class WeChatAuditLogger:
    """微信发送审计日志器"""
    
    LOG_DIR = Path("logs")
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._ensure_dir()
        self._current_log_file = self._log_file_path()
        self._decisions: List[Dict[str, Any]] = []
    
    def _ensure_dir(self):
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    def _log_file_path(self) -> Path:
        date_str = datetime.now().strftime("%Y%m%d")
        return self.LOG_DIR / f"wechat_audit_{date_str}.log"
    
    def reset_decisions(self):
        """重置当前决策链"""
        self._decisions = []
    
    def log_decision(self, step: str, result: str, details: Optional[Dict] = None):
        """记录一个决策步骤"""
        entry = {
            "time": datetime.now().isoformat(),
            "step": step,
            "result": result,
        }
        if details:
            # 过滤掉不可序列化的对象
            clean_details = {}
            for k, v in details.items():
                if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                    clean_details[k] = v
                else:
                    clean_details[k] = str(v)
            entry["details"] = clean_details
        self._decisions.append(entry)
    
    def log_attempt(self, contact: str, message: str, safety_level: str, dry_run: bool):
        """记录一次发送尝试的开始"""
        self.reset_decisions()
        entry = {
            "time": datetime.now().isoformat(),
            "event": "attempt",
            "contact": contact,
            "message": message,
            "safety_level": safety_level,
            "dry_run": dry_run,
        }
        self._append_line(entry)
    
    def log_result(self, success: bool, error: str, step_reached: str,
                   warnings: List[str], screenshot_path: Optional[str] = None):
        """记录一次发送尝试的结果"""
        entry = {
            "time": datetime.now().isoformat(),
            "event": "result",
            "success": success,
            "error": error,
            "step_reached": step_reached,
            "warnings": warnings,
            "screenshot_path": screenshot_path,
            "decisions": self._decisions,
        }
        self._append_line(entry)
    
    def _append_line(self, entry: Dict):
        """追加一行 JSON 到日志文件"""
        try:
            with open(self._log_file_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.warning(f"审计日志写入失败: {e}")
