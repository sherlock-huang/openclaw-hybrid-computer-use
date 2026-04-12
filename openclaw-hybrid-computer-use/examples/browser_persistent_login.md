# 浏览器持久化登录说明

## 问题
之前每次运行任务都要重新登录，因为浏览器是全新的无痕模式。

## 解决方案
现在浏览器使用**持久化用户数据目录**（`browser_data/`），登录状态会保存。

## 使用方法

### 第一次使用（登录）

1. 运行抖音任务：
```bash
py -m src execute examples/douyin_search.json
```

2. 在浏览器中**手动登录**抖音账号

3. 任务完成后，登录状态自动保存到 `browser_data/` 目录

### 后续使用（免登录）

再次运行任务：
```bash
py -m src execute examples/douyin_search.json
```

这次**不需要登录**，直接就是已登录状态！

## 技术细节

- 用户数据目录：`browser_data/`
- 包含：cookies、localStorage、登录状态、缓存
- 多个任务共享同一个用户数据目录

## 注意事项

1. **隐私安全**：`browser_data/` 包含你的登录信息，不要分享给他人
2. **切换账号**：删除 `browser_data/` 目录即可清除登录状态
3. **不同网站**：同一个浏览器数据目录可以用于多个网站

## 配置

在 `src/core/config.py` 中修改：
```python
browser_user_data_dir: Optional[str] = "browser_data"  # 用户数据目录
```

设为 `None` 则使用无痕模式（每次都要重新登录）。
