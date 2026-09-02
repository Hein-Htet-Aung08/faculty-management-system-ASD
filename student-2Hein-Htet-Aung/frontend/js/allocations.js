const allocationForm = document.getElementById("allocation-form");
const allocationOfferInput = document.getElementById("allocation-offer-id");
const allocationStaffInput = document.getElementById("allocation-staff-id");
const allocationClassroomInput = document.getElementById("allocation-classroom-id");
const allocationDayInput = document.getElementById("allocation-day");
const allocationDateRangeInput = document.getElementById("allocation-date-range");
const allocationStartTimeInput = document.getElementById("allocation-start-time");
const allocationEndTimeInput = document.getElementById("allocation-end-time");
const allocationClassTypeInput = document.getElementById("allocation-class-type");
const allocationClassSizeInput = document.getElementById("allocation-class-size");
const allocationStatusInput = document.getElementById("allocation-status");
const allocationCancelButton = document.getElementById("allocation-cancel-button");
const allocationMessage = document.getElementById("allocation-message");
const allocationsTableBody = document.getElementById("allocations-table-body");
const allocationsEmpty = document.getElementById("allocations-empty");

let editingAllocationId = null;

function allocationEscapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadAllocationOptions() {
  const [offersHtml, classroomsHtml] = await Promise.all([
    apiRequest("/subject-offers"),
    apiRequest("/classrooms")
  ]);

  const parser = new DOMParser();

  const offersDoc = parser.parseFromString(
    offersHtml,
    "text/html"
  );

  const classroomsDoc = parser.parseFromString(
    classroomsHtml,
    "text/html"
  );

  allocationOfferInput.innerHTML =
    `<option value="">Select subject offer</option>`;

  offersDoc.querySelectorAll("li").forEach(item => {
    const text = item.textContent.trim();
    const offerId = text.split(" - ")[0].trim();

    const option = document.createElement("option");
    option.value = offerId;
    option.textContent = offerId;

    allocationOfferInput.appendChild(option);
  });

  allocationClassroomInput.innerHTML =
    `<option value="">Select classroom</option>`;

  classroomsDoc.querySelectorAll("li").forEach(item => {
    const text = item.textContent.trim();
    const classroomId = text.split(" - ")[0].trim();

    const option = document.createElement("option");
    option.value = classroomId;
    option.textContent = classroomId;

    allocationClassroomInput.appendChild(option);
  });
}

function parseAllocationItem(text) {
  const parts = text.split(" - ").map(part => part.trim());

  if (parts.length < 8) {
    return null;
  }

  return {
    raw: text,
    parts
  };
}

async function loadAllocations() {
  try {
    const html = await apiRequest("/teaching-allocations");

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const items = doc.querySelectorAll("li");

    allocationsTableBody.innerHTML = "";

    if (items.length === 0) {
      allocationsEmpty.hidden = false;
      return;
    }

    allocationsEmpty.hidden = true;

    items.forEach(item => {
      const allocation = parseAllocationItem(
        item.textContent.trim()
      );

      if (!allocation) {
        return;
      }

      const parts = allocation.parts;
      const row = document.createElement("tr");

      row.dataset.rawAllocation = allocation.raw;

      row.innerHTML = `
        <td>${allocationEscapeHtml(parts[0])}</td>
        <td>${allocationEscapeHtml(parts[1])}</td>
        <td>${allocationEscapeHtml(parts[2])}</td>
        <td>${allocationEscapeHtml(parts[3])}</td>
        <td>${allocationEscapeHtml(parts[4])}</td>
        <td>${allocationEscapeHtml(parts[5])}</td>
        <td>${allocationEscapeHtml(parts[6])}</td>
        <td>${allocationEscapeHtml(parts[7])}</td>
        <td>${allocationEscapeHtml(parts[8] || "")}</td>
        <td>${allocationEscapeHtml(parts[9] || "")}</td>
        <td>
          <button
            class="btn secondary"
            type="button"
            data-action="edit"
          >
            Edit
          </button>

          <button
            class="btn secondary"
            type="button"
            data-action="delete"
            data-allocation-id="${allocationEscapeHtml(parts[0])}"
          >
            Delete
          </button>
        </td>
      `;

      allocationsTableBody.appendChild(row);
    });
  } catch (error) {
    allocationMessage.innerHTML = `
      <div class="error-state">
        ${allocationEscapeHtml(error.message)}
      </div>
    `;
  }
}

function getAllocationPayload() {
  const staffValue = allocationStaffInput.value.trim();

  return {
    offer_id: allocationOfferInput.value,
    assigned_staff_member:
      staffValue === "" ? null : Number(staffValue),
    classroom_id: allocationClassroomInput.value,
    day: allocationDayInput.value,
    date_range: allocationDateRangeInput.value.trim(),
    start_time: allocationStartTimeInput.value,
    end_time: allocationEndTimeInput.value,
    class_type: allocationClassTypeInput.value,
    expected_class_size: Number(
      allocationClassSizeInput.value
    ),
    allocation_status: allocationStatusInput.value
  };
}

async function saveAllocation(event) {
  event.preventDefault();

  const data = getAllocationPayload();

  try {
    if (editingAllocationId) {
      allocationMessage.innerHTML = await apiRequest(
        `/teaching-allocations/${editingAllocationId}`,
        {
          method: "PUT",
          body: JSON.stringify(data)
        }
      );
    } else {
      allocationMessage.innerHTML = await apiRequest(
        "/teaching-allocations",
        {
          method: "POST",
          body: JSON.stringify(data)
        }
      );
    }

    resetAllocationForm();
    await loadAllocations();
  } catch (error) {
    allocationMessage.innerHTML = `
      <div class="error-state">
        ${allocationEscapeHtml(error.message)}
      </div>
    `;
  }
}

async function startEditingAllocation(allocationId) {
  try {
    const html = await apiRequest(
      `/teaching-allocations/${allocationId}`
    );

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const item = doc.querySelector("li");

    if (!item) {
      throw new Error(
        "Unable to read teaching allocation."
      );
    }

    const parts = item.textContent
      .trim()
      .split(" - ")
      .map(part => part.trim());

    editingAllocationId = allocationId;

    allocationOfferInput.value = parts[1] || "";
    allocationStaffInput.value = parts[2] || "";
    allocationClassroomInput.value = parts[3] || "";
    allocationDayInput.value = parts[4] || "";
    allocationDateRangeInput.value = parts[5] || "";

    const timeParts = (parts[6] || "").split(" to ");

    allocationStartTimeInput.value =
      timeParts[0]?.trim() || "";

    allocationEndTimeInput.value =
      timeParts[1]?.trim() || "";

    allocationClassTypeInput.value =
      parts[7] || "";

    allocationClassSizeInput.value =
      parts[8] || "";

    allocationStatusInput.value =
      parts[9] || "PENDING";

    allocationForm.querySelector(
      'button[type="submit"]'
    ).textContent = "Update Teaching Allocation";

    allocationCancelButton.hidden = false;
  } catch (error) {
    allocationMessage.innerHTML = `
      <div class="error-state">
        ${allocationEscapeHtml(error.message)}
      </div>
    `;
  }
}

async function deleteAllocation(allocationId) {
  const confirmed = window.confirm(
    `Delete teaching allocation ${allocationId}?`
  );

  if (!confirmed) {
    return;
  }

  try {
    allocationMessage.innerHTML = await apiRequest(
      `/teaching-allocations/${allocationId}`,
      {
        method: "DELETE"
      }
    );

    if (
      String(editingAllocationId) ===
      String(allocationId)
    ) {
      resetAllocationForm();
    }

    await loadAllocations();
  } catch (error) {
    allocationMessage.innerHTML = `
      <div class="error-state">
        ${allocationEscapeHtml(error.message)}
      </div>
    `;
  }
}

function resetAllocationForm() {
  allocationForm.reset();

  editingAllocationId = null;

  allocationStatusInput.value = "PENDING";

  allocationForm.querySelector(
    'button[type="submit"]'
  ).textContent = "Add Teaching Allocation";

  allocationCancelButton.hidden = true;
}

allocationForm.addEventListener(
  "submit",
  saveAllocation
);

allocationCancelButton.addEventListener(
  "click",
  resetAllocationForm
);

allocationsTableBody.addEventListener(
  "click",
  event => {
    const button = event.target.closest("button");

    if (!button) {
      return;
    }

    const row = button.closest("tr");
    const allocationId =
      row.querySelector("td").textContent.trim();

    if (button.dataset.action === "edit") {
      startEditingAllocation(allocationId);
    }

    if (button.dataset.action === "delete") {
      deleteAllocation(allocationId);
    }
  }
);

Promise.all([
  loadAllocationOptions(),
  loadAllocations()
]).catch(error => {
  allocationMessage.innerHTML = `
    <div class="error-state">
      ${allocationEscapeHtml(error.message)}
    </div>
  `;
});