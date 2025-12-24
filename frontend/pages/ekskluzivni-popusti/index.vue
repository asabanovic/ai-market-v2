<template>
  <div class="min-h-screen bg-gradient-to-b from-orange-50 to-white">
    <!-- Hero Section -->
    <div class="bg-gradient-to-r from-orange-500 to-red-500 text-white py-12 md:py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 class="text-3xl md:text-4xl font-bold mb-4">
          Ekskluzivni Popusti
        </h1>
        <p class="text-lg md:text-xl text-orange-100 max-w-2xl mx-auto">
          Samo na Popust.ba - limitirane ponude lokalnih biznisa koje ne možete pronaći nigdje drugdje
        </p>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Feature Not Available -->
      <div v-if="!featureEnabled && !isAdmin" class="text-center py-16">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-4">
          <svg class="w-8 h-8 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Uskoro dolazi!</h2>
        <p class="text-gray-600 max-w-md mx-auto">
          Ekskluzivni popusti su trenutno u pripremi. Vrati se uskoro za nevjerovatne ponude lokalnih biznisa.
        </p>
      </div>

      <!-- Loading -->
      <div v-else-if="isLoading" class="text-center py-16">
        <div class="inline-flex items-center text-orange-600">
          <svg class="animate-spin h-8 w-8" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje ponuda...</span>
        </div>
      </div>

      <!-- No Coupons -->
      <div v-else-if="coupons.length === 0" class="text-center py-16">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Nema dostupnih kupona</h2>
        <p class="text-gray-600">Trenutno nema aktivnih ekskluzivnih ponuda. Vrati se kasnije!</p>
      </div>

      <!-- Coupons Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="coupon in coupons"
          :key="coupon.id"
          class="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 cursor-pointer group"
          @click="openCouponModal(coupon)"
        >
          <!-- Discount Badge -->
          <div class="relative bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white">
            <div class="absolute top-3 right-3 bg-white/20 backdrop-blur-sm rounded-full px-3 py-1 text-sm font-medium">
              {{ coupon.remaining_quantity }}/{{ coupon.total_quantity }} preostalo
            </div>
            <div class="text-5xl md:text-6xl font-black mb-1">
              {{ coupon.discount_percent }}%
            </div>
            <div class="text-orange-100 font-medium">POPUST</div>
          </div>

          <!-- Content -->
          <div class="p-6">
            <!-- Business Info -->
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center overflow-hidden">
                <img
                  v-if="coupon.business.logo_path"
                  :src="coupon.business.logo_path"
                  :alt="coupon.business.name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-xl font-bold text-gray-400">
                  {{ coupon.business.name.charAt(0) }}
                </span>
              </div>
              <div>
                <div class="font-medium text-gray-900">{{ coupon.business.name }}</div>
                <div class="flex items-center gap-2 text-sm text-gray-500">
                  <span>{{ coupon.business.city }}</span>
                  <span v-if="coupon.business.is_open" class="flex items-center text-green-600">
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                    Otvoreno
                  </span>
                </div>
              </div>
            </div>

            <!-- Article -->
            <h3 class="text-xl font-bold text-gray-900 mb-2 group-hover:text-orange-600 transition-colors">
              {{ coupon.article_name }}
            </h3>

            <!-- Price -->
            <div class="flex items-baseline gap-2 mb-4">
              <span class="text-2xl font-bold text-green-600">{{ coupon.final_price.toFixed(2) }} KM</span>
              <span class="text-lg text-gray-400 line-through">{{ coupon.normal_price.toFixed(2) }} KM</span>
            </div>

            <!-- Quantity & Validity -->
            <div class="flex items-center justify-between text-sm text-gray-500">
              <span v-if="coupon.quantity_description">{{ coupon.quantity_description }}</span>
              <span>Vrijedi {{ coupon.valid_days }} {{ coupon.valid_days === 1 ? 'dan' : 'dana' }}</span>
            </div>

            <!-- CTA -->
            <button class="mt-4 w-full py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
              </svg>
              Uzmi kupon za {{ coupon.credits_cost }} kredita
            </button>
          </div>
        </div>
      </div>

      <!-- Coupon Modal -->
      <CouponModal
        v-if="selectedCoupon"
        :coupon="selectedCoupon"
        :user-credits="userCredits"
        @close="selectedCoupon = null"
        @purchase="purchaseCoupon"
        @earn-credits="showEarnCreditsModal = true"
      />

      <!-- Earn Credits Modal -->
      <EarnCreditsModal
        v-if="showEarnCreditsModal"
        :required-credits="requiredCredits"
        :current-credits="userCredits"
        @close="closeEarnCreditsModal"
        @credits-earned="onCreditsEarned"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const { get, post } = useApi()
const { user } = useAuth()

const isLoading = ref(true)
const featureEnabled = ref(false)
const isAdmin = ref(false)
const coupons = ref<any[]>([])
const userCredits = ref(0)

const selectedCoupon = ref<any>(null)
const showEarnCreditsModal = ref(false)
const requiredCredits = ref(0)

onMounted(async () => {
  await loadData()
})

async function loadData() {
  isLoading.value = true
  try {
    // Check feature status
    const statusRes = await get('/api/coupons/feature-status')
    featureEnabled.value = statusRes.enabled
    isAdmin.value = statusRes.is_admin

    if (featureEnabled.value || isAdmin.value) {
      // Load coupons
      const couponsRes = await get('/api/coupons')
      coupons.value = couponsRes.coupons || []

      // Load user credits if logged in
      if (user.value) {
        const creditsRes = await get('/api/credits/balance')
        userCredits.value = creditsRes.available || 0
      }
    }
  } catch (error) {
    console.error('Error loading data:', error)
  } finally {
    isLoading.value = false
  }
}

function openCouponModal(coupon: any) {
  selectedCoupon.value = coupon
}

async function purchaseCoupon(coupon: any) {
  if (!user.value) {
    navigateTo('/prijava?redirect=/ekskluzivni-popusti')
    return
  }

  if (userCredits.value < coupon.credits_cost) {
    requiredCredits.value = coupon.credits_cost - userCredits.value
    showEarnCreditsModal.value = true
    return
  }

  try {
    const res = await post(`/api/coupons/${coupon.id}/purchase`, {})
    if (res.success) {
      // Show success and redirect to profile
      alert(`Kupon uspješno kupljen! Vaš kod: ${res.user_coupon.redemption_code}`)
      selectedCoupon.value = null
      await loadData()
      navigateTo('/profil?tab=kuponi')
    }
  } catch (error: any) {
    console.error('Error purchasing coupon:', error)
    alert(error.response?.data?.error || 'Greška pri kupovini kupona')
  }
}

function closeEarnCreditsModal() {
  showEarnCreditsModal.value = false
}

async function onCreditsEarned(newCredits: number) {
  userCredits.value = newCredits
  if (selectedCoupon.value && userCredits.value >= selectedCoupon.value.credits_cost) {
    showEarnCreditsModal.value = false
  }
}

useSeoMeta({
  title: 'Ekskluzivni Popusti - Popust.ba',
  description: 'Ekskluzivni popusti samo na Popust.ba - limitirane ponude lokalnih biznisa koje ne možete pronaći nigdje drugdje',
})
</script>
