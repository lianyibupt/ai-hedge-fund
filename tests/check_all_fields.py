#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面检查所有 Finnhub 字段映射
"""

import sys
import os
import finnhub
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv()

def check_all_fields():
    """检查所有字段映射"""
    print("🔍 全面检查 Finnhub API 字段映射")
    print("=" * 80)
    
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ 未找到 API 密钥")
        return
    
    client = finnhub.Client(api_key=api_key)
    symbol = "AAPL"
    
    print(f"📊 获取 {symbol} 的原始数据...")
    
    # 1. 获取原始 basic_financials 数据
    try:
        response = client.company_basic_financials(symbol, 'all')
        print(f"\n✅ 原始 basic_financials 响应结构:")
        print(f"🔧 响应包含的主要键: {list(response.keys())}")
        
        metrics = response.get('metric', {})
        series = response.get('series', {})
        
        print(f"\n📋 metric 字段 (共 {len(metrics)} 个):")
        for i, (key, value) in enumerate(sorted(metrics.items())):
            if i < 50:  # 限制输出前50个
                print(f"  {key}: {value}")
        
        if len(metrics) > 50:
            print(f"  ... 还有 {len(metrics) - 50} 个字段")
        
        if series:
            print(f"\n📋 series 结构:")
            for key, data in series.items():
                if isinstance(data, dict):
                    print(f"  {key}: {list(data.keys()) if data else 'empty'}")
                else:
                    print(f"  {key}: {type(data)}")
        
        # 2. 检查我们当前使用的字段
        current_fields = [
            '52WeekHigh', '52WeekLow', '52WeekPriceReturnDaily', 'beta',
            'peBasicExclExtraTTM', 'peTTM', 'pbQuarterly', 'pbAnnual', 
            'psQuarterly', 'psTTM', 'roeRfy', 'roeTTM', 'roaRfy', 'roaTTM',
            'epsBasicExclExtraItemsTTM', 'grossMarginTTM', 'operatingMarginTTM',
            'netMarginTTM', 'currentRatioQuarterly', 'quickRatioQuarterly',
            'revenueTTM', 'marketCapitalization', '10DayAverageTradingVolume'
        ]
        
        print(f"\n🔍 检查当前使用的字段映射:")
        print("-" * 60)
        available_count = 0
        missing_fields = []
        
        for field in current_fields:
            value = metrics.get(field)
            if value is not None:
                available_count += 1
                print(f"  ✅ {field}: {value}")
            else:
                missing_fields.append(field)
                print(f"  ❌ {field}: 缺失")
        
        print(f"\n📊 字段可用性统计:")
        print(f"  ✅ 可用字段: {available_count}/{len(current_fields)} ({available_count/len(current_fields)*100:.1f}%)")
        print(f"  ❌ 缺失字段: {len(missing_fields)}")
        
        if missing_fields:
            print(f"\n🔍 寻找缺失字段的替代映射:")
            for field in missing_fields:
                alternatives = find_alternative_fields(metrics, field)
                if alternatives:
                    print(f"  {field} 的可能替代字段:")
                    for alt in alternatives[:3]:  # 只显示前3个
                        print(f"    • {alt}: {metrics[alt]}")
        
        # 3. 检查数据格式问题
        print(f"\n🔧 检查数据格式问题:")
        format_issues = check_data_formats(metrics)
        for issue in format_issues:
            print(f"  ⚠️ {issue}")
        
        return True
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_alternative_fields(metrics, target_field):
    """寻找目标字段的替代字段"""
    alternatives = []
    
    # 定义字段映射关系
    field_mappings = {
        'peBasicExclExtraTTM': ['peTTM', 'peNormalizedAnnual'],
        'pbQuarterly': ['pbAnnual', 'pbTTM'],
        'psQuarterly': ['psTTM', 'psAnnual'],
        'roeRfy': ['roeTTM', 'roeAnnual'],
        'roaRfy': ['roaTTM', 'roaAnnual'],
        'currentRatioQuarterly': ['currentRatioAnnual', 'currentRatio'],
        'quickRatioQuarterly': ['quickRatioAnnual', 'quickRatio'],
    }
    
    # 关键字匹配
    target_keywords = {
        'grossMarginTTM': ['gross', 'margin'],
        'operatingMarginTTM': ['operating', 'margin'],
        'netMarginTTM': ['net', 'margin'],
        'revenueTTM': ['revenue', 'sales'],
    }
    
    # 首先检查预定义映射
    if target_field in field_mappings:
        for alt_field in field_mappings[target_field]:
            if alt_field in metrics:
                alternatives.append(alt_field)
    
    # 然后使用关键字搜索
    if target_field in target_keywords:
        keywords = target_keywords[target_field]
        for field_name in metrics.keys():
            if all(keyword.lower() in field_name.lower() for keyword in keywords):
                alternatives.append(field_name)
    
    return alternatives

def check_data_formats(metrics):
    """检查数据格式问题"""
    issues = []
    
    # 检查百分比格式问题
    percentage_fields = {
        'roeRfy': 'ROE',
        'roaRfy': 'ROA', 
        'roeTTM': 'ROE(TTM)',
        'roaTTM': 'ROA(TTM)',
        'grossMarginTTM': '毛利率',
        'operatingMarginTTM': '营业利润率',
        'netMarginTTM': '净利率'
    }
    
    for field, desc in percentage_fields.items():
        value = metrics.get(field)
        if value is not None:
            if value > 5:  # 可能是百分比格式
                issues.append(f"{desc}({field}): {value} - 可能需要除以100转换")
            elif value > 1:  # 可能是百分比格式但较小
                issues.append(f"{desc}({field}): {value} - 可能需要除以100转换")
    
    # 检查市值格式
    market_cap = metrics.get('marketCapitalization')
    if market_cap and market_cap > 1000000:
        issues.append(f"市值: {market_cap} - 数值过大，可能需要格式化")
    
    return issues

if __name__ == "__main__":
    check_all_fields()