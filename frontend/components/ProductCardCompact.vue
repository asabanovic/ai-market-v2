<template>
  <div
    class="bg-white overflow-hidden flex relative py-3 px-4"
    :class="[product.is_teaser ? 'opacity-90' : '']"
    @click="showDetails"
  >
    <!-- Teaser Blur Overlay (Anonymous Users) -->
    <div
      v-if="product.is_teaser"
      class="absolute inset-0 backdrop-blur-md bg-white/30 z-50 flex items-center justify-center"
    >
      <div class="bg-white rounded-lg shadow-lg p-4 mx-4 text-center">
        <Icon name="mdi:lock" class="w-8 h-8 text-purple-600 mx-auto mb-2" />
        <h3 class="text-base font-bold text-gray-900 mb-1">
          Registrujte se
        </h3>
        <NuxtLink
          to="/registracija"
          class="inline-block px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
          @click.stop
        >
          Besplatno
        </NuxtLink>
      </div>
    </div>

    <!-- Product Image -->
    <div class="w-24 h-24 flex-shrink-0 bg-white flex items-center justify-center p-2">
      <img
        v-if="product.image_path || product.product_image_url"
        :src="getImageUrl(product.image_path || product.product_image_url)"
        :alt="product.title"
        class="w-full h-full object-contain"
        @error="imageError = true"
      />
      <span v-else class="text-gray-400 text-xs">Nema Slike</span>
    </div>

    <!-- Product Info -->
    <div class="flex-1 p-3 flex flex-col justify-between min-w-0">
      <!-- Title & Store Row -->
      <div>
        <h3 class="text-gray-900 font-medium text-sm leading-tight line-clamp-2 mb-1">
          {{ product.title || 'Nepoznat proizvod' }}
        </h3>
        <div class="flex items-center gap-1.5">
          <!-- Business Logo -->
          <div
            v-if="businessLogo"
            class="w-4 h-4 rounded-sm overflow-hidden flex-shrink-0"
          >
            <img
              :src="businessLogo"
              :alt="product.business?.name"
              class="w-full h-full object-contain"
            />
          </div>
          <span class="text-gray-500 text-xs truncate">
            {{ product.business?.name || '' }}
          </span>
        </div>
      </div>

      <!-- Price Row -->
      <div class="flex items-center justify-between mt-2">
        <div class="flex items-baseline gap-1.5">
          <span class="text-lg font-bold text-gray-900">
            {{ formatPrice(product.discount_price || product.base_price) }} KM
          </span>
          <span
            v-if="product.discount_price && product.base_price > product.discount_price"
            class="text-xs text-gray-400 line-through"
          >
            {{ formatPrice(product.base_price) }}
          </span>
        </div>

        <!-- Discount Badge -->
        <div
          v-if="discountPercentage > 0"
          class="bg-red-500 text-white px-2 py-0.5 rounded text-xs font-bold"
        >
          -{{ discountPercentage }}%
        </div>
      </div>
    </div>

    <!-- Quick Actions (right side) -->
    <div class="flex flex-col justify-center gap-2 pr-3 pl-2 border-l border-gray-100">
      <!-- Favorite Button -->
      <FavoriteButton :product-id="product.id" :size="24" @click.stop />

      <!-- Add to List (logged in only) -->
      <button
        v-if="isLoggedIn"
        @click.stop="addToShoppingList"
        :disabled="isAddingToList"
        class="w-8 h-8 rounded-full bg-green-100 text-green-600 hover:bg-green-200 flex items-center justify-center transition-colors"
        title="Dodaj u listu"
      >
        <Icon name="mdi:playlist-plus" class="w-5 h-5" />
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

const config = useRuntimeConfig()
const cartStore = useCartStore()
const { handleApiError, showSuccess } = useCreditsToast()
const { user } = useAuth()

const props = defineProps<{
  product: any
}>()

const showModal = ref(false)
const imageError = ref(false)
const isAddingToList = ref(false)

const isLoggedIn = computed(() => !!user.value)

const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > 0 && props.product.discount_price < props.product.base_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
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
      props.product.business?.id || 1,
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
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
