# AutoEval WebUI Flask 应用

这是一个基于Flask的Web应用，提供AutoEval模型评测配置和状态管理的Web界面。

## 功能特性

- 🏠 **默认首页**: 访问根路径自动显示index.html
- 📁 **静态文件服务**: 支持访问所有静态文件（HTML、CSS、JS、JSON等）
- 🔧 **配置管理**: 提供RESTful API进行模型配置的读取和更新
- 📊 **评测状态**: 显示模型在各个数据集上的评测分数和状态
- 🔄 **智能降级**: 前端支持后端连接失败时自动切换到模拟数据
- 🌐 **跨域支持**: 启用CORS，支持跨域请求

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

#### 方法一：直接运行app.py
```bash
python app.py
```

#### 方法二：使用启动脚本
```bash
python run.py
```

### 3. 访问应用

服务器启动后，可以通过以下方式访问：

- **主页面**: http://localhost:8009/
- **数据管理器**: http://localhost:8009/data-manager.html
- **静态文件**: http://localhost:8009/文件名

## API 接口

### 配置管理

- `GET /config` - 获取完整配置
- `POST /update` - 更新配置
- `GET /config/<path>` - 获取特定路径的配置

### 评测状态

- `GET /evaluated` - 获取评测状态数据

### 系统信息

- `GET /health` - 健康检查
- `GET /datasets` - 获取数据集信息
- `GET /system-config` - 获取系统配置

## 文件结构

```
WebUI/
├── app.py              # Flask应用主文件
├── run.py              # 启动脚本
├── requirements.txt    # Python依赖
├── mock.json           # 模拟数据文件
├── index.html          # 主页面
├── data-manager.html   # 数据管理页面
├── script.js           # 前端JavaScript
├── mock.js             # 模拟数据管理
├── styles.css          # 样式文件
└── README.md           # 说明文档
```

## 配置说明

### 端口配置

在`app.py`中可以修改以下配置：

```python
PORT = 8009  # 服务端口
HOST = '0.0.0.0'  # 监听地址
JSON_FILE_PATH = 'mock.json'  # 数据文件路径
```

### 数据文件

应用使用`mock.json`作为数据源，包含：

- `modelConfigs`: 模型配置信息
- `evaluationStatus`: 评测状态和分数
- `commonDatasets`: 通用数据集列表
- `datasets`: 数据集分类信息
- `evaluationMetrics`: 评估指标
- `systemConfig`: 系统配置

## 开发说明

### 前端特性

- **智能降级**: 当后端不可用时，自动使用本地模拟数据
- **响应式设计**: 支持不同屏幕尺寸
- **实时更新**: 支持配置的实时更新和显示

### 后端特性

- **RESTful API**: 标准的REST接口设计
- **错误处理**: 完善的错误处理和状态码
- **文件服务**: 自动提供静态文件服务
- **跨域支持**: 启用CORS支持跨域请求

## 故障排除

### 常见问题

1. **端口被占用**
   - 修改`app.py`中的`PORT`变量
   - 或停止占用端口的其他服务

2. **依赖安装失败**
   - 确保Python版本 >= 3.7
   - 使用虚拟环境：`python -m venv venv && source venv/bin/activate`

3. **文件访问权限**
   - 确保应用有读取`mock.json`的权限
   - 确保有写入权限以保存配置更新

### 日志信息

启动时会显示以下信息：

```
Starting AutoEval WebUI server...
Server will run on: http://0.0.0.0:8009
Default page: http://localhost:8009/
API endpoints:
  - GET  /config          - 获取配置
  - POST /update          - 更新配置
  - GET  /evaluated       - 获取评测状态
  - GET  /health          - 健康检查
  - GET  /datasets        - 获取数据集信息
  - GET  /system-config   - 获取系统配置
Static files served from current directory
Press Ctrl+C to stop the server
```

## 许可证

本项目遵循MIT许可证。 