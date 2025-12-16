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
# CSS - 모바일 우선 컴팩트 디자인
# -----------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    :root {
        --bg: #0a0e14;
        --card: #12171f;
        --border: #1e2530;
        --text: #e6edf3;
        --text2: #7d8590;
        --text3: #484f58;
        --cyan: #00d4ff;
        --green: #3fb950;
        --red: #f85149;
        --amber: #d29922;
    }
    
    * { box-sizing: border-box; }
    
    .stApp {
        background: var(--bg);
        font-family: 'JetBrains Mono', monospace;
    }
    
    .main .block-container {
        padding: 0.75rem;
        max-width: 100%;
    }
    
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    
    /* 헤더 - 한 줄로 */
    .hdr {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        margin-bottom: 10px;
        border-bottom: 1px solid var(--border);
    }
    .hdr-left {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .hdr-icon {
        width: 32px; height: 32px;
        background: linear-gradient(135deg, var(--cyan), var(--green));
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px;
    }
    .hdr-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--cyan);
    }
    .hdr-date {
        font-size: 11px;
        color: var(--text2);
    }
    
    /* 메인 그리드: 가격 + 시그널 */
    .top-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 10px;
    }
    
    /* 가격 카드 */
    .price-box {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px;
    }
    .price-label {
        font-size: 10px;
        color: var(--text3);
        margin-bottom: 2px;
    }
    .price-main {
        font-size: 28px;
        font-weight: 700;
        color: var(--text);
        line-height: 1.1;
    }
    .price-change {
        font-size: 13px;
        font-weight: 600;
        margin-top: 2px;
    }
    .up { color: var(--green); }
    .down { color: var(--red); }
    .regime-tag {
        display: inline-block;
        font-size: 9px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        margin-top: 8px;
    }
    .regime-bull { background: rgba(63,185,80,0.15); color: var(--green); }
    .regime-bear { background: rgba(248,81,73,0.15); color: var(--red); }
    
    /* 시그널 카드 */
    .signal-box {
        border-radius: 12px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .sig-buy { background: linear-gradient(135deg, rgba(63,185,80,0.2), rgba(63,185,80,0.05)); border: 1px solid rgba(63,185,80,0.3); }
    .sig-sell { background: linear-gradient(135deg, rgba(248,81,73,0.2), rgba(248,81,73,0.05)); border: 1px solid rgba(248,81,73,0.3); }
    .sig-hold { background: var(--card); border: 1px solid var(--border); }
    .sig-icon { font-size: 24px; }
    .sig-label { font-size: 9px; color: var(--text3); margin: 4px 0 2px 0; }
    .sig-action { font-size: 15px; font-weight: 700; }
    .sig-action.buy { color: var(--green); }
    .sig-action.sell { color: var(--red); }
    .sig-action.hold { color: var(--text2); }
    .sig-detail { font-size: 10px; color: var(--text2); margin-top: 2px; }
    
    /* 포트폴리오 바 */
    .port-section {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 10px;
    }
    .port-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .port-title { font-size: 10px; color: var(--text3); }
    .port-values { font-size: 11px; color: var(--text); }
    .port-bar {
        height: 28px;
        background: #1a1f26;
        border-radius: 6px;
        overflow: hidden;
        display: flex;
    }
    .port-tqqq {
        background: linear-gradient(90deg, var(--cyan), var(--green));
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 700; color: var(--bg);
        min-width: 0;
        transition: width 0.3s;
    }
    .port-cash {
        flex: 1;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600; color: var(--text2);
    }
    
    /* MA 시그널 - 2x2 그리드 */
    .ma-section {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .ma-title {
        font-size: 10px;
        color: var(--text3);
        margin-bottom: 8px;
    }
    .ma-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
    }
    .ma-item {
        background: var(--bg);
        border-radius: 8px;
        padding: 10px 6px;
        text-align: center;
        border: 1px solid transparent;
    }
    .ma-item.active { border-color: var(--green); }
    .ma-item.inactive { border-color: var(--red); }
    .ma-item.disabled { opacity: 0.4; }
    .ma-num { font-size: 18px; font-weight: 700; color: var(--text); }
    .ma-stat { font-size: 9px; font-weight: 600; margin: 2px 0; }
    .ma-stat.above { color: var(--green); }
    .ma-stat.below { color: var(--red); }
    .ma-stat.na { color: var(--text3); }
    .ma-dev { font-size: 11px; color: var(--text2); }
    .ma-pct { font-size: 10px; font-weight: 600; margin-top: 4px; padding-top: 4px; border-top: 1px solid var(--border); }
    .ma-pct.pos { color: var(--green); }
    .ma-pct.zero { color: var(--text3); }
    
    /* Stochastic - 한 줄 */
    .stoch-section {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .stoch-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .stoch-item { text-align: center; }
    .stoch-lbl { font-size: 9px; color: var(--text3); }
    .stoch-val { font-size: 20px; font-weight: 700; }
    .stoch-k { color: var(--cyan); }
    .stoch-d { color: var(--amber); }
    .stoch-tag {
        font-size: 10px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
    }
    .stoch-bull { background: rgba(63,185,80,0.15); color: var(--green); }
    .stoch-bear { background: rgba(248,81,73,0.15); color: var(--red); }
    
    /* 차트 */
    .chart-box {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 10px;
    }
    
    /* 푸터 */
    .ftr {
        text-align: center;
        font-size: 9px;
        color: var(--text3);
        padding: 8px 0;
    }
    
    /* 버튼 */
    .stButton > button {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text2) !important;
        border-radius: 6px !important;
        font-size: 11px !important;
        padding: 6px 12px !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        border-color: var(--cyan) !important;
        color: var(--cyan) !important;
    }
    
    /* 모바일 2x2 그리드 유지 */
    @media (max-width: 480px) {
        .ma-grid { grid-template-columns: repeat(2, 1fr); }
        .top-grid { grid-template-columns: 1fr; }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# 분석기
# -----------------------------------------------------------
class TQQQAnalyzer:
    def __init__(self):
        self.stoch_config = {'period': 166, 'k_period': 57, 'd_period': 19}
        self.ma_periods = [20, 45, 151, 212]

    @st.cache_data(ttl=300)
    def get_data(_self, days_back=400):
        try:
            ticker = yf.Ticker('TQQQ')
            data = ticker.history(
                start=datetime.now() - timedelta(days=days_back),
                end=datetime.now(),
                auto_adjust=True
            )
            if data.empty:
                return None
            return pd.DataFrame({
                'Open': data['Open'], 'High': data['High'],
                'Low': data['Low'], 'Close': data['Close']
            }).dropna()
        except:
            return None

    def calc(self, df):
        d = df.copy()
        p, k, dd = self.stoch_config.values()
        d['HH'] = d['High'].rolling(p).max()
        d['LL'] = d['Low'].rolling(p).min()
        d['%K'] = ((d['Close'] - d['LL']) / (d['HH'] - d['LL']) * 100).rolling(k).mean()
        d['%D'] = d['%K'].rolling(dd).mean()
        for m in self.ma_periods:
            d[f'MA{m}'] = d['Close'].rolling(m).mean()
            d[f'D{m}'] = ((d['Close'] - d[f'MA{m}']) / d[f'MA{m}']) * 100
        return d.dropna()

    def analyze(self, d):
        c, p = d.iloc[-1], d.iloc[-2]
        bull = c['%K'] > c['%D']
        sigs = {m: c['Close'] > c[f'MA{m}'] for m in self.ma_periods}
        
        if bull:
            tqqq = sum(sigs.values()) * 0.25
        else:
            tqqq = (int(sigs[20]) + int(sigs[45])) * 0.5
        
        # prev
        pb = p['%K'] > p['%D']
        ps = {m: p['Close'] > p[f'MA{m}'] for m in self.ma_periods}
        pt = sum(ps.values()) * 0.25 if pb else (int(ps[20]) + int(ps[45])) * 0.5
        
        return {
            'price': c['Close'], 'chg': c['Close'] - p['Close'],
            'chg_pct': (c['Close'] - p['Close']) / p['Close'] * 100,
            'tqqq': tqqq, 'cash': 1 - tqqq, 'prev': pt, 'delta': tqqq - pt,
            'bull': bull, 'sigs': sigs,
            'k': c['%K'], 'd': c['%D'],
            'devs': {m: c[f'D{m}'] for m in self.ma_periods},
            'date': c.name
        }

# -----------------------------------------------------------
# 메인
# -----------------------------------------------------------
def main():
    az = TQQQAnalyzer()
    data = az.get_data()
    if data is None:
        st.error("데이터 로드 실패")
        return
    
    data = az.calc(data)
    r = az.analyze(data)
    
    days = ['월','화','수','목','금','토','일']
    dt = r['date'].strftime('%m.%d') + f" ({days[r['date'].weekday()]})"
    
    # 헤더
    st.markdown(f"""
    <div class="hdr">
        <div class="hdr-left">
            <div class="hdr-icon">⚡</div>
            <span class="hdr-title">TQQQ SNIPER</span>
        </div>
        <span class="hdr-date">{dt}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 가격 + 시그널 (2열 그리드)
    up = r['chg'] >= 0
    chg_cls = 'up' if up else 'down'
    chg_sign = '+' if up else ''
    reg_cls = 'regime-bull' if r['bull'] else 'regime-bear'
    reg_txt = '📈 BULL' if r['bull'] else '📉 BEAR'
    
    if r['delta'] > 0.01:
        sig_cls, sig_icon, sig_txt, sig_act = 'sig-buy', '🚀', f"+{r['delta']:.0%} 매수", 'buy'
    elif r['delta'] < -0.01:
        sig_cls, sig_icon, sig_txt, sig_act = 'sig-sell', '⚠️', f"{r['delta']:.0%} 매도", 'sell'
    else:
        sig_cls, sig_icon, sig_txt, sig_act = 'sig-hold', '☕', 'HOLD', 'hold'
    
    st.markdown(f"""
    <div class="top-grid">
        <div class="price-box">
            <div class="price-label">TQQQ</div>
            <div class="price-main">${r['price']:.2f}</div>
            <div class="price-change {chg_cls}">{chg_sign}${abs(r['chg']):.2f} ({chg_sign}{r['chg_pct']:.1f}%)</div>
            <div class="regime-tag {reg_cls}">{reg_txt}</div>
        </div>
        <div class="signal-box {sig_cls}">
            <div class="sig-icon">{sig_icon}</div>
            <div class="sig-label">ACTION</div>
            <div class="sig-action {sig_act}">{sig_txt}</div>
            <div class="sig-detail">{r['prev']:.0%} → {r['tqqq']:.0%}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 포트폴리오 바
    tpct = int(r['tqqq'] * 100)
    cpct = int(r['cash'] * 100)
    tqqq_label = f"TQQQ {tpct}%" if tpct >= 20 else ""
    
    st.markdown(f"""
    <div class="port-section">
        <div class="port-header">
            <span class="port-title">PORTFOLIO</span>
            <span class="port-values">TQQQ {tpct}% / CASH {cpct}%</span>
        </div>
        <div class="port-bar">
            <div class="port-tqqq" style="width:{max(tpct,3)}%">{tqqq_label}</div>
            <div class="port-cash">CASH {cpct}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # MA Signals - 4열 그리드 (모바일 2x2)
    ma_items = ""
    for m in az.ma_periods:
        above = r['sigs'][m]
        dev = r['devs'][m]
        
        if r['bull']:
            contrib = 25 if above else 0
            active = True
        else:
            if m in [20, 45]:
                contrib = 50 if above else 0
                active = True
            else:
                contrib = 0
                active = False
        
        if not active:
            cls, stat_cls, stat_txt = 'disabled', 'na', 'N/A'
        elif above:
            cls, stat_cls, stat_txt = 'active', 'above', '▲'
        else:
            cls, stat_cls, stat_txt = 'inactive', 'below', '▼'
        
        pct_cls = 'pos' if contrib > 0 else 'zero'
        pct_txt = f'+{contrib}%' if contrib > 0 else '—'
        
        ma_items += f"""
        <div class="ma-item {cls}">
            <div class="ma-num">{m}</div>
            <div class="ma-stat {stat_cls}">{stat_txt}</div>
            <div class="ma-dev">{dev:+.1f}%</div>
            <div class="ma-pct {pct_cls}">{pct_txt}</div>
        </div>
        """
    
    st.markdown(f"""
    <div class="ma-section">
        <div class="ma-title">📡 MA SIGNALS {'(4×25%)' if r['bull'] else '(20,45×50%)'}</div>
        <div class="ma-grid">{ma_items}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stochastic
    stoch_cls = 'stoch-bull' if r['bull'] else 'stoch-bear'
    stoch_txt = '%K > %D' if r['bull'] else '%K < %D'
    
    st.markdown(f"""
    <div class="stoch-section">
        <div class="stoch-left">
            <div class="stoch-item">
                <div class="stoch-lbl">%K</div>
                <div class="stoch-val stoch-k">{r['k']:.1f}</div>
            </div>
            <div class="stoch-item">
                <div class="stoch-lbl">%D</div>
                <div class="stoch-val stoch-d">{r['d']:.1f}</div>
            </div>
        </div>
        <div class="stoch-tag {stoch_cls}">{stoch_txt}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 차트
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    
    cd = data.iloc[-60:]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.06, row_heights=[0.75, 0.25])
    
    fig.add_trace(go.Candlestick(
        x=cd.index, open=cd['Open'], high=cd['High'], low=cd['Low'], close=cd['Close'],
        name='', increasing_line_color='#3fb950', decreasing_line_color='#f85149',
        increasing_fillcolor='#3fb950', decreasing_fillcolor='#f85149'
    ), row=1, col=1)
    
    colors = ['#d29922', '#00d4ff', '#a855f7', '#f472b6']
    for i, m in enumerate(az.ma_periods):
        fig.add_trace(go.Scatter(
            x=cd.index, y=cd[f'MA{m}'], name=f'{m}',
            line=dict(color=colors[i], width=1.2)
        ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=cd.index, y=cd['%K'], name='K',
                             line=dict(color='#00d4ff', width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=cd.index, y=cd['%D'], name='D',
                             line=dict(color='#d29922', width=1.5)), row=2, col=1)
    
    fig.update_layout(
        height=320, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(18,23,31,0.5)',
        xaxis_rangeslider_visible=False, showlegend=False,
        font=dict(family='JetBrains Mono', color='#7d8590', size=9)
    )
    fig.update_xaxes(gridcolor='rgba(30,37,48,0.8)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(30,37,48,0.8)', showgrid=True)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 버튼 + 푸터
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown('<div class="ftr">TQQQ Sniper v7 · Not Financial Advice</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
