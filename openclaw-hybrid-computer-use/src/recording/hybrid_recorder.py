"""混合录制器 - 自动检测并录制桌面或浏览器操作"""

import time
import logging
from typing import Optional, List
from datetime import datetime

from pynput import mouse, keyboard

from ..core.models import RecordingEvent, RecordingSession, RecordingMode
from ..utils.recording_overlay import RecordingOverlay
from ..perception.screen import ScreenCapture
from ..perception.detector import ElementDetector
from .window_detector import get_current_recording_mode
from .browser_recorder import BrowserRecorder

logger = logging.getLogger(__name__)


class HybridRecorder:
    """混合录制器"""
    
    def __init__(self, mode: RecordingMode = RecordingMode.HYBRID, 
                 user_data_dir: str = "browser_data"):
        self.mode = mode
        self.user_data_dir = user_data_dir
        
        self.is_recording = False
        self._session_name: Optional[str] = None
        self._start_time: Optional[float] = None
        self._events: List[RecordingEvent] = []
        
        self._overlay = RecordingOverlay()
        self._mouse_listener = None
        self._keyboard_listener = None
        self._browser_recorder: Optional[BrowserRecorder] = None
        
        self._input_buffer = ""
        self._last_input_time = 0.0
        
        logger.info(f"HybridRecorder 初始化: mode={mode.value}")
    
    def start_recording(self, name: Optional[str] = None):
        if self.is_recording:
            raise RuntimeError("已经在录制中")
        
        self.is_recording = True
        self._session_name = name or f"录制任务 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self._start_time = time.time()
        self._events = []
        self._input_buffer = ""
        
        self._overlay.show()
        
        # 连接浏览器录制器
        if self.mode in (RecordingMode.BROWSER, RecordingMode.HYBRID):
            self._browser_recorder = BrowserRecorder(self.user_data_dir)
            if self._browser_recorder.connect():
                logger.info("浏览器录制器已连接")
            else:
                logger.warning("浏览器录制器连接失败，将使用桌面录制")
        
        # 启动监听
        self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self._mouse_listener.start()
        
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self._keyboard_listener.start()
        
        print(f"🎬 开始录制... (模式: {self.mode.value}, 按 Ctrl+R 停止)")
    
    def stop_recording(self) -> RecordingSession:
        if not self.is_recording:
            raise RuntimeError("未在录制中")
        
        # 处理剩余输入
        if self._input_buffer:
            self._events.append(RecordingEvent(
                action="type",
                timestamp=time.time() - self._start_time,
                value=self._input_buffer,
                recording_mode=RecordingMode.DESKTOP
            ))
        
        self.is_recording = False
        
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._browser_recorder:
            self._browser_recorder.disconnect()
        
        self._overlay.hide()
        
        session = RecordingSession(
            name=self._session_name,
            start_time=datetime.fromtimestamp(self._start_time),
            events=self._events.copy()
        )
        
        print(f"✅ 录制完成: {len(self._events)} 个事件")
        return session
    
    def _on_mouse_click(self, x, y, button, pressed):
        if not pressed or not self.is_recording:
            return
        
        # 处理输入缓冲区
        if self._input_buffer:
            self._events.append(RecordingEvent(
                action="type",
                timestamp=self._last_input_time - self._start_time,
                value=self._input_buffer,
                recording_mode=RecordingMode.DESKTOP
            ))
            self._input_buffer = ""
        
        # 检测当前模式
        current_mode = RecordingMode.BROWSER if self.mode == RecordingMode.BROWSER else \
                       RecordingMode.DESKTOP if self.mode == RecordingMode.DESKTOP else \
                       RecordingMode.BROWSER if get_current_recording_mode() == "browser" else RecordingMode.DESKTOP
        
        # 尝试浏览器录制
        if current_mode == RecordingMode.BROWSER and self._browser_recorder:
            time.sleep(0.1)
            event = self._browser_recorder.get_last_event()
            if event and event.action == "browser_click":
                event.timestamp = time.time() - self._start_time
                self._events.append(event)
                logger.info(f"🌐 浏览器点击: {event.css_selector}")
                self._browser_recorder.clear_last_event()
                return
        
        # 桌面录制
        event = RecordingEvent(
            action="click",
            timestamp=time.time() - self._start_time,
            target=f"{int(x)},{int(y)}",
            position=(int(x), int(y)),
            recording_mode=RecordingMode.DESKTOP
        )
        self._events.append(event)
        logger.info(f"🖱️ 桌面点击: ({x}, {y})")
    
    def _on_key_press(self, key):
        if not self.is_recording:
            return
        
        try:
            char = key.char
            self._input_buffer += char
            self._last_input_time = time.time()
        except AttributeError:
            if key == keyboard.Key.enter:
                if self._input_buffer:
                    self._events.append(RecordingEvent(
                        action="type",
                        timestamp=self._last_input_time - self._start_time,
                        value=self._input_buffer,
                        recording_mode=RecordingMode.DESKTOP
                    ))
                    self._input_buffer = ""
                self._events.append(RecordingEvent(
                    action="press",
                    timestamp=time.time() - self._start_time,
                    value="enter",
                    recording_mode=RecordingMode.DESKTOP
                ))
