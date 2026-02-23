const DEFAULTS = {
  global_enabled: false,
  dry_run: true,
  allowlist_patterns: [],
  button_texts: ["Submit", "Continue", "Apply", "Yes"],
  container_selector: "form, [role='dialog'], .modal, main",
  cooldown_ms: 5000,
  debounce_ms: 250,
  site_overrides: {},
  last_click_by_origin: {}
};

function storageGet(keys) {
  return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
}

function storageSet(values) {
  return new Promise((resolve) => chrome.storage.local.set(values, resolve));
}

function parseOrigin(url) {
  try {
    return new URL(url).origin;
  } catch (error) {
    return "";
  }
}

function wildcardToRegExp(pattern) {
  const escaped = pattern
    .trim()
    .replace(/[.+^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`, "i");
}

function matchesAllowlist(url, patterns) {
  if (!Array.isArray(patterns) || patterns.length === 0) {
    return false;
  }

  for (const pattern of patterns) {
    const text = String(pattern || "").trim();
    if (!text) {
      continue;
    }
    try {
      if (wildcardToRegExp(text).test(url)) {
        return true;
      }
    } catch (error) {
      console.warn("Invalid allowlist pattern:", text, error);
    }
  }
  return false;
}

async function ensureDefaults() {
  const existing = await storageGet(Object.keys(DEFAULTS));
  const missing = {};
  for (const [key, value] of Object.entries(DEFAULTS)) {
    if (existing[key] === undefined) {
      missing[key] = value;
    }
  }
  if (Object.keys(missing).length > 0) {
    await storageSet(missing);
  }
}

async function computeStatus(url) {
  const settings = await storageGet(Object.keys(DEFAULTS));
  const origin = parseOrigin(url);
  const siteOverrides = settings.site_overrides || {};
  const siteEnabled = origin ? siteOverrides[origin] !== false : false;
  const allowlisted = matchesAllowlist(url, settings.allowlist_patterns || []);
  const active = Boolean(settings.global_enabled && siteEnabled && allowlisted);

  return {
    origin,
    globalEnabled: Boolean(settings.global_enabled),
    dryRun: Boolean(settings.dry_run),
    siteEnabled,
    allowlisted,
    active
  };
}

async function updateBadgeForTab(tabId, url) {
  if (!tabId || !url) {
    return;
  }
  const status = await computeStatus(url);
  let text = "OFF";
  let color = "#6b7280";

  if (status.active) {
    text = status.dryRun ? "DRY" : "ON";
    color = status.dryRun ? "#d97706" : "#15803d";
  } else if (status.globalEnabled && !status.allowlisted) {
    text = "WL";
    color = "#b91c1c";
  }

  chrome.action.setBadgeText({ tabId, text });
  chrome.action.setBadgeBackgroundColor({ tabId, color });
}

async function refreshActiveTabBadge() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];
  if (!tab || !tab.id || !tab.url) {
    return;
  }
  await updateBadgeForTab(tab.id, tab.url);
}

chrome.runtime.onInstalled.addListener(() => {
  ensureDefaults()
    .then(() => refreshActiveTabBadge())
    .catch((error) => console.error("Install init failed:", error));
});

chrome.runtime.onStartup.addListener(() => {
  ensureDefaults()
    .then(() => refreshActiveTabBadge())
    .catch((error) => console.error("Startup init failed:", error));
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const tab = await chrome.tabs.get(tabId);
  if (tab.url) {
    await updateBadgeForTab(tabId, tab.url);
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  const url = changeInfo.url || tab.url;
  if (url) {
    await updateBadgeForTab(tabId, url);
  }
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") {
    return;
  }
  const keys = Object.keys(changes);
  if (keys.some((k) => Object.prototype.hasOwnProperty.call(DEFAULTS, k))) {
    refreshActiveTabBadge().catch((error) => console.error("Badge refresh failed:", error));
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    await ensureDefaults();

    if (message?.type === "get_tab_status") {
      const url = message.url || sender.tab?.url || "";
      const status = await computeStatus(url);
      sendResponse({ ok: true, status });
      return;
    }

    if (message?.type === "toggle_global") {
      const stored = await storageGet(["global_enabled"]);
      const next = !Boolean(stored.global_enabled);
      await storageSet({ global_enabled: next });
      await refreshActiveTabBadge();
      sendResponse({ ok: true, global_enabled: next });
      return;
    }

    if (message?.type === "set_global_enabled") {
      const enabled = Boolean(message.enabled);
      await storageSet({ global_enabled: enabled });
      await refreshActiveTabBadge();
      sendResponse({ ok: true, global_enabled: enabled });
      return;
    }

    if (message?.type === "set_dry_run") {
      const enabled = Boolean(message.enabled);
      await storageSet({ dry_run: enabled });
      await refreshActiveTabBadge();
      sendResponse({ ok: true, dry_run: enabled });
      return;
    }

    if (message?.type === "set_site_enabled") {
      const origin = parseOrigin(message.origin || sender.tab?.url || "");
      if (!origin) {
        sendResponse({ ok: false, error: "invalid_origin" });
        return;
      }
      const stored = await storageGet(["site_overrides"]);
      const siteOverrides = { ...(stored.site_overrides || {}) };
      siteOverrides[origin] = Boolean(message.enabled);
      await storageSet({ site_overrides: siteOverrides });
      await refreshActiveTabBadge();
      sendResponse({ ok: true, site_overrides: siteOverrides });
      return;
    }

    if (message?.type === "report_click") {
      const origin = parseOrigin(message.origin || sender.tab?.url || "");
      if (!origin) {
        sendResponse({ ok: false, error: "invalid_origin" });
        return;
      }
      const stored = await storageGet(["last_click_by_origin"]);
      const next = { ...(stored.last_click_by_origin || {}) };
      next[origin] = {
        at: message.at || new Date().toISOString(),
        label: message.label || "Submit",
        dryRun: Boolean(message.dryRun)
      };
      await storageSet({ last_click_by_origin: next });
      sendResponse({ ok: true });
      return;
    }

    sendResponse({ ok: false, error: "unknown_message_type" });
  })().catch((error) => {
    console.error("Message handler failure:", error);
    sendResponse({ ok: false, error: String(error) });
  });

  return true;
});

