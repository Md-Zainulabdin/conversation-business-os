const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail || res.statusText,
      res.status
    );
  }

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
