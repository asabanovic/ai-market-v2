<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center gap-4">
          <NuxtLink to="/admin" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">PWA Install Analytics</h1>
            <p class="mt-1 text-sm text-gray-600">Pratite instalacije PWA aplikacije</p>
          </div>
        </div>
      </div>

      <!-- Days Filter -->
      <div class="mb-6 flex items-center gap-4">
        <label class="text-sm text-gray-600">Period:</label>
        <select v-model="days" @change="fetchData" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option :value="7">Zadnjih 7 dana</option>
          <option :value="14">Zadnjih 14 dana</option>
          <option :value="30">Zadnjih 30 dana</option>
          <option :value="90">Zadnjih 90 dana</option>
        </select>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-purple-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Ucitavanje...</span>
        </div>
      </div>

      <template v-else-if="data">
        <!-- Funnel Stats -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Install Funnel</h2>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div
              v-for="(step, index) in funnelSteps"
              :key="step.key"
              class="text-center p-4 rounded-lg"
              :class="step.bgClass"
            >
              <div class="text-2xl mb-1">{{ step.icon }}</div>
              <div class="text-xs text-gray-500 mb-1">{{ step.label }}</div>
              <div class="text-2xl font-bold" :class="step.textClass">
                {{ data.events[step.key]?.total || 0 }}
              </div>
              <!-- Conversion arrow -->
              <div v-if="index > 0 && index < 3" class="text-xs mt-2 text-gray-400">
                {{ getConversionFromPrevious(step.key, index) }}% conv.
              </div>
            </div>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Ukupno instalacija</div>
            <div class="text-3xl font-bold text-green-600">{{ data.summary.total_installs }}</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Prikazanih promptova</div>
            <div class="text-3xl font-bold text-blue-600">{{ data.summary.total_prompts }}</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Standalone posjeta</div>
            <div class="text-3xl font-bold text-purple-600">{{ data.events.standalone_launch?.total || 0 }}</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Conversion Rate</div>
            <div class="text-3xl font-bold text-gray-900">{{ data.conversion?.overall || 0 }}%</div>
          </div>
        </div>

        <!-- Platform Breakdown -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Platforme</h2>
          <div class="grid grid-cols-3 gap-4">
            <div
              v-for="platform in platformStats"
              :key="platform.name"
              class="text-center p-4 rounded-lg"
              :class="platform.bgClass"
            >
              <div class="text-2xl mb-1">{{ platform.icon }}</div>
              <div class="text-xs text-gray-500 mb-1">{{ platform.label }}</div>
              <div class="text-xl font-bold" :class="platform.textClass">
                {{ data.platforms[platform.name]?.installed || 0 }}
              </div>
            </div>
          </div>
        </div>

        <!-- Daily Trend -->
        <div v-if="data.daily_trend && data.daily_trend.length > 0" class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Dnevni trend</h2>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Datum</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Prikazano</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Prihvaceno</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Odbijeno</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Instalirano</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Standalone</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="day in data.daily_trend" :key="day.date" class="hover:bg-gray-50">
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{{ formatDate(day.date) }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-blue-600">{{ day.events?.prompt_shown || 0 }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-green-600">{{ day.events?.prompt_accepted || 0 }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-red-600">{{ day.events?.prompt_dismissed || 0 }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm font-bold text-green-700">{{ day.events?.installed || 0 }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-purple-600">{{ day.events?.standalone_launch || 0 }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Users Table -->
        <div class="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
          <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">Korisnici koji su instalirali</h2>
          </div>

          <div v-if="!data.users_installed || data.users_installed.length === 0" class="p-6 text-center text-gray-500">
            Nema korisnika za prikazati
          </div>

          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Korisnik</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Platforma</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Browser</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Instalirao</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="user in data.users_installed" :key="user.user_id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">{{ user.name || 'N/A' }}</div>
                    <div class="text-xs text-gray-500">{{ user.email }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      class="px-2 py-1 text-xs rounded-full"
                      :class="getPlatformBadgeClass(user.platform)"
                    >
                      {{ getPlatformIcon(user.platform) }} {{ user.platform || 'N/A' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ user.browser || 'N/A' }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(user.installed_at) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="text-red-600 mb-4">{{ error }}</div>
        <button @click="fetchData" class="px-4 py-2 bg-purple-600 text-white rounded-lg">
          Pokusaj ponovo
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'admin'
})

const { get } = useApi()

const days = ref(30)
const isLoading = ref(true)
const error = ref<string | null>(null)
const data = ref<any>(null)

const funnelSteps = [
  { key: 'prompt_shown', label: 'Prikazano', icon: '👁️', bgClass: 'bg-blue-50', textClass: 'text-blue-700' },
  { key: 'prompt_accepted', label: 'Prihvaceno', icon: '✅', bgClass: 'bg-green-50', textClass: 'text-green-700' },
  { key: 'installed', label: 'Instalirano', icon: '📱', bgClass: 'bg-purple-50', textClass: 'text-purple-700' },
  { key: 'prompt_dismissed', label: 'Odbijeno', icon: '❌', bgClass: 'bg-red-50', textClass: 'text-red-700' },
  { key: 'standalone_launch', label: 'Koristeno', icon: '🚀', bgClass: 'bg-yellow-50', textClass: 'text-yellow-700' },
]

const platformStats = [
  { name: 'android', label: 'Android', icon: '🤖', bgClass: 'bg-green-50', textClass: 'text-green-700' },
  { name: 'ios', label: 'iOS', icon: '🍎', bgClass: 'bg-gray-100', textClass: 'text-gray-700' },
  { name: 'desktop', label: 'Desktop', icon: '🖥️', bgClass: 'bg-blue-50', textClass: 'text-blue-700' },
]

async function fetchData() {
  isLoading.value = true
  error.value = null

  try {
    const response = await get(`/api/admin/analytics/pwa-install?days=${days.value}`)
    data.value = response
  } catch (e: any) {
    error.value = e.message || 'Greska pri ucitavanju'
    console.error('Failed to fetch PWA analytics:', e)
  } finally {
    isLoading.value = false
  }
}

function getConversionFromPrevious(key: string, index: number): string {
  if (index === 0) return '100'
  const prevKey = funnelSteps[index - 1]?.key
  if (!prevKey) return '0'
  const from = data.value?.events[prevKey]?.total || 0
  const to = data.value?.events[key]?.total || 0
  if (from === 0) return '0'
  return ((to / from) * 100).toFixed(0)
}

function getPlatformBadgeClass(platform: string): string {
  const classes: Record<string, string> = {
    'android': 'bg-green-100 text-green-700',
    'ios': 'bg-gray-100 text-gray-700',
    'desktop': 'bg-blue-100 text-blue-700'
  }
  return classes[platform] || 'bg-gray-100 text-gray-700'
}

function getPlatformIcon(platform: string): string {
  const icons: Record<string, string> = {
    'android': '🤖',
    'ios': '🍎',
    'desktop': '🖥️'
  }
  return icons[platform] || '📱'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('hr-HR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

onMounted(() => {
  fetchData()
})
</script>
