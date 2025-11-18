<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Svi proizvodi</h1>
        <p class="text-gray-600">Pretražite kroz sve proizvode sa popustima</p>
      </div>

      <!-- Filters Section -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Search -->
          <div>
            <label for="search" class="block text-sm font-medium text-gray-700 mb-1">
              Pretraži proizvode
            </label>
            <input
              id="search"
              v-model="filters.search"
              type="text"
              placeholder="Unesite naziv proizvoda..."
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              @input="debouncedSearch"
            />
          </div>

          <!-- Category Filter -->
          <div>
            <label for="category" class="block text-sm font-medium text-gray-700 mb-1">
              Kategorija
            </label>
            <select
              id="category"
              v-model="filters.category"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              @change="loadProducts"
            >
              <option value="">Sve kategorije</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <!-- Business Filter -->
          <div>
            <label for="business" class="block text-sm font-medium text-gray-700 mb-1">
              Biznis
            </label>
            <select
              id="business"
              v-model="filters.business"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              @change="loadProducts"
            >
              <option value="">Svi biznisi</option>
              <option v-for="biz in businesses" :key="biz.id" :value="biz.id">{{ biz.name }}</option>
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
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()
const route = useRoute()
const router = useRouter()

// State
const products = ref<any[]>([])
const businesses = ref<any[]>([])
const categories = ref<string[]>([])
const isLoading = ref(true)
const currentPage = ref(1)
const totalPages = ref(1)
const totalProducts = ref(0)
const perPage = 24

// Filters
const filters = ref({
  search: '',
  category: '',
  business: ''
})

// Load filters from URL query params
onMounted(() => {
  filters.value.search = (route.query.search as string) || ''
  filters.value.category = (route.query.category as string) || ''
  filters.value.business = (route.query.business as string) || ''
  currentPage.value = parseInt(route.query.page as string) || 1

  loadBusinesses()
  loadCategories()
  loadProducts()
})

// Watch for route changes
watch(() => route.query, () => {
  filters.value.search = (route.query.search as string) || ''
  filters.value.category = (route.query.category as string) || ''
  filters.value.business = (route.query.business as string) || ''
  currentPage.value = parseInt(route.query.page as string) || 1
  loadProducts()
})

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

// Debounced search
let searchTimeout: NodeJS.Timeout
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    updateURL()
    loadProducts()
  }, 500)
}

async function loadBusinesses() {
  try {
    const data = await get('/api/businesses')
    businesses.value = data.businesses || []
  } catch (error) {
    console.error('Error loading businesses:', error)
  }
}

async function loadCategories() {
  try {
    const data = await get('/api/categories')
    categories.value = data.categories || []
  } catch (error) {
    console.error('Error loading categories:', error)
  }
}

async function loadProducts() {
  isLoading.value = true

  try {
    const params = new URLSearchParams()
    if (filters.value.search) params.append('search', filters.value.search)
    if (filters.value.category) params.append('category', filters.value.category)
    if (filters.value.business) params.append('business', filters.value.business)
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
    search: '',
    category: '',
    business: ''
  }
  currentPage.value = 1
  updateURL()
  loadProducts()
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
  loadProducts()
}

function updateURL() {
  const query: any = {}
  if (filters.value.search) query.search = filters.value.search
  if (filters.value.category) query.category = filters.value.category
  if (filters.value.business) query.business = filters.value.business
  if (currentPage.value > 1) query.page = currentPage.value.toString()

  router.replace({ query })
}

useSeoMeta({
  title: 'Svi proizvodi - AI Pijaca',
  description: 'Pretražite kroz sve proizvode sa popustima iz vaših omiljenih trgovina',
})
</script>
