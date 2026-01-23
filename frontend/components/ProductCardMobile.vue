<template>
  <div
    class="product-card-mobile flex flex-col relative snap-center"
    :class="[product.is_teaser ? 'opacity-90' : '', hasActiveDiscount ? 'bg-green-200 ring-2 ring-green-500' : hasUpcomingDiscount ? 'bg-yellow-100 ring-2 ring-yellow-400' : product.contributor_name ? 'bg-white ring-2 ring-purple-400' : 'bg-white']"
  >
    <!-- Teaser Blur Overlay (Anonymous Users) -->
    <div
      v-if="product.is_teaser"
      class="absolute inset-0 backdrop-blur-md bg-white/30 z-50 flex items-center justify-center"
    >
      <div class="bg-white rounded-lg shadow-lg p-6 mx-4 text-center">
        <Icon name="mdi:lock" class="w-10 h-10 text-purple-600 mx-auto mb-3" />
        <h3 class="text-lg font-bold text-gray-900 mb-2">
          Registrujte se da vidite više
        </h3>
        <NuxtLink
          to="/registracija"
          class="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
          @click.stop
        >
          Besplatna registracija
        </NuxtLink>
      </div>
    </div>

    <!-- Discount Badge -->
    <div
      v-if="discountPercentage > 0"
      class="absolute top-3 right-3 bg-red-500 text-white px-3 py-1 rounded-lg text-base font-bold z-10"
    >
      -{{ discountPercentage }}%
    </div>

    <!-- Favorite Button -->
    <div class="absolute left-3 top-3 z-10">
      <FavoriteButton :product-id="product.id" :size="36" @click.stop />
    </div>

    <!-- Product Image - Large -->
    <div
      class="h-56 bg-gray-50 flex items-center justify-center p-4 cursor-pointer relative"
      @click="showDetails"
    >
      <img
        v-if="product.image_path || product.product_image_url"
        :src="getImageUrl(product.image_path || product.product_image_url)"
        :alt="product.title"
        class="max-h-full max-w-full object-contain"
        @error="imageError = true"
      />
      <span v-else class="text-gray-400">Nema Slike</span>

      <!-- Contributor Badge Overlay (bottom of image) -->
      <div
        v-if="product.contributor_name"
        class="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-purple-900/90 via-purple-800/70 to-transparent px-3 py-2.5"
      >
        <div class="flex items-center gap-2 text-white text-xs">
          <div class="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 ring-2 ring-white/50">
            <Icon name="mdi:account" class="w-4 h-4 text-white" />
          </div>
          <span class="line-clamp-2">
            Dodao/la <span class="font-semibold">{{ product.contributor_name }}</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Match Type Indicators Row - 3 columns -->
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

    <!-- Product Info -->
    <div class="p-4 flex-1 flex flex-col">
      <!-- Title -->
      <h3
        class="text-gray-900 font-semibold text-base leading-snug line-clamp-2 mb-2 cursor-pointer"
        @click="showDetails"
      >
        {{ product.title || 'Nepoznat proizvod' }}
      </h3>

      <!-- Store Info -->
      <div class="flex items-center gap-2 mb-3">
        <div
          v-if="businessLogo"
          class="w-6 h-6 rounded overflow-hidden flex-shrink-0"
        >
          <img
            :src="businessLogo"
            :alt="product.business?.name"
            class="w-full h-full object-contain"
          />
        </div>
        <div v-else class="w-6 h-6 bg-purple-600 rounded flex items-center justify-center flex-shrink-0">
          <span class="text-white text-xs font-bold">
            {{ product.business?.name?.[0] || '?' }}
          </span>
        </div>
        <span class="text-gray-600 text-sm">
          {{ product.business?.name || 'Nepoznata prodavnica' }}
        </span>
      </div>

      <!-- Price -->
      <div class="flex items-baseline gap-2 mb-2">
        <!-- Active discount: show discount price with crossed-out base price -->
        <template v-if="hasActiveDiscount">
          <span class="text-2xl font-bold text-gray-900">
            {{ formatPrice(product.discount_price) }} KM
          </span>
          <span class="text-base text-gray-400 line-through">
            {{ formatPrice(product.base_price) }} KM
          </span>
        </template>
        <!-- Upcoming or no discount: show base price only -->
        <template v-else>
          <span class="text-2xl font-bold text-gray-900">
            {{ formatPrice(product.base_price) }} KM
          </span>
        </template>
      </div>

      <!-- Relevance Score -->
      <div v-if="product.similarity_score" class="mb-3">
        <span class="text-xs text-gray-400">
          {{ Math.round(product.similarity_score * 100) }}% podudaranje
        </span>
      </div>

      <!-- Upcoming Discount -->
      <div
        v-if="hasUpcomingDiscount"
        class="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-300 rounded-lg px-3 py-2 mb-3"
      >
        <div class="flex items-center gap-1 text-xs text-yellow-800">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span class="font-medium">
            Akcija za {{ daysUntilDiscount }} {{ daysUntilDiscount === 1 ? 'dan' : 'dana' }} -
            <span class="text-green-700 font-bold">{{ formatPrice(product.discount_price) }} KM</span>
          </span>
        </div>
      </div>

      <!-- Expiry if applicable -->
      <div v-else-if="product.expires && product.has_discount" class="text-sm text-yellow-700 mb-3">
        Akcija do {{ formatShortDate(product.expires) }}
      </div>

      <!-- Recently Expired Discount - FOMO message -->
      <div
        v-else-if="recentlyExpiredDiscount"
        class="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 rounded-lg px-3 py-2 mb-3"
      >
        <p class="text-xs text-orange-800 font-medium">Popust istekao prije {{ daysAgoText }}</p>
        <button
          v-if="isLoggedIn && !isTracking"
          @click.stop="trackProductForDiscounts"
          :disabled="isAddingToTracked"
          class="text-xs text-orange-600 hover:text-orange-800 underline mt-1 flex items-center gap-1 disabled:opacity-50"
        >
          <Icon name="mdi:bell-plus" class="w-3 h-3" />
          Prati da ne propustis sljedeci
        </button>
        <NuxtLink
          v-else-if="!isLoggedIn"
          to="/registracija"
          class="text-xs text-orange-600 hover:text-orange-800 underline mt-1 block"
          @click.stop
        >
          Registruj se za obavjestenja
        </NuxtLink>
        <span v-else-if="isTracking" class="text-xs text-green-600 flex items-center gap-1 mt-1">
          <Icon name="mdi:bell-check" class="w-3 h-3" />
          Pratite ovaj proizvod
        </span>
      </div>

      <!-- Action Buttons -->
      <div class="mt-auto space-y-2">
        <!-- Add to List (logged in only) -->
        <button
          v-if="isLoggedIn"
          @click.stop="addToShoppingList"
          :disabled="isAddingToList"
          class="w-full py-3 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
        >
          <Icon name="mdi:cart-plus" class="w-5 h-5" />
          Dodaj u korpu
        </button>

        <!-- Details Button -->
        <button
          @click.stop="showDetails"
          class="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
        >
          Pogledaj detalje
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
const { handleApiError, showSuccess, showWarning } = useCreditsToast()
const { user } = useAuth()
const { post } = useApi()

const props = defineProps<{
  product: any
}>()

const showModal = ref(false)
const imageError = ref(false)
const isAddingToList = ref(false)
const isAddingToTracked = ref(false)
const isTracking = ref(false)

const isLoggedIn = computed(() => !!user.value)

const hasActiveDiscount = computed(() => {
  if (props.product.has_discount !== undefined) {
    return props.product.has_discount
  }
  // Fallback: manual check (must also check discount_starts)
  if (!props.product.discount_price ||
      props.product.base_price <= 0 ||
      props.product.discount_price >= props.product.base_price) {
    return false
  }
  // Check if discount has started (null = immediately active)
  if (props.product.discount_starts) {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const startDate = new Date(props.product.discount_starts)
    startDate.setHours(0, 0, 0, 0)
    if (startDate > today) {
      return false  // Discount hasn't started yet
    }
  }
  return true
})

// Compute upcoming discount (discount_starts is in the future)
const hasUpcomingDiscount = computed(() => {
  if (!props.product.discount_starts || !props.product.discount_price) {
    return false
  }
  if (props.product.discount_price >= props.product.base_price) {
    return false
  }
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const startDate = new Date(props.product.discount_starts)
  startDate.setHours(0, 0, 0, 0)
  return startDate > today
})

// Days until discount starts
const daysUntilDiscount = computed(() => {
  if (!hasUpcomingDiscount.value || !props.product.discount_starts) return 0
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const startDate = new Date(props.product.discount_starts)
  startDate.setHours(0, 0, 0, 0)
  const diffTime = startDate.getTime() - today.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
})

const discountPercentage = computed(() => {
  // Only show discount percentage badge when discount is ACTIVE (not upcoming)
  if (hasActiveDiscount.value && props.product.discount_price && props.product.base_price > 0 && props.product.discount_price < props.product.base_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
})

// Match counts for the 3 columns
const cloneCount = computed(() => props.product.match_counts?.clones || 0)
const siblingCount = computed(() => props.product.match_counts?.siblings || 0)
const brandVariantCount = computed(() => props.product.match_counts?.brand_variants || 0)

// Check if product is in user's favorites
const isFavorited = computed(() => {
  if (!isLoggedIn.value) return false
  return favoritesStore.isFavorited(props.product.id)
})

// Check if discount expired within last 10 days
const recentlyExpiredDiscount = computed(() => {
  if (!props.product.expires || props.product.has_discount) return false

  const now = new Date()
  let expiresDate = props.product.expires
  if (typeof expiresDate === 'string' && expiresDate.includes('T')) {
    expiresDate = expiresDate.split('T')[0]
  }
  const expiry = new Date(expiresDate + 'T23:59:59')

  if (isNaN(expiry.getTime())) return false

  const diff = now.getTime() - expiry.getTime()
  const daysDiff = Math.floor(diff / (1000 * 60 * 60 * 24))

  // Show if expired within last 10 days
  return daysDiff >= 0 && daysDiff <= 10
})

// Days ago text for FOMO message
const daysAgoText = computed(() => {
  if (!props.product.expires) return ''

  const now = new Date()
  let expiresDate = props.product.expires
  if (typeof expiresDate === 'string' && expiresDate.includes('T')) {
    expiresDate = expiresDate.split('T')[0]
  }
  const expiry = new Date(expiresDate + 'T23:59:59')
  const diff = now.getTime() - expiry.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return 'danas'
  if (days === 1) return '1 dan'
  if (days < 5) return `${days} dana`
  return `${days} dana`
})

const businessLogo = computed(() => {
  const logo = props.product.business?.logo || props.product.business?.logo_path
  if (!logo) return null

  if (logo.startsWith('http://') || logo.startsWith('https://')) {
    return logo
  }

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
  const url = new URL(window.location.href)
  url.searchParams.set('product', props.product.id.toString())
  window.history.pushState({}, '', url.toString())
}

function closeModal() {
  showModal.value = false
  const url = new URL(window.location.href)
  url.searchParams.delete('product')
  window.history.pushState({}, '', url.toString())
}

async function addToShoppingList() {
  isAddingToList.value = true

  try {
    const result = await cartStore.addItem(
      props.product.id,
      props.product.business_id || props.product.business?.id || 1,
      1
    )

    if (result.success) {
      showSuccess(`"${props.product.title}" dodano!`)
    } else if (result.error) {
      handleApiError(result.error)
    }
  } catch (error) {
    console.error('Error adding to shopping list:', error)
  } finally {
    isAddingToList.value = false
  }
}

// Track product for discount notifications
async function trackProductForDiscounts() {
  if (!isLoggedIn.value || isAddingToTracked.value) return

  isAddingToTracked.value = true

  try {
    const response = await post('/api/user/tracked-products', {
      search_term: props.product.title,
      original_text: props.product.title
    })

    if (response.success || response.id) {
      isTracking.value = true
      showSuccess('Pratimo ovaj proizvod! Obavijestit cemo vas o sljedecem popustu.')
    }
  } catch (error: any) {
    console.error('Error tracking product:', error)
    if (error.status === 409) {
      // Already tracking
      isTracking.value = true
      showSuccess('Vec pratite ovaj proizvod.')
    } else if (error.status === 402) {
      showWarning('Nemate dovoljno kredita za pracenje proizvoda.')
    } else {
      handleApiError(error)
    }
  } finally {
    isAddingToTracked.value = false
  }
}
</script>

<style scoped>
.product-card-mobile {
  width: 78vw;
  min-width: 78vw;
  max-width: 300px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
