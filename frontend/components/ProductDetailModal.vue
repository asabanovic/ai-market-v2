<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-start justify-center p-4"
      @click.self="closeModal"
    >
      <div class="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full my-8 animate-modal-in" @click.stop>
        <!-- Close Button -->
        <button
          @click="closeModal"
          class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors z-10"
        >
          <Icon name="mdi:close" class="w-8 h-8" />
        </button>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-8">
          <!-- Left Column - Product Info -->
          <div class="space-y-6">
            <!-- Product Image -->
            <div class="relative rounded-xl overflow-hidden bg-gray-100 h-64">
              <img
                v-if="product.image_path || product.product_image_url"
                :src="getImageUrl(product.image_path || product.product_image_url)"
                :alt="product.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="flex items-center justify-center h-full text-gray-400">
                <Icon name="mdi:image-off" class="w-16 h-16" />
              </div>

              <!-- Discount Badge -->
              <div
                v-if="discountPercentage > 0"
                class="absolute top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg text-lg font-bold shadow-lg"
              >
                -{{ discountPercentage }}%
              </div>
            </div>

            <!-- Product Title & Price -->
            <div>
              <h2 class="text-2xl font-bold text-gray-900 mb-4">{{ product.title }}</h2>
              <div class="flex items-baseline gap-3 mb-4">
                <span class="text-3xl font-bold text-green-600">
                  {{ formatPrice(product.discount_price || product.base_price) }} KM
                </span>
                <span
                  v-if="product.discount_price && product.base_price > product.discount_price"
                  class="text-xl text-gray-400 line-through"
                >
                  {{ formatPrice(product.base_price) }} KM
                </span>
              </div>

              <!-- Expiry Date -->
              <div v-if="product.expires" class="inline-block bg-yellow-100 text-yellow-700 px-4 py-2 rounded-lg text-sm font-medium">
                Važi do {{ formatBosnianDate(product.expires) }}
              </div>
            </div>

            <!-- Business Info -->
            <div class="bg-gray-50 rounded-xl p-4 space-y-3">
              <div class="flex items-center gap-3">
                <div v-if="product.business?.logo" class="w-12 h-12 rounded-lg overflow-hidden">
                  <img
                    :src="`${config.public.apiBase}/static/${product.business.logo}`"
                    :alt="product.business.name"
                    class="w-full h-full object-contain"
                  />
                </div>
                <div v-else class="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center text-white text-xl font-bold">
                  {{ product.business?.name?.[0] || '?' }}
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900">{{ product.business?.name || 'Nepoznato' }}</h3>
                  <p class="text-sm text-gray-600">{{ product.city || product.business?.city || 'BiH' }}</p>
                </div>
              </div>
            </div>

            <!-- Voting Section -->
            <div class="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6">
              <h3 class="font-semibold text-gray-900 mb-4 text-center">Ocijenite ovaj proizvod</h3>
              <div class="flex items-center justify-center gap-8">
                <!-- Thumbs Up -->
                <button
                  @click="handleVote('up')"
                  :disabled="isVoting"
                  :class="[
                    'flex flex-col items-center gap-2 p-4 rounded-xl transition-all',
                    userVote === 'up' ? 'bg-green-500 text-white scale-110' : 'bg-white text-gray-700 hover:bg-green-50 hover:scale-105'
                  ]"
                >
                  <Icon name="mdi:thumb-up" class="w-10 h-10" />
                  <span class="text-xl font-bold">{{ voteStats.upvotes }}</span>
                </button>

                <!-- Thumbs Down -->
                <button
                  @click="handleVote('down')"
                  :disabled="isVoting"
                  :class="[
                    'flex flex-col items-center gap-2 p-4 rounded-xl transition-all',
                    userVote === 'down' ? 'bg-red-500 text-white scale-110' : 'bg-white text-gray-700 hover:bg-red-50 hover:scale-105'
                  ]"
                >
                  <Icon name="mdi:thumb-down" class="w-10 h-10" />
                  <span class="text-xl font-bold">{{ voteStats.downvotes }}</span>
                </button>
              </div>
              <p v-if="!isAuthenticated" class="text-center text-sm text-gray-600 mt-4">
                <NuxtLink to="/registracija" class="text-purple-600 hover:underline font-medium">
                  Prijavite se
                </NuxtLink> da glasate i zaradite kredite!
              </p>
              <p v-else class="text-center text-sm text-green-600 mt-4">
                💰 +1 kredit za svaki glas!
              </p>
            </div>
          </div>

          <!-- Right Column - Comments Section -->
          <div class="flex flex-col h-full max-h-[600px]">
            <h3 class="text-xl font-bold text-gray-900 mb-4">Komentari</h3>

            <!-- Add Comment Form -->
            <div v-if="isAuthenticated" class="mb-6">
              <textarea
                v-model="newComment"
                :disabled="isSubmittingComment"
                placeholder="Ostavite komentar (min 20, max 1000 karaktera)..."
                rows="4"
                class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all resize-none"
                @input="validateComment"
              ></textarea>
              <div class="flex items-center justify-between mt-2">
                <span :class="['text-sm', commentValidation.isValid ? 'text-gray-500' : 'text-red-500']">
                  {{ newComment.length }} / 1000 karaktera
                  <span v-if="newComment.length > 0 && newComment.length < 20" class="ml-2 text-red-500">
                    (min 20)
                  </span>
                </span>
                <button
                  @click="submitComment"
                  :disabled="!commentValidation.isValid || isSubmittingComment"
                  class="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <span v-if="!isSubmittingComment">Objavi (+2 kredita 💰)</span>
                  <span v-else>Objavljivanje...</span>
                </button>
              </div>
            </div>
            <div v-else class="mb-6 p-4 bg-purple-50 rounded-xl text-center">
              <p class="text-gray-700 mb-2">Prijavite se da ostavite komentar i zaradite 2 kredita!</p>
              <NuxtLink to="/registracija" class="text-purple-600 hover:underline font-medium">
                Registrujte se besplatno
              </NuxtLink>
            </div>

            <!-- Comments List -->
            <div class="flex-1 overflow-y-auto space-y-4 pr-2">
              <div v-if="loadingComments" class="text-center py-8">
                <Icon name="mdi:loading" class="w-8 h-8 animate-spin text-purple-600 mx-auto" />
                <p class="text-gray-600 mt-2">Učitavanje komentara...</p>
              </div>

              <div v-else-if="comments.length === 0" class="text-center py-12">
                <Icon name="mdi:comment-off-outline" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p class="text-gray-500">Budite prvi koji će ostaviti komentar!</p>
              </div>

              <div
                v-else
                v-for="comment in comments"
                :key="comment.id"
                class="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors"
              >
                <div class="flex items-start gap-3">
                  <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                    {{ comment.user.first_name?.[0] || '?' }}
                  </div>
                  <div class="flex-1">
                    <div class="flex items-baseline gap-2 mb-2">
                      <span class="font-semibold text-gray-900">
                        {{ comment.user.first_name }} {{ comment.user.last_name }}
                      </span>
                      <span class="text-xs text-gray-500">
                        {{ formatCommentDate(comment.created_at) }}
                      </span>
                    </div>
                    <p class="text-gray-700 whitespace-pre-wrap">{{ comment.comment_text }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  show: boolean
  product: any
}>()

const emit = defineEmits<{
  close: []
}>()

const config = useRuntimeConfig()
const { post } = useApi()
const { isAuthenticated, user, refreshUser } = useAuth()
const { triggerCreditAnimation } = useCreditAnimation()

// State
const comments = ref<any[]>([])
const loadingComments = ref(false)
const voteStats = ref({ upvotes: 0, downvotes: 0 })
const userVote = ref<string | null>(null)
const isVoting = ref(false)

const newComment = ref('')
const isSubmittingComment = ref(false)
const commentValidation = ref({ isValid: false, message: '' })

// Computed
const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > props.product.discount_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
})

// Methods
const closeModal = () => {
  emit('close')
}

const getImageUrl = (path: string) => {
  if (path.startsWith('http')) return path
  return `${config.public.apiBase}/static/${path}`
}

const formatPrice = (price: number) => {
  return price?.toFixed(2) || '0.00'
}

const formatBosnianDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const formatCommentDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Upravo sada'
  if (minutes < 60) return `Prije ${minutes} min`
  if (hours < 24) return `Prije ${hours}h`
  if (days < 7) return `Prije ${days} dana`

  return date.toLocaleDateString('bs-BA', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const validateComment = () => {
  const length = newComment.value.trim().length
  commentValidation.value.isValid = length >= 20 && length <= 1000

  if (length === 0) {
    commentValidation.value.message = ''
  } else if (length < 20) {
    commentValidation.value.message = `Potrebno još ${20 - length} karaktera`
  } else if (length > 1000) {
    commentValidation.value.message = `Previše karaktera (${length - 1000} preko limita)`
  } else {
    commentValidation.value.message = 'Komentar je validan'
  }
}

const loadComments = async () => {
  loadingComments.value = true
  try {
    const response = await fetch(`${config.public.apiBase}/api/products/${props.product.id}/comments`)
    const data = await response.json()
    if (data.success) {
      comments.value = data.comments
    }
  } catch (error) {
    console.error('Error loading comments:', error)
  } finally {
    loadingComments.value = false
  }
}

const loadVotes = async () => {
  try {
    const response = await fetch(`${config.public.apiBase}/api/products/${props.product.id}/votes`)
    const data = await response.json()
    if (data.success) {
      voteStats.value = {
        upvotes: data.upvotes,
        downvotes: data.downvotes
      }
      userVote.value = data.user_vote
    }
  } catch (error) {
    console.error('Error loading votes:', error)
  }
}

const handleVote = async (voteType: 'up' | 'down') => {
  if (!isAuthenticated.value) {
    // Redirect to login
    navigateTo('/registracija')
    return
  }

  isVoting.value = true
  try {
    const response = await post(`/products/${props.product.id}/vote`, { vote_type: voteType })

    if (response.success) {
      // Update vote stats
      voteStats.value = response.vote_stats

      // Update user vote
      if (response.message === 'Vote removed') {
        userVote.value = null
      } else {
        userVote.value = voteType
      }

      // Trigger credit animation if credits were earned
      if (response.credits_earned > 0) {
        triggerCreditAnimation(response.credits_earned)
        // Refresh user data to update credit count
        await refreshUser()
      }
    }
  } catch (error: any) {
    console.error('Error voting:', error)
  } finally {
    isVoting.value = false
  }
}

const submitComment = async () => {
  if (!commentValidation.value.isValid) return

  isSubmittingComment.value = true
  try {
    const response = await post(`/products/${props.product.id}/comments`, {
      comment_text: newComment.value.trim()
    })

    if (response.success) {
      // Add new comment to the top of the list
      comments.value.unshift(response.comment)

      // Clear the textarea
      newComment.value = ''
      commentValidation.value = { isValid: false, message: '' }

      // Trigger credit animation
      triggerCreditAnimation(response.credits_earned)

      // Refresh user data to update credit count
      await refreshUser()
    }
  } catch (error: any) {
    console.error('Error submitting comment:', error)
  } finally {
    isSubmittingComment.value = false
  }
}

// Watch for modal opening to load data
watch(() => props.show, (newValue) => {
  if (newValue) {
    loadComments()
    loadVotes()
  }
})
</script>

<style scoped>
@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-modal-in {
  animation: modal-in 0.3s ease-out;
}

/* Custom scrollbar for comments */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #9333ea;
  border-radius: 10px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #7e22ce;
}
</style>
