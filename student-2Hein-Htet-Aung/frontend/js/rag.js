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


function showRagJson(
  panel,
  data
) {
  clearRagPanel(
    panel
  );

  const pre =
    document.createElement(
      "pre"
    );

  pre.textContent =
    JSON.stringify(
      data,
      null,
      2
    );

  pre.style.whiteSpace =
    "pre-wrap";

  pre.style.overflowWrap =
    "anywhere";

  panel.appendChild(
    pre
  );
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