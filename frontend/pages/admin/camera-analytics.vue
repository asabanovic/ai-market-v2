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
            <h1 class="text-2xl font-semibold text-gray-900">Camera Button Analytics</h1>
            <p class="mt-1 text-sm text-gray-600">Pratite kako korisnici koriste floating camera button</p>
          </div>
        </div>
      </div>

      <!-- Days Filter -->
      <div class="mb-6 flex items-center gap-4">
        <label class="text-sm text-gray-600">Period:</label>
        <select v-model="days" @change="fetchData" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option :value="7">Zadnjih 7 dana</option>
          <option :value="14">Zadnjih 14 dana</option>
          <option :value="30">Zadnjih 30 dana</option>
          <option :value="90">Zadnjih 90 dana</option>
        </select>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-purple-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <template v-else-if="data">
        <!-- Funnel Stats -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Funnel - Conversion Flow</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div
              v-for="(step, index) in funnelSteps"
              :key="step.key"
              class="text-center p-4 rounded-lg"
              :class="step.bgClass"
            >
              <div class="text-2xl mb-1">{{ step.icon }}</div>
              <div class="text-xs text-gray-500 mb-1">{{ step.label }}</div>
              <div class="text-2xl font-bold" :class="step.textClass">
                {{ data.funnel[step.key]?.total || 0 }}
              </div>
              <div class="text-xs text-gray-400">
                {{ getTotalPeople(step.key) }} osoba
              </div>
              <!-- Conversion arrow -->
              <div v-if="index > 0 && funnelSteps[index-1]" class="text-xs mt-2 text-gray-400">
                {{ getConversionRate(funnelSteps[index-1].key, step.key) }}% conv.
              </div>
            </div>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Ukupno interakcija</div>
            <div class="text-3xl font-bold text-gray-900">{{ data.summary.total_interactions }}</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Ulogovani korisnici</div>
            <div class="text-3xl font-bold text-purple-600">{{ data.summary.unique_logged_in_users }}</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Anonimne sesije</div>
            <div class="text-3xl font-bold text-gray-600">{{ data.summary.anonymous_sessions }}</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-500 mb-1">Uspješni uploadi</div>
            <div class="text-3xl font-bold text-green-600">{{ data.funnel.upload_complete?.total || 0 }}</div>
          </div>
        </div>

        <!-- Users Table -->
        <div class="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
          <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">Korisnici koji su interaktovali</h2>
          </div>

          <div v-if="data.users.length === 0" class="p-6 text-center text-gray-500">
            Nema korisnika za prikazati
          </div>

          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Korisnik</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Interakcije</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Akcije</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Zadnja aktivnost</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Slike</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="user in data.users" :key="user.user_id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <NuxtLink
                      v-if="user.user_id"
                      :to="`/admin/users/${user.user_id}`"
                      class="text-sm font-medium text-purple-600 hover:text-purple-800 hover:underline"
                    >
                      {{ user.name || 'N/A' }}
                    </NuxtLink>
                    <div v-else class="text-sm font-medium text-gray-900">{{ user.name || 'N/A' }}</div>
                    <div class="text-xs text-gray-500">{{ user.email }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-lg font-bold text-purple-600">{{ user.interaction_count }}</span>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex flex-wrap gap-1">
                      <span
                        v-for="action in user.actions"
                        :key="action"
                        class="px-2 py-1 text-xs rounded-full"
                        :class="getActionBadgeClass(action)"
                      >
                        {{ getActionLabel(action) }}
                      </span>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      class="px-2 py-1 text-xs rounded-full"
                      :class="user.completed_upload ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
                    >
                      {{ user.completed_upload ? 'Uploadovao' : 'Nije uploadovao' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(user.last_interaction) }}
                  </td>
                  <td class="px-6 py-4">
                    <div v-if="user.uploaded_images.length > 0" class="flex gap-2 cursor-pointer" @click="openGallery(user.uploaded_images)">
                      <div
                        v-for="img in user.uploaded_images.slice(0, 3)"
                        :key="img.id"
                        class="w-12 h-12 rounded-lg overflow-hidden border border-gray-200 hover:ring-2 hover:ring-purple-500"
                      >
                        <img
                          :src="getImageUrl(img.thumbnail_url || img.image_url)"
                          class="w-full h-full object-cover"
                          alt="Uploaded"
                        />
                      </div>
                      <span v-if="user.uploaded_images.length > 3" class="text-xs text-gray-500 self-center bg-gray-100 px-2 py-1 rounded-full hover:bg-purple-100 hover:text-purple-700">
                        +{{ user.uploaded_images.length - 3 }}
                      </span>
                    </div>
                    <span v-else class="text-xs text-gray-400">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="data.pagination.pages > 1" class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div class="text-sm text-gray-500">
              Stranica {{ data.pagination.page }} od {{ data.pagination.pages }}
            </div>
            <div class="flex gap-2">
              <button
                @click="goToPage(data.pagination.page - 1)"
                :disabled="data.pagination.page <= 1"
                class="px-3 py-1 border rounded text-sm disabled:opacity-50"
              >
                Prethodna
              </button>
              <button
                @click="goToPage(data.pagination.page + 1)"
                :disabled="data.pagination.page >= data.pagination.pages"
                class="px-3 py-1 border rounded text-sm disabled:opacity-50"
              >
                Sljedeća
              </button>
            </div>
          </div>
        </div>
      </template>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="text-red-600 mb-4">{{ error }}</div>
        <button @click="fetchData" class="px-4 py-2 bg-purple-600 text-white rounded-lg">
          Pokušaj ponovo
        </button>
      </div>
    </div>

    <!-- Image Gallery Modal -->
    <Teleport to="body">
      <div
        v-if="galleryImages.length > 0"
        class="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
        @click="closeGallery"
      >
        <div class="relative w-full h-full flex flex-col" @click.stop>
          <!-- Header -->
          <div class="flex-shrink-0 p-4 flex justify-between items-center text-white">
            <div>
              <div class="font-semibold">{{ currentGalleryImage?.extracted_name || 'Slika proizvoda' }}</div>
              <div class="text-sm text-gray-300">
                {{ currentGalleryImage?.status }}
                <span v-if="currentGalleryImage?.extracted_price">| {{ currentGalleryImage.extracted_price }} KM</span>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <span class="text-sm text-gray-300">{{ galleryIndex + 1 }} / {{ galleryImages.length }}</span>
              <button @click="closeGallery" class="text-gray-400 hover:text-white p-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Image Container -->
          <div class="flex-1 flex items-center justify-center relative px-16">
            <!-- Previous Button -->
            <button
              v-if="galleryImages.length > 1"
              @click.stop="prevImage"
              class="absolute left-4 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
            >
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>

            <!-- Main Image -->
            <img
              v-if="currentGalleryImage"
              :src="getImageUrl(currentGalleryImage.image_url)"
              class="max-w-full max-h-[75vh] object-contain rounded-lg"
              alt="Full image"
            />

            <!-- Next Button -->
            <button
              v-if="galleryImages.length > 1"
              @click.stop="nextImage"
              class="absolute right-4 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
            >
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <!-- Footer with metadata -->
          <div class="flex-shrink-0 p-4 text-sm text-gray-400">
            <div>Uploadovano: {{ formatDate(currentGalleryImage?.created_at) }}</div>
            <div v-if="currentGalleryImage?.processed_at">Obrađeno: {{ formatDate(currentGalleryImage.processed_at) }}</div>
          </div>

          <!-- Thumbnail Strip -->
          <div v-if="galleryImages.length > 1" class="flex-shrink-0 p-4 border-t border-white/10">
            <div class="flex gap-2 justify-center overflow-x-auto">
              <div
                v-for="(img, idx) in galleryImages"
                :key="img.id"
                @click.stop="galleryIndex = idx"
                class="w-16 h-16 rounded-lg overflow-hidden border-2 cursor-pointer flex-shrink-0 transition-all"
                :class="idx === galleryIndex ? 'border-purple-500 ring-2 ring-purple-500' : 'border-white/20 hover:border-white/50'"
              >
                <img
                  :src="getImageUrl(img.thumbnail_url || img.image_url)"
                  class="w-full h-full object-cover"
                  alt="Thumbnail"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'admin'
})

const config = useRuntimeConfig()
const { get } = useApi()

const days = ref(30)
const page = ref(1)
const isLoading = ref(true)
const error = ref<string | null>(null)
const data = ref<any>(null)

// Gallery state
const galleryImages = ref<any[]>([])
const galleryIndex = ref(0)
const currentGalleryImage = computed(() => galleryImages.value[galleryIndex.value] || null)

const funnelSteps = [
  { key: 'expand', label: 'Otvorio', icon: '👆', bgClass: 'bg-gray-100', textClass: 'text-gray-700' },
  { key: 'camera_click', label: 'Kamera', icon: '📷', bgClass: 'bg-blue-50', textClass: 'text-blue-700' },
  { key: 'gallery_click', label: 'Galerija', icon: '🖼️', bgClass: 'bg-purple-50', textClass: 'text-purple-700' },
  { key: 'upload_start', label: 'Preview', icon: '👁️', bgClass: 'bg-yellow-50', textClass: 'text-yellow-700' },
  { key: 'upload_complete', label: 'Upload OK', icon: '✅', bgClass: 'bg-green-50', textClass: 'text-green-700' },
  { key: 'upload_cancel', label: 'Odustao', icon: '❌', bgClass: 'bg-red-50', textClass: 'text-red-700' },
]

async function fetchData() {
  isLoading.value = true
  error.value = null

  try {
    const response = await get(`/api/admin/analytics/camera-button?days=${days.value}&page=${page.value}`)
    data.value = response
  } catch (e: any) {
    error.value = e.message || 'Greška pri učitavanju'
    console.error('Failed to fetch analytics:', e)
  } finally {
    isLoading.value = false
  }
}

function goToPage(newPage: number) {
  page.value = newPage
  fetchData()
}

function getTotalPeople(key: string): number {
  const funnel = data.value?.funnel[key]
  if (!funnel) return 0
  // Combine unique logged-in users and unique anonymous sessions
  return (funnel.unique_users || 0) + (funnel.unique_sessions || 0)
}

function getConversionRate(fromKey: string, toKey: string): string {
  const from = data.value?.funnel[fromKey]?.total || 0
  const to = data.value?.funnel[toKey]?.total || 0
  if (from === 0) return '0'
  return ((to / from) * 100).toFixed(0)
}

function getActionLabel(action: string): string {
  const labels: Record<string, string> = {
    'expand': 'Otvorio',
    'camera_click': 'Kamera',
    'gallery_click': 'Galerija',
    'upload_start': 'Preview',
    'upload_complete': 'Upload',
    'upload_cancel': 'Odustao'
  }
  return labels[action] || action
}

function getActionBadgeClass(action: string): string {
  const classes: Record<string, string> = {
    'expand': 'bg-gray-100 text-gray-700',
    'camera_click': 'bg-blue-100 text-blue-700',
    'gallery_click': 'bg-purple-100 text-purple-700',
    'upload_start': 'bg-yellow-100 text-yellow-700',
    'upload_complete': 'bg-green-100 text-green-700',
    'upload_cancel': 'bg-red-100 text-red-700'
  }
  return classes[action] || 'bg-gray-100 text-gray-700'
}

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  // Camera search images are stored in S3
  if (path.startsWith('popust/')) {
    return `https://aipijaca.s3.eu-central-1.amazonaws.com/${path}`
  }
  return `${config.public.apiBase}/static/${path}`
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('hr-HR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function openGallery(images: any[]) {
  galleryImages.value = images
  galleryIndex.value = 0
}

function closeGallery() {
  galleryImages.value = []
  galleryIndex.value = 0
}

function prevImage() {
  if (galleryIndex.value > 0) {
    galleryIndex.value--
  } else {
    galleryIndex.value = galleryImages.value.length - 1
  }
}

function nextImage() {
  if (galleryIndex.value < galleryImages.value.length - 1) {
    galleryIndex.value++
  } else {
    galleryIndex.value = 0
  }
}

// Keyboard navigation for gallery
function handleKeydown(e: KeyboardEvent) {
  if (galleryImages.value.length === 0) return

  if (e.key === 'Escape') {
    closeGallery()
  } else if (e.key === 'ArrowLeft') {
    prevImage()
  } else if (e.key === 'ArrowRight') {
    nextImage()
  }
}

onMounted(() => {
  fetchData()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
