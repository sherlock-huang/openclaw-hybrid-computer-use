"""GUI 任务编辑器

基于 tkinter 的可视化任务编排工具，支持：
- 浏览和搜索预定义任务
- 拖拽/点击添加任务到序列
- 编辑任务参数
- 保存/加载任务序列 JSON
- 执行并实时监控进度

使用示例::

    python -m src.gui.task_editor
"""

import json
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

# 将项目根目录加入路径
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from core.executor import TaskExecutor
from core.models import Task, TaskSequence
from core.tasks_predefined import list_predefined_tasks, create_predefined_task
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskEditorApp:
    """任务编辑器主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenClaw 任务编辑器")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)

        # 数据
        self.sequence: List[Dict[str, Any]] = []  # 当前任务序列（字典列表）
        self.predefined_tasks: List[Dict[str, Any]] = []
        self.selected_sequence_index: Optional[int] = None
        self.executor = TaskExecutor()
        self._exec_thread: Optional[threading.Thread] = None
        self._queue: queue.Queue = queue.Queue()

        # 样式
        self._setup_styles()
        # UI
        self._build_ui()
        # 加载预定义任务
        self._load_predefined_tasks()
        # 定时处理后台消息
        self._poll_queue()

    # ------------------------------------------------------------------
    # 样式
    # ------------------------------------------------------------------

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Microsoft YaHei", 12, "bold"))
        style.configure("Header.TLabel", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Action.TButton", font=("Microsoft YaHei", 9))

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self):
        # 主框架，左右三栏
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ---- 左栏：预定义任务列表 ----
        left = ttk.Frame(main, width=280)
        main.add(left, weight=1)

        ttk.Label(left, text="预定义任务", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 4))

        self.task_search_var = tk.StringVar()
        self.task_search_var.trace_add("write", self._on_search_change)
        ttk.Entry(left, textvariable=self.task_search_var).pack(fill=tk.X, pady=(0, 4))

        # 任务列表 Treeview
        cols = ("name", "desc")
        self.task_tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
        self.task_tree.heading("name", text="任务名")
        self.task_tree.heading("desc", text="描述")
        self.task_tree.column("name", width=100)
        self.task_tree.column("desc", width=140)
        self.task_tree.pack(fill=tk.BOTH, expand=True)
        self.task_tree.bind("<Double-1>", self._on_task_double_click)

        ttk.Button(left, text="添加到序列", command=self._on_add_selected_task).pack(fill=tk.X, pady=(4, 0))

        # ---- 中栏：任务序列编辑 ----
        center = ttk.Frame(main, width=500)
        main.add(center, weight=3)

        ttk.Label(center, text="任务序列", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 4))

        # 序列表格
        seq_cols = ("#", "action", "target", "value", "delay")
        self.seq_tree = ttk.Treeview(center, columns=seq_cols, show="headings", height=18)
        self.seq_tree.heading("#", text="#")
        self.seq_tree.heading("action", text="Action")
        self.seq_tree.heading("target", text="Target")
        self.seq_tree.heading("value", text="Value")
        self.seq_tree.heading("delay", text="Delay")
        self.seq_tree.column("#", width=30, anchor=tk.CENTER)
        self.seq_tree.column("action", width=100)
        self.seq_tree.column("target", width=120)
        self.seq_tree.column("value", width=120)
        self.seq_tree.column("delay", width=50, anchor=tk.CENTER)
        self.seq_tree.pack(fill=tk.BOTH, expand=True)
        self.seq_tree.bind("<<TreeviewSelect>>", self._on_sequence_select)

        # 序列操作按钮
        btn_row = ttk.Frame(center)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="上移", command=self._move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="下移", command=self._move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="删除", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="清空", command=self._clear_sequence).pack(side=tk.LEFT, padx=2)

        # ---- 右栏：参数编辑 ----
        right = ttk.Frame(main, width=320)
        main.add(right, weight=2)

        ttk.Label(right, text="任务参数", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 4))

        self.param_frame = ttk.LabelFrame(right, text="选中任务")
        self.param_frame.pack(fill=tk.BOTH, expand=True)

        # Action
        ttk.Label(self.param_frame, text="Action:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)
        self.var_action = tk.StringVar()
        ttk.Combobox(self.param_frame, textvariable=self.var_action,
                     values=["click", "type", "press", "hotkey", "launch", "wait",
                             "browser_launch", "browser_goto", "browser_click",
                             "browser_type", "screenshot", "wechat_send",
                             "excel_create", "excel_write_cell", "word_create"],
                     state="readonly", width=20).grid(row=0, column=1, sticky=tk.EW, padx=4, pady=2)

        # Target
        ttk.Label(self.param_frame, text="Target:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=2)
        self.var_target = tk.StringVar()
        ttk.Entry(self.param_frame, textvariable=self.var_target, width=24).grid(row=1, column=1, sticky=tk.EW, padx=4, pady=2)

        # Value
        ttk.Label(self.param_frame, text="Value:").grid(row=2, column=0, sticky=tk.W, padx=4, pady=2)
        self.var_value = tk.StringVar()
        ttk.Entry(self.param_frame, textvariable=self.var_value, width=24).grid(row=2, column=1, sticky=tk.EW, padx=4, pady=2)

        # Delay
        ttk.Label(self.param_frame, text="Delay(s):").grid(row=3, column=0, sticky=tk.W, padx=4, pady=2)
        self.var_delay = tk.DoubleVar(value=1.0)
        ttk.Spinbox(self.param_frame, from_=0, to=60, increment=0.5,
                    textvariable=self.var_delay, width=10).grid(row=3, column=1, sticky=tk.W, padx=4, pady=2)

        # 预定义任务参数（JSON）
        ttk.Label(self.param_frame, text="预定义参数(JSON):").grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=4, pady=(8, 2))
        self.txt_params = tk.Text(self.param_frame, height=6, width=28, wrap=tk.WORD)
        self.txt_params.grid(row=5, column=0, columnspan=2, sticky=tk.EW, padx=4, pady=2)

        ttk.Button(self.param_frame, text="应用修改", command=self._apply_params).grid(row=6, column=0, columnspan=2, pady=(4, 0))

        self.param_frame.columnconfigure(1, weight=1)

        # ---- 中部：日志与截图 Notebook ----
        mid = ttk.Frame(self.root)
        mid.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 4))

        self.notebook = ttk.Notebook(mid)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 日志页
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="执行日志")
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(fill=tk.Y, side=tk.RIGHT)
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 截图页
        shot_frame = ttk.Frame(self.notebook)
        self.notebook.add(shot_frame, text="截图预览")
        self.shot_label = ttk.Label(shot_frame, text="暂无截图")
        self.shot_label.pack(expand=True)

        # ---- 底部工具栏 ----
        bottom = ttk.Frame(self.root)
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 8))

        ttk.Separator(bottom, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 4))

        toolbar = ttk.Frame(bottom)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="加载 JSON", command=self._load_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存 JSON", command=self._save_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="执行序列", command=self._execute).pack(side=tk.LEFT, padx=(16, 2))
        ttk.Button(toolbar, text="停止", command=self._stop).pack(side=tk.LEFT, padx=2)

        self.progress = ttk.Progressbar(toolbar, mode="determinate", length=150)
        self.progress.pack(side=tk.LEFT, padx=(16, 4))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.LEFT, padx=4)

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def _load_predefined_tasks(self):
        try:
            self.predefined_tasks = list_predefined_tasks()
        except Exception as e:
            logger.error(f"加载预定义任务失败: {e}")
            self.predefined_tasks = []
        self._refresh_task_list()

    def _refresh_task_list(self):
        """根据搜索条件刷新任务列表"""
        query = self.task_search_var.get().lower()
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        for task in self.predefined_tasks:
            name = task.get("name", "")
            desc = task.get("description", "")
            if not query or query in name.lower() or query in desc.lower():
                self.task_tree.insert("", tk.END, values=(name, desc))

    def _on_search_change(self, *_):
        self._refresh_task_list()

    # ------------------------------------------------------------------
    # 任务序列操作
    # ------------------------------------------------------------------

    def _on_task_double_click(self, _event=None):
        self._on_add_selected_task()

    def _on_add_selected_task(self):
        sel = self.task_tree.selection()
        if not sel:
            return
        item = self.task_tree.item(sel[0])
        name = item["values"][0]
        self.sequence.append({
            "_type": "predefined",
            "_name": name,
            "action": "predefined",
            "target": name,
            "value": "",
            "delay": 1.0,
            "params": {},
        })
        self._refresh_sequence()
        self.status_var.set(f"已添加预定义任务: {name}")

    def _add_custom_task(self, action: str, target: str = "", value: str = "", delay: float = 1.0):
        self.sequence.append({
            "_type": "custom",
            "action": action,
            "target": target,
            "value": value,
            "delay": delay,
        })
        self._refresh_sequence()

    def _refresh_sequence(self):
        for item in self.seq_tree.get_children():
            self.seq_tree.delete(item)
        for i, task in enumerate(self.sequence, 1):
            self.seq_tree.insert(
                "", tk.END, iid=str(i - 1),
                values=(i, task.get("action", ""), task.get("target", ""),
                        task.get("value", ""), task.get("delay", 1.0))
            )

    def _on_sequence_select(self, _event=None):
        sel = self.seq_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.selected_sequence_index = idx
        task = self.sequence[idx]

        self.var_action.set(task.get("action", ""))
        self.var_target.set(task.get("target", ""))
        self.var_value.set(str(task.get("value", "")))
        self.var_delay.set(task.get("delay", 1.0))

        params = task.get("params", {})
        self.txt_params.delete("1.0", tk.END)
        if params:
            self.txt_params.insert(tk.END, json.dumps(params, ensure_ascii=False, indent=2))
        else:
            self.txt_params.insert(tk.END, "{}")

    def _apply_params(self):
        if self.selected_sequence_index is None:
            return
        idx = self.selected_sequence_index
        self.sequence[idx]["action"] = self.var_action.get()
        self.sequence[idx]["target"] = self.var_target.get()
        self.sequence[idx]["value"] = self.var_value.get()
        self.sequence[idx]["delay"] = self.var_delay.get()

        # 解析 JSON 参数
        try:
            text = self.txt_params.get("1.0", tk.END).strip()
            if text and text != "{}":
                self.sequence[idx]["params"] = json.loads(text)
            else:
                self.sequence[idx]["params"] = {}
        except json.JSONDecodeError as e:
            messagebox.showerror("参数错误", f"JSON 解析失败: {e}")
            return

        self._refresh_sequence()
        self.status_var.set(f"已更新任务 #{idx + 1}")

    def _move_up(self):
        sel = self.seq_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx > 0:
            self.sequence[idx], self.sequence[idx - 1] = self.sequence[idx - 1], self.sequence[idx]
            self._refresh_sequence()
            self.seq_tree.selection_set(str(idx - 1))

    def _move_down(self):
        sel = self.seq_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < len(self.sequence) - 1:
            self.sequence[idx], self.sequence[idx + 1] = self.sequence[idx + 1], self.sequence[idx]
            self._refresh_sequence()
            self.seq_tree.selection_set(str(idx + 1))

    def _delete_selected(self):
        sel = self.seq_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        del self.sequence[idx]
        self._refresh_sequence()
        self.selected_sequence_index = None

    def _clear_sequence(self):
        if messagebox.askyesno("确认", "确定要清空当前任务序列吗？"):
            self.sequence.clear()
            self._refresh_sequence()
            self.selected_sequence_index = None

    # ------------------------------------------------------------------
    # 保存 / 加载
    # ------------------------------------------------------------------

    def _save_json(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(_PROJECT_ROOT / "examples"),
        )
        if not path:
            return
        data = {
            "name": "gui_sequence",
            "tasks": [
                {
                    "action": t.get("action", ""),
                    "target": t.get("target", ""),
                    "value": t.get("value", ""),
                    "delay": t.get("delay", 1.0),
                }
                for t in self.sequence
            ],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.status_var.set(f"已保存: {path}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _load_json(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(_PROJECT_ROOT / "examples"),
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sequence.clear()
            for t in data.get("tasks", []):
                self.sequence.append({
                    "_type": "custom",
                    "action": t.get("action", ""),
                    "target": t.get("target", ""),
                    "value": t.get("value", ""),
                    "delay": t.get("delay", 1.0),
                    "params": t.get("params", {}),
                })
            self._refresh_sequence()
            self.status_var.set(f"已加载: {path}")
        except Exception as e:
            messagebox.showerror("加载失败", str(e))

    # ------------------------------------------------------------------
    # 执行
    # ------------------------------------------------------------------

    def _execute(self):
        if not self.sequence:
            messagebox.showwarning("提示", "任务序列为空")
            return
        if self._exec_thread and self._exec_thread.is_alive():
            messagebox.showwarning("提示", "已有任务正在执行")
            return

        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.shot_label.config(image="", text="暂无截图")

        self.progress["maximum"] = len(self.sequence)
        self.progress["value"] = 0
        self.status_var.set("执行中...")

        self._exec_thread = threading.Thread(target=self._run_sequence, daemon=True)
        self._exec_thread.start()

    def _run_sequence(self):
        """在后台线程中执行任务序列"""
        try:
            self._queue.put(("log", "正在解析任务序列..."))
            tasks = []
            for step in self.sequence:
                if step.get("_type") == "predefined":
                    name = step.get("_name", "")
                    params = step.get("params", {})
                    try:
                        seq = create_predefined_task(name, **params)
                        tasks.extend(seq.tasks)
                        self._queue.put(("log", f"解析预定义任务: {name} ({len(seq.tasks)} 步)"))
                    except Exception as e:
                        self._queue.put(("error", f"预定义任务 '{name}' 创建失败: {e}"))
                        return
                else:
                    tasks.append(Task(
                        action=step.get("action", ""),
                        target=step.get("target") or None,
                        value=step.get("value") or None,
                        delay=step.get("delay", 1.0),
                    ))

            sequence = TaskSequence(name="gui_sequence", tasks=tasks)
            self._queue.put(("start", len(tasks)))
            self._queue.put(("log", f"开始执行序列，共 {len(tasks)} 步"))

            result = self.executor.execute_sequence(sequence)

            # 发送最后一张截图（如果有）
            if result.screenshots:
                try:
                    from PIL import Image
                    last_shot = result.screenshots[-1]
                    pil_img = Image.fromarray(last_shot)
                    self._queue.put(("screenshot", pil_img))
                    self._queue.put(("log", f"捕获 {len(result.screenshots)} 张截图"))
                except Exception as e:
                    logger.warning(f"截图转换失败: {e}")

            if result.success:
                self._queue.put(("done", f"执行成功，完成 {result.completed_steps} 步，耗时 {result.duration:.2f}s"))
            else:
                self._queue.put(("done", f"执行失败: {result.error or '未知错误'}"))

        except Exception as e:
            logger.exception("GUI 执行任务异常")
            self._queue.put(("error", str(e)))

    def _stop(self):
        # 当前执行器没有提供中断机制，这里仅作 UI 反馈
        self.status_var.set("停止请求已发送（当前版本执行完成后才会停止）")

    def _log(self, message: str, tag: str = "info"):
        """向日志面板追加消息（线程安全，通过主线程调用）。"""
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _show_screenshot(self, image):
        """在截图预览页显示 PIL Image（线程安全）。"""
        try:
            from PIL import Image, ImageTk
            # 缩放到合适尺寸
            w, h = image.size
            max_w, max_h = 600, 400
            if w > max_w or h > max_h:
                ratio = min(max_w / w, max_h / h)
                image = image.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.shot_label.config(image=photo, text="")
            self.shot_label.image = photo  # 保持引用
            self.notebook.select(1)  # 切换到截图页
        except Exception as e:
            logger.warning(f"截图预览失败: {e}")

    def _poll_queue(self):
        """定时从后台线程读取消息并更新 UI"""
        try:
            while True:
                msg = self._queue.get_nowait()
                kind, data = msg
                if kind == "start":
                    self.progress["maximum"] = data
                    self._log(f"开始执行，共 {data} 个任务步骤")
                elif kind == "step":
                    self.progress["value"] = data
                elif kind == "log":
                    self._log(data)
                elif kind == "screenshot":
                    self._show_screenshot(data)
                elif kind == "done":
                    self.status_var.set(data)
                    self.progress["value"] = self.progress["maximum"]
                    self._log(data)
                elif kind == "error":
                    self.status_var.set(f"错误: {data}")
                    self._log(f"错误: {data}", tag="error")
                    messagebox.showerror("执行错误", data)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    # 入口
    # ------------------------------------------------------------------

    def run(self):
        self.root.mainloop()


def main():
    app = TaskEditorApp()
    app.run()


if __name__ == "__main__":
    main()
