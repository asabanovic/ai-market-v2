<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-gray-900">Korisnici</h1>
        <p class="mt-1 text-sm text-gray-600">Pregled i analiza korisnika platforme</p>
      </div>

      <!-- Analytics Chart Section -->
      <div class="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-medium text-gray-900">Aktivnost korisnika</h3>
          <!-- Interval Selector -->
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-500">Prikaz po:</span>
            <div class="inline-flex rounded-md shadow-sm">
              <button
                @click="changeInterval('hour')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-l-md border',
                  selectedInterval === 'hour'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                ]"
              >
                Sat
              </button>
              <button
                @click="changeInterval('day')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium border-t border-b',
                  selectedInterval === 'day'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                ]"
              >
                Dan
              </button>
              <button
                @click="changeInterval('month')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-r-md border',
                  selectedInterval === 'month'
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                ]"
              >
                Mjesec
              </button>
            </div>
          </div>
        </div>

        <!-- Chart Loading State -->
        <div v-if="chartLoading" class="flex items-center justify-center h-64">
          <svg class="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>

        <!-- Chart -->
        <div v-else class="h-64">
          <ClientOnly>
            <Line v-if="chartData" :data="chartData" :options="chartOptions" />
          </ClientOnly>
        </div>

        <!-- Summary Stats -->
        <div v-if="analyticsData" class="mt-6 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
          <div class="text-center">
            <p class="text-2xl font-semibold text-blue-600">{{ analyticsData.datasets.users.total }}</p>
            <p class="text-sm text-gray-500">{{ getIntervalLabel() }} - Novi korisnici</p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-semibold text-green-600">{{ analyticsData.datasets.searches.total }}</p>
            <p class="text-sm text-gray-500">{{ getIntervalLabel() }} - Pretrage</p>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-blue-100 rounded-md p-3">
              <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">Ukupno</p>
              <p class="text-xl font-semibold text-gray-900">{{ stats.total || 0 }}</p>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-green-100 rounded-md p-3">
              <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">Email</p>
              <p class="text-xl font-semibold text-gray-900">{{ stats.email || 0 }}</p>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-red-100 rounded-md p-3">
              <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">Google</p>
              <p class="text-xl font-semibold text-gray-900">{{ stats.google || 0 }}</p>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0 bg-purple-100 rounded-md p-3">
              <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">Telefon</p>
              <p class="text-xl font-semibold text-gray-900">{{ stats.phone || 0 }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Search -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div class="flex items-center gap-4">
          <div class="flex-1">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Pretrazi korisnike po email, telefon, ime..."
              class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              @keyup.enter="loadUsers(true)"
            />
          </div>
          <button
            @click="loadUsers(true)"
            class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Pretrazi
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <svg class="animate-spin mx-auto h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p class="mt-2 text-gray-500">Ucitavanje...</p>
      </div>

      <!-- Users Table -->
      <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kontakt</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registracija</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Krediti</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Zadnja prijava</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registrovan</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
                <td class="px-4 py-3">
                  <div class="flex items-center">
                    <div>
                      <p class="text-sm font-medium text-gray-900">
                        {{ user.first_name || user.last_name ? `${user.first_name || ''} ${user.last_name || ''}`.trim() : 'Nepoznato' }}
                      </p>
                      <p class="text-xs text-gray-500">{{ user.city || 'Grad nije postavljen' }}</p>
                    </div>
                    <span v-if="user.is_admin" class="ml-2 px-2 py-0.5 text-xs font-medium bg-red-100 text-red-800 rounded-full">Admin</span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <p v-if="user.email" class="text-sm text-gray-900">{{ user.email }}</p>
                  <p v-if="user.phone" class="text-sm text-gray-500">{{ user.phone }}</p>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    :class="{
                      'bg-green-100 text-green-800': user.registration_method === 'email',
                      'bg-red-100 text-red-800': user.registration_method === 'google',
                      'bg-purple-100 text-purple-800': user.registration_method === 'phone'
                    }"
                  >
                    {{ user.registration_method || 'unknown' }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="text-sm">
                    <p class="text-gray-900">{{ user.weekly_credits - user.weekly_credits_used }} / {{ user.weekly_credits }}</p>
                    <p v-if="user.extra_credits > 0" class="text-xs text-green-600">+{{ user.extra_credits }} extra</p>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div v-if="user.last_login" class="text-sm">
                    <p class="text-gray-900">{{ formatDateTime(user.last_login.created_at) }}</p>
                    <p class="text-xs text-gray-500">{{ user.last_login.device_type }} / {{ user.last_login.browser_name }}</p>
                  </div>
                  <span v-else class="text-sm text-gray-400">Nikad</span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(user.created_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pagination" class="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
          <div class="text-sm text-gray-700">
            Stranica <span class="font-medium">{{ pagination.page }}</span> od <span class="font-medium">{{ pagination.pages }}</span>
            ({{ pagination.total }} korisnika)
          </div>
          <div class="flex space-x-2">
            <button
              @click="goToPage(pagination.page - 1)"
              :disabled="pagination.page <= 1"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Prethodna
            </button>
            <button
              @click="goToPage(pagination.page + 1)"
              :disabled="pagination.page >= pagination.pages"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sljedeca
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

definePageMeta({
  middleware: ['auth', 'admin']
})

const { get } = useApi()

const isLoading = ref(true)
const chartLoading = ref(true)
const users = ref<any[]>([])
const stats = ref<any>({})
const pagination = ref<any>(null)
const searchQuery = ref('')
const currentPage = ref(1)

// Analytics state
const selectedInterval = ref('day')
const analyticsData = ref<any>(null)
const chartData = ref<any>(null)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        precision: 0
      }
    }
  },
  interaction: {
    intersect: false,
    mode: 'index' as const
  }
}

onMounted(async () => {
  await Promise.all([
    loadUsers(),
    loadAnalytics()
  ])
})

async function loadUsers(resetPage = false) {
  if (resetPage) {
    currentPage.value = 1
  }

  isLoading.value = true

  try {
    const params = new URLSearchParams()
    params.append('page', String(currentPage.value))
    params.append('per_page', '50')
    if (searchQuery.value.trim()) {
      params.append('search', searchQuery.value.trim())
    }

    const data = await get(`/api/admin/users?${params.toString()}`)
    users.value = data.users || []
    stats.value = data.stats || {}
    pagination.value = data.pagination
  } catch (error) {
    console.error('Error loading users:', error)
  } finally {
    isLoading.value = false
  }
}

// Convert array to cumulative (running total) values
function toCumulative(arr: number[]): number[] {
  let sum = 0
  return arr.map(val => {
    sum += val
    return sum
  })
}

async function loadAnalytics() {
  chartLoading.value = true

  try {
    const data = await get(`/api/admin/users/analytics?interval=${selectedInterval.value}`)
    analyticsData.value = data

    // Convert to cumulative values for slope chart
    const cumulativeUsers = toCumulative(data.datasets.users.data)
    const cumulativeSearches = toCumulative(data.datasets.searches.data)

    // Build chart data with cumulative values
    chartData.value = {
      labels: data.labels,
      datasets: [
        {
          label: data.datasets.users.label,
          data: cumulativeUsers,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.3,
          fill: true
        },
        {
          label: data.datasets.searches.label,
          data: cumulativeSearches,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.3,
          fill: true
        }
      ]
    }
  } catch (error) {
    console.error('Error loading analytics:', error)
  } finally {
    chartLoading.value = false
  }
}

function changeInterval(interval: string) {
  selectedInterval.value = interval
  loadAnalytics()
}

function getIntervalLabel() {
  if (selectedInterval.value === 'hour') return 'Zadnja 24 sata'
  if (selectedInterval.value === 'day') return 'Zadnjih 30 dana'
  return 'Zadnjih 12 mjeseci'
}

function goToPage(page: number) {
  if (page >= 1 && pagination.value && page <= pagination.value.pages) {
    currentPage.value = page
    loadUsers()
  }
}

function formatDate(dateString: string) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
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

useSeoMeta({
  title: 'Korisnici - Admin - Popust.ba',
  description: 'Pregled i analiza korisnika Popust.ba platforme'
})
</script>
