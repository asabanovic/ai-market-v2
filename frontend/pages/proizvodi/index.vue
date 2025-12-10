<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Pregledaj proizvode</h1>
        <p class="text-gray-600">Filtrirajte po kategoriji i prodavnici da pronađete najbolje popuste</p>
      </div>

      <!-- Filters Section -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <!-- Marketing Message -->
        <div class="bg-purple-50 border-l-4 border-purple-500 p-4 mb-6">
          <div class="flex items-start">
            <svg class="w-6 h-6 text-purple-600 mr-3 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-purple-900">
                Tražite određeni proizvod? Koristite pametnu pretragu na <NuxtLink to="/" class="underline hover:text-purple-600">početnoj stranici</NuxtLink> za najbolje rezultate!
              </p>
              <p class="text-xs text-purple-700 mt-1">
                Ovdje možete pregledati proizvode po kategoriji i prodavnici.
              </p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Business Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Prodavnica
            </label>
            <StoreSelector
              v-model="selectedStoreIds"
              :stores="businesses"
              @update:model-value="onStoresChange"
            />
          </div>

          <!-- Sort Filter -->
          <div>
            <label for="sort" class="block text-sm font-medium text-gray-700 mb-1">
              Sortiraj po
            </label>
            <select
              id="sort"
              v-model="filters.sort"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              @change="onSortChange"
            >
              <option value="discount_desc">Najveći popust</option>
              <option value="price_asc">Najjeftinije</option>
              <option value="price_desc">Najskuplje</option>
              <option value="newest">Najnovije</option>
            </select>
          </div>
        </div>

        <!-- Filter Actions -->
        <div class="mt-4 flex justify-between items-center">
          <div class="text-sm text-gray-600">
            Pronađeno: <strong>{{ totalProducts }}</strong> proizvoda
          </div>
          <button
            @click="resetFilters"
            class="text-sm text-purple-600 hover:text-purple-800 font-medium"
          >
            Resetuj filtere
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-purple-600">
          <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="text-lg">Učitavanje proizvoda...</span>
        </div>
      </div>

      <!-- Products Grid -->
      <div v-else-if="products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
        <ProductCard v-for="product in products" :key="product.id" :product="product" />
      </div>

      <!-- No Products Found -->
      <div v-else-if="!isLoading && products.length === 0" class="bg-white rounded-lg shadow-md p-12 text-center">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Nema proizvoda</h3>
        <p class="text-gray-600 mb-4">Pokušajte da promenite filtere ili pretražite drugačije</p>
        <button
          @click="resetFilters"
          class="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition duration-200"
        >
          Resetuj filtere
        </button>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1 && !isLoading" class="flex justify-center items-center space-x-2">
        <button
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
          class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Prethodna
        </button>

        <div class="flex space-x-1">
          <button
            v-for="page in visiblePages"
            :key="page"
            @click="changePage(page)"
            :class="[
              'px-4 py-2 border rounded-md',
              page === currentPage
                ? 'bg-purple-600 text-white border-purple-600'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            ]"
          >
            {{ page }}
          </button>
        </div>

        <button
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
          class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Sledeća
        </button>
      </div>
    </div>

    <!-- Registration Prompt -->
    <RegistrationPrompt
      v-if="showRegistrationPrompt"
      :product-count="totalActiveProducts"
      @close="showRegistrationPrompt = false"
    />
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()
const { user, authReady } = useAuth()
const route = useRoute()
const router = useRouter()
const { trackPageView, trackFilter, trackPagination } = useActivityTracking()

// State
const products = ref<any[]>([])
const showRegistrationPrompt = ref(false)
const totalActiveProducts = ref(0)
const businesses = ref<any[]>([])
const isLoading = ref(true)
const currentPage = ref(1)
const totalPages = ref(1)
const totalProducts = ref(0)
const perPage = 24
const selectedStoreIds = ref<number[]>([])

// Filters
const filters = ref({
  sort: 'discount_desc'
})

// Initialize page when auth is ready
const initPage = () => {
  // Redirect non-logged-in users to login page
  if (!user.value) {
    router.push('/prijava?redirect=/proizvodi')
    return
  }

  filters.value.sort = (route.query.sort as string) || 'discount_desc'
  currentPage.value = parseInt(route.query.page as string) || 1

  // Parse store IDs from URL
  const storeParam = route.query.stores as string
  if (storeParam) {
    selectedStoreIds.value = storeParam.split(',').map(id => parseInt(id)).filter(id => !isNaN(id))
  }

  // Track page view
  trackPageView('proizvodi', {
    sort: filters.value.sort,
    page: currentPage.value,
    stores: selectedStoreIds.value
  })

  loadBusinesses()
  loadProducts()
}

// Wait for auth to be ready before initializing
onMounted(() => {
  if (authReady.value) {
    initPage()
  }
})

// Watch for authReady to become true (if not ready on mount)
watch(authReady, (ready) => {
  if (ready) {
    initPage()
  }
})

// Watch for route changes
watch(() => route.query, () => {
  filters.value.sort = (route.query.sort as string) || 'discount_desc'
  currentPage.value = parseInt(route.query.page as string) || 1

  const storeParam = route.query.stores as string
  if (storeParam) {
    selectedStoreIds.value = storeParam.split(',').map(id => parseInt(id)).filter(id => !isNaN(id))
  } else {
    selectedStoreIds.value = []
  }
  loadProducts()
})

function onStoresChange() {
  currentPage.value = 1
  // Track store filter change
  trackFilter('proizvodi', 'stores', selectedStoreIds.value)
  loadProducts()
}

function onSortChange() {
  currentPage.value = 1
  // Track sort filter change
  trackFilter('proizvodi', 'sort', filters.value.sort)
  loadProducts()
}

// Computed
const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

async function loadBusinesses() {
  try {
    const data = await get('/api/businesses')
    businesses.value = data.businesses || []
  } catch (error) {
    console.error('Error loading businesses:', error)
  }
}

async function loadProducts() {
  isLoading.value = true

  try {
    const params = new URLSearchParams()
    if (selectedStoreIds.value.length > 0) {
      params.append('stores', selectedStoreIds.value.join(','))
    }
    if (filters.value.sort) params.append('sort', filters.value.sort)
    params.append('page', currentPage.value.toString())
    params.append('per_page', perPage.toString())

    const data = await get(`/api/products?${params.toString()}`)

    products.value = data.products || []
    totalPages.value = data.total_pages || 1
    totalProducts.value = data.total || 0

    updateURL()
  } catch (error) {
    console.error('Error loading products:', error)
    products.value = []
  } finally {
    isLoading.value = false
  }
}

function resetFilters() {
  filters.value = {
    sort: 'discount_desc'
  }
  selectedStoreIds.value = []
  currentPage.value = 1
  updateURL()
  loadProducts()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page

  // Track pagination
  trackPagination('proizvodi', page)

  window.scrollTo({ top: 0, behavior: 'smooth' })
  loadProducts()
}

function updateURL() {
  const query: any = {}
  if (selectedStoreIds.value.length > 0) query.stores = selectedStoreIds.value.join(',')
  if (filters.value.sort && filters.value.sort !== 'discount_desc') query.sort = filters.value.sort
  if (currentPage.value > 1) query.page = currentPage.value.toString()

  router.replace({ query })
}

useSeoMeta({
  title: 'Svi proizvodi - Popust.ba',
  description: 'Pretražite kroz sve proizvode sa popustima iz vaših omiljenih trgovina',
})
</script>
