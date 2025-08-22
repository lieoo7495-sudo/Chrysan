def print_det3d_data_sample(data_sample, indent=0):
    """
    递归打印 Det3DDataSample 的结构信息（shape, type）
    
    Args:
        data_sample (Det3DDataSample): 输入数据样本
        indent (int): 缩进层级（用于格式化输出）
    """
    indent_str = '    ' * indent
    
    # 打印 Det3DDataSample 基本信息
    print(f"{indent_str}Det3DDataSample (Type: {type(data_sample).__name__})")
    
    # 遍历所有属性
    for field_name in dir(data_sample):
        # 跳过私有属性和方法
        if field_name.startswith('_') or field_name in ['to', 'cpu', 'cuda']:
            continue
        
        # 获取属性值
        try:
            field_value = getattr(data_sample, field_name)
        except AttributeError:
            continue
        
        # 打印字段信息
        print(f"{indent_str}├── {field_name}: Type: {type(field_value).__name__}")
        
        # 处理 InstanceData 或 PointData
        if isinstance(field_value, (InstanceData, PointData)):
            print_instance_data(field_value, indent + 1)
        # 处理字典/列表等嵌套结构
        elif isinstance(field_value, (dict, list, tuple)):
            print_nested_data(field_value, indent + 1, prefix=field_name)
        # 处理 torch.Tensor 或其他有 shape 的对象
        elif hasattr(field_value, 'shape'):
            print(f"{indent_str}│   ├── Shape: {field_value.shape}")
        else:
            print(f"{indent_str}│   └── [Simple Type]")

def print_instance_data(instance_data, indent=0):
    """
    打印 InstanceData 或 PointData 的详细信息
    
    Args:
        instance_data (InstanceData|PointData): 实例数据
        indent (int): 缩进层级
    """
    indent_str = '    ' * indent
    
    # 打印类型信息
    data_type = 'InstanceData' if isinstance(instance_data, InstanceData) else 'PointData'
    print(f"{indent_str}├── {data_type} (Type: {type(instance_data).__name__})")
    
    # 打印元信息
    if hasattr(instance_data, '_metainfo_fields'):
        print(f"{indent_str}│   ├── Metainfo: {instance_data.metainfo}")
    
    # 打印所有数据字段
    for field_name in instance_data.keys():
        field_value = instance_data[field_name]
        
        # 打印字段基本信息
        print(f"{indent_str}│   ├── {field_name}: Type: {type(field_value).__name__}")
        
        # 处理有 shape 的对象
        if hasattr(field_value, 'shape'):
            print(f"{indent_str}│   │   ├── Shape: {field_value.shape}")
        # 处理嵌套结构
        elif isinstance(field_value, (dict, list, tuple)):
            print_nested_data(field_value, indent + 2, prefix=field_name)
        else:
            print(f"{indent_str}│   │   └── [Simple Type]")

def print_nested_data(data, indent=0, prefix=""):
    """
    打印嵌套数据（字典/列表/元组）
    
    Args:
        data: 嵌套数据
        indent: 缩进层级
        prefix: 前缀标签
    """
    indent_str = '    ' * indent
    
    # 打印容器基本信息
    if isinstance(data, dict):
        print(f"{indent_str}├── {prefix}: Dict (Length: {len(data)})")
        for key, value in data.items():
            print(f"{indent_str}│   ├── {key}: Type: {type(value).__name__}")
            if hasattr(value, 'shape'):
                print(f"{indent_str}│   │   ├── Shape: {value.shape}")
    elif isinstance(data, (list, tuple)):
        container_type = 'List' if isinstance(data, list) else 'Tuple'
        print(f"{indent_str}├── {prefix}: {container_type} (Length: {len(data)})")
        for i, item in enumerate(data):
            print(f"{indent_str}│   ├── {i}: Type: {type(item).__name__}")
            if hasattr(item, 'shape'):
                print(f"{indent_str}│   │   ├── Shape: {item.shape}")


# 使用示例
if __name__ == "__main__":
    import torch
    from mmengine.structures import InstanceData
    from mmdet3d.structures.bbox_3d import BaseInstance3DBoxes
    
    # 创建示例数据
    data_sample = Det3DDataSample()
    
    # 添加 3D 实例标注
    gt_instances_3d = InstanceData()
    gt_instances_3d.bboxes_3d = BaseInstance3DBoxes(torch.rand((5, 7)))
    gt_instances_3d.labels_3d = torch.randint(0, 3, (5,))
    gt_instances_3d.scores_3d = torch.rand((5,))
    data_sample.gt_instances_3d = gt_instances_3d
    
    # 添加预测结果
    pred_instances_3d = InstanceData()
    pred_instances_3d.bboxes_3d = BaseInstance3DBoxes(torch.rand((3, 7)))
    pred_instances_3d.labels_3d = torch.randint(0, 3, (3,))
    pred_instances_3d.scores_3d = torch.rand((3,))
    data_sample.pred_instances_3d = pred_instances_3d
    
    # 添加点云分割数据
    from mmdet3d.structures import PointData
    gt_pts_seg = PointData()
    gt_pts_seg.pts_semantic_mask = torch.rand(10)
    gt_pts_seg.pts_instance_mask = torch.rand(10)
    data_sample.gt_pts_seg = gt_pts_seg
    
    # 打印数据结构
    print_det3d_data_sample(data_sample)ss