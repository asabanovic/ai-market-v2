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
                <!-- Sort Dropdown -->
                <select
                  v-if="tracked.products.length > 1"
                  v-model="sortOrder[tracked.id]"
                  @change="sortProducts(tracked)"
                  class="text-sm border border-gray-300 rounded-md px-2 py-1 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="">Sortiraj</option>
                  <option value="price_asc">Cijena: najniža</option>
                  <option value="price_desc">Cijena: najviša</option>
                </select>
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
              <div
                v-for="product in tracked.products.slice(0, showAllProducts[tracked.id] ? undefined : 4)"
                :key="product.id"
                class="group bg-gray-50 rounded-lg overflow-hidden hover:bg-gray-100 transition-colors relative flex flex-col"
              >
                <!-- Social Interaction Header -->
                <div class="bg-gradient-to-b from-black/70 via-black/40 to-transparent px-2 py-2 absolute top-0 left-0 right-0 z-10">
                  <div class="flex items-center justify-between">
                    <!-- Favorite (Heart) -->
                    <button
                      @click.stop="toggleFavorite(product)"
                      class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
                      :class="isFavorited(product.id) ? 'text-red-500' : 'text-white hover:text-red-400'"
                      :title="isFavorited(product.id) ? 'Ukloni iz favorita' : 'Dodaj u favorite'"
                    >
                      <svg class="w-5 h-5" :fill="isFavorited(product.id) ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                    </button>

                    <!-- Vote Buttons & Comment -->
                    <div class="flex items-center gap-2">
                      <!-- Thumbs Up -->
                      <button
                        @click.stop="vote(product, 'up')"
                        class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
                        :class="productVotes[product.id] === 'up' ? 'text-green-400 bg-green-500/20' : 'text-white hover:text-green-400'"
                        title="Preporuči"
                      >
                        <svg class="w-5 h-5" :fill="productVotes[product.id] === 'up' ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                        </svg>
                      </button>

                      <!-- Thumbs Down -->
                      <button
                        @click.stop="vote(product, 'down')"
                        class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
                        :class="productVotes[product.id] === 'down' ? 'text-red-400 bg-red-500/20' : 'text-white hover:text-red-400'"
                        title="Ne preporučujem"
                      >
                        <svg class="w-5 h-5" :fill="productVotes[product.id] === 'down' ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                        </svg>
                      </button>

                      <!-- Comment Button -->
                      <button
                        @click.stop="openCommentModal(product)"
                        class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer text-white hover:text-purple-400"
                        title="Ostavi komentar"
                      >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Product Link (clickable area) -->
                <NuxtLink :to="`/proizvodi/${product.id}`" class="block p-3 pt-12 flex-1">
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

                <!-- Add to List Button -->
                <div class="px-3 pb-3 mt-auto">
                  <button
                    @click.stop="addToShoppingList(product)"
                    :disabled="addingToList[product.id]"
                    class="w-full py-2 px-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all text-sm font-medium inline-flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Icon name="mdi:playlist-plus" class="w-4 h-4" />
                    <span>Dodaj u listu</span>
                  </button>
                </div>
              </div>
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

      <!-- Comment Modal -->
      <div
        v-if="commentModalProduct"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="closeCommentModal"
      >
        <div class="bg-white rounded-xl p-6 max-w-md w-full shadow-xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">Ostavi komentar</h3>
            <button @click="closeCommentModal" class="text-gray-400 hover:text-gray-600">
              <Icon name="mdi:close" class="w-5 h-5" />
            </button>
          </div>

          <p class="text-sm text-gray-600 mb-3">{{ commentModalProduct.title }}</p>
          <p class="text-xs text-purple-700 mb-3 font-medium">Podijelite vaše iskustvo i zaradite +5 kredita!</p>

          <textarea
            v-model="commentText"
            rows="3"
            maxlength="280"
            class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
            placeholder="Vaš komentar... (min 5 karaktera)"
          />
          <p class="text-xs text-gray-500 mt-1 mb-4">{{ commentText.length }}/280</p>

          <div class="flex justify-end gap-3">
            <button
              type="button"
              @click="closeCommentModal"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
            >
              Odustani
            </button>
            <button
              @click="submitComment"
              :disabled="commentText.trim().length < 5 || isSubmittingComment"
              class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {{ isSubmittingComment ? 'Slanje...' : 'Pošalji (+5)' }}
            </button>
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
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'

definePageMeta({
  middleware: 'auth'
})

const { get, post, del } = useApi()
const { handleApiError, showSuccess, showWarning } = useCreditsToast()
const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()

const loading = ref(true)
const trackedProducts = ref<any[]>([])
const latestScan = ref<any>(null)
const hasTracking = ref(false)
const showAllProducts = ref<Record<number, boolean>>({})
const sortOrder = ref<Record<number, string>>({})

// Add modal
const showAddModal = ref(false)
const newProductTerm = ref('')
const isAdding = ref(false)

// Product actions state
const productVotes = ref<Record<number, string | null>>({})
const addingToList = ref<Record<number, boolean>>({})

// Comment modal
const commentModalProduct = ref<any>(null)
const commentText = ref('')
const isSubmittingComment = ref(false)

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

// Sort products by price
function sortProducts(tracked: any) {
  const order = sortOrder.value[tracked.id]
  if (!order) return

  const getPrice = (p: any) => p.discount_price || p.base_price || 0

  if (order === 'price_asc') {
    tracked.products.sort((a: any, b: any) => getPrice(a) - getPrice(b))
  } else if (order === 'price_desc') {
    tracked.products.sort((a: any, b: any) => getPrice(b) - getPrice(a))
  }
}

// Check if product is favorited
function isFavorited(productId: number): boolean {
  return favoritesStore.isFavorited(productId)
}

// Toggle favorite
async function toggleFavorite(product: any) {
  try {
    if (isFavorited(product.id)) {
      const favoriteId = favoritesStore.getFavoriteId(product.id)
      if (favoriteId) {
        await favoritesStore.removeFavorite(favoriteId)
        showSuccess('Uklonjeno iz favorita')
      }
    } else {
      await favoritesStore.addFavorite(product.id)
      showSuccess('Dodano u favorite!')
    }
  } catch (error) {
    console.error('Error toggling favorite:', error)
    handleApiError(error)
  }
}

// Vote on product
async function vote(product: any, voteType: 'up' | 'down') {
  try {
    const response = await post(`/api/products/${product.id}/vote`, {
      vote_type: voteType
    })

    if (response.success) {
      if (response.message === 'Vote removed') {
        productVotes.value[product.id] = null
      } else {
        productVotes.value[product.id] = voteType
      }

      if (response.credits_earned > 0) {
        showSuccess(`+${response.credits_earned} kredita za glasanje!`)
      }
    }
  } catch (error: any) {
    console.error('Error voting:', error)
    handleApiError(error)
  }
}

// Open comment modal
function openCommentModal(product: any) {
  commentModalProduct.value = product
  commentText.value = ''
}

// Close comment modal
function closeCommentModal() {
  commentModalProduct.value = null
  commentText.value = ''
}

// Submit comment
async function submitComment() {
  if (!commentModalProduct.value || commentText.value.trim().length < 5 || isSubmittingComment.value) return

  isSubmittingComment.value = true

  try {
    const response = await post(`/api/products/${commentModalProduct.value.id}/quick-comment`, {
      comment_text: commentText.value.trim()
    })

    if (response.success) {
      showSuccess(`+${response.credits_earned} kredita za komentar!`)
      closeCommentModal()
    }
  } catch (error: any) {
    console.error('Error adding comment:', error)
    if (error.message) {
      showWarning(error.message)
    } else {
      handleApiError(error)
    }
  } finally {
    isSubmittingComment.value = false
  }
}

// Add to shopping list
async function addToShoppingList(product: any) {
  addingToList.value[product.id] = true

  try {
    const result = await cartStore.addItem(
      product.id,
      product.business_id || 1,
      1
    )

    if (result.success) {
      showSuccess(`"${product.title}" dodano na listu!`)
    } else if (result.error) {
      handleApiError(result.error)
    }
  } catch (error) {
    console.error('Error adding to shopping list:', error)
    handleApiError(error)
  } finally {
    addingToList.value[product.id] = false
  }
}

onMounted(() => {
  fetchTrackedProducts()
})
</script>
