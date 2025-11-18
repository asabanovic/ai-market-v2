<template>
  <div class="bg-gray-50 dark:bg-gray-900 min-h-screen py-8">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center gap-4 mb-2">
          <NuxtLink
            to="/profil"
            class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <Icon name="mdi:arrow-left" class="w-6 h-6" />
          </NuxtLink>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
            Istorija Lista
          </h1>
        </div>
        <p class="text-gray-600 dark:text-gray-400">
          Pregled vaših prethodnih shopping lista
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-primary-600">
          <LoadingSpinner class="mr-3" />
          <span class="text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-6 py-4 rounded-lg"
      >
        <p>{{ error }}</p>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="!lists || lists.length === 0"
        class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center"
      >
        <Icon name="mdi:history" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Nema istorije
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          Vaše prethodne shopping liste će se prikazati ovdje
        </p>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Icon name="mdi:cart" class="w-5 h-5" />
          <span>Počni kupovinu</span>
        </NuxtLink>
      </div>

      <!-- Shopping Lists History -->
      <div v-else class="space-y-6">
        <div
          v-for="list in lists"
          :key="list.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden"
        >
          <!-- List Header -->
          <div class="bg-gray-50 dark:bg-gray-700 px-6 py-4 border-b dark:border-gray-600">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-3 mb-2">
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    Lista #{{ list.id }}
                  </h3>
                  <span
                    :class="[
                      'px-2 py-1 text-xs font-semibold rounded-full',
                      list.status === 'COMPLETED'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        : list.status === 'SENT'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-300'
                    ]"
                  >
                    {{ getStatusText(list.status) }}
                  </span>
                </div>
                <div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>
                    <Icon name="mdi:calendar" class="w-4 h-4 inline mr-1" />
                    {{ formatDate(list.created_at) }}
                  </span>
                  <span v-if="list.completed_at">
                    <Icon name="mdi:check-circle" class="w-4 h-4 inline mr-1" />
                    Završeno {{ formatDate(list.completed_at) }}
                  </span>
                  <span v-else-if="list.sent_at">
                    <Icon name="mdi:send" class="w-4 h-4 inline mr-1" />
                    Poslato {{ formatDate(list.sent_at) }}
                  </span>
                </div>
              </div>
              <div class="text-right">
                <p class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ list.total_amount.toFixed(2) }} KM
                </p>
                <p
                  v-if="list.total_savings > 0"
                  class="text-sm text-green-600 dark:text-green-400"
                >
                  Ušteda: {{ list.total_savings.toFixed(2) }} KM
                </p>
                <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {{ list.item_count }} {{ list.item_count === 1 ? 'artikal' : 'artikala' }}
                </p>
              </div>
            </div>
          </div>

          <!-- List Items by Store -->
          <div class="divide-y dark:divide-gray-600">
            <div
              v-for="group in list.groups"
              :key="group.business.id"
              class="p-6"
            >
              <!-- Store Header -->
              <div class="flex items-center gap-3 mb-4">
                <img
                  v-if="group.business.logo"
                  :src="group.business.logo"
                  :alt="group.business.name"
                  class="w-8 h-8 object-contain rounded"
                />
                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white">
                    {{ group.business.name }}
                  </h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    {{ group.business.city }}
                  </p>
                </div>
                <div class="ml-auto text-right">
                  <p class="text-lg font-bold text-gray-900 dark:text-white">
                    {{ group.subtotal.toFixed(2) }} KM
                  </p>
                </div>
              </div>

              <!-- Store Items -->
              <div class="space-y-2">
                <div
                  v-for="item in group.items"
                  :key="item.id"
                  :class="[
                    'flex items-center justify-between p-3 rounded-lg',
                    item.purchased ? 'bg-green-50 dark:bg-green-900/10' : 'bg-gray-50 dark:bg-gray-700'
                  ]"
                >
                  <div class="flex items-center gap-3 flex-1">
                    <!-- Purchased Indicator -->
                    <Icon
                      :name="item.purchased ? 'mdi:check-circle' : 'mdi:circle-outline'"
                      :class="[
                        'w-5 h-5',
                        item.purchased ? 'text-green-600 dark:text-green-400' : 'text-gray-300 dark:text-gray-600'
                      ]"
                    />

                    <!-- Product Name -->
                    <div class="flex-1">
                      <p
                        :class="[
                          'font-medium',
                          item.purchased
                            ? 'line-through text-gray-500 dark:text-gray-400'
                            : 'text-gray-900 dark:text-white'
                        ]"
                      >
                        {{ item.product_name }}
                      </p>
                      <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span>{{ item.qty }}x {{ item.price.toFixed(2) }} KM</span>
                        <span
                          v-if="item.old_price && item.old_price > item.price"
                          class="line-through text-xs"
                        >
                          {{ item.old_price.toFixed(2) }} KM
                        </span>
                        <span
                          v-if="item.discount_percent"
                          class="text-xs text-green-600 dark:text-green-400"
                        >
                          -{{ item.discount_percent }}%
                        </span>
                      </div>
                    </div>

                    <!-- Item Total -->
                    <div class="text-right">
                      <p class="font-semibold text-gray-900 dark:text-white">
                        {{ item.total.toFixed(2) }} KM
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div
          v-if="pagination && pagination.pages > 1"
          class="flex items-center justify-center gap-2 mt-8"
        >
          <button
            :disabled="!pagination.has_prev"
            @click="loadPage(pagination.page - 1)"
            class="px-4 py-2 border dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Icon name="mdi:chevron-left" class="w-5 h-5" />
          </button>

          <span class="px-4 py-2 text-gray-900 dark:text-white">
            Stranica {{ pagination.page }} od {{ pagination.pages }}
          </span>

          <button
            :disabled="!pagination.has_next"
            @click="loadPage(pagination.page + 1)"
            class="px-4 py-2 border dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Icon name="mdi:chevron-right" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { $api } = useNuxtApp()

interface ShoppingListItem {
  id: number
  product_id: number
  product_name: string
  qty: number
  price: number
  old_price?: number
  discount_percent?: number
  total: number
  purchased: boolean
  purchased_at: string | null
}

interface ShoppingListGroup {
  business: {
    id: number
    name: string
    logo?: string
    city: string
  }
  items: ShoppingListItem[]
  subtotal: number
}

interface ShoppingList {
  id: number
  status: string
  created_at: string
  expires_at?: string
  sent_at?: string
  completed_at?: string
  item_count: number
  total_amount: number
  total_savings: number
  groups: ShoppingListGroup[]
}

interface Pagination {
  page: number
  per_page: number
  total: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

const lists = ref<ShoppingList[]>([])
const pagination = ref<Pagination | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

async function loadHistory(page: number = 1) {
  isLoading.value = true
  error.value = null

  try {
    const data = await $api.get(`/shopping-lists/history?page=${page}&per_page=10`)
    lists.value = data.lists
    pagination.value = data.pagination
  } catch (err: any) {
    console.error('Failed to load shopping history:', err)
    error.value = err.message || 'Greška pri učitavanju istorije'
  } finally {
    isLoading.value = false
  }
}

async function loadPage(page: number) {
  await loadHistory(page)
  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    COMPLETED: 'Završeno',
    SENT: 'Poslato',
    EXPIRED: 'Isteklo',
    CANCELLED: 'Otkazano'
  }
  return statusMap[status] || status
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('bs-BA', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

// Load history on mount
onMounted(() => {
  loadHistory()
})
</script>
