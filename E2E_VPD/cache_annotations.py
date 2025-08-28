import os
import json
import hashlib
import pickle
import uuid
from pathlib import Path

def load_annotations(ann_file, num_samples, img_prefix):
    """原始加载标注的函数（示例实现）"""
    # 这里是你的实际加载逻辑
    print(f"执行原始加载函数: {ann_file}, {num_samples}, {img_prefix}")
    return [{"image": f"{img_prefix}/{i}.jpg", "annotation": "data"} for i in range(num_samples)]

def cached_load_annotations(ann_file, num_samples, img_prefix, cache_dir=".cache"):
    """
    带缓存的加载标注函数
    :param ann_file: 标注文件路径
    :param num_samples: 样本数量
    :param img_prefix: 图像路径前缀
    :param cache_dir: 缓存目录（默认为.cache）
    :return: data_infos数据
    """
    # 确保缓存目录存在
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建参数签名
    params = {
        "ann_file": ann_file,
        "num_samples": num_samples,
        "img_prefix": img_prefix
    }
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.sha256(param_str.encode()).hexdigest()
    
    # 元数据文件路径
    meta_file = Path(cache_dir) / "cache_metadata.json"
    
    # 加载或初始化元数据
    if meta_file.exists():
        with open(meta_file, 'r') as f:
            cache_meta = json.load(f)
    else:
        cache_meta = {}
    
    # 检查是否存在有效缓存
    if param_hash in cache_meta:
        entry = cache_meta[param_hash]
        pkl_path = Path(cache_dir) / entry['pkl_file']
        
        if pkl_path.exists():
            print(f"命中缓存: {entry['pkl_file']}")
            with open(pkl_path, 'rb') as f:
                return pickle.load(f)
    
    # 未命中缓存，执行原始加载
    data_infos = load_annotations(ann_file, num_samples, img_prefix)
    
    # 生成唯一pkl文件名
    pkl_filename = f"cache_{uuid.uuid4().hex}.pkl"
    pkl_path = Path(cache_dir) / pkl_filename
    
    # 保存数据到pkl
    with open(pkl_path, 'wb') as f:
        pickle.dump(data_infos, f)
    
    # 更新元数据
    cache_meta[param_hash] = {
        **params,
        "pkl_file": pkl_filename
    }
    
    with open(meta_file, 'w') as f:
        json.dump(cache_meta, f, indent=2)
    
    print(f"缓存已保存: {pkl_filename}")
    return data_infos