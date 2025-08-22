"""
个性化回测系统
适配2-3周交易周期，频率限制和个人交易策略
"""

import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import questionary
import matplotlib.pyplot as plt
import pandas as pd
from colorama import Fore, Style, init
import numpy as np
import itertools

from llm.models import LLM_ORDER, get_model_info
from personal_main import run_personal_hedge_fund
from tools.api import get_price_data, get_prices
from utils.display import print_backtest_results, format_backtest_row
from typing_extensions import Callable

init(autoreset=True)


class PersonalBacktester:
    def __init__(
        self,
        agent: Callable,
        tickers: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
        model_name: str = "gpt-4o",
        model_provider: str = "OpenAI",
        trading_frequency_days: int = 7,  # 每周检查一次交易机会
        max_trades_per_period: int = 10,  # 2周内最多10次交易
        hold_period_min: int = 14,  # 最少持有14天
        hold_period_max: int = 21,  # 最多持有21天
    ):
        """
        个性化回测器
        
        Args:
            agent: 交易代理函数
            tickers: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期  
            initial_capital: 初始资金
            model_name: LLM模型名称
            model_provider: LLM提供商
            trading_frequency_days: 交易检查频率(天)
            max_trades_per_period: 2周内最大交易次数
            hold_period_min: 最小持有期(天)
            hold_period_max: 最大持有期(天)
        """
        self.agent = agent
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.model_name = model_name
        self.model_provider = model_provider
        self.trading_frequency_days = trading_frequency_days
        self.max_trades_per_period = max_trades_per_period
        self.hold_period_min = hold_period_min
        self.hold_period_max = hold_period_max

        # 初始化投资组合
        self.portfolio_values = []
        self.portfolio = {
            "cash": initial_capital,
            "margin_used": 0.0,
            "margin_requirement": 0.0,
            "positions": {
                ticker: {
                    "long": 0,
                    "short": 0,
                    "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0,
                    "entry_date": None,  # 入场日期
                } for ticker in tickers
            },
            "realized_gains": {
                ticker: {
                    "long": 0.0,
                    "short": 0.0,
                } for ticker in tickers
            },
            "trading_history": []
        }

    def execute_personal_trade(self, ticker: str, action: str, quantity: float, current_price: float, current_date: str):
        """
        执行个性化交易（只做多，不做空）
        """
        if quantity <= 0:
            return 0

        quantity = int(quantity)
        position = self.portfolio["positions"][ticker]

        if action == "buy":
            cost = quantity * current_price
            if cost <= self.portfolio["cash"]:
                # 加权平均成本
                old_shares = position["long"]
                old_cost_basis = position["long_cost_basis"]
                total_shares = old_shares + quantity

                if total_shares > 0:
                    total_cost = old_cost_basis * old_shares + cost
                    position["long_cost_basis"] = total_cost / total_shares

                position["long"] += quantity
                position["entry_date"] = current_date  # 记录入场日期
                self.portfolio["cash"] -= cost
                
                # 记录交易历史
                self.portfolio["trading_history"].append({
                    "date": current_date,
                    "ticker": ticker,
                    "action": "buy",
                    "quantity": quantity,
                    "price": current_price
                })
                
                return quantity
            else:
                # 计算最大可买数量
                max_quantity = int(self.portfolio["cash"] / current_price)
                if max_quantity > 0:
                    return self.execute_personal_trade(ticker, action, max_quantity, current_price, current_date)
                return 0

        elif action == "sell":
            # 只能卖出持有的股票
            quantity = min(quantity, position["long"])
            if quantity > 0:
                # 计算已实现收益
                avg_cost_per_share = position["long_cost_basis"]
                realized_gain = (current_price - avg_cost_per_share) * quantity
                self.portfolio["realized_gains"][ticker]["long"] += realized_gain

                position["long"] -= quantity
                self.portfolio["cash"] += quantity * current_price

                if position["long"] == 0:
                    position["long_cost_basis"] = 0.0
                    position["entry_date"] = None

                # 记录交易历史
                self.portfolio["trading_history"].append({
                    "date": current_date,
                    "ticker": ticker,
                    "action": "sell",
                    "quantity": quantity,
                    "price": current_price
                })

                return quantity

        return 0

    def should_trade_today(self, current_date: str, last_trade_date: str = None) -> bool:
        """
        判断今天是否应该检查交易机会
        """
        if not last_trade_date:
            return True
            
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        last_dt = datetime.strptime(last_trade_date, "%Y-%m-%d")
        
        return (current_dt - last_dt).days >= self.trading_frequency_days

    def check_holding_period(self, ticker: str, current_date: str) -> dict:
        """
        检查持仓时间是否符合要求
        """
        position = self.portfolio["positions"][ticker]
        
        if position["long"] == 0 or not position["entry_date"]:
            return {"should_hold": False, "days_held": 0, "reason": "无持仓"}
        
        entry_dt = datetime.strptime(position["entry_date"], "%Y-%m-%d")
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        days_held = (current_dt - entry_dt).days
        
        if days_held < self.hold_period_min:
            return {
                "should_hold": True, 
                "days_held": days_held, 
                "reason": f"未满最小持有期{self.hold_period_min}天"
            }
        elif days_held >= self.hold_period_max:
            return {
                "should_hold": False, 
                "days_held": days_held, 
                "reason": f"达到最大持有期{self.hold_period_max}天"
            }
        else:
            return {
                "should_hold": False, 
                "days_held": days_held, 
                "reason": "可以根据信号决定"
            }

    def count_recent_trades(self, current_date: str) -> int:
        """
        计算最近2周的交易次数
        """
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        cutoff_date = current_dt - timedelta(days=14)
        
        recent_trades = 0
        for trade in self.portfolio["trading_history"]:
            trade_dt = datetime.strptime(trade["date"], "%Y-%m-%d")
            if trade_dt >= cutoff_date:
                recent_trades += 1
        
        return recent_trades

    def calculate_portfolio_value(self, current_prices):
        """
        计算投资组合总价值
        """
        total_value = self.portfolio["cash"]
        
        for ticker in self.tickers:
            position = self.portfolio["positions"][ticker]
            price = current_prices[ticker]
            
            # 多头仓位价值
            long_value = position["long"] * price
            total_value += long_value
        
        return total_value

    def run_backtest(self):
        """
        运行个性化回测
        """
        print(f"\n{Fore.CYAN}🎯 开始个性化回测{Style.RESET_ALL}")
        print(f"📅 回测期间: {self.start_date} 到 {self.end_date}")
        print(f"💰 初始资金: ${self.initial_capital:,.2f}")
        print(f"🔄 交易频率: 每{self.trading_frequency_days}天检查一次")
        print(f"📊 持仓周期: {self.hold_period_min}-{self.hold_period_max}天")
        print(f"🚫 频率限制: 2周内最多{self.max_trades_per_period}次交易\n")

        # 预取数据
        self._prefetch_data()

        # 生成交易日期（每周一次）
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        
        current_dt = start_dt
        trading_dates = []
        
        while current_dt <= end_dt:
            trading_dates.append(current_dt.strftime("%Y-%m-%d"))
            current_dt += timedelta(days=self.trading_frequency_days)

        # 初始化组合价值记录
        self.portfolio_values = [{"Date": start_dt, "Portfolio Value": self.initial_capital}]
        
        table_rows = []
        last_trade_date = None

        for current_date in trading_dates:
            current_dt = datetime.strptime(current_date, "%Y-%m-%d")
            
            # 检查是否应该交易
            if not self.should_trade_today(current_date, last_trade_date):
                continue

            # 获取当前价格
            try:
                current_prices = self._get_current_prices(current_date)
                if not current_prices:
                    continue
            except Exception as e:
                print(f"获取{current_date}价格失败: {e}")
                continue

            # 检查交易频率限制
            recent_trades = self.count_recent_trades(current_date)
            
            # 对每个股票检查持仓时间
            forced_actions = {}
            for ticker in self.tickers:
                hold_check = self.check_holding_period(ticker, current_date)
                if hold_check["should_hold"]:
                    forced_actions[ticker] = "hold"
                elif hold_check["reason"].startswith("达到最大持有期"):
                    forced_actions[ticker] = "sell"

            # 运行交易代理
            if recent_trades < self.max_trades_per_period:
                lookback_start = (current_dt - timedelta(days=30)).strftime("%Y-%m-%d")
                
                try:
                    output = self.agent(
                        tickers=self.tickers,
                        start_date=lookback_start,
                        end_date=current_date,
                        portfolio=self.portfolio,
                        model_name=self.model_name,
                        model_provider=self.model_provider,
                    )
                    decisions = output["decisions"]
                    analyst_signals = output["analyst_signals"]
                except Exception as e:
                    print(f"运行代理失败 {current_date}: {e}")
                    continue
            else:
                # 超过交易频率限制，只能强制卖出
                decisions = {ticker: {"action": "hold", "quantity": 0} for ticker in self.tickers}
                analyst_signals = {}

            # 执行交易
            executed_trades = {}
            for ticker in self.tickers:
                # 应用强制动作
                if ticker in forced_actions:
                    if forced_actions[ticker] == "sell":
                        position = self.portfolio["positions"][ticker]
                        executed_quantity = self.execute_personal_trade(
                            ticker, "sell", position["long"], current_prices[ticker], current_date
                        )
                        executed_trades[ticker] = executed_quantity
                        last_trade_date = current_date
                    else:
                        executed_trades[ticker] = 0
                else:
                    # 正常交易决策
                    decision = decisions.get(ticker, {"action": "hold", "quantity": 0})
                    action = decision.get("action", "hold")
                    quantity = decision.get("quantity", 0)

                    if action in ["buy", "sell"] and recent_trades < self.max_trades_per_period:
                        executed_quantity = self.execute_personal_trade(
                            ticker, action, quantity, current_prices[ticker], current_date
                        )
                        executed_trades[ticker] = executed_quantity
                        if executed_quantity > 0:
                            last_trade_date = current_date
                    else:
                        executed_trades[ticker] = 0

            # 计算组合价值
            total_value = self.calculate_portfolio_value(current_prices)
            portfolio_return = (total_value / self.initial_capital - 1) * 100

            # 记录组合价值
            self.portfolio_values.append({
                "Date": current_dt,
                "Portfolio Value": total_value
            })

            # 生成表格行
            date_rows = []
            for ticker in self.tickers:
                ticker_signals = {}
                for agent_name, signals in analyst_signals.items():
                    if ticker in signals:
                        ticker_signals[agent_name] = signals[ticker]

                bullish_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "bullish"])
                bearish_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "bearish"])
                neutral_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "neutral"])

                pos = self.portfolio["positions"][ticker]
                position_value = pos["long"] * current_prices[ticker]

                action = "hold"
                if ticker in forced_actions and forced_actions[ticker] == "sell":
                    action = "sell (强制)"
                elif ticker in decisions:
                    action = decisions[ticker].get("action", "hold")

                date_rows.append(
                    format_backtest_row(
                        date=current_date,
                        ticker=ticker,
                        action=action,
                        quantity=executed_trades.get(ticker, 0),
                        price=current_prices[ticker],
                        shares_owned=pos["long"],
                        position_value=position_value,
                        bullish_count=bullish_count,
                        bearish_count=bearish_count,
                        neutral_count=neutral_count,
                    )
                )

            # 添加汇总行
            date_rows.append(
                format_backtest_row(
                    date=current_date,
                    ticker="",
                    action="",
                    quantity=0,
                    price=0,
                    shares_owned=0,
                    position_value=0,
                    bullish_count=0,
                    bearish_count=0,
                    neutral_count=0,
                    is_summary=True,
                    total_value=total_value,
                    return_pct=portfolio_return,
                    cash_balance=self.portfolio["cash"],
                    total_position_value=total_value - self.portfolio["cash"],
                )
            )

            table_rows.extend(date_rows)
            print_backtest_results(table_rows)

        print(f"\n{Fore.GREEN}✅ 回测完成{Style.RESET_ALL}")
        return self.analyze_performance()

    def _prefetch_data(self):
        """预取回测所需的数据"""
        print("\n📊 预取回测数据...")
        
        # 扩展时间范围以获取足够的技术指标计算数据
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        extended_start = (start_dt - timedelta(days=90)).strftime("%Y-%m-%d")
        
        for ticker in self.tickers:
            try:
                get_prices(ticker, extended_start, self.end_date)
            except Exception as e:
                print(f"预取{ticker}数据失败: {e}")
        
        print("✅ 数据预取完成")

    def _get_current_prices(self, date: str) -> dict:
        """获取指定日期的股票价格"""
        current_prices = {}
        
        for ticker in self.tickers:
            try:
                price_data = get_price_data(ticker, date, date)
                if not price_data.empty:
                    current_prices[ticker] = price_data.iloc[-1]["close"]
                else:
                    # 尝试获取前一天的数据
                    prev_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                    price_data = get_price_data(ticker, prev_date, prev_date)
                    if not price_data.empty:
                        current_prices[ticker] = price_data.iloc[-1]["close"]
            except Exception:
                continue
                
        return current_prices if len(current_prices) == len(self.tickers) else None

    def analyze_performance(self):
        """分析回测表现"""
        if not self.portfolio_values:
            print("没有可分析的组合数据")
            return pd.DataFrame()

        performance_df = pd.DataFrame(self.portfolio_values).set_index("Date")
        if performance_df.empty:
            return performance_df

        final_value = performance_df["Portfolio Value"].iloc[-1]
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100

        print(f"\n{Fore.WHITE}{Style.BRIGHT}📈 个性化策略表现分析:{Style.RESET_ALL}")
        print(f"💰 总收益率: {Fore.GREEN if total_return >= 0 else Fore.RED}{total_return:.2f}%{Style.RESET_ALL}")
        
        # 交易统计
        total_trades = len(self.portfolio["trading_history"])
        buy_trades = len([t for t in self.portfolio["trading_history"] if t["action"] == "buy"])
        sell_trades = len([t for t in self.portfolio["trading_history"] if t["action"] == "sell"])
        
        print(f"🔄 总交易次数: {total_trades} (买入: {buy_trades}, 卖出: {sell_trades})")
        
        # 已实现收益
        total_realized = sum(
            self.portfolio["realized_gains"][ticker]["long"] 
            for ticker in self.tickers
        )
        print(f"💵 已实现收益: {Fore.GREEN if total_realized >= 0 else Fore.RED}${total_realized:,.2f}{Style.RESET_ALL}")

        # 绘制收益曲线
        plt.figure(figsize=(12, 6))
        plt.plot(performance_df.index, performance_df["Portfolio Value"], color="blue", linewidth=2)
        plt.title("个性化策略 - 组合价值变化", fontsize=14)
        plt.ylabel("组合价值 ($)")
        plt.xlabel("日期")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        return performance_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行个性化回测系统")
    parser.add_argument("--tickers", type=str, required=True, help="股票代码，逗号分隔")
    parser.add_argument("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--initial-capital", type=float, default=100000, help="初始资金")

    args = parser.parse_args()

    # 解析股票代码
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]

    # 设置日期
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=2)).strftime("%Y-%m-%d")

    # 选择模型
    model_choice = questionary.select(
        "选择LLM模型:",
        choices=[questionary.Choice(display, value=value) for display, value, _ in LLM_ORDER],
        style=questionary.Style([
            ("selected", "fg:green bold"),
            ("pointer", "fg:green bold"),
            ("highlighted", "fg:green"),
            ("answer", "fg:green bold"),
        ])
    ).ask()

    if not model_choice:
        print("\n中断退出...")
        sys.exit(0)

    model_info = get_model_info(model_choice)
    model_provider = model_info.provider.value if model_info else "Unknown"

    # 创建并运行回测器
    backtester = PersonalBacktester(
        agent=run_personal_hedge_fund,
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.initial_capital,
        model_name=model_choice,
        model_provider=model_provider,
    )

    performance_df = backtester.run_backtest()