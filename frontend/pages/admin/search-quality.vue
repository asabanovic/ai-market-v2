<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Search Quality Evaluation</h1>
          <p class="mt-1 text-sm text-gray-600">Praćenje i evaluacija kvalitete pretrage</p>
        </div>
        <NuxtLink
          to="/admin"
          class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
          </svg>
          Nazad na admin
        </NuxtLink>
      </div>

      <!-- Stats Overview -->
      <div v-if="stats" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <dt class="text-sm font-medium text-gray-500">Ukupno pretraga</dt>
          <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_searches }}</dd>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <dt class="text-sm font-medium text-gray-500">Pretrage bez rezultata</dt>
          <dd class="text-2xl font-semibold text-red-600">{{ stats.zero_result_searches }}</dd>
          <span class="text-sm text-gray-500">{{ stats.zero_result_rate?.toFixed(1) }}%</span>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <dt class="text-sm font-medium text-gray-500">Prosj. rezultata</dt>
          <dd class="text-2xl font-semibold text-green-600">{{ stats.avg_results_per_search }}</dd>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <dt class="text-sm font-medium text-gray-500">Problematične pretrage</dt>
          <dd class="text-2xl font-semibold text-orange-600">{{ stats.zero_result_queries?.length || 0 }}</dd>
        </div>
      </div>

      <!-- Filters and Search -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Filter po upitu</label>
            <input
              v-model="queryFilter"
              type="text"
              placeholder="Pretraži upite..."
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              @keyup.enter="loadLogs"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Min rezultata</label>
            <input
              v-model.number="minResults"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Max rezultata</label>
            <input
              v-model.number="maxResults"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div class="flex items-end">
            <button
              @click="loadLogs"
              class="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Filtriraj
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Search Logs Table -->
      <div v-else class="bg-white rounded-lg border border-gray-200">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Search Logs</h3>
        </div>

        <div v-if="logs.length === 0" class="text-center py-12 text-gray-500">
          Nema pronađenih logova pretrage
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vrijeme</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Upit</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rezultati</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prosj. Score</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(log.created_at) }}
                </td>
                <td class="px-4 py-3">
                  <div class="text-sm font-medium text-gray-900">{{ log.query }}</div>
                  <div v-if="log.parsed_query" class="text-xs text-gray-500 mt-1">
                    Parsed: {{ JSON.stringify(log.parsed_query).substring(0, 50) }}...
                  </div>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getResultCountClass(log.result_count)"
                  >
                    {{ log.result_count }}
                  </span>
                  <span v-if="log.total_before_filter" class="text-xs text-gray-400 ml-1">
                    / {{ log.total_before_filter }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span v-if="log.results_detail && log.results_detail.length > 0" class="text-sm font-medium text-gray-900">
                    {{ getAvgScore(log.results_detail).toFixed(3) }}
                  </span>
                  <span v-else class="text-sm text-gray-400">-</span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="flex space-x-2">
                    <button
                      @click="openLogDetail(log)"
                      class="text-indigo-600 hover:text-indigo-900 text-sm"
                    >
                      Detalji
                    </button>
                    <button
                      @click="rerunSearch(log)"
                      :disabled="rerunning === log.id"
                      class="text-green-600 hover:text-green-900 text-sm disabled:opacity-50"
                    >
                      {{ rerunning === log.id ? 'Re-running...' : 'Re-run' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pagination && pagination.pages > 1" class="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-700">
              Strana {{ pagination.page }} od {{ pagination.pages }} ({{ pagination.total }} ukupno)
            </div>
            <div class="flex space-x-2">
              <button
                v-if="pagination.page > 1"
                @click="loadLogs(pagination.page - 1)"
                class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Prethodna
              </button>
              <button
                v-if="pagination.page < pagination.pages"
                @click="loadLogs(pagination.page + 1)"
                class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Sljedeća
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Log Detail Modal -->
      <div v-if="selectedLog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="selectedLog = null">
        <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white">
            <h3 class="text-lg font-medium text-gray-900">Detalji pretrage: "{{ selectedLog.query }}"</h3>
            <button @click="selectedLog = null" class="text-gray-400 hover:text-gray-500">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="p-6">
            <!-- Meta Info -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <dt class="text-xs text-gray-500">Vrijeme</dt>
                <dd class="text-sm font-medium">{{ formatDateTime(selectedLog.created_at) }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500">Rezultati</dt>
                <dd class="text-sm font-medium">{{ selectedLog.result_count }} / {{ selectedLog.total_before_filter || 'N/A' }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500">Similarity Threshold</dt>
                <dd class="text-sm font-medium">{{ selectedLog.similarity_threshold }}</dd>
              </div>
              <div>
                <dt class="text-xs text-gray-500">K</dt>
                <dd class="text-sm font-medium">{{ selectedLog.k }}</dd>
              </div>
            </div>

            <!-- Parsed Query -->
            <div v-if="selectedLog.parsed_query" class="mb-6">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Parsed Query</h4>
              <pre class="bg-gray-50 p-3 rounded text-xs overflow-x-auto">{{ JSON.stringify(selectedLog.parsed_query, null, 2) }}</pre>
            </div>

            <!-- Results Detail -->
            <div v-if="selectedLog.results_detail && selectedLog.results_detail.length > 0">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Rezultati ({{ selectedLog.results_detail.length }})</h4>
              <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Rank</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Slika</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Proizvod</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Grupa</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Final Score</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Vector</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Text</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200">
                    <tr v-for="result in selectedLog.results_detail" :key="result.product_id" class="hover:bg-gray-50">
                      <td class="px-3 py-2 text-gray-500">{{ result.rank }}</td>
                      <td class="px-3 py-2">
                        <img
                          v-if="result.image_path"
                          :src="result.image_path"
                          :alt="result.title"
                          class="w-12 h-12 object-cover rounded"
                        />
                        <div v-else class="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                          <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        </div>
                      </td>
                      <td class="px-3 py-2">
                        <div class="max-w-xs truncate text-gray-900 font-medium">{{ result.title }}</div>
                        <div class="text-xs text-gray-400">ID: {{ result.product_id }}</div>
                      </td>
                      <td class="px-3 py-2 text-gray-500">{{ result.group || '-' }}</td>
                      <td class="px-3 py-2">
                        <span
                          class="px-2 py-1 rounded text-xs font-medium"
                          :class="getScoreClass(result.similarity)"
                        >
                          {{ result.similarity?.toFixed(3) }}
                        </span>
                      </td>
                      <td class="px-3 py-2 text-gray-600">{{ result.vector_score?.toFixed(3) }}</td>
                      <td class="px-3 py-2 text-gray-600">{{ result.text_score?.toFixed(3) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Comparison Results -->
            <div v-if="comparisonResults" class="mt-6 border-t pt-6">
              <h4 class="text-sm font-medium text-gray-700 mb-4">Re-run Usporedba</h4>

              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div class="bg-blue-50 p-3 rounded">
                  <dt class="text-xs text-blue-600">U oba</dt>
                  <dd class="text-lg font-semibold text-blue-700">{{ comparisonResults.comparison?.products_in_both || 0 }}</dd>
                </div>
                <div class="bg-green-50 p-3 rounded">
                  <dt class="text-xs text-green-600">Samo u novom</dt>
                  <dd class="text-lg font-semibold text-green-700">{{ comparisonResults.comparison?.products_only_in_new || 0 }}</dd>
                </div>
                <div class="bg-red-50 p-3 rounded">
                  <dt class="text-xs text-red-600">Samo u starom</dt>
                  <dd class="text-lg font-semibold text-red-700">{{ comparisonResults.comparison?.products_only_in_original || 0 }}</dd>
                </div>
                <div class="bg-purple-50 p-3 rounded">
                  <dt class="text-xs text-purple-600">Avg Score Change</dt>
                  <dd class="text-lg font-semibold" :class="getScoreChangeClass(comparisonResults.comparison?.avg_score_new - comparisonResults.comparison?.avg_score_original)">
                    {{ ((comparisonResults.comparison?.avg_score_new || 0) - (comparisonResults.comparison?.avg_score_original || 0)).toFixed(3) }}
                  </dd>
                </div>
              </div>

              <!-- Score Changes -->
              <div v-if="comparisonResults.comparison?.score_changes?.length > 0">
                <h5 class="text-xs font-medium text-gray-500 mb-2">Promjene scorova (sortirano po promjeni)</h5>
                <div class="max-h-48 overflow-y-auto">
                  <div
                    v-for="change in comparisonResults.comparison.score_changes"
                    :key="change.product_id"
                    class="flex justify-between items-center py-1 px-2 hover:bg-gray-50 text-sm"
                  >
                    <span class="truncate flex-1">{{ change.title }}</span>
                    <span class="text-gray-400 mx-2">{{ change.original_score?.toFixed(3) }} -></span>
                    <span class="font-medium">{{ change.new_score?.toFixed(3) }}</span>
                    <span
                      class="ml-2 px-2 py-0.5 rounded text-xs"
                      :class="getScoreChangeClass(change.score_change)"
                    >
                      {{ change.score_change > 0 ? '+' : '' }}{{ change.score_change?.toFixed(3) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const { get, post } = useApi()

const isLoading = ref(true)
const stats = ref<any>(null)
const logs = ref<any[]>([])
const pagination = ref<any>(null)
const selectedLog = ref<any>(null)
const comparisonResults = ref<any>(null)
const rerunning = ref<number | null>(null)

// Filters
const queryFilter = ref('')
const minResults = ref<number | undefined>(undefined)
const maxResults = ref<number | undefined>(undefined)

onMounted(async () => {
  await Promise.all([loadStats(), loadLogs()])
})

async function loadStats() {
  try {
    stats.value = await get('/api/admin/search/stats')
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

async function loadLogs(page = 1) {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', page.toString())
    params.append('per_page', '50')
    if (queryFilter.value) params.append('query', queryFilter.value)
    if (minResults.value !== undefined) params.append('min_results', minResults.value.toString())
    if (maxResults.value !== undefined) params.append('max_results', maxResults.value.toString())

    const data = await get(`/api/admin/search/logs?${params.toString()}`)
    logs.value = data.logs || []
    pagination.value = data.pagination
  } catch (error) {
    console.error('Error loading logs:', error)
  } finally {
    isLoading.value = false
  }
}

function openLogDetail(log: any) {
  selectedLog.value = log
  comparisonResults.value = null
}

async function rerunSearch(log: any) {
  rerunning.value = log.id
  try {
    const data = await post('/api/admin/search/rerun', {
      query: log.query,
      log_id: log.id
    })
    comparisonResults.value = data
    if (!selectedLog.value || selectedLog.value.id !== log.id) {
      selectedLog.value = log
    }
  } catch (error) {
    console.error('Error re-running search:', error)
  } finally {
    rerunning.value = null
  }
}

function formatDateTime(dateString: string) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getResultCountClass(count: number) {
  if (count === 0) return 'bg-red-100 text-red-800'
  if (count < 3) return 'bg-yellow-100 text-yellow-800'
  return 'bg-green-100 text-green-800'
}

function getScoreClass(score: number) {
  if (score >= 0.5) return 'bg-green-100 text-green-800'
  if (score >= 0.3) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

function getScoreChangeClass(change: number) {
  if (change > 0.01) return 'bg-green-100 text-green-800'
  if (change < -0.01) return 'bg-red-100 text-red-800'
  return 'bg-gray-100 text-gray-800'
}

function getAvgScore(results: any[]) {
  if (!results || results.length === 0) return 0
  const sum = results.reduce((acc, r) => acc + (r.similarity || 0), 0)
  return sum / results.length
}

useSeoMeta({
  title: 'Search Quality - Admin - Popust.ba',
  description: 'Evaluacija kvalitete pretrage na Popust.ba platformi',
})
</script>
