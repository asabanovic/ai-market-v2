<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center min-h-screen p-4">
      <div class="text-6xl mb-4">:(</div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">Radnja nije pronađena</h1>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <NuxtLink to="/" class="text-purple-600 hover:text-purple-800">
        Nazad na pocetnu
      </NuxtLink>
    </div>

    <!-- Business Page -->
    <div v-else-if="business">
      <!-- Full Width Map Section -->
      <div class="relative h-56 md:h-80 w-full">
        <!-- Leaflet Map Container -->
        <div
          v-if="hasLocations"
          ref="mapContainer"
          class="w-full h-full z-0 bg-gray-200"
        ></div>
        <!-- Fallback gradient if no locations -->
        <div
          v-else
          class="w-full h-full bg-gradient-to-r from-purple-600 to-blue-600"
        >
          <img
            v-if="business.cover_image_path"
            :src="getImageUrl(business.cover_image_path)"
            :alt="business.name"
            class="w-full h-full object-cover"
          />
        </div>
      </div>

      <!-- Content Container -->
      <div class="max-w-7xl mx-auto pb-8">
        <!-- Profile Section (Facebook-style: logo overlapping cover) -->
        <div class="bg-white shadow-sm relative mx-4 md:mx-6 rounded-b-lg -mt-10 pt-0 pb-4 px-5">
          <!-- Logo + Name Row -->
          <div class="flex items-end gap-4">
            <!-- Logo (overlapping the cover) -->
            <div class="flex-shrink-0 -mt-8">
              <div class="w-24 h-24 md:w-32 md:h-32 rounded-xl bg-white shadow-lg border-4 border-white overflow-hidden">
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

            <!-- Business Name + Rating -->
            <div class="flex-1 pt-14 md:pt-16">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <h1 class="text-2xl md:text-3xl font-bold text-gray-900">{{ business.name }}</h1>
                <!-- Rating Display -->
                <div v-if="business.average_rating > 0" class="flex items-center gap-1 bg-amber-50 px-3 py-1 rounded-full">
                  <svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                  <span class="font-bold text-amber-700">{{ business.average_rating.toFixed(1) }}</span>
                  <span class="text-amber-600 text-sm">({{ business.total_reviews }})</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Stats Row -->
          <div class="flex flex-wrap items-center gap-4 mt-4 text-sm">
            <!-- Total Products -->
            <div class="flex items-center gap-1.5 text-gray-600">
              <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <span><strong class="text-gray-800">{{ business.product_count }}</strong> proizvoda</span>
            </div>

            <!-- Location -->
            <div v-if="business.city" class="flex items-center gap-1.5 text-gray-600">
              <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>{{ business.city }}</span>
            </div>
          </div>

          <!-- Description -->
          <p v-if="business.description" class="mt-4 text-gray-600 text-sm">
            {{ business.description }}
          </p>

          <!-- Contact Links -->
          <div v-if="hasSocialLinks" class="flex flex-wrap gap-3 mt-4">
            <a v-if="business.website_url" :href="business.website_url" target="_blank" class="flex items-center gap-1.5 text-sm text-purple-600 hover:text-purple-800">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              Web stranica
            </a>
            <a v-if="business.facebook_url" :href="business.facebook_url" target="_blank" class="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
              Facebook
            </a>
            <a v-if="business.instagram_url" :href="business.instagram_url" target="_blank" class="flex items-center gap-1.5 text-sm text-pink-600 hover:text-pink-800">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
              </svg>
              Instagram
            </a>
          </div>
        </div>

        <!-- Featured Products -->
        <div v-if="featuredProducts.length > 0" class="mx-4 mt-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold text-gray-900">Istaknuti proizvodi</h2>
          </div>
          <div class="flex md:grid md:grid-cols-4 gap-4 overflow-x-auto md:overflow-visible pb-2 md:pb-0 snap-x snap-mandatory md:snap-none -mx-2 px-2 md:mx-0 md:px-0">
            <div v-for="product in featuredProducts.slice(0, 4)" :key="product.id" class="flex-shrink-0 w-[70vw] sm:w-[45vw] md:w-auto snap-start">
              <ProductCard :product="product" />
            </div>
          </div>
        </div>

        <!-- Login/Register CTA for all users (this is public page) -->
        <div v-if="!isAuthenticated" class="mx-4 mt-6">
          <div class="bg-gradient-to-r from-purple-600 to-purple-700 rounded-2xl p-8 text-center text-white shadow-lg">
            <div class="max-w-md mx-auto">
              <svg class="w-16 h-16 mx-auto mb-4 text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <h3 class="text-2xl font-bold mb-2">Pristupite svim proizvodima</h3>
              <p class="text-purple-200 mb-6">
                Prijavite se ili registrujte da vidite svih <strong class="text-white">{{ business.product_count }}</strong> proizvoda ove radnje i otkrijte najbolje popuste!
              </p>
              <div class="flex flex-col sm:flex-row gap-3 justify-center">
                <NuxtLink
                  to="/prijava"
                  class="px-6 py-3 bg-white text-purple-700 font-semibold rounded-lg hover:bg-purple-50 transition-colors"
                >
                  Prijava
                </NuxtLink>
                <NuxtLink
                  to="/registracija"
                  class="px-6 py-3 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-400 transition-colors border border-purple-400"
                >
                  Registracija
                </NuxtLink>
              </div>
            </div>
          </div>
        </div>

        <!-- Full Products Section (authenticated users) -->
        <div v-else class="mx-4 mt-6">
          <NuxtLink
            :to="`/radnja/${business.slug || business.id}`"
            class="inline-flex items-center gap-2 text-purple-600 hover:text-purple-800 font-medium"
          >
            Pogledaj sve proizvode
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const config = useRuntimeConfig()

const loading = ref(true)
const error = ref('')
const business = ref<any>(null)
const featuredProducts = ref<any[]>([])
const isAuthenticated = ref(false)
const mapContainer = ref<HTMLElement | null>(null)
let mapInstance: any = null

// Check if we have locations with valid coordinates
const hasLocations = computed(() => {
  if (!business.value?.locations || business.value.locations.length === 0) return false
  return business.value.locations.some((loc: any) => loc.latitude && loc.longitude)
})

// Check if business has any social links
const hasSocialLinks = computed(() => {
  if (!business.value) return false
  return business.value.website_url ||
         business.value.facebook_url ||
         business.value.instagram_url ||
         business.value.viber_contact ||
         business.value.contact_email
})

function getApiUrl() {
  return config.public.apiBase || 'http://localhost:5001'
}

function getImageUrl(path: string) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const apiUrl = getApiUrl()
  return `${apiUrl}${path.startsWith('/') ? '' : '/'}${path}`
}

function getToken() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token')
  }
  return null
}

async function initMap() {
  if (!mapContainer.value || !hasLocations.value) return

  try {
    const L = (await import('leaflet')).default
    await import('leaflet/dist/leaflet.css')

    // Clean up existing map
    if (mapInstance) {
      mapInstance.remove()
      mapInstance = null
    }

    const locations = business.value.locations.filter((loc: any) => loc.latitude && loc.longitude)
    if (locations.length === 0) return

    // Center on first location
    const firstLoc = locations[0]
    mapInstance = L.map(mapContainer.value, {
      center: [firstLoc.latitude, firstLoc.longitude],
      zoom: 14,
      zoomControl: true,
      attributionControl: false
    })

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19
    }).addTo(mapInstance)

    // Custom marker icon
    const customIcon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="background: #7c3aed; width: 32px; height: 32px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    // Add markers for all locations
    const markers: any[] = []
    locations.forEach((loc: any) => {
      const marker = L.marker([loc.latitude, loc.longitude], { icon: customIcon })
        .addTo(mapInstance)

      // Create popup content
      let popupContent = `<strong>${business.value.name}</strong>`
      if (loc.address) popupContent += `<br/>${loc.address}`
      if (loc.city) popupContent += `<br/>${loc.city}`

      marker.bindPopup(popupContent)
      markers.push(marker)
    })

    // Fit bounds if multiple locations
    if (markers.length > 1) {
      const group = L.featureGroup(markers)
      mapInstance.fitBounds(group.getBounds().pad(0.1))
    }

  } catch (err) {
    console.error('Error initializing Leaflet map:', err)
  }
}

async function fetchBusiness() {
  try {
    const slug = route.params.slug as string
    const token = getToken()

    // Build headers - token is optional for public access
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${getApiUrl()}/api/radnja/${slug}`, { headers })
    const data = await response.json()

    if (!response.ok) {
      error.value = data.error || 'Radnja nije pronađena'
      return
    }

    // Track authentication status from API response
    isAuthenticated.value = data.is_authenticated || false

    business.value = data.business
    featuredProducts.value = data.featured_products || []

    // Initialize map after data is loaded
    await nextTick()
    initMap()
  } catch (e) {
    error.value = 'Greška pri učitavanju radnje'
  } finally {
    loading.value = false
  }
}

// SEO Meta
useHead(() => ({
  title: business.value ? `${business.value.name} | Popust.ba` : 'Radnja | Popust.ba',
  meta: [
    {
      name: 'description',
      content: business.value?.description || `Pogledajte popuste u radnji ${business.value?.name || ''} na Popust.ba`
    }
  ]
}))

onMounted(async () => {
  await fetchBusiness()
})

// Watch for mapContainer to become available
watch(mapContainer, (newContainer) => {
  if (newContainer && hasLocations.value && !mapInstance) {
    initMap()
  }
})

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>
