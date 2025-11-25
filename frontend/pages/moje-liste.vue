<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Moje Liste</h1>
        <p class="mt-2 text-gray-600 dark:text-gray-400">
          Pregled svih vaših prethodnih lista za kupovinu
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="lists.length === 0" class="text-center py-12">
        <svg class="mx-auto h-24 w-24 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Nemate prethodnih lista</h3>
        <p class="mt-2 text-gray-600 dark:text-gray-400">
          Vaše prethodne liste će biti prikazane ovdje nakon što isteknu ili ih pošaljete.
        </p>
        <NuxtLink
          to="/"
          class="mt-6 inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          Pretraži proizvode
        </NuxtLink>
      </div>

      <!-- Lists Grid -->
      <div v-else class="space-y-6">
        <div
          v-for="list in lists"
          :key="list.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden"
        >
          <!-- List Header -->
          <div class="bg-gray-50 dark:bg-gray-700 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
            <div class="flex items-center justify-between">
              <div>
                <div class="flex items-center gap-3">
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    Lista #{{ list.id }}
                  </h3>
                  <span
                    :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      list.status === 'SENT'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                    ]"
                  >
                    {{ list.status === 'SENT' ? 'Poslano' : 'Isteklo' }}
                  </span>
                </div>
                <div class="mt-1 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(list.created_at) }}
                  </span>
                  <span v-if="list.sent_at" class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Poslano: {{ formatDate(list.sent_at) }}
                  </span>
                  <span class="flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                    </svg>
                    {{ list.item_count }} {{ list.item_count === 1 ? 'proizvod' : 'proizvoda' }}
                  </span>
                </div>
              </div>
              <div class="text-right">
                <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {{ list.total_amount.toFixed(2) }} KM
                </div>
                <div v-if="list.total_savings > 0" class="text-sm text-green-600 dark:text-green-400">
                  Ušteda: {{ list.total_savings.toFixed(2) }} KM
                </div>
              </div>
            </div>
          </div>

          <!-- List Items by Store -->
          <div class="p-6 space-y-6">
            <div
              v-for="(group, index) in list.groups"
              :key="index"
              class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              <!-- Store Header -->
              <div class="bg-gray-50 dark:bg-gray-700 px-4 py-3 flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <img
                    v-if="group.business.logo"
                    :src="getLogoUrl(group.business.logo)"
                    :alt="group.business.name"
                    class="w-8 h-8 object-contain"
                  />
                  <div>
                    <h4 class="font-semibold text-gray-900 dark:text-white">
                      {{ group.business.name }}
                    </h4>
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                      {{ group.business.city }}
                    </p>
                  </div>
                </div>
                <div class="text-right">
                  <span class="text-lg font-bold text-gray-900 dark:text-white">
                    {{ group.subtotal.toFixed(2) }} KM
                  </span>
                </div>
              </div>

              <!-- Store Items -->
              <div class="divide-y divide-gray-200 dark:divide-gray-700">
                <div
                  v-for="item in group.items"
                  :key="item.id"
                  class="px-4 py-3 flex items-center justify-between"
                >
                  <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ item.product_name }}
                    </p>
                    <div class="mt-1 flex items-center gap-3 text-xs text-gray-600 dark:text-gray-400">
                      <span>Količina: {{ item.qty }}</span>
                      <span>{{ item.price.toFixed(2) }} KM</span>
                      <span v-if="item.discount_percent" class="text-red-600 dark:text-red-400">
                        -{{ item.discount_percent }}%
                      </span>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-semibold text-gray-900 dark:text-white">
                      {{ item.total.toFixed(2) }} KM
                    </div>
                    <div v-if="item.old_price && item.old_price > item.price" class="text-xs text-gray-500 dark:text-gray-400 line-through">
                      {{ (item.old_price * item.qty).toFixed(2) }} KM
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="pagination.pages > 1" class="flex items-center justify-center gap-2 mt-8">
          <button
            @click="loadPage(pagination.page - 1)"
            :disabled="!pagination.has_prev"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            Prethodna
          </button>
          <span class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
            Stranica {{ pagination.page }} od {{ pagination.pages }}
          </span>
          <button
            @click="loadPage(pagination.page + 1)"
            :disabled="!pagination.has_next"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
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
  middleware: ['auth']
})

const { get } = useApi()
const toast = useToast()
const config = useRuntimeConfig()

function getLogoUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  // Add /static/ prefix if not already present
  const staticPath = cleanPath.startsWith('static/') ? cleanPath : `static/${cleanPath}`
  return `${config.public.apiBase}/${staticPath}`
}

const isLoading = ref(true)
const lists = ref<any[]>([])
const pagination = ref({
  page: 1,
  per_page: 20,
  total: 0,
  pages: 0,
  has_next: false,
  has_prev: false
})

onMounted(async () => {
  await loadLists()
})

async function loadLists(page = 1) {
  isLoading.value = true
  try {
    const data = await get(`/api/shopping-lists/history?page=${page}&per_page=20`)
    lists.value = data.lists
    pagination.value = data.pagination
  } catch (error) {
    console.error('Error loading shopping history:', error)
    toast.add({
      title: 'Greška',
      description: 'Nije moguće učitati prethodne liste',
      color: 'red'
    })
  } finally {
    isLoading.value = false
  }
}

async function loadPage(page: number) {
  if (page < 1 || page > pagination.value.pages) return
  await loadLists(page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

useSeoMeta({
  title: 'Moje Liste - Popust.ba',
  description: 'Pregled svih vaših prethodnih lista za kupovinu'
})
</script>
