<script setup lang="ts">
import { computed } from 'vue'
import type { Target } from '../types'
import { MATURITY_LEVELS } from '../types'

const props = defineProps<{ target: Target }>()
const emit = defineEmits<{
  select: [id: number]
  updateMaturity: [id: number, level: number]
}>()

const maturity = computed(() => MATURITY_LEVELS[props.target.maturity_level] || MATURITY_LEVELS[0])

const scorePercent = computed(() => {
  const t = props.target
  if (t.current_score == null || t.target_score == null || t.target_score === 0) return 0
  return Math.min(100, Math.round((t.current_score / t.target_score) * 100))
})
</script>

<template>
  <div class="card target-card" @click="emit('select', target.id)">
    <div class="card-header">
      <h4 class="target-title truncate">{{ target.title }}</h4>
      <span class="tag" :class="`tag-${target.status}`">{{ target.status }}</span>
    </div>

    <p v-if="target.description" class="target-desc text-sm text-secondary">
      {{ target.description }}
    </p>

    <div class="target-meta flex items-center gap-2 mt-2">
      <span class="tag" :class="`tag-l${target.maturity_level}`">
        {{ maturity.label }}
      </span>
      <span class="tag" :class="`tag-${target.priority}`">
        {{ target.priority }}
      </span>
      <span v-if="target.domain" class="text-xs text-muted">{{ target.domain }}</span>
    </div>

    <div v-if="target.target_score != null" class="score-section mt-4">
      <div class="flex justify-between items-center mb-2">
        <span class="text-xs text-secondary">Progress</span>
        <span class="text-xs font-mono">
          {{ target.current_score ?? 0 }} / {{ target.target_score }}
          <span class="text-muted">({{ scorePercent }}%)</span>
        </span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: scorePercent + '%', background: maturity.color }"></div>
      </div>
    </div>

    <div v-if="target.tags.length" class="target-tags flex gap-1 mt-2">
      <span v-for="tag in target.tags" :key="tag" class="text-xs text-muted">#{{ tag }}</span>
    </div>

    <div v-if="target.benchmarks.length" class="benchmarks mt-4">
      <div class="text-xs text-secondary mb-2">Benchmarks</div>
      <div class="bench-list">
        <div v-for="b in target.benchmarks" :key="b.id" class="bench-item">
          <span class="bench-name text-xs">{{ b.name }}</span>
          <span class="bench-value text-xs font-mono">
            {{ b.current_value ?? '—' }}{{ b.unit ? ` ${b.unit}` : '' }}
            <span v-if="b.target_value != null" class="text-muted">
              / {{ b.target_value }}{{ b.unit ? ` ${b.unit}` : '' }}
            </span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.target-card { cursor: pointer; }
.target-title { font-size: 15px; font-weight: 600; }
.target-desc {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-top: 6px;
}
.score-section { padding-top: 4px; }
.bench-list { display: flex; flex-direction: column; gap: 4px; }
.bench-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: var(--color-bg-primary);
  border-radius: var(--radius-sm);
}
.bench-name { font-weight: 500; }
</style>
