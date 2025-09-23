# 对冲基金Agent数据服务修改计划

## 项目概述
针对当前项目中的多个对冲基金agent，修改底层的股价数据服务，使用akshare和finnhub作为主要数据源，确保数据不可用时直接跳过而不影响服务正常运行。

## 当前架构分析

### 数据服务现状
- **主要数据源**: AKShare（免费）、RapidAPI Yahoo Finance（备用）
- **财务数据源**: AKShare（主要）、Finnhub（备用）
- **缓存机制**: 内存缓存 + SQLite数据库缓存
- **问题**: 数据不可用时抛出异常，影响服务正常运行

### 对冲基金Agent现状
- Warren Buffett Agent
- Cathie Wood Agent  
- Stanley Druckenmiller Agent
- 其他多个专业投资策略Agent
- 都通过 `src/tools/api.py` 获取数据

## 修改目标

### 主要目标
1. **使用AKShare和Finnhub作为主要数据源**
2. **实现容错机制**：数据不可用时直接跳过，不影响服务
3. **配置DeepSeek作为默认基座模型**

### 具体修改内容

## 1. 价格数据获取逻辑修改 (`src/tools/api.py`)

### 当前问题
- 第240行：当所有数据源失败时抛出异常
- 缺少Finnhub作为价格数据源的支持

### 修改方案
```python
# 修改 _get_prices_intelligent_cache 函数中的错误处理
if not filtered_prices:
    # 改为记录警告而不是抛出异常
    print(f"⚠️ 警告：无法获取 {ticker} 在 {start_date} 到 {end_date} 期间的价格数据")
    print(f"   市场区域: {region}")
    print(f"   缓存数据: {len(all_cached_prices)} 条")
    print(f"   新获取数据: {len(new_prices)} 条")
    # 返回空列表而不是抛出异常
    return []
```

### 添加Finnhub价格数据支持
```python
def _fetch_prices_from_finnhub(ticker: str, start_date: str, end_date: str, region: str = 'us') -> list[Price]:
    """从Finnhub API获取价格数据（实时报价）"""
    try:
        import finnhub
        from datetime import datetime
        
        # 初始化Finnhub客户端
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            print("⚠️ Finnhub API密钥未配置")
            return []
            
        client = finnhub.Client(api_key=api_key)
        
        # Finnhub免费账户主要支持实时报价，历史数据有限
        # 获取实时报价作为补充
        quote_data = client.quote(ticker)
        
        if quote_data and quote_data.get('c'):
            # 创建Price对象
            current_time = datetime.now().strftime("%Y-%m-%d")
            price = Price(
                open=quote_data.get('o', 0),
                close=quote_data.get('c', 0),
                high=quote_data.get('h', 0),
                low=quote_data.get('l', 0),
                volume=quote_data.get('v', 0),
                time=current_time
            )
            return [price]
            
        return []
        
    except Exception as e:
        print(f"❌ Finnhub价格数据获取失败: {str(e)}")
        return []
```

## 2. 财务指标获取逻辑修改

### 当前问题
- 财务指标获取缺少完整的容错机制
- AKShare财务指标功能有限

### 修改方案
```python
# 在get_financial_metrics函数中增强容错
def get_financial_metrics(...):
    # 现有的缓存检查逻辑...
    
    # 增强数据源尝试逻辑
    data_sources = [
        ("akshare", _fetch_financial_metrics_from_akshare),
        ("finnhub", _fetch_financial_metrics_from_finnhub),
        ("rapidapi", _fetch_financial_metrics_from_rapidapi_yahoo)
    ]
    
    for source_name, fetch_func in data_sources:
        try:
            metrics = fetch_func(ticker, end_date, period, limit, region)
            if metrics:
                # 缓存并返回数据
                return metrics
        except Exception as e:
            print(f"❌ {source_name} API获取财务指标失败: {str(e)}")
            continue
    
    # 所有数据源都失败时返回空列表
    print(f"⚠️ 所有数据源都无法获取 {ticker} 的财务指标")
    return []
```

## 3. 数据源优先级配置

### 价格数据优先级
1. **AKShare** (主要) - 免费，支持多市场
2. **Finnhub** (备用) - 免费实时报价
3. **RapidAPI Yahoo Finance** (最后备用)

### 财务指标优先级  
1. **Finnhub** (主要) - 免费基础财务指标
2. **AKShare** (备用) - 功能有限但免费
3. **RapidAPI Yahoo Finance** (最后备用)

## 4. DeepSeek模型配置

### 修改 `src/llm/models.py`
```python
# 将DeepSeek设为默认模型
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_PROVIDER = ModelProvider.DEEPSEEK

# 在模型列表中优先显示DeepSeek
AVAILABLE_MODELS = [
    LLMModel(
        display_name="[推荐] deepseek-v3",
        model_name="deepseek-chat", 
        provider=ModelProvider.DEEPSEEK
    ),
    # 其他模型...
]
```

## 5. API密钥管理

### 更新 `.env.example`
```env
# 主要数据源API密钥
FINNHUB_API_KEY=your-finnhub-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key

# 备用数据源API密钥  
RAPIDAPI_YAHOO_KEY=your-rapidapi-yahoo-key
```

## 实施步骤

1. **切换到Code模式**进行代码修改
2. **修改价格数据获取逻辑** - 增强容错机制
3. **修改财务指标获取逻辑** - 完善数据源优先级
4. **添加Finnhub价格数据支持** - 扩展数据源
5. **配置DeepSeek为默认模型** - 更新模型配置
6. **测试数据服务** - 验证容错机制
7. **验证Agent调用** - 确保服务正常运行

## 预期效果

- ✅ 数据不可用时服务继续运行
- ✅ 使用免费可靠的AKShare和Finnhub数据源  
- ✅ DeepSeek作为默认AI模型
- ✅ 完整的容错和日志记录机制
- ✅ 不影响现有对冲基金Agent功能