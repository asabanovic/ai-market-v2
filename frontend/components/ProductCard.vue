<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden relative hover:shadow-xl transition-shadow duration-300" :class="[product.is_teaser ? 'opacity-90' : '']">
    <!-- Teaser Blur Overlay (Anonymous Users) -->
    <div
      v-if="product.is_teaser"
      class="absolute inset-0 backdrop-blur-md bg-white/30 z-50 flex items-center justify-center"
    >
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4 text-center">
        <Icon name="mdi:lock" class="w-12 h-12 text-purple-600 mx-auto mb-3" />
        <h3 class="text-xl font-bold text-gray-900 mb-2">
          Registrujte se da vidite više
        </h3>
        <p class="text-gray-600 mb-4">
          Otkrijte sve proizvode i uštedite još više!
        </p>
        <NuxtLink
          to="/registracija"
          class="inline-block w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          Besplatna registracija
        </NuxtLink>
      </div>
    </div>

    <!-- Discount Badge -->
    <div
      v-if="discountPercentage > 0"
      class="absolute top-3 right-3 bg-red-500 text-white px-2 py-1 rounded-md text-sm font-bold z-10"
    >
      -{{ discountPercentage }}%
    </div>

    <!-- Favorite Button -->
    <div class="absolute left-3 top-3 z-10">
      <FavoriteButton :product-id="product.id" :size="32" @updated="handleFavoriteUpdate" />
    </div>

    <!-- Product Image -->
    <div class="h-48 bg-white flex items-center justify-center cursor-pointer" @click="showDetails">
      <img
        v-if="product.image_path || product.product_image_url"
        :src="getImageUrl(product.image_path || product.product_image_url)"
        :alt="product.title"
        class="h-full w-full object-contain"
        @error="imageError = true"
      />
      <span v-else-if="!imageError" class="text-gray-400 text-sm">Nema Slike</span>
      <span v-else class="text-gray-400 text-sm">Nema Slike</span>
    </div>

    <!-- Product Details -->
    <div class="p-4">
      <!-- Product Title -->
      <div class="mb-3 h-[2.5rem]">
        <h3 class="text-gray-900 font-medium text-sm leading-snug line-clamp-2">
          {{ product.title || 'Nepoznat proizvod' }}
        </h3>
      </div>

      <!-- Price Info -->
      <div class="mb-2">
        <span class="text-2xl font-bold text-gray-900">
          {{ formatPrice(product.discount_price || product.base_price) }} KM
        </span>
        <span
          v-if="product.discount_price && product.base_price > product.discount_price"
          class="text-gray-400 line-through ml-2"
        >
          {{ formatPrice(product.base_price) }} KM
        </span>
      </div>

      <!-- Expiry Date OR Price History (same row, consistent height) -->
      <div class="mb-2 min-h-[1.5rem] flex items-center justify-center">
        <!-- Show expiry date for products with active discount -->
        <div
          v-if="product.expires && product.has_discount"
          class="text-xs text-yellow-700 text-center"
        >
          do {{ formatShortDate(product.expires) }}
        </div>
        <!-- Show price history for products without active discount -->
        <div
          v-else-if="showPriceHistory && showSavingsCTA"
          class="w-full bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-md px-2 py-1 text-xs"
        >
          <div class="flex items-center justify-between">
            <span class="text-gray-600">Prethodna akcija: <strong class="text-green-600">{{ formatPrice(product.price_history.lowest_price) }} KM</strong></span>
            <button
              v-if="!isLoggedIn"
              @click.stop="goToRegister"
              class="text-purple-600 hover:text-purple-800 underline"
            >
              Obavijesti me
            </button>
            <button
              v-else-if="!isFavorited"
              @click.stop="addToFavorites"
              class="text-purple-600 hover:text-purple-800 underline flex items-center gap-0.5"
            >
              <Icon name="mdi:bell-plus" class="w-3 h-3" />
              Prati
            </button>
            <span v-else class="text-green-600 flex items-center gap-0.5">
              <Icon name="mdi:bell-check" class="w-3 h-3" />
              Pratim
            </span>
          </div>
        </div>
      </div>

      <!-- Business Info -->
      <div class="flex items-center gap-2 mb-4">
        <!-- Business Logo -->
        <div
          v-if="businessLogo"
          class="w-6 h-6 rounded-sm overflow-hidden"
        >
          <img
            :src="businessLogo"
            :alt="`${product.business.name} logo`"
            class="w-full h-full object-contain"
          />
        </div>
        <div v-else class="w-6 h-6 bg-green-600 rounded-sm flex items-center justify-center">
          <span class="text-white text-xs font-bold">
            {{ product.business?.name?.[0] || '' }}
          </span>
        </div>

        <span class="text-gray-700 font-medium text-sm">
          {{ product.business?.name || 'Nepoznat biznis' }}
        </span>
      </div>

      <!-- Action Buttons - Stacked Vertically -->
      <div class="flex flex-col gap-2">
        <!-- Shopping List Button (only for logged-in users) -->
        <button
          v-if="isLoggedIn"
          @click.stop="addToShoppingList"
          :disabled="isAddingToList"
          :title="'Dodaj u listu za kupovinu'"
          class="w-full py-2.5 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all duration-200 font-medium text-sm inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
        >
          <Icon name="mdi:playlist-plus" class="w-5 h-5 flex-shrink-0" />
          <span class="leading-none">Dodaj u listu</span>
        </button>

        <!-- Comment Button -->
        <button
          @click.stop="showDetails"
          class="w-full py-2.5 px-4 bg-white border-2 border-gray-200 text-gray-700 hover:border-purple-500 hover:text-purple-600 rounded-lg transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md"
        >
          Ostavi Komentar
        </button>

        <!-- Share Button -->
        <button
          @click.stop="shareProduct"
          class="w-full py-2.5 px-4 bg-white border-2 border-gray-200 text-gray-700 hover:border-blue-500 hover:text-blue-600 rounded-lg transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md"
        >
          Podijeli
        </button>
      </div>
    </div>

    <!-- Product Details Modal -->
    <ProductDetailModal
      :show="showModal"
      :product="product"
      @close="closeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'

const config = useRuntimeConfig()
const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()
const { handleApiError, showSuccess } = useCreditsToast()
const { user } = useAuth()

const props = defineProps<{
  product: any
}>()

const showModal = ref(false)
const imageError = ref(false)
const isAddingToList = ref(false)

// Check URL for product parameter on mount
onMounted(() => {
  if (process.client) {
    const urlParams = new URLSearchParams(window.location.search)
    const productId = urlParams.get('product')
    if (productId && parseInt(productId) === props.product.id) {
      showModal.value = true
    }
  }
})

const router = useRouter()

// Computed property to check if user is logged in
const isLoggedIn = computed(() => !!user.value)

// Check if product is in user's favorites
const isFavorited = computed(() => {
  if (!isLoggedIn.value) return false
  return favoritesStore.isFavorited(props.product.id)
})

// Show price history section if product has historical price data and is NOT currently on discount
const showPriceHistory = computed(() => {
  return props.product.price_history &&
         props.product.price_history.lowest_price &&
         props.product.price_history.potential_savings > 0 &&
         !props.product.has_discount
})

// Show savings CTA if potential savings are significant (> 0.50 KM)
const showSavingsCTA = computed(() => {
  return showPriceHistory.value &&
         props.product.price_history.potential_savings >= 0.50
})

const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > 0 && props.product.discount_price < props.product.base_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
})

// Computed property for business logo - handles different API response formats
const businessLogo = computed(() => {
  const logo = props.product.business?.logo || props.product.business?.logo_path
  if (!logo) return null

  // If it's already a full URL, return as-is
  if (logo.startsWith('http://') || logo.startsWith('https://')) {
    return logo
  }

  // Otherwise, prepend the API base with /static/
  return `${config.public.apiBase}/static/${logo}`
})

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `${config.public.apiBase}/static/${path}`
}

function formatPrice(price: number | string): string {
  const numPrice = typeof price === 'number' ? price : parseFloat(price) || 0
  return numPrice.toFixed(2)
}

function formatBosnianDate(dateString: string): string {
  if (!dateString) return ''

  const date = new Date(dateString)
  const days = ['Nedjelja', 'Ponedjeljak', 'Utorak', 'Srijeda', 'Četvrtak', 'Petak', 'Subota']
  const months = ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli', 'august', 'septembar', 'oktobar', 'novembar', 'decembar']

  const dayName = days[date.getDay()]
  const day = date.getDate()
  const month = months[date.getMonth()]
  const year = date.getFullYear()

  return `${dayName}, ${day}. ${month} ${year}.`
}

function formatShortDate(dateString: string): string {
  if (!dateString) return ''

  const date = new Date(dateString)
  const day = date.getDate()
  const month = date.getMonth() + 1
  const year = date.getFullYear()

  return `${day}.${month}.${year}.`
}

function showDetails() {
  showModal.value = true
  // Update URL with product ID
  const url = new URL(window.location.href)
  url.searchParams.set('product', props.product.id.toString())
  window.history.pushState({}, '', url.toString())
}

function closeModal() {
  showModal.value = false
  // Remove product ID from URL
  const url = new URL(window.location.href)
  url.searchParams.delete('product')
  window.history.pushState({}, '', url.toString())
}

async function addToShoppingList() {
  isAddingToList.value = true

  try {
    const result = await cartStore.addItem(
      props.product.id,
      props.product.business?.id || 1,
      1
    )

    if (result.success) {
      showSuccess(`"${props.product.title}" dodano na listu!`)
    } else if (result.error) {
      handleApiError(result.error)
    }
  } catch (error) {
    console.error('Error adding to shopping list:', error)
  } finally {
    isAddingToList.value = false
  }
}

function handleFavoriteUpdate() {
  // Refresh favorites count in header
  favoritesStore.fetchFavorites()
}

// Navigate to registration page
function goToRegister() {
  router.push('/registracija')
}

// Add product to favorites (from the price history CTA)
async function addToFavorites() {
  try {
    await favoritesStore.addFavorite(props.product.id)
    showSuccess('Dodano u favorite! Dobićete obavještenje kada cijena padne.')
  } catch (error) {
    console.error('Error adding to favorites:', error)
  }
}

async function shareProduct() {
  try {
    const productUrl = `${window.location.origin}/proizvodi/${props.product.id}`
    await navigator.clipboard.writeText(productUrl)
    showSuccess('Link kopiran! Podijelite sa prijateljima.')
  } catch (error) {
    console.error('Error copying link:', error)
    // Fallback if clipboard API doesn't work
    const textArea = document.createElement('textarea')
    textArea.value = `${window.location.origin}/proizvodi/${props.product.id}`
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    showSuccess('Link kopiran!')
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
