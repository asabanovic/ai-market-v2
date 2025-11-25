<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-gray-900">Admin Dashboard</h1>
        <p class="mt-1 text-sm text-gray-600">Pregled i upravljanje Popust.ba platformom</p>
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

      <template v-else>
        <!-- Quick Stats -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno korisnika</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_users || 0 }}</dd>
                </dl>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-sm text-gray-600">
                <span class="text-green-600 font-medium">+{{ stats.today_users || 0 }}</span> danas
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno biznisa</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_businesses || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno proizvoda</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_products || 0 }}</dd>
                </dl>
              </div>
            </div>
            <div class="mt-3 space-y-1">
              <div class="text-sm" :class="stats.products_without_embeddings > 0 ? 'text-orange-600' : 'text-green-600'">
                <span class="font-medium">{{ stats.products_with_embeddings || 0 }}/{{ stats.total_products || 0 }}</span> s embeddingom
                <span v-if="stats.products_without_embeddings > 0" class="text-orange-600 font-medium ml-1">
                  ({{ stats.products_without_embeddings }} čeka)
                </span>
              </div>
              <div class="text-sm" :class="stats.expired_products > 0 ? 'text-red-600' : 'text-green-600'">
                <span class="font-medium">{{ stats.active_products || 0 }}</span> aktivnih
                <span v-if="stats.expired_products > 0" class="text-red-600 font-medium ml-1">
                  ({{ stats.expired_products }} isteklo)
                </span>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno pretraga</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_searches || 0 }}</dd>
                </dl>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-sm text-gray-600">
                <span class="text-green-600 font-medium">+{{ stats.today_searches || 0 }}</span> danas
              </div>
            </div>
          </div>
        </div>

        <!-- Monthly Activity -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Mjesečna aktivnost</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <dt class="text-sm font-medium text-gray-500">Novi korisnici ovaj mjesec</dt>
              <dd class="text-xl font-semibold text-blue-600">{{ stats.monthly_users || 0 }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Pretrage ovaj mjesec</dt>
              <dd class="text-xl font-semibold text-green-600">{{ stats.monthly_searches || 0 }}</dd>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Recent Users -->
          <div class="bg-white rounded-lg border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">Najnoviji korisnici</h3>
            </div>
            <div class="divide-y divide-gray-200">
              <div v-for="user in recentUsers" :key="user.id" class="px-6 py-4">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ user.first_name || user.email }}</p>
                    <p class="text-sm text-gray-500">{{ user.email }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">{{ formatDate(user.created_at) }}</p>
                    <span v-if="user.is_admin" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Admin</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Searches -->
          <div class="bg-white rounded-lg border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">Najnovije pretrage</h3>
            </div>
            <div class="divide-y divide-gray-200">
              <div v-for="search in recentSearches" :key="search.id" class="px-6 py-4">
                <div class="flex justify-between">
                  <div class="flex-1">
                    <p class="text-sm text-gray-900 truncate">{{ search.query }}</p>
                    <div class="flex items-center space-x-2 mt-1">
                      <p class="text-xs text-gray-500">{{ formatDateTime(search.created_at) }}</p>
                      <span class="text-xs text-gray-400">•</span>
                      <p class="text-xs text-indigo-600">{{ search.user_name || 'Anonimni korisnik' }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Pagination -->
            <div v-if="searchesPagination && searchesPagination.pages > 1" class="px-6 py-3 border-t border-gray-200 bg-gray-50">
              <div class="flex items-center justify-between">
                <div class="text-sm text-gray-700">
                  Strana {{ searchesPagination.page }} od {{ searchesPagination.pages }}
                </div>
                <div class="flex space-x-2">
                  <button
                    v-if="searchesPagination.has_prev"
                    @click="loadSearches(searchesPagination.page - 1)"
                    class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
                  >
                    ← Prethodna
                  </button>
                  <button
                    v-if="searchesPagination.has_next"
                    @click="loadSearches(searchesPagination.page + 1)"
                    class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Sljedeća →
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Businesses -->
          <div class="bg-white rounded-lg border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">Najnoviji biznisi</h3>
            </div>
            <div class="divide-y divide-gray-200">
              <div v-for="business in recentBusinesses" :key="business.id" class="px-6 py-4">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ business.name }}</p>
                    <p class="text-sm text-gray-500">{{ business.city || 'Nepoznato' }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">ID: {{ business.id }}</p>
                    <p v-if="business.contact_phone" class="text-xs text-gray-500">{{ business.contact_phone }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Admin Actions -->
        <div class="mt-8 bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Admin akcije</h3>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <NuxtLink
              to="/business"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
              </svg>
              Upravljaj biznisom
            </NuxtLink>

            <NuxtLink
              to="/admin/products"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
              </svg>
              Svi proizvodi
            </NuxtLink>

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

const { post, get } = useApi()

const isLoading = ref(true)
const stats = ref<any>({})
const recentUsers = ref<any[]>([])
const recentSearches = ref<any[]>([])
const recentBusinesses = ref<any[]>([])
const searchesPagination = ref<any>(null)

onMounted(async () => {
  await loadDashboardData()
})

async function loadDashboardData() {
  isLoading.value = true

  try {
    const data = await get('/api/admin/stats')
    stats.value = data.stats || {}
    recentUsers.value = data.recent_users || []
    recentSearches.value = data.recent_searches || []
    recentBusinesses.value = data.recent_businesses || []
    searchesPagination.value = data.searches_pagination
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadSearches(page: number) {
  try {
    const data = await get(`/api/admin/dashboard?searches_page=${page}`)
    recentSearches.value = data.recent_searches || []
    searchesPagination.value = data.searches_pagination
  } catch (error) {
    console.error('Error loading searches:', error)
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

function formatDateTime(dateString: string) {
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
  title: 'Admin Dashboard - Popust.ba',
  description: 'Admin dashboard za upravljanje Popust.ba platformom',
})
</script>
