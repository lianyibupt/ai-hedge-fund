# AKShare API 使用指南

基于 [AKShare](https://github.com/akfamily/akshare) 的股票数据API服务，支持获取A股、港股、美股的历史股价和财务信息。

## 功能特性

- 📊 **多市场支持**: A股、港股、美股全覆盖
- 📈 **历史价格**: 获取指定时间范围内的历史股价数据
- 💰 **财务报表**: 资产负债表、利润表、现金流量表
- 🏢 **公司信息**: 公司基本信息、行业分类、上市日期等
- 📉 **实时行情**: 最新价格、涨跌幅、成交量等实时数据
- 🌐 **市场概览**: 整体市场状态统计

## 安装依赖

```bash
pip install akshare
```

## 快速开始

### 基本用法

```python
from src.tools.akshare_api import (
    get_stock_history,
    get_financial_statement,
    get_company_info,
    get_realtime_quote,
    get_market_overview
)

# 获取股票历史数据
df = get_stock_history("600036", "2024-01-01", "2024-12-31")

# 获取财务报表
balance_sheet = get_financial_statement("600036", "balance")

# 获取公司信息
info = get_company_info("600036")

# 获取实时行情
quote = get_realtime_quote("600036")

# 获取市场概览
market = get_market_overview()
```

### 股票代码格式

| 市场 | 示例代码 | AKShare格式 | 说明 |
|------|----------|-------------|------|
| A股 | 600036 | sh600036 | 上海A股 |
| A股 | 000001 | sz000001 | 深圳A股 |
| 港股 | 00700 | hk00700 | 港股 |
| 美股 | AAPL | usAAPL | 美股 |

支持自动识别市场，也可以直接使用标准代码。

## API 参考

### get_stock_history(symbol, start_date, end_date, adjust="qfq")

获取股票历史价格数据

**参数:**
- `symbol`: 股票代码
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `adjust`: 复权类型 ("qfq": 前复权, "hfq": 后复权, "": 不复权)

**返回:**
- DataFrame包含以下列: date, open, close, high, low, volume, amount, amplitude, change_percent, change

### get_financial_statement(symbol, report_type="balance")

获取财务报表数据

**参数:**
- `symbol`: 股票代码
- `report_type`: 报表类型 ("balance": 资产负债表, "income": 利润表, "cash": 现金流量表)

**返回:**
- DataFrame包含财务报表数据

### get_company_info(symbol)

获取公司基本信息

**参数:**
- `symbol`: 股票代码

**返回:**
- 字典包含公司基本信息

### get_realtime_quote(symbol)

获取实时行情数据

**参数:**
- `symbol`: 股票代码

**返回:**
- 字典包含实时行情数据

### get_market_overview()

获取市场概览信息

**返回:**
- 字典包含市场状态统计

## 示例代码

运行演示程序:

```bash
python examples/akshare_demo.py
```

## 错误处理

所有API函数都包含重试机制和错误处理，当网络请求失败时会自动重试3次。

## 注意事项

1. **数据延迟**: 实时行情数据可能有15分钟延迟
2. **市场时间**: 注意各市场的交易时间差异
3. **数据限制**: 大量频繁请求可能会被限制
4. **代码格式**: 确保使用正确的股票代码格式

## 支持的市场

- ✅ **A股**: 上海证券交易所、深圳证券交易所
- ✅ **港股**: 香港交易所
- ✅ **美股**: 纽约证券交易所、纳斯达克

## 依赖项

- akshare >= 1.12.0
- pandas >= 1.0.0
- tenacity >= 8.0.0

## 许可证

基于AKShare开源项目，遵循AKShare的许可证条款。