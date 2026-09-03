const aiAllocationInput = document.getElementById(
  "ai-allocation-id"
);

const aiAllocationDetails = document.getElementById(
  "ai-allocation-details"
);

const aiOfferInput = document.getElementById("ai-offer-id");
const aiRequiredExpertiseInput = document.getElementById(
  "ai-required-expertise"
);
const aiClassroomInput = document.getElementById("ai-classroom-id");
const aiDayInput = document.getElementById("ai-day");
const aiDateRangeInput = document.getElementById("ai-date-range");
const aiStartTimeInput = document.getElementById("ai-start-time");
const aiEndTimeInput = document.getElementById("ai-end-time");
const aiClassTypeInput = document.getElementById("ai-class-type");
const aiClassSizeInput = document.getElementById("ai-class-size");
const aiStatusInput = document.getElementById("ai-status");

const aiGenerateButton = document.getElementById(
  "ai-generate-button"
);

const aiGenerateAgainButton = document.getElementById(
  "ai-generate-again-button"
);

const aiMessage = document.getElementById("ai-message");
const aiResults = document.getElementById("ai-results");

const aiRejectedSection = document.getElementById(
  "ai-rejected-section"
);

const aiRejectedResults = document.getElementById(
  "ai-rejected-results"
);

let selectedAllocation = null;
let previousRecommendationIds = [];
let previousFailureReasons = [];

function aiEscapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function resetAiHistory() {
  previousRecommendationIds = [];
  previousFailureReasons = [];

  aiGenerateAgainButton.hidden = true;
  aiResults.innerHTML = "";
  aiRejectedResults.innerHTML = "";
  aiRejectedSection.hidden = true;
}

function parseAllocationListItem(text) {
  const parts = text
    .split(" - ")
    .map(part => part.trim());

  if (parts.length < 7) {
    return null;
  }

  const allocationId = parts[0];

  if (!/^\d+$/.test(allocationId)) {
    return null;
  }

  return {
    allocationId,
    offerId: parts[1],
    staff: parts[2],
    classroomId: parts[3],
    schedule: parts[4],
    classType: parts[5],
    status: parts[6]
  };
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

  const result = {};

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
      result.allocation_id = value;
    }

    if (key === "offer id") {
      result.offer_id = value;
    }

    if (key === "assigned staff member") {
      result.assigned_staff_member =
        value === "Unassigned" ? null : value;
    }

    if (key === "classroom id") {
      result.classroom_id = value;
    }

    if (key === "day") {
      result.day = value;
    }

    if (key === "date range") {
      result.date_range = value;
    }

    if (key === "start time") {
      result.start_time = value;
    }

    if (key === "end time") {
      result.end_time = value;
    }

    if (key === "class type") {
      result.class_type = value;
    }

    if (key === "expected class size") {
      result.expected_class_size = value;
    }

    if (key === "allocation status") {
      result.allocation_status = value;
    }
  });

  return result;
}

async function loadNeedsAssignmentAllocations() {
  try {
    const html = await apiRequest(
      "/teaching-allocations?status=NEEDS_ASSIGNMENT"
    );

    const parser = new DOMParser();

    const doc = parser.parseFromString(
      html,
      "text/html"
    );

    const items = doc.querySelectorAll("li");

    aiAllocationInput.innerHTML = `
      <option value="">
        Select an allocation
      </option>
    `;

    let count = 0;

    items.forEach(item => {
      const allocation = parseAllocationListItem(
        item.textContent.trim()
      );

      if (!allocation) {
        return;
      }

      if (
        allocation.status !==
        "NEEDS_ASSIGNMENT"
      ) {
        return;
      }

      const option =
        document.createElement("option");

      option.value =
        allocation.allocationId;

      option.textContent =
        `Allocation ${allocation.allocationId} · ` +
        `${allocation.offerId} · ` +
        `${allocation.classroomId} · ` +
        `${allocation.schedule}`;

      aiAllocationInput.appendChild(option);

      count++;
    });

    if (count === 0) {
      aiMessage.innerHTML = `
        <div class="empty-state">
          No teaching allocations currently require staff assignment.
        </div>
      `;
    } else {
      aiMessage.innerHTML = "";
    }
  } catch (error) {
    aiMessage.innerHTML = `
      <div class="error-state">
        ${aiEscapeHtml(error.message)}
      </div>
    `;
  }
}

async function loadRequiredExpertise(
  offerId
) {
  const subjectCode =
    String(offerId || "")
      .split("_")[0];

  if (!subjectCode) {
    return "";
  }

  const html =
    await apiRequest("/subjects");

  const parser = new DOMParser();

  const doc = parser.parseFromString(
    html,
    "text/html"
  );

  const items =
    doc.querySelectorAll("li");

  for (const item of items) {
    const parts = item.textContent
      .trim()
      .split(" - ")
      .map(part => part.trim());

    if (
      parts.length >= 3 &&
      parts[0] === subjectCode
    ) {
      return parts
        .slice(2)
        .join(" - ");
    }
  }

  return "";
}

async function loadSelectedAllocation(allocationId) {
  if (!allocationId) {
    selectedAllocation = null;
    aiAllocationDetails.hidden = true;
    resetAiHistory();
    return;
  }

  try {
    const html = await apiRequest(
      `/teaching-allocations/${allocationId}`
    );

    const parser = new DOMParser();

    const doc = parser.parseFromString(
      html,
      "text/html"
    );

    const details = doc.querySelector("p");

    if (!details) {
      throw new Error(
        "Unable to read teaching allocation."
      );
    }

    selectedAllocation =
      parseAllocationDetails(details);

    const requiredExpertise =
        await loadRequiredExpertise(
            selectedAllocation.offer_id
        );

    if (
      selectedAllocation.allocation_status !==
      "NEEDS_ASSIGNMENT"
    ) {
      throw new Error(
        "This allocation no longer requires assignment."
      );
    }

    aiOfferInput.value =
      selectedAllocation.offer_id || "";

    aiRequiredExpertiseInput.value =
        requiredExpertise;

    aiClassroomInput.value =
      selectedAllocation.classroom_id || "";

    aiDayInput.value =
      selectedAllocation.day || "";

    aiDateRangeInput.value =
      selectedAllocation.date_range || "";

    aiStartTimeInput.value =
      selectedAllocation.start_time || "";

    aiEndTimeInput.value =
      selectedAllocation.end_time || "";

    aiClassTypeInput.value =
      selectedAllocation.class_type || "";

    aiClassSizeInput.value =
      selectedAllocation.expected_class_size || "";

    aiStatusInput.value =
      selectedAllocation.allocation_status || "";

    resetAiHistory();

    aiMessage.innerHTML = "";
    aiAllocationDetails.hidden = false;
  } catch (error) {
    selectedAllocation = null;
    aiAllocationDetails.hidden = true;

    aiMessage.innerHTML = `
      <div class="error-state">
        ${aiEscapeHtml(error.message)}
      </div>
    `;
  }
}

function getAiPayload(includePrevious = false) {
  if (!selectedAllocation) {
    return null;
  }

  const data = {
    offer_id:
      selectedAllocation.offer_id,

    day:
      selectedAllocation.day,

    date_range:
      selectedAllocation.date_range,

    start_time:
      selectedAllocation.start_time,

    end_time:
      selectedAllocation.end_time,

    class_type:
      selectedAllocation.class_type,

    expected_class_size:
      Number(
        selectedAllocation.expected_class_size
      )
  };

  if (includePrevious) {
    data.previous_recommendation_ids =
      previousRecommendationIds;

    data.previous_failure_reasons =
      previousFailureReasons;
  }

  return data;
}

function renderAiRecommendations(
  recommendations
) {
  aiResults.innerHTML = "";

  if (
    !recommendations ||
    recommendations.length === 0
  ) {
    aiResults.innerHTML = `
      <div class="empty-state">
        No valid staff recommendations were returned.
      </div>
    `;

    return;
  }

  recommendations.forEach(
    recommendation => {
      const expertise = Array.isArray(
        recommendation.expertise
        )
        ? recommendation.expertise
            .map(item => {
                const area =
                item.expertise_area || "Unknown";

                const level =
                item.skill_level;

                return level
                ? `${area} · Level ${level}`
                : area;
            })
            .join(", ")
        : recommendation.expertise || "";

      const panel =
        document.createElement("div");

      panel.className = "panel-section";

      panel.innerHTML = `
        <h3>
          #${aiEscapeHtml(
            recommendation.rank
          )}
          ${aiEscapeHtml(
            recommendation.staff_name
          )}
        </h3>

        <p>
          <strong>Staff ID:</strong>
          ${aiEscapeHtml(
            recommendation.staff_id
          )}
        </p>

        <p>
          <strong>Expertise:</strong>
          ${aiEscapeHtml(expertise)}
        </p>

        <p>
          <strong>Reason:</strong>
          ${aiEscapeHtml(
            recommendation.reason
          )}
        </p>

        <p>
          <strong>Workload:</strong>
          ${aiEscapeHtml(
            recommendation.workload_summary
          )}
        </p>

        <button
            class="btn"
            type="button"
            data-action="assign-staff"
            data-staff-id="${aiEscapeHtml(
                recommendation.staff_id
            )}"
        >
            Assign Staff
        </button>
      `;

      aiResults.appendChild(panel);
    }
  );
}

function renderRejectedRecommendations(
  rejected
) {
  aiRejectedResults.innerHTML = "";

  if (!rejected || rejected.length === 0) {
    aiRejectedSection.hidden = true;
    return;
  }

  aiRejectedSection.hidden = false;

  rejected.forEach(recommendation => {
    const item =
      document.createElement("div");

    item.className = "error-state";

    item.innerHTML = `
      Staff
      ${aiEscapeHtml(
        recommendation.staff_id ??
        "Unknown"
      )}:
      ${aiEscapeHtml(
        recommendation.reason
      )}
    `;

    aiRejectedResults.appendChild(item);
  });
}

async function assignRecommendedStaff(
    staffId
    ) {
    if (!selectedAllocation) {
        throw new Error(
        "Select a teaching allocation first."
        );
    }

    const allocationId =
        selectedAllocation.allocation_id;

    const data = {
        offer_id:
        selectedAllocation.offer_id,

        assigned_staff_member:
        Number(staffId),

        classroom_id:
        selectedAllocation.classroom_id,

        day:
        selectedAllocation.day,

        date_range:
        selectedAllocation.date_range,

        start_time:
        selectedAllocation.start_time,

        end_time:
        selectedAllocation.end_time,

        class_type:
        selectedAllocation.class_type,

        expected_class_size:
        Number(
            selectedAllocation.expected_class_size
        ),

        allocation_status:
        "PENDING"
    };

    await apiRequest(
        `/teaching-allocations/${allocationId}`,
        {
        method: "PUT",
        body: JSON.stringify(data)
        }
    );

    aiMessage.innerHTML = `
        <div class="success-state">
        Staff ${aiEscapeHtml(staffId)}
        assigned to allocation
        ${aiEscapeHtml(allocationId)}.
        </div>
    `;

    selectedAllocation = null;

    aiAllocationDetails.hidden = true;

    resetAiHistory();

    await Promise.all([
        loadAllocations(),
        loadNeedsAssignmentAllocations()
    ]);
    }

async function generateAiRecommendations(
  includePrevious = false
) {
  const data =
    getAiPayload(includePrevious);

  if (!data) {
    aiMessage.innerHTML = `
      <div class="error-state">
        Select a teaching allocation first.
      </div>
    `;

    return;
  }

  aiGenerateButton.disabled = true;
  aiGenerateAgainButton.disabled = true;

  aiMessage.innerHTML = `
    <div
      class="loading-indicator"
      style="display:block"
    >
      Generating recommendations...
    </div>
  `;

  try {
    const response = await fetch(
      `${API_BASE_URL}/teaching-allocations/recommend`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json"
        },
        body: JSON.stringify(data)
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.error ||
        "Unable to generate recommendations."
      );
    }

    const recommendations =
      result.recommendations || [];

    const rejected =
      result.rejected_recommendations || [];

    previousRecommendationIds =
      recommendations
        .map(
          recommendation =>
            recommendation.staff_id
        )
        .filter(
          value =>
            value !== null &&
            value !== undefined
        );

    previousFailureReasons =
      rejected
        .map(
          recommendation =>
            recommendation.reason
        )
        .filter(Boolean);

    renderAiRecommendations(
      recommendations
    );

    renderRejectedRecommendations(
      rejected
    );

    aiGenerateAgainButton.hidden =
      !result.can_generate_again;

    aiMessage.innerHTML = "";
  } catch (error) {
    aiMessage.innerHTML = `
      <div class="error-state">
        ${aiEscapeHtml(error.message)}
      </div>
    `;
  } finally {
    aiGenerateButton.disabled = false;
    aiGenerateAgainButton.disabled = false;
  }
}

aiResults.addEventListener(
  "click",
  async event => {
    const button =
      event.target.closest(
        '[data-action="assign-staff"]'
      );

    if (!button) {
      return;
    }

    const staffId =
      button.dataset.staffId;

    try {
      button.disabled = true;

      await assignRecommendedStaff(
        staffId
      );
    } catch (error) {
      aiMessage.innerHTML = `
        <div class="error-state">
          ${aiEscapeHtml(
            error.message
          )}
        </div>
      `;

      button.disabled = false;
    }
  }
);

aiAllocationInput.addEventListener(
  "change",
  () => {
    loadSelectedAllocation(
      aiAllocationInput.value
    );
  }
);

aiGenerateButton.addEventListener(
  "click",
  () => {
    resetAiHistory();
    generateAiRecommendations(false);
  }
);

aiGenerateAgainButton.addEventListener(
  "click",
  () => {
    generateAiRecommendations(true);
  }
);

loadNeedsAssignmentAllocations();