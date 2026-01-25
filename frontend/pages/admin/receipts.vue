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
              <h1 class="text-2xl font-semibold text-gray-900">Uploadani racuni</h1>
              <p class="mt-1 text-sm text-gray-600">Pregled svih korisnickih racuna i OCR ekstrakcije</p>
            </div>
          </div>
          <button
            @click="loadData"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Osvjezi
          </button>
        </div>
      </div>

      <!-- Stats Summary -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupno</div>
          <div class="text-2xl font-bold text-gray-900">{{ stats.total_receipts }}</div>
        </div>
        <div class="bg-white rounded-lg border border-green-200 p-4 bg-green-50">
          <div class="text-sm text-green-700">Uspjesno</div>
          <div class="text-2xl font-bold text-green-600">{{ stats.by_status?.completed || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-yellow-200 p-4 bg-yellow-50">
          <div class="text-sm text-yellow-700">Na cekanju</div>
          <div class="text-2xl font-bold text-yellow-600">{{ stats.by_status?.pending || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-red-200 p-4 bg-red-50">
          <div class="text-sm text-red-700">Greska</div>
          <div class="text-2xl font-bold text-red-600">{{ stats.by_status?.failed || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-blue-200 p-4 bg-blue-50">
          <div class="text-sm text-blue-700">Korisnika</div>
          <div class="text-2xl font-bold text-blue-600">{{ stats.users_with_receipts || 0 }}</div>
        </div>
      </div>

      <!-- Additional Stats -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupno stavki</div>
          <div class="text-xl font-bold text-gray-900">{{ stats.total_items || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupan iznos</div>
          <div class="text-xl font-bold text-gray-900">{{ formatPrice(stats.total_amount || 0) }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Zadnjih 7 dana</div>
          <div class="text-xl font-bold text-gray-900">{{ stats.recent_uploads_7d || 0 }}</div>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-4 mb-6">
        <!-- Status Filter -->
        <div class="flex gap-2">
          <button
            @click="setFilter(null)"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              !statusFilter
                ? 'bg-indigo-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            ]"
          >
            Svi
          </button>
          <button
            @click="setFilter('completed')"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              statusFilter === 'completed'
                ? 'bg-green-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            ]"
          >
            Uspjesno
          </button>
          <button
            @click="setFilter('pending')"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              statusFilter === 'pending'
                ? 'bg-yellow-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            ]"
          >
            Na cekanju
          </button>
          <button
            @click="setFilter('failed')"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              statusFilter === 'failed'
                ? 'bg-red-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            ]"
          >
            Greska
          </button>
        </div>

        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Pretrazi po email, radnja, JIB..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            @keyup.enter="loadReceipts"
          />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Ucitavanje...</span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="receipts.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">Nema racuna</h3>
        <p class="mt-2 text-gray-600">Trenutno nema uploadanih racuna.</p>
      </div>

      <!-- Table View -->
      <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slika</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Radnja</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Iznos</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stavki</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Datum</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="receipt in receipts" :key="receipt.id" class="hover:bg-gray-50">
                <!-- Image -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div
                    class="w-16 h-20 bg-gray-100 rounded-lg overflow-hidden cursor-pointer"
                    @click="openViewModal(receipt)"
                  >
                    <img
                      :src="receipt.receipt_image_url"
                      :alt="`Receipt ${receipt.id}`"
                      class="w-full h-full object-cover"
                      @error="handleImageError"
                    />
                  </div>
                </td>

                <!-- User -->
                <td class="px-4 py-3">
                  <div class="text-sm font-medium text-gray-900">{{ receipt.user?.email || 'N/A' }}</div>
                  <div class="text-xs text-gray-500">{{ receipt.user?.name || '' }}</div>
                </td>

                <!-- Store -->
                <td class="px-4 py-3">
                  <div class="text-sm text-gray-900">{{ receipt.store_name || '-' }}</div>
                  <div v-if="receipt.jib" class="text-xs text-gray-500">JIB: {{ receipt.jib }}</div>
                </td>

                <!-- Amount -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="text-sm font-semibold text-gray-900">
                    {{ receipt.total_amount ? formatPrice(receipt.total_amount) : '-' }}
                  </div>
                </td>

                <!-- Items Count -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ receipt.items?.length || 0 }}</div>
                </td>

                <!-- Status -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <span
                    :class="[
                      'px-2 py-1 text-xs font-medium rounded-full',
                      getStatusClass(receipt.processing_status)
                    ]"
                  >
                    {{ getStatusLabel(receipt.processing_status) }}
                  </span>
                </td>

                <!-- Date -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="text-sm text-gray-900">{{ formatDate(receipt.created_at) }}</div>
                  <div v-if="receipt.receipt_date" class="text-xs text-gray-500">
                    Racun: {{ formatDate(receipt.receipt_date) }}
                  </div>
                </td>

                <!-- Actions -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="flex gap-2">
                    <button
                      @click="openViewModal(receipt)"
                      class="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      title="Pregledaj"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                    <button
                      @click="deleteReceipt(receipt)"
                      class="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Obrisi"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-700">
              Prikazano {{ receipts.length }} od {{ totalReceipts }} racuna
            </div>
            <div class="flex gap-2">
              <button
                @click="currentPage--; loadReceipts()"
                :disabled="currentPage <= 1"
                class="px-3 py-1 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Prethodna
              </button>
              <span class="px-3 py-1 text-sm text-gray-700">
                {{ currentPage }} / {{ totalPages }}
              </span>
              <button
                @click="currentPage++; loadReceipts()"
                :disabled="currentPage >= totalPages"
                class="px-3 py-1 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Sljedeca
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- View Modal -->
      <Teleport to="body">
        <div
          v-if="showViewModal && selectedReceipt"
          class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          @click.self="closeViewModal"
        >
          <div class="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
            <!-- Modal Header -->
            <div class="flex items-center justify-between p-4 border-b">
              <h3 class="text-lg font-semibold text-gray-900">
                Racun #{{ selectedReceipt.id }}
              </h3>
              <button
                @click="closeViewModal"
                class="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Modal Content -->
            <div class="flex flex-col md:flex-row max-h-[calc(90vh-130px)] overflow-hidden">
              <!-- Image -->
              <div class="md:w-1/2 p-4 bg-gray-100 flex items-center justify-center">
                <img
                  :src="selectedReceipt.receipt_image_url"
                  :alt="`Receipt ${selectedReceipt.id}`"
                  class="max-w-full max-h-[60vh] object-contain"
                />
              </div>

              <!-- Details -->
              <div class="md:w-1/2 p-4 overflow-y-auto">
                <!-- User Info -->
                <div class="mb-4 p-3 bg-blue-50 rounded-lg">
                  <div class="text-sm font-medium text-blue-800">Korisnik</div>
                  <div class="text-blue-900">{{ selectedReceipt.user?.email }}</div>
                  <div v-if="selectedReceipt.user?.name" class="text-sm text-blue-700">{{ selectedReceipt.user.name }}</div>
                </div>

                <!-- Store Info -->
                <div class="mb-4">
                  <h4 class="text-sm font-medium text-gray-500 mb-2">Radnja</h4>
                  <div class="text-lg font-semibold text-gray-900">{{ selectedReceipt.store_name || '-' }}</div>
                  <div v-if="selectedReceipt.store_address" class="text-sm text-gray-600">{{ selectedReceipt.store_address }}</div>
                  <div class="flex flex-wrap gap-2 mt-2">
                    <span v-if="selectedReceipt.jib" class="px-2 py-1 bg-gray-100 rounded text-xs">JIB: {{ selectedReceipt.jib }}</span>
                    <span v-if="selectedReceipt.pib" class="px-2 py-1 bg-gray-100 rounded text-xs">PIB: {{ selectedReceipt.pib }}</span>
                    <span v-if="selectedReceipt.ibfm" class="px-2 py-1 bg-gray-100 rounded text-xs">IBFM: {{ selectedReceipt.ibfm }}</span>
                  </div>
                </div>

                <!-- Amount & Date -->
                <div class="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <h4 class="text-sm font-medium text-gray-500">Ukupno</h4>
                    <div class="text-2xl font-bold text-green-600">
                      {{ selectedReceipt.total_amount ? formatPrice(selectedReceipt.total_amount) : '-' }}
                    </div>
                  </div>
                  <div>
                    <h4 class="text-sm font-medium text-gray-500">Datum racuna</h4>
                    <div class="text-lg text-gray-900">
                      {{ selectedReceipt.receipt_date ? formatDate(selectedReceipt.receipt_date) : '-' }}
                    </div>
                  </div>
                </div>

                <!-- Status -->
                <div class="mb-4">
                  <h4 class="text-sm font-medium text-gray-500 mb-1">Status</h4>
                  <span
                    :class="[
                      'px-3 py-1 text-sm font-medium rounded-full',
                      getStatusClass(selectedReceipt.processing_status)
                    ]"
                  >
                    {{ getStatusLabel(selectedReceipt.processing_status) }}
                  </span>
                  <div v-if="selectedReceipt.processing_error" class="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
                    {{ selectedReceipt.processing_error }}
                  </div>
                </div>

                <!-- Items -->
                <div v-if="selectedReceipt.items?.length > 0">
                  <h4 class="text-sm font-medium text-gray-500 mb-2">Stavke ({{ selectedReceipt.items.length }})</h4>
                  <div class="space-y-2 max-h-60 overflow-y-auto">
                    <div
                      v-for="item in selectedReceipt.items"
                      :key="item.id"
                      class="p-2 bg-gray-50 rounded-lg text-sm"
                    >
                      <div class="flex justify-between items-start">
                        <div class="flex-1">
                          <div class="font-medium text-gray-900">{{ item.parsed_name || item.raw_name }}</div>
                          <div class="text-xs text-gray-500">
                            <span v-if="item.brand">{{ item.brand }} | </span>
                            <span v-if="item.product_type">{{ item.product_type }}</span>
                          </div>
                          <div class="text-xs text-gray-400 mt-1">Raw: {{ item.raw_name }}</div>
                        </div>
                        <div class="text-right ml-2">
                          <div class="font-semibold text-gray-900">{{ formatPrice(item.line_total) }}</div>
                          <div class="text-xs text-gray-500">
                            {{ item.quantity }} {{ item.unit || 'kom' }} x {{ formatPrice(item.unit_price) }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Modal Footer -->
            <div class="p-4 border-t bg-gray-50 flex justify-end gap-2">
              <button
                @click="deleteReceipt(selectedReceipt); closeViewModal()"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Obrisi
              </button>
              <button
                @click="closeViewModal"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Zatvori
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

interface ReceiptItem {
  id: number
  raw_name: string
  parsed_name: string | null
  brand: string | null
  product_type: string | null
  quantity: number | null
  unit: string | null
  unit_price: number | null
  line_total: number | null
}

interface Receipt {
  id: number
  user_id: string
  receipt_image_url: string
  store_name: string | null
  store_address: string | null
  jib: string | null
  pib: string | null
  ibfm: string | null
  receipt_serial_number: string | null
  receipt_date: string | null
  total_amount: number | null
  processing_status: string
  processing_error: string | null
  created_at: string
  items?: ReceiptItem[]
  user?: {
    id: string
    email: string
    name: string
  }
}

interface Stats {
  total_receipts: number
  by_status: {
    completed: number
    failed: number
    pending: number
  }
  users_with_receipts: number
  total_items: number
  total_amount: number
  recent_uploads_7d: number
}

const { get, del } = useApi()

const isLoading = ref(false)
const receipts = ref<Receipt[]>([])
const stats = ref<Stats>({
  total_receipts: 0,
  by_status: { completed: 0, failed: 0, pending: 0 },
  users_with_receipts: 0,
  total_items: 0,
  total_amount: 0,
  recent_uploads_7d: 0
})
const statusFilter = ref<string | null>(null)
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const totalReceipts = ref(0)

const showViewModal = ref(false)
const selectedReceipt = ref<Receipt | null>(null)

async function loadData() {
  await Promise.all([loadStats(), loadReceipts()])
}

async function loadStats() {
  try {
    const data = await get('/api/admin/receipts/stats')
    stats.value = data
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

async function loadReceipts() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('page', currentPage.value.toString())
    params.set('per_page', '50')
    if (statusFilter.value) params.set('status', statusFilter.value)
    if (searchQuery.value) params.set('search', searchQuery.value)

    const data = await get(`/api/admin/receipts?${params.toString()}`)
    receipts.value = data.receipts
    totalPages.value = data.pages
    totalReceipts.value = data.total
  } catch (error) {
    console.error('Error loading receipts:', error)
  } finally {
    isLoading.value = false
  }
}

function setFilter(status: string | null) {
  statusFilter.value = status
  currentPage.value = 1
  loadReceipts()
}

function openViewModal(receipt: Receipt) {
  selectedReceipt.value = receipt
  showViewModal.value = true
}

function closeViewModal() {
  showViewModal.value = false
  selectedReceipt.value = null
}

async function deleteReceipt(receipt: Receipt) {
  if (!confirm(`Jeste li sigurni da zelite obrisati racun #${receipt.id}?`)) return

  try {
    await del(`/api/admin/receipts/${receipt.id}`)
    receipts.value = receipts.value.filter(r => r.id !== receipt.id)
    loadStats()
  } catch (error) {
    console.error('Error deleting receipt:', error)
    alert('Greska pri brisanju racuna')
  }
}

function getStatusClass(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'completed':
      return 'Uspjesno'
    case 'pending':
      return 'Na cekanju'
    case 'failed':
      return 'Greska'
    default:
      return status
  }
}

function formatPrice(amount: number | null): string {
  if (amount === null) return '-'
  return `${Number(amount).toFixed(2)} KM`
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('bs-BA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = '/placeholder-receipt.png'
}

onMounted(() => {
  loadData()
})
</script>
