<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">Učitavanje...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <Icon name="mdi:store-off" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Radnja nije pronađena</h2>
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <NuxtLink to="/" class="text-purple-600 hover:text-purple-800">
          ← Nazad na početnu
        </NuxtLink>
      </div>
    </div>

    <!-- Business Page -->
    <div v-else-if="business">
      <!-- Map Hero Section -->
      <div class="relative">
        <!-- Embedded Map or Gradient Background -->
        <div v-if="mapEmbedUrl" class="w-full h-64 md:h-80 lg:h-96">
          <iframe
            :src="mapEmbedUrl"
            width="100%"
            height="100%"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>
        </div>
        <div v-else class="w-full h-64 md:h-80 bg-gradient-to-br from-purple-600 to-purple-800">
          <div class="flex items-center justify-center h-full text-white/50">
            <div class="text-center">
              <Icon name="mdi:map-marker" class="w-16 h-16 mx-auto mb-2" />
              <p>Mapa lokacija nije dostupna</p>
            </div>
          </div>
        </div>

        <!-- Business Info Card (overlapping) -->
        <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-16 relative z-10">
          <div class="bg-white rounded-xl shadow-lg p-6">
            <div class="flex flex-col md:flex-row md:items-center gap-6">
              <!-- Logo -->
              <div class="flex-shrink-0">
                <img
                  v-if="business.logo_path"
                  :src="getImageUrl(business.logo_path)"
                  :alt="business.name"
                  class="w-24 h-24 md:w-32 md:h-32 object-contain rounded-xl border border-gray-200 bg-white"
                />
                <div v-else class="w-24 h-24 md:w-32 md:h-32 bg-gray-100 rounded-xl flex items-center justify-center">
                  <Icon name="mdi:store" class="w-12 h-12 text-gray-400" />
                </div>
              </div>

              <!-- Info -->
              <div class="flex-1">
                <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">{{ business.name }}</h1>
                <div class="flex flex-wrap items-center gap-4 text-gray-600">
                  <span class="flex items-center gap-1">
                    <Icon name="mdi:map-marker" class="w-5 h-5 text-purple-600" />
                    {{ business.city }}
                  </span>
                  <span v-if="business.contact_phone" class="flex items-center gap-1">
                    <Icon name="mdi:phone" class="w-5 h-5 text-purple-600" />
                    {{ business.contact_phone }}
                  </span>
                  <span class="flex items-center gap-1">
                    <Icon name="mdi:package-variant" class="w-5 h-5 text-purple-600" />
                    {{ business.product_count || 0 }} proizvoda
                  </span>
                </div>

                <!-- Actions -->
                <div class="flex flex-wrap gap-3 mt-4">
                  <a
                    v-if="business.google_link"
                    :href="business.google_link"
                    target="_blank"
                    class="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Icon name="mdi:google-maps" class="w-5 h-5" />
                    Pogledaj na Google Maps
                  </a>
                  <a
                    v-if="business.contact_phone"
                    :href="`tel:${business.contact_phone}`"
                    class="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Icon name="mdi:phone" class="w-5 h-5" />
                    Pozovi
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Products Section -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 mt-4">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-900">
            Akcije i popusti
          </h2>
          <span class="text-sm text-gray-500">{{ products.length }} proizvoda</span>
        </div>

        <!-- Products Grid -->
        <div v-if="products.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div
            v-for="product in products"
            :key="product.id"
            class="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
            @click="openProduct(product)"
          >
            <!-- Product Image -->
            <div class="aspect-square bg-gray-100 relative">
              <img
                v-if="product.image_path"
                :src="getImageUrl(product.image_path)"
                :alt="product.title"
                class="w-full h-full object-cover"
                @error="(e) => (e.target as HTMLImageElement).src = '/placeholder-product.png'"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <Icon name="mdi:image-off" class="w-12 h-12 text-gray-300" />
              </div>

              <!-- Discount Badge -->
              <div
                v-if="product.discount_percentage"
                class="absolute top-2 left-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded"
              >
                -{{ product.discount_percentage }}%
              </div>
            </div>

            <!-- Product Info -->
            <div class="p-3">
              <h3 class="text-sm font-medium text-gray-900 line-clamp-2 mb-2">
                {{ product.title }}
              </h3>
              <div class="flex items-center gap-2">
                <span class="text-lg font-bold text-purple-600">
                  {{ formatPrice(product.discount_price || product.base_price) }}
                </span>
                <span
                  v-if="product.discount_price && product.discount_price < product.base_price"
                  class="text-sm text-gray-400 line-through"
                >
                  {{ formatPrice(product.base_price) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12">
          <Icon name="mdi:package-variant-closed" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900 mb-2">Nema aktivnih akcija</h3>
          <p class="text-gray-600">Trenutno nema proizvoda na akciji u ovoj radnji.</p>
        </div>

        <!-- Load More -->
        <div v-if="hasMore" class="text-center mt-8">
          <button
            @click="loadMoreProducts"
            :disabled="isLoadingMore"
            class="px-6 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {{ isLoadingMore ? 'Učitavanje...' : 'Učitaj više' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Product Detail Modal -->
    <ProductDetailModal
      v-if="selectedProduct"
      :product="selectedProduct"
      :is-open="showProductModal"
      @close="closeProductModal"
    />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const config = useRuntimeConfig()
const { get } = useApi()

const businessId = computed(() => route.params.id as string)

const isLoading = ref(true)
const error = ref<string | null>(null)
const business = ref<any>(null)
const products = ref<any[]>([])
const page = ref(1)
const hasMore = ref(false)
const isLoadingMore = ref(false)

// Product modal
const selectedProduct = ref<any>(null)
const showProductModal = ref(false)

// Computed map embed URL
const mapEmbedUrl = computed(() => {
  if (!business.value?.google_link) return null
  return getMapEmbedUrl(business.value.google_link)
})

function getMapEmbedUrl(url: string): string | null {
  if (!url) return null

  try {
    if (url.includes('google.com/maps')) {
      // Format: /maps/search/query/@lat,lng,zoom
      const searchMatch = url.match(/\/maps\/search\/([^/@]+)/)
      if (searchMatch) {
        const query = decodeURIComponent(searchMatch[1].replace(/\+/g, ' '))
        return `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(query)}`
      }

      // Format: /maps/place/name/@lat,lng
      const placeMatch = url.match(/\/maps\/place\/([^/@]+)/)
      if (placeMatch) {
        const place = decodeURIComponent(placeMatch[1].replace(/\+/g, ' '))
        return `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(place)}`
      }

      // Format with coordinates
      const coordMatch = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+)z/)
      if (coordMatch) {
        const [, lat, lng, zoom] = coordMatch
        const pathQuery = url.match(/\/maps\/[^/]+\/([^/@]+)/)
        if (pathQuery) {
          const query = decodeURIComponent(pathQuery[1].replace(/\+/g, ' '))
          return `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(query)}&center=${lat},${lng}&zoom=${zoom}`
        }
        return `https://www.google.com/maps/embed/v1/view?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&center=${lat},${lng}&zoom=${zoom}`
      }
    }
    return null
  } catch (e) {
    return null
  }
}

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  // Handle paths that already have /static/ prefix
  if (path.startsWith('/static/')) return `${config.public.apiBase}${path}`
  // Handle paths that start with uploads/ or static/
  if (path.startsWith('uploads/') || path.startsWith('static/')) {
    return `${config.public.apiBase}/static/${path.replace('static/', '')}`
  }
  return `${config.public.apiBase}/static/${path}`
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('bs-BA', {
    style: 'currency',
    currency: 'BAM',
    minimumFractionDigits: 2
  }).format(price)
}

function openProduct(product: any) {
  // Add business info to product for the modal
  selectedProduct.value = {
    ...product,
    business: {
      id: business.value.id,
      name: business.value.name,
      logo: business.value.logo_path,
      city: business.value.city
    }
  }
  showProductModal.value = true
}

function closeProductModal() {
  showProductModal.value = false
  selectedProduct.value = null
}

async function loadBusiness() {
  try {
    const data = await get(`/api/radnja/${businessId.value}`)
    business.value = data.business
    products.value = data.products || []
    hasMore.value = data.has_more || false
  } catch (e: any) {
    error.value = e.message || 'Greška pri učitavanju radnje'
  } finally {
    isLoading.value = false
  }
}

async function loadMoreProducts() {
  if (isLoadingMore.value) return
  isLoadingMore.value = true

  try {
    page.value++
    const data = await get(`/api/radnja/${businessId.value}/products?page=${page.value}`)
    products.value = [...products.value, ...(data.products || [])]
    hasMore.value = data.has_more || false
  } catch (e) {
    console.error('Error loading more products:', e)
  } finally {
    isLoadingMore.value = false
  }
}

onMounted(() => {
  loadBusiness()
})

// SEO
useSeoMeta({
  title: () => business.value ? `${business.value.name} - Popust.ba` : 'Radnja - Popust.ba',
  description: () => business.value ? `Pogledajte akcije i popuste u ${business.value.name}, ${business.value.city}` : ''
})
</script>
