<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Pregledaj proizvode</h1>
        <p class="text-gray-600">Filtrirajte po kategoriji i prodavnici da pronađete najbolje popuste</p>
      </div>

      <!-- Followed Stores Section -->
      <div v-if="followedStores.length > 0" class="bg-white rounded-lg shadow-md p-4 mb-4">
        <h2 class="text-lg font-semibold text-gray-900 mb-3">Moje prodavnice</h2>
        <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
          <NuxtLink
            v-for="store in followedStores"
            :key="store.id"
            :to="store.slug ? `/prodavnica/${store.slug}` : `/radnja/${store.id}`"
            class="flex flex-col items-center p-2 rounded-lg hover:bg-gray-50 transition-colors group"
          >
            <div class="w-12 h-12 rounded-full bg-gray-100 overflow-hidden mb-2 flex items-center justify-center border border-gray-200 group-hover:border-purple-300">
              <img
                v-if="store.logo"
                :src="store.logo"
                :alt="store.name"
                class="w-full h-full object-cover"
              />
              <svg v-else class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <span class="text-xs text-gray-700 text-center line-clamp-2 group-hover:text-purple-600">{{ store.name }}</span>
          </NuxtLink>
        </div>
      </div>

      <!-- Category Selector -->
      <div class="bg-white rounded-lg shadow-md p-4 mb-4">
        <CategorySelector
          v-model="selectedCategory"
          :category-counts="categoryCounts"
          :disabled="!canPaginate"
          :current-sort="filters.sort"
          @update:model-value="onCategoryChange"
          @sort-cheapest="onSortCheapest"
        />
        <!-- Credits warning for category selector -->
        <div v-if="!canPaginate" class="mt-3 text-sm text-amber-700 flex items-center gap-2">
          <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Filteri su onemogućeni jer nemate dovoljno kredita. <button @click="showCreditsPopup = true" class="text-purple-600 font-medium hover:underline">Zaradite kredite</button></span>
        </div>
      </div>

      <!-- Filters Section -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Business Filter -->
          <div :class="{ 'opacity-50 pointer-events-none': !canPaginate }">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Prodavnica
            </label>
            <StoreSelector
              v-model="selectedStoreIds"
              :stores="businesses"
              :disabled="!canPaginate"
              @update:model-value="onStoresChange"
            />
          </div>

          <!-- Sort Filter -->
          <div :class="{ 'opacity-50': !canPaginate }">
            <label for="sort" class="block text-sm font-medium text-gray-700 mb-1">
              Sortiraj po
            </label>
            <select
              id="sort"
              v-model="filters.sort"
              :disabled="!canPaginate"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:cursor-not-allowed disabled:bg-gray-100"
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
      <div v-if="totalPages > 1 && !isLoading" class="flex flex-col items-center space-y-3">
        <!-- Low credits warning -->
        <div v-if="!canPaginate && currentPage === 1" class="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm text-amber-800 flex items-center gap-2">
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Nemate dovoljno kredita za pregled više stranica. <button @click="showCreditsPopup = true" class="text-purple-600 font-medium hover:underline">Zaradite kredite</button></span>
        </div>

        <div class="flex justify-center items-center space-x-2">
          <button
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Prije
          </button>

          <div class="flex space-x-1">
            <template v-for="(page, index) in visiblePages" :key="index">
              <!-- Ellipsis (not clickable) -->
              <span
                v-if="page === '...'"
                class="px-2 py-2 text-gray-500"
              >
                ...
              </span>
              <!-- Page number button -->
              <button
                v-else
                @click="changePage(page as number)"
                :disabled="(page as number) > 1 && !canPaginate"
                :class="[
                  'px-3 py-2 border rounded-md text-sm',
                  page === currentPage
                    ? 'bg-purple-600 text-white border-purple-600'
                    : (page as number) > 1 && !canPaginate
                      ? 'border-gray-200 text-gray-400 cursor-not-allowed bg-gray-50'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                ]"
              >
                {{ page }}
              </button>
            </template>
          </div>

          <button
            :disabled="currentPage === totalPages || !canPaginate"
            @click="changePage(currentPage + 1)"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Dalje
          </button>
        </div>
      </div>
    </div>

    <!-- Registration Prompt -->
    <RegistrationPrompt
      v-if="showRegistrationPrompt"
      :product-count="totalActiveProducts"
      @close="showRegistrationPrompt = false"
    />

    <!-- Earn Credits Popup -->
    <EarnCreditsPopup
      :is-visible="showCreditsPopup"
      :credits-needed="creditsNeeded"
      :credits-remaining="creditsRemaining"
      @close="showCreditsPopup = false"
      @go-to-products="goToProductsToEngage"
    />
  </div>
</template>

<script setup lang="ts">
const { get, post } = useApi()
const { user, authReady } = useAuth()
const route = useRoute()
const router = useRouter()
const { trackPageView, trackFilter, trackPagination } = useActivityTracking()
const config = useRuntimeConfig()

// State
const products = ref<any[]>([])
const showRegistrationPrompt = ref(false)
const totalActiveProducts = ref(0)
const businesses = ref<any[]>([])
const isLoading = ref(true)
const followedStores = ref<any[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const totalProducts = ref(0)
const perPage = 24
const selectedStoreIds = ref<number[]>([])
const selectedCategory = ref<string | null>(null)
const categoryCounts = ref<Record<string, number>>({})

// Credits popup state
const showCreditsPopup = ref(false)
const creditsNeeded = ref(3)
const creditsRemaining = ref(0)
const canPaginate = ref(true) // Whether user has enough credits for pagination

// Filters
const filters = ref({
  sort: 'price_desc'
})

// Initialize page when auth is ready
const initPage = () => {
  // Redirect non-logged-in users to login page
  if (!user.value) {
    router.push('/prijava?redirect=/proizvodi')
    return
  }

  filters.value.sort = (route.query.sort as string) || 'price_desc'
  currentPage.value = parseInt(route.query.page as string) || 1

  // Parse store IDs from URL
  const storeParam = route.query.stores as string
  if (storeParam) {
    selectedStoreIds.value = storeParam.split(',').map(id => parseInt(id)).filter(id => !isNaN(id))
  }

  // Parse category from URL
  const categoryParam = route.query.category as string
  if (categoryParam) {
    selectedCategory.value = categoryParam
  }

  loadBusinesses()
  loadFollowedStores()
  loadProducts()
}

// Wait for auth to be ready before initializing
onMounted(() => {
  // Mark that user has visited proizvodi (for feedback popup precondition)
  if (process.client) {
    localStorage.setItem('visited_proizvodi', 'true')
  }

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
  filters.value.sort = (route.query.sort as string) || 'price_desc'
  currentPage.value = parseInt(route.query.page as string) || 1

  const storeParam = route.query.stores as string
  if (storeParam) {
    selectedStoreIds.value = storeParam.split(',').map(id => parseInt(id)).filter(id => !isNaN(id))
  } else {
    selectedStoreIds.value = []
  }

  const categoryParam = route.query.category as string
  selectedCategory.value = categoryParam || null

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

function onCategoryChange() {
  currentPage.value = 1
  // Track category filter change
  trackFilter('proizvodi', 'category', selectedCategory.value)
  loadProducts()
}

function onSortCheapest() {
  filters.value.sort = 'price_asc'
  currentPage.value = 1
  trackFilter('proizvodi', 'sort', 'price_asc')
  loadProducts()
}

// Computed - smart pagination with ellipsis
const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 5) {
    // Show all pages if 5 or fewer
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // Always show first page
    pages.push(1)

    if (current <= 3) {
      // Near the beginning: 1 2 3 4 ... last
      for (let i = 2; i <= Math.min(4, total - 1); i++) {
        pages.push(i)
      }
      if (total > 4) {
        pages.push('...')
        pages.push(total)
      }
    } else if (current >= total - 2) {
      // Near the end: 1 ... last-3 last-2 last-1 last
      pages.push('...')
      for (let i = Math.max(2, total - 3); i <= total; i++) {
        pages.push(i)
      }
    } else {
      // In the middle: 1 ... curr-1 curr curr+1 ... last
      pages.push('...')
      pages.push(current - 1)
      pages.push(current)
      pages.push(current + 1)
      pages.push('...')
      pages.push(total)
    }
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

async function loadFollowedStores() {
  try {
    const data = await get('/auth/user/store-preferences')
    // Filter only the stores that are selected (followed)
    followedStores.value = (data.all_stores || []).filter((store: any) => store.is_selected)
  } catch (error) {
    console.error('Error loading followed stores:', error)
  }
}

async function loadProducts() {
  isLoading.value = true

  try {
    const params = new URLSearchParams()
    if (selectedStoreIds.value.length > 0) {
      params.append('stores', selectedStoreIds.value.join(','))
    }
    if (selectedCategory.value) {
      params.append('category', selectedCategory.value)
    }
    if (filters.value.sort) params.append('sort', filters.value.sort)
    params.append('page', currentPage.value.toString())
    params.append('per_page', perPage.toString())

    // Use fetch directly to handle 402 credit errors
    const config = useRuntimeConfig()
    const token = process.client ? localStorage.getItem('token') : null
    const response = await fetch(`${config.public.apiBase}/api/products?${params.toString()}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      }
    })

    const data = await response.json()

    // Handle insufficient credits error (402)
    if (response.status === 402 && data.error === 'insufficient_credits') {
      creditsNeeded.value = data.credits_needed || 3
      creditsRemaining.value = data.credits_remaining || 0
      showCreditsPopup.value = true
      // Reset to page 1 since they can't view this page
      currentPage.value = 1
      updateURL()
      // Don't clear products - keep showing page 1 results
      isLoading.value = false
      return
    }

    if (!response.ok) {
      throw new Error(data.error || 'Failed to load products')
    }

    products.value = data.products || []
    totalPages.value = data.total_pages || 1
    totalProducts.value = data.total || 0

    // Track page view with current filters/pagination
    trackPageView('proizvodi', {
      page: currentPage.value,
      sort: filters.value.sort,
      stores: selectedStoreIds.value,
      category: selectedCategory.value,
      total_products: totalProducts.value
    })

    // Update credits info
    if (data.credits_remaining !== undefined) {
      creditsRemaining.value = data.credits_remaining
    }
    if (data.can_paginate !== undefined) {
      canPaginate.value = data.can_paginate
    }

    // Update category counts if provided
    if (data.category_counts) {
      categoryCounts.value = data.category_counts
    }

    updateURL()

    // Track product impressions asynchronously (fire and forget)
    if (products.value.length > 0) {
      const productIds = products.value.map((p: any) => p.id)
      trackProductViews(productIds)
    }
  } catch (error) {
    console.error('Error loading products:', error)
    products.value = []
  } finally {
    isLoading.value = false
  }
}

function resetFilters() {
  filters.value = {
    sort: 'price_desc'
  }
  selectedStoreIds.value = []
  selectedCategory.value = null
  currentPage.value = 1
  updateURL()
  loadProducts()
}

// Navigate to first product to encourage engagement (commenting/voting)
function goToProductsToEngage() {
  showCreditsPopup.value = false
  // If we have products, navigate to the first one so user can engage
  if (products.value.length > 0) {
    const firstProduct = products.value[0]
    // Open product detail modal or navigate to product page
    // For now, scroll to products grid so user can click on any product
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
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
  if (selectedCategory.value) query.category = selectedCategory.value
  if (filters.value.sort && filters.value.sort !== 'price_desc') query.sort = filters.value.sort
  if (currentPage.value > 1) query.page = currentPage.value.toString()

  router.replace({ query })
}

// Track product views asynchronously (non-blocking)
async function trackProductViews(productIds: number[]) {
  if (!productIds || productIds.length === 0) return
  if (!process.client) return

  const token = localStorage.getItem('token')
  if (!token) return

  try {
    // Fire and forget - don't await, don't block UI
    fetch(`${config.public.apiBase}/api/products/track-views`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ product_ids: productIds })
    }).catch(() => {
      // Silently ignore tracking errors
    })
  } catch {
    // Silently ignore tracking errors
  }
}

useSeoMeta({
  title: 'Svi proizvodi - Popust.ba',
  description: 'Pretražite kroz sve proizvode sa popustima iz vaših omiljenih trgovina',
})
</script>
