"""Constants and utilities related to analysts configuration."""

from agents.ben_graham import ben_graham_agent
from agents.bill_ackman import bill_ackman_agent
from agents.cathie_wood import cathie_wood_agent
from agents.charlie_munger import charlie_munger_agent
from agents.fundamentals import fundamentals_agent
from agents.phil_fisher import phil_fisher_agent
from agents.peter_lynch import peter_lynch_agent
from agents.sentiment import sentiment_agent
from agents.stanley_druckenmiller import stanley_druckenmiller_agent
from agents.technicals import technical_analyst_agent
from agents.valuation import valuation_agent
from agents.warren_buffett import warren_buffett_agent
from agents.personal_trader import personal_trader_agent

# Define analyst configuration - single source of truth
ANALYST_CONFIG = {
    "technical_analyst": {
        "display_name": "Technical Analyst",
        "chinese_name": "技术分析师",
        "strategy_description": "基于价格和成交量技术指标分析，包括趋势跟踪、均值回归、动量策略和波动率分析",
        "agent_func": technical_analyst_agent,
        "order": 0,
    },
    "sentiment_analyst": {
        "display_name": "Sentiment Analyst",
        "chinese_name": "情绪分析师",
        "strategy_description": "分析市场情绪和内部交易数据，结合新闻情绪和内部交易模式判断市场方向",
        "agent_func": sentiment_agent,
        "order": 1,
    },
    "ben_graham": {
        "display_name": "Ben Graham",
        "chinese_name": "本杰明·格雷厄姆",
        "strategy_description": "价值投资之父，强调安全边际、净流动资产价值和格雷厄姆数估值方法",
        "agent_func": ben_graham_agent,
        "order": 2,
    },
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "chinese_name": "比尔·阿克曼",
        "strategy_description": "激进投资者，关注高质量企业、自由现金流和估值折扣，可能采取积极股东策略",
        "agent_func": bill_ackman_agent,
        "order": 3,
    },
    "cathie_wood": {
        "display_name": "Cathie Wood",
        "chinese_name": "凯茜·伍德",
        "strategy_description": "专注于颠覆性创新技术，重视长期增长潜力和总可寻址市场，接受高波动性",
        "agent_func": cathie_wood_agent,
        "order": 4,
    },
    "charlie_munger": {
        "display_name": "Charlie Munger",
        "chinese_name": "查理·芒格",
        "strategy_description": "多学科思维模型，强调企业质量、可预测性和管理能力，重视ROIC和护城河",
        "agent_func": charlie_munger_agent,
        "order": 5,
    },
    "peter_lynch": {
        "display_name": "Peter Lynch",
        "chinese_name": "彼得·林奇",
        "strategy_description": "成长股投资大师，关注合理价格成长(GARP)，重视PEG比率和可理解的企业",
        "agent_func": peter_lynch_agent,
        "order": 6,
    },
    "phil_fisher": {
        "display_name": "Phil Fisher",
        "chinese_name": "菲利普·费舍尔",
        "strategy_description": "成长股投资先驱，关注企业质量、研发投入和管理层能力，愿意为优质企业支付溢价",
        "agent_func": phil_fisher_agent,
        "order": 7,
    },
    "stanley_druckenmiller": {
        "display_name": "Stanley Druckenmiller",
        "chinese_name": "斯坦利·德鲁肯米勒",
        "strategy_description": "宏观对冲基金经理，寻求不对称风险回报机会，重视增长、动量和风险控制",
        "agent_func": stanley_druckenmiller_agent,
        "order": 8,
    },
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "chinese_name": "沃伦·巴菲特",
        "strategy_description": "价值投资大师，寻找具有持久竞争优势、内在价值和安全边际的优质企业",
        "agent_func": warren_buffett_agent,
        "order": 9,
    },
    "fundamentals_analyst": {
        "display_name": "Fundamentals Analyst",
        "chinese_name": "基本面分析师",
        "strategy_description": "综合分析盈利能力、增长性、财务健康和估值比率等基本面指标",
        "agent_func": fundamentals_agent,
        "order": 10,
    },
    "valuation_analyst": {
        "display_name": "Valuation Analyst",
        "chinese_name": "估值分析师",
        "strategy_description": "基于P/E、P/B等估值比率进行相对估值分析，识别低估或高估的投资机会",
        "agent_func": valuation_agent,
        "order": 11,
    },
    "personal_trader": {
        "display_name": "个人交易策略 (2-3周周期)",
        "chinese_name": "个性化交易策略",
        "strategy_description": "基于MACD、RSI、布林带和成交量的技术分析，适合2-3周的中短期交易周期",
        "agent_func": personal_trader_agent,
        "order": 12,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}
