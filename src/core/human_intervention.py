"""人机协作介入模块

当两层模型（Minimax + Mimo）都失败时，弹出交互式弹窗让用户介入决策。
支持：继续（手动修复后）、跳过、重试、终止。
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class HumanDecision(Enum):
    """用户决策类型"""
    CONTINUE = "continue"      # 用户手动修复后继续
    SKIP = "skip"              # 跳过此步骤
    RETRY = "retry"            # 重试整个任务序列
    ABORT = "abort"            # 终止执行


@dataclass
class InterventionResult:
    """人机协作结果"""
    decision: HumanDecision
    user_notes: str = ""           # 用户备注/说明
    manual_target: str = ""        # 用户手动指定的 target
    screenshot_path: str = ""      # 保存的截图路径
    duration_ms: float = 0.0       # 用户思考时间


class HumanInterventionHandler:
    """人机协作处理器"""

    DEBUG_DIR = "debug/human_intervention"

    def __init__(self, debug_dir: Optional[str] = None):
        self.debug_dir = Path(debug_dir or self.DEBUG_DIR)
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self._tk_available = self._check_tkinter()

    def _check_tkinter(self) -> bool:
        """检查 tkinter 是否可用"""
        try:
            import tkinter as tk
            from tkinter import messagebox, simpledialog
            return True
        except ImportError:
            logger.warning("tkinter 不可用，人机协作将降级为日志记录模式")
            return False

    def intervene(
        self,
        task,
        screenshot: np.ndarray,
        failure_reason: str = "",
        sequence_name: str = "",
    ) -> InterventionResult:
        """
        触发人机协作介入。

        Args:
            task: 失败的任务
            screenshot: 失败时的屏幕截图
            failure_reason: 失败原因说明
            sequence_name: 任务序列名称

        Returns:
            InterventionResult
        """
        start_time = time.time()

        # 保存截图
        timestamp = int(time.time())
        screenshot_path = self.debug_dir / f"{sequence_name}_{task.action}_{timestamp}.png"
        try:
            Image.fromarray(screenshot).save(screenshot_path)
        except Exception as e:
            logger.warning(f"保存截图失败: {e}")
            screenshot_path = Path("")

        if self._tk_available:
            decision, notes, manual_target = self._show_dialog(
                task=task,
                screenshot_path=str(screenshot_path),
                failure_reason=failure_reason,
            )
        else:
            # tkinter 不可用，降级为日志模式
            decision = self._fallback_console_mode(task, failure_reason)
            notes = ""
            manual_target = ""

        duration = (time.time() - start_time) * 1000

        result = InterventionResult(
            decision=decision,
            user_notes=notes,
            manual_target=manual_target,
            screenshot_path=str(screenshot_path),
            duration_ms=duration,
        )

        logger.info(
            f"人机协作决策: {decision.value}, "
            f"截图: {screenshot_path}, "
            f"耗时: {duration:.0f}ms"
        )
        return result

    def _show_dialog(
        self,
        task,
        screenshot_path: str,
        failure_reason: str,
    ) -> Tuple[HumanDecision, str, str]:
        """显示 tkinter 弹窗，返回用户决策"""
        import tkinter as tk
        from tkinter import ttk

        result_decision = HumanDecision.ABORT
        result_notes = ""
        result_target = ""

        def on_continue():
            nonlocal result_decision
            result_decision = HumanDecision.CONTINUE
            root.destroy()

        def on_skip():
            nonlocal result_decision
            result_decision = HumanDecision.SKIP
            root.destroy()

        def on_retry():
            nonlocal result_decision
            result_decision = HumanDecision.RETRY
            root.destroy()

        def on_abort():
            nonlocal result_decision
            result_decision = HumanDecision.ABORT
            root.destroy()

        root = tk.Tk()
        root.title("OpenClaw - 自动化遇到困难")
        root.geometry("600x500")
        root.attributes("-topmost", True)
        root.lift()

        # 主容器
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 任务信息
        ttk.Label(
            main_frame,
            text=f"任务序列: {task.action}(target={getattr(task, 'target', '')})",
            font=("Microsoft YaHei", 12, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(
            main_frame,
            text=f"失败原因: {failure_reason}",
            font=("Microsoft YaHei", 10),
            foreground="red",
        ).pack(anchor=tk.W, pady=(0, 10))

        # 截图显示
        try:
            from PIL import ImageTk
            img = Image.open(screenshot_path)
            # 缩放到合适大小
            img.thumbnail((560, 280), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = ttk.Label(main_frame, image=photo)
            img_label.image = photo  # 保持引用
            img_label.pack(pady=(0, 10))
        except Exception as e:
            ttk.Label(main_frame, text=f"[无法显示截图: {e}]").pack()

        # 手动输入 target（可选）
        ttk.Label(main_frame, text="手动指定目标（可选）:").pack(anchor=tk.W)
        target_entry = ttk.Entry(main_frame, width=60)
        target_entry.pack(fill=tk.X, pady=(0, 10))

        # 备注
        ttk.Label(main_frame, text="备注:").pack(anchor=tk.W)
        notes_entry = tk.Text(main_frame, height=3, width=60)
        notes_entry.pack(fill=tk.X, pady=(0, 10))

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="手动修复后继续", command=on_continue).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="跳过此步骤", command=on_skip).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重试任务", command=on_retry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="终止执行", command=on_abort).pack(side=tk.LEFT, padx=5)

        # 提示文字
        ttk.Label(
            main_frame,
            text="提示: 如果选择'手动修复后继续'，请先在屏幕上完成操作，然后点击按钮",
            font=("Microsoft YaHei", 9),
            foreground="gray",
        ).pack(anchor=tk.W, pady=(10, 0))

        root.mainloop()

        result_target = target_entry.get() if 'target_entry' in dir() else ""
        result_notes = notes_entry.get("1.0", tk.END).strip() if 'notes_entry' in dir() else ""

        return result_decision, result_notes, result_target

    def _fallback_console_mode(self, task, failure_reason: str) -> HumanDecision:
        """tkinter 不可用时，降级为控制台交互"""
        print("\n" + "=" * 60)
        print("[OpenClaw] 自动化遇到困难，需要人工介入")
        print(f"任务: {task.action}(target={getattr(task, 'target', '')})")
        print(f"失败原因: {failure_reason}")
        print("=" * 60)
        print("选项:")
        print("  1. continue - 我在屏幕上手动修复了，继续执行")
        print("  2. skip     - 跳过此步骤")
        print("  3. retry    - 重试整个任务")
        print("  4. abort    - 终止执行")
        print("=" * 60)

        choice = input("请选择 [1/2/3/4]: ").strip().lower()
        mapping = {
            "1": HumanDecision.CONTINUE,
            "continue": HumanDecision.CONTINUE,
            "2": HumanDecision.SKIP,
            "skip": HumanDecision.SKIP,
            "3": HumanDecision.RETRY,
            "retry": HumanDecision.RETRY,
            "4": HumanDecision.ABORT,
            "abort": HumanDecision.ABORT,
        }
        return mapping.get(choice, HumanDecision.ABORT)
