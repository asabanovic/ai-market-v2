<template>
  <div class="min-h-screen bg-white pb-20 md:pb-0">
    <div class="container mx-auto px-4 py-8 md:py-12">
      <div v-if="product" class="max-w-4xl mx-auto">
        <!-- Back button -->
        <button
          @click="$router.back()"
          class="flex items-center gap-2 text-gray-600 hover:text-purple-600 mb-6 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-5 h-5" />
          <span>Nazad</span>
        </button>

        <div class="grid md:grid-cols-2 gap-8">
          <!-- Product image -->
          <div>
            <img
              v-if="product.image_path"
              :src="product.image_path"
              :alt="product.title"
              class="w-full rounded-2xl shadow-lg"
            />
            <div v-else class="w-full aspect-square bg-gray-100 rounded-2xl flex items-center justify-center">
              <Icon name="mdi:image-off" class="w-24 h-24 text-gray-300" />
            </div>
          </div>

          <!-- Product details -->
          <div class="space-y-6">
            <div>
              <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">{{ product.title }}</h1>

              <div class="flex items-baseline flex-wrap gap-3 mb-6">
                <span
                  v-if="product.discount_price"
                  class="text-4xl md:text-5xl font-bold text-purple-600"
                >
                  {{ formatPrice(product.discount_price) }} KM
                </span>
                <span
                  :class="[
                    'text-2xl md:text-3xl font-bold',
                    product.discount_price ? 'line-through text-gray-400' : 'text-purple-600'
                  ]"
                >
                  {{ formatPrice(product.base_price) }} KM
                </span>
              </div>

              <div v-if="product.has_discount" class="inline-block bg-red-500 text-white px-4 py-2 rounded-full font-bold mb-6">
                Ušteda: -{{ product.discount_percentage }}%
              </div>
            </div>

            <div class="space-y-4 text-gray-700">
              <div v-if="product.category" class="flex items-center space-x-2">
                <Icon name="mdi:tag" class="w-5 h-5 text-gray-400" />
                <span>{{ product.category }}</span>
              </div>

              <div v-if="product.business" class="flex items-center space-x-2">
                <Icon name="mdi:store" class="w-5 h-5 text-gray-400" />
                <span class="font-medium">{{ product.business.name }}</span>
              </div>

              <div v-if="product.expires" class="flex items-center space-x-2">
                <Icon name="mdi:calendar" class="w-5 h-5 text-gray-400" />
                <span>Važi do: {{ formatDate(product.expires) }}</span>
              </div>
            </div>

            <!-- Store Actions -->
            <div class="pt-6 space-y-3">
              <!-- Google Maps link -->
              <a
                v-if="product.google_link"
                :href="product.google_link"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center justify-center gap-2 w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                <Icon name="mdi:map-marker" class="w-5 h-5" />
                <span>Pronađi prodavnicu</span>
              </a>

              <!-- Phone contact -->
              <a
                v-if="product.contact_phone"
                :href="`tel:${product.contact_phone}`"
                class="flex items-center justify-center gap-2 w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                <Icon name="mdi:phone" class="w-5 h-5" />
                <span>Nazovi: {{ product.contact_phone }}</span>
              </a>

              <!-- Add to cart -->
              <button
                @click="addToCart"
                class="flex items-center justify-center gap-2 w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-3 px-6 rounded-lg transition-colors"
              >
                <Icon name="mdi:cart-plus" class="w-5 h-5" />
                <span>Dodaj na listu</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading state -->
      <div v-else-if="isLoading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>

      <!-- Error state -->
      <div v-else class="text-center py-12">
        <Icon name="mdi:alert-circle" class="w-24 h-24 mx-auto mb-4 text-red-500" />
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Proizvod nije pronađen</h2>
        <p class="text-gray-600 mb-6">Ovaj proizvod više nije dostupan ili je uklonjen.</p>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-5 h-5" />
          <span>Nazad na proizvode</span>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'

const route = useRoute()
const api = useApi()
const cartStore = useCartStore()
const { handleApiError, showSuccess } = useCreditsToast()

const product = ref<any>(null)
const isLoading = ref(false)

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('bs-BA')
}

async function addToCart() {
  if (!product.value) return

  const result = await cartStore.addItem(
    product.value.id,
    product.value.business?.id,
    1
  )

  if (result.success) {
    showSuccess(`"${product.value.title}" dodano na listu!`)
  } else if (result.error) {
    handleApiError(result.error)
  }
}

// Load product on mount
onMounted(async () => {
  isLoading.value = true
  try {
    const response = await api.get(`/api/product/${route.params.id}`)
    product.value = response
  } catch (error) {
    console.error('Failed to load product:', error)
  } finally {
    isLoading.value = false
  }
})

useSeoMeta({
  title: computed(() => product.value ? `${product.value.title} - Popust.ba` : 'Proizvod - Popust.ba'),
  description: computed(() => product.value?.title || 'Product details'),
})
</script>
