<script setup lang="ts">
import { computed } from 'vue'
import { MATURITY_LEVELS } from '../types'
import type { Target } from '../types'

const props = defineProps<{
  targetsByMaturity: Record<number, Target[]>
}>()

const emit = defineEmits<{
  selectTarget: [id: number]
}>()

const levels = computed(() =>
  Object.entries(MATURITY_LEVELS).map(([lvl, meta]) => ({
    level: Number(lvl),
    ...meta,
    targets: props.targetsByMaturity[Number(lvl)] || [],
  }))
)
</script>

<template>
  <div class="pipeline">
    <h3 class="pipeline-title">Maturity Pipeline</h3>
    <p class="pipeline-subtitle text-sm text-secondary">SolveEverything L0-L5 maturity progression</p>
    <div class="pipeline-track">
      <div
        v-for="stage in levels"
        :key="stage.level"
        class="pipeline-stage"
      >
        <div class="stage-header">
          <span class="stage-dot" :style="{ background: stage.color }"></span>
          <span class="stage-label">{{ stage.label }}</span>
          <span class="stage-count" :class="`tag tag-l${stage.level}`">
            {{ stage.targets.length }}
          </span>
        </div>
        <div class="stage-description text-xs text-muted">{{ stage.description }}</div>
        <div class="stage-items">
          <div
            v-for="target in stage.targets"
            :key="target.id"
            class="stage-item"
            @click="emit('selectTarget', target.id)"
          >
            <span class="item-title truncate">{{ target.title }}</span>
            <span class="item-priority tag" :class="`tag-${target.priority}`">
              {{ target.priority }}
            </span>
          </div>
          <div v-if="stage.targets.length === 0" class="stage-empty text-xs text-muted">
            No targets
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pipeline { margin-bottom: 24px; }
.pipeline-title { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.pipeline-subtitle { margin-bottom: 16px; }

.pipeline-track {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

@media (max-width: 1200px) {
  .pipeline-track { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .pipeline-track { grid-template-columns: repeat(2, 1fr); }
}

.pipeline-stage {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px;
  min-height: 160px;
}
.pipeline-stage:hover { border-color: var(--color-border-light); }

.stage-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.stage-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.stage-label { font-size: 12px; font-weight: 600; flex: 1; }
.stage-count { font-size: 10px; }

.stage-description { margin-bottom: 10px; }

.stage-items { display: flex; flex-direction: column; gap: 6px; }

.stage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 6px 8px;
  background: var(--color-bg-primary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
}
.stage-item:hover { background: var(--color-bg-hover); }
.item-title { font-size: 12px; font-weight: 500; flex: 1; }
.item-priority { font-size: 9px; flex-shrink: 0; }

.stage-empty {
  padding: 12px 8px;
  text-align: center;
  font-style: italic;
}
</style>
