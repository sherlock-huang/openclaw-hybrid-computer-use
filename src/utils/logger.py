"""日志工具"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(level: str = "INFO", log_dir: str = "logs"):
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_dir: 日志文件保存目录
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有处理器
    root_logger.handlers = []
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = log_path / f"claw_desktop_{datetime.now():%Y%m%d_%H%M%S}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)
    
    # 设置第三方库日志级别
    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    logging.getLogger("paddleocr").setLevel(logging.WARNING)
    logging.getLogger("pyautogui").setLevel(logging.INFO)
    
    logging.info(f"日志系统初始化完成，日志文件: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    获取统一配置的日志器。

    所有模块应通过此函数获取 logger，确保命名一致：
        logger = get_logger(__name__)

    Args:
        name: 日志器名称，推荐传入 ``__name__``。

    Returns:
        配置好的 Logger 实例。
    """
    return logging.getLogger(name)
