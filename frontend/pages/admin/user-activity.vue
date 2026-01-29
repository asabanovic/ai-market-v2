<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header with Back Button -->
      <div class="mb-8">
        <NuxtLink
          to="/admin"
          class="inline-flex items-center text-sm text-gray-500 hover:text-purple-600 mb-4 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-4 h-4 mr-1" />
          Nazad na Dashboard
        </NuxtLink>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Aktivnost korisnika</h1>
        <p class="text-gray-600">Pratite promjene profila i aktivnosti korisnika</p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Zadnja 24h</p>
              <p class="text-3xl font-bold text-green-600">{{ stats.last_24h }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <Icon name="mdi:clock-outline" class="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Zadnjih 7 dana</p>
              <p class="text-3xl font-bold text-purple-600">{{ stats.last_7d }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
              <Icon name="mdi:calendar-week" class="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Zadnjih 30 dana</p>
              <p class="text-3xl font-bold text-blue-600">{{ stats.last_30d }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <Icon name="mdi:calendar-month" class="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Ukupno</p>
              <p class="text-3xl font-bold text-gray-900">{{ stats.total }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
              <Icon name="mdi:history" class="w-6 h-6 text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      <!-- Filter Buttons -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex flex-wrap gap-3">
          <button
            @click="setFilter('today')"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              activeFilter === 'today'
                ? 'bg-green-600 text-white'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            ]"
          >
            <Icon name="mdi:calendar-today" class="w-4 h-4 mr-1" />
            Danas
          </button>
          <button
            @click="setFilter('week')"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              activeFilter === 'week'
                ? 'bg-purple-600 text-white'
                : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
            ]"
          >
            <Icon name="mdi:calendar-week" class="w-4 h-4 mr-1" />
            Ova sedmica
          </button>
          <button
            @click="setFilter('month')"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              activeFilter === 'month'
                ? 'bg-blue-600 text-white'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            ]"
          >
            <Icon name="mdi:calendar-month" class="w-4 h-4 mr-1" />
            Ovaj mjesec
          </button>
          <button
            @click="setFilter('all')"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              activeFilter === 'all'
                ? 'bg-gray-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            <Icon name="mdi:calendar" class="w-4 h-4 mr-1" />
            Sve
          </button>
        </div>
      </div>

      <!-- Activity Logs Table -->
      <div class="bg-white rounded-lg shadow-md overflow-hidden mb-8">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Dnevnik aktivnosti</h3>
        </div>

        <div v-if="loading" class="flex items-center justify-center h-64">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tip aktivnosti</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Promjene</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Adresa</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vrijeme</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="log in logs"
                :key="log.id"
                class="hover:bg-gray-50"
              >
                <!-- User -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div class="text-sm font-medium text-gray-900">
                      {{ log.user_name || 'N/A' }}
                    </div>
                    <div class="text-sm text-gray-500">{{ log.user_email }}</div>
                  </div>
                </td>

                <!-- Activity Type -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="[
                      'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full',
                      getActivityTypeBadgeClass(log.activity_type)
                    ]"
                  >
                    {{ getActivityTypeLabel(log.activity_type) }}
                  </span>
                </td>

                <!-- Changes -->
                <td class="px-6 py-4">
                  <div v-if="log.changes" class="text-sm">
                    <div
                      v-for="(change, field) in log.changes"
                      :key="field"
                      class="mb-1"
                    >
                      <span class="font-medium text-gray-700">{{ getFieldLabel(field) }}:</span>
                      <div class="flex items-center gap-2 text-xs">
                        <span class="text-red-600 line-through">{{ formatValue(change.old) }}</span>
                        <Icon name="mdi:arrow-right" class="w-3 h-3 text-gray-400" />
                        <span class="text-green-600">{{ formatValue(change.new) }}</span>
                      </div>
                    </div>
                  </div>
                  <span v-else class="text-gray-400 text-sm">-</span>
                </td>

                <!-- IP Address -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-500">{{ log.ip_address || 'N/A' }}</div>
                </td>

                <!-- Time -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ formatDateTime(log.created_at) }}</div>
                </td>
              </tr>

              <tr v-if="logs.length === 0">
                <td colspan="5" class="px-6 py-12 text-center text-gray-500">
                  Nema aktivnosti u odabranom periodu
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pagination.pages > 1" class="bg-gray-50 px-6 py-4 flex items-center justify-between">
          <div class="text-sm text-gray-700">
            Stranica {{ pagination.page }} od {{ pagination.pages }} ({{ pagination.total }} zapisa)
          </div>
          <div class="flex gap-2">
            <button
              @click="changePage(pagination.page - 1)"
              :disabled="pagination.page === 1"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Prethodna
            </button>
            <button
              @click="changePage(pagination.page + 1)"
              :disabled="pagination.page === pagination.pages"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
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
definePageMeta({
  middleware: 'auth',
  layout: 'default'
})

const { get } = useApi()
const { user } = useAuth()

// Redirect non-admins
if (!user.value?.is_admin) {
  navigateTo('/')
}

const loading = ref(true)
const logs = ref<any[]>([])
const activeFilter = ref('all')
const pagination = ref({
  page: 1,
  per_page: 50,
  total: 0,
  pages: 0
})
const stats = ref({
  total: 0,
  last_24h: 0,
  last_7d: 0,
  last_30d: 0,
  by_type: {} as Record<string, number>
})

onMounted(() => {
  loadActivityLogs()
  loadStats()
})

async function loadActivityLogs(page = 1) {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', page.toString())
    params.append('per_page', pagination.value.per_page.toString())
    params.append('filter', activeFilter.value)

    const data = await get(`/api/admin/activity/logs?${params.toString()}`)
    logs.value = data.logs
    pagination.value = {
      page: data.page,
      per_page: data.per_page,
      total: data.total,
      pages: data.pages
    }
  } catch (error) {
    console.error('Error loading activity logs:', error)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const data = await get('/api/admin/activity/stats')
    stats.value = data
  } catch (error) {
    console.error('Error loading activity stats:', error)
  }
}

function setFilter(filter: string) {
  activeFilter.value = filter
  pagination.value.page = 1
  loadActivityLogs()
}

function changePage(page: number) {
  if (page >= 1 && page <= pagination.value.pages) {
    pagination.value.page = page
    loadActivityLogs(page)
  }
}

function getActivityTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'profile_update': 'Azuriranje profila',
    'login': 'Prijava',
    'logout': 'Odjava',
    'password_change': 'Promjena lozinke',
    'settings_change': 'Promjena postavki'
  }
  return labels[type] || type
}

function getActivityTypeBadgeClass(type: string): string {
  const classes: Record<string, string> = {
    'profile_update': 'bg-blue-100 text-blue-800',
    'login': 'bg-green-100 text-green-800',
    'logout': 'bg-gray-100 text-gray-800',
    'password_change': 'bg-yellow-100 text-yellow-800',
    'settings_change': 'bg-purple-100 text-purple-800'
  }
  return classes[type] || 'bg-gray-100 text-gray-800'
}

function getFieldLabel(field: string): string {
  const labels: Record<string, string> = {
    'first_name': 'Ime',
    'last_name': 'Prezime',
    'phone': 'Telefon',
    'city': 'Grad',
    'city_id': 'Grad ID',
    'notification_preferences': 'Notifikacije',
    'email_preferences': 'Email postavke'
  }
  return labels[field] || field
}

function formatValue(value: any): string {
  if (value === null || value === undefined) return 'prazno'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function formatDateTime(dateString: string | null) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

useSeoMeta({
  title: 'Aktivnost korisnika - Admin - Popust.ba',
  description: 'Admin panel za pracenje aktivnosti korisnika'
})
</script>
