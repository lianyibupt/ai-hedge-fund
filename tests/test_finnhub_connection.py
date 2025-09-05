#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Finnhub API连接和数据获取
"""

import os
import finnhub
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_finnhub_connection():
    """测试Finnhub API连接"""
    print("🔗 测试Finnhub API连接...")
    
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ 未找到FINNHUB_API_KEY环境变量")
        return
    
    print(f"✅ API密钥: {api_key[:8]}...")
    
    client = finnhub.Client(api_key=api_key)
    
    # 测试股票报价
    print("\n1. 测试股票报价...")
    try:
        quote = client.quote("AAPL")
        print(f"✅ AAPL当前价格: ${quote.get('c', 'N/A')}")
        print(f"   昨日收盘: ${quote.get('pc', 'N/A')}")
        print(f"   今日开盘: ${quote.get('o', 'N/A')}")
        print(f"   今日最高: ${quote.get('h', 'N/A')}")
        print(f"   今日最低: ${quote.get('l', 'N/A')}")
    except Exception as e:
        print(f"❌ 获取报价失败: {e}")
    
    # 测试公司信息
    print("\n2. 测试公司信息...")
    try:
        profile = client.company_profile2(symbol="AAPL")
        print(f"✅ 公司名称: {profile.get('name', 'N/A')}")
        print(f"   行业: {profile.get('finnhubIndustry', 'N/A')}")
        print(f"   市值: ${profile.get('marketCapitalization', 'N/A')}M")
        print(f"   国家: {profile.get('country', 'N/A')}")
        print(f"   交易所: {profile.get('exchange', 'N/A')}")
    except Exception as e:
        print(f"❌ 获取公司信息失败: {e}")
    
    # 测试财务指标
    print("\n3. 测试财务指标...")
    try:
        financials = client.company_basic_financials("AAPL", "all")
        if 'metric' in financials:
            metrics = financials['metric']
            print("✅ 财务指标获取成功:")
            print(f"   市盈率(P/E): {metrics.get('peBasicExclExtraTTM', 'N/A')}")
            print(f"   市净率(P/B): {metrics.get('pbQuarterly', 'N/A')}")
            print(f"   净资产收益率(ROE): {metrics.get('roeRfy', 'N/A')}")
            print(f"   毛利率: {metrics.get('grossMarginTTM', 'N/A')}")
            print(f"   营业利润率: {metrics.get('operatingMarginTTM', 'N/A')}")
            print(f"   52周最高: ${metrics.get('52WeekHigh', 'N/A')}")
            print(f"   52周最低: ${metrics.get('52WeekLow', 'N/A')}")
            print(f"   当前比率: {metrics.get('currentRatioQuarterly', 'N/A')}")
            print(f"   速动比率: {metrics.get('quickRatioQuarterly', 'N/A')}")
            
            # 检查数据格式
            print("\n🔍 数据格式检查:")
            gross_margin = metrics.get('grossMarginTTM')
            if gross_margin is not None:
                print(f"   毛利率原始值: {gross_margin} (类型: {type(gross_margin)})")
                if gross_margin > 1:
                    print("   ⚠️ 毛利率数据可能需要转换 (>1表示可能是百分比形式)")
                else:
                    print("   ✅ 毛利率数据格式正常 (0-1之间)")
        else:
            print("❌ 财务指标数据格式异常")
    except Exception as e:
        print(f"❌ 获取财务指标失败: {e}")
    
    # 测试推荐数据
    print("\n4. 测试分析师推荐...")
    try:
        recommendations = client.recommendation_trends("AAPL")
        if recommendations:
            print(f"✅ 获取到 {len(recommendations)} 条推荐数据")
            latest = recommendations[0]
            print(f"   最新期间: {latest.get('period', 'N/A')}")
            print(f"   强烈买入: {latest.get('strongBuy', 0)}")
            print(f"   买入: {latest.get('buy', 0)}")
            print(f"   持有: {latest.get('hold', 0)}")
            print(f"   卖出: {latest.get('sell', 0)}")
            print(f"   强烈卖出: {latest.get('strongSell', 0)}")
        else:
            print("⚠️ 未获取到推荐数据")
    except Exception as e:
        print(f"❌ 获取推荐数据失败: {e}")

if __name__ == "__main__":
    test_finnhub_connection()