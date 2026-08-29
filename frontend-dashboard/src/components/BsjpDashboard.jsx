import React, { useState, useEffect } from 'react';
import './BsjpDashboard.css';
import StockDetailModal from './StockDetailModal';

const BsjpDashboard = () => {
  const [signals, setSignals] = useState(() => {
    const saved = localStorage.getItem('bsjp_signals');
    return saved ? JSON.parse(saved) : [];
  });
  const [marketSentiment, setMarketSentiment] = useState(() => {
    return localStorage.getItem('bsjp_sentiment') || 'Analisis...';
  });
  const [historyInfo, setHistoryInfo] = useState({ win_rate: 0, file: '' });
  
  const [loadingScan, setLoadingScan] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  
  // Fitur Mode: Normal, Safe, Gorengan
  const [scanMode, setScanMode] = useState(() => {
    return localStorage.getItem('bsjp_mode') || 'normal';
  });
  const [selectedTicker, setSelectedTicker] = useState(null);

  // Fetch initial data (Weather & History)
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [weatherRes, historyRes] = await Promise.all([
          fetch('http://localhost:8000/api/weather').catch(() => null),
          fetch('http://localhost:8000/api/history').catch(() => null)
        ]);
        
        if (weatherRes && weatherRes.ok) {
          const weatherText = await weatherRes.text();
          try {
            const weatherData = JSON.parse(weatherText);
            setMarketSentiment(typeof weatherData === 'string' ? weatherData : weatherData.status || weatherData.label || weatherText);
          } catch {
            setMarketSentiment(weatherText.replace(/"/g, ''));
          }
        }

        if (historyRes && historyRes.ok) {
          const historyData = await historyRes.json();
          if(historyData.status === 'success') {
            setHistoryInfo(historyData);
          }
        }
      } catch (err) {
        console.error("Failed to load initial data", err);
      } finally {
        setLoadingInitial(false);
      }
    };
    fetchInitialData();
  }, []);

  const runAnalysis = async () => {
    if(loadingScan) return;
    setLoadingScan(true);
    try {
      const res = await fetch(`http://localhost:8000/api/scan?mode=${scanMode}`);
      const data = await res.json();
      if(data.status === 'success') {
        const newSignals = data.results || [];
        setSignals(newSignals);
        localStorage.setItem('bsjp_signals', JSON.stringify(newSignals));
        
        if (data.market_status) {
            const newSentiment = typeof data.market_status === 'string' ? data.market_status : data.market_status.status || data.market_status.label || 'Selesai';
            setMarketSentiment(newSentiment);
            localStorage.setItem('bsjp_sentiment', newSentiment);
        }
      }
    } catch (err) {
      console.error("Failed to run analysis", err);
      alert("Gagal menghubungi server API Python. Pastikan api.py sudah berjalan.");
    } finally {
      setLoadingScan(false);
    }
  };

  const buyCount = signals.filter(s => s.signal.toLowerCase().includes('buy')).length;
  const sellCount = signals.filter(s => s.signal.toLowerCase().includes('sell') || s.signal.toLowerCase().includes('take profit') || s.signal.toLowerCase().includes('cut loss')).length;
  
  // Calculate percentage for IHSG sentiment bar based on win_rate
  const sentimentPct = historyInfo.win_rate || 50;

  return (
    <div className="bsjp-dashboard-container">
      {/* Header */}
      <header className="bsjp-header">
        <div className="bsjp-header-title">
          <h1>BSJP Intelligence</h1>
          <p>Beli Sore Jual Pagi • Algorithmic Stock Signals</p>
        </div>
        <div className="bsjp-header-actions" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <select 
            value={scanMode} 
            onChange={(e) => {
              setScanMode(e.target.value);
              localStorage.setItem('bsjp_mode', e.target.value);
            }}
            className="glass-dropdown"
          >
            <option value="safe">Mode Safe (Ketat)</option>
            <option value="normal">Mode Normal</option>
            <option value="gorengan">Mode Gorengan (Intraday)</option>
          </select>
          <button className="btn-primary" onClick={runAnalysis} disabled={loadingScan}>
            {loadingScan ? 'Menganalisis...' : 'Run Analysis'}
          </button>
        </div>
      </header>

      {/* Bento Grid */}
      <div className="bsjp-grid">
        
        {/* Hero Card - Main Chart / Performance */}
        <div className="bsjp-card card-hero">
          <div className="card-title">
            <span>Portfolio Alpha</span>
            <svg className="icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
          </div>
          <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {loadingInitial ? (
               <div className="skeleton" style={{width: '200px', height: '60px', borderRadius: '8px'}} />
            ) : (
               <>
                 <h2 className="data-value-large text-green">+{historyInfo.win_rate}% Win</h2>
                 <p className="data-subtitle">Berdasarkan history {historyInfo.file || 'terbaru'}</p>
               </>
            )}
            
            {/* Mock Chart Area */}
            <div style={{ marginTop: '40px', height: '120px', display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
              {[30, 45, 20, 60, 80, 50, 90, 75, 100, 85, 110, 95, 120].map((h, i) => (
                <div key={i} style={{
                  flexGrow: 1,
                  height: `${h}%`,
                  background: i > 8 ? 'var(--accent-green)' : 'rgba(255,255,255,0.1)',
                  borderRadius: '4px 4px 0 0',
                  transition: 'var(--transition-smooth)',
                  animation: loadingScan ? 'pulse 1.5s infinite ease-in-out alternate' : 'none',
                  animationDelay: `${i * 0.1}s`
                }} className="chart-bar" />
              ))}
            </div>
          </div>
        </div>

        {/* Total Signals Today */}
        <div className="bsjp-card card-stat">
          <div className="card-title">
            <span>Signals Result</span>
            <svg className="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <div style={{ marginTop: 'auto' }}>
            {loadingScan ? (
               <div className="skeleton" style={{width: '100px', height: '60px', borderRadius: '8px'}} />
            ) : (
               <>
                 <h2 className="data-value-large">{signals.length > 0 ? signals.length : '-'}</h2>
                 <p className="data-subtitle">
                   {signals.length > 0 ? (
                     <><span className="text-green">{buyCount} Buy</span> / <span className="text-red">{sellCount} Sell</span></>
                   ) : "Klik Run Analysis untuk mulai"}
                 </p>
               </>
            )}
          </div>
        </div>

        {/* Market Sentiment */}
        <div className="bsjp-card card-market">
          <div className="card-title">
            <span>IHSG Sentiment</span>
          </div>
          <div style={{ marginTop: 'auto' }}>
            {loadingInitial ? (
                <div className="skeleton" style={{width: '150px', height: '60px', borderRadius: '8px'}} />
            ) : (
                <h2 className="data-value-large" style={{ fontSize: '1.8rem' }}>{marketSentiment}</h2>
            )}
            
            <div className="range-bar-container" style={{ marginTop: '24px' }}>
              <div className="range-labels">
                <span className="text-muted">Bearish</span>
                <span className="text-green">Bullish</span>
              </div>
              <div className="range-bar-bg">
                <div className="range-bar-fill" style={{ width: `${sentimentPct}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Live Watchlist / Signals List */}
        <div className="bsjp-card card-signals">
          <div className="card-title">
            <span>Actionable Signals ({scanMode.toUpperCase()})</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', cursor: 'pointer' }}>View All</span>
          </div>
          
          <div className="signal-list">
            {loadingScan ? (
              <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: '16px'}}>
                 <div className="spinner"></div>
                 <span style={{color: 'var(--text-muted)'}}>Scraping & Analisis Data dari YFinance...</span>
              </div>
            ) : signals.length === 0 ? (
              <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)'}}>
                Belum ada data scan terbaru
              </div>
            ) : (
              signals.map((signal, idx) => {
                const isBuy = signal.signal.toLowerCase().includes('buy');
                return (
                  <div className="signal-item" key={idx} onClick={() => setSelectedTicker(signal.ticker)} style={{ cursor: 'pointer' }}>
                    <div className="signal-stock">
                      <span className="signal-ticker">{signal.ticker}</span>
                      <span className="signal-company">{signal.sektor || 'IDX'} • Score: {signal.score}</span>
                    </div>
                    <div className="signal-data">
                      <span className={`badge ${isBuy ? 'badge-buy' : 'badge-sell'}`}>
                        {signal.signal}
                      </span>
                      <span className="signal-price">Rp {signal.close.toLocaleString('id-ID')}</span>
                      <span className="signal-target" style={{color: isBuy ? 'var(--accent-green)' : 'var(--accent-red)'}}>
                        {signal.chg}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Algorithmic Accuracy */}
        <div className="bsjp-card card-summary">
          <div className="card-title">
            <span>Model Win Rate</span>
          </div>
          <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', height: '140px' }}>
            {/* Circular Progress */}
            {loadingInitial ? (
                <div className="skeleton" style={{width: '100px', height: '100px', borderRadius: '50%'}} />
            ) : (
              <>
                <svg viewBox="0 0 100 100" style={{ width: '120px', height: '120px', transform: 'rotate(-90deg)' }}>
                  <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                  <circle cx="50" cy="50" r="45" fill="none" stroke="var(--accent-primary)" strokeWidth="8" strokeDasharray="283" strokeDashoffset={283 - (283 * (historyInfo.win_rate || 0)) / 100} strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1.5s ease-in-out' }} />
                </svg>
                <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: '700' }}>{historyInfo.win_rate || 0}%</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Latest Data</span>
                </div>
              </>
            )}
          </div>
        </div>

      </div>

      {/* Detail Modal */}
      {selectedTicker && (
        <StockDetailModal ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />
      )}
    </div>
  );
};

export default BsjpDashboard;
