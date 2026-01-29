<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <NuxtLink to="/admin" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </NuxtLink>
            <div>
              <h1 class="text-2xl font-semibold text-gray-900">API Usage Analytics</h1>
              <p class="mt-1 text-sm text-gray-600">Monitor LLM API costs and usage</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <!-- Period selector -->
            <select
              v-model="periodDays"
              @change="loadData"
              class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
            >
              <option :value="7">Last 7 days</option>
              <option :value="14">Last 14 days</option>
              <option :value="30">Last 30 days</option>
              <option :value="90">Last 90 days</option>
            </select>
            <button
              @click="loadData"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Loading...</span>
        </div>
      </div>

      <template v-else>
        <!-- Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <div>
                <p class="text-sm text-gray-500">Total Calls</p>
                <p class="text-2xl font-bold text-gray-900">{{ stats.totals?.calls || 0 }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p class="text-sm text-gray-500">Total Cost</p>
                <p class="text-2xl font-bold text-green-600">${{ (stats.totals?.cost_usd || 0).toFixed(4) }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p class="text-sm text-gray-500">Total Tokens</p>
                <p class="text-2xl font-bold text-gray-900">{{ formatNumber(stats.totals?.total_tokens || 0) }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p class="text-sm text-gray-500">Avg Response</p>
                <p class="text-2xl font-bold text-gray-900">{{ stats.totals?.avg_response_time_ms || 0 }}ms</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Success Rate + Token Breakdown -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <!-- Success Rate -->
          <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Success Rate</h3>
            <div class="flex items-center gap-4">
              <div class="relative w-24 h-24">
                <svg class="w-24 h-24 transform -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="#e5e7eb" stroke-width="8" fill="none" />
                  <circle
                    cx="48" cy="48" r="40"
                    stroke="#10b981"
                    stroke-width="8"
                    fill="none"
                    :stroke-dasharray="`${(stats.totals?.success_rate || 0) * 2.51} 251`"
                  />
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xl font-bold text-gray-900">{{ stats.totals?.success_rate || 0 }}%</span>
                </div>
              </div>
              <div class="flex-1">
                <div class="text-sm text-gray-600">
                  <p class="mb-1">Input tokens: <span class="font-semibold text-gray-900">{{ formatNumber(stats.totals?.input_tokens || 0) }}</span></p>
                  <p>Output tokens: <span class="font-semibold text-gray-900">{{ formatNumber(stats.totals?.output_tokens || 0) }}</span></p>
                </div>
              </div>
            </div>
          </div>

          <!-- By Provider -->
          <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">By Provider</h3>
            <div class="space-y-3">
              <div v-for="p in stats.by_provider" :key="p.provider" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                  <div :class="['w-3 h-3 rounded-full', p.provider === 'anthropic' ? 'bg-amber-500' : 'bg-blue-500']"></div>
                  <span class="font-medium text-gray-900 capitalize">{{ p.provider }}</span>
                </div>
                <div class="text-right">
                  <p class="font-semibold text-gray-900">{{ p.calls }} calls</p>
                  <p class="text-sm text-green-600">${{ p.cost_usd.toFixed(4) }}</p>
                </div>
              </div>
              <div v-if="!stats.by_provider?.length" class="text-center text-gray-500 py-4">
                No data yet
              </div>
            </div>
          </div>
        </div>

        <!-- By Model -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Usage by Model</h3>
          <div class="overflow-x-auto">
            <table class="min-w-full">
              <thead>
                <tr class="border-b border-gray-200">
                  <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">Model</th>
                  <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">Provider</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Calls</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Tokens</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Avg Response</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="m in stats.by_model" :key="m.model" class="hover:bg-gray-50">
                  <td class="py-3 px-4">
                    <span class="font-medium text-gray-900">{{ formatModelName(m.model) }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span :class="['px-2 py-1 text-xs font-medium rounded-full', m.provider === 'anthropic' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700']">
                      {{ m.provider }}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-right font-semibold text-gray-900">{{ m.calls }}</td>
                  <td class="py-3 px-4 text-right text-gray-600">{{ formatNumber(m.tokens) }}</td>
                  <td class="py-3 px-4 text-right font-semibold text-green-600">${{ m.cost_usd.toFixed(4) }}</td>
                  <td class="py-3 px-4 text-right text-gray-600">{{ m.avg_response_time_ms }}ms</td>
                </tr>
              </tbody>
            </table>
            <div v-if="!stats.by_model?.length" class="text-center text-gray-500 py-8">
              No usage data yet. Process some receipts to see statistics.
            </div>
          </div>
        </div>

        <!-- Daily Chart -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Daily Usage</h3>
          <div v-if="stats.daily?.length" class="h-64">
            <div class="flex items-end justify-between h-48 gap-1">
              <div
                v-for="day in stats.daily"
                :key="day.date"
                class="flex-1 flex flex-col items-center"
              >
                <div
                  class="w-full bg-indigo-500 rounded-t transition-all"
                  :style="{ height: getBarHeight(day.calls) + '%' }"
                  :title="`${day.date}: ${day.calls} calls, $${(day.cost_cents / 100).toFixed(4)}`"
                ></div>
              </div>
            </div>
            <div class="flex justify-between mt-2 text-xs text-gray-500">
              <span>{{ stats.daily[0]?.date }}</span>
              <span>{{ stats.daily[stats.daily.length - 1]?.date }}</span>
            </div>
          </div>
          <div v-else class="text-center text-gray-500 py-12">
            No daily data available
          </div>
        </div>

        <!-- Recent Logs -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">Recent API Calls</h3>
            <button
              @click="loadLogs"
              class="text-sm text-indigo-600 hover:text-indigo-700"
            >
              Refresh
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full">
              <thead>
                <tr class="border-b border-gray-200">
                  <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">Time</th>
                  <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">Model</th>
                  <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">Feature</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Tokens</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                  <th class="text-right py-3 px-4 text-sm font-medium text-gray-500">Time</th>
                  <th class="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50">
                  <td class="py-3 px-4 text-sm text-gray-600">{{ formatDateTime(log.created_at) }}</td>
                  <td class="py-3 px-4">
                    <span class="text-sm font-medium text-gray-900">{{ formatModelName(log.model) }}</span>
                  </td>
                  <td class="py-3 px-4 text-sm text-gray-600">{{ log.feature }}</td>
                  <td class="py-3 px-4 text-right text-sm text-gray-600">{{ formatNumber(log.total_tokens || 0) }}</td>
                  <td class="py-3 px-4 text-right text-sm font-medium text-green-600">
                    ${{ ((log.estimated_cost_cents || 0) / 100).toFixed(4) }}
                  </td>
                  <td class="py-3 px-4 text-right text-sm text-gray-600">{{ log.response_time_ms }}ms</td>
                  <td class="py-3 px-4 text-center">
                    <span :class="['px-2 py-1 text-xs font-medium rounded-full', log.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700']">
                      {{ log.success ? 'OK' : 'Error' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="!logs.length" class="text-center text-gray-500 py-8">
              No API calls logged yet
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

interface UsageStats {
  period_days: number
  totals: {
    calls: number
    input_tokens: number
    output_tokens: number
    total_tokens: number
    cost_cents: number
    cost_usd: number
    avg_response_time_ms: number
    success_rate: number
  }
  by_provider: Array<{
    provider: string
    calls: number
    tokens: number
    cost_cents: number
    cost_usd: number
  }>
  by_model: Array<{
    model: string
    provider: string
    calls: number
    tokens: number
    cost_cents: number
    cost_usd: number
    avg_response_time_ms: number
  }>
  daily: Array<{
    date: string
    calls: number
    tokens: number
    cost_cents: number
  }>
}

interface UsageLog {
  id: number
  provider: string
  model: string
  feature: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  estimated_cost_cents: number
  success: boolean
  response_time_ms: number
  created_at: string
}

const { get } = useApi()

const isLoading = ref(true)
const periodDays = ref(30)
const stats = ref<UsageStats>({
  period_days: 30,
  totals: {
    calls: 0,
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
    cost_cents: 0,
    cost_usd: 0,
    avg_response_time_ms: 0,
    success_rate: 0
  },
  by_provider: [],
  by_model: [],
  daily: []
})
const logs = ref<UsageLog[]>([])

async function loadData() {
  isLoading.value = true
  try {
    await Promise.all([loadStats(), loadLogs()])
  } finally {
    isLoading.value = false
  }
}

async function loadStats() {
  try {
    const data = await get(`/api/admin/api-usage/stats?days=${periodDays.value}`)
    stats.value = data
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

async function loadLogs() {
  try {
    const data = await get(`/api/admin/api-usage?days=${periodDays.value}&per_page=20`)
    logs.value = data.logs
  } catch (error) {
    console.error('Error loading logs:', error)
  }
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function formatModelName(model: string): string {
  const names: Record<string, string> = {
    'gpt-4o-mini': 'GPT-4o Mini',
    'gpt-4o': 'GPT-4o',
    'claude-3-5-haiku-20241022': 'Claude Haiku',
    'claude-sonnet-4-20250514': 'Claude Sonnet'
  }
  return names[model] || model
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('bs-BA', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getBarHeight(calls: number): number {
  if (!stats.value.daily?.length) return 0
  const maxCalls = Math.max(...stats.value.daily.map(d => d.calls))
  if (maxCalls === 0) return 0
  return Math.max((calls / maxCalls) * 100, 5)
}

onMounted(() => {
  loadData()
})
</script>
