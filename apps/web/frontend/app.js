// 交易分析系统前端逻辑
class TradingAnalysisApp {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.initializeEventListeners();
        this.setDefaultDates();
    }

    initializeEventListeners() {
        // 分析按钮
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeStocks();
        });

        // 清理缓存按钮
        document.getElementById('clearCacheBtn').addEventListener('click', () => {
            this.clearCache();
        });

        // 自动刷新处理
        document.getElementById('autoRefresh').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });
    }

    setDefaultDates() {
        const today = new Date();
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(today.getMonth() - 1);

        document.getElementById('startDate').value = oneMonthAgo.toISOString().split('T')[0];
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
    }

    async analyzeStocks() {
        const tickers = document.getElementById('tickersInput').value.trim();
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const enableFundamental = document.getElementById('enableFundamental').checked;
        const showDetailed = document.getElementById('showDetailed').checked;
        const showHistorical = document.getElementById('showHistorical').checked;

        if (!tickers) {
            this.showToast('请输入股票代码', 'error');
            return;
        }

        this.showLoading(true);

        try {
            const response = await axios.post(`${this.apiBase}/api/analyze`, {
                tickers: tickers.split(',').map(t => t.trim()),
                start_date: startDate,
                end_date: endDate,
                enable_fundamental: enableFundamental,
                show_detailed: showDetailed,
                show_historical: showHistorical
            });

            this.displayAnalysisResults(response.data.results);
        } catch (error) {
            console.error('分析错误:', error);
            this.showToast('分析失败，请检查网络连接', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayAnalysisResults(results) {
        const resultsContainer = document.getElementById('analysisResults');
        resultsContainer.innerHTML = '';

        results.forEach((result, index) => {
            const resultCard = this.createResultCard(result);
            resultsContainer.appendChild(resultCard);

            // 添加分隔线（除了最后一个）
            if (index < results.length - 1) {
                const divider = document.createElement('div');
                divider.className = 'divider';
                resultsContainer.appendChild(divider);
            }
        });
    }

    createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'card bg-base-100 shadow-xl';

        const signalClass = result.analysis.signal === '看涨' ? 'bullish' : 
                          result.analysis.signal === '看跌' ? 'bearish' : 'neutral';

        card.innerHTML = `
            <div class="card-body">
                <h2 class="card-title">📊 ${result.ticker_display} 分析结果</h2>
                
                <!-- 基本信息 -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">当前价格</div>
                        <div class="text-2xl font-bold">$${result.current_price.toFixed(2)}</div>
                    </div>
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">P/E比率</div>
                        <div class="text-2xl font-bold">${result.financial_metrics.pe_ratio ? result.financial_metrics.pe_ratio.toFixed(2) : 'N/A'}</div>
                    </div>
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">P/B比率</div>
                        <div class="text-2xl font-bold">${result.financial_metrics.pb_ratio ? result.financial_metrics.pb_ratio.toFixed(2) : 'N/A'}</div>
                    </div>
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">数据天数</div>
                        <div class="text-2xl font-bold">${result.data_days}</div>
                    </div>
                </div>

                <!-- 技术分析结果 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div>
                        <h3 class="text-lg font-semibold mb-3">🎯 技术分析结果</h3>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span>总体信号:</span>
                                <span class="${signalClass}">${result.analysis.signal}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>信心度:</span>
                                <span>${result.analysis.confidence}%</span>
                            </div>
                            <div>
                                <span class="font-medium">原因:</span>
                                <p class="text-sm opacity-80">${result.analysis.reason}</p>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h3 class="text-lg font-semibold mb-3">💡 交易建议</h3>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span>建议:</span>
                                <span class="${signalClass}">${this.generateRecommendation(result.analysis)}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>行动:</span>
                                <span>${this.generateAction(result.analysis)}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 各指标信号 -->
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3">📋 各指标信号</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        ${this.createIndicatorCards(result.analysis.details)}
                    </div>
                </div>

                <!-- 图表区域 -->
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3">📈 技术分析图表</h3>
                    <div id="chart-${result.ticker}" class="w-full h-96"></div>
                </div>

                <!-- 基本面分析（如果存在） -->
                ${result.fundamental_analysis ? this.createFundamentalAnalysisSection(result.fundamental_analysis) : ''}

                <!-- 操作按钮 -->
                <div class="card-actions justify-end">
                    <button class="btn btn-sm btn-outline" onclick="this.toggleDetailedView('${result.ticker}')">
                        📊 显示详细指标
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="this.toggleHistoricalView('${result.ticker}')">
                        📈 显示历史数据
                    </button>
                </div>
            </div>
        `;

        // 渲染图表
        this.renderChart(result);

        return card;
    }

    createIndicatorCards(details) {
        const indicators = [
            { name: 'MACD', data: details.macd },
            { name: 'RSI', data: details.rsi },
            { name: '布林带', data: details.bollinger },
            { name: '成交量', data: details.volume }
        ];

        return indicators.map(ind => {
            const signalClass = ind.data.signal === '看涨' ? 'bullish' : 
                             ind.data.signal === '看跌' ? 'bearish' : 'neutral';
            return `
                <div class="bg-base-200 p-3 rounded-lg">
                    <div class="font-medium">${ind.name}</div>
                    <div class="${signalClass}">${ind.data.signal}</div>
                    <div class="text-xs opacity-70 mt-1">${ind.data.reason}</div>
                </div>
            `;
        }).join('');
    }

    createFundamentalAnalysisSection(fundamental) {
        return `
            <div class="mb-6">
                <h3 class="text-lg font-semibold mb-3">📈 基本面分析结果</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">综合评分</div>
                        <div class="text-2xl font-bold">${fundamental.total_score}/50.0</div>
                    </div>
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">投资建议</div>
                        <div class="text-xl font-bold">${fundamental.investment_signal.value}</div>
                    </div>
                    <div class="metric-card p-4 rounded-lg">
                        <div class="text-sm opacity-70">信心度</div>
                        <div class="text-2xl font-bold">${fundamental.confidence}%</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderChart(result) {
        // 这里需要实现图表渲染逻辑
        // 使用Plotly.js渲染技术分析图表
        const layout = {
            title: `${result.ticker} 技术分析图表`,
            height: 400,
            showlegend: true,
            xaxis: { rangeslider: { visible: false } }
        };

        Plotly.newPlot(`chart-${result.ticker}`, [], layout);
    }

    generateRecommendation(analysis) {
        if (analysis.signal === '看涨' && analysis.confidence >= 60) {
            return '🟢 买入建议';
        } else if (analysis.signal === '看跌' && analysis.confidence >= 60) {
            return '🔴 卖出建议';
        } else {
            return '🟡 持有建议';
        }
    }

    generateAction(analysis) {
        if (analysis.signal === '看涨' && analysis.confidence >= 60) {
            return '考虑买入';
        } else if (analysis.signal === '看跌' && analysis.confidence >= 60) {
            return '考虑卖出';
        } else {
            return '继续观察';
        }
    }

    async clearCache() {
        try {
            await axios.post(`${this.apiBase}/api/cache/clear`);
            this.showToast('缓存清理成功', 'success');
        } catch (error) {
            console.error('清理缓存错误:', error);
            this.showToast('缓存清理失败', 'error');
        }
    }

    showLoading(show) {
        document.getElementById('loading').classList.toggle('hidden', !show);
    }

    showToast(message, type = 'info') {
        // 实现Toast通知
        const toast = document.createElement('div');
        toast.className = `toast toast-top toast-end`;
        toast.innerHTML = `
            <div class="alert alert-${type}">
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    startAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            this.analyzeStocks();
        }, 30000); // 30秒刷新一次
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }
}

// 初始化应用
const app = new TradingAnalysisApp();

// 工具函数
function toggleDetailedView(ticker) {
    const detailedSection = document.getElementById(`detailed-${ticker}`);
    detailedSection.classList.toggle('hidden');
}

function toggleHistoricalView(ticker) {
    const historicalSection = document.getElementById(`historical-${ticker}`);
    historicalSection.classList.toggle('hidden');
}