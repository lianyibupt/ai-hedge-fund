"""
个性化投资组合管理器
适配2-3周交易周期，限制交易频率(2周内不超过10次)
"""

import json
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm


class PersonalPortfolioDecision(BaseModel):
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision")
    hold_period: str = Field(description="Expected holding period (2-3 weeks)")


class PersonalPortfolioOutput(BaseModel):
    decisions: dict[str, PersonalPortfolioDecision] = Field(description="Dictionary of ticker to trading decisions")


##### 个性化投资组合管理代理 #####
def personal_portfolio_management_agent(state: AgentState):
    """
    基于个人交易约束的投资组合管理
    - 交易周期: 2-3周
    - 交易频率: 2周内不超过10次
    - 只做多不做空
    """
    
    # 获取投资组合和分析师信号
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    tickers = state["data"]["tickers"]
    current_date = state["data"]["end_date"]

    progress.update_status("personal_portfolio_management_agent", None, "分析信号")

    # 检查交易频率限制
    trading_history = portfolio.get("trading_history", [])
    recent_trades = _count_recent_trades(trading_history, current_date)
    
    # 获取仓位限制、当前价格和信号
    position_limits = {}
    current_prices = {}
    max_shares = {}
    signals_by_ticker = {}
    
    for ticker in tickers:
        progress.update_status("personal_portfolio_management_agent", ticker, "处理分析师信号")

        # 获取风险管理数据
        risk_data = analyst_signals.get("risk_management_agent", {}).get(ticker, {})
        position_limits[ticker] = risk_data.get("remaining_position_limit", 0)
        current_prices[ticker] = risk_data.get("current_price", 0)

        # 计算最大允许购买股数
        if current_prices[ticker] > 0:
            max_shares[ticker] = int(position_limits[ticker] / current_prices[ticker])
        else:
            max_shares[ticker] = 0

        # 获取信号（重点关注个人交易代理的信号）
        ticker_signals = {}
        for agent, signals in analyst_signals.items():
            if agent != "risk_management_agent" and ticker in signals:
                # 给个人交易代理更高的权重
                weight = 0.6 if agent == "personal_trader_agent" else 0.4
                ticker_signals[agent] = {
                    "signal": signals[ticker]["signal"], 
                    "confidence": signals[ticker]["confidence"],
                    "weight": weight
                }
        signals_by_ticker[ticker] = ticker_signals

    progress.update_status("personal_portfolio_management_agent", None, "制定交易决策")

    # 生成交易决策
    result = generate_personal_trading_decision(
        tickers=tickers,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
        recent_trades_count=recent_trades,
        current_date=current_date,
        model_name=state["metadata"]["model_name"],
        model_provider=state["metadata"]["model_provider"],
    )

    # 更新交易历史
    _update_trading_history(portfolio, result.decisions, current_date, current_prices)

    # 创建投资组合管理消息
    message = HumanMessage(
        content=json.dumps({ticker: decision.model_dump() for ticker, decision in result.decisions.items()}),
        name="personal_portfolio_management",
    )

    # 显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(
            {ticker: decision.model_dump() for ticker, decision in result.decisions.items()}, 
            "个性化投资组合管理代理"
        )

    progress.update_status("personal_portfolio_management_agent", None, "完成")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }


def generate_personal_trading_decision(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict,
    recent_trades_count: int,
    current_date: str,
    model_name: str,
    model_provider: str,
) -> PersonalPortfolioOutput:
    """
    基于个人交易策略生成交易决策
    """
    
    # 预处理：检查持仓时间和交易频率
    filtered_decisions = {}
    
    for ticker in tickers:
        # 检查当前持仓
        current_position = portfolio.get("positions", {}).get(ticker, {}).get("long", 0)
        
        # 检查持仓时间
        if current_position > 0:
            position_hold_days = _calculate_position_hold_days(portfolio, ticker, current_date)
            
            # 如果持仓未满2周，一般继续持有（除非有强烈卖出信号）
            if position_hold_days < 14:
                personal_signal = signals_by_ticker.get(ticker, {}).get("personal_trader_agent", {})
                if personal_signal.get("signal") != "bearish" or personal_signal.get("confidence", 0) < 80:
                    filtered_decisions[ticker] = PersonalPortfolioDecision(
                        action="hold",
                        quantity=0,
                        confidence=70.0,
                        reasoning=f"持仓{position_hold_days}天，未满2周持仓期，继续持有",
                        hold_period="继续持有至2-3周"
                    )
                    continue
        
        # 检查交易频率限制
        if recent_trades_count >= 10:
            filtered_decisions[ticker] = PersonalPortfolioDecision(
                action="hold",
                quantity=0,
                confidence=60.0,
                reasoning="近期交易次数已达上限(10次)，暂停交易",
                hold_period="等待下个交易周期"
            )
            continue
        
        # 正常决策流程
        signals = signals_by_ticker.get(ticker, {})
        decision = _make_individual_decision(ticker, signals, current_prices, max_shares, portfolio, current_position)
        filtered_decisions[ticker] = decision
    
    return PersonalPortfolioOutput(decisions=filtered_decisions)


def _make_individual_decision(ticker: str, signals: dict, current_prices: dict, max_shares: dict, portfolio: dict, current_position: int) -> PersonalPortfolioDecision:
    """
    为单个股票制定交易决策
    """
    current_price = current_prices.get(ticker, 0)
    max_buy_shares = max_shares.get(ticker, 0)
    cash_available = portfolio.get("cash", 0)
    
    # 计算加权信号
    weighted_score = 0
    total_weight = 0
    confidence_sum = 0
    
    reasoning_parts = []
    
    for agent, signal_data in signals.items():
        signal = signal_data.get("signal", "neutral")
        confidence = signal_data.get("confidence", 50)
        weight = signal_data.get("weight", 0.4)
        
        if signal == "bullish":
            weighted_score += weight * (confidence / 100)
        elif signal == "bearish":
            weighted_score -= weight * (confidence / 100)
        
        total_weight += weight
        confidence_sum += confidence * weight
        
        reasoning_parts.append(f"{agent}: {signal}({confidence}%)")
    
    # 标准化得分
    if total_weight > 0:
        final_score = weighted_score / total_weight
        avg_confidence = confidence_sum / total_weight
    else:
        final_score = 0
        avg_confidence = 50
    
    # 决策逻辑
    if final_score > 0.3 and current_position == 0:  # 买入信号
        # 计算买入数量（保守策略，使用可用资金的30-50%）
        max_investment = cash_available * 0.4  # 使用40%的资金
        shares_to_buy = min(int(max_investment / current_price), max_buy_shares)
        shares_to_buy = max(shares_to_buy, 100)  # 最少买100股
        
        if shares_to_buy > 0 and shares_to_buy * current_price <= cash_available:
            return PersonalPortfolioDecision(
                action="buy",
                quantity=shares_to_buy,
                confidence=min(avg_confidence, 85),
                reasoning=f"买入信号: {'; '.join(reasoning_parts)}",
                hold_period="2-3周"
            )
    
    elif final_score < -0.3 and current_position > 0:  # 卖出信号
        # 卖出全部或部分仓位
        shares_to_sell = current_position
        
        return PersonalPortfolioDecision(
            action="sell",
            quantity=shares_to_sell,
            confidence=min(avg_confidence, 85),
            reasoning=f"卖出信号: {'; '.join(reasoning_parts)}",
            hold_period="已达目标周期"
        )
    
    # 默认持有
    return PersonalPortfolioDecision(
        action="hold",
        quantity=0,
        confidence=max(avg_confidence, 50),
        reasoning=f"信号不明确或不符合交易条件: {'; '.join(reasoning_parts)}",
        hold_period="继续观察"
    )


def _count_recent_trades(trading_history: list, current_date: str, days: int = 14) -> int:
    """
    计算最近指定天数内的交易次数
    """
    if not trading_history:
        return 0
    
    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    cutoff_date = current_dt - timedelta(days=days)
    
    recent_trades = 0
    for trade in trading_history:
        trade_date = datetime.strptime(trade["date"], "%Y-%m-%d")
        if trade_date >= cutoff_date and trade["action"] in ["buy", "sell"]:
            recent_trades += 1
    
    return recent_trades


def _calculate_position_hold_days(portfolio: dict, ticker: str, current_date: str) -> int:
    """
    计算当前持仓的持有天数
    """
    trading_history = portfolio.get("trading_history", [])
    
    # 找到最近的买入日期
    last_buy_date = None
    for trade in reversed(trading_history):
        if trade["ticker"] == ticker and trade["action"] == "buy":
            last_buy_date = trade["date"]
            break
    
    if not last_buy_date:
        return 0
    
    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    buy_dt = datetime.strptime(last_buy_date, "%Y-%m-%d")
    
    return (current_dt - buy_dt).days


def _update_trading_history(portfolio: dict, decisions: dict, current_date: str, current_prices: dict):
    """
    更新交易历史记录
    """
    if "trading_history" not in portfolio:
        portfolio["trading_history"] = []
    
    for ticker, decision in decisions.items():
        if decision.action in ["buy", "sell"]:
            portfolio["trading_history"].append({
                "date": current_date,
                "ticker": ticker,
                "action": decision.action,
                "quantity": decision.quantity,
                "price": current_prices.get(ticker, 0),
                "reasoning": decision.reasoning
            })
    
    # 保留最近6个月的交易记录
    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    cutoff_date = current_dt - timedelta(days=180)
    
    portfolio["trading_history"] = [
        trade for trade in portfolio["trading_history"]
        if datetime.strptime(trade["date"], "%Y-%m-%d") >= cutoff_date
    ]