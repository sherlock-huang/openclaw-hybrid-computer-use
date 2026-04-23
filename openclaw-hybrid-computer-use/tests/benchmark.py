"""
性能基准测试

测量核心操作的性能指标。
"""

import time
import statistics
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_desktop import (
    ComputerUseAgent,
    ScreenCapture,
    ElementDetector,
    MouseController,
    KeyboardController,
    Task,
    TaskSequence,
)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    times: List[float]
    
    @property
    def mean(self) -> float:
        return statistics.mean(self.times)
    
    @property
    def median(self) -> float:
        return statistics.median(self.times)
    
    @property
    def min_time(self) -> float:
        return min(self.times)
    
    @property
    def max_time(self) -> float:
        return max(self.times)
    
    @property
    def stdev(self) -> float:
        if len(self.times) > 1:
            return statistics.stdev(self.times)
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": self.mean * 1000,
            "median_ms": self.median * 1000,
            "min_ms": self.min_time * 1000,
            "max_ms": self.max_time * 1000,
            "stdev_ms": self.stdev * 1000,
        }
    
    def __str__(self) -> str:
        return (f"{self.name}: {self.mean*1000:.1f}ms "
                f"(min={self.min_time*1000:.1f}, max={self.max_time*1000:.1f}, "
                f"n={self.iterations})")


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def benchmark_screenshot(self, iterations: int = 10) -> BenchmarkResult:
        """测试截图性能"""
        print(f"\n📸 测试截图性能 ({iterations} 次)...")
        
        capture = ScreenCapture()
        times = []
        
        for i in range(iterations):
            start = time.time()
            image = capture.capture()
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  迭代 {i+1}/{iterations}: {elapsed*1000:.1f}ms")
        
        result = BenchmarkResult("截图", iterations, times)
        self.results.append(result)
        return result
    
    def benchmark_detection(self, iterations: int = 5) -> BenchmarkResult:
        """测试元素检测性能"""
        print(f"\n🔍 测试元素检测性能 ({iterations} 次)...")
        
        capture = ScreenCapture()
        detector = ElementDetector()
        
        # 先截图一次用于检测
        image = capture.capture()
        
        times = []
        for i in range(iterations):
            start = time.time()
            elements = detector.detect(image)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  迭代 {i+1}/{iterations}: {elapsed*1000:.1f}ms (检测到 {len(elements)} 个元素)")
        
        result = BenchmarkResult("元素检测", iterations, times)
        self.results.append(result)
        return result
    
    def benchmark_mouse_move(self, iterations: int = 10) -> BenchmarkResult:
        """测试鼠标移动性能"""
        print(f"\n🖱️  测试鼠标移动性能 ({iterations} 次)...")
        
        mouse = MouseController()
        
        # 获取屏幕中心
        center_x = mouse.screen_width // 2
        center_y = mouse.screen_height // 2
        
        # 移动范围
        offset = 100
        positions = [
            (center_x - offset, center_y - offset),
            (center_x + offset, center_y - offset),
            (center_x + offset, center_y + offset),
            (center_x - offset, center_y + offset),
        ]
        
        times = []
        for i in range(iterations):
            pos = positions[i % len(positions)]
            
            start = time.time()
            mouse.move_to(pos[0], pos[1], duration=0.1)
            elapsed = time.time() - start
            times.append(elapsed)
            
            print(f"  迭代 {i+1}/{iterations}: {elapsed*1000:.1f}ms -> ({pos[0]}, {pos[1]})")
            time.sleep(0.1)
        
        result = BenchmarkResult("鼠标移动", iterations, times)
        self.results.append(result)
        return result
    
    def benchmark_task_execution(self, iterations: int = 5) -> BenchmarkResult:
        """测试任务执行性能"""
        print(f"\n⚡ 测试任务执行性能 ({iterations} 次)...")
        
        agent = ComputerUseAgent()
        
        # 简单的等待任务
        sequence = TaskSequence(
            name="benchmark",
            tasks=[
                Task("wait", delay=0.1),
                Task("wait", delay=0.1),
            ]
        )
        
        times = []
        for i in range(iterations):
            start = time.time()
            result = agent.execute(sequence)
            elapsed = time.time() - start
            times.append(elapsed)
            
            status = "✅" if result.success else "❌"
            print(f"  迭代 {i+1}/{iterations}: {elapsed*1000:.1f}ms {status}")
        
        result = BenchmarkResult("任务执行(2x wait)", iterations, times)
        self.results.append(result)
        return result
    
    def run_all(self):
        """运行所有基准测试"""
        print("=" * 60)
        print("🚀 OpenClaw Computer-Use Agent 性能基准测试")
        print("=" * 60)
        
        try:
            self.benchmark_screenshot(iterations=10)
        except Exception as e:
            print(f"  ❌ 截图测试失败: {e}")
        
        try:
            self.benchmark_detection(iterations=5)
        except Exception as e:
            print(f"  ❌ 检测测试失败: {e}")
        
        try:
            self.benchmark_mouse_move(iterations=5)
        except Exception as e:
            print(f"  ❌ 鼠标移动测试失败: {e}")
        
        try:
            self.benchmark_task_execution(iterations=5)
        except Exception as e:
            print(f"  ❌ 任务执行测试失败: {e}")
    
    def print_report(self):
        """打印测试报告"""
        print("\n" + "=" * 60)
        print("📊 性能基准测试报告")
        print("=" * 60)
        
        for result in self.results:
            print(f"\n{result.name}:")
            print(f"  平均: {result.mean*1000:.1f}ms")
            print(f"  中位数: {result.median*1000:.1f}ms")
            print(f"  范围: {result.min_time*1000:.1f}ms - {result.max_time*1000:.1f}ms")
            print(f"  标准差: {result.stdev*1000:.1f}ms")
        
        # 与目标对比
        print("\n" + "-" * 60)
        print("📈 与目标对比:")
        print("-" * 60)
        
        targets = {
            "截图": 500,  # ms
            "元素检测": 2000,  # ms
            "鼠标移动": 500,  # ms
        }
        
        for result in self.results:
            target = targets.get(result.name, None)
            if target:
                actual = result.mean * 1000
                if actual <= target:
                    status = "✅ 达标"
                else:
                    status = "⚠️  超标"
                print(f"  {result.name}: 实际={actual:.1f}ms, 目标={target}ms {status}")
    
    def save_report(self, path: str = "output/benchmark_report.json"):
        """保存报告到文件"""
        import json
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": [r.to_dict() for r in self.results]
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {path}")


def main():
    """主入口"""
    suite = BenchmarkSuite()
    suite.run_all()
    suite.print_report()
    suite.save_report()


if __name__ == "__main__":
    main()
