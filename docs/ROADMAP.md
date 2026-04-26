# 开发路线图

**文档版本**: v2.1  
**更新日期**: 2026-04-19  
**当前版本**: v0.6.0

---

## 版本历史

| 版本 | 发布日期 | 主要功能 |
|------|----------|----------|
| v0.1.0 | 2026-04-11 | MVP: 桌面自动化、10个任务、YOLO检测 |
| v0.2.0 | 2026-04-12 | 浏览器集成：Playwright、10+浏览器操作 |
| v0.2.1 | 2026-04-12 | 任务录制：桌面+浏览器混合录制 |
| v0.3.0 | 2026-04-13 | VLM智能模式：Kimi Coding API集成 |
| v0.3.1 | 2026-04-13 | 稳定性优化：28个预置任务、多重选择器、智能重试 |
| v0.4.0 | 2026-04-17 | Office自动化(Excel/Word)、64预置任务、智能定位、插件系统 |
| v0.5.0 | 2026-04-19 | 本地VLM支持(Qwen2-VL)、任务学习增强(坐标适配/模式提取/任务推荐) |
| v0.6.0 | 2026-04-25 | 任务调度器、批量任务执行、统一异常处理、GUI编辑器、65+预置任务 |

---

## v0.4.0 已完成功能

### 目标
提升任务成功率，扩展应用场景 ✅

### 功能清单

#### 1. Excel/Word 自动化 ✅
- [x] 读取/写入 Excel 单元格 (`ExcelController.write_cell/read_cell`)
- [x] 批量写入和图表生成 (`write_range`, `create_chart`)
- [x] Word 文档编辑 (`add_heading`, `add_paragraph`, `add_table`)
- [x] 模板填充 (`fill_template`, `replace_placeholder`)

#### 2. 更多预置任务 ✅ (64个)
- [x] 扩展到 50+ 预置任务 (实际 64 个)
- [x] 通用 actions: `file_copy`, `shell`, `clipboard`, `system_lock`, `screenshot_save`
- [x] 智能定位 actions: `locate_by_image`, `locate_by_text`, `locate_relative`, `locate_relation`, `wait_for`
- [x] 插件 actions: `plugin_invoke`, `plugin_list`

#### 3. 智能元素定位增强 ✅
- [x] 图像匹配定位 (`TemplateMatcher` + OpenCV `matchTemplate`)
- [x] 文字 OCR 定位 (`SmartLocator.locate_by_text` via PaddleOCR)
- [x] 相对坐标定位 (`SmartLocator.locate_relative`)
- [x] 元素关系链定位 (`SmartLocator.locate_relation`: 上下左右)

#### 4. 插件系统 v1 ✅
- [x] 插件接口定义 (`PluginInterface`)
- [x] 插件加载器 (`PluginLoader`: 内置 + 用户目录)
- [x] 内置插件：数据库操作 (`DatabasePlugin`: SQLite)
- [x] 内置插件：API 调用 (`APIPlugin`: HTTP GET/POST/PUT/DELETE)

---

## v0.5.0 已完成功能

### 目标
降低使用成本，提升隐私安全 ✅

### 功能清单

#### 1. 本地 VLM 支持 ✅
- [x] 集成本地视觉语言模型 (`LocalVLMClient`: Qwen2-VL-2B-Instruct)
- [x] 量化模型支持（4-bit / 8-bit 可选）
- [x] 延迟加载（首次使用时初始化，避免启动慢）
- [x] `VLMClient(provider="local")` 统一接口

#### 2. 任务学习增强 ✅
- [x] 坐标适配器 (`CoordinateAdapter`): 录制回放时自动重定位
  - 浏览器模式保留 CSS 选择器
  - 桌面模式支持窗口相对坐标 + 屏幕范围回退
- [x] 模式提取器 (`PatternExtractor`): 从多录制提取通用操作模式
  - 最长公共子序列 (LCS) 算法
  - 相似录制查找
- [x] 任务推荐器 (`TaskRecommender`)
  - 基于窗口标题推荐 (`recommend_by_window`)
  - 基于操作历史推荐下一步 (`recommend_by_history`)
- [x] 统一入口 (`TaskLearningEngine`) 集成到 `TaskExecutor`

#### 3. 批量任务与调度 (v0.6.0) ✅
- [x] 批量执行多个任务（顺序/并行）
- [x] 任务调度器（interval / cron / at）
- [x] 结果汇总报告（JSON / Markdown / HTML）
- [x] 统一异常处理体系

---

## v1.0.0 目标

### 目标
企业级稳定版本

### 功能清单

#### 1. 跨平台优化
- [ ] Windows 深度优化
- [ ] macOS 完整支持
- [ ] Linux 服务器支持

#### 2. 多显示器支持
- [ ] 多显示器检测
- [ ] 跨显示器操作
- [ ] 指定显示器执行

#### 3. 图形化界面
- [x] 任务编辑器 GUI（tkinter，v0.5.0）
- [ ] 实时执行监控
- [ ] 可视化任务构建器

#### 4. 企业级特性
- [ ] 执行日志审计
- [ ] 权限控制
- [ ] 敏感信息脱敏
- [ ] 性能监控

---

## 技术债务

### 待优化
- [ ] 消除 tkinter 线程警告
- [ ] 优化 YOLO 模型加载时间
- [ ] 减少内存占用
- [ ] 提升元素检测准确率

### 待重构
- [x] 统一错误处理（v0.6.0）
- [ ] 完善类型注解
- [ ] 优化测试覆盖率
- [ ] 文档自动化生成

---

## 社区计划

### 开源贡献
- [ ] 完善贡献指南
- [ ] Issue 模板
- [ ] PR 流程优化
- [ ] 社区讨论区

### 生态建设
- [ ] 任务市场（分享预置任务）
- [ ] 插件市场
- [ ] 教程视频
- [ ] 案例库

---

## 长期愿景

> "让每个人都能用自然语言控制计算机"

### 3年目标
- 成为开源桌面自动化领域 #1 项目
- 支持 1000+ 预置任务
- 企业级用户 100+
- 活跃开发者 50+

### 技术方向
- 端到端视觉语言模型
- 强化学习优化
- 跨应用智能规划
- 语音交互

---

**欢迎提出建议！通过 GitHub Issue 参与讨论。**
