
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