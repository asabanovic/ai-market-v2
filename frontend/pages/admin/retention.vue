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
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Povratak korisnika</h1>
        <p class="text-gray-600">Pratite korisnike koji se vracaju nakon registracije</p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Danas se vratilo</p>
              <p class="text-3xl font-bold text-green-600">{{ stats.returned_today }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <Icon name="mdi:account-check" class="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Ukupno se vratilo</p>
              <p class="text-3xl font-bold text-purple-600">{{ stats.total_returned }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
              <Icon name="mdi:account-multiple-check" class="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Ukupno korisnika</p>
              <p class="text-3xl font-bold text-gray-900">{{ stats.total_users }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
              <Icon name="mdi:account-group" class="w-6 h-6 text-gray-600" />
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Stopa povratka</p>
              <p class="text-3xl font-bold text-blue-600">{{ stats.return_rate }}%</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <Icon name="mdi:percent" class="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      <!-- Daily Activity Chart -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">Dnevna aktivnost</h3>
          <div class="inline-flex rounded-md shadow-sm">
            <button
              @click="loadDailyActivity(7)"
              :class="[
                'px-3 py-1.5 text-sm font-medium rounded-l-md border',
                activityDays === 7
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              ]"
            >
              7 dana
            </button>
            <button
              @click="loadDailyActivity(14)"
              :class="[
                'px-3 py-1.5 text-sm font-medium border-t border-b',
                activityDays === 14
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              ]"
            >
              14 dana
            </button>
            <button
              @click="loadDailyActivity(30)"
              :class="[
                'px-3 py-1.5 text-sm font-medium rounded-r-md border',
                activityDays === 30
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              ]"
            >
              30 dana
            </button>
          </div>
        </div>

        <div v-if="chartLoading" class="flex items-center justify-center h-64">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>
        <div v-else class="h-64">
          <ClientOnly>
            <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
          </ClientOnly>
        </div>
      </div>

      <!-- Cohort Analysis -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Kohort analiza (po nedeljama registracije)</h3>
        <div v-if="cohortLoading" class="flex items-center justify-center h-32">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left py-3 px-4 text-sm font-medium text-gray-500">Nedelja registracije</th>
                <th class="text-center py-3 px-4 text-sm font-medium text-gray-500">Registrovano</th>
                <th class="text-center py-3 px-4 text-sm font-medium text-gray-500">Vratilo se</th>
                <th class="text-center py-3 px-4 text-sm font-medium text-gray-500">Stopa povratka</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cohort in cohorts" :key="cohort.week_start" class="border-b border-gray-100 hover:bg-gray-50">
                <td class="py-3 px-4 text-sm text-gray-900">{{ cohort.week_label }}</td>
                <td class="py-3 px-4 text-sm text-gray-600 text-center">{{ cohort.registered }}</td>
                <td class="py-3 px-4 text-sm text-gray-600 text-center">{{ cohort.returned }}</td>
                <td class="py-3 px-4 text-center">
                  <span
                    :class="[
                      'px-2 py-1 rounded-full text-xs font-medium',
                      cohort.return_rate >= 50 ? 'bg-green-100 text-green-800' :
                      cohort.return_rate >= 25 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    ]"
                  >
                    {{ cohort.return_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
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
            Danas ({{ stats.returned_today }})
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
            Ova nedelja
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
            Svi
          </button>
        </div>
      </div>

      <!-- Returning Users Table -->
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Korisnici koji su se vratili</h3>
        </div>

        <div v-if="loading" class="flex items-center justify-center h-64">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kontakt</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registrovan</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Poslednja aktivnost</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Aktivni dani</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Streak</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="u in users"
                :key="u.id"
                class="hover:bg-gray-50 cursor-pointer"
                :class="{ 'bg-green-50': u.is_active_today }"
                @click="openUserProfile(u.id)"
              >
                <!-- User -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div
                      v-if="u.is_active_today"
                      class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"
                      title="Aktivan danas"
                    />
                    <div>
                      <div class="text-sm font-medium text-gray-900">
                        {{ u.name || 'N/A' }}
                      </div>
                      <div class="text-sm text-gray-500">{{ u.city || 'N/A' }}</div>
                    </div>
                  </div>
                </td>

                <!-- Contact -->
                <td class="px-6 py-4">
                  <div class="text-sm text-gray-900">
                    <div v-if="u.email" class="flex items-center gap-2">
                      <Icon name="mdi:email" class="w-4 h-4 text-gray-400" />
                      {{ u.email }}
                    </div>
                    <div v-if="u.phone" class="flex items-center gap-2 mt-1">
                      <Icon name="mdi:cellphone" class="w-4 h-4 text-gray-400" />
                      {{ u.phone }}
                    </div>
                  </div>
                  <span
                    :class="[
                      'mt-1 px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full',
                      u.registration_method === 'phone'
                        ? 'bg-green-100 text-green-800'
                        : u.registration_method === 'google'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                    ]"
                  >
                    {{ u.registration_method === 'phone' ? 'Telefon' : u.registration_method === 'google' ? 'Google' : 'Email' }}
                  </span>
                </td>

                <!-- Registered -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ formatDate(u.registered_at) }}</div>
                  <div class="text-xs text-gray-500">prije {{ u.days_since_registration }} dana</div>
                </td>

                <!-- Last Activity -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ formatDateShort(u.last_activity_date) }}</div>
                  <div v-if="u.first_return_gap_days !== null" class="text-xs text-gray-500">
                    Vratio se nakon {{ u.first_return_gap_days }} dana
                  </div>
                </td>

                <!-- Active Days -->
                <td class="px-6 py-4 whitespace-nowrap text-center">
                  <span class="text-lg font-semibold text-purple-600">{{ u.unique_active_days }}</span>
                </td>

                <!-- Streak -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <span v-if="u.current_streak >= 3" class="text-lg">
                      {{ u.current_streak >= 7 ? '🔥' : '✨' }}
                    </span>
                    <div>
                      <div class="text-sm font-medium text-gray-900">{{ u.current_streak }} dana</div>
                      <div class="text-xs text-gray-500">Max: {{ u.longest_streak }}</div>
                    </div>
                  </div>
                </td>

                <!-- Status -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col gap-1">
                    <span
                      v-if="u.is_active_today"
                      class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800"
                    >
                      Online danas
                    </span>
                    <span
                      :class="[
                        'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full',
                        u.is_verified
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-yellow-100 text-yellow-800'
                      ]"
                    >
                      {{ u.is_verified ? 'Verifikovan' : 'Nije verifikovan' }}
                    </span>
                  </div>
                </td>
              </tr>

              <tr v-if="users.length === 0">
                <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                  Nema korisnika koji su se vratili u odabranom periodu
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pagination.pages > 1" class="bg-gray-50 px-6 py-4 flex items-center justify-between">
          <div class="text-sm text-gray-700">
            Stranica {{ pagination.page }} od {{ pagination.pages }} ({{ pagination.total }} korisnika)
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
              Sledeca
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

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
const chartLoading = ref(true)
const cohortLoading = ref(true)
const users = ref<any[]>([])
const activeFilter = ref('today')
const activityDays = ref(14)
const pagination = ref({
  page: 1,
  per_page: 50,
  total: 0,
  pages: 0
})
const stats = ref({
  total_users: 0,
  total_with_activity: 0,
  total_returned: 0,
  returned_today: 0,
  return_rate: 0
})
const cohorts = ref<any[]>([])
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
  }
}

onMounted(() => {
  loadReturningUsers()
  loadDailyActivity(activityDays.value)
  loadCohortAnalysis()
})

async function loadReturningUsers(page = 1) {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', page.toString())
    params.append('per_page', pagination.value.per_page.toString())
    params.append('filter', activeFilter.value)

    const data = await get(`/api/admin/retention/returning-users?${params.toString()}`)
    users.value = data.users
    pagination.value = data.pagination
    stats.value = data.stats
  } catch (error) {
    console.error('Error loading returning users:', error)
  } finally {
    loading.value = false
  }
}

async function loadDailyActivity(days: number) {
  activityDays.value = days
  chartLoading.value = true
  try {
    const data = await get(`/api/admin/retention/daily-activity?days=${days}`)

    chartData.value = {
      labels: data.daily_activity.map((d: any) => formatDateShort(d.date)),
      datasets: [
        {
          label: 'Novi korisnici',
          data: data.daily_activity.map((d: any) => d.new_users),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderRadius: 4
        },
        {
          label: 'Vratili se',
          data: data.daily_activity.map((d: any) => d.returning_users),
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderRadius: 4
        }
      ]
    }
  } catch (error) {
    console.error('Error loading daily activity:', error)
  } finally {
    chartLoading.value = false
  }
}

async function loadCohortAnalysis() {
  cohortLoading.value = true
  try {
    const data = await get('/api/admin/retention/cohort?weeks=8')
    cohorts.value = data.cohorts
  } catch (error) {
    console.error('Error loading cohort analysis:', error)
  } finally {
    cohortLoading.value = false
  }
}

function setFilter(filter: string) {
  activeFilter.value = filter
  pagination.value.page = 1
  loadReturningUsers()
}

function changePage(page: number) {
  if (page >= 1 && page <= pagination.value.pages) {
    pagination.value.page = page
    loadReturningUsers(page)
  }
}

function formatDate(dateString: string | null) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDateShort(dateString: string | null) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', {
    day: '2-digit',
    month: '2-digit'
  })
}

function openUserProfile(userId: string) {
  navigateTo(`/admin/users/${userId}`)
}

useSeoMeta({
  title: 'Povratak korisnika - Admin - Popust.ba',
  description: 'Admin panel za pracenje povratka korisnika'
})
</script>
