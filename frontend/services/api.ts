import Constants from "expo-constants";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = (Constants.expoConfig?.extra?.apiUrl as string) ?? "http://localhost:8000";

const TOKEN_KEY = "soft-life-access-token";
const REQUEST_TIMEOUT_MS = 15000;
const RETRYABLE_METHODS = new Set(["GET"]);
const MAX_RETRIES = 2;

// expo-secure-store has no web implementation (there's no OS keychain to use
// in a browser) — fall back to AsyncStorage there, same as most Expo
// universal apps. Native platforms (the ones that actually ship to users)
// always get the real Keychain/Keystore-backed storage.
const tokenStore =
  Platform.OS === "web"
    ? { getItem: () => AsyncStorage.getItem(TOKEN_KEY), setItem: (v: string) => AsyncStorage.setItem(TOKEN_KEY, v), deleteItem: () => AsyncStorage.removeItem(TOKEN_KEY) }
    : { getItem: () => SecureStore.getItemAsync(TOKEN_KEY), setItem: (v: string) => SecureStore.setItemAsync(TOKEN_KEY, v), deleteItem: () => SecureStore.deleteItemAsync(TOKEN_KEY) };

export class ApiError extends Error {
  status: number;
  code: "http" | "timeout" | "offline" | "cancelled";

  constructor(message: string, status: number, code: ApiError["code"]) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export async function getToken(): Promise<string | null> {
  return tokenStore.getItem();
}

export async function setToken(token: string | null): Promise<void> {
  if (token) {
    await tokenStore.setItem(token);
  } else {
    await tokenStore.deleteItem();
  }
}

// Set by AuthContext so a 401 on any request can clear local session state,
// without api.ts importing AuthContext (which imports api.ts) and creating
// a circular dependency.
let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

function devLog(method: string, path: string, status: number | "error", detail?: unknown) {
  if (!__DEV__) return;
  // Never log request bodies (passwords, tokens) or auth headers — only the
  // method/path/outcome, which is enough to debug from the Metro console.
  console.log(`[api] ${method} ${path} -> ${status}`, detail ?? "");
}

function redactError(message: string): string {
  return message.replace(/Bearer\s+\S+/gi, "Bearer [redacted]");
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((e: { msg?: string }) => e.msg).filter(Boolean).join(" ") || `Request failed (${response.status})`;
    }
    return `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
  /** Set false to disable the default retry-on-GET-failure behavior for a call that shouldn't retry. */
  retry?: boolean;
};

async function performFetch(url: string, init: RequestInit, timeoutMs = REQUEST_TIMEOUT_MS): Promise<Response> {
  const timeoutController = new AbortController();
  const timeout = setTimeout(() => timeoutController.abort(), timeoutMs);

  // Combine the caller's signal (if any) with our own timeout signal.
  const externalSignal = init.signal;
  const onExternalAbort = () => timeoutController.abort();
  externalSignal?.addEventListener("abort", onExternalAbort);

  try {
    return await fetch(url, { ...init, signal: timeoutController.signal });
  } catch (error) {
    if (externalSignal?.aborted) {
      throw new ApiError("Request cancelled", 0, "cancelled");
    }
    if (timeoutController.signal.aborted) {
      throw new ApiError("That took longer than expected. Please try again.", 0, "timeout");
    }
    throw new ApiError("You're offline — check your connection and try again.", 0, "offline");
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", onExternalAbort);
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, signal, retry = true } = options;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const shouldRetry = retry && RETRYABLE_METHODS.has(method);
  const maxAttempts = shouldRetry ? MAX_RETRIES + 1 : 1;

  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await performFetch(`${API_URL}${path}`, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
      });

      if (!response.ok) {
        const detail = await parseErrorDetail(response);
        devLog(method, path, response.status, detail);

        if (response.status === 401 && auth) {
          await setToken(null);
          onUnauthorized?.();
        }

        // Retry transient server errors on safe GETs; never retry 4xx (the
        // request itself is the problem, retrying won't help).
        if (shouldRetry && response.status >= 500 && attempt < maxAttempts) {
          lastError = new ApiError(redactError(detail), response.status, "http");
          continue;
        }

        throw new ApiError(redactError(detail), response.status, "http");
      }

      devLog(method, path, response.status);
      if (response.status === 204) return undefined as T;
      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof ApiError) {
        const retryableNetworkError = error.code === "offline" || error.code === "timeout";
        if (shouldRetry && retryableNetworkError && attempt < maxAttempts) {
          lastError = error;
          continue;
        }
        devLog(method, path, "error", error.message);
        throw error;
      }
      throw error;
    }
  }

  throw lastError instanceof Error ? lastError : new ApiError("Request failed", 0, "http");
}

export async function apiUpload<T>(
  path: string,
  fileUri: string,
  fieldName = "photo",
  extraFields?: Record<string, string>
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const filename = fileUri.split("/").pop() || "photo.jpg";
  const match = /\.(\w+)$/.exec(filename);
  const ext = match ? match[1].toLowerCase() : "jpg";
  const mimeType = ext === "png" ? "image/png" : "image/jpeg";

  const formData = new FormData();
  formData.append(fieldName, { uri: fileUri, name: filename, type: mimeType } as unknown as Blob);
  if (extraFields) {
    Object.entries(extraFields).forEach(([key, value]) => formData.append(key, value));
  }

  // Uploads get a longer timeout (photo analysis can take a few seconds) and
  // are never retried automatically — resubmitting a large form body on a
  // flaky connection does more harm than good; the caller decides.
  const response = await performFetch(`${API_URL}${path}`, { method: "POST", headers, body: formData }, 30000);

  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    devLog("POST", path, response.status, detail);
    if (response.status === 401) {
      await setToken(null);
      onUnauthorized?.();
    }
    throw new ApiError(redactError(detail), response.status, "http");
  }

  devLog("POST", path, response.status);
  return response.json() as Promise<T>;
}

export { API_URL };
