let activeChart = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchWeather();
    
    // Sidebar Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');
    const pageTitle = document.getElementById('page-title');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active classes
            navItems.forEach(nav => nav.classList.remove('active'));
            viewSections.forEach(sec => sec.classList.remove('active', 'hidden'));
            viewSections.forEach(sec => sec.classList.add('hidden'));

            // Set active
            item.classList.add('active');
            const targetId = item.getAttribute('data-target');
            document.getElementById(targetId).classList.remove('hidden');
            document.getElementById(targetId).classList.add('active');

            // Update Title
            pageTitle.textContent = item.textContent.trim();

            // Load specific data if needed
            if (targetId === 'view-settings') loadSettings();
            if (targetId === 'view-history') loadHistoryFiles();
        });
    });

    document.getElementById('close-modal').addEventListener('click', () => {
        document.getElementById('stock-modal').classList.add('hidden');
    });

    // Settings Form Submission
    document.getElementById('settings-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const configData = {
            TELEGRAM_TOKEN: document.getElementById('cfg-telegram-token').value,
            TELEGRAM_CHAT_ID: document.getElementById('cfg-telegram-chat').value,
            SAFE_VSPIKE_MIN: parseInt(document.getElementById('cfg-safe-vspike').value),
            NORMAL_VSPIKE_MIN: parseInt(document.getElementById('cfg-normal-vspike').value),
            AGGRESSIVE_VSPIKE_MIN: parseInt(document.getElementById('cfg-agr-vspike').value),
            SAFE_RSI_MAX: parseInt(document.getElementById('cfg-safe-rsi').value),
            NORMAL_RSI_MAX: parseInt(document.getElementById('cfg-normal-rsi').value),
            AGGRESSIVE_RSI_MAX: parseInt(document.getElementById('cfg-agr-rsi').value)
        };
        
        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            if (res.ok) {
                alert('Pengaturan berhasil disimpan!');
            }
        } catch(e) {
            alert('Gagal menyimpan pengaturan.');
        }
    });
});

async function fetchWeather() {
    try {
        const response = await fetch('/api/weather');
        const data = await response.json();
        
        const badge = document.getElementById('weather-badge');
        const text = document.getElementById('weather-text');
        
        text.textContent = `Cuaca IHSG: ${data.label}`;
        
        if (data.status === 'CRASH') {
            badge.style.color = 'var(--accent-red)';
            badge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
        } else if (data.status === 'BULLISH') {
            badge.style.color = 'var(--accent-green)';
            badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        } else {
            badge.style.color = 'var(--text-main)';
        }
    } catch (e) {
        document.getElementById('weather-text').textContent = 'Gagal memuat cuaca';
    }
}

function startScanBSJP() {
    const mode = document.getElementById('bsjp-mode-select').value;
    startScan(mode);
}

async function startScan(mode) {
    const overlay = document.getElementById('global-progress');
    overlay.classList.remove('hidden');
    
    const gridId = mode === 'gorengan' ? 'results-grid-gorengan' : 'results-grid-swing';
    const grid = document.getElementById(gridId);
    
    try {
        const response = await fetch(`/api/scan?mode=${mode}`);
        const data = await response.json();
        
        grid.innerHTML = '';
        
        if (data.results && data.results.length > 0) {
            data.results.forEach(stock => {
                grid.appendChild(createCard(stock, mode));
            });
        } else {
            grid.innerHTML = `<div class="empty-state">Tidak ada saham yang lolos filter mode ${mode.toUpperCase()} hari ini.</div>`;
        }
    } catch (e) {
        grid.innerHTML = `<div class="empty-state" style="color:var(--accent-red)">Error: Gagal menghubungi server.</div>`;
    } finally {
        overlay.classList.add('hidden');
    }
}

function createCard(stock, mode) {
    const div = document.createElement('div');
    div.className = 'stock-card';
    
    let isGorengan = mode === 'gorengan';
    let chgClass = stock.chg >= 0 ? 'chg-up' : 'chg-down';
    let sign = stock.chg > 0 ? '+' : '';
    
    let targetMid = stock.panduan.target_mid || 0;
    let targetPct = ((targetMid - stock.close) / stock.close * 100).toFixed(2);
    let slPct = ((stock.close - stock.panduan.stop_loss) / stock.close * 100).toFixed(2);

    div.innerHTML = `
        <div class="card-header" style="cursor:pointer;" onclick="openModal('${stock.ticker}', '${stock.sektor.replace(/'/g, "\\'")}', ${stock.score}, '${stock.signal}')">
            <div>
                <div class="ticker-name">${stock.ticker}</div>
                <div class="ticker-sector">${stock.sektor.substring(0, 20)}</div>
                <div style="font-size:12px; margin-top:5px; color:var(--accent-blue)"><b>${stock.hint}</b></div>
            </div>
            <div class="chg-badge ${chgClass}">
                <div>${stock.close}</div>
                <div style="font-size: 14px;">${sign}${stock.chg}%</div>
            </div>
        </div>
        
        <div class="score-box">
            <span>Score: <strong>${stock.score}</strong>/180</span>
            <span class="signal-badge ${stock.signal}">${stock.signal}</span>
        </div>

        <div class="trading-plan">
            <div class="plan-row">
                <span>Beli Ideal</span>
                <strong>${stock.close}</strong>
            </div>
            <div class="plan-row">
                <span>Target Jual (Mid)</span>
                <strong class="target">${targetMid} (+${targetPct}%)</strong>
            </div>
            <div class="plan-row">
                <span>Stop Loss</span>
                <strong class="stop">${stock.panduan.stop_loss} (-${slPct}%)</strong>
            </div>
        </div>
        
        ${isGorengan ? '<div class="fast-trade-warning">🔥 FAST TRADE! JANGAN DIINAPKAN!</div>' : ''}
    `;

    return div;
}

// ==========================================
// MODAL LOGIC & TRADINGVIEW CHART
// ==========================================

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`button[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

async function renderChart(ticker) {
    const container = document.getElementById('chart-container');
    
    // Pastikan chart lama dihapus dari memori sebelum membuat baru
    if (activeChart) {
        try { activeChart.remove(); } catch(e) {}
        activeChart = null;
    }
    container.innerHTML = '';
    
    // Ensure container is visible before creating chart
    document.getElementById('tab-chart').classList.add('active');

    // Instantiate chart
    activeChart = LightweightCharts.createChart(container, {
        layout: {
            background: { type: 'solid', color: 'transparent' },
            textColor: '#94a3b8',
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        timeScale: {
            timeVisible: false,
            borderVisible: false,
        },
        rightPriceScale: {
            borderVisible: false,
        }
    });

    const candlestickSeries = activeChart.addCandlestickSeries({
        upColor: '#10b981', downColor: '#ef4444', borderVisible: false,
        wickUpColor: '#10b981', wickDownColor: '#ef4444'
    });

    // Auto-resize agar chart pas dengan layar pop-up Modal
    const ro = new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) return;
        const newRect = entries[0].contentRect;
        if (activeChart && newRect.width > 0 && newRect.height > 0) {
            activeChart.applyOptions({ height: newRect.height, width: newRect.width });
        }
    });
    ro.observe(container);

    try {
        const response = await fetch(`/api/chart/${ticker}`);
        const data = await response.json();
        if (data && data.length > 0) {
            candlestickSeries.setData(data);
            activeChart.timeScale().fitContent();
        } else {
            container.innerHTML = '<div class="empty-state">Data history harga saham tidak ditemukan.</div>';
        }
    } catch(e) {
        container.innerHTML = '<div class="empty-state">Error memuat data chart. Cek koneksi API.</div>';
        console.error(e);
    }
}

async function openModal(ticker, sektor, score, signal) {
    const modal = document.getElementById('stock-modal');
    modal.classList.remove('hidden');
    switchTab('tab-chart');
    
    document.getElementById('modal-ticker').textContent = ticker;
    document.getElementById('modal-sektor').textContent = sektor;
    
    document.getElementById('broker-flow-container').innerHTML = 'Menghubungi IDX API...';
    document.getElementById('news-container').innerHTML = 'Mencari berita...';

    // Render chart
    setTimeout(() => renderChart(ticker), 100); // give time for modal to display

    // Fetch detail dari API
    try {
        const response = await fetch(`/api/detail/${ticker}`);
        const data = await response.json();
        
        // Render Score Breakdown
        let scoreHtml = `
            <div class="detail-row"><span>Total Score</span><strong style="color:var(--accent-blue);font-size:20px;">${score}</strong></div>
            <div class="detail-row"><span>Signal Akhir</span><strong class="signal-badge ${signal}">${signal}</strong></div>
            <div style="margin-top:20px;margin-bottom:10px;color:var(--text-muted);font-size:14px;border-bottom:1px solid var(--glass-border);padding-bottom:5px;">Rincian Poin (Raw Values)</div>
        `;
        if (data.breakdown && data.breakdown.length > 0) {
            data.breakdown.forEach(item => {
                scoreHtml += `<div class="detail-row"><span style="color:var(--text-muted)">${item.label}</span><strong style="color:white">${item.value}</strong></div>`;
            });
        } else {
            scoreHtml += `<div style="text-align:center;color:var(--text-muted);margin-top:10px;">Lakukan scan ulang untuk memuat rincian.</div>`;
        }
        document.getElementById('score-breakdown-container').innerHTML = scoreHtml;

        // Render Broker
        if (data.broker_summary && data.broker_summary.status === 'success') {
            let html = '<div class="broker-grid">';
            html += '<div class="broker-col"><h4>Top Buyers</h4>';
            data.broker_summary.top_buyers.forEach(b => { html += `<div class="broker-item buy"><span>${b.broker}</span><span>+${(b.net_buy/1000).toFixed(1)}k lot</span></div>`; });
            html += '</div>';
            html += '<div class="broker-col"><h4>Top Sellers</h4>';
            data.broker_summary.top_sellers.forEach(s => { html += `<div class="broker-item sell"><span>${s.broker}</span><span>-${(s.net_sell/1000).toFixed(1)}k lot</span></div>`; });
            html += '</div></div>';
            document.getElementById('broker-flow-container').innerHTML = html;
        } else if (data.aggregate_whale && data.aggregate_whale.status !== '-') {
            let w = data.aggregate_whale;
            let color = w.net_foreign.includes('+') ? 'var(--accent-green)' : 'var(--accent-red)';
            document.getElementById('broker-flow-container').innerHTML = `
                <div style="text-align:center; margin-bottom:15px; color:var(--text-muted); font-size:13px;">Data spesifik broker ditutup oleh IDX hari ini.<br>Berikut adalah ringkasan Net Foreign Flow:</div>
                <div class="detail-row"><span>Whale Flow Status</span><strong style="color:${color}">${w.status}</strong></div>
                <div class="detail-row"><span>Net Foreign Value</span><strong style="color:${color}">${w.net_foreign}</strong></div>
                <div class="detail-row"><span>Foreign Dominance</span><strong style="color:white">${w.foreign_pct}</strong></div>
            `;
        } else {
            document.getElementById('broker-flow-container').innerHTML = 'Data broker dan asing tidak tersedia hari ini.';
        }
        
        // Render News
        if (data.news && data.news.length > 0) {
            let nHtml = '';
            data.news.forEach(n => { nHtml += `<div class="news-item"><div class="news-title">${n.judul}</div><div class="news-meta">${n.sumber} &bull; ${n.waktu}</div></div>`; });
            document.getElementById('news-container').innerHTML = nHtml;
        } else {
            document.getElementById('news-container').innerHTML = 'Tidak ada berita relevan dalam 3 hari terakhir.';
        }
        
    } catch (e) {
        document.getElementById('broker-flow-container').innerHTML = 'Gagal memuat data.';
        document.getElementById('news-container').innerHTML = 'Gagal memuat berita.';
    }
}

// ==========================================
// CONFIG & HISTORY LOGIC
// ==========================================

async function loadSettings() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        document.getElementById('cfg-telegram-token').value = data.TELEGRAM_TOKEN || '';
        document.getElementById('cfg-telegram-chat').value = data.TELEGRAM_CHAT_ID || '';
        document.getElementById('cfg-safe-vspike').value = data.SAFE_VSPIKE_MIN || '';
        document.getElementById('cfg-normal-vspike').value = data.NORMAL_VSPIKE_MIN || '';
        document.getElementById('cfg-agr-vspike').value = data.AGGRESSIVE_VSPIKE_MIN || '';
        document.getElementById('cfg-safe-rsi').value = data.SAFE_RSI_MAX || '';
        document.getElementById('cfg-normal-rsi').value = data.NORMAL_RSI_MAX || '';
        document.getElementById('cfg-agr-rsi').value = data.AGGRESSIVE_RSI_MAX || '';
    } catch(e) {
        console.error("Failed to load settings", e);
    }
}

async function loadHistory(filename = '') {
    const container = document.getElementById('history-content');
    container.innerHTML = '<div class="empty-state">Memuat riwayat performa... (Bisa butuh 5-10 detik untuk ambil harga terbaru)</div>';
    
    try {
        const url = filename ? `/api/history?file=${filename}` : '/api/history';
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.status === 'success') {
            let html = `
                <div class="history-stats">
                    <div class="stat-box"><span>Evaluasi File</span><strong>${data.file.replace('bsjp_hasil_','').replace('.csv','')}</strong></div>
                    <div class="stat-box"><span>Total Saham</span><strong>${data.data.length}</strong></div>
                    <div class="stat-box"><span>Win Rate Hari Ini</span><strong style="color:${data.win_rate > 50 ? 'var(--accent-green)' : 'var(--accent-red)'}">${data.win_rate}%</strong></div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Rec. Buy</th>
                            <th>Target</th>
                            <th>Current Close</th>
                            <th>Profit/Loss</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.data.forEach(row => {
                let color = row.is_win ? 'var(--accent-green)' : 'var(--accent-red)';
                let sign = row.profit_pct > 0 ? '+' : '';
                html += `
                    <tr>
                        <td><strong>${row.ticker}</strong></td>
                        <td>${row.buy_price}</td>
                        <td>${row.target_price}</td>
                        <td>${row.current_price}</td>
                        <td style="color:${color}; font-weight:600;">${sign}${row.profit_pct}%</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = `<div class="empty-state">${data.message}</div>`;
        }
    } catch(e) {
        container.innerHTML = '<div class="empty-state" style="color:var(--accent-red)">Gagal mengevaluasi riwayat (koneksi Yahoo Finance bermasalah).</div>';
    }
}

async function loadHistoryFiles() {
    const listContainer = document.getElementById('history-files-list');
    listContainer.innerHTML = '<div class="empty-state" style="font-size:12px; padding:0;">Loading list...</div>';
    
    try {
        const res = await fetch('/api/history/files');
        const files = await res.json();
        
        listContainer.innerHTML = '';
        if (files && files.length > 0) {
            files.forEach((f, index) => {
                const btn = document.createElement('button');
                btn.className = 'history-file-btn';
                if (index === 0) btn.classList.add('active');
                btn.textContent = f.label;
                btn.setAttribute('data-filename', f.filename);
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.history-file-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    loadHistory(f.filename);
                });
                listContainer.appendChild(btn);
            });
            // Load the first report by default
            loadHistory(files[0].filename);
        } else {
            listContainer.innerHTML = '<div class="empty-state" style="font-size:12px; padding:0;">Belum ada hasil scan tersimpan.</div>';
            document.getElementById('history-content').innerHTML = '<div class="empty-state">Belum ada hasil scan harian. Silakan lakukan scan BSJP terlebih dahulu.</div>';
        }
    } catch(e) {
        listContainer.innerHTML = '<div class="empty-state" style="font-size:12px; padding:0; color:var(--accent-red)">Gagal memuat daftar.</div>';
        console.error(e);
    }
}
