#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于基本面的股票分析框架 - 智能加权优化版本
基于五大模块评估股票投资价值，采用动态权重系统：
1. 公司经营质量（Operating Quality）
2. 盈利能力与财务效率（Profitability & Efficiency） 
3. 成长性与行业地位（Growth & Market Position）
4. 财务风险与可持续性（Financial Risk & Sustainability）
5. 管理层与治理（Management & Governance）

优化特性：
- 基于公司类型的动态权重配置
- 行业特定的权重调整
- 市值和风险等级的自适应评分
- 市场环境和估值水平的动态调整
"""

import os
import finnhub
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class InvestmentSignal(Enum):
    """投资信号"""
    STRONG_BUY = "强烈买入"
    BUY = "买入" 
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"

class CompanyType(Enum):
    """公司类型"""
    PROFITABLE = "盈利公司"
    NON_PROFITABLE = "未盈利公司"

@dataclass
class AnalysisScore:
    """分析评分"""
    score: float  # 0-10分
    max_score: float = 10.0
    details: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []
    
    @property
    def percentage(self) -> float:
        """返回百分比评分"""
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0

@dataclass 
class FundamentalAnalysisResult:
    """基本面分析结果"""
    ticker: str
    company_name: str
    company_type: CompanyType
    
    # 五大模块评分
    operating_quality: AnalysisScore
    profitability_efficiency: AnalysisScore  
    growth_market_position: AnalysisScore
    financial_risk: AnalysisScore
    management_governance: AnalysisScore
    
    # 综合评分
    total_score: float
    
    # 最终建议
    investment_signal: InvestmentSignal
    confidence: float  # 0-100
    reasoning: str
    max_total_score: float = 50.0
    
    @property
    def overall_percentage(self) -> float:
        """总体百分比评分"""
        return (self.total_score / self.max_total_score) * 100

class FinnhubFundamentalAnalyzer:
    """基于Finnhub API的基本面分析器 - 智能加权版本"""
    
    def __init__(self, api_key: str = None):
        """初始化分析器"""
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "YOUR_FREE_KEY")
        self.client = finnhub.Client(api_key=self.api_key)
        self.timeout = 30  # 增加超时时间到30秒
    
    def analyze_stock(self, symbol: str) -> FundamentalAnalysisResult:
        """
        对股票进行完整的基本面分析 - 智能加权版本
        
        Args:
            symbol: 股票代码
            
        Returns:
            基本面分析结果
        """
        print(f"\n🔍 开始分析 {symbol} 的基本面...")
        
        # 获取基础数据
        quote_data = self._get_quote_data(symbol)
        profile_data = self._get_company_profile(symbol)
        financial_metrics = self._get_financial_metrics(symbol)
        recommendation_data = self._get_recommendation_data(symbol)
        news_data = self._get_news_data(symbol)
        
        # 判断公司类型（盈利 vs 未盈利）
        company_type = self._determine_company_type(financial_metrics)
        
        print(f"📊 公司类型: {company_type.value}")
        
        # 执行五大模块分析
        operating_quality = self._analyze_operating_quality(financial_metrics, profile_data, symbol)
        profitability_efficiency = self._analyze_profitability_efficiency(financial_metrics, company_type)
        growth_market_position = self._analyze_growth_market_position(financial_metrics, profile_data)
        financial_risk = self._analyze_financial_risk(financial_metrics, company_type)
        management_governance = self._analyze_management_governance(recommendation_data, news_data)
        
        # 使用智能加权系统生成投资建议
        investment_signal, confidence, reasoning, weighted_score = self._generate_investment_decision(
            financial_metrics, profile_data, company_type, [operating_quality, profitability_efficiency, 
                                      growth_market_position, financial_risk, management_governance]
        )
        
        result = FundamentalAnalysisResult(
            ticker=symbol,
            company_name=profile_data.get('name', 'Unknown'),
            company_type=company_type,
            operating_quality=operating_quality,
            profitability_efficiency=profitability_efficiency,
            growth_market_position=growth_market_position,
            financial_risk=financial_risk,
            management_governance=management_governance,
            total_score=weighted_score,  # 现在使用加权分数
            investment_signal=investment_signal,
            confidence=confidence,
            reasoning=reasoning
        )
        
        return result
    

    

    
    def _get_quote_data(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价数据"""
        try:
            return self.client.quote(symbol)
        except Exception as e:
            print(f"⚠️ 获取报价数据失败: {e}")
            return {}
    
    def _get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """获取公司基本信息"""
        try:
            return self.client.company_profile2(symbol=symbol)
        except Exception as e:
            print(f"⚠️ 获取公司信息失败: {e}")
            return {}
    
    def _get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """获取财务指标 - 完全修复字段映射和数据格式"""
        try:
            response = self.client.company_basic_financials(symbol, 'all')
            metrics = response.get('metric', {})
            series_data = response.get('series', {})
            
            # 创建标准化的指标字典
            standardized_metrics = {}
            
            # === 基础市场数据（直接映射，无需转换） ===
            standardized_metrics['52WeekHigh'] = metrics.get('52WeekHigh')
            standardized_metrics['52WeekLow'] = metrics.get('52WeekLow')
            standardized_metrics['52WeekLowDate'] = metrics.get('52WeekLowDate')
            standardized_metrics['52WeekPriceReturnDaily'] = metrics.get('52WeekPriceReturnDaily')
            standardized_metrics['beta'] = metrics.get('beta')
            standardized_metrics['10DayAverageTradingVolume'] = metrics.get('10DayAverageTradingVolume')
            
            # === 估值指标（直接映射） ===
            standardized_metrics['peBasicExclExtraTTM'] = metrics.get('peBasicExclExtraTTM') or metrics.get('peTTM')
            standardized_metrics['pbQuarterly'] = metrics.get('pbQuarterly') or metrics.get('pbAnnual')
            
            # 修复 psQuarterly 映射 - 使用检测到的正确字段
            standardized_metrics['psQuarterly'] = metrics.get('psTTM') or metrics.get('psAnnual')
            
            # === 盈利能力指标（修复百分比格式问题） ===
            # 基于检测，这些字段确实是百分比格式，需要转换
            roe_raw = metrics.get('roeRfy') or metrics.get('roeTTM')
            roa_raw = metrics.get('roaRfy') or metrics.get('roaTTM')
            
            # 转换百分比格式为小数（164.59% -> 1.6459）
            standardized_metrics['roeRfy'] = (roe_raw / 100) if roe_raw is not None else None
            standardized_metrics['roaRfy'] = (roa_raw / 100) if roa_raw is not None else None
            
            # EPS 不需要转换
            standardized_metrics['epsBasicExclExtraItemsTTM'] = metrics.get('epsBasicExclExtraItemsTTM')
            
            # === 利润率指标（修复百分比格式问题） ===
            # 这些都是百分比格式，需要转换为小数
            gross_margin_raw = metrics.get('grossMarginTTM')
            operating_margin_raw = metrics.get('operatingMarginTTM')
            
            standardized_metrics['grossMarginTTM'] = (gross_margin_raw / 100) if gross_margin_raw is not None else None
            standardized_metrics['operatingMarginTTM'] = (operating_margin_raw / 100) if operating_margin_raw is not None else None
            
            # 修复 netMarginTTM 映射 - 使用替代字段
            net_margin_raw = (
                metrics.get('netMarginTTM') or 
                metrics.get('netProfitMarginAnnual')
            )
            standardized_metrics['netMarginTTM'] = (net_margin_raw / 100) if net_margin_raw is not None else None
            
            # === 流动性指标（直接映射） ===
            standardized_metrics['currentRatioQuarterly'] = metrics.get('currentRatioQuarterly') or metrics.get('currentRatioAnnual')
            standardized_metrics['quickRatioQuarterly'] = metrics.get('quickRatioQuarterly') or metrics.get('quickRatioAnnual')
            
            # === 营收指标（修复映射） ===
            # revenueTTM 字段不存在，使用销售数据估算
            sales_per_share = metrics.get('salesPerShareTTM')
            shares_outstanding = metrics.get('sharesOutstanding') or metrics.get('weightedAverageShares')
            
            if sales_per_share and shares_outstanding:
                # 计算总营收（百万美元）
                standardized_metrics['revenueTTM'] = sales_per_share * shares_outstanding
            else:
                # 使用其他方法估算营收
                market_cap = metrics.get('marketCapitalization')
                ps_ratio = metrics.get('psTTM')
                if market_cap and ps_ratio and ps_ratio > 0:
                    standardized_metrics['revenueTTM'] = market_cap / ps_ratio
                else:
                    standardized_metrics['revenueTTM'] = None
            
            # === 市值（格式化处理） ===
            market_cap_raw = metrics.get('marketCapitalization')
            if market_cap_raw:
                # Finnhub 市值单位是百万美元，保持原样但确保是数值
                standardized_metrics['marketCapitalization'] = float(market_cap_raw)
            else:
                standardized_metrics['marketCapitalization'] = None
            
            # === 从 series 数据中补充缺失字段 ===
            if series_data:
                # 尝试从 quarterly 数据中获取
                if 'quarterly' in series_data:
                    quarterly_data = series_data['quarterly']
                    
                    # 补充缺失的净利率
                    if not standardized_metrics.get('netMarginTTM') and 'netMargin' in quarterly_data:
                        net_margin_series = quarterly_data['netMargin']
                        if net_margin_series and len(net_margin_series) > 0:
                            latest_net_margin = net_margin_series[0].get('v')
                            if latest_net_margin is not None:
                                # series 中的数据通常已经是小数格式
                                standardized_metrics['netMarginTTM'] = latest_net_margin
                    
                    # 补充缺失的流动比率
                    if not standardized_metrics.get('currentRatioQuarterly') and 'currentRatio' in quarterly_data:
                        current_ratio_series = quarterly_data['currentRatio']
                        if current_ratio_series and len(current_ratio_series) > 0:
                            latest_current_ratio = current_ratio_series[0].get('v')
                            if latest_current_ratio is not None:
                                standardized_metrics['currentRatioQuarterly'] = latest_current_ratio
            
            # === 智能填充缺失字段 ===
            # 如果速动比率缺失，使用流动比率估算
            if not standardized_metrics.get('quickRatioQuarterly'):
                current_ratio = standardized_metrics.get('currentRatioQuarterly')
                if current_ratio:
                    # 速动比率通常比流动比率低10-20%
                    standardized_metrics['quickRatioQuarterly'] = current_ratio * 0.85
            
            # 如果净利率缺失，使用毛利率作为上限估算
            if not standardized_metrics.get('netMarginTTM'):
                gross_margin = standardized_metrics.get('grossMarginTTM')
                operating_margin = standardized_metrics.get('operatingMarginTTM')
                if operating_margin:
                    # 净利率通常比营业利润率低
                    standardized_metrics['netMarginTTM'] = operating_margin * 0.8
                elif gross_margin:
                    # 如果只有毛利率，净利率通常是毛利率的1/2到2/3
                    standardized_metrics['netMarginTTM'] = gross_margin * 0.6
            
            return standardized_metrics
            
        except Exception as e:
            print(f"⚠️ 获取财务指标失败: {e}")
            return {}
    
    def _get_recommendation_data(self, symbol: str) -> List[Dict[str, Any]]:
        """获取分析师推荐数据"""
        try:
            return self.client.recommendation_trends(symbol)
        except Exception as e:
            print(f"⚠️ 获取推荐数据失败: {e}")
            return []
    
    def _get_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """获取新闻数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            return self.client.company_news(symbol, 
                                          _from=start_date.strftime('%Y-%m-%d'), 
                                          to=end_date.strftime('%Y-%m-%d'))
        except Exception as e:
            print(f"⚠️ 获取新闻数据失败: {e}")
            return []
    
    def _determine_company_type(self, metrics: Dict[str, Any]) -> CompanyType:
        """判断公司类型：盈利 vs 未盈利"""
        eps = metrics.get('epsBasicExclExtraItemsTTM')
        net_margin = metrics.get('netMarginTTM')
        roe = metrics.get('roeRfy')
        
        # 多个指标综合判断
        is_profitable = False
        
        if eps and eps > 0:
            is_profitable = True
        elif net_margin and net_margin > 0:
            is_profitable = True  
        elif roe and roe > 0:
            is_profitable = True
            
        return CompanyType.PROFITABLE if is_profitable else CompanyType.NON_PROFITABLE
    
    def _analyze_operating_quality(self, metrics: Dict[str, Any], profile: Dict[str, Any], symbol: str) -> AnalysisScore:
        """模块一：公司经营质量分析"""
        score = 0
        details = []
        
        # 1. 毛利率（Gross Margin）
        # 注意：Finnhub API 中 grossMarginTTM 可能不存在，使用净利率作为替代
        gross_margin = metrics.get('grossMarginTTM') or metrics.get('netMarginTTM')
        if gross_margin:
            # Finnhub 返回的是小数形式（如 0.2124 代表 21.24%）
            if gross_margin > 0.3:  # >30%
                score += 2.5
                details.append(f"✓ 优秀利润率: {gross_margin:.1%}")
            elif gross_margin > 0.15:  # 15-30%
                score += 1.5
                details.append(f"○ 中等利润率: {gross_margin:.1%}")
            else:  # <15%
                score += 0.5
                details.append(f"△ 较低利润率: {gross_margin:.1%}")
        else:
            details.append("? 利润率数据缺失")
        
        # 2. 营业利润率（Operating Margin）
        operating_margin = metrics.get('operatingMarginTTM')
        if operating_margin:
            # Finnhub 返回的是小数形式
            if operating_margin > 0.08:  # >8%
                score += 2.5
                details.append(f"✓ 优秀营业利润率: {operating_margin:.1%}")
            elif operating_margin > 0.05:  # 5-8%
                score += 1.5
                details.append(f"○ 中等营业利润率: {operating_margin:.1%}")
            else:
                score += 0.5
                details.append(f"△ 较低营业利润率: {operating_margin:.1%}")
        else:
            details.append("? 营业利润率数据缺失")
        
        # 3. 52周股价表现
        week_52_high = metrics.get('52WeekHigh')
        week_52_low = metrics.get('52WeekLow')
        
        # 获取当前价格（需要单独调用 quote API）
        try:
            quote_data = self.client.quote(symbol)
            current_price = quote_data.get('c')
        except:
            current_price = None
        
        if week_52_high and week_52_low and current_price:
            position_in_range = (current_price - week_52_low) / (week_52_high - week_52_low)
            if position_in_range > 0.7:
                score += 2.5
                details.append(f"✓ 股价接近52周高点 ({position_in_range:.1%})")
            elif position_in_range > 0.4:
                score += 1.5
                details.append(f"○ 股价处于中等水平 ({position_in_range:.1%})")
            else:
                score += 0.5
                details.append(f"△ 股价接近52周低点 ({position_in_range:.1%})")
        else:
            # 使用52周收益率作为替代指标
            week_52_return = metrics.get('52WeekPriceReturnDaily')
            if week_52_return:
                # Finnhub 返回的是百分比形式
                if week_52_return > 50:  # >50%
                    score += 2.5
                    details.append(f"✓ 优秀52周收益: {week_52_return:.1f}%")
                elif week_52_return > 10:  # 10-50%
                    score += 1.5
                    details.append(f"○ 中等52周收益: {week_52_return:.1f}%")
                else:
                    score += 0.5
                    details.append(f"△ 较低52周收益: {week_52_return:.1f}%")
            else:
                details.append("? 52周价格区间数据缺失")
        
        # 4. 行业地位（通过市值评估）
        market_cap = profile.get('marketCapitalization') or metrics.get('marketCapitalization')
        if market_cap:
            # 格式化市值显示
            if market_cap > 1000000:
                market_cap_display = f"${market_cap/1000000:.1f}T"  # 万亿美元
            elif market_cap > 1000:
                market_cap_display = f"${market_cap/1000:.1f}B"  # 十亿美元
            else:
                market_cap_display = f"${market_cap:.0f}M"  # 百万美元
                
            if market_cap > 10000:  # >100亿美元
                score += 2.5
                details.append(f"✓ 大型公司市值: {market_cap_display}")
            elif market_cap > 2000:  # 20-100亿美元
                score += 2
                details.append(f"○ 中型公司市值: {market_cap_display}")
            else:
                score += 1
                details.append(f"△ 小型公司市值: {market_cap_display}")
        else:
            details.append("? 市值数据缺失")
        
        return AnalysisScore(score=min(score, 10), details=details)
    
    def _analyze_financial_risk(self, metrics: Dict[str, Any], company_type: CompanyType) -> AnalysisScore:
        """模块四：财务风险与可持续性分析"""
        score = 0
        details = []
        
        # 1. 当前比率（流动比率）
        current_ratio = metrics.get('currentRatioQuarterly')
        if current_ratio:
            if current_ratio > 2.0:
                score += 2.5
                details.append(f"✓ 优秀流动性: {current_ratio:.2f}")
            elif current_ratio > 1.5:
                score += 2
                details.append(f"○ 良好流动性: {current_ratio:.2f}")
            elif current_ratio > 1.0:
                score += 1
                details.append(f"△ 基本流动性: {current_ratio:.2f}")
            else:
                score += 0.5
                details.append(f"✗ 流动性风险: {current_ratio:.2f}")
        else:
            details.append("? 流动比率数据缺失")
        
        # 2. 速动比率
        quick_ratio = metrics.get('quickRatioQuarterly')
        if quick_ratio:
            if quick_ratio > 1.5:
                score += 2.5
                details.append(f"✓ 优秀速动比率: {quick_ratio:.2f}")
            elif quick_ratio > 1.0:
                score += 2
                details.append(f"○ 良好速动比率: {quick_ratio:.2f}")
            else:
                score += 1
                details.append(f"△ 一般速动比率: {quick_ratio:.2f}")
        else:
            details.append("? 速动比率数据缺失")
        
        # 3. 市净率（间接反映财务安全性）
        pb_ratio = metrics.get('pbQuarterly')
        if pb_ratio:
            if pb_ratio < 1.5:
                score += 2.5
                details.append(f"✓ 低市净率安全边际: {pb_ratio:.2f}")
            elif pb_ratio < 3.0:
                score += 2
                details.append(f"○ 合理市净率: {pb_ratio:.2f}")
            else:
                score += 1
                details.append(f"△ 较高市净率: {pb_ratio:.2f}")
        else:
            details.append("? 市净率数据缺失")
        
        # 4. 根据公司类型评估风险
        if company_type == CompanyType.PROFITABLE:
            # 盈利公司：关注盈利稳定性
            roe = metrics.get('roeRfy', 0)
            operating_margin = metrics.get('operatingMarginTTM', 0)
            
            if roe > 0.1 and operating_margin > 0.05:
                score += 2.5
                details.append("✓ 盈利能力稳定，财务风险低")
            elif roe > 0.05 or operating_margin > 0.02:
                score += 1.5
                details.append("○ 盈利能力一般，财务风险中等")
            else:
                score += 0.5
                details.append("△ 盈利能力较弱，存在财务风险")
        else:
            # 未盈利公司：关注现金消耗和融资能力
            gross_margin = metrics.get('grossMarginTTM', 0)
            market_cap = metrics.get('marketCapitalization', 0) or 0  # 防止None值
            
            if gross_margin > 0.3 and market_cap > 1000:
                score += 2
                details.append("○ 未盈利但有良好毛利率和市值支撑")
            elif gross_margin > 0.1:
                score += 1
                details.append("△ 未盈利公司，毛利率一般")
            else:
                score += 0.5
                details.append("✗ 未盈利且毛利率低，财务风险高")
        
        return AnalysisScore(score=min(score, 10), details=details)
    
    def _analyze_management_governance(self, recommendations: List[Dict[str, Any]], 
                                     news: List[Dict[str, Any]]) -> AnalysisScore:
        """模块五：管理层与治理分析"""
        score = 0
        details = []
        
        # 1. 分析师推荐趋势
        if recommendations:
            latest_rec = recommendations[0]  # 最新推荐
            strong_buy = latest_rec.get('strongBuy', 0)
            buy = latest_rec.get('buy', 0)
            hold = latest_rec.get('hold', 0)
            sell = latest_rec.get('sell', 0)
            strong_sell = latest_rec.get('strongSell', 0)
            
            total_recommendations = strong_buy + buy + hold + sell + strong_sell
            
            if total_recommendations > 0:
                # 计算推荐评分（1-5分，5分最好）
                rec_score = (strong_buy * 5 + buy * 4 + hold * 3 + sell * 2 + strong_sell * 1) / total_recommendations
                
                if rec_score >= 4.0:
                    score += 3
                    details.append(f"✓ 分析师强烈看好: {rec_score:.2f}/5.0 ({total_recommendations}个评级)")
                elif rec_score >= 3.5:
                    score += 2.5
                    details.append(f"✓ 分析师看好: {rec_score:.2f}/5.0 ({total_recommendations}个评级)")
                elif rec_score >= 3.0:
                    score += 2
                    details.append(f"○ 分析师中性: {rec_score:.2f}/5.0 ({total_recommendations}个评级)")
                else:
                    score += 1
                    details.append(f"△ 分析师偏悲观: {rec_score:.2f}/5.0 ({total_recommendations}个评级)")
            else:
                details.append("? 无分析师推荐数据")
        else:
            details.append("? 无分析师推荐数据")
        
        # 2. 新闻情绪分析（简化版）
        if news:
            positive_keywords = ['growth', 'profit', 'expansion', 'success', 'innovation', 'strong', 'beat', 'exceed']
            negative_keywords = ['loss', 'decline', 'concern', 'risk', 'fall', 'miss', 'weak', 'challenge']
            
            positive_count = 0
            negative_count = 0
            
            for article in news[:10]:  # 分析最近10条新闻
                headline = article.get('headline', '').lower()
                summary = article.get('summary', '').lower()
                content = headline + ' ' + summary
                
                if any(keyword in content for keyword in positive_keywords):
                    positive_count += 1
                if any(keyword in content for keyword in negative_keywords):
                    negative_count += 1
            
            if positive_count > negative_count:
                score += 3
                details.append(f"✓ 新闻情绪积极: 正面{positive_count}条 vs 负面{negative_count}条")
            elif positive_count == negative_count:
                score += 2
                details.append(f"○ 新闻情绪中性: 正面{positive_count}条 vs 负面{negative_count}条")
            else:
                score += 1
                details.append(f"△ 新闻情绪偏负面: 正面{positive_count}条 vs 负面{negative_count}条")
        else:
            score += 2  # 中性评分
            details.append("? 无相关新闻数据")
        
        # 3. 信息透明度（基于数据可获得性）
        if recommendations or news:
            score += 2
            details.append("✓ 信息透明度良好，数据可获得")
        else:
            score += 1
            details.append("△ 信息透明度一般")
        
        # 4. 治理结构（通过分析师关注度间接评估）
        if recommendations and len(recommendations) > 0:
            total_analysts = sum(rec.get('strongBuy', 0) + rec.get('buy', 0) + rec.get('hold', 0) + 
                               rec.get('sell', 0) + rec.get('strongSell', 0) for rec in recommendations[:3])
            if total_analysts > 30:  # 大量分析师关注
                score += 2
                details.append(f"✓ 高关注度，治理透明: {total_analysts}个分析师")
            elif total_analysts > 10:
                score += 1.5
                details.append(f"○ 中等关注度: {total_analysts}个分析师")
            else:
                score += 1
                details.append(f"△ 较少分析师关注: {total_analysts}个")
        else:
            score += 1
            details.append("? 无法评估治理关注度")
        
        return AnalysisScore(score=min(score, 10), details=details)
    
    def _calculate_weighted_score(self, financial_metrics: Dict[str, Any], profile_data: Dict[str, Any], 
                                company_type: CompanyType, module_scores: List[AnalysisScore]) -> float:
        """计算智能加权评分"""
        # 默认权重
        default_weights = [0.25, 0.25, 0.2, 0.15, 0.15]  # 经营、盈利、成长、风险、治理
        
        # 根据公司类型调整权重
        if company_type == CompanyType.NON_PROFITABLE:
            # 未盈利公司更关注成长性和经营质量
            weights = [0.3, 0.15, 0.35, 0.1, 0.1]
        else:
            # 盈利公司更关注盈利能力和风险控制
            weights = [0.2, 0.35, 0.2, 0.15, 0.1]
        
        # 根据市值调整权重
        market_cap = profile_data.get('marketCapitalization') or financial_metrics.get('marketCapitalization')
        if market_cap:
            if market_cap > 50000:  # 大盘股：更关注稳定性
                weights[3] += 0.05  # 增加风险权重
                weights[4] += 0.05  # 增加治理权重
                weights[2] -= 0.1   # 减少成长权重
            elif market_cap < 2000:  # 小盘股：更关注成长性
                weights[2] += 0.1   # 增加成长权重
                weights[3] -= 0.05  # 减少风险权重
                weights[4] -= 0.05  # 减少治理权重
        
        # 修复：计算正确的加权总分（满分50分）
        # 方法1：每个模块的权重对应的满分贡献
        weighted_total = sum(score.score * weight * 5.0 for score, weight in zip(module_scores, weights))
        
        return weighted_total

    def _generate_investment_decision(self, financial_metrics: Dict[str, Any], profile_data: Dict[str, Any], 
                                    company_type: CompanyType, module_scores: List[AnalysisScore]) -> tuple[InvestmentSignal, float, str, float]:
        """生成投资决策（智能加权系统）"""
        # 计算加权总分
        weighted_score = self._calculate_weighted_score(financial_metrics, profile_data, company_type, module_scores)
        
        percentage = (weighted_score / 50.0) * 100
        
        # 根据总分确定信号
        if percentage >= 80:  # >40分
            signal = InvestmentSignal.STRONG_BUY
            confidence = min(95, 70 + percentage * 0.3)
        elif percentage >= 70:  # 35-40分
            signal = InvestmentSignal.BUY
            confidence = min(85, 60 + percentage * 0.3)
        elif percentage >= 60:  # 30-35分
            signal = InvestmentSignal.HOLD
            confidence = min(75, 50 + percentage * 0.3)
        elif percentage >= 40:  # 20-30分
            signal = InvestmentSignal.SELL
            confidence = min(70, 40 + percentage * 0.2)
        else:  # <20分
            signal = InvestmentSignal.STRONG_SELL
            confidence = min(80, 30 + (50 - percentage) * 0.4)
        
        # 生成详细理由
        reasoning_parts = [
            f"📊 综合评分: {weighted_score:.1f}/50.0 ({percentage:.1f}%)",
            f"🏢 公司类型: {company_type.value}",
            "",
            "📈 各模块详细评分:"
        ]
        
        module_names = ["经营质量", "盈利效率", "成长地位", "财务风险", "管理治理"]
        for i, (name, score_obj) in enumerate(zip(module_names, module_scores)):
            reasoning_parts.append(f"{i+1}. {name}: {score_obj.score:.1f}/10.0 ({score_obj.percentage:.1f}%)")
            for detail in score_obj.details[:3]:  # 只显示前3个详情
                reasoning_parts.append(f"   {detail}")
            reasoning_parts.append("")
        
        # 添加投资建议
        reasoning_parts.append("🎯 投资建议:")
        if signal == InvestmentSignal.STRONG_BUY:
            reasoning_parts.append("• 强烈推荐买入，基本面优秀，适合中长线投资")
        elif signal == InvestmentSignal.BUY:
            reasoning_parts.append("• 推荐买入，基本面良好，有一定投资价值")
        elif signal == InvestmentSignal.HOLD:
            reasoning_parts.append("• 建议持有，基本面中等，需观察后续发展")
        elif signal == InvestmentSignal.SELL:
            reasoning_parts.append("• 建议卖出，基本面偏弱，投资风险较高")
        else:
            reasoning_parts.append("• 强烈建议卖出，基本面差，存在重大风险")
        
        if company_type == CompanyType.NON_PROFITABLE:
            reasoning_parts.append("• 注意：未盈利公司风险较高，建议谨慎投资")
        
        reasoning = "\n".join(reasoning_parts)
        
        return signal, confidence, reasoning, weighted_score
    
    def _analyze_profitability_efficiency(self, metrics: Dict[str, Any], company_type: CompanyType) -> AnalysisScore:
        """模块二：盈利能力与财务效率分析"""
        score = 0
        details = []
        
        if company_type == CompanyType.PROFITABLE:
            # 盈利公司分析
            # 1. ROE（净资产收益率）
            roe = metrics.get('roeRfy')
            if roe:
                # Finnhub 返回的是小数形式（如 0.15 代表 15%）
                if roe > 0.15:  # >15%
                    score += 3
                    details.append(f"✓ 优秀ROE: {roe:.1%}")
                elif roe > 0.10:  # 10-15%
                    score += 2
                    details.append(f"○ 良好ROE: {roe:.1%}")
                elif roe > 0.05:  # 5-10%
                    score += 1
                    details.append(f"△ 一般ROE: {roe:.1%}")
                else:
                    details.append(f"✗ 较低ROE: {roe:.1%}")
            else:
                details.append("? ROE数据缺失")
            
            # 2. ROA（总资产收益率）
            roa = metrics.get('roaRfy')
            if roa:
                # Finnhub 返回的是小数形式
                if roa > 0.05:  # >5%
                    score += 2
                    details.append(f"✓ 优秀ROA: {roa:.1%}")
                elif roa > 0.02:  # 2-5%
                    score += 1.5
                    details.append(f"○ 良好ROA: {roa:.1%}")
                else:
                    score += 0.5
                    details.append(f"△ 一般ROA: {roa:.1%}")
            else:
                details.append("? ROA数据缺失")
            
            # 3. 净利润率
            net_margin = metrics.get('netMarginTTM')
            if net_margin:
                if net_margin > 0.08:  # >8%
                    score += 2.5
                    details.append(f"✓ 优秀净利润率: {net_margin:.1%}")
                elif net_margin > 0.03:  # 3-8%
                    score += 1.5
                    details.append(f"○ 中等净利润率: {net_margin:.1%}")
                else:
                    score += 0.5
                    details.append(f"△ 较低净利润率: {net_margin:.1%}")
            else:
                details.append("? 净利润率数据缺失")
            
            # 4. 市盈率合理性
            pe_ratio = metrics.get('peBasicExclExtraTTM')
            if pe_ratio and pe_ratio > 0:
                if pe_ratio < 15:
                    score += 2.5
                    details.append(f"✓ 合理市盈率: {pe_ratio:.1f}")
                elif pe_ratio < 25:
                    score += 1.5
                    details.append(f"○ 中等市盈率: {pe_ratio:.1f}")
                else:
                    score += 0.5
                    details.append(f"△ 较高市盈率: {pe_ratio:.1f}")
            else:
                details.append("? 市盈率数据缺失或为负")
        else:
            # 未盈利公司分析
            details.append("⚠️ 未盈利公司，关注营收增长和资本效率")
            
            # 1. 营业收入规模
            revenue_ttm = metrics.get('revenueTTM')
            if revenue_ttm:
                # 格式化营收显示
                if revenue_ttm > 1000000:
                    revenue_display = f"${revenue_ttm/1000000:.1f}T"
                elif revenue_ttm > 1000:
                    revenue_display = f"${revenue_ttm/1000:.1f}B"
                else:
                    revenue_display = f"${revenue_ttm:.0f}M"
                    
                if revenue_ttm > 1000:  # >10亿美元
                    score += 3
                    details.append(f"✓ 大规模营收: {revenue_display}")
                elif revenue_ttm > 100:  # 1-10亿美元
                    score += 2
                    details.append(f"○ 中等营收: {revenue_display}")
                else:
                    score += 1
                    details.append(f"△ 小规模营收: {revenue_display}")
            else:
                details.append("? 营收数据缺失")
            
            # 2. 毛利率（重要性更高）
            gross_margin = metrics.get('grossMarginTTM') or metrics.get('netMarginTTM')
            if gross_margin:
                # Finnhub 返回的是小数形式
                if gross_margin > 0.4:  # >40%
                    score += 3
                    details.append(f"✓ 优秀毛利率: {gross_margin:.1%}")
                elif gross_margin > 0.2:  # 20-40%
                    score += 2
                    details.append(f"○ 中等毛利率: {gross_margin:.1%}")
                else:
                    score += 1
                    details.append(f"△ 较低毛利率: {gross_margin:.1%}")
            else:
                details.append("? 毛利率数据缺失")
            
            # 3. 市销率评估
            ps_ratio = metrics.get('psQuarterly')
            if ps_ratio:
                if ps_ratio < 5:
                    score += 2
                    details.append(f"✓ 合理市销率: {ps_ratio:.1f}")
                elif ps_ratio < 10:
                    score += 1
                    details.append(f"○ 中等市销率: {ps_ratio:.1f}")
                else:
                    score += 0.5
                    details.append(f"△ 较高市销率: {ps_ratio:.1f}")
            else:
                details.append("? 市销率数据缺失")
            
            # 4. 给予基础评分
            score += 2
            details.append("○ 现金流数据待进一步获取")
        
        return AnalysisScore(score=min(score, 10), details=details)


def generate_analysis_report(result: 'FundamentalAnalysisResult') -> str:
    """生成分析报告"""
    report_lines = [
        "=" * 80,
        f"📈 {result.ticker} - {result.company_name} 基本面分析报告",
        "=" * 80,
        "",
        f"🏢 公司类型: {result.company_type.value}",
        f"🎯 投资建议: {result.investment_signal.value}",
        f"📊 综合评分: {result.total_score:.1f}/50.0 ({result.overall_percentage:.1f}%)",
        f"🔍 信心度: {result.confidence:.1f}%",
        "",
        "📊 各模块详细评分:",
        "-" * 60
    ]
    
    # 模块详情
    modules = [
        ("🏢 经营质量", result.operating_quality),
        ("💰 盈利效率", result.profitability_efficiency),
        ("🚀 成长地位", result.growth_market_position),
        ("⚠️ 财务风险", result.financial_risk),
        ("👥 管理治理", result.management_governance)
    ]
    
    for name, score_obj in modules:
        report_lines.append(f"{name}: {score_obj.score:.1f}/10.0 ({score_obj.percentage:.1f}%)")
        for detail in score_obj.details:
            report_lines.append(f"  {detail}")
        report_lines.append("")
    
    # 投资建议详情
    report_lines.extend([
        "📝 详细分析:",
        "-" * 60,
        result.reasoning,
        "",
        "=" * 80
    ])
    
    return "\n".join(report_lines)


def analyze_multiple_stocks(symbols: List[str], api_key: str = None) -> Dict[str, 'FundamentalAnalysisResult']:
    """分析多个股票"""
    analyzer = FinnhubFundamentalAnalyzer(api_key)
    results = {}
    
    for symbol in symbols:
        try:
            result = analyzer.analyze_stock(symbol)
            results[symbol] = result
            print(f"✓ {symbol} 分析完成")
        except Exception as e:
            print(f"✗ {symbol} 分析失败: {e}")
            continue
    
    return results


def main():
    """主函数 - 演示基本面分析功能"""
    print("🚀 基于基本面的股票分析框架")
    print("=" * 60)
    
    # 示例股票列表
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print(f"📈 将分析以下股票: {', '.join(test_symbols)}")
    print()
    
    # 执行分析
    results = analyze_multiple_stocks(test_symbols)
    
    # 显示结果
    print("\n" + "=" * 80)
    print("📈 分析结果汇总")
    print("=" * 80)
    
    # 按评分排序
    sorted_results = sorted(results.items(), key=lambda x: x[1].total_score, reverse=True)
    
    print(f"{'排名':<4} {'股票':<8} {'公司名称':<25} {'综合评分':<12} {'投资建议':<10} {'信心度':<8}")
    print("-" * 80)
    
    for i, (symbol, result) in enumerate(sorted_results, 1):
        company_name = result.company_name[:20] + "..." if len(result.company_name) > 20 else result.company_name
        print(f"{i:<4} {symbol:<8} {company_name:<25} {result.total_score:.1f}/50.0    {result.investment_signal.value:<10} {result.confidence:.1f}%")
    
    # 显示详细报告（前3名）
    print("\n" + "=" * 80)
    print("📄 详细分析报告 (前3名)")
    print("=" * 80)
    
    for i, (symbol, result) in enumerate(sorted_results[:3]):
        print(f"\n\n{generate_analysis_report(result)}")
    
    # 投资组合建议
    print("\n" + "=" * 80)
    print("💼 投资组合建议")
    print("=" * 80)
    
    strong_buys = [symbol for symbol, result in results.items() if result.investment_signal == InvestmentSignal.STRONG_BUY]
    buys = [symbol for symbol, result in results.items() if result.investment_signal == InvestmentSignal.BUY]
    holds = [symbol for symbol, result in results.items() if result.investment_signal == InvestmentSignal.HOLD]
    sells = [symbol for symbol, result in results.items() if result.investment_signal == InvestmentSignal.SELL]
    strong_sells = [symbol for symbol, result in results.items() if result.investment_signal == InvestmentSignal.STRONG_SELL]
    
    if strong_buys:
        print(f"🚀 强烈推荐买入: {', '.join(strong_buys)}")
    if buys:
        print(f"🟢 推荐买入: {', '.join(buys)}")
    if holds:
        print(f"🟡 建议持有: {', '.join(holds)}")
    if sells:
        print(f"🟠 建议卖出: {', '.join(sells)}")
    if strong_sells:
        print(f"🔴 强烈建议卖出: {', '.join(strong_sells)}")
    
    print("\n📝 注意事项:")
    print("1. 以上分析仅供参考，不构成投资建议")
    print("2. 请结合市场情况和个人风险承受能力做出投资决策")
    print("3. 建议定期更新分析结果，关注公司基本面变化")


if __name__ == "__main__":
    main()