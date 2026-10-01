const ragRefreshButton =
  document.getElementById(
    "rag-refresh-button"
  );

const ragRetrieveForm =
  document.getElementById(
    "rag-retrieve-form"
  );

const ragAskForm =
  document.getElementById(
    "rag-ask-form"
  );


function clearRagPanel(panel) {
  while (panel.firstChild) {
    panel.removeChild(
      panel.firstChild
    );
  }
}


function showRagMessage(
  panel,
  message,
  className = "empty-state"
) {
  clearRagPanel(
    panel
  );

  const paragraph =
    document.createElement(
      "p"
    );

  paragraph.className =
    className;

  paragraph.textContent =
    message;

  panel.appendChild(
    paragraph
  );
}


function escapeRagHtml(
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


function ragRawJsonBlock(
  data
) {
  return `
    <details class="raw-json-details">
      <summary>
        View raw JSON
      </summary>

      <pre>${escapeRagHtml(
        JSON.stringify(
          data,
          null,
          2
        )
      )}</pre>
    </details>
  `;
}


function showRagRetrieval(
  panel,
  data
) {
  clearRagPanel(
    panel
  );

  if (
    data.status !== "success"
  ) {
    showRagMessage(
      panel,
      data.error ||
        "RAG retrieval failed.",
      "error-state"
    );

    return;
  }

  const results =
    data.results || [];

  const cards =
    results
      .map(
        result => `
          <article class="retrieval-card">

            <div class="retrieval-card-header">

              <div>
                <span class="tool-result-eyebrow">
                  RESULT #${escapeRagHtml(
                    result.rank
                  )}
                </span>

                <h4>
                  ${escapeRagHtml(
                    result.source_id ||
                    result.chunk_id ||
                    "Retrieved Context"
                  )}
                </h4>
              </div>

              <span class="stamp status-active">
                ${escapeRagHtml(
                  result.authority_tier ||
                  "unknown"
                )}
              </span>

            </div>

            <div class="retrieval-meta">

              <span>
                Feature:
                <strong>
                  ${escapeRagHtml(
                    result.feature ||
                    "Unknown"
                  )}
                </strong>
              </span>

              <span>
                Student:
                <strong>
                  ${escapeRagHtml(
                    result.student ||
                    "Unknown"
                  )}
                </strong>
              </span>

              <span>
                Chunk:
                <strong>
                  ${escapeRagHtml(
                    result.chunk_id ||
                    "Unknown"
                  )}
                </strong>
              </span>

            </div>

            <p class="retrieval-text">
              ${escapeRagHtml(
                result.text ||
                "No text returned."
              )}
            </p>

          </article>
        `
      )
      .join("");

  panel.innerHTML = `
    <div class="tool-result-card">

      <div class="tool-result-header">

        <div>
          <span class="tool-result-eyebrow">
            RAG CORPUS
          </span>

          <h3>
            Knowledge Base Refreshed
          </h3>
        </div>

        <span class="stamp status-active">
          Ready
        </span>

      </div>

      <div class="result-fact-grid">

        <div class="result-fact">
          <span>Chunks Indexed</span>
          <strong>
            ${escapeRagHtml(
              data.chunk_count
            )}
          </strong>
        </div>

        <div class="result-fact">
          <span>Vector Store</span>
          <strong>
            ${escapeRagHtml(
              data.vector_store_status ||
              "Unknown"
            )}
          </strong>
        </div>

        <div class="result-fact">
          <span>Collection</span>
          <strong>
            ${escapeRagHtml(
              data.collection ||
              "Unknown"
            )}
          </strong>
        </div>

      </div>

      ${ragRawJsonBlock(data)}

    </div>
  `;
}


function showRagAnswer(
  panel,
  data
) {
  clearRagPanel(
    panel
  );

  if (
    data.status !== "success"
  ) {
    showRagMessage(
      panel,
      data.error ||
        "RAG request failed.",
      "error-state"
    );

    return;
  }


  const answerHeading =
    document.createElement(
      "strong"
    );

  answerHeading.textContent =
    "Answer";

  panel.appendChild(
    answerHeading
  );


  const answer =
    document.createElement(
      "p"
    );

  answer.textContent =
    data.answer ||
    "No answer returned.";

  panel.appendChild(
    answer
  );


  const confidence =
    document.createElement(
      "p"
    );

  const confidenceLabel =
    document.createElement(
      "strong"
    );

  confidenceLabel.textContent =
    "Confidence: ";

  confidence.appendChild(
    confidenceLabel
  );

  confidence.appendChild(
    document.createTextNode(
      data.confidence_category ||
      "Unknown"
    )
  );

  panel.appendChild(
    confidence
  );


  const citationsHeading =
    document.createElement(
      "strong"
    );

  citationsHeading.textContent =
    "Citations";

  panel.appendChild(
    citationsHeading
  );


  const citations =
    data.citations || [];

  if (
    citations.length === 0
  ) {
    const noCitations =
      document.createElement(
        "p"
      );

    noCitations.textContent =
      "No citations returned.";

    panel.appendChild(
      noCitations
    );

    return;
  }


  const citationList =
    document.createElement(
      "ul"
    );

  citations.forEach(
    citation => {
      const item =
        document.createElement(
          "li"
        );

      const source =
        citation.source_id ||
        citation.chunk_id ||
        "unknown source";

      item.textContent =
        `${source} ` +
        `(${citation.authority_tier || "unknown authority"})`;

      citationList.appendChild(
        item
      );
    }
  );

  panel.appendChild(
    citationList
  );
}


if (
  ragRefreshButton
) {
  ragRefreshButton.addEventListener(
    "click",
    async () => {
      const panel =
        document.getElementById(
          "rag-refresh-result"
        );

      showRagMessage(
        panel,
        "Refreshing shared RAG corpus..."
      );

      ragRefreshButton.disabled =
        true;

      try {
        const data =
          await apiRequest(
            "/rag/refresh",
            {
              method:
                "POST",

              body:
                JSON.stringify({})
            }
          );

        showRagRetrieval(
          panel,
          data
        );

      } catch (error) {
        showRagMessage(
          panel,
          error.message,
          "error-state"
        );

      } finally {
        ragRefreshButton.disabled =
          false;
      }
    }
  );
}


if (
  ragRetrieveForm
) {
  ragRetrieveForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      const panel =
        document.getElementById(
          "rag-retrieve-result"
        );

      const query =
        document
          .getElementById(
            "rag-retrieve-query"
          )
          .value
          .trim();

      const k =
        Number(
          document
            .getElementById(
              "rag-retrieve-k"
            )
            .value
        );

      showRagMessage(
        panel,
        "Retrieving grounded context..."
      );

      try {
        const data =
          await apiRequest(
            "/rag/retrieve",
            {
              method:
                "POST",

              body:
                JSON.stringify(
                  {
                    query,
                    k
                  }
                )
            }
          );

        showRagJson(
          panel,
          data
        );

      } catch (error) {
        showRagMessage(
          panel,
          error.message,
          "error-state"
        );
      }
    }
  );
}


if (
  ragAskForm
) {
  ragAskForm.addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      const panel =
        document.getElementById(
          "rag-ask-result"
        );

      const query =
        document
          .getElementById(
            "rag-ask-query"
          )
          .value
          .trim();

      const k =
        Number(
          document
            .getElementById(
              "rag-ask-k"
            )
            .value
        );

      showRagMessage(
        panel,
        "Retrieving evidence and generating a grounded answer..."
      );

      try {
        const data =
          await apiRequest(
            "/rag/ask",
            {
              method:
                "POST",

              body:
                JSON.stringify(
                  {
                    query,
                    k
                  }
                )
            }
          );

        showRagAnswer(
          panel,
          data
        );

      } catch (error) {
        showRagMessage(
          panel,
          error.message,
          "error-state"
        );
      }
    }
  );
}