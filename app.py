import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="TQQQ/GLD Sniper v3.1",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 커스텀
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
</style>
""", unsafe_allow_html=True)

class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기 - v3.1 (First-In Logic Applied)"""

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

    def check_historical_signal(self, data, end_idx, strategy_type, params):
        """과거 신호 우선 (First-In) 로직 적용"""
        is_active, trigger_date, trigger_details = False, None, {}
        days_check = params['holding_days'] if strategy_type == 'error_buy' else params['sell_days']
        ma_period = params['ma_period']
        threshold = params['deviation_threshold'] if strategy_type == 'error_buy' else params['error_rate']

        # 중요: range(days_check - 1, -1, -1) -> 과거부터 현재 순으로 검색
        # 예: 7일전 -> 6일전 -> ... -> 오늘
        for i in range(days_check - 1, -1, -1):
            idx = end_idx - i
            if idx < 0: continue
            row = data.iloc[idx]
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
                is_active = True
                trigger_date = row.name
                # 가장 먼저 발생한(가장 오래된) 신호를 찾으면 즉시 확정하고 루프 종료
                # 이렇게 하면 그 이후(더 최근)에 발생한 신호는 무시됨 (기간 연장 방지)
                trigger_details = {'trigger_deviation': deviation, 'days_ago': i}
                break 

        return is_active, trigger_date, trigger_details

    def analyze_portfolio(self, data, target_idx=None):
        if target_idx is None: target_idx = len(data) - 1
        target_data = data.iloc[target_idx]
        is_bullish = target_data['%K'] > target_data['%D']
        ma_signals = {p: target_data['TQQQ_Close'] > target_data[f'MA_{p}'] for p in self.ma_periods}
        
        if is_bullish: base_tqqq = sum(ma_signals.values()) * 0.25
        else: base_tqqq = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5 * 0.5
        
        base_gld = 1 - base_tqqq
        base_cash = 0
        
        active_error_strats, error_logs = [], {}
        for name, params in self.error_rate_strategies.items():
            active, _, details = self.check_historical_signal(data, target_idx, 'error_buy', params)
            if active:
                active_error_strats.append(name)
                error_logs[name] = details
        error_adj = len(active_error_strats) * 0.25
        
        active_sell_strats, sell_logs = [], {}
        for name, params in self.optimized_strategies.items():
            active, _, details = self.check_historical_signal(data, target_idx, 'optimized_sell', params)
            if active:
                active_sell_strats.append(name)
                sell_logs[name] = details
        opt_adj = len(active_sell_strats) * 0.25
        
        final_tqqq, final_gld, final_cash = base_tqqq, base_gld, base_cash
        
        if error_adj > 0:
            amt = min(final_gld, error_adj)
            final_gld -= amt
            final_tqqq += amt
        if opt_adj > 0:
            amt = min(final_tqqq, opt_adj)
            final_tqqq -= amt
            final_cash += amt
            
        total = final_tqqq + final_gld + final_cash
        if total > 0:
            final_tqqq /= total; final_gld /= total; final_cash /= total
            
        return {
            'final_tqqq': final_tqqq, 'final_gld': final_gld, 'final_cash': final_cash,
            'base_tqqq': base_tqqq, 'error_adj': error_adj, 'opt_adj': -opt_adj,
            'active_error_strats': active_error_strats, 'active_sell_strats': active_sell_strats,
            'error_logs': error_logs, 'sell_logs': sell_logs,
            'is_bullish': is_bullish
        }

    def analyze_all(self, data):
        today = self.analyze_portfolio(data)
        yesterday = self.analyze_portfolio(data, len(data)-2)
        changes = {'tqqq': today['final_tqqq'] - yesterday['final_tqqq'], 'gld': today['final_gld'] - yesterday['final_gld']}
        actions = []
        for asset, chg in changes.items():
            if chg > 0.01: actions.append({'action': '매수', 'asset': asset.upper(), 'amt': chg})
            elif chg < -0.01: actions.append({'action': '매도', 'asset': asset.upper(), 'amt': abs(chg)})
        return today, yesterday, changes, actions

def main():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🎯 TQQQ Sniper Dashboard")
    with col2:
        if st.button("🔄 Refresh", type="primary"):
            st.cache_data.clear()
            st.rerun()
            
    analyzer = RealTimeInvestmentAnalyzer()
    data = analyzer.get_latest_data()
    
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        res_today, res_prev, changes, actions = analyzer.analyze_all(data)
        
        # 1. Action Card
        st.markdown("### 📢 Action Required")
        if actions:
            for a in actions:
                if a['action'] == '매수':
                    st.success(f"### 🚀 {a['asset']} {a['amt']:.1%} 매수하세요")
                else:
                    st.error(f"### 📉 {a['asset']} {a['amt']:.1%} 매도하세요")
        else:
            st.info("### ☕ 오늘은 매매 없이 홀딩입니다.")

        st.markdown("---")

        # 2. Portfolio Overview
        st.markdown("### 💼 Portfolio Composition")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("TQQQ Allocation", f"{res_today['final_tqqq']:.1%}", f"{changes['tqqq']:+.1%}")
            st.progress(res_today['final_tqqq'])
        with c2:
            st.metric("GLD Allocation", f"{res_today['final_gld']:.1%}", f"{changes['gld']:+.1%}")
            st.progress(res_today['final_gld'])
        with c3:
            st.metric("Cash Allocation", f"{res_today['final_cash']:.1%}", "")
            st.progress(res_today['final_cash'])

        # 3. Strategy Monitor
        st.markdown("---")
        st.subheader("🔍 Strategy Monitor")
        
        tab1, tab2, tab3 = st.tabs(["📉 매수 전략 (Buy)", "📈 매도 전략 (Sell)", "📊 시장 차트"])
        
        with tab1:
            st.markdown(f"**조정 비중: {res_today['error_adj']:.1%} (GLD → TQQQ)**")
            for name, params in analyzer.error_rate_strategies.items():
                ma = params['ma_period']
                threshold = params['deviation_threshold']
                current_dev = latest[f'Deviation_{ma}']
                is_active = name in res_today['active_error_strats']
                
                if current_dev > 0:
                    progress = 0.0
                else:
                    if current_dev <= threshold:
                        progress = 1.0
                    else:
                        progress = min(1.0, abs(current_dev) / abs(threshold))
                
                with st.container():
                    col_name, col_prog, col_val = st.columns([2, 4, 2])
                    with col_name:
                        st.markdown(f"**MA {ma}**")
                        if is_active:
                            st.caption(f"✅ {res_today['error_logs'][name]['days_ago']}일전 진입")
                        else:
                            st.caption("💤 대기중")
                    with col_prog:
                        st.progress(progress)
                    with col_val:
                        if is_active:
                            st.markdown("✅ **진입 완료**")
                        else:
                            gap = current_dev - threshold
                            if gap > 0:
                                st.markdown(f"📉 **-{gap:.1f}%p** 남음")
                            else:
                                st.markdown("⚠️ **조건 대기**")
                    st.divider()

        with tab2:
            st.markdown(f"**조정 비중: {abs(res_today['opt_adj']):.1%} (TQQQ → Cash)**")
            for name, params in analyzer.optimized_strategies.items():
                ma = params['ma_period']
                target = params['error_rate']
                current_dev = latest[f'Deviation_{ma}']
                is_active = name in res_today['active_sell_strats']
                
                if current_dev < 0:
                    progress = 0.0
                else:
                    if current_dev >= target:
                        progress = 1.0
                    else:
                        progress = min(1.0, current_dev / target)
                
                dep_msg = ""
                if 'depends_on' in params and not (latest['TQQQ_Close'] > latest[f"MA_{params['depends_on']}"]):
                    dep_msg = "🚫 MA조건 미달"

                with st.container():
                    col_name, col_prog, col_val = st.columns([2, 4, 2])
                    with col_name:
                        st.markdown(f"**Opt MA {ma}**")
                        if is_active:
                            st.caption(f"🚨 {res_today['sell_logs'][name]['days_ago']}일전 매도")
                        elif dep_msg:
                            st.caption(dep_msg)
                        else:
                            st.caption("💤 대기중")
                    with col_prog:
                        st.progress(progress)
                    with col_val:
                        if is_active:
                            st.markdown("🚨 **매도 완료**")
                        else:
                            gap = target - current_dev
                            if gap > 0:
                                st.markdown(f"📈 **+{gap:.1f}%p** 남음")
                            else:
                                st.markdown("⚠️ **조건 대기**")
                    st.divider()

        with tab3:
            fig = go.Figure()
            chart_data = data.iloc[-120:]
            fig.add_trace(go.Candlestick(x=chart_data.index, open=chart_data['TQQQ_Open'], high=chart_data['TQQQ_High'], low=chart_data['TQQQ_Low'], close=chart_data['TQQQ_Close'], name='TQQQ'))
            colors = ['#FF9900', '#00CC99', '#3366FF', '#FF33CC']
            for i, ma in enumerate(analyzer.ma_periods):
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data[f'MA_{ma}'], name=f'MA {ma}', line=dict(color=colors[i], width=1)))
            fig.update_layout(height=500, margin=dict(l=0,r=0,t=20,b=0), template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
