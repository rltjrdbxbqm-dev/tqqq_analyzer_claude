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
    page_title="실시간 투자 신호 분석기 v2.2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기 - v2.2 (과거 신호 추적 기능 추가)"""

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

    @st.cache_data(ttl=300)  # 5분 캐시
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

        # 스토캐스틱 계산
        period = self.stoch_config['period']
        k_period = self.stoch_config['k_period']
        d_period = self.stoch_config['d_period']

        df['Highest_High'] = df['TQQQ_High'].rolling(window=period).max()
        df['Lowest_Low'] = df['TQQQ_Low'].rolling(window=period).min()

        df['%K_raw'] = ((df['TQQQ_Close'] - df['Lowest_Low']) /
                        (df['Highest_High'] - df['Lowest_Low'])) * 100
        df['%K'] = df['%K_raw'].rolling(window=k_period).mean()
        df['%D'] = df['%K'].rolling(window=d_period).mean()

        # 이동평균 계산
        for period in self.ma_periods:
            df[f'MA_{period}'] = df['TQQQ_Close'].rolling(window=period).mean()

        # 오차율 계산
        for period in self.ma_periods:
            # 오차율 = (종가 - 이평선) / 이평선 * 100
            df[f'Deviation_{period}'] = ((df['TQQQ_Close'] - df[f'MA_{period}']) / df[f'MA_{period}']) * 100

        return df.dropna()

    def check_historical_signal(self, data, end_idx, strategy_type, params):
        """
        과거 데이터를 조회하여 현재 유효한 신호가 있는지 확인
        end_idx: 분석 기준 시점 (정수 인덱스)
        """
        is_active = False
        trigger_date = None
        trigger_details = {}

        if strategy_type == 'error_buy':
            holding_days = params['holding_days']
            ma_period = params['ma_period']
            threshold = params['deviation_threshold']
            
            # 오늘을 포함하여 과거 holding_days 기간 동안 신호가 있었는지 확인
            # range(0, holding_days) -> 0일전(오늘), 1일전, ... 
            for i in range(holding_days):
                check_idx = end_idx - i
                if check_idx < 0: continue
                
                row = data.iloc[check_idx]
                
                # 당시의 조건 확인
                price_above_ma = row['TQQQ_Close'] > row[f'MA_{ma_period}']
                deviation = row[f'Deviation_{ma_period}']
                
                # 매수 신호 조건: MA 아래에 있고, 오차율이 기준선 이하
                if (not price_above_ma) and (deviation <= threshold):
                    is_active = True
                    trigger_date = row.name # 날짜
                    trigger_details = {
                        'trigger_deviation': deviation,
                        'days_ago': i,
                        'trigger_price': row['TQQQ_Close']
                    }
                    break # 가장 최근 신호 하나만 찾으면 됨 (또는 가장 오래된 것 등 논리에 따라 다름. 여기선 '유지 중'이므로 존재 여부가 중요)

        elif strategy_type == 'optimized_sell':
            sell_days = params['sell_days']
            ma_period = params['ma_period']
            error_threshold = params['error_rate']
            
            for i in range(sell_days):
                check_idx = end_idx - i
                if check_idx < 0: continue
                
                row = data.iloc[check_idx]
                
                # 의존성 체크 (당시 시점 기준)
                is_disabled = False
                if 'depends_on' in params:
                    k_val = row['%K']
                    d_val = row['%D']
                    is_bullish = k_val > d_val
                    
                    if not is_bullish:
                        dep_ma = params['depends_on']
                        if not (row['TQQQ_Close'] > row[f'MA_{dep_ma}']):
                            is_disabled = True
                
                if not is_disabled:
                    price_above_ma = row['TQQQ_Close'] > row[f'MA_{ma_period}']
                    deviation = row[f'Deviation_{ma_period}'] # 이게 error_rate와 같은 개념
                    
                    # 매도 신호 조건: MA 위에 있고, 오차율이 기준선 이상
                    if price_above_ma and (deviation >= error_threshold):
                        is_active = True
                        trigger_date = row.name
                        trigger_details = {
                            'trigger_deviation': deviation,
                            'days_ago': i,
                            'trigger_price': row['TQQQ_Close']
                        }
                        break

        return is_active, trigger_date, trigger_details

    def analyze_portfolio(self, data, target_idx=None):
        """포트폴리오 분석 (특정 시점 기준, 과거 이력 포함)"""
        if target_idx is None:
            target_idx = len(data) - 1
            
        target_data = data.iloc[target_idx]
        
        # 1. 기본 전략 (스토캐스틱 + MA) - *기본 전략은 현재 시점 기준*
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
        
        # 2. 오차율 전략 (매수) - *과거 이력 조회*
        active_error_strategies = []
        error_strategy_logs = []
        
        for strategy_name, params in self.error_rate_strategies.items():
            is_active, trig_date, details = self.check_historical_signal(
                data, target_idx, 'error_buy', params
            )
            
            if is_active:
                active_error_strategies.append(strategy_name)
                error_strategy_logs.append({
                    'name': strategy_name,
                    'type': 'active',
                    'info': details
                })
        
        error_rate_adjustment = len(active_error_strategies) * 0.25
        
        # 3. 최적화 전략 (매도) - *과거 이력 조회*
        active_sell_strategies = []
        sell_strategy_logs = []
        
        for strategy_name, params in self.optimized_strategies.items():
            is_active, trig_date, details = self.check_historical_signal(
                data, target_idx, 'optimized_sell', params
            )
            
            if is_active:
                active_sell_strategies.append(strategy_name)
                sell_strategy_logs.append({
                    'name': strategy_name,
                    'type': 'active',
                    'info': details
                })
        
        optimized_sell_adjustment = len(active_sell_strategies) * 0.25
        
        # 종합 포지션 계산
        final_tqqq = base_tqqq
        final_gld = base_gld
        final_cash = base_cash
        
        # 오차율 조정 (GLD → TQQQ)
        if error_rate_adjustment > 0:
            transfer_amount = min(final_gld, error_rate_adjustment)
            final_gld -= transfer_amount
            final_tqqq += transfer_amount
        
        # 최적화 조정 (TQQQ → 현금)
        if optimized_sell_adjustment > 0:
            transfer_amount = min(final_tqqq, optimized_sell_adjustment)
            final_tqqq -= transfer_amount
            final_cash += transfer_amount
        
        # 정규화
        total = final_tqqq + final_gld + final_cash
        if total > 0:
            final_tqqq = final_tqqq / total
            final_gld = final_gld / total
            final_cash = final_cash / total
            
        return {
            'final_tqqq': final_tqqq,
            'final_gld': final_gld,
            'final_cash': final_cash,
            'base_tqqq': base_tqqq,
            'error_adjustment': error_rate_adjustment,
            'optimized_adjustment': -optimized_sell_adjustment,
            'active_error_strategies': active_error_strategies,
            'active_sell_strategies': active_sell_strategies,
            'is_bullish': is_bullish,
            'stoch_k': k_value,
            'stoch_d': d_value,
            'error_logs': error_strategy_logs,
            'sell_logs': sell_strategy_logs
        }

    def analyze_all_strategies_v22(self, data):
        """통합 분석 및 리포팅 - v2.2"""
        # 당일 포트폴리오 (마지막 인덱스 기준 과거 추적 포함)
        today_idx = len(data) - 1
        today_portfolio = self.analyze_portfolio(data, target_idx=today_idx)
        
        # 전일 포트폴리오 (마지막-1 인덱스 기준 과거 추적 포함)
        yesterday_idx = len(data) - 2
        yesterday_portfolio = self.analyze_portfolio(data, target_idx=yesterday_idx)
        
        # 변화량 계산
        portfolio_changes = {
            'tqqq_change': today_portfolio['final_tqqq'] - yesterday_portfolio['final_tqqq'],
            'gld_change': today_portfolio['final_gld'] - yesterday_portfolio['final_gld'],
            'cash_change': today_portfolio['final_cash'] - yesterday_portfolio['final_cash']
        }
        
        # 매매 지침 생성
        trading_actions = []
        if portfolio_changes['tqqq_change'] > 0.01:
            trading_actions.append({'action': '매수', 'asset': 'TQQQ', 'amount': f"{portfolio_changes['tqqq_change']:.1%}", 'source': 'GLD/현금'})
        elif portfolio_changes['tqqq_change'] < -0.01:
            trading_actions.append({'action': '매도', 'asset': 'TQQQ', 'amount': f"{abs(portfolio_changes['tqqq_change']):.1%}", 'destination': '현금'})
            
        if portfolio_changes['gld_change'] > 0.01:
            trading_actions.append({'action': '매수', 'asset': 'GLD', 'amount': f"{portfolio_changes['gld_change']:.1%}", 'source': 'TQQQ/현금'})
        elif portfolio_changes['gld_change'] < -0.01:
            trading_actions.append({'action': '매도', 'asset': 'GLD', 'amount': f"{abs(portfolio_changes['gld_change']):.1%}", 'destination': 'TQQQ'})

        return {
            'today_portfolio': today_portfolio,
            'yesterday_portfolio': yesterday_portfolio,
            'portfolio_changes': portfolio_changes,
            'trading_actions': trading_actions
        }

def main():
    st.title("🎯 실시간 투자 신호 분석기 v2.2")
    st.markdown("TQQQ/GLD/Cash 포트폴리오 최적화 (과거 신호 추적 적용)")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 새로고침", type="primary"):
            st.cache_data.clear()
            st.rerun()
    with col3:
        st.markdown(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    analyzer = RealTimeInvestmentAnalyzer()
    
    with st.spinner('📥 데이터 로딩 및 분석 중...'):
        data = analyzer.get_latest_data()
        
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        yesterday = data.iloc[-2]
        
        # --- 상단 지표 섹션 ---
        st.subheader("📊 시장 현황")
        col1, col2, col3, col4 = st.columns(4)
        tqqq_change = ((latest['TQQQ_Close'] - yesterday['TQQQ_Close']) / yesterday['TQQQ_Close']) * 100
        gld_change = ((latest['GLD_Close'] - yesterday['GLD_Close']) / yesterday['GLD_Close']) * 100
        
        with col1: st.metric("TQQQ", f"${latest['TQQQ_Close']:.2f}", f"{tqqq_change:+.2f}%")
        with col2: st.metric("GLD", f"${latest['GLD_Close']:.2f}", f"{gld_change:+.2f}%")
        with col3: st.metric("Stoch %K", f"{latest['%K']:.2f}", "Bull" if latest['%K'] > latest['%D'] else "Bear", delta_color="normal" if latest['%K'] > latest['%D'] else "inverse")
        with col4: st.metric("Stoch %D", f"{latest['%D']:.2f}", "")

        # --- 차트 섹션 (요청사항 반영) ---
        st.subheader("📈 TQQQ 기술적 분석 차트")
        
        # 최근 1년치 정도만 차트에 표시
        chart_data = data.iloc[-250:]
        
        fig = go.Figure()
        
        # 캔들스틱
        fig.add_trace(go.Candlestick(
            x=chart_data.index,
            open=chart_data['TQQQ_Open'],
            high=chart_data['TQQQ_High'],
            low=chart_data['TQQQ_Low'],
            close=chart_data['TQQQ_Close'],
            name='TQQQ'
        ))
        
        # 이동평균선 추가
        colors = ['#FF9900', '#00CC99', '#3366FF', '#FF33CC']
        for idx, ma in enumerate(analyzer.ma_periods):
            fig.add_trace(go.Scatter(
                x=chart_data.index,
                y=chart_data[f'MA_{ma}'],
                mode='lines',
                name=f'MA {ma}',
                line=dict(width=1.5, color=colors[idx])
            ))
            
        fig.update_layout(
            height=500,
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- 분석 결과 섹션 ---
        results = analyzer.analyze_all_strategies_v22(data)
        today_port = results['today_portfolio']
        
        st.markdown("---")
        st.subheader("📋 오늘의 매매 및 포지션")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 📅 전일 포지션")
            p = results['yesterday_portfolio']
            st.write(f"TQQQ: {p['final_tqqq']:.1%} | GLD: {p['final_gld']:.1%} | Cash: {p['final_cash']:.1%}")
        with c2:
            st.markdown("### 📅 **당일 권장 포지션**")
            p = today_port
            st.write(f"**TQQQ: {p['final_tqqq']:.1%}** | **GLD: {p['final_gld']:.1%}** | **Cash: {p['final_cash']:.1%}**")
        with c3:
            st.markdown("### 🔄 변동 내역")
            ch = results['portfolio_changes']
            st.write(f"TQQQ: {ch['tqqq_change']:+.1%} | GLD: {ch['gld_change']:+.1%}")

        if results['trading_actions']:
            st.info("🔔 **매매 신호 발생!**")
            for action in results['trading_actions']:
                st.write(f"- {action['action']} **{action['asset']}** {action['amount']} ({action.get('source', '')}{action.get('destination', '')})")
        else:
            st.success("✅ 포지션 유지 (특이사항 없음)")

        st.markdown("---")
        
        # --- 계산 상세 과정 (요청사항 반영: 오차율 표시) ---
        with st.expander("🔍 포지션 계산 과정 상세 (오차율 및 활성 상태)", expanded=True):
            st.markdown(f"""
            ### 1️⃣ 기본 전략 (스토캐스틱 & MA)
            - **상태**: {'🟢 Bullish (상승장)' if today_port['is_bullish'] else '🔴 Bearish (하락장)'}
            - **기본 배분**: TQQQ {today_port['base_tqqq']:.1%} / GLD {1-today_port['base_tqqq']:.1%}
            """)
            
            st.markdown("### 2️⃣ 오차율 전략 (매수 신호)")
            if today_port['active_error_strategies']:
                for strat in today_port['error_logs']:
                    s_info = analyzer.error_rate_strategies[strat['name']]
                    current_dev = latest[f"Deviation_{s_info['ma_period']}"]
                    trigger_dev = strat['info']['trigger_deviation']
                    
                    st.markdown(f"""
                    - **✅ {strat['name']} 활성**: {strat['info']['days_ago']}일 전 발동됨
                        - **현재 오차율**: `{current_dev:.2f}%` (기준: `{s_info['deviation_threshold']}%` 이하)
                        - **발동 당시 오차율**: `{trigger_dev:.2f}%`
                        - **보유 기간**: {s_info['holding_days']}일간 유지
                    """)
                st.markdown(f"👉 **조정 결과**: GLD에서 **{today_port['error_adjustment']:.1%}**를 TQQQ로 이동")
            else:
                st.markdown("- 💤 활성화된 매수 전략 없음")
                # 현재 상태 보여주기
                st.markdown("#### 🔎 현재 오차율 모니터링")
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

            st.markdown("### 3️⃣ 최적화 전략 (매도 신호)")
            if today_port['active_sell_strategies']:
                for strat in today_port['sell_logs']:
                    s_info = analyzer.optimized_strategies[strat['name']]
                    current_dev = latest[f"Deviation_{s_info['ma_period']}"]
                    trigger_dev = strat['info']['trigger_deviation']
                    
                    st.markdown(f"""
                    - **🚨 {strat['name']} 활성**: {strat['info']['days_ago']}일 전 발동됨
                        - **현재 오차율**: `{current_dev:.2f}%` (기준: `{s_info['error_rate']}%` 이상)
                        - **발동 당시 오차율**: `{trigger_dev:.2f}%`
                        - **매도 기간**: {s_info['sell_days']}일간 현금 보유
                    """)
                st.markdown(f"👉 **조정 결과**: TQQQ에서 **{abs(today_port['optimized_adjustment']):.1%}**를 현금화")
            else:
                st.markdown("- 💤 활성화된 매도 전략 없음")

if __name__ == "__main__":
    main()
