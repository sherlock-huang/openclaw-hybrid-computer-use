#!/usr/bin/env python3
"""诊断脚本 - 检查微信功能问题"""

import sys
import traceback

print("=" * 50)
print("诊断微信功能")
print("=" * 50)

# 1. 检查 Python
print(f"\n1. Python 版本: {sys.version}")
print(f"   平台: {sys.platform}")

# 2. 检查导入
try:
    print("\n2. 检查导入...")
    from src.utils.wechat_helper import WeChatHelper, WIN32_AVAILABLE
    print(f"   ✅ WeChatHelper 导入成功")
    print(f"   WIN32_AVAILABLE: {WIN32_AVAILABLE}")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

# 3. 检查微信窗口
try:
    print("\n3. 检查微信窗口...")
    helper = WeChatHelper()
    handle = helper.find_wechat_window()
    if handle:
        print(f"   ✅ 找到微信窗口: {handle}")
    else:
        print(f"   ❌ 未找到微信窗口")
        print("   请确保微信已登录并打开")
except Exception as e:
    print(f"   ❌ 检查失败: {e}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("诊断完成")
print("=" * 50)
