const MCP_STORAGE_KEY = "mcpMode";

const mcpModeToggle =
  document.getElementById("mcp-mode-toggle");

const mcpModeStatus =
  document.getElementById("mcp-mode-status");


function getMcpMode() {
  return (
    localStorage.getItem(MCP_STORAGE_KEY) === "on"
      ? "on"
      : "off"
  );
}


function setMcpMode(mode) {
  localStorage.setItem(
    MCP_STORAGE_KEY,
    mode
  );

  if (mcpModeToggle) {
    mcpModeToggle.checked =
      mode === "on";
  }

  if (mcpModeStatus) {
    mcpModeStatus.textContent =
      mode === "on"
        ? "ON"
        : "OFF";
  }
}


if (mcpModeToggle) {
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


document.body.addEventListener(
  "htmx:configRequest",
  event => {
    const element =
      event.detail.elt;

    if (
      element &&
      element.closest("#mcp-tools")
    ) {
      event.detail.headers[
        "X-MCP-Mode"
      ] = getMcpMode();
    }
  }
);


setMcpMode(
  getMcpMode()
);