<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTargetingStore } from '../stores/targeting'
import { useAuthStore } from '../stores/auth'
import AppHeader from '../components/AppHeader.vue'
import MetricsPanel from '../components/MetricsPanel.vue'
import MaturityPipeline from '../components/MaturityPipeline.vue'
import TargetCard from '../components/TargetCard.vue'
import CreateTargetModal from '../components/CreateTargetModal.vue'
import type { TargetCreatePayload } from '../types'

const router = useRouter()
const store = useTargetingStore()
const authStore = useAuthStore()
const showCreate = ref(false)

onMounted(async () => {
  await Promise.all([store.loadTargets(), store.loadMaturitySummary()])
})

function goToTarget(id: number) {
  router.push(`/target/${id}`)
}

async function handleCreate(payload: TargetCreatePayload) {
  const target = await store.createTarget(payload)
  if (target) {
    showCreate.value = false
  }
}
</script>

<template>
  <div class="dashboard">
    <AppHeader />

    <main class="dashboard-main">
      <!-- Top section: Metrics -->
      <MetricsPanel
        :targets="store.targets"
        :maturity-summary="store.maturitySummary"
      />

      <!-- Maturity Pipeline -->
      <div class="section mt-4">
        <MaturityPipeline
          :targets-by-maturity="store.targetsByMaturity"
          @select-target="goToTarget"
        />
      </div>

      <!-- Target List -->
      <div class="section mt-4">
        <div class="section-header">
          <div>
            <h3 class="section-title">Intelligence Targets</h3>
            <p class="text-sm text-secondary">{{ store.totalTargets }} targets defined</p>
          </div>
          <div class="flex gap-2">
            <select v-model="store.filterStatus" class="select" style="width:140px" @change="store.loadTargets()">
              <option :value="null">All statuses</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
            <button v-if="authStore.isLoggedIn" class="btn btn-primary" @click="showCreate = true">
              + New Target
            </button>
          </div>
        </div>

        <div v-if="store.isLoading" class="loading-state">Loading targets...</div>

        <div v-else-if="store.targets.length === 0" class="empty-state">
          <div class="empty-icon">&#9678;</div>
          <h4>No targets defined yet</h4>
          <p class="text-sm text-secondary">
            Create your first intelligence target to start the SolveEverything maturity pipeline.
          </p>
          <button v-if="authStore.isLoggedIn" class="btn btn-primary mt-4" @click="showCreate = true">
            + Create First Target
          </button>
          <button v-else class="btn btn-primary mt-4" @click="authStore.login">
            Sign In to Get Started
          </button>
        </div>

        <div v-else class="target-grid">
          <TargetCard
            v-for="target in store.targets"
            :key="target.id"
            :target="target"
            @select="goToTarget"
          />
        </div>

        <!-- Sign-in prompt for unauthenticated users -->
        <div v-if="!authStore.isLoggedIn && store.targets.length > 0" class="auth-prompt">
          <button class="btn btn-primary" @click="authStore.login">
            Sign In to manage your own targets
          </button>
        </div>
      </div>
    </main>

    <CreateTargetModal
      v-if="showCreate"
      @close="showCreate = false"
      @create="handleCreate"
    />
  </div>
</template>

<style scoped>
.dashboard { min-height: 100vh; }

.dashboard-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.section { }
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-title { font-size: 16px; font-weight: 700; }

.target-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 60px 20px;
}
.empty-icon {
  font-size: 48px;
  color: var(--color-accent);
  margin-bottom: 12px;
}
.empty-state h4 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}

.auth-prompt {
  text-align: center;
  padding: 20px;
  margin-top: 24px;
  border-top: 1px solid var(--color-border);
}
</style>
