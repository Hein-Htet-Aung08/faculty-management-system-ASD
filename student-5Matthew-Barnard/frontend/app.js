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
  if (!response.ok) throw new Error(body?.error || `Request failed (${response.status})`);
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
  return `<span class="status-pill status-${escapeHtml(key)}">${escapeHtml(value || '—')}</span>`;
}

function formatCell(field, value) {
  if (field === 'status') return statusPill(value);
  if (field === 'progress') {
    const progress = Number(value || 0);
    return `<div class="progress-cell"><span>${progress}%</span><div><i style="width:${progress}%"></i></div></div>`;
  }
  if (field === 'rating') return value == null ? '—' : `${escapeHtml(value)} / 5`;
  return escapeHtml(value == null || value === '' ? '—' : value);
}

async function checkServices() {
  try {
    await api('/health');
    $('#service-status').textContent = 'Services online';
    $('#service-dot').classList.add('online');
  } catch (_) {
    try {
      const response = await fetch('/api/development-goals');
      if (!response.ok) throw new Error();
      $('#service-status').textContent = 'Services online';
      $('#service-dot').classList.add('online');
    } catch (_) {
      $('#service-status').textContent = 'Services unavailable';
      $('#service-dot').classList.add('offline');
    }
  }
}

async function loadMetrics() {
  try {
    const [reviews, goals, programs, recommendations] = await Promise.all([
      api('/performance-reviews'), api('/development-goals'), api('/training-programs'),
      api('/development-recommendations')
    ]);
    $('#count-reviews').textContent = reviews.length;
    $('#count-goals').textContent = goals.filter((goal) => !['Completed', 'Cancelled'].includes(goal.status)).length;
    $('#count-programs').textContent = programs.length;
    $('#count-recommendations').textContent = recommendations.filter((row) => row.status === 'Pending').length;
  } catch (error) {
    toast(error.message, true);
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
  if (resource === 'ai-mode') {
    $('#resource-panel').hidden = true;
    $('#ai-panel').hidden = false;
    return;
  }
  currentResource = resource;
  const config = resources[resource];
  $('#resource-panel').hidden = false;
  $('#ai-panel').hidden = true;
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

checkServices();
loadMetrics();
activateResource('development-goals');
