export const DEFAULT_BASE = "";

export function getStoredToken(): string {
  return localStorage.getItem("pixelDeckToken") || "";
}

export function storeToken(token: string): void {
  localStorage.setItem("pixelDeckToken", token);
}

type ApiOptions = {
  method?: string;
  body?: BodyInit | Record<string, unknown> | null;
  token?: string;
  query?: Record<string, string | number | boolean | undefined | null>;
};

type UploadOptions = {
  method?: string;
  token?: string;
  query?: Record<string, string | number | boolean | undefined | null>;
  onProgress?: (progress: number) => void;
};

function appendQuery(url: URL, query?: ApiOptions["query"]): void {
  if (!query) {
    return;
  }
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
}

function isBinaryBody(body: unknown): body is BodyInit {
  return body instanceof FormData || body instanceof Blob || body instanceof ArrayBuffer || ArrayBuffer.isView(body);
}

export async function apiRequest<T = unknown>(
  path: string,
  { method = "GET", body, token, query }: ApiOptions = {},
): Promise<T> {
  const url = new URL(`${DEFAULT_BASE}${path}`, window.location.origin);
  appendQuery(url, query);

  const headers: Record<string, string> = {};
  if (token) {
    headers["X-API-Token"] = token;
  }

  const payload = body;
  if (payload && !isBinaryBody(payload)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    body: isBinaryBody(payload) ? payload : payload ? JSON.stringify(payload) : undefined,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }
  return (await response.text()) as T;
}

export function uploadFile<T = unknown>(
  path: string,
  file: File,
  { method = "POST", token, query, onProgress }: UploadOptions = {},
): Promise<T> {
  const url = new URL(`${DEFAULT_BASE}${path}`, window.location.origin);
  appendQuery(url, query);

  return new Promise<T>((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open(method, url.toString(), true);

    if (token) {
      request.setRequestHeader("X-API-Token", token);
    }

    request.responseType = "text";
    request.onload = () => {
      if (request.status < 200 || request.status >= 300) {
        reject(new Error(request.responseText || `Request failed (${request.status})`));
        return;
      }

      const contentType = request.getResponseHeader("content-type") || "";
      const responseText = request.responseText || "";
      if (contentType.includes("application/json")) {
        try {
          resolve(JSON.parse(responseText) as T);
        } catch (error) {
          reject(error);
        }
        return;
      }

      resolve(responseText as T);
    };
    request.onerror = () => reject(new Error("Network error"));

    if (request.upload && onProgress) {
      request.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
    }

    const formData = new FormData();
    formData.append("file", file);
    request.send(formData);
  });
}


