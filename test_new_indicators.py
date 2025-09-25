#!/usr/bin/env python3
"""
测试新添加的技术指标：ROC、随机指标、威廉指标
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from utils.personal_indicators import (
    calculate_roc, calculate_stochastic, calculate_williams_r,
    analyze_roc_signals, analyze_stochastic_signals, analyze_williams_r_signals,
    generate_comprehensive_signal
)

def test_new_indicators():
    """测试新添加的指标"""
    print("🧪 测试新添加的技术指标...")
    
    # 创建测试数据
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 生成模拟价格数据
    prices_df = pd.DataFrame({
        'open': np.random.normal(100, 5, 100),
        'high': np.random.normal(105, 5, 100),
        'low': np.random.normal(95, 5, 100),
        'close': np.random.normal(100, 5, 100),
        'volume': np.random.normal(1000000, 200000, 100)
    }, index=dates)
    
    # 确保价格数据合理
    prices_df['high'] = prices_df[['open', 'high', 'close']].max(axis=1)
    prices_df['low'] = prices_df[['open', 'low', 'close']].min(axis=1)
    prices_df['volume'] = prices_df['volume'].abs()
    
    print("✅ 测试数据创建成功")
    
    # 测试ROC指标
    try:
        roc = calculate_roc(prices_df)
        roc_signals = analyze_roc_signals(roc)
        print(f"✅ ROC指标测试成功 - 当前值: {roc_signals['current_roc']:.2f}%, 信号: {roc_signals['signal']}")
    except Exception as e:
        print(f"❌ ROC指标测试失败: {e}")
    
    # 测试随机指标
    try:
        stoch_data = calculate_stochastic(prices_df)
        stoch_signals = analyze_stochastic_signals(stoch_data)
        print(f"✅ 随机指标测试成功 - K值: {stoch_signals['current_k']:.2f}, D值: {stoch_signals['current_d']:.2f}, 信号: {stoch_signals['signal']}")
    except Exception as e:
        print(f"❌ 随机指标测试失败: {e}")
    
    # 测试威廉指标
    try:
        williams_r = calculate_williams_r(prices_df)
        wr_signals = analyze_williams_r_signals(williams_r)
        print(f"✅ 威廉指标测试成功 - 当前值: {wr_signals['current_wr']:.2f}, 信号: {wr_signals['signal']}")
    except Exception as e:
        print(f"❌ 威廉指标测试失败: {e}")
    
    # 测试综合信号生成
    try:
        comprehensive_result = generate_comprehensive_signal(prices_df)
        print(f"✅ 综合信号测试成功 - 总体信号: {comprehensive_result['signal']}, 信心度: {comprehensive_result['confidence']}%")
        
        # 显示各指标权重
        print("📊 各指标权重分配:")
        print(f"  - MACD: 20%")
        print(f"  - RSI: 15%")
        print(f"  - 布林带: 15%")
        print(f"  - 成交量: 10%")
        print(f"  - ROC: 15%")
        print(f"  - 随机指标: 15%")
        print(f"  - 威廉指标: 10%")
        
        # 显示各指标信号
        print("📋 各指标信号:")
        for indicator_name, indicator_data in comprehensive_result['details'].items():
            print(f"  - {indicator_name.upper()}: {indicator_data['signal']} ({indicator_data['reason']})")
            
    except Exception as e:
        print(f"❌ 综合信号测试失败: {e}")
    
    print("\n🎉 所有新指标测试完成！")

if __name__ == "__main__":
    test_new_indicators()