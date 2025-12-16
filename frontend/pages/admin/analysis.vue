<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Analiza cijena</h1>
            <p class="mt-1 text-sm text-gray-600">Pretražite proizvode i uporedite cijene između trgovina</p>
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
            {{ isLoading ? 'Tražim...' : 'Pretraži' }}
          </button>
          <button
            v-if="products.length > 0"
            @click="clearSearch"
            class="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Očisti
          </button>
          <span v-if="total > 0" class="text-sm text-gray-500">
            Pronađeno {{ total }} proizvoda
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
            <div class="text-sm text-gray-500">Najniža cijena</div>
            <div class="text-xl font-semibold text-green-600">{{ formatPrice(priceStats.min) }} KM</div>
            <div class="text-xs text-gray-400">{{ priceStats.minStore }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Najviša cijena</div>
            <div class="text-xl font-semibold text-red-600">{{ formatPrice(priceStats.max) }} KM</div>
            <div class="text-xs text-gray-400">{{ priceStats.maxStore }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-500">Prosječna cijena</div>
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
          <!-- Logo for screenshots -->
          <div class="flex flex-col items-center justify-center mb-6">
            <img src="/logo.png" alt="Popust.ba" class="h-16" />
            <span class="text-2xl font-bold text-gray-800 mt-2">popust.ba</span>
          </div>
          <div class="flex gap-4 items-stretch">
            <!-- Chart -->
            <div class="flex-1 h-80 bg-white rounded-lg p-4 border border-gray-200">
              <canvas ref="chartCanvas"></canvas>
            </div>
            <!-- Selected Product Image (right side) -->
            <div v-if="selectedProductImage" class="w-64 flex-shrink-0 relative">
              <button @click="selectedProductImage = null" class="absolute top-1 right-1 z-10 text-gray-400 hover:text-gray-600 bg-white rounded-full p-1 shadow">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <img
                v-if="selectedProductImage.image_path"
                :src="selectedProductImage.image_path"
                :alt="selectedProductImage.title"
                class="w-full h-80 object-contain"
              />
              <div v-else class="w-full h-80 bg-gray-50 flex items-center justify-center">
                <svg class="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
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
                  <div class="flex flex-col gap-1">
                    <button
                      @click="excludeProduct(product.id)"
                      class="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                      title="Izuzmi iz analize"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <button
                      @click="selectProductForChart(product)"
                      class="p-1 text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded"
                      title="Prikaži pored grafikona"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center">
                    <!-- Image -->
                    <div class="relative group mr-3 cursor-pointer" @click="openEditProduct(product)">
                      <img
                        v-if="product.image_path"
                        :src="product.image_path"
                        :alt="product.title"
                        class="w-10 h-10 rounded object-cover"
                      />
                      <div v-else class="w-10 h-10 rounded bg-gray-200 flex items-center justify-center">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div class="absolute inset-0 bg-black bg-opacity-50 rounded opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </div>
                    </div>
                    <!-- Title -->
                    <div class="flex-1">
                      <div class="cursor-pointer group" @click="openEditProduct(product)">
                        <div class="text-sm font-medium text-gray-900 group-hover:text-indigo-600">
                          {{ product.title }}
                          <svg class="w-3 h-3 inline-block ml-1 opacity-0 group-hover:opacity-100 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </div>
                      </div>
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
        <h3 class="mt-4 text-lg font-medium text-gray-900">Pretražite proizvode</h3>
        <p class="mt-2 text-sm text-gray-500">Unesite naziv proizvoda da vidite cijene u različitim trgovinama</p>
        <div class="mt-4 flex flex-wrap justify-center gap-2">
          <button @click="quickSearch('mlijeko')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">mlijeko</button>
          <button @click="quickSearch('alpsko')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">alpsko</button>
          <button @click="quickSearch('jogurt')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">jogurt</button>
          <button @click="quickSearch('pileća prsa')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">pileca prsa</button>
          <button @click="quickSearch('coca cola')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200">coca cola</button>
        </div>
      </div>
    </div>

    <!-- Edit Product Modal -->
    <div v-if="editingProduct" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeEditProduct">
      <div class="relative top-20 mx-auto p-8 border w-full max-w-5xl shadow-lg rounded-md bg-white">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h3 class="text-2xl font-bold text-gray-900">Uredi proizvod</h3>
            <p class="text-sm text-gray-500 mt-1">ID: {{ editingProduct.id }} | {{ editingProduct.business_name }}</p>
          </div>
          <button @click="closeEditProduct" class="text-gray-400 hover:text-gray-600">
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
                <div v-if="editImagePath" class="relative">
                  <img :src="editImagePath" :alt="editTitle" class="w-96 h-96 object-contain rounded-lg border-2 border-green-400 shadow-md bg-gray-50">
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
                  <img :src="getFullImageUrl(originalImagePath)" alt="Original" class="w-96 h-96 object-contain rounded-lg border-2 shadow-md bg-gray-50" :class="getFullImageUrl(originalImagePath) === editImagePath ? 'border-green-400' : 'border-gray-300 opacity-80'">
                  <span class="absolute -top-2 -right-2 px-3 py-1 text-xs font-bold text-white rounded-full shadow" :class="getFullImageUrl(originalImagePath) === editImagePath ? 'bg-green-500' : 'bg-gray-500'">Original</span>
                </div>
                <button
                  v-if="getFullImageUrl(originalImagePath) !== editImagePath"
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
                @click="($refs.imageInput as HTMLInputElement).click()"
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
                    :placeholder="editTitle || 'Unesite pojam za pretragu...'"
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
                      :class="editImagePath === getFullImageUrl(imgPath) ? 'border-green-500 ring-2 ring-green-300' : 'border-gray-200 hover:border-purple-400'"
                    >
                    <div
                      v-if="editImagePath === getFullImageUrl(imgPath)"
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
              v-model="editTitle"
              type="text"
              id="edit_title"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
            >
          </div>

          <!-- Price Info (read-only) -->
          <div class="text-sm text-gray-500 pt-2">
            Cijena: <span class="font-medium text-gray-900">{{ formatPrice(editingProduct.effective_price) }} KM</span>
            <span v-if="editingProduct.discount_price && editingProduct.discount_price < editingProduct.base_price" class="text-green-600 ml-2">
              (popust od {{ formatPrice(editingProduct.base_price) }} KM)
            </span>
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              @click="closeEditProduct"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Otkaži
            </button>
            <button
              type="submit"
              :disabled="isSaving"
              class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {{ isSaving ? 'Čuvam...' : 'Sačuvaj' }}
            </button>
          </div>
        </form>
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

const { get, put, post } = useApi()

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

// Editing state - full product edit
const editingProduct = ref<Product | null>(null)
const editTitle = ref('')
const editImagePath = ref('')
const isSaving = ref(false)

// Image suggestion state
const suggestedImages = ref<string[]>([])
const originalImagePath = ref<string | null>(null)
const isSuggestingImages = ref(false)
const isRevertingImage = ref(false)
const showSuggestedImages = ref(false)
const imageSearchQuery = ref('')
const isUploadingImage = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)

// Selected product image for chart display
const selectedProductImage = ref<Product | null>(null)

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

// Edit product popup functions
function openEditProduct(product: Product) {
  editingProduct.value = product
  editTitle.value = product.title
  editImagePath.value = product.image_path || ''
  originalImagePath.value = product.image_path || null
  suggestedImages.value = []
  showSuggestedImages.value = false
  imageSearchQuery.value = ''
}

function closeEditProduct() {
  editingProduct.value = null
  editTitle.value = ''
  editImagePath.value = ''
  originalImagePath.value = null
  suggestedImages.value = []
  showSuggestedImages.value = false
  imageSearchQuery.value = ''
}

// Suggest images function
async function suggestImages() {
  if (!editingProduct.value) return

  // Use custom query if provided, otherwise fall back to title
  const query = imageSearchQuery.value.trim() || editTitle.value
  if (!query) {
    alert('Unesite pojam za pretragu ili naziv proizvoda')
    return
  }

  isSuggestingImages.value = true
  try {
    const data = await post(`/api/admin/products/${editingProduct.value.id}/suggest-images`, { query })

    if (data.success) {
      suggestedImages.value = data.suggested_images || []
      if (data.original_image_path) {
        originalImagePath.value = data.original_image_path
      }
      if (suggestedImages.value.length > 0) {
        // Auto-expand the section to show the images
        showSuggestedImages.value = true
      } else {
        alert('Nisu pronađene slike za ovaj proizvod')
      }
    } else {
      alert(data.error || 'Greška pri pretrazi slika')
    }
  } catch (error: any) {
    console.error('Suggest images error:', error)
    alert('Greška pri pretrazi slika')
  } finally {
    isSuggestingImages.value = false
  }
}

async function selectSuggestedImage(imagePath: string) {
  if (!editingProduct.value) return

  try {
    const data = await post(`/api/admin/products/${editingProduct.value.id}/select-image`, {
      image_path: imagePath
    })

    if (data.success) {
      editImagePath.value = getFullImageUrl(data.image_path)
    } else {
      alert(data.error || 'Greška pri odabiru slike')
    }
  } catch (error: any) {
    console.error('Select image error:', error)
    alert('Greška pri odabiru slike')
  }
}

async function revertToOriginal() {
  if (!editingProduct.value || !originalImagePath.value) return

  isRevertingImage.value = true
  try {
    const data = await post(`/api/admin/products/${editingProduct.value.id}/revert-image`, {})

    if (data.success) {
      editImagePath.value = getFullImageUrl(data.image_path || originalImagePath.value)
    } else {
      alert(data.error || 'Greška pri vraćanju slike')
    }
  } catch (error: any) {
    console.error('Revert image error:', error)
    alert('Greška pri vraćanju slike')
  } finally {
    isRevertingImage.value = false
  }
}

async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('Slika je prevelika. Maksimalna veličina je 5MB.')
    return
  }

  // Validate file type
  if (!file.type.startsWith('image/')) {
    alert('Molimo odaberite sliku (JPG, PNG, GIF)')
    return
  }

  if (!editingProduct.value) return

  isUploadingImage.value = true
  try {
    const formData = new FormData()
    formData.append('image', file)

    // Get auth token
    const token = process.client ? localStorage.getItem('token') : null
    const config = useRuntimeConfig()
    const headers: HeadersInit = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(
      `${config.public.apiBase}/api/admin/products/${editingProduct.value.id}/upload-cropped-image`,
      {
        method: 'POST',
        headers,
        body: formData
      }
    )

    const data = await response.json()

    if (data.success) {
      editImagePath.value = getFullImageUrl(data.image_path)
    } else {
      alert(data.error || 'Greška pri uploadu slike')
    }
  } catch (error: any) {
    console.error('Upload error:', error)
    alert('Greška pri uploadu slike')
  } finally {
    isUploadingImage.value = false
    // Reset input
    if (input) input.value = ''
  }
}

function getFullImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const bucket = 'aipijaca'
  const region = 'eu-central-1'
  return `https://${bucket}.s3.${region}.amazonaws.com/${path}`
}

async function saveProduct() {
  if (!editingProduct.value) return

  isSaving.value = true
  try {
    await put(`/api/admin/products/${editingProduct.value.id}`, {
      title: editTitle.value,
      image_path: editImagePath.value
    })

    // Update local state
    const idx = products.value.findIndex(p => p.id === editingProduct.value!.id)
    if (idx !== -1) {
      products.value[idx].title = editTitle.value
      products.value[idx].image_path = editImagePath.value
    }

    closeEditProduct()
  } catch (error) {
    console.error('Save error:', error)
    alert('Greška pri spremanju')
  } finally {
    isSaving.value = false
  }
}

// Select product image for chart display
function selectProductForChart(product: Product) {
  selectedProductImage.value = product
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

  // Group products by store, keeping each product separate
  const storeGroups: Record<string, { products: Product[]; logo: string | null }> = {}

  filteredProducts.value.forEach(p => {
    if (!storeGroups[p.business_name]) {
      storeGroups[p.business_name] = { products: [], logo: p.business_logo }
    }
    storeGroups[p.business_name].products.push(p)
  })

  const storeNames = Object.keys(storeGroups)
  if (storeNames.length === 0) return // No data to show

  // Calculate average price per store for sorting
  const storeAvgPrices = storeNames.map(store => {
    const prices = storeGroups[store].products.map(p => p.effective_price)
    return prices.reduce((a, b) => a + b, 0) / prices.length
  })

  // Sort stores by average price (lowest first)
  const sortedStoreIndices = storeAvgPrices.map((_, i) => i).sort((a, b) => storeAvgPrices[a] - storeAvgPrices[b])
  const sortedStoreNames = sortedStoreIndices.map(i => storeNames[i])

  // Build flat arrays for each product bar, grouped by store
  const allProducts: Product[] = []
  const storeStartIndices: { storeName: string; startIdx: number; endIdx: number }[] = []

  sortedStoreNames.forEach(storeName => {
    const startIdx = allProducts.length
    // Sort products within store by price
    const storeProducts = [...storeGroups[storeName].products].sort((a, b) => a.effective_price - b.effective_price)
    allProducts.push(...storeProducts)
    storeStartIndices.push({ storeName, startIdx, endIdx: allProducts.length - 1 })
  })

  if (allProducts.length === 0) return

  // Find global min/max for coloring
  const allPrices = allProducts.map(p => p.effective_price)
  const globalMin = Math.min(...allPrices)
  const globalMax = Math.max(...allPrices)

  // Create labels (product titles truncated)
  const labels = allProducts.map(p => {
    const title = p.title.length > 20 ? p.title.substring(0, 20) + '...' : p.title
    return title
  })

  // Create colors based on price
  const backgroundColors = allProducts.map(p => {
    if (p.effective_price === globalMin) return 'rgba(34, 197, 94, 0.8)' // Green for lowest
    if (p.effective_price === globalMax) return 'rgba(239, 68, 68, 0.8)' // Red for highest
    return 'rgba(99, 102, 241, 0.8)' // Indigo for others
  })

  const borderColors = allProducts.map(p => {
    if (p.effective_price === globalMin) return 'rgb(34, 197, 94)'
    if (p.effective_price === globalMax) return 'rgb(239, 68, 68)'
    return 'rgb(99, 102, 241)'
  })

  // Custom plugin to draw store logos and separators
  const storeGroupPlugin = {
    id: 'storeGroupPlugin',
    afterDraw: (chart: any) => {
      const ctx = chart.ctx
      const xAxis = chart.scales.x
      const yAxis = chart.scales.y
      const chartArea = chart.chartArea

      storeStartIndices.forEach((group, groupIdx) => {
        const { storeName, startIdx, endIdx } = group

        // Calculate center position for this store group
        const startX = xAxis.getPixelForValue(startIdx)
        const endX = xAxis.getPixelForValue(endIdx)
        const centerX = (startX + endX) / 2
        const y = yAxis.bottom + 10

        // Draw vertical separator line before each store (except first)
        if (groupIdx > 0) {
          const prevEndX = xAxis.getPixelForValue(startIdx - 1)
          const separatorX = (prevEndX + startX) / 2
          ctx.save()
          ctx.strokeStyle = '#d1d5db'
          ctx.lineWidth = 2
          ctx.setLineDash([5, 5])
          ctx.beginPath()
          ctx.moveTo(separatorX, chartArea.top)
          ctx.lineTo(separatorX, chartArea.bottom + 70)
          ctx.stroke()
          ctx.restore()
        }

        const logoImg = logoImages.value.get(storeName)

        if (logoImg) {
          // Draw logo
          const logoSize = 36
          ctx.drawImage(logoImg, centerX - logoSize / 2, y, logoSize, logoSize)

          // Draw store name below logo
          ctx.fillStyle = '#374151'
          ctx.font = 'bold 11px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(storeName, centerX, y + logoSize + 12)
        } else {
          // No logo - just draw store name
          ctx.fillStyle = '#374151'
          ctx.font = 'bold 12px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(storeName, centerX, y + 20)
        }
      })
    }
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Cijena (KM)',
          data: allProducts.map(p => p.effective_price),
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          bottom: 75 // Extra space for logos and names
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            title: (context) => {
              const idx = context[0].dataIndex
              return allProducts[idx].title
            },
            label: (context) => {
              const idx = context.dataIndex
              const product = allProducts[idx]
              return `Cijena: ${product.effective_price.toFixed(2)} KM`
            },
            afterLabel: (context) => {
              const idx = context.dataIndex
              const product = allProducts[idx]
              const lines = [`Trgovina: ${product.business_name}`]
              if (product.discount_price && product.discount_price < product.base_price) {
                lines.push(`Redovna: ${product.base_price.toFixed(2)} KM`)
                lines.push(`Popust: -${product.discount_percent}%`)
              }
              return lines
            }
          }
        },
        // Display values on top of bars
        datalabels: {
          display: true,
          color: '#1f2937',
          anchor: 'end',
          align: 'top',
          rotation: -45,
          font: {
            weight: 'bold',
            size: 11
          },
          formatter: (value: number) => value.toFixed(2)
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: Math.max(...allPrices) * 1.25, // Expand by 25% to fit rotated labels
          title: {
            display: true,
            text: 'Cijena (KM)'
          }
        },
        x: {
          ticks: {
            display: false // Hide default labels, we use custom plugin
          },
          title: {
            display: false
          }
        }
      }
    },
    plugins: [storeGroupPlugin]
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
  description: 'Analiza i poređenje cijena proizvoda između trgovina',
})
</script>
