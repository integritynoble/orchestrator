import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../services/api'
import type { Target, TargetCreatePayload, MaturitySummary } from '../types'

export const useTargetingStore = defineStore('targeting', () => {
  const targets = ref<Target[]>([])
  const selectedTarget = ref<Target | null>(null)
  const maturitySummary = ref<MaturitySummary>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const filterStatus = ref<string | null>(null)

  const activeTargets = computed(() => targets.value.filter(t => t.status === 'active'))
  const totalTargets = computed(() => targets.value.length)

  const targetsByMaturity = computed(() => {
    const grouped: Record<number, Target[]> = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [] }
    for (const t of targets.value) {
      if (t.status !== 'archived') {
        const lvl = t.maturity_level
        if (grouped[lvl]) grouped[lvl].push(t)
      }
    }
    return grouped
  })

  async function loadTargets() {
    isLoading.value = true
    error.value = null
    try {
      const params = filterStatus.value ? `?status=${filterStatus.value}` : ''
      const res = await api.get<{ targets: Target[]; total: number }>(`/targets${params}`)
      targets.value = res.targets
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  async function loadMaturitySummary() {
    try {
      const res = await api.get<{ summary: MaturitySummary }>('/targets/maturity-summary')
      maturitySummary.value = res.summary
    } catch { /* */ }
  }

  async function createTarget(payload: TargetCreatePayload): Promise<Target | null> {
    try {
      const target = await api.post<Target>('/targets', payload)
      targets.value.unshift(target)
      await loadMaturitySummary()
      return target
    } catch (e: any) {
      error.value = e.message
      return null
    }
  }

  async function updateTarget(id: number, payload: Partial<TargetCreatePayload>): Promise<boolean> {
    try {
      const updated = await api.put<Target>(`/targets/${id}`, payload)
      const idx = targets.value.findIndex(t => t.id === id)
      if (idx !== -1) targets.value[idx] = updated
      if (selectedTarget.value?.id === id) selectedTarget.value = updated
      await loadMaturitySummary()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  async function deleteTarget(id: number): Promise<boolean> {
    try {
      await api.del(`/targets/${id}`)
      targets.value = targets.value.filter(t => t.id !== id)
      if (selectedTarget.value?.id === id) selectedTarget.value = null
      await loadMaturitySummary()
      return true
    } catch (e: any) {
      error.value = e.message
      return false
    }
  }

  async function selectTarget(id: number) {
    try {
      selectedTarget.value = await api.get<Target>(`/targets/${id}`)
    } catch (e: any) {
      error.value = e.message
    }
  }

  return {
    targets, selectedTarget, maturitySummary, isLoading, error, filterStatus,
    activeTargets, totalTargets, targetsByMaturity,
    loadTargets, loadMaturitySummary, createTarget, updateTarget, deleteTarget, selectTarget,
  }
})
