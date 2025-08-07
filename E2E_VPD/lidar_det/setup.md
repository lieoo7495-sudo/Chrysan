
```
fnc/                      # 包名
├── fnc/
│   ├── __init__.py       # 一行暴露接口
│   └── _lib/
│       └── libfnc.so     # 已有文件
└── setup.py              # 纯搬运，无需编译
```

fnc/__init__.py
```
import os, ctypes, sys

# 计算 so 绝对路径（兼容 PyInstaller、zipapp 等）
_lib_path = os.path.join(os.path.dirname(__file__), "_lib", "libfnc.so")
try:
    _lib = ctypes.CDLL(_lib_path)
except OSError as e:
    raise RuntimeError(f"Cannot load libfnc.so: {e}") from e

# 声明函数原型：int add(int, int)
add = _lib.add
add.argtypes = (ctypes.c_int, ctypes.c_int)
add.restype  = ctypes.c_int
```
setup.py
```
from setuptools import setup, find_packages
setup(
    name="fnc",
    version="0.1.0",
    packages=find_packages(),
    package_data={"fnc": ["_lib/*.so"]},
    python_requires=">=3.7",
)
```


```
pip install .
python -m build
```


```
import ctypes, re, subprocess, pathlib
so = pathlib.Path('lidar_det_ext.so')

# 1) 列出所有“外部可见”的 C 函数符号
raw = subprocess.check_output(['nm', '-D', so]).decode()
funcs = re.findall(r' T ([^\s]+)', raw)

# 2) 过滤掉 C++ 修饰符（用 c++filt）
clean = subprocess.check_output(['c++filt'], input='\n'.join(funcs).encode()).decode().split()

print(clean)    # 这些就是 ctypes 可能能调到的 C 级函数名
```


2so
```
lidar_tools/                 # git 仓库根
├── pyproject.toml           # 现代打包首选
├── setup.py                 # 兼容旧版 pip（可选）
├── README.md
├── src/
│   └── lidar_tools/         # ← 真正的包目录
│       ├── __init__.py      # 自动加载 so 并暴露函数
│       ├── _libs/           # 存放两个 .so
│       │   ├── lidar_det_ext.so
│       │   └── voxel_layer.so
│       └── _ctypes_api.py   # 把 ctypes 声明集中写（可选）
└── tests/
    └── test_basic.py
```

src/lidar_tools/init.py
```
"""
lidar_tools: Python wrapper around lidar_det_ext.so & voxel_layer.so
"""
import os
import ctypes
from pathlib import Path

# 1. 计算 so 的绝对路径（无论用户从哪 import 都能找得到）
_PKG_DIR = Path(__file__).resolve().parent
_LIDAR_SO = _PKG_DIR / "_libs" / "lidar_det_ext.so"
_VOXEL_SO = _PKG_DIR / "_libs" / "voxel_layer.so"

# 2. 按依赖顺序加载
try:
    _voxel = ctypes.CDLL(str(_VOXEL_SO), ctypes.RTLD_GLOBAL)
    _lidar = ctypes.CDLL(str(_LIDAR_SO), ctypes.RTLD_GLOBAL)
except OSError as e:
    raise RuntimeError(f"Could not load native libraries: {e}") from e

# 3. 声明函数原型（示例，按你实际头文件改）
# --- voxel_layer.so ---
voxelize = _voxel.voxelize
voxelize.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int]
voxelize.restype  = ctypes.c_int

# --- lidar_det_ext.so ---
create_detector = _lidar.create_detector
create_detector.argtypes = [ctypes.c_int, ctypes.c_float]
create_detector.restype  = ctypes.c_void_p

destroy_detector = _lidar.destroy_detector
destroy_detector.argtypes = [ctypes.c_void_p]
destroy_detector.restype  = None

process = _lidar.process
process.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)]
process.restype  = ctypes.c_int

# 4. 暴露 __all__，方便 IDE 自动补全
__all__ = ["voxelize", "create_detector", "destroy_detector", "process"]
```

pyproject.toml
```
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lidar_tools"
version = "0.1.0"
description = "Lightweight ctypes wrapper for lidar native libs"
readme = "README.md"
requires-python = ">=3.7"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
lidar_tools = ["_libs/*.so"]
```

setup.py
```
from setuptools import setup, find_packages

setup(
    name="lidar_tools",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"lidar_tools": ["_libs/*.so"]},
    python_requires=">=3.7",
    zip_safe=False,   # 必须 False 才能正确解压 so
)
```

```
pip install .

python -m build
```