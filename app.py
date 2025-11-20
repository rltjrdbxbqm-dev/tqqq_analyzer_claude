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
    page_title="실시간 투자 신호 분석기 v2.3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기 - v2.3 (최적화 전략 목표치 표시 강화)"""

    def __init__(self):
        # 전략 설정
        self.stoch_config = {
            'period': 166,
            'k_period': 57,
            'd_period': 19
        }

        self.ma_periods = [20, 45, 151, 212]

        # 오차율 전략 설정 (매수)
        self.error_rate_strategies = {
            'TQQQ_Strategy_1': {'ma_period': 20, 'deviation_threshold': -12, 'holding_days': 8},
            'TQQQ_Strategy_2': {'ma_period': 45, 'deviation_threshold': -11, 'holding_days': 5},
            'TQQQ_Strategy_3': {'ma_period': 151, 'deviation_threshold': -21, 'holding_days': 8},
            'TQQQ_Strategy_4': {'ma_period': 212, 'deviation_threshold': -15, 'holding_days': 4},
        }

        # 최적화 전략 설정 (매도)
        self.optimized_strategies = {
            'TQQQ_Optimized_1': {'ma_period': 45, 'error_rate': 33, 'sell_days': 11},
            'TQQQ_Optimized_2': {'ma_period': 151, 'error_rate': 55, 'sell_days': 13, 'depends_on': 20},
            'TQQQ_Optimized_3': {'ma_period': 212, 'error_rate': 55, 'sell_days': 12, 'depends_on': 45},
        }

    @st.cache_data(ttl=300)
    def get_latest_data(_self, days_back=400):
        """최신 데이터 가져오기"""
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
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in data[ticker].columns:
                        combined_data[f'{ticker}_{col}'] = data[ticker][col]

            combined_data = combined_data.dropna()
            return combined_data

        except Exception as e:
            st.error(f"❌ 데이터 다운로드 실패: {e}")
            return None

    def calculate_technical_indicators(self, data):
        """기술적 지표 계산"""
        df = data.copy()

        # 스토캐스틱
        period = self.stoch_config['period']
        k_period = self.stoch_config['k_period']
        d_period = self.stoch_config['d_period']

        df['Highest_High'] = df['TQQQ_High'].rolling(window=period).max()
        df['Lowest_Low'] = df['TQQQ_Low'].rolling(window=period).min()

        df['%K_raw'] = ((df['TQQQ_Close'] - df['Lowest_Low']) /
                        (df['Highest_High'] - df['Lowest_Low'])) * 100
        df['%K'] = df['%K_raw'].rolling(window=k_period).mean()
        df['%D'] = df['%K'].rolling(window=d_period).mean()

        # 이동평균 & 오차율
        for period in self.ma_periods:
            df[f'MA_{period}'] = df['TQQQ_Close'].rolling(window=period).mean()
            df[f'Deviation_{period}'] = ((df['TQQQ_Close'] - df[f'MA_{period}']) / df[f'MA_{period}']) * 100

        return df.dropna()

    def check_historical_signal(self, data, end_idx, strategy_type, params):
        """과거 신호 추적"""
        is_active = False
        trigger_date = None
        trigger_details = {}

        if strategy_type == 'error_buy':
            holding_days = params['holding_days']
            ma_period = params['ma_period']
            threshold = params['deviation_threshold']
            
            for i in range(holding_days):
                check_idx = end_idx - i
                if check_idx < 0: continue
                row = data.iloc[check_idx]
                
                price_above_ma = row['TQQQ_Close'] > row[f'MA_{ma_period}']
                deviation = row[f'Deviation_{ma_period}']
                
                if (not price_above_ma) and (deviation <= threshold):
                    is_active = True
                    trigger_date = row.name
                    trigger_details = {'trigger_deviation': deviation, 'days_ago': i}
                    break

        elif strategy_type == 'optimized_sell':
            sell_days = params['sell_days']
            ma_period = params['ma_period']
            error_threshold = params['error_rate']
            
            for i in range(sell_days):
                check_idx = end_idx - i
                if check_idx < 0: continue
                row = data.iloc[check_idx]
                
                is_disabled = False
                if 'depends_on' in params:
                    if not (row['TQQQ_Close'] > row[f"MA_{params['depends_on']}"]):
                        is_disabled = True
                
                if not is_disabled:
                    price_above_ma = row['TQQQ_Close'] > row[f'MA_{ma_period}']
                    deviation = row[f'Deviation_{ma_period}']
                    
                    if price_above_ma and (deviation >= error_threshold):
                        is_active = True
                        trigger_date = row.name
                        trigger_details = {'trigger_deviation': deviation, 'days_ago': i}
                        break

        return is_active, trigger_date, trigger_details

    def analyze_portfolio(self, data, target_idx=None):
        if target_idx is None: target_idx = len(data) - 1
        target_data = data.iloc[target_idx]
        
        # 1. 기본 전략
        k_value = target_data['%K']
        d_value = target_data['%D']
        is_bullish = k_value > d_value
        
        ma_signals = {}
        for period in self.ma_periods:
            ma_signals[period] = target_data['TQQQ_Close'] > target_data[f'MA_{period}']
            
        if is_bullish:
            base_tqqq = sum(ma_signals.values()) * 0.25
        else:
            short_ma_signals = sum([ma_signals[20], ma_signals[45]])
            base_tqqq = short_ma_signals * 0.5
        
        base_gld = 1 - base_tqqq
        base_cash = 0
        
        # 2. 오차율 전략 (매수)
        active_error_strategies = []
        error_strategy_logs = []
        for name, params in self.error_rate_strategies.items():
            is_active, _, details = self.check_historical_signal(data, target_idx, 'error_buy', params)
            if is_active:
                active_error_strategies.append(name)
                error_strategy_logs.append({'name': name, 'info': details})
        
        error_adjustment = len(active_error_strategies) * 0.25
        
        # 3. 최적화 전략 (매도)
        active_sell_strategies = []
        sell_strategy_logs = []
        for name, params in self.optimized_strategies.items():
            is_active, _, details = self.check_historical_signal(data, target_idx, 'optimized_sell', params)
            if is_active:
                active_sell_strategies.append(name)
                sell_strategy_logs.append({'name': name, 'info': details})
        
        optimized_adjustment = len(active_sell_strategies) * 0.25
        
        # 종합 계산
        final_tqqq = base_tqqq
        final_gld = base_gld
        final_cash = base_cash
        
        if error_adjustment > 0:
            amt = min(final_gld, error_adjustment)
            final_gld -= amt
            final_tqqq += amt
            
        if optimized_adjustment > 0:
            amt = min(final_tqqq, optimized_adjustment)
            final_tqqq -= amt
            final_cash += amt
            
        total = final_tqqq + final_gld + final_cash
        if total > 0:
            final_tqqq /= total
            final_gld /= total
            final_cash /= total
            
        return {
            'final_tqqq': final_tqqq, 'final_gld': final_gld, 'final_cash': final_cash,
            'base_tqqq': base_tqqq,
            'error_adjustment': error_adjustment, 'optimized_adjustment': -optimized_adjustment,
            'active_error_strategies': active_error_strategies,
            'active_sell_strategies': active_sell_strategies,
            'is_bullish': is_bullish,
            'error_logs': error_strategy_logs, 'sell_logs': sell_strategy_logs
        }

    def analyze_all_strategies(self, data):
        today = self.analyze_portfolio(data)
        yesterday = self.analyze_portfolio(data, target_idx=len(data)-2)
        
        changes = {
            'tqqq': today['final_tqqq'] - yesterday['final_tqqq'],
            'gld': today['final_gld'] - yesterday['final_gld'],
            'cash': today['final_cash'] - yesterday['final_cash']
        }
        
        actions = []
        if changes['tqqq'] > 0.01: actions.append({'action': '매수', 'asset': 'TQQQ', 'amt': changes['tqqq']})
        elif changes['tqqq'] < -0.01: actions.append({'action': '매도', 'asset': 'TQQQ', 'amt': abs(changes['tqqq'])})
        
        if changes['gld'] > 0.01: actions.append({'action': '매수', 'asset': 'GLD', 'amt': changes['gld']})
        elif changes['gld'] < -0.01: actions.append({'action': '매도', 'asset': 'GLD', 'amt': abs(changes['gld'])})
        
        return today, yesterday, changes, actions

def main():
    st.title("🎯 실시간 투자 신호 분석기 v2.3")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 새로고침", type="primary"):
            st.cache_data.clear()
            st.rerun()
    with col3:
        st.markdown(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    analyzer = RealTimeInvestmentAnalyzer()
    
    with st.spinner('분석 중...'):
        data = analyzer.get_latest_data()
        
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        yesterday = data.iloc[-2]
        today_port, yesterday_port, changes, actions = analyzer.analyze_all_strategies(data)
        
        # 시장 현황
        st.subheader("📊 시장 현황")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("TQQQ", f"${latest['TQQQ_Close']:.2f}", f"{((latest['TQQQ_Close']/yesterday['TQQQ_Close'])-1)*100:+.2f}%")
        with c2: st.metric("GLD", f"${latest['GLD_Close']:.2f}", f"{((latest['GLD_Close']/yesterday['GLD_Close'])-1)*100:+.2f}%")
        with c3: st.metric("Stoch %K", f"{latest['%K']:.2f}", "Bull" if latest['%K'] > latest['%D'] else "Bear")
        with c4: st.metric("Stoch %D", f"{latest['%D']:.2f}", "")

        # 차트
        st.subheader("📈 TQQQ 차트")
        fig = go.Figure()
        chart_data = data.iloc[-250:]
        fig.add_trace(go.Candlestick(x=chart_data.index, open=chart_data['TQQQ_Open'], high=chart_data['TQQQ_High'], low=chart_data['TQQQ_Low'], close=chart_data['TQQQ_Close'], name='TQQQ'))
        colors = ['#FF9900', '#00CC99', '#3366FF', '#FF33CC']
        for i, ma in enumerate(analyzer.ma_periods):
            fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data[f'MA_{ma}'], mode='lines', name=f'MA {ma}', line=dict(width=1.5, color=colors[i])))
        fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)

        # 포지션 결과
        st.markdown("---")
        st.subheader("📋 포트폴리오 권장사항")
        c1, c2, c3 = st.columns(3)
        with c1: st.info(f"**어제**: TQQQ {yesterday_port['final_tqqq']:.1%} / GLD {yesterday_port['final_gld']:.1%} / 현금 {yesterday_port['final_cash']:.1%}")
        with c2: st.success(f"**오늘**: TQQQ {today_port['final_tqqq']:.1%} / GLD {today_port['final_gld']:.1%} / 현금 {today_port['final_cash']:.1%}")
        with c3: st.warning(f"**변동**: TQQQ {changes['tqqq']:+.1%} / GLD {changes['gld']:+.1%}")
        
        if actions:
            for act in actions:
                st.write(f"🔔 **{act['action']}**: {act['asset']} {act['amt']:.1%}")
        else:
            st.write("✅ 포지션 유지")

        # 상세 분석 (수정됨)
        st.markdown("---")
        with st.expander("🔍 포지션 계산 상세 및 전략 모니터링", expanded=True):
            # 1. 오차율 매수 전략
            st.markdown("### 2️⃣ 오차율 전략 (매수, GLD → TQQQ)")
            if today_port['active_error_strategies']:
                for log in today_port['error_logs']:
                    st.write(f"✅ **{log['name']} 활성**: {log['info']['days_ago']}일전 발동 (당시 오차 {log['info']['trigger_deviation']:.2f}%)")
            
            # 오차율 모니터링
            st.markdown("#### 📉 현재 오차율 vs 매수 기준(Threshold)")
            cols = st.columns(4)
            for i, (name, params) in enumerate(analyzer.error_rate_strategies.items()):
                cur_dev = latest[f"Deviation_{params['ma_period']}"]
                with cols[i]:
                    st.metric(
                        f"MA {params['ma_period']}",
                        f"{cur_dev:.2f}%",
                        f"기준 {params['deviation_threshold']}%",
                        delta_color="normal" if cur_dev <= params['deviation_threshold'] else "off"
                    )

            st.markdown("---")
            
            # 2. 최적화 매도 전략 (여기가 수정됨)
            st.markdown("### 3️⃣ 최적화 전략 (매도, TQQQ → 현금)")
            if today_port['active_sell_strategies']:
                for log in today_port['sell_logs']:
                    st.write(f"🚨 **{log['name']} 활성**: {log['info']['days_ago']}일전 발동 (당시 오차 {log['info']['trigger_deviation']:.2f}%)")
            
            # 최적화 목표치 모니터링 추가
            st.markdown("#### 📈 현재 오차율 vs 매도 목표(Target)")
            cols_opt = st.columns(len(analyzer.optimized_strategies))
            for i, (name, params) in enumerate(analyzer.optimized_strategies.items()):
                cur_dev = latest[f"Deviation_{params['ma_period']}"]
                target = params['error_rate']
                
                # 매도 전략은 이격도가 목표치보다 '높아야' 발동하므로, 높을수록 target에 가까워지는 것(positive perspective for monitoring) 
                # 혹은 목표 달성 시 매도이므로 위험 신호로 볼 수도 있음.
                # 여기서는 목표치까지 얼마나 남았는지 직관적으로 보여줌.
                with cols_opt[i]:
                    st.metric(
                        f"{name.split('_')[1]} (MA{params['ma_period']})",
                        f"{cur_dev:.2f}%",
                        f"목표 {target}%",
                        delta_color="inverse"  # 목표치보다 낮으면(안전) 회색/녹색, 높으면(매도구간) 빨간색 처리 자동 적용
                    )

if __name__ == "__main__":
    main()
