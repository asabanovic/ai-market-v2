<template>
  <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-gray-900/75 transition-opacity" @click="$emit('close')"></div>

      <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

      <!-- Modal -->
      <div class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
        <!-- Header with Discount -->
        <div class="bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white relative">
          <button
            @click="$emit('close')"
            class="absolute top-4 right-4 text-white/80 hover:text-white"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
          <div class="text-6xl font-black mb-1">{{ coupon.discount_percent }}%</div>
          <div class="text-orange-100 font-medium text-lg">POPUST</div>
        </div>

        <!-- Content -->
        <div class="p-6">
          <!-- Business -->
          <div class="flex items-center gap-4 mb-6 pb-6 border-b">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center overflow-hidden">
              <img
                v-if="coupon.business.logo_path"
                :src="coupon.business.logo_path"
                :alt="coupon.business.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-2xl font-bold text-gray-400">
                {{ coupon.business.name.charAt(0) }}
              </span>
            </div>
            <div class="flex-1">
              <div class="font-semibold text-gray-900 text-lg">{{ coupon.business.name }}</div>
              <div class="flex items-center gap-2 text-sm text-gray-500">
                <span>{{ coupon.business.city }}</span>
                <span v-if="coupon.business.is_open" class="flex items-center text-green-600">
                  <span class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                  Otvoreno
                </span>
                <span v-else-if="coupon.business.is_open === false" class="text-gray-500">
                  Zatvoreno
                </span>
              </div>
              <a
                v-if="coupon.business.google_link"
                :href="coupon.business.google_link"
                target="_blank"
                class="text-sm text-orange-600 hover:text-orange-700 flex items-center gap-1 mt-1"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                Prikaži na mapi
              </a>
            </div>
          </div>

          <!-- Article -->
          <h2 class="text-2xl font-bold text-gray-900 mb-2">{{ coupon.article_name }}</h2>
          <p v-if="coupon.description" class="text-gray-600 mb-4">{{ coupon.description }}</p>

          <!-- Price -->
          <div class="flex items-baseline gap-3 mb-4">
            <span class="text-3xl font-bold text-green-600">{{ coupon.final_price.toFixed(2) }} KM</span>
            <span class="text-xl text-gray-400 line-through">{{ coupon.normal_price.toFixed(2) }} KM</span>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              Ušteda {{ coupon.savings.toFixed(2) }} KM
            </span>
          </div>

          <!-- Details -->
          <div class="grid grid-cols-2 gap-4 mb-6 text-sm">
            <div class="bg-gray-50 rounded-lg p-3">
              <div class="text-gray-500">Količina</div>
              <div class="font-medium text-gray-900">{{ coupon.quantity_description || 'Po komadu' }}</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-3">
              <div class="text-gray-500">Validnost</div>
              <div class="font-medium text-gray-900">{{ coupon.valid_days }} {{ coupon.valid_days === 1 ? 'dan' : 'dana' }}</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-3">
              <div class="text-gray-500">Preostalo</div>
              <div class="font-medium text-gray-900">{{ coupon.remaining_quantity }} od {{ coupon.total_quantity }}</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-3">
              <div class="text-gray-500">Cijena</div>
              <div class="font-medium text-orange-600">{{ coupon.credits_cost }} kredita</div>
            </div>
          </div>

          <!-- Reviews -->
          <div v-if="coupon.reviews && coupon.reviews.length > 0" class="mb-6">
            <h3 class="font-medium text-gray-900 mb-3">Recenzije</h3>
            <div class="space-y-3">
              <div v-for="(review, idx) in coupon.reviews.slice(0, 3)" :key="idx" class="bg-gray-50 rounded-lg p-3">
                <div class="flex items-center gap-2 mb-1">
                  <div class="flex">
                    <svg v-for="i in 5" :key="i" class="w-4 h-4" :class="i <= review.rating ? 'text-yellow-400' : 'text-gray-300'" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  </div>
                  <span class="text-sm text-gray-500">{{ review.user_name }}</span>
                </div>
                <p v-if="review.comment" class="text-sm text-gray-600">{{ review.comment }}</p>
              </div>
            </div>
          </div>

          <!-- Credit Balance -->
          <div class="bg-orange-50 rounded-lg p-4 mb-6">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm text-orange-700">Vaši krediti</div>
                <div class="text-2xl font-bold text-orange-600">{{ userCredits }}</div>
              </div>
              <div v-if="userCredits < coupon.credits_cost">
                <button
                  @click="$emit('earn-credits')"
                  class="text-sm text-orange-600 hover:text-orange-700 font-medium flex items-center gap-1"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  Zaradi još {{ coupon.credits_cost - userCredits }} kredita
                </button>
              </div>
            </div>
          </div>

          <!-- CTA -->
          <button
            @click="$emit('purchase', coupon)"
            :disabled="coupon.is_sold_out"
            :class="[
              'w-full py-4 rounded-xl font-semibold text-lg transition-colors flex items-center justify-center gap-2',
              coupon.is_sold_out
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : userCredits >= coupon.credits_cost
                  ? 'bg-orange-500 hover:bg-orange-600 text-white'
                  : 'bg-orange-100 text-orange-600 hover:bg-orange-200'
            ]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
            </svg>
            <span v-if="coupon.is_sold_out">Rasprodano</span>
            <span v-else-if="userCredits >= coupon.credits_cost">
              Kupi kupon za {{ coupon.credits_cost }} kredita
            </span>
            <span v-else>
              Nedovoljno kredita ({{ coupon.credits_cost - userCredits }} još)
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  coupon: any
  userCredits: number
}>()

defineEmits(['close', 'purchase', 'earn-credits'])
</script>
