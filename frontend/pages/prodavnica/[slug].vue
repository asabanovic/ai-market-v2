<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center min-h-screen p-4">
      <div class="text-6xl mb-4">:(</div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">Prodavnica nije pronađena</h1>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <NuxtLink to="/" class="text-blue-600 hover:underline">Povratak na početnu</NuxtLink>
    </div>

    <!-- Business Page -->
    <div v-else-if="business" class="max-w-7xl mx-auto">
      <!-- Cover Image -->
      <div class="relative h-48 md:h-64 bg-gradient-to-r from-blue-600 to-purple-600">
        <img
          v-if="business.cover_image_path"
          :src="getImageUrl(business.cover_image_path)"
          :alt="business.name"
          class="w-full h-full object-cover"
        />
      </div>

      <!-- Business Info Header -->
      <div class="bg-white shadow-sm -mt-16 relative mx-4 rounded-lg p-6">
        <div class="flex flex-col md:flex-row md:items-start gap-4">
          <!-- Logo -->
          <div class="flex-shrink-0 -mt-16 md:-mt-20">
            <div class="w-24 h-24 md:w-32 md:h-32 rounded-lg bg-white shadow-lg border-4 border-white overflow-hidden">
              <img
                v-if="business.logo_path"
                :src="getImageUrl(business.logo_path)"
                :alt="business.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full bg-gray-200 flex items-center justify-center">
                <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Business Details -->
          <div class="flex-1 md:mt-0 mt-4">
            <h1 class="text-2xl md:text-3xl font-bold text-gray-900">{{ business.name }}</h1>

            <!-- Rating -->
            <div v-if="business.average_rating" class="flex items-center gap-2 mt-2">
              <div class="flex items-center">
                <svg v-for="i in 5" :key="i" class="w-5 h-5" :class="i <= Math.round(business.average_rating) ? 'text-yellow-400' : 'text-gray-300'" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span class="ml-2 text-gray-600">{{ business.average_rating.toFixed(1) }} ({{ business.total_reviews }} recenzija)</span>
              </div>
            </div>

            <!-- Description -->
            <p v-if="business.description" class="text-gray-600 mt-3">{{ business.description }}</p>
          </div>
        </div>

        <!-- Contact Info Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t">
          <!-- Address -->
          <div v-if="business.address || business.city" class="flex items-start gap-3">
            <div class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <p class="text-sm text-gray-500">Adresa</p>
              <p class="font-medium text-gray-900">{{ business.address }}</p>
              <p class="text-gray-600">{{ business.city }}</p>
            </div>
          </div>

          <!-- Phone -->
          <div v-if="business.contact_phone" class="flex items-start gap-3">
            <div class="flex-shrink-0 w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div>
              <p class="text-sm text-gray-500">Telefon</p>
              <a :href="'tel:' + business.contact_phone" class="font-medium text-gray-900 hover:text-blue-600">
                {{ business.contact_phone }}
              </a>
            </div>
          </div>

          <!-- Working Hours -->
          <div v-if="business.working_hours" class="flex items-start gap-3">
            <div class="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p class="text-sm text-gray-500">Radno vrijeme</p>
              <p class="font-medium text-gray-900">{{ business.working_hours }}</p>
            </div>
          </div>
        </div>

        <!-- Google Maps Link -->
        <div v-if="business.google_link" class="mt-4">
          <a :href="business.google_link" target="_blank" rel="noopener noreferrer"
             class="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            Pogledaj na Google Maps
          </a>
        </div>
      </div>

      <!-- Map Section (if address is available) -->
      <div v-if="business.address && business.city" class="mx-4 mt-6">
        <div class="bg-white rounded-lg shadow-sm overflow-hidden">
          <iframe
            :src="getMapUrl()"
            width="100%"
            height="300"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            class="w-full"
          ></iframe>
        </div>
      </div>

      <!-- Products Section -->
      <div class="mx-4 mt-6 mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-900">
            Proizvodi
            <span v-if="business.product_count" class="text-gray-500 font-normal text-base">({{ business.product_count }})</span>
          </h2>
        </div>

        <!-- Not Logged In - CTA -->
        <div v-if="!isLoggedIn" class="bg-white rounded-lg shadow-sm p-8 text-center">
          <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Registrujte se da vidite proizvode</h3>
          <p class="text-gray-600 mb-6">Prijavite se ili kreirajte nalog da pristupite katalog proizvoda i popustima.</p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <NuxtLink
              to="/registracija"
              class="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Registrujte se
            </NuxtLink>
            <NuxtLink
              to="/prijava"
              class="px-6 py-3 bg-white text-blue-600 font-medium rounded-lg border border-blue-600 hover:bg-blue-50 transition-colors"
            >
              Prijavite se
            </NuxtLink>
          </div>
        </div>

        <!-- Logged In - Products Grid -->
        <div v-else>
          <!-- Search -->
          <div class="mb-4">
            <div class="relative">
              <input
                v-model="searchQuery"
                @input="debouncedSearch"
                type="text"
                placeholder="Pretraži proizvode..."
                class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
              />
              <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <!-- Loading Products -->
          <div v-if="loadingProducts" class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>

          <!-- Products Grid -->
          <div v-else-if="products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <ProductCard v-for="product in products" :key="product.id" :product="product" />
          </div>

          <!-- No Products -->
          <div v-else class="bg-white rounded-lg shadow-sm p-8 text-center">
            <p class="text-gray-600">Nema proizvoda za prikaz</p>
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="flex justify-center mt-6 gap-2">
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Prethodna
            </button>
            <span class="px-4 py-2 text-gray-600">
              {{ currentPage }} / {{ totalPages }}
            </span>
            <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Sljedeća
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const config = useRuntimeConfig()

const loading = ref(true)
const error = ref('')
const business = ref<any>(null)
const products = ref<any[]>([])
const loadingProducts = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)

// Check if user is logged in
const isLoggedIn = computed(() => {
  if (typeof window !== 'undefined') {
    return !!localStorage.getItem('token')
  }
  return false
})

function getApiUrl() {
  return config.public.apiBase || 'http://localhost:5001'
}

function getImageUrl(path: string) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${getApiUrl()}${path}`
}

function getMapUrl() {
  if (!business.value) return ''
  const address = encodeURIComponent(`${business.value.address}, ${business.value.city}, Bosnia and Herzegovina`)
  return `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${address}&zoom=17`
}

async function fetchBusiness() {
  try {
    const slug = route.params.slug as string
    const response = await fetch(`${getApiUrl()}/api/prodavnica/${slug}`)
    const data = await response.json()

    if (!response.ok) {
      error.value = data.error || 'Prodavnica nije pronađena'
      return
    }

    business.value = data.business
  } catch (e) {
    error.value = 'Greška pri učitavanju prodavnice'
  } finally {
    loading.value = false
  }
}

async function fetchProducts() {
  if (!isLoggedIn.value) return

  loadingProducts.value = true
  try {
    const slug = route.params.slug as string
    const token = localStorage.getItem('token')
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      per_page: '30',
      ...(searchQuery.value && { search: searchQuery.value })
    })

    const response = await fetch(`${getApiUrl()}/api/prodavnica/${slug}/products?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      products.value = data.products
      totalPages.value = data.pages
    }
  } catch (e) {
    console.error('Error fetching products:', e)
  } finally {
    loadingProducts.value = false
  }
}

let searchTimeout: any = null
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchProducts()
  }, 300)
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchProducts()
  }
}

onMounted(async () => {
  await fetchBusiness()
  if (business.value && isLoggedIn.value) {
    await fetchProducts()
  }
})
</script>
