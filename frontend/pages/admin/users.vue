<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Korisnici</h1>
        <p class="text-gray-600">Pregled svih registrovanih korisnika i njihovih OTP kodova</p>
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
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metoda</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Krediti</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OTP Kod</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registrovan</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
                <!-- User -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div>
                      <div class="text-sm font-medium text-gray-900">
                        {{ user.first_name || 'N/A' }} {{ user.last_name || '' }}
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
                </td>

                <!-- Registration Method -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="[
                      'px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full',
                      user.registration_method === 'phone'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    ]"
                  >
                    {{ user.registration_method === 'phone' ? 'Telefon' : 'Email' }}
                  </span>
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

                <!-- Credits -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ user.daily_credits_used || 0 }} / {{ user.daily_credits || 10 }}
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

const users = ref<any[]>([])
const searchQuery = ref('')
const pagination = ref({
  page: 1,
  per_page: 50,
  total: 0,
  pages: 0
})

// Computed stats
const totalUsers = computed(() => pagination.value.total)
const emailUsers = computed(() => users.value.filter(u => u.registration_method === 'email').length)
const phoneUsers = computed(() => users.value.filter(u => u.registration_method === 'phone').length)
const verifiedUsers = computed(() => users.value.filter(u => u.is_verified).length)

onMounted(() => {
  loadUsers()
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

useSeoMeta({
  title: 'Korisnici - Admin - Popust.ba',
  description: 'Admin panel za upravljanje korisnicima'
})
</script>
