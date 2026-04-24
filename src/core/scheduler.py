"""任务调度器

支持 interval / cron / at 三种调度模式，后台线程运行。

使用示例::

    from core.scheduler import TaskScheduler
    from core.batch_models import BatchTaskConfig

    config = BatchTaskConfig.from_json("batch.json")
    scheduler = TaskScheduler(config)

    # 每 3600 秒执行一次
    scheduler.start_interval(3600)

    # 或每天 9:00 执行
    scheduler.start_cron("0 9 * * *")

    # 停止
    scheduler.stop()
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from .batch_executor import BatchExecutor
from .batch_models import BatchTaskConfig, BatchReportGenerator
from ..utils.exceptions import ConfigError, ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """任务调度器"""

    def __init__(self, config: BatchTaskConfig, executor: Optional[BatchExecutor] = None):
        self.config = config
        self.executor = executor or BatchExecutor()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._run_count = 0
        self._last_result = None

    # ------------------------------------------------------------------
    # 启动接口
    # ------------------------------------------------------------------

    def start_interval(self, seconds: float):
        """按固定间隔启动调度（秒）。"""
        if self._running:
            raise RuntimeError("调度器已在运行，请先调用 stop()")
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop_interval, args=(seconds,), daemon=True
        )
        self._thread.start()
        self._running = True
        logger.info(f"调度器启动: 间隔模式, {seconds}s, 任务={self.config.name}")

    def start_cron(self, cron_expr: str):
        """按 cron 表达式启动调度。"""
        if self._running:
            raise RuntimeError("调度器已在运行，请先调用 stop()")
        try:
            from croniter import croniter
        except ImportError:
            raise ConfigError(
                "croniter 未安装，无法使用 cron 模式。运行: pip install croniter"
            )
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop_cron, args=(cron_expr,), daemon=True
        )
        self._thread.start()
        self._running = True
        logger.info(f"调度器启动: cron 模式, '{cron_expr}', 任务={self.config.name}")

    def run_once_at(self, target: datetime):
        """在指定时间执行一次（阻塞直到完成）。"""
        now = datetime.now()
        if target <= now:
            raise ValidationError(f"目标时间 {target} 已经过去")
        wait_seconds = (target - now).total_seconds()
        logger.info(f"单次任务将在 {target} 执行，等待 {wait_seconds:.0f}s")
        time.sleep(wait_seconds)
        self._execute_once()

    def run_once(self):
        """立即执行一次（阻塞直到完成）。"""
        self._execute_once()

    # ------------------------------------------------------------------
    # 停止
    # ------------------------------------------------------------------

    def stop(self):
        """停止调度器。"""
        if not self._running:
            return
        logger.info("调度器停止请求")
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._running = False
        logger.info("调度器已停止")

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def run_count(self) -> int:
        return self._run_count

    # ------------------------------------------------------------------
    # 内部循环
    # ------------------------------------------------------------------

    def _loop_interval(self, seconds: float):
        """固定间隔循环。"""
        while not self._stop_event.is_set():
            self._execute_once()
            # 分段 sleep 以便及时响应停止
            for _ in range(int(seconds)):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
            # 处理小数部分
            if not self._stop_event.is_set() and seconds % 1 > 0:
                time.sleep(seconds % 1)

    def _loop_cron(self, cron_expr: str):
        """cron 表达式循环。"""
        from croniter import croniter
        itr = croniter(cron_expr, datetime.now())
        while not self._stop_event.is_set():
            next_run: datetime = itr.get_next(datetime)
            wait = (next_run - datetime.now()).total_seconds()
            if wait > 0:
                logger.info(f"下次执行: {next_run}, 等待 {wait:.0f}s")
                # 分段 sleep
                slept = 0.0
                while slept < wait and not self._stop_event.is_set():
                    step = min(1.0, wait - slept)
                    time.sleep(step)
                    slept += step
            if self._stop_event.is_set():
                break
            self._execute_once()
            itr = croniter(cron_expr, datetime.now())

    def _execute_once(self):
        """执行一次批量任务。"""
        self._run_count += 1
        idx = self._run_count
        logger.info(f"第 {idx} 次执行开始")
        try:
            result = self.executor.run(self.config)
            self._last_result = result
            logger.info(
                f"第 {idx} 次执行完成: {result.success_count}/{result.total_count} 成功, "
                f"耗时 {result.duration:.2f}s"
            )
            # 保存报告
            try:
                report = BatchReportGenerator(result)
                path = report.save()
                logger.info(f"报告已保存: {path}")
            except Exception as e:
                logger.warning(f"报告保存失败: {e}")
        except Exception as e:
            logger.exception(f"第 {idx} 次执行异常")


# ----------------------------------------------------------------------
# CLI 辅助
# ----------------------------------------------------------------------

def run_scheduler_cli(config_path: str, mode: str, value: str, once: bool = False):
    """命令行入口，用于后台运行调度器。"""
    config = BatchTaskConfig.from_json(config_path)
    scheduler = TaskScheduler(config)

    if once:
        if mode == "at":
            target = datetime.fromisoformat(value)
            scheduler.run_once_at(target)
        else:
            scheduler.run_once()
        return

    if mode == "interval":
        seconds = float(value)
        scheduler.start_interval(seconds)
    elif mode == "cron":
        scheduler.start_cron(value)
    else:
        raise ValidationError(f"未知的调度模式: {mode}")

    # 守护：等待中断
    try:
        while scheduler.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        scheduler.stop()
