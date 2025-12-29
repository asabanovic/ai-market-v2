<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <!-- Notifications -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <div
        v-for="(notification, index) in notifications"
        :key="index"
        class="px-4 py-3 rounded-lg shadow-lg max-w-sm"
        :class="{
          'bg-green-100 text-green-800 border border-green-200': notification.type === 'success',
          'bg-red-100 text-red-800 border border-red-200': notification.type === 'error',
          'bg-blue-100 text-blue-800 border border-blue-200': notification.type === 'info'
        }"
      >
        <span class="text-sm">{{ notification.message }}</span>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Duplikati proizvoda</h1>
            <p class="mt-1 text-sm text-gray-500">
              Pronadi i spoji duplikate proizvoda unutar trgovine
            </p>
          </div>
          <NuxtLink to="/admin" class="text-sm text-indigo-600 hover:text-indigo-800">
            &larr; Nazad na admin
          </NuxtLink>
        </div>
      </div>

      <!-- Store Selection -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex flex-wrap items-end gap-4">
          <div class="flex-1 min-w-[200px]">
            <label class="block text-sm font-medium text-gray-700 mb-1">Trgovina</label>
            <select
              v-model="selectedBusinessId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option :value="null">Odaberi trgovinu...</option>
              <option v-for="business in businesses" :key="business.id" :value="business.id">
                {{ business.name }} ({{ business.product_count || '?' }} proizvoda)
              </option>
            </select>
          </div>
          <div class="w-32">
            <label class="block text-sm font-medium text-gray-700 mb-1">Threshold</label>
            <input
              v-model.number="threshold"
              type="number"
              min="0.5"
              max="1"
              step="0.05"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <button
            @click="findDuplicates"
            :disabled="!selectedBusinessId || isLoading"
            class="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg v-if="isLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isLoading ? 'Trazim...' : 'Pronadi duplikate' }}</span>
          </button>
        </div>
      </div>

      <!-- Results Summary -->
      <div v-if="duplicates.length > 0" class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Pronadeno {{ duplicates.length }} grupa duplikata</h2>
            <p class="text-sm text-gray-500">Ukupno {{ totalDuplicateProducts }} proizvoda koji mogu biti spojeni</p>
          </div>
          <button
            v-if="duplicates.length > 0"
            @click="mergeAllRecommended"
            :disabled="isMerging"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 text-sm"
          >
            {{ isMerging ? 'Spajam...' : 'Spoji sve preporucene' }}
          </button>
        </div>
      </div>

      <!-- No Results -->
      <div v-else-if="searchPerformed && !isLoading" class="bg-white rounded-lg shadow-sm p-12 text-center">
        <svg class="w-16 h-16 mx-auto text-green-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nema duplikata!</h3>
        <p class="text-gray-500">Nisu pronadeni duplikati proizvoda u ovoj trgovini.</p>
      </div>

      <!-- Duplicate Groups -->
      <div class="space-y-4">
        <div
          v-for="(group, groupIndex) in duplicates"
          :key="groupIndex"
          class="bg-white rounded-lg shadow-sm overflow-hidden"
          :class="{ 'opacity-50': group.merged }"
        >
          <!-- Group Header -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div>
              <span class="text-sm font-medium text-gray-900">
                {{ group.normalized_title }}
              </span>
              <span class="ml-2 text-xs px-2 py-1 rounded-full" :class="{
                'bg-green-100 text-green-800': group.match_type === 'exact',
                'bg-yellow-100 text-yellow-800': group.match_type === 'fuzzy'
              }">
                {{ group.match_type === 'exact' ? 'Identican' : `${Math.round(group.similarity * 100)}% slicnost` }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="group.merged" class="text-sm text-green-600 font-medium">Spojeno!</span>
              <button
                v-else
                @click="mergeGroup(group)"
                :disabled="isMerging"
                class="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:bg-gray-400"
              >
                Spoji u #{{ group.recommended_keep }}
              </button>
            </div>
          </div>

          <!-- Products in Group -->
          <div class="divide-y divide-gray-100">
            <div
              v-for="product in group.products"
              :key="product.id"
              class="px-6 py-4 flex items-center gap-4"
              :class="{ 'bg-green-50 border-l-4 border-green-500': product.id === group.recommended_keep }"
            >
              <!-- Product Image -->
              <div class="w-16 h-16 flex-shrink-0 bg-gray-100 rounded overflow-hidden">
                <img
                  v-if="product.image_path"
                  :src="product.image_path"
                  :alt="product.title"
                  class="w-full h-full object-contain"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>

              <!-- Product Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-gray-900">{{ product.title }}</span>
                  <span v-if="product.id === group.recommended_keep" class="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded">
                    Zadrzati
                  </span>
                </div>
                <div class="text-sm text-gray-500">
                  ID: {{ product.id }} | Kategorija: {{ product.category || 'N/A' }}
                </div>
              </div>

              <!-- Price -->
              <div class="text-right">
                <div v-if="product.discount_price && product.discount_price < product.base_price" class="text-sm">
                  <span class="text-gray-400 line-through">{{ product.base_price?.toFixed(2) }} KM</span>
                  <span class="ml-1 text-red-600 font-medium">{{ product.discount_price?.toFixed(2) }} KM</span>
                </div>
                <div v-else class="text-sm font-medium text-gray-900">
                  {{ product.base_price?.toFixed(2) }} KM
                </div>
                <div class="text-xs text-gray-400">
                  {{ product.created_at ? new Date(product.created_at).toLocaleDateString('hr') : 'N/A' }}
                </div>
              </div>

              <!-- Keep Button -->
              <button
                v-if="product.id !== group.recommended_keep && !group.merged"
                @click="setRecommendedKeep(group, product.id)"
                class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-100"
                title="Odaberi ovaj kao glavni"
              >
                Odaberi
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
  layout: 'admin',
  middleware: ['admin']
})

const config = useRuntimeConfig()
const { get, post } = useApi()

interface Product {
  id: number
  title: string
  base_price: number
  discount_price: number | null
  image_path: string | null
  category: string | null
  created_at: string | null
}

interface DuplicateGroup {
  products: Product[]
  normalized_title: string
  similarity: number
  recommended_keep: number
  match_type: 'exact' | 'fuzzy'
  merged?: boolean
}

interface Business {
  id: number
  name: string
  product_count?: number
}

const businesses = ref<Business[]>([])
const selectedBusinessId = ref<number | null>(null)
const threshold = ref(0.85)
const duplicates = ref<DuplicateGroup[]>([])
const isLoading = ref(false)
const isMerging = ref(false)
const searchPerformed = ref(false)
const notifications = ref<{ type: string; message: string }[]>([])

const totalDuplicateProducts = computed(() => {
  return duplicates.value.reduce((sum, group) => sum + group.products.length, 0)
})

// Fetch businesses on mount
onMounted(async () => {
  try {
    const data = await get('/api/businesses')
    businesses.value = data.businesses || []

    // Also get product counts for each business
    for (const business of businesses.value) {
      try {
        const productsData = await get(`/api/businesses/${business.id}/products?per_page=1`)
        business.product_count = productsData.total || 0
      } catch (e) {
        // Ignore errors
      }
    }
  } catch (e) {
    showNotification('error', 'Greska pri ucitavanju trgovina')
  }
})

async function findDuplicates() {
  if (!selectedBusinessId.value) return

  isLoading.value = true
  searchPerformed.value = true
  duplicates.value = []

  try {
    const data = await get(`/api/admin/products/duplicates/${selectedBusinessId.value}?threshold=${threshold.value}`)
    duplicates.value = data.duplicates || []

    if (duplicates.value.length > 0) {
      showNotification('info', `Pronadeno ${duplicates.value.length} grupa duplikata`)
    }
  } catch (e: any) {
    showNotification('error', e.message || 'Greska pri trazenju duplikata')
  } finally {
    isLoading.value = false
  }
}

async function mergeGroup(group: DuplicateGroup) {
  if (group.merged) return

  const mergeIds = group.products
    .filter(p => p.id !== group.recommended_keep)
    .map(p => p.id)

  if (mergeIds.length === 0) return

  isMerging.value = true

  try {
    const result = await post('/api/admin/products/merge', {
      keep_id: group.recommended_keep,
      merge_ids: mergeIds,
      delete_merged: true
    })

    if (result.success) {
      group.merged = true
      showNotification('success', `Spojeno ${result.merged_count} proizvoda u #${group.recommended_keep}`)
    } else {
      showNotification('error', result.error || 'Greska pri spajanju')
    }
  } catch (e: any) {
    showNotification('error', e.message || 'Greska pri spajanju')
  } finally {
    isMerging.value = false
  }
}

async function mergeAllRecommended() {
  const unmerged = duplicates.value.filter(g => !g.merged)
  if (unmerged.length === 0) return

  if (!confirm(`Jeste li sigurni da zelite spojiti ${unmerged.length} grupa duplikata?`)) {
    return
  }

  isMerging.value = true
  let successCount = 0
  let errorCount = 0

  for (const group of unmerged) {
    const mergeIds = group.products
      .filter(p => p.id !== group.recommended_keep)
      .map(p => p.id)

    if (mergeIds.length === 0) continue

    try {
      const result = await post('/api/admin/products/merge', {
        keep_id: group.recommended_keep,
        merge_ids: mergeIds,
        delete_merged: true
      })

      if (result.success) {
        group.merged = true
        successCount++
      } else {
        errorCount++
      }
    } catch (e) {
      errorCount++
    }
  }

  isMerging.value = false

  if (successCount > 0) {
    showNotification('success', `Uspjesno spojeno ${successCount} grupa`)
  }
  if (errorCount > 0) {
    showNotification('error', `Greska pri spajanju ${errorCount} grupa`)
  }
}

function setRecommendedKeep(group: DuplicateGroup, productId: number) {
  group.recommended_keep = productId
}

function showNotification(type: string, message: string) {
  notifications.value.push({ type, message })
  setTimeout(() => {
    notifications.value.shift()
  }, 5000)
}
</script>
