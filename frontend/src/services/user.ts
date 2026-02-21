/**
 * UserService — matches CompareGPT-AIScientist auth pattern exactly.
 */

import { config } from '../config'

const ACCESS_TOKEN_KEY = 'access_token'
const USER_PROFILE_KEY = 'user_profile'
const API_BASE = '/api'

export interface UserProfile {
  user_info: {
    user_id: number
    user_name: string | null
    role: string | null
  }
  balance?: {
    credit: number | null
    token: number | null
  }
  api_key?: string
}

function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

function setAccessToken(token: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

function getCachedUserProfile(): UserProfile | null {
  const raw = localStorage.getItem(USER_PROFILE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function setCachedUserProfile(profile: UserProfile) {
  localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(profile))
}

function clearCachedUserProfile() {
  localStorage.removeItem(USER_PROFILE_KEY)
}

function isAuthenticated(): boolean {
  return !!getAccessToken()
}

function initiateLogin() {
  window.location.href = config.ssoUrl
}

async function handleOAuthCallback(ssoToken: string): Promise<{ success: boolean; user?: UserProfile; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/user/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sso_token: ssoToken }),
    })
    const data = await res.json()
    if (data.success && data.access_token && data.user) {
      setAccessToken(data.access_token)
      setCachedUserProfile(data.user)
      return { success: true, user: data.user }
    }
    return { success: false, error: data.message || 'Authentication failed' }
  } catch (err: any) {
    return { success: false, error: err.message || 'Network error' }
  }
}

async function validateToken(): Promise<{ valid: boolean; user?: UserProfile; require_reauth?: boolean }> {
  const token = getAccessToken()
  if (!token) return { valid: false }
  try {
    const res = await fetch(`${API_BASE}/user/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    })
    const data = await res.json()
    if (data.valid && data.user) {
      setCachedUserProfile(data.user)
      return { valid: true, user: data.user }
    }
    if (data.require_reauth) {
      clearAccessToken()
      clearCachedUserProfile()
      return { valid: false, require_reauth: true }
    }
    return { valid: false }
  } catch {
    return { valid: false }
  }
}

async function logout(): Promise<void> {
  const token = getAccessToken()
  if (token) {
    try {
      await fetch(`${API_BASE}/user/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      })
    } catch {
      /* best effort */
    }
  }
  clearAccessToken()
  clearCachedUserProfile()
}

export const userService = {
  getAccessToken,
  setAccessToken,
  clearAccessToken,
  getCachedUserProfile,
  setCachedUserProfile,
  clearCachedUserProfile,
  isAuthenticated,
  initiateLogin,
  handleOAuthCallback,
  validateToken,
  logout,
}
