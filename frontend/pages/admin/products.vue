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

    <!-- Floating Save/Cancel Bar for pending changes -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="transform opacity-0 translate-y-4"
      enter-to-class="transform opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="transform opacity-100 translate-y-0"
      leave-to-class="transform opacity-0 translate-y-4"
    >
      <div
        v-if="hasPendingChanges"
        class="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 flex items-center gap-4 px-6 py-3 bg-white rounded-lg shadow-xl border border-gray-200"
      >
        <span class="text-sm text-gray-700">
          {{ pendingChangesCount }} promjena
        </span>
        <button
          @click="cancelAllChanges"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
        >
          Odustani
        </button>
        <button
          @click="saveAllChanges"
          :disabled="isSavingChanges"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          <span v-if="isSavingChanges">Spremam...</span>
          <span v-else>Spremi sve</span>
        </button>
      </div>
    </Transition>

    <!-- Edit Product Modal -->
    <div v-if="showEditModal && editingProduct" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <!-- Backdrop -->
        <div class="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" @click="closeEditModal"></div>

        <!-- Modal Panel -->
        <div class="relative z-10 w-full max-w-2xl overflow-hidden text-left bg-white rounded-lg shadow-xl transform transition-all">
          <!-- Header -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-medium text-gray-900">Uredi proizvod #{{ editingProduct.id }}</h3>
              <button @click="closeEditModal" class="text-gray-400 hover:text-gray-500">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="px-6 py-4">
            <!-- Product Image and Title -->
            <div class="flex gap-6 mb-6">
              <!-- Image -->
              <div class="flex-shrink-0">
                <div class="w-40 h-40 bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    v-if="editingProduct.image_path"
                    :src="getProductImageUrl(editingProduct.image_path)"
                    :alt="editingProduct.title"
                    class="w-full h-full object-contain"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                    <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>
              <!-- Title and Price -->
              <div class="flex-grow">
                <h4 class="text-lg font-medium text-gray-900 mb-2">{{ editingProduct.title }}</h4>
                <div class="text-sm text-gray-500 mb-2">
                  <span class="font-medium">Cijena:</span> {{ formatPrice(editingProduct.base_price) }} KM
                  <span v-if="hasDiscount(editingProduct)" class="ml-2 text-green-600 font-medium">
                    ({{ formatPrice(editingProduct.discount_price) }} KM)
                  </span>
                </div>
                <div class="text-sm text-gray-500">
                  <span class="font-medium">Match key:</span>
                  <code class="ml-1 px-2 py-0.5 bg-gray-100 rounded text-xs">{{ editingProduct.match_key || 'N/A' }}</code>
                </div>
              </div>
            </div>

            <!-- Edit Fields -->
            <div class="grid grid-cols-2 gap-4">
              <!-- Brand -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                <input
                  v-model="editingProduct.brand"
                  type="text"
                  class="w-full px-3 py-2 text-gray-900 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="npr. Menprom"
                />
              </div>

              <!-- Product Type -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Tip proizvoda</label>
                <input
                  v-model="editingProduct.product_type"
                  type="text"
                  class="w-full px-3 py-2 text-gray-900 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="npr. sudzuk"
                />
              </div>

              <!-- Size Value -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Velicina (broj)</label>
                <input
                  v-model="editingProduct.size_value"
                  type="number"
                  step="0.01"
                  class="w-full px-3 py-2 text-gray-900 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="npr. 300"
                />
              </div>

              <!-- Size Unit -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Jedinica</label>
                <input
                  v-model="editingProduct.size_unit"
                  type="text"
                  class="w-full px-3 py-2 text-gray-900 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="npr. g, ml, kom"
                />
              </div>

              <!-- Category Group -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Kategorija</label>
                <select
                  v-model="editingProduct.category_group"
                  class="w-full px-3 py-2 text-gray-900 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">-</option>
                  <option value="meso">meso</option>
                  <option value="mlijeko">mlijeko</option>
                  <option value="pica">pica</option>
                  <option value="voce_povrce">voce_povrce</option>
                  <option value="kuhinja">kuhinja</option>
                  <option value="ves">ves</option>
                  <option value="ciscenje">ciscenje</option>
                  <option value="higijena">higijena</option>
                  <option value="slatkisi">slatkisi</option>
                  <option value="kafa">kafa</option>
                  <option value="smrznuto">smrznuto</option>
                  <option value="pekara">pekara</option>
                  <option value="ljubimci">ljubimci</option>
                  <option value="bebe">bebe</option>
                  <option value="ostalo">ostalo</option>
                </select>
              </div>

              <!-- Variant -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Varijanta</label>
                <input
                  v-model="editingProduct.variant"
                  type="text"
                  class="w-full px-3 py-2 text-gray-900 border border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="npr. crveni, xxl"
                />
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
            <button
              @click="closeEditModal"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Odustani
            </button>
            <button
              @click="saveEditedProduct"
              :disabled="isUpdatingProduct.has(editingProduct.id)"
              class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <span v-if="isUpdatingProduct.has(editingProduct.id)">Spremam...</span>
              <span v-else>Spremi</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Related Products Modal -->
    <div v-if="showRelatedModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <!-- Backdrop -->
        <div class="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" @click="closeRelatedModal"></div>

        <!-- Modal Panel -->
        <div class="relative z-10 w-full max-w-4xl overflow-hidden text-left bg-white rounded-lg shadow-xl transform transition-all">
          <!-- Header -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-medium text-gray-900">{{ relatedModalTitle }}</h3>
              <button @click="closeRelatedModal" class="text-gray-400 hover:text-gray-500">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <!-- Source product info -->
            <div v-if="relatedSourceProduct" class="mt-2 text-sm text-gray-600">
              <span class="font-medium">Source:</span> {{ relatedSourceProduct.brand }} - {{ relatedSourceProduct.product_type }}
              <span v-if="relatedSourceProduct.size_value"> | {{ relatedSourceProduct.size_value }}{{ relatedSourceProduct.size_unit }}</span>
              <span class="ml-2 text-xs text-gray-400">match_key: {{ relatedSourceProduct.match_key }}</span>
            </div>
          </div>

          <!-- Body -->
          <div class="px-6 py-4 max-h-96 overflow-y-auto">
            <!-- Loading -->
            <div v-if="isLoadingRelated" class="flex items-center justify-center py-8">
              <svg class="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span class="ml-3 text-gray-600">Ucitavanje...</span>
            </div>

            <!-- Empty state -->
            <div v-else-if="relatedProducts.length === 0" class="text-center py-8 text-gray-500">
              Nema povezanih proizvoda.
            </div>

            <!-- Products table -->
            <table v-else class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Slika</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Proizvod</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Biznis</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Velicina</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cijena</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="product in relatedProducts" :key="product.id" class="hover:bg-gray-50">
                  <td class="px-4 py-2 whitespace-nowrap">
                    <div class="w-12 h-12 bg-gray-100 rounded overflow-hidden">
                      <img
                        v-if="product.image_path"
                        :src="getProductImageUrl(product.image_path)"
                        :alt="product.title"
                        class="w-full h-full object-contain"
                      />
                      <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    </div>
                  </td>
                  <td class="px-4 py-2">
                    <div class="text-sm font-medium text-gray-900 max-w-xs truncate" :title="product.title">{{ product.title }}</div>
                    <div class="text-xs text-gray-500">ID: {{ product.id }} | {{ product.brand }} - {{ product.product_type }}</div>
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap">
                    <span class="text-sm text-gray-900">{{ product.business_name }}</span>
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap">
                    <span class="text-sm text-gray-900">
                      {{ product.size_value }}{{ product.size_unit }}
                    </span>
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap">
                    <div class="text-sm text-gray-900">{{ formatPrice(product.base_price) }} KM</div>
                    <div v-if="product.discount_price && product.discount_price < product.base_price" class="text-xs text-green-600 font-medium">
                      {{ formatPrice(product.discount_price) }} KM
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
            <span class="text-sm text-gray-500">{{ relatedProducts.length }} proizvoda</span>
            <button
              @click="closeRelatedModal"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Zatvori
            </button>
          </div>
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

      <!-- Filters -->
      <div class="mb-6 bg-white rounded-lg border border-gray-200 p-4">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700">Biznis:</label>
            <select
              v-model="selectedBusinessFilter"
              @change="loadProducts(true)"
              class="block w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option :value="null">Svi biznisi</option>
              <option v-for="business in allBusinesses" :key="business.id" :value="business.id">
                {{ business.name }}
              </option>
            </select>
          </div>
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700">Status:</label>
            <select
              v-model="categorizationFilter"
              @change="loadProducts(true)"
              class="block w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="all">Svi proizvodi</option>
              <option value="uncategorized">Nekategorizirani</option>
              <option value="no_matches">Bez matcheva (0)</option>
              <option value="has_matches">Sa matchevima (1+)</option>
            </select>
          </div>
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700">Pretraga:</label>
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text"
              placeholder="Brand, tip, naziv..."
              class="block w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
          <span class="text-sm text-gray-500">
            ({{ stats.total_products }} proizvoda)
          </span>
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
                  <!-- Categorization buttons group -->
                  <div class="inline-flex rounded-md shadow-sm">
                    <button
                      @click="categorizeBusinessProducts(businessData.business.id, false)"
                      :disabled="isCategorizingBusiness.has(businessData.business.id)"
                      class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-l-md text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      title="Kategoriziraj samo proizvode kojima nedostaju podaci"
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
                    <button
                      @click="categorizeBusinessProducts(businessData.business.id, true)"
                      :disabled="isCategorizingBusiness.has(businessData.business.id)"
                      class="inline-flex items-center px-2 py-1.5 border-l border-purple-400 text-xs font-medium rounded-r-md text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      title="Forsiraj re-kategorizaciju SVIH proizvoda (prepisuje postojece)"
                    >
                      <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
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
                    <th class="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        :checked="isBusinessFullySelected(businessData.business.id)"
                        @change="toggleBusinessSelection(businessData.business.id)"
                        class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proizvod</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Matches</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Brand</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tip</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Velicina</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grupa</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cijena</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="product in businessData.products" :key="product.id" class="hover:bg-gray-50">
                    <!-- Checkbox -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <input
                        type="checkbox"
                        :checked="selectedProductIds.has(product.id)"
                        @change="toggleProductSelection(product.id)"
                        class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    </td>
                    <!-- Product Name + Image -->
                    <td class="px-4 py-3">
                      <div class="text-sm font-medium text-gray-900 max-w-xs truncate" :title="product.title">{{ product.title }}</div>
                      <div class="text-xs text-gray-500 mb-2">ID: {{ product.id }}</div>

                      <!-- Current Image + Suggestions -->
                      <div class="mt-2">
                        <!-- Main image -->
                        <div
                          class="w-[100px] h-[100px] bg-gray-100 rounded-lg overflow-hidden border-2 border-dashed border-gray-300 cursor-pointer hover:border-indigo-400 transition-colors"
                          @click="loadImageSuggestions(product)"
                          :title="product.image_path ? 'Klikni za prijedloge slika' : 'Klikni za pretragu slika'"
                        >
                          <img
                            v-if="product.image_path"
                            :src="getProductImageUrl(product.image_path)"
                            :alt="product.title"
                            class="w-full h-full object-contain"
                          />
                          <div v-else class="w-full h-full flex flex-col items-center justify-center text-gray-400">
                            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <span class="text-xs mt-1">Klikni</span>
                          </div>
                        </div>

                        <!-- Image Suggestions (below main image) -->
                        <div v-if="imageSuggestions[product.id] !== undefined" class="mt-2">
                          <!-- Loading state -->
                          <div v-if="isLoadingImageSuggestions.has(product.id)" class="flex items-center gap-2 text-xs text-gray-500">
                            <svg class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Tražim...
                          </div>

                          <!-- Suggestions row -->
                          <div v-else-if="imageSuggestions[product.id]?.length > 0" class="flex gap-2 flex-wrap">
                            <div
                              v-for="(img, idx) in imageSuggestions[product.id]"
                              :key="idx"
                              class="w-[100px] h-[100px] bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-indigo-500 transition-all flex-shrink-0"
                              :class="{ 'ring-2 ring-green-500': isSettingImage[product.id] === idx }"
                              @click="setProductImage(product, img, idx)"
                              :title="'Postavi kao sliku proizvoda'"
                            >
                              <img
                                :src="img"
                                :alt="'Suggestion ' + (idx + 1)"
                                class="w-full h-full object-contain"
                                @error="handleImageError($event, product.id, idx)"
                              />
                            </div>
                            <!-- Refresh button -->
                            <div
                              class="w-[100px] h-[100px] bg-gray-200 rounded-lg cursor-pointer hover:bg-gray-300 transition-colors flex items-center justify-center flex-shrink-0"
                              @click="loadImageSuggestions(product)"
                              title="Učitaj druge slike"
                            >
                              <svg class="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                              </svg>
                            </div>
                          </div>

                          <!-- No results -->
                          <div v-else-if="imageSuggestions[product.id]?.length === 0" class="text-xs text-gray-400">
                            Nema slika
                          </div>
                        </div>
                      </div>
                    </td>
                    <!-- Match & Sibling Counts -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <div class="flex flex-col gap-1">
                        <!-- Match count (exact clones) -->
                        <button
                          v-if="product.match_count > 0"
                          @click="showRelatedProducts(product, 'matches')"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 hover:bg-green-200 cursor-pointer transition-colors"
                          :title="'Exact matches: ' + product.match_key"
                        >
                          {{ product.match_count }} clone{{ product.match_count > 1 ? 's' : '' }}
                        </button>
                        <span
                          v-else-if="product.match_key"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500"
                          :title="product.match_key"
                        >
                          0 clones
                        </span>
                        <!-- Sibling count (same brand+type, any size) -->
                        <button
                          v-if="product.sibling_count > 0"
                          @click="showRelatedProducts(product, 'siblings')"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer transition-colors"
                          :title="'Siblings (any size): ' + product.brand + ':' + product.product_type"
                        >
                          {{ product.sibling_count }} sibling{{ product.sibling_count > 1 ? 's' : '' }}
                        </button>
                        <span
                          v-else-if="product.brand && product.product_type"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500"
                        >
                          0 siblings
                        </span>
                        <!-- Alternative count (same product_type + size, different brand) -->
                        <button
                          v-if="product.alternative_count > 0"
                          @click="showRelatedProducts(product, 'alternatives')"
                          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 hover:bg-purple-200 cursor-pointer transition-colors"
                          :title="'Alternative brands for ' + product.product_type + ' ' + product.size_value + product.size_unit"
                        >
                          {{ product.alternative_count }} alt
                        </button>
                        <span v-if="!product.match_key && !product.brand && !product.product_type" class="text-gray-400 text-xs" title="Nedostaju podaci za matching">-</span>
                      </div>
                    </td>
                    <!-- Brand (editable) -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <input
                        type="text"
                        :value="pendingChanges[product.id]?.brand ?? product.brand ?? ''"
                        @input="trackChange(product.id, 'brand', ($event.target as HTMLInputElement).value, product.brand)"
                        @keyup.enter="($event.target as HTMLInputElement).blur()"
                        class="w-24 text-xs text-gray-900 border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        :class="{
                          'bg-red-50 border-red-300': !product.brand || product.brand === 'unknown',
                          'bg-yellow-50 border-yellow-400': pendingChanges[product.id]?.brand !== undefined
                        }"
                        placeholder="brand"
                      />
                    </td>
                    <!-- Product Type (editable) -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <input
                        type="text"
                        :value="pendingChanges[product.id]?.product_type ?? product.product_type ?? ''"
                        @input="trackChange(product.id, 'product_type', ($event.target as HTMLInputElement).value, product.product_type)"
                        @keyup.enter="($event.target as HTMLInputElement).blur()"
                        class="w-24 text-xs text-gray-900 border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        :class="{
                          'bg-red-50 border-red-300': !product.product_type || product.product_type === 'unknown',
                          'bg-yellow-50 border-yellow-400': pendingChanges[product.id]?.product_type !== undefined
                        }"
                        placeholder="tip"
                      />
                    </td>
                    <!-- Size (editable) -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <div class="flex items-center space-x-1">
                        <input
                          type="number"
                          step="0.01"
                          :value="pendingChanges[product.id]?.size_value ?? product.size_value ?? ''"
                          @input="trackChange(product.id, 'size_value', ($event.target as HTMLInputElement).value, product.size_value)"
                          @keyup.enter="($event.target as HTMLInputElement).blur()"
                          class="w-16 text-xs text-gray-900 border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          :class="{
                            'bg-red-50 border-red-300': !product.size_value || product.size_value === 0,
                            'bg-yellow-50 border-yellow-400': pendingChanges[product.id]?.size_value !== undefined
                          }"
                          placeholder="0"
                        />
                        <input
                          type="text"
                          :value="pendingChanges[product.id]?.size_unit ?? product.size_unit ?? ''"
                          @input="trackChange(product.id, 'size_unit', ($event.target as HTMLInputElement).value, product.size_unit)"
                          @keyup.enter="($event.target as HTMLInputElement).blur()"
                          class="w-12 text-xs text-gray-900 border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          :class="{
                            'bg-red-50 border-red-300': !product.size_unit || product.size_unit === 'unknown',
                            'bg-yellow-50 border-yellow-400': pendingChanges[product.id]?.size_unit !== undefined
                          }"
                          placeholder="g/ml"
                        />
                      </div>
                    </td>
                    <!-- Category Group (editable dropdown) -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <select
                        :value="pendingChanges[product.id]?.category_group ?? product.category_group ?? ''"
                        @change="trackChange(product.id, 'category_group', ($event.target as HTMLSelectElement).value, product.category_group)"
                        class="text-xs text-gray-900 border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        :class="{
                          'bg-red-50 border-red-300': !product.category_group,
                          'bg-yellow-50 border-yellow-400': pendingChanges[product.id]?.category_group !== undefined
                        }"
                      >
                        <option value="">-</option>
                        <option value="meso">meso</option>
                        <option value="mlijeko">mlijeko</option>
                        <option value="pica">pica</option>
                        <option value="voce_povrce">voce_povrce</option>
                        <option value="kuhinja">kuhinja</option>
                        <option value="ves">ves</option>
                        <option value="ciscenje">ciscenje</option>
                        <option value="higijena">higijena</option>
                        <option value="slatkisi">slatkisi</option>
                        <option value="kafa">kafa</option>
                        <option value="smrznuto">smrznuto</option>
                        <option value="pekara">pekara</option>
                        <option value="ljubimci">ljubimci</option>
                        <option value="bebe">bebe</option>
                        <option value="ostalo">ostalo</option>
                      </select>
                    </td>
                    <!-- Price -->
                    <td class="px-4 py-3 whitespace-nowrap text-xs">
                      <div class="text-gray-900">{{ formatPrice(product.base_price) }} KM</div>
                      <div v-if="hasDiscount(product)" class="text-green-600 font-medium">
                        {{ formatPrice(product.discount_price) }} KM
                      </div>
                    </td>
                    <!-- Actions -->
                    <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium space-x-1">
                      <!-- Edit button -->
                      <button
                        @click="openEditModal(product)"
                        class="inline-flex items-center px-2 py-1 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        title="Uredi proizvod"
                      >
                        <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <!-- Vectorize button -->
                      <button
                        @click="vectorizeSingleProduct(product.id)"
                        :disabled="isVectorizingProduct.has(product.id)"
                        class="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        :title="`Vectorize product ${product.id}`"
                      >
                        <svg v-if="isVectorizingProduct.has(product.id)" class="animate-spin h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <svg v-else class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
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

          <!-- Pagination Controls -->
          <div v-if="totalPages > 1" class="mt-6 flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-sm text-gray-700">
              Prikazano {{ (currentPage - 1) * perPage + 1 }}-{{ Math.min(currentPage * perPage, totalProducts) }} od {{ totalProducts }} proizvoda
            </div>
            <div class="flex items-center space-x-2">
              <!-- First page -->
              <button
                @click="goToPage(1)"
                :disabled="currentPage === 1"
                class="px-3 py-1 text-sm font-medium border rounded-md transition-colors"
                :class="currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
              >
                &laquo;
              </button>
              <!-- Previous page -->
              <button
                @click="goToPage(currentPage - 1)"
                :disabled="currentPage === 1"
                class="px-3 py-1 text-sm font-medium border rounded-md transition-colors"
                :class="currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
              >
                &lsaquo;
              </button>
              <!-- Page numbers -->
              <template v-for="page in paginationPages" :key="page">
                <span v-if="page === '...'" class="px-2 text-gray-400">...</span>
                <button
                  v-else
                  @click="goToPage(page as number)"
                  class="px-3 py-1 text-sm font-medium border rounded-md transition-colors"
                  :class="currentPage === page ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
                >
                  {{ page }}
                </button>
              </template>
              <!-- Next page -->
              <button
                @click="goToPage(currentPage + 1)"
                :disabled="currentPage === totalPages"
                class="px-3 py-1 text-sm font-medium border rounded-md transition-colors"
                :class="currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
              >
                &rsaquo;
              </button>
              <!-- Last page -->
              <button
                @click="goToPage(totalPages)"
                :disabled="currentPage === totalPages"
                class="px-3 py-1 text-sm font-medium border rounded-md transition-colors"
                :class="currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
              >
                &raquo;
              </button>
              <!-- Per page selector -->
              <select
                v-model="perPage"
                @change="loadProducts(true)"
                class="ml-4 text-sm border-gray-300 rounded-md focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option :value="25">25 po stranici</option>
                <option :value="50">50 po stranici</option>
                <option :value="100">100 po stranici</option>
                <option :value="200">200 po stranici</option>
              </select>
            </div>
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

const { get, post, patch } = useApi()

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
const allBusinesses = ref<Array<{ id: number; name: string }>>([])
const selectedBusinessFilter = ref<number | null>(null)
const categorizationFilter = ref<string>('all')
const searchQuery = ref<string>('')
const embeddingStats = ref<any>({})

// Pagination state
const currentPage = ref(1)
const perPage = ref(50)
const totalProducts = ref(0)
const totalPages = ref(0)
const productEmbeddingStatus = ref<Map<number, string>>(new Map())
const selectedProductIds = ref<Set<number>>(new Set())
const isRegenerating = ref(false)
const isVectorizingProduct = ref<Set<number>>(new Set())
const isCategorizingBusiness = ref<Set<number>>(new Set())
const isUpdatingProduct = ref<Set<number>>(new Set())
const editingProduct = ref<any>(null)
const showEditModal = ref(false)
const showRelatedModal = ref(false)
const relatedProducts = ref<any[]>([])
const relatedModalTitle = ref('')
const relatedSourceProduct = ref<any>(null)
const isLoadingRelated = ref(false)

// Image suggestions state
const imageSuggestions = ref<Record<number, string[]>>({})
const isLoadingImageSuggestions = ref<Set<number>>(new Set())
const isSettingImage = ref<Record<number, number | null>>({})
const imageSearchAttempts = ref<Record<number, number>>({})

// Pending changes state for inline editing
const pendingChanges = ref<Record<number, Record<string, any>>>({})
const isSavingChanges = ref(false)

// Computed for pending changes
const hasPendingChanges = computed(() => Object.keys(pendingChanges.value).length > 0)
const pendingChangesCount = computed(() => {
  let count = 0
  for (const productId in pendingChanges.value) {
    count += Object.keys(pendingChanges.value[productId]).length
  }
  return count
})

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
  // Fully categorized = has category_group AND all matching fields (product_type, size_value, size_unit)
  // Note: brand is optional (can be null for products without a known brand)
  const fullyCategorized = businessData.products.filter((p: any) =>
    p.category_group &&
    p.product_type &&
    p.size_value !== null && p.size_value !== undefined &&
    p.size_unit
  ).length
  if (fullyCategorized === total) {
    return `✅ ${fullyCategorized}/${total} kategorizirano`
  }
  return `${fullyCategorized}/${total} kategorizirano`
}

const averageProductsPerBusiness = computed(() => {
  if (!stats.value.total_businesses || stats.value.total_businesses === 0) return 0
  return (stats.value.total_products / stats.value.total_businesses).toFixed(1)
})

// Compute visible page numbers with ellipsis
const paginationPages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    // Show all pages if 7 or less
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // Always show first page
    pages.push(1)

    if (current > 3) {
      pages.push('...')
    }

    // Show pages around current
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (current < total - 2) {
      pages.push('...')
    }

    // Always show last page
    pages.push(total)
  }

  return pages
})

onMounted(async () => {
  try {
    await loadProducts()
    // Note: loadEmbeddingStatus requires /api/admin/embeddings/stats endpoint which may not exist
    // Silently skip if not available
  } finally {
    isLoading.value = false
  }
})

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadProducts(true) // Reset to page 1 on new search
  }, 300)
}

async function loadProducts(resetPage: boolean = false) {
  try {
    if (resetPage) {
      currentPage.value = 1
    }

    // Build URL with filters and pagination
    const params = new URLSearchParams()
    params.append('page', String(currentPage.value))
    params.append('per_page', String(perPage.value))
    if (selectedBusinessFilter.value) {
      params.append('business_id', String(selectedBusinessFilter.value))
    }
    if (categorizationFilter.value && categorizationFilter.value !== 'all') {
      params.append('categorization_filter', categorizationFilter.value)
    }
    if (searchQuery.value && searchQuery.value.trim()) {
      params.append('search', searchQuery.value.trim())
    }
    const url = '/api/admin/products?' + params.toString()
    const data = await get(url)

    // Update pagination info
    if (data.pagination) {
      totalProducts.value = data.pagination.total
      totalPages.value = data.pagination.total_pages
    }

    stats.value = data.stats || {}

    // Group flat products by business for display
    const productsFlat = data.products || []
    const groupedByBusiness = new Map<number, { business: any; products: any[] }>()

    for (const product of productsFlat) {
      const businessId = product.business_id
      if (!groupedByBusiness.has(businessId)) {
        groupedByBusiness.set(businessId, {
          business: {
            id: businessId,
            name: product.business_name,
            logo: product.business_logo
          },
          products: []
        })
      }
      groupedByBusiness.get(businessId)!.products.push(product)
    }

    businessesWithProducts.value = Array.from(groupedByBusiness.values())

    // Only update allBusinesses on first load (when not filtered)
    if (data.all_businesses && (!allBusinesses.value.length || !selectedBusinessFilter.value)) {
      allBusinesses.value = data.all_businesses
    }
  } catch (error) {
    console.error('Error loading products:', error)
    showNotification('Nije moguće učitati proizvode', 'error')
  }
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadProducts()
  }
}

async function updateProductField(productId: number, field: string, value: string) {
  if (isUpdatingProduct.value.has(productId)) return

  isUpdatingProduct.value.add(productId)
  isUpdatingProduct.value = new Set(isUpdatingProduct.value)

  try {
    const response = await patch(`/api/admin/products/${productId}/categorization`, {
      [field]: value
    })

    if (response.success) {
      // Update the local product data
      for (const business of businessesWithProducts.value) {
        const product = business.products.find((p: any) => p.id === productId)
        if (product) {
          product[field] = response.product[field]
          product.match_key = response.product.match_key
          break
        }
      }
      showNotification(`Proizvod ${productId} ažuriran`, 'success')
    }
  } catch (error: any) {
    console.error(`Error updating product ${productId}:`, error)
    showNotification(error.message || 'Nije moguće ažurirati proizvod', 'error')
  } finally {
    isUpdatingProduct.value.delete(productId)
    isUpdatingProduct.value = new Set(isUpdatingProduct.value)
  }
}

// Track changes for inline editing (floating save bar)
function trackChange(productId: number, field: string, newValue: string, originalValue: any) {
  const normalizedNew = newValue?.toString().trim() || ''
  const normalizedOriginal = originalValue?.toString().trim() || ''

  if (normalizedNew === normalizedOriginal) {
    // Value reverted to original, remove from pending changes
    if (pendingChanges.value[productId]) {
      delete pendingChanges.value[productId][field]
      if (Object.keys(pendingChanges.value[productId]).length === 0) {
        delete pendingChanges.value[productId]
      }
      pendingChanges.value = { ...pendingChanges.value }
    }
  } else {
    // Track the change
    if (!pendingChanges.value[productId]) {
      pendingChanges.value[productId] = {}
    }
    pendingChanges.value[productId][field] = newValue
    pendingChanges.value = { ...pendingChanges.value }
  }
}

function cancelAllChanges() {
  pendingChanges.value = {}
  // Force re-render by reloading products (since we need to reset input values)
  loadProducts()
}

async function saveAllChanges() {
  if (!hasPendingChanges.value) return

  isSavingChanges.value = true
  let successCount = 0
  let errorCount = 0

  try {
    const productIds = Object.keys(pendingChanges.value).map(Number)

    for (const productId of productIds) {
      const changes = pendingChanges.value[productId]
      if (!changes || Object.keys(changes).length === 0) continue

      try {
        const response = await patch(`/api/admin/products/${productId}/categorization`, changes)

        if (response.success) {
          // Update the local product data
          for (const business of businessesWithProducts.value) {
            const product = business.products.find((p: any) => p.id === productId)
            if (product) {
              for (const [field, value] of Object.entries(changes)) {
                product[field] = response.product[field]
              }
              product.match_key = response.product.match_key
              break
            }
          }
          successCount++
        } else {
          errorCount++
        }
      } catch (error) {
        console.error(`Error updating product ${productId}:`, error)
        errorCount++
      }
    }

    // Clear pending changes
    pendingChanges.value = {}

    if (errorCount === 0) {
      showNotification(`Spremljeno ${successCount} proizvoda`, 'success')
    } else {
      showNotification(`Spremljeno ${successCount}, neuspješno ${errorCount}`, 'error')
    }
  } catch (error: any) {
    console.error('Error saving changes:', error)
    showNotification(error.message || 'Greška pri spremanju', 'error')
  } finally {
    isSavingChanges.value = false
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

// Track categorization job IDs per business
const categorizationJobs = ref<Map<number, string>>(new Map())

async function categorizeBusinessProducts(businessId: number, force: boolean = false) {
  if (force && !confirm('Da li ste sigurni da zelite RE-kategorizirati SVE proizvode? Ovo ce prepisati postojece vrijednosti.')) {
    return
  }

  isCategorizingBusiness.value.add(businessId)
  isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)

  try {
    const response = await post('/api/admin/products/categorize', {
      business_id: businessId,
      force: force
    })

    if (response.status === 'no_products') {
      showNotification('Nema proizvoda za kategorizaciju', 'info')
      isCategorizingBusiness.value.delete(businessId)
      isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
      return
    }

    if (response.status === 'already_running') {
      showNotification('Kategorizacija je već u toku za ovaj biznis', 'info')
      categorizationJobs.value.set(businessId, response.job_id)
      // Start polling for this job
      pollCategorizationStatus(businessId, response.job_id)
      return
    }

    if (response.job_id) {
      showNotification(`Kategorizacija pokrenuta u pozadini za ${response.remaining} proizvoda. Ne blokira server.`, 'success')
      categorizationJobs.value.set(businessId, response.job_id)
      // Start polling for status
      pollCategorizationStatus(businessId, response.job_id)
    }

  } catch (error: any) {
    console.error(`Error starting categorization for business ${businessId}:`, error)
    showNotification(error.message || 'Nije moguće pokrenuti kategorizaciju', 'error')
    isCategorizingBusiness.value.delete(businessId)
    isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
  }
}

async function pollCategorizationStatus(businessId: number, jobId: string) {
  try {
    const response = await get(`/api/admin/products/categorize/status/${jobId}`)

    if (response.status === 'running') {
      // Show progress notification every 30 seconds
      const processed = response.processed || 0
      const remaining = response.remaining || 0
      console.log(`Kategorization progress: ${processed} processed, ${remaining} remaining`)

      // Continue polling every 10 seconds
      setTimeout(() => pollCategorizationStatus(businessId, jobId), 10000)
    } else if (response.status === 'completed') {
      showNotification(`Kategorizacija završena! Obrađeno ${response.processed} proizvoda.`, 'success')
      isCategorizingBusiness.value.delete(businessId)
      isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
      categorizationJobs.value.delete(businessId)
      await loadProducts()
    } else if (response.status === 'error' || response.status === 'cancelled') {
      showNotification(`Kategorizacija ${response.status === 'cancelled' ? 'otkazana' : 'prekinuta'}`, 'error')
      isCategorizingBusiness.value.delete(businessId)
      isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
      categorizationJobs.value.delete(businessId)
    }
  } catch (error) {
    console.error('Error polling categorization status:', error)
    // Continue polling even on error
    setTimeout(() => pollCategorizationStatus(businessId, jobId), 10000)
  }
}

function formatPrice(price: number): string {
  return price.toFixed(2)
}

function openEditModal(product: any) {
  editingProduct.value = { ...product }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  editingProduct.value = null
}

async function saveEditedProduct() {
  if (!editingProduct.value) return

  const productId = editingProduct.value.id
  isUpdatingProduct.value.add(productId)
  isUpdatingProduct.value = new Set(isUpdatingProduct.value)

  try {
    const response = await patch(`/api/admin/products/${productId}/categorization`, {
      brand: editingProduct.value.brand,
      product_type: editingProduct.value.product_type,
      size_value: editingProduct.value.size_value,
      size_unit: editingProduct.value.size_unit,
      category_group: editingProduct.value.category_group,
      variant: editingProduct.value.variant
    })

    if (response.success) {
      // Update the local product data in the list
      for (const business of businessesWithProducts.value) {
        const product = business.products.find((p: any) => p.id === productId)
        if (product) {
          product.brand = response.product.brand
          product.product_type = response.product.product_type
          product.size_value = response.product.size_value
          product.size_unit = response.product.size_unit
          product.category_group = response.product.category_group
          product.variant = response.product.variant
          product.match_key = response.product.match_key
          break
        }
      }
      showNotification('Proizvod uspjesno azuriran', 'success')
      closeEditModal()
    }
  } catch (error: any) {
    console.error(`Error updating product ${productId}:`, error)
    showNotification(error.message || 'Nije moguce azurirati proizvod', 'error')
  } finally {
    isUpdatingProduct.value.delete(productId)
    isUpdatingProduct.value = new Set(isUpdatingProduct.value)
  }
}

function getProductImageUrl(imagePath: string | null): string {
  if (!imagePath) return ''
  if (imagePath.startsWith('http')) return imagePath
  // For S3 images, construct the full URL
  return `https://popust-ba.s3.eu-central-1.amazonaws.com/${imagePath}`
}

// Image suggestion functions
async function loadImageSuggestions(product: any) {
  const productId = product.id

  // Increment attempt counter for query variation
  const attempt = (imageSearchAttempts.value[productId] || 0) + 1
  imageSearchAttempts.value[productId] = attempt

  // Initialize the suggestions array for this product to trigger the loading UI
  imageSuggestions.value[productId] = []
  isLoadingImageSuggestions.value.add(productId)
  isLoadingImageSuggestions.value = new Set(isLoadingImageSuggestions.value)

  try {
    const data = await get(`/api/admin/products/${productId}/suggest-images?attempt=${attempt}`)
    imageSuggestions.value[productId] = data.images || []
  } catch (error: any) {
    console.error('Error loading image suggestions:', error)
    showNotification(error.message || 'Greška pri učitavanju slika', 'error')
    imageSuggestions.value[productId] = []
  } finally {
    isLoadingImageSuggestions.value.delete(productId)
    isLoadingImageSuggestions.value = new Set(isLoadingImageSuggestions.value)
  }
}

async function setProductImage(product: any, imageUrl: string, idx: number) {
  const productId = product.id
  isSettingImage.value[productId] = idx

  try {
    await post(`/api/admin/products/${productId}/set-image`, { image_url: imageUrl })

    // Update the product in the local state
    for (const businessData of businessesWithProducts.value) {
      const productIndex = businessData.products.findIndex((p: any) => p.id === productId)
      if (productIndex !== -1) {
        businessData.products[productIndex].image_path = imageUrl
        break
      }
    }

    showNotification('Slika je uspješno postavljena', 'success')

    // Clear the suggestions for this product
    delete imageSuggestions.value[productId]
  } catch (error: any) {
    console.error('Error setting product image:', error)
    showNotification(error.message || 'Greška pri postavljanju slike', 'error')
  } finally {
    isSettingImage.value[productId] = null
  }
}

function handleImageError(event: Event, productId: number, idx: number) {
  // Remove the broken image from suggestions
  const images = imageSuggestions.value[productId]
  if (images && images[idx]) {
    images.splice(idx, 1)
    imageSuggestions.value[productId] = [...images]
  }
}

function hasDiscount(product: any): boolean {
  return product.discount_price && product.discount_price < product.base_price
}

async function showRelatedProducts(product: any, type: 'matches' | 'siblings' | 'alternatives') {
  isLoadingRelated.value = true
  relatedSourceProduct.value = product
  if (type === 'matches') {
    relatedModalTitle.value = `Clones of "${product.title}" (exact match_key)`
  } else if (type === 'siblings') {
    relatedModalTitle.value = `Siblings of "${product.title}" (same brand+type, any size)`
  } else {
    relatedModalTitle.value = `Alternatives to "${product.title}" (same type+size, different brand)`
  }
  showRelatedModal.value = true
  relatedProducts.value = []

  try {
    const data = await get(`/api/admin/products/${product.id}/related?type=${type}`)
    relatedProducts.value = data.related_products || []
  } catch (error: any) {
    console.error('Error loading related products:', error)
    showNotification(error.message || 'Nije moguce ucitati povezane proizvode', 'error')
  } finally {
    isLoadingRelated.value = false
  }
}

function closeRelatedModal() {
  showRelatedModal.value = false
  relatedProducts.value = []
  relatedSourceProduct.value = null
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
