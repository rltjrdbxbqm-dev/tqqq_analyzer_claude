import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Zap, Shield, DollarSign, Activity, ChevronRight, Clock, Target, AlertTriangle, CheckCircle, XCircle, BarChart3, Layers } from 'lucide-react';

// 시뮬레이션 데이터
const mockData = {
  dataDate: '2025-06-02',
  weekday: '월',
  tqqq: { price: 78.42, change: 2.34 },
  gld: { price: 242.18, change: -0.52 },
  portfolio: {
    tqqq: 0.75,
    gld: 0.25,
    cash: 0.0,
    prevTqqq: 0.50,
    prevGld: 0.50,
  },
  isBullish: true,
  stochastic: { k: 72.4, d: 68.1 },
  deviations: {
    ma20: 5.2,
    ma45: 8.7,
    ma151: 15.3,
    ma212: 22.1,
  },
  buyStrategies: [
    { name: 'MA 20', threshold: -12, current: 5.2, active: false, remainingDays: 0, triggerDate: null },
    { name: 'MA 45', threshold: -11, current: 8.7, active: false, remainingDays: 0, triggerDate: null },
    { name: 'MA 151', threshold: -21, current: 15.3, active: true, remainingDays: 5, triggerDate: '05-28' },
    { name: 'MA 212', threshold: -15, current: 22.1, active: false, remainingDays: 0, triggerDate: null },
  ],
  sellStrategies: [
    { name: 'Opt MA 45', threshold: 33, current: 8.7, active: false, remainingDays: 0, dependency: null, depMet: true },
    { name: 'Opt MA 151', threshold: 55, current: 15.3, active: false, remainingDays: 0, dependency: 'MA 20', depMet: true },
    { name: 'Opt MA 212', threshold: 55, current: 22.1, active: true, remainingDays: 8, dependency: 'MA 45', depMet: true, triggerDate: '05-25' },
  ],
  actions: [
    { type: 'buy', asset: 'TQQQ', amount: 0.25 }
  ]
};

export default function TQQQSniperDashboard() {
  const [data, setData] = useState(mockData);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('buy');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1500);
  };

  const getProgressColor = (progress, type) => {
    if (type === 'buy') {
      if (progress >= 1) return 'from-emerald-500 to-cyan-400';
      if (progress >= 0.7) return 'from-amber-500 to-orange-400';
      return 'from-slate-600 to-slate-500';
    } else {
      if (progress >= 1) return 'from-rose-500 to-pink-400';
      if (progress >= 0.7) return 'from-amber-500 to-orange-400';
      return 'from-slate-600 to-slate-500';
    }
  };

  const calculateBuyProgress = (current, threshold) => {
    if (current > 0) return 0;
    if (current <= threshold) return 1;
    return Math.min(1, Math.abs(current) / Math.abs(threshold));
  };

  const calculateSellProgress = (current, threshold) => {
    if (current < 0) return 0;
    if (current >= threshold) return 1;
    return Math.min(1, current / threshold);
  };

  return (
    <div className="min-h-screen bg-[#0a0b0f] text-white overflow-x-hidden" style={{ fontFamily: "'JetBrains Mono', 'SF Mono', monospace" }}>
      {/* 배경 효과 */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl" />
        {/* 그리드 패턴 */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                             linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-6">
        {/* 헤더 */}
        <header className={`mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-xl blur-lg opacity-50" />
                <div className="relative bg-gradient-to-br from-cyan-500 to-emerald-500 p-3 rounded-xl">
                  <Target className="w-6 h-6 text-black" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">
                  <span className="bg-gradient-to-r from-cyan-400 via-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                    TQQQ SNIPER
                  </span>
                  <span className="text-slate-500 text-sm ml-2 font-normal">v4.6</span>
                </h1>
                <p className="text-slate-500 text-xs tracking-wider">REAL-TIME SIGNAL ANALYSIS</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <div className={`w-2 h-2 rounded-full ${data.isBullish ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50' : 'bg-rose-400 shadow-lg shadow-rose-400/50'}`} />
                <span className="text-xs text-slate-400">
                  {data.isBullish ? 'BULLISH' : 'BEARISH'} REGIME
                </span>
              </div>
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="group relative p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded-xl border border-slate-700/50 hover:border-cyan-500/30 transition-all duration-300"
              >
                <RefreshCw className={`w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-colors ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* 날짜 배지 */}
          <div className={`mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-slate-800/30 rounded-lg border border-slate-700/30 transition-all duration-700 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}>
            <Clock className="w-3 h-3 text-cyan-400" />
            <span className="text-xs text-slate-400">데이터 기준:</span>
            <span className="text-xs font-semibold text-cyan-400">{data.dataDate} ({data.weekday}) 장마감</span>
          </div>
        </header>

        {/* 액션 카드 */}
        <section className={`mb-6 transition-all duration-700 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          {data.actions.length > 0 ? (
            data.actions.map((action, idx) => (
              <div 
                key={idx}
                className={`relative overflow-hidden rounded-2xl p-1 ${
                  action.type === 'buy' 
                    ? 'bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-emerald-500/20' 
                    : 'bg-gradient-to-r from-rose-500/20 via-pink-500/20 to-rose-500/20'
                }`}
              >
                <div className="relative bg-[#0d0e12] rounded-xl p-5">
                  <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
                    {action.type === 'buy' ? (
                      <TrendingUp className="w-full h-full text-emerald-400" />
                    ) : (
                      <TrendingDown className="w-full h-full text-rose-400" />
                    )}
                  </div>
                  
                  <div className="relative flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${
                      action.type === 'buy' 
                        ? 'bg-emerald-500/20 text-emerald-400' 
                        : 'bg-rose-500/20 text-rose-400'
                    }`}>
                      {action.type === 'buy' ? <Zap className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                    </div>
                    
                    <div className="flex-1">
                      <p className="text-slate-400 text-sm mb-1">Action Required</p>
                      <p className={`text-xl font-bold ${
                        action.type === 'buy' ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {action.asset} {(action.amount * 100).toFixed(0)}% {action.type === 'buy' ? '매수' : '매도'}
                      </p>
                    </div>
                    
                    <ChevronRight className={`w-6 h-6 ${
                      action.type === 'buy' ? 'text-emerald-400' : 'text-rose-400'
                    }`} />
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="relative overflow-hidden rounded-2xl bg-slate-800/20 border border-slate-700/30 p-5">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-slate-700/30 text-slate-400">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm mb-1">No Action Required</p>
                  <p className="text-lg font-medium text-slate-300">오늘은 매매 없이 홀딩 ☕</p>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* 포트폴리오 구성 */}
        <section className={`mb-6 transition-all duration-700 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <h2 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4" />
            PORTFOLIO COMPOSITION
          </h2>
          
          <div className="grid grid-cols-3 gap-3">
            {/* TQQQ */}
            <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/30 hover:border-cyan-500/30 transition-all duration-300 p-4">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-500 font-medium">TQQQ</span>
                  <span className={`text-xs font-semibold ${
                    data.portfolio.tqqq > data.portfolio.prevTqqq ? 'text-emerald-400' : 
                    data.portfolio.tqqq < data.portfolio.prevTqqq ? 'text-rose-400' : 'text-slate-400'
                  }`}>
                    {data.portfolio.tqqq > data.portfolio.prevTqqq ? '+' : ''}
                    {((data.portfolio.tqqq - data.portfolio.prevTqqq) * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-3xl font-bold text-cyan-400 mb-3">
                  {(data.portfolio.tqqq * 100).toFixed(0)}%
                </p>
                <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-1000"
                    style={{ width: `${data.portfolio.tqqq * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* GLD */}
            <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/30 hover:border-amber-500/30 transition-all duration-300 p-4">
              <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-500 font-medium">GLD</span>
                  <span className={`text-xs font-semibold ${
                    data.portfolio.gld > data.portfolio.prevGld ? 'text-emerald-400' : 
                    data.portfolio.gld < data.portfolio.prevGld ? 'text-rose-400' : 'text-slate-400'
                  }`}>
                    {data.portfolio.gld > data.portfolio.prevGld ? '+' : ''}
                    {((data.portfolio.gld - data.portfolio.prevGld) * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-3xl font-bold text-amber-400 mb-3">
                  {(data.portfolio.gld * 100).toFixed(0)}%
                </p>
                <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-amber-500 to-yellow-400 rounded-full transition-all duration-1000"
                    style={{ width: `${data.portfolio.gld * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Cash */}
            <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/30 hover:border-slate-500/30 transition-all duration-300 p-4">
              <div className="absolute inset-0 bg-gradient-to-br from-slate-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-500 font-medium">CASH</span>
                  <span className="text-xs font-semibold text-slate-400">-</span>
                </div>
                <p className="text-3xl font-bold text-slate-400 mb-3">
                  {(data.portfolio.cash * 100).toFixed(0)}%
                </p>
                <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-slate-500 to-slate-400 rounded-full transition-all duration-1000"
                    style={{ width: `${Math.max(data.portfolio.cash * 100, 0)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 전략 모니터 */}
        <section className={`transition-all duration-700 delay-400 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <h2 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            STRATEGY MONITOR
          </h2>

          {/* 탭 네비게이션 */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setActiveTab('buy')}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all duration-300 ${
                activeTab === 'buy'
                  ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-800/30 text-slate-400 border border-slate-700/30 hover:border-slate-600/50'
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                <TrendingUp className="w-4 h-4" />
                매수 전략 (Buy)
              </span>
            </button>
            <button
              onClick={() => setActiveTab('sell')}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-medium transition-all duration-300 ${
                activeTab === 'sell'
                  ? 'bg-gradient-to-r from-rose-500/20 to-pink-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-slate-800/30 text-slate-400 border border-slate-700/30 hover:border-slate-600/50'
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                <TrendingDown className="w-4 h-4" />
                매도 전략 (Sell)
              </span>
            </button>
          </div>

          {/* 매수 전략 탭 */}
          {activeTab === 'buy' && (
            <div className="space-y-3">
              <div className="px-4 py-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20 mb-4">
                <span className="text-xs text-emerald-400">
                  조정 비중: <span className="font-bold">25.0%</span> (GLD → TQQQ)
                </span>
              </div>
              
              {data.buyStrategies.map((strategy, idx) => {
                const progress = calculateBuyProgress(strategy.current, strategy.threshold);
                return (
                  <div 
                    key={idx}
                    className={`relative overflow-hidden rounded-xl border transition-all duration-300 ${
                      strategy.active 
                        ? 'bg-emerald-500/5 border-emerald-500/30' 
                        : 'bg-slate-800/30 border-slate-700/30 hover:border-slate-600/50'
                    }`}
                  >
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold ${
                            strategy.active 
                              ? 'bg-emerald-500/20 text-emerald-400' 
                              : 'bg-slate-700/50 text-slate-400'
                          }`}>
                            {strategy.name.split(' ')[1]}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{strategy.name}</p>
                            <p className="text-xs text-slate-500">
                              {strategy.active 
                                ? `✅ 진입일: ${strategy.triggerDate}` 
                                : '💤 대기중'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          {strategy.active ? (
                            <div>
                              <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 rounded-lg text-emerald-400 text-xs font-semibold">
                                <CheckCircle className="w-3 h-3" />
                                진입 완료
                              </span>
                              <p className="text-xs text-slate-400 mt-1">
                                ⏳ {strategy.remainingDays} 거래일 남음
                              </p>
                            </div>
                          ) : (
                            <div>
                              <p className="text-xs text-slate-400">
                                현재: <span className="text-slate-300">{strategy.current.toFixed(1)}%</span>
                              </p>
                              <p className="text-xs text-slate-500">
                                목표: {strategy.threshold}%
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* 프로그레스 바 */}
                      <div className="h-2 bg-slate-700/30 rounded-full overflow-hidden">
                        <div 
                          className={`h-full bg-gradient-to-r ${getProgressColor(progress, 'buy')} rounded-full transition-all duration-700`}
                          style={{ width: `${progress * 100}%` }}
                        />
                      </div>
                      
                      {!strategy.active && strategy.current > 0 && (
                        <p className="text-xs text-slate-500 mt-2">
                          📉 <span className="text-amber-400">-{(strategy.current - strategy.threshold).toFixed(1)}%p</span> 남음
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* 매도 전략 탭 */}
          {activeTab === 'sell' && (
            <div className="space-y-3">
              <div className="px-4 py-2 bg-rose-500/10 rounded-lg border border-rose-500/20 mb-4">
                <span className="text-xs text-rose-400">
                  조정 비중: <span className="font-bold">25.0%</span> (TQQQ → Cash)
                </span>
              </div>
              
              {data.sellStrategies.map((strategy, idx) => {
                const progress = calculateSellProgress(strategy.current, strategy.threshold);
                const isDisabled = strategy.dependency && !strategy.depMet;
                
                return (
                  <div 
                    key={idx}
                    className={`relative overflow-hidden rounded-xl border transition-all duration-300 ${
                      strategy.active 
                        ? 'bg-rose-500/5 border-rose-500/30' 
                        : isDisabled
                          ? 'bg-slate-900/50 border-slate-800/50 opacity-60'
                          : 'bg-slate-800/30 border-slate-700/30 hover:border-slate-600/50'
                    }`}
                  >
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold ${
                            strategy.active 
                              ? 'bg-rose-500/20 text-rose-400' 
                              : 'bg-slate-700/50 text-slate-400'
                          }`}>
                            {strategy.name.split(' ')[2]}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{strategy.name}</p>
                            <p className="text-xs text-slate-500">
                              {strategy.active 
                                ? `🚨 매도일: ${strategy.triggerDate}` 
                                : isDisabled
                                  ? `🚫 ${strategy.dependency} 조건 미달`
                                  : '💤 대기중'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          {strategy.active ? (
                            <div>
                              <span className="inline-flex items-center gap-1 px-2 py-1 bg-rose-500/20 rounded-lg text-rose-400 text-xs font-semibold">
                                <AlertTriangle className="w-3 h-3" />
                                매도 (현금)
                              </span>
                              <p className="text-xs text-slate-400 mt-1">
                                ⏳ {strategy.remainingDays} 거래일 남음
                              </p>
                            </div>
                          ) : (
                            <div>
                              <p className="text-xs text-slate-400">
                                현재: <span className="text-slate-300">{strategy.current.toFixed(1)}%</span>
                              </p>
                              <p className="text-xs text-slate-500">
                                목표: +{strategy.threshold}%
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* 프로그레스 바 */}
                      <div className="h-2 bg-slate-700/30 rounded-full overflow-hidden">
                        <div 
                          className={`h-full bg-gradient-to-r ${getProgressColor(progress, 'sell')} rounded-full transition-all duration-700`}
                          style={{ width: `${progress * 100}%` }}
                        />
                      </div>
                      
                      {!strategy.active && !isDisabled && (
                        <p className="text-xs text-slate-500 mt-2">
                          📈 <span className="text-amber-400">+{(strategy.threshold - strategy.current).toFixed(1)}%p</span> 남음
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Stochastic 인디케이터 */}
        <section className={`mt-6 transition-all duration-700 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <div className="rounded-2xl bg-gradient-to-br from-slate-800/30 to-slate-900/30 border border-slate-700/30 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-violet-500/20 rounded-lg">
                  <BarChart3 className="w-4 h-4 text-violet-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Stochastic Oscillator (166, 57, 19)</p>
                  <p className="text-sm font-medium">
                    <span className="text-cyan-400">%K: {data.stochastic.k.toFixed(1)}</span>
                    <span className="text-slate-500 mx-2">/</span>
                    <span className="text-amber-400">%D: {data.stochastic.d.toFixed(1)}</span>
                  </p>
                </div>
              </div>
              <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                data.isBullish 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              }`}>
                {data.isBullish ? '📈 Bullish' : '📉 Bearish'}
              </div>
            </div>
          </div>
        </section>

        {/* 푸터 */}
        <footer className={`mt-8 text-center transition-all duration-700 delay-600 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <p className="text-xs text-slate-600">
            Built with precision • Not financial advice
          </p>
        </footer>
      </div>
    </div>
  );
}
