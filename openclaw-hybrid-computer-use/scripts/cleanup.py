#!/usr/bin/env python3
"""
项目清理脚本

用法:
    python scripts/cleanup.py          # 查看可清理的文件
    python scripts/cleanup.py --yes    # 确认清理
"""

import os
import sys
import glob
from pathlib import Path


def get_files_to_clean():
    """获取可清理的文件列表。"""
    files_to_clean = []
    
    # 1. 旧日志文件（保留最近3个）
    log_dir = Path("logs")
    if log_dir.exists():
        logs = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        old_logs = logs[3:]  # 保留前3个
        files_to_clean.extend(("log", f) for f in old_logs)
    
    # 2. 临时截图文件
    for pattern in ["*_result.png", "*_test.png", "vlm_*.png", "simple_*.png", "douyin_*.png"]:
        for f in Path(".").glob(pattern):
            if f.is_file():
                files_to_clean.append(("screenshot", f))
    
    # 3. 临时JSON文件
    for pattern in ["test_*.json", "*_auto.json", "simple_*.json"]:
        for f in Path(".").glob(pattern):
            if f.is_file() and f.name not in ["requirements.txt"]:
                files_to_clean.append(("temp_json", f))
    
    # 4. 测试输出文件
    for pattern in ["test_output.txt", "*.tmp"]:
        for f in Path(".").glob(pattern):
            if f.is_file():
                files_to_clean.append(("temp_output", f))
    
    # 5. temp_backup 目录中的文件
    temp_backup = Path("temp_backup")
    if temp_backup.exists():
        files_to_clean.append(("temp_backup_dir", temp_backup))
    
    return files_to_clean


def format_size(size_bytes):
    """格式化文件大小。"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes/(1024*1024):.1f}MB"


def main():
    """主函数。"""
    files = get_files_to_clean()
    
    if not files:
        print("✅ 没有需要清理的文件")
        return
    
    # 按类型分组
    by_type = {}
    total_size = 0
    for ftype, fpath in files:
        if ftype not in by_type:
            by_type[ftype] = []
        by_type[ftype].append(fpath)
        if fpath.is_file():
            total_size += fpath.stat().st_size
    
    print("=" * 60)
    print("🧹 可清理的文件")
    print("=" * 60)
    
    for ftype, fpaths in by_type.items():
        type_names = {
            "log": "📄 旧日志文件",
            "screenshot": "🖼️  临时截图",
            "temp_json": "📋 临时JSON",
            "temp_output": "📝 测试输出",
            "temp_backup_dir": "📦 临时备份目录"
        }
        print(f"\n{type_names.get(ftype, ftype)}:")
        for fpath in fpaths:
            if fpath.is_file():
                size = fpath.stat().st_size
                print(f"  - {fpath} ({format_size(size)})")
            else:
                print(f"  - {fpath}/ (目录)")
    
    print(f"\n总计: {len(files)} 项, {format_size(total_size)}")
    print("=" * 60)
    
    # 检查是否需要清理
    if "--yes" in sys.argv:
        confirm = "y"
    else:
        confirm = input("\n确认清理? (y/N): ").strip().lower()
    
    if confirm == "y":
        removed = 0
        for ftype, fpath in files:
            try:
                if fpath.is_file():
                    fpath.unlink()
                    removed += 1
                elif fpath.is_dir():
                    import shutil
                    shutil.rmtree(fpath)
                    removed += 1
            except Exception as e:
                print(f"❌ 删除失败 {fpath}: {e}")
        
        print(f"\n✅ 已清理 {removed} 项")
    else:
        print("\n❎ 已取消")


if __name__ == "__main__":
    main()
