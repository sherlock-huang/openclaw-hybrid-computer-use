# 修复 PowerShell 中文乱码

## 问题现象

在 PowerShell 中运行 Python 脚本时，中文显示为乱码：
```
Ϣ˵Ϻ
```

## 解决方案

### 方案一：临时修复（推荐）

在 PowerShell 中执行以下命令：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

然后运行脚本：
```powershell
py wechat_send.py "张三" "晚上好！"
```

### 方案二：使用 CMD（最简单）

不使用 PowerShell，改用 CMD：

```cmd
wechat_send_cmd.bat "张三" "晚上好！"
```

或直接在 CMD 中运行：
```cmd
py wechat_send.py "张三" "晚上好！"
```

### 方案三：永久修复

以管理员身份运行 PowerShell，执行：

```powershell
# 设置当前会话
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 永久保存到配置文件
$profileContent = @"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8
"@

Add-Content -Path $PROFILE -Value $profileContent
```

然后重启 PowerShell。

### 方案四：修改系统区域设置

1. 打开 **设置** -> **时间和语言** -> **语言和区域**
2. 点击 **管理语言设置**
3. 点击 **更改系统区域设置**
4. 勾选 **"Beta: 使用 Unicode UTF-8 提供全球语言支持"**
5. 重启电脑

## 推荐做法

| 场景 | 推荐方案 |
|------|----------|
| 临时使用 | 方案一：设置编码变量 |
| 日常使用 | 方案二：使用 CMD |
| 长期使用 PowerShell | 方案三：修改配置文件 |
| 彻底解决 | 方案四：修改系统设置 |

## 验证修复

修复后，运行以下命令应该显示正常中文：

```powershell
py wechat_send.py "文件传输助手" "测试"
```

预期输出：
```
Sending to: 文件传输助手
Message: 测试
Confirm? (y/n):
```
