# 示例任务

## 抖音搜索 (douyin_search.json)

在抖音网页版搜索UP主并查看视频。

### 使用方法

1. 确保已登录抖音网页版（cookies 会保留）
2. 运行任务：
   ```bash
   py -m src execute examples/douyin_search.json
   ```

### 自定义搜索

编辑 `douyin_search.json`，修改第 4 个任务的 `value`：

```json
{
  "action": "browser_type",
  "target": "[data-e2e='search-input']",
  "value": "你想搜索的UP主名称"
}
```

### 注意事项

- 抖音网站结构可能变化，如果失败请检查选择器
- 首次运行需要登录抖音账号
- 截图保存在当前目录
