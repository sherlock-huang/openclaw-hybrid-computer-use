#!/usr/bin/env python3
"""
第一阶段验证脚本 - 检查项目结构和基础代码
"""

import sys
import ast
from pathlib import Path


def check_file_syntax(path: Path) -> bool:
    """检查 Python 文件语法"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {path} - {e}")
        return False


def verify_project():
    """验证项目结构"""
    print("=" * 60)
    print("OpenClaw Computer-Use Agent - 第一阶段验证")
    print("=" * 60)
    
    # 检查目录结构
    print("\n📁 目录结构检查:")
    required_dirs = [
        "src", "src/core", "src/perception", "src/action", "src/utils",
        "tests", "examples", "models", "docs"
    ]
    
    all_dirs_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path}")
        if not exists:
            all_dirs_exist = False
    
    if not all_dirs_exist:
        print("\n❌ 目录结构不完整!")
        return False
    
    # 检查核心文件
    print("\n📄 核心文件检查:")
    required_files = [
        "src/__init__.py",
        "src/core/__init__.py", "src/core/agent.py", "src/core/executor.py",
        "src/core/models.py", "src/core/config.py",
        "src/perception/__init__.py", "src/perception/screen.py",
        "src/perception/detector.py", "src/perception/ocr.py",
        "src/action/__init__.py", "src/action/mouse.py",
        "src/action/keyboard.py", "src/action/app_manager.py",
        "src/utils/__init__.py", "src/utils/logger.py", "src/utils/image.py",
        "tests/__init__.py",
        "requirements.txt", "README.md",
    ]
    
    all_files_valid = True
    for file_path in required_files:
        path = Path(file_path)
        exists = path.exists()
        
        if not exists:
            print(f"  ❌ {file_path} - 文件不存在")
            all_files_valid = False
            continue
        
        # 检查 Python 文件语法
        if file_path.endswith('.py'):
            valid = check_file_syntax(path)
            if valid:
                print(f"  ✅ {file_path}")
            else:
                all_files_valid = False
        else:
            print(f"  ✅ {file_path}")
    
    if not all_files_valid:
        print("\n❌ 文件检查未通过!")
        return False
    
    # 检查类定义
    print("\n🔍 核心类定义检查:")
    classes_to_check = [
        ("src/core/agent.py", "ComputerUseAgent"),
        ("src/core/executor.py", "TaskExecutor"),
        ("src/core/models.py", "Task"),
        ("src/core/models.py", "TaskSequence"),
        ("src/core/models.py", "UIElement"),
        ("src/perception/screen.py", "ScreenCapture"),
        ("src/perception/detector.py", "ElementDetector"),
        ("src/perception/ocr.py", "TextRecognizer"),
        ("src/action/mouse.py", "MouseController"),
        ("src/action/keyboard.py", "KeyboardController"),
        ("src/action/app_manager.py", "ApplicationManager"),
    ]
    
    all_classes_found = True
    for file_path, class_name in classes_to_check:
        path = Path(file_path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found = f"class {class_name}" in content
        status = "✅" if found else "❌"
        print(f"  {status} {class_name} (in {file_path})")
        
        if not found:
            all_classes_found = False
    
    if not all_classes_found:
        print("\n❌ 类定义检查未通过!")
        return False
    
    # 检查关键方法
    print("\n🔧 关键方法检查:")
    methods_to_check = [
        ("src/perception/screen.py", "def capture"),
        ("src/perception/detector.py", "def detect"),
        ("src/action/mouse.py", "def move_to"),
        ("src/action/mouse.py", "def click"),
        ("src/action/keyboard.py", "def type_text"),
        ("src/action/app_manager.py", "def launch"),
        ("src/core/executor.py", "def execute"),
    ]
    
    all_methods_found = True
    for file_path, method_sig in methods_to_check:
        path = Path(file_path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found = method_sig in content
        status = "✅" if found else "❌"
        print(f"  {status} {method_sig} (in {file_path})")
        
        if not found:
            all_methods_found = False
    
    if not all_methods_found:
        print("\n❌ 方法检查未通过!")
        return False
    
    # 统计代码行数
    print("\n📊 代码统计:")
    total_lines = 0
    py_files = list(Path("src").rglob("*.py"))
    for py_file in py_files:
        with open(py_file, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
            total_lines += lines
    
    print(f"  Python 文件数: {len(py_files)}")
    print(f"  总代码行数: {total_lines}")
    
    # 最终结论
    print("\n" + "=" * 60)
    print("✅ 第一阶段验证通过!")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 安装依赖: pip install -r requirements.txt")
    print("  2. 下载 YOLO 模型")
    print("  3. 运行测试: python -m pytest tests/ -v")
    print("  4. 运行示例: python examples/basic_usage.py")
    
    return True


if __name__ == "__main__":
    try:
        success = verify_project()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
