const DEFAULTS = {
  global_enabled: false,
  dry_run: true,
  allowlist_patterns: [],
  site_overrides: {},
  last_click_by_origin: {}
};

function storageGet(keys) {
  return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
}

function runtimeSend(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
        return;
      }
      resolve(response || { ok: true });
    });
  });
}

function parseOrigin(url) {
  try {
    return new URL(url).origin;
  } catch (error) {
    return "";
  }
}

async function currentTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0] || null;
}

function setStatus(text, type) {
  const node = document.getElementById("statusText");
  node.textContent = text;
  if (type === "active") {
    node.style.background = "#dcfce7";
  } else if (type === "warning") {
    node.style.background = "#fef3c7";
  } else if (type === "error") {
    node.style.background = "#fee2e2";
  } else {
    node.style.background = "#e2e8f0";
  }
}

async function load() {
  const tab = await currentTab();
  const url = tab?.url || "";
  const origin = parseOrigin(url);
  const isHttp = /^https?:\/\//i.test(url);

  const statusResp = await runtimeSend({ type: "get_tab_status", url });
  const raw = await storageGet(Object.keys(DEFAULTS));
  const settings = { ...DEFAULTS, ...raw };

  const globalEnabledInput = document.getElementById("globalEnabled");
  const siteEnabledInput = document.getElementById("siteEnabled");
  const dryRunInput = document.getElementById("dryRun");

  globalEnabledInput.checked = Boolean(settings.global_enabled);
  dryRunInput.checked = Boolean(settings.dry_run);
  siteEnabledInput.disabled = !isHttp || !origin;

  if (statusResp?.ok && statusResp.status) {
    siteEnabledInput.checked = Boolean(statusResp.status.siteEnabled);
    if (statusResp.status.active) {
      setStatus(
        statusResp.status.dryRun ? "Active on this page (dry-run)." : "Active on this page (live).",
        "active"
      );
    } else if (statusResp.status.globalEnabled && !statusResp.status.allowlisted) {
      setStatus("Not active: URL is not in allowlist.", "warning");
    } else if (!statusResp.status.siteEnabled) {
      setStatus("Not active: disabled for this site.", "warning");
    } else {
      setStatus("Automation is paused.", "neutral");
    }
  } else {
    siteEnabledInput.checked = true;
    setStatus("Unable to read extension status.", "error");
  }

  const originText = document.getElementById("originText");
  originText.textContent = origin ? `Site: ${origin}` : "Site: unsupported page";

  const clickMap = settings.last_click_by_origin || {};
  const clickInfo = origin ? clickMap[origin] : null;
  const lastClickText = document.getElementById("lastClickText");
  if (clickInfo?.at) {
    const stamp = new Date(clickInfo.at).toLocaleString();
    const mode = clickInfo.dryRun ? "dry-run" : "live";
    lastClickText.textContent = `Last action: ${stamp} (${mode})`;
  } else {
    lastClickText.textContent = "Last action: none";
  }

  globalEnabledInput.dataset.origin = origin;
  siteEnabledInput.dataset.origin = origin;
  dryRunInput.dataset.origin = origin;
}

document.getElementById("openOptions").addEventListener("click", () => chrome.runtime.openOptionsPage());

document.getElementById("globalEnabled").addEventListener("change", async (event) => {
  const checkbox = event.currentTarget;
  await runtimeSend({ type: "set_global_enabled", enabled: checkbox.checked });
  await load();
});

document.getElementById("dryRun").addEventListener("change", async (event) => {
  const checkbox = event.currentTarget;
  await runtimeSend({ type: "set_dry_run", enabled: checkbox.checked });
  await load();
});

document.getElementById("siteEnabled").addEventListener("change", async (event) => {
  const checkbox = event.currentTarget;
  const origin = checkbox.dataset.origin || "";
  if (!origin) {
    return;
  }
  await runtimeSend({
    type: "set_site_enabled",
    origin,
    enabled: checkbox.checked
  });
  await load();
});

load().catch((error) => {
  console.error("Popup load failed:", error);
  setStatus("Popup failed to load status.", "error");
});
