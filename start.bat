@echo off
chcp 65001 >nul
echo ========================================
echo  番茄病虫害智能诊断系统 - 一键启动
echo ========================================
echo.

REM 使用 pytorch_gpu 环境（YOLOv8 消融实验需要 ultralytics）
call conda activate pytorch_gpu

start "后端 Flask :5000" cmd /k "cd /d %~dp0backend && conda activate pytorch_gpu && python app.py"
timeout /t 2 /nobreak >nul
start "前端 Vue :5173" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo 已打开两个窗口（后端使用 conda 环境 pytorch_gpu）
echo   后端  http://127.0.0.1:5000
echo   前端  http://localhost:5173
echo.
echo 启动后请确认后端窗口显示: ultralytics: OK
echo 若 5000 端口被占用，先关闭旧的 python app.py 窗口
echo.
echo 请在浏览器打开: http://localhost:5173
pause
