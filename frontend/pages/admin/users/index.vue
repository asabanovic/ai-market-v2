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
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Korisnici</h1>
        <p class="text-gray-600">Pregled svih registrovanih korisnika i njihovih OTP kodova</p>
      </div>

      <!-- Analytics Chart Section -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">Aktivnost korisnika</h3>
          <!-- Interval Selector -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">Prikaz po:</span>
            <div class="inline-flex rounded-md shadow-sm">
              <button
                @click="changeInterval('hour')"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-l-md border',
                  selectedInterval === 'hour'
                    ? 'bg-purple-600 text-white border-purple-600'
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
                    ? 'bg-purple-600 text-white border-purple-600'
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
                    ? 'bg-purple-600 text-white border-purple-600'
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
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
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

      <!-- Search -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex gap-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Pretraži po email, telefon, ime..."
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            @input="debouncedSearch"
          />
          <button
            @click="loadUsers"
            class="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition"
          >
            <Icon name="mdi:magnify" class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Ukupno korisnika</p>
              <p class="text-2xl font-bold text-gray-900">{{ totalUsers }}</p>
            </div>
            <Icon name="mdi:account-group" class="w-12 h-12 text-purple-600" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Email registracije</p>
              <p class="text-2xl font-bold text-gray-900">{{ emailUsers }}</p>
            </div>
            <Icon name="mdi:email" class="w-12 h-12 text-blue-600" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Google registracije</p>
              <p class="text-2xl font-bold text-gray-900">{{ googleUsers }}</p>
            </div>
            <Icon name="mdi:google" class="w-12 h-12 text-red-500" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Phone registracije</p>
              <p class="text-2xl font-bold text-gray-900">{{ phoneUsers }}</p>
            </div>
            <Icon name="mdi:cellphone" class="w-12 h-12 text-green-600" />
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Verifikovani</p>
              <p class="text-2xl font-bold text-gray-900">{{ verifiedUsers }}</p>
            </div>
            <Icon name="mdi:check-circle" class="w-12 h-12 text-teal-600" />
          </div>
        </div>
      </div>

      <!-- Users Table -->
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kontakt</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <div>Aktivnost (7 dana)</div>
                  <div class="flex gap-2 mt-1 font-normal normal-case">
                    <span class="flex items-center gap-1"><span class="w-2 h-2 bg-blue-400 rounded"></span>pretrage</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 bg-yellow-400 rounded"></span>proizvodi</span>
                    <span class="flex items-center gap-1"><span class="w-2 h-2 bg-purple-400 rounded"></span>interakcije</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Poslednja prijava</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prodavnice</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Krediti</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OTP Kod</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registrovan</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50 cursor-pointer" @click="openUserProfile(user.id)">
                <!-- User -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div>
                      <div class="text-sm font-medium text-gray-900 hover:text-indigo-600 transition-colors">
                        {{ user.first_name || 'N/A' }} {{ user.last_name || '' }}
                        <Icon name="mdi:open-in-new" class="w-3 h-3 inline ml-1 opacity-0 group-hover:opacity-100" />
                      </div>
                      <div class="text-sm text-gray-500">{{ user.city || 'N/A' }}</div>
                    </div>
                  </div>
                </td>

                <!-- Contact -->
                <td class="px-6 py-4">
                  <div class="text-sm text-gray-900">
                    <div v-if="user.email" class="flex items-center gap-2">
                      <Icon name="mdi:email" class="w-4 h-4 text-gray-400" />
                      {{ user.email }}
                    </div>
                    <div v-if="user.phone" class="flex items-center gap-2">
                      <Icon name="mdi:cellphone" class="w-4 h-4 text-gray-400" />
                      {{ user.phone }}
                    </div>
                  </div>
                  <span
                    :class="[
                      'mt-1 px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full',
                      user.registration_method === 'phone'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    ]"
                  >
                    {{ user.registration_method === 'phone' ? 'Telefon' : 'Email' }}
                  </span>
                </td>

                <!-- Activity Chart -->
                <td class="px-6 py-4">
                  <div v-if="userActivity[user.id]" class="flex items-end gap-0.5 h-8">
                    <div
                      v-for="(day, index) in userActivity[user.id]"
                      :key="index"
                      class="flex flex-col items-center"
                    >
                      <div class="flex gap-px">
                        <!-- Search bar (blue) -->
                        <div
                          class="w-1.5 bg-blue-400 rounded-t transition-all"
                          :style="{ height: `${Math.min(day.searches * 4, 24)}px` }"
                          :title="`${day.day}: ${day.searches} pretraga`"
                        ></div>
                        <!-- Proizvodi visits bar (yellow) -->
                        <div
                          class="w-1.5 bg-yellow-400 rounded-t transition-all"
                          :style="{ height: `${Math.min((day.proizvodi || 0) * 4, 24)}px` }"
                          :title="`${day.day}: ${day.proizvodi || 0} posjeta Proizvodi`"
                        ></div>
                        <!-- Engagement bar (purple) -->
                        <div
                          class="w-1.5 bg-purple-400 rounded-t transition-all"
                          :style="{ height: `${Math.min(day.engagements * 4, 24)}px` }"
                          :title="`${day.day}: ${day.engagements} interakcija`"
                        ></div>
                      </div>
                      <span class="text-[8px] text-gray-400 mt-0.5">{{ day.day.substring(0, 2) }}</span>
                    </div>
                  </div>
                  <div v-else-if="loadingActivity[user.id]" class="text-xs text-gray-400">
                    <Icon name="mdi:loading" class="w-4 h-4 animate-spin" />
                  </div>
                  <button
                    v-else
                    @click="loadUserActivity(user.id)"
                    class="text-xs text-purple-600 hover:text-purple-800"
                  >
                    Učitaj
                  </button>
                </td>

                <!-- Status -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col gap-1">
                    <span
                      v-if="user.is_admin"
                      class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800"
                    >
                      Admin
                    </span>
                    <span
                      :class="[
                        'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full',
                        user.is_verified
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      ]"
                    >
                      {{ user.is_verified ? 'Verifikovan' : 'Nije verifikovan' }}
                    </span>
                  </div>
                </td>

                <!-- Last Login -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div v-if="user.last_login" class="text-sm">
                    <div class="flex items-center gap-1 mb-1">
                      <Icon
                        :name="getDeviceIcon(user.last_login.device_type)"
                        class="w-4 h-4 text-gray-500"
                      />
                      <span class="text-gray-900">{{ user.last_login.device_type || 'N/A' }}</span>
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ user.last_login.os_name || '' }} {{ user.last_login.browser_name ? `/ ${user.last_login.browser_name}` : '' }}
                    </div>
                    <div class="text-xs text-gray-400 mt-1">
                      {{ formatDate(user.last_login.created_at) }}
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-400">
                    N/A
                  </div>
                </td>

                <!-- Preferred Stores -->
                <td class="px-6 py-4" @click.stop>
                  <div v-if="user.preferred_stores && user.preferred_stores.length > 0" class="flex flex-wrap gap-1 max-w-xs">
                    <span
                      v-for="store in user.preferred_stores.slice(0, 3)"
                      :key="store.id"
                      class="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700"
                      :title="store.name"
                    >
                      {{ truncateStoreName(store.name) }}
                    </span>
                    <button
                      v-if="user.preferred_stores.length > 3"
                      @click="showStoresModal(user)"
                      class="px-2 py-0.5 text-xs rounded bg-purple-100 text-purple-700 hover:bg-purple-200 cursor-pointer"
                    >
                      +{{ user.preferred_stores.length - 3 }}
                    </button>
                  </div>
                  <div v-else class="text-sm text-gray-400">
                    Sve
                  </div>
                </td>

                <!-- Credits -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div>{{ user.weekly_credits_used || 0 }} / {{ user.weekly_credits || 10 }} <span class="text-gray-400 text-xs">tjedno</span></div>
                  <div v-if="user.extra_credits" class="text-purple-600 text-xs">+{{ user.extra_credits }} ekstra</div>
                </td>

                <!-- OTP Code -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div v-if="user.latest_otp" class="text-sm">
                    <div class="font-mono font-bold text-lg text-purple-600">
                      {{ user.latest_otp.code }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      <div v-if="!user.latest_otp.expired && !user.latest_otp.is_used" class="text-green-600">
                        ✓ Aktivan
                      </div>
                      <div v-else-if="user.latest_otp.is_used" class="text-gray-400">
                        Iskorišten
                      </div>
                      <div v-else class="text-red-600">
                        Istekao
                      </div>
                      <div class="mt-1">
                        {{ formatDate(user.latest_otp.created_at) }}
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-400">
                    N/A
                  </div>
                </td>

                <!-- Created At -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(user.created_at) }}
                </td>

                <!-- Actions -->
                <td class="px-6 py-4 whitespace-nowrap" @click.stop>
                  <button
                    @click="openUserProfile(user.id)"
                    class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                  >
                    <Icon name="mdi:account-details" class="w-4 h-4 mr-1" />
                    Profil
                  </button>
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
              Sledeća
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Stores Modal -->
    <div
      v-if="storesModalUser"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="storesModalUser = null"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">
            Prodavnice - {{ storesModalUser.first_name || storesModalUser.email }}
          </h3>
          <button
            @click="storesModalUser = null"
            class="text-gray-400 hover:text-gray-600"
          >
            <Icon name="mdi:close" class="w-6 h-6" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[60vh]">
          <div class="space-y-2">
            <div
              v-for="store in storesModalUser.preferred_stores"
              :key="store.id"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <Icon name="mdi:store" class="w-5 h-5 text-purple-600" />
              <span class="text-gray-900">{{ store.name }}</span>
            </div>
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
  middleware: 'auth',
  layout: 'default'
})

const { get } = useApi()
const { user } = useAuth()

// Redirect non-admins
if (!user.value?.is_admin) {
  navigateTo('/')
}

const users = ref<any[]>([])
const searchQuery = ref('')
const pagination = ref({
  page: 1,
  per_page: 50,
  total: 0,
  pages: 0
})
const userActivity = ref<Record<string, any[]>>({})
const loadingActivity = ref<Record<string, boolean>>({})
const storesModalUser = ref<any>(null)

// Analytics chart state
const selectedInterval = ref('day')
const analyticsData = ref<any>(null)
const chartData = ref<any>(null)
const chartLoading = ref(true)

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

// Stats from server (not computed from current page)
const stats = ref({
  total: 0,
  email: 0,
  google: 0,
  phone: 0,
  verified: 0
})

// Computed stats from server data
const totalUsers = computed(() => stats.value.total)
const emailUsers = computed(() => stats.value.email)
const googleUsers = computed(() => stats.value.google)
const phoneUsers = computed(() => stats.value.phone)
const verifiedUsers = computed(() => stats.value.verified)

onMounted(() => {
  loadUsers()
  loadAnalytics()
})

async function loadUsers(page = 1) {
  try {
    const params = new URLSearchParams()
    params.append('page', page.toString())
    params.append('per_page', pagination.value.per_page.toString())
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }

    const data = await get(`/api/admin/users?${params.toString()}`)
    users.value = data.users
    pagination.value = data.pagination

    // Update stats from server response
    if (data.stats) {
      stats.value = data.stats
    }

    // Load activity for all users after loading
    nextTick(() => {
      loadAllUserActivities()
    })
  } catch (error) {
    console.error('Error loading users:', error)
  }
}

function changePage(page: number) {
  if (page >= 1 && page <= pagination.value.pages) {
    pagination.value.page = page
    loadUsers(page)
  }
}

let searchTimeout: NodeJS.Timeout
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadUsers(1)
  }, 500)
}

function formatDate(dateString: string) {
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

function getDeviceIcon(deviceType: string | null): string {
  switch (deviceType) {
    case 'mobile':
      return 'mdi:cellphone'
    case 'tablet':
      return 'mdi:tablet'
    case 'desktop':
      return 'mdi:monitor'
    default:
      return 'mdi:help-circle-outline'
  }
}

function truncateStoreName(name: string): string {
  if (name.length > 12) {
    return name.substring(0, 10) + '...'
  }
  return name
}

function showStoresModal(user: any) {
  storesModalUser.value = user
}

async function loadUserActivity(userId: string) {
  loadingActivity.value[userId] = true
  try {
    const data = await get(`/api/admin/users/${userId}/activity`)
    userActivity.value[userId] = data.activity
  } catch (error) {
    console.error('Error loading user activity:', error)
  } finally {
    loadingActivity.value[userId] = false
  }
}

async function loadAllUserActivities() {
  // Load activity for all visible users in parallel
  const promises = users.value.map(u => loadUserActivity(u.id))
  await Promise.all(promises)
}

function openUserProfile(userId: string) {
  navigateTo(`/admin/users/${userId}`)
}

// Analytics functions
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

useSeoMeta({
  title: 'Korisnici - Admin - Popust.ba',
  description: 'Admin panel za upravljanje korisnicima'
})
</script>
