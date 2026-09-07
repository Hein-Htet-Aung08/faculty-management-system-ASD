const BACKEND = window.BACKEND_URL || "http://localhost:5003";

function value(elementId) {
    const element = document.getElementById(elementId);
    return element ? element.value.trim() : "";
}

function show(panelId) {
    document.getElementById(panelId).hidden = false;
}

function message(panelId, text, kind = "warn") {
    const css = kind === "info" ? "empty-state" : "error-state";
    document.getElementById(panelId).innerHTML = `<p class="${css}">${text}</p>`;
}

async function render(panelId, url, options = {}) {
    const panel = document.getElementById(panelId);

    try {
        const response = await fetch(url, options);
        panel.innerHTML = await response.text();
    } catch (error) {
        panel.innerHTML =
            `<p class="error-state">Request failed. Is the backend running at ` +
            `${BACKEND}?</p><pre>${error}</pre>`;
    }
}
