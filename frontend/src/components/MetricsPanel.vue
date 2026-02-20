<script setup lang="ts">
import { computed } from 'vue'
import type { Target, MaturitySummary } from '../types'
import { MATURITY_LEVELS } from '../types'

const props = defineProps<{
  targets: Target[]
  maturitySummary: MaturitySummary
}>()

const totalActive = computed(() => props.targets.filter(t => t.status === 'active').length)
const totalCompleted = computed(() => props.targets.filter(t => t.status === 'completed').length)
const totalPaused = computed(() => props.targets.filter(t => t.status === 'paused').length)
const criticalCount = computed(() => props.targets.filter(t => t.priority === 'critical' && t.status === 'active').length)

const avgMaturity = computed(() => {
  const active = props.targets.filter(t => t.status === 'active')
  if (active.length === 0) return 0
  const sum = active.reduce((s, t) => s + t.maturity_level, 0)
  return (sum / active.length).toFixed(1)
})

const maturityBars = computed(() =>
  Object.entries(MATURITY_LEVELS).map(([lvl, meta]) => ({
    level: Number(lvl),
    ...meta,
    count: props.maturitySummary[Number(lvl)] || 0,
  }))
)

const maxCount = computed(() => Math.max(1, ...maturityBars.value.map(b => b.count)))
</script>

<template>
  <div class="metrics-panel">
    <!-- KPI cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value">{{ totalActive }}</div>
        <div class="kpi-label">Active Targets</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--color-accent);">{{ avgMaturity }}</div>
        <div class="kpi-label">Avg Maturity</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--color-completed);">{{ totalCompleted }}</div>
        <div class="kpi-label">Completed</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color: var(--color-critical);">{{ criticalCount }}</div>
        <div class="kpi-label">Critical</div>
      </div>
    </div>

    <!-- Maturity distribution -->
    <div class="maturity-chart">
      <div class="chart-title text-sm text-secondary">Maturity Distribution</div>
      <div class="chart-bars">
        <div v-for="bar in maturityBars" :key="bar.level" class="chart-bar-wrapper">
          <div class="chart-bar-value text-xs font-mono">{{ bar.count }}</div>
          <div class="chart-bar-track">
            <div
              class="chart-bar-fill"
              :style="{
                height: (bar.count / maxCount * 100) + '%',
                background: bar.color,
              }"
            ></div>
          </div>
          <div class="chart-bar-label text-xs text-muted">L{{ bar.level }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metrics-panel { display: flex; flex-direction: column; gap: 20px; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

.kpi-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: center;
}
.kpi-value { font-size: 28px; font-weight: 800; font-family: var(--font-mono); line-height: 1.2; }
.kpi-label { font-size: 11px; color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }

.maturity-chart {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
}
.chart-title { margin-bottom: 12px; font-weight: 600; }

.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 100px;
}
.chart-bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
}
.chart-bar-value { font-weight: 600; }
.chart-bar-track {
  flex: 1;
  width: 100%;
  background: var(--color-bg-primary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}
.chart-bar-fill {
  width: 100%;
  border-radius: var(--radius-sm);
  min-height: 2px;
  transition: height 0.4s ease;
}
.chart-bar-label { font-weight: 600; }
</style>
