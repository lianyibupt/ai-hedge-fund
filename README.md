# AI Hedge Fund

This is a proof of concept for an AI-powered hedge fund.  The goal of this project is to explore the use of AI to make trading decisions.  This project is for **educational** purposes only and is not intended for real trading or investment.

This system employs several agents working together:

1. Ben Graham Agent - The godfather of value investing, only buys hidden gems with a margin of safety
2. Bill Ackman Agent - An activist investors, takes bold positions and pushes for change
3. Cathie Wood Agent - The queen of growth investing, believes in the power of innovation and disruption
4. Charlie Munger Agent - Warren Buffett's partner, only buys wonderful businesses at fair prices
5. Peter Lynch Agent - Legendary growth investor who seeks "ten-baggers" and invests in what he knows
6. Phil Fisher Agent - Legendary growth investor who mastered scuttlebutt analysis
7. Stanley Druckenmiller Agent - Macro legend who hunts for asymmetric opportunities with growth potential
8. Warren Buffett Agent - The oracle of Omaha, seeks wonderful companies at a fair price
9. Valuation Agent - Calculates the intrinsic value of a stock and generates trading signals
10. Sentiment Agent - Analyzes market sentiment and generates trading signals
11. Fundamentals Agent - Analyzes fundamental data and generates trading signals
12. Technicals Agent - Analyzes technical indicators and generates trading signals
13. Risk Manager - Calculates risk metrics and sets position limits
14. Portfolio Manager - Makes final trading decisions and generates orders
    
<img width="1042" alt="Screenshot 2025-03-22 at 6 19 07 PM" src="https://github.com/user-attachments/assets/cbae3dcf-b571-490d-b0ad-3f0f035ac0d4" />


**Note**: the system simulates trading decisions, it does not actually trade.

[![Twitter Follow](https://img.shields.io/twitter/follow/virattt?style=social)](https://twitter.com/virattt)

## Disclaimer

This project is for **educational and research purposes only**.

- Not intended for real trading or investment
- No warranties or guarantees provided
- Past performance does not indicate future results
- Creator assumes no liability for financial losses
- Consult a financial advisor for investment decisions

By using this software, you agree to use it solely for learning purposes.

## Table of Contents
- [How to Install](#how-to-install)
- [How to Run](#how-to-run)
  - [⌨️ Command Line Interface](#️-command-line-interface)
  - [🖥️ Web Application](#️-web-application)
- [How to Contribute](#how-to-contribute)
- [Feature Requests](#feature-requests)
- [License](#license)

## Setup

### 国内用户快速安装 (Chinese Users Quick Setup)

**方式1: 使用自动安装脚本（推荐）**
```bash
# 克隆项目
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund

# 运行自动安装脚本（已配置国内镜像源）
./install_dependencies.sh
```

**方式2: 手动使用国内镜像安装**
```bash
# 升级 pip
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装核心依赖
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit pandas matplotlib plotly yfinance python-dotenv

# 安装完整依赖（可选）
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

**方式3: Poetry + 国内镜像**
```bash
# 配置 Poetry 使用国内镜像
poetry config repositories.tsinghua https://pypi.tuna.tsinghua.edu.cn/simple
poetry install
```

### International Users Setup

Clone the repository:
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

### 2. Set up API keys

Create a `.env` file for your API keys:
```bash
# Create .env file for your API keys (in the root directory)
cp .env.example .env
```

Open and edit the `.env` file to add your API keys:
```bash
# For running LLMs hosted by openai (gpt-4o, gpt-4o-mini, etc.)
OPENAI_API_KEY=your-openai-api-key

# For getting financial data to power the hedge fund
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
```

**Important**: You must set at least one LLM API key (e.g. `OPENAI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, or `DEEPSEEK_API_KEY`) for the hedge fund to work. 

**Financial Data**: Data for AAPL, GOOGL, MSFT, NVDA, and TSLA is free and does not require an API key. For any other ticker, you will need to set the `FINANCIAL_DATASETS_API_KEY` in the .env file.

## How to Run

### ⌨️ Command Line Interface

You can run the AI Hedge Fund directly via terminal. This approach offers more granular control and is useful for automation, scripting, and integration purposes.

<img width="992" alt="Screenshot 2025-01-06 at 5 50 17 PM" src="https://github.com/user-attachments/assets/e8ca04bf-9989-4a7d-a8b4-34e04666663b" />

#### Quick Start

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

#### Run the AI Hedge Fund
```bash
poetry run python src/main.py --ticker AAPL,MSFT,NVDA
```

You can also specify a `--ollama` flag to run the AI hedge fund using local LLMs.

```bash
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --ollama
```

You can optionally specify the start and end dates to make decisions over a specific time period.

```bash
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01
```

#### Run the Backtester
```bash
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA
```

**Example Output:**
<img width="941" alt="Screenshot 2025-01-06 at 5 47 52 PM" src="https://github.com/user-attachments/assets/00e794ea-8628-44e6-9a84-8f8a31ad3b47" />

Note: The `--ollama`, `--start-date`, and `--end-date` flags work for the backtester, as well!

### 🖥️ Web Application

The new way to run the AI Hedge Fund is through our web application that provides a user-friendly interface. This is recommended for users who prefer visual interfaces over command line tools.

Please see detailed instructions on how to install and run the web application [here](https://github.com/virattt/ai-hedge-fund/tree/main/app).

<img width="1721" alt="Screenshot 2025-06-28 at 6 41 03 PM" src="https://github.com/user-attachments/assets/b95ab696-c9f4-416c-9ad1-51feb1f5374b" />


## How to Contribute

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

**Important**: Please keep your pull requests small and focused.  This will make it easier to review and merge.

## Feature Requests

If you have a feature request, please open an [issue](https://github.com/virattt/ai-hedge-fund/issues) and make sure it is tagged with `enhancement`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
