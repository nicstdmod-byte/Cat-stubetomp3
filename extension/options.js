const $ = (id) => document.getElementById(id);

// Made-up examples for the live preview.
const PREVIEW_SAMPLES = [
  { title: "Artist Name - Song Name (Official Video)", channel: "ArtistNameVEVO", index: 1, total: 12, playlist: "My Playlist", id: "abc123" },
  { title: "Another Song [Lyrics]", channel: "Some Band - Topic", index: 2, total: 12, playlist: "My Playlist", id: "def456" },
  { title: "Live Session (HD)", channel: "Indie Channel", index: 3, total: 12, playlist: "My Playlist", id: "ghi789" },
];

let settings;
let musicDir = "";
let previewTimer = null;
let savedTimer = null;

function flashSaved() {
  $("saved").classList.add("show");
  clearTimeout(savedTimer);
  savedTimer = setTimeout(() => $("saved").classList.remove("show"), 1200);
}

async function update(changes) {
  settings = await saveSettings(changes);
  flashSaved();
  schedulePreview();
}

// A preset <select> with a "Custom…" option that reveals a text box.
function bindPattern(selectId, inputId, key) {
  const select = $(selectId);
  const input = $(inputId);
  const presets = [...select.options].map((o) => o.value).filter((v) => v !== "custom");
  const isPreset = presets.includes(settings[key]);
  select.value = isPreset ? settings[key] : "custom";
  input.value = settings[key];
  input.classList.toggle("hidden", isPreset);

  select.addEventListener("change", () => {
    const custom = select.value === "custom";
    input.classList.toggle("hidden", !custom);
    if (custom) input.focus();
    else {
      input.value = select.value;
      update({ [key]: select.value });
    }
  });
  input.addEventListener("input", () => update({ [key]: input.value }));
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(renderPreview, 250);
}

async function renderPreview() {
  try {
    const { names, folder } = await helper("preview", { settings, samples: PREVIEW_SAMPLES });
    $("preview-folder").textContent = "📁 " + folder;
    $("preview-list").replaceChildren(...names.map((name) => el("li", {}, name)));
  } catch (err) {
    $("preview-folder").textContent = "";
    $("preview-list").replaceChildren(el("li", { class: "muted" }, "Preview needs the helper to be installed."));
  }
}

async function checkHelper() {
  const box = $("helper-status");
  box.textContent = "Checking…";
  try {
    const info = await helper("ping");
    musicDir = info.musicDir;
    $("baseFolder").placeholder = musicDir;
    const line = (ok, text) => el("div", { class: ok ? "status-ok" : "status-bad" }, (ok ? "✔ " : "✖ ") + text);
    box.replaceChildren(
      line(true, `Helper connected (version ${info.helper}, ${info.system}, Python ${info.python})`),
      line(Boolean(info.ytdlp), info.ytdlp ? `yt-dlp ${info.ytdlp}` : "yt-dlp is missing. Run the installer again."),
      line(info.ffmpeg, info.ffmpeg ? "ffmpeg found" : "ffmpeg is missing. Run the installer again."),
      line(Boolean(info.jsRuntime), info.jsRuntime
        ? `JavaScript runtime: ${info.jsRuntime}`
        : "No JavaScript runtime (deno). Some YouTube videos may fail. Run the installer again."));
    $("update-ytdlp").disabled = false;
  } catch (err) {
    $("update-ytdlp").disabled = true;
    box.replaceChildren(
      el("div", { class: "status-bad" }, err instanceof HelperMissingError
        ? "✖ Helper not found. Install it with install.bat (Windows) or install.sh (Linux), then restart the browser."
        : "✖ " + err.message),
      el("button", { class: "link", onclick: () => api.tabs.create({ url: INSTALL_GUIDE_URL }) }, "Open install guide"));
  }
}

async function init() {
  settings = await loadSettings();

  $("baseFolder").value = settings.baseFolder;
  $("baseFolder").addEventListener("change", () => update({ baseFolder: $("baseFolder").value.trim() }));
  $("reset-folder").addEventListener("click", () => {
    $("baseFolder").value = "";
    update({ baseFolder: "" });
  });
  $("browse").addEventListener("click", async () => {
    try {
      const { path } = await helper("pick_folder", { current: settings.baseFolder || musicDir || null });
      if (path) {
        $("baseFolder").value = path;
        update({ baseFolder: path });
      }
    } catch (err) {
      alert("Could not open the folder picker: " + err.message);
    }
  });

  bindPattern("subfolderPreset", "subfolderPattern", "subfolderPattern");
  bindPattern("namePreset", "namePattern", "namePattern");

  for (const key of ["cleanJunk", "embedMetadata", "embedThumbnail"]) {
    $(key).checked = settings[key];
    $(key).addEventListener("change", () => update({ [key]: $(key).checked }));
  }
  $("quality").value = settings.quality;
  $("quality").addEventListener("change", () => update({ quality: $("quality").value }));
  for (const radio of document.querySelectorAll("input[name=onExisting]")) {
    radio.checked = radio.value === settings.onExisting;
    radio.addEventListener("change", () => update({ onExisting: radio.value }));
  }

  $("recheck").addEventListener("click", checkHelper);
  $("update-ytdlp").addEventListener("click", async () => {
    $("update-ytdlp").disabled = true;
    $("update-result").textContent = "Updating… this can take a minute.";
    try {
      const { before, after } = await helper("update_ytdlp");
      $("update-result").textContent = before === after ? `Already up to date (${after}).` : `Updated ${before} → ${after}.`;
      checkHelper();
    } catch (err) {
      $("update-result").textContent = err.message;
    } finally {
      $("update-ytdlp").disabled = false;
    }
  });

  await checkHelper();
  renderPreview();
}

init();
