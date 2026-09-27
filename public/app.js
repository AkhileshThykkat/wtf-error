const $ = (selector) => document.querySelector(selector);
const state = { incident: null, incidents: [], evidence: [], messages: [], findings: [], busy: false };
let toastTimer;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.body ? { "content-type": "application/json" } : {}), ...options.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

function toast(message, error = false) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.toggle("error", error);
  node.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove("show"), 3400);
}

function dateLabel(value) {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));
}

async function loadIncidents(selectFirst = true) {
  state.incidents = await api("/api/incidents?limit=100");
  $("#incident-list").innerHTML = state.incidents.map((incident) => `
    <button class="incident-link ${state.incident?.id === incident.id ? "active" : ""}" data-id="${escapeHtml(incident.id)}">
      <strong>${escapeHtml(incident.title)}</strong>
      <small>${escapeHtml(incident.status)} · ${escapeHtml(dateLabel(incident.created_at))}</small>
    </button>`).join("");
  document.querySelectorAll(".incident-link").forEach((button) => {
    button.addEventListener("click", () => selectIncident(button.dataset.id));
  });
  if (state.incident) {
    state.incident = state.incidents.find(({ id }) => id === state.incident.id) || null;
  }
  if (!state.incident && selectFirst && state.incidents.length) await selectIncident(state.incidents[0].id);
  renderWorkspace();
}

function renderWorkspace() {
  const incident = state.incident;
  $("#welcome").hidden = Boolean(incident);
  $("#incident-workspace").hidden = !incident;
  if (!incident) return;
  $("#incident-title").textContent = incident.title;
  $("#incident-status").textContent = incident.status.toUpperCase();
  $("#incident-environment").textContent = incident.environment;
  $("#incident-symptoms").textContent = incident.symptoms;
  $("#evidence-count").textContent = state.evidence.length;
  $("#finding-count").textContent = state.findings.length;
  renderEvidence();
  renderMessages();
  renderFindings();
}

async function selectIncident(id) {
  if (state.busy) return;
  const incident = state.incidents.find((item) => item.id === id);
  if (!incident) return;
  state.incident = incident;
  state.evidence = [];
  state.messages = [];
  state.findings = [];
  renderWorkspace();
  const base = `/api/incidents/${encodeURIComponent(id)}`;
  try {
    [state.evidence, state.messages, state.findings] = await Promise.all([
      api(`${base}/evidence`), api(`${base}/messages`), api(`${base}/findings`),
    ]);
    renderWorkspace();
    await loadIncidents(false);
  } catch (error) {
    toast(error.message, true);
    const base = `/api/incidents/${encodeURIComponent(state.incident.id)}`;
    state.messages = await api(`${base}/messages`).catch(() => state.messages);
    renderMessages();
  }
}

function renderEvidence() {
  const list = $("#evidence-list");
  if (!state.evidence.length) {
    list.innerHTML = '<div class="empty-state">Add a log excerpt or command output. Secrets are masked before saving.</div>';
    return;
  }
  list.innerHTML = state.evidence.map((item) => {
    const lines = item.content.split("\n").map((line) => escapeHtml(line).replace(/^\[([^\]]+)\]/, '<span class="line-ref">[$1]</span>')).join("\n");
    return `<article class="evidence-item" id="evidence-${escapeHtml(item.id)}">
      <div class="item-top"><span>${escapeHtml(item.source)}</span><time>${escapeHtml(dateLabel(item.created_at))}</time></div>
      <pre>${lines}</pre>
    </article>`;
  }).join("");
}

function renderAssistant(content) {
  let result;
  try { result = JSON.parse(content); } catch { return `<p>${escapeHtml(content)}</p>`; }
  const causes = Array.isArray(result.possible_causes) ? result.possible_causes : [];
  const steps = Array.isArray(result.next_steps) ? result.next_steps : [];
  return `<p>${escapeHtml(result.analysis)}</p>
    ${causes.length ? `<ul>${causes.map((cause) => `<li>${escapeHtml(cause)}</li>`).join("")}</ul>` : ""}
    ${steps.length ? `<p class="message-role">NEXT CHECKS</p><ul>${steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ul>` : ""}`;
}

function renderMessages() {
  const node = $("#conversation");
  if (!state.messages.length) {
    node.innerHTML = '<div class="empty-state">Share what you’ve checked so far, or run an investigation to get started.</div>';
    return;
  }
  node.innerHTML = state.messages.map((message) => `
    <article class="message ${message.role === "user" ? "user" : "assistant"}">
      <div class="message-role">${message.role === "user" ? "YOU" : "INVESTIGATION"}</div>
      ${message.role === "assistant" ? renderAssistant(message.content) : `<p>${escapeHtml(message.content)}</p>`}
    </article>`).join("");
  node.scrollTop = node.scrollHeight;
}

function renderFindings() {
  const node = $("#finding-list");
  if (!state.findings.length) {
    node.innerHTML = '<div class="empty-state">Evidence-backed findings will show up here.</div>';
    return;
  }
  node.innerHTML = state.findings.map((finding) => `<article class="finding-item">
    <h3>${escapeHtml(finding.title)}</h3><p>${escapeHtml(finding.detail)}</p>
    ${finding.evidence_line_ids?.length ? `<div class="finding-refs">${finding.evidence_line_ids.map((id) => `<a href="#evidence-${escapeHtml(id.split("-").slice(0, 2).join("-"))}">${escapeHtml(id)}</a>`).join("")}</div>` : ""}
  </article>`).join("");
}

function openIncidentDialog() { $("#incident-dialog").showModal(); }
$("#new-incident-open").addEventListener("click", openIncidentDialog);
$("#new-incident-welcome").addEventListener("click", openIncidentDialog);
$("#new-incident-close").addEventListener("click", () => $("#incident-dialog").close());

$("#incident-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const incident = await api("/api/incidents", { method: "POST", body: JSON.stringify({
      title: $("#new-title").value, symptoms: $("#new-symptoms").value, environment: $("#new-environment").value,
    }) });
    form.reset();
    $("#incident-dialog").close();
    await loadIncidents(false);
    await selectIncident(incident.id);
    toast("Incident created.");
  } catch (error) { toast(error.message, true); }
});

$("#evidence-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.incident) return;
  try {
    const item = await api(`/api/incidents/${encodeURIComponent(state.incident.id)}/evidence`, {
      method: "POST", body: JSON.stringify({ source: $("#evidence-source").value || "Pasted logs", content: $("#evidence-content").value }),
    });
    state.evidence.push(item);
    $("#evidence-content").value = "";
    renderWorkspace();
    toast("Redacted evidence saved.");
  } catch (error) { toast(error.message, true); }
});

async function runInvestigation(question = "") {
  if (!state.incident || state.busy) return;
  state.busy = true;
  $("#investigate-button").disabled = true;
  $("#message-form button").disabled = true;
  try {
    const base = `/api/incidents/${encodeURIComponent(state.incident.id)}`;
    if (question.trim()) {
      await api(`${base}/messages`, { method: "POST", body: JSON.stringify({ content: question.trim() }) });
    }
    await api(`${base}/investigate`, { method: "POST" });
    [state.evidence, state.messages, state.findings] = await Promise.all([
      api(`${base}/evidence`), api(`${base}/messages`), api(`${base}/findings`),
    ]);
    renderWorkspace();
    toast("Investigation updated.");
  } catch (error) {
    toast(error.message, true);
    const base = `/api/incidents/${encodeURIComponent(state.incident.id)}`;
    state.messages = await api(`${base}/messages`).catch(() => state.messages);
    renderMessages();
  }
  finally {
    state.busy = false;
    $("#investigate-button").disabled = false;
    $("#message-form button").disabled = false;
  }
}

$("#investigate-button").addEventListener("click", () => runInvestigation());
$("#message-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#message-input");
  const question = input.value;
  if (!question.trim()) return;
  input.value = "";
  await runInvestigation(question);
});

loadIncidents().catch((error) => toast(error.message, true));
