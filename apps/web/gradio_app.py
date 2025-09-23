import gradio as gr
import sys
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

# 添加必要的目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
src_dir = os.path.join(project_root, 'src')
cli_dir = os.path.join(project_root, 'apps', 'cli')
sys.path.insert(0, src_dir)
sys.path.insert(0, cli_dir)

from main import run_hedge_fund
from utils.analysts import ANALYST_ORDER
from llm.models import LLM_ORDER, get_model_info

# 默认日期设置
today = datetime.now().strftime("%Y-%m-%d")
three_months_ago = (datetime.now() - relativedelta(months=3)).strftime("%Y-%m-%d")

# 获取分析师和模型选项
analyst_choices = [(display, value) for display, value in ANALYST_ORDER]
model_choices = [(display, value) for display, value, _ in LLM_ORDER]

def run_hedge_fund_interface(
    tickers,
    start_date,
    end_date,
    initial_cash,
    margin_requirement,
    show_reasoning,
    selected_analysts,
    model_choice
):
    # 处理股票代码输入
    tickers = [t.strip() for t in tickers.split(",") if t.strip()]
    
    # 初始化投资组合
    portfolio = {
        "cash": float(initial_cash),
        "margin_requirement": float(margin_requirement),
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            } for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,
                "short": 0.0,
            } for ticker in tickers
        }
    }
    
    # 获取模型提供商
    model_info = get_model_info(model_choice)
    model_provider = model_info.provider.value if model_info else "Unknown"
    
    # 运行对冲基金
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=show_reasoning,
        selected_analysts=selected_analysts,
        model_name=model_choice,
        model_provider=model_provider,
    )
    
    # 格式化输出结果
    output = {
        "交易决策": result["decisions"],
        "分析师信号": result["analyst_signals"]
    }
    return output

# 创建界面
with gr.Blocks(title="AI对冲基金交易系统") as demo:
    gr.Markdown("# 🏦 AI对冲基金交易系统")
    
    with gr.Row():
        with gr.Column():
            tickers = gr.Textbox(
                label="股票代码(逗号分隔)",
                placeholder="例如: AAPL,MSFT,GOOG",
                value="RXRX,CRWV,SBET,CRCL"
            )
            start_date = gr.Textbox(
                label="开始日期(YYYY-MM-DD)",
                value=three_months_ago
            )
            end_date = gr.Textbox(
                label="结束日期(YYYY-MM-DD)",
                value=today
            )
            initial_cash = gr.Number(
                label="初始资金($)",
                value=100000.0
            )
            margin_requirement = gr.Number(
                label="保证金要求(%)",
                value=0.0
            )
            show_reasoning = gr.Checkbox(
                label="显示分析推理过程"
            )
            
        with gr.Column():
            selected_analysts = gr.CheckboxGroup(
                label="选择分析师",
                choices=analyst_choices,
                value=[value for _, value in ANALYST_ORDER[:3]]  # 默认选择前3个
            )
            model_choice = gr.Radio(
                label="选择LLM模型",
                choices=model_choices,
                value=model_choices[0][1]  # 默认第一个模型
            )
    
    run_btn = gr.Button("运行对冲基金", variant="primary")
    output = gr.JSON(label="交易结果")
    
    run_btn.click(
        fn=run_hedge_fund_interface,
        inputs=[
            tickers,
            start_date,
            end_date,
            initial_cash,
            margin_requirement,
            show_reasoning,
            selected_analysts,
            model_choice
        ],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch()