const API_BASE_URL = "http://localhost:5002";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType =
    response.headers.get("content-type") || "";

  let data;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    if (
      typeof data === "object" &&
      data !== null
    ) {
      if (data.error) {
        message = data.error;
      } else if (
        Array.isArray(data.errors) &&
        data.errors.length > 0
      ) {
        message = data.errors.join(" ");
      }
    }

    if (
      typeof data === "string" &&
      data.trim()
    ) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        data,
        "text/html"
      );

      const text = doc.body.textContent.trim();

      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return data;
}