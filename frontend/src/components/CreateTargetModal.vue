<script setup lang="ts">
import { reactive, ref } from 'vue'
import { MATURITY_LEVELS, PRIORITY_OPTIONS, DOMAIN_OPTIONS } from '../types'
import type { TargetCreatePayload } from '../types'

const emit = defineEmits<{
  close: []
  create: [payload: TargetCreatePayload]
}>()

const form = reactive<TargetCreatePayload>({
  title: '',
  description: '',
  domain: '',
  maturity_level: 0,
  priority: 'medium',
  benchmark_definition: '',
  success_criteria: '',
  target_score: undefined,
  tags: [],
  benchmarks: [],
  resources: [],
})

const tagInput = ref('')

function addTag() {
  const tag = tagInput.value.trim().toLowerCase()
  if (tag && !form.tags!.includes(tag)) {
    form.tags!.push(tag)
  }
  tagInput.value = ''
}

function removeTag(t: string) {
  form.tags = form.tags!.filter(x => x !== t)
}

function addBenchmark() {
  form.benchmarks!.push({ name: '', metric_type: 'score', target_value: undefined, unit: '' })
}

function removeBenchmark(i: number) {
  form.benchmarks!.splice(i, 1)
}

function addResource() {
  form.resources!.push({ resource_type: 'compute', allocated: 0, unit: '' })
}

function removeResource(i: number) {
  form.resources!.splice(i, 1)
}

function submit() {
  if (!form.title.trim()) return
  emit('create', { ...form })
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h3 class="modal-title">Create Intelligence Target</h3>

      <div class="form-group">
        <label class="form-label">Title *</label>
        <input v-model="form.title" class="input" placeholder="e.g. Automate clinical trial data analysis" />
      </div>

      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea v-model="form.description" class="textarea" placeholder="Describe the target problem and desired outcome..." />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Domain</label>
          <select v-model="form.domain" class="select">
            <option value="">Select domain</option>
            <option v-for="d in DOMAIN_OPTIONS" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Priority</label>
          <select v-model="form.priority" class="select">
            <option v-for="p in PRIORITY_OPTIONS" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Initial Maturity Level</label>
        <select v-model.number="form.maturity_level" class="select">
          <option v-for="(meta, lvl) in MATURITY_LEVELS" :key="lvl" :value="Number(lvl)">
            {{ meta.label }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Benchmark Definition</label>
        <textarea v-model="form.benchmark_definition" class="textarea" placeholder="How will success be measured? What test cases?" />
      </div>

      <div class="form-group">
        <label class="form-label">Success Criteria</label>
        <textarea v-model="form.success_criteria" class="textarea" placeholder="What conditions must be met to advance maturity?" />
      </div>

      <div class="form-group">
        <label class="form-label">Target Score</label>
        <input v-model.number="form.target_score" type="number" class="input" placeholder="e.g. 95" />
      </div>

      <!-- Tags -->
      <div class="form-group">
        <label class="form-label">Tags</label>
        <div class="tag-input-row">
          <input
            v-model="tagInput"
            class="input"
            placeholder="Add tag and press Enter"
            @keydown.enter.prevent="addTag"
          />
        </div>
        <div v-if="form.tags!.length" class="tag-list mt-1">
          <span v-for="t in form.tags" :key="t" class="tag tag-active" @click="removeTag(t)">
            {{ t }} &times;
          </span>
        </div>
      </div>

      <!-- Benchmarks -->
      <div class="form-group">
        <div class="flex justify-between items-center mb-2">
          <label class="form-label" style="margin:0">Benchmarks</label>
          <button class="btn btn-sm btn-ghost" @click="addBenchmark">+ Add</button>
        </div>
        <div v-for="(b, i) in form.benchmarks" :key="i" class="sub-row">
          <input v-model="b.name" class="input" placeholder="Benchmark name" />
          <select v-model="b.metric_type" class="select" style="max-width:120px">
            <option value="score">Score</option>
            <option value="accuracy">Accuracy</option>
            <option value="latency">Latency</option>
            <option value="cost">Cost</option>
          </select>
          <input v-model.number="b.target_value" type="number" class="input" placeholder="Target" style="max-width:90px" />
          <input v-model="b.unit" class="input" placeholder="Unit" style="max-width:70px" />
          <button class="btn btn-sm btn-danger btn-ghost" @click="removeBenchmark(i)">&times;</button>
        </div>
      </div>

      <!-- Resources -->
      <div class="form-group">
        <div class="flex justify-between items-center mb-2">
          <label class="form-label" style="margin:0">Resources</label>
          <button class="btn btn-sm btn-ghost" @click="addResource">+ Add</button>
        </div>
        <div v-for="(r, i) in form.resources" :key="i" class="sub-row">
          <select v-model="r.resource_type" class="select" style="max-width:130px">
            <option value="compute">Compute</option>
            <option value="budget">Budget</option>
            <option value="tokens">Tokens</option>
            <option value="time">Time</option>
          </select>
          <input v-model.number="r.allocated" type="number" class="input" placeholder="Amount" style="max-width:100px" />
          <input v-model="r.unit" class="input" placeholder="Unit" style="max-width:80px" />
          <button class="btn btn-sm btn-danger btn-ghost" @click="removeResource(i)">&times;</button>
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn" @click="emit('close')">Cancel</button>
        <button class="btn btn-primary" :disabled="!form.title.trim()" @click="submit">
          Create Target
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-list .tag { cursor: pointer; }
.sub-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
</style>
