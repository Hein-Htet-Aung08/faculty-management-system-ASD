// Default for local dev and docker-compose. In Docker, the container overwrites
// this file at startup when the API_BASE env var is set (see docker-entrypoint).
window.APP_CONFIG = { API_BASE: "http://127.0.0.1:5001" };
