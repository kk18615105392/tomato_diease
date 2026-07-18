# 番茄病虫害系统 - PowerShell 安装脚本（首次运行）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================"
Write-Host " 后端 Python 依赖"
Write-Host "========================================"
Set-Location (Join-Path $Root "backend")
python -m pip install -U pip
python -m pip install -r requirements.txt
python ultralytics_patch.py
python -c "from ultralytics import YOLO; print('ultralytics OK')"

Write-Host ""
Write-Host "========================================"
Write-Host " 前端 npm 依赖"
Write-Host "========================================"
Set-Location (Join-Path $Root "frontend")
npm install

Write-Host ""
Write-Host "安装完成。启动方式："
Write-Host "  终端1: cd backend; python app.py"
Write-Host "  终端2: cd frontend; npm run dev"
Write-Host "  浏览器: http://localhost:5173/diagnose"
