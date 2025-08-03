import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS

# 配置信息
JSON_FILE_PATH = 'mock.json'  # JSON 文件路径
PORT = 8009  # 服务端口
HOST = '0.0.0.0'  # 监听所有网络接口

# 确保 JSON 文件存在
if not os.path.exists(JSON_FILE_PATH):
    print(f"Warning: {JSON_FILE_PATH} not found. Using empty data.")
    default_data = {
        "modelConfigs": {},
        "evaluationStatus": {},
        "commonDatasets": {
            "standard": [],
            "COT": []
        },
        "datasets": {
            "predefined": []
        },
        "evaluationMetrics": {},
        "modelTypes": {},
        "systemConfig": {},
        "metadata": {
            "version": "1.0.0",
            "description": "Default AutoEval configuration"
        }
    }
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, indent=2, ensure_ascii=False)
    print(f"Created default JSON file: {JSON_FILE_PATH}")

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 辅助函数：读取 JSON 文件
def read_json_file():
    """读取并解析 JSON 文件"""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "JSON file not found"
    except json.JSONDecodeError:
        return None, "Invalid JSON format"

# 辅助函数：写入 JSON 文件
def write_json_file(data):
    """将数据写入 JSON 文件"""
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True, None
    except Exception as e:
        return False, str(e)

# 路由：根路径 - 返回index.html
@app.route('/')
def index():
    """默认返回index.html页面"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "index.html not found", 404

# 路由：静态文件服务
@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    # 检查文件是否存在
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    else:
        return f"File {filename} not found", 404

# 路由：获取整个 JSON 配置
@app.route('/config', methods=['GET'])
def get_config():
    """返回整个 JSON 配置"""
    data, error = read_json_file()
    if error:
        return jsonify({"error": error}), 404
    return jsonify(data)

# 路由：更新配置
@app.route('/update', methods=['POST'])
def update_config():
    """更新 JSON 文件的内容"""
    # 验证请求内容
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # 获取更新数据
    update_data = request.get_json()

    # 读取当前配置
    current_config, error = read_json_file()
    if error:
        return jsonify({"error": error}), 404

    # 应用更新（深度合并）
    def deep_merge(target, source):
        """深度合并两个字典"""
        for key, value in source.items():
            if isinstance(value, dict):
                node = target.setdefault(key, {})
                deep_merge(node, value)
            else:
                target[key] = value
        return target

    # 执行更新
    updated_config = deep_merge(current_config, update_data)

    # 保存更新
    success, error = write_json_file(updated_config)
    if not success:
        return jsonify({"error": f"Failed to save file: {error}"}), 500

    return jsonify({"status": "success", "message": "Configuration updated"})

# 路由：获取评测状态数据
@app.route('/evaluated', methods=['GET'])
def get_evaluated():
    """返回评测状态数据"""
    data, error = read_json_file()
    if error:
        return jsonify({"error": error}), 404

    # 提取评测状态和通用数据集
    evaluation_status = data.get('evaluationStatus', {})
    common_datasets = data.get('commonDatasets', {
        "standard": [],
        "COT": []
    })

    return jsonify({
        "status": "success",
        "evaluation_status": evaluation_status,
        "common_datasets": common_datasets,
        "message": "评测状态数据加载成功"
    })

# 路由：健康检查
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "message": "AutoEval WebUI service is running",
        "port": PORT,
        "json_file": JSON_FILE_PATH
    })

# 路由：获取数据集信息
@app.route('/datasets', methods=['GET'])
def get_datasets():
    """获取数据集信息"""
    data, error = read_json_file()
    if error:
        return jsonify({"error": error}), 404

    datasets_info = {
        "predefined": data.get('datasets', {}).get('predefined', []),
        "categories": data.get('datasets', {}).get('categories', {}),
        "evaluationMetrics": data.get('evaluationMetrics', {})
    }

    return jsonify({
        "success": True,
        "data": datasets_info
    })

# 路由：获取系统配置
@app.route('/system-config', methods=['GET'])
def get_system_config():
    """获取系统配置"""
    data, error = read_json_file()
    if error:
        return jsonify({"error": error}), 404

    system_config = data.get('systemConfig', {})

    return jsonify({
        "success": True,
        "data": system_config
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({"error": "Internal server error"}), 500

# 启动服务器
def run_server():
    """运行Flask服务器"""
    print(f"Starting AutoEval WebUI server...")
    print(f"Server will run on: http://{HOST}:{PORT}")
    print(f"Default page: http://localhost:{PORT}/")
    print(f"API endpoints:")
    print(f"  - GET  /config          - 获取配置")
    print(f"  - POST /update          - 更新配置")
    print(f"  - GET  /evaluated       - 获取评测状态")
    print(f"  - GET  /health          - 健康检查")
    print(f"  - GET  /datasets        - 获取数据集信息")
    print(f"  - GET  /system-config   - 获取系统配置")
    print(f"Static files served from current directory")
    print(f"Press Ctrl+C to stop the server")
    
    app.run(host=HOST, port=PORT, debug=True)

if __name__ == '__main__':
    run_server()
