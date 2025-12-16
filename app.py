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
# 페이지 설정
# -----------------------------------------------------------
st.set_page_config(
    page_title="TQQQ Sniper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------
# CSS 스타일 (모바일 최적화)
# -----------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #080b12;
        --bg-card: rgba(13, 17, 23, 0.9);
        --border: rgba(48, 54, 61, 0.6);
        --text-primary: #f0f6fc;
        --text-secondary: #8b949e;
        --text-muted: #484f58;
        --accent-cyan: #00d4ff;
        --accent-green: #00ff88;
        --accent-red: #ff4757;
        --accent-amber: #ffb800;
    }
    
    .stApp {
        background: var(--bg-primary);
        font-family: 'Outfit', sans-serif;
    }
    
    .main .block-container {
        padding: 1rem 1rem;
        max-width: 100%;
    }
    
    /* 숨김 요소 */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    
    /* 헤더 */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 16px;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .logo-area {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-green));
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    .logo-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .date-info {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-green);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    
    /* 가격 카드 */
    .price-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 212, 255, 0.25);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
    }
    
    .ticker-name {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 4px;
    }
    
    .price-row {
        display: flex;
        align-items: baseline;
        gap: 12px;
        flex-wrap: wrap;
    }
    
    .main-price {
        font-family: 'JetBrains Mono', monospace;
        font-size: 42px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .price-change {
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 600;
    }
    
    .up { color: var(--accent-green); }
    .down { color: var(--accent-red); }
    
    .regime-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        margin-top: 12px;
    }
    
    .regime-bull {
        background: rgba(0, 255, 136, 0.15);
        border: 1px solid rgba(0, 255, 136, 0.3);
        color: var(--accent-green);
    }
    
    .regime-bear {
        background: rgba(255, 71, 87, 0.15);
        border: 1px solid rgba(255, 71, 87, 0.3);
        color: var(--accent-red);
    }
    
    /* 시그널 카드 */
    .signal-card {
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 12px;
    }
    
    .signal-buy {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.15), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 255, 136, 0.3);
    }
    
    .signal-sell {
        background: linear-gradient(135deg, rgba(255, 71, 87, 0.15), rgba(255, 71, 87, 0.05));
        border: 1px solid rgba(255, 71, 87, 0.3);
    }
    
    .signal-hold {
        background: var(--bg-card);
        border: 1px solid var(--border);
    }
    
    .signal-icon {
        font-size: 32px;
        margin-bottom: 6px;
    }
    
    .signal-label {
        font-size: 10px;
        color: var(--text-muted);
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    
    .signal-action {
        font-family: 'JetBrains Mono', monospace;
        font-size: 18px;
        font-weight: 700;
    }
    
    .signal-action.buy { color: var(--accent-green); }
    .signal-action.sell { color: var(--accent-red); }
    .signal-action.hold { color: var(--text-secondary); }
    
    .signal-detail {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
    }
    
    /* 포트폴리오 */
    .portfolio-section {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .section-label {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-muted);
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    
    .alloc-bar {
        height: 40px;
        background: #1a1f26;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        margin-bottom: 12px;
    }
    
    .alloc-tqqq {
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        color: #080b12;
        transition: width 0.3s;
    }
    
    .alloc-cash {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-secondary);
    }
    
    .alloc-details {
        display: flex;
        justify-content: space-between;
    }
    
    .alloc-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .alloc-dot {
        width: 10px;
        height: 10px;
        border-radius: 3px;
    }
    
    .dot-tqqq { background: linear-gradient(135deg, var(--accent-cyan), var(--accent-green)); }
    .dot-cash { background: #3d444d; }
    
    .alloc-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .alloc-change {
        font-size: 12px;
        margin-left: 4px;
    }
    
    /* MA 카드 */
    .ma-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px;
        text-align: center;
        height: 100%;
    }
    
    .ma-card.active {
        border-color: rgba(0, 255, 136, 0.4);
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.08), transparent);
    }
    
    .ma-card.inactive {
        border-color: rgba(255, 71, 87, 0.4);
        background: linear-gradient(135deg, rgba(255, 71, 87, 0.08), transparent);
    }
    
    .ma-card.disabled {
        opacity: 0.4;
    }
    
    .ma-period {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .ma-status {
        font-size: 10px;
        font-weight: 600;
        margin: 4px 0;
    }
    
    .ma-status.above { color: var(--accent-green); }
    .ma-status.below { color: var(--accent-red); }
    .ma-status.na { color: var(--text-muted); }
    
    .ma-dev {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: var(--text-secondary);
    }
    
    .ma-contrib {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 600;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--border);
    }
    
    .ma-contrib.positive { color: var(--accent-green); }
    .ma-contrib.zero { color: var(--text-muted); }
    
    /* Stochastic */
    .stoch-section {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .stoch-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    
    .stoch-values {
        display: flex;
        gap: 20px;
    }
    
    .stoch-item {
        text-align: center;
    }
    
    .stoch-label {
        font-size: 10px;
        color: var(--text-muted);
        margin-bottom: 2px;
    }
    
    .stoch-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 24px;
        font-weight: 700;
    }
    
    .stoch-k { color: var(--accent-cyan); }
    .stoch-d { color: var(--accent-amber); }
    
    /* 차트 */
    .chart-container {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 12px;
        margin-bottom: 12px;
    }
    
    /* 푸터 */
    .app-footer {
        text-align: center;
        color: var(--text-muted);
        font-size: 10px;
        padding: 12px 0;
        border-top: 1px solid var(--border);
    }
    
    /* 버튼 */
    .stButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        border-color: var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# 분석기 클래스
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
# 메인 앱
# -----------------------------------------------------------
def main():
    analyzer = TQQQAnalyzer()
    data = analyzer.get_data()
    
    if data is None:
        st.error("데이터를 불러올 수 없습니다.")
        return
    
    data = analyzer.calculate_indicators(data)
    r = analyzer.analyze(data)
    
    # 날짜 정보
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    date_str = r['date'].strftime('%Y.%m.%d')
    day_str = day_names[r['date'].weekday()]
    
    # ===== 헤더 =====
    st.markdown(f"""
    <div class="app-header">
        <div class="logo-area">
            <div class="logo-icon">⚡</div>
            <span class="logo-text">TQQQ SNIPER</span>
        </div>
        <div class="date-info">
            <div class="live-dot"></div>
            {date_str} ({day_str})
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 가격 카드 =====
    price_up = r['price_change'] >= 0
    change_class = 'up' if price_up else 'down'
    change_sign = '+' if price_up else ''
    regime_class = 'regime-bull' if r['is_bullish'] else 'regime-bear'
    regime_text = '📈 BULLISH' if r['is_bullish'] else '📉 BEARISH'
    
    st.markdown(f"""
    <div class="price-card">
        <div class="ticker-name">TQQQ</div>
        <div class="price-row">
            <span class="main-price">${r['price']:.2f}</span>
            <span class="price-change {change_class}">{change_sign}${abs(r['price_change']):.2f} ({change_sign}{r['price_change_pct']:.2f}%)</span>
        </div>
        <div class="regime-pill {regime_class}">{regime_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 시그널 카드 =====
    if r['change'] > 0.01:
        sig_class, sig_icon = 'signal-buy', '🚀'
        sig_text = f"TQQQ {r['change']:.0%} 매수"
        sig_action_class = 'buy'
    elif r['change'] < -0.01:
        sig_class, sig_icon = 'signal-sell', '⚠️'
        sig_text = f"TQQQ {abs(r['change']):.0%} 매도"
        sig_action_class = 'sell'
    else:
        sig_class, sig_icon = 'signal-hold', '☕'
        sig_text = "HOLD"
        sig_action_class = 'hold'
    
    sig_detail = f"비중 {r['prev_tqqq']:.0%} → {r['tqqq']:.0%}"
    
    st.markdown(f"""
    <div class="signal-card {sig_class}">
        <div class="signal-icon">{sig_icon}</div>
        <div class="signal-label">TODAY'S ACTION</div>
        <div class="signal-action {sig_action_class}">{sig_text}</div>
        <div class="signal-detail">{sig_detail}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 포트폴리오 =====
    tqqq_pct = r['tqqq'] * 100
    change_sign = '+' if r['change'] >= 0 else ''
    change_class = 'up' if r['change'] >= 0 else 'down'
    
    st.markdown(f"""
    <div class="portfolio-section">
        <div class="section-label">📊 PORTFOLIO ALLOCATION</div>
        <div class="alloc-bar">
            <div class="alloc-tqqq" style="width: {max(tqqq_pct, 5)}%;">{'TQQQ ' + str(int(r['tqqq']*100)) + '%' if tqqq_pct >= 15 else ''}</div>
            <div class="alloc-cash">CASH {int(r['cash']*100)}%</div>
        </div>
        <div class="alloc-details">
            <div class="alloc-item">
                <div class="alloc-dot dot-tqqq"></div>
                <span class="alloc-text">TQQQ {r['tqqq']:.0%}</span>
                <span class="alloc-change {change_class}">{change_sign}{r['change']:.0%}</span>
            </div>
            <div class="alloc-item">
                <div class="alloc-dot dot-cash"></div>
                <span class="alloc-text">CASH {r['cash']:.0%}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== MA Signals (Streamlit 네이티브 컴포넌트 사용) =====
    st.markdown('<div class="section-label" style="margin: 16px 0 8px 0;">📡 MA SIGNALS</div>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    for i, ma in enumerate(analyzer.ma_periods):
        is_above = r['ma_signals'][ma]
        dev = r['deviations'][ma]
        
        # 비중 기여도 계산
        if r['is_bullish']:
            contrib = 25 if is_above else 0
            is_active = True
        else:
            if ma in [20, 45]:
                contrib = 50 if is_above else 0
                is_active = True
            else:
                contrib = 0
                is_active = False
        
        # 카드 스타일
        if not is_active:
            card_class = 'disabled'
            status_class = 'na'
            status_text = 'N/A'
        elif is_above:
            card_class = 'active'
            status_class = 'above'
            status_text = '▲ ABOVE'
        else:
            card_class = 'inactive'
            status_class = 'below'
            status_text = '▼ BELOW'
        
        contrib_class = 'positive' if contrib > 0 else 'zero'
        contrib_text = f'+{contrib}%' if contrib > 0 else '—'
        
        with cols[i]:
            st.markdown(f"""
            <div class="ma-card {card_class}">
                <div class="ma-period">{ma}</div>
                <div class="ma-status {status_class}">{status_text}</div>
                <div class="ma-dev">{dev:+.1f}%</div>
                <div class="ma-contrib {contrib_class}">{contrib_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ===== Stochastic =====
    st.markdown(f"""
    <div class="stoch-section">
        <div class="section-label">📊 STOCHASTIC (166, 57, 19)</div>
        <div class="stoch-row">
            <div class="stoch-values">
                <div class="stoch-item">
                    <div class="stoch-label">%K</div>
                    <div class="stoch-val stoch-k">{r['stoch_k']:.1f}</div>
                </div>
                <div class="stoch-item">
                    <div class="stoch-label">%D</div>
                    <div class="stoch-val stoch-d">{r['stoch_d']:.1f}</div>
                </div>
            </div>
            <div class="regime-pill {'regime-bull' if r['is_bullish'] else 'regime-bear'}">
                {'%K > %D' if r['is_bullish'] else '%K < %D'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== 차트 =====
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    chart_data = data.iloc[-80:]
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3]
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
        increasing_fillcolor='#00ff88',
        decreasing_fillcolor='#ff4757'
    ), row=1, col=1)
    
    # 이동평균선
    ma_colors = ['#ffb800', '#00d4ff', '#a855f7', '#ff6b9d']
    for i, ma in enumerate(analyzer.ma_periods):
        fig.add_trace(go.Scatter(
            x=chart_data.index,
            y=chart_data[f'MA{ma}'],
            name=f'MA{ma}',
            line=dict(color=ma_colors[i], width=1.5),
            opacity=0.9
        ), row=1, col=1)
    
    # Stochastic
    fig.add_trace(go.Scatter(
        x=chart_data.index, y=chart_data['%K'],
        name='%K', line=dict(color='#00d4ff', width=1.5)
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=chart_data.index, y=chart_data['%D'],
        name='%D', line=dict(color='#ffb800', width=1.5)
    ), row=2, col=1)
    
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=0, b=0),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(13, 17, 23, 0.5)',
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=10)
        ),
        font=dict(family='JetBrains Mono', color='#8b949e', size=10)
    )
    
    fig.update_xaxes(gridcolor='rgba(48, 54, 61, 0.3)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(48, 54, 61, 0.3)', showgrid=True)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== 새로고침 버튼 =====
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()
    
    # ===== 푸터 =====
    st.markdown("""
    <div class="app-footer">
        TQQQ Sniper v6.1 · Strategy 3 Basic + Cash · Not Financial Advice
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
