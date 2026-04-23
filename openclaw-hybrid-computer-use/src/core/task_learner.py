"""任务学习数据结构和记录器"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class TaskPattern:
    """任务模式"""
    task_type: str           # 任务类型（如 wechat_send, browser_click）
    target_signature: str    # 目标特征（如联系人名称、URL）
    actions: List[Dict]      # 操作序列
    success_count: int = 0
    fail_count: int = 0
    last_used: float = 0
    avg_duration: float = 0.0
    optimal_delay: float = 1.0           # 学习到的最佳等待时间
    environment_key: str = ""            # 环境指纹
    strategy_hints: Dict = field(default_factory=dict)  # 策略提示
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0.0
    
    def record_result(self, success: bool, duration: float):
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        self.last_used = time.time()
        # 更新平均耗时
        total = self.success_count + self.fail_count
        self.avg_duration = (self.avg_duration * (total - 1) + duration) / total
        # 更新最佳等待时间（简单 EWMA）
        if total > 1:
            self.optimal_delay = self.optimal_delay * 0.7 + duration * 0.3
        else:
            self.optimal_delay = duration
    
    def get_adjusted_delay(self, base_delay: float) -> float:
        """根据成功率动态调整等待时间"""
        if self.success_rate > 0.9:
            return max(0.3, base_delay * 0.6)
        elif self.success_rate >= 0.5:
            return base_delay
        else:
            return base_delay * 1.5


class TaskLearner:
    """任务学习器"""
    
    LEARN_FILE = Path("browser_data/task_patterns.json")
    
    def __init__(self):
        self.patterns: Dict[str, TaskPattern] = {}
        self.load()
    
    def _make_key(self, task_type: str, target: str) -> str:
        return f"{task_type}:{target}"
    
    def _get_env_key(self) -> str:
        """生成当前环境指纹"""
        try:
            import screeninfo
            monitor = screeninfo.get_monitors()[0]
            return f"{monitor.width}x{monitor.height}_{monitor.name or 'default'}"
        except Exception:
            # fallback
            try:
                import pyautogui
                w, h = pyautogui.size()
                return f"{w}x{h}_unknown"
            except Exception:
                return "unknown"
    
    def learn(self, task_type: str, target: str, actions: List[Dict], 
              success: bool, duration: float, strategy_hints: Optional[Dict] = None):
        """记录一次任务执行结果"""
        key = self._make_key(task_type, target)
        if key not in self.patterns:
            self.patterns[key] = TaskPattern(
                task_type=task_type,
                target_signature=target,
                actions=actions,
                environment_key=self._get_env_key()
            )
        
        self.patterns[key].record_result(success, duration)
        
        # 更新策略提示
        if strategy_hints:
            self.patterns[key].strategy_hints.update(strategy_hints)
        
        self.save()
    
    def suggest(self, task_type: str, target: str) -> Optional[TaskPattern]:
        """推荐最佳执行方式"""
        key = self._make_key(task_type, target)
        pattern = self.patterns.get(key)
        if pattern and pattern.success_rate >= 0.5:
            return pattern
        
        # 模糊匹配：找同类型中成功率最高的
        best = None
        for p in self.patterns.values():
            if p.task_type == task_type:
                if best is None or p.success_rate > best.success_rate:
                    best = p
        return best
    
    def apply_learned_settings(self, task_type: str, target: str, task_dict: Dict) -> Dict:
        """
        将学习到的最佳设置应用到任务配置中
        
        Returns:
            修改后的 task_dict
        """
        pattern = self.suggest(task_type, target)
        if not pattern:
            return dict(task_dict)
        
        result = dict(task_dict)
        
        # 1. 调整 delay
        if "delay" in result:
            result["delay"] = pattern.get_adjusted_delay(result["delay"])
        
        # 2. 注入策略提示
        if pattern.strategy_hints:
            result["_strategy_hints"] = dict(pattern.strategy_hints)
        
        # 3. 如果成功率极低 (<0.3)，增加重试次数提示
        if pattern.success_rate < 0.3:
            result["_extra_retries"] = 2
        
        return result
    
    def get_stats(self) -> List[Dict]:
        """获取所有任务的学习统计"""
        stats = []
        for key, p in self.patterns.items():
            stats.append({
                "key": key,
                "task_type": p.task_type,
                "target": p.target_signature,
                "success_count": p.success_count,
                "fail_count": p.fail_count,
                "success_rate": p.success_rate,
                "avg_duration": p.avg_duration,
                "optimal_delay": p.optimal_delay,
                "environment_key": p.environment_key,
                "strategy_hints": p.strategy_hints,
                "last_used": p.last_used,
            })
        return stats
    
    def reset_pattern(self, task_type: str, target: str) -> bool:
        """重置某个任务的学习记录"""
        key = self._make_key(task_type, target)
        if key in self.patterns:
            del self.patterns[key]
            self.save()
            return True
        return False
    
    def export(self, path: str) -> bool:
        """导出学习记录到指定路径"""
        try:
            data = {k: asdict(v) for k, v in self.patterns.items()}
            export_path = Path(path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def _learn_file_path(self) -> Path:
        return Path(self.LEARN_FILE)
    
    def save(self):
        data = {k: asdict(v) for k, v in self.patterns.items()}
        learn_file = self._learn_file_path()
        learn_file.parent.mkdir(parents=True, exist_ok=True)
        with open(learn_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        learn_file = self._learn_file_path()
        if learn_file.exists():
            try:
                with open(learn_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for k, v in data.items():
                    self.patterns[k] = TaskPattern(**v)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Failed to load task patterns: {e}")
