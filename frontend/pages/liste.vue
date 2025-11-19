<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
          Moje Kupovne Liste
        </h1>
        <p class="text-gray-600">
          Pregled statistike i historije kupovina
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <LoadingSpinner class="mx-auto" />
        <p class="mt-4 text-gray-600">Učitavanje statistike...</p>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg"
      >
        <p>{{ error }}</p>
      </div>

      <!-- Dashboard Content -->
      <div v-else-if="stats">
        <!-- All-Time Statistics Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- Total Lists -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Ukupno Lista</p>
                <p class="text-3xl font-bold text-gray-900">
                  {{ stats.all_time.total_lists }}
                </p>
              </div>
              <svg class="w-12 h-12 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
          </div>

          <!-- Total Spent -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Ukupno Potrošeno</p>
                <p class="text-3xl font-bold text-gray-900">
                  {{ stats.all_time.total_spent.toFixed(2) }} KM
                </p>
              </div>
              <svg class="w-12 h-12 text-purple-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>

          <!-- Total Savings -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Ukupno Ušteda</p>
                <p class="text-3xl font-bold text-green-600">
                  {{ stats.all_time.total_savings.toFixed(2) }} KM
                </p>
              </div>
              <svg class="w-12 h-12 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 7h-2v4H7v2h4v4h2v-4h4v-2h-4V7zm-1-5C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
              </svg>
            </div>
          </div>

          <!-- Savings Percentage -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Postotak Uštede</p>
                <p class="text-3xl font-bold text-green-600">
                  {{ stats.all_time.savings_percentage }}%
                </p>
              </div>
              <svg class="w-12 h-12 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Charts Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Timeline Chart -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
              Vremenska Linija Kupovina
            </h3>
            <div v-if="stats.timeline && stats.timeline.length > 0">
              <Bar :data="timelineChartData" :options="timelineChartOptions" :height="280" />
            </div>
            <p v-else class="text-gray-500 text-center py-8">
              Nema podataka
            </p>
          </div>

          <!-- Monthly Spend vs Save Chart -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
              Mjesečna Potrošnja vs Ušteda
            </h3>
            <div v-if="stats.monthly_breakdown && stats.monthly_breakdown.length > 0">
              <Bar :data="monthlyChartData" :options="monthlyChartOptions" :height="280" />
            </div>
            <p v-else class="text-gray-500 text-center py-8">
              Nema podataka
            </p>
          </div>
        </div>

        <!-- All Lists -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Sve Liste
          </h3>
          <div v-if="lists.length > 0" class="space-y-3">
            <NuxtLink
              v-for="list in lists"
              :key="list.id"
              :to="`/profil/liste?list_id=${list.id}`"
              class="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="font-semibold text-gray-900">
                    {{ getListName(list.created_at) }}
                  </h4>
                  <p class="text-sm text-gray-600">
                    {{ list.item_count }} {{ list.item_count === 1 ? 'artikal' : 'artikala' }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="font-bold text-gray-900">
                    {{ list.total_amount.toFixed(2) }} KM
                  </p>
                  <p v-if="list.total_savings > 0" class="text-sm text-green-600">
                    Ušteda: {{ list.total_savings.toFixed(2) }} KM
                  </p>
                </div>
              </div>
            </NuxtLink>
          </div>
          <p v-else class="text-gray-500 text-center py-8">
            Nemate još shopping lista
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

definePageMeta({
  middleware: 'auth'
})

const { $api } = useNuxtApp()

interface Statistics {
  all_time: {
    total_lists: number
    total_spent: number
    total_savings: number
    total_original_price: number
    savings_percentage: number
    total_items_purchased: number
    average_per_list: number
  }
  monthly_breakdown: Array<{
    month: string
    lists_count: number
    total_spent: number
    total_saved: number
    items_count: number
  }>
  timeline: Array<{
    date: string
    amount: number
    saved: number
    items: number
    status: string
  }>
}

const stats = ref<Statistics | null>(null)
const lists = ref<any[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)

// Timeline Chart Data
const timelineChartData = computed(() => {
  if (!stats.value?.timeline?.length) return { labels: [], datasets: [] }

  const recentTimeline = stats.value.timeline.slice(0, 20).reverse()

  return {
    labels: recentTimeline.map(item => formatShortDate(item.date)),
    datasets: [
      {
        label: 'Potrošeno (KM)',
        data: recentTimeline.map(item => item.amount),
        backgroundColor: 'rgba(147, 51, 234, 0.8)',
        borderColor: 'rgb(147, 51, 234)',
        borderWidth: 2,
        borderRadius: 6,
        hoverBackgroundColor: 'rgba(147, 51, 234, 1)',
      }
    ]
  }
})

const timelineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          return context.parsed.y.toFixed(2) + ' KM'
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: function(value: any) {
          return value + ' KM'
        }
      }
    },
    x: {
      ticks: {
        maxRotation: 45,
        minRotation: 45,
        font: {
          size: 10
        }
      }
    }
  }
}

// Monthly Chart Data
const monthlyChartData = computed(() => {
  if (!stats.value?.monthly_breakdown?.length) return { labels: [], datasets: [] }

  const recentMonths = stats.value.monthly_breakdown.slice(0, 6)

  return {
    labels: recentMonths.map(month => formatMonth(month.month)),
    datasets: [
      {
        label: 'Potrošeno',
        data: recentMonths.map(month => month.total_spent),
        backgroundColor: 'rgba(147, 51, 234, 0.8)',
        borderColor: 'rgb(147, 51, 234)',
        borderWidth: 2,
        borderRadius: 6,
        stack: 'stack0',
      },
      {
        label: 'Ušteda',
        data: recentMonths.map(month => month.total_saved),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 2,
        borderRadius: 6,
        stack: 'stack0',
      }
    ]
  }
})

const monthlyChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + ' KM'
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      stacked: true,
      ticks: {
        callback: function(value: any) {
          return value + ' KM'
        }
      }
    },
    x: {
      stacked: true,
      ticks: {
        font: {
          size: 11
        }
      }
    }
  }
}

async function loadData() {
  isLoading.value = true
  error.value = null

  try {
    // Load statistics
    const statsData = await $api.get('/shopping-lists/statistics')
    stats.value = statsData

    // Load lists
    const listsData = await $api.get('/shopping-lists/history?page=1&per_page=20')
    lists.value = listsData.lists
  } catch (err: any) {
    console.error('Failed to load dashboard data:', err)
    error.value = err.message || 'Greška pri učitavanju podataka'
  } finally {
    isLoading.value = false
  }
}

function formatMonth(monthStr: string): string {
  const [year, month] = monthStr.split('-')
  const date = new Date(parseInt(year), parseInt(month) - 1)
  const formatted = new Intl.DateTimeFormat('bs-BA', { month: 'long', year: 'numeric' }).format(date)
  // Capitalize first letter
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

function formatShortDate(dateStr: string): string {
  const date = new Date(dateStr)
  const formatted = new Intl.DateTimeFormat('bs-BA', { day: 'numeric', month: 'long' }).format(date)
  // Capitalize first letter of month
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

function formatDay(dateStr: string): string {
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('bs-BA', { day: 'numeric', month: 'numeric' }).format(date)
}

function getListName(dateString: string): string {
  const date = new Date(dateString)
  const day = date.getDate()
  const month = new Intl.DateTimeFormat('bs-BA', { month: 'long' }).format(date)
  const year = date.getFullYear()
  const weekday = new Intl.DateTimeFormat('bs-BA', { weekday: 'long' }).format(date)

  // Format: "28 Novembar 2025, Utorak"
  // Capitalize first letter of month and weekday
  const monthCapitalized = month.charAt(0).toUpperCase() + month.slice(1)
  const weekdayCapitalized = weekday.charAt(0).toUpperCase() + weekday.slice(1)

  return `${day} ${monthCapitalized} ${year}, ${weekdayCapitalized}`
}


onMounted(() => {
  loadData()
})
</script>
