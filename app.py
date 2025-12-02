import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# -----------------------------------------------------------
# 1. 페이지 설정 및 프리미엄 CSS 스타일링
# -----------------------------------------------------------
st.set_page_config(
    page_title="TQQQ Sniper v4.6",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 프리미엄 다크 테마 CSS
st.markdown("""
<style>
    /* 폰트 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    /* 전역 스타일 */
    .stApp {
        background: linear-gradient(135deg, #0a0b0f 0%, #0d0e14 50%, #0a0b0f 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* 헤더 스타일 */
    .premium-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 8px;
    }
    
    .header-icon {
        background: linear-gradient(135deg, #06b6d4, #10b981);
        padding: 14px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 30px rgba(6, 182, 212, 0.3);
    }
    
    .header-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(90deg, #06b6d4, #10b981, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    .header-version {
        color: #64748b;
        font-size: 14px;
        font-weight: 400;
    }
    
    .header-subtitle {
        color: #64748b;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 2px;
    }
    
    /* 날짜 배지 */
    .date-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(71, 85, 105, 0.3);
        padding: 8px 14px;
        border-radius: 10px;
        margin: 16px 0 24px 0;
    }
    
    .date-badge-icon {
        color: #06b6d4;
    }
    
    .date-badge-label {
        color: #94a3b8;
        font-size: 12px;
    }
    
    .date-badge-value {
        color: #06b6d4;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* 레짐 배지 */
    .regime-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        white-space: nowrap;
        flex-shrink: 0;
    }
    
    .regime-bullish {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #10b981;
    }
    
    .regime-bearish {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #ef4444;
    }
    
    .regime-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .regime-dot-bullish {
        background: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }
    
    .regime-dot-bearish {
        background: #ef4444;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* 액션 카드 */
    .action-card {
        position: relative;
        border-radius: 16px;
        padding: 2px;
        margin-bottom: 24px;
        overflow: hidden;
    }
    
    .action-card-buy {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(6, 182, 212, 0.3));
    }
    
    .action-card-sell {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(236, 72, 153, 0.3));
    }
    
    .action-card-hold {
        background: rgba(51, 65, 85, 0.3);
    }
    
    .action-card-inner {
        background: #0d0e14;
        border-radius: 14px;
        padding: 20px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .action-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    
    .action-icon-buy {
        background: rgba(16, 185, 129, 0.2);
    }
    
    .action-icon-sell {
        background: rgba(239, 68, 68, 0.2);
    }
    
    .action-icon-hold {
        background: rgba(100, 116, 139, 0.2);
    }
    
    .action-content {
        flex: 1;
    }
    
    .action-label {
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 4px;
    }
    
    .action-text {
        font-size: 18px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        white-space: nowrap;
    }
    
    .action-text-buy {
        color: #10b981;
    }
    
    .action-text-sell {
        color: #ef4444;
    }
    
    .action-text-hold {
        color: #94a3b8;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* 포트폴리오 카드 */
    .portfolio-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.5));
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 16px;
        padding: 20px;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .portfolio-card:hover {
        border-color: rgba(6, 182, 212, 0.3);
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.1);
    }
    
    .portfolio-card-gld:hover {
        border-color: rgba(245, 158, 11, 0.3);
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.1);
    }
    
    .portfolio-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .portfolio-label {
        color: #64748b;
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .portfolio-change {
        font-size: 12px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .portfolio-change-up {
        color: #10b981;
    }
    
    .portfolio-change-down {
        color: #ef4444;
    }
    
    .portfolio-change-neutral {
        color: #64748b;
    }
    
    .portfolio-value {
        font-size: 32px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 12px;
    }
    
    .portfolio-value-tqqq {
        color: #06b6d4;
    }
    
    .portfolio-value-gld {
        color: #f59e0b;
    }
    
    .portfolio-value-cash {
        color: #94a3b8;
    }
    
    /* 커스텀 프로그레스 바 */
    .progress-container {
        height: 8px;
        background: rgba(51, 65, 85, 0.5);
        border-radius: 4px;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    .progress-tqqq {
        background: linear-gradient(90deg, #06b6d4, #10b981);
    }
    
    .progress-gld {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
    }
    
    .progress-cash {
        background: linear-gradient(90deg, #64748b, #94a3b8);
    }
    
    /* 전략 탭 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.3);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 12px;
        color: #94a3b8;
        padding: 12px 24px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(6, 182, 212, 0.1);
        border-color: rgba(6, 182, 212, 0.3);
        color: #06b6d4;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 16px;
    }
    
    /* 전략 카드 */
    .strategy-card {
        background: rgba(30, 41, 59, 0.3);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }
    
    .strategy-card:hover {
        border-color: rgba(100, 116, 139, 0.5);
    }
    
    .strategy-card-active-buy {
        background: rgba(16, 185, 129, 0.05);
        border-color: rgba(16, 185, 129, 0.3);
    }
    
    .strategy-card-active-sell {
        background: rgba(239, 68, 68, 0.05);
        border-color: rgba(239, 68, 68, 0.3);
    }
    
    .strategy-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    
    .strategy-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .strategy-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .strategy-icon-active-buy {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .strategy-icon-active-sell {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .strategy-icon-inactive {
        background: rgba(71, 85, 105, 0.3);
        color: #94a3b8;
    }
    
    .strategy-name {
        font-weight: 600;
        color: #e2e8f0;
        font-size: 14px;
    }
    
    .strategy-status {
        color: #64748b;
        font-size: 12px;
        margin-top: 2px;
    }
    
    .strategy-status-active {
        color: #10b981;
    }
    
    .strategy-status-sell {
        color: #ef4444;
    }
    
    .strategy-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .strategy-badge-active {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .strategy-badge-sell {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .strategy-badge-aborted {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .strategy-remaining {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .strategy-progress {
        height: 6px;
        background: rgba(51, 65, 85, 0.5);
        border-radius: 3px;
        overflow: hidden;
        margin-top: 8px;
    }
    
    .strategy-progress-bar {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    
    .strategy-progress-buy {
        background: linear-gradient(90deg, #10b981, #06b6d4);
    }
    
    .strategy-progress-sell {
        background: linear-gradient(90deg, #ef4444, #ec4899);
    }
    
    .strategy-progress-inactive {
        background: linear-gradient(90deg, #475569, #64748b);
    }
    
    .strategy-gap {
        color: #64748b;
        font-size: 12px;
        margin-top: 8px;
    }
    
    .strategy-gap-value {
        color: #f59e0b;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* 조정 비중 배지 */
    .adjustment-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        border-radius: 10px;
        font-size: 12px;
        margin-bottom: 16px;
    }
    
    .adjustment-badge-buy {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .adjustment-badge-sell {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .adjustment-value {
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Stochastic 카드 */
    .stoch-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.3), rgba(15, 23, 42, 0.3));
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 16px;
        padding: 12px 16px;
        margin-top: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: nowrap;
        gap: 8px;
    }
    
    .stoch-info {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
        flex: 1;
    }
    
    .stoch-icon {
        width: 36px;
        height: 36px;
        min-width: 36px;
        background: rgba(139, 92, 246, 0.2);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    
    .stoch-label {
        color: #64748b;
        font-size: 10px;
        margin-bottom: 2px;
        white-space: nowrap;
    }
    
    .stoch-values {
        font-size: 13px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        white-space: nowrap;
    }
    
    .stoch-k {
        color: #06b6d4;
    }
    
    .stoch-d {
        color: #f59e0b;
    }
    
    .stoch-sep {
        color: #64748b;
        margin: 0 4px;
    }
    
    /* 구분선 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(71, 85, 105, 0.5), transparent);
        margin: 24px 0;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        color: #475569;
        font-size: 11px;
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid rgba(71, 85, 105, 0.2);
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(71, 85, 105, 0.5);
        color: #94a3b8;
        border-radius: 10px;
        padding: 8px 16px;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: rgba(6, 182, 212, 0.1);
        border-color: rgba(6, 182, 212, 0.3);
        color: #06b6d4;
    }
    
    /* Plotly 차트 배경 */
    .js-plotly-plot {
        border-radius: 16px;
        overflow: hidden;
    }
    
    /* 스크롤바 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0b0f;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
    
    /* 숨기기 */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    .stDeployButton {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# 2. 분석기 클래스 정의
# -----------------------------------------------------------
class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기 - v4.6 (기본 전략 하락장 비중 계산 오류 수정)"""

    def __init__(self):
        self.stoch_config = {'period': 166, 'k_period': 57, 'd_period': 19}
        self.ma_periods = [20, 45, 151, 212]
        
        self.error_rate_strategies = {
            'TQQQ_Strategy_1': {'ma_period': 20, 'deviation_threshold': -12, 'holding_days': 8},
            'TQQQ_Strategy_2': {'ma_period': 45, 'deviation_threshold': -11, 'holding_days': 5},
            'TQQQ_Strategy_3': {'ma_period': 151, 'deviation_threshold': -21, 'holding_days': 8},
            'TQQQ_Strategy_4': {'ma_period': 212, 'deviation_threshold': -15, 'holding_days': 4},
        }
        
        self.optimized_strategies = {
            'TQQQ_Optimized_1': {'ma_period': 45, 'error_rate': 33, 'sell_days': 11},
            'TQQQ_Optimized_2': {'ma_period': 151, 'error_rate': 55, 'sell_days': 13, 'depends_on': 20},
            'TQQQ_Optimized_3': {'ma_period': 212, 'error_rate': 55, 'sell_days': 12, 'depends_on': 45},
        }

    @st.cache_data(ttl=300)
    def get_latest_data(_self, days_back=400):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        try:
            tickers = ['TQQQ', 'GLD']
            data = {}
            for ticker in tickers:
                stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if isinstance(stock_data.columns, pd.MultiIndex):
                    stock_data.columns = stock_data.columns.droplevel(1)
                data[ticker] = stock_data
            
            combined_data = pd.DataFrame()
            for ticker in tickers:
                for col in ['Open', 'High', 'Low', 'Close']:
                    if col in data[ticker].columns:
                        combined_data[f'{ticker}_{col}'] = data[ticker][col]
            
            return combined_data.dropna()
        except Exception as e:
            st.error(f"데이터 오류: {e}")
            return None

    def calculate_technical_indicators(self, data):
        df = data.copy()
        period, k_p, d_p = self.stoch_config.values()
        
        df['Highest_High'] = df['TQQQ_High'].rolling(window=period).max()
        df['Lowest_Low'] = df['TQQQ_Low'].rolling(window=period).min()
        df['%K'] = ((df['TQQQ_Close'] - df['Lowest_Low']) / (df['Highest_High'] - df['Lowest_Low']) * 100).rolling(window=k_p).mean()
        df['%D'] = df['%K'].rolling(window=d_p).mean()
        
        for ma in self.ma_periods:
            df[f'MA_{ma}'] = df['TQQQ_Close'].rolling(window=ma).mean()
            df[f'Deviation_{ma}'] = ((df['TQQQ_Close'] - df[f'MA_{ma}']) / df[f'MA_{ma}']) * 100
        return df.dropna()

    def calculate_base_allocation_series(self, data):
        is_bullish = data['%K'] > data['%D']
        
        ma_signals = pd.DataFrame(index=data.index)
        for ma in self.ma_periods:
            ma_signals[ma] = (data['TQQQ_Close'] > data[f'MA_{ma}']).astype(int)
            
        bull_alloc = ma_signals.sum(axis=1) * 0.25
        bear_alloc = (ma_signals[20] + ma_signals[45]) * 0.5
        
        base_alloc = pd.Series(np.where(is_bullish, bull_alloc, bear_alloc), index=data.index)
        base_change_mask = base_alloc.diff().fillna(0) != 0
        return base_change_mask

    def check_signal_with_simulation(self, data, strategy_type, params, base_change_mask):
        target_days = params['holding_days'] if strategy_type == 'error_buy' else params['sell_days']
        ma_period = params['ma_period']
        threshold = params['deviation_threshold'] if strategy_type == 'error_buy' else params['error_rate']

        remaining_days = 0 
        last_trigger_info = {}
        aborted_today = False
        
        for idx, row in data.iterrows():
            if remaining_days > 0:
                if base_change_mask[idx]:
                    remaining_days = 0 
                    if idx == data.index[-1]:
                        aborted_today = True
                    continue 

            if remaining_days > 0:
                remaining_days -= 1
            
            price_above_ma = row['TQQQ_Close'] > row[f'MA_{ma_period}']
            deviation = row[f'Deviation_{ma_period}']
            
            condition = False
            if strategy_type == 'error_buy':
                condition = (not price_above_ma) and (deviation <= threshold)
            else: 
                is_disabled = False
                if 'depends_on' in params and not (row['TQQQ_Close'] > row[f"MA_{params['depends_on']}"]):
                    is_disabled = True
                condition = (not is_disabled) and price_above_ma and (deviation >= threshold)
            
            if condition:
                remaining_days = target_days
                last_trigger_info = {
                    'trigger_deviation': deviation,
                    'trigger_date': idx
                }
                aborted_today = False

        is_active = remaining_days > 0
        
        final_details = {}
        if last_trigger_info:
            today = data.index[-1]
            days_ago_calendar = (today - last_trigger_info['trigger_date']).days
            
            final_details = {
                'trigger_deviation': last_trigger_info['trigger_deviation'],
                'days_ago': days_ago_calendar,
                'trigger_date': last_trigger_info['trigger_date'],
                'remaining_trading_days': remaining_days,
                'aborted_today': aborted_today
            }

        return is_active, remaining_days, final_details

    def analyze_portfolio(self, data, target_idx=None):
        if target_idx is not None:
            analysis_data = data.iloc[:target_idx+1]
        else:
            analysis_data = data
            
        target_data = analysis_data.iloc[-1]
        
        base_change_mask = self.calculate_base_allocation_series(analysis_data)
        
        is_bullish = target_data['%K'] > target_data['%D']
        ma_signals = {p: target_data['TQQQ_Close'] > target_data[f'MA_{p}'] for p in self.ma_periods}
        
        if is_bullish: 
            base_tqqq = sum(ma_signals.values()) * 0.25
        else: 
            base_tqqq = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5
        
        base_gld = 1 - base_tqqq
        base_cash = 0
        
        active_error_strats, error_logs = [], {}
        for name, params in self.error_rate_strategies.items():
            active, remaining, details = self.check_signal_with_simulation(analysis_data, 'error_buy', params, base_change_mask)
            if active:
                active_error_strats.append(name)
            if details:
                error_logs[name] = details
        error_adj = len(active_error_strats) * 0.25
        
        active_sell_cash = []
        sell_logs = {}
        for name, params in self.optimized_strategies.items():
            active, remaining, details = self.check_signal_with_simulation(analysis_data, 'optimized_sell', params, base_change_mask)
            if active:
                active_sell_cash.append(name)
            if details:
                sell_logs[name] = details

        opt_cash_adj = len(active_sell_cash) * 0.25
        
        final_tqqq, final_gld, final_cash = base_tqqq, base_gld, base_cash
        
        if error_adj > 0:
            amt = min(final_gld, error_adj)
            final_gld -= amt
            final_tqqq += amt
            
        if opt_cash_adj > 0:
            amt = min(final_tqqq, opt_cash_adj)
            final_tqqq -= amt
            final_cash += amt
            
        total = final_tqqq + final_gld + final_cash
        if total > 0:
            final_tqqq /= total; final_gld /= total; final_cash /= total
            
        return {
            'final_tqqq': final_tqqq, 'final_gld': final_gld, 'final_cash': final_cash,
            'base_tqqq': base_tqqq, 
            'error_adj': error_adj, 
            'opt_cash_adj': -opt_cash_adj, 
            'active_error_strats': active_error_strats, 
            'active_sell_cash': active_sell_cash,
            'error_logs': error_logs, 'sell_logs': sell_logs,
            'is_bullish': is_bullish
        }

    def analyze_all(self, data):
        today = self.analyze_portfolio(data)
        data_prev = data.iloc[:-1]
        yesterday = self.analyze_portfolio(data_prev)
        
        changes = {'tqqq': today['final_tqqq'] - yesterday['final_tqqq'], 'gld': today['final_gld'] - yesterday['final_gld']}
        actions = []
        for asset, chg in changes.items():
            if chg > 0.01: actions.append({'action': '매수', 'asset': asset.upper(), 'amt': chg})
            elif chg < -0.01: actions.append({'action': '매도', 'asset': asset.upper(), 'amt': abs(chg)})
        return today, yesterday, changes, actions


# -----------------------------------------------------------
# 3. 헬퍼 함수
# -----------------------------------------------------------
def render_action_card(actions):
    if actions:
        for a in actions:
            if a['action'] == '매수':
                st.markdown(f"""
                <div class="action-card action-card-buy">
                    <div class="action-card-inner">
                        <div class="action-icon action-icon-buy">⚡</div>
                        <div class="action-content">
                            <div class="action-label">Action Required</div>
                            <div class="action-text action-text-buy">{a['asset']} {a['amt']:.1%} 매수</div>
                        </div>
                        <div style="color: #10b981; font-size: 24px;">→</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="action-card action-card-sell">
                    <div class="action-card-inner">
                        <div class="action-icon action-icon-sell">⚠️</div>
                        <div class="action-content">
                            <div class="action-label">Action Required</div>
                            <div class="action-text action-text-sell">{a['asset']} {a['amt']:.1%} 매도</div>
                        </div>
                        <div style="color: #ef4444; font-size: 24px;">→</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="action-card action-card-hold">
            <div class="action-card-inner">
                <div class="action-icon action-icon-hold">🛡️</div>
                <div class="action-content">
                    <div class="action-label">No Action Required</div>
                    <div class="action-text action-text-hold">홀딩 유지 ☕</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_portfolio_card(asset, value, change, prev_value):
    colors = {
        'TQQQ': {'value': 'portfolio-value-tqqq', 'progress': 'progress-tqqq', 'hover': ''},
        'GLD': {'value': 'portfolio-value-gld', 'progress': 'progress-gld', 'hover': 'portfolio-card-gld'},
        'CASH': {'value': 'portfolio-value-cash', 'progress': 'progress-cash', 'hover': ''}
    }
    
    change_class = 'portfolio-change-neutral'
    change_prefix = ''
    if change > 0.001:
        change_class = 'portfolio-change-up'
        change_prefix = '+'
    elif change < -0.001:
        change_class = 'portfolio-change-down'
    
    change_text = f"{change_prefix}{change:.0%}" if abs(change) > 0.001 else "—"
    
    st.markdown(f"""
    <div class="portfolio-card {colors[asset]['hover']}">
        <div class="portfolio-header">
            <span class="portfolio-label">{asset}</span>
            <span class="portfolio-change {change_class}">{change_text}</span>
        </div>
        <div class="portfolio-value {colors[asset]['value']}">{value:.0%}</div>
        <div class="progress-container">
            <div class="progress-bar {colors[asset]['progress']}" style="width: {value*100}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_buy_strategy_card(name, params, latest, is_active, log_info, aborted):
    ma = params['ma_period']
    threshold = params['deviation_threshold']
    current_dev = latest[f'Deviation_{ma}']
    
    if current_dev > 0:
        progress = 0
    elif current_dev <= threshold:
        progress = 100
    else:
        progress = min(100, abs(current_dev) / abs(threshold) * 100)
    
    # 카드 스타일 결정
    if is_active:
        card_border = "border-left: 3px solid #10b981;"
        card_bg = "background: rgba(16, 185, 129, 0.05);"
    else:
        card_border = "border-left: 3px solid #475569;"
        card_bg = "background: rgba(30, 41, 59, 0.3);"
    
    # 상태 텍스트
    if is_active and log_info:
        trigger_date_str = log_info['trigger_date'].strftime('%m-%d')
        status_text = f"✅ 진입일: {trigger_date_str}"
        status_color = "#10b981"
    elif aborted:
        status_text = "🛑 강제종료"
        status_color = "#ef4444"
    else:
        status_text = "💤 대기중"
        status_color = "#64748b"
    
    # 배지 & 잔여일
    badge_text = ""
    remaining_text = ""
    if is_active and log_info:
        remaining = log_info['remaining_trading_days']
        est_days = int(remaining * 1.45)
        target_date = datetime.now() + timedelta(days=est_days)
        badge_text = "✓ 진입 완료"
        remaining_text = f"⏳ {remaining}일 남음 (~{target_date.strftime('%m-%d')})"
    elif aborted:
        badge_text = "🛑 강제 종료"
    
    # 갭 계산
    gap_text = ""
    if not is_active and not aborted:
        if current_dev > 0:
            gap = current_dev - threshold
            gap_text = f"📉 -{gap:.1f}%p 남음"
        else:
            gap_text = "⚠️ 조건 대기"
    
    # 프로그레스 바 색상
    if is_active:
        prog_color = "linear-gradient(90deg, #10b981, #06b6d4)"
    elif progress >= 70:
        prog_color = "linear-gradient(90deg, #f59e0b, #fbbf24)"
    else:
        prog_color = "linear-gradient(90deg, #475569, #64748b)"
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            st.markdown(f"""
            <div style="width: 45px; height: 45px; background: {'rgba(16, 185, 129, 0.2)' if is_active else 'rgba(71, 85, 105, 0.3)'}; 
                        border-radius: 10px; display: flex; align-items: center; justify-content: center; 
                        font-size: 14px; font-weight: 700; color: {'#10b981' if is_active else '#94a3b8'}; 
                        font-family: 'JetBrains Mono', monospace;">{ma}</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="font-weight: 600; color: #e2e8f0; font-size: 14px; margin-bottom: 2px;">MA{ma} 이탈률</div>
            <div style="color: {status_color}; font-size: 12px;">{status_text}</div>
            """, unsafe_allow_html=True)
        
        with col3:
            if badge_text:
                badge_bg = "rgba(16, 185, 129, 0.2)" if is_active else "rgba(239, 68, 68, 0.2)"
                badge_color = "#10b981" if is_active else "#ef4444"
                st.markdown(f"""
                <div style="text-align: right;">
                    <span style="display: inline-block; padding: 4px 10px; background: {badge_bg}; 
                                 border-radius: 6px; font-size: 11px; font-weight: 600; color: {badge_color}; 
                                 font-family: 'JetBrains Mono', monospace;">{badge_text}</span>
                </div>
                """, unsafe_allow_html=True)
                if remaining_text:
                    st.markdown(f"""
                    <div style="text-align: right; color: #94a3b8; font-size: 11px; margin-top: 4px; 
                                font-family: 'JetBrains Mono', monospace;">{remaining_text}</div>
                    """, unsafe_allow_html=True)
        
        # 프로그레스 바
        st.markdown(f"""
        <div style="height: 6px; background: rgba(51, 65, 85, 0.5); border-radius: 3px; overflow: hidden; margin: 8px 0;">
            <div style="height: 100%; width: {progress}%; background: {prog_color}; border-radius: 3px; transition: width 0.5s ease;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # 갭 표시
        if gap_text:
            st.markdown(f"""
            <div style="color: #64748b; font-size: 12px;">
                {gap_text.split(' ')[0]} <span style="color: #f59e0b; font-weight: 600; font-family: 'JetBrains Mono', monospace;">{' '.join(gap_text.split(' ')[1:])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


def render_sell_strategy_card(name, params, latest, is_active, log_info, aborted):
    ma = params['ma_period']
    threshold = params['error_rate']
    current_dev = latest[f'Deviation_{ma}']
    
    dep_check = True
    dep_msg = ""
    if 'depends_on' in params:
        dep_ma = params['depends_on']
        if not (latest['TQQQ_Close'] > latest[f'MA_{dep_ma}']):
            dep_check = False
            dep_msg = f"🚫 MA{dep_ma} 조건 미달"
    
    if current_dev < 0:
        progress = 0
    elif current_dev >= threshold:
        progress = 100
    else:
        progress = min(100, current_dev / threshold * 100)
    
    # 상태 텍스트
    if is_active and log_info:
        trigger_date_str = log_info['trigger_date'].strftime('%m-%d')
        status_text = f"🚨 매도일: {trigger_date_str}"
        status_color = "#ef4444"
    elif aborted:
        status_text = "🛑 강제종료"
        status_color = "#ef4444"
    elif not dep_check:
        status_text = dep_msg
        status_color = "#64748b"
    else:
        status_text = "💤 대기중"
        status_color = "#64748b"
    
    # 배지 & 잔여일
    badge_text = ""
    remaining_text = ""
    if is_active and log_info:
        remaining = log_info['remaining_trading_days']
        est_days = int(remaining * 1.45)
        target_date = datetime.now() + timedelta(days=est_days)
        badge_text = "🚨 매도 (현금)"
        remaining_text = f"⏳ {remaining}일 남음 (~{target_date.strftime('%m-%d')})"
    elif aborted:
        badge_text = "🛑 강제 종료"
    
    # 갭 계산
    gap_text = ""
    if not is_active and not aborted and dep_check:
        if current_dev >= 0:
            gap = threshold - current_dev
            gap_text = f"📈 +{gap:.1f}%p 남음"
        else:
            gap_text = "⚠️ 조건 대기"
    
    # 프로그레스 바 색상
    if is_active:
        prog_color = "linear-gradient(90deg, #ef4444, #ec4899)"
    elif progress >= 70:
        prog_color = "linear-gradient(90deg, #f59e0b, #fbbf24)"
    else:
        prog_color = "linear-gradient(90deg, #475569, #64748b)"
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            st.markdown(f"""
            <div style="width: 45px; height: 45px; background: {'rgba(239, 68, 68, 0.2)' if is_active else 'rgba(71, 85, 105, 0.3)'}; 
                        border-radius: 10px; display: flex; align-items: center; justify-content: center; 
                        font-size: 14px; font-weight: 700; color: {'#ef4444' if is_active else '#94a3b8'}; 
                        font-family: 'JetBrains Mono', monospace;">{ma}</div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="font-weight: 600; color: #e2e8f0; font-size: 14px; margin-bottom: 2px;">MA{ma} 이탈률</div>
            <div style="color: {status_color}; font-size: 12px;">{status_text}</div>
            """, unsafe_allow_html=True)
        
        with col3:
            if badge_text:
                badge_bg = "rgba(239, 68, 68, 0.2)"
                badge_color = "#ef4444"
                st.markdown(f"""
                <div style="text-align: right;">
                    <span style="display: inline-block; padding: 4px 10px; background: {badge_bg}; 
                                 border-radius: 6px; font-size: 11px; font-weight: 600; color: {badge_color}; 
                                 font-family: 'JetBrains Mono', monospace;">{badge_text}</span>
                </div>
                """, unsafe_allow_html=True)
                if remaining_text:
                    st.markdown(f"""
                    <div style="text-align: right; color: #94a3b8; font-size: 11px; margin-top: 4px; 
                                font-family: 'JetBrains Mono', monospace;">{remaining_text}</div>
                    """, unsafe_allow_html=True)
        
        # 프로그레스 바
        st.markdown(f"""
        <div style="height: 6px; background: rgba(51, 65, 85, 0.5); border-radius: 3px; overflow: hidden; margin: 8px 0;">
            <div style="height: 100%; width: {progress}%; background: {prog_color}; border-radius: 3px; transition: width 0.5s ease;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # 갭 표시
        if gap_text:
            st.markdown(f"""
            <div style="color: #64748b; font-size: 12px;">
                {gap_text.split(' ')[0]} <span style="color: #f59e0b; font-weight: 600; font-family: 'JetBrains Mono', monospace;">{' '.join(gap_text.split(' ')[1:])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------
# 4. 메인 실행 함수
# -----------------------------------------------------------
def main():
    # 헤더
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
        <div class="premium-header">
            <div class="header-icon">🎯</div>
            <div>
                <div>
                    <span class="header-title">TQQQ SNIPER</span>
                    <span class="header-version">v4.6</span>
                </div>
                <div class="header-subtitle">Real-Time Signal Analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    analyzer = RealTimeInvestmentAnalyzer()
    data = analyzer.get_latest_data()
    
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        
        # 날짜 및 레짐 배지
        day_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
        weekday_str = day_map[latest.name.weekday()]
        data_date = latest.name.strftime('%Y-%m-%d')
        
        res_today, res_prev, changes, actions = analyzer.analyze_all(data)
        
        regime_class = 'regime-bullish' if res_today['is_bullish'] else 'regime-bearish'
        regime_dot_class = 'regime-dot-bullish' if res_today['is_bullish'] else 'regime-dot-bearish'
        regime_text = 'BULLISH' if res_today['is_bullish'] else 'BEARISH'
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div class="date-badge">
                <span class="date-badge-icon">📅</span>
                <span class="date-badge-label">데이터 기준:</span>
                <span class="date-badge-value">{data_date} ({weekday_str}) 장마감</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="regime-badge {regime_class}">
                <div class="regime-dot {regime_dot_class}"></div>
                {regime_text} REGIME
            </div>
            """, unsafe_allow_html=True)
        
        # 액션 카드
        render_action_card(actions)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # 포트폴리오 구성
        st.markdown("""
        <div class="section-title">
            <span>📊</span> PORTFOLIO COMPOSITION
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            render_portfolio_card('TQQQ', res_today['final_tqqq'], changes['tqqq'], res_prev['final_tqqq'])
        with col2:
            render_portfolio_card('GLD', res_today['final_gld'], changes['gld'], res_prev['final_gld'])
        with col3:
            cash_change = res_today['final_cash'] - res_prev['final_cash']
            render_portfolio_card('CASH', res_today['final_cash'], cash_change, res_prev['final_cash'])
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # 전략 모니터
        st.markdown("""
        <div class="section-title">
            <span>📡</span> STRATEGY MONITOR
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📈 매수 전략 (Buy)", "📉 매도 전략 (Sell)", "📊 차트"])
        
        with tab1:
            st.markdown(f"""
            <div class="adjustment-badge adjustment-badge-buy">
                조정 비중: <span class="adjustment-value">{res_today['error_adj']:.1%}</span> (GLD → TQQQ)
            </div>
            """, unsafe_allow_html=True)
            
            for name, params in analyzer.error_rate_strategies.items():
                is_active = name in res_today['active_error_strats']
                log_info = res_today['error_logs'].get(name)
                aborted = log_info.get('aborted_today', False) if log_info else False
                render_buy_strategy_card(name, params, latest, is_active, log_info, aborted)
        
        with tab2:
            st.markdown(f"""
            <div class="adjustment-badge adjustment-badge-sell">
                조정 비중: <span class="adjustment-value">{abs(res_today['opt_cash_adj']):.1%}</span> (TQQQ → Cash)
            </div>
            """, unsafe_allow_html=True)
            
            for name, params in analyzer.optimized_strategies.items():
                is_active = name in res_today['active_sell_cash']
                log_info = res_today['sell_logs'].get(name)
                aborted = log_info.get('aborted_today', False) if log_info else False
                render_sell_strategy_card(name, params, latest, is_active, log_info, aborted)
        
        with tab3:
            fig = go.Figure()
            chart_data = data.iloc[-120:]
            
            fig.add_trace(go.Candlestick(
                x=chart_data.index,
                open=chart_data['TQQQ_Open'],
                high=chart_data['TQQQ_High'],
                low=chart_data['TQQQ_Low'],
                close=chart_data['TQQQ_Close'],
                name='TQQQ',
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444',
                increasing_fillcolor='rgba(16, 185, 129, 0.8)',
                decreasing_fillcolor='rgba(239, 68, 68, 0.8)'
            ))
            
            ma_colors = ['#f59e0b', '#06b6d4', '#8b5cf6', '#ec4899']
            for i, ma in enumerate(analyzer.ma_periods):
                fig.add_trace(go.Scatter(
                    x=chart_data.index,
                    y=chart_data[f'MA_{ma}'],
                    name=f'MA {ma}',
                    line=dict(color=ma_colors[i], width=1.5),
                    opacity=0.8
                ))
            
            fig.update_layout(
                height=500,
                margin=dict(l=0, r=0, t=20, b=0),
                template="plotly_dark",
                paper_bgcolor='rgba(10, 11, 15, 0)',
                plot_bgcolor='rgba(10, 11, 15, 0.5)',
                xaxis_rangeslider_visible=False,
                xaxis=dict(
                    gridcolor='rgba(71, 85, 105, 0.2)',
                    showgrid=True
                ),
                yaxis=dict(
                    gridcolor='rgba(71, 85, 105, 0.2)',
                    showgrid=True
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0)'
                ),
                font=dict(family="JetBrains Mono, monospace", color='#94a3b8')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Stochastic 인디케이터
        st.markdown(f"""
        <div class="stoch-card">
            <div class="stoch-info">
                <div class="stoch-icon">📊</div>
                <div>
                    <div class="stoch-label">Stochastic (166, 57, 19)</div>
                    <div class="stoch-values">
                        <span class="stoch-k">%K {latest['%K']:.1f}</span>
                        <span class="stoch-sep">/</span>
                        <span class="stoch-d">%D {latest['%D']:.1f}</span>
                    </div>
                </div>
            </div>
            <div class="regime-badge {regime_class}">
                {'📈' if res_today['is_bullish'] else '📉'} {regime_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 푸터
        st.markdown("""
        <div class="footer">
            Built with precision • Not financial advice
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
