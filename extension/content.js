const API_BASE_URL = "http://127.0.0.1:8000";
const OVERLAY_ID = "public-data-widget-overlay";

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
  document.getElementById(OVERLAY_ID)?.remove();
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
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 700;
      color: #334155;
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
  const dataset = chart?.datasets?.[0];
  if (!chart || !Array.isArray(chart.labels) || !dataset || !Array.isArray(dataset.data)) {
    return "";
  }

  const values = dataset.data.map((value) => Number(value)).filter((value) => Number.isFinite(value));
  const max = Math.max(...values, 1);

  return `
    <div class="pdw-chart">
      <div class="pdw-chart-title">${escapeHtml(dataset.label || "차트")}</div>
      ${chart.labels
        .map((label, index) => {
          const rawValue = Number(dataset.data[index] || 0);
          const width = Math.max(2, Math.round((rawValue / max) * 100));
          return `
            <div class="pdw-bar-row">
              <span>${escapeHtml(label)}</span>
              <span class="pdw-bar-track"><span class="pdw-bar-fill" style="width: ${width}%"></span></span>
              <span>${escapeHtml(rawValue)}${dataset.unit ? ` ${escapeHtml(dataset.unit)}` : ""}</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
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

  renderLoadingOverlay(query);
  fetchWidgetData(query)
    .then(renderOverlay)
    .catch(() => {
      renderErrorOverlay("백엔드가 실행 중인지 확인해주세요. 기본 주소는 http://127.0.0.1:8000 입니다.");
    });
})();
