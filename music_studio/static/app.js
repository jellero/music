const state = { projects: [], project: null };
const $ = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail || response.statusText);
  }
  return response.json();
}

function setStatus(text, online = true) {
  $("#status-text").textContent = text;
  $("#status-dot").classList.toggle("online", online);
}

function noteName(pitch) {
  const names = ["C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B"];
  return `${names[pitch % 12]}${Math.floor(pitch / 12) - 1}`;
}

function colorFor(index) {
  return ["#b7ff4a", "#63d9ff", "#ffb05c", "#dc82ff", "#ff7f91"][index % 5];
}

async function loadProjects(selectFirst = true) {
  state.projects = await api("/api/projects");
  const list = $("#project-list");
  list.innerHTML = "";
  for (const project of state.projects) {
    const button = document.createElement("button");
    button.className = `project-item${state.project?.id === project.id ? " active" : ""}`;
    button.innerHTML = `<strong>${escapeHtml(project.name)}</strong><small>${project.tempo} BPM · ${escapeHtml(project.key)}</small>`;
    button.onclick = () => loadProject(project.id);
    list.appendChild(button);
  }
  if (!state.projects.length) list.innerHTML = '<div class="empty-state">Nessun progetto.</div>';
  if (selectFirst && !state.project && state.projects[0]) await loadProject(state.projects[0].id);
}

async function loadProject(projectId) {
  state.project = await api(`/api/projects/${projectId}`);
  renderAll();
  await loadProjects(false);
}

function renderAll() {
  const project = state.project;
  $("#compose").disabled = !project;
  $("#render").disabled = !project;
  if (!project) return;
  $("#project-name").textContent = project.name;
  $("#project-key").textContent = project.key;
  $("#project-meta").textContent = `${project.tempo} BPM · ${project.time_signature} · ${project.bars} battute`;
  $("#note-count").textContent = `${project.tracks.reduce((sum, track) => sum + track.notes.length, 0)} note`;
  renderTrackFilter();
  renderScore();
  renderMixer();
  renderPianoRoll();
  renderArtifacts();
}

function renderTrackFilter() {
  const select = $("#track-filter");
  const current = select.value;
  select.innerHTML = '<option value="all">Tutte le tracce</option>';
  for (const track of state.project.tracks) {
    const option = document.createElement("option");
    option.value = track.id;
    option.textContent = track.name;
    select.appendChild(option);
  }
  select.value = [...select.options].some((item) => item.value === current) ? current : "all";
}

function renderScore() {
  const container = $("#score");
  const selected = $("#track-filter").value;
  const tracks = state.project.tracks.filter((track) => selected === "all" || track.id === selected);
  if (!tracks.length) {
    container.className = "score empty-state";
    container.textContent = "Nessuna nota.";
    return;
  }
  container.className = "score";
  const width = Math.max(920, state.project.bars * 180 + 80);
  const rowHeight = 110;
  const height = tracks.length * rowHeight + 34;
  const beatWidth = 42;
  const beatsPerBar = Number(state.project.time_signature.split("/")[0]);
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="#f8f6ee"/>`;
  tracks.forEach((track, trackIndex) => {
    const y = 36 + trackIndex * rowHeight;
    svg += `<text x="12" y="${y + 19}" font-family="system-ui" font-size="12" font-weight="700">${escapeHtml(track.name)}</text>`;
    for (let line = 0; line < 5; line++) svg += `<line x1="75" y1="${y + line * 10}" x2="${width - 20}" y2="${y + line * 10}" stroke="#595959"/>`;
    for (let bar = 0; bar <= state.project.bars; bar++) {
      const x = 75 + bar * beatsPerBar * beatWidth;
      svg += `<line x1="${x}" y1="${y}" x2="${x}" y2="${y + 40}" stroke="#111"/>`;
    }
    track.notes.forEach((note) => {
      const x = 75 + note.start * beatWidth + 4;
      const noteY = y + 40 - (note.pitch - 60) * 2.5;
      svg += `<ellipse cx="${x}" cy="${noteY}" rx="6" ry="4.5" transform="rotate(-18 ${x} ${noteY})" fill="#111"/>`;
      if (note.duration <= 1) svg += `<line x1="${x + 5}" y1="${noteY}" x2="${x + 5}" y2="${noteY - 26}" stroke="#111" stroke-width="1.5"/>`;
    });
  });
  container.innerHTML = `${svg}</svg>`;
}

function renderMixer() {
  const container = $("#mixer");
  if (!state.project.tracks.length) {
    container.className = "mixer empty-state";
    container.textContent = "Nessuna traccia.";
    return;
  }
  container.className = "mixer";
  container.innerHTML = state.project.tracks.map((track, index) => `
    <div class="channel"><div class="channel-head"><div><strong>${escapeHtml(track.name)}</strong><br><small>${escapeHtml(track.instrument)}</small></div><small>${track.notes.length} note</small></div><div class="meter"><span style="width:${Math.round(track.volume * 100)}%;background:${colorFor(index)}"></span></div></div>`).join("");
}

function renderPianoRoll() {
  const container = $("#piano-roll");
  const notes = state.project.tracks.flatMap((track, index) => track.notes.map((note) => ({ ...note, trackIndex: index, trackName: track.name })));
  if (!notes.length) {
    container.className = "piano-roll empty-state";
    container.textContent = "Nessuna sequenza.";
    return;
  }
  container.className = "piano-roll";
  const minPitch = Math.max(0, Math.min(...notes.map((note) => note.pitch)) - 2);
  const maxPitch = Math.min(127, Math.max(...notes.map((note) => note.pitch)) + 2);
  const pitchHeight = 10;
  const beatWidth = 42;
  const beats = state.project.bars * Number(state.project.time_signature.split("/")[0]);
  const width = Math.max(1000, beats * beatWidth + 64);
  const height = (maxPitch - minPitch + 1) * pitchHeight;
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="#0c0e12"/>`;
  for (let pitch = minPitch; pitch <= maxPitch; pitch++) {
    const y = (maxPitch - pitch) * pitchHeight;
    const black = [1,3,6,8,10].includes(pitch % 12);
    svg += `<rect x="0" y="${y}" width="${width}" height="${pitchHeight}" fill="${black ? "#10131a" : "#151820"}"/>`;
    if (pitch % 12 === 0) svg += `<text x="4" y="${y + 8}" font-family="system-ui" font-size="8" fill="#7f8794">${noteName(pitch)}</text>`;
    svg += `<line x1="0" y1="${y}" x2="${width}" y2="${y}" stroke="#20242d"/>`;
  }
  for (let beat = 0; beat <= beats; beat++) {
    const x = 54 + beat * beatWidth;
    svg += `<line x1="${x}" y1="0" x2="${x}" y2="${height}" stroke="${beat % 4 === 0 ? "#3b414e" : "#242933"}"/>`;
  }
  notes.forEach((note) => {
    const x = 54 + note.start * beatWidth;
    const y = (maxPitch - note.pitch) * pitchHeight + 1;
    const w = Math.max(3, note.duration * beatWidth - 2);
    svg += `<rect x="${x}" y="${y}" width="${w}" height="${pitchHeight - 2}" rx="2" fill="${colorFor(note.trackIndex)}"><title>${escapeHtml(note.trackName)} · ${noteName(note.pitch)}</title></rect>`;
  });
  container.innerHTML = `${svg}</svg>`;
}

function renderArtifacts() {
  const container = $("#artifacts");
  const artifacts = state.project.manifest?.artifacts || [];
  if (!artifacts.length) {
    container.className = "artifact-list empty-state";
    container.textContent = "Esegui il rendering.";
    $("#play").disabled = true;
    return;
  }
  container.className = "artifact-list";
  container.innerHTML = artifacts.map((item) => `<a class="artifact" href="${item.url}" download><strong>${item.format.toUpperCase()}</strong><small>${formatBytes(item.size)}</small></a>`).join("");
  const wav = artifacts.find((item) => item.format === "wav");
  if (wav) {
    $("#audio").src = `${wav.url}?v=${Date.now()}`;
    $("#play").disabled = false;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB"];
  const index = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

$("#new-project").onclick = () => $("#project-dialog").showModal();
$("#project-form").onsubmit = async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const project = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        tempo: Number(form.get("tempo")),
        key: form.get("key"),
        time_signature: form.get("time_signature"),
        bars: Number(form.get("bars")),
      }),
    });
    $("#project-dialog").close();
    await loadProject(project.id);
  } catch (error) { alert(error.message); }
};

$("#compose").onclick = async () => {
  if (!state.project) return;
  setStatus("Composizione…", false);
  try {
    await api(`/api/projects/${state.project.id}/compose`, {
      method: "POST",
      body: JSON.stringify({ style: "minimal", instruments: ["piano", "strings", "bass"], seed: Math.floor(Math.random() * 10000) }),
    });
    await loadProject(state.project.id);
    setStatus("Pronto");
  } catch (error) { setStatus(error.message, false); }
};

$("#render").onclick = async () => {
  if (!state.project) return;
  setStatus("Rendering…", false);
  try {
    await api(`/api/projects/${state.project.id}/render`, {
      method: "POST",
      body: JSON.stringify({ formats: ["wav", "mid", "musicxml"] }),
    });
    await loadProject(state.project.id);
    setStatus("Render completato");
  } catch (error) { setStatus(error.message, false); }
};

$("#play").onclick = () => {
  const audio = $("#audio");
  if (audio.paused) audio.play(); else audio.pause();
};
$("#track-filter").onchange = renderScore;

(async () => {
  try {
    await api("/api/health");
    setStatus("Studio online");
    await loadProjects();
  } catch (error) { setStatus(`Offline: ${error.message}`, false); }
})();
