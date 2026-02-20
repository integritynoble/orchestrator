/**
 * API service — mirrors CompareGPT pattern.
 * Auto-injects Bearer token, handles errors.
 */

const API_BASE = '/api'
const ACCESS_TOKEN_KEY = 'access_token'

function getHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...extra }
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

async function request<T>(method: string, endpoint: string, body?: unknown): Promise<T> {
  const opts: RequestInit = { method, headers: getHeaders() }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(`${API_BASE}${endpoint}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export const api = {
  get: <T>(ep: string) => request<T>('GET', ep),
  post: <T>(ep: string, data?: unknown) => request<T>('POST', ep, data),
  put: <T>(ep: string, data?: unknown) => request<T>('PUT', ep, data),
  del: <T>(ep: string) => request<T>('DELETE', ep),
}

export function setToken(token: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

export function hasToken(): boolean {
  return !!localStorage.getItem(ACCESS_TOKEN_KEY)
}
