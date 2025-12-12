<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center gap-4">
          <NuxtLink to="/admin" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Povratne informacije korisnika</h1>
            <p class="mt-1 text-sm text-gray-600">Pregled svih povratnih informacija i prijedloga</p>
          </div>
        </div>
      </div>

      <!-- Stats Summary -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupno povratnih informacija</div>
          <div class="text-2xl font-bold text-gray-900">{{ total }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Prosječna ocjena</div>
          <div class="text-2xl font-bold text-yellow-600 flex items-center gap-1">
            {{ averageRating.toFixed(1) }}
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Od registrovanih korisnika</div>
          <div class="text-2xl font-bold text-blue-600">{{ registeredCount }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Od anonimnih korisnika</div>
          <div class="text-2xl font-bold text-gray-600">{{ anonymousCount }}</div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="feedbackList.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Nema povratnih informacija</h3>
        <p class="mt-1 text-sm text-gray-500">Korisnici još uvijek nisu ostavili povratne informacije.</p>
      </div>

      <!-- Feedback List -->
      <div v-else class="space-y-4">
        <div
          v-for="fb in feedbackList"
          :key="fb.id"
          class="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <!-- User Avatar -->
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                :class="fb.user_email ? 'bg-blue-600' : 'bg-gray-400'"
              >
                {{ fb.user_email ? fb.user_email[0].toUpperCase() : '?' }}
              </div>
              <div>
                <div class="font-medium text-gray-900">
                  {{ fb.user_email || 'Anonimni korisnik' }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ formatDateTime(fb.created_at) }}
                  <span v-if="fb.trigger_type" class="ml-2 px-1.5 py-0.5 bg-gray-100 rounded text-gray-600">
                    {{ fb.trigger_type }}
                  </span>
                  <span v-if="fb.device_type" class="ml-1 px-1.5 py-0.5 bg-gray-100 rounded text-gray-600">
                    {{ fb.device_type }}
                  </span>
                </div>
              </div>
            </div>
            <!-- Rating -->
            <div v-if="fb.rating" class="flex items-center gap-1">
              <template v-for="star in 5" :key="star">
                <svg
                  class="w-5 h-5"
                  :class="star <= fb.rating ? 'text-yellow-400' : 'text-gray-300'"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </template>
            </div>
          </div>

          <!-- Feedback Content -->
          <div class="space-y-3">
            <div v-if="fb.what_to_improve" class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs font-medium text-gray-500 mb-1">Šta biste poboljšali?</div>
              <p class="text-sm text-gray-900">{{ fb.what_to_improve }}</p>
            </div>
            <div v-if="fb.how_to_help" class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs font-medium text-gray-500 mb-1">Kako možemo pomoći?</div>
              <p class="text-sm text-gray-900">{{ fb.how_to_help }}</p>
            </div>
            <div v-if="fb.what_would_make_you_use" class="bg-gray-50 rounded-lg p-3">
              <div class="text-xs font-medium text-gray-500 mb-1">Šta bi vas natjeralo da koristite app svaki put?</div>
              <p class="text-sm text-gray-900">{{ fb.what_would_make_you_use }}</p>
            </div>
            <div v-if="fb.comments" class="bg-blue-50 rounded-lg p-3">
              <div class="text-xs font-medium text-blue-600 mb-1">Dodatni komentari</div>
              <p class="text-sm text-gray-900">{{ fb.comments }}</p>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="pages > 1" class="flex items-center justify-center gap-2 mt-6">
          <button
            @click="loadPage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Prethodna
          </button>
          <span class="text-sm text-gray-700">
            Stranica {{ currentPage }} od {{ pages }}
          </span>
          <button
            @click="loadPage(currentPage + 1)"
            :disabled="currentPage === pages"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Sljedeća
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const { get } = useApi()

const isLoading = ref(true)
const feedbackList = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pages = ref(1)

// Computed stats
const averageRating = computed(() => {
  const rated = feedbackList.value.filter(f => f.rating)
  if (rated.length === 0) return 0
  return rated.reduce((sum, f) => sum + f.rating, 0) / rated.length
})

const registeredCount = computed(() => {
  return feedbackList.value.filter(f => f.user_email).length
})

const anonymousCount = computed(() => {
  return feedbackList.value.filter(f => !f.user_email).length
})

onMounted(async () => {
  await loadFeedback()
})

async function loadFeedback() {
  isLoading.value = true
  try {
    const data = await get(`/api/admin/feedback?page=${currentPage.value}&per_page=20`)
    feedbackList.value = data.feedback || []
    total.value = data.total || 0
    pages.value = data.pages || 1
  } catch (error) {
    console.error('Error loading feedback:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadPage(page: number) {
  if (page < 1 || page > pages.value) return
  currentPage.value = page
  await loadFeedback()
}

function formatDateTime(dateString: string) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

useSeoMeta({
  title: 'Povratne informacije - Admin - Popust.ba',
  description: 'Pregled povratnih informacija korisnika',
})
</script>
