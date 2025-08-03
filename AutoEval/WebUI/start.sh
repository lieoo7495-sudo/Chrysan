#!/bin/bash

echo "AutoEval WebUI 启动脚本"
echo "========================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

# 启动服务器
echo "启动AutoEval WebUI服务器..."
echo "访问地址: http://localhost:8009/"
echo "按 Ctrl+C 停止服务器"
echo

python3 app.py 