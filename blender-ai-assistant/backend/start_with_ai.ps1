# Blender AI 助手启动脚本（启用 AI）
# PowerShell 版本

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Blender AI 助手服务器启动" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 刷新环境变量
Write-Host "[1/3] 刷新环境变量..." -ForegroundColor Yellow
$env:DASHSCOPE_API_KEY = [Environment]::GetEnvironmentVariable("DASHSCOPE_API_KEY", "User")

if ($env:DASHSCOPE_API_KEY) {
    $keyPreview = $env:DASHSCOPE_API_KEY.Substring(0, [Math]::Min(20, $env:DASHSCOPE_API_KEY.Length))
    Write-Host "  |____ DASHSCOPE_API_KEY: $keyPreview..." -ForegroundColor Green
    Write-Host "  |____ AI 模式: 已启用" -ForegroundColor Green
} else {
    Write-Host "  |____ DASHSCOPE_API_KEY: 未设置" -ForegroundColor Yellow
    Write-Host "  |____ AI 模式: 规则引擎（降级）" -ForegroundColor Yellow
    Write-Host "`n  提示：要启用完整 AI 功能，请设置环境变量" -ForegroundColor Yellow
    Write-Host '  运行：[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "sk-your-key", "User")' -ForegroundColor Yellow
}
Write-Host ""

# 检查 Python
Write-Host "[2/3] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  |____ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  |____ Python 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host "  |____ 请安装 Python 3.10+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 启动服务器
Write-Host "[3/3] 启动服务器..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

try {
    python main.py
} catch {
    Write-Host "`n发生错误: $_" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "服务器已停止" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "按回车键退出"
