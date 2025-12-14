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
        <div class="flex items-center justify-between">
          <span class="text-sm">{{ notification.message }}</span>
          <button @click="removeNotification(index)" class="ml-2 text-current opacity-70 hover:opacity-100">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Svi proizvodi</h1>
            <p class="mt-1 text-sm text-gray-600">Pregled svih proizvoda u sistemu prema biznisom</p>
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
      <div v-if="selectedProductIds.size > 0" class="mb-6 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <span class="text-sm font-medium text-indigo-900">
              {{ selectedProductIds.size }} proizvoda odabrano
            </span>
            <button
              @click="clearSelection"
              class="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Poništi izbor
            </button>
          </div>
          <button
            @click="regenerateSelectedEmbeddings"
            :disabled="isRegenerating"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            <svg v-if="isRegenerating" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            {{ isRegenerating ? 'Regeneriram...' : 'Regeneriraj embeddings' }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <template v-else>
        <!-- Summary Stats -->
        <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno proizvoda</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_products || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Sa embeddings</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ embeddingStats.up_to_date || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Potreban refresh</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ embeddingStats.needs_refresh || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Bez embeddings</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ embeddingStats.no_embedding || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Biznisi</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_businesses || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="mb-6 flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center space-x-4">
            <span class="text-sm font-medium text-gray-700">Bulk akcije:</span>
            <button
              @click="selectAllNeedsRefresh"
              class="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Odaberi sve sa potrebnim refresh-om
            </button>
            <button
              @click="selectAllNoEmbedding"
              class="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Odaberi sve bez embeddings
            </button>
          </div>
          <div class="flex items-center space-x-3">
            <button
              @click="vectorizeAllProducts"
              :disabled="isRegenerating"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <svg v-if="isRegenerating" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <svg v-else class="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Vectorize ALL
            </button>
            <button
              @click="regenerateAllChanged"
              :disabled="isRegenerating"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <svg v-if="isRegenerating" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Regeneriraj SVE promjenjene
            </button>
          </div>
        </div>

        <!-- Products by Business -->
        <div class="space-y-8">
          <div
            v-for="businessData in businessesWithProducts"
            :key="businessData.business.id"
            class="bg-white rounded-lg border border-gray-200 overflow-hidden"
          >
            <!-- Business Header -->
            <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-medium text-gray-900">{{ businessData.business.name }}</h3>
                  <div class="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <span>{{ businessData.business.city || 'Nepoznato' }}</span>
                    <span v-if="businessData.business.contact_phone">{{ businessData.business.contact_phone }}</span>
                    <span>{{ businessData.products.length }} proizvoda</span>
                    <span class="text-purple-600">
                      {{ getCategorizationProgress(businessData) }}
                    </span>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <button
                    @click="categorizeBusinessProducts(businessData.business.id)"
                    :disabled="isCategorizingBusiness.has(businessData.business.id)"
                    class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    <svg v-if="isCategorizingBusiness.has(businessData.business.id)" class="animate-spin -ml-1 mr-1.5 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <svg v-else class="-ml-1 mr-1.5 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                    {{ isCategorizingBusiness.has(businessData.business.id) ? 'Kategoriziram...' : 'AI Kategoriziraj' }}
                  </button>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    ID: {{ businessData.business.id }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Products Table -->
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        :checked="isBusinessFullySelected(businessData.business.id)"
                        @change="toggleBusinessSelection(businessData.business.id)"
                        class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Embedding Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proizvod</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kategorija</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Osnovna cijena</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cijena sa popustom</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tagovi</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grupa</th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="product in businessData.products" :key="product.id" class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        :checked="selectedProductIds.has(product.id)"
                        @change="toggleProductSelection(product.id)"
                        class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span
                        v-if="getEmbeddingStatus(product.id) === 'no_embedding'"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                      >
                        Bez embeddings
                      </span>
                      <span
                        v-else-if="getEmbeddingStatus(product.id) === 'needs_refresh'"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
                      >
                        Potreban refresh
                      </span>
                      <span
                        v-else-if="getEmbeddingStatus(product.id) === 'up_to_date'"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                      >
                        Ažurirano
                      </span>
                      <span v-else class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Nepoznato
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm font-medium text-gray-900">{{ product.title }}</div>
                      <div class="text-xs text-gray-500">ID: {{ product.id }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {{ product.category || 'Ostalo' }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ formatPrice(product.base_price) }} KM
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                      <span v-if="hasDiscount(product)" class="text-green-600 font-medium">
                        {{ formatPrice(product.discount_price) }} KM
                      </span>
                      <span v-else class="text-gray-500">-</span>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex flex-wrap gap-1">
                        <span
                          v-for="(tag, index) in product.tags?.slice(0, 3)"
                          :key="index"
                          class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700"
                        >
                          {{ tag }}
                        </span>
                        <span
                          v-if="product.tags && product.tags.length > 3"
                          class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700"
                        >
                          +{{ product.tags.length - 3 }}
                        </span>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span
                        v-if="product.category_group"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getCategoryGroupColor(product.category_group)"
                      >
                        {{ getCategoryGroupIcon(product.category_group) }} {{ product.category_group }}
                      </span>
                      <span v-else class="text-gray-400 text-xs">-</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        @click="vectorizeSingleProduct(product.id)"
                        :disabled="isVectorizingProduct.has(product.id)"
                        class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        :title="`Vectorize product ${product.id}`"
                      >
                        <svg v-if="isVectorizingProduct.has(product.id)" class="animate-spin -ml-1 mr-1 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <svg v-else class="-ml-1 mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        {{ isVectorizingProduct.has(product.id) ? 'Vectorizing...' : 'Vectorize' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="businessesWithProducts.length === 0" class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Nema proizvoda</h3>
            <p class="mt-1 text-sm text-gray-500">Trenutno nema proizvoda u sistemu.</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const { get, post } = useApi()

// Notifications
const notifications = ref<Array<{ message: string; type: 'success' | 'error' | 'info' }>>([])

function showNotification(message: string, type: 'success' | 'error' | 'info' = 'info') {
  const notification = { message, type }
  notifications.value.push(notification)
  setTimeout(() => {
    const index = notifications.value.indexOf(notification)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }, 5000)
}

function removeNotification(index: number) {
  notifications.value.splice(index, 1)
}

const isLoading = ref(true)
const stats = ref<any>({})
const businessesWithProducts = ref<any[]>([])
const embeddingStats = ref<any>({})
const productEmbeddingStatus = ref<Map<number, string>>(new Map())
const selectedProductIds = ref<Set<number>>(new Set())
const isRegenerating = ref(false)
const isVectorizingProduct = ref<Set<number>>(new Set())
const isCategorizingBusiness = ref<Set<number>>(new Set())

// Category group helpers
const categoryGroupIcons: Record<string, string> = {
  meso: '🥩',
  mlijeko: '🥛',
  pica: '🥤',
  voce_povrce: '🥬',
  kuhinja: '🍳',
  ves: '🧺',
  ciscenje: '🧹',
  higijena: '🧴',
  slatkisi: '🍫',
  kafa: '☕',
  smrznuto: '🧊',
  pekara: '🥖',
  ljubimci: '🐕',
  bebe: '👶'
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

function getCategoryGroupIcon(group: string): string {
  return categoryGroupIcons[group] || '📦'
}

function getCategoryGroupColor(group: string): string {
  return categoryGroupColors[group] || 'bg-gray-100 text-gray-800'
}

function getCategorizationProgress(businessData: any): string {
  const total = businessData.products.length
  const categorized = businessData.products.filter((p: any) => p.category_group).length
  if (categorized === total) {
    return `✅ ${categorized}/${total} kategorizirano`
  }
  return `${categorized}/${total} kategorizirano`
}

const averageProductsPerBusiness = computed(() => {
  if (!stats.value.total_businesses || stats.value.total_businesses === 0) return 0
  return (stats.value.total_products / stats.value.total_businesses).toFixed(1)
})

onMounted(async () => {
  try {
    await loadProducts()
    // Load embedding status in background (optional, don't block UI)
    loadEmbeddingStatus().catch(e => console.log('Embedding stats not available'))
  } finally {
    isLoading.value = false
  }
})

async function loadProducts() {
  try {
    const data = await get('/api/admin/products')
    stats.value = data.stats || {}
    businessesWithProducts.value = data.businesses_with_products || []
  } catch (error) {
    console.error('Error loading products:', error)
    showNotification('Nije moguće učitati proizvode', 'error')
  }
}

async function loadEmbeddingStatus() {
  try {
    const data = await get('/api/admin/embeddings/stats')
    embeddingStats.value = data || {}

    // Load detailed status for all products
    const statusData = await get('/api/admin/embeddings/products/status?per_page=1000')
    if (statusData.products) {
      const statusMap = new Map()
      statusData.products.forEach((p: any) => {
        statusMap.set(p.id, p.status)
      })
      productEmbeddingStatus.value = statusMap
    }
  } catch (error) {
    console.error('Error loading embedding status:', error)
  }
}

function getEmbeddingStatus(productId: number): string {
  return productEmbeddingStatus.value.get(productId) || 'unknown'
}

function toggleProductSelection(productId: number) {
  if (selectedProductIds.value.has(productId)) {
    selectedProductIds.value.delete(productId)
  } else {
    selectedProductIds.value.add(productId)
  }
  // Trigger reactivity
  selectedProductIds.value = new Set(selectedProductIds.value)
}

function toggleBusinessSelection(businessId: number) {
  const business = businessesWithProducts.value.find(b => b.business.id === businessId)
  if (!business) return

  const productIds = business.products.map((p: any) => p.id)
  const allSelected = productIds.every((id: number) => selectedProductIds.value.has(id))

  if (allSelected) {
    // Deselect all
    productIds.forEach((id: number) => selectedProductIds.value.delete(id))
  } else {
    // Select all
    productIds.forEach((id: number) => selectedProductIds.value.add(id))
  }
  selectedProductIds.value = new Set(selectedProductIds.value)
}

function isBusinessFullySelected(businessId: number): boolean {
  const business = businessesWithProducts.value.find(b => b.business.id === businessId)
  if (!business || business.products.length === 0) return false

  const productIds = business.products.map((p: any) => p.id)
  return productIds.every((id: number) => selectedProductIds.value.has(id))
}

function selectAllNeedsRefresh() {
  const productsNeedingRefresh: number[] = []
  businessesWithProducts.value.forEach(business => {
    business.products.forEach((product: any) => {
      if (getEmbeddingStatus(product.id) === 'needs_refresh') {
        productsNeedingRefresh.push(product.id)
      }
    })
  })
  productsNeedingRefresh.forEach(id => selectedProductIds.value.add(id))
  selectedProductIds.value = new Set(selectedProductIds.value)

  showNotification(`Odabrano ${productsNeedingRefresh.length} proizvoda sa potrebnim refresh-om`, 'info')
}

function selectAllNoEmbedding() {
  const productsNoEmbedding: number[] = []
  businessesWithProducts.value.forEach(business => {
    business.products.forEach((product: any) => {
      if (getEmbeddingStatus(product.id) === 'no_embedding') {
        productsNoEmbedding.push(product.id)
      }
    })
  })
  productsNoEmbedding.forEach(id => selectedProductIds.value.add(id))
  selectedProductIds.value = new Set(selectedProductIds.value)

  showNotification(`Odabrano ${productsNoEmbedding.length} proizvoda bez embeddings`, 'info')
}

function clearSelection() {
  selectedProductIds.value.clear()
  selectedProductIds.value = new Set()
}

async function regenerateSelectedEmbeddings() {
  if (selectedProductIds.value.size === 0) {
    showNotification('Nije odabran nijedan proizvod', 'error')
    return
  }

  isRegenerating.value = true

  try {
    const response = await post('/api/admin/embeddings/regenerate', {
      product_ids: Array.from(selectedProductIds.value)
    })

    showNotification(`Regeneracija pokrenuta za ${selectedProductIds.value.size} proizvoda`, 'success')

    // Clear selection and reload status after a delay
    clearSelection()
    setTimeout(async () => {
      await loadEmbeddingStatus()
    }, 3000)

  } catch (error: any) {
    console.error('Error regenerating embeddings:', error)
    showNotification(error.message || 'Nije moguće regenerirati embeddings', 'error')
  } finally {
    isRegenerating.value = false
  }
}

async function regenerateAllChanged() {
  if (!confirm('Da li ste sigurni da želite regenerirati embeddings za SVE promijenjene proizvode? Ovo može potrajati.')) {
    return
  }

  isRegenerating.value = true

  try {
    const response = await post('/api/admin/embeddings/regenerate', {
      changed_only: true
    })

    showNotification('Regeneracija pokrenuta za sve promijenjene proizvode', 'success')

    // Reload status after a delay
    setTimeout(async () => {
      await loadEmbeddingStatus()
    }, 3000)

  } catch (error: any) {
    console.error('Error regenerating embeddings:', error)
    showNotification(error.message || 'Nije moguće regenerirati embeddings', 'error')
  } finally {
    isRegenerating.value = false
  }
}

async function vectorizeAllProducts() {
  if (!confirm('Da li ste sigurni da želite vectorize SVE proizvode? Ovo može potrajati i koštati kredite na OpenAI.')) {
    return
  }

  isRegenerating.value = true

  try {
    const response = await post('/api/admin/embeddings/vectorize-batch', {
      force: true
    })

    showNotification(`Vectorizovano ${response.stats?.succeeded || 0}/${response.stats?.processed || 0} proizvoda`, 'success')

    // Reload status after a delay
    setTimeout(async () => {
      await loadEmbeddingStatus()
      await loadProducts()
    }, 3000)

  } catch (error: any) {
    console.error('Error vectorizing all products:', error)
    showNotification(error.message || 'Nije moguće vectorize sve proizvode', 'error')
  } finally {
    isRegenerating.value = false
  }
}

async function vectorizeSingleProduct(productId: number) {
  isVectorizingProduct.value.add(productId)
  isVectorizingProduct.value = new Set(isVectorizingProduct.value)

  try {
    const response = await post('/api/admin/embeddings/vectorize-batch', {
      product_ids: [productId],
      force: true
    })

    showNotification(`Proizvod ${productId} je vectorizovan`, 'success')

    // Reload status for this product
    setTimeout(async () => {
      await loadEmbeddingStatus()
    }, 2000)

  } catch (error: any) {
    console.error(`Error vectorizing product ${productId}:`, error)
    showNotification(error.message || `Nije moguće vectorize proizvod ${productId}`, 'error')
  } finally {
    isVectorizingProduct.value.delete(productId)
    isVectorizingProduct.value = new Set(isVectorizingProduct.value)
  }
}

async function categorizeBusinessProducts(businessId: number) {
  isCategorizingBusiness.value.add(businessId)
  isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)

  try {
    const response = await post('/api/admin/products/categorize', {
      business_id: businessId
    })

    showNotification(response.message || `Kategorizirano ${response.categorized_count} proizvoda`, 'success')

    // If there are more products to categorize, ask if user wants to continue
    if (response.remaining_count > 0) {
      const continueCateg = confirm(`Još ${response.remaining_count} proizvoda čeka kategorizaciju. Nastaviti?`)
      if (continueCateg) {
        // Reload data first then continue
        await loadProducts()
        await categorizeBusinessProducts(businessId)
        return
      }
    }

    // Reload products to show updated categories
    await loadProducts()

  } catch (error: any) {
    console.error(`Error categorizing products for business ${businessId}:`, error)
    showNotification(error.message || 'Nije moguće kategorizirati proizvode', 'error')
  } finally {
    isCategorizingBusiness.value.delete(businessId)
    isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
  }
}

function formatPrice(price: number): string {
  return price.toFixed(2)
}

function hasDiscount(product: any): boolean {
  return product.discount_price && product.discount_price < product.base_price
}

function calculateDiscountPercent(product: any): number {
  if (!hasDiscount(product)) return 0
  return Math.round(((product.base_price - product.discount_price) / product.base_price) * 100)
}

useSeoMeta({
  title: 'Svi proizvodi - Admin - Popust.ba',
  description: 'Pregled svih proizvoda u sistemu prema biznisom',
})
</script>
