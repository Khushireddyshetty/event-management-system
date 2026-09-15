/**
 * Axios instance pre-configured to point at the Flask backend.
 * All API calls use /api prefix so Vite dev-server proxy forwards them.
 */
import axios from "axios";

const API = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Global response error handler
API.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.error ||
      err.response?.data?.message ||
      err.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(msg));
  }
);

export default API;
