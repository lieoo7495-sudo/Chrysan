
```html
tests/
├── test_dataset_integrity.py       # 主测试文件
├── fixtures/                       # 测试数据
│   ├── sample_data_001.pkl         # 与原框架相同的测试数据
│   └── expected_outputs_001.pkl    # 预期输出样本
└── utils/
    └── compare_utils.py            # 比较工具函数
```

```python
import pytest
import numpy as np
from deepdiff import DeepDiff
from uvp_dataset.dataset import UVPDataset

class TestDatasetIntegrity:
    """测试数据完整性和准确性的测试套件"""
    
    @pytest.fixture
    def original_dataset(self):
        """原框架中的Dataset实例"""
        from tasks.bev_task.uvp_model.datasets_v2.dataset_streameffective import StreamBevEffectiveV2
        return StreamBevEffectiveV2(config=original_config)
    
    @pytest.fixture
    def new_dataset(self):
        """新架构的Dataset实例"""
        return UVPDataset(config=test_config)
    
    @pytest.fixture
    def sample_indexes(self):
        """覆盖各种情况的测试索引"""
        return [0, 100, -1]  # 首样本、中间样本、末尾样本
    
    def test_output_structure(self, original_dataset, new_dataset):
        """测试输出结构一致性"""
        orig_seq = original_dataset[0]
        new_seq = new_dataset[0]
        
        # 验证返回元素数量
        assert len(orig_seq) == 3
        assert len(new_seq) == 3
        
        # 验证元素名称
        assert hasattr(orig_seq, '_fields')  # 如果是namedtuple
        assert orig_seq._fields == ('seq_input', 'seq_labels', 'seq_extras')
        
    def test_data_integrity(self, original_dataset, new_dataset, sample_indexes):
        """测试数据内容一致性"""
        for idx in sample_indexes:
            orig_output = original_dataset[idx]
            new_output = new_dataset[idx]
            
            # 对三个返回值分别进行比较
            self._compare_sequences(orig_output.seq_input, new_output.seq_input)
            self._compare_sequences(orig_output.seq_labels, new_output.seq_labels)
            self._compare_sequences(orig_output.seq_extras, new_output.seq_extras)
    
    def _compare_sequences(self, orig, new):
        """比较两个数据序列的深层结构"""
        # 类型检查
        assert type(orig) == type(new)
        
        # 数据结构比较
        if isinstance(orig, (np.ndarray, torch.Tensor)):
            assert orig.shape == new.shape
            assert orig.dtype == new.dtype
            np.testing.assert_allclose(orig, new, rtol=1e-5, atol=1e-8)
        elif isinstance(orig, dict):
            assert set(orig.keys()) == set(new.keys())
            for k in orig:
                self._compare_sequences(orig[k], new[k])
        elif isinstance(orig, (list, tuple)):
            assert len(orig) == len(new)
            for o, n in zip(orig, new):
                self._compare_sequences(o, n)
        else:
            assert orig == new
```

```python
def test_data_structure_consistency():
    """测试返回值的完整数据结构"""
    sample = dataset[0]
    
    # 验证seq_input结构
    assert isinstance(sample.seq_input, dict)
    assert 'sensor_data' in sample.seq_input
    assert 'timestamp' in sample.seq_input
    assert isinstance(sample.seq_input['sensor_data'], np.ndarray)
    
    # 验证seq_labels结构
    assert isinstance(sample.seq_labels, dict)
    assert 'class_labels' in sample.seq_labels
    assert 'regression_targets' in sample.seq_labels
    
    # 验证seq_extras结构
    assert isinstance(sample.seq_extras, dict)
    assert 'metadata' in sample.seq_extras
    assert 'auxiliary_info' in sample.seq_extras
```

```python
def test_numerical_equivalence(original_dataset, new_dataset):
    """测试数值精度一致性"""
    orig = original_dataset[0]
    new = new_dataset[0]
    
    # 比较浮点数组
    np.testing.assert_allclose(
        orig.seq_input['sensor_data'], 
        new.seq_input['sensor_data'],
        rtol=1e-5,  # 相对容差
        atol=1e-8   # 绝对容差
    )
    
    # 比较整型标签
    np.testing.assert_array_equal(
        orig.seq_labels['class_labels'],
        new.seq_labels['class_labels']
    )
```

```python
@pytest.mark.parametrize("index", [
    0,                      # 第一个样本
    len(dataset)-1,         # 最后一个样本
    -1,                     # 负索引
    len(dataset)//2,        # 中间样本
    pytest.param(9999, marks=pytest.mark.xfail(raises=IndexError))  # 越界索引
])
def test_index_boundaries(index):
    """测试各种边界条件下的数据一致性"""
    orig = original_dataset[index]
    new = new_dataset[index]
    compare_outputs(orig, new)
```

## hight
```python
from deepdiff import DeepDiff

def compare_using_deepdiff(orig, new):
    """使用DeepDiff进行复杂结构比较"""
    diff = DeepDiff(
        orig, 
        new,
        ignore_order=True,
        significant_digits=6,
        exclude_paths=["root['timestamp']"]  # 排除可能变化的时间戳
    )
    assert not diff, f"发现差异: {diff}"
```

```python
def custom_comparator(orig, new):
    """处理特殊情况的比较逻辑"""
    if isinstance(orig, CustomType):
        return orig.value == new.value
    elif isinstance(orig, np.ndarray):
        return np.allclose(orig, new, atol=1e-6)
    return orig == new
```

```python
def test_metadata_consistency():
    """测试元数据的合理变化"""
    orig_extras = original_output.seq_extras
    new_extras = new_output.seq_extras
    
    # 允许某些字段变化
    assert orig_extras['metadata']['version'] == new_extras['metadata']['version']
    assert orig_extras['metadata']['source'] == new_extras['metadata']['source']
    
    # 允许时间类字段不同
    assert 'creation_time' in new_extras['metadata']
```

## 数据生存
```python
@pytest.fixture(scope="module")
def golden_data():
    """生成/加载基准测试数据"""
    data_path = "tests/fixtures/golden_samples.pkl"
    if not os.path.exists(data_path):
        generate_golden_samples(data_path)
    return load_pickle(data_path)

def generate_golden_samples(path):
    """使用原框架生成基准数据"""
    dataset = OriginalDataset(config)
    samples = [dataset[i] for i in range(10)]
    save_pickle(samples, path)
```

```python
def test_data_version_compatibility():
    """测试数据版本兼容性"""
    assert dataset.data_version == EXPECTED_VERSION
    assert dataset.schema_hash == GOLDEN_HASH
```

```sh
#!/bin/bash
# run_integrity_tests.sh

# 1. 使用原框架生成基准数据
python generate_golden_data.py --config original_config.yaml

# 2. 运行完整性测试
pytest tests/test_dataset_integrity.py -v --cov=uvp_dataset

# 3. 生成差异报告
python compare_reports.py --old golden_report.json --new current_report.json
```

```yml
# .github/workflows/integrity_test.yml
jobs:
  data-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install -e .
      - run: bash scripts/run_integrity_tests.sh
      - name: Upload diff report
        uses: actions/upload-artifact@v2
        with:
          name: data-diff-report
          path: reports/diff_report.json
```