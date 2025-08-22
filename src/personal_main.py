"""
个性化交易系统主入口
适配2-3周交易周期的个人交易策略
"""

import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Back, Style, init
import questionary
from agents.personal_trader import personal_trader_agent
from agents.personal_portfolio_manager import personal_portfolio_management_agent
from agents.risk_manager import risk_management_agent
from agents.fundamentals import fundamentals_agent
from agents.technicals import technical_analyst_agent
from agents.sentiment import sentiment_agent
from agents.valuation import valuation_agent
from graph.state import AgentState
from utils.display import print_trading_output
from utils.progress import progress
from llm.models import LLM_ORDER, get_model_info
import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

# 加载环境变量
load_dotenv()
init(autoreset=True)


def parse_personal_response(response):
    """解析JSON字符串并返回字典"""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON解码错误: {e}\n响应: {repr(response)}")
        return None
    except TypeError as e:
        print(f"无效响应类型 (期望字符串，得到 {type(response).__name__}): {e}")
        return None
    except Exception as e:
        print(f"解析响应时发生意外错误: {e}\n响应: {repr(response)}")
        return None


def run_personal_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    model_name: str = "gpt-4o",
    model_provider: str = "OpenAI",
):
    """运行个性化对冲基金系统"""
    
    # 开始进度跟踪
    progress.start()

    try:
        # 使用个性化工作流
        agent = personal_app

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="基于个人交易策略进行交易决策分析。",
                    )
                ],
                "data": {
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )

        return {
            "decisions": parse_personal_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
            "analysis_data": {
                ticker: {
                    "fundamentals": final_state["data"].get("fundamentals", {}).get(ticker),
                    "valuation": final_state["data"].get("valuation", {}).get(ticker),
                    "metrics": final_state["data"].get("metrics", {}).get(ticker),
                }
                for ticker in tickers
            }
        }
    finally:
        # 停止进度跟踪
        progress.stop()


def start_personal(state: AgentState):
    """初始化个性化工作流"""
    return state


def create_personal_workflow():
    """创建个性化交易工作流"""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start_personal)
    
    # 添加个性化交易代理（核心） - 简化版本
    workflow.add_node("personal_trader_agent", personal_trader_agent)
    
    # 添加基础分析代理（精简版）
    workflow.add_node("fundamentals_agent", fundamentals_agent)
    
    # 添加风险管理和投资组合管理
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("personal_portfolio_management_agent", personal_portfolio_management_agent)

    # 设置顺序连接关系 - 避免并发问题
    workflow.add_edge("start_node", "personal_trader_agent")
    workflow.add_edge("personal_trader_agent", "fundamentals_agent")
    workflow.add_edge("fundamentals_agent", "risk_management_agent")
    workflow.add_edge("risk_management_agent", "personal_portfolio_management_agent")
    workflow.add_edge("personal_portfolio_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow


# 创建个性化应用
personal_workflow = create_personal_workflow()
personal_app = personal_workflow.compile()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行个性化交易系统")
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=100000.0,
        help="初始现金仓位，默认100,000"
    )
    parser.add_argument(
        "--tickers", 
        type=str, 
        required=True, 
        help="股票代码，用逗号分隔"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="开始日期 (YYYY-MM-DD)，默认为结束日期前3个月",
    )
    parser.add_argument(
        "--end-date", 
        type=str, 
        help="结束日期 (YYYY-MM-DD)，默认为今天"
    )
    parser.add_argument(
        "--show-reasoning", 
        action="store_true", 
        help="显示每个代理的推理过程"
    )

    args = parser.parse_args()

    # 解析股票代码
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    
    print(f"\n{Fore.CYAN}🎯 个性化交易系统{Style.RESET_ALL}")
    print(f"📈 交易周期: 2-3周")
    print(f"🔄 频率限制: 2周内不超过10次交易")
    print(f"📊 策略: MACD + RSI + 布林带 + 成交量分析")
    print(f"💼 标的: {', '.join(tickers)}\n")

    # 选择LLM模型
    model_choice = questionary.select(
        "选择您的LLM模型:",
        choices=[questionary.Choice(display, value=value) for display, value, _ in LLM_ORDER],
        style=questionary.Style([
            ("selected", "fg:green bold"),
            ("pointer", "fg:green bold"),
            ("highlighted", "fg:green"),
            ("answer", "fg:green bold"),
        ])
    ).ask()

    if not model_choice:
        print("\n\n接收到中断信号，退出...")
        sys.exit(0)
    else:
        # 获取模型信息
        model_info = get_model_info(model_choice)
        if model_info:
            model_provider = model_info.provider.value
            print(f"\n选择的{Fore.CYAN}{model_provider}{Style.RESET_ALL}模型: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
        else:
            model_provider = "Unknown"
            print(f"\n选择的模型: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")

    # 验证日期格式
    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("开始日期必须是YYYY-MM-DD格式")

    if args.end_date:
        try:
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("结束日期必须是YYYY-MM-DD格式")

    # 设置开始和结束日期
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    if not args.start_date:
        # 计算结束日期前3个月
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")
    else:
        start_date = args.start_date

    # 初始化投资组合（适配个人交易策略）
    portfolio = {
        "cash": args.initial_cash,  # 初始现金
        "margin_requirement": 0.0,  # 不使用保证金
        "margin_used": 0.0,  # 不做空
        "positions": {
            ticker: {
                "long": 0,  # 持有的多头股数
                "short": 0,  # 不做空
                "long_cost_basis": 0.0,  # 平均成本价
                "short_cost_basis": 0.0,  # 不使用
                "short_margin_used": 0.0,  # 不使用
            } for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # 已实现收益
                "short": 0.0,  # 不使用
            } for ticker in tickers
        },
        "trading_history": []  # 交易历史记录
    }

    # 运行个性化对冲基金
    result = run_personal_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        model_name=model_choice,
        model_provider=model_provider,
    )
    
    print_trading_output(result)