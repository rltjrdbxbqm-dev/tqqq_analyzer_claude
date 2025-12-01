import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from pandas.tseries.offsets import BusinessDay
import warnings
warnings.filterwarnings('ignore')

# -----------------------------------------------------------
# 1. 페이지 설정 및 CSS 스타일링
# -----------------------------------------------------------
st.set_page_config(
    page_title="TQQQ/GLD Sniper v4.5",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px;
    }
    .date-badge {
        background-color: #262730;
        padding: 2px 6px;
        border-radius: 5px;
        font-weight: bold;
        color: #00CC99;
        border: 1px solid #00CC99;
        font-size: 0.9em;
    }
    .status-aborted { color: #FF4B4B; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# 2. 분석기 클래스 정의
# -----------------------------------------------------------
class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기 - v4.5 (기본 전략 변화 시 특수 전략 강제 종료)"""

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
        """
        [NEW] 기본 전략의 비중 변화를 전체 기간에 대해 미리 계산
        - 목적: 기본 전략의 포지션 변경 시점(Change Point)을 감지하기 위함
        """
        # 1. Bullish/Bearish 계산
        is_bullish = data['%K'] > data['%D']
        
        # 2. MA 시그널 계산 (Vectorized)
        ma_signals = pd.DataFrame(index=data.index)
        for ma in self.ma_periods:
            ma_signals[ma] = (data['TQQQ_Close'] > data[f'MA_{ma}']).astype(int)
            
        # 3. 비중 계산
        # Bullish: 전체 MA 점수 합산 * 0.25
        bull_alloc = ma_signals.sum(axis=1) * 0.25
        
        # Bearish: (MA20 + MA45) * 0.5 * 0.5 = (MA20 + MA45) * 0.25
        bear_alloc = (ma_signals[20] + ma_signals[45]) * 0.25
        
        base_alloc = pd.Series(np.where(is_bullish, bull_alloc, bear_alloc), index=data.index)
        
        # 4. 변화 감지 (diff가 0이 아니면 변화 발생)
        # fillna(0)으로 첫날은 변화 없는 것으로 처리
        base_change_mask = base_alloc.diff().fillna(0) != 0
        
        return base_change_mask

    def check_signal_with_simulation(self, data, strategy_type, params, base_change_mask):
        """
        [수정] 시뮬레이션 엔진
        - 기본 전략 변화(base_change_mask) 감지 시 강제 종료 로직 추가
        """
        target_days = params['holding_days'] if strategy_type == 'error_buy' else params['sell_days']
        ma_period = params['ma_period']
        threshold = params['deviation_threshold'] if strategy_type == 'error_buy' else params['error_rate']

        remaining_days = 0 
        last_trigger_info = {}
        aborted_today = False # 오늘 강제 종료되었는지 여부
        
        for idx, row in data.iterrows():
            # 1. 기본 전략 변화 체크 (우선순위 최상)
            if remaining_days > 0:
                if base_change_mask[idx]:
                    remaining_days = 0 # 강제 종료
                    # 만약 오늘 날짜에 강제 종료가 일어났다면 기록
                    if idx == data.index[-1]:
                        aborted_today = True
                    continue # 이번 턴은 종료 처리만 하고 넘어감

            # 2. 하루 차감
            if remaining_days > 0:
                remaining_days -= 1
            
            # 3. 신호 조건 확인
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
            
            # 4. 신호 발생 (리셋)
            if condition:
                remaining_days = target_days
                last_trigger_info = {
                    'trigger_deviation': deviation,
                    'trigger_date': idx
                }
                aborted_today = False # 다시 활성화되었으므로 abort 상태 해제

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
                'aborted_today': aborted_today # UI 표시용
            }

        return is_active, remaining_days, final_details

    def analyze_portfolio(self, data, target_idx=None):
        if target_idx is not None:
            analysis_data = data.iloc[:target_idx+1]
        else:
            analysis_data = data
            
        target_data = analysis_data.iloc[-1]
        
        # 0. 기본 전략 변화 마스크 계산
        base_change_mask = self.calculate_base_allocation_series(analysis_data)
        
        # 1. 기본 전략
        is_bullish = target_data['%K'] > target_data['%D']
        ma_signals = {p: target_data['TQQQ_Close'] > target_data[f'MA_{p}'] for p in self.ma_periods}
        
        if is_bullish: base_tqqq = sum(ma_signals.values()) * 0.25
        else: base_tqqq = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5 * 0.5
        
        base_gld = 1 - base_tqqq
        base_cash = 0
        
        # 2. 매수 전략 (기본전략 변화 감지 적용)
        active_error_strats, error_logs = [], {}
        for name, params in self.error_rate_strategies.items():
            active, remaining, details = self.check_signal_with_simulation(analysis_data, 'error_buy', params, base_change_mask)
            if active:
                active_error_strats.append(name)
            if details: # 로그는 활성 여부 상관없이 있으면 저장
                error_logs[name] = details
        error_adj = len(active_error_strats) * 0.25
        
        # 3. 매도 전략 (기본전략 변화 감지 적용)
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
# 3. 메인 실행 함수
# -----------------------------------------------------------
def main():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### 🎯 TQQQ Sniper v4.5")
    with col2:
        if st.button("🔄 Refresh", type="primary"):
            st.cache_data.clear()
            st.rerun()
            
    analyzer = RealTimeInvestmentAnalyzer()
    data = analyzer.get_latest_data()
    
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        
        day_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
        weekday_str = day_map[latest.name.weekday()]
        data_date = latest.name.strftime('%Y-%m-%d')
        st.markdown(f"###### 📅 데이터 기준일: <span class='date-badge'>{data_date} ({weekday_str}) 장마감</span>", unsafe_allow_html=True)

        res_today, res_prev, changes, actions = analyzer.analyze_all(data)
        
        # 1. Action Card
        st.markdown("### 📢 Action Required")
        if actions:
            for a in actions:
                if a['action'] == '매수':
                    st.success(f"**🚀 {a['asset']} {a['amt']:.1%} 매수하세요**")
                else:
                    st.error(f"**📉 {a['asset']} {a['amt']:.1%} 매도하세요**")
        else:
            st.info("**☕ 오늘은 매매 없이 홀딩입니다.**")

        st.markdown("---")

        # 2. Portfolio Overview
        st.markdown("### 💼 Portfolio Composition")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("TQQQ", f"{res_today['final_tqqq']:.1%}", f"{changes['tqqq']:+.1%}")
            st.progress(res_today['final_tqqq'])
        with c2:
            st.metric("GLD", f"{res_today['final_gld']:.1%}", f"{changes['gld']:+.1%}")
            st.progress(res_today['final_gld'])
        with c3:
            st.metric("Cash", f"{res_today['final_cash']:.1%}", "")
            st.progress(res_today['final_cash'])

        # 3. Strategy Monitor
        st.markdown("---")
        st.subheader("🔍 Strategy Monitor")
        
        tab1, tab2, tab3 = st.tabs(["📉 매수 전략 (Buy)", "📈 매도 전략 (Sell)", "📊 시장 차트"])
        
        # Tab 1: 매수 전략
        with tab1:
            st.markdown(f"**조정 비중: {res_today['error_adj']:.1%} (GLD → TQQQ)**")
            for name, params in analyzer.error_rate_strategies.items():
                ma = params['ma_period']
                threshold = params['deviation_threshold']
                current_dev = latest[f'Deviation_{ma}']
                is_active = name in res_today['active_error_strats']
                
                if current_dev > 0: progress = 0.0
                else:
                    if current_dev <= threshold: progress = 1.0
                    else: progress = min(1.0, abs(current_dev) / abs(threshold))
                
                with st.container():
                    col_name, col_prog, col_val = st.columns([2, 4, 2])
                    with col_name:
                        st.markdown(f"**MA {ma}**")
                        if is_active:
                            log_info = res_today['error_logs'][name]
                            trigger_date_str = log_info['trigger_date'].strftime('%m-%d')
                            st.caption(f"✅ 진입일: {trigger_date_str}")
                        elif name in res_today['error_logs'] and res_today['error_logs'][name].get('aborted_today'):
                             st.caption("🛑 기본전략 변화로 종료")
                        else:
                            st.caption("💤 대기중")
                    with col_prog:
                        st.progress(progress)
                    with col_val:
                        if is_active:
                            log_info = res_today['error_logs'][name]
                            remaining = log_info['remaining_trading_days']
                            est_days = int(remaining * 1.45) 
                            target_date = datetime.now() + timedelta(days=est_days)
                            st.markdown("<span class='status-active'>✅ 진입 완료</span>", unsafe_allow_html=True)
                            st.markdown(f"⏳ **{remaining} 거래일 남음**")
                            st.caption(f"(예상: {target_date.strftime('%m-%d')} 경)")
                        elif name in res_today['error_logs'] and res_today['error_logs'][name].get('aborted_today'):
                            st.markdown("<span class='status-aborted'>🛑 강제 종료</span>", unsafe_allow_html=True)
                            st.caption("기본전략 변경 감지")
                        else:
                            gap = current_dev - threshold
                            if gap > 0: st.markdown(f"📉 **-{gap:.1f}%p** 남음")
                            else: st.markdown("⚠️ **조건 대기**")
                    st.divider()

        # Tab 2: 매도 전략
        with tab2:
            st.markdown(f"**조정 비중: {abs(res_today['opt_cash_adj']):.1%} (TQQQ → Cash)**")
            
            for name, params in analyzer.optimized_strategies.items():
                ma = params['ma_period']
                target = params['error_rate']
                current_dev = latest[f'Deviation_{ma}']
                is_active = name in res_today['active_sell_cash']
                
                if current_dev < 0: progress = 0.0
                else:
                    if current_dev >= target: progress = 1.0
                    else: progress = min(1.0, current_dev / target)
                
                dep_msg = ""
                if 'depends_on' in params and not (latest['TQQQ_Close'] > latest[f"MA_{params['depends_on']}"]):
                    dep_msg = "🚫 MA조건 미달"

                with st.container():
                    col_name, col_prog, col_val = st.columns([2, 4, 2])
                    with col_name:
                        st.markdown(f"**Opt MA {ma}**")
                        if is_active:
                            if name in res_today['sell_logs']:
                                log_info = res_today['sell_logs'][name]
                                trigger_date_str = log_info['trigger_date'].strftime('%m-%d')
                                st.caption(f"🚨 매도일: {trigger_date_str}")
                        elif name in res_today['sell_logs'] and res_today['sell_logs'][name].get('aborted_today'):
                             st.caption("🛑 기본전략 변화로 종료")
                        elif dep_msg: st.caption(dep_msg)
                        else: st.caption("💤 대기중")
                        
                    with col_prog:
                        st.progress(progress)
                        
                    with col_val:
                        if is_active:
                            log_info = res_today['sell_logs'][name]
                            remaining = log_info['remaining_trading_days']
                            est_days = int(remaining * 1.45)
                            target_date = datetime.now() + timedelta(days=est_days)
                            st.markdown("<span class='status-cash'>🚨 매도 (현금)</span>", unsafe_allow_html=True)
                            st.markdown(f"⏳ **{remaining} 거래일 남음**")
                            st.caption(f"(예상: {target_date.strftime('%m-%d')} 경)")
                        elif name in res_today['sell_logs'] and res_today['sell_logs'][name].get('aborted_today'):
                            st.markdown("<span class='status-aborted'>🛑 강제 종료</span>", unsafe_allow_html=True)
                            st.caption("기본전략 변경 감지")
                        else:
                            gap = target - current_dev
                            if gap > 0: st.markdown(f"📈 **+{gap:.1f}%p** 남음")
                            else: st.markdown("⚠️ **조건 대기**")
                    st.divider()

        # Tab 3: 차트
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
