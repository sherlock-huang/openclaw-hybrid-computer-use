"""TaskLearner CLI 测试"""

import unittest
import tempfile
import shutil
import os
import sys
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.task_learner import TaskLearner
from src.core.task_learner_cli import main


class TestTaskLearnerCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        TaskLearner.LEARN_FILE = self.temp_dir + "/task_patterns.json"
        self.learner = TaskLearner()
        self.learner.learn("wechat_send", "张三", [{"type": "click"}], True, 1.5)
        self.learner.learn("browser_click", "btn", [{"type": "click"}], False, 0.5)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_stats_command(self):
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["task_learner_cli", "stats"]
            rc = main()
        output = f.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("wechat_send", output)
        self.assertIn("browser_click", output)
    
    def test_top_command(self):
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["task_learner_cli", "top"]
            rc = main()
        output = f.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("wechat_send", output)
    
    def test_worst_command(self):
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["task_learner_cli", "worst"]
            rc = main()
        output = f.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("browser_click", output)
    
    def test_reset_command(self):
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["task_learner_cli", "reset", "wechat_send", "张三"]
            rc = main()
        output = f.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("已重置", output)
        
        # 创建新实例验证确实删除了
        new_learner = TaskLearner()
        self.assertIsNone(new_learner.suggest("wechat_send", "张三"))
    
    def test_export_command(self):
        export_path = self.temp_dir + "/export.json"
        f = io.StringIO()
        with redirect_stdout(f):
            sys.argv = ["task_learner_cli", "export", export_path]
            rc = main()
        output = f.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("已导出", output)
        self.assertTrue(os.path.exists(export_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
