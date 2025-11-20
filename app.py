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
    """실시간 투자 신호 분석기 - v2.2"""

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
            'TQQQ_Optimized_2': {'ma_period': 151, 'error_rate': 55, 'sell_days': 13, 'depends_on': 20},
            'TQQQ_Optimized_3': {'ma_period': 212, 'error_rate': 55, 'sell_days': 12, 'depends_on': 45},
        }

        # 진행중인 전략 추적
        self.active_strategies = {
            'error_rate_buy': [],  # 진행중인 오차율 매수 전략
            'optimized_sell': []   # 진행중인 최적화 매도 전략
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
            df[f'Deviation_{period}'] = ((df['TQQQ_Close'] - df[f'MA_{period}']) / df[f'MA_{period}']) * 100

        return df.dropna()

    def track_active_strategies(self, data):
        """진행중인 전략 추적 및 업데이트"""
        current_date = data.index[-1]
        
        # 진행중인 오차율 매수 전략 업데이트
        updated_error_strategies = []
        for strategy in self.active_strategies['error_rate_buy']:
            buy_date = strategy['buy_date']
            holding_days = strategy['holding_days']
            
            # 보유 기간 계산
            days_held = (current_date - buy_date).days
            if days_held < holding_days:
                # 아직 보유 중
                strategy['days_held'] = days_held
                strategy['days_remaining'] = holding_days - days_held
                updated_error_strategies.append(strategy)
        
        self.active_strategies['error_rate_buy'] = updated_error_strategies
        
        # 진행중인 최적화 매도 전략 업데이트
        updated_sell_strategies = []
        for strategy in self.active_strategies['optimized_sell']:
            sell_date = strategy['sell_date']
            rebuy_days = strategy['rebuy_days']
            
            # 재매수까지 남은 일수 계산
            days_since_sell = (current_date - sell_date).days
            if days_since_sell < rebuy_days:
                # 아직 현금 보유 중
                strategy['days_since_sell'] = days_since_sell
                strategy['days_until_rebuy'] = rebuy_days - days_since_sell
                updated_sell_strategies.append(strategy)
        
        self.active_strategies['optimized_sell'] = updated_sell_strategies

    def analyze_portfolio(self, data, use_yesterday=False):
        """포트폴리오 분석 (오늘 또는 어제 기준)"""
        if use_yesterday and len(data) > 1:
            target_data = data.iloc[-2]  # 전일 데이터
            date_label = data.index[-2].strftime('%Y-%m-%d') if hasattr(data.index[-2], 'strftime') else str(data.index[-2])
        else:
            target_data = data.iloc[-1]  # 당일 데이터
            date_label = data.index[-1].strftime('%Y-%m-%d') if hasattr(data.index[-1], 'strftime') else str(data.index[-1])
        
        # 진행중인 전략 추적 업데이트
        self.track_active_strategies(data)
        
        # 스토캐스틱
        k_value = target_data['%K']
        d_value = target_data['%D']
        is_bullish = k_value > d_value
        
        # MA 신호
        ma_signals = {}
        for period in self.ma_periods:
            ma_signals[period] = target_data['TQQQ_Close'] > target_data[f'MA_{period}']
        
        # 1. 기본 전략
        if is_bullish:
            base_tqqq = sum(ma_signals.values()) * 0.25
        else:
            short_ma_signals = sum([ma_signals[20], ma_signals[45]])
            base_tqqq = short_ma_signals * 0.5
        
        base_gld = 1 - base_tqqq
        base_cash = 0
        
        # 2. 오차율 전략 (기본 + 진행중인 전략)
        active_error_strategies = []
        error_rates = {}
        for strategy_name, params in self.error_rate_strategies.items():
            ma_period = params['ma_period']
            threshold = params['deviation_threshold']
            current_deviation = target_data[f'Deviation_{ma_period}']
            current_price = target_data['TQQQ_Close']
            current_ma = target_data[f'MA_{ma_period}']
            
            price_above_ma = current_price > current_ma
            buy_signal = (not price_above_ma) and (current_deviation <= threshold)
            
            error_rates[ma_period] = current_deviation
            
            if buy_signal:
                active_error_strategies.append({
                    'name': strategy_name,
                    'ma_period': ma_period,
                    'deviation': current_deviation,
                    'threshold': threshold,
                    'holding_days': params['holding_days']
                })
        
        # 진행중인 오차율 매수 전략도 활성으로 간주
        for active_strategy in self.active_strategies['error_rate_buy']:
            if active_strategy not in active_error_strategies:
                active_error_strategies.append(active_strategy)
        
        error_rate_adjustment = len(active_error_strategies) * 0.25
        
        # 3. 최적화 전략
        sell_strategies = []
        disabled_strategies = []
        optimized_error_rates = {}
        
        for strategy_name, params in self.optimized_strategies.items():
            ma_period = params['ma_period']
            error_threshold = params['error_rate']
            
            # 현재 오차율 계산
            current_price = target_data['TQQQ_Close']
            current_ma = target_data[f'MA_{ma_period}']
            current_error_rate = ((current_price - current_ma) / current_ma) * 100
            optimized_error_rates[ma_period] = {
                'current': current_error_rate,
                'target': error_threshold
            }
            
            # 하락 추세일 때 의존성 체크
            is_disabled = False
            if not is_bullish and 'depends_on' in params:
                depends_on_ma = params['depends_on']
                if not ma_signals[depends_on_ma]:
                    is_disabled = True
                    disabled_strategies.append(strategy_name)
            
            if not is_disabled:
                basic_signal = current_price > current_ma
                
                if basic_signal:
                    sell_signal = current_error_rate >= error_threshold
                    if sell_signal:
                        sell_strategies.append(strategy_name)
        
        # 진행중인 최적화 매도 전략도 활성으로 간주
        optimized_sell_adjustment = len(sell_strategies) * 0.25 + len(self.active_strategies['optimized_sell']) * 0.25
        
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
            'active_error_count': len(active_error_strategies),
            'active_error_strategies': active_error_strategies,
            'sell_strategies_count': len(sell_strategies),
            'error_rates': error_rates,
            'optimized_error_rates': optimized_error_rates,
            'active_optimized_sell_count': len(self.active_strategies['optimized_sell']),
            'date': date_label
        }

    def execute_strategies(self, data, analysis_results):
        """전략 실행 및 진행중인 전략 업데이트"""
        current_date = data.index[-1]
        latest = data.iloc[-1]
        
        # 오차율 매수 전략 실행
        for strategy in analysis_results['error_strategy_details']:
            if strategy['status'] == '🚀 매수신호':
                # 새로운 매수 전략인지 확인
                strategy_exists = False
                for active_strategy in self.active_strategies['error_rate_buy']:
                    if active_strategy['name'] == strategy['name']:
                        strategy_exists = True
                        break
                
                if not strategy_exists:
                    self.active_strategies['error_rate_buy'].append({
                        'name': strategy['name'],
                        'ma_period': strategy['ma_period'],
                        'buy_date': current_date,
                        'holding_days': strategy['holding_days'],
                        'deviation_at_buy': strategy['current_deviation'],
                        'target_sell_date': strategy['sell_date']
                    })
        
        # 최적화 매도 전략 실행
        for strategy in analysis_results['optimized_strategy_details']:
            if strategy['status'] == '🔴 매도신호' and not strategy.get('is_disabled', False):
                # 새로운 매도 전략인지 확인
                strategy_exists = False
                for active_strategy in self.active_strategies['optimized_sell']:
                    if active_strategy['name'] == strategy['name']:
                        strategy_exists = True
                        break
                
                if not strategy_exists:
                    self.active_strategies['optimized_sell'].append({
                        'name': strategy['name'],
                        'ma_period': strategy['ma_period'],
                        'sell_date': current_date,
                        'rebuy_days': strategy['sell_days'],
                        'error_rate_at_sell': strategy['current_error_rate'],
                        'target_rebuy_date': strategy['rebuy_date']
                    })

    def create_tqqq_chart(self, data):
        """TQQQ 차트 생성 (4개 이동평균선 포함)"""
        # 최근 100일 데이터 사용
        chart_data = data.tail(100).copy()
        
        fig = go.Figure()
        
        # TQQQ 종가 라인
        fig.add_trace(go.Scatter(
            x=chart_data.index,
            y=chart_data['TQQQ_Close'],
            name='TQQQ Close',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # 이동평균선들
        colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # 서로 다른 색상
        for i, period in enumerate(self.ma_periods):
            fig.add_trace(go.Scatter(
                x=chart_data.index,
                y=chart_data[f'MA_{period}'],
                name=f'MA {period}',
                line=dict(color=colors[i], width=1.5, dash='dash')
            ))
        
        fig.update_layout(
            title='TQQQ 주가 및 이동평균선 (최근 100일)',
            xaxis_title='날짜',
            yaxis_title='가격 ($)',
            height=400,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig

    def analyze_all_strategies_v22(self, data):
        """모든 전략 상세 분석 - v2.2"""
        latest = data.iloc[-1]
        
        # 당일 포트폴리오
        today_portfolio = self.analyze_portfolio(data, use_yesterday=False)
        
        # 전일 포트폴리오
        yesterday_portfolio = self.analyze_portfolio(data, use_yesterday=True)
        
        # 포트폴리오 변화 계산
        portfolio_changes = {
            'tqqq_change': today_portfolio['final_tqqq'] - yesterday_portfolio['final_tqqq'],
            'gld_change': today_portfolio['final_gld'] - yesterday_portfolio['final_gld'],
            'cash_change': today_portfolio['final_cash'] - yesterday_portfolio['final_cash']
        }
        
        # 매매 지침 생성
        trading_actions = []
        
        if portfolio_changes['tqqq_change'] > 0.01:
            trading_actions.append({
                'action': '매수',
                'asset': 'TQQQ',
                'amount': f"{portfolio_changes['tqqq_change']:.1%}",
                'source': 'GLD/현금'
            })
        elif portfolio_changes['tqqq_change'] < -0.01:
            trading_actions.append({
                'action': '매도',
                'asset': 'TQQQ',
                'amount': f"{abs(portfolio_changes['tqqq_change']):.1%}",
                'destination': '현금'
            })
        
        if portfolio_changes['gld_change'] > 0.01:
            trading_actions.append({
                'action': '매수',
                'asset': 'GLD',
                'amount': f"{portfolio_changes['gld_change']:.1%}",
                'source': 'TQQQ/현금'
            })
        elif portfolio_changes['gld_change'] < -0.01:
            trading_actions.append({
                'action': '매도',
                'asset': 'GLD',
                'amount': f"{abs(portfolio_changes['gld_change']):.1%}",
                'destination': 'TQQQ'
            })
        
        # 기술적 지표
        k_value = latest['%K']
        d_value = latest['%D']
        is_bullish = k_value > d_value
        
        ma_signals = {}
        for period in self.ma_periods:
            ma_signals[period] = latest['TQQQ_Close'] > latest[f'MA_{period}']
        
        # 오차율 전략 상세
        error_strategy_details = []
        active_error_strategies = []
        
        for strategy_name, params in self.error_rate_strategies.items():
            ma_period = params['ma_period']
            threshold = params['deviation_threshold']
            holding_days = params['holding_days']
            current_deviation = latest[f'Deviation_{ma_period}']
            current_price = latest['TQQQ_Close']
            current_ma = latest[f'MA_{ma_period}']
            
            price_above_ma = current_price > current_ma
            buy_signal = (not price_above_ma) and (current_deviation <= threshold)
            
            if buy_signal:
                active_error_strategies.append(strategy_name)
                sell_date = datetime.now() + timedelta(days=holding_days)
                if sell_date.weekday() == 5:
                    sell_date += timedelta(days=2)
                elif sell_date.weekday() == 6:
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
        
        # 최적화 전략 상세
        optimized_strategy_details = []
        hold_strategies = []
        sell_strategies = []
        disabled_strategies = []
        
        for strategy_name, params in self.optimized_strategies.items():
            ma_period = params['ma_period']
            error_threshold = params['error_rate']
            sell_days = params['sell_days']
            
            is_disabled = False
            if not is_bullish and 'depends_on' in params:
                depends_on_ma = params['depends_on']
                if not ma_signals[depends_on_ma]:
                    is_disabled = True
                    disabled_strategies.append(strategy_name)
                    optimized_strategy_details.append({
                        'name': strategy_name,
                        'ma_period': ma_period,
                        'current_error_rate': 0,
                        'threshold': error_threshold,
                        'status': f'⛔ 비활성 (MA{depends_on_ma} 미충족)',
                        'rebuy_date': None,
                        'sell_days': None,
                        'is_disabled': True
                    })
            
            if not is_disabled:
                current_price = latest['TQQQ_Close']
                current_ma = latest[f'MA_{ma_period}']
                basic_signal = current_price > current_ma
                
                if basic_signal:
                    current_error_rate = ((current_price - current_ma) / current_ma) * 100
                    sell_signal = current_error_rate >= error_threshold
                    
                    if sell_signal:
                        sell_strategies.append(strategy_name)
                        rebuy_date = datetime.now() + timedelta(days=sell_days)
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
                            'sell_days': sell_days,
                            'is_disabled': False
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
                            'sell_days': None,
                            'is_disabled': False
                        })
                else:
                    optimized_strategy_details.append({
                        'name': strategy_name,
                        'ma_period': ma_period,
                        'current_error_rate': 0,
                        'threshold': error_threshold,
                        'status': '❌ MA하회',
                        'rebuy_date': None,
                        'sell_days': None,
                        'is_disabled': False
                    })
        
        active_optimized_count = len(self.optimized_strategies) - len(disabled_strategies)
        
        analysis_results = {
            # 기술적 지표
            'stoch_k': k_value,
            'stoch_d': d_value,
            'is_bullish': is_bullish,
            'ma_signals': ma_signals,
            
            # 포트폴리오
            'today_portfolio': today_portfolio,
            'yesterday_portfolio': yesterday_portfolio,
            'portfolio_changes': portfolio_changes,
            'trading_actions': trading_actions,
            
            # 오차율 전략
            'active_error_count': len(active_error_strategies),
            'error_strategy_details': error_strategy_details,
            
            # 최적화 전략
            'hold_strategies_count': len(hold_strategies),
            'sell_strategies_count': len(sell_strategies),
            'disabled_strategies_count': len(disabled_strategies),
            'active_optimized_count': active_optimized_count,
            'optimized_strategy_details': optimized_strategy_details
        }
        
        # 전략 실행
        self.execute_strategies(data, analysis_results)
        
        return analysis_results

def main():
    # 헤더
    st.title("🎯 실시간 투자 신호 분석기 v2.2")
    st.markdown("TQQQ/GLD/Cash 포트폴리오 최적화 시스템 - 진행중인 전략 반영")
    
    # 새로고침 버튼
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 새로고침", type="primary"):
            st.cache_data.clear()
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
        results = analyzer.analyze_all_strategies_v22(data)
        
        st.markdown("---")
        
        # 매매 지침 섹션 (날짜 정보 추가)
        st.subheader("📋 오늘의 매매 지침")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown(f"### 📅 전일 포트폴리오 ({results['yesterday_portfolio']['date']})")
            yesterday_port = results['yesterday_portfolio']
            st.markdown(f"""
            - **TQQQ**: {yesterday_port['final_tqqq']:.1%}
            - **GLD**: {yesterday_port['final_gld']:.1%}
            - **현금**: {yesterday_port['final_cash']:.1%}
            """)
        
        with col2:
            st.markdown(f"### 📅 당일 권장 포트폴리오 ({results['today_portfolio']['date']})")
            today_port = results['today_portfolio']
            st.markdown(f"""
            - **TQQQ**: {today_port['final_tqqq']:.1%}
            - **GLD**: {today_port['final_gld']:.1%}
            - **현금**: {today_port['final_cash']:.1%}
            """)
        
        with col3:
            st.markdown("### 🔄 포지션 변화")
            changes = results['portfolio_changes']
            
            # 변화 표시
            for asset, change, emoji in [
                ('TQQQ', changes['tqqq_change'], '📈' if changes['tqqq_change'] > 0 else '📉' if changes['tqqq_change'] < 0 else '➡️'),
                ('GLD', changes['gld_change'], '📈' if changes['gld_change'] > 0 else '📉' if changes['gld_change'] < 0 else '➡️'),
                ('현금', changes['cash_change'], '📈' if changes['cash_change'] > 0 else '📉' if changes['cash_change'] < 0 else '➡️')
            ]:
                if abs(change) > 0.01:
                    st.markdown(f"- **{asset}**: {emoji} {change:+.1%}")
                else:
                    st.markdown(f"- **{asset}**: ➡️ 변화없음")
        
        # 진행중인 전략 표시
        if analyzer.active_strategies['error_rate_buy'] or analyzer.active_strategies['optimized_sell']:
            st.markdown("---")
            st.subheader("🔄 진행중인 전략 현황")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if analyzer.active_strategies['error_rate_buy']:
                    st.markdown("### 📈 진행중인 오차율 매수 전략")
                    for strategy in analyzer.active_strategies['error_rate_buy']:
                        st.info(f"""
                        **{strategy['name']}**
                        - 매수일: {strategy['buy_date'].strftime('%Y-%m-%d')}
                        - 보유기간: {strategy['days_held']}/{strategy['holding_days']}일
                        - 남은일수: {strategy['days_remaining']}일
                        - 목표매도일: {strategy['target_sell_date']}
                        """)
                else:
                    st.markdown("### 📈 진행중인 오차율 매수 전략")
                    st.caption("진행중인 전략 없음")
            
            with col2:
                if analyzer.active_strategies['optimized_sell']:
                    st.markdown("### 📉 진행중인 최적화 매도 전략")
                    for strategy in analyzer.active_strategies['optimized_sell']:
                        st.warning(f"""
                        **{strategy['name']}**
                        - 매도일: {strategy['sell_date'].strftime('%Y-%m-%d')}
                        - 현금보유: {strategy['days_since_sell']}/{strategy['rebuy_days']}일
                        - 재매수까지: {strategy['days_until_rebuy']}일
                        - 목표재매수일: {strategy['target_rebuy_date']}
                        """)
                else:
                    st.markdown("### 📉 진행중인 최적화 매도 전략")
                    st.caption("진행중인 전략 없음")
        
        # 구체적 매매 액션
        if results['trading_actions']:
            st.markdown("---")
            st.subheader("🎯 실행할 매매")
            
            investment = st.number_input(
                "총 투자금 (원)",
                min_value=100000,
                max_value=100000000,
                value=1000000,
                step=100000,
                format="%d",
                key="action_investment"
            )
            
            for action in results['trading_actions']:
                if action['action'] == '매수':
                    amount_krw = investment * float(action['amount'].strip('%')) / 100
                    if action['asset'] == 'TQQQ':
                        shares = int(amount_krw / latest['TQQQ_Close'] / 1300)
                        st.success(f"""
                        ✅ **{action['asset']} 매수**
                        - 비중: {action['amount']}
                        - 금액: {amount_krw:,.0f}원 (약 {shares}주)
                        - 자금원: {action['source']}에서 전환
                        """)
                    else:
                        shares = int(amount_krw / latest['GLD_Close'] / 1300)
                        st.success(f"""
                        ✅ **{action['asset']} 매수**
                        - 비중: {action['amount']}
                        - 금액: {amount_krw:,.0f}원 (약 {shares}주)
                        - 자금원: {action['source']}에서 전환
                        """)
                else:  # 매도
                    amount_krw = investment * float(action['amount'].strip('%')) / 100
                    if action['asset'] == 'TQQQ':
                        shares = int(amount_krw / latest['TQQQ_Close'] / 1300)
                        st.warning(f"""
                        🔻 **{action['asset']} 매도**
                        - 비중: {action['amount']}
                        - 금액: {amount_krw:,.0f}원 (약 {shares}주)
                        - 전환: {action['destination']}로 이동
                        """)
                    else:
                        shares = int(amount_krw / latest['GLD_Close'] / 1300)
                        st.warning(f"""
                        🔻 **{action['asset']} 매도**
                        - 비중: {action['amount']}
                        - 금액: {amount_krw:,.0f}원 (약 {shares}주)
                        - 전환: {action['destination']}로 이동
                        """)
        else:
            st.info("📌 오늘은 포지션 변경 없음 (홀딩)")
        
        st.markdown("---")
        
        # TQQQ 차트 섹션 추가
        st.subheader("📈 TQQQ 차트 분석")
        tqqq_chart = analyzer.create_tqqq_chart(data)
        st.plotly_chart(tqqq_chart, use_container_width=True)
        
        # 종합 권장사항
        st.subheader("🎯 종합 투자 권장사항")
        
        col1, col2 = st.columns([1, 1])
        
        today_port = results['today_portfolio']
        
        with col1:
            # 포지션 차트 (현금 포함)
            fig = go.Figure(data=[
                go.Bar(name='TQQQ', x=['권장 포지션'], y=[today_port['final_tqqq']*100], 
                       marker_color='#00CC88', text=f"{today_port['final_tqqq']:.1%}",
                       textposition='inside'),
                go.Bar(name='GLD', x=['권장 포지션'], y=[today_port['final_gld']*100],
                       marker_color='#FFD700', text=f"{today_port['final_gld']:.1%}",
                       textposition='inside'),
                go.Bar(name='Cash', x=['권장 포지션'], y=[today_port['final_cash']*100],
                       marker_color='#87CEEB', text=f"{today_port['final_cash']:.1%}" if today_port['final_cash'] > 0.01 else "",
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
                format="%d",
                key="portfolio_investment"
            )
            
            tqqq_amount = investment * today_port['final_tqqq']
            gld_amount = investment * today_port['final_gld']
            cash_amount = investment * today_port['final_cash']
            
            st.info(f"""
            **TQQQ**: {tqqq_amount:,.0f}원 ({int(tqqq_amount/latest['TQQQ_Close']/1300) if tqqq_amount > 0 else 0}주)  
            **GLD**: {gld_amount:,.0f}원 ({int(gld_amount/latest['GLD_Close']/1300) if gld_amount > 0 else 0}주)
            **현금**: {cash_amount:,.0f}원
            """)
        
        # 포지션 계산 과정 (오차율 정보 추가)
        with st.expander("📊 포지션 계산 과정 상세"):
            # 오차율 정보 표시
            st.markdown("### 📊 현재 오차율 현황")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔻 오차율 매수 전략")
                error_rates = results['today_portfolio']['error_rates']
                for i, period in enumerate([20, 45, 151, 212]):
                    deviation = error_rates.get(period, 0)
                    threshold = analyzer.error_rate_strategies[f'TQQQ_Strategy_{i+1}']['deviation_threshold']
                    status = "🟢 매수신호" if deviation <= threshold else "🔴 대기중"
                    st.metric(
                        f"MA{period} 오차율",
                        f"{deviation:.1f}%",
                        f"기준: {threshold}%",
                        delta_color="normal" if deviation <= threshold else "off"
                    )
                    st.caption(status)
            
            with col2:
                st.markdown("#### 🔺 최적화 매도 전략")
                optimized_rates = results['today_portfolio']['optimized_error_rates']
                for i, period in enumerate([45, 151, 212]):
                    if period in optimized_rates:
                        current = optimized_rates[period]['current']
                        target = optimized_rates[period]['target']
                        status = "🔴 매도신호" if current >= target else "🟢 보유중"
                        st.metric(
                            f"MA{period} 오차율",
                            f"{current:.1f}%",
                            f"목표: {target}%",
                            delta_color="normal" if current >= target else "off"
                        )
                        st.caption(status)
            
            st.markdown("### 🔧 전략 활성화 현황")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **오차율 매수 전략:**
                - 신규 활성 신호: {results['active_error_count']}개
                - 진행중인 전략: {len(analyzer.active_strategies['error_rate_buy'])}개
                - 총 조정 비중: **+{today_port['error_adjustment']:.1%}** (GLD → TQQQ)
                """)
                
                if results['today_portfolio']['active_error_strategies']:
                    st.markdown("**활성화된 전략:**")
                    for strategy in results['today_portfolio']['active_error_strategies']:
                        st.markdown(f"- {strategy['name']}: 오차율 {strategy.get('deviation', 'N/A'):.1f}% ≤ {strategy.get('threshold', 'N/A')}%")
            
            with col2:
                st.markdown(f"""
                **최적화 매도 전략:**
                - 신규 매도 신호: {today_port['sell_strategies_count']}개
                - 진행중인 전략: {today_port['active_optimized_sell_count']}개
                - 총 조정 비중: **{today_port['optimized_adjustment']:.1%}** (TQQQ → 현금)
                - 비활성 전략: {results['disabled_strategies_count']}개
                """)
            
            st.markdown("### 🧮 최종 포지션 계산")
            st.markdown(f"""
            ```
            기본 TQQQ 비중: {today_port['base_tqqq']:.1%}
            + 오차율 매수 조정: +{today_port['error_adjustment']:.1%}
            + 최적화 매도 조정: {today_port['optimized_adjustment']:+.1%}
            ----------------------------------
            최종 TQQQ: {today_port['final_tqqq']:.1%}
            최종 GLD: {today_port['final_gld']:.1%}
            최종 현금: {today_port['final_cash']:.1%}
            ```
            """)
        
        # 투자 유의사항
        with st.expander("⚠️ 투자 유의사항"):
            st.warning("""
            **v2.2 주요 개선사항:**
            - 진행중인 전략 추적 시스템 추가
            - 최적화 전략 오차율 목표치 표시
            - 과거 전략 실행 결과 포트폴리오 반영
            - 실시간 전략 상태 모니터링

            **투자 원칙:**
            - 이 분석은 참고용이며 투자 권유가 아닙니다
            - 실제 투자 시 시장 뉴스와 경제 지표를 추가로 고려하세요
            - 분할 매수/매도를 통한 리스크 분산을 권장합니다
            - 정기적인 포트폴리오 리밸런싱이 필요합니다
            - 레버리지 ETF(TQQQ)는 높은 변동성을 가집니다
            
            **진행중인 전략 반영:**
            - 오차율 매수 전략: 보유기간 동안 지속적으로 TQQQ 비중 증가
            - 최적화 매도 전략: 재매수 기간 동안 지속적으로 현금 비중 증가
            - 전략 완료 시 자동으로 포트폴리오에서 제외
            """)

if __name__ == "__main__":
    main()
