


```html
uvp_dataset/
├── uvp_dataset/               # 核心Python包
│   ├── __init__.py
│   ├── dataset.py             # 主Dataset类 (原StreamBevEffectiveV2)
│   ├── data_composer.py       # DataComposer组件
│   ├── load_storage.py        # LoadStorage组件
│   ├── constants.py           # 常量定义
│   ├── exceptions.py          # 自定义异常
│   └── utils/                 # 工具函数
│       └── data_utils.py
├── tests/                     # 单元测试
│   ├── test_dataset.py
│   └── test_data_composer.py
├── requirements.txt           # 三方依赖
├── setup.py                   # 安装配置
└── examples/                  # 使用示例
    ├── ufo_integration.py
    └── verl_integration.py
```


命名空间冲突问题
```python
import importlib.util
import sys
import os

# 定义两个模块的路径
original_path = '/path/to/original/SBEffv2.py'
new_path = '/path/to/new/SBEffv2.py'

# 加载 original
spec_original = importlib.util.spec_from_file_location("original_sbeff", original_path)
original_sbeff = importlib.util.module_from_spec(spec_original)
# 将模块所在目录加入 sys.path（局部）
original_dir = os.path.dirname(original_path)
sys.path.insert(0, original_dir)
spec_original.loader.exec_module(original_sbeff)
sys.path.remove(original_dir)

# 加载 new
spec_new = importlib.util.spec_from_file_location("new_sbeff", new_path)
new_sbeff = importlib.util.module_from_spec(spec_new)
new_dir = os.path.dirname(new_path)
sys.path.insert(0, new_dir)
spec_new.loader.exec_module(new_sbeff)
sys.path.remove(new_dir)
```

```python
def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    old_path = sys.path[:]
    sys.path.insert(0, os.path.dirname(path))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old_path
    return module

original = load_module_from_path("original", "/path/to/original/SBEffv2.py")
new = load_module_from_path("new", "/path/to/new/SBEffv2.py")
```

隔离导入，包含路径
```python
import importlib.util
import sys
import os

def load_isolated(name, py_file_path):
    spec = importlib.util.spec_from_file_location(name, py_file_path)
    module = importlib.util.module_from_spec(spec)

    original_path = sys.path[:]

    module_dir = os.path.dirname(os.path.abspath(py_file_path))
    sys.path.insert(0, module_dir)

    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_path

    return module

original = load_isolated("original_sbeff", "/abs/path/to/original/SBEffv2.py")
new      = load_isolated("new_sbeff",      "/abs/path/to/new/SBEffv2.py")
```

```python
import importlib.util
import sys
import os

def load_package_module(package_root, module_name, alias):
    original_path = sys.path[:]

    sys.path.insert(0, os.path.dirname(package_root))

    try:
        loader = importlib.machinery.PathFinder.find_module(
            os.path.basename(package_root), [os.path.dirname(package_root)]
        )
        if loader is None:
            raise ImportError(f"Cannot find package {package_root}")

        pkg = loader.load_module()

        module = importlib.import_module(f"{pkg.__name__}.{module_name}")
    finally:
        sys.path[:] = original_path

    return module

original = load_package_module("/abs/path/to/original", "SBEffv2", "original")
new      = load_package_module("/abs/path/to/new",      "SBEffv2", "new")
```

```python
import os, sys, importlib.util

def mount_pkg(real_dir, fake_name):
    """
    把 real_dir 下的包结构挂到 sys.modules[fake_name] 下，
    之后就可以 from fake_name.xxx import yyy
    """
    real_dir = os.path.abspath(real_dir)
    sys.path.insert(0, real_dir)            # 临时放到最前面
    spec = importlib.util.spec_from_file_location(
        fake_name,
        os.path.join(real_dir, "uvp_module", "__init__.py")
    )
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[fake_name] = pkg
    spec.loader.exec_module(pkg)
    return fake_name

# 挂载两份
original_name = mount_pkg("/abs/path/to/original", "original_uvp")
new_name      = mount_pkg("/abs/path/to/new",      "new_uvp")

# 现在可以直接 from import
from original_uvp.datasets_v2.dataset_streameffective import StreamBevV2 as StreamBevV2_original
from new_uvp.datasets_v2.dataset_streameffective      import StreamBevV2 as StreamBevV2_new

# 验证
print(StreamBevV2_original is StreamBevV2_new)  # False
```
