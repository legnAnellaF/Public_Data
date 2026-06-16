const API_BASE_URL = "http://127.0.0.1:8000";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "FETCH_PUBLIC_DATA_WIDGET") {
    return false;
  }

  const query = message.query || "";
  const pageUrl = message.page_url || "";

  fetch(`${API_BASE_URL}/api/widget`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      query,
      page_url: pageUrl,
      source: "browser_extension"
    })
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

  return true;
});