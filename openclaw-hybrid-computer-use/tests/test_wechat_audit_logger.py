"""WeChatAuditLogger 测试"""

import unittest
import tempfile
import shutil
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_audit_logger import WeChatAuditLogger


class TestWeChatAuditLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = WeChatAuditLogger.LOG_DIR
        WeChatAuditLogger.LOG_DIR = Path(self.temp_dir)
        self.logger = WeChatAuditLogger()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        WeChatAuditLogger.LOG_DIR = self.original_log_dir
    
    def test_log_attempt_creates_file(self):
        self.logger.log_attempt("张三", "Hello", "strict", False)
        log_files = list(Path(self.temp_dir).glob("wechat_audit_*.log"))
        self.assertEqual(len(log_files), 1)
        
        with open(log_files[0], "r", encoding="utf-8") as f:
            line = json.loads(f.readline())
            self.assertEqual(line["event"], "attempt")
            self.assertEqual(line["contact"], "张三")
            self.assertEqual(line["message"], "Hello")
    
    def test_log_result_with_decisions(self):
        self.logger.log_attempt("张三", "Hello", "strict", False)
        self.logger.log_decision("search", "ok")
        self.logger.log_decision("validate", "ok", {"ocr": "张三"})
        self.logger.log_result(True, "发送成功", "done", [])
        
        log_files = list(Path(self.temp_dir).glob("wechat_audit_*.log"))
        with open(log_files[0], "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f.readlines()]
        
        self.assertEqual(lines[0]["event"], "attempt")
        self.assertEqual(lines[1]["event"], "result")
        self.assertTrue(lines[1]["success"])
        self.assertEqual(len(lines[1]["decisions"]), 2)
        self.assertEqual(lines[1]["decisions"][1]["details"]["ocr"], "张三")
    
    def test_log_result_with_unserializable_filtered(self):
        self.logger.log_attempt("张三", "Hello", "strict", False)
        # 传入不可序列化的对象应被过滤
        self.logger.log_decision("test", "ok", {"obj": object()})
        
        log_files = list(Path(self.temp_dir).glob("wechat_audit_*.log"))
        with open(log_files[0], "r", encoding="utf-8") as f:
            line = json.loads(f.readline())
        
        self.assertEqual(line["event"], "attempt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
