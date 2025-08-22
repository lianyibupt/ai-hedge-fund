#!/usr/bin/env python3
"""
简单测试 iTick API 调用
验证 API key 和调用方式是否正确
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_basic_itick_call():
    """基础 iTick API 调用测试"""
    api_key = os.getenv("ITICK_API_KEY")
    print(f"🔑 使用 API Key: {api_key[:10]}...{api_key[-10:] if api_key and len(api_key) > 20 else api_key}")
    
    url = "https://api.itick.org/stock/tick"
    headers = {"accept": "application/json", "token": api_key}
    params = {"region": "us", "code": "AAPL"}
    
    try:
        print("📡 发起请求...")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        print(f"   Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 调用成功！")
            print(f"📄 响应数据: {data}")
            return True
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def test_historical_data():
    """测试历史数据接口"""
    api_key = os.getenv("ITICK_API_KEY")
    
    url = "https://api.itick.org/stock/kline"
    headers = {"accept": "application/json", "token": api_key}
    params = {
        "region": "us", 
        "code": "AAPL",
        "kType": "8",  # 日K线，根据文档是8
        "limit": 10
    }
    
    try:
        print("\\n📈 测试历史数据接口...")
        print(f"   URL: {url}")
        print(f"   Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 历史数据API调用成功！")
            print(f"📄 响应数据: {data}")
            return True
        else:
            print(f"❌ 历史数据API调用失败: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 iTick API 基础测试")
    print("=" * 40)
    
    # 测试实时数据
    result1 = test_basic_itick_call()
    
    # 测试历史数据  
    result2 = test_historical_data()
    
    print("\\n" + "=" * 40)
    if result1 and result2:
        print("🎉 iTick API 测试全部通过！")
    else:
        print("⚠️ iTick API 测试部分失败，可能需要检查API密钥或配额")