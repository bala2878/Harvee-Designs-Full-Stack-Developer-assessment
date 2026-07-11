// Replaced at build time in production via docker build ARG API_BASE_URL
// (see frontend/Dockerfile). For local `ng serve`, this default targets the
// dockerized backend on localhost:8000.
export const environment = {
  production: false,
  apiBaseUrl: "http://localhost:8000/api/v1",
};
