<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const status = ref<'loading' | 'error'>('loading')
const errorMessage = ref('')
let timeoutId: ReturnType<typeof setTimeout> | null = null

onMounted(async () => {
  // Safety timeout — 15s
  timeoutId = setTimeout(() => {
    if (status.value === 'loading') {
      status.value = 'error'
      errorMessage.value = 'Authentication timed out. Please try again.'
    }
  }, 15000)

  // Check for error from SSO
  if (route.query.error) {
    status.value = 'error'
    errorMessage.value = (route.query.error as string) || 'SSO returned an error'
    return
  }

  const ssoToken = (route.query.token as string) || (route.query.access_token as string)
  if (!ssoToken) {
    status.value = 'error'
    errorMessage.value = 'No authentication token received'
    return
  }

  const ok = await authStore.handleOAuthCallback(ssoToken)
  if (ok) {
    router.replace('/')
  } else {
    status.value = 'error'
    errorMessage.value = authStore.error || 'Authentication failed'
  }
})

onUnmounted(() => {
  if (timeoutId) clearTimeout(timeoutId)
})

function retry() {
  authStore.login()
}
</script>

<template>
  <div class="callback-page">
    <div v-if="status === 'loading'" class="callback-card">
      <div class="spinner-ring"></div>
      <p class="callback-text">Authenticating...</p>
    </div>
    <div v-else class="callback-card error">
      <div class="error-icon">!</div>
      <p class="callback-text">{{ errorMessage }}</p>
      <button class="btn btn-primary" @click="retry">Try Again</button>
    </div>
  </div>
</template>

<style scoped>
.callback-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--color-bg-primary);
}
.callback-card {
  text-align: center;
  padding: 48px;
  border-radius: 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  min-width: 320px;
}
.callback-text {
  margin-top: 16px;
  color: var(--color-text-secondary);
  font-size: 14px;
}
.spinner-ring {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
.error .callback-text { color: #ef4444; }
.btn {
  margin-top: 20px;
  padding: 8px 24px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}
.btn-primary {
  background: var(--color-accent);
  color: white;
}
.btn-primary:hover { opacity: 0.9; }
</style>
