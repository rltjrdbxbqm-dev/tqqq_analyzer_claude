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
    page_title="TQQQ Sniper v5.1",
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
    
    .portfolio-card-cash:hover {
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
    
    .portfolio-value-cash {
        color: #f59e0b;
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
    
    .progress-cash {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
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
    """실시간 투자 신호 분석기 - v5.1 (기본 전략 Only, Cash 방어)"""

    def __init__(self):
        self.stoch_config = {'period': 166, 'k_period': 57, 'd_period': 19}
        self.ma_periods = [20, 45, 151, 212]

    @st.cache_data(ttl=300)
    def get_latest_data(_self, days_back=400):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        try:
            # TQQQ만 다운로드 (Cash는 가격 데이터 불필요)
            ticker = yf.Ticker('TQQQ')
            stock_data = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if stock_data.empty:
                st.error("TQQQ 데이터를 가져올 수 없습니다.")
                return None
            
            # 컬럼명 정리
            combined_data = pd.DataFrame()
            combined_data['TQQQ_Open'] = stock_data['Open']
            combined_data['TQQQ_High'] = stock_data['High']
            combined_data['TQQQ_Low'] = stock_data['Low']
            combined_data['TQQQ_Close'] = stock_data['Close']
            
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

    def analyze_portfolio(self, data):
        target_data = data.iloc[-1]
        
        is_bullish = target_data['%K'] > target_data['%D']
        ma_signals = {p: target_data['TQQQ_Close'] > target_data[f'MA_{p}'] for p in self.ma_periods}
        
        if is_bullish: 
            base_tqqq = sum(ma_signals.values()) * 0.25
        else: 
            base_tqqq = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5
        
        base_cash = 1 - base_tqqq
            
        return {
            'final_tqqq': base_tqqq, 
            'final_cash': base_cash,
            'is_bullish': is_bullish,
            'ma_signals': ma_signals
        }

    def analyze_all(self, data):
        today = self.analyze_portfolio(data)
        data_prev = data.iloc[:-1]
        yesterday = self.analyze_portfolio(data_prev)
        
        changes = {
            'tqqq': today['final_tqqq'] - yesterday['final_tqqq'], 
            'cash': today['final_cash'] - yesterday['final_cash']
        }
        
        actions = []
        tqqq_chg = changes['tqqq']
        if tqqq_chg > 0.01: 
            actions.append({'action': '매수', 'asset': 'TQQQ', 'amt': tqqq_chg})
        elif tqqq_chg < -0.01: 
            actions.append({'action': '매도', 'asset': 'TQQQ', 'amt': abs(tqqq_chg)})
        
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
        'CASH': {'value': 'portfolio-value-cash', 'progress': 'progress-cash', 'hover': 'portfolio-card-cash'},
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


def render_base_strategy_card(ma, latest, is_bullish, ma_periods):
    """기본 전략 카드 렌더링"""
    price = latest['TQQQ_Close']
    ma_value = latest[f'MA_{ma}']
    deviation = latest[f'Deviation_{ma}']
    is_above = price > ma_value
    
    # 상승장: 모든 MA 25%씩 기여
    # 하락장: MA20, MA45만 50%씩 기여
    if is_bullish:
        contribution = 0.25 if is_above else 0
        is_active_in_regime = True
    else:
        if ma in [20, 45]:
            contribution = 0.5 if is_above else 0
            is_active_in_regime = True
        else:
            contribution = 0
            is_active_in_regime = False
    
    # 스타일 결정
    if not is_active_in_regime:
        icon_bg = "rgba(71, 85, 105, 0.2)"
        icon_color = "#475569"
        status_text = "🚫 하락장 미적용"
        status_color = "#475569"
        prog_color = "linear-gradient(90deg, #334155, #475569)"
    elif is_above:
        icon_bg = "rgba(16, 185, 129, 0.2)"
        icon_color = "#10b981"
        status_text = f"✅ MA 상회 (+{deviation:.1f}%)"
        status_color = "#10b981"
        prog_color = "linear-gradient(90deg, #10b981, #06b6d4)"
    else:
        icon_bg = "rgba(239, 68, 68, 0.2)"
        icon_color = "#ef4444"
        status_text = f"❌ MA 하회 ({deviation:.1f}%)"
        status_color = "#ef4444"
        prog_color = "linear-gradient(90deg, #475569, #64748b)"
    
    # 비중 기여도 텍스트
    if not is_active_in_regime:
        contrib_text = "—"
        contrib_color = "#475569"
    elif contribution > 0:
        contrib_text = f"+{contribution:.0%}"
        contrib_color = "#10b981"
    else:
        contrib_text = "0%"
        contrib_color = "#64748b"
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            st.markdown(f"""
            <div style="width: 45px; height: 45px; background: {icon_bg}; 
                        border-radius: 10px; display: flex; align-items: center; justify-content: center; 
                        font-size: 14px; font-weight: 700; color: {icon_color}; 
                        font-family: 'JetBrains Mono', monospace;">{ma}</div>
            """, unsafe_allow_html=True)
        
        with col2:
            regime_note = ""
            if is_bullish:
                regime_note = "(25%)"
            else:
                regime_note = "(50%)" if ma in [20, 45] else ""
            st.markdown(f"""
            <div style="font-weight: 600; color: #e2e8f0; font-size: 14px; margin-bottom: 2px;">MA{ma} <span style="color: #64748b; font-size: 11px;">{regime_note}</span></div>
            <div style="color: {status_color}; font-size: 12px;">{status_text}</div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 2px;">TQQQ 비중 기여</div>
                <div style="font-size: 18px; font-weight: 700; color: {contrib_color}; font-family: 'JetBrains Mono', monospace;">{contrib_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 프로그레스 바 (MA 대비 가격 위치 시각화)
        # 0% = MA 대비 -30%, 100% = MA 대비 +30%
        normalized = (deviation + 30) / 60 * 100
        normalized = max(0, min(100, normalized))
        
        st.markdown(f"""
        <div style="position: relative; height: 6px; background: rgba(51, 65, 85, 0.5); border-radius: 3px; overflow: visible; margin: 8px 0;">
            <div style="position: absolute; left: 50%; top: 0; width: 1px; height: 6px; background: #64748b;"></div>
            <div style="height: 100%; width: {normalized}%; background: {prog_color}; border-radius: 3px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # 가격 정보
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; color: #64748b; font-size: 11px; font-family: 'JetBrains Mono', monospace;">
            <span>현재가: ${price:.2f}</span>
            <span>MA{ma}: ${ma_value:.2f}</span>
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
                    <span class="header-version">v5.1</span>
                </div>
                <div class="header-subtitle">Strategy 3 Basic + Cash Defense</div>
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
        
        col1, col2 = st.columns(2)
        with col1:
            render_portfolio_card('TQQQ', res_today['final_tqqq'], changes['tqqq'], res_prev['final_tqqq'])
        with col2:
            render_portfolio_card('CASH', res_today['final_cash'], changes['cash'], res_prev['final_cash'])
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # 전략 모니터
        st.markdown("""
        <div class="section-title">
            <span>📡</span> STRATEGY MONITOR
        </div>
        """, unsafe_allow_html=True)
        
        # 기본 전략 요약
        regime_icon = "📈" if res_today['is_bullish'] else "📉"
        regime_label = "상승장" if res_today['is_bullish'] else "하락장"
        regime_desc = "4개 MA 각 25%" if res_today['is_bullish'] else "MA20, MA45 각 50%"
        
        st.markdown(f"""
        <div style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 10px;
                    background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); color: #a78bfa;
                    margin-bottom: 16px; font-size: 12px;">
            {regime_icon} 현재 레짐: <span style="font-weight: 700; font-family: 'JetBrains Mono', monospace;">{regime_label}</span> · {regime_desc}
        </div>
        """, unsafe_allow_html=True)
        
        # 기본 TQQQ 비중 표시
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; 
                    background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.2); 
                    border-radius: 10px; margin-bottom: 16px;">
            <span style="color: #94a3b8; font-size: 13px;">기본 전략 TQQQ 비중</span>
            <span style="color: #06b6d4; font-size: 20px; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{res_today['final_tqqq']:.0%}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 각 MA별 상태
        for ma in analyzer.ma_periods:
            render_base_strategy_card(ma, latest, res_today['is_bullish'], analyzer.ma_periods)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # 차트
        st.markdown("""
        <div class="section-title">
            <span>📊</span> PRICE CHART
        </div>
        """, unsafe_allow_html=True)
        
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
            height=450,
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
            Strategy 3 Basic + Cash Defense • Built with precision • Not financial advice
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
