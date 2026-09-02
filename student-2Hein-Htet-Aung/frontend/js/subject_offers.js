const subjectOfferForm = document.getElementById("subject-offer-form");
const offerSubjectCodeInput = document.getElementById("offer-subject-code");
const offerSemesterInput = document.getElementById("offer-semester");
const offerYearInput = document.getElementById("offer-year");
const offerEnrollmentInput = document.getElementById("offer-enrollment");
const subjectOfferCancelButton = document.getElementById("subject-offer-cancel-button");
const subjectOfferMessage = document.getElementById("subject-offer-message");
const subjectOffersTableBody = document.getElementById("subject-offers-table-body");
const subjectOffersEmpty = document.getElementById("subject-offers-empty");

let editingOfferId = null;

async function loadSubjectOffers() {
  try {
    const html = await apiRequest("/subject-offers");

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const items = doc.querySelectorAll("li");

    subjectOffersTableBody.innerHTML = "";

    if (items.length === 0) {
      subjectOffersEmpty.hidden = false;
      return;
    }

    subjectOffersEmpty.hidden = true;

    items.forEach(item => {
      const text = item.textContent.trim();
      const parts = text.split(" - ");

      if (parts.length < 4) {
        return;
      }

      const offerId = parts[0].trim();
      const subjectCode = parts[1].trim();

      const semesterYear = parts[2].trim().split(" ");
      const semester = semesterYear[0];
      const year = semesterYear[1];

      const expectedEnrollment = parts
        .slice(3)
        .join(" - ")
        .replace("Expected Enrolment:", "")
        .trim();

      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${offerId}</td>
        <td>${subjectCode}</td>
        <td>${semester}</td>
        <td>${year}</td>
        <td>${expectedEnrollment}</td>
        <td>
          <button
            class="btn secondary"
            type="button"
            data-action="edit"
            data-offer-id="${offerId}"
          >
            Edit
          </button>

          <button
            class="btn secondary"
            type="button"
            data-action="delete"
            data-offer-id="${offerId}"
          >
            Delete
          </button>
        </td>
      `;

      subjectOffersTableBody.appendChild(row);
    });
  } catch (error) {
    subjectOfferMessage.innerHTML = `
      <div class="error-state">${error.message}</div>
    `;
  }
}

async function saveSubjectOffer(event) {
  event.preventDefault();

  const data = {
    subject_code: offerSubjectCodeInput.value.trim(),
    semester: offerSemesterInput.value,
    year: Number(offerYearInput.value),
    expected_enrollment: Number(offerEnrollmentInput.value)
  };

  try {
    if (editingOfferId) {
      subjectOfferMessage.innerHTML = await apiRequest(
        `/subject-offers/${encodeURIComponent(editingOfferId)}`,
        {
          method: "PUT",
          body: JSON.stringify(data)
        }
      );
    } else {
      subjectOfferMessage.innerHTML = await apiRequest(
        "/subject-offers",
        {
          method: "POST",
          body: JSON.stringify(data)
        }
      );
    }

    resetSubjectOfferForm();
    await loadSubjectOffers();
  } catch (error) {
    subjectOfferMessage.innerHTML = `
      <div class="error-state">${error.message}</div>
    `;
  }
}

function startEditingSubjectOffer(row) {
  const cells = row.querySelectorAll("td");

  editingOfferId = cells[0].textContent.trim();

  offerSubjectCodeInput.value = cells[1].textContent.trim();
  offerSemesterInput.value = cells[2].textContent.trim();
  offerYearInput.value = cells[3].textContent.trim();
  offerEnrollmentInput.value = cells[4].textContent.trim();

  subjectOfferForm.querySelector('button[type="submit"]').textContent =
    "Update Subject Offer";

  subjectOfferCancelButton.hidden = false;
}

async function deleteSubjectOffer(offerId) {
  const confirmed = window.confirm(
    `Delete subject offer ${offerId}?`
  );

  if (!confirmed) {
    return;
  }

  try {
    subjectOfferMessage.innerHTML = await apiRequest(
      `/subject-offers/${encodeURIComponent(offerId)}`,
      {
        method: "DELETE"
      }
    );

    if (editingOfferId === offerId) {
      resetSubjectOfferForm();
    }

    await loadSubjectOffers();
  } catch (error) {
    subjectOfferMessage.innerHTML = `
      <div class="error-state">${error.message}</div>
    `;
  }
}

function resetSubjectOfferForm() {
  subjectOfferForm.reset();

  editingOfferId = null;

  subjectOfferForm.querySelector('button[type="submit"]').textContent =
    "Add Subject Offer";

  subjectOfferCancelButton.hidden = true;
}

subjectOfferForm.addEventListener(
  "submit",
  saveSubjectOffer
);

subjectOfferCancelButton.addEventListener(
  "click",
  resetSubjectOfferForm
);

subjectOffersTableBody.addEventListener(
  "click",
  event => {
    const button = event.target.closest("button");

    if (!button) {
      return;
    }

    const action = button.dataset.action;
    const offerId = button.dataset.offerId;
    const row = button.closest("tr");

    if (action === "edit") {
      startEditingSubjectOffer(row);
    }

    if (action === "delete") {
      deleteSubjectOffer(offerId);
    }
  }
);

loadSubjectOffers();