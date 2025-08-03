#!/usr/bin/env python3
"""
AutoEval WebUI 启动脚本
用于启动Flask服务器
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import run_server
    print("AutoEval WebUI 启动中...")
    run_server()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖: pip install -r requirements.txt")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n服务器已停止")
except Exception as e:
    print(f"启动失败: {e}")
    sys.exit(1) 