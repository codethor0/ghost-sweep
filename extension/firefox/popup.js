async function loadCurrentPageUrl() {
  const pageUrlElement = document.getElementById("page-url");
  const reportLink = document.getElementById("report-link");

  if (!pageUrlElement || !reportLink) {
    return;
  }

  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const activeTab = tabs[0];
  const currentUrl = activeTab?.url ?? "No active tab URL available";
  pageUrlElement.textContent = currentUrl;

  const encodedUrl = encodeURIComponent(currentUrl);
  reportLink.href = `http://localhost:3000/?posting_url=${encodedUrl}`;
}

loadCurrentPageUrl().catch(() => {
  const pageUrlElement = document.getElementById("page-url");
  if (pageUrlElement) {
    pageUrlElement.textContent = "Unable to read the active tab URL.";
  }
});
