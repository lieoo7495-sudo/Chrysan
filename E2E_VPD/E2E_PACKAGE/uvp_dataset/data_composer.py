class DataComposer:
    def __init__(self, config: Dict):
        self._init_from_config(config)
    
    def compose(self, raw_data: Dict) -> Dict:
        """保持与原版完全相同的数据组合逻辑"""
        # 原样迁移数据组合逻辑
        processed = {}
        processed['features'] = self._extract_features(raw_data)
        # ... 其他处理
        return processed