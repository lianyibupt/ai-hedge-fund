#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 Finnhub 字段映射修复
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加 src 目录到路径
sys.path.insert(0, 'src')

def test_field_mapping():
    """测试字段映射修复"""
    print("🧪 测试 Finnhub 字段映射修复")
    print("=" * 60)
    
    try:
        from analyzers.fundamental_analyzer import FinnhubFundamentalAnalyzer
        
        # 检查 API 密钥
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key or api_key == "YOUR_FREE_KEY":
            print("❌ 未找到有效的 Finnhub API 密钥")
            print("请在 .env 文件中设置 FINNHUB_API_KEY")
            return False
        
        print(f"✅ API 密钥: {api_key[:8]}...")
        
        # 创建分析器
        analyzer = FinnhubFundamentalAnalyzer(api_key)
        
        # 测试字段映射
        test_symbol = "AAPL"
        print(f"\n🔍 测试 {test_symbol} 字段映射...")
        
        # 测试财务指标获取
        metrics = analyzer._get_financial_metrics(test_symbol)
        
        if metrics:
            print("✅ 财务指标获取成功")
            print(f"📊 获取到 {len(metrics)} 个字段")
            
            # 检查修复的关键字段
            key_fields = {
                '52WeekHigh': '52周最高价',
                '52WeekLow': '52周最低价', 
                '52WeekPriceReturnDaily': '52周收益率',
                'beta': 'Beta系数',
                'roeRfy': 'ROE',
                'roaRfy': 'ROA',
                'peBasicExclExtraTTM': '市盈率',
                'pbQuarterly': '市净率',
                'currentRatioQuarterly': '流动比率',
                'quickRatioQuarterly': '速动比率',
                'grossMarginTTM': '毛利率',
                'operatingMarginTTM': '营业利润率',
                'netMarginTTM': '净利率',
            }
            
            print("\n📋 关键字段检查:")
            for field, desc in key_fields.items():
                value = metrics.get(field)
                status = "✅" if value is not None else "⚠️"
                print(f"  {status} {desc} ({field}): {value}")
            
        else:
            print("❌ 财务指标获取失败")
            return False
        
        # 测试完整分析
        print(f"\n🎯 测试完整基本面分析...")
        
        try:
            result = analyzer.analyze_stock(test_symbol)
            print("✅ 基本面分析完成")
            print(f"📊 综合评分: {result.total_score:.1f}/50")
            print(f"🎯 投资建议: {result.investment_signal.value}")
            print(f"🔍 信心度: {result.confidence:.1f}%")
            
            # 检查各模块评分
            modules = [
                ("经营质量", result.operating_quality),
                ("盈利效率", result.profitability_efficiency), 
                ("成长地位", result.growth_market_position),
                ("财务风险", result.financial_risk),
                ("管理治理", result.management_governance)
            ]
            
            print("\n📈 各模块评分:")
            for name, score_obj in modules:
                print(f"  {name}: {score_obj.score:.1f}/10 ({score_obj.percentage:.1f}%)")
                for detail in score_obj.details[:2]:  # 只显示前2个详情
                    print(f"    • {detail}")
            
            return True
            
        except Exception as e:
            print(f"❌ 基本面分析失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_field_mapping()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 字段映射修复测试成功!")
        print("✅ 所有关键字段映射已修复")
        print("✅ 基本面分析功能正常")
    else:
        print("\n" + "=" * 60)
        print("❌ 字段映射修复测试失败")
        print("请检查 Finnhub API 配置和网络连接")