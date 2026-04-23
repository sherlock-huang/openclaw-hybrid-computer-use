#!/usr/bin/env python3
"""运行所有录制功能测试"""
import subprocess
import sys

test_files = [
    "tests/test_recorder.py",
    "tests/test_recording_overlay.py", 
    "tests/test_shortcut_listener.py",
    "tests/test_recorder_integration.py"
]

print("🧪 运行录制功能测试套件\n")
print("=" * 60)

for test_file in test_files:
    print(f"\n📋 运行: {test_file}")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 通过")
    else:
        print("❌ 失败")
        print(result.stdout)
        print(result.stderr)

print("\n" + "=" * 60)
print("测试完成！")
