const $ = (id) => document.getElementById(id);
const YOUTUBE_URL = /^https?:\/\/((www|m|music)\.)?youtube\.com\/(watch|playlist|shorts\/)|^https?:\/\/youtu\.be\//;

let settings;
let listing = null;      // reply from the helper's "list" command
let lastClicked = null;  // index of the last clicked checkbox, for Shift+click
let pollTimer = null;
let currentJob = null;   // the download shown in the progress view

function show(view) {
  for (const id of ["view-message", "view-list", "view-progress"]) $(id).classList.toggle("hidden", id !== view);
}

function showMessage(text, ...actions) {
  $("message-text").textContent = text;
  $("message-actions").replaceChildren(...actions);
  show("view-message");
}

function showHelperMissing() {
  const steps = el("ol", {},
    el("li", {}, "Download Cat'sTube2Mp3 from GitHub."),
    el("li", {}, "Windows: double-click ", el("code", {}, "install\\install.bat"), "."),
    el("li", {}, "Linux: run ", el("code", {}, "install/install.sh"), "."),
    el("li", {}, "Restart the browser and open this popup again."));
  showMessage("The Cat'sTube2Mp3 helper is not installed (or not working). It is needed to download and convert songs.",
    steps,
    el("button", { onclick: () => api.tabs.create({ url: INSTALL_GUIDE_URL }) }, "Open install guide"));
}

function showError(err) {
  if (err instanceof HelperMissingError) return showHelperMissing();
  showMessage("Something went wrong:\n" + (err?.message || err),
    el("button", { onclick: start }, "Try again"));
}

function setFolder(path) {
  // The folder box is right-to-left so long paths cut off at the start; LRM marks keep the slashes in place.
  $("folder").textContent = "‎" + path + "‎";
  $("folder").title = path;
}

function formatDuration(seconds) {
  if (!seconds) return "";
  const s = Math.round(seconds);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

// ---------------------------------------------------------------- song picker

function checkboxes() {
  return [...document.querySelectorAll("#song-list input[type=checkbox]")];
}

function updateSelection() {
  const boxes = checkboxes().filter((b) => !b.disabled);
  const picked = boxes.filter((b) => b.checked).length;
  $("select-all").checked = boxes.length > 0 && picked === boxes.length;
  $("select-all").indeterminate = picked > 0 && picked < boxes.length;
  $("select-count").textContent = `(${picked} of ${boxes.length})`;
  $("download").disabled = picked === 0;
  $("download").textContent = picked === 1 ? "Download 1 song" : `Download ${picked} songs`;
}

function onSongClick(event) {
  const box = event.target;
  const index = Number(box.dataset.index);
  if (event.shiftKey && lastClicked !== null) {
    const [from, to] = [Math.min(lastClicked, index), Math.max(lastClicked, index)];
    for (const other of checkboxes()) {
      const i = Number(other.dataset.index);
      if (i >= from && i <= to && !other.disabled) other.checked = box.checked;
    }
  }
  lastClicked = index;
  updateSelection();
}

function renderList() {
  const { entries, playlist, isPlaylist, folder } = listing;
  $("playlist-title").textContent = isPlaylist ? `🎵 ${playlist || "Playlist"} (${entries.length} songs)` : "🎵 Single video";
  setFolder(folder);
  $("quality").value = settings.quality;

  $("song-list").replaceChildren(...entries.map((entry, i) => {
    const box = el("input", {
      type: "checkbox",
      checked: !entry.done && !entry.unavailable,
      disabled: entry.unavailable,
      dataset: { index: i },
      onclick: onSongClick,
    });
    let state = el("span", { class: "state muted" }, formatDuration(entry.duration));
    if (entry.unavailable) state = el("span", { class: "state status-bad" }, "unavailable");
    else if (entry.done) state = el("span", { class: "state status-ok" }, "✔ done");
    return el("li", { class: entry.unavailable ? "off" : "" },
      box,
      el("span", { class: "num" }, String(entry.index).padStart(2, "0")),
      el("label", { class: "name", title: entry.title, onclick: () => !box.disabled && box.click() },
        el("div", {}, entry.title),
        el("div", { class: "file" }, entry.filename)),
      state);
  }));
  lastClicked = null;
  updateSelection();
  show("view-list");
}

async function loadList(url) {
  showMessage("Reading the playlist… (big playlists can take a little while)");
  listing = await helper("list", { url, settings });
  renderList();
}

async function startDownload() {
  const picked = checkboxes().filter((b) => b.checked).map((b) => listing.entries[Number(b.dataset.index)]);
  $("download").disabled = true;
  try {
    await helper("start", { entries: picked, folder: listing.folder, playlist: listing.playlist, settings });
    await pollStatus();
  } catch (err) {
    showError(err);
  }
}

// ---------------------------------------------------------------- progress

const STATUS_TEXT = {
  queued: ["waiting", "muted"],
  downloading: ["downloading", "status-warn"],
  converting: ["converting…", "status-warn"],
  done: ["✔ done", "status-ok"],
  skipped: ["skipped", "muted"],
  error: ["✖ failed", "status-bad"],
  cancelled: ["cancelled", "muted"],
};

function renderJob(job) {
  currentJob = job;
  const items = job.items;
  const finished = items.filter((i) => !["queued", "downloading", "converting"].includes(i.status)).length;
  const current = items.find((i) => i.status === "downloading" || i.status === "converting");
  const partial = current ? (current.status === "converting" ? 0.9 : (current.percent || 0) / 100 * 0.9) : 0;
  const done = items.filter((i) => i.status === "done").length;
  const failed = items.filter((i) => i.status === "error").length;
  const skipped = items.filter((i) => i.status === "skipped").length;
  const running = job.state === "running";

  $("job-title").textContent = running ? `Downloading ${job.playlist ? "“" + job.playlist + "”" : ""}` : {
    done: "Finished", cancelled: "Cancelled", error: "Stopped",
  }[job.state] || "Finished";
  $("job-bar").style.width = `${Math.min(100, ((finished + partial) / items.length) * 100)}%`;

  const parts = [`${finished} of ${items.length}`];
  if (done) parts.push(`${done} saved`);
  if (skipped) parts.push(`${skipped} skipped`);
  if (failed) parts.push(`${failed} failed`);
  $("job-summary").textContent = parts.join(" · ") + (job.error ? `\n${job.error}` : "");

  $("job-list").replaceChildren(...items.map((item) => {
    const [text, cls] = STATUS_TEXT[item.status] || [item.status, "muted"];
    const label = item.status === "downloading" ? `${text} ${item.percent || 0}%` : text;
    return el("li", { title: item.error || "" },
      el("span", { class: "num" }, String(item.index).padStart(2, "0")),
      el("span", { class: "name" },
        el("div", {}, item.filename || item.title),
        item.error ? el("div", { class: "file status-bad" }, item.error) : null),
      el("span", { class: `state ${cls}` }, label));
  }));

  $("cancel").classList.toggle("hidden", !running);
  $("back").classList.toggle("hidden", running);
  show("view-progress");

  if (current && running) {
    const row = $("job-list").children[items.indexOf(current)];
    row?.scrollIntoView({ block: "nearest" });
  }
}

async function pollStatus() {
  clearTimeout(pollTimer);
  const { job } = await helper("status");
  if (!job) return false;
  renderJob(job);
  if (job.state === "running") pollTimer = setTimeout(() => pollStatus().catch(showError), 1000);
  return true;
}

// ---------------------------------------------------------------- startup

async function start() {
  try {
    settings = await loadSettings();
    showMessage("Connecting to the helper…");
    await helper("ping");

    // Show the current download, or the last one until the user clicks "Done".
    if (await pollStatus()) return;

    const [tab] = await api.tabs.query({ active: true, currentWindow: true });
    if (!tab?.url || !YOUTUBE_URL.test(tab.url)) {
      showMessage("Open a YouTube playlist or video, then click the cat again. 🐱");
      return;
    }
    await loadList(tab.url);
  } catch (err) {
    showError(err);
  }
}

$("select-all").addEventListener("change", (e) => {
  for (const box of checkboxes()) if (!box.disabled) box.checked = e.target.checked;
  updateSelection();
});
$("download").addEventListener("click", startDownload);
$("quality").addEventListener("change", async (e) => { settings = await saveSettings({ quality: e.target.value }); });
$("change-folder").addEventListener("click", async () => {
  try {
    const { path } = await helper("pick_folder", { current: settings.baseFolder || null });
    if (!path) return;
    settings = await saveSettings({ baseFolder: path });
    const [tab] = await api.tabs.query({ active: true, currentWindow: true });
    await loadList(tab.url);
  } catch (err) {
    showError(err);
  }
});
$("cancel").addEventListener("click", () => helper("cancel").catch(showError));
$("open-folder").addEventListener("click", () => {
  const folder = currentJob?.folder || listing?.folder;
  if (folder) helper("open_folder", { folder }).catch(showError);
});
$("back").addEventListener("click", async () => {
  clearTimeout(pollTimer);
  await helper("clear").catch(() => {});
  currentJob = null;
  start();
});
$("open-settings").addEventListener("click", () => api.runtime.openOptionsPage());

start();
