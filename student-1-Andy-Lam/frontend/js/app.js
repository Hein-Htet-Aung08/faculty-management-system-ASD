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
                <button onclick="viewStaffDetail(${person.staff_id})">View</button>
                <button onclick="editStaff(${person.staff_id})">Edit</button>
                <button onclick="deleteStaff(${person.staff_id})">Delete</button>
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

// INITIAL PAGE LOAD
loadStaffList();  
loadDepartmentOptions("department-filter");
loadDepartmentOptions("form-department");