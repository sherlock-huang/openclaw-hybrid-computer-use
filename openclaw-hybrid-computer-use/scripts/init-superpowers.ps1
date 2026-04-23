# 新项目 Superpowers 初始化脚本
# 在项目根目录运行: .\init-superpowers.ps1

Write-Host "🚀 初始化 Superpowers 项目配置..." -ForegroundColor Green

# 创建目录
New-Item -ItemType Directory -Force -Path "docs\superpowers\specs" | Out-Null
New-Item -ItemType Directory -Force -Path "docs\superpowers\plans" | Out-Null
Write-Host "✅ 创建目录: docs/superpowers/{specs,plans}/"

# 创建 AGENTS.md (如果不存在)
if (-not (Test-Path "AGENTS.md")) {
    @'
# 项目配置

本项目使用 Superpowers 技能系统进行开发。

## 快速开始

```
# 新功能设计
"请用 Superpowers 设计 XX 功能"

# 调试问题  
"用 systematic-debugging 定位这个 bug"

# 代码审查
"使用 requesting-code-review 审查这段代码"
```

## 项目文档

- `docs/superpowers/specs/` - 设计文档（由 brainstorming 创建）
- `docs/superpowers/plans/` - 实现计划（由 writing-plans 创建）

---

**Superpowers 版本**: main  
**安装时间**: 2026-04-11
'@ | Out-File -FilePath "AGENTS.md" -Encoding utf8
    Write-Host "✅ 创建 AGENTS.md"
} else {
    Write-Host "⚠️  AGENTS.md 已存在，跳过"
}

Write-Host ""
Write-Host "🎉 初始化完成！可以开始使用 Superpowers:" -ForegroundColor Green
Write-Host "   示例: '请用 Superpowers 设计新功能'" -ForegroundColor Cyan
