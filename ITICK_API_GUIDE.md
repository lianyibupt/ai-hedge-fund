# iTick API 集成使用说明

## 概述

本项目已成功集成 iTick API，为 personal trading 系统提供实时股票数据获取能力。系统采用智能回退机制，优先使用 iTick API，在API不可用时自动切换到模拟数据。

## 配置说明

### 1. API 密钥配置

在项目根目录的 `.env` 文件中添加以下配置：

```env
# iTick API 密钥
ITICK_API_KEY=your_itick_api_key_here
```

### 2. 支持的市场和周期

**支持的市场 (region):**
- `US` - 美股
- `HK` - 港股  
- `SH` - 上证
- `SZ` - 深证
- `SG` - 新加坡
- `JP` - 日本

**支持的K线周期 (kType):**
- `1m` - 1分钟 (kType=1)
- `5m` - 5分钟 (kType=2)
- `15m` - 15分钟 (kType=3)
- `30m` - 30分钟 (kType=4)
- `1h` - 1小时 (kType=5)
- `2h` - 2小时 (kType=6)
- `4h` - 4小时 (kType=7)
- `1d` - 1天 (kType=8)
- `1w` - 1周 (kType=9)
- `1M` - 1月 (kType=10)

## 使用方法

### 1. 简化版个人交易系统

```bash
# 使用 Poetry 运行
poetry run python src/simple_personal_trading.py --tickers AAPL,MSFT --start-date 2025-01-01 --end-date 2025-08-22

# 或直接运行
python src/simple_personal_trading.py --tickers AAPL --start-date 2025-08-01 --end-date 2025-08-22
```

### 2. 完整的个人交易系统

```bash
poetry run python src/personal_main.py --tickers AAPL,MSFT,NVDA --initial-cash 100000
```

### 3. 主对冲基金系统

```bash
poetry run python src/main.py --tickers AAPL,MSFT,NVDA --show-reasoning
```

## API 数据格式

### 价格数据 (K线)

iTick API 返回的 K线数据格式：

```json
{
  "code": 0,
  "msg": null,
  "data": [
    {
      "t": 1754611200000,  // 时间戳 (毫秒)
      "o": 220.83,         // 开盘价
      "h": 231.00,         // 最高价
      "l": 219.25,         // 最低价
      "c": 229.35,         // 收盘价
      "v": 113853967,      // 成交数量
      "tu": 24962482264.75 // 成交金额
    }
  ]
}
```

### 实时价格数据

```json
{
  "code": 0,
  "msg": null,
  "data": {
    "s": "AAPL",         // 股票代码
    "ld": 225.35,        // 最新价格
    "t": 1755820680000,  // 时间戳
    "v": 100             // 成交量
  }
}
```

## 智能回退机制

系统采用多层回退策略：

1. **第一优先级**: iTick API - 获取实时股票数据
2. **第二优先级**: Mock Data - 生成合理的模拟数据

当 iTick API 不可用时（如网络问题、API 限额等），系统会自动切换到模拟数据，确保交易分析功能正常运行。

## 交易策略规范

根据项目规范，交易策略遵循以下要求：

- **交易周期**: 14-21天持仓期
- **交易频率**: 2周内不超过10次交易
- **买入信号**: 需要至少3个指标同时满足
  - MACD 金叉
  - RSI 回升
  - 布林下轨企稳
  - 成交量放大
- **卖出信号**: 需要至少2个指标同时满足
  - MACD 死叉
  - RSI 超买回落
  - 布林上轨见顶
  - 成交量萎缩

## 测试验证

### 运行集成测试

```bash
# 测试 iTick API 基础功能
python test_basic_itick.py

# 测试完整集成
python test_itick_only.py

# 测试模拟数据回退
python test_mock_data.py
```

### 预期结果

- iTick API 连接成功
- 历史数据获取正常
- 统一API接口工作正常
- 智能回退机制生效
- 个人交易系统分析正常

## 故障排除

### 常见问题

1. **401 Unauthorized 错误**
   - 检查 `.env` 文件中的 `ITICK_API_KEY` 是否正确
   - 确认 API 密钥有效且未过期

2. **数据为空**
   - 检查股票代码格式 (如: AAPL, 700)
   - 确认市场代码正确 (US, HK等)
   - 验证时间范围参数

3. **网络连接问题**
   - 系统会自动回退到模拟数据
   - 检查网络连接和防火墙设置

### 日志信息

系统会输出详细的运行日志：
- `🔄 尝试从 iTick API 获取数据...` - 正在调用 iTick API
- `✅ 成功从 iTick API 获取数据` - API 调用成功
- `❌ iTick API 获取失败` - API 调用失败，会自动回退
- `🔄 尝试从 Mock Data 获取数据...` - 使用模拟数据回退

## 版本更新

### v1.0.0 (当前版本)
- ✅ 集成 iTick API
- ✅ 实现智能回退机制
- ✅ 支持多市场数据获取
- ✅ 优化个人交易系统
- ✅ 完善错误处理和日志

### 未来计划
- [ ] 添加更多技术指标
- [ ] 支持实时数据推送
- [ ] 增强风险管理模块
- [ ] 添加更多市场支持