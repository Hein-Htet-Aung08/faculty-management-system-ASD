
const maRunForm = document.getElementById("ma-run-form");
const maDecisionForm = document.getElementById("ma-decision-form");
const maMessage = document.getElementById("ma-message");
const maOutput = document.getElementById("ma-output");
const maDecision = document.getElementById("ma-decision");
const maCorrection = document.getElementById("ma-correction");

let maWorkflowId = null;

function maShowMessage(message, error = false) {
  maMessage.textContent = message;
  maMessage.className = error ? "error-state" : "empty-state";
}

function maRenderWorkflow(workflow) {
  maWorkflowId = workflow.workflow_id;

  document.getElementById("ma-plan").textContent =
    workflow.planner_result?.plan || "No plan available.";

  document.getElementById("ma-worker").textContent =
    workflow.worker_result?.output || "No worker output.";

  document.getElementById("ma-reviewer").textContent =
    workflow.reviewer_result?.review || "No review available.";

  document.getElementById("ma-checks").textContent =
    (workflow.automated_checks || [])
      .map(check =>
        `${check.passed ? "PASS" : "FAIL"} | ${check.check}: ${check.detail}`
      )
      .join("\n") || "No checks recorded.";

  document.getElementById("ma-evidence").textContent =
    (workflow.evidence || [])
      .map(item => item.source)
      .join("\n") || "No evidence available.";

  maOutput.hidden = false;

  maDecisionForm.hidden =
    workflow.human_decision?.status !== "pending";

  maShowMessage(
    `Workflow status: ${workflow.status}`
  );
}

maRunForm.addEventListener("submit", async event => {
  event.preventDefault();

  const button = document.getElementById("ma-run-button");
  button.disabled = true;

  maOutput.hidden = true;
  maDecisionForm.hidden = true;
  maWorkflowId = null;

  maShowMessage(
    "Running Planner, Worker and Reviewer. This may take several minutes..."
  );

  try {
    const workflow = await apiRequest(
      "/multi-agent/workflow",
      {
        method: "POST",
        body: JSON.stringify({
          user_request: document.getElementById("ma-request")
            .value.trim()
        })
      }
    );

    maRenderWorkflow(workflow);
    await maLoadHistory();

  } catch (error) {
    maShowMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
});

maDecision.addEventListener("change", () => {
  const correcting = maDecision.value === "Correct";

  document.getElementById("ma-correction-container").hidden =
    !correcting;

  maCorrection.required = correcting;
});

maDecisionForm.addEventListener("submit", async event => {
  event.preventDefault();

  if (!maWorkflowId) return;

  const button = maDecisionForm.querySelector(
    'button[type="submit"]'
  );
  button.disabled = true;

  const body = {
    decision: maDecision.value,
    reviewer: document.getElementById("ma-reviewer-name")
      .value.trim(),
    notes: document.getElementById("ma-notes").value.trim()
  };

  if (body.decision === "Correct") {
    body.correction = maCorrection.value.trim();
  }

  try {
    const workflow = await apiRequest(
      `/multi-agent/workflow/${encodeURIComponent(maWorkflowId)}/decision`,
      {
        method: "POST",
        body: JSON.stringify(body)
      }
    );

    maRenderWorkflow(workflow);
    await maLoadHistory();

  } catch (error) {
    maShowMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
});

async function maLoadHistory() {
  try {
    const response = await apiRequest(
      "/multi-agent/workflow/history?limit=20"
    );

    const list = document.getElementById("ma-history");
    list.replaceChildren();

    for (const item of response.workflows || []) {
      const li = document.createElement("li");
      const button = document.createElement("button");

      button.type = "button";
      button.className = "btn secondary";
      button.textContent =
        `${item.user_request} (${item.status})`;

      button.addEventListener("click", async () => {
        try {
          const workflow = await apiRequest(
            `/multi-agent/workflow/${encodeURIComponent(item.workflow_id)}`
          );
          maRenderWorkflow(workflow);
        } catch (error) {
          maShowMessage(error.message, true);
        }
      });

      li.appendChild(button);
      list.appendChild(li);
    }

    if (!list.children.length) {
      const empty = document.createElement("li");
      empty.textContent = "No workflows yet.";
      list.appendChild(empty);
    }
  } catch (error) {
    maShowMessage(error.message, true);
  }
}

document.getElementById("ma-refresh")
  .addEventListener("click", maLoadHistory);
