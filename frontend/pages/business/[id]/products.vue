<template>
  <div class="bg-gray-50 py-8 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">{{ business?.name }}</h1>
            <p class="text-gray-600">Upravljanje proizvodima</p>
          </div>
          <NuxtLink
            to="/business"
            class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md font-medium hover:bg-gray-400 transition duration-200"
          >
            ← Nazad na dashboard
          </NuxtLink>
        </div>
      </div>

      <!-- Add Product Forms - Collapsible -->
      <div class="mb-8">
        <button
          @click="showAddProductForms = !showAddProductForms"
          class="w-full flex items-center justify-between bg-white rounded-lg shadow-md p-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            <span class="text-lg font-semibold text-gray-900">Dodaj proizvod</span>
          </div>
          <svg
            class="w-5 h-5 text-gray-500 transition-transform"
            :class="{ 'rotate-180': showAddProductForms }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </button>

        <div v-show="showAddProductForms" class="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Manual Form -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Dodaj proizvod - manuelno</h2>
            <form @submit.prevent="submitManualProduct" class="space-y-4">
            <div>
              <label for="title" class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda *</label>
              <input
                v-model="manualForm.title"
                type="text"
                id="title"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                placeholder="Naziv proizvoda"
              >
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label for="base_price" class="block text-sm font-medium text-gray-700 mb-1">Osnovna cijena (KM) *</label>
                <input
                  v-model.number="manualForm.base_price"
                  type="number"
                  step="0.01"
                  id="base_price"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  placeholder="0.00"
                >
              </div>

              <div>
                <label for="discount_price" class="block text-sm font-medium text-gray-700 mb-1">Cijena sa popustom (KM)</label>
                <input
                  v-model.number="manualForm.discount_price"
                  type="number"
                  step="0.01"
                  id="discount_price"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  placeholder="0.00"
                >
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label for="category" class="block text-sm font-medium text-gray-700 mb-1">Kategorija</label>
                <select
                  v-model="manualForm.category"
                  id="category"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm bg-white"
                >
                  <option value="">-- Odaberi kategoriju --</option>
                  <option v-for="cat in uniqueCategories" :key="cat" :value="cat">{{ cat }}</option>
                  <option value="__custom__">+ Nova kategorija...</option>
                </select>
                <input
                  v-if="manualForm.category === '__custom__'"
                  v-model="newManualCategory"
                  type="text"
                  class="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  placeholder="Unesite novu kategoriju..."
                  @input="manualForm.category = newManualCategory"
                >
              </div>

              <div>
                <label for="expires" class="block text-sm font-medium text-gray-700 mb-1">Datum isteka akcije</label>
                <input
                  v-model="manualForm.expires"
                  type="date"
                  id="expires"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                >
              </div>
            </div>

            <div>
              <label for="product_url" class="block text-sm font-medium text-gray-700 mb-1">Link na proizvod</label>
              <input
                v-model="manualForm.product_url"
                type="url"
                id="product_url"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                placeholder="https://..."
              >
            </div>

            <button
              type="submit"
              :disabled="isSubmittingManual"
              class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md font-medium hover:bg-indigo-700 transition duration-200 disabled:opacity-50"
            >
              {{ isSubmittingManual ? 'Dodaje se...' : 'Dodaj proizvod' }}
            </button>
          </form>
        </div>

        <!-- AI Parsing Form -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Dodaj proizvod - AI parsing</h2>
          <form @submit.prevent="submitAIProduct" class="space-y-4">
            <div>
              <label for="product_text" class="block text-sm font-medium text-gray-700 mb-1">Opis proizvoda</label>
              <textarea
                v-model="aiForm.product_text"
                id="product_text"
                rows="8"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                placeholder="Unesite opis proizvoda, AI će automatski parsirati podatke.&#10;&#10;Primjer:&#10;iPhone 15 Pro Max 256GB, novo u trgovini, garancija 2 godine.&#10;Originalna cijena 2500 KM, sada na akciji za 2200 KM.&#10;Akcija važi do kraja mjeseca."
              ></textarea>
            </div>

            <button
              type="submit"
              :disabled="isSubmittingAI"
              class="w-full bg-green-600 text-white py-2 px-4 rounded-md font-medium hover:bg-green-700 transition duration-200 disabled:opacity-50"
            >
              <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              {{ isSubmittingAI ? 'AI parsira...' : 'Dodaj sa AI parsing' }}
            </button>
          </form>
        </div>
        </div>
      </div>

      <!-- Bulk Import JSON - Collapsible -->
      <div class="mb-8">
        <button
          @click="showBulkImport = !showBulkImport"
          class="w-full flex items-center justify-between bg-white rounded-lg shadow-md p-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <span class="text-lg">📦</span>
            <span class="text-lg font-semibold text-gray-900">Bulk Import (JSON)</span>
          </div>
          <svg
            class="w-5 h-5 text-gray-500 transition-transform"
            :class="{ 'rotate-180': showBulkImport }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </button>

        <div v-show="showBulkImport" class="mt-4 bg-white rounded-lg shadow-md p-6">
          <form @submit.prevent="openBulkPreview" class="space-y-4">
            <div>
              <label for="products_json" class="block text-sm font-medium text-gray-700 mb-1">
                JSON sa proizvodima
                <a
                  href="https://github.com/asabanovic/ai-market/blob/main/BULK_IMPORT_PRODUCTS.md"
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 text-xs ml-2"
                >
                  (Pogledaj format)
                </a>
              </label>
              <textarea
                v-model="bulkImportJson"
                id="products_json"
                rows="12"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-mono text-gray-900"
                placeholder='{"products": [{"title": "Proizvod", "base_price": 10, "category": "Kategorija"}]}'
              ></textarea>
              <p class="mt-1 text-xs text-gray-500">
                Unesite JSON sa listom proizvoda. Sistem će automatski generisati tagove za svaki proizvod.
              </p>
            </div>
            <button
              type="submit"
              :disabled="!bulkImportJson.trim()"
              class="w-full bg-purple-600 text-white px-4 py-3 rounded-md font-medium hover:bg-purple-700 transition duration-200 flex items-center justify-center disabled:opacity-50"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
              Pregled proizvoda
            </button>
          </form>
          <div v-if="bulkImportStatus" class="mt-4">
            <div :class="[bulkImportStatus.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200', 'border rounded-md p-4']">
              <p :class="[bulkImportStatus.type === 'success' ? 'text-green-800' : 'text-red-800', 'text-sm']">
                {{ bulkImportStatus.message }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Products List -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-gray-900">
            Proizvodi ({{ filteredProductsCount }})
            <span v-if="selectedProducts.length > 0" class="ml-2 text-sm text-blue-600">
              ({{ selectedProducts.length }} označeno)
            </span>
          </h2>
          <div v-if="products.length > 0" class="flex gap-2">
            <button
              @click="regenerateAllTags"
              :disabled="isRegeneratingTags"
              class="bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 transition duration-200 flex items-center disabled:opacity-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              {{ isRegeneratingTags ? 'Regeneriše...' : 'Regeneriši tagove' }}
            </button>
            <button
              v-if="selectedProducts.length > 0"
              @click="bulkDeleteSelected"
              class="bg-orange-600 text-white px-4 py-2 rounded-md font-medium hover:bg-orange-700 transition duration-200"
            >
              Obriši označene
            </button>
            <button
              @click="deleteAllProducts"
              class="bg-red-600 text-white px-4 py-2 rounded-md font-medium hover:bg-red-700 transition duration-200"
            >
              Obriši sve proizvode
            </button>
          </div>
        </div>

        <!-- Search and Sort -->
        <div class="mb-4 flex flex-col sm:flex-row gap-4">
          <!-- Search Input -->
          <div class="flex-1 relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Pretrazi proizvode po nazivu..."
              class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
            >
            <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <!-- Sort Dropdown -->
          <div class="sm:w-64">
            <select
              v-model="sortBy"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 bg-white"
            >
              <option value="created_at_desc">Najnovije prvo</option>
              <option value="created_at_asc">Najstarije prvo</option>
              <option value="views_desc">Najvise pregleda</option>
              <option value="views_asc">Najmanje pregleda</option>
              <option value="discount_desc">Najveci popust</option>
              <option value="discount_asc">Najmanji popust</option>
              <option value="price_desc">Najvisa cijena</option>
              <option value="price_asc">Najniza cijena</option>
              <option value="title_asc">Naziv (A-Z)</option>
              <option value="title_desc">Naziv (Z-A)</option>
            </select>
          </div>
        </div>

        <div v-if="filteredProducts.length > 0" class="overflow-x-auto">
          <table class="min-w-full table-auto">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    :checked="selectedProducts.length === filteredProducts.length && filteredProducts.length > 0"
                    @change="toggleSelectAll"
                    class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  >
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slika</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proizvod</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Opis za pretragu</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Embedding Text</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AI</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cijena</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kategorija</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tagovi</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dodano</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Istek</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pregledi</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="product in filteredProducts" :key="product.id" class="product-row">
                <td class="px-4 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    :checked="selectedProducts.includes(product.id)"
                    @change="toggleProductSelection(product.id)"
                    class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  >
                </td>
                <td class="px-4 py-4 whitespace-nowrap text-sm font-medium">
                  <button @click="editProduct(product.id)" class="text-indigo-600 hover:text-indigo-900 mr-3">Uredi</button>
                  <button @click="deleteProduct(product.id)" class="text-red-600 hover:text-red-900">Obriši</button>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <img
                    v-if="product.image_path"
                    :src="getFullImageUrl(product.image_path)"
                    :alt="product.title"
                    loading="lazy"
                    class="w-16 h-16 object-cover rounded border border-gray-200"
                    @error="handleImageError"
                  >
                  <div v-else class="w-16 h-16 bg-gray-100 rounded border border-gray-200 flex items-center justify-center">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ product.title }}</div>
                  <div v-if="product.discount_percentage > 0" class="text-xs text-red-600">
                    -{{ product.discount_percentage }}% popust
                  </div>
                </td>
                <td class="px-4 py-4 max-w-xs">
                  <div class="text-sm text-gray-700 truncate" :title="product.enriched_description">
                    {{ product.enriched_description || 'Nema opisa' }}
                  </div>
                </td>
                <td class="px-4 py-4 max-w-xs">
                  <div v-if="product.has_embedding" class="space-y-1">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      ✓ Has Embedding
                    </span>
                    <div class="text-xs text-gray-500 truncate" :title="product.embedding_text">
                      {{ (product.embedding_text || '').substring(0, 50) }}{{ (product.embedding_text || '').length > 50 ? '...' : '' }}
                    </div>
                  </div>
                  <div v-else>
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                      ✗ No Embedding
                    </span>
                  </div>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <div v-if="product.brand || product.product_type || product.size_value" class="space-y-1">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      ✓ AI
                    </span>
                    <div class="text-xs text-gray-500" :title="`${product.brand || ''} ${product.product_type || ''} ${product.size_value || ''}${product.size_unit || ''}`">
                      {{ product.brand || '-' }}
                    </div>
                  </div>
                  <div v-else>
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                      -
                    </span>
                  </div>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-900">
                    <template v-if="product.discount_price">
                      <span class="font-bold text-red-600">{{ formatPrice(product.discount_price) }} KM</span><br>
                      <span class="text-gray-500 line-through text-xs">{{ formatPrice(product.base_price) }} KM</span>
                    </template>
                    <template v-else>
                      <span class="font-bold">{{ formatPrice(product.base_price) }} KM</span>
                    </template>
                  </div>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <span class="text-sm text-gray-500">{{ product.category || 'N/A' }}</span>
                </td>
                <td class="px-4 py-4">
                  <div v-if="product.tags && product.tags.length > 0" class="flex flex-wrap gap-1">
                    <span
                      v-for="(tag, idx) in product.tags.slice(0, 3)"
                      :key="idx"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {{ tag }}
                    </span>
                    <span
                      v-if="product.tags.length > 3"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600"
                    >
                      +{{ product.tags.length - 3 }}
                    </span>
                  </div>
                  <span v-else class="text-sm text-red-500">Nema tagova</span>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <div v-if="product.created_at" class="text-sm text-gray-900">{{ formatDate(product.created_at) }}</div>
                  <div v-if="product.created_at" class="text-xs text-gray-500">{{ formatTime(product.created_at) }}</div>
                  <span v-else class="text-sm text-gray-500">N/A</span>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <span v-if="product.expires" class="text-sm" :class="isExpired(product.expires) ? 'text-red-600' : 'text-gray-900'">
                    {{ formatDate(product.expires) }}
                  </span>
                  <span v-else class="text-sm text-gray-500">Bez isteka</span>
                </td>
                <td class="px-4 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <svg class="w-4 h-4 text-gray-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                    </svg>
                    <span class="text-sm font-medium text-gray-700">{{ product.views || 0 }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center py-8">
          <div class="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Nema proizvoda</h3>
          <p class="text-gray-600">Dodajte prvi proizvod koristeći formu iznad</p>
        </div>

        <!-- Pagination Controls -->
        <div v-if="totalPages > 1" class="flex items-center justify-between border-t border-gray-200 pt-4 mt-6">
          <div class="flex-1 flex justify-between sm:hidden">
            <button
              @click="goToPreviousPage"
              :disabled="currentPage === 1"
              class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Prethodna
            </button>
            <button
              @click="goToNextPage"
              :disabled="currentPage === totalPages"
              class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sljedeća
            </button>
          </div>
          <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p class="text-sm text-gray-700">
                Prikazano <span class="font-medium">{{ (currentPage - 1) * perPage + 1 }}</span> do <span class="font-medium">{{ Math.min(currentPage * perPage, totalProducts) }}</span> od <span class="font-medium">{{ totalProducts }}</span> proizvoda
              </p>
            </div>
            <div>
              <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  @click="goToPreviousPage"
                  :disabled="currentPage === 1"
                  class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                  </svg>
                </button>

                <!-- Page Numbers -->
                <template v-for="page in displayedPages" :key="page">
                  <button
                    v-if="page !== '...'"
                    @click="goToPage(page as number)"
                    :class="[
                      page === currentPage
                        ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                        : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50',
                      'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                    ]"
                  >
                    {{ page }}
                  </button>
                  <span
                    v-else
                    class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                  >
                    ...
                  </span>
                </template>

                <button
                  @click="goToNextPage"
                  :disabled="currentPage === totalPages"
                  class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notification area -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <div
        v-for="(notification, idx) in notifications"
        :key="idx"
        :class="[
          'p-4 border rounded-md shadow-lg max-w-sm',
          notification.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' :
          notification.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' :
          'bg-blue-50 border-blue-200 text-blue-700'
        ]"
      >
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="notification.type === 'success' ? 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' :
                   notification.type === 'error' ? 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z' :
                   'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'"
              />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium">{{ notification.message }}</p>
          </div>
          <div class="ml-auto pl-3">
            <button @click="removeNotification(idx)" class="text-gray-400 hover:text-gray-600">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Product Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeEditModal">
      <div class="relative top-20 mx-auto p-8 border w-full max-w-5xl shadow-lg rounded-md bg-white">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-2xl font-bold text-gray-900">Uredi proizvod</h3>
          <button @click="closeEditModal" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveProduct" class="space-y-4">
          <!-- Image Preview and Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-3">Slika proizvoda</label>

            <!-- Current and Original Images Side by Side -->
            <div class="flex items-start gap-8 mb-4">
              <!-- Current Image -->
              <div class="flex-shrink-0">
                <div v-if="editForm.image_path" class="relative">
                  <img :src="getFullImageUrl(editForm.image_path)" :alt="editForm.title" class="w-96 h-96 object-contain rounded-lg border-2 border-green-400 shadow-md bg-gray-50">
                  <span class="absolute -top-2 -right-2 px-3 py-1 text-xs font-bold bg-green-500 text-white rounded-full shadow">Trenutna</span>
                </div>
                <div v-else class="w-96 h-96 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                  <svg class="w-24 h-24 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                </div>
              </div>

              <!-- Original Image (always show when available) -->
              <div v-if="originalImagePath" class="flex-shrink-0">
                <div class="relative">
                  <img :src="getFullImageUrl(originalImagePath)" alt="Original" class="w-96 h-96 object-contain rounded-lg border-2 shadow-md bg-gray-50" :class="originalImagePath === editForm.image_path ? 'border-green-400' : 'border-gray-300 opacity-80'">
                  <span class="absolute -top-2 -right-2 px-3 py-1 text-xs font-bold text-white rounded-full shadow" :class="originalImagePath === editForm.image_path ? 'bg-green-500' : 'bg-gray-500'">Original</span>
                </div>
                <button
                  v-if="originalImagePath !== editForm.image_path"
                  type="button"
                  @click="revertToOriginal"
                  :disabled="isRevertingImage"
                  class="mt-3 w-full px-3 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
                >
                  {{ isRevertingImage ? 'Vraćam...' : 'Vrati original' }}
                </button>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3 mb-4">
              <input
                type="file"
                accept="image/*"
                @change="handleImageUpload"
                ref="imageInput"
                class="hidden"
              >
              <button
                type="button"
                @click="$refs.imageInput.click()"
                :disabled="isUploadingImage"
                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {{ isUploadingImage ? 'Uploadujem...' : 'Upload slike' }}
              </button>
              <button
                type="button"
                @click="suggestImages"
                :disabled="isSuggestingImages"
                class="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
              >
                <svg v-if="isSuggestingImages" class="w-4 h-4 inline mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ isSuggestingImages ? 'Tražim...' : 'Predloži slike' }}
              </button>
              <span class="text-xs text-gray-500 self-center">JPG, PNG ili GIF (max 5MB)</span>
            </div>

            <!-- Custom Search Query Input - always visible for custom search -->
            <div class="mb-4">
              <div class="flex gap-3 items-end">
                <div class="flex-1">
                  <label class="block text-xs font-medium text-gray-600 mb-1">Pojam za pretragu slika (opcionalno):</label>
                  <input
                    v-model="imageSearchQuery"
                    type="text"
                    :placeholder="editForm.title || 'Unesite pojam za pretragu...'"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 text-sm"
                    @keyup.enter="suggestImages"
                  >
                </div>
              </div>
              <p class="text-xs text-gray-500 mt-1">Ako ostavite prazno, koristit će se naziv proizvoda</p>
            </div>

            <!-- Suggested Images Collapsible Section -->
            <div v-if="suggestedImages.length > 0" class="border border-gray-200 rounded-lg">
              <button
                type="button"
                @click="showSuggestedImages = !showSuggestedImages"
                class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <span class="text-sm font-medium text-gray-700">
                  Predložene slike ({{ suggestedImages.length }})
                </span>
                <svg
                  class="w-5 h-5 text-gray-500 transition-transform"
                  :class="{ 'rotate-180': showSuggestedImages }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </button>
              <div v-show="showSuggestedImages" class="p-4 border-t border-gray-200">
                <p class="text-xs text-gray-500 mb-3">Klikni na sliku za odabir</p>
                <div class="grid grid-cols-5 gap-4">
                  <div
                    v-for="(imgPath, idx) in suggestedImages"
                    :key="idx"
                    @click="selectSuggestedImage(imgPath)"
                    class="relative cursor-pointer group"
                  >
                    <img
                      :src="getFullImageUrl(imgPath)"
                      :alt="`Suggestion ${idx + 1}`"
                      class="w-full h-48 object-contain rounded border-2 transition-all bg-gray-50"
                      :class="getFullImageUrl(imgPath) === editForm.image_path ? 'border-green-500 ring-2 ring-green-300' : 'border-gray-200 hover:border-purple-400'"
                    >
                    <div
                      v-if="getFullImageUrl(imgPath) === editForm.image_path"
                      class="absolute inset-0 bg-green-500 bg-opacity-20 rounded flex items-center justify-center"
                    >
                      <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
                      </svg>
                    </div>
                    <div
                      v-else
                      class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 rounded transition-all flex items-center justify-center"
                    >
                      <span class="opacity-0 group-hover:opacity-100 text-white text-xs font-medium bg-black bg-opacity-50 px-2 py-1 rounded">Odaberi</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <label for="edit_title" class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda *</label>
            <input
              v-model="editForm.title"
              type="text"
              id="edit_title"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
            >
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="edit_base_price" class="block text-sm font-medium text-gray-700 mb-1">Osnovna cijena (KM) *</label>
              <input
                v-model.number="editForm.base_price"
                type="number"
                step="0.01"
                id="edit_base_price"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
              >
            </div>

            <div>
              <label for="edit_discount_price" class="block text-sm font-medium text-gray-700 mb-1">Cijena sa popustom (KM)</label>
              <input
                v-model.number="editForm.discount_price"
                type="number"
                step="0.01"
                id="edit_discount_price"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
              >
            </div>
          </div>

          <div>
            <label for="edit_category" class="block text-sm font-medium text-gray-700 mb-1">Kategorija</label>
            <select
              v-model="editForm.category"
              id="edit_category"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900 bg-white"
            >
              <option value="">-- Odaberi kategoriju --</option>
              <option v-for="cat in uniqueCategories" :key="cat" :value="cat">{{ cat }}</option>
              <option value="__custom__">+ Nova kategorija...</option>
            </select>
            <input
              v-if="editForm.category === '__custom__' || (!uniqueCategories.includes(editForm.category || '') && editForm.category && editForm.category !== '')"
              v-model="customCategory"
              type="text"
              class="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
              placeholder="Unesite novu kategoriju..."
              @input="editForm.category = customCategory"
            >
          </div>

          <div>
            <label for="edit_expires" class="block text-sm font-medium text-gray-700 mb-1">Datum isteka akcije</label>
            <input
              v-model="editForm.expires"
              type="date"
              id="edit_expires"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
            >
          </div>

          <!-- Tags -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Tagovi</label>
            <div class="flex flex-wrap gap-2 mb-2">
              <span
                v-for="(tag, idx) in editForm.tags"
                :key="idx"
                class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
              >
                {{ tag }}
                <button
                  type="button"
                  @click="removeTag(idx)"
                  class="ml-2 text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
              <span v-if="!editForm.tags || editForm.tags.length === 0" class="text-sm text-gray-500">Nema tagova</span>
            </div>
            <button
              type="button"
              @click="regenerateTags"
              :disabled="isRegeneratingTagsSingle"
              class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {{ isRegeneratingTagsSingle ? 'Regenerišem...' : 'Regeneriši tagove (AI)' }}
            </button>
          </div>

          <div>
            <div class="flex justify-between items-center mb-1">
              <label for="edit_enriched_description" class="block text-sm font-medium text-gray-700">Opis za pretragu</label>
              <button
                type="button"
                @click="regenerateDescription"
                :disabled="isRegeneratingDescription"
                class="px-3 py-1 text-xs font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
              >
                {{ isRegeneratingDescription ? 'Regenerišem...' : 'Regeneriši opis (AI)' }}
              </button>
            </div>
            <textarea
              v-model="editForm.enriched_description"
              id="edit_enriched_description"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-gray-900"
              placeholder="Detaljan opis proizvoda koji će se koristiti za semantičku pretragu..."
            ></textarea>
            <p class="mt-1 text-xs text-gray-500">Ovaj opis se koristi za AI-powered pretragu proizvoda.</p>
          </div>

          <!-- Product Matching Fields -->
          <div class="border-t border-gray-200 pt-4 mt-4">
            <div class="flex justify-between items-center mb-3">
              <h4 class="text-sm font-semibold text-gray-700">Polja za uparivanje proizvoda</h4>
              <button
                type="button"
                @click="extractMatchingFields"
                :disabled="isExtractingMatching"
                class="px-3 py-1 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {{ isExtractingMatching ? 'Ekstrahujem...' : 'Ekstrahuj (AI)' }}
              </button>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <!-- Brand -->
              <div>
                <label for="edit_brand" class="block text-sm font-medium text-gray-700 mb-1">Brend</label>
                <input
                  v-model="editForm.brand"
                  type="text"
                  id="edit_brand"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-gray-900"
                  placeholder="npr. Coca-Cola, Nestle..."
                >
              </div>

              <!-- Product Type -->
              <div>
                <label for="edit_product_type" class="block text-sm font-medium text-gray-700 mb-1">Tip proizvoda</label>
                <input
                  v-model="editForm.product_type"
                  type="text"
                  id="edit_product_type"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-gray-900"
                  placeholder="npr. cola, jogurt, mlijeko..."
                >
              </div>

              <!-- Size Value -->
              <div>
                <label for="edit_size_value" class="block text-sm font-medium text-gray-700 mb-1">Veličina (broj)</label>
                <input
                  v-model.number="editForm.size_value"
                  type="number"
                  step="0.01"
                  id="edit_size_value"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-gray-900"
                  placeholder="npr. 500, 1, 250..."
                >
              </div>

              <!-- Size Unit -->
              <div>
                <label for="edit_size_unit" class="block text-sm font-medium text-gray-700 mb-1">Jedinica mjere</label>
                <select
                  v-model="editForm.size_unit"
                  id="edit_size_unit"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-gray-900"
                >
                  <option value="">Odaberi...</option>
                  <option value="ml">ml (mililitar)</option>
                  <option value="l">l (litar)</option>
                  <option value="g">g (gram)</option>
                  <option value="kg">kg (kilogram)</option>
                  <option value="kom">kom (komad)</option>
                  <option value="pak">pak (pakovanje)</option>
                </select>
              </div>

              <!-- Variant -->
              <div class="col-span-2">
                <label for="edit_variant" class="block text-sm font-medium text-gray-700 mb-1">Varijanta</label>
                <input
                  v-model="editForm.variant"
                  type="text"
                  id="edit_variant"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-gray-900"
                  placeholder="npr. zero, light, original..."
                >
              </div>

              <!-- Match Key (read-only) -->
              <div class="col-span-2" v-if="editForm.match_key">
                <label class="block text-sm font-medium text-gray-700 mb-1">Ključ za uparivanje</label>
                <div class="px-3 py-2 bg-gray-100 border border-gray-200 rounded-md text-sm text-gray-600 font-mono">
                  {{ editForm.match_key }}
                </div>
                <p class="mt-1 text-xs text-gray-500">Automatski generisan ključ za pronalaženje identičnih proizvoda u različitim radnjama.</p>
              </div>
            </div>
          </div>

          <!-- Price History -->
          <div v-if="priceHistory.length > 0">
            <label class="block text-sm font-medium text-gray-700 mb-2">Historija cijena</label>
            <div class="overflow-x-auto">
              <table class="min-w-full text-sm border border-gray-200 rounded">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Datum</th>
                    <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Osnovna</th>
                    <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">S popustom</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  <tr v-for="(h, idx) in priceHistory" :key="idx">
                    <td class="px-3 py-2 text-gray-600">{{ formatDateTime(h.recorded_at) }}</td>
                    <td class="px-3 py-2 text-right text-gray-900">{{ h.base_price?.toFixed(2) }} KM</td>
                    <td class="px-3 py-2 text-right text-gray-900">{{ h.discount_price ? h.discount_price.toFixed(2) + ' KM' : '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              @click="closeEditModal"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Otkaži
            </button>
            <button
              type="submit"
              :disabled="isSavingProduct"
              class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {{ isSavingProduct ? 'Čuvam...' : 'Sačuvaj' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Image Cropper Modal -->
  <div v-if="showCropperModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Izreži sliku</h3>
        <button @click="closeCropperModal" class="text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <div class="mb-4">
        <p class="text-sm text-gray-600 mb-2">Odaberite dio slike za izrezivanje (1:1 omjer, 400x400px)</p>
        <div class="flex justify-center bg-gray-100 rounded-lg p-4">
          <img
            ref="cropperImageRef"
            :src="cropperImageUrl"
            alt="Cropper"
            class="max-h-96"
          >
        </div>
      </div>

      <div class="flex justify-end gap-3">
        <button
          type="button"
          @click="closeCropperModal"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          Otkaži
        </button>
        <button
          type="button"
          @click="applyCrop"
          :disabled="isCropping"
          class="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50"
        >
          {{ isCropping ? 'Obrađujem...' : 'Primijeni' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Bulk Import Preview Modal -->
  <div v-if="showBulkPreview" class="fixed inset-0 bg-gray-800 bg-opacity-75 overflow-y-auto h-full w-full z-50">
    <!-- Floating action buttons -->
    <div class="fixed bottom-6 left-1/2 transform -translate-x-1/2 flex gap-4 z-[60]">
      <button
        @click="cancelBulkPreview"
        class="px-6 py-3 text-lg font-medium text-gray-700 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        Otkaži
      </button>
      <button
        @click="confirmBulkUpload"
        :disabled="isSubmittingBulk || previewProducts.length === 0"
        class="px-8 py-3 text-lg font-medium text-white bg-green-600 rounded-full shadow-lg hover:bg-green-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
        </svg>
        {{ isSubmittingBulk ? 'Uploading...' : `Upload ${previewProducts.length} proizvoda` }}
      </button>
    </div>

    <div class="relative mx-auto p-6 w-full max-w-7xl">
      <!-- Header -->
      <div class="bg-white rounded-t-xl shadow-lg p-6 mb-0">
        <div class="flex justify-between items-center">
          <div>
            <h3 class="text-2xl font-bold text-gray-900">Pregled proizvoda za upload</h3>
            <p class="text-gray-600 mt-1">
              {{ filteredPreviewProducts.length }} od {{ previewProducts.length }} proizvoda
              <span v-if="previewSearchQuery"> (filtrirano)</span>
              . Kliknite na X da uklonite proizvod.
            </p>
          </div>
          <button @click="cancelBulkPreview" class="text-gray-400 hover:text-gray-600">
            <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <!-- Search filter for preview products -->
        <div class="mt-4">
          <div class="relative">
            <input
              v-model="previewSearchQuery"
              type="text"
              placeholder="Pretraži proizvode po nazivu..."
              class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
            <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <button
              v-if="previewSearchQuery"
              @click="previewSearchQuery = ''"
              class="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Products Grid -->
      <div class="bg-gray-50 rounded-b-xl shadow-lg p-6 pb-24">
        <div v-if="previewProducts.length === 0" class="text-center py-12">
          <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
          </svg>
          <p class="text-gray-600 text-lg">Svi proizvodi su uklonjeni</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          <div
            v-for="(product, index) in filteredPreviewProducts"
            :key="product._originalIndex ?? index"
            class="bg-white rounded-lg shadow-md overflow-hidden relative group hover:shadow-lg transition-shadow"
          >
            <!-- Remove button -->
            <button
              @click="removePreviewProduct(product._originalIndex ?? index)"
              class="absolute top-2 right-2 z-10 bg-red-500 text-white rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
              title="Ukloni proizvod"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>

            <!-- Discount badge -->
            <div
              v-if="product.has_discount"
              class="absolute top-2 left-2 bg-red-500 text-white px-2 py-0.5 rounded-full text-xs font-bold"
            >
              -{{ product.discount_percentage }}%
            </div>

            <!-- Product Image or Placeholder -->
            <div class="w-full h-32 bg-gradient-to-br from-purple-100 to-indigo-100 flex items-center justify-center">
              <img
                v-if="product.image_url"
                :src="product.image_url"
                :alt="product.title"
                class="w-full h-32 object-contain"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              >
              <svg v-else class="w-10 h-10 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
            </div>

            <!-- Product info -->
            <div class="p-3">
              <h4 class="font-semibold text-sm text-gray-900 line-clamp-2 mb-2" :title="product.title">
                {{ product.title }}
              </h4>

              <div class="flex items-baseline gap-2 mb-2">
                <span
                  v-if="product.discount_price"
                  class="text-lg font-bold text-green-600"
                >
                  {{ formatPrice(product.discount_price) }} KM
                </span>
                <span
                  :class="[
                    'font-bold',
                    product.discount_price ? 'text-sm line-through text-gray-400' : 'text-lg text-green-600'
                  ]"
                >
                  {{ formatPrice(product.base_price) }} KM
                </span>
              </div>

              <div v-if="product.category" class="text-xs text-gray-500 flex items-center gap-1 mb-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                </svg>
                {{ product.category }}
              </div>

              <div v-if="product.expires" class="text-xs text-gray-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                {{ product.expires }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

definePageMeta({
  middleware: ['auth']
})

const route = useRoute()
const config = useRuntimeConfig()
const { get, post, del: deleteApi } = useApi()
const businessId = computed(() => route.params.id)

// Reactive data
const business = ref<any>(null)
const products = ref<any[]>([])
const selectedProducts = ref<number[]>([])
const notifications = ref<any[]>([])
const searchQuery = ref('')
const previewSearchQuery = ref('')
const sortBy = ref('created_at_desc')
const showAddProductForms = ref(false)
const showBulkImport = ref(false)

// Computed property for unique categories
const uniqueCategories = computed(() => {
  const categories = products.value
    .map(p => p.category)
    .filter(c => c && c.trim() !== '')
  return [...new Set(categories)].sort()
})

// Computed property for filtered products (now server-side, so just return products)
const filteredProducts = computed(() => products.value)

const filteredProductsCount = computed(() => totalProducts.value)

// Computed property for filtered preview products (client-side search)
const filteredPreviewProducts = computed(() => {
  if (!previewSearchQuery.value.trim()) {
    // Add original index to each product for proper removal
    return previewProducts.value.map((p, i) => ({ ...p, _originalIndex: i }))
  }
  const query = previewSearchQuery.value.toLowerCase().trim()
  return previewProducts.value
    .map((p, i) => ({ ...p, _originalIndex: i }))
    .filter(p => p.title?.toLowerCase().includes(query))
})

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, (newValue) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchProducts()
  }, 300)
})

// Watch sortBy changes
watch(sortBy, () => {
  currentPage.value = 1
  fetchProducts()
})

// Pagination state
const currentPage = ref(1)
const totalPages = ref(1)
const totalProducts = ref(0)
const perPage = ref(50)

// Form states
const isSubmittingManual = ref(false)
const isSubmittingAI = ref(false)
const isSubmittingBulk = ref(false)
const isRegeneratingTags = ref(false)

// Form data
const manualForm = ref({
  title: '',
  base_price: null,
  discount_price: null,
  category: '',
  expires: '',
  product_url: ''
})
const newManualCategory = ref('')

const aiForm = ref({
  product_text: ''
})

const bulkImportJson = ref('')
const bulkImportStatus = ref<any>(null)

// Bulk import preview state
const showBulkPreview = ref(false)
const previewProducts = ref<Array<{
  title: string
  base_price: number
  discount_price?: number
  category?: string
  expires?: string
  product_url?: string
  image_url?: string
  has_discount?: boolean
  discount_percentage?: number
}>>([])

// Edit modal state
const showEditModal = ref(false)
const isSavingProduct = ref(false)
const isUploadingImage = ref(false)
const isRegeneratingDescription = ref(false)
const isExtractingMatching = ref(false)
const isRegeneratingTagsSingle = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const customCategory = ref('')
const priceHistory = ref<any[]>([])

// Image suggestion state
const suggestedImages = ref<string[]>([])
const originalImagePath = ref<string | null>(null)
const isSuggestingImages = ref(false)
const isRevertingImage = ref(false)
const showSuggestedImages = ref(false)
const imageSearchQuery = ref('')

// Cropper state
const showCropperModal = ref(false)
const cropperImageUrl = ref('')
const cropperImagePath = ref('')
const cropperImageRef = ref<HTMLImageElement | null>(null)
const isCropping = ref(false)
let cropperInstance: Cropper | null = null

const editForm = ref({
  id: null as number | null,
  title: '',
  base_price: null as number | null,
  discount_price: null as number | null,
  category: '',
  expires: '',
  product_url: '',
  enriched_description: '',
  image_path: '',
  tags: [] as string[],
  // Product matching fields
  brand: '',
  product_type: '',
  size_value: null as number | null,
  size_unit: '',
  variant: '',
  match_key: ''
})

// Fetch business and products
async function fetchBusiness() {
  try {
    business.value = await get(`/api/businesses/${businessId.value}`)
  } catch (error) {
    showNotification('Greška pri učitavanju biznisa', 'error')
  }
}

async function fetchProducts() {
  try {
    let url = `/api/businesses/${businessId.value}/products?page=${currentPage.value}&per_page=${perPage.value}`
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`
    }
    if (sortBy.value) {
      url += `&sort=${sortBy.value}`
    }
    const data = await get(url)
    products.value = data.products || []

    // Update pagination metadata
    if (data.pagination) {
      totalPages.value = data.pagination.total_pages
      totalProducts.value = data.pagination.total
    }
  } catch (error) {
    showNotification('Greška pri učitavanju proizvoda', 'error')
  }
}

// Submit handlers
async function submitManualProduct() {
  isSubmittingManual.value = true
  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/dodaj`, manualForm.value)

    if (data.success) {
      showNotification('Proizvod je uspješno dodat!', 'success')
      manualForm.value = {
        title: '',
        base_price: null,
        discount_price: null,
        category: '',
        expires: '',
        product_url: ''
      }
      setTimeout(() => fetchProducts(), 1000)
    } else {
      showNotification(data.error || 'Došlo je do greške', 'error')
    }
  } catch (error) {
    showNotification('Došlo je do greške prilikom dodavanja proizvoda', 'error')
  } finally {
    isSubmittingManual.value = false
  }
}

async function submitAIProduct() {
  isSubmittingAI.value = true
  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/dodaj`, aiForm.value)

    if (data.success) {
      showNotification('Proizvod je uspješno dodat sa AI parsing!', 'success')
      aiForm.value.product_text = ''
      setTimeout(() => fetchProducts(), 1000)
    } else {
      showNotification(data.error || 'Došlo je do greške', 'error')
    }
  } catch (error) {
    showNotification('Došlo je do greške prilikom AI parsing', 'error')
  } finally {
    isSubmittingAI.value = false
  }
}

async function submitBulkImport() {
  isSubmittingBulk.value = true
  bulkImportStatus.value = null

  try {
    const jsonData = JSON.parse(bulkImportJson.value)
    if (!jsonData.products || !Array.isArray(jsonData.products)) {
      throw new Error('JSON mora imati "products" array')
    }
  } catch (error: any) {
    showNotification('Nevažeći JSON format: ' + error.message, 'error')
    isSubmittingBulk.value = false
    return
  }

  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/bulk-import`, JSON.parse(bulkImportJson.value))

    if (data.success) {
      bulkImportStatus.value = {
        type: 'success',
        message: data.message || `✓ Uspješno importovano ${data.imported_count} proizvoda!`
      }
      showNotification(data.message || 'Proizvodi su uspješno importovani!', 'success')
      setTimeout(() => {
        fetchProducts()
        bulkImportJson.value = ''
      }, 2000)
    } else {
      bulkImportStatus.value = {
        type: 'error',
        message: '✗ Greška: ' + (data.error || 'Nepoznata greška')
      }
      showNotification(data.error || 'Greška pri importu', 'error')
    }
  } catch (error) {
    bulkImportStatus.value = {
      type: 'error',
      message: '✗ Greška pri importu'
    }
    showNotification('Došlo je do greške prilikom importa', 'error')
  } finally {
    isSubmittingBulk.value = false
  }
}

// Bulk import preview functions
function openBulkPreview() {
  bulkImportStatus.value = null

  try {
    const jsonData = JSON.parse(bulkImportJson.value)
    if (!jsonData.products || !Array.isArray(jsonData.products)) {
      throw new Error('JSON mora imati "products" array')
    }

    // Process products for preview
    previewProducts.value = jsonData.products.map((product: any) => {
      const hasDiscount = product.discount_price && product.discount_price < product.base_price
      const discountPercentage = hasDiscount
        ? Math.round((1 - product.discount_price / product.base_price) * 100)
        : 0

      return {
        title: product.title || 'Bez naziva',
        base_price: product.base_price || 0,
        discount_price: product.discount_price || null,
        category: product.category || null,
        expires: product.expires || null,
        product_url: product.product_url || null,
        image_url: product.image_url || null,
        has_discount: hasDiscount,
        discount_percentage: discountPercentage
      }
    })

    showBulkPreview.value = true
  } catch (error: any) {
    showNotification('Nevažeći JSON format: ' + error.message, 'error')
  }
}

function removePreviewProduct(index: number) {
  previewProducts.value.splice(index, 1)
}

function cancelBulkPreview() {
  showBulkPreview.value = false
  previewProducts.value = []
  previewSearchQuery.value = ''
}

async function confirmBulkUpload() {
  if (previewProducts.value.length === 0) {
    showNotification('Nema proizvoda za upload', 'error')
    return
  }

  isSubmittingBulk.value = true
  bulkImportStatus.value = null

  try {
    // Build the products array from preview (without computed fields)
    const productsToUpload = previewProducts.value.map(p => ({
      title: p.title,
      base_price: p.base_price,
      discount_price: p.discount_price,
      category: p.category,
      expires: p.expires,
      product_url: p.product_url,
      image_url: p.image_url
    }))

    const data = await post(`/biznisi/${businessId.value}/proizvodi/bulk-import`, {
      products: productsToUpload
    })

    if (data.success) {
      bulkImportStatus.value = {
        type: 'success',
        message: data.message || `✓ Uspješno importovano ${data.imported_count} proizvoda!`
      }
      showNotification(data.message || 'Proizvodi su uspješno importovani!', 'success')
      showBulkPreview.value = false
      previewProducts.value = []
      bulkImportJson.value = ''
      setTimeout(() => fetchProducts(), 2000)
    } else {
      bulkImportStatus.value = {
        type: 'error',
        message: '✗ Greška: ' + (data.error || 'Nepoznata greška')
      }
      showNotification(data.error || 'Greška pri importu', 'error')
    }
  } catch (error) {
    bulkImportStatus.value = {
      type: 'error',
      message: '✗ Greška pri importu'
    }
    showNotification('Došlo je do greške prilikom importa', 'error')
  } finally {
    isSubmittingBulk.value = false
  }
}

async function regenerateAllTags() {
  if (!confirm('Da li ste sigurni da želite regenerisati tagove za sve proizvode? Ovo može potrajati nekoliko minuta.')) {
    return
  }

  isRegeneratingTags.value = true
  showNotification('Regeneracija tagova u toku... Molimo sačekajte.', 'info')

  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/regenerate-tags`, {})

    if (data.success) {
      showNotification(`Uspješno regenerisano ${data.updated_count} tagova!`, 'success')
      setTimeout(() => fetchProducts(), 2000)
    } else {
      showNotification(data.error || 'Greška pri regeneraciji tagova', 'error')
    }
  } catch (error) {
    showNotification('Greška pri regeneraciji tagova', 'error')
  } finally {
    isRegeneratingTags.value = false
  }
}

async function deleteAllProducts() {
  if (!confirm('Da li ste sigurni da želite obrisati sve proizvode iz ove radnje? Ova akcija se ne može poništiti.')) {
    return
  }

  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/obrisi-sve`, {})

    if (data.success) {
      showNotification(`Obrisano je ${data.deleted_count} proizvoda`, 'success')
      setTimeout(() => fetchProducts(), 1000)
    } else {
      showNotification('Došlo je do greške prilikom brisanja', 'error')
    }
  } catch (error) {
    showNotification('Došlo je do greške', 'error')
  }
}

async function bulkDeleteSelected() {
  if (selectedProducts.value.length === 0) {
    showNotification('Niste označili nijedan proizvod', 'error')
    return
  }

  if (!confirm(`Da li ste sigurni da želite obrisati ${selectedProducts.value.length} označenih proizvoda?`)) {
    return
  }

  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/bulk-delete`, { product_ids: selectedProducts.value })

    if (data.success) {
      showNotification(`Uspješno obrisano ${data.deleted_count} proizvoda`, 'success')
      selectedProducts.value = []
      setTimeout(() => fetchProducts(), 1000)
    } else {
      showNotification(data.error || 'Greška pri brisanju', 'error')
    }
  } catch (error) {
    showNotification('Greška pri brisanju proizvoda', 'error')
  }
}

async function editProduct(productId: number) {
  const product = products.value.find(p => p.id === productId)
  if (!product) {
    showNotification('Proizvod nije pronađen', 'error')
    return
  }

  // Populate edit form with product data
  editForm.value = {
    id: product.id,
    title: product.title,
    base_price: product.base_price,
    discount_price: product.discount_price,
    category: product.category || '',
    expires: product.expires ? product.expires.split('T')[0] : '',
    product_url: product.product_url || '',
    enriched_description: product.enriched_description || '',
    image_path: product.image_path || '',
    tags: product.tags || [],
    // Product matching fields
    brand: product.brand || '',
    product_type: product.product_type || '',
    size_value: product.size_value || null,
    size_unit: product.size_unit || '',
    variant: product.variant || '',
    match_key: product.match_key || ''
  }

  // Reset custom category if the product's category is not in the list
  customCategory.value = uniqueCategories.value.includes(product.category || '') ? '' : (product.category || '')

  // Reset suggestion state
  suggestedImages.value = []
  originalImagePath.value = product.image_path || null  // Store the original image path
  imageSearchQuery.value = ''  // Reset search query

  // Fetch price history and suggested images in parallel
  try {
    const [historyData, suggestionsData] = await Promise.all([
      get(`/api/products/${productId}/price-history`).catch(() => []),
      get(`/api/admin/products/${productId}/suggested-images`).catch(() => ({}))
    ])

    priceHistory.value = historyData || []

    if (suggestionsData.suggested_images && suggestionsData.suggested_images.length > 0) {
      suggestedImages.value = suggestionsData.suggested_images
      // Auto-expand suggested images when they exist
      showSuggestedImages.value = true
    }
    // If backend provides original_image_path (from previous suggestions), prefer that
    if (suggestionsData.original_image_path) {
      originalImagePath.value = suggestionsData.original_image_path
    }
  } catch (error) {
    priceHistory.value = []
  }

  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  priceHistory.value = []
  // Reset suggestion state
  suggestedImages.value = []
  originalImagePath.value = null
  showSuggestedImages.value = false
  // Reset form
  editForm.value = {
    id: null,
    title: '',
    base_price: null,
    discount_price: null,
    category: '',
    expires: '',
    product_url: '',
    enriched_description: '',
    image_path: '',
    tags: []
  }
}

function removeTag(index: number) {
  editForm.value.tags.splice(index, 1)
}

async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    showNotification('Slika je prevelika. Maksimalna veličina je 5MB.', 'error')
    return
  }

  // Validate file type
  if (!file.type.startsWith('image/')) {
    showNotification('Molimo odaberite sliku (JPG, PNG, GIF)', 'error')
    return
  }

  isUploadingImage.value = true
  try {
    const formData = new FormData()
    formData.append('image', file)

    // Get auth token
    const token = process.client ? localStorage.getItem('token') : null
    const headers: HeadersInit = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(
      `${config.public.apiBase}/biznisi/${businessId.value}/proizvodi/${editForm.value.id}/upload-image`,
      {
        method: 'POST',
        headers,
        body: formData
      }
    )

    const data = await response.json()

    if (data.success) {
      editForm.value.image_path = data.image_url
      showNotification('Slika je uspješno uploadovana', 'success')
    } else {
      showNotification(data.error || 'Greška pri uploadu slike', 'error')
    }
  } catch (error: any) {
    console.error('Image upload error:', error)
    showNotification('Greška pri uploadu slike', 'error')
  } finally {
    isUploadingImage.value = false
    // Reset input
    if (input) input.value = ''
  }
}

async function regenerateTags() {
  if (!editForm.value.id) return

  isRegeneratingTagsSingle.value = true
  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/${editForm.value.id}/regenerate-tags`, {})

    if (data.success && data.tags) {
      editForm.value.tags = data.tags
      showNotification('Tagovi su uspješno regenerisani', 'success')
    } else {
      showNotification(data.error || 'Greška pri regeneraciji tagova', 'error')
    }
  } catch (error: any) {
    console.error('Regenerate tags error:', error)
    showNotification('Greška pri regeneraciji tagova', 'error')
  } finally {
    isRegeneratingTagsSingle.value = false
  }
}

async function regenerateDescription() {
  if (!editForm.value.id) return

  isRegeneratingDescription.value = true
  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/${editForm.value.id}/regenerate-description`, {})

    if (data.success && data.description) {
      editForm.value.enriched_description = data.description
      showNotification('Opis je uspješno regenerisan', 'success')
    } else {
      showNotification(data.error || 'Greška pri regeneraciji opisa', 'error')
    }
  } catch (error: any) {
    console.error('Regenerate description error:', error)
    showNotification('Greška pri regeneraciji opisa', 'error')
  } finally {
    isRegeneratingDescription.value = false
  }
}

async function extractMatchingFields() {
  if (!editForm.value.id) return

  isExtractingMatching.value = true
  try {
    const data = await post(`/biznisi/${businessId.value}/proizvodi/${editForm.value.id}/extract-matching`, {})

    if (data.success) {
      // Update form with extracted values
      editForm.value.brand = data.brand || ''
      editForm.value.product_type = data.product_type || ''
      editForm.value.size_value = data.size_value || null
      editForm.value.size_unit = data.size_unit || ''
      editForm.value.variant = data.variant || ''
      editForm.value.match_key = data.match_key || ''
      showNotification('Polja za uparivanje su uspješno ekstraktovana (AI)', 'success')
    } else {
      showNotification(data.error || 'Greška pri ekstrakciji', 'error')
    }
  } catch (error: any) {
    console.error('Extract matching fields error:', error)
    showNotification('Greška pri ekstrakciji polja', 'error')
  } finally {
    isExtractingMatching.value = false
  }
}

async function saveProduct() {
  if (!editForm.value.id) return

  isSavingProduct.value = true
  try {
    const payload = {
      title: editForm.value.title,
      base_price: editForm.value.base_price,
      discount_price: editForm.value.discount_price,
      category: editForm.value.category,
      expires: editForm.value.expires,
      product_url: editForm.value.product_url,
      enriched_description: editForm.value.enriched_description,
      image_path: editForm.value.image_path,
      tags: editForm.value.tags,
      // Product matching fields
      brand: editForm.value.brand || null,
      product_type: editForm.value.product_type || null,
      size_value: editForm.value.size_value || null,
      size_unit: editForm.value.size_unit || null,
      variant: editForm.value.variant || null
    }

    const { put } = useApi()
    const data = await put(`/biznisi/${businessId.value}/proizvodi/${editForm.value.id}`, payload)

    if (data.success) {
      showNotification('Proizvod je uspješno ažuriran', 'success')
      closeEditModal()
      setTimeout(() => fetchProducts(), 500)
    } else {
      showNotification(data.error || 'Greška pri ažuriranju proizvoda', 'error')
    }
  } catch (error: any) {
    console.error('Save product error:', error)
    showNotification(error.message || 'Greška pri ažuriranju proizvoda', 'error')
  } finally {
    isSavingProduct.value = false
  }
}

async function deleteProduct(productId: number) {
  if (!confirm('Da li ste sigurni da želite obrisati ovaj proizvod?')) {
    return
  }

  try {
    const data = await deleteApi(`/biznisi/${businessId.value}/proizvodi/${productId}`)

    if (data.success) {
      showNotification('Proizvod je uspješno obrisan', 'success')
      // Remove from local array for immediate UI update
      products.value = products.value.filter(p => p.id !== productId)
      // Also fetch fresh data
      setTimeout(() => fetchProducts(), 500)
    } else {
      showNotification(data.error || 'Greška pri brisanju proizvoda', 'error')
    }
  } catch (error: any) {
    console.error('Delete product error:', error)
    showNotification('Greška pri brisanju proizvoda', 'error')
  }
}

// Selection handlers
function toggleSelectAll(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    selectedProducts.value = filteredProducts.value.map(p => p.id)
  } else {
    selectedProducts.value = []
  }
}

function toggleProductSelection(productId: number) {
  const index = selectedProducts.value.indexOf(productId)
  if (index > -1) {
    selectedProducts.value.splice(index, 1)
  } else {
    selectedProducts.value.push(productId)
  }
}

// Notification helpers
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

// Utility functions
function formatPrice(price: number): string {
  return price.toFixed(2)
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatDateTime(dateString: string): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleTimeString('sr-Latn-BA', { hour: '2-digit', minute: '2-digit' })
}

function isExpired(dateString: string): boolean {
  return new Date(dateString) < new Date()
}

function handleImageError(event: Event) {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
  if (target.nextElementSibling) {
    (target.nextElementSibling as HTMLElement).style.display = 'flex'
  }
}

// Get full image URL from S3 path
function getFullImageUrl(path: string | null): string {
  if (!path) return ''
  // If it's already a full URL, return it
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // Otherwise, construct the S3 URL
  return `https://aipijaca.s3.eu-central-1.amazonaws.com/${path}`
}

// Image suggestion functions
async function suggestImages() {
  if (!editForm.value.id) {
    showNotification('Proizvod mora biti sačuvan prije pretrage slika', 'error')
    return
  }

  // Use custom query if provided, otherwise fall back to title
  const searchQuery = imageSearchQuery.value.trim() || editForm.value.title
  if (!searchQuery) {
    showNotification('Unesite pojam za pretragu ili naziv proizvoda', 'error')
    return
  }

  isSuggestingImages.value = true
  try {
    const data = await post(`/api/admin/products/${editForm.value.id}/suggest-images`, { query: searchQuery })

    if (data.success) {
      suggestedImages.value = data.suggested_images || []
      if (data.original_image_path) {
        originalImagePath.value = data.original_image_path
      }
      if (suggestedImages.value.length > 0) {
        showNotification(`Pronađeno ${suggestedImages.value.length} slika`, 'success')
        // Auto-expand the section to show the images
        showSuggestedImages.value = true
      } else {
        showNotification('Nisu pronađene slike za ovaj proizvod', 'info')
      }
    } else {
      showNotification(data.error || 'Greška pri pretrazi slika', 'error')
    }
  } catch (error: any) {
    console.error('Suggest images error:', error)
    showNotification('Greška pri pretrazi slika', 'error')
  } finally {
    isSuggestingImages.value = false
  }
}

async function selectSuggestedImage(imagePath: string) {
  if (!editForm.value.id) return

  try {
    const data = await post(`/api/admin/products/${editForm.value.id}/select-image`, {
      image_path: imagePath
    })

    if (data.success) {
      editForm.value.image_path = data.image_path
      showNotification('Slika je odabrana', 'success')
    } else {
      showNotification(data.error || 'Greška pri odabiru slike', 'error')
    }
  } catch (error: any) {
    console.error('Select image error:', error)
    showNotification('Greška pri odabiru slike', 'error')
  }
}

async function revertToOriginal() {
  if (!editForm.value.id || !originalImagePath.value) return

  isRevertingImage.value = true
  try {
    const data = await post(`/api/admin/products/${editForm.value.id}/revert-image`, {})

    if (data.success) {
      editForm.value.image_path = data.image_path || originalImagePath.value
      showNotification('Vraćena originalna slika', 'success')
    } else {
      showNotification(data.error || 'Greška pri vraćanju slike', 'error')
    }
  } catch (error: any) {
    console.error('Revert image error:', error)
    showNotification('Greška pri vraćanju slike', 'error')
  } finally {
    isRevertingImage.value = false
  }
}

// Cropper functions
function openCropperModal(imagePath: string) {
  cropperImagePath.value = imagePath
  cropperImageUrl.value = getFullImageUrl(imagePath)
  showCropperModal.value = true

  // Initialize cropper after DOM update
  nextTick(() => {
    if (cropperImageRef.value && !cropperInstance) {
      cropperInstance = new Cropper(cropperImageRef.value, {
        aspectRatio: 1,
        viewMode: 1,
        dragMode: 'move',
        autoCropArea: 0.8,
        restore: false,
        guides: true,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        checkCrossOrigin: false
      })
    }
  })
}

function closeCropperModal() {
  showCropperModal.value = false
  cropperImageUrl.value = ''
  cropperImagePath.value = ''
  if (cropperInstance) {
    cropperInstance.destroy()
    cropperInstance = null
  }
}

async function applyCrop() {
  if (!cropperInstance || !editForm.value.id) return

  isCropping.value = true

  try {
    // Get cropped canvas with 400x400 dimensions
    const canvas = cropperInstance.getCroppedCanvas({
      width: 400,
      height: 400,
      imageSmoothingEnabled: true,
      imageSmoothingQuality: 'high'
    })

    if (!canvas) {
      showNotification('Greška pri izrezivanju slike', 'error')
      return
    }

    // Convert canvas to blob
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.9)
    })

    if (!blob) {
      showNotification('Greška pri obradi slike', 'error')
      return
    }

    // Create FormData and upload
    const formData = new FormData()
    formData.append('image', blob, 'cropped.jpg')
    formData.append('original_suggestion_path', cropperImagePath.value)

    const response = await fetch(`${config.public.apiBase}/api/admin/products/${editForm.value.id}/upload-cropped-image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useCookie('auth_token').value}`
      },
      body: formData
    })

    const data = await response.json()

    if (data.success) {
      editForm.value.image_path = data.image_path
      showNotification('Slika uspješno izrezana i spremljena', 'success')
      closeCropperModal()
    } else {
      showNotification(data.error || 'Greška pri spremanju slike', 'error')
    }
  } catch (error: any) {
    console.error('Crop error:', error)
    showNotification('Greška pri izrezivanju slike', 'error')
  } finally {
    isCropping.value = false
  }
}

// Pagination functions
function goToPage(page: number) {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
  selectedProducts.value = [] // Clear selections when changing page
  fetchProducts()
  // Scroll to products list
  const productsSection = document.querySelector('.bg-white.rounded-lg.shadow-md.p-6')
  if (productsSection) {
    productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function goToNextPage() {
  if (currentPage.value < totalPages.value) {
    goToPage(currentPage.value + 1)
  }
}

function goToPreviousPage() {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1)
  }
}

// Computed property for displayed page numbers
const displayedPages = computed(() => {
  const pages: (number | string)[] = []
  const maxDisplayed = 7 // Maximum number of page buttons to show

  if (totalPages.value <= maxDisplayed) {
    // Show all pages if total is less than max
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // Always show first page
    pages.push(1)

    if (currentPage.value > 3) {
      pages.push('...')
    }

    // Show pages around current page
    const start = Math.max(2, currentPage.value - 1)
    const end = Math.min(totalPages.value - 1, currentPage.value + 1)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (currentPage.value < totalPages.value - 2) {
      pages.push('...')
    }

    // Always show last page
    pages.push(totalPages.value)
  }

  return pages
})

// Initialize
onMounted(() => {
  fetchBusiness()
  fetchProducts()
})

useSeoMeta({
  title: 'Upravljanje proizvodima - Popust.ba',
  description: 'Dodajte i upravljajte proizvodima za vaš biznis',
})
</script>
