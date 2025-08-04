from verl.data_provider import DataProvider
from uvp_dataset import UVPDataset

class UVPDataProvider(DataProvider):
    def __init__(self, config):
        super().__init__()
        self.source = UVPDataset(config)
    
    def __next__(self):
        return self.source.__next__()