"""录制状态悬浮窗"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional


class RecordingOverlay:
    """录制状态悬浮窗"""
    
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.is_recording = False
        self.elapsed_time = 0
        self.start_time: Optional[float] = None
        self._thread: Optional[threading.Thread] = None
        self.label: Optional[tk.Label] = None
    
    def show(self):
        """显示录制指示器"""
        if self.root is not None:
            return  # 已经在显示
        
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-alpha', 0.8)  # 半透明
        
        # 定位到屏幕右上角
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"150x50+{screen_width-160}+10")
        
        # 红色背景框架
        frame = tk.Frame(self.root, bg='red', padx=10, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # REC 文字 + 计时器
        self.label = tk.Label(
            frame, 
            text="● REC 00:00", 
            fg='white', 
            bg='red',
            font=('Arial', 12, 'bold')
        )
        self.label.pack()
        
        self.is_recording = True
        self.start_time = time.time()
        
        # 在新线程运行 UI (避免阻塞主线程)
        self._thread = threading.Thread(target=self._run_ui)
        self._thread.daemon = True
        self._thread.start()
    
    def _run_ui(self):
        """运行 UI 主循环"""
        self._update_timer()
        self.root.mainloop()
    
    def _update_timer(self):
        """更新计时器"""
        if self.is_recording and self.root and self.label:
            elapsed = int(time.time() - self.start_time)
            self.elapsed_time = elapsed
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.label.config(text=f"● REC {minutes:02d}:{seconds:02d}")
            
            # 每秒更新一次
            if self.root:
                self.root.after(1000, self._update_timer)
    
    def hide(self):
        """隐藏录制指示器"""
        self.is_recording = False
        if self.root:
            try:
                self.root.destroy()
            except tk.TclError:
                pass  # 窗口可能已经关闭
            self.root = None
            self.label = None
