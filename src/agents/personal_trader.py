"""
个性化交易代理
基于2-3周交易周期的技术分析策略
实现MACD、RSI、布林带和成交量的综合分析
"""

import json
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_prices, prices_to_df
from utils.progress import progress
from utils.personal_indicators import (
    calculate_macd,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_volume_analysis,
    analyze_macd_signals,
    analyze_rsi_signals,
    analyze_bollinger_signals,
    analyze_volume_signals,
    generate_comprehensive_signal
)
from datetime import datetime, timedelta


def personal_trader_agent(state: AgentState):
    """
    个性化交易代理 - 基于用户定制的2-3周交易策略
    使用MACD、RSI、布林带和成交量分析生成交易信号
    """
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    # 初始化分析结果
    personal_analysis = {}

    for ticker in tickers:
        progress.update_status("personal_trader_agent", ticker, "获取价格数据")

        # 获取历史价格数据（需要更多数据来计算技术指标）
        # 为了计算技术指标，我们需要更长的历史数据
        extended_start = _get_extended_start_date(start_date)
        
        prices = get_prices(
            ticker=ticker,
            start_date=extended_start,
            end_date=end_date,
        )

        if not prices:
            progress.update_status("personal_trader_agent", ticker, "失败: 无法获取价格数据")
            continue

        # 转换为DataFrame
        prices_df = prices_to_df(prices)
        
        if len(prices_df) < 30:
            progress.update_status("personal_trader_agent", ticker, "失败: 数据不足")
            continue

        progress.update_status("personal_trader_agent", ticker, "分析技术指标")

        # 生成综合交易信号
        comprehensive_result = generate_comprehensive_signal(prices_df)
        
        # 检查是否符合交易条件
        trade_decision = _evaluate_trade_decision(comprehensive_result)
        
        # 生成详细的分析报告
        detailed_analysis = _generate_detailed_analysis(prices_df, comprehensive_result, trade_decision)
        
        personal_analysis[ticker] = {
            "signal": trade_decision["action"],
            "confidence": trade_decision["confidence"],
            "reasoning": detailed_analysis,
            "technical_details": comprehensive_result["details"],
            "entry_conditions": trade_decision.get("entry_conditions", {}),
            "exit_conditions": trade_decision.get("exit_conditions", {})
        }

        progress.update_status("personal_trader_agent", ticker, "完成")

    # 创建消息
    message = HumanMessage(
        content=json.dumps(personal_analysis),
        name="personal_trader_agent",
    )

    # 显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(personal_analysis, "个性化交易代理")

    # 添加到分析师信号
    state["data"]["analyst_signals"]["personal_trader_agent"] = personal_analysis

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }


def _get_extended_start_date(start_date: str, extend_days: int = 90) -> str:
    """
    获取扩展的开始日期，用于计算技术指标
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    extended_start_dt = start_dt - timedelta(days=extend_days)
    return extended_start_dt.strftime("%Y-%m-%d")


def _evaluate_trade_decision(comprehensive_result: dict) -> dict:
    """
    基于综合信号评估交易决策
    """
    signal = comprehensive_result["signal"]
    confidence = comprehensive_result["confidence"]
    details = comprehensive_result["details"]
    
    # 买入条件检查
    if signal == "bullish":
        buy_conditions = _check_buy_conditions(details)
        if buy_conditions["is_valid"]:
            return {
                "action": "bullish",
                "confidence": confidence,
                "entry_conditions": buy_conditions,
                "reason": f"买入信号确认: {buy_conditions['summary']}"
            }
    
    # 卖出条件检查
    elif signal == "bearish":
        sell_conditions = _check_sell_conditions(details)
        if sell_conditions["is_valid"]:
            return {
                "action": "bearish", 
                "confidence": confidence,
                "exit_conditions": sell_conditions,
                "reason": f"卖出信号确认: {sell_conditions['summary']}"
            }
    
    # 默认持有
    return {
        "action": "neutral",
        "confidence": 50,
        "reason": "技术指标信号不明确或不符合入场条件"
    }


def _check_buy_conditions(details: dict) -> dict:
    """
    检查买入条件
    买入条件：
    1. MACD: DIF在0轴下方金叉DEA且向上发散，或DIF在0轴上方回踩后再次向上
    2. RSI: 从30以下回升突破40或50，但未进入超买区(<70)
    3. BOLL: 价格触及或跌破下轨且有企稳迹象，中轨向上
    4. 成交量: 明显放大(1.5倍以上)
    """
    macd = details["macd"]
    rsi = details["rsi"]
    boll = details["bollinger"]
    volume = details["volume"]
    
    # MACD条件
    macd_valid = (
        (macd["is_golden_cross"] and not macd["dif_above_zero"] and macd["dif_trend"] == "up") or
        (macd["dif_above_zero"] and macd["dif_trend"] == "up" and macd["current_dif"] > macd["current_dea"])
    )
    
    # RSI条件  
    rsi_valid = (
        rsi["is_oversold_recovery"] and rsi["current_rsi"] < 70
    )
    
    # 布林带条件
    boll_valid = (
        (boll["is_touching_lower"] or boll["price_position"] < 0.3) and
        boll["middle_trend"] == "up" and
        boll.get("has_long_lower_shadow", False)
    )
    
    # 成交量条件
    volume_valid = volume["is_surge"]
    
    # 计算满足条件数量
    conditions_met = sum([macd_valid, rsi_valid, boll_valid, volume_valid])
    
    # 至少满足3个条件才考虑买入
    is_valid = conditions_met >= 3
    
    conditions_summary = []
    if macd_valid:
        conditions_summary.append("MACD金叉向上")
    if rsi_valid:
        conditions_summary.append("RSI超卖回升")
    if boll_valid:
        conditions_summary.append("布林下轨企稳")
    if volume_valid:
        conditions_summary.append("成交量放大")
    
    return {
        "is_valid": is_valid,
        "conditions_met": conditions_met,
        "total_conditions": 4,
        "summary": " + ".join(conditions_summary) if conditions_summary else "条件不足",
        "details": {
            "macd_valid": macd_valid,
            "rsi_valid": rsi_valid,
            "boll_valid": boll_valid,
            "volume_valid": volume_valid
        }
    }


def _check_sell_conditions(details: dict) -> dict:
    """
    检查卖出条件
    卖出条件：
    1. MACD: DIF在0轴上方死叉DEA，或DIF在高位拐头向下
    2. RSI: 从70以上回落跌破60或50
    3. BOLL: 价格触及或突破上轨且出现长上影线
    4. 成交量: 量价背离或高点放量滞涨
    """
    macd = details["macd"]
    rsi = details["rsi"]
    boll = details["bollinger"]
    volume = details["volume"]
    
    # MACD条件
    macd_valid = (
        (macd["is_death_cross"] and macd["dif_above_zero"]) or
        (macd["dif_trend"] == "down" and macd["current_dif"] > 0)
    )
    
    # RSI条件
    rsi_valid = rsi["is_overbought_decline"]
    
    # 布林带条件
    boll_valid = (
        (boll["is_touching_upper"] or boll["price_position"] > 0.8) and
        boll.get("has_long_upper_shadow", False)
    )
    
    # 成交量条件（这里简化处理，实际应该结合价格走势）
    volume_valid = volume["volume_ratio"] < 0.8  # 成交量萎缩
    
    # 计算满足条件数量
    conditions_met = sum([macd_valid, rsi_valid, boll_valid, volume_valid])
    
    # 至少满足2个条件才考虑卖出
    is_valid = conditions_met >= 2
    
    conditions_summary = []
    if macd_valid:
        conditions_summary.append("MACD死叉向下")
    if rsi_valid:
        conditions_summary.append("RSI超买回落")
    if boll_valid:
        conditions_summary.append("布林上轨见顶")
    if volume_valid:
        conditions_summary.append("成交量萎缩")
    
    return {
        "is_valid": is_valid,
        "conditions_met": conditions_met,
        "total_conditions": 4,
        "summary": " + ".join(conditions_summary) if conditions_summary else "条件不足",
        "details": {
            "macd_valid": macd_valid,
            "rsi_valid": rsi_valid,
            "boll_valid": boll_valid,
            "volume_valid": volume_valid
        }
    }


def _generate_detailed_analysis(prices_df, comprehensive_result, trade_decision):
    """
    生成详细的分析报告
    """
    current_price = prices_df['close'].iloc[-1]
    
    analysis = {
        "当前价格": f"{current_price:.2f}",
        "综合信号": comprehensive_result["signal"],
        "信号强度": f"{comprehensive_result['confidence']}%",
        "交易建议": trade_decision["action"],
        "建议原因": trade_decision["reason"],
        "技术指标分析": {
            "MACD分析": comprehensive_result["details"]["macd"]["reason"],
            "RSI分析": comprehensive_result["details"]["rsi"]["reason"],
            "布林带分析": comprehensive_result["details"]["bollinger"]["reason"],
            "成交量分析": comprehensive_result["details"]["volume"]["reason"]
        }
    }
    
    # 添加入场/出场条件
    if "entry_conditions" in trade_decision:
        analysis["入场条件"] = trade_decision["entry_conditions"]["summary"]
    if "exit_conditions" in trade_decision:
        analysis["出场条件"] = trade_decision["exit_conditions"]["summary"]
    
    return analysis