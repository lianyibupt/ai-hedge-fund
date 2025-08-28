# 缓存机制重新设计指南

## 概述

本项目的缓存机制已重新设计，采用**股票代码 + 日期**作为缓存键，确保能够获取到最新的日期数据，避免数据过期问题。

## 新缓存机制特点

### 1. 分层缓存结构
- **内存缓存**：快速访问，按日期分隔存储
- **SQLite缓存**：持久化存储，支持跨会话
- **API源**：最终数据源，当缓存未命中时调用

### 2. 智能缓存键设计
```python
# 旧设计（存在数据过期问题）
cache_key = "AAPL"  # 只使用股票代码

# 新设计（确保数据新鲜度）
cache_key = "AAPL_2024-08-28"  # 股票代码 + 日期
```

### 3. 数据类型特定的缓存策略

#### 价格数据缓存
- **缓存键格式**: `{TICKER}_{DATE}`
- **缓存时效**: 24小时
- **存储结构**: `{ticker: {date: price_data}}`

```python
# 示例：存储AAPL在不同日期的价格数据
{
    "AAPL": {
        "2024-08-26": {...price_data...},
        "2024-08-27": {...price_data...},
        "2024-08-28": {...price_data...}
    }
}
```

#### 财务指标缓存
- **缓存键格式**: `{TICKER}_financial_{REPORT_PERIOD}`
- **缓存时效**: 7天（168小时）
- **存储结构**: `{ticker: {report_period: financial_data}}`

#### 其他数据缓存
- **内部交易**: 24小时缓存时效
- **公司新闻**: 6小时缓存时效
- **财务报表项目**: 7天缓存时效

## 主要改进

### 1. 解决数据过期问题
```python
# 旧机制问题
def get_prices(ticker):
    if ticker in cache:
        return cache[ticker]  # 可能返回过期数据
    
# 新机制解决方案
def get_prices(ticker, start_date, end_date):
    cached_data = cache.get_prices(ticker, start_date, end_date)
    if cached_data:
        # 只返回指定日期范围内的新鲜数据
        return [price for price in cached_data if is_fresh(price)]
```

### 2. 精确的日期范围查询
- 支持按日期范围过滤缓存数据
- 自动检查数据新鲜度
- 避免返回过期或无关数据

### 3. 灵活的缓存管理
```python
# 获取缓存统计
stats = cache.get_cache_stats()

# 清理过期缓存
expired_count = cache.clear_expired_cache()

# 清除特定股票的所有缓存
cache.clear_ticker_cache("AAPL")

# 清空所有缓存
cache.clear_all_cache()
```

## 使用示例

### 基本用法
```python
from data.cache import get_cache
from tools.api import get_prices

# 获取价格数据（自动使用缓存）
prices = get_prices("AAPL", "2024-08-01", "2024-08-28")

# 检查缓存状态
cache = get_cache()
stats = cache.get_cache_stats()
print(f"缓存的股票数量: {stats['cache_summary']['total_tickers']}")
```

### 缓存管理
```python
# 清理过期数据
expired_count = cache.clear_expired_cache()
print(f"清理了 {expired_count} 个过期缓存项")

# 清除特定股票缓存
cache.clear_ticker_cache("AAPL")

# 获取详细统计信息
stats = cache.get_cache_stats()
```

## Web界面功能

在`personal_trading_app.py`中新增的缓存管理功能：

### 1. 缓存统计显示
- 内存缓存统计（总体、价格、财务）
- 数据库缓存统计
- 实时缓存状态监控

### 2. 缓存管理操作
- 清理过期缓存（内存 + 数据库）
- 清空所有内存缓存
- 清除特定股票缓存
- 刷新缓存状态

### 3. 自动缓存维护
- 每次API调用后自动更新缓存时间戳
- 查询时自动检查数据新鲜度
- 后台自动清理过期数据

## 性能优化

### 1. 减少API调用
- 智能缓存命中，避免重复请求
- 按日期粒度缓存，提高缓存利用率

### 2. 内存使用优化
- 自动清理过期数据
- 按需加载，支持日期范围查询

### 3. 查询速度提升
- O(1)缓存键查找
- 预先按日期索引数据

## 注意事项

1. **时间敏感性**：价格数据缓存24小时，财务数据缓存7天
2. **内存管理**：定期清理过期缓存，避免内存泄漏
3. **数据一致性**：内存缓存和数据库缓存保持同步
4. **错误处理**：缓存失败时自动降级到API调用

## 迁移指南

如果你正在使用旧的缓存API，请按以下方式更新：

```python
# 旧API
cached_data = cache.get_prices(ticker)

# 新API
cached_data = cache.get_prices(ticker, start_date, end_date)
```

这个新的缓存机制确保了：
- ✅ 数据始终是最新的
- ✅ 按日期精确缓存和查询
- ✅ 自动过期清理
- ✅ 详细的缓存统计和管理
- ✅ 更好的性能和内存使用

通过这种设计，系统能够更智能地管理数据缓存，提供更准确和及时的交易分析数据。