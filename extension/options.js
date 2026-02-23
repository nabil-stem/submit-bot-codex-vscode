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

function listFromTextarea(value) {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function textareaFromList(items) {
  return (items || []).join("\n");
}

function status(message) {
  const node = document.getElementById("saveStatus");
  node.textContent = message;
}

async function load() {
  const raw = await storageGet(Object.keys(DEFAULTS));
  const config = { ...DEFAULTS, ...raw };

  document.getElementById("globalEnabled").checked = Boolean(config.global_enabled);
  document.getElementById("dryRun").checked = Boolean(config.dry_run);
  document.getElementById("allowlistPatterns").value = textareaFromList(config.allowlist_patterns);
  document.getElementById("buttonTexts").value = textareaFromList(config.button_texts);
  document.getElementById("containerSelector").value = String(config.container_selector || "");
  document.getElementById("cooldownMs").value = String(config.cooldown_ms);
  document.getElementById("debounceMs").value = String(config.debounce_ms);
}

async function save() {
  const cooldown = Number(document.getElementById("cooldownMs").value || 0);
  const debounce = Number(document.getElementById("debounceMs").value || 0);

  const payload = {
    global_enabled: Boolean(document.getElementById("globalEnabled").checked),
    dry_run: Boolean(document.getElementById("dryRun").checked),
    allowlist_patterns: listFromTextarea(document.getElementById("allowlistPatterns").value),
    button_texts: listFromTextarea(document.getElementById("buttonTexts").value),
    container_selector: String(document.getElementById("containerSelector").value || "").trim(),
    cooldown_ms: Math.min(300000, Math.max(0, Number.isFinite(cooldown) ? cooldown : DEFAULTS.cooldown_ms)),
    debounce_ms: Math.min(5000, Math.max(50, Number.isFinite(debounce) ? debounce : DEFAULTS.debounce_ms))
  };

  await storageSet(payload);
  status(`Saved at ${new Date().toLocaleTimeString()}`);
}

async function reset() {
  await storageSet({ ...DEFAULTS });
  await load();
  status("Defaults restored.");
}

document.getElementById("saveButton").addEventListener("click", () => {
  save().catch((error) => status(`Save failed: ${error}`));
});

document.getElementById("resetButton").addEventListener("click", () => {
  reset().catch((error) => status(`Reset failed: ${error}`));
});

load().catch((error) => status(`Load failed: ${error}`));

