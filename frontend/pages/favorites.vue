<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Omiljeni Proizvodi</h1>
          <p class="mt-2 text-gray-600">Vaša lista omiljenih proizvoda</p>
        </div>
        <button
          v-if="favoritesStore.count > 0 && !favoritesStore.loading"
          @click="showClearConfirmation = true"
          class="inline-flex items-center px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded-lg transition-all duration-200"
        >
          <Icon name="mdi:delete" class="w-5 h-5 mr-2" />
          Obriši sve
        </button>
      </div>

      <!-- Interest Setup Banner - Always visible for logged in users -->
      <div
        v-if="showInterestBanner"
        class="mb-6 bg-gradient-to-r from-purple-600 to-purple-700 rounded-xl p-4 md:p-5 text-white shadow-lg"
      >
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 class="font-bold text-lg">Obavještenja o popustima</h3>
            <p class="text-purple-100 text-sm mt-1">
              Odaberite namirnice koje kupujete i javit ćemo vam čim budu na akciji!
            </p>
          </div>
          <button
            @click="openInterestPopup"
            class="px-5 py-2.5 bg-white text-purple-700 font-semibold rounded-lg hover:bg-purple-50 transition-colors shadow-md whitespace-nowrap flex items-center gap-2"
          >
            <Icon name="mdi:cog" class="w-5 h-5" />
            Uredi interese
          </button>
        </div>
      </div>

      <!-- Clear All Confirmation Modal -->
      <div
        v-if="showClearConfirmation"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showClearConfirmation = false"
      >
        <div class="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
          <div class="flex items-center gap-3 mb-4">
            <div class="bg-red-100 rounded-full p-2">
              <Icon name="mdi:alert" class="w-6 h-6 text-red-600" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900">Obrisati sve omiljene?</h3>
          </div>
          <p class="text-gray-600 mb-6">
            Jeste li sigurni da želite obrisati sve omiljene proizvode ({{ favoritesStore.count }})?
            Ova akcija se ne može poništiti.
          </p>
          <div class="flex justify-end gap-3">
            <button
              @click="showClearConfirmation = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
            >
              Odustani
            </button>
            <button
              @click="clearAllFavorites"
              :disabled="isClearing"
              class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {{ isClearing ? 'Brisanje...' : 'Da, obriši sve' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Statistics Section -->
      <div v-if="favoritesStore.count > 0 && !favoritesStore.loading" class="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 mb-8">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Statistika omiljenih</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="text-2xl font-bold text-purple-600">{{ stats.totalItems }}</div>
            <div class="text-sm text-gray-600">Proizvoda</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="text-2xl font-bold text-red-600">{{ stats.itemsOnSale }}</div>
            <div class="text-sm text-gray-600">Na popustu</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="text-2xl font-bold text-green-600">{{ stats.totalValue.toFixed(2) }}</div>
            <div class="text-sm text-gray-600">KM ukupno</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="text-2xl font-bold text-gray-500">{{ stats.originalValue.toFixed(2) }}</div>
            <div class="text-sm text-gray-600">KM bez popusta</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="text-2xl font-bold text-green-600">{{ stats.totalSavings.toFixed(2) }}</div>
            <div class="text-sm text-gray-600">KM uštede</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="text-2xl font-bold text-orange-600">{{ stats.avgDiscount }}%</div>
            <div class="text-sm text-gray-600">Prosječan popust</div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="favoritesStore.loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="favoritesStore.count === 0" class="text-center py-12">
        <Icon name="mdi:heart-outline" class="w-24 h-24 text-gray-400 mx-auto mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Nemate omiljenih proizvoda</h3>
        <p class="text-gray-600 mb-6">Počnite dodavati proizvode u omiljene kako biste ih brzo pronašli kasnije</p>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          Pretraži proizvode
        </NuxtLink>
      </div>

      <!-- Grouped by Store -->
      <div v-else class="space-y-8">
        <div
          v-for="store in groupedByStore"
          :key="store.id"
          class="bg-white rounded-lg shadow-md overflow-hidden"
        >
          <!-- Store Header -->
          <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <img
                  v-if="store.logo"
                  :src="store.logo"
                  :alt="store.name"
                  class="w-10 h-10 object-contain rounded"
                />
                <div v-else class="w-10 h-10 bg-gray-200 rounded flex items-center justify-center">
                  <Icon name="mdi:store" class="w-6 h-6 text-gray-400" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-gray-900">{{ store.name }}</h3>
                  <p class="text-sm text-gray-600">{{ store.totalItems }} proizvoda</p>
                </div>
              </div>
              <div class="text-right">
                <div class="text-lg font-bold text-green-600">{{ store.totalValue.toFixed(2) }} KM</div>
                <div v-if="store.totalSavings > 0" class="text-sm text-gray-500">
                  Ušteda: <span class="text-green-600 font-medium">{{ store.totalSavings.toFixed(2) }} KM</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Mobile: Card Layout -->
          <div class="md:hidden divide-y divide-gray-200">
            <div
              v-for="favorite in store.paginatedItems"
              :key="'mobile-' + favorite.favorite_id"
              class="p-4 bg-white"
            >
              <NuxtLink
                :to="`/proizvodi/${favorite.product_id}`"
                class="flex items-start gap-3 mb-3"
              >
                <div class="flex-shrink-0 h-16 w-16">
                  <img
                    v-if="favorite.image_url"
                    :src="favorite.image_url"
                    :alt="favorite.name"
                    class="h-16 w-16 rounded object-cover"
                  />
                  <div v-else class="h-16 w-16 rounded bg-gray-200 flex items-center justify-center">
                    <Icon name="mdi:image-off" class="w-6 h-6 text-gray-400" />
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-900 line-clamp-2">{{ favorite.name }}</div>
                  <div class="flex items-center gap-2 mt-1">
                    <span class="text-base font-bold text-purple-600">{{ favorite.price.toFixed(2) }} KM</span>
                    <span v-if="favorite.old_price" class="text-xs text-gray-500 line-through">
                      {{ favorite.old_price.toFixed(2) }} KM
                    </span>
                    <span
                      v-if="favorite.discount_percent"
                      class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                    >
                      -{{ favorite.discount_percent }}%
                    </span>
                  </div>
                  <div v-if="favorite.expires" class="mt-1">
                    <span :class="getExpiryClass(favorite.expires)" class="text-xs font-medium">
                      {{ getDaysLeft(favorite.expires) }}
                    </span>
                  </div>
                </div>
              </NuxtLink>
              <div class="flex items-center gap-2">
                <button
                  @click="addToCart(favorite)"
                  class="flex-1 inline-flex items-center justify-center px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-all"
                >
                  <Icon name="mdi:playlist-plus" class="w-4 h-4 mr-1" />
                  Dodaj u listu
                </button>
                <button
                  @click="removeFavorite(favorite.favorite_id)"
                  class="inline-flex items-center justify-center px-3 py-2 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded-lg transition-all"
                  title="Ukloni"
                >
                  <Icon name="mdi:heart-off" class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- Desktop: Table Layout -->
          <table class="hidden md:table min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proizvod</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kategorija</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cijena</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Popust</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Važi do</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="favorite in store.paginatedItems"
                :key="favorite.favorite_id"
                class="hover:bg-gray-50 transition-colors"
              >
                <!-- Product -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <NuxtLink
                    :to="`/proizvodi/${favorite.product_id}`"
                    class="flex items-center gap-3 group"
                  >
                    <div class="flex-shrink-0 h-12 w-12">
                      <img
                        v-if="favorite.image_url"
                        :src="favorite.image_url"
                        :alt="favorite.name"
                        class="h-12 w-12 rounded object-cover group-hover:ring-2 group-hover:ring-purple-500 transition-all"
                      />
                      <div v-else class="h-12 w-12 rounded bg-gray-200 flex items-center justify-center group-hover:ring-2 group-hover:ring-purple-500 transition-all">
                        <Icon name="mdi:image-off" class="w-6 h-6 text-gray-400" />
                      </div>
                    </div>
                    <div class="max-w-xs">
                      <div class="text-sm font-medium text-gray-900 truncate group-hover:text-purple-600 transition-colors">{{ favorite.name }}</div>
                    </div>
                  </NuxtLink>
                </td>

                <!-- Category -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm text-gray-500">{{ favorite.category || '-' }}</span>
                </td>

                <!-- Price -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col">
                    <span class="text-sm font-bold text-purple-600">{{ favorite.price.toFixed(2) }} KM</span>
                    <span v-if="favorite.old_price" class="text-xs text-gray-500 line-through">
                      {{ favorite.old_price.toFixed(2) }} KM
                    </span>
                  </div>
                </td>

                <!-- Discount -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    v-if="favorite.discount_percent"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                  >
                    -{{ favorite.discount_percent }}%
                  </span>
                  <span v-else class="text-sm text-gray-400">-</span>
                </td>

                <!-- Expires -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div v-if="favorite.expires" class="flex flex-col">
                    <span :class="getExpiryClass(favorite.expires)" class="text-sm font-medium">
                      {{ getDaysLeft(favorite.expires) }}
                    </span>
                    <span class="text-xs text-gray-400">{{ formatDate(favorite.expires) }}</span>
                  </div>
                  <span v-else class="text-sm text-gray-400">-</span>
                </td>

                <!-- Actions -->
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="addToCart(favorite)"
                      class="inline-flex items-center px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <Icon name="mdi:playlist-plus" class="w-4 h-4 mr-1" />
                      Dodaj u listu
                    </button>
                    <button
                      @click="removeFavorite(favorite.favorite_id)"
                      class="inline-flex items-center px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded-lg transition-all duration-200"
                      title="Ukloni iz omiljenih"
                    >
                      <Icon name="mdi:heart-off" class="w-4 h-4 mr-1" />
                      Ukloni
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination for this store -->
          <div v-if="store.totalPages > 1" class="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div class="flex items-center justify-between">
              <div class="text-sm text-gray-700">
                Prikazano {{ (store.currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(store.currentPage * itemsPerPage, store.totalItems) }} od {{ store.totalItems }}
              </div>
              <div class="flex items-center gap-2">
                <button
                  @click="changePage(store.id, store.currentPage - 1)"
                  :disabled="store.currentPage === 1"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Prethodna
                </button>
                <span class="text-sm text-gray-600">{{ store.currentPage }} / {{ store.totalPages }}</span>
                <button
                  @click="changePage(store.id, store.currentPage + 1)"
                  :disabled="store.currentPage === store.totalPages"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Sljedeća
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFavoritesStore } from '~/stores/favorites'
import { useCartStore } from '~/stores/cart'

definePageMeta({
  middleware: 'auth'
})

const favoritesStore = useFavoritesStore()
const cartStore = useCartStore()
const { handleApiError, showSuccess } = useCreditsToast()
const { user } = useAuth()

const itemsPerPage = 10
const storePages = ref<Record<number, number>>({})
const showClearConfirmation = ref(false)
const isClearing = ref(false)
const showInterestPopup = ref(false)
const bannerDismissed = ref(false)

// Always show interest banner for logged in users (so they can update their selections)
const showInterestBanner = computed(() => {
  // Must be logged in to show
  return !!user.value
})

function openInterestPopup() {
  // Emit event to app.vue to open the popup
  if (process.client) {
    window.dispatchEvent(new CustomEvent('open-interest-popup'))
  }
}

function dismissInterestBanner() {
  bannerDismissed.value = true
}

// Statistics computed property
const stats = computed(() => {
  const items = favoritesStore.items
  if (!items || items.length === 0) {
    return {
      totalItems: 0,
      itemsOnSale: 0,
      totalValue: 0,
      originalValue: 0,
      totalSavings: 0,
      avgDiscount: 0
    }
  }

  const totalItems = items.length
  const itemsOnSale = items.filter(item => item.discount_percent && item.discount_percent > 0).length
  const totalValue = items.reduce((sum, item) => sum + (item.price || 0), 0)
  const originalValue = items.reduce((sum, item) => sum + (item.old_price || item.price || 0), 0)
  const totalSavings = originalValue - totalValue

  const discountedItems = items.filter(item => item.discount_percent && item.discount_percent > 0)
  const avgDiscount = discountedItems.length > 0
    ? Math.round(discountedItems.reduce((sum, item) => sum + (item.discount_percent || 0), 0) / discountedItems.length)
    : 0

  return {
    totalItems,
    itemsOnSale,
    totalValue,
    originalValue,
    totalSavings,
    avgDiscount
  }
})

// Group favorites by store with pagination
const groupedByStore = computed(() => {
  const items = favoritesStore.items
  if (!items || items.length === 0) return []

  // Group by business
  const storeMap = new Map<number, {
    id: number
    name: string
    logo: string | null
    items: any[]
  }>()

  items.forEach(item => {
    const businessId = item.business?.id || 0
    const businessName = item.business?.name || 'Nepoznato'
    const businessLogo = item.business?.logo || null

    if (!storeMap.has(businessId)) {
      storeMap.set(businessId, {
        id: businessId,
        name: businessName,
        logo: businessLogo,
        items: []
      })
    }
    storeMap.get(businessId)!.items.push(item)
  })

  // Convert to array and add pagination info
  return Array.from(storeMap.values())
    .sort((a, b) => b.items.length - a.items.length)
    .map(store => {
      const currentPage = storePages.value[store.id] || 1
      const totalItems = store.items.length
      const totalPages = Math.ceil(totalItems / itemsPerPage)
      const startIndex = (currentPage - 1) * itemsPerPage
      const paginatedItems = store.items.slice(startIndex, startIndex + itemsPerPage)

      const totalValue = store.items.reduce((sum, item) => sum + (item.price || 0), 0)
      const originalValue = store.items.reduce((sum, item) => sum + (item.old_price || item.price || 0), 0)
      const totalSavings = originalValue - totalValue

      return {
        ...store,
        totalItems,
        totalPages,
        currentPage,
        paginatedItems,
        totalValue,
        totalSavings
      }
    })
})

function changePage(storeId: number, page: number) {
  storePages.value[storeId] = page
}

// Fetch favorites on mount
onMounted(async () => {
  await favoritesStore.fetchFavorites()
})

async function removeFavorite(favoriteId: number) {
  const result = await favoritesStore.removeFavorite(favoriteId)
  if (result.success) {
    showSuccess('Uklonjeno iz omiljenih')
  } else if (result.error) {
    handleApiError(result.error)
  }
}

async function clearAllFavorites() {
  isClearing.value = true
  try {
    const result = await favoritesStore.clearAll()
    if (result.success) {
      showSuccess('Svi omiljeni proizvodi su obrisani')
      showClearConfirmation.value = false
      // Reset store pages
      storePages.value = {}
    } else if (result.error) {
      handleApiError(result.error)
    }
  } finally {
    isClearing.value = false
  }
}

async function addToCart(favorite: any) {
  const result = await cartStore.addItem(
    favorite.product_id,
    favorite.business.id,
    1
  )

  if (result.success) {
    showSuccess(`"${favorite.name}" dodano na listu!`)
  } else if (result.error) {
    handleApiError(result.error)
  }
}

// Expiry date helpers
function getDaysLeft(expiresDate: string): string {
  if (!expiresDate) return '-'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expires = new Date(expiresDate)
  expires.setHours(0, 0, 0, 0)
  const diffTime = expires.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return 'Isteklo'
  if (diffDays === 0) return 'Danas'
  if (diffDays === 1) return 'Sutra'
  return `${diffDays} dana`
}

function getExpiryClass(expiresDate: string): string {
  if (!expiresDate) return 'text-gray-400'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expires = new Date(expiresDate)
  expires.setHours(0, 0, 0, 0)
  const diffTime = expires.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return 'text-gray-400'
  if (diffDays <= 2) return 'text-red-600'
  if (diffDays <= 5) return 'text-orange-600'
  return 'text-green-600'
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const months = ['Januar', 'Februar', 'Mart', 'April', 'Maj', 'Juni', 'Juli', 'August', 'Septembar', 'Oktobar', 'Novembar', 'Decembar']
  return `${months[date.getMonth()]} ${date.getDate()}`
}
</script>
