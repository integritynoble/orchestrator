<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTargetingStore } from '../stores/targeting'
import AppHeader from '../components/AppHeader.vue'
import { MATURITY_LEVELS, PRIORITY_OPTIONS, STATUS_OPTIONS } from '../types'

const route = useRoute()
const router = useRouter()
const store = useTargetingStore()

const editing = ref(false)
const editForm = ref<Record<string, any>>({})
const confirmDelete = ref(false)

const target = computed(() => store.selectedTarget)
const maturity = computed(() => {
  if (!target.value) return MATURITY_LEVELS[0]
  return MATURITY_LEVELS[target.value.maturity_level] || MATURITY_LEVELS[0]
})

const scorePercent = computed(() => {
  const t = target.value
  if (!t || t.current_score == null || t.target_score == null || t.target_score === 0) return 0
  return Math.min(100, Math.round((t.current_score / t.target_score) * 100))
})

onMounted(async () => {
  const id = Number(route.params.id)
  await store.selectTarget(id)
})

function startEdit() {
  if (!target.value) return
  editForm.value = {
    title: target.value.title,
    description: target.value.description || '',
    domain: target.value.domain || '',
    maturity_level: target.value.maturity_level,
    status: target.value.status,
    priority: target.value.priority,
    benchmark_definition: target.value.benchmark_definition || '',
    success_criteria: target.value.success_criteria || '',
    current_score: target.value.current_score,
    target_score: target.value.target_score,
  }
  editing.value = true
}

async function saveEdit() {
  if (!target.value) return
  const ok = await store.updateTarget(target.value.id, editForm.value)
  if (ok) {
    editing.value = false
    await store.selectTarget(target.value.id)
  }
}

async function advanceMaturity() {
  if (!target.value || target.value.maturity_level >= 5) return
  await store.updateTarget(target.value.id, { maturity_level: target.value.maturity_level + 1 })
  await store.selectTarget(target.value.id)
}

async function handleDelete() {
  if (!target.value) return
  await store.deleteTarget(target.value.id)
  router.push('/')
}
</script>

<template>
  <div class="detail-page">
    <AppHeader />

    <main class="detail-main">
      <div class="back-row">
        <button class="btn btn-ghost btn-sm" @click="router.push('/')">
          &larr; Back to Dashboard
        </button>
      </div>

      <div v-if="!target" class="loading-state">Loading...</div>

      <template v-else>
        <!-- Header card -->
        <div class="detail-header card">
          <div class="flex justify-between items-center">
            <div>
              <h1 class="detail-title">{{ target.title }}</h1>
              <div class="flex gap-2 mt-2">
                <span class="tag" :class="`tag-l${target.maturity_level}`">{{ maturity.label }}</span>
                <span class="tag" :class="`tag-${target.status}`">{{ target.status }}</span>
                <span class="tag" :class="`tag-${target.priority}`">{{ target.priority }}</span>
                <span v-if="target.domain" class="tag" style="background:var(--color-bg-primary);color:var(--color-text-secondary);">
                  {{ target.domain }}
                </span>
              </div>
            </div>
            <div class="flex gap-2">
              <button
                v-if="target.maturity_level < 5 && target.status === 'active'"
                class="btn btn-sm"
                @click="advanceMaturity"
              >
                Advance to L{{ target.maturity_level + 1 }}
              </button>
              <button class="btn btn-sm" @click="startEdit">Edit</button>
              <button class="btn btn-sm btn-danger" @click="confirmDelete = true">Delete</button>
            </div>
          </div>

          <p v-if="target.description" class="text-secondary mt-4">{{ target.description }}</p>

          <!-- Progress -->
          <div v-if="target.target_score != null" class="mt-4">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm text-secondary">Score Progress</span>
              <span class="font-mono text-sm">
                {{ target.current_score ?? 0 }} / {{ target.target_score }}
                ({{ scorePercent }}%)
              </span>
            </div>
            <div class="progress-bar" style="height:8px;">
              <div
                class="progress-fill"
                :style="{ width: scorePercent + '%', background: maturity.color }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Detail grid -->
        <div class="detail-grid mt-4">
          <!-- Benchmark Definition -->
          <div class="card">
            <h3 class="card-section-title">Benchmark Definition</h3>
            <p class="text-sm text-secondary" style="white-space:pre-wrap;">
              {{ target.benchmark_definition || 'No benchmark definition set.' }}
            </p>
          </div>

          <!-- Success Criteria -->
          <div class="card">
            <h3 class="card-section-title">Success Criteria</h3>
            <p class="text-sm text-secondary" style="white-space:pre-wrap;">
              {{ target.success_criteria || 'No success criteria set.' }}
            </p>
          </div>

          <!-- Benchmarks -->
          <div class="card">
            <h3 class="card-section-title">Benchmarks ({{ target.benchmarks.length }})</h3>
            <div v-if="target.benchmarks.length === 0" class="text-sm text-muted">No benchmarks recorded.</div>
            <div v-for="b in target.benchmarks" :key="b.id" class="bench-row">
              <div>
                <div class="text-sm font-mono">{{ b.name }}</div>
                <div class="text-xs text-muted">{{ b.metric_type }}</div>
              </div>
              <div class="text-right">
                <div class="font-mono text-sm">{{ b.current_value ?? '—' }} {{ b.unit || '' }}</div>
                <div v-if="b.target_value != null" class="text-xs text-muted">
                  Target: {{ b.target_value }} {{ b.unit || '' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Resources -->
          <div class="card">
            <h3 class="card-section-title">Resources ({{ target.resources.length }})</h3>
            <div v-if="target.resources.length === 0" class="text-sm text-muted">No resources allocated.</div>
            <div v-for="r in target.resources" :key="r.id" class="resource-row">
              <div class="text-sm">{{ r.resource_type }}</div>
              <div class="resource-bar-wrapper">
                <div class="progress-bar" style="height:6px;">
                  <div
                    class="progress-fill"
                    :style="{ width: r.allocated > 0 ? (r.consumed / r.allocated * 100) + '%' : '0%' }"
                  ></div>
                </div>
              </div>
              <div class="text-xs font-mono text-right">
                {{ r.consumed }} / {{ r.allocated }} {{ r.unit || '' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div v-if="target.tags.length" class="flex gap-2 mt-4">
          <span v-for="tag in target.tags" :key="tag" class="tag tag-active">#{{ tag }}</span>
        </div>

        <div class="text-xs text-muted mt-4">
          Created: {{ target.created_at }} | Updated: {{ target.updated_at }}
        </div>
      </template>

      <!-- Edit modal -->
      <div v-if="editing" class="modal-overlay" @click.self="editing = false">
        <div class="modal-content">
          <h3 class="modal-title">Edit Target</h3>
          <div class="form-group">
            <label class="form-label">Title</label>
            <input v-model="editForm.title" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea v-model="editForm.description" class="textarea" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Status</label>
              <select v-model="editForm.status" class="select">
                <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Priority</label>
              <select v-model="editForm.priority" class="select">
                <option v-for="p in PRIORITY_OPTIONS" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Maturity Level</label>
            <select v-model.number="editForm.maturity_level" class="select">
              <option v-for="(meta, lvl) in MATURITY_LEVELS" :key="lvl" :value="Number(lvl)">
                {{ meta.label }}
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Current Score</label>
              <input v-model.number="editForm.current_score" type="number" class="input" />
            </div>
            <div class="form-group">
              <label class="form-label">Target Score</label>
              <input v-model.number="editForm.target_score" type="number" class="input" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Benchmark Definition</label>
            <textarea v-model="editForm.benchmark_definition" class="textarea" />
          </div>
          <div class="form-group">
            <label class="form-label">Success Criteria</label>
            <textarea v-model="editForm.success_criteria" class="textarea" />
          </div>
          <div class="modal-actions">
            <button class="btn" @click="editing = false">Cancel</button>
            <button class="btn btn-primary" @click="saveEdit">Save Changes</button>
          </div>
        </div>
      </div>

      <!-- Delete confirmation -->
      <div v-if="confirmDelete" class="modal-overlay" @click.self="confirmDelete = false">
        <div class="modal-content" style="max-width:400px;">
          <h3 class="modal-title">Delete Target?</h3>
          <p class="text-secondary">This action cannot be undone. All benchmarks and resources will be removed.</p>
          <div class="modal-actions">
            <button class="btn" @click="confirmDelete = false">Cancel</button>
            <button class="btn btn-danger" @click="handleDelete">Delete</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.detail-page { min-height: 100vh; }
.detail-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}
.back-row { margin-bottom: 16px; }
.detail-title { font-size: 24px; font-weight: 800; }
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 768px) { .detail-grid { grid-template-columns: 1fr; } }

.card-section-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}
.bench-row, .resource-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: var(--color-bg-primary);
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
}
.resource-row {
  display: grid;
  grid-template-columns: 80px 1fr 90px;
  gap: 10px;
  align-items: center;
}
.resource-bar-wrapper { flex: 1; }
.text-right { text-align: right; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.loading-state { text-align: center; padding: 60px; color: var(--color-text-muted); }
</style>
