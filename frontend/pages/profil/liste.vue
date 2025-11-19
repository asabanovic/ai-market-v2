<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center gap-4 mb-2">
          <NuxtLink
            :to="viewingSingleList ? '/liste' : '/profil'"
            class="text-gray-600 hover:text-gray-900"
          >
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 19l-7-7 7-7" />
            </svg>
          </NuxtLink>
          <h1 class="text-3xl font-bold text-gray-900">
            {{ viewingSingleList ? 'Detalji Liste' : 'Prethodne Liste' }}
          </h1>
        </div>
        <p class="text-gray-600">
          {{ viewingSingleList ? 'Pregled detalja kupovne liste' : 'Pregled vaših prethodnih shopping lista' }}
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
        class="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg"
      >
        <p>{{ error }}</p>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="!lists || lists.length === 0"
        class="bg-white rounded-lg shadow-md p-12 text-center"
      >
        <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">
          Nema istorije
        </h3>
        <p class="text-gray-600 mb-6">
          Vaše prethodne shopping liste će se prikazati ovdje
        </p>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          <span>Počni kupovinu</span>
        </NuxtLink>
      </div>

      <!-- Shopping Lists History -->
      <div v-else class="space-y-6">
        <div
          v-for="list in lists"
          :key="list.id"
          class="bg-white rounded-lg shadow-md overflow-hidden"
        >
          <!-- List Header -->
          <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-3 mb-2">
                  <h3 class="text-lg font-semibold text-gray-900">
                    {{ getListName(list.created_at) }}
                  </h3>
                  <span
                    :class="[
                      'px-2 py-1 text-xs font-semibold rounded-full',
                      list.status === 'COMPLETED'
                        ? 'bg-green-100 text-green-800'
                        : list.status === 'SENT'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    ]"
                  >
                    {{ getStatusText(list.status) }}
                  </span>
                </div>
                <div class="flex items-center gap-4 text-sm text-gray-600">
                  <span>
                    <svg class="w-4 h-4 inline mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(list.created_at) }}
                  </span>
                  <span v-if="list.completed_at">
                    <svg class="w-4 h-4 inline mr-1" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    Završeno {{ formatDate(list.completed_at) }}
                  </span>
                  <span v-else-if="list.sent_at">
                    <svg class="w-4 h-4 inline mr-1" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                    Poslato {{ formatDate(list.sent_at) }}
                  </span>
                </div>
              </div>
              <div class="text-right">
                <p class="text-2xl font-bold text-gray-900">
                  {{ list.total_amount.toFixed(2) }} KM
                </p>
                <p
                  v-if="list.total_savings > 0"
                  class="text-sm text-green-600"
                >
                  Ušteda: {{ list.total_savings.toFixed(2) }} KM
                </p>
                <p class="text-xs text-gray-600 mt-1">
                  {{ list.item_count }} {{ list.item_count === 1 ? 'artikal' : 'artikala' }}
                </p>
              </div>
            </div>
          </div>

          <!-- List Items by Store -->
          <div class="divide-y divide-gray-200">
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
                  <h4 class="font-semibold text-gray-900">
                    {{ group.business.name }}
                  </h4>
                  <p class="text-sm text-gray-600">
                    {{ group.business.city }}
                  </p>
                </div>
                <div class="ml-auto text-right">
                  <p class="text-lg font-bold text-gray-900">
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
                    item.purchased ? 'bg-green-50' : 'bg-gray-50'
                  ]"
                >
                  <div class="flex items-center gap-3 flex-1">
                    <!-- Purchased Indicator -->
                    <Icon
                      :name="item.purchased ? 'mdi:check-circle' : 'mdi:circle-outline'"
                      :class="[
                        'w-5 h-5',
                        item.purchased ? 'text-green-600' : 'text-gray-300'
                      ]"
                    />

                    <!-- Product Name -->
                    <div class="flex-1">
                      <p
                        :class="[
                          'font-medium',
                          item.purchased
                            ? 'line-through text-gray-500'
                            : 'text-gray-900'
                        ]"
                      >
                        {{ item.product_name }}
                      </p>
                      <div class="flex items-center gap-2 text-sm text-gray-600">
                        <span>Količina: {{ item.qty }}x</span>
                        <span
                          v-if="item.discount_percent"
                          class="text-xs text-green-600 font-semibold"
                        >
                          -{{ item.discount_percent }}%
                        </span>
                      </div>
                    </div>

                    <!-- Item Total with Price Breakdown -->
                    <div class="text-right">
                      <div v-if="item.old_price && item.old_price > item.price" class="space-y-1">
                        <p class="text-sm text-gray-500 line-through">
                          {{ item.old_price.toFixed(2) }} KM
                        </p>
                        <p class="font-semibold text-green-600">
                          {{ item.price.toFixed(2) }} KM
                        </p>
                        <p class="text-xs text-gray-500">
                          Ukupno: {{ item.total.toFixed(2) }} KM
                        </p>
                      </div>
                      <div v-else>
                        <p class="font-semibold text-gray-900">
                          {{ item.price.toFixed(2) }} KM
                        </p>
                        <p class="text-xs text-gray-500">
                          Ukupno: {{ item.total.toFixed(2) }} KM
                        </p>
                      </div>
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
            class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <span class="px-4 py-2 text-gray-900">
            Stranica {{ pagination.page }} od {{ pagination.pages }}
          </span>

          <button
            :disabled="!pagination.has_next"
            @click="loadPage(pagination.page + 1)"
            class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5l7 7-7 7" />
            </svg>
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

const route = useRoute()
const lists = ref<ShoppingList[]>([])
const pagination = ref<Pagination | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

// Check if we're viewing a single list
const viewingSingleList = computed(() => !!route.query.list_id)

async function loadHistory(page: number = 1) {
  isLoading.value = true
  error.value = null

  try {
    // Build API URL with optional list_id parameter
    let url = '/shopping-lists/history'
    const params = new URLSearchParams()

    if (route.query.list_id) {
      params.append('list_id', route.query.list_id as string)
    } else {
      params.append('page', page.toString())
      params.append('per_page', '10')
    }

    const data = await $api.get(`${url}?${params.toString()}`)

    lists.value = data.lists
    // Hide pagination when viewing single list
    pagination.value = route.query.list_id ? null : data.pagination
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

function getListName(dateString: string): string {
  const date = new Date(dateString)
  const day = date.getDate()
  const month = new Intl.DateTimeFormat('bs-BA', { month: 'long' }).format(date)
  const year = date.getFullYear()
  const weekday = new Intl.DateTimeFormat('bs-BA', { weekday: 'long' }).format(date)

  // Format: "28 November 2025, Utorak"
  // Capitalize first letter of month and weekday
  const monthCapitalized = month.charAt(0).toUpperCase() + month.slice(1)
  const weekdayCapitalized = weekday.charAt(0).toUpperCase() + weekday.slice(1)

  return `${day} ${monthCapitalized} ${year}, ${weekdayCapitalized}`
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const day = date.getDate()
  const month = new Intl.DateTimeFormat('bs-BA', { month: 'long' }).format(date)
  const year = date.getFullYear()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')

  // Capitalize first letter of month
  const monthCapitalized = month.charAt(0).toUpperCase() + month.slice(1)

  // Format: "18 Novembar 2025 20:32"
  return `${day} ${monthCapitalized} ${year} ${hours}:${minutes}`
}

// Load history on mount
onMounted(() => {
  loadHistory()
})

// Watch for route changes to reload data when list_id changes
watch(() => route.query.list_id, () => {
  loadHistory()
})
</script>
