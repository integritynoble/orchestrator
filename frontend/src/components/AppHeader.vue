<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo">
        <span class="logo-icon">&#9678;</span>
        <span class="logo-text">Intelligence Orchestrator</span>
        <span class="logo-badge">TARGETING</span>
      </router-link>
    </div>
    <div class="header-right">
      <div v-if="authStore.isLoggedIn" class="user-info">
        <span v-if="authStore.credit !== null" class="balance-badge">
          {{ authStore.credit }} credits
        </span>
        <span class="user-name">{{ authStore.userName }}</span>
        <span class="user-role">{{ authStore.userRole }}</span>
        <button class="btn btn-ghost btn-sm" @click="authStore.logout">Logout</button>
      </div>
      <div v-else class="user-info">
        <button class="btn btn-sm btn-primary" @click="authStore.login">Sign In</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-left { display: flex; align-items: center; }
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--color-text-primary);
}
.logo-icon { font-size: 22px; color: var(--color-accent); }
.logo-text { font-size: 15px; font-weight: 700; letter-spacing: -0.3px; }
.logo-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-accent-bg);
  color: var(--color-accent);
  border: 1px solid rgba(99, 102, 241, 0.2);
}
.header-right { display: flex; align-items: center; gap: 12px; }
.user-info { display: flex; align-items: center; gap: 10px; }
.user-name { font-size: 13px; font-weight: 600; color: var(--color-text-primary); }
.user-role {
  font-size: 11px;
  color: var(--color-text-secondary);
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
}
.balance-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.2);
}
</style>
