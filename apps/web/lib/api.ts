const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const isForm = options.body instanceof FormData;
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem("token");
      document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    const body = await res.json().catch(() => ({}));
    const detail =
      body && typeof body === "object" && "detail" in body ? body.detail : undefined;
    throw new ApiError(
      typeof detail === "string" ? detail : res.statusText,
      res.status,
      detail
    );
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get<T>(path: string) {
    return request<T>(path);
  },
  post<T>(path: string, body: unknown) {
    return request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  postForm<T>(path: string, form: FormData) {
    return request<T>(path, {
      method: "POST",
      body: form,
    });
  },
  put<T>(path: string, body: unknown) {
    return request<T>(path, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },
  delete<T = void>(path: string) {
    return request<T>(path, { method: "DELETE" });
  },
};
