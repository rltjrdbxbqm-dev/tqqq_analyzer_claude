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
    page_title="실시간 투자 신호 분석기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class RealTimeInvestmentAnalyzer:
    """실시간 투자 신호 분석기"""

    def __init__(self):
        # 전략 설정
        self.stoch_config = {
            'period': 166,
            'k_period': 57,
            'd_period': 19
        }

        self.ma_periods = [20, 45, 151, 212]

        # 오차율 전략 설정
        self.error_rate_strategies = {
            'TQQQ_Strategy_1': {'ma_period': 20, 'deviation_threshold': -12, 'holding_days': 8},
            'TQQQ_Strategy_2': {'ma_period': 45, 'deviation_threshold': -11, 'holding_days': 5},
            'TQQQ_Strategy_3': {'ma_period': 151, 'deviation_threshold': -21, 'holding_days': 8},
            'TQQQ_Strategy_4': {'ma_period': 212, 'deviation_threshold': -15, 'holding_days': 4},
        }

        # 최적화 전략 설정
        self.optimized_strategies = {
            'TQQQ_Optimized_1': {'ma_period': 45, 'error_rate': 33, 'sell_days': 11},
            'TQQQ_Optimized_2': {'ma_period': 151, 'error_rate': 55, 'sell_days': 13},
            'TQQQ_Optimized_3': {'ma_period': 212, 'error_rate': 55, 'sell_days': 12},
        }

    def get_latest_data(self, days_back=400):
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
            df[f'Deviation_{period}'] = ((df['TQQQ_Close'] - df[f'MA_{period}']) / df[f'MA_{period}']) * 100

        return df.dropna()

    def analyze_all_strategies_detailed(self, data):
        """모든 전략 상세 분석"""
        latest = data.iloc[-1]
        
        # 1. 스토캐스틱 + MA 전략
        k_value = latest['%K']
        d_value = latest['%D']
        is_bullish = k_value > d_value
        
        ma_signals = {}
        for period in self.ma_periods:
            ma_signals[period] = latest['TQQQ_Close'] > latest[f'MA_{period}']
        
        if is_bullish:
            tqqq_position_1 = sum(ma_signals.values()) * 0.25
        else:
            short_ma_signals = sum([ma_signals[20], ma_signals[45]])
            tqqq_position_1 = short_ma_signals * 0.5
        
        # 2. 오차율 전략 (상세 정보 포함)
        error_strategy_details = []
        active_error_strategies = []
        above_ma_count = 0
        
        for strategy_name, params in self.error_rate_strategies.items():
            ma_period = params['ma_period']
            threshold = params['deviation_threshold']
            holding_days = params['holding_days']
            current_deviation = latest[f'Deviation_{ma_period}']
            current_price = latest['TQQQ_Close']
            current_ma = latest[f'MA_{ma_period}']
            
            price_above_ma = current_price > current_ma
            if price_above_ma:
                above_ma_count += 1
            
            buy_signal = (not price_above_ma) and (current_deviation <= threshold)
            
            if buy_signal:
                active_error_strategies.append(strategy_name)
                sell_date = datetime.now() + timedelta(days=holding_days)
                # 주말 조정
                if sell_date.weekday() == 5:  # 토요일
                    sell_date += timedelta(days=2)
                elif sell_date.weekday() == 6:  # 일요일
                    sell_date += timedelta(days=1)
                
                error_strategy_details.append({
                    'name': strategy_name,
                    'ma_period': ma_period,
                    'current_deviation': current_deviation,
                    'threshold': threshold,
                    'status': '🚀 매수신호',
                    'sell_date': sell_date.strftime('%Y-%m-%d'),
                    'holding_days': holding_days
                })
        
        if above_ma_count == len(self.error_rate_strategies):
            tqqq_position_2 = 1.0
        elif len(active_error_strategies) > 0:
            tqqq_position_2 = len(active_error_strategies) / len(self.error_rate_strategies)
        else:
            tqqq_position_2 = above_ma_count / len(self.error_rate_strategies)
        
        # 3. 최적화 전략 (상세 정보 포함)
        optimized_strategy_details = []
        hold_strategies = []
        sell_strategies = []
        
        for strategy_name, params in self.optimized_strategies.items():
            ma_period = params['ma_period']
            error_threshold = params['error_rate']
            sell_days = params['sell_days']
            
            current_price = latest['TQQQ_Close']
            current_ma = latest[f'MA_{ma_period}']
            basic_signal = current_price > current_ma
            
            if basic_signal:
                current_error_rate = ((current_price - current_ma) / current_ma) * 100
                sell_signal = current_error_rate >= error_threshold
                
                if sell_signal:
                    sell_strategies.append(strategy_name)
                    rebuy_date = datetime.now() + timedelta(days=sell_days)
                    # 주말 조정
                    if rebuy_date.weekday() == 5:
                        rebuy_date += timedelta(days=2)
                    elif rebuy_date.weekday() == 6:
                        rebuy_date += timedelta(days=1)
                    
                    optimized_strategy_details.append({
                        'name': strategy_name,
                        'ma_period': ma_period,
                        'current_error_rate': current_error_rate,
                        'threshold': error_threshold,
                        'status': '🔴 매도신호',
                        'rebuy_date': rebuy_date.strftime('%Y-%m-%d'),
                        'sell_days': sell_days
                    })
                else:
                    hold_strategies.append(strategy_name)
                    optimized_strategy_details.append({
                        'name': strategy_name,
                        'ma_period': ma_period,
                        'current_error_rate': current_error_rate,
                        'threshold': error_threshold,
                        'status': '🟢 보유권장',
                        'rebuy_date': None,
                        'sell_days': None
                    })
            else:
                optimized_strategy_details.append({
                    'name': strategy_name,
                    'ma_period': ma_period,
                    'current_error_rate': 0,
                    'threshold': error_threshold,
                    'status': '❌ MA하회',
                    'rebuy_date': None,
                    'sell_days': None
                })
        
        tqqq_position_3 = len(hold_strategies) / len(self.optimized_strategies)
        
        # 종합 계산 (전략1 기본 + 전략2,3 조정)
        base_tqqq = tqqq_position_1
        error_rate_adjustment = len(active_error_strategies) * 0.05 if active_error_strategies else 0
        hold_ratio = len(hold_strategies) / len(self.optimized_strategies)
        optimized_adjustment = (hold_ratio - 1.0) * 0.2 if hold_ratio < 1.0 else 0
        
        final_tqqq = max(0, min(1.0, base_tqqq + error_rate_adjustment + optimized_adjustment))
        final_gld = 1 - final_tqqq
        
        return {
            'stoch_k': k_value,
            'stoch_d': d_value,
            'is_bullish': is_bullish,
            'ma_signals': ma_signals,
            'base_tqqq': base_tqqq,
            'error_adjustment': error_rate_adjustment,
            'optimized_adjustment': optimized_adjustment,
            'final_tqqq': final_tqqq,
            'final_gld': final_gld,
            'active_error_count': len(active_error_strategies),
            'hold_strategies_count': len(hold_strategies),
            'error_strategy_details': error_strategy_details,
            'optimized_strategy_details': optimized_strategy_details,
            'sell_strategies_count': len(sell_strategies)
        }

def main():
    # 헤더
    st.title("🎯 실시간 투자 신호 분석기")
    st.markdown("TQQQ/GLD 포트폴리오 최적화 시스템")
    
    # 새로고침 버튼
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 새로고침", type="primary"):
            st.rerun()
    with col3:
        st.markdown(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    # 분석기 초기화 및 데이터 로드
    analyzer = RealTimeInvestmentAnalyzer()
    
    with st.spinner('📥 데이터 로딩 중...'):
        data = analyzer.get_latest_data()
        
    if data is not None:
        data = analyzer.calculate_technical_indicators(data)
        latest = data.iloc[-1]
        yesterday = data.iloc[-2]
        
        # 현재 가격 정보
        st.subheader("📊 현재 시장 상황")
        
        col1, col2, col3, col4 = st.columns(4)
        
        tqqq_change = ((latest['TQQQ_Close'] - yesterday['TQQQ_Close']) / yesterday['TQQQ_Close']) * 100
        gld_change = ((latest['GLD_Close'] - yesterday['GLD_Close']) / yesterday['GLD_Close']) * 100
        
        with col1:
            st.metric(
                "TQQQ", 
                f"${latest['TQQQ_Close']:.2f}",
                f"{tqqq_change:+.2f}%",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "GLD",
                f"${latest['GLD_Close']:.2f}",
                f"{gld_change:+.2f}%",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                "Stochastic %K",
                f"{latest['%K']:.2f}",
                f"{'상승' if latest['%K'] > latest['%D'] else '하락'}",
                delta_color="normal" if latest['%K'] > latest['%D'] else "inverse"
            )
        
        with col4:
            st.metric(
                "Stochastic %D",
                f"{latest['%D']:.2f}",
                ""
            )
        
        # 전략 분석
        results = analyzer.analyze_all_strategies_detailed(data)
        
        st.markdown("---")
        
        # 종합 권장사항
        st.subheader("🎯 종합 투자 권장사항")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 포지션 차트
            fig = go.Figure(data=[
                go.Bar(name='TQQQ', x=['권장 포지션'], y=[results['final_tqqq']*100], 
                       marker_color='#00CC88', text=f"{results['final_tqqq']:.1%}",
                       textposition='inside'),
                go.Bar(name='GLD', x=['권장 포지션'], y=[results['final_gld']*100],
                       marker_color='#FFD700', text=f"{results['final_gld']:.1%}",
                       textposition='inside')
            ])
            fig.update_layout(
                title="포트폴리오 구성",
                yaxis_title="비중 (%)",
                barmode='stack',
                height=300,
                showlegend=True,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 투자 금액 계산
            st.markdown("### 💰 투자 금액 계산기")
            
            investment = st.number_input(
                "총 투자금 (원)",
                min_value=100000,
                max_value=100000000,
                value=1000000,
                step=100000,
                format="%d"
            )
            
            tqqq_amount = investment * results['final_tqqq']
            gld_amount = investment * results['final_gld']
            
            st.info(f"""
            **TQQQ**: {tqqq_amount:,.0f}원 ({int(tqqq_amount/latest['TQQQ_Close']/1300)}주)  
            **GLD**: {gld_amount:,.0f}원 ({int(gld_amount/latest['GLD_Close']/1300)}주)
            """)
        
        # 전략별 상세 정보 - 개선된 버전
        st.markdown("---")
        st.subheader("📈 전략별 상세 분석")
        
        # 탭으로 구성
        tab1, tab2, tab3 = st.tabs(["1️⃣ 기본 전략", "2️⃣ 오차율 전략", "3️⃣ 최적화 전략"])
        
        with tab1:
            st.markdown(f"### 스토캐스틱 + 이동평균 전략")
            st.markdown(f"**현재 상태**: {'🟢 상승 추세' if results['is_bullish'] else '🔴 하락 추세'}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**이동평균 조건:**")
                for period, signal in results['ma_signals'].items():
                    status = '✅ 충족' if signal else '❌ 미충족'
                    price = latest[f'MA_{period}']
                    deviation = latest[f'Deviation_{period}']
                    st.markdown(f"• MA{period}: {status}")
                    st.caption(f"  가격: ${price:.2f} (오차: {deviation:+.2f}%)")
            
            with col2:
                st.markdown("**포지션 계산:**")
                st.markdown(f"• 기본 TQQQ 비중: **{results['base_tqqq']:.1%}**")
                st.markdown(f"• GLD 비중: **{(1-results['base_tqqq']):.1%}**")
                
                if results['is_bullish']:
                    st.info("상승 추세: 4개 MA 조건 × 25%씩")
                else:
                    st.info("하락 추세: MA20,45 조건 × 50%씩")
        
        with tab2:
            st.markdown(f"### 오차율 하락 매수 전략")
            st.markdown(f"**활성 매수 신호**: {results['active_error_count']}개")
            
            if results['error_strategy_details']:
                st.success(f"🚀 **매수 신호 발생! TQQQ 비중 +{results['error_adjustment']:.1%}**")
                
                for detail in results['error_strategy_details']:
                    with st.expander(f"MA{detail['ma_period']} 전략 - {detail['status']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**현재 오차율**: {detail['current_deviation']:.2f}%")
                            st.markdown(f"**매수 임계값**: {detail['threshold']:.1f}%")
                            st.markdown(f"**상태**: {detail['status']}")
                        with col2:
                            st.markdown(f"**보유 기간**: {detail['holding_days']}일")
                            st.markdown(f"**매도 예정일**: {detail['sell_date']}")
                            gap = detail['current_deviation'] - detail['threshold']
                            st.markdown(f"**임계값 초과**: {gap:.2f}%p")
            else:
                st.info("⏳ 현재 매수 신호 없음 (조정 대기 중)")
                
                # 대기 중인 전략들의 현황 표시
                st.markdown("**각 전략 현황:**")
                for strategy_name, params in analyzer.error_rate_strategies.items():
                    ma_period = params['ma_period']
                    current_deviation = latest[f'Deviation_{ma_period}']
                    threshold = params['deviation_threshold']
                    gap = current_deviation - threshold
                    
                    if latest['TQQQ_Close'] > latest[f'MA_{ma_period}']:
                        status = "📈 MA 상회 (전략 비활성)"
                    else:
                        status = f"⏳ 하락 대기 (추가 {gap:.2f}%p 필요)"
                    
                    st.caption(f"• MA{ma_period}: 오차율 {current_deviation:.2f}% / 임계값 {threshold}% - {status}")
        
        with tab3:
            st.markdown(f"### 백테스트 최적화 전략")
            st.markdown(f"**보유 권장**: {results['hold_strategies_count']}/{len(analyzer.optimized_strategies)}")
            st.markdown(f"**매도 신호**: {results['sell_strategies_count']}개")
            
            if results['optimized_adjustment'] != 0:
                if results['optimized_adjustment'] < 0:
                    st.warning(f"⚠️ **조정: TQQQ 비중 {results['optimized_adjustment']:.1%}**")
                    st.caption("매도 신호로 인한 포지션 축소")
                else:
                    st.success(f"✅ **조정: TQQQ 비중 +{results['optimized_adjustment']:.1%}**")
            else:
                st.info("조정 없음 (전체 보유 권장)")
            
            # 각 전략 상세 정보
            for detail in results['optimized_strategy_details']:
                icon = "🔴" if detail['status'] == '🔴 매도신호' else "🟢" if detail['status'] == '🟢 보유권장' else "❌"
                
                with st.expander(f"{icon} MA{detail['ma_period']} 전략 - {detail['status']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**현재 오차율**: {detail['current_error_rate']:.2f}%")
                        st.markdown(f"**매도 임계값**: {detail['threshold']:.1f}%")
                        st.markdown(f"**상태**: {detail['status']}")
                    
                    with col2:
                        if detail['status'] == '🔴 매도신호':
                            st.markdown(f"**조정 기간**: {detail['sell_days']}일")
                            st.markdown(f"**재매수 예정일**: {detail['rebuy_date']}")
                            gap = detail['current_error_rate'] - detail['threshold']
                            st.markdown(f"**임계값 초과**: +{gap:.2f}%p")
                        elif detail['status'] == '🟢 보유권장':
                            gap = detail['threshold'] - detail['current_error_rate']
                            st.markdown(f"**매도까지 여유**: {gap:.2f}%p")
            
            # 조정 계산 설명
            with st.expander("📊 조정값 계산 방법"):
                st.markdown(f"""
                **조정값 = (보유권장 비율 - 1.0) × 0.2**
                
                • 보유권장 비율: {results['hold_strategies_count']}/3 = {results['hold_strategies_count']/3:.2f}
                • 계산: ({results['hold_strategies_count']/3:.2f} - 1.0) × 0.2 = **{results['optimized_adjustment']:.3f}**
                
                **의미:**
                - 3개 모두 보유 권장 시: 조정 없음 (0%)
                - 2개 보유 권장 시: TQQQ -6.7% 조정
                - 1개 보유 권장 시: TQQQ -13.3% 조정
                - 0개 보유 권장 시: TQQQ -20% 조정
                """)
        
        # 차트
        st.markdown("---")
        st.subheader("📊 가격 차트 (최근 30일)")
        
        # 최근 30일 데이터
        recent_data = data.tail(30)
        
        fig = go.Figure()
        
        # TQQQ 가격과 이동평균
        fig.add_trace(go.Scatter(
            x=recent_data.index,
            y=recent_data['TQQQ_Close'],
            name='TQQQ',
            line=dict(color='#00CC88', width=2)
        ))
        
        # 이동평균선들
        colors = ['blue', 'orange', 'red', 'purple']
        for i, period in enumerate(analyzer.ma_periods):
            fig.add_trace(go.Scatter(
                x=recent_data.index,
                y=recent_data[f'MA_{period}'],
                name=f'MA{period}',
                line=dict(color=colors[i], width=1, dash='dash'),
                opacity=0.7
            ))
        
        fig.update_layout(
            title="TQQQ 가격 및 이동평균선",
            xaxis_title="날짜",
            yaxis_title="가격 ($)",
            height=400,
            hovermode='x unified',
            showlegend=True,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 투자 유의사항
        with st.expander("⚠️ 투자 유의사항"):
            st.warning("""
            - 이 분석은 참고용이며 투자 권유가 아닙니다
            - 실제 투자 시 시장 뉴스와 경제 지표를 추가로 고려하세요
            - 분할 매수/매도를 통한 리스크 분산을 권장합니다
            - 정기적인 포트폴리오 리밸런싱이 필요합니다
            - 레버리지 ETF(TQQQ)는 높은 변동성을 가집니다
            """)

if __name__ == "__main__":
    main()
