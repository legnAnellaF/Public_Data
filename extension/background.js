const API_BASE_URL = "http://127.0.0.1:8000";

function postJson(endpoint, payload, sendResponse) {
  fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })
    .then(async (response) => {
      const data = await response.json();
      sendResponse({
        ok: response.ok,
        status: response.status,
        data
      });
    })
    .catch((error) => {
      sendResponse({
        ok: false,
        error: String(error)
      });
    });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) {
    return false;
  }

  const query = message.query || "";
  const pageUrl = message.page_url || "";

  if (message.type === "SEARCH_PUBLIC_DATASETS") {
    postJson(
      "/api/datasets/search",
      {
        query,
        page_url: pageUrl,
        source: "browser_extension",
        limit: message.limit || 5
      },
      sendResponse
    );
    return true;
  }

  if (message.type === "FETCH_PUBLIC_DATA_WIDGET") {
    const payload = {
      query,
      page_url: pageUrl,
      source: "browser_extension"
    };

    if (message.target_link) {
      payload.target_link = message.target_link;
    }

    postJson("/api/widget", payload, sendResponse);
    return true;
  }

  return false;
});
