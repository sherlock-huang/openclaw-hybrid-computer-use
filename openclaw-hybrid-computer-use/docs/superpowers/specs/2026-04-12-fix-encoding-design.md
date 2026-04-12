# 修复中文乱码设计文档

**日期:** 2026-04-12  
**问题:** Windows 控制台显示中文为乱码 (����)  
**原因:** 控制台代码页为 GBK (936)，但程序输出 UTF-8

---

## 解决方案

### 方案1: 程序启动时设置 UTF-8 代码页 (推荐)

在 `src/__init__.py` 或 `src/__main__.py` 开头添加：

```python
import sys
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)  # UTF-8
    kernel32.SetConsoleOutputCP(65001)  # UTF-8
```

### 方案2: 设置 stdout/stderr 编码

```python
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### 方案3: 使用 `chcp` 命令 (用户侧)

在运行程序前执行：
```bash
chcp 65001
py -m src ...
```

**选择方案1**，对用户透明，无需手动设置。

---

## 实施步骤

1. 修改 `src/__init__.py` 添加编码设置
2. 测试中文输出是否正常
3. 更新文档说明

---

## 影响范围

- 所有使用中文的输出都会修复
- 日志文件不受影响（已正确处理）
- 仅 Windows 平台生效
