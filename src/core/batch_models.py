"""批量任务数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import ExecutionResult


class ExecutionMode(Enum):
    """批量执行模式"""
    SEQUENTIAL = "sequential"   # 顺序执行
    PARALLEL = "parallel"       # 并行执行


class ReportFormat(Enum):
    """报告输出格式"""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


@dataclass
class BatchTaskItem:
    """批量任务中的一个任务项"""
    task_name: str                      # 预定义任务名或任务文件路径
    params: Dict[str, Any] = field(default_factory=dict)   # 任务参数
    label: Optional[str] = None         # 自定义标签（用于报告）
    enabled: bool = True                # 是否启用
    retries: int = 0                    # 独立重试次数（覆盖默认值）

    def to_dict(self) -> Dict:
        return {
            "task_name": self.task_name,
            "params": self.params,
            "label": self.label,
            "enabled": self.enabled,
            "retries": self.retries,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BatchTaskItem":
        return cls(
            task_name=data["task_name"],
            params=data.get("params", {}),
            label=data.get("label"),
            enabled=data.get("enabled", True),
            retries=data.get("retries", 0),
        )


@dataclass
class BatchTaskConfig:
    """批量任务配置"""
    name: str
    items: List[BatchTaskItem]
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_workers: int = 4                # 并行模式下的最大线程数
    stop_on_error: bool = False         # 出错时是否停止后续任务
    report_format: ReportFormat = ReportFormat.MARKDOWN
    report_dir: str = "reports"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "mode": self.mode.value,
            "max_workers": self.max_workers,
            "stop_on_error": self.stop_on_error,
            "report_format": self.report_format.value,
            "report_dir": self.report_dir,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BatchTaskConfig":
        return cls(
            name=data["name"],
            items=[BatchTaskItem.from_dict(i) for i in data.get("items", [])],
            mode=ExecutionMode(data.get("mode", "sequential")),
            max_workers=data.get("max_workers", 4),
            stop_on_error=data.get("stop_on_error", False),
            report_format=ReportFormat(data.get("report_format", "markdown")),
            report_dir=data.get("report_dir", "reports"),
        )

    @classmethod
    def from_json(cls, filepath: str) -> "BatchTaskConfig":
        import json
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


@dataclass
class BatchItemResult:
    """单个批量任务的执行结果"""
    item: BatchTaskItem
    result: ExecutionResult
    started_at: datetime
    finished_at: datetime

    @property
    def duration(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def label(self) -> str:
        return self.item.label or self.item.task_name

    def to_dict(self) -> Dict:
        return {
            "label": self.label,
            "task_name": self.item.task_name,
            "success": self.result.success,
            "duration": self.duration,
            "completed_steps": self.result.completed_steps,
            "error": self.result.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
        }


@dataclass
class BatchTaskResult:
    """批量任务整体执行结果"""
    config: BatchTaskConfig
    items: List[BatchItemResult]
    started_at: datetime
    finished_at: datetime

    @property
    def duration(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def total_count(self) -> int:
        return len(self.items)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.items if r.result.success)

    @property
    def failed_count(self) -> int:
        return self.total_count - self.success_count

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    def to_dict(self) -> Dict:
        return {
            "config_name": self.config.name,
            "mode": self.config.mode.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "duration": self.duration,
            "total": self.total_count,
            "success": self.success_count,
            "failed": self.failed_count,
            "success_rate": round(self.success_rate, 4),
            "items": [item.to_dict() for item in self.items],
        }


class BatchReportGenerator:
    """批量任务报告生成器"""

    def __init__(self, result: BatchTaskResult):
        self.result = result

    def generate(self, fmt: ReportFormat) -> str:
        if fmt == ReportFormat.JSON:
            return self._generate_json()
        elif fmt == ReportFormat.MARKDOWN:
            return self._generate_markdown()
        elif fmt == ReportFormat.HTML:
            return self._generate_html()
        else:
            return self._generate_markdown()

    def _generate_json(self) -> str:
        import json
        return json.dumps(self.result.to_dict(), ensure_ascii=False, indent=2)

    def _generate_markdown(self) -> str:
        r = self.result
        lines = [
            f"# 批量任务报告: {r.config.name}",
            "",
            f"- **执行模式**: {r.config.mode.value}",
            f"- **开始时间**: {r.started_at:%Y-%m-%d %H:%M:%S}",
            f"- **结束时间**: {r.finished_at:%Y-%m-%d %H:%M:%S}",
            f"- **总耗时**: {r.duration:.2f}s",
            f"- **任务总数**: {r.total_count}",
            f"- **成功**: {r.success_count}",
            f"- **失败**: {r.failed_count}",
            f"- **成功率**: {r.success_rate * 100:.1f}%",
            "",
            "## 详细结果",
            "",
            "| # | 标签 | 任务 | 结果 | 耗时 | 步骤 | 错误 |",
            "|---|------|------|------|------|------|------|",
        ]
        for i, item in enumerate(r.items, 1):
            status = "✅ 成功" if item.result.success else "❌ 失败"
            error = item.result.error or ""
            if error:
                error = error.replace("|", "\\|").replace("\n", " ")
                error = error[:60] + "..." if len(error) > 60 else error
            lines.append(
                f"| {i} | {item.label} | {item.item.task_name} | {status} | "
                f"{item.duration:.2f}s | {item.result.completed_steps} | {error} |"
            )
        lines.append("")
        return "\n".join(lines)

    def _generate_html(self) -> str:
        r = self.result
        rows = ""
        for i, item in enumerate(r.items, 1):
            status_class = "success" if item.result.success else "fail"
            status_text = "成功" if item.result.success else "失败"
            error = item.result.error or ""
            error = error[:100] + "..." if len(error) > 100 else error
            rows += (
                f'<tr class="{status_class}">'
                f'<td>{i}</td>'
                f'<td>{item.label}</td>'
                f'<td>{item.item.task_name}</td>'
                f'<td><span class="badge {status_class}">{status_text}</span></td>'
                f'<td>{item.duration:.2f}s</td>'
                f'<td>{item.result.completed_steps}</td>'
                f'<td><pre>{error}</pre></td>'
                f'</tr>'
            )

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>批量任务报告 - {r.config.name}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 16px 0; }}
        .summary p {{ margin: 4px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #fafafa; }}
        .success {{ color: #2e7d32; }}
        .fail {{ color: #c62828; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
        .badge.success {{ background: #e8f5e9; }}
        .badge.fail {{ background: #ffebee; }}
        pre {{ margin: 0; font-size: 12px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>📊 批量任务报告: {r.config.name}</h1>
    <div class="summary">
        <p><strong>执行模式:</strong> {r.config.mode.value}</p>
        <p><strong>开始时间:</strong> {r.started_at:%Y-%m-%d %H:%M:%S}</p>
        <p><strong>结束时间:</strong> {r.finished_at:%Y-%m-%d %H:%M:%S}</p>
        <p><strong>总耗时:</strong> {r.duration:.2f}s</p>
        <p><strong>成功率:</strong> {r.success_count}/{r.total_count} ({r.success_rate * 100:.1f}%)</p>
    </div>
    <table>
        <tr><th>#</th><th>标签</th><th>任务</th><th>结果</th><th>耗时</th><th>步骤</th><th>错误</th></tr>
        {rows}
    </table>
</body>
</html>
""".strip()

    def save(self, filepath: Optional[str] = None) -> str:
        """生成并保存报告，返回保存路径"""
        if filepath is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = self.result.config.report_format.value
            filepath = str(Path(self.result.config.report_dir) / f"batch_{self.result.config.name}_{ts}.{ext}")
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        content = self.generate(self.result.config.report_format)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
