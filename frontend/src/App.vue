<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.initialize()
})
</script>

<template>
  <div id="app-root">
    <RouterView />
  </div>
</template>

<style scoped>
#app-root {
  min-height: 100vh;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}
</style>
