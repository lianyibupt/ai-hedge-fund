from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
from tools.api import get_prices, prices_to_df
import json


##### Risk Management Agent #####
def risk_management_agent(state: AgentState):
    """Controls position sizing based on real-world risk factors for multiple tickers."""
    portfolio = state["data"]["portfolio"]
    data = state["data"]
    tickers = data["tickers"]

    # Initialize risk analysis for each ticker
    risk_analysis = {}
    current_prices = {}  # Store prices here to avoid redundant API calls

    for ticker in tickers:
        progress.update_status("risk_management_agent", ticker, "Analyzing price data")

        prices = get_prices(
            ticker=ticker,
            start_date=data["start_date"],
            end_date=data["end_date"],
        )

        if not prices:
            progress.update_status("risk_management_agent", ticker, "Failed: No price data found, using default price")
            # 使用默认价格而不是跳过，避免影响后续分析
            current_price = 1.0  # 默认价格
            current_prices[ticker] = current_price
            progress.update_status("risk_management_agent", ticker, f"Using default price: {current_price}")
        else:
            prices_df = prices_to_df(prices)
            current_price = prices_df["close"].iloc[0]  # 使用iloc[0]获取最新价格
            current_prices[ticker] = current_price  # Store the current price
            progress.update_status("risk_management_agent", ticker, f"Current price: {current_price}")

        progress.update_status("risk_management_agent", ticker, "Calculating position limits")

        # 确保current_price变量存在
        current_price = current_prices[ticker]

        # Calculate current position value for this ticker
        positions = portfolio.get("positions", {})
        current_position = positions.get(ticker, {})
        
        # Calculate long position value
        long_shares = current_position.get("long", 0)
        long_cost_basis = current_position.get("long_cost_basis", 0.0)
        long_value = long_shares * current_price if long_shares > 0 else 0
        
        # Calculate short position value (short positions are liabilities)
        short_shares = current_position.get("short", 0)
        short_cost_basis = current_position.get("short_cost_basis", 0.0)
        short_value = short_shares * current_price if short_shares > 0 else 0
        
        # Total position value (long positions are assets, short positions are liabilities)
        current_position_value = long_value - short_value

        # Calculate total portfolio value (cash + long positions - short positions)
        total_portfolio_value = portfolio.get("cash", 0)
        for t, pos in positions.items():
            t_price = current_prices.get(t, 0) if t == ticker else 0  # Use current price for this ticker, 0 for others (will be updated later)
            long_val = pos.get("long", 0) * t_price
            short_val = pos.get("short", 0) * t_price
            total_portfolio_value += long_val - short_val

        # Base limit is 20% of portfolio for any single position
        position_limit = total_portfolio_value * 0.20

        # For existing positions, subtract current position value from limit
        remaining_position_limit = position_limit - current_position_value

        # Ensure we don't exceed available cash
        max_position_size = min(remaining_position_limit, portfolio.get("cash", 0))

        risk_analysis[ticker] = {
            "remaining_position_limit": float(max_position_size),
            "current_price": float(current_price),
            "reasoning": {
                "portfolio_value": float(total_portfolio_value),
                "current_position": float(current_position_value),
                "position_limit": float(position_limit),
                "remaining_limit": float(remaining_position_limit),
                "available_cash": float(portfolio.get("cash", 0)),
            },
        }

        progress.update_status("risk_management_agent", ticker, "Done")

    message = HumanMessage(
        content=json.dumps(risk_analysis),
        name="risk_management_agent",
    )

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(risk_analysis, "Risk Management Agent")

    # Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["risk_management_agent"] = risk_analysis

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }
