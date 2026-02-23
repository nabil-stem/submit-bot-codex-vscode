const DEFAULTS = {
  global_enabled: false,
  dry_run: true,
  allowlist_patterns: [],
  button_texts: ["Submit", "Continue", "Apply", "Yes"],
  container_selector: "form, [role='dialog'], .modal, main",
  cooldown_ms: 5000,
  debounce_ms: 250,
  site_overrides: {}
};

const state = {
  config: { ...DEFAULTS },
  active: false,
  lastActionMs: 0,
  lastClickIso: null,
  overlay: null,
  observer: null,
  debounceTimer: null
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

function normalizeText(text) {
  return String(text || "").replace(/\s+/g, " ").trim().toLowerCase();
}

function wildcardToRegExp(pattern) {
  const escaped = String(pattern || "")
    .trim()
    .replace(/[.+^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`, "i");
}

function urlMatchesAllowlist(url, patterns) {
  if (!Array.isArray(patterns) || patterns.length === 0) {
    return false;
  }
  for (const pattern of patterns) {
    const candidate = String(pattern || "").trim();
    if (!candidate) {
      continue;
    }
    try {
      if (wildcardToRegExp(candidate).test(url)) {
        return true;
      }
    } catch (error) {
      console.warn("Ignoring invalid allowlist pattern:", candidate, error);
    }
  }
  return false;
}

function buttonTextMatches(buttonText, configuredPatterns) {
  const normalizedText = normalizeText(buttonText);
  if (!normalizedText) {
    return false;
  }
  for (const pattern of configuredPatterns || []) {
    const normalizedPattern = normalizeText(pattern);
    if (!normalizedPattern) {
      continue;
    }
    if (normalizedText === normalizedPattern) {
      return true;
    }
    if (normalizedText.startsWith(`${normalizedPattern} `)) {
      return true;
    }
    if (` ${normalizedText} `.includes(` ${normalizedPattern} `)) {
      return true;
    }
  }
  return false;
}

function isVisible(element) {
  if (!(element instanceof Element)) {
    return false;
  }
  const style = window.getComputedStyle(element);
  if (
    style.display === "none" ||
    style.visibility === "hidden" ||
    style.opacity === "0" ||
    style.pointerEvents === "none"
  ) {
    return false;
  }
  const rect = element.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return false;
  }
  if (rect.bottom < 0 || rect.right < 0) {
    return false;
  }
  if (rect.top > window.innerHeight || rect.left > window.innerWidth) {
    return false;
  }
  return true;
}

function isEnabled(element) {
  if (!(element instanceof HTMLElement)) {
    return false;
  }
  const disabledAttr = element.getAttribute("disabled");
  const ariaDisabled = normalizeText(element.getAttribute("aria-disabled")) === "true";
  if (disabledAttr !== null || ariaDisabled) {
    return false;
  }
  if ("disabled" in element && element.disabled) {
    return false;
  }
  return true;
}

function textOfButton(element) {
  if (!(element instanceof HTMLElement)) {
    return "";
  }
  if (element instanceof HTMLInputElement) {
    return (element.value || element.getAttribute("aria-label") || "").trim();
  }
  return (element.innerText || element.textContent || element.getAttribute("aria-label") || "").trim();
}

function withinContainer(element, selector) {
  const value = String(selector || "").trim();
  if (!value) {
    return true;
  }
  try {
    return Boolean(element.closest(value));
  } catch (error) {
    console.warn("Invalid container selector:", value, error);
    return false;
  }
}

function currentOrigin() {
  try {
    return window.location.origin;
  } catch (error) {
    return "";
  }
}

function computeActive(config) {
  const origin = currentOrigin();
  const overrides = config.site_overrides || {};
  const siteEnabled = origin ? overrides[origin] !== false : false;
  const allowlisted = urlMatchesAllowlist(window.location.href, config.allowlist_patterns || []);
  return Boolean(config.global_enabled && siteEnabled && allowlisted);
}

function ensureOverlay() {
  if (state.overlay) {
    return state.overlay;
  }
  const node = document.createElement("div");
  node.id = "submit-autoclicker-overlay";
  Object.assign(node.style, {
    position: "fixed",
    right: "12px",
    bottom: "12px",
    zIndex: "2147483647",
    background: "#052e16",
    color: "#dcfce7",
    font: "12px/1.3 Segoe UI, Tahoma, sans-serif",
    padding: "8px 10px",
    borderRadius: "8px",
    boxShadow: "0 6px 24px rgba(0, 0, 0, 0.25)",
    border: "1px solid #15803d",
    maxWidth: "260px",
    pointerEvents: "none"
  });
  state.overlay = node;
  document.documentElement.appendChild(node);
  return node;
}

function removeOverlay() {
  if (state.overlay && state.overlay.parentNode) {
    state.overlay.parentNode.removeChild(state.overlay);
  }
  state.overlay = null;
}

function updateOverlay() {
  if (!state.active) {
    removeOverlay();
    return;
  }
  const node = ensureOverlay();
  const mode = state.config.dry_run ? "DRY-RUN" : "LIVE";
  const last = state.lastClickIso
    ? new Date(state.lastClickIso).toLocaleTimeString()
    : "No clicks yet";
  node.textContent = `Auto-click active (${mode}) | Last: ${last}`;
}

function findFirstCandidate() {
  const selector = "button, input[type='submit'], input[type='button'], [role='button']";
  const nodes = document.querySelectorAll(selector);
  for (const node of nodes) {
    if (!(node instanceof HTMLElement)) {
      continue;
    }
    if (!isVisible(node)) {
      continue;
    }
    if (!isEnabled(node)) {
      continue;
    }
    if (!withinContainer(node, state.config.container_selector)) {
      continue;
    }
    const text = textOfButton(node);
    if (!buttonTextMatches(text, state.config.button_texts || [])) {
      continue;
    }
    return node;
  }
  return null;
}

async function scanAndMaybeClick() {
  if (!state.active) {
    return;
  }
  const now = Date.now();
  const cooldownMs = Math.max(0, Number(state.config.cooldown_ms || 0));
  if (now - state.lastActionMs < cooldownMs) {
    return;
  }

  const button = findFirstCandidate();
  if (!button) {
    return;
  }

  state.lastActionMs = now;
  const text = textOfButton(button);

  if (state.config.dry_run) {
    console.info("[submit-autoclicker] Dry-run candidate:", text);
  } else {
    try {
      button.click();
      console.info("[submit-autoclicker] Clicked:", text);
    } catch (error) {
      console.warn("[submit-autoclicker] Click failed:", error);
      return;
    }
  }

  state.lastClickIso = new Date().toISOString();
  updateOverlay();
  await runtimeSend({
    type: "report_click",
    origin: currentOrigin(),
    at: state.lastClickIso,
    dryRun: Boolean(state.config.dry_run),
    label: text
  });
}

function scheduleScan() {
  if (state.debounceTimer) {
    clearTimeout(state.debounceTimer);
  }
  const debounce = Math.max(50, Number(state.config.debounce_ms || 250));
  state.debounceTimer = setTimeout(() => {
    scanAndMaybeClick().catch((error) => console.error("scanAndMaybeClick failed:", error));
  }, debounce);
}

function startObserver() {
  if (state.observer) {
    return;
  }
  state.observer = new MutationObserver(() => scheduleScan());
  state.observer.observe(document.documentElement || document.body, {
    childList: true,
    subtree: true,
    attributes: true
  });
}

async function refreshConfig() {
  const keys = Object.keys(DEFAULTS);
  const raw = await storageGet(keys);
  state.config = { ...DEFAULTS, ...raw };
  state.active = computeActive(state.config);
  updateOverlay();
}

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") {
    return;
  }
  const relevant = Object.keys(changes).some((key) => Object.prototype.hasOwnProperty.call(DEFAULTS, key));
  if (!relevant) {
    return;
  }
  refreshConfig()
    .then(() => scheduleScan())
    .catch((error) => console.error("Failed to refresh config after storage change:", error));
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "content_status") {
    sendResponse({
      ok: true,
      active: state.active,
      dryRun: Boolean(state.config.dry_run),
      lastClickIso: state.lastClickIso
    });
    return true;
  }
  return false;
});

async function init() {
  await refreshConfig();
  startObserver();
  scheduleScan();
  setInterval(() => {
    if (state.active) {
      scheduleScan();
    }
  }, 2000);
}

init().catch((error) => console.error("content.js init failed:", error));

