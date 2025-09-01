#!/usr/bin/env python3
"""
快速测试港股00700数据获取
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🧪 快速测试港股00700数据获取")
    print("=" * 40)
    
    try:
        from tools.api import get_prices, _detect_ticker_region
        
        ticker = "00700"
        
        # 检测市场
        region = _detect_ticker_region(ticker)
        print(f"📍 市场检测: {ticker} -> {region}")
        
        # 使用合理的日期范围（最近30天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        print(f"📅 查询日期范围: {start_date_str} 到 {end_date_str}")
        
        # 获取价格数据
        print("📊 开始获取价格数据...")
        prices = get_prices(ticker, start_date_str, end_date_str, region)
        
        if prices:
            print(f"✅ 成功获取 {len(prices)} 条价格数据")
            print(f"💰 最新价格: ${prices[-1].close:.2f}")
            
            # 显示日期范围
            dates = [p.time for p in prices]
            print(f"📊 数据日期范围: {min(dates)} 到 {max(dates)}")
            
            return True
        else:
            print("❌ 获取数据失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 港股00700数据获取测试成功！")
    else:
        print("\n⚠️ 港股00700数据获取测试失败，请检查API配置和网络连接。")