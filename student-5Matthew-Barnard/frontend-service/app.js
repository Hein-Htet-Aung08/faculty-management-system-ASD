const API = '/api';

const resources = {
  'development-goals': {
    title: 'Development goals', singular: 'goal', kicker: 'Development planning',
    description: 'Track measurable goals and progress for each staff member.',
    id: 'goalID', filters: ['staffID', 'status'],
    statuses: ['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled'],
    columns: [
      ['goalID', 'ID'], ['staffID', 'Staff'], ['title', 'Goal'],
      ['targetDate', 'Target'], ['progress', 'Progress'], ['status', 'Status']
    ],
    fields: [
      ['staffID', 'Staff ID', 'number', true], ['title', 'Title', 'text', true],
      ['description', 'Description', 'textarea'], ['targetDate', 'Target date', 'date'],
      ['progress', 'Progress (%)', 'number'],
      ['status', 'Status', 'select', true, ['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled']]
    ]
  },
  'performance-reviews': {
    title: 'Performance reviews', singular: 'review', kicker: 'Performance records',
    description: 'Record ratings, feedback, reviewers and acknowledgement status.',
    id: 'reviewID', filters: ['staffID', 'status'],
    statuses: ['Draft', 'Scheduled', 'Completed', 'Acknowledged'],
    columns: [
      ['reviewID', 'ID'], ['staffID', 'Staff'], ['reviewDate', 'Review date'],
      ['rating', 'Rating'], ['feedback', 'Feedback'], ['status', 'Status']
    ],
    fields: [
      ['staffID', 'Staff ID', 'number', true], ['reviewDate', 'Review date', 'date', true],
      ['reviewerID', 'Reviewer ID', 'number', true], ['rating', 'Rating (1–5)', 'number'],
      ['feedback', 'Feedback', 'textarea'],
      ['status', 'Status', 'select', true, ['Draft', 'Scheduled', 'Completed', 'Acknowledged']]
    ]
  },
  'training-programs': {
    title: 'Training catalogue', singular: 'training program', kicker: 'Learning opportunities',
    description: 'Maintain available programs, dates, providers and skill areas.',
    id: 'trainingID', filters: [], statuses: [],
    columns: [
      ['trainingID', 'ID'], ['title', 'Program'], ['provider', 'Provider'],
      ['startDate', 'Starts'], ['endDate', 'Ends'], ['skillArea', 'Skill area']
    ],
    fields: [
      ['title', 'Title', 'text', true], ['description', 'Description', 'textarea'],
      ['provider', 'Provider', 'text'], ['startDate', 'Start date', 'date'],
      ['endDate', 'End date', 'date'], ['skillArea', 'Skill area', 'text']
    ]
  },
  'staff-training': {
    title: 'Staff training', singular: 'staff training record', kicker: 'Training participation',
    description: 'Track staff enrolment, completion and withdrawal status.',
    id: 'staffTrainingID', filters: ['staffID', 'status'],
    statuses: ['Enrolled', 'In Progress', 'Completed', 'Withdrawn'],
    columns: [
      ['staffTrainingID', 'ID'], ['staffID', 'Staff'], ['trainingID', 'Program ID'],
      ['enrolmentDate', 'Enrolled'], ['completionDate', 'Completed'], ['status', 'Status']
    ],
    fields: [
      ['staffID', 'Staff ID', 'number', true], ['trainingID', 'Training program ID', 'number', true],
      ['enrolmentDate', 'Enrolment date', 'date'], ['completionDate', 'Completion date', 'date'],
      ['status', 'Status', 'select', true, ['Enrolled', 'In Progress', 'Completed', 'Withdrawn']]
    ]
  },
  'development-recommendations': {
    title: 'Development recommendations', singular: 'recommendation', kicker: 'Human-reviewed advice',
    description: 'Review AI-generated and manager-created actions with their rationale.',
    id: 'recommendationID', filters: ['staffID', 'status'],
    statuses: ['Pending', 'Accepted', 'Rejected', 'Modified'],
    columns: [
      ['recommendationID', 'ID'], ['staffID', 'Staff'], ['recommendationType', 'Type'],
      ['recommendation', 'Recommendation'], ['rationale', 'Rationale'], ['status', 'Decision']
    ],
    fields: [
      ['staffID', 'Staff ID', 'number', true], ['goalID', 'Related goal ID', 'number'],
      ['recommendationType', 'Type', 'select', true, ['Training', 'Goal', 'Mentoring', 'Experience']],
      ['recommendation', 'Recommendation', 'textarea', true], ['rationale', 'Rationale', 'textarea'],
      ['dateGenerated', 'Date generated', 'date', true],
      ['status', 'Decision status', 'select', true, ['Pending', 'Accepted', 'Rejected', 'Modified']]
    ]
  }
};

let currentResource = 'development-goals';
let currentRows = [];
let editingId = null;
let currentWorkflow = null;
let multiAgentEnabled = false;
let multiAgentBusy = false;
const staffDirectory = new Map();

const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? '')
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  const body = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.details || body?.error || `Request failed (${response.status})`);
  return body;
}

function toast(message, isError = false) {
  const element = $('#toast');
  element.textContent = message;
  element.className = `toast show ${isError ? 'error' : ''}`;
  window.setTimeout(() => { element.className = 'toast'; }, 3200);
}

function statusPill(value) {
  const key = String(value || '').toLowerCase().replaceAll(' ', '-');
  return `<span class="stamp status-pill status-${escapeHtml(key)}">${escapeHtml(value || '—')}</span>`;
}

function formatCell(field, value) {
  if (field === 'status') return statusPill(value);
  if (field === 'staffID' || field === 'reviewerID') {
    const name = staffDirectory.get(Number(value));
    return name ? `${escapeHtml(name)} <small class="record-id">#${escapeHtml(value)}</small>` : escapeHtml(value);
  }
  if (field === 'progress') {
    const progress = Number(value || 0);
    return `<div class="progress-cell"><span>${progress}%</span><div><i style="width:${progress}%"></i></div></div>`;
  }
  if (field === 'rating') return value == null ? '—' : `${escapeHtml(value)} / 5`;
  return escapeHtml(value == null || value === '' ? '—' : value);
}

async function loadStaffDirectory() {
  try {
    const result = await api('/integration/staff');
    (result.staff || []).forEach((staff) => {
      staffDirectory.set(Number(staff.staff_id), staff.name);
    });
  } catch (_) {
    // Staff names are an integration enhancement; IDs remain usable standalone.
  }
}

async function loadMetrics() {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const [reviews, goals, programs, recommendations] = await Promise.all([
        api('/performance-reviews'), api('/development-goals'), api('/training-programs'),
        api('/development-recommendations')
      ]);
      $('#count-reviews').textContent = reviews.length;
      $('#count-goals').textContent = goals.filter((goal) => !['Completed', 'Cancelled'].includes(goal.status)).length;
      $('#count-programs').textContent = programs.length;
      $('#count-recommendations').textContent = recommendations.filter((row) => row.status === 'Pending').length;
      return;
    } catch (error) {
      if (attempt === 2) toast(error.message, true);
      else await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
  }
}

function configureFilters(config) {
  const hasStaff = config.filters.includes('staffID');
  const hasStatus = config.filters.includes('status');
  $('#staff-filter-label').hidden = !hasStaff;
  $('#status-filter-label').hidden = !hasStatus;
  $('#status-filter').innerHTML = '<option value="">All statuses</option>'
    + config.statuses.map((status) => `<option>${escapeHtml(status)}</option>`).join('');
}

function filterQuery(config) {
  const params = new URLSearchParams();
  if (config.filters.includes('staffID') && $('#staff-filter').value) {
    params.set('staffID', $('#staff-filter').value);
  }
  if (config.filters.includes('status') && $('#status-filter').value) {
    params.set('status', $('#status-filter').value);
  }
  return params.toString() ? `?${params}` : '';
}

async function loadResource() {
  const config = resources[currentResource];
  $('#table-body').innerHTML = '<tr><td colspan="20" class="loading-cell">Loading records…</td></tr>';
  try {
    currentRows = await api(`/${currentResource}${filterQuery(config)}`);
    renderTable(config);
  } catch (error) {
    currentRows = [];
    renderTable(config);
    toast(error.message, true);
  }
}

function renderTable(config) {
  $('#table-head').innerHTML = config.columns
    .map(([, label]) => `<th>${escapeHtml(label)}</th>`).join('') + '<th>Actions</th>';
  $('#empty-state').hidden = currentRows.length > 0;
  $('#table-body').innerHTML = currentRows.map((row) => {
    const cells = config.columns.map(([field]) => `<td>${formatCell(field, row[field])}</td>`).join('');
    const decisions = currentResource === 'development-recommendations' && row.status === 'Pending'
      ? `<button class="mini-button accept" data-decision="Accepted">Accept</button>
         <button class="mini-button reject" data-decision="Rejected">Reject</button>` : '';
    return `<tr data-id="${row[config.id]}">${cells}<td class="actions-cell">
      ${decisions}<button class="mini-button" data-action="edit">Edit</button>
      <button class="mini-button danger" data-action="delete">Delete</button></td></tr>`;
  }).join('');
}

function activateResource(resource) {
  document.querySelectorAll('.nav-button').forEach((button) => {
    button.classList.toggle('active', button.dataset.resource === resource);
  });
  $('#multi-agent-panel').hidden = resource !== 'multi-agent-mode';
  if (resource === 'multi-agent-mode') {
    $('#resource-panel').hidden = true;
    $('#ai-panel').hidden = true;
    $('#mcp-panel').hidden = true;
    $('#rag-panel').hidden = true;
    checkMultiAgent();
    return;
  }
  if (resource === 'ai-mode') {
    $('#resource-panel').hidden = true;
    $('#ai-panel').hidden = false;
    $('#mcp-panel').hidden = true;
    $('#rag-panel').hidden = true;
    return;
  }
  if (resource === 'mcp-mode') {
    $('#resource-panel').hidden = true;
    $('#ai-panel').hidden = true;
    $('#mcp-panel').hidden = false;
    $('#rag-panel').hidden = true;
    return;
  }
  if (resource === 'rag-mode') {
    $('#resource-panel').hidden = true;
    $('#ai-panel').hidden = true;
    $('#mcp-panel').hidden = true;
    $('#rag-panel').hidden = false;
    return;
  }
  currentResource = resource;
  const config = resources[resource];
  $('#resource-panel').hidden = false;
  $('#ai-panel').hidden = true;
  $('#mcp-panel').hidden = true;
  $('#rag-panel').hidden = true;
  $('#resource-kicker').textContent = config.kicker;
  $('#resource-title').textContent = config.title;
  $('#resource-description').textContent = config.description;
  $('#add-record').textContent = `+ Add ${config.singular}`;
  configureFilters(config);
  loadResource();
}

function makeField([name, label, type, required, options], value) {
  const requiredMark = required ? ' <span>*</span>' : '';
  let control;
  if (type === 'textarea') {
    control = `<textarea id="field-${name}" name="${name}" ${required ? 'required' : ''}>${escapeHtml(value ?? '')}</textarea>`;
  } else if (type === 'select') {
    control = `<select id="field-${name}" name="${name}" ${required ? 'required' : ''}>
      <option value="">Select…</option>${options.map((option) =>
        `<option ${value === option ? 'selected' : ''}>${escapeHtml(option)}</option>`).join('')}</select>`;
  } else {
    const step = ['progress', 'rating'].includes(name) ? '0.1' : '1';
    control = `<input id="field-${name}" name="${name}" type="${type}" value="${escapeHtml(value ?? '')}"
      ${type === 'number' ? `step="${step}"` : ''} ${required ? 'required' : ''} />`;
  }
  return `<label class="${type === 'textarea' ? 'wide-field' : ''}">${label}${requiredMark}${control}</label>`;
}

function openForm(row = null) {
  const config = resources[currentResource];
  editingId = row ? row[config.id] : null;
  $('#form-kicker').textContent = row ? `Editing ${config.singular}` : 'New record';
  $('#form-title').textContent = `${row ? 'Update' : 'Add'} ${config.singular}`;
  $('#form-fields').innerHTML = config.fields.map((field) => makeField(field, row?.[field[0]])).join('');
  $('#form-error').hidden = true;
  $('#record-dialog').showModal();
}

function readForm() {
  const config = resources[currentResource];
  const payload = {};
  config.fields.forEach(([name, , type, required]) => {
    const value = $(`#field-${name}`).value;
    if (value === '' && !required) return;
    payload[name] = type === 'number' ? Number(value) : value;
  });
  return payload;
}

async function saveForm(event) {
  event.preventDefault();
  const config = resources[currentResource];
  try {
    const path = editingId ? `/${currentResource}/${editingId}` : `/${currentResource}`;
    await api(path, { method: editingId ? 'PUT' : 'POST', body: JSON.stringify(readForm()) });
    $('#record-dialog').close();
    toast(`${config.singular} ${editingId ? 'updated' : 'created'}`);
    await Promise.all([loadResource(), loadMetrics()]);
  } catch (error) {
    $('#form-error').textContent = error.message;
    $('#form-error').hidden = false;
  }
}

async function handleTableAction(event) {
  const button = event.target.closest('button');
  const rowElement = event.target.closest('tr[data-id]');
  if (!button || !rowElement) return;
  const config = resources[currentResource];
  const id = Number(rowElement.dataset.id);
  const row = currentRows.find((item) => item[config.id] === id);

  if (button.dataset.action === 'edit') return openForm(row);
  if (button.dataset.decision) {
    try {
      await api(`/${currentResource}/${id}`, {
        method: 'PUT', body: JSON.stringify({ status: button.dataset.decision })
      });
      toast(`Recommendation ${button.dataset.decision.toLowerCase()}`);
      await Promise.all([loadResource(), loadMetrics()]);
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (button.dataset.action === 'delete') {
    if (!window.confirm(`Delete this ${config.singular}?`)) return;
    try {
      await api(`/${currentResource}/${id}`, { method: 'DELETE' });
      toast(`${config.singular} deleted`);
      await Promise.all([loadResource(), loadMetrics()]);
    } catch (error) { toast(error.message, true); }
  }
}

async function checkAi() {
  const status = $('#ai-status');
  status.textContent = 'Checking…';
  status.className = 'ai-status checking';
  try {
    const result = await api('/ai/health');
    status.textContent = `${result.model} ready`;
    status.className = 'ai-status ready';
  } catch (error) {
    status.textContent = 'Ollama unavailable';
    status.className = 'ai-status failed';
    toast(error.message, true);
  }
}

async function generateAiRecommendation() {
  const staffID = Number($('#ai-staff-id').value);
  const button = $('#generate-ai');
  const resultBox = $('#ai-result');
  button.disabled = true;
  button.textContent = 'Generating…';
  try {
    const result = await api('/ai/recommend-development', {
      method: 'POST', body: JSON.stringify({ staffID })
    });
    const rec = result.recommendation;
    resultBox.innerHTML = `<p class="eyebrow ai-accent">Saved as recommendation #${rec.recommendationID}</p>
      <h3>${escapeHtml(rec.recommendation)}</h3><p>${escapeHtml(rec.rationale)}</p>
      <div class="ai-meta"><span>${escapeHtml(rec.recommendationType)}</span>
      <span>${escapeHtml(result.model)}</span>${statusPill(rec.status)}</div>`;
    resultBox.hidden = false;
    toast('AI recommendation generated and saved for review');
    await loadMetrics();
  } catch (error) {
    resultBox.innerHTML = `<h3>Recommendation could not be generated</h3><p>${escapeHtml(error.message)}</p>`;
    resultBox.hidden = false;
    toast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = 'Generate recommendation';
  }
}

async function checkMcp() {
  try {
    const result = await api('/mcp/status');
    $('#mcp-status').textContent = result.enabled ? 'MCP enabled' : 'MCP disabled';
    $('#mcp-status').className = `ai-status ${result.enabled ? 'ready' : 'failed'}`;
  } catch (_) {
    $('#mcp-status').textContent = 'Backend unavailable';
    $('#mcp-status').className = 'ai-status failed';
  }
}

function mcpTable(columns, rows) {
  if (!rows.length) return '<p>No records found.</p>';
  const head = columns.map(([, title]) => `<th>${escapeHtml(title)}</th>`).join('');
  const body = rows.map((row) => `<tr>${columns.map(([field]) =>
    `<td>${escapeHtml(row[field] ?? '—')}</td>`).join('')}</tr>`).join('');
  return `<div class="table-wrap"><table class="ledger-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function mcpSection(title, columns, rows) {
  return `<section class="mcp-section"><h4>${escapeHtml(title)} (${rows.length})</h4>${mcpTable(columns, rows)}</section>`;
}

async function runMcp(buttonSelector, resultSelector, path, payload, render) {
  const button = $(buttonSelector);
  const resultBox = $(resultSelector);
  button.disabled = true;
  resultBox.hidden = false;
  resultBox.textContent = 'Calling MCP tool…';
  try {
    const result = await api(path, { method: 'POST', body: JSON.stringify(payload) });
    resultBox.innerHTML = render(result);
  } catch (error) {
    resultBox.innerHTML = `<p class="form-error">${escapeHtml(error.message)}</p>`;
  } finally {
    button.disabled = false;
  }
}

function showDevelopmentSummary(result) {
  const data = result.data;
  const name = staffDirectory.get(Number(data.staffID));
  const title = name ? `${escapeHtml(name)} <small class="record-id">#${data.staffID}</small>`
    : `Staff #${escapeHtml(data.staffID)}`;
  return `<h3>${title}</h3>`
    + mcpSection('Performance reviews', [
      ['reviewDate', 'Date'], ['rating', 'Rating'], ['feedback', 'Feedback'], ['status', 'Status']
    ], data.reviews)
    + mcpSection('Development goals', [
      ['title', 'Goal'], ['progress', 'Progress (%)'], ['targetDate', 'Target'], ['status', 'Status']
    ], data.goals)
    + mcpSection('Staff training', [
      ['trainingTitle', 'Program'], ['enrolmentDate', 'Enrolled'], ['status', 'Status']
    ], data.training)
    + mcpSection('Recommendations', [
      ['recommendation', 'Recommendation'], ['rationale', 'Rationale'], ['status', 'Decision']
    ], data.recommendations);
}

function showTrainingPrograms(result) {
  return `<h3>${escapeHtml(result.match_count)} program(s) for ${escapeHtml(result.query)}</h3>`
    + mcpTable([
      ['title', 'Program'], ['provider', 'Provider'], ['startDate', 'Starts'],
      ['endDate', 'Ends'], ['skillArea', 'Skill area']
    ], result.data);
}

async function checkRag() {
  try {
    const result = await api('/rag/status');
    $('#rag-status').textContent = result.enabled ? 'RAG enabled' : 'RAG disabled';
    $('#rag-status').className = `ai-status ${result.enabled ? 'ready' : 'failed'}`;
  } catch (_) {
    $('#rag-status').textContent = 'Backend unavailable';
    $('#rag-status').className = 'ai-status failed';
  }
}

function showRagAnswer(result) {
  const answer = String(result.answer || '').trim();
  if (!answer || answer.toLowerCase().startsWith('insufficient context')) {
    return '<p class="eyebrow ai-accent">Confidence: Insufficient</p><h3>Insufficient context</h3><p>There is not enough relevant recorded information to answer this question.</p>';
  }
  const citations = Array.isArray(result.citations) ? result.citations : [];
  const sources = citations.length
    ? `<h4>Sources</h4><ol class="rag-sources">${citations.map((citation) =>
      `<li>${escapeHtml(citation.source_id)} <span>${escapeHtml(citation.authority_tier)}</span></li>`
    ).join('')}</ol>`
    : '<p>No sources returned.</p>';
  return `<p class="eyebrow ai-accent">Confidence: ${escapeHtml(result.confidence_category || 'Unknown')}</p>
    <h3>Grounded answer</h3><p>${escapeHtml(answer)}</p>${sources}`;
}

async function askRag() {
  const query = $('#rag-query').value.trim();
  const resultBox = $('#rag-result');
  if (!query) {
    resultBox.hidden = false;
    resultBox.innerHTML = '<p class="form-error">Enter a question first.</p>';
    return;
  }
  const button = $('#rag-ask-button');
  button.disabled = true;
  resultBox.hidden = false;
  resultBox.textContent = 'Retrieving context and generating an answer…';
  try {
    const result = await api('/rag/ask', { method: 'POST', body: JSON.stringify({ query }) });
    resultBox.innerHTML = showRagAnswer(result);
  } catch (error) {
    resultBox.innerHTML = `<p class="form-error">${escapeHtml(error.message)}</p>`;
  } finally {
    button.disabled = false;
  }
}

async function refreshRag() {
  const button = $('#rag-refresh-button');
  const resultBox = $('#rag-result');
  button.disabled = true;
  resultBox.hidden = false;
  resultBox.textContent = 'Refreshing context from current records…';
  try {
    const result = await api('/rag/refresh', { method: 'POST' });
    resultBox.innerHTML = `<p>Context refreshed: ${escapeHtml(result.chunk_count)} chunks indexed.</p>`;
  } catch (error) {
    resultBox.innerHTML = `<p class="form-error">${escapeHtml(error.message)}</p>`;
  } finally {
    button.disabled = false;
  }
}

function setMultiAgentBusy(busy) {
  multiAgentBusy = busy;
  $('#multi-agent-run').disabled = busy || !multiAgentEnabled;
  $('#multi-agent-refresh').disabled = busy || !multiAgentEnabled;
  $('#multi-agent-review-fields').disabled = busy || !multiAgentEnabled
    || currentWorkflow?.human_decision?.status !== 'pending';
  $('#multi-agent-history').querySelectorAll('button').forEach((button) => {
    button.disabled = busy || !multiAgentEnabled;
  });
}

function multiAgentMessage(message, isError = false) {
  const box = $('#multi-agent-message');
  box.textContent = message;
  box.className = isError ? 'form-error' : '';
  box.hidden = !message;
}

async function checkMultiAgent() {
  if (multiAgentBusy) return;
  setMultiAgentBusy(true);
  const status = $('#multi-agent-status');
  status.textContent = 'Checking...';
  status.className = 'ai-status checking';
  try {
    const result = await api('/multi-agent/status');
    multiAgentEnabled = result.enabled;
    status.textContent = result.enabled ? 'Multi-Agent enabled' : 'Multi-Agent disabled';
    status.className = `ai-status ${result.enabled ? 'ready' : 'failed'}`;
    if (result.enabled) await loadMultiAgentHistory();
  } catch (error) {
    multiAgentEnabled = false;
    status.textContent = 'Backend unavailable';
    status.className = 'ai-status failed';
    multiAgentMessage(error.message, true);
  } finally {
    setMultiAgentBusy(false);
  }
}

function multiAgentStage(title, result, field) {
  return `<section class="workflow-stage"><h3>${escapeHtml(title)}</h3>
    <p class="workflow-meta">Status: ${escapeHtml(result?.status || 'Unknown')}</p>
    <div class="workflow-text">${escapeHtml(result?.[field] || 'No output returned.')}</div></section>`;
}

function showMultiAgentWorkflow(workflow) {
  currentWorkflow = workflow;
  const decision = workflow.human_decision || {};
  const checks = Array.isArray(workflow.automated_checks) ? workflow.automated_checks : [];
  const sources = workflow.worker_result?.evidence_sources || [];
  const recorded = decision.status === 'recorded'
    ? `<section class="workflow-stage"><h3>Human decision: ${escapeHtml(decision.decision)}</h3>
      <p>Reviewed by ${escapeHtml(decision.reviewer)}</p>
      <div class="workflow-text">${escapeHtml(decision.notes || '')}</div>
      ${decision.correction ? `<h4>Correction</h4><div class="workflow-text">${escapeHtml(decision.correction)}</div>` : ''}</section>`
    : '';
  const box = $('#multi-agent-result');
  box.innerHTML = `<h3>${escapeHtml(workflow.user_request)}</h3>
    <p class="workflow-meta">${escapeHtml(workflow.workflow_id)} | ${escapeHtml(String(workflow.status || '').replaceAll('_', ' '))}</p>`
    + multiAgentStage('Planner', workflow.planner_result, 'plan')
    + multiAgentStage('Worker', workflow.worker_result, 'output')
    + multiAgentStage('Reviewer', workflow.reviewer_result, 'review')
    + `<section class="workflow-stage"><h3>Automated checks</h3><ul>${checks.map((check) =>
      `<li>${check.passed ? 'Passed' : 'Failed'}: ${escapeHtml(check.check)}${check.detail ? ` - ${escapeHtml(check.detail)}` : ''}</li>`
    ).join('')}</ul>
      <details><summary>Evidence sources (${sources.length})</summary>
      <ul class="rag-sources">${sources.map((source) => `<li>${escapeHtml(source)}</li>`).join('')}</ul></details></section>`
    + recorded;
  box.hidden = false;
  $('#multi-agent-decision-form').reset();
  $('#multi-agent-decision-form').hidden = decision.status !== 'pending';
  updateMultiAgentCorrection();
}

function updateMultiAgentCorrection() {
  const correcting = $('#multi-agent-decision').value === 'Correct';
  $('#multi-agent-correction-label').hidden = !correcting;
  $('#multi-agent-correction').required = correcting;
  $('#multi-agent-correction').disabled = !correcting;
}

async function loadMultiAgentHistory() {
  const box = $('#multi-agent-history');
  box.textContent = 'Loading history...';
  try {
    const result = await api('/multi-agent/workflow/history?limit=20');
    const workflows = result.workflows || [];
    box.innerHTML = workflows.length ? `<ul class="workflow-history">${workflows.map((workflow) =>
      `<li><button type="button" class="btn secondary secondary-button" data-workflow-id="${escapeHtml(workflow.workflow_id)}">${escapeHtml(workflow.user_request)}</button>
        <span class="workflow-meta">${escapeHtml(String(workflow.status || '').replaceAll('_', ' '))} | ${escapeHtml(workflow.timestamp)}</span></li>`
    ).join('')}</ul>` : '<p>No workflows recorded yet.</p>';
    setMultiAgentBusy(multiAgentBusy);
  } catch (error) {
    box.innerHTML = `<p class="form-error">${escapeHtml(error.message)}</p>`;
  }
}

async function runMultiAgentWorkflow(event) {
  event.preventDefault();
  if (multiAgentBusy || !multiAgentEnabled) return;
  const user_request = $('#multi-agent-request').value.trim();
  if (!user_request) return multiAgentMessage('Enter a request first.', true);
  setMultiAgentBusy(true);
  currentWorkflow = null;
  $('#multi-agent-result').hidden = true;
  $('#multi-agent-decision-form').hidden = true;
  $('#multi-agent-run').textContent = 'Running...';
  multiAgentMessage('Running Planner, Worker and Reviewer. This may take several minutes.');
  try {
    const workflow = await api('/multi-agent/workflow', {
      method: 'POST', body: JSON.stringify({ user_request })
    });
    showMultiAgentWorkflow(workflow);
    multiAgentMessage('Workflow ready for human review.');
    await loadMultiAgentHistory();
  } catch (error) {
    multiAgentMessage(error.message, true);
  } finally {
    $('#multi-agent-run').textContent = 'Run workflow';
    setMultiAgentBusy(false);
  }
}

async function openMultiAgentWorkflow(workflowId) {
  if (multiAgentBusy || !multiAgentEnabled) return;
  setMultiAgentBusy(true);
  currentWorkflow = null;
  $('#multi-agent-result').hidden = true;
  $('#multi-agent-decision-form').hidden = true;
  multiAgentMessage('Loading workflow...');
  try {
    const workflow = await api(`/multi-agent/workflow/${encodeURIComponent(workflowId)}`);
    showMultiAgentWorkflow(workflow);
    multiAgentMessage('');
  } catch (error) {
    multiAgentMessage(error.message, true);
  } finally {
    setMultiAgentBusy(false);
  }
}

async function saveMultiAgentDecision(event) {
  event.preventDefault();
  if (multiAgentBusy || !multiAgentEnabled || currentWorkflow?.human_decision?.status !== 'pending') return;
  const payload = {
    decision: $('#multi-agent-decision').value,
    reviewer: $('#multi-agent-reviewer').value.trim(),
    notes: $('#multi-agent-notes').value.trim()
  };
  if (!payload.reviewer) return multiAgentMessage('Enter your name first.', true);
  if (payload.decision === 'Correct') {
    payload.correction = $('#multi-agent-correction').value.trim();
    if (!payload.correction) return multiAgentMessage('Enter the correction first.', true);
  }
  setMultiAgentBusy(true);
  multiAgentMessage('Saving human decision...');
  try {
    const workflow = await api(`/multi-agent/workflow/${encodeURIComponent(currentWorkflow.workflow_id)}/decision`, {
      method: 'POST', body: JSON.stringify(payload)
    });
    showMultiAgentWorkflow(workflow);
    multiAgentMessage('Human decision saved.');
    await loadMultiAgentHistory();
  } catch (error) {
    multiAgentMessage(error.message, true);
  } finally {
    setMultiAgentBusy(false);
  }
}

$('#multi-agent-request-form').addEventListener('submit', runMultiAgentWorkflow);
$('#multi-agent-decision-form').addEventListener('submit', saveMultiAgentDecision);
$('#multi-agent-decision').addEventListener('change', updateMultiAgentCorrection);
$('#multi-agent-refresh').addEventListener('click', async () => {
  if (multiAgentBusy || !multiAgentEnabled) return;
  setMultiAgentBusy(true);
  try { await loadMultiAgentHistory(); }
  finally { setMultiAgentBusy(false); }
});
$('#multi-agent-history').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-workflow-id]');
  if (button) openMultiAgentWorkflow(button.dataset.workflowId);
});

document.querySelectorAll('.nav-button').forEach((button) => {
  button.addEventListener('click', () => activateResource(button.dataset.resource));
});
$('#add-record').addEventListener('click', () => openForm());
$('#apply-filters').addEventListener('click', loadResource);
$('#clear-filters').addEventListener('click', () => {
  $('#staff-filter').value = '';
  $('#status-filter').value = '';
  loadResource();
});
$('#table-body').addEventListener('click', handleTableAction);
$('#record-form').addEventListener('submit', saveForm);
$('#close-dialog').addEventListener('click', () => $('#record-dialog').close());
$('#cancel-dialog').addEventListener('click', () => $('#record-dialog').close());
$('#check-ai').addEventListener('click', checkAi);
$('#generate-ai').addEventListener('click', generateAiRecommendation);
$('#mcp-summary-button').addEventListener('click', () => runMcp(
  '#mcp-summary-button', '#mcp-summary-result', '/mcp/development-summary',
  { staffID: Number($('#mcp-staff-id').value) }, showDevelopmentSummary
));
$('#mcp-training-button').addEventListener('click', () => runMcp(
  '#mcp-training-button', '#mcp-training-result', '/mcp/training-by-skill',
  { skillArea: $('#mcp-skill-area').value.trim() }, showTrainingPrograms
));
$('#rag-ask-button').addEventListener('click', askRag);
$('#rag-refresh-button').addEventListener('click', refreshRag);

async function initialise() {
  await loadStaffDirectory();
  await loadMetrics();
  await checkMcp();
  await checkRag();
  activateResource('development-goals');
}

initialise();
