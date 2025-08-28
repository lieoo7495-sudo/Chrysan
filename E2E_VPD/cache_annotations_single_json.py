import os
import json
import hashlib
import pickle
import inspect
import glob
from pathlib import Path
import mono3d  # 导入包含parse_annotation的模块

def load_annotations(ann_file, num_samples, img_prefix):
    """原始加载标注的函数（实际实现应替换为此函数）"""
    # 这里是您的实际加载逻辑
    print(f"执行原始加载函数: {ann_file}, {num_samples}, {img_prefix}")
    return [{"image": f"{img_prefix}/{i}.jpg", "annotation": "data"} for i in range(num_samples)]

def get_code_version():
    """获取关键函数的代码版本签名（包含parse_annotation）"""
    try:
        # 获取parse_annotation函数的源代码
        parse_func = mono3d.parse_annotation
        parse_source = inspect.getsource(parse_func)
        
        # 获取整个模块的源代码
        module_source = inspect.getsource(mono3d)
        
        # 生成组合代码的哈希
        combined_code = f"{parse_source}{module_source}"
        return hashlib.sha256(combined_code.encode()).hexdigest()
    except Exception as e:
        print(f"获取代码版本时出错: {e}")
        return "unknown_version"

def cached_load_annotations(ann_file, num_samples, img_prefix, cache_dir=".cache", return_cache_info=False):
    """
    带缓存信息的加载标注函数
    :param ann_file: 标注文件路径
    :param num_samples: 样本数量
    :param img_prefix: 图像路径前缀
    :param cache_dir: 缓存目录（默认为.cache）
    :param return_cache_info: 是否返回缓存信息
    :return: data_infos数据（如果return_cache_info为True，则返回(data, cache_info)）
    """
    # 确保缓存目录存在
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建参数签名（包含代码版本）
    params = {
        "ann_file": ann_file,
        "num_samples": num_samples,
        "img_prefix": img_prefix,
        "code_version": get_code_version()
    }
    
    # 生成唯一的参数哈希
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.sha256(param_str.encode()).hexdigest()
    
    # 构建缓存文件路径
    meta_file = Path(cache_dir) / f"meta_{param_hash}.json"
    pkl_file = Path(cache_dir) / f"data_{param_hash}.pkl"
    
    # 准备缓存信息对象
    cache_info = {
        "meta_file": str(meta_file),
        "pkl_file": str(pkl_file),
        "param_hash": param_hash,
        "exists": False,
        "valid": False
    }
    
    # 检查缓存是否存在且有效
    if meta_file.exists() and pkl_file.exists():
        cache_info["exists"] = True
        
        try:
            # 验证缓存有效性
            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)
                
            # 加载成功则标记为有效
            cache_info["valid"] = True
            print(f"命中缓存: {meta_file.name}")
            
            # 返回结果和缓存信息
            return (data, cache_info) if return_cache_info else data
            
        except Exception as e:
            print(f"缓存加载失败: {e}")
            cache_info["valid"] = False
    
    # 未命中缓存或缓存无效，执行原始加载
    data = load_annotations(ann_file, num_samples, img_prefix)
    
    # 保存元数据
    with open(meta_file, 'w') as f:
        json.dump({
            **params,
            "pkl_file": pkl_file.name,
            "param_hash": param_hash
        }, f, indent=2)
    
    # 保存数据
    with open(pkl_file, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"创建新缓存: {meta_file.name}")
    
    # 更新缓存信息
    cache_info.update({
        "exists": True,
        "valid": True,
        "created": True
    })
    
    # 返回结果和缓存信息
    return (data, cache_info) if return_cache_info else data

def list_cache_files(cache_dir=".cache"):
    """列出缓存目录中的所有元数据文件"""
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return []
    
    return [str(f) for f in cache_dir.glob("meta_*.json")]

def get_cache_info(meta_file_path):
    """获取指定元数据文件的详细信息"""
    meta_file = Path(meta_file_path)
    if not meta_file.exists():
        return {"error": "元数据文件不存在"}
    
    cache_dir = meta_file.parent
    cache_info = {"meta_file": str(meta_file)}
    
    try:
        # 加载元数据内容
        with open(meta_file, 'r') as f:
            meta_content = json.load(f)
            cache_info.update(meta_content)
        
        # 检查对应的pkl文件是否存在
        pkl_file = cache_dir / meta_content["pkl_file"]
        cache_info["pkl_file"] = str(pkl_file)
        cache_info["pkl_exists"] = pkl_file.exists()
        
        # 尝试加载数据以验证缓存有效性
        if pkl_file.exists():
            try:
                with open(pkl_file, 'rb') as f:
                    pickle.load(f)
                cache_info["valid"] = True
            except Exception as e:
                cache_info["valid"] = False
                cache_info["error"] = f"数据加载失败: {e}"
        else:
            cache_info["valid"] = False
            cache_info["error"] = "数据文件不存在"
    
    except Exception as e:
        cache_info["error"] = f"元数据加载失败: {e}"
    
    return cache_info