// Determine search query based on host
function getSearchQuery() {
    const url = new URL(window.location.href);
    if (window.location.hostname.includes("google")) {
        return url.searchParams.get("q");
    } else if (window.location.hostname.includes("naver")) {
        return url.searchParams.get("query");
    }
    return null;
}

// Global state to store search results for the "Back" button
let globalSearchResults = null;
let globalWidgetData = null;
let currentQuery = null;

async function fetchSearchList(query) {
    try {
        const response = await fetch("http://localhost:8000/api/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: query,
                page_url: window.location.href,
                source: "browser_extension"
            })
        });
        if (!response.ok) throw new Error("Network response was not ok");
        return await response.json();
    } catch (error) {
        console.error("[Data Overlay] Failed to fetch search list:", error);
        return null;
    }
}

async function fetchWidgetData(query, target_link) {
    try {
        const response = await fetch("http://localhost:8000/api/widget", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: query,
                page_url: window.location.href,
                source: "browser_extension",
                target_link: target_link
            })
        });
        if (!response.ok) throw new Error("Network response was not ok");
        return await response.json();
    } catch (error) {
        console.error("[Data Overlay] Failed to fetch data:", error);
        return null;
    }
}

function showLoading(title = "Loading BI Dashboard") {
    let container = document.getElementById("pd-dashboard-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "pd-dashboard-container";
        document.body.appendChild(container);
    }
    
    container.innerHTML = `
        <div id="pd-dashboard-header">
            <h3 class="pd-skeleton pd-skeleton-title" style="width: 200px; height: 24px;"></h3>
            <button id="pd-dashboard-close">&times;</button>
        </div>
        <div style="padding: 20px; text-align: center; color: #64748b; font-size: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 150px;">
            <div class="pd-spinner" style="width: 40px; height: 40px; border: 3px solid rgba(37, 99, 235, 0.2); border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px;"></div>
            <p>${title}</p>
        </div>
    `;

    // Add spin keyframes if not exists
    if (!document.getElementById("pd-spin-style")) {
        const style = document.createElement('style');
        style.id = "pd-spin-style";
        style.innerHTML = `@keyframes spin { to { transform: rotate(360deg); } }`;
        document.head.appendChild(style);
    }

    document.getElementById("pd-dashboard-close").addEventListener("click", () => {
        container.remove();
    });
}

function injectSearchList(data, query) {
    let container = document.getElementById("pd-dashboard-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "pd-dashboard-container";
        document.body.appendChild(container);
    }

    if (!data || data.status !== "ok" || !data.results || data.results.length === 0) {
        container.innerHTML = `
            <div id="pd-dashboard-header">
                <h3 id="pd-dashboard-title">검색 결과 없음</h3>
                <button id="pd-dashboard-close">&times;</button>
            </div>
            <p id="pd-dashboard-summary" style="padding-bottom: 20px;">'${query}'와(과) 관련된 공공데이터 파일(CSV/Excel)을 찾을 수 없습니다.</p>
        `;
        document.getElementById("pd-dashboard-close").addEventListener("click", () => container.remove());
        return;
    }

    const resultsHtml = data.results.map((item, index) => `
        <div class="pd-list-item" style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 8px; border: 1px solid #e2e8f0; transition: all 0.2s;">
            <div style="flex: 1; min-width: 0; padding-right: 12px; display: flex; align-items: center; gap: 10px;">
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; color: #2563eb; font-weight: bold; font-size: 13px; padding: 4px 8px; border-radius: 4px; white-space: nowrap;">
                    Top ${index + 1}
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="color: #1e293b; font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;">${item.title}</div>
                    <div style="color: #64748b; font-size: 12px;">🏢 ${item.provider}</div>
                </div>
            </div>
            <button class="pd-btn-visualize" data-link="${item.link}" style="background: #ffffff; color: #2563eb; border: 1px solid #bfdbfe; padding: 6px 12px; border-radius: 4px; font-weight: 600; font-size: 12px; cursor: pointer; white-space: nowrap; transition: all 0.2s;">
                📊 시각화
            </button>
        </div>
    `).join('');

    container.innerHTML = `
        <div id="pd-dashboard-header">
            <h3 id="pd-dashboard-title">🔎 '${query}' 연관 데이터셋 추천</h3>
            <div style="display: flex; align-items: center;">
                ${globalWidgetData ? `<button id="pd-btn-back-to-chart" style="background: #ffffff; border: 1px solid #e2e8f0; color: #475569; font-size: 13px; font-weight: bold; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-right: 12px; transition: all 0.2s;">⬅️ 이전 차트로</button>` : ''}
                <button id="pd-dashboard-close">&times;</button>
            </div>
        </div>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; font-size: 13px; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span>💡</span>
            <span><strong>추천 기준:</strong> 검색어 연관성이 높으며, 공공데이터포털 내 <strong>조회수 및 다운로드 수</strong>가 가장 많은 신뢰도 높은 데이터를 우선 선별했습니다.</span>
        </div>
        <div id="pd-list-container" style="max-height: 250px; overflow-y: auto; padding-right: 4px;">
            ${resultsHtml}
        </div>
    `;

    document.getElementById("pd-dashboard-close").addEventListener("click", () => container.remove());
    if (globalWidgetData) {
        document.getElementById("pd-btn-back-to-chart").addEventListener("click", () => injectWidget(globalWidgetData));
    }

    // Add hover effects and click listeners
    const listItems = container.querySelectorAll('.pd-list-item');
    const buttons = container.querySelectorAll('.pd-btn-visualize');
    
    listItems.forEach(item => {
        item.addEventListener('mouseenter', () => item.style.background = '#f1f5f9');
        item.addEventListener('mouseleave', () => item.style.background = '#f8fafc');
    });

    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.background = '#eff6ff';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.background = '#ffffff';
        });
        btn.addEventListener('click', async (e) => {
            const targetLink = e.target.getAttribute('data-link');
            showLoading("데이터 다운로드 및 AI 분석 중...");
            const data = await fetchWidgetData(currentQuery, targetLink);
            injectWidget(data);
        });
    });
}

let currentChart = null;
let currentPage = 0;
let itemsPerPage = 6;
let currentYear = null;
let currentDimension = null;

function renderTabs() {
    const widget = globalWidgetData.widget;
    
    const yearContainer = document.getElementById('pd-year-tabs');
    if (yearContainer) {
        yearContainer.innerHTML = widget.available_years.map(year => `
            <button class="pd-year-btn" data-year="${year}" style="
                background: ${year === currentYear ? '#f0fdf4' : '#f8fafc'};
                color: ${year === currentYear ? '#16a34a' : '#64748b'};
                border: 1px solid ${year === currentYear ? '#86efac' : '#e2e8f0'};
                padding: 6px 14px;
                border-radius: 14px;
                font-weight: bold;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
                white-space: nowrap;
            ">${year === '전체' ? '전체 기간' : year + '년'}</button>
        `).join('');
        
        yearContainer.querySelectorAll('.pd-year-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                currentYear = e.target.getAttribute('data-year');
                renderTabs();
                renderDashboardInner();
            });
        });
    }
    
    const dimContainer = document.getElementById('pd-dim-tabs');
    if (dimContainer) {
        dimContainer.innerHTML = widget.available_dimensions.map(dim => `
            <button class="pd-dim-btn" data-dim="${dim}" style="
                background: ${dim === currentDimension ? '#eff6ff' : 'transparent'};
                color: ${dim === currentDimension ? '#2563eb' : '#64748b'};
                border: none;
                border-bottom: 2px solid ${dim === currentDimension ? '#2563eb' : 'transparent'};
                padding: 6px 12px;
                font-weight: bold;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
                white-space: nowrap;
            ">${dim}</button>
        `).join('');
        
        dimContainer.querySelectorAll('.pd-dim-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                currentDimension = e.target.getAttribute('data-dim');
                renderTabs();
                renderDashboardInner();
            });
        });
    }
}

function injectWidget(data) {
    const container = document.getElementById("pd-dashboard-container");
    if (!container) return;

    if (!data || data.status !== "ok" || !data.widget) {
        container.innerHTML = `
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                <button id="pd-btn-back" style="background: #ffffff; border: 1px solid #e2e8f0; color: #475569; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 12px; border-radius: 4px; display: flex; align-items: center; transition: all 0.2s;">
                    ⬅️ 리스트로 뒤로가기
                </button>
                <button id="pd-dashboard-close" style="background: none; border: none; color: #94a3b8; font-size: 20px; cursor: pointer;">&times;</button>
            </div>
            <div id="pd-dashboard-header" style="margin-top: 0;">
                <h3 id="pd-dashboard-title">데이터 분석 실패</h3>
            </div>
            <p id="pd-dashboard-summary" style="padding-bottom: 20px;">서버 통신에 실패했거나 연관된 수치형 데이터가 없습니다.</p>
        `;
        document.getElementById("pd-dashboard-close").addEventListener("click", () => container.remove());
        document.getElementById("pd-btn-back").addEventListener("click", () => injectSearchList(globalSearchResults, currentQuery));
        return;
    }

    globalWidgetData = data;
    const widget = data.widget;
    
    if (widget.views && widget.available_years && widget.available_dimensions) {
        if (!currentYear || !widget.available_years.includes(currentYear)) {
            currentYear = widget.available_years[0];
        }
        if (!currentDimension || !widget.available_dimensions.includes(currentDimension)) {
            currentDimension = widget.available_dimensions[0];
        }
        
        container.innerHTML = `
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                <button id="pd-btn-back" style="background: #ffffff; border: 1px solid #e2e8f0; color: #475569; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 12px; border-radius: 4px; display: flex; align-items: center; transition: all 0.2s;">
                    ⬅️ 다른 연관 데이터 보기
                </button>
                <button id="pd-dashboard-close" style="background: none; border: none; color: #94a3b8; font-size: 20px; cursor: pointer;">&times;</button>
            </div>
            
            <div id="pd-tabs-container" style="margin-bottom: 15px;">
                <div id="pd-year-tabs" style="display: flex; gap: 8px; margin-bottom: 10px; overflow-x: auto; padding-bottom: 4px;"></div>
                <div id="pd-dim-tabs" style="display: flex; gap: 8px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; overflow-x: auto;"></div>
            </div>
            
            <div id="pd-dashboard-inner"></div>
        `;
        
        document.getElementById("pd-dashboard-close").addEventListener("click", () => container.remove());
        const btnBack = document.getElementById("pd-btn-back");
        btnBack.addEventListener("mouseenter", () => { btnBack.style.background = '#f8fafc'; });
        btnBack.addEventListener("mouseleave", () => { btnBack.style.background = '#ffffff'; });
        btnBack.addEventListener("click", () => injectSearchList(globalSearchResults, currentQuery));
        
        renderTabs();
        renderDashboardInner();
    } else {
        container.innerHTML = `<div id="pd-dashboard-inner"></div>`;
        renderDashboardInner(widget);
    }
}

function renderDashboardInner(legacyWidget = null) {
    let widget = legacyWidget;
    if (!widget && globalWidgetData && globalWidgetData.widget) {
        widget = globalWidgetData.widget;
        const activeView = widget.views[currentYear][currentDimension];
        widget.chart = {
            type: activeView.chart_type,
            labels: activeView.labels,
            datasets: activeView.datasets
        };
        widget.table_data = activeView.table_data;
        widget.title = activeView.chart_title;
    }
    
    const container = document.getElementById("pd-dashboard-inner");
    if (!container) return;
    
    currentPage = 0;
    
    let maxGlobalIndex = 0;
    let maxGlobalValue = -Infinity;
    
    // Find the target index matching the core keyword. If not found, fallback to max value.
    let keywordIdx = -1;
    if (widget.chart && widget.chart.datasets && widget.chart.datasets.length > 0 && widget.chart.datasets[0].data.length > 0) {
        widget.chart.datasets[0].data.forEach((v, i) => {
            if (v > maxGlobalValue) { maxGlobalValue = v; maxGlobalIndex = i; }
            if (widget.core_keyword && widget.chart.labels[i].includes(widget.core_keyword)) {
                keywordIdx = i;
            }
        });
        maxGlobalIndex = (keywordIdx !== -1) ? keywordIdx : maxGlobalIndex;
        maxGlobalValue = widget.chart.datasets[0].data[maxGlobalIndex];
    }

    const totalItemsRaw = widget.chart ? widget.chart.labels.length : 0;
    
    // 1. Separate Pinned Item from Normal Items
    let normalIndices = [];
    let pinnedIndex = -1;
    if (totalItemsRaw > 0) {
        pinnedIndex = maxGlobalIndex; // Pinned item is the matched keyword (or max)
        for (let i = 0; i < totalItemsRaw; i++) {
            if (i !== pinnedIndex) normalIndices.push(i);
        }
    }
    
    if (totalItemsRaw <= 8) {
        itemsPerPage = totalItemsRaw;
    } else {
        itemsPerPage = 6; // 5 normal + 1 pinned
    }
    
    const normalItemsPerPage = itemsPerPage === totalItemsRaw ? totalItemsRaw : itemsPerPage - 1;
    const totalPages = Math.ceil(normalIndices.length / normalItemsPerPage);

    // Calculate KPIs using the primary dataset (index 0)
    let total = 0, avg = 0, max = 0;
    if (widget.chart && widget.chart.datasets[0] && widget.chart.datasets[0].data.length > 0) {
        const dataset = widget.chart.datasets[0].data;
        total = dataset.reduce((a, b) => a + parseFloat(b || 0), 0);
        avg = (total / dataset.length).toFixed(1);
        max = Math.max(...dataset.map(v => parseFloat(v || 0)));
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    }

    const metricName = widget.chart && widget.chart.datasets.length > 0 ? widget.chart.datasets[0].label : '수치';
    const pureTopLabel = widget.chart && widget.chart.labels ? widget.chart.labels[maxGlobalIndex] : '';
    const defaultTopLabel = pureTopLabel ? `${pureTopLabel} (${metricName})` : '';
    
    let defaultTopValue = maxGlobalValue !== -Infinity ? formatNumber(maxGlobalValue) : '';
    const rawType = widget.chart && widget.chart.type ? widget.chart.type : 'bar';
    if ((rawType === 'pie' || rawType === 'doughnut') && total > 0 && maxGlobalValue !== -Infinity) {
        const pct = ((maxGlobalValue / total) * 100).toFixed(1);
        defaultTopValue += ` <span style="font-size: 22px; color: #94a3b8; font-weight: 500; margin-left: 8px;">(${pct}%)</span>`;
    }

    let topItemsHtml = '';
    if (widget.chart && widget.chart.labels && widget.chart.labels.length > 0 && widget.chart.datasets[0].data.length > 0) {
        const labels = widget.chart.labels;
        const data = widget.chart.datasets[0].data;
        
        let items = labels.map((label, idx) => ({
            label: label,
            value: parseFloat(data[idx] || 0)
        }));
        
        items.sort((a, b) => b.value - a.value);
        const top3 = items.slice(0, 3);
        
        const fontSizes = ['24px', '18px', '14px'];
        const colors = ['#10b981', '#10b981', '#10b981'];
        const weights = ['800', '600', '400'];
        
        const rankItems = top3.map((item, idx) => {
            return `<span style="font-size: ${fontSizes[idx]}; color: ${colors[idx]}; font-weight: ${weights[idx]}; margin: 0 10px;">
                ${idx + 1}. ${item.label}
            </span>`;
        }).join('');
        
        topItemsHtml = `
            <div style="display: flex; align-items: baseline; justify-content: center; flex-wrap: wrap; margin-top: 14px;">
                ${rankItems}
            </div>
        `;
    }

    const themeStr = currentQuery ? currentQuery : (widget.title || "데이터 현황 분석");

    const heroHtml = widget.chart && topItemsHtml ? `
        <div id="pd-hero-scorecard" style="text-align: center; margin-bottom: 16px; padding: 20px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="color: #0f172a; font-size: 22px; font-weight: 800; margin-bottom: 14px; letter-spacing: -0.5px;">${themeStr}</div>
            <div style="width: 40px; height: 3px; background: #22c55e; margin: 0 auto; border-radius: 2px;"></div>
            ${topItemsHtml}
        </div>
    ` : '';

    let tableHtml = '';
    if (widget.table_data && widget.table_data.headers && widget.table_data.rows) {
        const headers = widget.table_data.headers;
        const rows = widget.table_data.rows;
        
        const thHtml = headers.map(h => `<th style="padding: 10px; background: #f8fafc; color: #475569; font-size: 13px; font-weight: bold; text-align: left; border-bottom: 1px solid #e2e8f0; white-space: nowrap;">${h}</th>`).join('');
        
        const trHtml = rows.map((row, idx) => {
            const bg = idx % 2 === 0 ? '#fcfcfc' : '#ffffff';
            const tdHtml = row.map((cell, cidx) => {
                let cellText = cell;
                if (typeof cell === 'number') {
                    cellText = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 1 }).format(cell);
                }
                return `<td style="padding: 10px; border-bottom: 1px solid #f1f5f9; color: ${cidx === 0 ? '#2563eb' : '#334155'}; font-weight: ${cidx === 0 ? 'bold' : 'normal'}; font-size: 13px; white-space: nowrap;">${cellText}</td>`;
            }).join('');
            return `<tr style="background: ${bg}; transition: background 0.2s;" onmouseover="this.style.background='#eff6ff'" onmouseout="this.style.background='${bg}'">${tdHtml}</tr>`;
        }).join('');
        
        tableHtml = `
            <div style="margin-bottom: 20px; border-radius: 6px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <div style="background: #f8fafc; padding: 10px 14px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 14px;">📑</span> <span style="color: #475569; font-size: 13px; font-weight: bold;">원본 데이터 미리보기 (Top 50)</span>
                    </div>
                </div>
                <div style="max-height: 220px; overflow: auto;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead style="position: sticky; top: 0; z-index: 10; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                            <tr>${thHtml}</tr>
                        </thead>
                        <tbody>
                            ${trHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    const chartHtml = widget.chart ? `
        <div id="pd-dashboard-chart-area" style="position: relative; height: 350px; margin-bottom: 10px; border-radius: 6px; background: #ffffff; border: 1px solid #e2e8f0; padding: 10px; box-sizing: border-box;">
            <canvas id="pd-dashboard-canvas"></canvas>
        </div>
    ` : `
        <div style="height: 200px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 15px; background: #f8fafc; border-radius: 6px; margin-bottom: 15px; border: 1px dashed #cbd5e1;">
            <p>📊 ${widget.summary || "차트로 나타낼 수 있는 유효한 수치 데이터가 없습니다."}</p>
        </div>
    `;

    let precautionsHtml = '';
    if (widget.startup_precautions && widget.startup_precautions.length > 0) {
        const listHtml = widget.startup_precautions.map(p => `<li style="margin-bottom: 8px; line-height: 1.5; font-size: 13px; color: #1e293b;">${p}</li>`).join('');
        precautionsHtml = `
            <div style="margin-bottom: 15px; padding: 16px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                <div style="color: #b45309; font-size: 15px; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                    <span>🚨</span> <span>초보 창업자를 위한 AI 심층 분석 및 주의사항</span>
                </div>
                <ul style="margin: 0; padding-left: 20px;">
                    ${listHtml}
                </ul>
            </div>
        `;
    }

    container.innerHTML = `
        ${heroHtml}
        ${tableHtml}
        ${chartHtml}
        ${precautionsHtml}
        
        <div id="pd-dashboard-pagination-container" style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 10px; display: ${totalItemsRaw > itemsPerPage ? 'flex' : 'none'};">
            <button id="pd-btn-prev" style="background: #f8fafc; border: 1px solid #e2e8f0; color: #94a3b8; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 16px; border-radius: 4px; transition: all 0.2s;" disabled>
                ◀ 이전
            </button>
            <span id="pd-page-info" style="color: #475569; font-size: 13px; font-weight: bold;">
                1 / ${totalPages}
            </span>
            <button id="pd-btn-next" style="background: #ffffff; border: 1px solid #e2e8f0; color: #2563eb; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 16px; border-radius: 4px; transition: all 0.2s;">
                다음 ▶
            </button>
        </div>

        <div id="pd-dashboard-footer">
            <p id="pd-dashboard-source">출처: ${widget.source || '공공데이터포털'}</p>
            ${widget.file_name ? `<a id="pd-dashboard-download" href="http://localhost:8000/api/download?file=${encodeURIComponent(widget.file_name)}" target="_blank" download>💾 원본 엑셀 다운로드</a>` : ''}
        </div>
    `;

    // Render Chart.js
    if (widget.chart) {
        if (currentChart) {
            currentChart.destroy();
        }
        
        const ctx = document.getElementById("pd-dashboard-canvas").getContext("2d");
        
        const chartType = widget.chart.type || "bar";
        let actualChartType = chartType;
        let isHorizontal = false;
        let isHistogram = false;
        let isArea = false;
        let isDoughnut = false;
        let isScatter = false;

        if (chartType === "horizontal_bar") {
            actualChartType = "bar";
            isHorizontal = true;
        } else if (chartType === "histogram") {
            actualChartType = "bar";
            isHistogram = true;
        } else if (chartType === "area") {
            actualChartType = "line";
            isArea = true;
        } else if (chartType === "doughnut") {
            actualChartType = "doughnut";
            isDoughnut = true;
        } else if (chartType === "scatter") {
            actualChartType = "scatter";
            isScatter = true;
            // Scatter needs data transformed to {x, y}
            if (widget.chart.datasets.length >= 2) {
                const scatterData = [];
                const xData = widget.chart.datasets[0].data;
                const yData = widget.chart.datasets[1].data;
                for (let i = 0; i < Math.min(xData.length, yData.length, itemsPerPage); i++) {
                    scatterData.push({ x: parseFloat(xData[i]), y: parseFloat(yData[i]) });
                }
                widget.chart.datasets = [{
                    label: widget.chart.datasets[1].label + " vs " + widget.chart.datasets[0].label,
                    data: scatterData,
                }];
                widget.chart.labels = []; // clear labels for scatter
            }
        }
        
        const isMultiDataset = widget.chart.datasets.length > 1 && !isScatter;

        // Build dual y-axes config
        const scales = {};
        
        if (isHorizontal) {
            scales.x = {
                type: 'linear',
                display: false,
                beginAtZero: true,
                grace: '25%'
            };
            scales.y = {
                type: 'category',
                grid: { display: false },
                border: { display: false },
                ticks: { 
                    color: (context) => {
                        const lbl = context.chart && context.chart.data.labels[context.index];
                        const isPinned = lbl === widget.chart.labels[maxGlobalIndex];
                        return isPinned ? '#0f172a' : '#64748b';
                    }, 
                    font: (context) => {
                        const lbl = context.chart && context.chart.data.labels[context.index];
                        const isPinned = lbl === widget.chart.labels[maxGlobalIndex];
                        return {
                            family: "'Pretendard', sans-serif",
                            weight: isPinned ? 'bold' : 'normal',
                            size: isPinned ? 13 : 12
                        };
                    }
                }
            };
        } else {
            scales.x = {
                type: isScatter ? 'linear' : 'category',
                grid: { display: false },
                border: { display: false },
                ticks: { 
                    color: (context) => {
                        const lbl = context.chart && context.chart.data.labels[context.index];
                        const isPinned = lbl === widget.chart.labels[maxGlobalIndex];
                        return isPinned ? '#0f172a' : '#64748b';
                    }, 
                    font: (context) => {
                        const lbl = context.chart && context.chart.data.labels[context.index];
                        const isPinned = lbl === widget.chart.labels[maxGlobalIndex];
                        return {
                            family: "'Pretendard', sans-serif",
                            weight: isPinned ? 'bold' : 'normal',
                            size: isPinned ? 13 : 12
                        };
                    }
                },
                beginAtZero: isScatter
            };
            
            if (actualChartType !== 'pie' && actualChartType !== 'doughnut') {
                scales.y = {
                    type: 'linear',
                    display: false, // 수치를 숨겨서 깔끔하게
                    beginAtZero: true,
                    grace: '50%'
                };
            }
        }

        const palette = [
            { bg: 'rgba(16, 185, 129, 0.8)', border: '#10b981' }, // Green
            { bg: 'rgba(245, 158, 11, 0.8)', border: '#f59e0b' }, // Orange
            { bg: 'rgba(56, 189, 248, 0.8)', border: '#38bdf8' }, // Blue
            { bg: 'rgba(168, 85, 247, 0.8)', border: '#a855f7' }, // Purple
            { bg: 'rgba(236, 72, 153, 0.8)', border: '#ec4899' }, // Pink
        ];

        const multiColors = [
            { base: '#10b981', top: '#34d399', right: '#059669' }, // Green
            { base: '#f59e0b', top: '#fbbf24', right: '#d97706' }, // Orange
            { base: '#38bdf8', top: '#7dd3fc', right: '#0284c7' }, // Blue
            { base: '#a855f7', top: '#c084fc', right: '#7e22ce' }, // Purple
            { base: '#ec4899', top: '#f472b6', right: '#db2777' }, // Pink
        ];

        const getPageData = (page) => {
            if (isScatter) return { labels: [], dataIndices: [] };
            
            const start = page * itemsPerPage;
            const end = start + itemsPerPage;
            const pageNormalIndices = normalIndices.slice(start, end);
            
            let pageIndices = [...pageNormalIndices];
            if (pinnedIndex !== -1 && !pageIndices.includes(pinnedIndex)) {
                pageIndices.push(pinnedIndex);
            }
            
            // Sort to create staircase (descending)
            pageIndices.sort((a, b) => {
                const valA = widget.chart.datasets[0].data[a] || 0;
                const valB = widget.chart.datasets[0].data[b] || 0;
                return valB - valA;
            });
            
            return {
                labels: pageIndices.map(i => widget.chart.labels[i]),
                dataIndices: pageIndices
            };
        };

        const buildDatasets = (page) => {
            const { dataIndices } = getPageData(page);
            
            return widget.chart.datasets.map((ds, i) => {
                let type = actualChartType;
                let bgColor, borderColor;
                const c = palette[i % palette.length];
                
                let pointRadius = isScatter ? 6 : 3;
                let pointBgColor = c.border;

                const isScatterType = type === 'scatter';
                
                let targetData = [];
                if (isScatterType) {
                    targetData = ds.data;
                } else {
                    targetData = dataIndices.map(idx => ds.data[idx]);
                }

                if (isScatterType) {
                    bgColor = c.bg;
                    borderColor = c.border;
                } else if (actualChartType === 'pie' || actualChartType === 'doughnut') {
                    bgColor = dataIndices.map(idx => idx === maxGlobalIndex ? '#22c55e' : '#cbd5e1');
                    borderColor = dataIndices.map(idx => idx === maxGlobalIndex ? '#16a34a' : '#94a3b8');
                } else if (type === 'line' && !isScatterType) {
                    bgColor = isArea ? c.bg.replace('0.8', '0.2') : 'transparent';
                    borderColor = c.border;
                    pointBgColor = dataIndices.map(idx => idx === maxGlobalIndex ? '#fff' : c.bg);
                    pointRadius = dataIndices.map(idx => idx === maxGlobalIndex ? 7 : 3);
                } else {
                    if (isMultiDataset) {
                        bgColor = c.bg;
                        borderColor = c.border;
                    } else {
                        bgColor = dataIndices.map(idx => idx === maxGlobalIndex ? '#22c55e' : '#e2e8f0');
                        borderColor = dataIndices.map(idx => idx === maxGlobalIndex ? '#16a34a' : '#cbd5e1');
                    }
                }

                return {
                    label: ds.label,
                    data: targetData,
                    type: type,
                    yAxisID: (actualChartType === 'pie' || actualChartType === 'doughnut') ? undefined : 'y',
                    offset: (actualChartType === 'pie' || actualChartType === 'doughnut') ? dataIndices.map(idx => idx === maxGlobalIndex ? 20 : 0) : 0,
                    backgroundColor: bgColor,
                    borderColor: borderColor,
                    borderWidth: isScatter ? 0 : 2,
                    fill: isArea,
                    tension: 0.4,
                    pointBackgroundColor: pointBgColor,
                    pointRadius: pointRadius,
                    pointHoverRadius: isScatter ? 8 : 6,
                    borderRadius: (type === 'bar' && !isHistogram) ? 4 : 0,
                    maxBarThickness: 60,
                    categoryPercentage: isHistogram ? 1.0 : 0.8,
                    barPercentage: isHistogram ? 1.0 : 0.9,
                    _multiColors: isMultiDataset ? multiColors[i % multiColors.length] : null
                };
            });
        };

        let currentHoverIndex = null;

        const initialPageInfo = getPageData(0);
        let displayLabels = initialPageInfo.labels;
        
        if (!isScatter && (actualChartType === 'pie' || actualChartType === 'doughnut')) {
            const initialDataIndices = initialPageInfo.dataIndices;
            const primaryData = initialDataIndices.map(idx => widget.chart.datasets[0].data[idx]);
            const total = primaryData.reduce((sum, val) => sum + val, 0);
            displayLabels = displayLabels.map((lbl, idx) => {
                const val = primaryData[idx];
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return `${lbl} (${pct}%)`;
            });
        }

        const plugin3DBar = {
            id: 'plugin3DBar',
            afterDatasetsDraw(chart, args, options) {
                if (actualChartType !== 'bar') return;
                
                const ctx = chart.ctx;
                
                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    const meta = chart.getDatasetMeta(datasetIndex);
                    if (!meta.hidden) {
                        meta.data.forEach((element, index) => {
                            if (!element.width && !isHorizontal) return;
                            if (!element.height && isHorizontal) return;
                            
                            const val = dataset.data[index];
                            if (val === 0 || val === null || val === undefined) return;
                            
                            const lbl = chart.data.labels[index];
                            const isMax = lbl === widget.chart.labels[maxGlobalIndex];
                            
                            let topColor, rightColor;
                            if (dataset._multiColors) {
                                topColor = dataset._multiColors.top;
                                rightColor = dataset._multiColors.right;
                            } else {
                                topColor = isMax ? '#4ade80' : '#e2e8f0';
                                rightColor = isMax ? '#16a34a' : '#94a3b8';
                            }
                            
                            const { x, y, base, width, height } = element;
                            const dx = 12; // 3D depth x
                            const dy = -10; // 3D depth y
                            
                            ctx.save();
                            
                            if (isHorizontal) {
                                const h = height / 2;
                                
                                // Draw Top Face
                                ctx.fillStyle = topColor;
                                ctx.beginPath();
                                ctx.moveTo(base, y - h);
                                ctx.lineTo(base + dx, y - h + dy);
                                ctx.lineTo(x + dx, y - h + dy);
                                ctx.lineTo(x, y - h);
                                ctx.closePath();
                                ctx.fill();
                                
                                // Draw Right Face
                                ctx.fillStyle = rightColor;
                                ctx.beginPath();
                                ctx.moveTo(x, y - h);
                                ctx.lineTo(x + dx, y - h + dy);
                                ctx.lineTo(x + dx, y + h + dy);
                                ctx.lineTo(x, y + h);
                                ctx.closePath();
                                ctx.fill();
                                
                                // Draw Value Text
                                const textVal = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 1 }).format(val);
                                ctx.fillStyle = dataset._multiColors ? dataset._multiColors.base : (isMax ? '#16a34a' : '#475569');
                                ctx.textAlign = 'left';
                                ctx.textBaseline = 'middle';
                                const fontSize = isMax ? 22 : 13;
                                ctx.font = `bold ${fontSize}px 'Pretendard', sans-serif`;
                                ctx.fillText(textVal, x + dx + 10, y + dy);
                                
                            } else {
                                const w = width / 2;
                                
                                // Draw Right Face
                                ctx.fillStyle = rightColor;
                                ctx.beginPath();
                                ctx.moveTo(x + w, y);
                                ctx.lineTo(x + w + dx, y + dy);
                                ctx.lineTo(x + w + dx, base + dy);
                                ctx.lineTo(x + w, base);
                                ctx.closePath();
                                ctx.fill();
                                
                                // Draw Top Face
                                ctx.fillStyle = topColor;
                                ctx.beginPath();
                                ctx.moveTo(x - w, y);
                                ctx.lineTo(x - w + dx, y + dy);
                                ctx.lineTo(x + w + dx, y + dy);
                                ctx.lineTo(x + w, y);
                                ctx.closePath();
                                ctx.fill();
                                
                                // Draw Value Text
                                const textVal = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 1 }).format(val);
                                ctx.fillStyle = dataset._multiColors ? dataset._multiColors.base : (isMax ? '#16a34a' : '#475569');
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'bottom';
                                const fontSize = isMax ? 26 : 14;
                                ctx.font = `bold ${fontSize}px 'Pretendard', sans-serif`;
                                ctx.fillText(textVal, x + dx/2, y + dy - 6);
                            }
                            
                            ctx.restore();
                        });
                    }
                });
            }
        };

        const plugin3DPie = {
            id: 'plugin3DPie',
            beforeDatasetsDraw(chart, args, options) {
                if (actualChartType !== 'pie' && actualChartType !== 'doughnut') return;
                
                const ctx = chart.ctx;
                
                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    const meta = chart.getDatasetMeta(datasetIndex);
                    if (!meta.hidden) {
                        const depth = 15; // 3D depth
                        
                        for (let d = depth; d > 0; d--) {
                            meta.data.forEach((element, index) => {
                                const { startAngle, endAngle, innerRadius, outerRadius, x, y } = element;
                                if (!outerRadius) return;
                                
                                const pageInfo = getPageData(currentPage);
                                const originalIndex = pageInfo.dataIndices[index];
                                const isMax = originalIndex === maxGlobalIndex;
                                
                                ctx.save();
                                ctx.translate(x, y + d);
                                
                                ctx.beginPath();
                                ctx.arc(0, 0, outerRadius, startAngle, endAngle);
                                if (actualChartType === 'doughnut') {
                                    ctx.arc(0, 0, innerRadius, endAngle, startAngle, true);
                                } else {
                                    ctx.lineTo(0, 0);
                                }
                                ctx.closePath();
                                
                                ctx.fillStyle = isMax ? '#059669' : '#475569';
                                ctx.fill();
                                
                                // Draw stroke to define edges
                                ctx.strokeStyle = isMax ? '#059669' : '#475569';
                                ctx.lineWidth = 1;
                                ctx.stroke();
                                
                                ctx.restore();
                            });
                        }
                    }
                });
            },
            afterDatasetsDraw(chart, args, options) {
                if (actualChartType !== 'pie' && actualChartType !== 'doughnut') return;
                
                const ctx = chart.ctx;
                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    const meta = chart.getDatasetMeta(datasetIndex);
                    if (meta.hidden) return;
                    
                    meta.data.forEach((element, index) => {
                        const val = dataset.data[index];
                        if (!val || val === 0) return;
                        
                        const angle = element.endAngle - element.startAngle;
                        if (angle < 0.2) return; // Skip if slice is too small to fit text
                        
                        const pageInfo = getPageData(currentPage);
                        const originalIndex = pageInfo.dataIndices[index];
                        const isMax = originalIndex === maxGlobalIndex;
                        
                        let pctStr = '';
                        if (total > 0) pctStr = `${((val / total) * 100).toFixed(1)}%`;
                        
                        const pos = element.tooltipPosition();
                        
                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        
                        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                        ctx.shadowBlur = 4;
                        ctx.shadowOffsetY = 2;
                        
                        ctx.fillStyle = isMax ? '#ffffff' : '#f8fafc';
                        const formattedVal = new Intl.NumberFormat().format(val);
                        
                        if (isMax) {
                            ctx.font = `900 24px 'Pretendard', sans-serif`;
                            ctx.fillText(formattedVal, pos.x, pos.y - 12);
                            ctx.font = `bold 16px 'Pretendard', sans-serif`;
                            ctx.fillText(pctStr, pos.x, pos.y + 14);
                        } else {
                            ctx.font = `bold 13px 'Pretendard', sans-serif`;
                            ctx.fillText(formattedVal, pos.x, pos.y - 8);
                            ctx.font = `normal 12px 'Pretendard', sans-serif`;
                            ctx.fillText(pctStr, pos.x, pos.y + 8);
                        }
                        
                        ctx.restore();
                    });
                });
            }
        };

        currentChart = new Chart(ctx, {
            type: actualChartType,
            data: {
                labels: displayLabels,
                datasets: buildDatasets(0)
            },
            options: {
                indexAxis: isHorizontal ? 'y' : 'x',
                responsive: true,
                maintainAspectRatio: false,
                layout: { 
                    padding: { 
                        top: 45, 
                        right: isHorizontal ? 150 : 0,
                        bottom: (actualChartType === 'pie' || actualChartType === 'doughnut') ? 25 : 0
                    } 
                },
                animation: { duration: 1000, easing: 'easeOutQuart' },
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: isMultiDataset || isScatter,
                        position: 'top',
                        labels: { color: '#475569', font: {family: "'Pretendard', sans-serif"} }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.85)',
                        titleColor: '#94a3b8',
                        bodyColor: '#10b981',
                        padding: 14,
                        cornerRadius: 12,
                        displayColors: false,
                        titleFont: { size: 13, family: "'Pretendard', sans-serif", weight: 'normal' },
                        bodyFont: { size: 16, family: "'Pretendard', sans-serif", weight: 'bold' },
                        callbacks: {
                            title: function(context) {
                                const item = context[0];
                                const metricName = item.dataset.label || '';
                                const rawLabel = item.label || '';
                                return `${rawLabel} ${metricName}`;
                            },
                            label: function(context) { 
                                let labelStr = formatNumber(context.raw); 
                                if (actualChartType === 'pie' || actualChartType === 'doughnut') {
                                    const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                    const pct = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                                    labelStr += ` (${pct}%)`;
                                }
                                return labelStr;
                            }
                        }
                    }
                },
                scales: (actualChartType === 'pie' || actualChartType === 'doughnut') ? {} : scales
            },
            plugins: [plugin3DBar, plugin3DPie]
        });
        
        // Setup Pagination button logic
        const btnPrev = document.getElementById("pd-btn-prev");
        const btnNext = document.getElementById("pd-btn-next");
        const pageInfo = document.getElementById("pd-page-info");
        
        const updatePaginationUI = () => {
            if (currentPage === 0) {
                btnPrev.disabled = true;
                btnPrev.style.background = 'rgba(30, 41, 59, 0.8)';
                btnPrev.style.color = '#64748b';
                btnPrev.style.cursor = 'not-allowed';
            } else {
                btnPrev.disabled = false;
                btnPrev.style.background = 'rgba(56, 189, 248, 0.15)';
                btnPrev.style.color = '#38bdf8';
                btnPrev.style.cursor = 'pointer';
            }
            
            if (currentPage >= totalPages - 1) {
                btnNext.disabled = true;
                btnNext.style.background = 'rgba(30, 41, 59, 0.8)';
                btnNext.style.color = '#64748b';
                btnNext.style.cursor = 'not-allowed';
            } else {
                btnNext.disabled = false;
                btnNext.style.background = 'rgba(56, 189, 248, 0.15)';
                btnNext.style.color = '#38bdf8';
                btnNext.style.cursor = 'pointer';
            }
            pageInfo.innerText = `${currentPage + 1} / ${totalPages}`;
        };

        if (btnPrev && btnNext) {
            const updateChart = (page) => {
                const pageInfo = getPageData(page);
                currentChart.data.labels = pageInfo.labels;
                currentChart.data.datasets = buildDatasets(page);
                
                currentChart.update();
                updatePaginationUI();
            };

            btnPrev.addEventListener("click", () => {
                if (currentPage > 0) {
                    currentPage--;
                    updateChart(currentPage);
                }
            });
            
            btnNext.addEventListener("click", () => {
                if (currentPage < totalPages - 1) {
                    currentPage++;
                    updateChart(currentPage);
                }
            });
            updatePaginationUI();
        }
    }
}

async function init() {
    const query = getSearchQuery();
    if (query) {
        currentQuery = query;
        showLoading("공공데이터포털 검색 중...");
        setTimeout(async () => {
            const data = await fetchSearchList(query);
            globalSearchResults = data;
            
            // Zero-Click UX: 바로 데이터 시각화 실행
            if (data && data.status === "ok" && data.results && data.results.length > 0) {
                // 다중 데이터셋 시맨틱 조인이 필요한 복잡한 검색어인지 판별 (휴리스틱)
                const isComplexQuery = query.includes("와") || query.includes("과") || query.includes("비교") || query.includes("합쳐") || query.includes("융합") || query.includes(",");
                
                if (isComplexQuery) {
                    showLoading("✨ [AI Smart Join] 5개의 공공데이터 엑셀 파일을 다운로드하고 데이터를 융합 분석 중입니다... (약 10~15초 소요)");
                    const widgetData = await fetchWidgetData(query, "SMART_JOIN");
                    injectWidget(widgetData);
                } else {
                    showLoading("최적의 데이터를 다운로드 및 AI 분석 중...");
                    const topResult = data.results[0];
                    const widgetData = await fetchWidgetData(query, topResult.link);
                    injectWidget(widgetData);
                }
            } else {
                // 검색 결과가 아예 없으면 실패 화면 표시
                injectSearchList(data, query);
            }
        }, 800);
    }
}

init();
