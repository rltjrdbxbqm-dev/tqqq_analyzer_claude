import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# -----------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------
st.set_page_config(
    page_title="TQQQ Sniper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------
# 2. 프리미엄 CSS - 트레이딩 터미널 스타일
# -----------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #080b12;
        --bg-secondary: #0d1117;
        --bg-card: rgba(13, 17, 23, 0.8);
        --border: rgba(48, 54, 61, 0.6);
        --text-primary: #f0f6fc;
        --text-secondary: #8b949e;
        --text-muted: #484f58;
        --accent-cyan: #00d4ff;
        --accent-green: #00ff88;
        --accent-red: #ff4757;
        --accent-amber: #ffb800;
        --accent-purple: #a855f7;
        --glow-cyan: rgba(0, 212, 255, 0.15);
        --glow-green: rgba(0, 255, 136, 0.15);
        --glow-red: rgba(255, 71, 87, 0.15);
    }
    
    .stApp {
        background: var(--bg-primary);
        background-image: 
            radial-gradient(ellipse at 0% 0%, rgba(0, 212, 255, 0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 100% 100%, rgba(0, 255, 136, 0.03) 0%, transparent 50%);
        font-family: 'Outfit', sans-serif;
    }
    
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1400px;
    }
    
    /* 스크롤바 */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    
    /* 숨김 요소 */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    
    /* ========== 헤더 영역 ========== */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0 1.5rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.5rem;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .logo-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-green));
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 0 20px var(--glow-cyan);
    }
    
    .logo-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    
    .logo-version {
        font-size: 11px;
        color: var(--text-muted);
        font-weight: 400;
        margin-left: 8px;
    }
    
    .header-meta {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .data-timestamp {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: var(--text-secondary);
        font-family: 'JetBrains Mono', monospace;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-green);
        border-radius: 50%;
        animation: pulse 2s infinite;
        box-shadow: 0 0 8px var(--accent-green);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.9); }
    }
    
    /* ========== 히어로 카드 - 현재가 ========== */
    .hero-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    
    .hero-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    }
    
    .hero-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 24px;
    }
    
    .price-section {
        display: flex;
        align-items: baseline;
        gap: 16px;
    }
    
    .ticker-label {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 1px;
    }
    
    .current-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 52px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
        text-shadow: 0 0 40px var(--glow-cyan);
    }
    
    .price-change {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    .change-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 600;
    }
    
    .change-percent {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 500;
    }
    
    .change-up { color: var(--accent-green); }
    .change-down { color: var(--accent-red); }
    
    /* ========== 시그널 카드 ========== */
    .signal-card {
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .signal-card:hover {
        transform: translateY(-2px);
    }
    
    .signal-buy {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.12), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 255, 136, 0.3);
        box-shadow: 0 0 30px var(--glow-green);
    }
    
    .signal-sell {
        background: linear-gradient(135deg, rgba(255, 71, 87, 0.12), rgba(255, 71, 87, 0.05));
        border: 1px solid rgba(255, 71, 87, 0.3);
        box-shadow: 0 0 30px var(--glow-red);
    }
    
    .signal-hold {
        background: var(--bg-card);
        border: 1px solid var(--border);
    }
    
    .signal-icon {
        font-size: 36px;
        margin-bottom: 8px;
    }
    
    .signal-label {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    
    .signal-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 20px;
        font-weight: 700;
    }
    
    .signal-text-buy { color: var(--accent-green); }
    .signal-text-sell { color: var(--accent-red); }
    .signal-text-hold { color: var(--text-secondary); }
    
    .signal-detail {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 6px;
    }
    
    /* ========== 레짐 배지 ========== */
    .regime-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 100px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 600;
    }
    
    .regime-bullish {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
        color: var(--accent-green);
    }
    
    .regime-bearish {
        background: rgba(255, 71, 87, 0.1);
        border: 1px solid rgba(255, 71, 87, 0.3);
        color: var(--accent-red);
    }
    
    /* ========== 포트폴리오 게이지 ========== */
    .portfolio-section {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .section-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    .allocation-bar {
        height: 48px;
        background: var(--bg-secondary);
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        position: relative;
    }
    
    .alloc-tqqq {
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: width 0.5s ease;
        position: relative;
    }
    
    .alloc-cash {
        background: linear-gradient(90deg, #2d333b, #3d444d);
        height: 100%;
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .alloc-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        color: var(--bg-primary);
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    
    .alloc-label-cash {
        color: var(--text-secondary);
        text-shadow: none;
    }
    
    .allocation-details {
        display: flex;
        justify-content: space-between;
        margin-top: 16px;
    }
    
    .alloc-item {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .alloc-dot {
        width: 12px;
        height: 12px;
        border-radius: 4px;
    }
    
    .alloc-dot-tqqq {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-green));
    }
    
    .alloc-dot-cash {
        background: #3d444d;
    }
    
    .alloc-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    .alloc-name {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .alloc-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 700;
        color: var(--accent-cyan);
    }
    
    .alloc-value-cash {
        color: var(--text-secondary);
    }
    
    .alloc-change {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin-left: 8px;
    }
    
    /* ========== MA 신호 그리드 ========== */
    .ma-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    
    @media (max-width: 768px) {
        .ma-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    .ma-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: all 0.2s;
    }
    
    .ma-card:hover {
        border-color: var(--accent-cyan);
    }
    
    .ma-card-active {
        border-color: var(--accent-green);
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.05), transparent);
    }
    
    .ma-card-inactive {
        border-color: var(--accent-red);
        background: linear-gradient(135deg, rgba(255, 71, 87, 0.05), transparent);
    }
    
    .ma-card-disabled {
        opacity: 0.4;
    }
    
    .ma-period {
        font-family: 'JetBrains Mono', monospace;
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    
    .ma-status {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .ma-status-above { color: var(--accent-green); }
    .ma-status-below { color: var(--accent-red); }
    .ma-status-disabled { color: var(--text-muted); }
    
    .ma-deviation {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .ma-contrib {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--border);
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 600;
    }
    
    .ma-contrib-active { color: var(--accent-green); }
    .ma-contrib-zero { color: var(--text-muted); }
    
    /* ========== Stochastic 미터 ========== */
    .stoch-section {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    
    .stoch-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    
    .stoch-values {
        display: flex;
        gap: 24px;
    }
    
    .stoch-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .stoch-label {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-muted);
        letter-spacing: 1px;
    }
    
    .stoch-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 28px;
        font-weight: 700;
    }
    
    .stoch-k { color: var(--accent-cyan); }
    .stoch-d { color: var(--accent-amber); }
    
    .stoch-meter {
        flex: 1;
        max-width: 300px;
        height: 8px;
        background: var(--bg-secondary);
        border-radius: 4px;
        position: relative;
        overflow: visible;
    }
    
    .stoch-marker {
        position: absolute;
        top: -4px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        transform: translateX(-50%);
        box-shadow: 0 0 10px;
    }
    
    .stoch-marker-k {
        background: var(--accent-cyan);
        box-shadow: 0 0 10px var(--accent-cyan);
    }
    
    .stoch-marker-d {
        background: var(--accent-amber);
        box-shadow: 0 0 10px var(--accent-amber);
    }
    
    /* ========== 차트 영역 ========== */
    .chart-section {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* ========== 푸터 ========== */
    .footer {
        text-align: center;
        color: var(--text-muted);
        font-size: 11px;
        padding: 16px 0;
        border-top: 1px solid var(--border);
        margin-top: 8px;
    }
    
    /* ========== 버튼 오버라이드 ========== */
    .stButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        border-color: var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
        box-shadow: 0 0 15px var(--glow-cyan) !important;
    }
    
    /* 반응형 */
    @media (max-width: 640px) {
        .current-price { font-size: 36px; }
        .hero-content { flex-direction: column; align-items: flex-start; }
        .allocation-details { flex-direction: column; gap: 12px; }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# 3. 분석기 클래스
# -----------------------------------------------------------
class TQQQAnalyzer:
    def __init__(self):
        self.stoch_config = {'period': 166, 'k_period': 57, 'd_period': 19}
        self.ma_periods = [20, 45, 151, 212]

    @st.cache_data(ttl=300)
    def get_data(_self, days_back=400):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        try:
            ticker = yf.Ticker('TQQQ')
            data = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            if data.empty:
                return None
            df = pd.DataFrame({
                'Open': data['Open'],
                'High': data['High'],
                'Low': data['Low'],
                'Close': data['Close']
            })
            return df.dropna()
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return None

    def calculate_indicators(self, data):
        df = data.copy()
        p, k, d = self.stoch_config.values()
        
        df['HH'] = df['High'].rolling(window=p).max()
        df['LL'] = df['Low'].rolling(window=p).min()
        df['%K'] = ((df['Close'] - df['LL']) / (df['HH'] - df['LL']) * 100).rolling(window=k).mean()
        df['%D'] = df['%K'].rolling(window=d).mean()
        
        for ma in self.ma_periods:
            df[f'MA{ma}'] = df['Close'].rolling(window=ma).mean()
            df[f'Dev{ma}'] = ((df['Close'] - df[f'MA{ma}']) / df[f'MA{ma}']) * 100
        
        return df.dropna()

    def analyze(self, data):
        curr = data.iloc[-1]
        prev = data.iloc[-2]
        
        is_bullish = curr['%K'] > curr['%D']
        ma_signals = {p: curr['Close'] > curr[f'MA{p}'] for p in self.ma_periods}
        
        if is_bullish:
            tqqq_ratio = sum(ma_signals.values()) * 0.25
        else:
            tqqq_ratio = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5
        
        cash_ratio = 1 - tqqq_ratio
        
        # 전일 비중
        prev_bullish = prev['%K'] > prev['%D']
        prev_ma = {p: prev['Close'] > prev[f'MA{p}'] for p in self.ma_periods}
        if prev_bullish:
            prev_tqqq = sum(prev_ma.values()) * 0.25
        else:
            prev_tqqq = (int(prev_ma[20]) + int(prev_ma[45])) * 0.5
        
        change = tqqq_ratio - prev_tqqq
        
        return {
            'price': curr['Close'],
            'prev_price': prev['Close'],
            'price_change': curr['Close'] - prev['Close'],
            'price_change_pct': (curr['Close'] - prev['Close']) / prev['Close'] * 100,
            'tqqq': tqqq_ratio,
            'cash': cash_ratio,
            'prev_tqqq': prev_tqqq,
            'change': change,
            'is_bullish': is_bullish,
            'ma_signals': ma_signals,
            'stoch_k': curr['%K'],
            'stoch_d': curr['%D'],
            'deviations': {p: curr[f'Dev{p}'] for p in self.ma_periods},
            'ma_values': {p: curr[f'MA{p}'] for p in self.ma_periods},
            'date': curr.name
        }

# -----------------------------------------------------------
# 4. 메인 앱
# -----------------------------------------------------------
def main():
    analyzer = TQQQAnalyzer()
    data = analyzer.get_data()
    
    if data is None:
        st.error("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return
    
    data = analyzer.calculate_indicators(data)
    result = analyzer.analyze(data)
    
    # ===== 헤더 =====
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    date_str = result['date'].strftime('%Y.%m.%d')
    day_str = day_names[result['date'].weekday()]
    
    st.markdown(f"""
    <div class="header-container">
        <div class="logo-section">
            <div class="logo-icon">⚡</div>
            <div>
                <span class="logo-text">TQQQ SNIPER</span>
                <span class="logo-version">v6.0</span>
            </div>
        </div>
        <div class="header-meta">
            <div class="data-timestamp">
                <div class="live-dot"></div>
                {date_str} ({day_str}) 장마감
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 히어로 - 현재가 & 시그널 =====
    price_up = result['price_change'] >= 0
    change_class = 'change-up' if price_up else 'change-down'
    change_sign = '+' if price_up else ''
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        regime_class = 'regime-bullish' if result['is_bullish'] else 'regime-bearish'
        regime_icon = '📈' if result['is_bullish'] else '📉'
        regime_text = 'BULLISH' if result['is_bullish'] else 'BEARISH'
        
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-content">
                <div>
                    <div class="ticker-label">TQQQ</div>
                    <div class="price-section">
                        <div class="current-price">${result['price']:.2f}</div>
                        <div class="price-change">
                            <div class="change-value {change_class}">{change_sign}${abs(result['price_change']):.2f}</div>
                            <div class="change-percent {change_class}">{change_sign}{result['price_change_pct']:.2f}%</div>
                        </div>
                    </div>
                </div>
                <div class="regime-badge {regime_class}">
                    {regime_icon} {regime_text} REGIME
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # 시그널 카드
        if result['change'] > 0.01:
            signal_class = 'signal-buy'
            signal_icon = '🚀'
            signal_text = f"TQQQ {result['change']:.0%} 매수"
            signal_text_class = 'signal-text-buy'
            signal_detail = f"비중 {result['prev_tqqq']:.0%} → {result['tqqq']:.0%}"
        elif result['change'] < -0.01:
            signal_class = 'signal-sell'
            signal_icon = '⚠️'
            signal_text = f"TQQQ {abs(result['change']):.0%} 매도"
            signal_text_class = 'signal-text-sell'
            signal_detail = f"비중 {result['prev_tqqq']:.0%} → {result['tqqq']:.0%}"
        else:
            signal_class = 'signal-hold'
            signal_icon = '☕'
            signal_text = "HOLD"
            signal_text_class = 'signal-text-hold'
            signal_detail = "변동 없음"
        
        st.markdown(f"""
        <div class="signal-card {signal_class}">
            <div class="signal-icon">{signal_icon}</div>
            <div class="signal-label">TODAY'S ACTION</div>
            <div class="signal-text {signal_text_class}">{signal_text}</div>
            <div class="signal-detail">{signal_detail}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== 포트폴리오 배분 =====
    tqqq_pct = result['tqqq'] * 100
    cash_pct = result['cash'] * 100
    change_sign = '+' if result['change'] >= 0 else ''
    change_class = 'change-up' if result['change'] >= 0 else 'change-down'
    
    st.markdown(f"""
    <div class="portfolio-section">
        <div class="section-header">
            <div class="section-title">📊 PORTFOLIO ALLOCATION</div>
        </div>
        <div class="allocation-bar">
            <div class="alloc-tqqq" style="width: {tqqq_pct}%;">
                <span class="alloc-label">TQQQ {result['tqqq']:.0%}</span>
            </div>
            <div class="alloc-cash">
                <span class="alloc-label alloc-label-cash">CASH {result['cash']:.0%}</span>
            </div>
        </div>
        <div class="allocation-details">
            <div class="alloc-item">
                <div class="alloc-dot alloc-dot-tqqq"></div>
                <div class="alloc-info">
                    <div class="alloc-name">TQQQ</div>
                    <div>
                        <span class="alloc-value">{result['tqqq']:.0%}</span>
                        <span class="alloc-change {change_class}">{change_sign}{result['change']:.0%}</span>
                    </div>
                </div>
            </div>
            <div class="alloc-item">
                <div class="alloc-dot alloc-dot-cash"></div>
                <div class="alloc-info">
                    <div class="alloc-name">CASH</div>
                    <div>
                        <span class="alloc-value alloc-value-cash">{result['cash']:.0%}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== MA 신호 그리드 =====
    st.markdown('<div class="section-title" style="margin-bottom: 12px;">📡 MA SIGNALS</div>', unsafe_allow_html=True)
    
    ma_html = '<div class="ma-grid">'
    for ma in analyzer.ma_periods:
        is_above = result['ma_signals'][ma]
        dev = result['deviations'][ma]
        
        # 비중 기여도 계산
        if result['is_bullish']:
            contrib = 25 if is_above else 0
            is_active = True
        else:
            if ma in [20, 45]:
                contrib = 50 if is_above else 0
                is_active = True
            else:
                contrib = 0
                is_active = False
        
        # 카드 클래스
        if not is_active:
            card_class = 'ma-card-disabled'
            status_class = 'ma-status-disabled'
            status_text = 'N/A'
        elif is_above:
            card_class = 'ma-card-active'
            status_class = 'ma-status-above'
            status_text = '▲ ABOVE'
        else:
            card_class = 'ma-card-inactive'
            status_class = 'ma-status-below'
            status_text = '▼ BELOW'
        
        contrib_class = 'ma-contrib-active' if contrib > 0 else 'ma-contrib-zero'
        contrib_text = f'+{contrib}%' if contrib > 0 else '—'
        
        ma_html += f"""
        <div class="ma-card {card_class}">
            <div class="ma-period">{ma}</div>
            <div class="ma-status {status_class}">{status_text}</div>
            <div class="ma-deviation">{dev:+.1f}%</div>
            <div class="ma-contrib {contrib_class}">{contrib_text}</div>
        </div>
        """
    ma_html += '</div>'
    st.markdown(ma_html, unsafe_allow_html=True)
    
    # ===== Stochastic =====
    st.markdown(f"""
    <div class="stoch-section">
        <div class="stoch-content">
            <div class="stoch-values">
                <div class="stoch-item">
                    <div class="stoch-label">%K</div>
                    <div class="stoch-value stoch-k">{result['stoch_k']:.1f}</div>
                </div>
                <div class="stoch-item">
                    <div class="stoch-label">%D</div>
                    <div class="stoch-value stoch-d">{result['stoch_d']:.1f}</div>
                </div>
            </div>
            <div class="stoch-meter">
                <div class="stoch-marker stoch-marker-d" style="left: {result['stoch_d']}%;"></div>
                <div class="stoch-marker stoch-marker-k" style="left: {result['stoch_k']}%;"></div>
            </div>
            <div class="regime-badge {'regime-bullish' if result['is_bullish'] else 'regime-bearish'}">
                {'%K > %D' if result['is_bullish'] else '%K < %D'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 차트 =====
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    
    chart_data = data.iloc[-100:]
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=('', '')
    )
    
    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=chart_data.index,
        open=chart_data['Open'],
        high=chart_data['High'],
        low=chart_data['Low'],
        close=chart_data['Close'],
        name='TQQQ',
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff4757',
        increasing_fillcolor='rgba(0, 255, 136, 0.8)',
        decreasing_fillcolor='rgba(255, 71, 87, 0.8)'
    ), row=1, col=1)
    
    # 이동평균선
    ma_colors = ['#ffb800', '#00d4ff', '#a855f7', '#ff6b9d']
    for i, ma in enumerate(analyzer.ma_periods):
        fig.add_trace(go.Scatter(
            x=chart_data.index,
            y=chart_data[f'MA{ma}'],
            name=f'MA{ma}',
            line=dict(color=ma_colors[i], width=1.5),
            opacity=0.85
        ), row=1, col=1)
    
    # Stochastic
    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=chart_data['%K'],
        name='%K',
        line=dict(color='#00d4ff', width=2)
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=chart_data['%D'],
        name='%D',
        line=dict(color='#ffb800', width=2)
    ), row=2, col=1)
    
    # 레이아웃
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=10, b=0),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(13, 17, 23, 0.5)',
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11)
        ),
        font=dict(family='JetBrains Mono, monospace', color='#8b949e', size=11)
    )
    
    fig.update_xaxes(gridcolor='rgba(48, 54, 61, 0.4)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(48, 54, 61, 0.4)', showgrid=True)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== 푸터 =====
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("""
    <div class="footer">
        TQQQ Sniper v6.0 · Strategy 3 Basic + Cash Defense · Not Financial Advice
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
