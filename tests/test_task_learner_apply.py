"""TaskLearner 自动应用学习配置测试"""

import unittest
import tempfile
import shutil
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.task_learner import TaskLearner, TaskPattern


class TestTaskLearnerApply(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        TaskLearner.LEARN_FILE = self.temp_dir + "/task_patterns.json"
        self.learner = TaskLearner()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_apply_high_success_rate_shortens_delay(self):
        self.learner.learn("wechat_send", "张三", [{"type": "click"}], True, 1.0)
        self.learner.learn("wechat_send", "张三", [{"type": "click"}], True, 1.0)
        self.learner.learn("wechat_send", "张三", [{"type": "click"}], True, 1.0)
        
        task = {"action": "wechat_send", "target": "张三", "value": "hi", "delay": 1.0}
        adjusted = self.learner.apply_learned_settings("wechat_send", "张三", task)
        
        # 成功率 100% > 0.9，delay 应该缩短到 0.6
        self.assertAlmostEqual(adjusted["delay"], 0.6, places=2)
    
    def test_apply_low_success_rate_extends_delay(self):
        self.learner.learn("wechat_send", "李四", [{"type": "click"}], False, 1.0)
        self.learner.learn("wechat_send", "李四", [{"type": "click"}], False, 1.0)
        self.learner.learn("wechat_send", "李四", [{"type": "click"}], False, 1.0)
        self.learner.learn("wechat_send", "李四", [{"type": "click"}], True, 1.0)
        
        task = {"action": "wechat_send", "target": "李四", "value": "hi", "delay": 1.0}
        adjusted = self.learner.apply_learned_settings("wechat_send", "李四", task)
        
        # 成功率 25% < 0.5，delay 应该延长到 1.5
        self.assertAlmostEqual(adjusted["delay"], 1.5, places=2)
        self.assertEqual(adjusted["_extra_retries"], 2)
    
    def test_apply_strategy_hints(self):
        self.learner.learn(
            "wechat_send", "王五", [{"type": "click"}], True, 1.0,
            strategy_hints={"wechat_selector": "ocr"}
        )
        
        task = {"action": "wechat_send", "target": "王五", "value": "hi", "delay": 1.0}
        adjusted = self.learner.apply_learned_settings("wechat_send", "王五", task)
        
        self.assertEqual(adjusted["_strategy_hints"]["wechat_selector"], "ocr")
    
    def test_apply_no_pattern_returns_unchanged(self):
        task = {"action": "unknown_task", "target": "nobody", "delay": 2.0}
        adjusted = self.learner.apply_learned_settings("unknown_task", "nobody", task)
        self.assertEqual(adjusted["delay"], 2.0)
        self.assertNotIn("_extra_retries", adjusted)


class TestTaskPatternAdjustedDelay(unittest.TestCase):
    def test_get_adjusted_delay_high_success(self):
        p = TaskPattern("click", "btn", [])
        p.success_count = 10
        p.fail_count = 0
        self.assertEqual(p.get_adjusted_delay(1.0), 0.6)
    
    def test_get_adjusted_delay_medium_success(self):
        p = TaskPattern("click", "btn", [])
        p.success_count = 7
        p.fail_count = 3
        self.assertEqual(p.get_adjusted_delay(1.0), 1.0)
    
    def test_get_adjusted_delay_low_success(self):
        p = TaskPattern("click", "btn", [])
        p.success_count = 1
        p.fail_count = 4
        self.assertEqual(p.get_adjusted_delay(1.0), 1.5)
    
    def test_get_adjusted_delay_minimum(self):
        p = TaskPattern("click", "btn", [])
        p.success_count = 100
        p.fail_count = 0
        self.assertEqual(p.get_adjusted_delay(0.1), 0.3)  # 最小值限制


if __name__ == "__main__":
    unittest.main(verbosity=2)
