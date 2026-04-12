"""配置管理"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """应用配置"""
    
    # 模型配置
    yolo_model_path: str = "models/yolov8n.pt"
    yolo_conf_threshold: float = 0.5
    yolo_nms_threshold: float = 0.45
    
    # OCR配置
    ocr_lang: str = "ch"  # 中文
    ocr_use_gpu: bool = False
    
    # 屏幕配置
    screen_resolution: tuple = (1920, 1080)
    capture_region: Optional[tuple] = None  # (x, y, w, h)，None为全屏
    
    # 控制配置
    mouse_smooth_move: bool = True
    mouse_default_duration: float = 0.5
    mouse_failsafe: bool = True
    
    # 执行配置
    default_delay: float = 1.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 日志配置
    log_level: str = "INFO"
    log_dir: str = "logs"
    save_screenshots: bool = True
    
    # 浏览器配置
    browser_headless: bool = False  # 是否无头模式
    browser_default_type: str = "chromium"  # 默认浏览器
    browser_timeout: int = 30  # 默认超时（秒）
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        config = cls()
        
        if os.getenv("CLAW_YOLO_MODEL"):
            config.yolo_model_path = os.getenv("CLAW_YOLO_MODEL")
        if os.getenv("CLAW_OCR_LANG"):
            config.ocr_lang = os.getenv("CLAW_OCR_LANG")
        if os.getenv("CLAW_LOG_LEVEL"):
            config.log_level = os.getenv("CLAW_LOG_LEVEL")
            
        return config
    
    def ensure_dirs(self):
        """确保必要的目录存在"""
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.yolo_model_path).parent.mkdir(parents=True, exist_ok=True)
