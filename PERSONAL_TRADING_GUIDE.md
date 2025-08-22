# 个性化交易系统使用指南

## 🎯 系统概述

基于您的交易需求，我已经为您定制了一套完整的个性化交易系统：

### 交易约束
- ✅ **交易周期**: 2-3周 (14-21天持仓期)
- ✅ **交易频率**: 2周内最多10次交易
- ✅ **检查频率**: 每周检查一次交易机会
- ✅ **只做多**: 不使用做空策略

### 技术指标策略
- ✅ **MACD**: DIF金叉/死叉、0轴位置、趋势判断
- ✅ **RSI**: 超买超卖、区间突破
- ✅ **布林带**: 上下轨触及、中轨趋势、企稳信号
- ✅ **成交量**: 放量确认、量价背离

## 🚀 快速开始

### 1. 运行个性化交易系统

```bash
# 基本使用
poetry run python src/personal_main.py --tickers AAPL,MSFT,NVDA

# 显示详细推理过程
poetry run python src/personal_main.py --tickers AAPL,MSFT,NVDA --show-reasoning

# 指定时间范围
poetry run python src/personal_main.py --tickers AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01

# 设置初始资金
poetry run python src/personal_main.py --tickers AAPL,MSFT,NVDA --initial-cash 200000
```

### 2. 运行个性化回测

```bash
# 基本回测
poetry run python src/personal_backtester.py --tickers AAPL,MSFT,NVDA

# 指定回测期间
poetry run python src/personal_backtester.py --tickers AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-12-01

# 设置初始资金
poetry run python src/personal_backtester.py --tickers AAPL,MSFT,NVDA --initial-capital 200000
```

## 📊 核心功能

### 1. 买入信号检测
系统会自动检测以下买入条件的组合：
- **MACD**: DIF在0轴下方金叉DEA且向上发散，或DIF在0轴上方回踩后再次向上
- **RSI**: 从30以下回升突破40或50，但未进入超买区(<70)
- **布林带**: 价格触及或跌破下轨且有企稳迹象(长下影线)，中轨向上
- **成交量**: 明显放大(1.5倍以上)

**买入条件**: 至少满足3个条件才会生成买入信号

### 2. 卖出信号检测
系统会自动检测以下卖出条件的组合：
- **MACD**: DIF在0轴上方死叉DEA，或DIF在高位拐头向下
- **RSI**: 从70以上回落跌破60或50
- **布林带**: 价格触及或突破上轨且出现长上影线
- **成交量**: 成交量萎缩或量价背离

**卖出条件**: 至少满足2个条件才会生成卖出信号

### 3. 风险管理
- **持仓时间控制**: 强制14-21天持仓期
- **交易频率限制**: 2周内最多10次交易
- **资金管理**: 单次投入不超过可用资金的40%
- **止损保护**: 基于技术指标的动态止损

## 🔧 文件结构

```
src/
├── utils/personal_indicators.py          # 个性化技术指标计算
├── agents/personal_trader.py             # 个性化交易代理
├── agents/personal_portfolio_manager.py  # 个性化投资组合管理
├── personal_main.py                      # 个性化交易系统入口
└── personal_backtester.py               # 个性化回测系统
```

## 📈 输出示例

### 交易信号输出
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 75,
    "reasoning": {
      "当前价格": "150.25",
      "综合信号": "bullish", 
      "信号强度": "75%",
      "交易建议": "bullish",
      "技术指标分析": {
        "MACD分析": "DIF在0轴下方金叉DEA且向上发散",
        "RSI分析": "RSI从30回升至50以上，突破超卖区",
        "布林带分析": "价格触及布林下轨并出现长下影线，中轨向上",
        "成交量分析": "成交量放大1.8倍，资金进场"
      }
    }
  }
}
```

### 回测结果示例
```
📈 个性化策略表现分析:
💰 总收益率: +12.5%
🔄 总交易次数: 8 (买入: 4, 卖出: 4)
💵 已实现收益: $12,500.00
```

## ⚙️ 系统优势

### 1. 严格遵循个人约束
- 自动控制交易频率，避免过度交易
- 强制持仓期管理，培养中期投资习惯
- 风险控制机制，保护资金安全

### 2. 多指标综合决策
- 4种核心技术指标综合分析
- 加权信号合成，提高准确性
- 详细的推理过程，便于学习

### 3. 完整的回测验证
- 历史数据验证策略有效性
- 详细的交易记录和分析
- 可视化收益曲线

### 4. 高度可定制
- 可调整各项参数
- 支持不同股票组合
- 灵活的时间范围设置

## 🔄 与原系统的兼容性

个性化系统完全独立，不会影响原有的AI对冲基金系统：

- **原系统**: 继续使用 `src/main.py` 和 `src/backtester.py`
- **个人系统**: 使用 `src/personal_main.py` 和 `src/personal_backtester.py`
- **共享组件**: 数据获取、LLM接口等基础设施

## 🛠️ 自定义调优

如需调整策略参数，可修改以下文件：

1. **技术指标参数**: `src/utils/personal_indicators.py`
2. **交易条件**: `src/agents/personal_trader.py`
3. **持仓管理**: `src/agents/personal_portfolio_manager.py`
4. **回测设置**: `src/personal_backtester.py`

## 📞 技术支持

如果您需要进一步的定制或有任何问题，可以：

1. 修改技术指标的计算参数
2. 调整买入/卖出条件的权重
3. 自定义风险管理规则
4. 添加新的技术指标

系统设计为模块化架构，便于扩展和修改。