<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Prijave proizvoda</h1>
          <p class="mt-1 text-sm text-gray-600">Pregled i upravljanje prijavama korisnika</p>
        </div>
        <NuxtLink
          to="/admin"
          class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <Icon name="mdi:arrow-left" class="w-4 h-4 mr-2" />
          Nazad na dashboard
        </NuxtLink>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
          <div class="text-2xl font-bold text-yellow-700">{{ reportStats.pending || 0 }}</div>
          <div class="text-sm text-yellow-600">Na cekanju</div>
        </div>
        <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div class="text-2xl font-bold text-blue-700">{{ reportStats.reviewed || 0 }}</div>
          <div class="text-sm text-blue-600">Pregledano</div>
        </div>
        <div class="bg-green-50 rounded-lg p-4 border border-green-200">
          <div class="text-2xl font-bold text-green-700">{{ reportStats.resolved || 0 }}</div>
          <div class="text-sm text-green-600">Rijeseno</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div class="text-2xl font-bold text-gray-700">{{ reportStats.dismissed || 0 }}</div>
          <div class="text-sm text-gray-600">Odbaceno</div>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="bg-white rounded-lg border border-gray-200 mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              v-for="tab in tabs"
              :key="tab.value"
              @click="currentFilter = tab.value"
              :class="[
                'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                currentFilter === tab.value
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ tab.label }}
              <span
                v-if="tab.value === 'pending' && reportStats.pending > 0"
                class="ml-2 px-2 py-0.5 rounded-full text-xs bg-yellow-100 text-yellow-800"
              >
                {{ reportStats.pending }}
              </span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <Icon name="mdi:loading" class="w-8 h-8 animate-spin" />
          <span class="ml-3 text-lg">Ucitavanje...</span>
        </div>
      </div>

      <!-- Reports List -->
      <div v-else-if="reports.length > 0" class="space-y-4">
        <div
          v-for="report in reports"
          :key="report.id"
          class="bg-white rounded-lg border border-gray-200 overflow-hidden"
        >
          <div class="p-6">
            <div class="flex items-start gap-6">
              <!-- Product Image -->
              <div class="flex-shrink-0">
                <div v-if="report.product" class="w-24 h-24 rounded-lg overflow-hidden bg-gray-100">
                  <img
                    v-if="report.product.image_path"
                    :src="getImageUrl(report.product.image_path)"
                    :alt="report.product.title"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="flex items-center justify-center h-full text-gray-400">
                    <Icon name="mdi:image-off" class="w-8 h-8" />
                  </div>
                </div>
                <div v-else class="w-24 h-24 rounded-lg bg-red-50 flex items-center justify-center">
                  <Icon name="mdi:delete" class="w-8 h-8 text-red-400" />
                </div>
              </div>

              <!-- Report Details -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900">
                      {{ report.product?.title || 'Proizvod obrisan' }}
                    </h3>
                    <p v-if="report.product?.business" class="text-sm text-gray-500">
                      {{ report.product.business.name }}
                    </p>
                  </div>
                  <span
                    :class="[
                      'px-3 py-1 rounded-full text-sm font-medium',
                      statusColors[report.status]
                    ]"
                  >
                    {{ statusLabels[report.status] }}
                  </span>
                </div>

                <!-- Reporter Info -->
                <div class="mt-3 flex items-center gap-4 text-sm text-gray-600">
                  <div class="flex items-center gap-1">
                    <Icon name="mdi:account" class="w-4 h-4" />
                    <span>{{ report.reporter.first_name }} {{ report.reporter.last_name }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <Icon name="mdi:email" class="w-4 h-4" />
                    <span>{{ report.reporter.email }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <Icon name="mdi:clock" class="w-4 h-4" />
                    <span>{{ formatDateTime(report.created_at) }}</span>
                  </div>
                </div>

                <!-- Reason -->
                <div v-if="report.reason" class="mt-3 p-3 bg-gray-50 rounded-lg">
                  <p class="text-sm text-gray-700">
                    <span class="font-medium">Razlog:</span> {{ report.reason }}
                  </p>
                </div>

                <!-- Admin Notes -->
                <div v-if="report.admin_notes" class="mt-3 p-3 bg-blue-50 rounded-lg">
                  <p class="text-sm text-blue-700">
                    <span class="font-medium">Admin biljeska:</span> {{ report.admin_notes }}
                  </p>
                </div>

                <!-- Actions -->
                <div class="mt-4 flex items-center gap-3">
                  <button
                    v-if="report.product"
                    @click="openProduct(report.product.id)"
                    class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                  >
                    <Icon name="mdi:open-in-new" class="w-4 h-4 mr-1" />
                    Vidi proizvod
                  </button>

                  <button
                    v-if="report.status === 'pending'"
                    @click="updateReportStatus(report.id, 'reviewed')"
                    class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    <Icon name="mdi:eye" class="w-4 h-4 mr-1" />
                    Oznaci kao pregledano
                  </button>

                  <button
                    v-if="report.status !== 'resolved'"
                    @click="updateReportStatus(report.id, 'resolved')"
                    class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-green-600 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                  >
                    <Icon name="mdi:check" class="w-4 h-4 mr-1" />
                    Rijesi
                  </button>

                  <button
                    v-if="report.status !== 'dismissed'"
                    @click="updateReportStatus(report.id, 'dismissed')"
                    class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Icon name="mdi:close" class="w-4 h-4 mr-1" />
                    Odbaci
                  </button>

                  <button
                    @click="openNotesModal(report)"
                    class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Icon name="mdi:note-edit" class="w-4 h-4 mr-1" />
                    Biljeska
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="pagination && pagination.pages > 1" class="flex items-center justify-between bg-white px-6 py-4 rounded-lg border border-gray-200">
          <div class="text-sm text-gray-700">
            Strana {{ pagination.page }} od {{ pagination.pages }} ({{ pagination.total }} ukupno)
          </div>
          <div class="flex space-x-2">
            <button
              v-if="pagination.has_prev"
              @click="loadReports(pagination.page - 1)"
              class="px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Prethodna
            </button>
            <button
              v-if="pagination.has_next"
              @click="loadReports(pagination.page + 1)"
              class="px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Sljedeca
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <Icon name="mdi:flag-off" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nema prijava</h3>
        <p class="text-gray-500">Trenutno nema prijava u ovoj kategoriji.</p>
      </div>
    </div>

    <!-- Notes Modal -->
    <Teleport to="body">
      <div
        v-if="showNotesModal"
        class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
        @click.self="showNotesModal = false"
      >
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Admin biljeska</h3>
          <textarea
            v-model="adminNotes"
            rows="4"
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all resize-none text-gray-900"
            placeholder="Unesite biljesku..."
          ></textarea>
          <div class="flex gap-3 mt-4">
            <button
              @click="showNotesModal = false"
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Odustani
            </button>
            <button
              @click="saveNotes"
              class="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Sacuvaj
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const config = useRuntimeConfig()
const { get, put } = useApi()

const isLoading = ref(true)
const reports = ref<any[]>([])
const reportStats = ref<any>({})
const pagination = ref<any>(null)
const currentFilter = ref<string | null>(null)

const showNotesModal = ref(false)
const selectedReport = ref<any>(null)
const adminNotes = ref('')

const tabs = [
  { label: 'Sve', value: null },
  { label: 'Na cekanju', value: 'pending' },
  { label: 'Pregledano', value: 'reviewed' },
  { label: 'Rijeseno', value: 'resolved' },
  { label: 'Odbaceno', value: 'dismissed' }
]

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  reviewed: 'bg-blue-100 text-blue-800',
  resolved: 'bg-green-100 text-green-800',
  dismissed: 'bg-gray-100 text-gray-800'
}

const statusLabels: Record<string, string> = {
  pending: 'Na cekanju',
  reviewed: 'Pregledano',
  resolved: 'Rijeseno',
  dismissed: 'Odbaceno'
}

onMounted(async () => {
  await loadReports()
})

watch(currentFilter, () => {
  loadReports(1)
})

async function loadReports(page = 1) {
  isLoading.value = true
  try {
    let url = `/api/admin/reports?page=${page}&per_page=20`
    if (currentFilter.value) {
      url += `&status=${currentFilter.value}`
    }
    const data = await get(url)
    reports.value = data.reports || []
    reportStats.value = data.stats || {}
    pagination.value = data.pagination
  } catch (error) {
    console.error('Error loading reports:', error)
  } finally {
    isLoading.value = false
  }
}

async function updateReportStatus(reportId: number, status: string) {
  try {
    await put(`/api/admin/reports/${reportId}`, { status })
    // Refresh the list
    await loadReports(pagination.value?.page || 1)
  } catch (error) {
    console.error('Error updating report:', error)
  }
}

function openNotesModal(report: any) {
  selectedReport.value = report
  adminNotes.value = report.admin_notes || ''
  showNotesModal.value = true
}

async function saveNotes() {
  if (!selectedReport.value) return

  try {
    await put(`/api/admin/reports/${selectedReport.value.id}`, {
      admin_notes: adminNotes.value
    })
    showNotesModal.value = false
    await loadReports(pagination.value?.page || 1)
  } catch (error) {
    console.error('Error saving notes:', error)
  }
}

function openProduct(productId: number) {
  window.open(`/?product=${productId}`, '_blank')
}

function getImageUrl(path: string) {
  if (path.startsWith('http')) return path
  return `${config.public.apiBase}/static/${path}`
}

function formatDateTime(dateString: string) {
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
  title: 'Prijave proizvoda - Admin - Popust.ba',
  description: 'Pregled prijava proizvoda na Popust.ba platformi'
})
</script>
