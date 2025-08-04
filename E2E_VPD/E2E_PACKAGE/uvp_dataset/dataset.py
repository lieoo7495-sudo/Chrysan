from typing import Any, Dict, Iterator
from .data_composer import DataComposer
from .load_storage import LoadStorage

class UVPDataset:
    def __init__(self, config: Dict[str, Any]):
        """
        保持与原StreamBevEffectiveV2相同的接口
        Args:
            config: 与原实现完全兼容的配置字典
        """
        self.loader = LoadStorage(config['storage'])
        self.composer = DataComposer(config['composer'])
        self._init_parameters(config)
    
    def __iter__(self) -> Iterator[Dict]:
        """保持与原版完全相同的迭代接口"""
        for raw_data in self.loader:
            yield self.composer.compose(raw_data)
    
    def _init_parameters(self, config: Dict):
        """初始化各种参数，从原实现中迁移过来"""
        # 保持与原版完全相同的参数初始化逻辑
        self.batch_size = config.get('batch_size', 32)
        # ... 其他参数