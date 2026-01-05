<template>
  <div class="rounded-lg shadow-md overflow-hidden relative hover:shadow-xl transition-shadow duration-300" :class="[product.is_teaser ? 'opacity-90' : '', hasActiveDiscount ? 'bg-green-200 ring-2 ring-green-500' : 'bg-white']">
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

    <!-- Social Interaction Header (Transparent) -->
    <div class="absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-black/70 via-black/40 to-transparent px-2 py-2 pointer-events-none">
      <div class="flex items-center justify-between pointer-events-auto">
        <!-- Favorite (Heart) -->
        <button
          @click.stop="toggleFavorite"
          class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
          :class="isFavorited ? 'text-red-500' : 'text-white hover:text-red-400'"
          :title="isFavorited ? 'Ukloni iz favorita' : 'Dodaj u favorite'"
        >
          <svg class="w-5 h-5" :fill="isFavorited ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </button>

        <!-- Vote Buttons -->
        <div class="flex items-center gap-2">
          <!-- Thumbs Up -->
          <button
            @click.stop="vote('up')"
            class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
            :class="userVote === 'up' ? 'text-green-400 bg-green-500/20' : 'text-white hover:text-green-400'"
            :title="'Preporuči (+2 kredita)'"
          >
            <svg class="w-5 h-5" :fill="userVote === 'up' ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </svg>
            <span v-if="upvotes > 0" class="text-xs font-medium">{{ upvotes }}</span>
          </button>

          <!-- Thumbs Down -->
          <button
            @click.stop="vote('down')"
            class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
            :class="userVote === 'down' ? 'text-red-400 bg-red-500/20' : 'text-white hover:text-red-400'"
            :title="'Ne preporučujem (+2 kredita)'"
          >
            <svg class="w-5 h-5" :fill="userVote === 'down' ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
            </svg>
            <span v-if="downvotes > 0" class="text-xs font-medium">{{ downvotes }}</span>
          </button>

          <!-- Comment Button -->
          <button
            @click.stop="toggleQuickComment"
            class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
            :class="showQuickCommentInput ? 'text-purple-400 bg-purple-500/20' : 'text-white hover:text-purple-400'"
            :title="'Ostavi komentar (+5 kredita)'"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span v-if="commentCount > 0" class="text-xs font-medium">{{ commentCount }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Comment Cloud Popup -->
    <div
      v-if="showQuickCommentInput"
      class="absolute top-12 left-2 right-2 z-30 bg-white rounded-lg shadow-xl p-3 border border-purple-200 pointer-events-auto"
      @click.stop
    >
      <p class="text-xs text-purple-700 mb-2 font-medium">Podijelite vaše iskustvo s ovim proizvodom i zaradite kredite!</p>
      <div class="flex items-start gap-2">
        <textarea
          v-model="quickComment"
          rows="2"
          maxlength="280"
          class="flex-1 p-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-gray-900"
          placeholder="Vaš komentar... (min 5 karaktera)"
          @keydown.enter.prevent="submitQuickComment"
        />
        <button
          @click.stop="submitQuickComment"
          :disabled="quickComment.trim().length < 5 || isSubmittingComment"
          class="px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg v-if="isSubmittingComment" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span v-else>+5</span>
        </button>
      </div>
      <p class="text-xs text-gray-500 mt-1">{{ quickComment.length }}/280 · Dobijate +5 kredita</p>
    </div>

    <!-- Discount Badge -->
    <div
      v-if="discountPercentage > 0"
      class="absolute top-10 right-3 bg-red-500 text-white px-2 py-1 rounded-md text-sm font-bold z-10"
    >
      -{{ discountPercentage }}%
    </div>

    <!-- Price History Badge -->
    <div
      v-if="priceHistoryCount > 0 && !discountPercentage"
      class="absolute top-10 right-3 bg-blue-500 text-white px-2 py-1 rounded-md text-xs font-bold z-10 flex items-center gap-1"
      :title="`${priceHistoryCount} prethodn${priceHistoryCount === 1 ? 'a' : 'e'} cijena`"
    >
      <Icon name="mdi:chart-line" class="w-3 h-3" />
      +{{ priceHistoryCount }}
    </div>

    <!-- Product Image -->
    <div class="h-48 bg-white flex items-center justify-center cursor-pointer pt-6 relative" @click="showDetails">
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

    <!-- Match Type Indicators Row - Always visible, 3 columns -->
    <div class="grid grid-cols-3 border-t border-gray-100">
      <!-- Clones (same product, other stores) -->
      <div
        class="flex flex-col items-center justify-center py-2 cursor-pointer transition-colors"
        :class="cloneCount > 0 ? 'bg-blue-50/70 hover:bg-blue-100/70' : 'bg-gray-50/50'"
        :title="cloneCount > 0 ? `Dostupno u ${cloneCount} drugih prodavnica` : 'Nema u drugim prodavnicama'"
        @click="cloneCount > 0 && showDetails()"
      >
        <Icon name="mdi:store-outline" class="w-4 h-4" :class="cloneCount > 0 ? 'text-blue-600' : 'text-gray-300'" />
        <span class="text-xs font-medium mt-0.5" :class="cloneCount > 0 ? 'text-blue-700' : 'text-gray-300'">{{ cloneCount }}</span>
      </div>

      <!-- Siblings (other sizes) -->
      <div
        class="flex flex-col items-center justify-center py-2 border-x border-gray-100 cursor-pointer transition-colors"
        :class="siblingCount > 0 ? 'bg-purple-50/70 hover:bg-purple-100/70' : 'bg-gray-50/50'"
        :title="siblingCount > 0 ? `${siblingCount} drugih veličina` : 'Nema drugih veličina'"
        @click="siblingCount > 0 && showDetails()"
      >
        <Icon name="mdi:arrow-expand-horizontal" class="w-4 h-4" :class="siblingCount > 0 ? 'text-purple-600' : 'text-gray-300'" />
        <span class="text-xs font-medium mt-0.5" :class="siblingCount > 0 ? 'text-purple-700' : 'text-gray-300'">{{ siblingCount }}</span>
      </div>

      <!-- Brand variants (other brands) -->
      <div
        class="flex flex-col items-center justify-center py-2 cursor-pointer transition-colors"
        :class="brandVariantCount > 0 ? 'bg-amber-50/70 hover:bg-amber-100/70' : 'bg-gray-50/50'"
        :title="brandVariantCount > 0 ? `${brandVariantCount} alternativnih brendova` : 'Nema alternativnih brendova'"
        @click="brandVariantCount > 0 && showDetails()"
      >
        <Icon name="mdi:swap-horizontal" class="w-4 h-4" :class="brandVariantCount > 0 ? 'text-amber-600' : 'text-gray-300'" />
        <span class="text-xs font-medium mt-0.5" :class="brandVariantCount > 0 ? 'text-amber-700' : 'text-gray-300'">{{ brandVariantCount }}</span>
      </div>
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

      <!-- Countdown Timer OR Price History (same row, consistent height) -->
      <div class="mb-2 min-h-[1.5rem] flex items-center justify-center">
        <!-- Show countdown for products with active discount -->
        <div
          v-if="product.expires && hasActiveDiscount && countdownText"
          class="flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full"
          :class="isExpiringSoon ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ countdownText }}</span>
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
              @click.stop="toggleFavorite"
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

      <!-- Action Button -->
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
const { handleApiError, showSuccess, showWarning } = useCreditsToast()
const { user } = useAuth()
const { post } = useApi()

const props = defineProps<{
  product: any
}>()

const showModal = ref(false)
const imageError = ref(false)
const isAddingToList = ref(false)

// Engagement state
const upvotes = ref(0)
const downvotes = ref(0)
const commentCount = ref(0)
const userVote = ref<string | null>(null)
const showQuickCommentInput = ref(false)
const quickComment = ref('')
const isSubmittingComment = ref(false)
const isVoting = ref(false)

// Countdown timer state
const countdownText = ref('')
const isExpiringSoon = ref(false)
let countdownInterval: ReturnType<typeof setInterval> | null = null

// Compute has active discount (handle both has_discount flag and manual check)
const hasActiveDiscount = computed(() => {
  // Check has_discount flag from API first
  if (props.product.has_discount !== undefined) {
    return props.product.has_discount
  }
  // Fallback: manual check
  return props.product.discount_price &&
         props.product.base_price > 0 &&
         props.product.discount_price < props.product.base_price
})

// Check URL for product parameter on mount
onMounted(() => {
  if (process.client) {
    const urlParams = new URLSearchParams(window.location.search)
    const productId = urlParams.get('product')
    if (productId && parseInt(productId) === props.product.id) {
      showModal.value = true
    }

    // Start countdown timer if product has expiry
    if (props.product.expires && hasActiveDiscount.value) {
      updateCountdown()
      countdownInterval = setInterval(updateCountdown, 1000) // Update every second for ticking effect
    }
  }
})

onUnmounted(() => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
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

// Get count of price history entries (for the badge)
const priceHistoryCount = computed(() => {
  return props.product.price_history?.history_count || 0
})

// Check if product has any matches (clones, siblings, or brand variants)
const hasAnyMatches = computed(() => {
  const counts = props.product.match_counts
  if (!counts) return false
  return (counts.clones || 0) + (counts.siblings || 0) + (counts.brand_variants || 0) > 0
})

// Total count of all matches
const totalMatchCount = computed(() => {
  const counts = props.product.match_counts
  if (!counts) return 0
  return (counts.clones || 0) + (counts.siblings || 0) + (counts.brand_variants || 0)
})

// Individual match counts for display
const cloneCount = computed(() => props.product.match_counts?.clones || 0)
const siblingCount = computed(() => props.product.match_counts?.siblings || 0)
const brandVariantCount = computed(() => props.product.match_counts?.brand_variants || 0)

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

// Update countdown timer
function updateCountdown() {
  if (!props.product.expires) {
    countdownText.value = ''
    return
  }

  const now = new Date()
  // Handle different date formats - extract just the date part if it's a full ISO string
  let expiresDate = props.product.expires
  if (typeof expiresDate === 'string' && expiresDate.includes('T')) {
    expiresDate = expiresDate.split('T')[0]
  }
  const expiry = new Date(expiresDate + 'T23:59:59') // End of day
  const diff = expiry.getTime() - now.getTime()

  // Check for invalid date
  if (isNaN(diff)) {
    countdownText.value = ''
    return
  }

  if (diff <= 0) {
    countdownText.value = 'Isteklo'
    isExpiringSoon.value = true
    return
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  // Mark as expiring soon if less than 2 days
  isExpiringSoon.value = days < 2

  if (days > 0) {
    // Show days, hours, minutes for multi-day countdowns
    countdownText.value = `${days}d ${hours}h ${minutes}m`
  } else if (hours > 0) {
    // Show hours, minutes, seconds when less than a day
    countdownText.value = `${hours}h ${minutes}m ${seconds}s`
  } else if (minutes > 0) {
    // Show minutes and seconds when less than an hour
    countdownText.value = `${minutes}m ${seconds}s`
  } else {
    // Show just seconds in final countdown
    countdownText.value = `${seconds}s`
  }
}

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // Handle paths that already include /static or static/
  if (path.startsWith('/static/') || path.startsWith('static/')) {
    return `${config.public.apiBase}${path.startsWith('/') ? '' : '/'}${path}`
  }
  return `${config.public.apiBase}/static/${path}`
}

function formatPrice(price: number | string): string {
  const numPrice = typeof price === 'number' ? price : parseFloat(price) || 0
  return numPrice.toFixed(2)
}

function showDetails() {
  showModal.value = true
  showQuickCommentInput.value = false
  // Update URL with product ID
  const url = new URL(window.location.href)
  url.searchParams.set('product', props.product.id.toString())
  window.history.pushState({}, '', url.toString())

  // Track individual product view (async, non-blocking)
  trackSingleProductView(props.product.id)
}

// Track single product view when modal opens
function trackSingleProductView(productId: number) {
  if (!process.client) return

  const token = localStorage.getItem('token')
  if (!token) return

  try {
    fetch(`${config.public.apiBase}/api/products/track-views`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ product_ids: [productId] })
    }).catch(() => {
      // Silently ignore tracking errors
    })
  } catch {
    // Silently ignore tracking errors
  }
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

// Navigate to registration page
function goToRegister() {
  router.push('/registracija')
}

// Toggle favorite
async function toggleFavorite() {
  if (!isLoggedIn.value) {
    router.push('/registracija')
    return
  }

  try {
    if (isFavorited.value) {
      const favoriteId = favoritesStore.getFavoriteId(props.product.id)
      if (favoriteId) {
        await favoritesStore.removeFavorite(favoriteId)
        showSuccess('Uklonjeno iz favorita')
      }
    } else {
      await favoritesStore.addFavorite(props.product.id)
      showSuccess('Dodano u favorite!')
    }
  } catch (error) {
    console.error('Error toggling favorite:', error)
  }
}

// Vote on product
async function vote(voteType: 'up' | 'down') {
  if (!isLoggedIn.value) {
    router.push('/registracija')
    return
  }

  if (isVoting.value) return
  isVoting.value = true

  try {
    const response = await post(`/api/products/${props.product.id}/vote`, {
      vote_type: voteType
    })

    if (response.success) {
      upvotes.value = response.vote_stats.upvotes
      downvotes.value = response.vote_stats.downvotes

      // Update user's vote state
      if (response.message === 'Vote removed') {
        userVote.value = null
      } else {
        userVote.value = voteType
      }

      if (response.credits_earned > 0) {
        showSuccess(`+${response.credits_earned} kredita za glasanje! Sada imate ukupno ${response.total_credits} kredita.`)
      }
    }
  } catch (error: any) {
    console.error('Error voting:', error)
    handleApiError(error)
  } finally {
    isVoting.value = false
  }
}

// Toggle quick comment input
function toggleQuickComment() {
  if (!isLoggedIn.value) {
    router.push('/registracija')
    return
  }
  showQuickCommentInput.value = !showQuickCommentInput.value
  if (showQuickCommentInput.value) {
    quickComment.value = ''
  }
}

// Submit quick comment
async function submitQuickComment() {
  if (!isLoggedIn.value || quickComment.value.trim().length < 5 || isSubmittingComment.value) return

  isSubmittingComment.value = true

  try {
    const response = await post(`/api/products/${props.product.id}/quick-comment`, {
      comment_text: quickComment.value.trim()
    })

    if (response.success) {
      commentCount.value = response.comment_count
      showSuccess(`+${response.credits_earned} kredita za komentar! Sada imate ukupno ${response.total_credits} kredita.`)
      quickComment.value = ''
      showQuickCommentInput.value = false
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

// Expose method to update engagement stats from parent
defineExpose({
  updateEngagementStats: (stats: { upvotes: number; downvotes: number; comments: number; user_vote: string | null }) => {
    upvotes.value = stats.upvotes
    downvotes.value = stats.downvotes
    commentCount.value = stats.comments
    userVote.value = stats.user_vote
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
