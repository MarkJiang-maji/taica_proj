const state = {
  summary: null,
  attacks: [],
  selectedAttackId: "PI-RAG-001",
  defenseEnabled: false,
};

const $ = (selector) => document.querySelector(selector);

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function fixed(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function fetchJsonSync(url, options = {}) {
  const request = new XMLHttpRequest();
  request.open(options.method || "GET", url, false);
  request.setRequestHeader("Content-Type", "application/json");
  request.send(options.body || null);
  if (request.status < 200 || request.status >= 300) {
    throw new Error(`${request.status} ${request.statusText}`);
  }
  return JSON.parse(request.responseText);
}

function uniqueAttacks(results) {
  const seen = new Map();
  results.forEach((result) => {
    if (!seen.has(result.attack_id)) {
      seen.set(result.attack_id, result);
    }
  });
  return Array.from(seen.values());
}

function renderOverview(summary) {
  const score = Number(summary.overall_risk_score || 0);
  $("#riskScore").textContent = score;
  $("#riskLevel").textContent = summary.overall_risk_level || "unknown";
  $("#riskArc").style.strokeDashoffset = String(364 - (364 * score) / 100);

  const metrics = [
    ["Undefended ASR", percent(summary.red_team.undefended_attack_success_rate), "Attack suite success before middleware"],
    ["Defended ASR", percent(summary.red_team.defended_attack_success_rate), "Residual success after isolation"],
    ["Poison Retrieval", percent(summary.scanner.poison_retrieval_rate), "High-risk chunks in top-k retrieval"],
    ["Detector F1", fixed(summary.benchmark.f1), `${summary.benchmark.num_rows} public samples`],
  ];
  $("#metricGrid").innerHTML = metrics
    .map(
      ([label, value, detail]) => `
        <div class="metric-card">
          <span>${label}</span>
          <strong>${value}</strong>
          <p>${detail}</p>
        </div>
      `,
    )
    .join("");
}

function renderBenchmark(summary) {
  const metrics = [
    ["Accuracy", summary.benchmark.accuracy],
    ["Precision", summary.benchmark.precision],
    ["Recall", summary.benchmark.recall],
    ["F1", summary.benchmark.f1],
  ];
  $("#benchmarkBars").innerHTML = metrics
    .map(
      ([label, value]) => `
        <div class="bar-row">
          <span>${label}</span>
          <div class="bar-track"><div class="bar-value" style="width:${percent(value)}"></div></div>
          <strong>${fixed(value)}</strong>
        </div>
      `,
    )
    .join("");

  $("#asrChart").innerHTML = [
    ["Defense Off", summary.red_team.undefended_attack_success_rate, "danger"],
    ["Defense On", summary.red_team.defended_attack_success_rate, "safe"],
  ]
    .map(
      ([label, value, tone]) => `
        <div class="compare-bar">
          <strong>${percent(value)}</strong>
          <div class="compare-fill ${tone === "safe" ? "safe" : ""}" style="height:${Math.max(10, Number(value) * 150)}px"></div>
          <span>${label}</span>
        </div>
      `,
    )
    .join("");
}

function renderAttackList() {
  $("#attackList").innerHTML = state.attacks
    .map(
      (attack) => `
        <button class="attack-item ${attack.attack_id === state.selectedAttackId ? "active" : ""}" data-attack-id="${attack.attack_id}" type="button">
          <strong>${attack.attack_id}</strong>
          <span>${attack.name}</span>
        </button>
      `,
    )
    .join("");
  document.querySelectorAll(".attack-item").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedAttackId = button.dataset.attackId;
      renderAttackList();
      loadAttackReplay();
    });
  });
}

function setDefenseMode(enabled) {
  state.defenseEnabled = enabled;
  $("#defenseOff").classList.toggle("active", !enabled);
  $("#defenseOn").classList.toggle("active", enabled);
  loadAttackReplay();
}

async function loadAttackReplay() {
  const payload = await fetchJson("/api/attack", {
    method: "POST",
    body: JSON.stringify({
      attack_id: state.selectedAttackId,
      defense_enabled: state.defenseEnabled,
    }),
  });
  const matched = payload.success_signals.some((signal) =>
    payload.model_output.toLowerCase().includes(signal.toLowerCase()),
  );
  $("#attackTitle").textContent = `${payload.attack_id} ${payload.name}`;
  $("#attackMeta").textContent = `${payload.category} · ${payload.severity}`;
  $("#attackBadge").textContent = matched ? "SUCCESS" : "BLOCKED";
  $("#attackBadge").className = `badge ${matched ? "danger" : "safe"}`;
  $("#userQuery").textContent = payload.user_query;
  $("#maliciousDoc").textContent = payload.malicious_document.content;
  $("#modelOutput").textContent = payload.model_output;
}

function loadAttackReplaySync() {
  const payload = fetchJsonSync("/api/attack", {
    method: "POST",
    body: JSON.stringify({
      attack_id: state.selectedAttackId,
      defense_enabled: state.defenseEnabled,
    }),
  });
  const matched = payload.success_signals.some((signal) =>
    payload.model_output.toLowerCase().includes(signal.toLowerCase()),
  );
  $("#attackTitle").textContent = `${payload.attack_id} ${payload.name}`;
  $("#attackMeta").textContent = `${payload.category} · ${payload.severity}`;
  $("#attackBadge").textContent = matched ? "SUCCESS" : "BLOCKED";
  $("#attackBadge").className = `badge ${matched ? "danger" : "safe"}`;
  $("#userQuery").textContent = payload.user_query;
  $("#maliciousDoc").textContent = payload.malicious_document.content;
  $("#modelOutput").textContent = payload.model_output;
}

function renderKnowledge(summary) {
  $("#scanStats").innerHTML = [
    `${summary.scanner.document_count} documents`,
    `${summary.scanner.high_risk_chunk_count} high-risk chunks`,
    `${percent(summary.scanner.affected_query_rate)} affected queries`,
  ]
    .map((item) => `<span>${item}</span>`)
    .join("");
  $("#knowledgeRows").innerHTML = summary.scanner.retrieval_findings
    .slice(0, 12)
    .map(
      (finding) => `
        <tr>
          <td>${finding.query}</td>
          <td>${finding.rank}</td>
          <td>${finding.title}</td>
          <td class="risk-cell">${finding.risk_score}</td>
          <td>${finding.categories.join(", ")}</td>
        </tr>
      `,
    )
    .join("");
}

function renderTools(summary) {
  $("#toolList").innerHTML = summary.tool_audit.findings
    .map(
      (tool) => `
        <div class="tool-item">
          <div class="tool-top">
            <strong>${tool.tool_name}</strong>
            <span class="badge ${tool.approval_required ? "danger" : "safe"}">${tool.risk_level}</span>
          </div>
          <p>${tool.risky_capabilities.length ? tool.risky_capabilities.join(", ") : "read-only capability"}</p>
          <p>${tool.least_privilege_recommendation}</p>
        </div>
      `,
    )
    .join("");
}

async function renderLlmValidation() {
  const data = await fetchJson("/api/llm-validation");
  if (data.status === "not_run") {
    $("#llmValidation").innerHTML = `
      <p>Local Ollama judge is optional and has not been run in this workspace.</p>
      <code class="code-line">${data.command}</code>
      <p>Recommended local models: qwen3:4b or llama3.2:3b.</p>
    `;
    return;
  }
  $("#llmValidation").innerHTML = `
    <p>Model: ${data.model}</p>
    <p>Completed judgments: ${data.completed}/${data.attempted}</p>
    <p>Agreement with deterministic judge: ${percent(data.agreement_rate)}</p>
    <code class="code-line">${data.setup.command}</code>
  `;
}

function renderLlmValidationSync() {
  const data = fetchJsonSync("/api/llm-validation");
  if (data.status === "not_run") {
    $("#llmValidation").innerHTML = `
      <p>Local Ollama judge is optional and has not been run in this workspace.</p>
      <code class="code-line">${data.command}</code>
      <p>Recommended local models: qwen3:4b or llama3.2:3b.</p>
    `;
    return;
  }
  $("#llmValidation").innerHTML = `
    <p>Model: ${data.model}</p>
    <p>Completed judgments: ${data.completed}/${data.attempted}</p>
    <p>Agreement with deterministic judge: ${percent(data.agreement_rate)}</p>
    <code class="code-line">${data.setup.command}</code>
  `;
}

async function loadSummary() {
  $("#serverStatus").textContent = "Loading evidence";
  state.summary = await fetchJson("/api/summary");
  state.attacks = uniqueAttacks(state.summary.red_team.results);
  renderOverview(state.summary);
  renderBenchmark(state.summary);
  renderAttackList();
  renderKnowledge(state.summary);
  renderTools(state.summary);
  await renderLlmValidation();
  await loadAttackReplay();
  $("#serverStatus").textContent = `Run ${state.summary.run_id}`;
}

function loadSummarySync() {
  $("#serverStatus").textContent = "Loading evidence";
  state.summary = fetchJsonSync("/api/summary");
  state.attacks = uniqueAttacks(state.summary.red_team.results);
  renderOverview(state.summary);
  renderBenchmark(state.summary);
  renderAttackList();
  renderKnowledge(state.summary);
  renderTools(state.summary);
  renderLlmValidationSync();
  loadAttackReplaySync();
  $("#serverStatus").textContent = `Run ${state.summary.run_id}`;
  if (window.location.hash) {
    document.querySelector(window.location.hash)?.scrollIntoView();
  }
}

async function rerunValidation() {
  $("#rerunBtn").disabled = true;
  $("#rerunBtn").textContent = "Running";
  try {
    state.summary = await fetchJson("/api/run", {
      method: "POST",
      body: JSON.stringify({}),
    });
    state.attacks = uniqueAttacks(state.summary.red_team.results);
    renderOverview(state.summary);
    renderBenchmark(state.summary);
    renderAttackList();
    renderKnowledge(state.summary);
    renderTools(state.summary);
    await loadAttackReplay();
    $("#serverStatus").textContent = `Run ${state.summary.run_id}`;
  } finally {
    $("#rerunBtn").disabled = false;
    $("#rerunBtn").textContent = "Run Validation";
  }
}

$("#defenseOff").addEventListener("click", () => setDefenseMode(false));
$("#defenseOn").addEventListener("click", () => setDefenseMode(true));
$("#rerunBtn").addEventListener("click", rerunValidation);

if (new URLSearchParams(window.location.search).has("snapshot")) {
  try {
    loadSummarySync();
  } catch (error) {
    $("#serverStatus").textContent = "API error";
    $("#metricGrid").innerHTML = `<div class="metric-card"><span>Error</span><strong>Failed</strong><p>${error.message}</p></div>`;
  }
} else {
  loadSummary().catch((error) => {
    $("#serverStatus").textContent = "API error";
    $("#metricGrid").innerHTML = `<div class="metric-card"><span>Error</span><strong>Failed</strong><p>${error.message}</p></div>`;
  });
}
