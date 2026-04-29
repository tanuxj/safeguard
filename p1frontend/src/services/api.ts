import axios from "axios";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setAccessToken,
} from "./authStorage";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

const refreshClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

let refreshPromise: Promise<string | null> | null = null;

async function requestNewAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  refreshPromise = refreshClient
    .post("/auth/refresh", {
      refresh_token: refreshToken,
    })
    .then((res) => {
      const newAccessToken = res.data?.access_token as string | undefined;
      if (!newAccessToken) {
        clearTokens();
        return null;
      }
      setAccessToken(newAccessToken);
      return newAccessToken;
    })
    .catch(() => {
      clearTokens();
      return null;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

export async function bootstrapAuthSession(): Promise<void> {
  if (!getAccessToken() && getRefreshToken()) {
    await requestNewAccessToken();
  }
}

API.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

API.interceptors.response.use(
  async (response) => {
    const originalRequest = response.config as
      | ({ _retry?: boolean } & {
          headers: Record<string, string>;
        })
      | undefined;

    if (!originalRequest) {
      return response;
    }

    const message =
      typeof response.data?.message === "string"
        ? response.data.message.toLowerCase()
        : "";

    // Some backend routes currently return 200 with "unauthorized".
    // Treat it like auth failure and retry once after refresh.
    if (message === "unauthorized" && !originalRequest._retry) {
      originalRequest._retry = true;
      const newAccessToken = await requestNewAccessToken();

      if (newAccessToken) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return API(originalRequest);
      }
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config as
      | ({ _retry?: boolean } & {
          headers: Record<string, string>;
        })
      | undefined;
    const status = error.response?.status as number | undefined;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const newAccessToken = await requestNewAccessToken();

      if (newAccessToken) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return API(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export default API;