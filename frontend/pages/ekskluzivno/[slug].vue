<template>
  <div class="min-h-screen bg-gradient-to-b from-orange-50 to-white">
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <svg class="animate-spin h-12 w-12 text-orange-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p class="text-gray-600">Učitavanje...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="text-center max-w-md px-4">
        <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Biznis nije pronađen</h1>
        <p class="text-gray-600 mb-6">{{ error }}</p>
        <NuxtLink to="/" class="inline-flex items-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>
          </svg>
          Nazad na početnu
        </NuxtLink>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else-if="business">
      <!-- Cover Image Hero -->
      <div class="relative h-64 md:h-80 lg:h-96 bg-gradient-to-r from-orange-500 to-red-500">
        <img
          v-if="business.cover_image_path"
          :src="business.cover_image_path"
          :alt="business.name"
          class="absolute inset-0 w-full h-full object-cover"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent"></div>

        <!-- Business Info Overlay -->
        <div class="absolute bottom-0 left-0 right-0 p-6 md:p-8">
          <div class="max-w-7xl mx-auto flex items-end gap-4 md:gap-6">
            <!-- Logo -->
            <div class="w-20 h-20 md:w-28 md:h-28 bg-white rounded-2xl shadow-xl flex items-center justify-center overflow-hidden flex-shrink-0">
              <img
                v-if="business.logo_path"
                :src="business.logo_path"
                :alt="business.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-3xl md:text-4xl font-bold text-orange-500">
                {{ business.name.charAt(0) }}
              </span>
            </div>

            <!-- Business Details -->
            <div class="flex-1 text-white">
              <h1 class="text-2xl md:text-4xl font-bold mb-1 drop-shadow-lg">{{ business.name }}</h1>
              <div class="flex flex-wrap items-center gap-2 md:gap-4 text-white/90 text-sm md:text-base">
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                  {{ business.city }}
                </span>
                <span v-if="business.category" class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                  </svg>
                  {{ business.category }}
                </span>
              </div>
            </div>

            <!-- Share Button -->
            <button
              @click="shareOnFacebook"
              class="hidden md:flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors shadow-lg"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.77 7.46H14.5v-1.9c0-.9.6-1.1 1-1.1h3V.5h-4.33C10.24.5 9.5 3.44 9.5 5.32v2.15h-3v4h3v12h5v-12h3.85l.42-4z"/>
              </svg>
              Podijeli
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile Share Button -->
      <div class="md:hidden px-4 py-3 bg-white border-b">
        <button
          @click="shareOnFacebook"
          class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M18.77 7.46H14.5v-1.9c0-.9.6-1.1 1-1.1h3V.5h-4.33C10.24.5 9.5 3.44 9.5 5.32v2.15h-3v4h3v12h5v-12h3.85l.42-4z"/>
          </svg>
          Podijeli na Facebook
        </button>
      </div>

      <!-- Content -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Exclusive Offers Header -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center gap-2 bg-orange-100 text-orange-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <span class="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></span>
            Ekskluzivno na Popust.ba
          </div>
          <h2 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            Ekskluzivni Popusti
          </h2>
          <p class="text-gray-600 max-w-2xl mx-auto">
            Iskoristi jedinstvene ponude koje možeš pronaći samo ovdje!
          </p>
        </div>

        <!-- No Coupons -->
        <div v-if="coupons.length === 0" class="text-center py-16">
          <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Nema aktivnih kupona</h3>
          <p class="text-gray-600">Trenutno nema aktivnih ekskluzivnih ponuda za ovaj biznis.</p>
        </div>

        <!-- Coupons Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="coupon in coupons"
            :key="coupon.id"
            class="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <!-- Coupon Image or Discount Badge -->
            <div class="relative">
              <div v-if="coupon.image_path" class="aspect-video bg-gray-100">
                <img :src="coupon.image_path" :alt="coupon.article_name" class="w-full h-full object-cover" />
              </div>
              <div v-else class="bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white text-center">
                <div class="text-5xl md:text-6xl font-black mb-1">{{ coupon.discount_percent }}%</div>
                <div class="text-orange-100 font-medium">POPUST</div>
              </div>

              <!-- Remaining Badge -->
              <div class="absolute top-3 right-3 bg-black/70 backdrop-blur-sm rounded-full px-3 py-1.5 text-white text-sm font-bold">
                <span class="text-orange-400">{{ coupon.remaining_quantity }}</span>/{{ coupon.total_quantity }} preostalo
              </div>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- FOMO Countdown Timer -->
              <div v-if="coupon.countdown" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
                <div class="text-xs text-red-600 font-medium mb-2 flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  PONUDA ISTIČE ZA:
                </div>
                <div class="grid grid-cols-4 gap-2 text-center">
                  <div class="bg-white rounded-lg p-2 shadow-sm">
                    <div class="text-xl md:text-2xl font-black text-red-600">{{ coupon.countdown.days }}</div>
                    <div class="text-xs text-gray-500">dana</div>
                  </div>
                  <div class="bg-white rounded-lg p-2 shadow-sm">
                    <div class="text-xl md:text-2xl font-black text-red-600">{{ coupon.countdown.hours }}</div>
                    <div class="text-xs text-gray-500">sati</div>
                  </div>
                  <div class="bg-white rounded-lg p-2 shadow-sm">
                    <div class="text-xl md:text-2xl font-black text-red-600">{{ coupon.countdown.minutes }}</div>
                    <div class="text-xs text-gray-500">min</div>
                  </div>
                  <div class="bg-white rounded-lg p-2 shadow-sm">
                    <div class="text-xl md:text-2xl font-black text-red-600 tabular-nums">{{ coupon.countdown.seconds }}</div>
                    <div class="text-xs text-gray-500">sek</div>
                  </div>
                </div>
              </div>

              <!-- Article Name -->
              <h3 class="text-xl font-bold text-gray-900 mb-2">{{ coupon.article_name }}</h3>

              <!-- Price -->
              <div class="flex items-baseline gap-2 mb-3">
                <span class="text-2xl font-bold text-green-600">{{ coupon.final_price.toFixed(2) }} KM</span>
                <span class="text-lg text-gray-400 line-through">{{ coupon.normal_price.toFixed(2) }} KM</span>
                <span class="ml-auto px-2 py-1 bg-green-100 text-green-700 text-sm font-bold rounded-lg">
                  -{{ coupon.discount_percent }}%
                </span>
              </div>

              <!-- FOMO Text -->
              <div class="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-xl">
                <p class="text-orange-800 text-sm font-medium">
                  <span class="inline-flex items-center gap-1">
                    <svg class="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clip-rule="evenodd"></path>
                    </svg>
                    Prvih {{ coupon.total_quantity }} osoba koji preuzmu kupon!
                  </span>
                </p>
              </div>

              <!-- Store Location (if applicable) -->
              <div v-if="coupon.store" class="mb-4 text-sm text-gray-600 flex items-start gap-2">
                <svg class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <div>
                  <div class="font-medium text-gray-900">{{ coupon.store.name }}</div>
                  <div>{{ coupon.store.address }}, {{ coupon.store.city }}</div>
                </div>
              </div>

              <!-- CTA Button -->
              <button
                v-if="isAuthenticated"
                @click="claimCoupon(coupon)"
                :disabled="coupon.remaining_quantity === 0"
                class="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
                </svg>
                {{ coupon.remaining_quantity === 0 ? 'Nema više kupona' : `Preuzmi za ${coupon.credits_cost} kredita` }}
              </button>
              <NuxtLink
                v-else
                :to="`/registracija?redirect=/ekskluzivno/${slug}`"
                class="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path>
                </svg>
                Registruj se BESPLATNO da preuzmeš!
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- Stores Section (if multiple) -->
        <div v-if="stores.length > 1" class="mt-12">
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lokacije</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="store in stores"
              :key="store.id"
              class="bg-white rounded-xl shadow p-4 border border-gray-100"
            >
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-900">{{ store.name }}</div>
                  <div class="text-sm text-gray-600">{{ store.address }}, {{ store.city }}</div>
                  <div v-if="store.phone" class="text-sm text-gray-500 mt-1">
                    <a :href="`tel:${store.phone}`" class="hover:text-orange-600">{{ store.phone }}</a>
                  </div>
                  <div v-if="store.is_open_now !== undefined" class="mt-2">
                    <span v-if="store.is_open_now" class="inline-flex items-center text-xs text-green-600 font-medium">
                      <span class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                      Otvoreno
                    </span>
                    <span v-else class="inline-flex items-center text-xs text-red-600 font-medium">
                      <span class="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
                      Zatvoreno
                    </span>
                  </div>
                  <a
                    v-if="store.google_maps_link"
                    :href="store.google_maps_link"
                    target="_blank"
                    rel="noopener"
                    class="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 mt-2"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                    </svg>
                    Otvori u Google Maps
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Back to All Coupons -->
        <div class="mt-12 text-center">
          <NuxtLink
            to="/ekskluzivni-popusti"
            class="inline-flex items-center gap-2 text-orange-600 hover:text-orange-700 font-medium"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16l-4-4m0 0l4-4m-4 4h18"></path>
            </svg>
            Pogledaj sve ekskluzivne popuste
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { get, post } = useApi()
const { user, isAuthenticated } = useAuth()

const slug = computed(() => route.params.slug as string)

const isLoading = ref(true)
const error = ref<string | null>(null)
const business = ref<any>(null)
const stores = ref<any[]>([])
const coupons = ref<any[]>([])
const shareData = ref<any>(null)

// Countdown timer interval
let countdownInterval: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await loadLandingPage()
  startCountdownTimer()
})

onUnmounted(() => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }
})

async function loadLandingPage() {
  isLoading.value = true
  error.value = null

  try {
    const response = await get(`/api/ekskluzivno/${slug.value}`)
    business.value = response.business
    stores.value = response.stores || []
    shareData.value = response.share

    // Process coupons and add countdown data
    coupons.value = (response.coupons || []).map((coupon: any) => ({
      ...coupon,
      countdown: coupon.expires_at ? calculateCountdown(coupon.expires_at) : null
    }))
  } catch (err: any) {
    console.error('Error loading landing page:', err)
    error.value = err.message || 'Greška pri učitavanju stranice'
  } finally {
    isLoading.value = false
  }
}

function calculateCountdown(expiresAt: string) {
  const now = new Date().getTime()
  const expiry = new Date(expiresAt).getTime()
  const diff = expiry - now

  if (diff <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true }
  }

  return {
    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
    hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
    minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
    seconds: Math.floor((diff % (1000 * 60)) / 1000),
    expired: false
  }
}

function startCountdownTimer() {
  countdownInterval = setInterval(() => {
    coupons.value = coupons.value.map(coupon => ({
      ...coupon,
      countdown: coupon.expires_at ? calculateCountdown(coupon.expires_at) : null
    }))
  }, 1000)
}

function shareOnFacebook() {
  if (!shareData.value) return

  const fbShareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareData.value.url)}&quote=${encodeURIComponent(shareData.value.title)}`
  window.open(fbShareUrl, 'facebook-share', 'width=580,height=296')
}

async function claimCoupon(coupon: any) {
  if (!isAuthenticated.value) {
    navigateTo(`/registracija?redirect=/ekskluzivno/${slug.value}`)
    return
  }

  try {
    const response = await post(`/api/coupons/${coupon.id}/purchase`, {})
    if (response.success) {
      alert(`Kupon uspješno preuzet! Tvoj kod: ${response.user_coupon.redemption_code}`)
      // Refresh data
      await loadLandingPage()
      // Redirect to profile
      navigateTo('/profil?tab=kuponi')
    }
  } catch (err: any) {
    console.error('Error claiming coupon:', err)
    alert(err.message || 'Greška pri preuzimanju kupona')
  }
}

// SEO
useSeoMeta({
  title: () => business.value ? `${business.value.name} - Ekskluzivni Popusti | Popust.ba` : 'Ekskluzivni Popusti | Popust.ba',
  description: () => shareData.value?.description || 'Ekskluzivni popusti samo na Popust.ba',
  ogTitle: () => shareData.value?.title || 'Ekskluzivni Popusti | Popust.ba',
  ogDescription: () => shareData.value?.description || 'Ekskluzivni popusti samo na Popust.ba',
  ogImage: () => business.value?.cover_image_path || business.value?.logo_path,
  ogUrl: () => shareData.value?.url,
  twitterCard: 'summary_large_image',
})
</script>

<style scoped>
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
</style>
