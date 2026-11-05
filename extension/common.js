// Shared by the popup and the settings page.
const api = globalThis.browser ?? globalThis.chrome;
const HOST_NAME = "catstube2mp3.helper";

const DEFAULT_SETTINGS = {
  baseFolder: "",
  subfolderPattern: "{playlist}",
  namePattern: "{artist} - {title}",
  quality: "192",
  cleanJunk: true,
  embedMetadata: true,
  embedThumbnail: true,
  onExisting: "number",
};

async function loadSettings() {
  const { settings } = await api.storage.local.get("settings");
  return { ...DEFAULT_SETTINGS, ...(settings || {}) };
}

async function saveSettings(changes) {
  const settings = { ...(await loadSettings()), ...changes };
  await api.storage.local.set({ settings });
  return settings;
}

class HelperMissingError extends Error {}

// Send one command to the native helper and return its reply, or throw.
async function helper(cmd, data = {}) {
  let reply;
  try {
    reply = await api.runtime.sendNativeMessage(HOST_NAME, { cmd, ...data });
  } catch (err) {
    const text = String(err?.message || err);
    if (/not found|no such native application|specified native messaging host|disconnected|exited/i.test(text)) {
      throw new HelperMissingError(text);
    }
    throw err;
  }
  if (!reply?.ok) throw new Error(reply?.error || "The helper returned no answer.");
  return reply;
}

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (value !== undefined && value !== null && value !== false) node[key] = value;
  }
  node.append(...children.filter((c) => c !== null && c !== undefined && c !== false));
  return node;
}

const INSTALL_GUIDE_URL = "https://github.com/YOUR-GITHUB-NAME/CatsTube2Mp3#install";
