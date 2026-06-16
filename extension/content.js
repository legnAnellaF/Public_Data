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
        <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 150px;">
            <div class="pd-spinner" style="width: 40px; height: 40px; border: 3px solid rgba(56, 189, 248, 0.2); border-top-color: #38bdf8; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px;"></div>
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
        <div class="pd-list-item" style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(30, 41, 59, 0.5); border-radius: 8px; margin-bottom: 8px; border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.2s;">
            <div style="flex: 1; min-width: 0; padding-right: 12px;">
                <div style="color: #f8fafc; font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;">${item.title}</div>
                <div style="color: #94a3b8; font-size: 12px;">🏢 ${item.provider}</div>
            </div>
            <button class="pd-btn-visualize" data-link="${item.link}" style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2); padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; cursor: pointer; white-space: nowrap; transition: all 0.2s;">
                📊 시각화
            </button>
        </div>
    `).join('');

    container.innerHTML = `
        <div id="pd-dashboard-header">
            <h3 id="pd-dashboard-title">🔎 '${query}' 연관 데이터셋 Top 5</h3>
            <button id="pd-dashboard-close">&times;</button>
        </div>
        <p id="pd-dashboard-summary" style="margin-bottom: 12px;">분석하고 싶은 데이터를 선택하여 시각화 버튼을 눌러주세요.</p>
        <div id="pd-list-container" style="max-height: 250px; overflow-y: auto; padding-right: 4px;">
            ${resultsHtml}
        </div>
    `;

    document.getElementById("pd-dashboard-close").addEventListener("click", () => container.remove());

    // Add hover effects and click listeners
    const listItems = container.querySelectorAll('.pd-list-item');
    const buttons = container.querySelectorAll('.pd-btn-visualize');
    
    listItems.forEach(item => {
        item.addEventListener('mouseenter', () => item.style.background = 'rgba(30, 41, 59, 0.8)');
        item.addEventListener('mouseleave', () => item.style.background = 'rgba(30, 41, 59, 0.5)');
    });

    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.background = 'rgba(56, 189, 248, 0.2)';
            btn.style.color = '#bae6fd';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.background = 'rgba(56, 189, 248, 0.1)';
            btn.style.color = '#38bdf8';
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
const itemsPerPage = 15;

function injectWidget(data) {
    const container = document.getElementById("pd-dashboard-container");
    if (!container) return; // If user closed it

    if (!data || data.status !== "ok" || !data.widget) {
        // Handle Error State
        container.innerHTML = `
            <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
                <button id="pd-btn-back" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 12px; border-radius: 6px; display: flex; align-items: center; transition: all 0.2s;">
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

    const widget = data.widget;
    
    // Calculate KPIs using the primary dataset (index 0)
    let total = 0, avg = 0, max = 0;
    if (widget.chart && widget.chart.datasets[0] && widget.chart.datasets[0].data.length > 0) {
        const dataset = widget.chart.datasets[0].data;
        total = dataset.reduce((a, b) => a + b, 0);
        avg = (total / dataset.length).toFixed(1);
        max = Math.max(...dataset);
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    }

    // Reset pagination state
    currentPage = 0;
    const totalItems = widget.chart ? widget.chart.labels.length : 0;
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    // Build widget HTML
    container.innerHTML = `
        <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
            <button id="pd-btn-back" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 12px; border-radius: 6px; display: flex; align-items: center; transition: all 0.2s;">
                ⬅️ 리스트로 뒤로가기
            </button>
            <button id="pd-dashboard-close" style="background: none; border: none; color: #94a3b8; font-size: 20px; cursor: pointer;">&times;</button>
        </div>
        <div id="pd-dashboard-header" style="margin-top: 0;">
            <h3 id="pd-dashboard-title" style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${widget.title}</h3>
        </div>
        <p id="pd-dashboard-summary">${widget.summary}</p>
        
        <div class="pd-dashboard-kpi-row">
            <div class="pd-kpi-card">
                <div class="pd-kpi-title">주요지표 합계</div>
                <div class="pd-kpi-val">${formatNumber(total)}</div>
            </div>
            <div class="pd-kpi-card">
                <div class="pd-kpi-title">주요지표 평균</div>
                <div class="pd-kpi-val">${formatNumber(avg)}</div>
            </div>
            <div class="pd-kpi-card">
                <div class="pd-kpi-title">최고 수치</div>
                <div class="pd-kpi-val">${formatNumber(max)}</div>
            </div>
        </div>

        <div id="pd-dashboard-chart-area" style="position: relative; height: 300px; margin-bottom: 10px;">
            <canvas id="pd-dashboard-canvas"></canvas>
        </div>
        
        <div id="pd-dashboard-pagination-container" style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 10px; display: ${totalItems > itemsPerPage ? 'flex' : 'none'};">
            <button id="pd-btn-prev" style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); color: #f8fafc; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 16px; border-radius: 6px; transition: all 0.2s;" disabled>
                ◀ 이전
            </button>
            <span id="pd-page-info" style="color: #94a3b8; font-size: 13px; font-weight: bold;">
                1 / ${totalPages}
            </span>
            <button id="pd-btn-next" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; font-weight: bold; font-size: 13px; cursor: pointer; padding: 6px 16px; border-radius: 6px; transition: all 0.2s;">
                다음 ▶
            </button>
        </div>

        <div id="pd-dashboard-footer">
            <p id="pd-dashboard-source">출처: ${widget.source}</p>
            ${widget.file_name ? `<a id="pd-dashboard-download" href="http://localhost:8000/api/download?file=${encodeURIComponent(widget.file_name)}" target="_blank" download>💾 원본 엑셀 다운로드</a>` : ''}
        </div>
    `;

    document.getElementById("pd-dashboard-close").addEventListener("click", () => container.remove());
    
    const btnBack = document.getElementById("pd-btn-back");
    btnBack.addEventListener("mouseenter", () => { btnBack.style.background = 'rgba(56, 189, 248, 0.25)'; btnBack.style.color = '#bae6fd'; });
    btnBack.addEventListener("mouseleave", () => { btnBack.style.background = 'rgba(56, 189, 248, 0.15)'; btnBack.style.color = '#38bdf8'; });
    btnBack.addEventListener("click", () => injectSearchList(globalSearchResults, currentQuery));

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

        if (chartType === "horizontal_bar") {
            actualChartType = "bar";
            isHorizontal = true;
        } else if (chartType === "histogram") {
            actualChartType = "bar";
            isHistogram = true;
        }
        
        // Setup premium colors for multi-datasets
        const paletteBackgrounds = [
            'rgba(99, 102, 241, 0.7)',
            'rgba(16, 185, 129, 0.7)',
            'rgba(245, 158, 11, 0.7)',
            'rgba(236, 72, 153, 0.7)'
        ];
        const paletteBorders = [
            'rgb(99, 102, 241)',
            'rgb(16, 185, 129)',
            'rgb(245, 158, 11)',
            'rgb(236, 72, 153)'
        ];
        
        const isMultiDataset = widget.chart.datasets.length > 1;

        // Build dual y-axes config
        const scales = {
            x: {
                grid: { display: isHorizontal, color: 'rgba(255, 255, 255, 0.05)', borderDash: [5, 5] },
                ticks: { color: '#94a3b8', font: {family: "'Pretendard', sans-serif"} },
                beginAtZero: isHorizontal
            }
        };

        if (actualChartType !== 'pie') {
            scales.y = {
                type: 'linear',
                display: true,
                position: isHorizontal ? 'bottom' : 'left',
                grid: { color: isHorizontal ? 'transparent' : 'rgba(255, 255, 255, 0.05)', borderDash: [5, 5] },
                ticks: { color: '#94a3b8', font: {family: "'Pretendard', sans-serif"} },
                beginAtZero: true
            };
            
            // If multiple datasets and not horizontal, use a secondary Y axis
            if (isMultiDataset && !isHorizontal && !isHistogram) {
                scales.y1 = {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#94a3b8', font: {family: "'Pretendard', sans-serif"} },
                    beginAtZero: true
                };
            }
        }

        const buildDatasets = (page) => {
            const start = page * itemsPerPage;
            const end = start + itemsPerPage;
            return widget.chart.datasets.map((ds, i) => {
                let yAxisID = 'y';
                let type = actualChartType;
                
                if (isMultiDataset && !isHorizontal && !isHistogram) {
                    if (i === 1) {
                        yAxisID = 'y1';
                        type = 'line'; // Force line for 2nd dataset for combo chart
                    } else if (i === 2) {
                        yAxisID = 'y1';
                        type = 'bar'; // 3rd dataset
                    }
                }
                
                // Color index modulo length just in case
                const cIdx = i % paletteBackgrounds.length;
                
                return {
                    label: ds.label,
                    data: ds.data.slice(start, end),
                    type: type,
                    yAxisID: actualChartType === 'pie' ? undefined : yAxisID,
                    backgroundColor: (type === 'line' || isHistogram) ? paletteBackgrounds[cIdx].replace('0.7', '0.2') : paletteBackgrounds[cIdx],
                    borderColor: paletteBorders[cIdx],
                    borderWidth: 2,
                    fill: type === 'line' || isHistogram,
                    tension: 0.4,
                    borderRadius: (type === 'bar' && !isHistogram) ? 4 : 0,
                    categoryPercentage: isHistogram ? 1.0 : 0.8,
                    barPercentage: isHistogram ? 1.0 : 0.9,
                };
            });
        };

        currentChart = new Chart(ctx, {
            type: actualChartType,
            data: {
                labels: widget.chart.labels.slice(0, itemsPerPage),
                datasets: buildDatasets(0)
            },
            options: {
                indexAxis: isHorizontal ? 'y' : 'x',
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: actualChartType === 'pie' || isMultiDataset,
                        position: 'top',
                        labels: { color: '#e5e7eb', font: {family: "'Pretendard', sans-serif"} }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: true,
                        titleFont: { size: 14, family: "'Pretendard', sans-serif" },
                        bodyFont: { size: 13, family: "'Pretendard', sans-serif" }
                    }
                },
                scales: actualChartType === 'pie' ? {} : scales
            }
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
            btnPrev.addEventListener("click", () => {
                if (currentPage > 0) {
                    currentPage--;
                    updatePaginationUI();
                    currentChart.data.labels = widget.chart.labels.slice(currentPage * itemsPerPage, (currentPage + 1) * itemsPerPage);
                    currentChart.data.datasets = buildDatasets(currentPage);
                    currentChart.update();
                }
            });
            btnNext.addEventListener("click", () => {
                if (currentPage < totalPages - 1) {
                    currentPage++;
                    updatePaginationUI();
                    currentChart.data.labels = widget.chart.labels.slice(currentPage * itemsPerPage, (currentPage + 1) * itemsPerPage);
                    currentChart.data.datasets = buildDatasets(currentPage);
                    currentChart.update();
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
            injectSearchList(data, query);
        }, 800);
    }
}

init();
