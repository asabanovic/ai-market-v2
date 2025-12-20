<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Moji Proizvodi</h1>
          <p class="mt-2 text-gray-600">Praćeni proizvodi i pronađene ponude</p>
        </div>
        <button
          @click="showAddModal = true"
          class="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-all duration-200"
        >
          <Icon name="mdi:plus" class="w-5 h-5 mr-2" />
          Dodaj proizvod
        </button>
      </div>

      <!-- Scan Info Banner -->
      <div
        v-if="latestScan"
        class="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 md:p-5 border border-green-200"
      >
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600" />
              <h3 class="font-bold text-gray-900">Posljednje skeniranje: {{ formatDate(latestScan.date) }}</h3>
            </div>
            <p class="text-gray-600 text-sm mt-1">
              {{ latestScan.summary || `Pronađeno ${latestScan.total_products} proizvoda` }}
            </p>
          </div>
          <div class="flex items-center gap-4">
            <div v-if="latestScan.new_products > 0" class="flex items-center gap-1.5">
              <span class="bg-green-100 text-green-700 px-2.5 py-1 rounded-full text-sm font-medium">
                {{ latestScan.new_products }} novih
              </span>
            </div>
            <div v-if="latestScan.new_discounts > 0" class="flex items-center gap-1.5">
              <span class="bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full text-sm font-medium">
                {{ latestScan.new_discounts }} sniženih
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State (no tracking) -->
      <div v-if="!loading && !hasTracking" class="text-center py-12 bg-white rounded-lg shadow-sm">
        <Icon name="mdi:magnify-scan" class="w-24 h-24 text-gray-400 mx-auto mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Nemate praćenih proizvoda</h3>
        <p class="text-gray-600 mb-6 max-w-md mx-auto">
          Dodajte proizvode koje želite pratiti i automatski ćemo ih tražiti u svim radnjama.
          Obavijestit ćemo vas o novim ponudama i popustima!
        </p>
        <button
          @click="showAddModal = true"
          class="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          <Icon name="mdi:plus" class="w-5 h-5 mr-2" />
          Dodaj prvi proizvod
        </button>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>

      <!-- Tracked Products List -->
      <div v-else class="space-y-6">
        <div
          v-for="tracked in trackedProducts"
          :key="tracked.id"
          class="bg-white rounded-lg shadow-md overflow-hidden"
        >
          <!-- Tracked Term Header -->
          <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <Icon name="mdi:tag-search" class="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-gray-900">{{ tracked.search_term }}</h3>
                  <p v-if="tracked.original_text && tracked.original_text !== tracked.search_term" class="text-sm text-gray-500">
                    iz: {{ tracked.original_text }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-sm text-gray-500">{{ tracked.products.length }} pronađeno</span>
                <button
                  @click="removeTracked(tracked.id)"
                  class="text-gray-400 hover:text-red-500 transition-colors"
                  title="Ukloni praćenje"
                >
                  <Icon name="mdi:close" class="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          <!-- Products Grid -->
          <div v-if="tracked.products.length > 0" class="p-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <NuxtLink
                v-for="product in tracked.products.slice(0, showAllProducts[tracked.id] ? undefined : 4)"
                :key="product.id"
                :to="`/proizvodi/${product.id}`"
                class="group bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors"
              >
                <!-- Product Image -->
                <div class="aspect-square mb-3 bg-white rounded-lg overflow-hidden">
                  <img
                    v-if="product.image_url"
                    :src="product.image_url"
                    :alt="product.title"
                    class="w-full h-full object-contain group-hover:scale-105 transition-transform"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center">
                    <Icon name="mdi:image-off" class="w-12 h-12 text-gray-300" />
                  </div>
                </div>

                <!-- Badges -->
                <div class="flex items-center gap-1.5 mb-2">
                  <span
                    v-if="product.is_new_today"
                    class="bg-green-100 text-green-700 px-1.5 py-0.5 rounded text-xs font-medium"
                  >
                    NOVO
                  </span>
                  <span
                    v-if="product.price_dropped_today"
                    class="bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-xs font-medium"
                  >
                    SNIŽENO
                  </span>
                  <span
                    v-if="product.discount_price"
                    class="bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded text-xs font-medium"
                  >
                    AKCIJA
                  </span>
                </div>

                <!-- Title -->
                <h4 class="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-purple-600 transition-colors">
                  {{ product.title }}
                </h4>

                <!-- Store -->
                <p class="text-xs text-gray-500 mt-1">{{ product.business }}</p>

                <!-- Price -->
                <div class="mt-2 flex items-center gap-2">
                  <span class="text-lg font-bold text-purple-600">
                    {{ (product.discount_price || product.base_price)?.toFixed(2) }} KM
                  </span>
                  <span v-if="product.discount_price && product.base_price" class="text-xs text-gray-500 line-through">
                    {{ product.base_price.toFixed(2) }} KM
                  </span>
                </div>
              </NuxtLink>
            </div>

            <!-- Show More Button -->
            <div v-if="tracked.products.length > 4" class="mt-4 text-center">
              <button
                @click="showAllProducts[tracked.id] = !showAllProducts[tracked.id]"
                class="text-purple-600 hover:text-purple-700 text-sm font-medium"
              >
                {{ showAllProducts[tracked.id] ? 'Prikaži manje' : `Prikaži sve (${tracked.products.length})` }}
              </button>
            </div>
          </div>

          <!-- No Products Found -->
          <div v-else class="p-6 text-center text-gray-500">
            <Icon name="mdi:package-variant-remove" class="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p>Nema pronađenih proizvoda za ovaj pojam.</p>
            <p class="text-sm mt-1">Pokušajte dodati vaše omiljene radnje u postavkama.</p>
          </div>
        </div>
      </div>

      <!-- Add Product Modal -->
      <div
        v-if="showAddModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="showAddModal = false"
      >
        <div class="bg-white rounded-xl p-6 max-w-md w-full shadow-xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">Dodaj proizvod za praćenje</h3>
            <button @click="showAddModal = false" class="text-gray-400 hover:text-gray-600">
              <Icon name="mdi:close" class="w-5 h-5" />
            </button>
          </div>

          <form @submit.prevent="addTrackedProduct">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda</label>
              <input
                v-model="newProductTerm"
                type="text"
                placeholder="npr. mlijeko, nutella, coca cola..."
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
                minlength="2"
              />
              <p class="text-xs text-gray-500 mt-1">Unesite naziv proizvoda koji želite pratiti</p>
            </div>

            <div class="flex justify-end gap-3">
              <button
                type="button"
                @click="showAddModal = false"
                class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
              >
                Odustani
              </button>
              <button
                type="submit"
                :disabled="isAdding || !newProductTerm.trim()"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {{ isAdding ? 'Dodavanje...' : 'Dodaj' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { get, post, del } = useApi()
const { handleApiError, showSuccess } = useCreditsToast()

const loading = ref(true)
const trackedProducts = ref<any[]>([])
const latestScan = ref<any>(null)
const hasTracking = ref(false)
const showAllProducts = ref<Record<number, boolean>>({})

// Add modal
const showAddModal = ref(false)
const newProductTerm = ref('')
const isAdding = ref(false)

async function fetchTrackedProducts() {
  loading.value = true
  try {
    const data = await get('/api/user/tracked-products')
    trackedProducts.value = data.tracked_products || []
    latestScan.value = data.latest_scan
    hasTracking.value = data.has_tracking
  } catch (error) {
    console.error('Error fetching tracked products:', error)
    handleApiError(error)
  } finally {
    loading.value = false
  }
}

async function addTrackedProduct() {
  if (!newProductTerm.value.trim()) return

  isAdding.value = true
  try {
    const response = await post('/api/user/tracked-products', {
      search_term: newProductTerm.value.trim()
    })
    if (response.success) {
      showSuccess(response.message || 'Proizvod dodan za praćenje')
      showAddModal.value = false
      newProductTerm.value = ''
      await fetchTrackedProducts()
    }
  } catch (error: any) {
    handleApiError(error)
  } finally {
    isAdding.value = false
  }
}

async function removeTracked(trackedId: number) {
  if (!confirm('Jeste li sigurni da želite ukloniti ovaj proizvod iz praćenja?')) return

  try {
    const response = await del(`/api/user/tracked-products/${trackedId}`)
    if (response.success) {
      showSuccess('Praćenje ukinuto')
      trackedProducts.value = trackedProducts.value.filter(t => t.id !== trackedId)
      if (trackedProducts.value.length === 0) {
        hasTracking.value = false
      }
    }
  } catch (error) {
    handleApiError(error)
  }
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return 'Danas'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Jučer'
  }

  const months = ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli', 'august', 'septembar', 'oktobar', 'novembar', 'decembar']
  return `${date.getDate()}. ${months[date.getMonth()]}`
}

onMounted(() => {
  fetchTrackedProducts()
})
</script>
