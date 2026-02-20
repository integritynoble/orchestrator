<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

onMounted(async () => {
  const ssoToken = (route.query.token as string) || (route.query.sso_token as string)
  if (ssoToken) {
    const ok = await authStore.handleSSOCallback(ssoToken)
    if (ok) {
      router.replace('/')
      return
    }
  }
  router.replace('/')
})
</script>

<template>
  <div class="callback-page">
    <div class="spinner">Authenticating...</div>
  </div>
</template>

<style scoped>
.callback-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: var(--color-text-secondary);
}
</style>
