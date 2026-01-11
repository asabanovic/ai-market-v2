<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <NuxtLink to="/admin" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </NuxtLink>
            <div>
              <h1 class="text-2xl font-semibold text-gray-900">Podrška - Razgovori</h1>
              <p class="mt-1 text-sm text-gray-600">Pregled svih razgovora sa korisnicima</p>
            </div>
          </div>
          <button
            @click="showNewMessageModal = true"
            class="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Nova poruka
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupno razgovora</div>
          <div class="text-2xl font-bold text-gray-900">{{ conversations.length }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Nepročitanih poruka</div>
          <div class="text-2xl font-bold text-red-600">{{ totalUnread }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupno poruka</div>
          <div class="text-2xl font-bold text-blue-600">{{ totalMessages }}</div>
        </div>
      </div>

      <!-- Loading -->
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
      <div v-else-if="conversations.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Nema razgovora</h3>
        <p class="mt-1 text-sm text-gray-500">Razgovori će se pojaviti kada počnete komunicirati sa korisnicima.</p>
      </div>

      <!-- Conversations List -->
      <div v-else class="space-y-4">
        <NuxtLink
          v-for="conv in conversations"
          :key="conv.user_id"
          :to="`/admin/support/${conv.user_id}`"
          class="block bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <!-- User Avatar -->
              <div class="w-12 h-12 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                {{ (conv.user_name || conv.user_email || '?')[0].toUpperCase() }}
              </div>
              <div>
                <div class="font-medium text-gray-900">
                  {{ conv.user_name || conv.user_email }}
                </div>
                <div class="text-sm text-gray-500">{{ conv.user_email }}</div>
                <div v-if="conv.last_message_preview" class="text-sm text-gray-600 mt-1 truncate max-w-md">
                  <span v-if="conv.last_message_sender === 'admin'" class="text-indigo-600 font-medium">Vi: </span>
                  {{ conv.last_message_preview }}
                </div>
              </div>
            </div>

            <div class="text-right">
              <div class="text-xs text-gray-500">{{ formatRelativeTime(conv.last_message_at) }}</div>
              <div class="flex items-center gap-2 mt-2 justify-end">
                <span class="text-xs text-gray-400">{{ conv.message_count }} poruka</span>
                <span
                  v-if="conv.unread_count > 0"
                  class="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full"
                >
                  {{ conv.unread_count }}
                </span>
              </div>
            </div>
          </div>
        </NuxtLink>
      </div>

      <!-- New Message Modal -->
      <div v-if="showNewMessageModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-lg w-full max-w-md shadow-xl">
          <div class="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900">Nova poruka</h2>
            <button @click="closeModal" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="p-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Pretraži korisnika po email-u</label>
            <div class="relative">
              <input
                v-model="searchQuery"
                @input="searchUsers"
                type="text"
                placeholder="Unesite email..."
                class="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400"
              />
              <div v-if="isSearching" class="absolute right-3 top-2.5">
                <svg class="animate-spin h-5 w-5 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            </div>

            <!-- Search Results -->
            <div v-if="searchResults.length > 0" class="mt-3 border border-gray-200 rounded-lg max-h-60 overflow-y-auto">
              <button
                v-for="user in searchResults"
                :key="user.id"
                @click="selectUser(user)"
                class="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
              >
                <div class="font-medium text-gray-900">{{ user.name }}</div>
                <div class="text-sm text-gray-500">{{ user.email }}</div>
              </button>
            </div>

            <!-- No results -->
            <div v-else-if="searchQuery.length >= 2 && !isSearching && searchResults.length === 0" class="mt-3 text-sm text-gray-500 text-center py-4">
              Nema rezultata za "{{ searchQuery }}"
            </div>

            <!-- Hint -->
            <p v-else-if="searchQuery.length < 2" class="mt-2 text-xs text-gray-500">
              Unesite najmanje 2 karaktera za pretragu
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const router = useRouter()
const { get } = useApi()

const isLoading = ref(true)
const conversations = ref<any[]>([])

// New message modal state
const showNewMessageModal = ref(false)
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const isSearching = ref(false)
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const totalUnread = computed(() => {
  return conversations.value.reduce((sum, c) => sum + (c.unread_count || 0), 0)
})

const totalMessages = computed(() => {
  return conversations.value.reduce((sum, c) => sum + (c.message_count || 0), 0)
})

onMounted(async () => {
  await loadConversations()
})

async function loadConversations() {
  isLoading.value = true
  try {
    const data = await get('/api/support/admin/conversations')
    conversations.value = data.conversations || []
  } catch (error) {
    console.error('Error loading conversations:', error)
  } finally {
    isLoading.value = false
  }
}

// Search users for new message
async function searchUsers() {
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }

  // Debounce search
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  searchTimeout = setTimeout(async () => {
    isSearching.value = true
    try {
      const data = await get(`/api/support/admin/search-users?q=${encodeURIComponent(searchQuery.value)}`)
      searchResults.value = data.users || []
    } catch (error) {
      console.error('Error searching users:', error)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }, 300)
}

function selectUser(user: any) {
  closeModal()
  router.push(`/admin/support/${user.id}`)
}

function closeModal() {
  showNewMessageModal.value = false
  searchQuery.value = ''
  searchResults.value = []
}

function formatRelativeTime(dateString: string) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'upravo sada'
  if (diffMins < 60) return `prije ${diffMins} min`
  if (diffHours < 24) return `prije ${diffHours}h`
  if (diffDays < 7) return `prije ${diffDays}d`

  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

useSeoMeta({
  title: 'Podrška - Admin - Popust.ba',
  description: 'Pregled razgovora sa korisnicima',
})
</script>
