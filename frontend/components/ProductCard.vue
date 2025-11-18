<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden relative hover:shadow-xl transition-shadow duration-300">
    <!-- Discount Badge -->
    <div
      v-if="discountPercentage > 0"
      class="absolute top-3 right-3 bg-red-500 text-white px-2 py-1 rounded-md text-sm font-bold z-10"
    >
      -{{ discountPercentage }}%
    </div>

    <!-- Favorite Button (Top Left) -->
    <div class="absolute top-3 left-3 z-10">
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
        <!-- Shopping List Button -->
        <button
          @click.stop="addToShoppingList"
          :disabled="isAddingToList"
          :title="'Dodaj u listu za kupovinu'"
          class="w-full py-2.5 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all duration-200 font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
        >
          <Icon name="mdi:playlist-plus" class="w-5 h-5" />
          <span>Dodaj u listu</span>
        </button>

        <!-- Details Button -->
        <button
          @click.stop="showDetails"
          class="w-full py-2.5 px-4 bg-white border-2 border-gray-200 text-gray-700 hover:border-purple-500 hover:text-purple-600 rounded-lg transition-all duration-200 font-medium text-sm flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
        >
          <Icon name="mdi:information-outline" class="w-5 h-5" />
          <span>Detalji</span>
        </button>
      </div>
    </div>

    <!-- Product Details Modal -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
        @click="showModal = false"
      >
        <div class="relative top-20 mx-auto p-0 border w-full max-w-4xl shadow-lg rounded-lg bg-white" @click.stop>
          <div class="flex">
            <!-- Left side - Business info -->
            <div class="w-1/2 p-6">
              <div class="flex justify-between items-start mb-4">
                <h3 class="text-xl font-bold text-gray-900">
                  {{ product.business?.name || 'Nepoznato poslovanje' }}
                </h3>
                <button @click="showModal = false" class="text-gray-400 hover:text-gray-600">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Business logo -->
              <div v-if="product.business?.logo" class="mb-4">
                <img
                  :src="`${config.public.apiBase}/static/${product.business.logo}`"
                  alt="Logo"
                  class="h-16 w-auto object-contain rounded"
                />
              </div>
              <div v-else class="mb-4 p-4 bg-green-100 rounded-lg text-center">
                <div class="w-12 h-12 bg-green-500 rounded mx-auto mb-2 flex items-center justify-center text-white font-bold text-lg">
                  {{ product.business?.name?.[0] || '?' }}
                </div>
                <span class="text-green-700 text-sm">Logo uskoro</span>
              </div>

              <!-- Product info -->
              <div class="mb-4 p-4 bg-gray-50 rounded-lg">
                <h4 class="font-semibold text-gray-900 mb-2">{{ product.title }}</h4>
                <div class="text-lg">
                  <span class="font-bold text-green-600">
                    {{ formatPrice(product.discount_price || product.base_price) }} KM
                  </span>
                  <span
                    v-if="product.discount_price && product.base_price > product.discount_price"
                    class="ml-2 text-sm text-gray-500 line-through"
                  >
                    {{ formatPrice(product.base_price) }} KM
                  </span>
                </div>
              </div>

              <!-- Business details -->
              <div class="space-y-3">
                <div class="flex items-center space-x-2">
                  <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span class="text-gray-700">{{ product.city || 'Nepoznat grad' }}</span>
                </div>

                <div v-if="product.contact_phone" class="flex items-center space-x-2">
                  <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  <span class="text-gray-700">{{ product.contact_phone }}</span>
                </div>

                <div v-if="product.expires" class="flex items-center space-x-2">
                  <svg class="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span class="text-orange-700 font-medium">Važi do: {{ formatBosnianDate(product.expires) }}</span>
                </div>
              </div>
            </div>

            <!-- Right side - Map/Location -->
            <div class="w-1/2">
              <div class="h-full min-h-96 bg-gray-100 rounded-r-lg flex items-center justify-center">
                <div v-if="product.google_link" class="text-center p-6">
                  <svg class="w-16 h-16 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p class="text-lg font-medium text-gray-700 mb-2">Lokacija: {{ product.city || 'Nepoznato' }}</p>
                  <a
                    :href="product.google_link"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Pogledaj na mapi
                  </a>
                </div>
                <div v-else class="text-center text-gray-500">
                  <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p class="text-sm">Mapa nije dostupna</p>
                  <p class="text-xs text-gray-400 mt-1">Lokacija: {{ product.city || 'Nepoznato' }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'

const config = useRuntimeConfig()
const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()
const { handleApiError, showSuccess } = useCreditsToast()

const props = defineProps<{
  product: any
}>()

const showModal = ref(false)
const imageError = ref(false)
const isAddingToList = ref(false)

const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > 0 && props.product.discount_price < props.product.base_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
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
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
