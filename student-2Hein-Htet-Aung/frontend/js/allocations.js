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

function showAllocationError(message) {
  allocationMessage.innerHTML = `
    <div class="error-state">
      ${allocationEscapeHtml(message)}
    </div>
  `;
}

function parseAllocationDetails(element) {
  const lines = element.innerHTML
    .split(/<br\s*\/?>/i)
    .map(line => {
      const temp = document.createElement("div");
      temp.innerHTML = line;
      return temp.textContent.trim();
    })
    .filter(Boolean);

  const allocation = {};

  lines.forEach(line => {
    const separatorIndex = line.indexOf(":");

    if (separatorIndex === -1) {
      return;
    }

    const key = line
      .slice(0, separatorIndex)
      .trim()
      .toLowerCase();

    const value = line
      .slice(separatorIndex + 1)
      .trim();

    if (key === "allocation id") {
      allocation.allocation_id = value;
    }

    if (key === "offer id") {
      allocation.offer_id = value;
    }

    if (key === "assigned staff member") {
      allocation.staff_display = value;
    }

    if (key === "assigned staff id") {
      allocation.assigned_staff_member =
        value === "Unassigned"
          ? null
          : Number(value);
    }

    if (key === "classroom id") {
      allocation.classroom_id = value;
    }

    if (key === "day") {
      allocation.day = value;
    }

    if (key === "date range") {
      allocation.date_range = value;
    }

    if (key === "start time") {
      allocation.start_time = value;
    }

    if (key === "end time") {
      allocation.end_time = value;
    }

    if (key === "class type") {
      allocation.class_type = value;
    }

    if (key === "expected class size") {
      allocation.expected_class_size = value;
    }

    if (key === "allocation status") {
      allocation.allocation_status = value;
    }
  });

  return allocation;
}

async function getAllocationDetails(allocationId) {
  const html = await apiRequest(
    `/teaching-allocations/${allocationId}?refresh=${Date.now()}`
  );

  const parser = new DOMParser();

  const doc = parser.parseFromString(
    html,
    "text/html"
  );

  const element = doc.querySelector("p");

  if (!element) {
    throw new Error(
      `Unable to read allocation ${allocationId}.`
    );
  }

  return parseAllocationDetails(element);
}

async function loadAllocationOptions() {
  const refresh = Date.now();

  const [offersHtml, classroomsHtml] =
    await Promise.all([
      apiRequest(
        `/subject-offers?refresh=${refresh}`
      ),
      apiRequest(
        `/classrooms?refresh=${refresh}`
      )
    ]);

  const parser = new DOMParser();

  const offersDoc =
    parser.parseFromString(
      offersHtml,
      "text/html"
    );

  const classroomsDoc =
    parser.parseFromString(
      classroomsHtml,
      "text/html"
    );

  allocationOfferInput.innerHTML = `
    <option value="">
      Select subject offer
    </option>
  `;

  offersDoc
    .querySelectorAll("li")
    .forEach(item => {
      const offerId =
        item.textContent
          .trim()
          .split(" - ")[0]
          .trim();

      const option =
        document.createElement(
          "option"
        );

      option.value = offerId;
      option.textContent = offerId;

      allocationOfferInput.appendChild(
        option
      );
    });

  allocationClassroomInput.innerHTML = `
    <option value="">
      Select classroom
    </option>
  `;

  classroomsDoc
    .querySelectorAll("li")
    .forEach(item => {
      const classroomId =
        item.textContent
          .trim()
          .split(" - ")[0]
          .trim();

      const option =
        document.createElement(
          "option"
        );

      option.value = classroomId;
      option.textContent = classroomId;

      allocationClassroomInput.appendChild(
        option
      );
    });
}

async function loadAllocations() {
  allocationsTableBody.innerHTML = "";
  allocationsEmpty.hidden = true;

  try {
    const html = await apiRequest(
      `/teaching-allocations?refresh=${Date.now()}`
    );

    const parser = new DOMParser();

    const doc = parser.parseFromString(
      html,
      "text/html"
    );

    const items =
      doc.querySelectorAll("li");

    items.forEach(item => {
      const parts =
        item.textContent
          .trim()
          .split(" - ")
          .map(
            part => part.trim()
          );

      if (parts.length !== 7) {
        return;
      }

      const allocationId =
        parts[0];

      const offerId =
        parts[1];

      const staff =
        parts[2];

      let staffName =
        "Unassigned";

      let staffId =
        "—";

      if (staff !== "Unassigned") {
        const match = staff.match(
          /^(.*)\s+\((\d+)\)$/
        );

        if (match) {
          staffName =
            match[1].trim();

          staffId =
            match[2];
        } else {
          staffName = staff;
        }
      }

      const classroomId =
        parts[3];

      const schedule =
        parts[4];

      const classType =
        parts[5];

      const status =
        parts[6];

      const scheduleMatch =
        schedule.match(
          /^([A-Z]{3})\s+(\d{2}:\d{2})-(\d{2}:\d{2})$/
        );

      const day =
        scheduleMatch
          ? scheduleMatch[1]
          : "";

      const startTime =
        scheduleMatch
          ? scheduleMatch[2]
          : "";

      const endTime =
        scheduleMatch
          ? scheduleMatch[3]
          : "";

      const row =
        document.createElement("tr");

      row.dataset.allocationId =
        allocationId;

      row.innerHTML = `
        <td>
          ${allocationEscapeHtml(
            allocationId
          )}
        </td>

        <td>
          ${allocationEscapeHtml(
            offerId
          )}
        </td>

        <td>
          ${allocationEscapeHtml(
            staffName
          )}
        </td>

        <td>
          ${allocationEscapeHtml(
            staffId
          )}
        </td>

        <td>
          ${allocationEscapeHtml(
            classroomId
          )}
        </td>

        <td>
          ${allocationEscapeHtml(
            day
          )}
        </td>

        <td>
          View on Edit
        </td>

        <td>
          ${allocationEscapeHtml(
            startTime
          )}
          -
          ${allocationEscapeHtml(
            endTime
          )}
        </td>

        <td>
          ${allocationEscapeHtml(
            classType
          )}
        </td>

        <td>
          View on Edit
        </td>

        <td>
          ${allocationEscapeHtml(
            status
          )}
        </td>

        <td>
          <button
            class="btn secondary"
            type="button"
            data-action="edit"
            data-allocation-id="${allocationEscapeHtml(
              allocationId
            )}"
          >
            Edit
          </button>

          <button
            class="btn secondary"
            type="button"
            data-action="delete"
            data-allocation-id="${allocationEscapeHtml(
              allocationId
            )}"
          >
            Delete
          </button>
        </td>
      `;

      allocationsTableBody.appendChild(
        row
      );
    });

    allocationsEmpty.hidden =
      allocationsTableBody.children
        .length > 0;

  } catch (error) {
    allocationsEmpty.hidden = false;

    showAllocationError(
      error.message
    );
  }
}

function getAllocationPayload() {
  const staffValue =
    allocationStaffInput.value.trim();

  return {
    offer_id:
      allocationOfferInput.value,

    assigned_staff_member:
      staffValue === ""
        ? null
        : Number(staffValue),

    classroom_id:
      allocationClassroomInput.value,

    day:
      allocationDayInput.value,

    date_range:
      allocationDateRangeInput
        .value
        .trim(),

    start_time:
      allocationStartTimeInput.value,

    end_time:
      allocationEndTimeInput.value,

    class_type:
      allocationClassTypeInput.value,

    expected_class_size:
      Number(
        allocationClassSizeInput.value
      ),

    allocation_status:
      allocationStatusInput.value
  };
}

async function saveAllocation(event) {
  event.preventDefault();

  allocationMessage.innerHTML = "";

  const data =
    getAllocationPayload();

  try {
    let result;

    if (editingAllocationId) {
      result = await apiRequest(
        `/teaching-allocations/${editingAllocationId}`,
        {
          method: "PUT",
          body: JSON.stringify(data)
        }
      );
    } else {
      result = await apiRequest(
        "/teaching-allocations",
        {
          method: "POST",
          body: JSON.stringify(data)
        }
      );
    }

    resetAllocationForm();

    await loadAllocations();

    if (
      typeof result === "object" &&
      result !== null &&
      result.message
    ) {
      allocationMessage.innerHTML = `
        <p>
          ${allocationEscapeHtml(
            result.message
          )}
        </p>
      `;
    } else if (result) {
      allocationMessage.innerHTML =
        result;
    }

  } catch (error) {
    showAllocationError(
      error.message
    );
  }
}

async function startEditingAllocation(
  allocationId
) {
  allocationMessage.innerHTML = "";

  try {
    const allocation =
      await getAllocationDetails(
        allocationId
      );

    editingAllocationId =
      allocation.allocation_id;

    allocationOfferInput.value =
      allocation.offer_id || "";

    allocationStaffInput.value =
      allocation
        .assigned_staff_member ?? "";

    allocationClassroomInput.value =
      allocation.classroom_id || "";

    allocationDayInput.value =
      allocation.day || "";

    allocationDateRangeInput.value =
      allocation.date_range || "";

    allocationStartTimeInput.value =
      allocation.start_time || "";

    allocationEndTimeInput.value =
      allocation.end_time || "";

    allocationClassTypeInput.value =
      allocation.class_type || "";

    allocationClassSizeInput.value =
      allocation
        .expected_class_size || "";

    allocationStatusInput.value =
      allocation
        .allocation_status ||
      "PENDING";

    allocationForm.querySelector(
      'button[type="submit"]'
    ).textContent =
      "Update Teaching Allocation";

    allocationCancelButton.hidden =
      false;

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });

  } catch (error) {
    showAllocationError(
      error.message
    );
  }
}

async function deleteAllocation(
  allocationId
) {
  const confirmed =
    window.confirm(
      `Delete teaching allocation ${allocationId}?`
    );

  if (!confirmed) {
    return;
  }

  allocationMessage.innerHTML = "";

  try {
    const result =
      await apiRequest(
        `/teaching-allocations/${allocationId}`,
        {
          method: "DELETE"
        }
      );

    const deletedRow =
      allocationsTableBody.querySelector(
        `tr[data-allocation-id="${CSS.escape(
          String(allocationId)
        )}"]`
      );

    if (deletedRow) {
      deletedRow.remove();
    }

    if (
      String(editingAllocationId) ===
      String(allocationId)
    ) {
      resetAllocationForm();
    }

    allocationsEmpty.hidden =
      allocationsTableBody.children
        .length > 0;

    await loadAllocations();

    if (
      typeof result === "object" &&
      result !== null &&
      result.message
    ) {
      allocationMessage.innerHTML = `
        <p>
          ${allocationEscapeHtml(
            result.message
          )}
        </p>
      `;
    } else if (result) {
      allocationMessage.innerHTML =
        result;
    }

  } catch (error) {
    showAllocationError(
      error.message
    );
  }
}

function resetAllocationForm() {
  allocationForm.reset();

  editingAllocationId = null;

  allocationStatusInput.value =
    "PENDING";

  allocationForm.querySelector(
    'button[type="submit"]'
  ).textContent =
    "Add Teaching Allocation";

  allocationCancelButton.hidden =
    true;
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
  async event => {
    const button =
      event.target.closest("button");

    if (!button) {
      return;
    }

    const allocationId =
      button.dataset.allocationId;

    if (!allocationId) {
      return;
    }

    if (
      button.dataset.action ===
      "edit"
    ) {
      await startEditingAllocation(
        allocationId
      );
    }

    if (
      button.dataset.action ===
      "delete"
    ) {
      await deleteAllocation(
        allocationId
      );
    }
  }
);

loadAllocationOptions();
loadAllocations();