const API_BASE = "http://127.0.0.1:5001";
let currentStaffId = null;
let editingStaffId = null;


// --- RENDERING ---
function renderStaffRows(staffArray) {
    const tbody = document.getElementById("staff-table-body");
    tbody.innerHTML = staffArray.map(person => `
        <tr>
            <td>${person.name}</td>
            <td>${person.department_name}</td>
            <td>${person.position}</td>
            <td>${person.expertise_area || "—"}</td>
            <td>${person.status}</td>
            <td>
                <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                    <button class="btn secondary" style="padding: 0.35rem 0.7rem; font-size: 0.8rem;" onclick="viewStaffDetail(${person.staff_id})">View</button>
                    <button class="btn secondary" style="padding: 0.35rem 0.7rem; font-size: 0.8rem;" onclick="editStaff(${person.staff_id})">Edit</button>
                    <button class="btn secondary" style="padding: 0.35rem 0.7rem; font-size: 0.8rem; border-color: var(--alert-rust); color: var(--alert-rust);" onclick="deleteStaff(${person.staff_id})">Delete</button>
                </div>
            </td>
        </tr>
    `).join("");
}

// --- DATA LOADING ---
async function loadStaffList() {
    const response = await fetch(`${API_BASE}/api/staff`);
    const staff = await response.json();
    renderStaffRows(staff);
    populatePositionOptions(staff);
}

async function loadDepartmentOptions(targetElementId) {
    const response = await fetch(`${API_BASE}/api/departments`);
    const departments = await response.json();
    const select = document.getElementById(targetElementId);
    select.innerHTML = '<option value="">-- Select Department --</option>';

    departments.forEach(dept => {
        const option = document.createElement("option");
        option.value = dept.department_id;
        option.textContent = dept.department_name;
        select.appendChild(option);
    });
}

function populatePositionOptions(staffArray) {
    const positions = [...new Set(staffArray.map(person => person.position))];

    const select = document.getElementById("position-filter");
    select.innerHTML = '<option value="">-- Select Position --</option>';  // reset first

    positions.forEach(pos => {
        const option = document.createElement("option");
        option.value = pos;
        option.textContent = pos;
        select.appendChild(option);
    });
}

// --- STAFF ACTIONS ---
async function deleteStaff(staffId) {
    const confirmed = confirm("Are you sure you want to delete this staff member?");
    if (!confirmed) return;

    const response = await fetch(`${API_BASE}/api/staff/${staffId}`, {
        method: "DELETE"
    });

    if (response.ok) {
        loadStaffList();  // refresh the table
    } else {
        alert("Failed to delete staff member.");
    }
}

async function viewStaffDetail(staffId) {
    currentStaffId = staffId;

    const [staffRes, qualRes, expRes, availRes] = await Promise.all([
        fetch(`${API_BASE}/api/staff/${staffId}`),
        fetch(`${API_BASE}/api/staff/${staffId}/qualifications`),
        fetch(`${API_BASE}/api/staff/${staffId}/expertise`),
        fetch(`${API_BASE}/api/staff/${staffId}/availability`)
    ]);

    const staff = await staffRes.json();
    const qualifications = await qualRes.json();
    const expertise = await expRes.json();
    const availability = await availRes.json();

    document.getElementById("detail-name").textContent = staff.name;
    document.getElementById("detail-info").textContent =
        `${staff.department_name} — ${staff.position} — ${staff.email} — ${staff.phone}`;

    document.getElementById("detail-qualifications").innerHTML =
        qualifications.map(q => `<li>${q.qualification_name}, ${q.institution} (${q.year_obtained})</li>`).join("");

    document.getElementById("detail-expertise").innerHTML =
        expertise.map(e => `<li>${e.expertise_area} (skill level ${e.skill_level}/5)</li>`).join("");

    document.getElementById("detail-availability").innerHTML =
        availability.map(a => `<li>${a.day}, ${a.time_slot} — ${a.availability_status}</li>`).join("");

    document.getElementById("detail-ai-analysis").innerHTML = "";  // clear AI result
    document.getElementById("staff-list-section").style.display = "none";
    document.getElementById("staff-detail-section").style.display = "block";
}

// --- SEARCH AND FILTER ---
async function searchStaffByExpertise() {
    const query = document.getElementById("search-input").value;
    const response = await fetch(`${API_BASE}/api/staff/search?expertise=${encodeURIComponent(query)}`);
    const results = await response.json();
    renderStaffRows(results);
}

async function filterStaff() {
    const department = document.getElementById("department-filter").value;
    const position = document.getElementById("position-filter").value;
    const response = await fetch(`${API_BASE}/api/staff/filter?department_id=${department}&position=${position}`);
    const results = await response.json();  
    renderStaffRows(results);
}

// --- FORM HANDLING ---
function showAddForm() {
    editingStaffId = null;
    document.getElementById("form-title").textContent = "Add New Staff";
    document.getElementById("staff-form").reset();
    
    const expertiseField = document.getElementById("form-expertise-area");
    const skillLevelField = document.getElementById("form-skill-level");
    expertiseField.disabled = false;               
    skillLevelField.disabled = false;               
    expertiseField.required = true;                  
    skillLevelField.required = true;                 
    document.getElementById("staff-list-section").style.display = "none";
    document.getElementById("staff-form-section").style.display = "block";
}

async function editStaff(staffId) {

    const [staffRes, expRes] = await Promise.all([
        fetch(`${API_BASE}/api/staff/${staffId}`),
        fetch(`${API_BASE}/api/staff/${staffId}/expertise`)   
    ]);
 
    const staff = await staffRes.json();
    const expertise = await expRes.json();            
 
    editingStaffId = staffId;
    document.getElementById("form-title").textContent = "Edit Staff";
    document.getElementById("staff-form").reset();     
    document.getElementById("form-name").value = staff.name;
    document.getElementById("form-email").value = staff.email;
    document.getElementById("form-phone").value = staff.phone;
    document.getElementById("form-department").value = staff.department_id;
    document.getElementById("form-position").value = staff.position;
    document.getElementById("form-employment-type").value = staff.employment_type;
    document.getElementById("form-status").value = staff.status;

    const expertiseField = document.getElementById("form-expertise-area");
    const skillLevelField = document.getElementById("form-skill-level");
 
    if (expertise.length > 0) {
        expertiseField.value = expertise[0].expertise_area;
        skillLevelField.value = expertise[0].skill_level;
    } else {
        expertiseField.value = "";
        skillLevelField.value = "";
    }

    expertiseField.disabled = true;
    skillLevelField.disabled = true;
    expertiseField.required = false;
    skillLevelField.required = false;
 
    document.getElementById("staff-list-section").style.display = "none";
    document.getElementById("staff-form-section").style.display = "block";
}

// --- AI ANALYSIS ---
async function generateAnalysis() {
    const button = document.getElementById("generate-analysis-btn");
    const resultDiv = document.getElementById("detail-ai-analysis");

    button.disabled = true;
    resultDiv.textContent = "Generating analysis, please wait...";

    try {
        const response = await fetch(`${API_BASE}/api/staff/${currentStaffId}/generate_analysis`, {
            method: "POST"
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `<p>${data.generated_summary}</p><p>Suitability Score: ${data.suitability_score}/10</p>`;
        } else {
            resultDiv.textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        resultDiv.textContent = "Failed to reach the AI service.";
    }

    button.disabled = false;
}

// --- AI ASSISTANT: SHARED MCP + RAG (Release 1) ---
// Model/tool output is untrusted text, so it is escaped before going into innerHTML
function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
}

function rawJsonBlock(data) {
    return `<details><summary>Raw tool result (JSON)</summary><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></details>`;
}

async function postJson(path, body) {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {})
    });
    const data = await response.json();
    return { ok: response.ok, data };
}

async function loadAiServicesStatus() {
    const note = document.getElementById("ai-services-note");
    let status = { mcp_enabled: false, rag_enabled: false };

    try {
        const response = await fetch(`${API_BASE}/api/ai-services/status`);
        status = await response.json();
    } catch (error) {
        note.textContent = "Could not reach the Staff Management backend.";
    }

    document.querySelectorAll(".mcp-btn").forEach(btn => btn.disabled = !status.mcp_enabled);
    document.querySelectorAll(".rag-btn").forEach(btn => btn.disabled = !status.rag_enabled);

    const disabled = [];
    if (!status.mcp_enabled) disabled.push("MCP");
    if (!status.rag_enabled) disabled.push("RAG");
    if (disabled.length && !note.textContent) {
        note.textContent = `${disabled.join(" and ")} integration is disabled on this server.`;
    }
}

function renderMcpProfile(result) {
    const { staff, expertise, qualifications, availability } = result.data;
    const list = (items, format) => items.length
        ? `<ul>${items.map(item => `<li>${format(item)}</li>`).join("")}</ul>`
        : `<p class="empty-state">None recorded</p>`;

    return `
        <div class="ai-meta">Tool: ${escapeHtml(result.tool)} <span class="stamp status-active">${escapeHtml(result.status)}</span></div>
        <h4>${escapeHtml(staff.name)}</h4>
        <p>${escapeHtml(staff.position)} &mdash; ${escapeHtml(staff.department_name)} &mdash; ${escapeHtml(staff.employment_type)}, ${escapeHtml(staff.status)}</p>
        <strong>Expertise</strong>
        ${list(expertise, e => `${escapeHtml(e.expertise_area)} (skill level ${escapeHtml(e.skill_level)}/5)`)}
        <strong>Qualifications</strong>
        ${list(qualifications, q => `${escapeHtml(q.qualification_name)}, ${escapeHtml(q.institution)} (${escapeHtml(q.year_obtained)})`)}
        <strong>Availability</strong>
        ${list(availability, a => `${escapeHtml(a.day)} ${escapeHtml(a.time_slot)} &mdash; ${escapeHtml(a.availability_status)}`)}
        ${rawJsonBlock(result)}
    `;
}

function renderMcpSearch(result) {
    const rows = result.data.map(person => `
        <li>${escapeHtml(person.name)} &mdash; ${escapeHtml(person.expertise_area)} (skill ${escapeHtml(person.skill_level)}/5),
            ${escapeHtml(person.position)}, ${escapeHtml(person.department_name)}</li>
    `).join("");

    return `
        <div class="ai-meta">Tool: ${escapeHtml(result.tool)} <span class="stamp status-active">${escapeHtml(result.status)}</span>
            ${escapeHtml(result.match_count)} match(es) for "${escapeHtml(result.query)}"</div>
        ${rows ? `<ul>${rows}</ul>` : `<p class="empty-state">No staff match that expertise.</p>`}
        ${rawJsonBlock(result)}
    `;
}

async function runMcpTool(path, body, render) {
    const resultDiv = document.getElementById("mcp-result");
    const buttons = document.querySelectorAll(".mcp-btn");

    buttons.forEach(btn => btn.disabled = true);
    resultDiv.textContent = "Calling MCP tool...";

    try {
        const { ok, data } = await postJson(path, body);

        if (ok) {
            resultDiv.innerHTML = render(data);
        } else {
            // Tool errors (e.g. staff not found) still carry the structured result
            const message = data.error || (data.data && data.data.error) || "Tool call failed";
            resultDiv.innerHTML = `<div class="error-state">${escapeHtml(message)}</div>${data.status ? rawJsonBlock(data) : ""}`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-state">Failed to reach the Staff Management backend.</div>`;
    }

    buttons.forEach(btn => btn.disabled = false);
}

const CONFIDENCE_STAMP = {
    High: "status-active",
    Medium: "status-proposed",
    Low: "status-on-hold",
    Insufficient: "status-on-hold"
};

function renderRagAnswer(data) {
    const stampClass = CONFIDENCE_STAMP[data.confidence_category] || "status-proposed";
    const confidence = `<span class="stamp ${stampClass}">Confidence: ${escapeHtml(data.confidence_category)}</span>`;

    if (data.insufficient_context) {
        return `
            <div class="ai-meta">${confidence}</div>
            <p class="ai-answer"><strong>Insufficient context.</strong></p>
            <p class="empty-state">No staff records relevant to this question were found, so no answer was generated.</p>
        `;
    }

    const citations = data.citations.map(c => `
        <li>${escapeHtml(c.source_id)} <span class="ai-hint">(${escapeHtml(c.feature)}, ${escapeHtml(c.authority_tier)})</span></li>
    `).join("");

    return `
        <div class="ai-meta">${confidence}</div>
        <p class="ai-answer">${escapeHtml(data.answer)}</p>
        <strong>Sources</strong>
        <ol class="ai-citations">${citations}</ol>
    `;
}

async function askRag(event) {
    event.preventDefault();
    const question = document.getElementById("rag-question").value.trim();
    const resultDiv = document.getElementById("rag-result");
    const buttons = document.querySelectorAll(".rag-btn");

    buttons.forEach(btn => btn.disabled = true);
    resultDiv.textContent = "Retrieving staff records and generating a grounded answer...";

    try {
        const { ok, data } = await postJson("/api/rag/ask", { question });
        resultDiv.innerHTML = ok
            ? renderRagAnswer(data)
            : `<div class="error-state">${escapeHtml(data.error)}</div>`;
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-state">Failed to reach the Staff Management backend.</div>`;
    }

    buttons.forEach(btn => btn.disabled = false);
}

async function refreshRag() {
    const resultDiv = document.getElementById("rag-result");
    const buttons = document.querySelectorAll(".rag-btn");

    buttons.forEach(btn => btn.disabled = true);
    resultDiv.textContent = "Rebuilding the knowledge base from current records...";

    try {
        const { ok, data } = await postJson("/api/rag/refresh");
        resultDiv.innerHTML = ok
            ? `<p>Knowledge base refreshed: ${escapeHtml(data.chunk_count)} records indexed.</p>`
            : `<div class="error-state">${escapeHtml(data.error)}</div>`;
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-state">Failed to reach the Staff Management backend.</div>`;
    }

    buttons.forEach(btn => btn.disabled = false);
}

// EVENT LISTENERS
document.getElementById("add-staff-btn").addEventListener("click", showAddForm);

document.getElementById("cancel-form-btn").addEventListener("click", function() {
    document.getElementById("staff-form-section").style.display = "none";
    document.getElementById("staff-list-section").style.display = "block";
});

document.getElementById("staff-form").addEventListener("submit", async function(event) {
    event.preventDefault();  // stops the page from reloading

    const staffData = {
        name: document.getElementById("form-name").value,
        email: document.getElementById("form-email").value,
        phone: document.getElementById("form-phone").value,
        department_id: document.getElementById("form-department").value,
        position: document.getElementById("form-position").value,
        employment_type: document.getElementById("form-employment-type").value,
        status: document.getElementById("form-status").value
    };

    if (editingStaffId === null) {
        staffData.expertise_area = document.getElementById("form-expertise-area").value;
        staffData.skill_level = parseInt(document.getElementById("form-skill-level").value);
        const response = await fetch(`${API_BASE}/api/staff`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(staffData)
        });
    }

    else {
        const response = await fetch(`${API_BASE}/api/staff/${editingStaffId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(staffData)
        });
    }

    document.getElementById("staff-form-section").style.display = "none";
    document.getElementById("staff-list-section").style.display = "block";
    loadStaffList();
});

document.getElementById("back-to-list-btn").addEventListener("click", function() {
    document.getElementById("staff-detail-section").style.display = "none";
    document.getElementById("staff-list-section").style.display = "block";
    loadStaffList();
});

document.getElementById("search-btn").addEventListener("click", searchStaffByExpertise);
document.getElementById("filter-btn").addEventListener("click", filterStaff);

document.getElementById("generate-analysis-btn").addEventListener("click", generateAnalysis);

document.getElementById("mcp-profile-form").addEventListener("submit", function(event) {
    event.preventDefault();
    const staffId = parseInt(document.getElementById("mcp-staff-id").value);
    runMcpTool("/api/mcp/staff-profile", { staff_id: staffId }, renderMcpProfile);
});

document.getElementById("mcp-search-form").addEventListener("submit", function(event) {
    event.preventDefault();
    const expertise = document.getElementById("mcp-expertise").value.trim();
    runMcpTool("/api/mcp/search-expertise", { expertise }, renderMcpSearch);
});

document.getElementById("rag-form").addEventListener("submit", askRag);
document.getElementById("rag-refresh-btn").addEventListener("click", refreshRag);

// INITIAL PAGE LOAD
loadStaffList();
loadDepartmentOptions("department-filter");
loadDepartmentOptions("form-department");
loadAiServicesStatus();