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

              <!-- Report Button -->
              <div class="mt-3">
                <button
                  @click="openReportModal"
                  class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all group"
                  :class="hasReported
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-red-50 text-red-600 hover:bg-red-100 hover:text-red-700'"
                  :disabled="hasReported"
                >
                  <Icon name="mdi:flag-outline" class="w-4 h-4 group-hover:scale-110 transition-transform" />
                  <span v-if="hasReported">Prijavljeno</span>
                  <span v-else>Prijavi</span>
                  <div class="relative">
                    <Icon
                      name="mdi:help-circle-outline"
                      class="w-4 h-4 text-gray-400 hover:text-red-500 cursor-help transition-colors"
                    />
                    <div class="absolute bottom-full left-0 mb-2 w-48 p-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 pointer-events-none">
                      Prijavite ako je nesto pogresno (slika, cijena, istekla akcija)
                      <div class="absolute top-full left-3 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <!-- Business Info -->
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="flex items-center gap-3">
                <div v-if="businessLogo && !businessLogoError" class="w-12 h-12 rounded-lg overflow-hidden bg-white">
                  <img
                    :src="businessLogo"
                    :alt="product.business?.name"
                    class="w-full h-full object-contain"
                    @error="businessLogoError = true"
                  />
                </div>
                <div v-else class="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center text-white text-xl font-bold">
                  {{ product.business?.name?.[0] || '?' }}
                </div>
                <div class="flex-1">
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
                    userVote === 'up' ? 'bg-green-500 text-white scale-110' : 'text-gray-700 hover:bg-green-50 hover:scale-105'
                  ]"
                >
                  <svg class="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.08-.66-.23-.45-.52-.86-.88-1.22L14 2 7.59 8.41C7.21 8.79 7 9.3 7 9.83v7.84C7 18.95 8.05 20 9.34 20h8.11c.7 0 1.36-.37 1.72-.97l2.66-6.15z"/>
                  </svg>
                  <span class="text-xl font-bold">{{ voteStats.upvotes }}</span>
                </button>

                <!-- Thumbs Down -->
                <button
                  @click="handleVote('down')"
                  :disabled="isVoting"
                  :class="[
                    'flex flex-col items-center gap-2 p-4 rounded-xl transition-all',
                    userVote === 'down' ? 'bg-red-500 text-white scale-110' : 'text-gray-700 hover:bg-red-50 hover:scale-105'
                  ]"
                >
                  <svg class="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M22 4h-2c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h2V4zM2.17 11.12c-.11.25-.17.52-.17.8V13c0 1.1.9 2 2 2h5.5l-.92 4.65c-.05.22-.02.46.08.66.23.45.52.86.88 1.22L10 22l6.41-6.41c.38-.38.59-.89.59-1.42V6.34C17 5.05 15.95 4 14.66 4h-8.1c-.71 0-1.36.37-1.72.97l-2.67 6.15z"/>
                  </svg>
                  <span class="text-xl font-bold">{{ voteStats.downvotes }}</span>
                </button>
              </div>
              <p v-if="!isAuthenticated" class="text-center text-sm text-gray-600 mt-4">
                <NuxtLink to="/registracija" class="text-purple-600 hover:underline font-medium">
                  Prijavite se
                </NuxtLink> da glasate i zaradite kredite!
              </p>
              <p v-else class="text-center text-sm text-green-600 mt-4">
                💰 +2 kredita za svaki glas!
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
                placeholder="Ostavite komentar (min 10, max 1000 karaktera)..."
                rows="4"
                class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all resize-none text-gray-900"
                @input="validateComment"
              ></textarea>
              <div class="flex items-center justify-between mt-2">
                <span :class="['text-sm', commentValidation.isValid ? 'text-gray-500' : 'text-red-500']">
                  {{ newComment.length }} / 1000 karaktera
                  <span v-if="newComment.length > 0 && newComment.length < 10" class="ml-2 text-red-500">
                    (min 10)
                  </span>
                </span>
                <button
                  @click="submitComment"
                  :disabled="!commentValidation.isValid || isSubmittingComment"
                  class="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <span v-if="!isSubmittingComment">Objavi (+5 kredita 💰)</span>
                  <span v-else>Objavljivanje...</span>
                </button>
              </div>
            </div>
            <div v-else class="mb-6 p-4 bg-purple-50 rounded-xl text-center">
              <p class="text-gray-700 mb-2">Prijavite se da ostavite komentar i zaradite 5 kredita!</p>
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

    <!-- Report Modal -->
    <div
      v-if="showReportModal"
      class="fixed inset-0 bg-black bg-opacity-50 z-[60] flex items-center justify-center p-4"
      @click.self="closeReportModal"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-modal-in" @click.stop>
        <div class="text-center mb-6">
          <!-- Product image thumbnail -->
          <div class="w-20 h-20 rounded-xl overflow-hidden mx-auto mb-4 bg-gray-100">
            <img
              v-if="product.image_path || product.product_image_url"
              :src="getImageUrl(product.image_path || product.product_image_url)"
              :alt="product.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="flex items-center justify-center h-full text-gray-400">
              <Icon name="mdi:image-off" class="w-8 h-8" />
            </div>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Prijavi proizvod</h3>
          <p class="text-gray-600 text-sm">
            Prijavite ako je nesto pogresno sa ovim proizvodom (npr. pogresna slika, cijena, istekla akcija, itd.)
          </p>
        </div>

        <!-- Report Form -->
        <div v-if="!reportSubmitted">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Razlog prijave (opciono)
            </label>
            <textarea
              v-model="reportReason"
              placeholder="Opisite sta je pogresno..."
              rows="3"
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:ring-2 focus:ring-red-200 outline-none transition-all resize-none text-gray-900"
            ></textarea>
          </div>

          <div class="flex gap-3">
            <button
              @click="closeReportModal"
              class="flex-1 px-4 py-3 border-2 border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            >
              Odustani
            </button>
            <button
              @click="submitReport"
              :disabled="isSubmittingReport"
              class="flex-1 px-4 py-3 bg-red-500 text-white rounded-xl font-medium hover:bg-red-600 disabled:opacity-50 transition-colors"
            >
              <span v-if="!isSubmittingReport">Prijavi (+5 kredita)</span>
              <span v-else>Slanje...</span>
            </button>
          </div>
        </div>

        <!-- Success State -->
        <div v-else class="text-center">
          <h4 class="text-lg font-semibold text-gray-900 mb-2">Hvala na prijavi!</h4>
          <p class="text-gray-600 mb-4">Pregledacemo ovaj proizvod u najkracem roku.</p>
          <p class="text-green-600 font-medium mb-4">+5 kredita dodato na vas racun!</p>

          <!-- Optional: Add more details -->
          <div v-if="!reportReason && !feedbackSubmitted" class="bg-gray-50 rounded-xl p-4 mb-4">
            <p class="text-sm text-gray-600 mb-2">Zelite li dodati vise detalja?</p>
            <textarea
              v-model="additionalFeedback"
              placeholder="Dodatne informacije..."
              rows="2"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none text-gray-900 mb-2"
            ></textarea>
            <button
              @click="submitAdditionalFeedback"
              :disabled="!additionalFeedback.trim()"
              class="text-sm text-purple-600 hover:text-purple-700 font-medium disabled:opacity-50"
            >
              Posalji dodatne informacije
            </button>
          </div>

          <button
            @click="closeReportModal"
            class="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Zatvori
          </button>
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
const { get, post, put } = useApi()
const { isAuthenticated, user, refreshUser } = useAuth()
const { triggerCreditAnimation } = useCreditAnimation()
const { refreshCredits } = useSearchCredits()

// State
const comments = ref<any[]>([])
const loadingComments = ref(false)
const voteStats = ref({ upvotes: 0, downvotes: 0 })
const userVote = ref<string | null>(null)
const isVoting = ref(false)

const newComment = ref('')
const isSubmittingComment = ref(false)
const commentValidation = ref({ isValid: false, message: '' })
const businessLogoError = ref(false)

// Report state
const showReportModal = ref(false)
const reportReason = ref('')
const isSubmittingReport = ref(false)
const reportSubmitted = ref(false)
const hasReported = ref(false)
const additionalFeedback = ref('')
const feedbackSubmitted = ref(false)

// Computed
const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > props.product.discount_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
})

// Computed property for business logo - handles different API response formats
const businessLogo = computed(() => {
  const logo = props.product.business?.logo || props.product.business?.logo_path
  if (!logo) return null

  // If it's already a full URL, return as-is
  if (logo.startsWith('http://') || logo.startsWith('https://')) {
    return logo
  }

  // Otherwise, prepend the API base with /static/
  return `${config.public.apiBase}/static/${logo}`
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
  const days = ['Nedjelja', 'Ponedjeljak', 'Utorak', 'Srijeda', 'Četvrtak', 'Petak', 'Subota']
  const months = ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli', 'august', 'septembar', 'oktobar', 'novembar', 'decembar']

  const dayName = days[date.getDay()]
  const day = date.getDate()
  const month = months[date.getMonth()]
  const year = date.getFullYear()

  return `${dayName}, ${day}. ${month} ${year}.`
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
  commentValidation.value.isValid = length >= 10 && length <= 1000

  if (length === 0) {
    commentValidation.value.message = ''
  } else if (length < 10) {
    commentValidation.value.message = `Potrebno još ${10 - length} karaktera`
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
    const response = await post(`/api/products/${props.product.id}/vote`, { vote_type: voteType })

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
        // Refresh user data and credits in header
        await refreshUser()
        await refreshCredits()
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
    const response = await post(`/api/products/${props.product.id}/comments`, {
      comment_text: newComment.value.trim()
    })

    if (response.success) {
      // Add new comment to the top of the list
      comments.value.unshift(response.comment)

      // Clear the textarea
      newComment.value = ''
      commentValidation.value = { isValid: false, message: '' }

      // Trigger credit animation if credits were earned
      if (response.credits_earned > 0) {
        triggerCreditAnimation(response.credits_earned)
        // Refresh user data and credits in header
        await refreshUser()
        await refreshCredits()
      }
    }
  } catch (error: any) {
    console.error('Error submitting comment:', error)
  } finally {
    isSubmittingComment.value = false
  }
}

// Report methods
const checkReportStatus = async () => {
  const productId = props.product?.id
  if (!isAuthenticated.value || !productId) return

  const token = localStorage.getItem('token')
  if (!token) return

  try {
    const response = await fetch(`${config.public.apiBase}/api/products/${productId}/report/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success && data.has_reported) {
        hasReported.value = true
      }
    }
  } catch (error) {
    console.error('Error checking report status:', error)
  }
}

const openReportModal = () => {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
    return
  }
  if (hasReported.value) return
  showReportModal.value = true
}

const closeReportModal = () => {
  showReportModal.value = false
  // Reset state after close animation
  setTimeout(() => {
    if (!hasReported.value) {
      reportReason.value = ''
      reportSubmitted.value = false
    }
    additionalFeedback.value = ''
    feedbackSubmitted.value = false
  }, 300)
}

const submitReport = async () => {
  isSubmittingReport.value = true
  try {
    const response = await post(`/api/products/${props.product.id}/report`, {
      reason: reportReason.value.trim() || null
    })

    if (response.success) {
      reportSubmitted.value = true
      hasReported.value = true

      // Trigger credit animation
      if (response.credits_earned > 0) {
        triggerCreditAnimation(response.credits_earned)
        await refreshUser()
        await refreshCredits()
      }
    }
  } catch (error: any) {
    console.error('Error submitting report:', error)
    // Check if already reported - the error message contains this info
    if (error.message?.includes('Vec ste prijavili') || error.message?.includes('already')) {
      hasReported.value = true
      showReportModal.value = false
    }
  } finally {
    isSubmittingReport.value = false
  }
}

const submitAdditionalFeedback = async () => {
  if (!additionalFeedback.value.trim()) return

  try {
    const response = await put(`/api/products/${props.product.id}/report`, {
      reason: additionalFeedback.value.trim()
    })

    if (response.success) {
      feedbackSubmitted.value = true
    }
  } catch (error) {
    console.error('Error submitting additional feedback:', error)
  }
}

// Watch for modal opening to load data
watch(() => props.show, async (newValue) => {
  if (newValue) {
    businessLogoError.value = false
    // Reset report state for new product BEFORE checking
    showReportModal.value = false
    reportReason.value = ''
    reportSubmitted.value = false
    hasReported.value = false
    additionalFeedback.value = ''
    feedbackSubmitted.value = false

    // Load data in parallel
    loadComments()
    loadVotes()
    // Check if user already reported this product
    await checkReportStatus()
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
