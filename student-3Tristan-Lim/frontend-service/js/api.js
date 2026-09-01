const BACKEND = window.BACKEND_URL || "http://localhost:5301";

function value(elementId) {
    const element = document.getElementById(elementId);
    return element ? element.value.trim() : "";
}

function show(panelId) {
    document.getElementById(panelId).classList.remove("is-hidden");
}

function message(panelId, text, kind = "warn") {
    document.getElementById(panelId).innerHTML =
        `<p class="msg msg-${kind}">${text}</p>`;
}

async function render(panelId, url, options = {}) {
    const panel = document.getElementById(panelId);

    try {
        const response = await fetch(url, options);
        panel.innerHTML = await response.text();
    } catch (error) {
        panel.innerHTML =
            `<p class="msg msg-error">Request failed. Is the backend running at ` +
            `${BACKEND}?</p><pre>${error}</pre>`;
    }
}
