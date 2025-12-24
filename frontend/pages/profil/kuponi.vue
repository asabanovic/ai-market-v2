<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Moji Kuponi</h1>
          <p class="text-gray-600">Pregled vaših ekskluzivnih popusta</p>
        </div>
        <NuxtLink
          to="/profil"
          class="text-purple-600 hover:text-purple-700 font-medium flex items-center gap-1"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
          Nazad
        </NuxtLink>
      </div>

      <!-- Tabs -->
      <div class="bg-white rounded-lg shadow-md mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex-1 py-4 px-4 text-center border-b-2 font-medium text-sm',
                activeTab === tab.id
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ tab.name }}
              <span v-if="getTabCount(tab.id) > 0" class="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                {{ getTabCount(tab.id) }}
              </span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-orange-600">
          <svg class="animate-spin h-8 w-8" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje kupona...</span>
        </div>
      </div>

      <!-- No Coupons -->
      <div v-else-if="filteredCoupons.length === 0" class="bg-white rounded-lg shadow-md p-12 text-center">
        <svg class="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nema kupona</h3>
        <p class="text-gray-500 mb-6">
          {{ activeTab === 'active' ? 'Nemate aktivnih kupona.' : activeTab === 'redeemed' ? 'Nemate iskorištenih kupona.' : 'Nemate isteklih kupona.' }}
        </p>
        <NuxtLink
          to="/ekskluzivni-popusti"
          class="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
        >
          Pogledaj ekskluzivne popuste
        </NuxtLink>
      </div>

      <!-- Coupons List -->
      <div v-else class="space-y-4">
        <div
          v-for="uc in filteredCoupons"
          :key="uc.id"
          class="bg-white rounded-lg shadow-md overflow-hidden"
        >
          <div class="p-6">
            <div class="flex items-start gap-4">
              <!-- Status Badge -->
              <div class="flex-shrink-0">
                <div
                  :class="[
                    'w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold text-white',
                    uc.status === 'active' ? 'bg-green-500' : uc.status === 'redeemed' ? 'bg-blue-500' : 'bg-gray-400'
                  ]"
                >
                  {{ uc.coupon.discount_percent }}%
                </div>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <h3 class="text-lg font-semibold text-gray-900">{{ uc.coupon.article_name }}</h3>
                  <span
                    :class="[
                      'px-2 py-0.5 text-xs font-medium rounded-full',
                      uc.status === 'active' ? 'bg-green-100 text-green-800' :
                      uc.status === 'redeemed' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    ]"
                  >
                    {{ uc.status === 'active' ? 'Aktivan' : uc.status === 'redeemed' ? 'Iskorišten' : 'Istekao' }}
                  </span>
                </div>

                <div class="text-sm text-gray-500 mb-2">{{ uc.business.name }}</div>

                <div class="flex items-center gap-4 text-sm">
                  <div>
                    <span class="text-gray-500">Cijena:</span>
                    <span class="font-medium text-green-600 ml-1">{{ uc.coupon.final_price.toFixed(2) }} KM</span>
                    <span class="text-gray-400 line-through ml-1">{{ uc.coupon.normal_price.toFixed(2) }} KM</span>
                  </div>
                </div>

                <!-- Active Coupon Details -->
                <div v-if="uc.status === 'active'" class="mt-4">
                  <!-- Redemption Code -->
                  <div class="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
                    <div class="text-sm text-orange-700 mb-1">Vaš kod za redempciju:</div>
                    <div class="text-3xl font-mono font-bold text-orange-600 tracking-widest">
                      {{ uc.redemption_code }}
                    </div>
                    <div class="text-xs text-orange-600 mt-2">
                      Pokažite ovaj kod prodavaču pri kupovini
                    </div>
                  </div>

                  <!-- Expiry -->
                  <div class="flex items-center gap-2 text-sm">
                    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span class="text-gray-500">Ističe:</span>
                    <span class="font-medium text-gray-900">{{ formatDate(uc.expires_at) }}</span>
                    <span class="text-orange-600">({{ getTimeRemaining(uc.expires_at) }})</span>
                  </div>

                  <!-- Google Maps Link -->
                  <a
                    v-if="uc.business.google_link"
                    :href="uc.business.google_link"
                    target="_blank"
                    class="inline-flex items-center gap-1 mt-3 text-orange-600 hover:text-orange-700 text-sm font-medium"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    Prikaži na mapi
                  </a>
                </div>

                <!-- Redeemed Coupon - Rating -->
                <div v-else-if="uc.status === 'redeemed'" class="mt-4">
                  <div class="text-sm text-gray-500 mb-2">Iskorišteno: {{ formatDate(uc.redeemed_at) }}</div>

                  <!-- Rating Form -->
                  <div v-if="uc.can_review && !uc.buyer_to_business_rating" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div class="text-sm font-medium text-blue-700 mb-2">Ocijenite uslugu</div>
                    <div class="flex items-center gap-1 mb-3">
                      <button
                        v-for="star in 5"
                        :key="star"
                        @click="ratingForm.rating = star"
                        class="focus:outline-none"
                      >
                        <svg
                          class="w-8 h-8"
                          :class="star <= ratingForm.rating ? 'text-yellow-400' : 'text-gray-300'"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </button>
                    </div>
                    <textarea
                      v-model="ratingForm.comment"
                      rows="2"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
                      placeholder="Komentar (opcionalno)"
                    ></textarea>
                    <button
                      @click="submitRating(uc)"
                      :disabled="ratingForm.rating === 0"
                      class="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50"
                    >
                      Pošalji ocjenu
                    </button>
                  </div>

                  <!-- Existing Rating -->
                  <div v-else-if="uc.buyer_to_business_rating" class="text-sm text-gray-600">
                    <span>Vaša ocjena:</span>
                    <span class="ml-2">
                      <span v-for="star in 5" :key="star" class="inline">
                        <svg
                          class="w-4 h-4 inline"
                          :class="star <= uc.buyer_to_business_rating ? 'text-yellow-400' : 'text-gray-300'"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </span>
                    </span>
                  </div>

                  <!-- Product Review (24h after) -->
                  <div v-if="uc.can_product_review && !uc.buyer_product_review" class="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
                    <div class="text-sm font-medium text-green-700 mb-2">Recenzija proizvoda</div>
                    <p class="text-xs text-green-600 mb-3">Podijelite svoje iskustvo sa ovim proizvodom</p>
                    <textarea
                      v-model="productReviewForm.review"
                      rows="3"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
                      placeholder="Napišite recenziju (min 20 karaktera)..."
                    ></textarea>
                    <button
                      @click="submitProductReview(uc)"
                      :disabled="!productReviewForm.review || productReviewForm.review.length < 20"
                      class="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 disabled:opacity-50"
                    >
                      Pošalji recenziju
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth']
})

const { get, post } = useApi()

const isLoading = ref(true)
const coupons = ref<any[]>([])
const activeTab = ref('active')

const tabs = [
  { id: 'active', name: 'Aktivni' },
  { id: 'redeemed', name: 'Iskorišteni' },
  { id: 'expired', name: 'Istekli' }
]

const ratingForm = ref({
  rating: 0,
  comment: ''
})

const productReviewForm = ref({
  review: ''
})

const filteredCoupons = computed(() => {
  return coupons.value.filter(c => c.status === activeTab.value)
})

function getTabCount(tabId: string) {
  return coupons.value.filter(c => c.status === tabId).length
}

onMounted(async () => {
  await loadCoupons()
})

async function loadCoupons() {
  isLoading.value = true
  try {
    const res = await get('/api/user/coupons')
    coupons.value = res.coupons || []
  } catch (error) {
    console.error('Error loading coupons:', error)
  } finally {
    isLoading.value = false
  }
}

function formatDate(dateString: string) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getTimeRemaining(dateString: string) {
  const expires = new Date(dateString)
  const now = new Date()
  const diff = expires.getTime() - now.getTime()

  if (diff <= 0) return 'isteklo'

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))

  if (days > 0) return `još ${days} ${days === 1 ? 'dan' : 'dana'}`
  return `još ${hours} ${hours === 1 ? 'sat' : 'sati'}`
}

async function submitRating(userCoupon: any) {
  if (ratingForm.value.rating === 0) return

  try {
    await post(`/api/user/coupons/${userCoupon.id}/review`, {
      rating: ratingForm.value.rating,
      comment: ratingForm.value.comment
    })
    ratingForm.value = { rating: 0, comment: '' }
    await loadCoupons()
  } catch (error: any) {
    console.error('Error submitting rating:', error)
    alert(error.response?.data?.error || 'Greška pri slanju ocjene')
  }
}

async function submitProductReview(userCoupon: any) {
  if (!productReviewForm.value.review || productReviewForm.value.review.length < 20) return

  try {
    await post(`/api/user/coupons/${userCoupon.id}/product-review`, {
      review: productReviewForm.value.review
    })
    productReviewForm.value = { review: '' }
    await loadCoupons()
  } catch (error: any) {
    console.error('Error submitting review:', error)
    alert(error.response?.data?.error || 'Greška pri slanju recenzije')
  }
}

useSeoMeta({
  title: 'Moji Kuponi - Popust.ba',
})
</script>
