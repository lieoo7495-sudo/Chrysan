def print_instance_data(data, indent=0, prefix=""):
    """
    递归打印 InstanceData 的结构信息（shape, type）
    
    :param data: 输入数据（任意嵌套结构）
    :param indent: 缩进层级（用于格式化输出）
    :param prefix: 当前项的前缀标签（如 Key/Index）
    """
    # 生成当前层级的缩进字符串
    indent_str = "│   " * indent + "├── "
    
    # 打印当前项的前缀标签和类型
    print(f"{indent_str}{prefix}Type: {type(data).__name__}", end="")
    
    # 尝试获取并打印 shape 属性（如果存在）
    try:
        shape = getattr(data, 'shape', None)
        if shape is not None:
            print(f", Shape: {shape}")
        else:
            print(", Shape: N/A")
    except Exception:
        print(", Shape: <Error>")
    
    # 根据数据类型递归处理子项
    if isinstance(data, dict):
        # 字典类型：遍历所有键值对
        print("│   " * (indent + 1) + f"└── Dict Items: {len(data)}")
        for key, value in data.items():
            print_instance_data(value, indent + 1, f"Key: '{key}'")
    
    elif isinstance(data, (list, tuple)):
        # 列表/元组类型：遍历所有元素
        seq_type = "List" if isinstance(data, list) else "Tuple"
        print("│   " * (indent + 1) + f"└── {seq_type} Length: {len(data)}")
        for idx, item in enumerate(data):
            print_instance_data(item, indent + 1, f"Index: {idx}")

# 示例测试
if __name__ == "__main__":
    # 构造示例数据结构（包含字典、列表、张量等）
    import numpy as np
    import torch
    
    example_data = {
        "tensor": torch.rand(2, 3),
        "numpy_array": np.zeros((4, 5)),
        "nested_dict": {
            "int_value": 42,
            "float_list": [1.1, 2.2, 3.3]
        },
        "mixed_list": [
            "text",
            np.ones(6),
            {"key": True}
        ]
    }
    
    print_instance_data(example_data)