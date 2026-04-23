"""WindowLockGuard 测试"""

import unittest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.window_lock_guard import WindowLockGuard


class TestWindowLockGuard(unittest.TestCase):
    @patch("src.utils.window_lock_guard.win32gui.IsWindow", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.IsWindowVisible", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.GetWindowText", return_value="微信")
    @patch("src.utils.window_lock_guard.win32gui.GetForegroundWindow", return_value=12345)
    def test_check_all_pass(self, mock_fg, mock_title, mock_visible, mock_iswindow):
        guard = WindowLockGuard(12345)
        stable, reason = guard.check()
        self.assertTrue(stable)
        self.assertEqual(reason, "")
    
    @patch("src.utils.window_lock_guard.win32gui.IsWindow", return_value=False)
    def test_check_invalid_hwnd(self, mock_iswindow):
        guard = WindowLockGuard(12345)
        stable, reason = guard.check()
        self.assertFalse(stable)
        self.assertIn("失效", reason)
    
    @patch("src.utils.window_lock_guard.win32gui.IsWindow", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.IsWindowVisible", return_value=False)
    def test_check_not_visible(self, mock_visible, mock_iswindow):
        guard = WindowLockGuard(12345)
        stable, reason = guard.check()
        self.assertFalse(stable)
        self.assertIn("不可见", reason)
    
    @patch("src.utils.window_lock_guard.win32gui.IsWindow", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.IsWindowVisible", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.GetWindowText", return_value="QQ")
    def test_check_title_changed(self, mock_title, mock_visible, mock_iswindow):
        guard = WindowLockGuard(12345)
        stable, reason = guard.check()
        self.assertFalse(stable)
        self.assertIn("标题", reason)
    
    @patch("src.utils.window_lock_guard.win32gui.IsWindow", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.IsWindowVisible", return_value=True)
    @patch("src.utils.window_lock_guard.win32gui.GetWindowText", return_value="微信")
    @patch("src.utils.window_lock_guard.win32gui.GetForegroundWindow", return_value=99999)
    def test_check_not_foreground(self, mock_fg, mock_title, mock_visible, mock_iswindow):
        guard = WindowLockGuard(12345)
        stable, reason = guard.check()
        self.assertFalse(stable)
        self.assertIn("前台", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
