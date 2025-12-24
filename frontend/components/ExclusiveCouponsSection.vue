<template>
  <div v-if="isVisible" class="py-8 lg:py-12 bg-gradient-to-b from-orange-50 to-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center gap-2 bg-orange-100 text-orange-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
          <span class="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></span>
          Samo na Popust.ba
        </div>
        <h2 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          Ekskluzivni Popusti
        </h2>
        <p class="text-gray-600 max-w-2xl mx-auto">
          Limitirane ponude lokalnih biznisa koje ne možete pronaći nigdje drugdje
        </p>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex justify-center py-8">
        <div class="inline-flex items-center text-orange-600">
          <svg class="animate-spin h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Učitavanje...
        </div>
      </div>

      <!-- Coupons Grid -->
      <div v-else-if="coupons.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <NuxtLink
          v-for="coupon in displayedCoupons"
          :key="coupon.id"
          to="/ekskluzivni-popusti"
          class="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 group"
        >
          <!-- Discount Badge -->
          <div class="relative bg-gradient-to-r from-orange-500 to-red-500 p-5 text-white">
            <div class="absolute top-2 right-2 bg-white/20 backdrop-blur-sm rounded-full px-2 py-0.5 text-xs font-medium">
              {{ coupon.remaining_quantity }}/{{ coupon.total_quantity }}
            </div>
            <div class="text-4xl md:text-5xl font-black">{{ coupon.discount_percent }}%</div>
            <div class="text-orange-100 text-sm font-medium">POPUST</div>
          </div>

          <!-- Content -->
          <div class="p-5">
            <!-- Business -->
            <div class="flex items-center gap-2 mb-3">
              <div class="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center overflow-hidden">
                <img
                  v-if="coupon.business.logo_path"
                  :src="coupon.business.logo_path"
                  :alt="coupon.business.name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-sm font-bold text-gray-400">
                  {{ coupon.business.name.charAt(0) }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-gray-900 truncate">{{ coupon.business.name }}</div>
                <div class="flex items-center gap-1 text-xs text-gray-500">
                  <span v-if="coupon.business.is_open" class="flex items-center text-green-600">
                    <span class="w-1.5 h-1.5 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                    Otvoreno
                  </span>
                  <span v-else>{{ coupon.business.city }}</span>
                </div>
              </div>
            </div>

            <!-- Article -->
            <h3 class="font-bold text-gray-900 mb-2 group-hover:text-orange-600 transition-colors line-clamp-2">
              {{ coupon.article_name }}
            </h3>

            <!-- Price -->
            <div class="flex items-baseline gap-2">
              <span class="text-xl font-bold text-green-600">{{ coupon.final_price.toFixed(2) }} KM</span>
              <span class="text-sm text-gray-400 line-through">{{ coupon.normal_price.toFixed(2) }} KM</span>
            </div>
          </div>
        </NuxtLink>
      </div>

      <!-- No Coupons -->
      <div v-else class="text-center py-8">
        <p class="text-gray-500">Trenutno nema aktivnih ekskluzivnih ponuda.</p>
      </div>

      <!-- View All Link -->
      <div v-if="coupons.length > 0" class="text-center mt-8">
        <NuxtLink
          to="/ekskluzivni-popusti"
          class="inline-flex items-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors"
        >
          Vidi sve ekskluzivne popuste
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
          </svg>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const isLoading = ref(true)
const isVisible = ref(false)
const coupons = ref<any[]>([])

const displayedCoupons = computed(() => coupons.value.slice(0, 3))

onMounted(async () => {
  try {
    // Check if feature is enabled
    const statusRes = await get('/api/coupons/feature-status')
    if (!statusRes.enabled && !statusRes.is_admin) {
      isVisible.value = false
      return
    }

    // Load coupons
    const couponsRes = await get('/api/coupons')
    coupons.value = couponsRes.coupons || []
    isVisible.value = coupons.value.length > 0 || statusRes.is_admin
  } catch (error) {
    console.error('Error loading exclusive coupons:', error)
    isVisible.value = false
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
