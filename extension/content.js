const OVERLAY_ID = "public-data-widget-overlay";
const CHART_PAGE_SIZE = 8;
const CHART_COLORS = [
  { fill: "rgba(37, 99, 235, 0.72)", line: "rgba(37, 99, 235, 0.18)", border: "#2563eb" },
  { fill: "rgba(5, 150, 105, 0.72)", line: "rgba(5, 150, 105, 0.18)", border: "#059669" },
  { fill: "rgba(217, 119, 6, 0.72)", line: "rgba(217, 119, 6, 0.18)", border: "#d97706" },
  { fill: "rgba(219, 39, 119, 0.72)", line: "rgba(219, 39, 119, 0.18)", border: "#db2777" }
];

let activeChart = null;

const CATEGORY_LABELS = {
  environment_air_quality: "대기질",
  real_estate: "부동산",
  traffic: "교통",
  weather: "날씨",
  economy: "경제",
  unknown: "미지원"
};

function detectSearchQuery() {
  return getSearchQueryFromUrl() || getSearchQueryFromInput();
}

function getSearchQueryFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const host = window.location.hostname;
  const keys = host.includes("naver.com") ? ["query", "q"] : ["q", "query"];

  for (const key of keys) {
    const value = params.get(key);
    if (value && value.trim()) {
      return value.trim();
    }
  }

  return "";
}

function getSearchQueryFromInput() {
  const selectors = [
    'input[name="q"]',
    'input[name="query"]',
    'input[type="search"]',
    "#query"
  ];

  for (const selector of selectors) {
    const input = document.querySelector(selector);
    if (input && input.value && input.value.trim()) {
      return input.value.trim();
    }
  }

  return "";
}

function fetchWidgetData(query) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      {
        type: "FETCH_PUBLIC_DATA_WIDGET",
        query,
        page_url: window.location.href
      },
      (response) => {
        if (chrome.runtime.lastError) {
          resolve({
            ok: false,
            error: chrome.runtime.lastError.message
          });
          return;
        }

        resolve(response);
      }
    );
  });
}

async function loadAndRenderWidget(query) {
  renderLoadingOverlay(query);

  const response = await fetchWidgetData(query);

  if (!response || !response.ok) {
    renderErrorOverlay(
      response?.error || "백엔드 위젯 연결에 실패했습니다."
    );
    return;
  }

  renderOverlay(response.data);
}

function renderOverlay(apiResponse) {
  if (!apiResponse || typeof apiResponse !== "object") {
    renderErrorOverlay("위젯 응답 형식이 올바르지 않습니다.");
    return;
  }

  if (apiResponse.status === "unsupported") {
    renderMessageOverlay({
      title: "지원하지 않는 검색어",
      message: apiResponse.message || "현재 지원하지 않는 검색어입니다.",
      tone: "muted",
      apiResponse
    });
    return;
  }

  if (apiResponse.status === "error") {
    renderMessageOverlay({
      title: "위젯 오류",
      message: apiResponse.message || "공공데이터 위젯을 불러오지 못했습니다.",
      tone: "error",
      apiResponse
    });
    return;
  }

  if (apiResponse.status !== "ok" || !apiResponse.widget) {
    renderErrorOverlay("위젯 응답에 표시할 데이터가 없습니다.");
    return;
  }

  const widget = apiResponse.widget;
  const intent = apiResponse.intent || {};
  const source = widget.source || {};
  const shell = createOverlayShell();
  const category = CATEGORY_LABELS[intent.category] || intent.category || "분류 없음";
  const mockBadge = source.is_mock ? '<span class="pdw-badge pdw-badge-mock">mock</span>' : "";

  shell.body.innerHTML = `
    <div class="pdw-header-row">
      <div>
        <div class="pdw-eyebrow">${escapeHtml(apiResponse.query || "검색어")}</div>
        <h2>${escapeHtml(widget.title || "공공데이터 위젯")}</h2>
      </div>
      <button class="pdw-close" type="button" aria-label="닫기">×</button>
    </div>
    <div class="pdw-badge-row">
      <span class="pdw-badge">${escapeHtml(category)}</span>
      ${mockBadge}
    </div>
    <p class="pdw-summary">${escapeHtml(widget.summary || "공공데이터 기반 요약 정보입니다.")}</p>
    ${renderCards(widget.cards || [])}
    ${renderChart(widget.chart)}
    ${renderTable(widget.table)}
    <div class="pdw-source">출처: ${escapeHtml(source.name || "공공데이터")} ${
      source.updated_at ? `· ${escapeHtml(source.updated_at)}` : ""
    }</div>
  `;

  shell.body.querySelector(".pdw-close").addEventListener("click", removeExistingOverlay);
  mountOverlay(shell.overlay);
  hydrateChart(shell.body, widget.chart);
}

function renderLoadingOverlay(query) {
  const shell = createOverlayShell("loading");
  shell.body.innerHTML = `
    <div class="pdw-header-row">
      <div>
        <div class="pdw-eyebrow">${escapeHtml(query)}</div>
        <h2>공공데이터 위젯 불러오는 중</h2>
      </div>
      <button class="pdw-close" type="button" aria-label="닫기">×</button>
    </div>
    <p class="pdw-summary">검색어에 맞는 공공데이터를 확인하고 있습니다.</p>
  `;
  shell.body.querySelector(".pdw-close").addEventListener("click", removeExistingOverlay);
  mountOverlay(shell.overlay);
}

function renderErrorOverlay(message) {
  renderMessageOverlay({
    title: "공공데이터 위젯 연결 실패",
    message,
    tone: "error"
  });
}

function renderMessageOverlay({ title, message, tone, apiResponse }) {
  const shell = createOverlayShell(tone);
  const category = apiResponse?.intent?.category;
  const categoryLabel = category ? `<span class="pdw-badge">${escapeHtml(CATEGORY_LABELS[category] || category)}</span>` : "";

  shell.body.innerHTML = `
    <div class="pdw-header-row">
      <div>
        <div class="pdw-eyebrow">${escapeHtml(apiResponse?.query || "공공데이터")}</div>
        <h2>${escapeHtml(title)}</h2>
      </div>
      <button class="pdw-close" type="button" aria-label="닫기">×</button>
    </div>
    <div class="pdw-badge-row">${categoryLabel}</div>
    <p class="pdw-summary">${escapeHtml(message)}</p>
  `;

  shell.body.querySelector(".pdw-close").addEventListener("click", removeExistingOverlay);
  mountOverlay(shell.overlay);
}

function removeExistingOverlay() {
  destroyActiveChart();
  document.getElementById(OVERLAY_ID)?.remove();
}

function destroyActiveChart() {
  if (!activeChart) {
    return;
  }

  activeChart.destroy();
  activeChart = null;
}

function createOverlayShell(tone = "") {
  const overlay = document.createElement("aside");
  overlay.id = OVERLAY_ID;
  overlay.className = `pdw-overlay ${tone ? `pdw-${tone}` : ""}`;
  overlay.setAttribute("role", "complementary");

  const style = document.createElement("style");
  style.textContent = `
    #${OVERLAY_ID} {
      position: fixed;
      right: 20px;
      bottom: 20px;
      width: min(400px, calc(100vw - 32px));
      max-height: min(520px, calc(100vh - 32px));
      overflow: auto;
      z-index: 2147483647;
      box-sizing: border-box;
      padding: 18px;
      border: 1px solid #d8dee9;
      border-radius: 8px;
      background: #ffffff;
      color: #172033;
      box-shadow: 0 16px 48px rgba(15, 23, 42, 0.22);
      font-family: Arial, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
      line-height: 1.45;
    }
    #${OVERLAY_ID} * { box-sizing: border-box; }
    #${OVERLAY_ID} .pdw-header-row {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    #${OVERLAY_ID} h2 {
      margin: 2px 0 0;
      font-size: 18px;
      line-height: 1.3;
      color: #111827;
    }
    #${OVERLAY_ID} .pdw-eyebrow {
      font-size: 12px;
      color: #64748b;
      word-break: keep-all;
      overflow-wrap: anywhere;
    }
    #${OVERLAY_ID} .pdw-close {
      flex: 0 0 auto;
      width: 30px;
      height: 30px;
      border: 0;
      border-radius: 6px;
      background: #f1f5f9;
      color: #334155;
      font-size: 22px;
      line-height: 1;
      cursor: pointer;
    }
    #${OVERLAY_ID} .pdw-badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }
    #${OVERLAY_ID} .pdw-badge {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 3px 8px;
      border-radius: 999px;
      background: #e0f2fe;
      color: #075985;
      font-size: 12px;
      font-weight: 700;
    }
    #${OVERLAY_ID} .pdw-badge-mock {
      background: #fef3c7;
      color: #92400e;
    }
    #${OVERLAY_ID} .pdw-summary {
      margin: 12px 0;
      color: #475569;
      font-size: 14px;
    }
    #${OVERLAY_ID} .pdw-cards {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin: 12px 0;
    }
    #${OVERLAY_ID} .pdw-card {
      min-width: 0;
      padding: 10px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #f8fafc;
    }
    #${OVERLAY_ID} .pdw-card-label {
      font-size: 12px;
      color: #64748b;
    }
    #${OVERLAY_ID} .pdw-card-value {
      margin-top: 3px;
      font-size: 18px;
      font-weight: 800;
      color: #0f172a;
      overflow-wrap: anywhere;
    }
    #${OVERLAY_ID} .pdw-card-unit {
      margin-left: 3px;
      font-size: 12px;
      color: #64748b;
      font-weight: 500;
    }
    #${OVERLAY_ID} .pdw-chart {
      margin-top: 12px;
      padding: 10px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }
    #${OVERLAY_ID} .pdw-chart-title {
      font-size: 13px;
      font-weight: 700;
      color: #334155;
      min-width: 0;
      overflow-wrap: anywhere;
    }
    #${OVERLAY_ID} .pdw-chart-title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }
    #${OVERLAY_ID} .pdw-chart-meta {
      flex: 0 0 auto;
      color: #64748b;
      font-size: 11px;
    }
    #${OVERLAY_ID} .pdw-chart-canvas-wrap {
      position: relative;
      width: 100%;
      height: 220px;
    }
    #${OVERLAY_ID} .pdw-chart-canvas {
      width: 100% !important;
      height: 100% !important;
    }
    #${OVERLAY_ID} .pdw-chart-fallback {
      display: none;
    }
    #${OVERLAY_ID} .pdw-chart.pdw-chart-fallback-mode .pdw-chart-canvas-wrap {
      display: none;
    }
    #${OVERLAY_ID} .pdw-chart.pdw-chart-fallback-mode .pdw-chart-fallback {
      display: block;
    }
    #${OVERLAY_ID} .pdw-chart-controls {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 10px;
    }
    #${OVERLAY_ID} .pdw-chart-nav {
      min-width: 54px;
      min-height: 28px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #ffffff;
      color: #334155;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }
    #${OVERLAY_ID} .pdw-chart-nav:disabled {
      cursor: not-allowed;
      color: #94a3b8;
      background: #f8fafc;
    }
    #${OVERLAY_ID} .pdw-chart-page {
      min-width: 42px;
      text-align: center;
      color: #64748b;
      font-size: 12px;
      font-weight: 700;
    }
    #${OVERLAY_ID} .pdw-bar-row {
      display: grid;
      grid-template-columns: 82px 1fr auto;
      gap: 8px;
      align-items: center;
      margin: 6px 0;
      font-size: 12px;
      color: #475569;
    }
    #${OVERLAY_ID} .pdw-bar-track {
      height: 8px;
      overflow: hidden;
      border-radius: 999px;
      background: #e2e8f0;
    }
    #${OVERLAY_ID} .pdw-bar-fill {
      height: 100%;
      min-width: 2px;
      border-radius: inherit;
      background: #2563eb;
    }
    #${OVERLAY_ID} table {
      width: 100%;
      margin-top: 12px;
      border-collapse: collapse;
      font-size: 12px;
    }
    #${OVERLAY_ID} th,
    #${OVERLAY_ID} td {
      padding: 7px 6px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
      vertical-align: top;
    }
    #${OVERLAY_ID} th {
      color: #334155;
      background: #f8fafc;
    }
    #${OVERLAY_ID} .pdw-source {
      margin-top: 12px;
      color: #64748b;
      font-size: 12px;
    }
    #${OVERLAY_ID}.pdw-error {
      border-color: #fecaca;
    }
    @media (max-width: 480px) {
      #${OVERLAY_ID} {
        right: 12px;
        bottom: 12px;
        width: calc(100vw - 24px);
      }
      #${OVERLAY_ID} .pdw-cards {
        grid-template-columns: 1fr;
      }
    }
  `;

  const body = document.createElement("div");
  overlay.append(style, body);
  return { overlay, body };
}

function renderCards(cards) {
  if (!Array.isArray(cards) || cards.length === 0) {
    return "";
  }

  return `
    <div class="pdw-cards">
      ${cards
        .map(
          (card) => `
            <div class="pdw-card">
              <div class="pdw-card-label">${escapeHtml(card.label || "항목")}</div>
              <div class="pdw-card-value">
                ${escapeHtml(card.value ?? "")}
                ${card.unit ? `<span class="pdw-card-unit">${escapeHtml(card.unit)}</span>` : ""}
              </div>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderChart(chart) {
  const normalized = normalizeChart(chart);
  if (!normalized) {
    return "";
  }

  const title = normalized.datasets.length > 1
    ? `${normalized.datasets[0].label} 외 ${normalized.datasets.length - 1}개 지표`
    : normalized.datasets[0].label;
  const totalPages = getChartPageCount(normalized);
  const controls = totalPages > 1
    ? `
      <div class="pdw-chart-controls">
        <button class="pdw-chart-nav" type="button" data-pdw-chart-prev>이전</button>
        <span class="pdw-chart-page" data-pdw-chart-page>1 / ${totalPages}</span>
        <button class="pdw-chart-nav" type="button" data-pdw-chart-next>다음</button>
      </div>
    `
    : "";

  return `
    <div class="pdw-chart" data-pdw-chart>
      <div class="pdw-chart-title-row">
        <div class="pdw-chart-title">${escapeHtml(title || "차트")}</div>
        <div class="pdw-chart-meta">${escapeHtml(getChartTypeLabel(normalized.type))}</div>
      </div>
      <div class="pdw-chart-canvas-wrap">
        <canvas class="pdw-chart-canvas"></canvas>
      </div>
      <div class="pdw-chart-fallback">${renderFallbackBars(normalized, 0)}</div>
      ${controls}
    </div>
  `;
}

function normalizeChart(chart) {
  if (!chart || !Array.isArray(chart.labels) || !Array.isArray(chart.datasets)) {
    return null;
  }

  const labels = chart.labels.map((label) => String(label ?? ""));
  if (labels.length === 0) {
    return null;
  }

  const datasets = [];
  chart.datasets.forEach((dataset, index) => {
    const sourceData = Array.isArray(dataset?.data) ? dataset.data : [];
    const hasFiniteData = sourceData
      .slice(0, labels.length)
      .some((value) => Number.isFinite(Number(value)));

    if (!hasFiniteData) {
      return;
    }

    datasets.push({
      label: String(dataset?.label || `데이터 ${index + 1}`),
      unit: String(dataset?.unit || ""),
      data: labels.map((_, dataIndex) => {
        const value = Number(sourceData[dataIndex]);
        return Number.isFinite(value) ? value : 0;
      })
    });
  });

  if (datasets.length === 0) {
    return null;
  }

  return {
    type: normalizeChartType(chart.type),
    labels,
    datasets
  };
}

function normalizeChartType(type) {
  const normalizedType = String(type || "bar").toLowerCase();
  if (["bar", "line", "horizontal_bar", "histogram"].includes(normalizedType)) {
    return normalizedType;
  }
  return "bar";
}

function getChartTypeLabel(type) {
  const labels = {
    bar: "bar",
    line: "line",
    horizontal_bar: "horizontal",
    histogram: "histogram"
  };
  return labels[type] || "chart";
}

function getRenderableChartType(type) {
  return type === "line" ? "line" : "bar";
}

function getChartPageCount(chart) {
  return Math.max(1, Math.ceil(chart.labels.length / CHART_PAGE_SIZE));
}

function getChartPageBounds(chart, page) {
  const start = page * CHART_PAGE_SIZE;
  const end = Math.min(start + CHART_PAGE_SIZE, chart.labels.length);
  return { start, end };
}

function getChartPageLabels(chart, page) {
  const { start, end } = getChartPageBounds(chart, page);
  return chart.labels.slice(start, end);
}

function hydrateChart(root, chart) {
  const chartElement = root.querySelector("[data-pdw-chart]");
  const normalized = normalizeChart(chart);
  if (!chartElement || !normalized) {
    return;
  }

  const canvas = chartElement.querySelector(".pdw-chart-canvas");
  const fallback = chartElement.querySelector(".pdw-chart-fallback");
  const prevButton = chartElement.querySelector("[data-pdw-chart-prev]");
  const nextButton = chartElement.querySelector("[data-pdw-chart-next]");
  const pageInfo = chartElement.querySelector("[data-pdw-chart-page]");
  const totalPages = getChartPageCount(normalized);
  let currentPage = 0;

  function updatePagination() {
    if (pageInfo) {
      pageInfo.textContent = `${currentPage + 1} / ${totalPages}`;
    }
    if (prevButton) {
      prevButton.disabled = currentPage === 0;
    }
    if (nextButton) {
      nextButton.disabled = currentPage >= totalPages - 1;
    }
  }

  function renderFallbackPage() {
    chartElement.classList.add("pdw-chart-fallback-mode");
    if (fallback) {
      fallback.innerHTML = renderFallbackBars(normalized, currentPage);
    }
    updatePagination();
  }

  function updateChartPage() {
    if (!activeChart) {
      renderFallbackPage();
      return;
    }

    activeChart.data.labels = getChartPageLabels(normalized, currentPage);
    activeChart.data.datasets = buildChartDatasets(normalized, currentPage);
    activeChart.update();
    updatePagination();
  }

  function wirePagination(updatePage) {
    prevButton?.addEventListener("click", () => {
      if (currentPage === 0) {
        return;
      }
      currentPage -= 1;
      updatePage();
    });

    nextButton?.addEventListener("click", () => {
      if (currentPage >= totalPages - 1) {
        return;
      }
      currentPage += 1;
      updatePage();
    });

    updatePage();
  }

  if (typeof Chart === "undefined" || !canvas) {
    wirePagination(renderFallbackPage);
    return;
  }

  try {
    activeChart = new Chart(canvas.getContext("2d"), {
      type: getRenderableChartType(normalized.type),
      data: {
        labels: getChartPageLabels(normalized, 0),
        datasets: buildChartDatasets(normalized, 0)
      },
      options: buildChartOptions(normalized)
    });
    chartElement.classList.remove("pdw-chart-fallback-mode");
    wirePagination(updateChartPage);
  } catch (error) {
    console.warn("[Public Data Widget] Chart rendering failed", error);
    destroyActiveChart();
    wirePagination(renderFallbackPage);
  }
}

function buildChartDatasets(chart, page) {
  const { start, end } = getChartPageBounds(chart, page);
  const actualType = getRenderableChartType(chart.type);
  const isHistogram = chart.type === "histogram";
  const isHorizontal = chart.type === "horizontal_bar";
  const useCombo = chart.datasets.length > 1 && actualType === "bar" && !isHistogram && !isHorizontal;

  return chart.datasets.map((dataset, index) => {
    const color = CHART_COLORS[index % CHART_COLORS.length];
    const datasetType = useCombo && index % 2 === 1 ? "line" : actualType;
    const yAxisID = useCombo && index % 2 === 1 ? "y1" : "y";

    return {
      label: dataset.label,
      data: dataset.data.slice(start, end),
      type: datasetType,
      yAxisID: isHorizontal ? undefined : yAxisID,
      backgroundColor: datasetType === "line" ? color.line : color.fill,
      borderColor: color.border,
      borderWidth: 2,
      borderRadius: datasetType === "bar" && !isHistogram ? 4 : 0,
      categoryPercentage: isHistogram ? 1 : 0.72,
      barPercentage: isHistogram ? 1 : 0.82,
      fill: datasetType === "line" ? false : isHistogram,
      tension: 0.35
    };
  });
}

function buildChartOptions(chart) {
  const isHorizontal = chart.type === "horizontal_bar";
  const isHistogram = chart.type === "histogram";
  const actualType = getRenderableChartType(chart.type);
  const useCombo = chart.datasets.length > 1 && actualType === "bar" && !isHistogram && !isHorizontal;
  const scales = {
    x: {
      beginAtZero: isHorizontal,
      grid: { color: "rgba(148, 163, 184, 0.18)" },
      ticks: { color: "#475569", maxRotation: 0, autoSkip: true }
    },
    y: {
      beginAtZero: true,
      grid: { color: "rgba(148, 163, 184, 0.18)" },
      ticks: { color: "#475569" }
    }
  };

  if (useCombo) {
    scales.y1 = {
      beginAtZero: true,
      position: "right",
      grid: { drawOnChartArea: false },
      ticks: { color: "#475569" }
    };
  }

  return {
    indexAxis: isHorizontal ? "y" : "x",
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        display: chart.datasets.length > 1,
        position: "bottom",
        labels: {
          boxWidth: 10,
          boxHeight: 10,
          color: "#334155"
        }
      },
      tooltip: {
        callbacks: {
          label(context) {
            const dataset = chart.datasets[context.datasetIndex] || {};
            const rawValue = Number(context.raw);
            const value = Number.isFinite(rawValue) ? rawValue : 0;
            const label = context.dataset.label ? `${context.dataset.label}: ` : "";
            return `${label}${formatChartValue(value, dataset.unit)}`;
          }
        }
      }
    },
    scales
  };
}

function renderFallbackBars(chart, page) {
  const { start, end } = getChartPageBounds(chart, page);
  const dataset = chart.datasets[0];
  const labels = chart.labels.slice(start, end);
  const values = dataset.data.slice(start, end);
  const max = Math.max(...values.map((value) => Math.abs(value)), 1);

  return labels
    .map((label, index) => {
      const rawValue = values[index] || 0;
      const width = Math.max(2, Math.round((Math.abs(rawValue) / max) * 100));
      const color = CHART_COLORS[index % CHART_COLORS.length].border;
      return `
        <div class="pdw-bar-row">
          <span>${escapeHtml(label)}</span>
          <span class="pdw-bar-track"><span class="pdw-bar-fill" style="width: ${width}%; background: ${color}"></span></span>
          <span>${escapeHtml(formatChartValue(rawValue, dataset.unit))}</span>
        </div>
      `;
    })
    .join("");
}

function formatChartValue(value, unit = "") {
  const formatted = new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 2
  }).format(value);
  return unit ? `${formatted} ${unit}` : formatted;
}

function renderTable(table) {
  if (!table || !Array.isArray(table.columns) || !Array.isArray(table.rows) || table.rows.length === 0) {
    return "";
  }

  return `
    <table>
      <thead>
        <tr>${table.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${table.rows
          .slice(0, 6)
          .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`)
          .join("")}
      </tbody>
    </table>
  `;
}

function mountOverlay(overlay) {
  removeExistingOverlay();
  document.documentElement.appendChild(overlay);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    };
    return entities[char];
  });
}

(function initPublicDataWidget() {
  const query = detectSearchQuery();
  if (!query) {
    return;
  }

  loadAndRenderWidget(query).catch(() => {
    renderErrorOverlay("백엔드가 실행 중인지 확인해주세요. 기본 주소는 http://127.0.0.1:8000 입니다.");
  });
})();
