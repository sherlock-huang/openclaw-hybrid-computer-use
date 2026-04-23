"""应用管理器"""

import logging
import platform
import subprocess
import time
from typing import Optional, Dict

from ..core.config import Config


class ApplicationManager:
    """应用管理器"""
    
    # MVP支持的应用映射
    APP_MAP: Dict[str, Dict[str, str]] = {
        "calculator": {
            "linux": "gnome-calculator",
            "darwin": "Calculator",
            "win32": "calc.exe"
        },
        "notepad": {
            "linux": "gedit",
            "darwin": "TextEdit",
            "win32": "notepad.exe"
        },
        "chrome": {
            "linux": "google-chrome",
            "darwin": "Google Chrome",
            "win32": "chrome"
        },
        "explorer": {
            "linux": "nautilus",
            "darwin": "Finder",
            "win32": "explorer.exe"
        },
        "terminal": {
            "linux": "gnome-terminal",
            "darwin": "Terminal",
            "win32": "cmd.exe"
        }
    }
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self.system = platform.system().lower()
        self.logger.info(f"当前系统: {self.system}")
    
    def launch(self, app_name: str, wait: float = 0.5) -> bool:
        """
        启动应用
        
        Args:
            app_name: 应用名称 (calculator, notepad, chrome等)
            wait: 启动后等待时间
            
        Returns:
            是否成功启动
        """
        app_name_lower = app_name.lower()
        
        # 查找应用命令
        cmd = None
        if app_name_lower in self.APP_MAP:
            cmd = self.APP_MAP[app_name_lower].get(self.system)
        
        if not cmd:
            # 尝试直接使用应用名
            cmd = app_name
        
        try:
            self.logger.info(f"启动应用: {app_name} (命令: {cmd})")
            
            if self.system == "win32":
                # Windows
                subprocess.Popen(cmd, shell=True)
            elif self.system == "darwin":
                # macOS
                subprocess.Popen(["open", "-a", cmd])
            else:
                # Linux
                subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if wait > 0:
                time.sleep(wait)
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动应用失败: {e}")
            return False
    
    def is_running(self, app_name: str) -> bool:
        """
        检查应用是否运行
        
        Args:
            app_name: 应用名称
            
        Returns:
            是否正在运行
        """
        try:
            if self.system == "win32":
                import psutil
                for proc in psutil.process_iter(['name']):
                    if app_name.lower() in proc.info['name'].lower():
                        return True
            else:
                result = subprocess.run(
                    ["pgrep", "-f", app_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
        except Exception as e:
            self.logger.error(f"检查应用状态失败: {e}")
        
        return False
    
    def kill(self, app_name: str) -> bool:
        """
        关闭应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            是否成功关闭
        """
        try:
            self.logger.info(f"关闭应用: {app_name}")
            
            if self.system == "win32":
                subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"], check=False)
            else:
                subprocess.run(["pkill", "-f", app_name], check=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"关闭应用失败: {e}")
            return False
    
    def register_app(self, name: str, linux_cmd: str, mac_cmd: str, win_cmd: str):
        """
        注册自定义应用
        
        Args:
            name: 应用名称
            linux_cmd: Linux命令
            mac_cmd: macOS命令
            win_cmd: Windows命令
        """
        self.APP_MAP[name] = {
            "linux": linux_cmd,
            "darwin": mac_cmd,
            "win32": win_cmd
        }
        self.logger.info(f"注册应用: {name}")
