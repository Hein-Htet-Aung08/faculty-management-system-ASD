const subjectOfferForm =
  document.getElementById("subject-offer-form");

const offerSubjectCodeInput =
  document.getElementById("offer-subject-code");

const offerSemesterInput =
  document.getElementById("offer-semester");

const offerYearInput =
  document.getElementById("offer-year");

const offerEnrollmentInput =
  document.getElementById("offer-enrollment");

const subjectOfferCancelButton =
  document.getElementById(
    "subject-offer-cancel-button"
  );

const subjectOfferMessage =
  document.getElementById(
    "subject-offer-message"
  );

const subjectOffersTableBody =
  document.getElementById(
    "subject-offers-table-body"
  );

const subjectOffersEmpty =
  document.getElementById(
    "subject-offers-empty"
  );


let editingOfferId = null;


function escapeOfferHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function showSubjectOfferError(message) {
  subjectOfferMessage.innerHTML = `
    <div class="error-state">
      ${escapeOfferHtml(message)}
    </div>
  `;
}


function validateSubjectOfferForm() {
  const errors = [];

  const subjectCode =
    offerSubjectCodeInput.value.trim();

  const semester =
    offerSemesterInput.value.trim();

  const yearText =
    offerYearInput.value.trim();

  const enrollmentText =
    offerEnrollmentInput.value.trim();

  if (!/^\d{5}$/.test(subjectCode)) {
    errors.push(
      "Subject code must contain exactly 5 digits."
    );
  }

  if (
    !["AUT", "SPR", "SUM"].includes(
      semester
    )
  ) {
    errors.push(
      "Semester must be AUT, SPR, or SUM."
    );
  }

  if (!/^\d{4}$/.test(yearText)) {
    errors.push(
      "Year must contain exactly 4 digits."
    );
  }

  const enrollment =
    Number(enrollmentText);

  if (
    !enrollmentText ||
    !Number.isInteger(enrollment) ||
    enrollment <= 0
  ) {
    errors.push(
      "Expected enrollment must be a positive whole number."
    );
  }

  return errors;
}


async function loadSubjectOffers() {
  try {
    const html =
      await apiRequest(
        "/subject-offers"
      );

    const parser =
      new DOMParser();

    const doc =
      parser.parseFromString(
        html,
        "text/html"
      );

    const items =
      doc.querySelectorAll("li");

    subjectOffersTableBody.innerHTML =
      "";

    if (items.length === 0) {
      subjectOffersEmpty.hidden = false;
      return;
    }

    subjectOffersEmpty.hidden = true;

    items.forEach(item => {
      const text =
        item.textContent.trim();

      const parts =
        text.split(" - ");

      if (parts.length < 4) {
        return;
      }

      const offerId =
        parts[0].trim();

      const subjectCode =
        parts[1].trim();

      const semesterYear =
        parts[2].trim().split(" ");

      const semester =
        semesterYear[0];

      const year =
        semesterYear[1];

      const expectedEnrollment =
        parts
          .slice(3)
          .join(" - ")
          .replace(
            "Expected Enrolment:",
            ""
          )
          .trim();

      const row =
        document.createElement("tr");

      row.innerHTML = `
        <td>
          ${escapeOfferHtml(offerId)}
        </td>

        <td>
          ${escapeOfferHtml(subjectCode)}
        </td>

        <td>
          ${escapeOfferHtml(semester)}
        </td>

        <td>
          ${escapeOfferHtml(year)}
        </td>

        <td>
          ${escapeOfferHtml(
            expectedEnrollment
          )}
        </td>

        <td>
          <button
            class="btn secondary"
            type="button"
            data-action="edit"
            data-offer-id="${escapeOfferHtml(
              offerId
            )}"
          >
            Edit
          </button>

          <button
            class="btn secondary"
            type="button"
            data-action="delete"
            data-offer-id="${escapeOfferHtml(
              offerId
            )}"
          >
            Delete
          </button>
        </td>
      `;

      subjectOffersTableBody.appendChild(
        row
      );
    });

  } catch (error) {
    showSubjectOfferError(
      error.message
    );
  }
}


async function saveSubjectOffer(event) {
  event.preventDefault();

  subjectOfferMessage.innerHTML = "";

  const errors =
    validateSubjectOfferForm();

  if (errors.length > 0) {
    showSubjectOfferError(
      errors.join(" ")
    );

    return;
  }

  const data = {
    subject_code:
      offerSubjectCodeInput.value.trim(),

    semester:
      offerSemesterInput.value,

    year:
      offerYearInput.value.trim(),

    expected_enrollment:
      Number(
        offerEnrollmentInput.value
      )
  };

  try {
    if (editingOfferId) {
      subjectOfferMessage.innerHTML =
        await apiRequest(
          `/subject-offers/${encodeURIComponent(
            editingOfferId
          )}`,
          {
            method: "PUT",
            body: JSON.stringify(data)
          }
        );
    } else {
      subjectOfferMessage.innerHTML =
        await apiRequest(
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
    showSubjectOfferError(
      error.message
    );
  }
}


function startEditingSubjectOffer(row) {
  const cells =
    row.querySelectorAll("td");

  editingOfferId =
    cells[0].textContent.trim();

  offerSubjectCodeInput.value =
    cells[1].textContent.trim();

  offerSemesterInput.value =
    cells[2].textContent.trim();

  offerYearInput.value =
    cells[3].textContent.trim();

  offerEnrollmentInput.value =
    cells[4].textContent.trim();

  subjectOfferMessage.innerHTML = "";

  subjectOfferForm.querySelector(
    'button[type="submit"]'
  ).textContent =
    "Update Subject Offer";

  subjectOfferCancelButton.hidden =
    false;
}


async function deleteSubjectOffer(
  offerId
) {
  const confirmed =
    window.confirm(
      `Delete subject offer ${offerId}?`
    );

  if (!confirmed) {
    return;
  }

  subjectOfferMessage.innerHTML = "";

  try {
    subjectOfferMessage.innerHTML =
      await apiRequest(
        `/subject-offers/${encodeURIComponent(
          offerId
        )}`,
        {
          method: "DELETE"
        }
      );

    if (
      editingOfferId === offerId
    ) {
      resetSubjectOfferForm();
    }

    await loadSubjectOffers();

  } catch (error) {
    showSubjectOfferError(
      error.message
    );
  }
}


function resetSubjectOfferForm() {
  subjectOfferForm.reset();

  editingOfferId = null;

  subjectOfferMessage.innerHTML = "";

  subjectOfferForm.querySelector(
    'button[type="submit"]'
  ).textContent =
    "Add Subject Offer";

  subjectOfferCancelButton.hidden =
    true;
}


subjectOfferForm.addEventListener(
  "submit",
  saveSubjectOffer
);


subjectOfferCancelButton.addEventListener(
  "click",
  resetSubjectOfferForm
);


offerSubjectCodeInput.addEventListener(
  "input",
  () => {
    offerSubjectCodeInput.value =
      offerSubjectCodeInput.value
        .replace(/\D/g, "")
        .slice(0, 5);
  }
);


offerYearInput.addEventListener(
  "input",
  () => {
    offerYearInput.value =
      offerYearInput.value
        .replace(/\D/g, "")
        .slice(0, 4);
  }
);


subjectOffersTableBody.addEventListener(
  "click",
  event => {
    const button =
      event.target.closest("button");

    if (!button) {
      return;
    }

    const action =
      button.dataset.action;

    const offerId =
      button.dataset.offerId;

    const row =
      button.closest("tr");

    if (action === "edit") {
      startEditingSubjectOffer(row);
    }

    if (action === "delete") {
      deleteSubjectOffer(offerId);
    }
  }
);


loadSubjectOffers();