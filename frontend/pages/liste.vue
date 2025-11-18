<template>
  <div class="bg-gray-50 dark:bg-gray-900 min-h-screen py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Moje Shopping Liste
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
          Pregled statistike i istorije kupovina
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <LoadingSpinner class="mx-auto" />
        <p class="mt-4 text-gray-600 dark:text-gray-400">Učitavanje statistike...</p>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-6 py-4 rounded-lg"
      >
        <p>{{ error }}</p>
      </div>

      <!-- Dashboard Content -->
      <div v-else-if="stats">
        <!-- All-Time Statistics Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- Total Lists -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">Ukupno Lista</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">
                  {{ stats.all_time.total_lists }}
                </p>
              </div>
              <Icon name="mdi:clipboard-list" class="w-12 h-12 text-blue-500" />
            </div>
          </div>

          <!-- Total Spent -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">Ukupno Potrošeno</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">
                  {{ stats.all_time.total_spent.toFixed(2) }} KM
                </p>
              </div>
              <Icon name="mdi:cash" class="w-12 h-12 text-purple-500" />
            </div>
          </div>

          <!-- Total Savings -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">Ukupno Ušteda</p>
                <p class="text-3xl font-bold text-green-600 dark:text-green-400">
                  {{ stats.all_time.total_savings.toFixed(2) }} KM
                </p>
              </div>
              <Icon name="mdi:piggy-bank" class="w-12 h-12 text-green-500" />
            </div>
          </div>

          <!-- Savings Percentage -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">Postotak Uštede</p>
                <p class="text-3xl font-bold text-green-600 dark:text-green-400">
                  {{ stats.all_time.savings_percentage }}%
                </p>
              </div>
              <Icon name="mdi:chart-line" class="w-12 h-12 text-green-500" />
            </div>
          </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Monthly Spending Chart -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Mjesečna Potrošnja
            </h3>
            <div v-if="stats.monthly_breakdown.length > 0" class="space-y-3">
              <div
                v-for="month in stats.monthly_breakdown.slice(0, 6)"
                :key="month.month"
                class="space-y-1"
              >
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600 dark:text-gray-400">{{ formatMonth(month.month) }}</span>
                  <span class="font-semibold text-gray-900 dark:text-white">{{ month.total_spent.toFixed(2) }} KM</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    class="bg-purple-600 h-2 rounded-full transition-all duration-500"
                    :style="{ width: getPercentage(month.total_spent, maxMonthlySpent) + '%' }"
                  ></div>
                </div>
              </div>
            </div>
            <p v-else class="text-gray-500 dark:text-gray-400 text-center py-8">
              Nema podataka
            </p>
          </div>

          <!-- Monthly Savings Chart -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Mjesečna Ušteda
            </h3>
            <div v-if="stats.monthly_breakdown.length > 0" class="space-y-3">
              <div
                v-for="month in stats.monthly_breakdown.slice(0, 6)"
                :key="month.month"
                class="space-y-1"
              >
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600 dark:text-gray-400">{{ formatMonth(month.month) }}</span>
                  <span class="font-semibold text-green-600 dark:text-green-400">{{ month.total_saved.toFixed(2) }} KM</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    class="bg-green-600 h-2 rounded-full transition-all duration-500"
                    :style="{ width: getPercentage(month.total_saved, maxMonthlySaved) + '%' }"
                  ></div>
                </div>
              </div>
            </div>
            <p v-else class="text-gray-500 dark:text-gray-400 text-center py-8">
              Nema podataka
            </p>
          </div>
        </div>

        <!-- Timeline Chart -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Vremenska Linija Kupovina
          </h3>
          <div v-if="stats.timeline.length > 0" class="overflow-x-auto">
            <div class="flex items-end gap-2 min-w-max pb-4" style="height: 200px">
              <div
                v-for="(item, index) in stats.timeline.slice(0, 30).reverse()"
                :key="index"
                class="flex flex-col items-center gap-1"
              >
                <div
                  class="w-8 bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer relative group"
                  :style="{ height: getTimelineHeight(item.amount) + '%' }"
                  :title="`${formatShortDate(item.date)}: ${item.amount} KM`"
                >
                  <!-- Tooltip on hover -->
                  <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block">
                    <div class="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                      {{ formatShortDate(item.date) }}<br/>
                      {{ item.amount }} KM
                    </div>
                  </div>
                </div>
                <span class="text-[10px] text-gray-500 dark:text-gray-400 rotate-45 origin-top-left mt-2">
                  {{ formatDay(item.date) }}
                </span>
              </div>
            </div>
          </div>
          <p v-else class="text-gray-500 dark:text-gray-400 text-center py-8">
            Nema podataka
          </p>
        </div>

        <!-- All Lists -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Sve Liste
          </h3>
          <div v-if="lists.length > 0" class="space-y-3">
            <NuxtLink
              v-for="list in lists"
              :key="list.id"
              :to="`/profil/liste-istorija`"
              class="block p-4 border dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white">
                    {{ getListName(list.created_at) }}
                  </h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    {{ list.item_count }} {{ list.item_count === 1 ? 'artikal' : 'artikala' }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="font-bold text-gray-900 dark:text-white">
                    {{ list.total_amount.toFixed(2) }} KM
                  </p>
                  <p v-if="list.total_savings > 0" class="text-sm text-green-600 dark:text-green-400">
                    Ušteda: {{ list.total_savings.toFixed(2) }} KM
                  </p>
                </div>
              </div>
            </NuxtLink>
          </div>
          <p v-else class="text-gray-500 dark:text-gray-400 text-center py-8">
            Nemate još shopping lista
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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

const maxMonthlySpent = computed(() => {
  if (!stats.value?.monthly_breakdown.length) return 0
  return Math.max(...stats.value.monthly_breakdown.map(m => m.total_spent))
})

const maxMonthlySaved = computed(() => {
  if (!stats.value?.monthly_breakdown.length) return 0
  return Math.max(...stats.value.monthly_breakdown.map(m => m.total_saved))
})

const maxTimelineAmount = computed(() => {
  if (!stats.value?.timeline.length) return 0
  return Math.max(...stats.value.timeline.map(t => t.amount))
})

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
  return new Intl.DateTimeFormat('bs-BA', { month: 'long', year: 'numeric' }).format(date)
}

function formatShortDate(dateStr: string): string {
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('bs-BA', { day: 'numeric', month: 'short' }).format(date)
}

function formatDay(dateStr: string): string {
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('bs-BA', { day: 'numeric', month: 'numeric' }).format(date)
}

function getListName(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('bs-BA', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date)
}

function getPercentage(value: number, max: number): number {
  if (max === 0) return 0
  return Math.round((value / max) * 100)
}

function getTimelineHeight(amount: number): number {
  if (maxTimelineAmount.value === 0) return 0
  return Math.max((amount / maxTimelineAmount.value) * 100, 5) // Minimum 5% for visibility
}

onMounted(() => {
  loadData()
})
</script>
