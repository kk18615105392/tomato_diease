@echo off
chcp 65001 >nul
echo ========================================
echo  番茄病虫害系统 - 环境安装（首次运行）
echo ========================================
echo.

cd /d %~dp0backend

echo [1/2] 安装 Python 依赖（含 ultralytics / torch）...
python -m pip install -U pip
python -m pip install -r requirements.txt

echo.
echo 注册 YOLOv8 自定义模块 MLCA / CBAM / PFA ...
python ultralytics_patch.py

echo.
echo 验证 ultralytics ...
python -c "from ultralytics import YOLO; print('ultralytics OK')"
if errorlevel 1 (
    echo.
    echo 安装失败，请确认已安装 Python 3.10+ 且 pip 可用
    pause
    exit /b 1
)

cd /d %~dp0frontend
echo.
echo [2/2] 安装前端依赖...
call npm install

echo.
echo ========================================
echo  安装完成！接下来双击 start.bat 启动
echo ========================================
pause
