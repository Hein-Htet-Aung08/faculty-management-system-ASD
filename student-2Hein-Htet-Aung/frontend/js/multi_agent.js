
/*
 * Student 2: Multi-Agent Workflow
 * Release 2 presentation interface
 *
 * Preserves the existing HTML IDs and backend API contract.
 * No changes required to index.html or the backend.
 */

const maRunForm = document.getElementById("ma-run-form");
const maDecisionForm = document.getElementById("ma-decision-form");
const maMessage = document.getElementById("ma-message");
const maOutput = document.getElementById("ma-output");
const maDecision = document.getElementById("ma-decision");
const maCorrection = document.getElementById("ma-correction");

let maWorkflowId = null;

/* ==========================================================
   STYLES
   ========================================================== */

const maStyles = document.createElement("style");

maStyles.textContent = `
  #multi-agent {
    --ma-primary: #365c80;
    --ma-primary-light: #edf4fa;
    --ma-border: #dce5ed;
    --ma-text: #253747;
    --ma-muted: #64748b;
    --ma-success: #16835e;
    --ma-danger: #bd4545;
    --ma-radius: 14px;
  }

  #multi-agent > h2 {
    margin-bottom: 8px;
    letter-spacing: -0.025em;
  }

  #multi-agent > p {
    color: var(--ma-muted);
    margin-bottom: 22px;
  }

  #ma-run-form,
  #ma-decision-form,
  #multi-agent .ma-history-panel {
    border: 1px solid var(--ma-border);
    background: #fff;
    border-radius: var(--ma-radius);
    padding: 22px;
    margin: 18px 0;
    box-shadow: 0 4px 18px rgba(31, 53, 73, 0.045);
  }

  #ma-run-form textarea,
  #ma-decision-form textarea,
  #ma-decision-form input,
  #ma-decision-form select {
    width: 100%;
    box-sizing: border-box;
    border-radius: 9px;
  }

  #ma-run-button {
    margin-top: 12px;
  }

  #ma-run-button:disabled,
  #ma-decision-form button:disabled {
    opacity: 0.6;
    cursor: wait;
  }

  #ma-message:not(:empty) {
    margin: 16px 0;
    border-radius: 10px;
    padding: 13px 16px;
    font-size: 0.92rem;
    line-height: 1.55;
  }

  #ma-message.empty-state {
    background: #edf4fa;
    color: #315779;
    border: 1px solid #d2e3f0;
  }

  #ma-message.error-state {
    background: #fff1f0;
    color: #9b3333;
    border: 1px solid #f1cbcb;
  }

  #ma-output[hidden],
  #ma-decision-form[hidden] {
    display: none !important;
  }

  #ma-output {
    margin: 24px 0;
  }

  .ma-summary {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 14px;
    padding: 18px 20px;
    margin-bottom: 20px;
    border: 1px solid var(--ma-border);
    background: linear-gradient(135deg, #f3f8fc, #ffffff);
    border-radius: var(--ma-radius);
  }

  .ma-summary-title {
    font-size: 1.02rem;
    font-weight: 750;
    color: var(--ma-text);
    margin: 0 0 5px;
  }

  .ma-workflow-id {
    font-size: 0.75rem;
    color: var(--ma-muted);
    overflow-wrap: anywhere;
  }

  .ma-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border-radius: 999px;
    padding: 7px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    background: #edf4fa;
    color: #365c80;
    border: 1px solid #d1e0ed;
  }

  .ma-badge[data-status="accepted"] {
    background: #e9f8f0;
    color: #13724e;
    border-color: #c9ebd8;
  }

  .ma-badge[data-status="rejected"] {
    background: #fff0ef;
    color: #a63c3c;
    border-color: #f1cdca;
  }

  .ma-badge[data-status="corrected"],
  .ma-badge[data-status="partially_accepted"],
  .ma-badge[data-status="awaiting_human_review"] {
    background: #fff7e8;
    color: #95600a;
    border-color: #f0dfb8;
  }

  .ma-timeline {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 9px;
    margin-bottom: 21px;
  }

  .ma-timeline-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 7px;
    padding: 13px 7px;
    border: 1px solid var(--ma-border);
    border-radius: 11px;
    background: #fff;
    text-align: center;
    min-width: 0;
  }

  .ma-timeline-number {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #e9f1f8;
    color: var(--ma-primary);
    font-size: 0.8rem;
    font-weight: 800;
  }

  .ma-timeline-item.complete .ma-timeline-number {
    background: #e4f5ed;
    color: var(--ma-success);
  }

  .ma-timeline-item.pending .ma-timeline-number {
    background: #fff3db;
    color: #99620b;
  }

  .ma-timeline-label {
    font-size: 0.79rem;
    color: var(--ma-text);
    font-weight: 650;
  }

  .ma-card {
    border: 1px solid var(--ma-border);
    border-radius: var(--ma-radius);
    background: #fff;
    margin: 15px 0;
    overflow: hidden;
    box-shadow: 0 3px 15px rgba(28, 50, 70, 0.04);
  }

  .ma-card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 15px 19px;
    background: #f5f8fb;
    border-bottom: 1px solid var(--ma-border);
  }

  .ma-card-icon {
    display: grid;
    place-items: center;
    flex-shrink: 0;
    width: 35px;
    height: 35px;
    border-radius: 10px;
    background: #e1ebf4;
    color: var(--ma-primary);
    font-size: 1rem;
    font-weight: 800;
  }

  .ma-card-heading {
    margin: 0 !important;
    font-size: 1rem;
    font-weight: 750;
    color: var(--ma-text);
  }

  .ma-card-subtitle {
    margin: 3px 0 0;
    color: var(--ma-muted);
    font-size: 0.78rem;
  }

  .ma-card-body {
    padding: 18px 20px;
    color: var(--ma-text);
    font-size: 0.91rem;
    line-height: 1.7;
    overflow-wrap: anywhere;
  }

  .ma-formatted-output {
    white-space: normal;
    overflow-wrap: anywhere;
  }

  .ma-formatted-output p {
    margin: 0 0 12px;
    line-height: 1.7;
  }

  .ma-formatted-output p:last-child {
    margin-bottom: 0;
  }

  .ma-formatted-output ul,
  .ma-formatted-output ol {
    margin: 8px 0 13px;
    padding-left: 22px;
  }

  .ma-formatted-output li {
    margin: 5px 0;
  }

  .ma-formatted-output strong {
    font-weight: 750;
    color: #1b3853;
  }

  .ma-formatted-output h4,
  .ma-formatted-output h5 {
    font-size: 0.95rem;
    color: #254f73;
    margin: 16px 0 8px;
  }

  .ma-formatted-output h4:first-child {
    margin-top: 0;
  }

  .ma-code-block {
    display: block;
    background: #f2f6f9;
    border: 1px solid #e2e9ef;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    overflow-x: auto;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.82rem;
    line-height: 1.55;
  }

  .ma-check-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 9px;
  }

  .ma-check-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8fafc;
    border: 1px solid #e8edf2;
    padding: 12px;
    border-radius: 9px;
  }

  .ma-check-icon {
    font-weight: 800;
    color: var(--ma-success);
    flex-shrink: 0;
  }

  .ma-check-item.failed .ma-check-icon {
    color: var(--ma-danger);
  }

  .ma-check-name {
    font-weight: 700;
    font-size: 0.87rem;
  }

  .ma-check-detail {
    color: var(--ma-muted);
    font-size: 0.82rem;
    margin-top: 3px;
  }

  .ma-evidence-list {
    margin: 0;
    padding-left: 21px;
  }

  .ma-evidence-list li {
    margin: 7px 0;
    overflow-wrap: anywhere;
  }

  .ma-muted {
    color: var(--ma-muted);
  }

  .ma-evidence-card {
    margin-top: 15px;
  }

  .ma-evidence-card .ma-card-body {
    padding-top: 10px;
  }

  .ma-evidence-card summary {
    cursor: pointer;
    padding: 12px 0;
    font-weight: 700;
    color: var(--ma-primary);
  }

  .ma-evidence-card details[open] summary {
    margin-bottom: 8px;
  }

  #ma-decision-form {
    border-left: 4px solid #52799d;
    padding: 22px;
  }

  #ma-decision-form > h3 {
    color: var(--ma-text);
    margin-top: 0;
    margin-bottom: 15px;
  }

  #ma-decision-form .form-field {
    margin: 12px 0;
  }

  #multi-agent .ma-history-panel h3 {
    margin-top: 0;
  }

  #ma-history {
    display: grid;
    gap: 9px;
    list-style: none;
    padding: 0;
    margin: 15px 0 0;
  }

  #ma-history li {
    margin: 0;
    padding: 0;
  }

  #ma-history button {
    width: 100%;
    text-align: left;
    white-space: normal;
    overflow-wrap: anywhere;
    line-height: 1.5;
  }

  .ma-history-entry {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .ma-history-status {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--ma-primary);
    text-transform: capitalize;
  }

  @media (max-width: 640px) {
    .ma-timeline {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .ma-card-body,
    #ma-run-form,
    #ma-decision-form {
      padding: 15px;
    }

    .ma-summary {
      padding: 15px;
    }
  }
`;

document.head.appendChild(maStyles);

/* ==========================================================
   SAFE TEXT FORMATTING
   ========================================================== */

function maEscape(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function maInlineFormat(text) {
  let result = maEscape(text);

  result = result.replace(
    /\*\*(.+?)\*\*/g,
    "<strong>$1</strong>"
  );

  result = result.replace(
    /`([^`]+)`/g,
    "<code>$1</code>"
  );

  return result;
}

function maFormatText(value) {
  const text = String(value ?? "").trim();

  if (!text) {
    return '<p class="ma-muted">No output available.</p>';
  }

  const lines = text.split(/\r?\n/);
  const result = [];
  let list = null;
  let inCode = false;
  let codeLines = [];
  let paragraph = [];

  function closeParagraph() {
    if (paragraph.length) {
      result.push(
        `<p>${paragraph.map(maInlineFormat).join(" ")}</p>`
      );
      paragraph = [];
    }
  }

  function closeList() {
    if (list) {
      result.push(`</${list}>`);
      list = null;
    }
  }

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      closeParagraph();
      closeList();

      if (inCode) {
        result.push(
          `<pre class="ma-code-block">${maEscape(
            codeLines.join("\n")
          )}</pre>`
        );
        codeLines = [];
      }

      inCode = !inCode;
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    if (!trimmed) {
      closeParagraph();
      closeList();
      continue;
    }

    const heading = trimmed.match(/^#{1,5}\s+(.+)$/);

    if (heading) {
      closeParagraph();
      closeList();
      result.push(
        `<h4>${maInlineFormat(heading[1])}</h4>`
      );
      continue;
    }

    const bullet = trimmed.match(/^[-*•]\s+(.+)$/);
    const numbered = trimmed.match(/^\d+[.)]\s+(.+)$/);

    if (bullet || numbered) {
      closeParagraph();

      const type = bullet ? "ul" : "ol";

      if (list !== type) {
        closeList();
        result.push(`<${type}>`);
        list = type;
      }

      result.push(
        `<li>${maInlineFormat(
          bullet ? bullet[1] : numbered[1]
        )}</li>`
      );
      continue;
    }

    closeList();

    // Preserve visible indentation in structured output.
    if (/^\s{2,}\S/.test(line)) {
      closeParagraph();
      result.push(
        `<pre class="ma-code-block">${maEscape(line)}</pre>`
      );
      continue;
    }

    paragraph.push(trimmed);
  }

  closeParagraph();
  closeList();

  if (inCode && codeLines.length) {
    result.push(
      `<pre class="ma-code-block">${maEscape(
        codeLines.join("\n")
      )}</pre>`
    );
  }

  return result.join("\n");
}

/* ==========================================================
   CREATE PRESENTATION CARDS
   ========================================================== */

function maMakeCard({
  title,
  subtitle,
  icon,
  contentId,
  collapsible = false
}) {
  const original = document.getElementById(contentId);

  if (!original) {
    return null;
  }

  const card = document.createElement("article");
  card.className = "ma-card";

  if (collapsible) {
    card.classList.add("ma-evidence-card");
  }

  const header = document.createElement("div");
  header.className = "ma-card-header";

  const symbol = document.createElement("span");
  symbol.className = "ma-card-icon";
  symbol.textContent = icon;

  const info = document.createElement("div");

  const heading = document.createElement("h3");
  heading.className = "ma-card-heading";
  heading.textContent = title;

  const description = document.createElement("p");
  description.className = "ma-card-subtitle";
  description.textContent = subtitle;

  info.append(heading, description);
  header.append(symbol, info);

  const body = document.createElement("div");
  body.className = "ma-card-body";

  // Keep the original ID for compatibility.
  original.className = "ma-formatted-output";
  original.removeAttribute("style");
  body.appendChild(original);

  if (collapsible) {
    const details = document.createElement("details");

    const summary = document.createElement("summary");
    summary.textContent = "Show evidence sources";

    details.append(summary, body);
    card.append(header, details);
  } else {
    card.append(header, body);
  }

  return card;
}

function maPrepareLayout() {
  const content = [
    {
      title: "01. Planner Agent",
      subtitle: "Planning and evidence requirements",
      icon: "01",
      contentId: "ma-plan"
    },
    {
      title: "02. Worker Agent",
      subtitle: "Execution and evidence-based findings",
      icon: "02",
      contentId: "ma-worker"
    },
    {
      title: "Automated Evidence Checks",
      subtitle: "Deterministic workflow validation",
      icon: "✓",
      contentId: "ma-checks"
    },
    {
      title: "03. Reviewer Agent",
      subtitle: "Independent review and recommendations",
      icon: "03",
      contentId: "ma-reviewer"
    },
    {
      title: "Evidence Sources",
      subtitle: "Supporting records supplied to the workflow",
      icon: "≡",
      contentId: "ma-evidence",
      collapsible: true
    }
  ];

  // Remove the old standalone headings.
  for (const heading of maOutput.querySelectorAll("h3")) {
    heading.remove();
  }

  const summary = document.createElement("div");
  summary.className = "ma-summary";
  summary.id = "ma-summary";

  const timeline = document.createElement("div");
  timeline.className = "ma-timeline";
  timeline.id = "ma-timeline";

  maOutput.prepend(timeline);
  maOutput.prepend(summary);

  for (const item of content) {
    const card = maMakeCard(item);
    if (card) {
      maOutput.appendChild(card);
    }
  }

  const decisionHeading = maDecisionForm.querySelector("h3");

  if (decisionHeading) {
    decisionHeading.textContent = "04. Human Review & Decision";
  }

  const history = document.getElementById("ma-history");

  const historyPanel = history?.closest(".panel-section");

  if (historyPanel) {
    historyPanel.classList.add("ma-history-panel");
  }
}

maPrepareLayout();

/* ==========================================================
   WORKFLOW STATUS AND RENDERING
   ========================================================== */

function maStatusLabel(status) {
  return String(status || "unknown")
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase());
}

function maShowMessage(message, error = false) {
  maMessage.textContent = message;
  maMessage.className = error ? "error-state" : "empty-state";
}

function maRenderSummary(workflow) {
  const summary = document.getElementById("ma-summary");
  const status = String(workflow.status || "unknown");

  summary.replaceChildren();

  const info = document.createElement("div");

  const title = document.createElement("p");
  title.className = "ma-summary-title";
  title.textContent = "Workflow Execution Report";

  const id = document.createElement("div");
  id.className = "ma-workflow-id";
  id.textContent =
    `Workflow ID: ${workflow.workflow_id || "Unavailable"}`;

  info.append(title, id);

  const badge = document.createElement("span");
  badge.className = "ma-badge";
  badge.dataset.status = status;
  badge.textContent = maStatusLabel(status);

  summary.append(info, badge);
}

function maRenderTimeline(workflow) {
  const timeline = document.getElementById("ma-timeline");
  timeline.replaceChildren();

  const humanComplete =
    workflow.human_decision?.status === "recorded";

  const stages = [
    ["Planner", Boolean(workflow.planner_result)],
    ["Worker", Boolean(workflow.worker_result)],
    ["Reviewer", Boolean(workflow.reviewer_result)],
    ["Human Review", humanComplete]
  ];

  stages.forEach(([label, complete], index) => {
    const item = document.createElement("div");

    item.className =
      `ma-timeline-item ${complete ? "complete" : "pending"}`;

    const number = document.createElement("span");
    number.className = "ma-timeline-number";
    number.textContent = complete ? "✓" : String(index + 1);

    const name = document.createElement("span");
    name.className = "ma-timeline-label";
    name.textContent = label;

    item.append(number, name);
    timeline.appendChild(item);
  });
}

function maRenderChecks(checks) {
  if (!Array.isArray(checks) || !checks.length) {
    return '<p class="ma-muted">No checks recorded.</p>';
  }

  return `
    <ul class="ma-check-list">
      ${checks.map(check => `
        <li class="ma-check-item ${check.passed ? "" : "failed"}">
          <span class="ma-check-icon">
            ${check.passed ? "✓" : "✕"}
          </span>
          <div>
            <div class="ma-check-name">
              ${maEscape(check.check || "Unnamed check")}
            </div>
            <div class="ma-check-detail">
              ${maEscape(check.detail || "")}
            </div>
          </div>
        </li>
      `).join("")}
    </ul>
  `;
}

function maRenderEvidence(evidence) {
  if (!Array.isArray(evidence) || !evidence.length) {
    return '<p class="ma-muted">No evidence sources recorded.</p>';
  }

  return `
    <ul class="ma-evidence-list">
      ${evidence.map(item => `
        <li>${maEscape(item.source || "Unknown source")}</li>
      `).join("")}
    </ul>
  `;
}

function maRenderHumanDecision(workflow) {
  let display = document.getElementById("ma-recorded-decision");

  if (!display) {
    display = document.createElement("article");
    display.id = "ma-recorded-decision";
    display.className = "ma-card";

    maOutput.appendChild(display);
  }

  const human = workflow.human_decision || {};

  if (human.status !== "recorded") {
    display.hidden = true;
    return;
  }

  display.hidden = false;

  display.innerHTML = `
    <div class="ma-card-header">
      <span class="ma-card-icon">04</span>
      <div>
        <h3 class="ma-card-heading">Human Review Completed</h3>
        <p class="ma-card-subtitle">
          Final human oversight and recorded decision
        </p>
      </div>
    </div>
    <div class="ma-card-body">
      <p><strong>Decision:</strong>
        ${maEscape(human.decision || "Not specified")}
      </p>
      <p><strong>Reviewer:</strong>
        ${maEscape(human.reviewer || "Not specified")}
      </p>
      ${human.notes ? `
        <p><strong>Notes:</strong></p>
        ${maFormatText(human.notes)}
      ` : ""}
      ${human.correction ? `
        <p><strong>Correction:</strong></p>
        ${maFormatText(human.correction)}
      ` : ""}
    </div>
  `;
}

function maRenderWorkflow(workflow) {
  maWorkflowId = workflow.workflow_id;

  maRenderSummary(workflow);
  maRenderTimeline(workflow);

  document.getElementById("ma-plan").innerHTML =
    maFormatText(workflow.planner_result?.plan);

  document.getElementById("ma-worker").innerHTML =
    maFormatText(workflow.worker_result?.output);

  document.getElementById("ma-reviewer").innerHTML =
    maFormatText(workflow.reviewer_result?.review);

  document.getElementById("ma-checks").innerHTML =
    maRenderChecks(workflow.automated_checks);

  document.getElementById("ma-evidence").innerHTML =
    maRenderEvidence(workflow.evidence);

  maRenderHumanDecision(workflow);

  maOutput.hidden = false;

  maDecisionForm.hidden =
    workflow.human_decision?.status !== "pending";

  maShowMessage(
    `Workflow status: ${maStatusLabel(workflow.status)}`
  );

  // Make the results easy to see during recording.
  maOutput.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}

/* ==========================================================
   RUN WORKFLOW
   ========================================================== */

maRunForm.addEventListener("submit", async event => {
  event.preventDefault();

  const button = document.getElementById("ma-run-button");
  const request = document.getElementById("ma-request")
    .value.trim();

  if (!request) {
    maShowMessage("Enter a workflow request first.", true);
    return;
  }

  button.disabled = true;
  button.textContent = "Running Workflow...";

  maOutput.hidden = true;
  maDecisionForm.hidden = true;
  maWorkflowId = null;

  maShowMessage(
    "Running Planner, Worker and Reviewer. " +
    "The workflow is processing your request..."
  );

  try {
    const workflow = await apiRequest(
      "/multi-agent/workflow",
      {
        method: "POST",
        body: JSON.stringify({
          user_request: request
        })
      }
    );

    maRenderWorkflow(workflow);

    await maLoadHistory();

  } catch (error) {
    maShowMessage(error.message, true);

  } finally {
    button.disabled = false;
    button.textContent = "Run Workflow";
  }
});

/* ==========================================================
   HUMAN REVIEW
   ========================================================== */

maDecision.addEventListener("change", () => {
  const correcting = maDecision.value === "Correct";

  document.getElementById("ma-correction-container").hidden =
    !correcting;

  maCorrection.required = correcting;
});

maDecisionForm.addEventListener("submit", async event => {
  event.preventDefault();

  if (!maWorkflowId) {
    maShowMessage("No workflow selected.", true);
    return;
  }

  const button = maDecisionForm.querySelector(
    'button[type="submit"]'
  );

  button.disabled = true;

  const body = {
    decision: maDecision.value,
    reviewer: document.getElementById("ma-reviewer-name")
      .value.trim(),
    notes: document.getElementById("ma-notes")
      .value.trim()
  };

  if (body.decision === "Correct") {
    body.correction = maCorrection.value.trim();
  }

  try {
    const workflow = await apiRequest(
      `/multi-agent/workflow/${encodeURIComponent(
        maWorkflowId
      )}/decision`,
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

/* ==========================================================
   WORKFLOW HISTORY
   ========================================================== */

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
      button.className = "btn secondary ma-history-entry";

      const request = document.createElement("span");
      request.textContent =
        item.user_request || "Untitled workflow";

      const status = document.createElement("span");
      status.className = "ma-history-status";
      status.textContent = maStatusLabel(item.status);

      button.append(request, status);

      button.addEventListener("click", async () => {
        try {
          const workflow = await apiRequest(
            `/multi-agent/workflow/${encodeURIComponent(
              item.workflow_id
            )}`
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
      empty.className = "ma-muted";
      empty.textContent = "No workflows recorded yet.";
      list.appendChild(empty);
    }

  } catch (error) {
    maShowMessage(error.message, true);
  }
}

document.getElementById("ma-refresh")
  .addEventListener("click", maLoadHistory);
