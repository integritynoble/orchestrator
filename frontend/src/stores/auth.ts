import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, setToken, clearToken, hasToken } from '../services/api'
import type { User, UserInfo } from '../types'

const SSO_LOGIN_URL = 'https://comparegpt.io/sso/login'
const SSO_LOGOUT_URL = 'https://comparegpt.io/sso/logout'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(false)

  const isLoggedIn = computed(() => isAuthenticated.value && user.value !== null)

  async function initialize() {
    if (!hasToken()) return
    isLoading.value = true
    try {
      const res = await api.post<{ success: boolean; valid: boolean; user?: User }>('/user/validate', {})
      if (res.valid && res.user) {
        user.value = res.user.user_info
        isAuthenticated.value = true
      } else {
        clearToken()
      }
    } catch {
      clearToken()
    } finally {
      isLoading.value = false
    }
  }

  async function handleSSOCallback(ssoToken: string) {
    isLoading.value = true
    try {
      const res = await api.post<{ success: boolean; access_token?: string; user?: User }>(
        '/user/validate',
        { sso_token: ssoToken },
      )
      if (res.success && res.access_token && res.user) {
        setToken(res.access_token)
        user.value = res.user.user_info
        isAuthenticated.value = true
        return true
      }
    } catch {
      /* noop */
    } finally {
      isLoading.value = false
    }
    return false
  }

  function login() {
    const redirect = encodeURIComponent(window.location.origin + '/sso/callback')
    window.location.href = `${SSO_LOGIN_URL}?redirect=${redirect}`
  }

  function logout() {
    clearToken()
    user.value = null
    isAuthenticated.value = false
    window.location.href = SSO_LOGOUT_URL
  }

  return { user, isAuthenticated, isLoading, isLoggedIn, initialize, handleSSOCallback, login, logout }
})
