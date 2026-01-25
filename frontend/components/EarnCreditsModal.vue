<template>
  <div class="fixed inset-0 z-[100] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-gray-900/75 transition-opacity" @click="$emit('close')"></div>

      <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

      <!-- Modal -->
      <div class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-xl sm:w-full max-h-[90vh] flex flex-col">
        <!-- Header -->
        <div class="bg-gradient-to-r from-purple-500 to-indigo-500 p-6 text-white sticky top-0 z-10">
          <button
            @click="$emit('close')"
            class="absolute top-4 right-4 text-white/80 hover:text-white"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
          <h2 class="text-xl font-bold mb-2">Zaradi kredite brzo!</h2>
          <p class="text-purple-100">Lajkaj ili komentiraj proizvode da zaradiš kredite</p>
        </div>

        <!-- Progress Bar -->
        <div class="px-6 py-4 bg-gray-50 border-b sticky top-[104px] z-10">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700">
              Tvoji krediti: <span class="text-purple-600 font-bold">{{ earnedCredits }}</span>
            </span>
            <span class="text-sm text-gray-500">
              Potrebno: {{ requiredCredits + currentCredits }}
            </span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all duration-500 ease-out"
              :style="{ width: `${progressPercent}%` }"
            ></div>
          </div>
          <div v-if="earnedCredits >= requiredCredits + currentCredits" class="mt-2 text-center">
            <span class="text-green-600 font-medium">Imaš dovoljno kredita!</span>
          </div>
        </div>

        <!-- Products List -->
        <div class="flex-1 overflow-y-auto p-6">
          <div v-if="isLoading" class="text-center py-8">
            <div class="inline-flex items-center text-purple-600">
              <svg class="animate-spin h-6 w-6" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span class="ml-2">Učitavanje proizvoda...</span>
            </div>
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="product in products"
              :key="product.id"
              class="bg-white border rounded-xl p-4 hover:border-purple-200 transition-colors"
            >
              <div class="flex gap-4">
                <!-- Product Image -->
                <div class="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    v-if="product.image_url"
                    :src="product.image_url"
                    :alt="product.title"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                </div>

                <!-- Product Info -->
                <div class="flex-1 min-w-0">
                  <h4 class="font-medium text-gray-900 text-sm line-clamp-2">{{ product.title }}</h4>
                  <div class="flex items-center gap-2 mt-1">
                    <span v-if="product.discount_price" class="text-green-600 font-medium">{{ product.discount_price.toFixed(2) }} KM</span>
                    <span v-else class="text-gray-900">{{ product.base_price.toFixed(2) }} KM</span>
                    <span class="text-xs text-gray-500">{{ product.business?.name }}</span>
                  </div>

                  <!-- Actions -->
                  <div class="flex items-center gap-3 mt-3">
                    <!-- Like Button -->
                    <button
                      @click="voteProduct(product, 'up')"
                      :disabled="product.voted"
                      :class="[
                        'flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                        product.voted
                          ? 'bg-green-100 text-green-700'
                          : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                      ]"
                    >
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                      </svg>
                      <span v-if="product.voted">Lajkano!</span>
                      <span v-else>Lajk (+2)</span>
                    </button>

                    <!-- Comment Button -->
                    <button
                      v-if="!product.showComment && !product.commented"
                      @click="product.showComment = true"
                      class="flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                      </svg>
                      Komentar (+5)
                    </button>

                    <span v-if="product.commented" class="text-sm text-green-600 font-medium">
                      Komentarisano!
                    </span>
                  </div>

                  <!-- Comment Input -->
                  <div v-if="product.showComment && !product.commented" class="mt-3">
                    <textarea
                      v-model="product.commentText"
                      rows="2"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Napiši komentar (min 20 karaktera)..."
                    ></textarea>
                    <div class="flex items-center justify-between mt-2">
                      <span class="text-xs" :class="product.commentText?.length >= 20 ? 'text-green-600' : 'text-gray-400'">
                        {{ product.commentText?.length || 0 }}/20 min
                      </span>
                      <div class="flex gap-2">
                        <button
                          @click="product.showComment = false"
                          class="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                        >
                          Otkaži
                        </button>
                        <button
                          @click="commentProduct(product)"
                          :disabled="!product.commentText || product.commentText.length < 20"
                          class="px-3 py-1 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Pošalji
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 bg-gray-50 border-t sticky bottom-0">
          <button
            @click="handleClose"
            :class="[
              'w-full py-3 rounded-xl font-semibold transition-colors',
              earnedCredits >= requiredCredits + currentCredits
                ? 'bg-green-500 hover:bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            ]"
          >
            {{ earnedCredits >= requiredCredits + currentCredits ? 'Nastavi sa kupovinom' : 'Zatvori' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  requiredCredits: number
  currentCredits: number
}>()

const emit = defineEmits(['close', 'credits-earned'])

const { get, post } = useApi()

const isLoading = ref(true)
const products = ref<any[]>([])
const earnedCredits = ref(props.currentCredits)

const progressPercent = computed(() => {
  const target = props.requiredCredits + props.currentCredits
  return Math.min(100, (earnedCredits.value / target) * 100)
})

onMounted(async () => {
  await loadProducts()
})

async function loadProducts() {
  isLoading.value = true
  try {
    // Get random products from various categories for engagement
    const res = await get('/api/products/for-engagement?limit=20')
    products.value = (res.products || []).map((p: any) => ({
      ...p,
      voted: false,
      commented: false,
      showComment: false,
      commentText: ''
    }))
  } catch (error) {
    console.error('Error loading products:', error)
    // Fallback to empty
    products.value = []
  } finally {
    isLoading.value = false
  }
}

async function voteProduct(product: any, voteType: string) {
  if (product.voted) return

  try {
    const res = await post(`/api/products/${product.id}/vote`, { vote_type: voteType })
    product.voted = true

    if (res.credits_earned) {
      earnedCredits.value += res.credits_earned
      emit('credits-earned', earnedCredits.value)
    }
  } catch (error: any) {
    if (error.response?.status === 409) {
      // Already voted
      product.voted = true
    } else {
      console.error('Error voting:', error)
    }
  }
}

async function commentProduct(product: any) {
  if (product.commented || !product.commentText || product.commentText.length < 20) return

  try {
    const res = await post(`/api/products/${product.id}/comment`, {
      comment: product.commentText
    })
    product.commented = true
    product.showComment = false

    if (res.credits_earned) {
      earnedCredits.value += res.credits_earned
      emit('credits-earned', earnedCredits.value)
    }
  } catch (error: any) {
    console.error('Error commenting:', error)
    alert(error.response?.data?.error || 'Greška pri slanju komentara')
  }
}

function handleClose() {
  emit('close')
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
