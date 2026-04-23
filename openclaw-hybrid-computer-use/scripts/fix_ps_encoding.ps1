# 修复 PowerShell 中文乱码
# 以管理员身份运行此脚本

Write-Host "修复 PowerShell 中文编码..." -ForegroundColor Green

# 方法1: 设置当前会话编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 方法2: 永久修复（修改配置文件）
$profilePath = $PROFILE

if (!(Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force
    Write-Host "创建配置文件: $profilePath" -ForegroundColor Yellow
}

# 添加编码设置到配置文件
$encodingConfig = @"
# 设置 UTF-8 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
"@

# 检查是否已存在
$content = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($content -notcontains "OutputEncoding = [System.Text.Encoding]::UTF8") {
    Add-Content -Path $profilePath -Value "`n$encodingConfig"
    Write-Host "已添加编码配置到配置文件" -ForegroundColor Green
} else {
    Write-Host "编码配置已存在" -ForegroundColor Yellow
}

# 方法3: 设置系统区域（需要重启）
Write-Host "`n提示: 如果仍有问题，请检查系统区域设置:" -ForegroundColor Cyan
Write-Host "  设置 -> 时间和语言 -> 语言和区域 -> 管理语言设置" -ForegroundColor Cyan
Write-Host "  -> 更改系统区域设置 -> 勾选'Beta:使用 Unicode UTF-8'" -ForegroundColor Cyan

Write-Host "`n修复完成！请重启 PowerShell 查看效果。" -ForegroundColor Green
pause
