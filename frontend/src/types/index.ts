export interface UserInfo {
  user_id: number
  user_name: string | null
  email: string | null
  role: string | null
}

export interface User {
  valid: boolean
  user_info: UserInfo
  api_key?: string
}

export interface Benchmark {
  id: number
  name: string
  metric_type: string
  current_value: number | null
  target_value: number | null
  unit: string | null
  recorded_at: string | null
}

export interface Resource {
  id: number
  resource_type: string
  allocated: number
  consumed: number
  unit: string | null
}

export interface Target {
  id: number
  user_id: number
  title: string
  description: string | null
  domain: string | null
  maturity_level: number
  status: string
  priority: string
  benchmark_definition: string | null
  success_criteria: string | null
  current_score: number | null
  target_score: number | null
  tags: string[]
  benchmarks: Benchmark[]
  resources: Resource[]
  created_at: string | null
  updated_at: string | null
}

export interface TargetCreatePayload {
  title: string
  description?: string
  domain?: string
  maturity_level?: number
  priority?: string
  benchmark_definition?: string
  success_criteria?: string
  target_score?: number
  tags?: string[]
  benchmarks?: { name: string; metric_type: string; target_value?: number; unit?: string }[]
  resources?: { resource_type: string; allocated: number; unit?: string }[]
}

export interface MaturitySummary {
  [level: number]: number
}

export const MATURITY_LEVELS: Record<number, { label: string; description: string; color: string }> = {
  0: { label: 'L0 — Unmeasured', description: 'Problem exists but no metrics defined', color: '#6b7280' },
  1: { label: 'L1 — Measured', description: 'Metrics defined, manual process', color: '#ef4444' },
  2: { label: 'L2 — Assisted', description: 'AI-assisted with human oversight', color: '#f97316' },
  3: { label: 'L3 — Automated', description: 'Automated with audit trail', color: '#eab308' },
  4: { label: 'L4 — Industrialized', description: 'Scaled, reliable, cost-effective', color: '#22c55e' },
  5: { label: 'L5 — Solved', description: 'Commoditized — problem solved', color: '#6366f1' },
}

export const PRIORITY_OPTIONS = ['critical', 'high', 'medium', 'low'] as const
export const STATUS_OPTIONS = ['active', 'paused', 'completed', 'archived'] as const
export const DOMAIN_OPTIONS = [
  'Healthcare', 'Education', 'Energy', 'Finance', 'Security',
  'Infrastructure', 'Research', 'Climate', 'Agriculture', 'Custom',
] as const
