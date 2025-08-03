@echo off
echo AutoEval WebUI 启动脚本
echo ========================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

REM 启动服务器
echo 启动AutoEval WebUI服务器...
echo 访问地址: http://localhost:8009/
echo 按 Ctrl+C 停止服务器
echo.

python app.py

pause 