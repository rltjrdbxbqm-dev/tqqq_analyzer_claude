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
    page_title="실시간 투자 신호 분석기 v2.4",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기 - v2.4 (통합 모니터링 및 남은 오차율 표시)"""

    def __init__(self):
        # 전략 설정
        self.stoch_config = {'period': 166, 'k_period': 57, 'd_period': 19}
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
        # 스토캐스틱
        period, k_p, d_p = self.stoch_config.values()
        df['Highest_High'] = df['TQQQ_High'].rolling(window=period).max()
        df['Lowest_Low'] = df['TQQQ_Low'].rolling(window=period).min()
        df['%K'] = ((df['TQQQ_Close'] - df['Lowest_Low']) / (df['Highest_High'] - df['Lowest_Low']) * 100).rolling(window=k_p).mean()
        df['%D'] = df['%K'].rolling(window=d_p).mean()

        # MA 및 오차율
        for ma in self.ma_periods:
            df[f'MA_{ma}'] = df['TQQQ_Close'].rolling(window=ma).mean()
            df[f'Deviation_{ma}'] = ((df['TQQQ_Close'] - df[f'MA_{ma}']) / df[f'MA_{ma}']) * 100
        return df.dropna()

    def check_historical_signal(self, data, end_idx, strategy_type, params):
        is_active, trigger_date, trigger_details = False, None, {}
        days_check = params['holding_days'] if strategy_type == 'error_buy' else params['sell_days']
        ma_period = params['ma_period']
        threshold = params['deviation_threshold'] if strategy_type == 'error_buy' else params['error_rate']

        for i in range(days_check):
            idx = end_idx - i
            if idx < 0: continue
            row = data.iloc[idx]
            price_above_ma = row['TQQQ_Close'] > row[f'MA_{ma_period}']
            deviation = row[f'Deviation_{ma_period}']

            condition = False
            if strategy_type == 'error_buy':
                condition = (not price_above_ma) and (deviation <= threshold)
            else: # optimized_sell
                is_disabled = False
                if 'depends_on' in params and not (row['TQQQ_Close'] > row[f"MA_{params['depends_on']}"]):
                    is_disabled = True
                condition = (not is_disabled) and price_above_ma and (deviation >= threshold)

            if condition:
                is_active = True
                trigger_date = row.name
                trigger_details = {'trigger_deviation': deviation, 'days_ago': i}
                break
        return is_active, trigger_date, trigger_details

    def analyze_portfolio(self, data, target_idx=None):
        if target_idx is None: target_idx = len(data) - 1
        target_data = data.iloc[target_idx]
        
        # 1. 기본
        is_bullish = target_data['%K'] > target_data['%D']
        ma_signals = {p: target_data['TQQQ_Close'] > target_data[f'MA_{p}'] for p in self.ma_periods}
        
        if is_bullish: base_tqqq = sum(ma_signals.values()) * 0.25
        else: base_tqqq = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5 * 0.5
        
        base_gld = 1 - base_tqqq
        base_cash = 0
        
        # 2. 오차율(매수)
        active_error_strats = []
        error_logs = {} # 딕셔너리로 변경하여 이름으로 접근 용이하게 함
        for name, params in self.error_rate_strategies.items():
            active, _, details = self.check_historical_signal(data, target_idx, 'error_buy', params)
            if active:
                active_error_strats.append(name)
                error_logs[name] = details
        
        error_adj = len(active_error_strats) * 0.25
        
        # 3. 최적화(매도)
        active_sell_strats = []
        sell_logs = {}
        for name, params in self.optimized_strategies.items():
            active, _, details = self.check_historical_signal(data, target_idx, 'optimized_sell', params)
            if active:
                active_sell_strats.append(name)
                sell_logs[name] = details

        opt_adj = len(active_sell_strats) * 0.25
        
        # 최종 계산
        final_tqqq = base_tqqq
        final_gld = base_gld
        final_cash = base_cash

        # GLD -> TQQQ
        if error_adj > 0:
            amt = min(final_gld, error_adj)
            final_gld -= amt
            final_tqqq += amt
        
        # TQQQ -> Cash
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
            'is_bullish': is_bullish, 'ma_signals': ma_signals
        }

    def analyze_all(self, data):
        today = self.analyze_portfolio(data)
        yesterday = self.analyze_portfolio(data, len(data)-2)
        
        changes = {
            'tqqq': today['final_tqqq'] - yesterday['final_tqqq'],
            'gld': today['final_gld'] - yesterday['final_gld']
        }
        
        actions = []
        for asset, chg in changes.items():
            if chg > 0.01: actions.append({'action': '매수', 'asset': asset.upper(), 'amt': chg})
            elif chg < -0.01: actions.append({'action': '매도', 'asset': asset.upper(), 'amt': abs(chg)})
            
        return today, yesterday, changes, actions

def main():
    st.title("🎯 실시간 투자 신호 분석기 v2.4")
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 새로고침"): st.cache_data.clear(); st.rerun()
        
    analyzer = RealTimeInvestmentAnalyzer()
    data = analyzer.get_latest_data()
    
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        res_today, res_prev, changes, actions = analyzer.analyze_all(data)
        
        # 1. 시장 현황 (간소화)
        st.info(f"**TQQQ**: ${latest['TQQQ_Close']:.2f} | **GLD**: ${latest['GLD_Close']:.2f} | **Stoch**: {'Bull' if res_today['is_bullish'] else 'Bear'} ({latest['%K']:.1f})")
        
        # 2. 차트
        with st.expander("📈 TQQQ 차트 보기", expanded=False):
            fig = go.Figure()
            chart_data = data.iloc[-150:]
            fig.add_trace(go.Candlestick(x=chart_data.index, open=chart_data['TQQQ_Open'], high=chart_data['TQQQ_High'], low=chart_data['TQQQ_Low'], close=chart_data['TQQQ_Close'], name='TQQQ'))
            colors = ['#FF9900', '#00CC99', '#3366FF', '#FF33CC']
            for i, ma in enumerate(analyzer.ma_periods):
                fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data[f'MA_{ma}'], name=f'MA {ma}', line=dict(color=colors[i], width=1)))
            fig.update_layout(height=400, margin=dict(l=0,r=0,t=20,b=0), template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # 3. 포트폴리오 결과
        st.subheader("📋 포트폴리오 현황")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"**어제**: TQQQ {res_prev['final_tqqq']:.1%} / GLD {res_prev['final_gld']:.1%} / Cash {res_prev['final_cash']:.1%}")
        with c2: st.markdown(f"**오늘**: **TQQQ {res_today['final_tqqq']:.1%}** / **GLD {res_today['final_gld']:.1%}** / **Cash {res_today['final_cash']:.1%}**")
        with c3: 
            if actions:
                for a in actions: st.markdown(f"🔔 **{a['action']} {a['asset']}**: {a['amt']:.1%}")
            else: st.markdown("✅ **포지션 유지**")

        # 4. 통합 전략 모니터링 (핵심 수정 부분)
        st.markdown("---")
        st.subheader("🔍 포지션 계산 상세 & 전략 모니터링")
        
        # 4-1. 오차율 매수 전략 통합 뷰
        with st.container():
            st.markdown(f"#### 2️⃣ 오차율 매수 전략 (GLD → TQQQ) : **{res_today['error_adj']:.1%} 조정**")
            
            # 헤더
            cols = st.columns([1.5, 1.5, 1, 1, 2])
            cols[0].markdown("**전략명**")
            cols[1].markdown("**상태**")
            cols[2].markdown("**현재오차**")
            cols[3].markdown("**목표오차**")
            cols[4].markdown("**달성까지 (Gap)**")
            st.markdown("<hr style='margin: 5px 0'>", unsafe_allow_html=True)

            for name, params in analyzer.error_rate_strategies.items():
                ma = params['ma_period']
                threshold = params['deviation_threshold']
                current_dev = latest[f'Deviation_{ma}']
                
                is_active = name in res_today['active_error_strats']
                
                cols = st.columns([1.5, 1.5, 1, 1, 2])
                cols[0].text(f"{name.split('_')[1]} (MA{ma})")
                
                # 상태 표시
                if is_active:
                    days_ago = res_today['error_logs'][name]['days_ago']
                    cols[1].markdown(f"✅ **활성** ({days_ago}일전)")
                else:
                    cols[1].text("💤 대기")
                
                cols[2].text(f"{current_dev:.2f}%")
                cols[3].text(f"{threshold}%")
                
                # Gap 계산 (매수는 오차율이 더 낮아져야 함)
                # Gap = 현재 - 목표 (양수면 더 떨어져야 함, 음수면 이미 달성)
                gap = current_dev - threshold
                if is_active:
                    cols[4].markdown("🚀 **진입 완료**")
                elif gap > 0:
                    cols[4].markdown(f"📉 **{gap:.2f}% 더 하락 필요**")
                else:
                    # 활성 상태는 아니지만 조건은 충족한 경우(MA 조건 불만족 등)
                    cols[4].markdown(f"⚠️ 조건 확인 필요")

        st.write("") # 여백

        # 4-2. 최적화 매도 전략 통합 뷰
        with st.container():
            st.markdown(f"#### 3️⃣ 최적화 매도 전략 (TQQQ → Cash) : **{abs(res_today['opt_adj']):.1%} 조정**")
            
            # 헤더
            cols = st.columns([1.5, 1.5, 1, 1, 2])
            cols[0].markdown("**전략명**")
            cols[1].markdown("**상태**")
            cols[2].markdown("**현재오차**")
            cols[3].markdown("**목표오차**")
            cols[4].markdown("**달성까지 (Gap)**")
            st.markdown("<hr style='margin: 5px 0'>", unsafe_allow_html=True)

            for name, params in analyzer.optimized_strategies.items():
                ma = params['ma_period']
                target = params['error_rate']
                current_dev = latest[f'Deviation_{ma}']
                
                is_active = name in res_today['active_sell_strats']
                
                cols = st.columns([1.5, 1.5, 1, 1, 2])
                cols[0].text(f"{name.split('_')[1]} (MA{ma})")
                
                # 상태
                if is_active:
                    days_ago = res_today['sell_logs'][name]['days_ago']
                    cols[1].markdown(f"🚨 **활성** ({days_ago}일전)")
                else:
                    # 의존성 체크
                    dep_msg = ""
                    if 'depends_on' in params:
                         if not (latest['TQQQ_Close'] > latest[f"MA_{params['depends_on']}"]):
                             dep_msg = "(MA 미달)"
                    cols[1].text(f"💤 대기 {dep_msg}")
                
                cols[2].text(f"{current_dev:.2f}%")
                cols[3].text(f"{target}%")
                
                # Gap 계산 (매도는 오차율이 더 커져야 함)
                # Gap = 목표 - 현재 (양수면 더 올라야 함)
                gap = target - current_dev
                if is_active:
                    cols[4].markdown("🔴 **매도 실행 중**")
                elif gap > 0:
                    cols[4].markdown(f"📈 **{gap:.2f}% 더 상승 필요**")
                else:
                    cols[4].markdown(f"⚠️ MA 조건 등 미충족")

if __name__ == "__main__":
    main()
