const MCP_STORAGE_KEY =
  "mcpMode";

const mcpModeToggle =
  document.getElementById(
    "mcp-mode-toggle"
  );

const mcpModeStatus =
  document.getElementById(
    "mcp-mode-status"
  );

const mcpClassroomForm =
  document.getElementById(
    "mcp-classroom-form"
  );

const mcpValidationForm =
  document.getElementById(
    "mcp-validation-form"
  );


function getMcpMode() {
  return (
    localStorage.getItem(
      MCP_STORAGE_KEY
    ) === "on"
      ? "on"
      : "off"
  );
}


function setMcpMode(
  mode
) {
  localStorage.setItem(
    MCP_STORAGE_KEY,
    mode
  );

  if (
    mcpModeToggle
  ) {
    mcpModeToggle.checked =
      mode === "on";
  }

  if (
    mcpModeStatus
  ) {
    mcpModeStatus.textContent =
      mode === "on"
        ? "ON"
        : "OFF";
  }
}


function escapeHtml(
  value
) {
  return String(
    value ?? ""
  ).replace(
    /[&<>"']/g,
    character => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;"
    })[character]
  );
}


function rawJsonBlock(
  data
) {
  return `
    <details class="raw-json-details">
      <summary>
        View raw JSON
      </summary>

      <pre>${escapeHtml(
        JSON.stringify(
          data,
          null,
          2
        )
      )}</pre>
    </details>
  `;
}


function showMcpLoading(
  panel,
  message
) {
  panel.innerHTML = `
    <div class="result-loading">
      ${escapeHtml(message)}
    </div>
  `;
}


function showMcpError(
  panel,
  message
) {
  panel.innerHTML = `
    <div class="error-state">
      ${escapeHtml(message)}
    </div>
  `;
}


async function callMcp(
  path,
  form
) {
  const response =
    await fetch(
      `${API_BASE_URL}${path}`,
      {
        method:
          "POST",

        headers: {
          "X-MCP-Mode":
            getMcpMode()
        },

        body:
          new FormData(
            form
          )
      }
    );

  const contentType =
    response.headers.get(
      "content-type"
    ) || "";

  let data;

  if (
    contentType.includes(
      "application/json"
    )
  ) {
    data =
      await response.json();

  } else {
    data =
      await response.text();
  }

  if (
    !response.ok
  ) {
    const message =
      typeof data === "object"
        ? (
            data.error ||
            "MCP tool failed."
          )
        : data;

    throw new Error(
      message
    );
  }

  return data;
}


function renderAvailabilityCard(
  data,
  form
) {
  const result =
    data.data || {};

  const available =
    result.available === true;

  const classroom =
    form.elements[
      "classroom_id"
    ].value;

  const date =
    form.elements[
      "date"
    ].value;

  const year =
    form.elements[
      "year"
    ].value;

  const start =
    form.elements[
      "start_time"
    ].value;

  const end =
    form.elements[
      "end_time"
    ].value;

  let detail;

  if (
    available
  ) {
    detail = `
      <p class="result-callout success">
        No conflicting teaching allocation was found.
      </p>
    `;

  } else if (
    result.conflicting_allocation_id
  ) {
    detail = `
      <p class="result-callout warning">
        Conflicts with teaching allocation
        #${escapeHtml(
          result.conflicting_allocation_id
        )}.
      </p>
    `;

  } else {
    detail = `
      <p class="result-callout warning">
        ${escapeHtml(
          result.error ||
          "The classroom is unavailable."
        )}
      </p>
    `;
  }

  return `
    <div class="tool-result-card">

      <div class="tool-result-header">

        <div>
          <span class="tool-result-eyebrow">
            MCP TOOL
          </span>

          <h3>
            Classroom Availability
          </h3>
        </div>

        <span class="stamp ${
          available
            ? "status-active"
            : "status-on-hold"
        }">
          ${
            available
              ? "Available"
              : "Unavailable"
          }
        </span>

      </div>

      <div class="result-fact-grid">

        <div class="result-fact">
          <span>Classroom</span>
          <strong>
            ${escapeHtml(classroom)}
          </strong>
        </div>

        <div class="result-fact">
          <span>Date</span>
          <strong>
            ${escapeHtml(date)}/${escapeHtml(year)}
          </strong>
        </div>

        <div class="result-fact">
          <span>Time</span>
          <strong>
            ${escapeHtml(start)}
            –
            ${escapeHtml(end)}
          </strong>
        </div>

        <div class="result-fact">
          <span>Tool</span>
          <strong>
            ${escapeHtml(data.tool)}
          </strong>
        </div>

      </div>

      ${detail}

      ${rawJsonBlock(data)}

    </div>
  `;
}


function renderValidationCard(
  data,
  form
) {
  const result =
    data.data || {};

  const valid =
    result.valid === true;

  const errors =
    Array.isArray(
      result.errors
    )
      ? result.errors
      : [];

  const errorHtml =
    errors.length
      ? `
        <div class="validation-list">
          <strong>
            Validation issues
          </strong>

          <ul>
            ${errors
              .map(
                error => `
                  <li>
                    ${escapeHtml(error)}
                  </li>
                `
              )
              .join("")}
          </ul>
        </div>
      `
      : `
        <p class="result-callout success">
          The proposed allocation satisfies the current
          allocation validation rules.
        </p>
      `;

  return `
    <div class="tool-result-card">

      <div class="tool-result-header">

        <div>
          <span class="tool-result-eyebrow">
            MCP TOOL
          </span>

          <h3>
            Teaching Allocation Validation
          </h3>
        </div>

        <span class="stamp ${
          valid
            ? "status-active"
            : "status-on-hold"
        }">
          ${
            valid
              ? "Valid"
              : "Needs Attention"
          }
        </span>

      </div>

      <div class="result-fact-grid">

        <div class="result-fact">
          <span>Subject Offer</span>
          <strong>
            ${escapeHtml(
              form.elements[
                "offer_id"
              ].value
            )}
          </strong>
        </div>

        <div class="result-fact">
          <span>Classroom</span>
          <strong>
            ${escapeHtml(
              form.elements[
                "classroom_id"
              ].value
            )}
          </strong>
        </div>

        <div class="result-fact">
          <span>Schedule</span>
          <strong>
            ${escapeHtml(
              form.elements[
                "day"
              ].value
            )}
            ${escapeHtml(
              form.elements[
                "start_time"
              ].value
            )}
            –
            ${escapeHtml(
              form.elements[
                "end_time"
              ].value
            )}
          </strong>
        </div>

        <div class="result-fact">
          <span>Class Type / Size</span>
          <strong>
            ${escapeHtml(
              form.elements[
                "class_type"
              ].value
            )}
            ·
            ${escapeHtml(
              form.elements[
                "expected_class_size"
              ].value
            )}
          </strong>
        </div>

      </div>

      ${errorHtml}

      ${rawJsonBlock(data)}

    </div>
  `;
}


if (
  mcpModeToggle
) {
  mcpModeToggle.addEventListener(
    "change",
    () => {
      setMcpMode(
        mcpModeToggle.checked
          ? "on"
          : "off"
      );
    }
  );
}


if (
  mcpClassroomForm
) {
  mcpClassroomForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      const panel =
        document.getElementById(
          "mcp-classroom-result"
        );

      showMcpLoading(
        panel,
        "Checking classroom availability..."
      );

      try {
        const data =
          await callMcp(
            "/mcp/check-classroom-availability",
            mcpClassroomForm
          );

        panel.innerHTML =
          renderAvailabilityCard(
            data,
            mcpClassroomForm
          );

      } catch (
        error
      ) {
        showMcpError(
          panel,
          error.message
        );
      }
    }
  );
}


if (
  mcpValidationForm
) {
  mcpValidationForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      const panel =
        document.getElementById(
          "mcp-validation-result"
        );

      showMcpLoading(
        panel,
        "Validating teaching allocation..."
      );

      try {
        const data =
          await callMcp(
            "/mcp/validate-teaching-allocation",
            mcpValidationForm
          );

        panel.innerHTML =
          renderValidationCard(
            data,
            mcpValidationForm
          );

      } catch (
        error
      ) {
        showMcpError(
          panel,
          error.message
        );
      }
    }
  );
}


setMcpMode(
  getMcpMode()
);