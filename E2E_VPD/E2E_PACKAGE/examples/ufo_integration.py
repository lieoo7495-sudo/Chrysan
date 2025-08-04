from ufo.dataloader import BaseDataLoader
from uvp_dataset import UVPDataset

class UVPDataLoaderAdapter(BaseDataLoader):
    def __init__(self, dataset_config):
        self.dataset = UVPDataset(dataset_config)
    
    def get_batch(self):
        return next(iter(self.dataset))