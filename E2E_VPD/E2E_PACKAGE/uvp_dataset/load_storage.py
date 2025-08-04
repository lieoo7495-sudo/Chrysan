class LoadStorage:
    def __init__(self, config: Dict):
        self.storage_type = config['type']
        # 初始化存储后端
    
    def __iter__(self):
        """保持与原版相同的数据加载逻辑"""
        while True:
            yield self._load_next_batch()