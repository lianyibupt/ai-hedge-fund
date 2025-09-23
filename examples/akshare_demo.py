"""
AKShare API使用示例
演示如何获取A股、港股、美股的历史股价和财务信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.akshare_api import (
    get_prices_akshare,
    get_financial_metrics_akshare,
    get_company_info_akshare,
    test_akshare_connection
)
import pandas as pd

def demo_akshare_api():
    """演示AKShare API的使用"""
    
    print("🎯 AKShare API 使用演示")
    print("=" * 50)
    
    # 1. 获取A股历史数据
    print("\n1. 📊 获取A股历史数据 (招商银行 600036)")
    prices_a = get_prices_akshare("600036", "2024-01-01", "2024-12-31")
    df_a = pd.DataFrame([p.model_dump() for p in prices_a]) if prices_a else pd.DataFrame()
    if not df_a.empty:
        print(f"✅ 获取到 {len(df_a)} 条A股历史数据")
        print(f"时间范围: {df_a.index[0]} 到 {df_a.index[-1]}")
        print(f"最新收盘价: {df_a['close'].iloc[-1]:.2f}")
        print(f"年内最高价: {df_a['high'].max():.2f}")
        print(f"年内最低价: {df_a['low'].min():.2f}")
    else:
        print("❌ 未获取到A股历史数据")
    
    # 2. 获取港股历史数据
    print("\n2. 📊 获取港股历史数据 (腾讯控股 00700)")
    prices_hk = get_prices_akshare("00700", "2024-01-01", "2024-12-31")
    df_hk = pd.DataFrame([p.model_dump() for p in prices_hk]) if prices_hk else pd.DataFrame()
    if not df_hk.empty:
        print(f"✅ 获取到 {len(df_hk)} 条港股历史数据")
        print(f"最新收盘价: {df_hk['close'].iloc[-1]:.2f}")
    else:
        print("❌ 未获取到港股历史数据")
    
    # 3. 获取美股历史数据
    print("\n3. 📊 获取美股历史数据 (苹果 AAPL)")
    prices_us = get_prices_akshare("AAPL", "2024-01-01", "2024-12-31")
    df_us = pd.DataFrame([p.model_dump() for p in prices_us]) if prices_us else pd.DataFrame()
    if not df_us.empty:
        print(f"✅ 获取到 {len(df_us)} 条美股历史数据")
        print(f"最新收盘价: {df_us['close'].iloc[-1]:.2f}")
    else:
        print("❌ 未获取到美股历史数据")
    
    # 4. 获取公司信息
    print("\n4. 🏢 获取公司基本信息")
    stocks = ["600036", "00700", "AAPL"]
    for symbol in stocks:
        info = get_company_info_akshare(symbol)
        print(f"\n{symbol}:")
        print(f"  公司名称: {info.get('name', '未知')}")
        print(f"  所属行业: {info.get('industry', '未知')}")
        if 'listing_date' in info:
            print(f"  上市日期: {info.get('listing_date', '未知')}")
    
    # 5. 获取财务报表
    print("\n5. 💰 获取财务报表数据")
    metrics = get_financial_metrics_akshare("600036", "2024-12-31")
    balance_sheet = pd.DataFrame([m.model_dump() for m in metrics]) if metrics else pd.DataFrame()
    if not balance_sheet.empty:
        print(f"✅ 获取到 {len(balance_sheet)} 条资产负债表数据")
        # 显示最新的几条记录
        print(balance_sheet.head(3).to_string())
    else:
        print("❌ 未获取到资产负债表数据")
    
    # 6. 测试连接
    print("\n6. 🔗 测试AKShare连接")
    connected = test_akshare_connection()
    print(f"AKShare连接状态: {'✅ 成功' if connected else '❌ 失败'}")
    print("ℹ️  实时行情功能当前版本暂不支持")
    
    # 7. 跳过市场概览
    print("\n7. ⏭️  跳过市场概览（当前版本不支持）")
    print("ℹ️  市场概览功能当前版本暂不支持")
    
    print("\n" + "=" * 50)
    print("✅ AKShare API 演示完成！")

if __name__ == "__main__":
    demo_akshare_api()