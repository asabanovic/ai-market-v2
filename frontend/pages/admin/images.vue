<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">AI Podudaranje Slika</h1>
            <p class="mt-1 text-sm text-gray-600">Masovno podudaranje slika proizvoda koristeci GPT-4o Vision</p>
          </div>
          <NuxtLink
            to="/admin"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Nazad na Admin Dashboard
          </NuxtLink>
        </div>
      </div>

      <!-- Bulk Actions Toolbar -->
      <div v-if="selectedProductIds.size > 0" class="mb-6 bg-purple-50 border border-purple-200 rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <span class="text-sm font-medium text-purple-900">
              {{ selectedProductIds.size }} proizvoda odabrano
            </span>
            <button
              @click="clearSelection"
              class="text-sm text-purple-600 hover:text-purple-800"
            >
              Ponisti izbor
            </button>
          </div>
          <div class="flex items-center space-x-3">
            <button
              @click="runBulkImageMatching"
              :disabled="isProcessing"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <svg v-if="isProcessing" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <svg v-else class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              {{ isProcessing ? `Obradujem... (${processingProgress}/${selectedProductIds.size})` : 'Pokreni AI Matching' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Filter Controls -->
      <div class="mb-6 bg-white rounded-lg border border-gray-200 p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <span class="text-sm font-medium text-gray-700">Filter:</span>
            <button
              @click="filterMode = 'all'"
              :class="[
                'px-3 py-1 rounded-md text-sm',
                filterMode === 'all' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Svi ({{ stats.total || 0 }})
            </button>
            <button
              @click="filterMode = 'no_image'"
              :class="[
                'px-3 py-1 rounded-md text-sm',
                filterMode === 'no_image' ? 'bg-red-600 text-white' : 'bg-red-50 text-red-700 hover:bg-red-100'
              ]"
            >
              Bez slike ({{ stats.no_image || 0 }})
            </button>
            <button
              @click="filterMode = 'has_original'"
              :class="[
                'px-3 py-1 rounded-md text-sm',
                filterMode === 'has_original' ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
              ]"
            >
              Ima original ({{ stats.has_original || 0 }})
            </button>
          </div>
          <div class="flex items-center space-x-3">
            <button
              @click="selectAllFiltered"
              class="text-sm text-purple-600 hover:text-purple-800"
            >
              Odaberi sve filtrirane
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-purple-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Ucitavanje proizvoda...</span>
        </div>
      </div>

      <!-- Products Grid -->
      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <div
          v-for="product in filteredProducts"
          :key="product.id"
          :class="[
            'relative bg-white rounded-lg border-2 overflow-hidden cursor-pointer transition-all',
            selectedProductIds.has(product.id) ? 'border-purple-500 ring-2 ring-purple-200' : 'border-gray-200 hover:border-gray-300'
          ]"
          @click="toggleProductSelection(product.id)"
        >
          <!-- Selection Checkbox -->
          <div class="absolute top-2 left-2 z-10">
            <input
              type="checkbox"
              :checked="selectedProductIds.has(product.id)"
              @click.stop="toggleProductSelection(product.id)"
              class="h-5 w-5 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
          </div>

          <!-- Match Result Badge -->
          <div v-if="matchResults[product.id]" class="absolute top-2 right-2 z-10">
            <span
              :class="[
                'inline-flex items-center px-2 py-1 rounded-full text-xs font-bold',
                matchResults[product.id].best_match?.confidence >= 90 ? 'bg-green-500 text-white' :
                matchResults[product.id].best_match?.confidence >= 70 ? 'bg-yellow-500 text-white' :
                matchResults[product.id].best_match?.confidence >= 50 ? 'bg-orange-500 text-white' :
                'bg-red-500 text-white'
              ]"
            >
              {{ matchResults[product.id].best_match?.confidence || 0 }}%
            </span>
          </div>

          <!-- Image Replaced Indicator -->
          <div v-if="isImageReplaced(product)" class="absolute top-2 right-2 z-10" :class="{ 'right-14': matchResults[product.id] }">
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-blue-500 text-white" title="Slika je zamijenjena">
              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Zamijenjena
            </span>
          </div>

          <!-- Processing Indicator -->
          <div v-if="processingProductIds.has(product.id)" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-20">
            <svg class="animate-spin h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>

          <!-- Product Image -->
          <div class="aspect-square bg-white">
            <img
              v-if="product.image_path || product.original_image_path"
              :src="getImageUrl(product.image_path || product.original_image_path)"
              :alt="product.title"
              class="w-full h-full object-contain"
              @error="handleImageError"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
            </div>
          </div>

          <!-- Product Info -->
          <div class="p-3">
            <h3 class="text-sm font-medium text-gray-900 line-clamp-2">{{ product.title }}</h3>
            <p class="text-xs text-gray-500 mt-1">ID: {{ product.id }}</p>
            <p v-if="product.business_name" class="text-xs text-gray-400 truncate">{{ product.business_name }}</p>
          </div>

          <!-- Quick Actions -->
          <div class="px-3 pb-3 flex gap-2">
            <button
              @click.stop="openMatchModal(product)"
              class="flex-1 px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
            >
              Podudaranje
            </button>
            <button
              v-if="matchResults[product.id]?.best_match?.confidence >= 80"
              @click.stop="applyBestMatch(product.id)"
              class="flex-1 px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
            >
              Primijeni
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!isLoading && filteredProducts.length === 0" class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Nema proizvoda</h3>
        <p class="mt-1 text-sm text-gray-500">Nema proizvoda koji odgovaraju filteru.</p>
      </div>

      <!-- Match Modal -->
      <div v-if="showMatchModal" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
          <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="closeMatchModal"></div>

          <div class="relative bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:max-w-4xl sm:w-full">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <h3 class="text-lg font-medium text-gray-900">AI Podudaranje Slika</h3>
                  <p class="text-sm text-gray-500">{{ selectedProduct?.title }}</p>
                </div>
                <button @click="closeMatchModal" class="text-gray-400 hover:text-gray-600">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>

              <!-- Original Image -->
              <div class="mb-6">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Originalna slika proizvoda:</h4>
                <div class="w-48 h-48 bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    v-if="selectedProduct?.original_image_path || selectedProduct?.image_path"
                    :src="getImageUrl(selectedProduct?.original_image_path || selectedProduct?.image_path)"
                    :alt="selectedProduct?.title"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                    <span class="text-sm">Nema originalne slike</span>
                  </div>
                </div>
              </div>

              <!-- Suggested Images with Match Scores -->
              <div v-if="modalMatchResult">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Predlozene slike (klikni za odabir):</h4>
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  <div
                    v-for="(match, index) in modalMatchResult.matches.filter((m: any) => m.image_path)"
                    :key="index"
                    :class="[
                      'relative rounded-lg overflow-hidden cursor-pointer border-3 transition-all',
                      selectedImagePath === match.image_path ? 'border-purple-500 ring-4 ring-purple-200 scale-105' :
                      match.is_best ? 'border-green-500 ring-2 ring-green-200' : 'border-gray-200 hover:border-gray-400'
                    ]"
                    @click="selectSuggestedImage(match.image_path)"
                  >
                    <!-- Selected Checkmark -->
                    <div v-if="selectedImagePath === match.image_path" class="absolute top-1 right-1 z-10 bg-purple-600 rounded-full p-1">
                      <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div class="aspect-square bg-gray-100">
                      <img
                        :src="getImageUrl(match.image_path)"
                        :alt="`Suggestion ${index + 1}`"
                        class="w-full h-full object-cover"
                        @error="handleImageError"
                      />
                    </div>
                    <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 px-2 py-1">
                      <div class="flex items-center justify-between">
                        <span
                          :class="[
                            'text-xs font-bold',
                            match.confidence >= 90 ? 'text-green-400' :
                            match.confidence >= 70 ? 'text-yellow-400' :
                            match.confidence >= 50 ? 'text-orange-400' :
                            'text-red-400'
                          ]"
                        >
                          {{ match.confidence }}%
                        </span>
                        <span v-if="match.is_best" class="text-xs text-green-400">AI najbolji</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- AI Analysis -->
                <div v-if="modalMatchResult.analysis" class="mt-4 p-3 bg-gray-50 rounded-lg">
                  <h5 class="text-sm font-medium text-gray-700 mb-1">AI Analiza:</h5>
                  <p class="text-sm text-gray-600">{{ modalMatchResult.analysis }}</p>
                </div>
              </div>

              <!-- Loading State for Modal -->
              <div v-else-if="isMatchingProduct" class="flex items-center justify-center py-12">
                <svg class="animate-spin h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span class="ml-3 text-gray-600">AI analizira slike...</span>
              </div>

              <!-- Start Matching Button -->
              <div v-else class="text-center py-8">
                <button
                  @click="runSingleMatch(selectedProduct.id)"
                  class="inline-flex items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-purple-600 hover:bg-purple-700"
                >
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Pokreni AI Matching
                </button>
              </div>
            </div>

            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                v-if="modalMatchResult?.matches?.length"
                @click="applySelectedMatch"
                :disabled="!selectedImagePath"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {{ selectedImagePath ? 'Primijeni odabranu sliku' : 'Odaberi sliku' }}
              </button>
              <button
                @click="closeMatchModal"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Zatvori
              </button>
            </div>
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

const config = useRuntimeConfig()
const { get, post } = useApi()
const { showSuccess, showError, showInfo } = useCreditsToast()

const isLoading = ref(true)
const products = ref<any[]>([])
const stats = ref<any>({})
const selectedProductIds = ref<Set<number>>(new Set())
const filterMode = ref<'all' | 'no_image' | 'has_original'>('all')

const isProcessing = ref(false)
const processingProgress = ref(0)
const processingProductIds = ref<Set<number>>(new Set())
const matchResults = ref<Record<number, any>>({})

const showMatchModal = ref(false)
const selectedProduct = ref<any>(null)
const modalMatchResult = ref<any>(null)
const isMatchingProduct = ref(false)
const selectedImagePath = ref<string | null>(null)

const filteredProducts = computed(() => {
  if (filterMode.value === 'all') return products.value
  if (filterMode.value === 'no_image') {
    return products.value.filter(p => !p.image_path && !p.original_image_path)
  }
  if (filterMode.value === 'has_original') {
    return products.value.filter(p => p.original_image_path)
  }
  return products.value
})

onMounted(async () => {
  await loadProducts()
})

async function loadProducts() {
  try {
    const data = await get('/api/admin/products/images')
    products.value = data.products || []
    stats.value = data.stats || {}
  } catch (error) {
    console.error('Error loading products:', error)
    showError('Nije moguce ucitati proizvode', 'Greska')
  } finally {
    isLoading.value = false
  }
}

function getImageUrl(path: string | null): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const bucket = 'aipijaca'
  const region = 'eu-central-1'
  return `https://${bucket}.s3.${region}.amazonaws.com/${path}`
}

function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  // Hide the image if it fails to load
  img.style.display = 'none'
  // Show a placeholder icon in parent
  const parent = img.parentElement
  if (parent && !parent.querySelector('.error-placeholder')) {
    const placeholder = document.createElement('div')
    placeholder.className = 'error-placeholder w-full h-full flex items-center justify-center text-gray-400'
    placeholder.innerHTML = `<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
    </svg>`
    parent.appendChild(placeholder)
  }
}

function isImageReplaced(product: any): boolean {
  // Check if the product has both original and current images, and they differ
  if (!product.original_image_path || !product.image_path) return false
  // Normalize paths for comparison (remove S3 URL prefix if present)
  const originalPath = product.original_image_path.replace(/^https?:\/\/[^/]+\//, '')
  const currentPath = product.image_path.replace(/^https?:\/\/[^/]+\//, '')
  return originalPath !== currentPath
}

function toggleProductSelection(productId: number) {
  if (selectedProductIds.value.has(productId)) {
    selectedProductIds.value.delete(productId)
  } else {
    selectedProductIds.value.add(productId)
  }
  selectedProductIds.value = new Set(selectedProductIds.value)
}

function clearSelection() {
  selectedProductIds.value.clear()
  selectedProductIds.value = new Set()
}

function selectAllFiltered() {
  filteredProducts.value.forEach(p => selectedProductIds.value.add(p.id))
  selectedProductIds.value = new Set(selectedProductIds.value)
  showInfo(`Odabrano ${selectedProductIds.value.size} proizvoda`, 'Odabrano')
}

async function runBulkImageMatching() {
  if (selectedProductIds.value.size === 0) return

  isProcessing.value = true
  processingProgress.value = 0
  const productIds = Array.from(selectedProductIds.value)
  const totalProducts = productIds.length
  const BATCH_SIZE = 10 // Process up to 10 in parallel

  // Process in batches of 10
  for (let i = 0; i < productIds.length; i += BATCH_SIZE) {
    const batch = productIds.slice(i, i + BATCH_SIZE)

    // Mark all in batch as processing
    batch.forEach(id => processingProductIds.value.add(id))
    processingProductIds.value = new Set(processingProductIds.value)

    // Process batch in parallel
    const results = await Promise.allSettled(
      batch.map(async (productId) => {
        try {
          const result = await post(`/api/admin/products/${productId}/ai-match-images`)
          matchResults.value[productId] = result
          processingProgress.value++

          // Auto-apply if 100% match
          if (result.best_match?.confidence === 100) {
            await applyBestMatch(productId)
          }
          return { productId, success: true }
        } catch (error) {
          console.error(`Error matching product ${productId}:`, error)
          processingProgress.value++
          return { productId, success: false, error }
        } finally {
          // Remove from processing immediately when done
          processingProductIds.value.delete(productId)
          processingProductIds.value = new Set(processingProductIds.value)
        }
      })
    )
  }

  isProcessing.value = false
  showSuccess(`Obradeno ${processingProgress.value} proizvoda`, 'Zavrseno')
}

function openMatchModal(product: any) {
  selectedProduct.value = product
  modalMatchResult.value = matchResults.value[product.id] || null
  selectedImagePath.value = null
  showMatchModal.value = true
}

function closeMatchModal() {
  showMatchModal.value = false
  selectedProduct.value = null
  modalMatchResult.value = null
  selectedImagePath.value = null
}

async function runSingleMatch(productId: number) {
  isMatchingProduct.value = true

  try {
    const result = await post(`/api/admin/products/${productId}/ai-match-images`)
    modalMatchResult.value = result
    matchResults.value[productId] = result

    if (result.best_match) {
      selectedImagePath.value = result.best_match.image_path
    }
  } catch (error) {
    console.error('Error matching product:', error)
    showError('Nije moguce analizirati slike', 'Greska')
  } finally {
    isMatchingProduct.value = false
  }
}

function selectSuggestedImage(imagePath: string) {
  selectedImagePath.value = imagePath
}

async function applySelectedMatch() {
  if (!selectedProduct.value || !selectedImagePath.value) return

  try {
    await post(`/api/admin/products/${selectedProduct.value.id}/select-image`, {
      image_path: selectedImagePath.value
    })

    // Update local product - keep original_image_path intact, update image_path
    const product = products.value.find(p => p.id === selectedProduct.value.id)
    if (product) {
      // Store original if not already stored
      if (!product.original_image_path && product.image_path) {
        product.original_image_path = product.image_path
      }
      product.image_path = selectedImagePath.value
    }

    showSuccess('Slika je primijenjena', 'Uspjesno')

    closeMatchModal()
  } catch (error) {
    console.error('Error applying image:', error)
    showError('Nije moguce primijeniti sliku', 'Greska')
  }
}

async function applyBestMatch(productId: number) {
  const result = matchResults.value[productId]
  if (!result?.best_match) return

  try {
    await post(`/api/admin/products/${productId}/select-image`, {
      image_path: result.best_match.image_path
    })

    // Update local product - keep original_image_path intact, update image_path
    const product = products.value.find(p => p.id === productId)
    if (product) {
      // Store original if not already stored
      if (!product.original_image_path && product.image_path) {
        product.original_image_path = product.image_path
      }
      product.image_path = result.best_match.image_path
    }

    showSuccess(`Slika primijenjena za proizvod ${productId}`, 'Uspjesno')
  } catch (error) {
    console.error('Error applying image:', error)
  }
}

useSeoMeta({
  title: 'AI Podudaranje Slika - Admin - Popust.ba',
  description: 'Masovno podudaranje slika proizvoda koristeci GPT-4o Vision',
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
