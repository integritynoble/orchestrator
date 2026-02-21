import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userService, type UserProfile } from '../services/user'
import { config } from '../config'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserProfile | null>(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isLoggedIn = computed(() => isAuthenticated.value && user.value !== null)
  const userName = computed(() => user.value?.user_info?.user_name || 'User')
  const userRole = computed(() => user.value?.user_info?.role || 'user')
  const credit = computed(() => user.value?.balance?.credit ?? null)
  const token = computed(() => user.value?.balance?.token ?? null)

  async function initialize() {
    if (!userService.isAuthenticated()) return
    isLoading.value = true
    error.value = null
    try {
      const result = await userService.validateToken()
      if (result.valid && result.user) {
        user.value = result.user
        isAuthenticated.value = true
      } else {
        userService.clearAccessToken()
        userService.clearCachedUserProfile()
        if (result.require_reauth) {
          error.value = 'Session expired'
        }
      }
    } catch {
      userService.clearAccessToken()
      userService.clearCachedUserProfile()
    } finally {
      isLoading.value = false
    }
  }

  async function handleOAuthCallback(ssoToken: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      const result = await userService.handleOAuthCallback(ssoToken)
      if (result.success && result.user) {
        user.value = result.user
        isAuthenticated.value = true
        return true
      }
      error.value = result.error || 'Authentication failed'
      return false
    } catch (err: any) {
      error.value = err.message || 'Authentication failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  function login() {
    userService.initiateLogin()
  }

  async function logout() {
    await userService.logout()
    user.value = null
    isAuthenticated.value = false
    error.value = null
    window.location.href = config.logoutUrl
  }

  return {
    user, isAuthenticated, isLoading, error,
    isLoggedIn, userName, userRole, credit, token,
    initialize, handleOAuthCallback, login, logout,
  }
})
