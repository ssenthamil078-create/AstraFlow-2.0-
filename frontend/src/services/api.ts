/**
 * Base API Client for AstraFlow
 */

// In production (Vercel), the frontend and backend are on different domains,
// so every request needs an absolute URL. Set VITE_API_BASE_URL in Vercel's
// project settings to the Render backend's URL (e.g. https://astraflow-api.onrender.com).
// Left empty, requests stay relative — which only works when something
// (like the Vite dev proxy) sits in front of both on the same origin.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

function resolveUrl(endpoint: string): string {
  if (/^https?:\/\//i.test(endpoint)) return endpoint;
  return `${API_BASE_URL}${endpoint}`;
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const token = typeof window !== 'undefined' ? localStorage.getItem('astra_token') : null;
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(resolveUrl(endpoint), {
    ...options,
    headers,
  });

  if (!response.ok) {
    // Read body once as text, then try to parse as JSON
    let errorData: any;
    const rawText = await response.text();
    try {
      errorData = JSON.parse(rawText);
    } catch {
      errorData = rawText;
    }

    // 401 = token expired or user doesn't exist in DB (e.g. after DB switch)
    // Clear the stale token and redirect to login
    if (response.status === 401) {
      const isAuthEndpoint = endpoint.includes('/api/auth/login') || endpoint.includes('/api/auth/register');
      if (!isAuthEndpoint) {
        localStorage.removeItem('astra_token');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }

    const message = errorData?.detail || errorData?.error || errorData?.message || `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, errorData);
  }

  return response.json();
}
