from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Optional
import sys
import os
import re
from pydantic import BaseModel

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

# 导入原有的分析模块
from tools.api import get_prices, prices_to_df, get_financial_metrics, cleanup_cache, get_cache_stats, clear_ticker_cache
from data.cache import get_cache
from data.database import get_database_manager
from utils.personal_indicators import generate_comprehensive_signal
from analyzers.fundamental_analyzer import FinnhubFundamentalAnalyzer

app = FastAPI(title="交易分析系统API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")

# 请求模型
class AnalysisRequest(BaseModel):
    tickers: List[str]
    start_date: str
    end_date: str
    enable_fundamental: bool = True
    show_detailed: bool = False
    show_historical: bool = False

class CacheClearRequest(BaseModel):
    ticker: Optional[str] = None

# 响应模型
class AnalysisResult(BaseModel):
    ticker: str
    ticker_display: str
    region: str
    current_price: float
    analysis: dict
    financial_metrics: dict
    fundamental_analysis: Optional[dict] = None
    data_days: int
    prices_df: Optional[dict] = None

class AnalysisResponse(BaseModel):
    results: List[AnalysisResult]
    cache_stats: Optional[dict] = None

# 工具函数
def detect_market_region(ticker: str) -> str:
    """检测股票代码的市场区域"""
    ticker = ticker.strip().upper()
    
    if ticker.startswith('HK.') or (ticker.isdigit() and len(ticker) in [4, 5]):
        return 'hk'
    
    if ticker.isdigit() and len(ticker) == 6:
        first_digit = ticker[0]
        if first_digit in ['6', '9']:
            return 'sh'
        elif first_digit in ['0', '3']:
            return 'sz'
    
    if ticker.endswith('.SH'):
        return 'sh'
    elif ticker.endswith('.SZ'):
        return 'sz'
    
    return 'us'

def format_ticker_display(ticker: str, region: str) -> str:
    """格式化股票代码显示"""
    region_names = {
        'us': '🇺🇸 美股',
        'hk': '🇭🇰 港股', 
        'sh': '🇨🇳 上证',
        'sz': '🇨🇳 深证',
        'sg': '🇸🇬 新加坡',
        'jp': '🇯🇵 日本'
    }
    return f"{ticker} ({region_names.get(region, '🌍 其他')})"

def validate_ticker_format(ticker: str) -> tuple[bool, str]:
    """验证股票代码格式"""
    ticker = ticker.strip().upper()
    
    if not ticker:
        return False, "股票代码不能为空"
    
    if re.match(r'^[A-Z]{1,5}$', ticker):
        return True, ""
    
    if re.match(r'^HK\.[0-9]{5}$', ticker):
        return True, ""
    
    if re.match(r'^[0-9]{4,5}$', ticker):
        return True, ""
    
    if re.match(r'^[0-9]{6}$', ticker):
        return True, ""
    
    if re.match(r'^[0-9]{6}\.(SH|SZ)$', ticker):
        return True, ""
    
    return False, f"不支持的股票代码格式: {ticker}"

def get_prices_with_region(ticker: str, start_date: str, end_date: str, region: str):
    """根据市场区域获取价格数据"""
    return get_prices(ticker, start_date, end_date, region)

def get_financial_metrics_with_region(ticker: str, end_date: str, region: str):
    """根据市场区域获取财务指标"""
    return get_financial_metrics(ticker, end_date, region=region)

# API路由
@app.get("/")
async def read_root():
    """返回前端页面"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_stocks(request: AnalysisRequest):
    """分析股票"""
    results = []
    
    for ticker in request.tickers:
        try:
            # 检测市场区域
            region = detect_market_region(ticker)
            ticker_display = format_ticker_display(ticker, region)
            
            # 验证股票代码
            is_valid, error_msg = validate_ticker_format(ticker)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # 获取扩展的历史数据
            extended_start = (datetime.strptime(request.start_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
            
            # 获取价格数据
            prices = get_prices_with_region(ticker, extended_start, request.end_date, region)
            if not prices:
                raise HTTPException(status_code=404, detail=f"无法获取 {ticker_display} 的价格数据")
            
            # 转换为DataFrame
            prices_df = prices_to_df(prices)
            if len(prices_df) < 30:
                raise HTTPException(status_code=400, detail=f"{ticker_display}数据不足（仅{len(prices_df)}天）")
            
            # 技术分析
            analysis_result = generate_comprehensive_signal(prices_df)
            
            # 获取财务指标
            pe_ratio = None
            pb_ratio = None
            try:
                financial_metrics = get_financial_metrics_with_region(ticker, request.end_date, region)
                if financial_metrics:
                    pe_ratio = financial_metrics[0].price_to_earnings_ratio
                    pb_ratio = financial_metrics[0].price_to_book_ratio
            except Exception:
                pass
            
            # 基本面分析
            fundamental_result = None
            if request.enable_fundamental and region == 'us':
                try:
                    analyzer = FinnhubFundamentalAnalyzer()
                    fundamental_result = analyzer.analyze_stock(ticker)
                except Exception:
                    pass
            
            # 获取当前价格
            current_price = prices_df['close'].iloc[-1] if len(prices_df) > 0 else None
            
            # 构建结果 - 修复 numpy 类型序列化问题
            prices_dict = None
            if request.show_historical:
                # 将 numpy 类型转换为 Python 原生类型
                prices_dict = prices_df.astype(object).where(pd.notnull(prices_df), None).to_dict()
            
            result = AnalysisResult(
                ticker=ticker,
                ticker_display=ticker_display,
                region=region,
                current_price=float(current_price) if current_price is not None else None,
                analysis=analysis_result,
                financial_metrics={
                    'pe_ratio': float(pe_ratio) if pe_ratio is not None else None,
                    'pb_ratio': float(pb_ratio) if pb_ratio is not None else None
                },
                fundamental_analysis=fundamental_result,
                data_days=int(len(prices_df)),
                prices_df=prices_dict
            )
            
            results.append(result)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"分析 {ticker} 时出错: {str(e)}")
    
    # 获取缓存统计
    cache_stats = get_cache_stats()
    
    return AnalysisResponse(results=results, cache_stats=cache_stats)

@app.post("/api/cache/clear")
async def clear_cache(request: CacheClearRequest = None):
    """清理缓存"""
    try:
        if request and request.ticker:
            # 清理特定股票的缓存
            cleared_count = clear_ticker_cache(request.ticker)
            return {"message": f"已清除 {request.ticker} 的缓存", "cleared_count": cleared_count}
        else:
            # 清理所有过期缓存
            cache_instance = get_cache()
            expired_count = cache_instance.clear_expired_cache()
            cleanup_cache()
            return {"message": "缓存清理完成", "expired_count": expired_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")

@app.get("/api/cache/stats")
async def get_cache_statistics():
    """获取缓存统计信息"""
    try:
        stats = get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)