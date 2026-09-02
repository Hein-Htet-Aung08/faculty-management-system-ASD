const aiRecommendationForm = document.getElementById(
  "ai-recommendation-form"
);

const aiOfferInput = document.getElementById("ai-offer-id");
const aiDayInput = document.getElementById("ai-day");
const aiDateRangeInput = document.getElementById("ai-date-range");
const aiStartTimeInput = document.getElementById("ai-start-time");
const aiEndTimeInput = document.getElementById("ai-end-time");
const aiClassTypeInput = document.getElementById("ai-class-type");
const aiClassSizeInput = document.getElementById("ai-class-size");

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

async function loadAiOfferOptions() {
  try {
    const html = await apiRequest("/subject-offers");

    const parser = new DOMParser();
    const doc = parser.parseFromString(
      html,
      "text/html"
    );

    aiOfferInput.innerHTML =
      `<option value="">Select subject offer</option>`;

    doc.querySelectorAll("li").forEach(item => {
      const text = item.textContent.trim();

      const offerId = text
        .split(" - ")[0]
        .trim();

      const option = document.createElement("option");

      option.value = offerId;
      option.textContent = offerId;

      aiOfferInput.appendChild(option);
    });
  } catch (error) {
    aiMessage.innerHTML = `
      <div class="error-state">
        ${aiEscapeHtml(error.message)}
      </div>
    `;
  }
}

function getAiPayload(includePrevious = false) {
  const data = {
    offer_id: aiOfferInput.value,
    day: aiDayInput.value,
    date_range: aiDateRangeInput.value.trim(),
    start_time: aiStartTimeInput.value,
    end_time: aiEndTimeInput.value,
    class_type: aiClassTypeInput.value,
    expected_class_size: Number(
      aiClassSizeInput.value
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

function renderAiRecommendations(recommendations) {
  aiResults.innerHTML = "";

  if (!recommendations || recommendations.length === 0) {
    aiResults.innerHTML = `
      <div class="empty-state">
        No valid staff recommendations were returned.
      </div>
    `;
    return;
  }

  recommendations.forEach(recommendation => {
    const panel = document.createElement("div");

    panel.className = "panel-section";

    const expertise = Array.isArray(
      recommendation.expertise
    )
      ? recommendation.expertise.join(", ")
      : recommendation.expertise || "";

    panel.innerHTML = `
      <h3>
        #${aiEscapeHtml(recommendation.rank)}
        ${aiEscapeHtml(recommendation.staff_name)}
      </h3>

      <p>
        <strong>Staff ID:</strong>
        ${aiEscapeHtml(recommendation.staff_id)}
      </p>

      <p>
        <strong>Expertise:</strong>
        ${aiEscapeHtml(expertise)}
      </p>

      <p>
        <strong>Reason:</strong>
        ${aiEscapeHtml(recommendation.reason)}
      </p>

      <p>
        <strong>Workload:</strong>
        ${aiEscapeHtml(recommendation.workload_summary)}
      </p>
    `;

    aiResults.appendChild(panel);
  });
}

function renderRejectedRecommendations(rejected) {
  aiRejectedResults.innerHTML = "";

  if (!rejected || rejected.length === 0) {
    aiRejectedSection.hidden = true;
    return;
  }

  aiRejectedSection.hidden = false;

  rejected.forEach(item => {
    const panel = document.createElement("div");

    panel.className = "error-state";

    panel.innerHTML = `
      Staff ${aiEscapeHtml(item.staff_id ?? "Unknown")}:
      ${aiEscapeHtml(item.reason)}
    `;

    aiRejectedResults.appendChild(panel);
  });
}

async function generateAiRecommendations(
  includePrevious = false
) {
  const data = getAiPayload(includePrevious);

  aiMessage.innerHTML = `
    <div class="loading-indicator" style="display:block">
      Generating recommendations...
    </div>
  `;

  aiGenerateButton.disabled = true;
  aiGenerateAgainButton.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/teaching-allocations/recommend`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
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
        .map(item => item.staff_id)
        .filter(id => id !== null && id !== undefined);

    previousFailureReasons =
      rejected
        .map(item => item.reason)
        .filter(Boolean);

    renderAiRecommendations(recommendations);
    renderRejectedRecommendations(rejected);

    aiMessage.innerHTML = "";

    aiGenerateAgainButton.hidden =
      !result.can_generate_again;
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

function resetAiHistory() {
  previousRecommendationIds = [];
  previousFailureReasons = [];

  aiGenerateAgainButton.hidden = true;
}

aiRecommendationForm.addEventListener(
  "submit",
  event => {
    event.preventDefault();

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

[
  aiOfferInput,
  aiDayInput,
  aiDateRangeInput,
  aiStartTimeInput,
  aiEndTimeInput,
  aiClassTypeInput,
  aiClassSizeInput
].forEach(input => {
  input.addEventListener(
    "change",
    resetAiHistory
  );
});

loadAiOfferOptions();