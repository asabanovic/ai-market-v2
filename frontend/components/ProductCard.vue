<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden relative hover:shadow-xl transition-shadow duration-300" :class="relevanceBorderClass">
    <!-- Relevance Badge -->
    <div
      v-if="product.similarity !== undefined"
      :class="relevanceBadgeClass"
      class="absolute top-3 left-3 px-3 py-1.5 rounded-md text-sm font-extrabold z-20 shadow-lg cursor-help"
      :title="relevanceTooltip"
    >
      <div class="flex items-center gap-1">
        <span>{{ relevanceLabel }}</span>
        <svg class="w-3 h-3 opacity-70" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
      </div>
    </div>

    <!-- Discount Badge -->
    <div
      v-if="discountPercentage > 0"
      class="absolute top-3 right-3 bg-red-500 text-white px-2 py-1 rounded-md text-sm font-bold z-10"
    >
      -{{ discountPercentage }}%
    </div>

    <!-- Favorite Button (moved down if relevance badge exists) -->
    <div :class="['absolute left-3 z-10', product.similarity !== undefined ? 'top-12' : 'top-3']">
      <FavoriteButton :product-id="product.id" :size="32" @updated="handleFavoriteUpdate" />
    </div>

    <!-- Product Image -->
    <div class="h-48 bg-gray-100 flex items-center justify-center cursor-pointer" @click="showDetails">
      <img
        v-if="product.image_path || product.product_image_url"
        :src="getImageUrl(product.image_path || product.product_image_url)"
        :alt="product.title"
        class="h-full w-full object-cover"
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
      <div class="mb-3">
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

      <!-- Expiry Date -->
      <div class="mb-3 min-h-[2rem]">
        <div
          v-if="product.expires"
          class="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-md text-center text-sm font-medium"
        >
          do {{ formatBosnianDate(product.expires) }}
        </div>
      </div>

      <!-- Business Info -->
      <div class="flex items-center gap-2 mb-4">
        <!-- Business Logo -->
        <div
          v-if="product.business?.logo"
          class="w-6 h-6 rounded-sm overflow-hidden"
        >
          <img
            :src="`${config.public.apiBase}/static/${product.business.logo}`"
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
        <span v-if="product.city || product.business?.city" class="text-gray-500 text-sm">
          {{ product.city || product.business?.city || 'BiH'}}
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
          class="w-full py-2.5 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all duration-200 font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
        >
          <Icon name="mdi:playlist-plus" class="w-5 h-5" />
          <span>Dodaj u listu</span>
        </button>

        <!-- Comment Button -->
        <button
          @click.stop="showDetails"
          class="w-full py-2.5 px-4 bg-white border-2 border-gray-200 text-gray-700 hover:border-purple-500 hover:text-purple-600 rounded-lg transition-all duration-200 font-medium text-sm flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
        >
          <Icon name="mdi:comment-outline" class="w-5 h-5" />
          <span>Ostavi Komentar</span>
        </button>

        <!-- Share Button -->
        <button
          @click.stop="shareProduct"
          class="w-full py-2.5 px-4 bg-white border-2 border-gray-200 text-gray-700 hover:border-blue-500 hover:text-blue-600 rounded-lg transition-all duration-200 font-medium text-sm flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
        >
          <Icon name="mdi:share-variant" class="w-5 h-5" />
          <span>Podijeli</span>
        </button>
      </div>
    </div>

    <!-- Product Details Modal -->
    <ProductDetailModal
      :show="showModal"
      :product="product"
      @close="showModal = false"
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

// Computed property to check if user is logged in
const isLoggedIn = computed(() => !!user.value)

const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > 0 && props.product.discount_price < props.product.base_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
})

// Relevance level based on similarity score
const relevanceLevel = computed(() => {
  const similarity = props.product.similarity
  if (similarity === undefined) return null

  // Define thresholds for relevance
  if (similarity >= 0.75) return 'high'      // Highly relevant - green
  if (similarity >= 0.55) return 'medium'    // Somewhat related - orange
  return 'low'                                // Least related - red
})

const relevanceBadgeClass = computed(() => {
  switch (relevanceLevel.value) {
    case 'high':
      return 'bg-green-600 text-white'
    case 'medium':
      return 'bg-orange-600 text-white'
    case 'low':
      return 'bg-red-500 text-white'
    default:
      return ''
  }
})

const relevanceBorderClass = computed(() => {
  switch (relevanceLevel.value) {
    case 'high':
      return 'border-4 border-green-500 shadow-green-200 shadow-lg'
    case 'medium':
      return 'border-4 border-orange-500 shadow-orange-200 shadow-lg'
    case 'low':
      return 'border-4 border-red-400 shadow-red-200 shadow-lg'
    default:
      return ''
  }
})

const relevanceLabel = computed(() => {
  const similarity = props.product.similarity
  if (similarity === undefined) return ''

  const percentage = Math.round(similarity * 100)
  return `${percentage}%`
})

const relevanceTooltip = computed(() => {
  const similarity = props.product.similarity
  if (similarity === undefined) return ''

  const percentage = Math.round(similarity * 100)

  switch (relevanceLevel.value) {
    case 'high':
      return `Indeks relevantnosti: ${percentage}% - Odlično poklapanje sa vašom pretragom`
    case 'medium':
      return `Indeks relevantnosti: ${percentage}% - Dobro poklapanje, sličan proizvod`
    case 'low':
      return `Indeks relevantnosti: ${percentage}% - Slabije poklapanje, može biti zanimljivo`
    default:
      return ''
  }
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

function showDetails() {
  showModal.value = true
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

async function shareProduct() {
  try {
    const productUrl = `${window.location.origin}/?product=${props.product.id}`
    await navigator.clipboard.writeText(productUrl)
    showSuccess('Link kopiran! Podijelite sa prijateljima.')
  } catch (error) {
    console.error('Error copying link:', error)
    // Fallback if clipboard API doesn't work
    const textArea = document.createElement('textarea')
    textArea.value = `${window.location.origin}/?product=${props.product.id}`
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
