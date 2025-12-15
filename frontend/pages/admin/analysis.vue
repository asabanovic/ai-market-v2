<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Analiza cijena</h1>
            <p class="mt-1 text-sm text-gray-600">Pretrazite proizvode i uporedite cijene izmedju trgovina</p>
          </div>
          <NuxtLink
            to="/admin"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Nazad
          </NuxtLink>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Search Input -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Pretraga po nazivu</label>
            <div class="relative">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="npr. mlijeko, alpsko, jogurt..."
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-900"
                style="color: #111827;"
                @keyup.enter="search"
              />
              <svg class="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <!-- Category Group Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Kategorija</label>
            <select
              v-model="selectedCategoryGroup"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-900 appearance-none"
              style="color: #111827;"
            >
              <option value="" class="text-gray-900">Sve kategorije</option>
              <option v-for="cat in filters.category_groups" :key="cat" :value="cat" class="text-gray-900">
                {{ getCategoryGroupLabel(cat) }}
              </option>
            </select>
          </div>

          <!-- Business Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Trgovina ({{ filters.businesses?.length || 0 }})</label>
            <select
              v-model="selectedBusiness"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-900 appearance-none"
              style="color: #111827;"
            >
              <option value="" class="text-gray-900">Sve trgovine</option>
              <option v-for="b in filters.businesses" :key="b.id" :value="b.id" class="text-gray-900">
                {{ b.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Search Button -->
        <div class="mt-4 flex items-center gap-4">
          <button
            @click="search"
            :disabled="isLoading"
            class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed flex items-center"
          >
            <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ isLoading ? 'Trazim...' : 'Pretrazi' }}
          </button>
          <button
            v-if="products.length > 0"
            @click="clearSearch"
            class="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Ocisti
          </button>
          <span v-if="total > 0" class="text-sm text-gray-500">
            Pronadeno {{ total }} proizvoda
          </span>
        </div>
      </div>

      <!-- Results Summary & Chart Toggle -->
      <div v-if="products.length > 0" class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-4">
            <h2 class="text-lg font-medium text-gray-900">Rezultati pretrage</h2>
            <span class="text-sm text-gray-500">({{ filteredProducts.length }} od {{ products.length }})</span>
            <button
              v-if="excludedIds.size > 0"
              @click="resetExcluded"
              class="px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg flex items-center gap-1"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Vrati izuzete ({{ excludedIds.size }})
            </button>
          </div>
          <div class="flex items-center gap-4">
            <button
              @click="viewMode = 'table'"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium',
                viewMode === 'table' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
              ]"
            >
              Tabela
            </button>
            <button
              @click="viewMode = 'chart'"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium',
                viewMode === 'chart' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
              ]"
            >
              Grafikon
            </button>
          </div>
        </div>

        <!-- Price Stats -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Najniza cijena</div>
            <div class="text-xl font-semibold text-green-600">{{ formatPrice(priceStats.min) }} KM</div>
            <div class="text-xs text-gray-400">{{ priceStats.minStore }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Najvisa cijena</div>
            <div class="text-xl font-semibold text-red-600">{{ formatPrice(priceStats.max) }} KM</div>
            <div class="text-xs text-gray-400">{{ priceStats.maxStore }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Prosjecna cijena</div>
            <div class="text-xl font-semibold text-gray-900">{{ formatPrice(priceStats.avg) }} KM</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Razlika</div>
            <div class="text-xl font-semibold text-amber-600">{{ formatPrice(priceStats.max - priceStats.min) }} KM</div>
            <div class="text-xs text-gray-400">{{ priceStats.diffPercent }}% razlike</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Broj trgovina</div>
            <div class="text-xl font-semibold text-indigo-600">{{ priceStats.storeCount }}</div>
          </div>
        </div>

        <!-- Chart View -->
        <div v-if="viewMode === 'chart'" class="mb-6">
          <div class="h-80 bg-white rounded-lg p-4 border border-gray-200">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </div>

        <!-- Table View -->
        <div v-if="viewMode === 'table'" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-10"></th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proizvod</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trgovina</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kategorija</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Osnovna cijena</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Akcijska cijena</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Efektivna cijena</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Popust</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="product in filteredProducts" :key="product.id" class="hover:bg-gray-50">
                <td class="px-2 py-3 text-center">
                  <button
                    @click="excludeProduct(product.id)"
                    class="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                    title="Izuzmi iz analize"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center">
                    <img
                      v-if="product.image_path"
                      :src="product.image_path"
                      :alt="product.title"
                      class="w-10 h-10 rounded object-cover mr-3"
                    />
                    <div class="w-10 h-10 rounded bg-gray-200 mr-3 flex items-center justify-center" v-else>
                      <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <div class="text-sm font-medium text-gray-900">{{ product.title }}</div>
                      <div class="text-xs text-gray-500">ID: {{ product.id }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="text-sm text-gray-900">{{ product.business_name }}</div>
                  <div class="text-xs text-gray-500">{{ product.business_city }}</div>
                </td>
                <td class="px-4 py-3">
                  <span v-if="product.category_group" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium" :class="getCategoryGroupColor(product.category_group)">
                    {{ getCategoryGroupLabel(product.category_group) }}
                  </span>
                  <span v-else class="text-xs text-gray-400">{{ product.category || '-' }}</span>
                </td>
                <td class="px-4 py-3 text-right text-sm text-gray-900">
                  {{ formatPrice(product.base_price) }} KM
                </td>
                <td class="px-4 py-3 text-right text-sm">
                  <span v-if="product.discount_price && product.discount_price < product.base_price" class="text-green-600 font-medium">
                    {{ formatPrice(product.discount_price) }} KM
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span class="text-sm font-semibold" :class="getPriceClass(product.effective_price)">
                    {{ formatPrice(product.effective_price) }} KM
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span v-if="product.discount_percent > 0" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    -{{ product.discount_percent }}%
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pages > 1" class="mt-6 flex items-center justify-between">
          <div class="text-sm text-gray-500">
            Stranica {{ currentPage }} od {{ pages }}
          </div>
          <div class="flex gap-2">
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Prethodna
            </button>
            <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage === pages"
              class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Sljedeca
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="hasSearched && !isLoading" class="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">Nema rezultata</h3>
        <p class="mt-2 text-sm text-gray-500">Pokusajte sa drugim pojmom za pretragu</p>
      </div>

      <!-- Initial State -->
      <div v-else-if="!hasSearched" class="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <svg class="mx-auto h-12 w-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">Pretrazite proizvode</h3>
        <p class="mt-2 text-sm text-gray-500">Unesite naziv proizvoda da vidite cijene u razlicitim trgovinama</p>
        <div class="mt-4 flex flex-wrap justify-center gap-2">
          <button @click="quickSearch('mlijeko')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">mlijeko</button>
          <button @click="quickSearch('alpsko')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">alpsko</button>
          <button @click="quickSearch('jogurt')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">jogurt</button>
          <button @click="quickSearch('pileća prsa')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">pileca prsa</button>
          <button @click="quickSearch('coca cola')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">coca cola</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import ChartDataLabels from 'chartjs-plugin-datalabels'

Chart.register(...registerables, ChartDataLabels)

definePageMeta({
  middleware: ['auth', 'admin']
})

const { get } = useApi()

interface Product {
  id: number
  title: string
  category: string
  category_group: string
  base_price: number
  discount_price: number
  effective_price: number
  discount_percent: number
  business_id: number
  business_name: string
  business_city: string
  business_logo: string | null
  image_path: string
  tags: string[]
  created_at: string
}

interface Filters {
  businesses: { id: number; name: string }[]
  category_groups: string[]
}

const searchQuery = ref('')
const selectedCategoryGroup = ref('')
const selectedBusiness = ref<number | ''>('')
const isLoading = ref(false)
const hasSearched = ref(false)
const viewMode = ref<'table' | 'chart'>('table')

const products = ref<Product[]>([])
const total = ref(0)
const pages = ref(0)
const currentPage = ref(1)
const filters = ref<Filters>({ businesses: [], category_groups: [] })

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

// Excluded products (temporary, in-browser only)
const excludedIds = ref<Set<number>>(new Set())

// Filtered products (excluding temporarily removed ones)
const filteredProducts = computed(() => {
  return products.value.filter(p => !excludedIds.value.has(p.id))
})

function excludeProduct(id: number) {
  excludedIds.value = new Set([...excludedIds.value, id])
  // Update chart if in chart view
  if (viewMode.value === 'chart') {
    nextTick(() => updateChart())
  }
}

function resetExcluded() {
  excludedIds.value = new Set()
  // Update chart if in chart view
  if (viewMode.value === 'chart') {
    nextTick(() => updateChart())
  }
}

// Category group helpers
const categoryGroupLabels: Record<string, string> = {
  meso: 'Meso',
  mlijeko: 'Mlijeko',
  pica: 'Pica',
  voce_povrce: 'Voce/Povrce',
  kuhinja: 'Kuhinja',
  ves: 'Ves',
  ciscenje: 'Ciscenje',
  higijena: 'Higijena',
  slatkisi: 'Slatkisi',
  kafa: 'Kafa',
  smrznuto: 'Smrznuto',
  pekara: 'Pekara',
  ljubimci: 'Ljubimci',
  bebe: 'Bebe'
}

const categoryGroupColors: Record<string, string> = {
  meso: 'bg-red-100 text-red-800',
  mlijeko: 'bg-blue-100 text-blue-800',
  pica: 'bg-cyan-100 text-cyan-800',
  voce_povrce: 'bg-green-100 text-green-800',
  kuhinja: 'bg-yellow-100 text-yellow-800',
  ves: 'bg-indigo-100 text-indigo-800',
  ciscenje: 'bg-teal-100 text-teal-800',
  higijena: 'bg-pink-100 text-pink-800',
  slatkisi: 'bg-amber-100 text-amber-800',
  kafa: 'bg-orange-100 text-orange-800',
  smrznuto: 'bg-sky-100 text-sky-800',
  pekara: 'bg-lime-100 text-lime-800',
  ljubimci: 'bg-violet-100 text-violet-800',
  bebe: 'bg-rose-100 text-rose-800'
}

function getCategoryGroupLabel(group: string): string {
  return categoryGroupLabels[group] || group
}

function getCategoryGroupColor(group: string): string {
  return categoryGroupColors[group] || 'bg-gray-100 text-gray-800'
}

// Price statistics (based on filtered products)
const priceStats = computed(() => {
  if (filteredProducts.value.length === 0) {
    return { min: 0, max: 0, avg: 0, minStore: '', maxStore: '', diffPercent: 0, storeCount: 0 }
  }

  const prices = filteredProducts.value.map(p => p.effective_price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const avg = prices.reduce((a, b) => a + b, 0) / prices.length

  const minProduct = filteredProducts.value.find(p => p.effective_price === min)
  const maxProduct = filteredProducts.value.find(p => p.effective_price === max)

  const uniqueStores = new Set(filteredProducts.value.map(p => p.business_id))

  return {
    min,
    max,
    avg,
    minStore: minProduct?.business_name || '',
    maxStore: maxProduct?.business_name || '',
    diffPercent: min > 0 ? Math.round(((max - min) / min) * 100) : 0,
    storeCount: uniqueStores.size
  }
})

function getPriceClass(price: number): string {
  if (filteredProducts.value.length === 0) return 'text-gray-900'

  const { min, max } = priceStats.value
  if (price === min) return 'text-green-600'
  if (price === max) return 'text-red-600'
  return 'text-gray-900'
}

function formatPrice(price: number): string {
  return price?.toFixed(2) || '0.00'
}

async function search() {
  if (!searchQuery.value.trim() && !selectedCategoryGroup.value && !selectedBusiness.value) {
    return
  }

  isLoading.value = true
  hasSearched.value = true

  try {
    const params = new URLSearchParams()
    if (searchQuery.value.trim()) {
      params.set('q', searchQuery.value.trim())
    }
    if (selectedCategoryGroup.value) {
      params.set('category_group', selectedCategoryGroup.value)
    }
    if (selectedBusiness.value) {
      params.set('business_id', String(selectedBusiness.value))
    }
    params.set('page', String(currentPage.value))
    params.set('per_page', '100')

    const data = await get(`/api/admin/products/analysis?${params.toString()}`)

    products.value = data.products || []
    total.value = data.total || 0
    pages.value = data.pages || 0
    filters.value = data.filters || { businesses: [], category_groups: [] }

    // Load logos and update chart if in chart view
    if (viewMode.value === 'chart' && products.value.length > 0) {
      await loadLogoImages()
      nextTick(() => updateChart())
    }
  } catch (error) {
    console.error('Search error:', error)
  } finally {
    isLoading.value = false
  }
}

function quickSearch(term: string) {
  searchQuery.value = term
  search()
}

function clearSearch() {
  searchQuery.value = ''
  selectedCategoryGroup.value = ''
  selectedBusiness.value = ''
  products.value = []
  total.value = 0
  pages.value = 0
  currentPage.value = 1
  hasSearched.value = false
  excludedIds.value = new Set()

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

function goToPage(page: number) {
  if (page < 1 || page > pages.value) return
  currentPage.value = page
  search()
}

// Store logo images cache
const logoImages = ref<Map<string, HTMLImageElement>>(new Map())

async function loadLogoImages() {
  const storeLogos = new Map<string, string | null>()

  // Get unique logos for stores from filtered products
  filteredProducts.value.forEach(p => {
    if (!storeLogos.has(p.business_name)) {
      storeLogos.set(p.business_name, p.business_logo)
    }
  })

  // Load images - without crossOrigin to avoid CORS issues
  // Images loaded without crossOrigin can still be displayed but may taint canvas
  const loadPromises: Promise<void>[] = []
  storeLogos.forEach((logo, storeName) => {
    if (logo && !logoImages.value.has(storeName)) {
      const promise = new Promise<void>((resolve) => {
        const img = new Image()
        // Don't set crossOrigin - just load the image
        img.onload = () => {
          logoImages.value.set(storeName, img)
          resolve()
        }
        img.onerror = () => {
          console.log(`Failed to load logo for ${storeName}`)
          resolve()
        }
        img.src = logo
      })
      loadPromises.push(promise)
    }
  })

  await Promise.all(loadPromises)
}

function updateChart() {
  if (!chartCanvas.value) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  // Group by store and calculate average price (using filtered products)
  const storeData: Record<string, { prices: number[]; name: string; logo: string | null }> = {}

  filteredProducts.value.forEach(p => {
    if (!storeData[p.business_name]) {
      storeData[p.business_name] = { prices: [], name: p.business_name, logo: p.business_logo }
    }
    storeData[p.business_name].prices.push(p.effective_price)
  })

  const labels = Object.keys(storeData)
  if (labels.length === 0) return // No data to show

  const avgPrices = labels.map(store => {
    const prices = storeData[store].prices
    return prices.reduce((a, b) => a + b, 0) / prices.length
  })
  const minPrices = labels.map(store => Math.min(...storeData[store].prices))
  const maxPrices = labels.map(store => Math.max(...storeData[store].prices))
  const productCounts = labels.map(store => storeData[store].prices.length)

  // Sort by average price
  const sortedIndices = avgPrices.map((_, i) => i).sort((a, b) => avgPrices[a] - avgPrices[b])
  const sortedLabels = sortedIndices.map(i => labels[i])

  // Custom plugin to draw logos and store names on x-axis
  const logoPlugin = {
    id: 'logoPlugin',
    afterDraw: (chart: any) => {
      const ctx = chart.ctx
      const xAxis = chart.scales.x
      const yAxis = chart.scales.y

      sortedLabels.forEach((storeName, index) => {
        const x = xAxis.getPixelForValue(index)
        const y = yAxis.bottom + 10
        const logoImg = logoImages.value.get(storeName)

        if (logoImg) {
          // Draw logo - larger size
          const logoSize = 40
          ctx.drawImage(logoImg, x - logoSize / 2, y, logoSize, logoSize)

          // Draw store name below logo
          ctx.fillStyle = '#374151'
          ctx.font = '12px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(storeName, x, y + logoSize + 14)
        } else {
          // No logo - just draw store name
          ctx.fillStyle = '#374151'
          ctx.font = '13px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(storeName, x, y + 20)
        }
      })
    }
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels: sortedLabels,
      datasets: [
        {
          label: 'Prosjecna cijena (KM)',
          data: sortedIndices.map(i => avgPrices[i]),
          backgroundColor: sortedIndices.map((_, idx) =>
            idx === 0 ? 'rgba(34, 197, 94, 0.8)' :
            idx === sortedIndices.length - 1 ? 'rgba(239, 68, 68, 0.8)' :
            'rgba(99, 102, 241, 0.8)'
          ),
          borderColor: sortedIndices.map((_, idx) =>
            idx === 0 ? 'rgb(34, 197, 94)' :
            idx === sortedIndices.length - 1 ? 'rgb(239, 68, 68)' :
            'rgb(99, 102, 241)'
          ),
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          bottom: 75 // Extra space for larger logos and names
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            afterLabel: (context) => {
              const idx = sortedIndices[context.dataIndex]
              return [
                `Min: ${minPrices[idx].toFixed(2)} KM`,
                `Max: ${maxPrices[idx].toFixed(2)} KM`,
                `Proizvoda: ${productCounts[idx]}`
              ]
            }
          }
        },
        // Display values on top of bars
        datalabels: {
          display: true,
          color: '#1f2937',
          anchor: 'end',
          align: 'top',
          font: {
            weight: 'bold',
            size: 14
          },
          formatter: (value: number) => value.toFixed(2) + ' KM'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: Math.max(...avgPrices) * 1.2, // Expand by 20% to fit labels
          title: {
            display: true,
            text: 'Cijena (KM)'
          }
        },
        x: {
          ticks: {
            display: false // Hide default labels, we draw custom ones with logos
          },
          title: {
            display: false
          }
        }
      }
    },
    plugins: [logoPlugin]
  })
}

// Watch for view mode changes to update chart
watch(viewMode, async (newMode) => {
  if (newMode === 'chart' && filteredProducts.value.length > 0) {
    await loadLogoImages()
    nextTick(() => updateChart())
  }
})

// Load filters on mount
onMounted(async () => {
  try {
    const data = await get('/api/admin/products/analysis?per_page=1')
    if (data.filters) {
      filters.value = data.filters
    }
    console.log('Loaded filters:', filters.value)
  } catch (error) {
    console.error('Error loading filters:', error)
  }
})

useSeoMeta({
  title: 'Analiza cijena - Admin - Popust.ba',
  description: 'Analiza i poredjenje cijena proizvoda izmedju trgovina',
})
</script>
