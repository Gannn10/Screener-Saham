import React, { useState, useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const StockDetailModal = ({ ticker, onClose }) => {
  const [activeTab, setActiveTab] = useState('chart');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    broker_summary: [],
    aggregate_whale: {},
    breakdown: [],
    news: []
  });
  const [chartData, setChartData] = useState([]);
  
  const chartContainerRef = useRef(null);
  const chartInstance = useRef(null);

  // Fetch Data
  useEffect(() => {
    if (!ticker) return;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const [detailRes, chartRes] = await Promise.all([
          fetch(`http://localhost:8000/api/detail/${ticker}`),
          fetch(`http://localhost:8000/api/chart/${ticker}`)
        ]);
        
        if(detailRes.ok) setData(await detailRes.json());
        if(chartRes.ok) setChartData(await chartRes.json());
      } catch (err) {
        console.error("Failed fetching detail", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [ticker]);

  // Init Chart
  useEffect(() => {
    if (activeTab !== 'chart' || loading || chartData.length === 0) return;
    
    if (chartContainerRef.current) {
      if (chartInstance.current) {
         chartInstance.current.remove();
      }
      
      try {
        const chart = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth || 600,
        height: 350,
        layout: {
          background: { type: 'solid', color: '#06070a' },
          textColor: '#9496a8',
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        rightPriceScale: {
          borderColor: 'rgba(255, 255, 255, 0.1)',
        },
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.1)',
          timeVisible: true,
        },
      });
      
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#00FFA3',
        downColor: '#FF3366',
        borderVisible: false,
        wickUpColor: '#00FFA3',
        wickDownColor: '#FF3366',
      });
      
      candlestickSeries.setData(chartData);
      chart.timeScale().fitContent();
      
      chartInstance.current = chart;
      
      const handleResize = () => {
        if(chartContainerRef.current && chartInstance.current) {
            chartInstance.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
      };
      window.addEventListener('resize', handleResize);
      return () => {
          window.removeEventListener('resize', handleResize);
          if (chartInstance.current) {
              chartInstance.current.remove();
              chartInstance.current = null;
          }
      };
      } catch(e) {
          console.error("Error creating chart:", e);
      }
    }
  }, [activeTab, loading, chartData]);

  if (!ticker) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        <div className="modal-header">
          <div className="modal-title-group">
            <h2 className="modal-ticker">{ticker}</h2>
            <span className="badge badge-buy">Detail Analysis</span>
          </div>
          <button className="btn-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div className="modal-tabs">
          <button className={`tab-btn ${activeTab === 'chart' ? 'active' : ''}`} onClick={() => setActiveTab('chart')}>Live Chart</button>
          <button className={`tab-btn ${activeTab === 'score' ? 'active' : ''}`} onClick={() => setActiveTab('score')}>Score Breakdown</button>
          <button className={`tab-btn ${activeTab === 'broker' ? 'active' : ''}`} onClick={() => setActiveTab('broker')}>Broker Flow</button>
          <button className={`tab-btn ${activeTab === 'news' ? 'active' : ''}`} onClick={() => setActiveTab('news')}>Berita Terkini</button>
        </div>

        <div className="modal-body">
          {loading ? (
             <div className="modal-loading">
                <div className="spinner"></div>
                <p>Mengambil data detail {ticker}...</p>
             </div>
          ) : (
            <>
              {/* TAB CHART */}
              <div className="tab-pane" style={{ display: activeTab === 'chart' ? 'block' : 'none' }}>
                {chartData.length > 0 ? (
                   <div ref={chartContainerRef} style={{ width: '100%', height: '350px' }} />
                ) : (
                   <div className="empty-state">Data chart tidak tersedia</div>
                )}
              </div>

              {/* TAB SCORE BREAKDOWN */}
              <div className="tab-pane" style={{ display: activeTab === 'score' ? 'block' : 'none' }}>
                <div className="score-grid">
                  {Array.isArray(data.breakdown) ? data.breakdown.map((item, idx) => (
                    <div className="score-card" key={idx}>
                       <span className="score-label">{item?.label}</span>
                       <span className="score-value">{item?.value}</span>
                    </div>
                  )) : <div className="empty-state">Data tidak tersedia</div>}
                </div>
              </div>

              {/* TAB BROKER FLOW */}
              <div className="tab-pane" style={{ display: activeTab === 'broker' ? 'block' : 'none' }}>
                <div className="whale-card mb-4">
                   <div className="whale-header">Whale / Foreign Flow</div>
                   <div className="whale-data">
                      <div>Status: <span className={data.aggregate_whale.status?.includes('Akumulasi') ? 'text-green' : 'text-red'}>{data.aggregate_whale.status}</span></div>
                      <div>Net Foreign: {data.aggregate_whale.net_foreign}</div>
                      <div>Foreign Pct: {data.aggregate_whale.foreign_pct}</div>
                   </div>
                </div>
                
                <h4 className="section-subtitle">Top Broker Accumulation</h4>
                {Array.isArray(data.broker_summary) && data.broker_summary.length > 0 ? (
                  <table className="broker-table">
                    <thead>
                      <tr>
                        <th>Broker</th>
                        <th>Type</th>
                        <th>Volume</th>
                        <th>Avg Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.broker_summary.map((b, idx) => (
                        <tr key={idx}>
                          <td>{b.broker}</td>
                          <td className={b.type === 'BUY' ? 'text-green' : 'text-red'}>{b.type}</td>
                          <td>{b.volume}</td>
                          <td>{b.avg_price}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="empty-state">Data broker belum tersedia untuk hari ini</div>
                )}
              </div>

              {/* TAB NEWS */}
              <div className="tab-pane" style={{ display: activeTab === 'news' ? 'block' : 'none' }}>
                <div className="news-list">
                   {Array.isArray(data.news) && data.news.length > 0 ? (
                     data.news.map((n, idx) => (
                       <div className="news-item" key={idx}>
                          <a href={n.link || n.url || `https://www.google.com/search?q=${encodeURIComponent(n.judul || n.title)}`} target="_blank" rel="noreferrer" className="news-title">{n.judul || n.title}</a>
                          <span className="news-meta">{n.sumber || n.publisher} • {n.waktu || n.time}</span>
                       </div>
                     ))
                   ) : (
                     <div className="empty-state">Tidak ada berita relevan hari ini</div>
                   )}
                </div>
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  );
};

export default StockDetailModal;
