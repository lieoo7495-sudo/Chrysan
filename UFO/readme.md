# Det23D-Dataset

> **本数据集是从 [Det23D]中解耦出的独立数据集加载**，仅保留与数据读取、预处理、格式转换相关的核心代码，方便在其它项目或实验环境中复用 Det23D 的数据 pipeline

---

## 1. 目录结构

```
Det23D-Standalone-Dataset
├── Det23D
│   └── datasets
│       ├── mono3d.py          # 单目 3D 检测数据集封装
│       └── multifusiondataset.py  # 多模态/多视角融合数据集封装
├── infrastructure             # 工具类、通用组件
├── lib                        # 第三方依赖或编译扩展
├── tests                      # 单元测试 & 数据加载示例
└── README.md
```

---

## 2. 核心数据集说明

| 文件 | 功能 |
|---|---|
| `Det23D/datasets/mono3d.py` | 单目 3D 检测专用数据类 |
| `Det23D/datasets/multifusiondataset.py` | 多模态（LiDAR + Camera）、多视角 |

---

## 3. 装载方法（Pipeline 配置）

数据集**不内置**任何配置文件，仅暴露数据类接口。需在项目中通过 `pipeline` 字段显式指定数据加载流程。下面给出最小可运行示例：

```python
# pipeline_example.py
from Det23D.datasets import Mono3DDataset, MultiFusionDataset


```

### 关键字段说明
- `_mono3d_datasets['dataload']`：配置dataload
- `ann_file`：指向 Det23D 格式的 info 文件
- `pipeline`：一个 list，每个元素为 dict，包含 `type` 字段与对应参数；transforms, loading已于pipeline中支持
- `mono3d_train_pipeline`：mono3d数据加载pipeline
- `pv_dataset`：初始化`MultiFusionDataset`数据实例
- `train_dataloader`：通过`type='PvDataset'`使用adapter接口



---

## 4. 快速开始

1. Clone Det23D
   ```bash
   copy file to your project
   ```

2. 测试用例  
Det23D.tests
├── ts_dataset_MultiFusionDataset.py # MultiFusion用例
└── ts_pv_dataset.py # pv_adapter用例

---