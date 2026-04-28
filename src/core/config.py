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
    browser_user_data_dir: Optional[str] = "browser_data"  # 用户数据目录，保存登录状态

    # Self-Healing Phase 2: VLM 融合诊断配置
    vlm_diagnosis_enabled: bool = True           # 是否启用 VLM 融合诊断
    vlm_diagnosis_provider: str = "auto"         # auto | minimax | mimo | openai
    vlm_max_candidates: int = 15                 # 传给 VLM 的最大候选元素数
    vlm_verify_enabled: bool = True              # 是否启用 Verify Loop
    vlm_max_verify_rounds: int = 2               # 最大验证重试轮数
    skill_file: str = "skills/self_healing_skills.jsonl"  # Skill 文件路径

    # 本地 VLM 离线兜底配置
    local_vlm_enabled: bool = True               # 是否启用本地 VLM 兜底
    local_vlm_model: str = "Qwen/Qwen2-VL-2B-Instruct"  # 本地模型名
    local_vlm_device: str = "auto"               # auto | cpu | cuda
    local_vlm_cache_dir: Optional[str] = "models/cache"  # 模型缓存目录
    local_vlm_load_in_4bit: bool = False         # 4-bit 量化（最小内存）
    local_vlm_load_in_8bit: bool = False         # 8-bit 量化
    local_vlm_max_tokens: int = 1024             # 最大生成 token 数
    local_vlm_temperature: float = 0.2           # 采样温度

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
        if os.getenv("CLAW_VLM_DIAGNOSIS"):
            config.vlm_diagnosis_enabled = os.getenv("CLAW_VLM_DIAGNOSIS").lower() in ("true", "1", "yes")

        return config
    
    def ensure_dirs(self):
        """确保必要的目录存在"""
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.yolo_model_path).parent.mkdir(parents=True, exist_ok=True)
        if self.browser_user_data_dir:
            Path(self.browser_user_data_dir).mkdir(parents=True, exist_ok=True)
