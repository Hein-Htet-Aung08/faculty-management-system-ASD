const classroomForm = document.getElementById("classroom-form");
const classroomIdInput = document.getElementById("classroom-id");
const classroomBuildingInput = document.getElementById("classroom-building");
const classroomFloorInput = document.getElementById("classroom-floor");
const classroomRoomNumberInput = document.getElementById("classroom-room-number");
const classroomCapacityInput = document.getElementById("classroom-capacity");
const classroomRoomTypeInput = document.getElementById("classroom-room-type");
const facilitySearchInput = document.getElementById("facility-search");
const facilityTags = document.getElementById("facility-tags");
const facilitySuggestions = document.getElementById("facility-suggestions");
const classroomCancelButton = document.getElementById("classroom-cancel-button");
const classroomMessage = document.getElementById("classroom-message");
const classroomsTableBody = document.getElementById("classrooms-table-body");
const classroomsEmpty = document.getElementById("classrooms-empty");

let editingClassroomId = null;
let selectedFacilities = [];

const facilityOptions = [
  "Air Conditioning",
  "AV System",
  "Computers",
  "Document Camera",
  "Dual Monitors",
  "HDMI",
  "Microphone",
  "Projector",
  "Recording Equipment",
  "Smart Board",
  "Speakers",
  "Video Conferencing",
  "Whiteboard",
  "WiFi"
];

function classroomEscapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function updateClassroomId() {
  const building = classroomBuildingInput.value.trim().toUpperCase();
  const floor = classroomFloorInput.value.trim();
  const roomNumber = classroomRoomNumberInput.value.trim();

  if (!building || !floor || !roomNumber) {
    classroomIdInput.value = "";
    return;
  }

  classroomIdInput.value =
    `${building}.${floor}.${roomNumber}`;
}

function renderFacilityTags() {
  facilityTags.innerHTML = "";

  selectedFacilities.forEach(facility => {
    const tag = document.createElement("span");

    tag.innerHTML = `
      ${classroomEscapeHtml(facility)}
      <button
        type="button"
        data-facility="${classroomEscapeHtml(facility)}"
        aria-label="Remove ${classroomEscapeHtml(facility)}"
      >
        ×
      </button>
    `;

    facilityTags.appendChild(tag);
  });
}

function addFacility(value) {
  const facility = value.trim();

  if (!facility) {
    return;
  }

  const exists = selectedFacilities.some(
    current => current.toLowerCase() === facility.toLowerCase()
  );

  if (!exists) {
    selectedFacilities.push(facility);
  }

  facilitySearchInput.value = "";

  renderFacilityTags();
  renderFacilitySuggestions();
}

function removeFacility(value) {
  selectedFacilities = selectedFacilities.filter(
    facility => facility !== value
  );

  renderFacilityTags();
  renderFacilitySuggestions();
}

function renderFacilitySuggestions() {
  facilitySuggestions.innerHTML = "";

  const search = facilitySearchInput.value.trim();

  if (!search) {
    return;
  }

  const lowerSearch = search.toLowerCase();

  const matches = facilityOptions.filter(option => {
    const alreadySelected = selectedFacilities.some(
      facility => facility.toLowerCase() === option.toLowerCase()
    );

    return (
      option.toLowerCase().includes(lowerSearch) &&
      !alreadySelected
    );
  });

  matches.forEach(facility => {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = facility;
    button.dataset.facility = facility;

    facilitySuggestions.appendChild(button);
  });

  const exactMatch = facilityOptions.some(
    option => option.toLowerCase() === lowerSearch
  );

  const alreadySelected = selectedFacilities.some(
    option => option.toLowerCase() === lowerSearch
  );

  if (!exactMatch && !alreadySelected) {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = `Add "${search}"`;
    button.dataset.facility = search;

    facilitySuggestions.appendChild(button);
  }
}

function parseClassroomItem(text) {
  const parts = text.split(" - ").map(part => part.trim());

  if (parts.length < 4) {
    return null;
  }

  const classroomId = parts[0];
  const roomType = parts[1];
  const capacity = parts[2]
    .replace("Capacity:", "")
    .trim();
  const facilities = parts.slice(3).join(" - ").trim();

  const idParts = classroomId.split(".");

  if (idParts.length < 3) {
    return null;
  }

  const building = idParts[0];
  const floor = idParts[1];
  const roomNumber = idParts.slice(2).join(".");

  return {
    classroomId,
    building,
    floor,
    roomNumber,
    capacity,
    roomType,
    facilities
  };
}

async function loadClassrooms() {
  try {
    const html = await apiRequest("/classrooms");

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const items = doc.querySelectorAll("li");

    classroomsTableBody.innerHTML = "";

    if (items.length === 0) {
      classroomsEmpty.hidden = false;
      return;
    }

    classroomsEmpty.hidden = true;

    items.forEach(item => {
      const classroom = parseClassroomItem(
        item.textContent.trim()
      );

      if (!classroom) {
        return;
      }

      const row = document.createElement("tr");

      row.dataset.classroom = JSON.stringify(classroom);

      row.innerHTML = `
        <td>${classroomEscapeHtml(classroom.classroomId)}</td>
        <td>${classroomEscapeHtml(classroom.building)}</td>
        <td>${classroomEscapeHtml(classroom.floor)}</td>
        <td>${classroomEscapeHtml(classroom.roomNumber)}</td>
        <td>${classroomEscapeHtml(classroom.capacity)}</td>
        <td>${classroomEscapeHtml(classroom.roomType)}</td>
        <td>${classroomEscapeHtml(classroom.facilities)}</td>
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
            data-classroom-id="${classroomEscapeHtml(classroom.classroomId)}"
          >
            Delete
          </button>
        </td>
      `;

      classroomsTableBody.appendChild(row);
    });
  } catch (error) {
    classroomMessage.innerHTML = `
      <div class="error-state">
        ${classroomEscapeHtml(error.message)}
      </div>
    `;
  }
}

async function saveClassroom(event) {
  event.preventDefault();

  if (selectedFacilities.length === 0) {
    classroomMessage.innerHTML = `
      <div class="error-state">
        Add at least one facility.
      </div>
    `;
    return;
  }

  updateClassroomId();

  const data = {
    classroom_id: classroomIdInput.value,
    building: classroomBuildingInput.value.trim().toUpperCase(),
    floor: classroomFloorInput.value.trim(),
    room_number: classroomRoomNumberInput.value.trim(),
    capacity: Number(classroomCapacityInput.value),
    room_type: classroomRoomTypeInput.value.trim(),
    facilities: selectedFacilities.join(",")
  };

  try {
    if (editingClassroomId) {
      classroomMessage.innerHTML = await apiRequest(
        `/classrooms/${encodeURIComponent(editingClassroomId)}`,
        {
          method: "PUT",
          body: JSON.stringify(data)
        }
      );
    } else {
      classroomMessage.innerHTML = await apiRequest(
        "/classrooms",
        {
          method: "POST",
          body: JSON.stringify(data)
        }
      );
    }

    resetClassroomForm();
    await loadClassrooms();
  } catch (error) {
    classroomMessage.innerHTML = `
      <div class="error-state">
        ${classroomEscapeHtml(error.message)}
      </div>
    `;
  }
}

function startEditingClassroom(row) {
  const classroom = JSON.parse(row.dataset.classroom);

  editingClassroomId = classroom.classroomId;

  classroomBuildingInput.value = classroom.building;
  classroomFloorInput.value = classroom.floor;
  classroomRoomNumberInput.value = classroom.roomNumber;
  classroomCapacityInput.value = classroom.capacity;
  classroomRoomTypeInput.value = classroom.roomType;

  selectedFacilities = classroom.facilities
    .split(",")
    .map(value => value.trim())
    .filter(Boolean);

  updateClassroomId();
  renderFacilityTags();

  classroomForm.querySelector('button[type="submit"]').textContent =
    "Update Classroom";

  classroomCancelButton.hidden = false;
}

async function deleteClassroom(classroomId) {
  const confirmed = window.confirm(
    `Delete classroom ${classroomId}?`
  );

  if (!confirmed) {
    return;
  }

  try {
    classroomMessage.innerHTML = await apiRequest(
      `/classrooms/${encodeURIComponent(classroomId)}`,
      {
        method: "DELETE"
      }
    );

    if (editingClassroomId === classroomId) {
      resetClassroomForm();
    }

    await loadClassrooms();
  } catch (error) {
    classroomMessage.innerHTML = `
      <div class="error-state">
        ${classroomEscapeHtml(error.message)}
      </div>
    `;
  }
}

function resetClassroomForm() {
  classroomForm.reset();

  editingClassroomId = null;
  selectedFacilities = [];

  classroomIdInput.value = "";

  renderFacilityTags();
  renderFacilitySuggestions();

  classroomForm.querySelector('button[type="submit"]').textContent =
    "Add Classroom";

  classroomCancelButton.hidden = true;
}

classroomBuildingInput.addEventListener(
  "input",
  updateClassroomId
);

classroomFloorInput.addEventListener(
  "input",
  updateClassroomId
);

classroomRoomNumberInput.addEventListener(
  "input",
  updateClassroomId
);

facilitySearchInput.addEventListener(
  "input",
  renderFacilitySuggestions
);

facilitySearchInput.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();

    const value = facilitySearchInput.value.trim();

    if (value) {
      addFacility(value);
    }
  }

  if (
    event.key === "Backspace" &&
    facilitySearchInput.value === "" &&
    selectedFacilities.length > 0
  ) {
    selectedFacilities.pop();
    renderFacilityTags();
  }
});

facilitySuggestions.addEventListener("click", event => {
  const button = event.target.closest("button");

  if (!button) {
    return;
  }

  addFacility(button.dataset.facility);
});

facilityTags.addEventListener("click", event => {
  const button = event.target.closest("button");

  if (!button) {
    return;
  }

  removeFacility(button.dataset.facility);
});

classroomForm.addEventListener(
  "submit",
  saveClassroom
);

classroomCancelButton.addEventListener(
  "click",
  resetClassroomForm
);

classroomsTableBody.addEventListener("click", event => {
  const button = event.target.closest("button");

  if (!button) {
    return;
  }

  const action = button.dataset.action;
  const row = button.closest("tr");

  if (action === "edit") {
    startEditingClassroom(row);
  }

  if (action === "delete") {
    deleteClassroom(button.dataset.classroomId);
  }
});

loadClassrooms();