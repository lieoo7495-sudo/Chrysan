#!/usr/bin/env python3
"""
AutoEval WebUI API 测试脚本
用于测试Flask应用的各个API接口
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8009"
TEST_DATA = {
    "test_model": {
        "data": {
            "trained_date": "2024-02-15",
            "trained_time": "10:00",
            "model_path": "/models/test-model",
            "model_name": "Test-Model"
        },
        "Eval_Statu": {
            "VLMEvalKit": {
                "Statu": 1,
                "Datasets": "test_dataset"
            },
            "VLMEvalKit_COT": {
                "Statu": 0,
                "Datasets": ""
            },
            "MIRB": 0,
            "mmiu": 0
        }
    }
}

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_get_config():
    """测试获取配置接口"""
    print("\n🔍 测试获取配置接口...")
    try:
        response = requests.get(f"{BASE_URL}/config")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取配置成功，数据大小: {len(str(data))} 字符")
            return True
        else:
            print(f"❌ 获取配置失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取配置异常: {e}")
        return False

def test_update_config():
    """测试更新配置接口"""
    print("\n🔍 测试更新配置接口...")
    try:
        response = requests.post(
            f"{BASE_URL}/update",
            json=TEST_DATA,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 更新配置成功: {data}")
            return True
        else:
            print(f"❌ 更新配置失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 更新配置异常: {e}")
        return False

def test_get_evaluated():
    """测试获取评测状态接口"""
    print("\n🔍 测试获取评测状态接口...")
    try:
        response = requests.get(f"{BASE_URL}/evaluated")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取评测状态成功，模型数量: {len(data.get('evaluation_status', {}))}")
            return True
        else:
            print(f"❌ 获取评测状态失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取评测状态异常: {e}")
        return False

def test_get_datasets():
    """测试获取数据集接口"""
    print("\n🔍 测试获取数据集接口...")
    try:
        response = requests.get(f"{BASE_URL}/datasets")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取数据集成功: {len(data.get('data', {}).get('predefined', []))} 个数据集")
            return True
        else:
            print(f"❌ 获取数据集失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取数据集异常: {e}")
        return False

def test_static_files():
    """测试静态文件访问"""
    print("\n🔍 测试静态文件访问...")
    files_to_test = ['index.html', 'mock.json', 'styles.css']
    
    for filename in files_to_test:
        try:
            response = requests.get(f"{BASE_URL}/{filename}")
            if response.status_code == 200:
                print(f"✅ {filename} 访问成功")
            else:
                print(f"❌ {filename} 访问失败: {response.status_code}")
        except Exception as e:
            print(f"❌ {filename} 访问异常: {e}")

def test_index_page():
    """测试首页访问"""
    print("\n🔍 测试首页访问...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            content = response.text
            if "AutoEval Config" in content:
                print("✅ 首页访问成功，内容正确")
                return True
            else:
                print("❌ 首页内容不正确")
                return False
        else:
            print(f"❌ 首页访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 首页访问异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 AutoEval WebUI API...")
    print(f"📡 测试地址: {BASE_URL}")
    print("=" * 50)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(2)
    
    # 执行测试
    tests = [
        test_health_check,
        test_index_page,
        test_get_config,
        test_update_config,
        test_get_evaluated,
        test_get_datasets,
        test_static_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查服务器状态")
    
    print("\n💡 提示:")
    print("- 确保Flask服务器正在运行: python app.py")
    print("- 检查端口8009是否被占用")
    print("- 查看服务器日志获取更多信息")

if __name__ == "__main__":
    main() 