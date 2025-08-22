# SQLite数据库功能使用说明

## 概述

本文档介绍了为个人交易分析系统新增的SQLite数据库功能，包括查询记录存储、API缓存机制和分析结果追溯等核心特性。

## 主要功能

### 1. 查询记录存储 📝

系统会自动记录每次分析查询的详细信息：

- **查询参数**: 股票代码、日期范围、分析配置
- **会话信息**: 会话ID、用户IP、查询时间
- **结果统计**: 分析结果数量、平均信心度

**数据库表**: `query_records`

### 2. 技术分析结果保存 📊

每次技术分析的结果都会完整保存：

- **基本信息**: 股票代码、当前价格、数据天数
- **分析信号**: 总体信号、信心度、分析原因
- **指标详情**: MACD、RSI、布林带、成交量各项指标
- **交易建议**: 投资建议、操作建议、风险评估
- **财务指标**: PE比率、PB比率等基本面数据

**数据库表**: `analysis_results`

### 3. 多级API缓存 💾

实现了高效的多级缓存机制：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   内存缓存    │ -> │  SQLite缓存  │ -> │  iTick API  │
│  (第一级)    │    │   (第二级)   │    │   (数据源)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### 缓存策略

- **内存缓存**: 程序运行期间有效，访问速度最快
- **SQLite缓存**: 持久化存储，支持过期时间管理
  - 价格数据: 缓存24小时
  - 财务数据: 缓存7天
- **iTick API**: 最终数据源，仅在缓存未命中时调用

**数据库表**: `price_cache`, `financial_cache`

## 文件结构

```
src/
├── data/
│   ├── database.py          # SQLite数据库管理器
│   └── cache.py            # 内存缓存（原有）
├── tools/
│   └── api.py              # API接口（已集成多级缓存）
└── personal_trading_app.py  # Streamlit应用（已集成数据库功能）

项目根目录/
├── trading_data.db         # SQLite数据库文件
├── test_database.py        # 数据库功能测试脚本
└── demo_database_features.py # 功能演示脚本
```

## 使用方法

### 1. 启动Streamlit应用

```bash
cd /Users/bytedance/Documents/code/ai-hedge-fund
streamlit run src/personal_trading_app.py
```

### 2. 新增的界面功能

#### 侧边栏选项
- **显示查询历史**: 查看历史查询记录
- **显示缓存统计**: 查看缓存使用情况
- **清理过期缓存**: 手动清理过期的缓存数据

#### 主界面功能
- **查询记录自动保存**: 每次分析都会自动保存查询记录
- **分析结果追溯**: 可以查看之前的分析历史
- **缓存状态显示**: 实时显示数据来源（内存缓存/SQLite缓存/API调用）

### 3. 数据库管理

#### 查看缓存统计
```python
from tools.api import get_cache_stats

stats = get_cache_stats()
print(stats)
```

#### 清理过期缓存
```python
from tools.api import cleanup_cache

cleanup_cache()
```

#### 查询历史记录
```python
from data.database import get_database_manager

db_manager = get_database_manager()
history_df = db_manager.get_query_history(limit=10)
analysis_df = db_manager.get_analysis_history(ticker='AAPL', limit=20)
```

## 技术优势

### 1. 性能提升 🚀
- **减少API调用**: 多级缓存机制显著减少对iTick API的调用次数
- **提高响应速度**: 缓存数据访问速度比API调用快10-100倍
- **降低延迟**: 大部分查询可以直接从缓存获取数据

### 2. 数据持久化 💾
- **离线访问**: 缓存数据支持离线分析
- **历史追溯**: 完整保存所有查询和分析记录
- **数据安全**: SQLite数据库提供ACID事务保证

### 3. 用户体验 ✨
- **查询历史**: 可以回顾之前的分析结果
- **趋势分析**: 通过历史数据分析股票趋势变化
- **决策支持**: 基于历史分析结果进行投资决策

## 数据库架构

### 核心表结构

#### 1. query_records (查询记录表)
```sql
CREATE TABLE query_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    tickers TEXT NOT NULL,                  -- JSON格式股票代码列表
    start_date DATE,
    end_date DATE,
    analysis_params TEXT,                   -- JSON格式分析参数
    user_ip TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. analysis_results (分析结果表)
```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_record_id INTEGER,
    ticker TEXT NOT NULL,
    current_price REAL,
    signal TEXT,                           -- 看涨/看跌/中性
    confidence INTEGER,
    reason TEXT,
    macd_signal TEXT,
    rsi_signal TEXT,
    bollinger_signal TEXT,
    volume_signal TEXT,
    recommendation TEXT,
    recommendation_action TEXT,
    data_days INTEGER,
    pe_ratio REAL,
    pb_ratio REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_record_id) REFERENCES query_records (id)
);
```

#### 3. price_cache (价格缓存表)
```sql
CREATE TABLE price_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    api_source TEXT DEFAULT 'itick',
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    UNIQUE(ticker, date, api_source)
);
```

#### 4. financial_cache (财务缓存表)
```sql
CREATE TABLE financial_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    report_period DATE,
    period TEXT,                           -- ttm, annual, quarterly
    currency TEXT,
    market_cap REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    -- ... 更多财务指标
    api_source TEXT DEFAULT 'itick',
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    raw_data TEXT,                         -- JSON格式原始数据
    UNIQUE(ticker, report_period, period, api_source)
);
```

## 测试与验证

### 1. 运行测试脚本
```bash
# 功能测试
python test_database.py

# 功能演示
python demo_database_features.py
```

### 2. 测试覆盖范围
- ✅ 数据库初始化
- ✅ 查询记录CRUD操作
- ✅ 分析结果保存和查询
- ✅ 价格数据缓存机制
- ✅ 财务数据缓存机制
- ✅ 缓存统计和清理
- ✅ API集成功能

## 配置说明

### 缓存过期时间
```python
# 在 database.py 中可以调整缓存时间
PRICE_CACHE_HOURS = 24      # 价格数据缓存24小时
FINANCIAL_CACHE_HOURS = 168 # 财务数据缓存7天(168小时)
```

### 数据库位置
```python
# 默认数据库位置
DEFAULT_DB_PATH = "项目根目录/trading_data.db"

# 自定义数据库位置
from data.database import DatabaseManager
db_manager = DatabaseManager(db_path="/custom/path/trading.db")
```

## 常见问题

### 1. 数据库文件权限问题
**问题**: 无法创建或访问数据库文件
**解决**: 确保程序对目标目录有读写权限

### 2. 缓存数据过期
**问题**: 缓存数据过期导致频繁API调用
**解决**: 调整缓存过期时间或手动清理过期缓存

### 3. 数据库文件过大
**问题**: 长期使用后数据库文件变大
**解决**: 定期清理历史数据或压缩数据库

```python
# 清理30天前的查询记录
db_manager.cleanup_old_records(days=30)
```

## 后续优化建议

1. **数据压缩**: 对历史数据进行压缩存储
2. **分区存储**: 按时间范围分区存储数据
3. **索引优化**: 优化查询性能的数据库索引
4. **备份机制**: 自动备份重要的分析数据
5. **数据导出**: 支持将分析结果导出为Excel或CSV格式

## 支持与反馈

如有问题或建议，请联系开发团队或提交Issue。

---

*最后更新: 2025-08-22*