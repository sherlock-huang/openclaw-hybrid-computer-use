"""录制状态悬浮窗

所有 tkinter 操作在单一后台线程中执行，彻底消除跨线程警告。
"""

import queue
import threading
import time
import tkinter as tk
from typing import Optional


class RecordingOverlay:
    """录制状态悬浮窗"""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._cmd_queue: queue.Queue = queue.Queue()
        self._is_running = False

    def show(self):
        """显示录制指示器"""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._run_ui, daemon=True)
        self._thread.start()

    def _run_ui(self):
        """在后台线程中创建并运行 UI（tkinter 唯一合法线程）。"""
        root = tk.Tk()
        root.overrideredirect(True)   # 无边框
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.8)

        screen_width = root.winfo_screenwidth()
        root.geometry(f"150x50+{screen_width - 160}+10")

        frame = tk.Frame(root, bg="red", padx=10, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            frame,
            text="● REC 00:00",
            fg="white",
            bg="red",
            font=("Arial", 12, "bold"),
        )
        label.pack()

        start_time = time.time()
        is_recording = True

        def update_timer():
            if is_recording and root.winfo_exists():
                elapsed = int(time.time() - start_time)
                minutes = elapsed // 60
                seconds = elapsed % 60
                label.config(text=f"● REC {minutes:02d}:{seconds:02d}")
                root.after(1000, update_timer)

        def poll_queue():
            """轮询主线程指令。"""
            nonlocal is_recording
            try:
                while True:
                    cmd = self._cmd_queue.get_nowait()
                    if cmd == "hide":
                        is_recording = False
                        if root.winfo_exists():
                            root.destroy()
                        return
            except queue.Empty:
                pass
            if root.winfo_exists():
                root.after(100, poll_queue)

        update_timer()
        poll_queue()
        root.mainloop()
        self._is_running = False

    def hide(self):
        """隐藏录制指示器（线程安全）。"""
        self._cmd_queue.put("hide")
