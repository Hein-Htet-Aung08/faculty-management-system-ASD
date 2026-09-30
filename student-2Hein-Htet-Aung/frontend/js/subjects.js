const subjectForm =
  document.getElementById("subject-form");

const subjectCodeInput =
  document.getElementById("subject-code");

const subjectNameInput =
  document.getElementById("subject-name");

const expertiseSearchInput =
  document.getElementById("expertise-search");

const expertiseTags =
  document.getElementById("expertise-tags");

const expertiseSuggestions =
  document.getElementById(
    "expertise-suggestions"
  );

const subjectCancelButton =
  document.getElementById(
    "subject-cancel-button"
  );

const subjectMessage =
  document.getElementById(
    "subject-message"
  );

const subjectsTableBody =
  document.getElementById(
    "subjects-table-body"
  );

const subjectsEmpty =
  document.getElementById(
    "subjects-empty"
  );


let editingSubjectCode = null;
let selectedExpertise = [];


const expertiseOptions = [
  "Agentic AI",
  "Algorithms",
  "Architecture",
  "Cloud Computing",
  "Computation Theory",
  "Cybersecurity",
  "Data Engineering",
  "Databases",
  "DevOps",
  "Frontend Development",
  "HTTP",
  "Infrastructure",
  "Machine Learning",
  "Networking",
  "Programming",
  "Security",
  "Software Architecture",
  "Software Development",
  "Software Engineering",
  "SQL",
  "UI Design",
  "Web Development"
];


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function showSubjectError(message) {
  subjectMessage.innerHTML = `
    <div class="error-state">
      ${escapeHtml(message)}
    </div>
  `;
}


function validateSubjectForm() {
  const errors = [];

  const subjectCode =
    subjectCodeInput.value.trim();

  const subjectName =
    subjectNameInput.value.trim();

  if (!subjectCode) {
    errors.push(
      "Subject code is required."
    );
  } else if (
    !/^\d{5}$/.test(subjectCode)
  ) {
    errors.push(
      "Subject code must contain exactly 5 digits."
    );
  }

  if (!subjectName) {
    errors.push(
      "Subject name is required."
    );
  }

  if (
    selectedExpertise.length === 0
  ) {
    errors.push(
      "Add at least one required expertise."
    );
  }

  const invalidExpertise =
    selectedExpertise.some(
      expertise =>
        !expertise.trim() ||
        expertise.includes(",")
    );

  if (invalidExpertise) {
    errors.push(
      "Expertise entries cannot be blank or contain commas."
    );
  }

  return errors;
}


function renderExpertiseTags() {
  expertiseTags.innerHTML = "";

  selectedExpertise.forEach(
    expertise => {
      const tag =
        document.createElement("span");

      tag.innerHTML = `
        ${escapeHtml(expertise)}
        <button
          type="button"
          data-expertise="${escapeHtml(
            expertise
          )}"
          aria-label="Remove ${escapeHtml(
            expertise
          )}"
        >
          ×
        </button>
      `;

      expertiseTags.appendChild(tag);
    }
  );
}


function addExpertise(value) {
  const expertise = value.trim();

  if (!expertise) {
    return;
  }

  if (expertise.includes(",")) {
    showSubjectError(
      "Add expertise items separately. Do not use commas inside an expertise."
    );

    return;
  }

  const alreadySelected =
    selectedExpertise.some(
      item =>
        item.toLowerCase() ===
        expertise.toLowerCase()
    );

  if (alreadySelected) {
    expertiseSearchInput.value = "";

    renderExpertiseSuggestions();

    return;
  }

  selectedExpertise.push(expertise);

  expertiseSearchInput.value = "";

  subjectMessage.innerHTML = "";

  renderExpertiseTags();
  renderExpertiseSuggestions();
}


function removeExpertise(value) {
  selectedExpertise =
    selectedExpertise.filter(
      expertise =>
        expertise !== value
    );

  renderExpertiseTags();
  renderExpertiseSuggestions();
}


function getMatchingExpertise() {
  const search =
    expertiseSearchInput.value
      .trim()
      .toLowerCase();

  if (!search) {
    return [];
  }

  return expertiseOptions.filter(
    option => {
      const matchesSearch =
        option
          .toLowerCase()
          .includes(search);

      const alreadySelected =
        selectedExpertise.some(
          expertise =>
            expertise.toLowerCase() ===
            option.toLowerCase()
        );

      return (
        matchesSearch &&
        !alreadySelected
      );
    }
  );
}


function renderExpertiseSuggestions() {
  expertiseSuggestions.innerHTML = "";

  const searchValue =
    expertiseSearchInput.value.trim();

  if (!searchValue) {
    return;
  }

  const matches =
    getMatchingExpertise();

  matches.forEach(expertise => {
    const button =
      document.createElement("button");

    button.type = "button";
    button.textContent = expertise;

    button.dataset.expertise =
      expertise;

    expertiseSuggestions.appendChild(
      button
    );
  });

  const exactMatchExists =
    expertiseOptions.some(
      option =>
        option.toLowerCase() ===
        searchValue.toLowerCase()
    );

  const selectedMatchExists =
    selectedExpertise.some(
      option =>
        option.toLowerCase() ===
        searchValue.toLowerCase()
    );

  if (
    !exactMatchExists &&
    !selectedMatchExists &&
    !searchValue.includes(",")
  ) {
    const customButton =
      document.createElement("button");

    customButton.type = "button";

    customButton.textContent =
      `Add "${searchValue}"`;

    customButton.dataset.expertise =
      searchValue;

    expertiseSuggestions.appendChild(
      customButton
    );
  }
}


async function loadSubjects() {
  try {
    const html =
      await apiRequest("/subjects");

    const parser =
      new DOMParser();

    const doc =
      parser.parseFromString(
        html,
        "text/html"
      );

    const items =
      doc.querySelectorAll("li");

    subjectsTableBody.innerHTML = "";

    if (items.length === 0) {
      subjectsEmpty.hidden = false;
      return;
    }

    subjectsEmpty.hidden = true;

    items.forEach(item => {
      const text =
        item.textContent.trim();

      const parts =
        text.split(" - ");

      if (parts.length < 3) {
        return;
      }

      const subjectCode =
        parts[0].trim();

      const name =
        parts[1].trim();

      const requiredExpertise =
        parts
          .slice(2)
          .join(" - ")
          .trim();

      const row =
        document.createElement("tr");

      row.innerHTML = `
        <td>
          ${escapeHtml(subjectCode)}
        </td>

        <td>
          ${escapeHtml(name)}
        </td>

        <td>
          ${escapeHtml(
            requiredExpertise
          )}
        </td>

        <td>
          <button
            class="btn secondary"
            type="button"
            data-action="edit"
            data-code="${escapeHtml(
              subjectCode
            )}"
          >
            Edit
          </button>

          <button
            class="btn secondary"
            type="button"
            data-action="delete"
            data-code="${escapeHtml(
              subjectCode
            )}"
          >
            Delete
          </button>
        </td>
      `;

      subjectsTableBody.appendChild(
        row
      );
    });
  } catch (error) {
    showSubjectError(
      error.message
    );
  }
}


async function saveSubject(event) {
  event.preventDefault();

  subjectMessage.innerHTML = "";

  const validationErrors =
    validateSubjectForm();

  if (
    validationErrors.length > 0
  ) {
    showSubjectError(
      validationErrors.join(" ")
    );

    return;
  }

  const data = {
    subject_code:
      subjectCodeInput.value.trim(),

    name:
      subjectNameInput.value.trim(),

    required_expertise:
      selectedExpertise.join(",")
  };

  try {
    if (editingSubjectCode) {
      subjectMessage.innerHTML =
        await apiRequest(
          `/subjects/${encodeURIComponent(
            editingSubjectCode
          )}`,
          {
            method: "PUT",
            body: JSON.stringify(data)
          }
        );
    } else {
      subjectMessage.innerHTML =
        await apiRequest(
          "/subjects",
          {
            method: "POST",
            body: JSON.stringify(data)
          }
        );
    }

    resetSubjectForm();

    await loadSubjects();

  } catch (error) {
    showSubjectError(
      error.message
    );
  }
}


function startEditingSubject(row) {
  const cells =
    row.querySelectorAll("td");

  editingSubjectCode =
    cells[0].textContent.trim();

  subjectCodeInput.value =
    editingSubjectCode;

  subjectCodeInput.readOnly = true;

  subjectNameInput.value =
    cells[1].textContent.trim();

  selectedExpertise =
    cells[2].textContent
      .split(",")
      .map(
        value =>
          value.trim()
      )
      .filter(Boolean);

  subjectMessage.innerHTML = "";

  expertiseSearchInput.value = "";

  renderExpertiseTags();
  renderExpertiseSuggestions();

  subjectForm.querySelector(
    'button[type="submit"]'
  ).textContent =
    "Update Subject";

  subjectCancelButton.hidden = false;

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
}


async function deleteSubject(
  subjectCode
) {
  const confirmed =
    window.confirm(
      `Delete subject ${subjectCode}?`
    );

  if (!confirmed) {
    return;
  }

  subjectMessage.innerHTML = "";

  try {
    subjectMessage.innerHTML =
      await apiRequest(
        `/subjects/${encodeURIComponent(
          subjectCode
        )}`,
        {
          method: "DELETE"
        }
      );

    if (
      editingSubjectCode ===
      subjectCode
    ) {
      resetSubjectForm();
    }

    await loadSubjects();

  } catch (error) {
    showSubjectError(
      error.message
    );
  }
}


function resetSubjectForm() {
  subjectForm.reset();

  editingSubjectCode = null;

  selectedExpertise = [];

  subjectCodeInput.readOnly = false;

  subjectMessage.innerHTML = "";

  renderExpertiseTags();
  renderExpertiseSuggestions();

  subjectForm.querySelector(
    'button[type="submit"]'
  ).textContent =
    "Add Subject";

  subjectCancelButton.hidden = true;
}


subjectForm.addEventListener(
  "submit",
  saveSubject
);


subjectCancelButton.addEventListener(
  "click",
  resetSubjectForm
);


subjectCodeInput.addEventListener(
  "input",
  () => {
    if (subjectCodeInput.readOnly) {
      return;
    }

    subjectCodeInput.value =
      subjectCodeInput.value
        .replace(/\D/g, "")
        .slice(0, 5);
  }
);


expertiseSearchInput.addEventListener(
  "input",
  renderExpertiseSuggestions
);


expertiseSearchInput.addEventListener(
  "keydown",
  event => {
    if (event.key === "Enter") {
      event.preventDefault();

      const value =
        expertiseSearchInput.value
          .trim();

      if (value) {
        addExpertise(value);
      }
    }

    if (
      event.key === "Backspace" &&
      expertiseSearchInput.value === "" &&
      selectedExpertise.length > 0
    ) {
      selectedExpertise.pop();

      renderExpertiseTags();
    }
  }
);


expertiseSuggestions.addEventListener(
  "click",
  event => {
    const button =
      event.target.closest("button");

    if (!button) {
      return;
    }

    addExpertise(
      button.dataset.expertise
    );
  }
);


expertiseTags.addEventListener(
  "click",
  event => {
    const button =
      event.target.closest("button");

    if (!button) {
      return;
    }

    removeExpertise(
      button.dataset.expertise
    );
  }
);


subjectsTableBody.addEventListener(
  "click",
  event => {
    const button =
      event.target.closest("button");

    if (!button) {
      return;
    }

    const action =
      button.dataset.action;

    const subjectCode =
      button.dataset.code;

    const row =
      button.closest("tr");

    if (action === "edit") {
      startEditingSubject(row);
    }

    if (action === "delete") {
      deleteSubject(subjectCode);
    }
  }
);


loadSubjects();