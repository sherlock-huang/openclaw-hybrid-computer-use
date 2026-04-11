"""任务录制器"""

import time
import logging
from datetime import datetime
from typing import List, Optional, Callable
from pathlib import Path

from pynput import mouse, keyboard

from .models import RecordingEvent, RecordingSession, TaskSequence
from ..utils.recording_overlay import RecordingOverlay
from ..perception.screen import ScreenCapture
from ..perception.detector import ElementDetector

logger = logging.getLogger(__name__)


class TaskRecorder:
    """任务录制器"""
    
    def __init__(self):
        self.is_recording = False
        self._session_name: Optional[str] = None
        self._start_time: Optional[float] = None
        self._events: List[RecordingEvent] = []
        self._overlay = RecordingOverlay()
        
        # 输入监听器
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        
        # 依赖
        self._screen = ScreenCapture()
        self._detector = ElementDetector()
        
        # 当前输入缓冲区（用于合并连续输入）
        self._input_buffer = ""
        self._last_input_time = 0.0
    
    def start_recording(self, name: Optional[str] = None):
        """
        开始录制
        
        Args:
            name: 会话名称，默认自动生成
        """
        if self.is_recording:
            raise RuntimeError("Already recording. Call stop_recording() first.")
        
        self.is_recording = True
        self._session_name = name or f"录制任务 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self._start_time = time.time()
        self._events = []
        self._input_buffer = ""
        
        # 显示录制指示器
        self._overlay.show()
        
        # 启动鼠标监听
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click
        )
        self._mouse_listener.start()
        
        # 启动键盘监听
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.start()
        
        logger.info(f"🎬 开始录制: {self._session_name}")
        print(f"🎬 开始录制... (按 Ctrl+R 停止)")
    
    def stop_recording(self) -> RecordingSession:
        """
        停止录制并返回会话
        
        Returns:
            RecordingSession: 录制的会话
        """
        if not self.is_recording:
            raise RuntimeError("Not recording. Call start_recording() first.")
        
        # 先处理缓冲区中剩余的输入
        self._flush_input_buffer()
        
        self.is_recording = False
        
        # 停止监听器
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        # 隐藏指示器
        self._overlay.hide()
        
        # 创建会话
        session = RecordingSession(
            name=self._session_name,
            start_time=datetime.fromtimestamp(self._start_time),
            events=self._events.copy()
        )
        
        logger.info(f"✅ 录制完成: {len(self._events)} 个事件")
        print(f"✅ 录制完成: {len(self._events)} 个事件")
        
        return session
    
    def _on_mouse_click(self, x, y, button, pressed):
        """鼠标点击回调"""
        if not pressed or not self.is_recording:
            return
        
        # 先处理缓冲区中的输入（避免输入和点击事件顺序混乱）
        self._flush_input_buffer()
        
        try:
            # 截图并检测元素
            image = self._screen.capture()
            elements = self._detector.detect(image)
            
            # 找到点击位置的元素
            target = None
            element_type = None
            for elem in elements:
                if (elem.bbox.x1 <= x <= elem.bbox.x2 and 
                    elem.bbox.y1 <= y <= elem.bbox.y2):
                    target = elem.id
                    element_type = elem.element_type.value
                    break
            
            # 记录事件
            event = RecordingEvent(
                action="click",
                timestamp=time.time() - self._start_time,
                target=target,
                position=(int(x), int(y)),
                element_type=element_type
            )
            self._events.append(event)
            
            if target:
                logger.debug(f"🖱️  Click @ ({x}, {y}) -> {target}")
            else:
                logger.debug(f"🖱️  Click @ ({x}, {y}) -> coordinate")
                
        except Exception as e:
            logger.error(f"Error processing mouse click: {e}")
            # 即使检测失败，也记录坐标
            event = RecordingEvent(
                action="click",
                timestamp=time.time() - self._start_time,
                position=(int(x), int(y))
            )
            self._events.append(event)
    
    def _on_key_press(self, key):
        """按键按下回调"""
        if not self.is_recording:
            return
        
        try:
            # 普通字符按键
            char = key.char
            self._input_buffer += char
            self._last_input_time = time.time()
        except AttributeError:
            # 特殊按键
            if key == keyboard.Key.enter:
                self._flush_input_buffer()
                # 记录回车键
                event = RecordingEvent(
                    action="press",
                    timestamp=time.time() - self._start_time,
                    value="enter"
                )
                self._events.append(event)
            elif key == keyboard.Key.tab:
                self._flush_input_buffer()
                event = RecordingEvent(
                    action="press",
                    timestamp=time.time() - self._start_time,
                    value="tab"
                )
                self._events.append(event)
            elif key == keyboard.Key.esc:
                self._flush_input_buffer()
                event = RecordingEvent(
                    action="press",
                    timestamp=time.time() - self._start_time,
                    value="esc"
                )
                self._events.append(event)
    
    def _on_key_release(self, key):
        """按键释放回调"""
        pass  # 目前不需要处理
    
    def _flush_input_buffer(self):
        """将输入缓冲区中的内容保存为事件"""
        if self._input_buffer:
            event = RecordingEvent(
                action="type",
                timestamp=self._last_input_time - self._start_time,
                value=self._input_buffer
            )
            self._events.append(event)
            logger.debug(f"⌨️  Type: {self._input_buffer}")
            self._input_buffer = ""
