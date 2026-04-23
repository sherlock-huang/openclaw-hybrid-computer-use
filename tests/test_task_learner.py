"""任务学习器测试"""

import unittest
import tempfile
import shutil
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.task_learner import TaskLearner, TaskPattern


class TestTaskLearner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        TaskLearner.LEARN_FILE = self.temp_dir + "/task_patterns.json"
        self.learner = TaskLearner()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_learn_and_suggest(self):
        self.learner.learn("wechat_send", "张三", [{"type": "click"}], True, 2.0)
        pattern = self.learner.suggest("wechat_send", "张三")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.success_rate, 1.0)
    
    def test_success_rate_calculation(self):
        self.learner.learn("test", "target", [], True, 1.0)
        self.learner.learn("test", "target", [], False, 1.0)
        pattern = self.learner.suggest("test", "target")
        self.assertEqual(pattern.success_rate, 0.5)
    
    def test_persistence(self):
        self.learner.learn("test", "target", [{"a": 1}], True, 1.0)
        
        # 重新加载
        learner2 = TaskLearner()
        pattern = learner2.suggest("test", "target")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.actions, [{"a": 1}])


class TestTaskPattern(unittest.TestCase):
    def test_success_rate_initial(self):
        pattern = TaskPattern("click", "button", [])
        self.assertEqual(pattern.success_rate, 0.0)
    
    def test_record_result_updates_stats(self):
        pattern = TaskPattern("type", "input", [])
        pattern.record_result(True, 1.5)
        self.assertEqual(pattern.success_count, 1)
        self.assertEqual(pattern.fail_count, 0)
        self.assertEqual(pattern.avg_duration, 1.5)
        
        pattern.record_result(False, 0.5)
        self.assertEqual(pattern.success_count, 1)
        self.assertEqual(pattern.fail_count, 1)
        self.assertEqual(pattern.success_rate, 0.5)
    
    def test_record_result_updates_optimal_delay(self):
        pattern = TaskPattern("click", "btn", [])
        pattern.record_result(True, 2.0)
        self.assertEqual(pattern.optimal_delay, 2.0)
        pattern.record_result(True, 4.0)
        # EWMA: 2.0 * 0.7 + 4.0 * 0.3 = 2.6
        self.assertAlmostEqual(pattern.optimal_delay, 2.6, places=2)


class TestTaskLearnerEnvironment(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        TaskLearner.LEARN_FILE = self.temp_dir + "/task_patterns.json"
        self.learner = TaskLearner()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_env_key_fallback(self):
        key = self.learner._get_env_key()
        self.assertIsInstance(key, str)
        self.assertTrue(len(key) > 0)
    
    def test_learn_with_strategy_hints(self):
        self.learner.learn(
            "wechat_send", "张三", [{"type": "click"}], True, 1.0,
            strategy_hints={"wechat_selector": "ocr"}
        )
        pattern = self.learner.suggest("wechat_send", "张三")
        self.assertEqual(pattern.strategy_hints.get("wechat_selector"), "ocr")
    
    def test_get_stats(self):
        self.learner.learn("wechat_send", "张三", [{"type": "click"}], True, 1.0)
        stats = self.learner.get_stats()
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["task_type"], "wechat_send")
        self.assertEqual(stats[0]["success_rate"], 1.0)
    
    def test_export(self):
        self.learner.learn("test", "target", [{"a": 1}], True, 1.0)
        export_path = self.temp_dir + "/export.json"
        success = self.learner.export(export_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))


if __name__ == "__main__":
    unittest.main()
