const state = { catalogueId: null, document: null, tab: "items", recordId: null, newRecord: false };
const typeMetadata = {
  radio: ["station_name"], music_track: ["track_title","artist","album_artist","album_title","composer","disc_number","track_number","release_date"],
  podcast_episode: ["episode_title","podcast_title","creator","publisher","publication_date","episode_number"], live_tv: ["channel_name"],
  tv_episode: ["episode_title","series_title","season_number","episode_number","first_broadcast_date"], movie: ["movie_title","secondary_title","studio","release_date"],
  photo: ["image_title","creator","creation_datetime","location","latitude","longitude","width_pixels","height_pixels"]
};
const $ = id => document.getElementById(id);
const enc = value => encodeURIComponent(value);

async function api(url, options = {}) {
  const response = await fetch(url, options);
  let payload;
  try { payload = await response.json(); } catch { payload = {}; }
  if (!response.ok) throw new Error(payload.message || payload.error || `Request failed (${response.status})`);
  return payload;
}
function message(text, error = false) { const box = $("message"); box.textContent = text; box.className = `message${error ? " error" : ""}`; clearTimeout(message.timer); message.timer = setTimeout(() => box.classList.add("hidden"), 6500); }

async function start() {
  document.querySelectorAll("[data-tab]").forEach(button => button.addEventListener("click", () => switchTab(button.dataset.tab)));
  document.querySelectorAll("[data-close]").forEach(button => button.addEventListener("click", () => $(button.dataset.close).close()));
  $("catalogue-select").addEventListener("change", event => loadCatalogue(event.target.value));
  $("add-record").addEventListener("click", addRecord); $("delete-record").addEventListener("click", deleteRecord);
  $("editor").addEventListener("submit", save); $("item-type").addEventListener("change", renderMetadata);
  $("artwork-source").addEventListener("change", toggleAssetButton); $("pick-asset").addEventListener("click", () => browseAssets(""));
  $("add-method").addEventListener("click", () => addMethod()); $("history").addEventListener("click", showHistory);
  Object.keys(typeMetadata).forEach(type => $("item-type").add(new Option(type.replaceAll("_", " "), type)));
  try {
    const capabilities = await api("api/capabilities");
    $("provider-status").textContent = `MediaCat schema ${capabilities.current_catalogue_schema_version}`;
    $("provider-status").className = "status ok";
  } catch (error) { $("provider-status").textContent = "MediaCat unavailable"; $("provider-status").className = "status error"; message(error.message, true); }
  await loadCatalogues();
}

async function loadCatalogues() {
  const payload = await api("api/catalogues"); const select = $("catalogue-select");
  select.replaceChildren(new Option("Select a catalogue", ""));
  payload.catalogues.forEach(cat => select.add(new Option(`${cat.catalogue_id} · ${cat.item_count} items`, cat.catalogue_id)));
  payload.errors.forEach(error => message(`${error.file || "Catalogues"}: ${error.message}`, true));
}
async function loadCatalogue(id) {
  if (!id) { state.catalogueId = null; state.document = null; $("editor").classList.add("hidden"); $("empty-state").classList.remove("hidden"); return; }
  const payload = await api(`api/catalogues/${enc(id)}`); state.catalogueId = id; state.document = payload.document; state.recordId = null;
  $("catalogue-file").textContent = payload.relative_name; $("empty-state").classList.add("hidden"); $("editor").classList.remove("hidden"); renderList();
}
function switchTab(tab) { commitRecord(); state.tab = tab; state.recordId = null; document.querySelectorAll("[data-tab]").forEach(button => button.classList.toggle("active", button.dataset.tab === tab)); $("list-title").textContent = tab === "items" ? "Items" : "Categories"; renderList(); }
function records() { return state.document?.[state.tab] || {}; }
function renderList() {
  const list = $("record-list"); list.replaceChildren();
  Object.entries(records()).forEach(([id, record]) => { const button = document.createElement("button"); button.type = "button"; button.textContent = record.catalogue_label || record.category_label || id; button.title = id; button.classList.toggle("active", id === state.recordId); button.addEventListener("click", () => selectRecord(id)); list.append(button); });
  if (!state.recordId && Object.keys(records()).length) selectRecord(Object.keys(records())[0]); else if (!Object.keys(records()).length) addRecord();
}
function selectRecord(id) { commitRecord(); state.recordId = id; state.newRecord = false; renderList(); fillEditor(); }
function addRecord() { if (!state.document) return; commitRecord(); state.recordId = ""; state.newRecord = true; fillEditor(); }
function deleteRecord() { if (!state.recordId || !confirm(`Delete ${state.recordId}?`)) return; delete records()[state.recordId]; if (state.tab === "items") Object.values(state.document.categories || {}).forEach(category => category.items = (category.items || []).filter(id => id !== state.recordId)); state.recordId = null; renderList(); }

function fillEditor() {
  const itemMode = state.tab === "items"; $("item-fields").classList.toggle("hidden", !itemMode); $("category-fields").classList.toggle("hidden", itemMode);
  $("item-fields").querySelectorAll("input,select,textarea,button").forEach(control => control.disabled = !itemMode);
  $("category-fields").querySelectorAll("input,select,textarea,button").forEach(control => control.disabled = itemMode);
  const record = state.recordId ? records()[state.recordId] : {};
  $("record-heading").textContent = state.recordId || `New ${itemMode ? "item" : "category"}`; $("delete-record").disabled = !state.recordId;
  if (itemMode) {
    $("item-id").value = state.recordId || ""; $("item-id").disabled = Boolean(state.recordId); $("item-label").value = record.catalogue_label || ""; $("item-type").value = record.type || "radio";
    $("item-description").value = record.description || ""; $("item-tags").value = (record.tags || []).join(", ");
    const artwork = record.artwork || {}; $("artwork-source").value = artwork.source_type || ""; $("artwork-path").value = artwork.path || artwork.local || ""; $("artwork-external").value = artwork.external || ""; toggleAssetButton(); renderMetadata(record.type_metadata || {});
    $("method-list").replaceChildren(); Object.entries(record.execution_methods || {}).forEach(([name, method]) => addMethod(name, method.source || {}));
  } else {
    $("category-id").value = state.recordId || ""; $("category-id").disabled = Boolean(state.recordId); $("category-label").value = record.category_label || ""; renderCategoryItems(record.items || []);
  }
}
function renderMetadata(values = null) { const container = $("metadata-fields"); if (values === null) values = readMetadata(); container.replaceChildren(); (typeMetadata[$("item-type").value] || []).forEach(name => { const label = document.createElement("label"); label.textContent = name.replaceAll("_", " "); const input = document.createElement("input"); input.dataset.metadata = name; input.value = values[name] ?? ""; label.append(input); container.append(label); }); }
function readMetadata() { const result = {}; document.querySelectorAll("[data-metadata]").forEach(input => { if (input.value !== "") result[input.dataset.metadata] = /^\d+(\.\d+)?$/.test(input.value) ? Number(input.value) : input.value; }); return result; }
function renderCategoryItems(selected) { const container = $("category-items"); container.replaceChildren(); Object.entries(state.document.items || {}).forEach(([id,item]) => { const label = document.createElement("label"); const box = document.createElement("input"); box.type = "checkbox"; box.value = id; box.checked = selected.includes(id); label.append(box, document.createTextNode(item.catalogue_label || id)); container.append(label); }); }
function toggleAssetButton() { $("pick-asset").disabled = $("artwork-source").value !== "ha-assets"; }

function addMethod(name = "ha_mplayer", source = {source_type: "url"}) {
  const row = document.createElement("div"); row.className = "method"; row.innerHTML = `<label>Method<select data-method><option value="ha_mplayer">ha_mplayer</option><option value="g_home_device">g_home_device</option></select></label><label>Source<select data-source><option value="url">URL</option><option value="ha_media_source">HA media source</option><option value="assistant_command">Assistant command</option></select></label><div class="method-details"></div><button type="button" class="danger">Remove</button>`;
  row.querySelector("[data-method]").value = name; row.querySelector("[data-source]").value = source.source_type || "url"; row.dataset.value = JSON.stringify(source);
  row.querySelector("button").addEventListener("click", () => row.remove()); row.querySelector("[data-source]").addEventListener("change", () => renderMethod(row, {})); renderMethod(row, source); $("method-list").append(row);
}
function renderMethod(row, source) { const kind = row.querySelector("[data-source]").value; const fields = kind === "url" ? ["url","mime_type","provider"] : kind === "ha_media_source" ? ["provider","uri","media_type"] : ["provider","command","append_target"]; const box = row.querySelector(".method-details"); box.replaceChildren(); fields.forEach(name => { const label = document.createElement("label"); label.textContent = name.replaceAll("_", " "); const input = document.createElement("input"); input.dataset.sourceField = name; input.value = source[name] ?? (name === "append_target" ? "true" : ""); label.append(input); box.append(label); }); }
function readMethods() { const result = {}; document.querySelectorAll(".method").forEach(row => { const source = {source_type: row.querySelector("[data-source]").value}; row.querySelectorAll("[data-source-field]").forEach(input => { if (input.value !== "") source[input.dataset.sourceField] = input.dataset.sourceField === "append_target" ? input.value === "true" : input.value; }); result[row.querySelector("[data-method]").value] = {source}; }); return result; }

function commitRecord() {
  if (!state.document || !$("editor").checkValidity() || state.recordId === null) return;
  if (state.tab === "items") {
    const id = state.recordId || $("item-id").value.trim(); if (!id) return;
    const prior = state.recordId ? records()[state.recordId] : {}; const record = {...prior, catalogue_label: $("item-label").value.trim(), type: $("item-type").value, type_metadata: readMetadata(), execution_methods: readMethods()};
    const description = $("item-description").value.trim(); const tags = $("item-tags").value.split(",").map(value => value.trim()).filter(Boolean); if (description) record.description = description; else delete record.description; if (tags.length) record.tags = tags; else delete record.tags;
    const source = $("artwork-source").value, path = $("artwork-path").value.trim(), external = $("artwork-external").value.trim(); if (source === "ha-assets" && path) record.artwork = {source_type: source, path}; else if (source === "direct" && (path || external)) record.artwork = {source_type: source, ...(path ? {local:path} : {}), ...(external ? {external} : {})}; else delete record.artwork;
    records()[id] = record; state.recordId = id;
  } else {
    const id = state.recordId || $("category-id").value.trim(); if (!id) return; const items = [...$("category-items").querySelectorAll("input:checked")].map(input => input.value); records()[id] = {category_label: $("category-label").value.trim(), items}; state.recordId = id;
  }
  state.newRecord = false;
}
async function save(event) {
  event.preventDefault(); commitRecord();
  try { const result = await api(`api/catalogues/${enc(state.catalogueId)}/save`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({document:state.document})}); if (!result.saved) { message((result.validation.errors || []).map(error => error.message).join("; ") || "MediaCat rejected the candidate", true); return; } message(result.runtime_active ? `Saved, snapshot ${result.snapshot}, and reloaded MediaCat.` : `Saved with snapshot ${result.snapshot}, but MediaCat reload failed. The prior runtime remains active.`, !result.runtime_active); await loadCatalogue(state.catalogueId); } catch (error) { message(error.message, true); }
}

async function browseAssets(directory) {
  try { const payload = await api(`api/assets?directory=${enc(directory || ".")}`); const grid = $("asset-grid"); grid.replaceChildren(); $("asset-breadcrumb").textContent = payload.directory ? `/${payload.directory}` : "/"; if (payload.parent !== null) grid.append(assetButton("↰", "Parent", () => browseAssets(payload.parent)));
    payload.entries.forEach(entry => { if (entry.kind === "directory") grid.append(assetButton("📁", entry.name, () => browseAssets(entry.path))); else { const button = assetButton(null, entry.name, () => { $("artwork-source").value = "ha-assets"; $("artwork-path").value = entry.path; $("asset-dialog").close(); }); const image = document.createElement("img"); image.src = `api/asset?path=${enc(entry.path)}`; image.alt = ""; button.prepend(image); grid.append(button); } }); $("asset-dialog").showModal();
  } catch (error) { message(error.message, true); }
}
function assetButton(icon, label, action) { const button = document.createElement("button"); button.type = "button"; button.className = "asset"; if (icon) { const span = document.createElement("strong"); span.textContent = icon; button.append(span); } const text = document.createElement("span"); text.textContent = label; button.append(text); button.addEventListener("click", action); return button; }

async function showHistory() { try { const payload = await api(`api/catalogues/${enc(state.catalogueId)}/history`); const list = $("history-list"); list.replaceChildren(); $("history-diff").textContent = ""; if (!payload.history.length) list.textContent = "No snapshots yet."; payload.history.forEach(entry => { const row = document.createElement("div"); row.className = "history-row"; const code = document.createElement("code"); code.textContent = entry.snapshot; const diff = document.createElement("button"); diff.textContent = "Diff"; diff.addEventListener("click", async () => $("history-diff").textContent = (await api(`api/catalogues/${enc(state.catalogueId)}/history/${enc(entry.snapshot)}/diff`)).diff || "No differences."); const restore = document.createElement("button"); restore.textContent = "Restore"; restore.addEventListener("click", () => restoreSnapshot(entry.snapshot)); row.append(code,diff,restore); list.append(row); }); $("history-dialog").showModal(); } catch (error) { message(error.message, true); } }
async function restoreSnapshot(snapshot) { if (!confirm(`Validate and restore ${snapshot}?`)) return; try { const result = await api(`api/catalogues/${enc(state.catalogueId)}/history/${enc(snapshot)}/restore`, {method:"POST", headers:{"Content-Type":"application/json"}, body:"{}"}); if (!result.restored) { message("MediaCat rejected this snapshot.", true); return; } message(result.runtime_active ? "Snapshot restored and MediaCat reloaded." : "Snapshot restored on disk, but MediaCat retained its prior runtime.", !result.runtime_active); $("history-dialog").close(); await loadCatalogue(state.catalogueId); } catch (error) { message(error.message, true); } }

start().catch(error => message(error.message, true));
