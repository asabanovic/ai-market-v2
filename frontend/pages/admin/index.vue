<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-gray-900">Admin Dashboard</h1>
        <p class="mt-1 text-sm text-gray-600">Pregled i upravljanje Popust.ba platformom</p>
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
        <!-- Admin Actions -->
        <div class="mb-8 bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Admin akcije</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <NuxtLink
              to="/business"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
              </svg>
              Upravljaj biznisom
            </NuxtLink>

            <NuxtLink
              to="/admin/products"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
              </svg>
              Svi proizvodi
            </NuxtLink>

            <NuxtLink
              to="/admin/users"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
              </svg>
              Svi korisnici
            </NuxtLink>

            <NuxtLink
              to="/admin/reports"
              class="inline-flex items-center px-4 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"></path>
              </svg>
              Prijave proizvoda
              <span v-if="stats.pending_reports > 0" class="ml-2 px-2 py-0.5 rounded-full text-xs bg-red-200 text-red-800">
                {{ stats.pending_reports }}
              </span>
            </NuxtLink>

            <NuxtLink
              to="/admin/images"
              class="inline-flex items-center px-4 py-2 border border-purple-300 rounded-md shadow-sm text-sm font-medium text-purple-700 bg-purple-50 hover:bg-purple-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              AI Image Matching
            </NuxtLink>

            <NuxtLink
              to="/admin/product-matches"
              class="inline-flex items-center px-4 py-2 border border-cyan-300 rounded-md shadow-sm text-sm font-medium text-cyan-700 bg-cyan-50 hover:bg-cyan-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
              </svg>
              Product Matching
            </NuxtLink>

            <NuxtLink
              to="/admin/search-quality"
              class="inline-flex items-center px-4 py-2 border border-yellow-300 rounded-md shadow-sm text-sm font-medium text-yellow-700 bg-yellow-50 hover:bg-yellow-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              Search Quality
            </NuxtLink>

            <NuxtLink
              to="/admin/feedback"
              class="inline-flex items-center px-4 py-2 border border-teal-300 rounded-md shadow-sm text-sm font-medium text-teal-700 bg-teal-50 hover:bg-teal-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
              </svg>
              Povratne informacije
            </NuxtLink>

            <NuxtLink
              to="/admin/engagement"
              class="inline-flex items-center px-4 py-2 border border-indigo-300 rounded-md shadow-sm text-sm font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              Engagement
            </NuxtLink>

            <NuxtLink
              to="/admin/analysis"
              class="inline-flex items-center px-4 py-2 border border-emerald-300 rounded-md shadow-sm text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
              </svg>
              Analiza cijena
            </NuxtLink>

            <NuxtLink
              to="/admin/credits"
              class="inline-flex items-center px-4 py-2 border border-pink-300 rounded-md shadow-sm text-sm font-medium text-pink-700 bg-pink-50 hover:bg-pink-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Krediti
            </NuxtLink>

            <NuxtLink
              to="/admin/emails"
              class="inline-flex items-center px-4 py-2 border border-orange-300 rounded-md shadow-sm text-sm font-medium text-orange-700 bg-orange-50 hover:bg-orange-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
              Email & Job Logs
            </NuxtLink>

            <NuxtLink
              to="/admin/retention"
              class="inline-flex items-center px-4 py-2 border border-green-300 rounded-md shadow-sm text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Povratak korisnika
            </NuxtLink>

            <NuxtLink
              to="/admin/ekskluzivni-popusti"
              class="inline-flex items-center px-4 py-2 border border-orange-300 rounded-md shadow-sm text-sm font-medium text-orange-700 bg-orange-50 hover:bg-orange-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
              </svg>
              Ekskluzivni Popusti
            </NuxtLink>

            <NuxtLink
              to="/admin/social-media"
              class="inline-flex items-center px-4 py-2 border border-blue-300 rounded-md shadow-sm text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path>
              </svg>
              Social Media
            </NuxtLink>
          </div>
        </div>

        <!-- Search Tester -->
        <div class="mb-8 bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Test pretrage</h3>
          <div class="space-y-4">
            <!-- Search Input and Slider -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Upit za pretragu</label>
                <div class="flex gap-2">
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="npr. nes kafa, badem, mlijeko..."
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    @keyup.enter="runSearchTest"
                  />
                  <button
                    @click="runSearchTest"
                    :disabled="searchLoading || !searchQuery.trim()"
                    class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span v-if="searchLoading">...</span>
                    <span v-else>Traži</span>
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Min. sličnost: <span class="text-indigo-600 font-bold">{{ minSimilarity.toFixed(2) }}</span>
                </label>
                <input
                  v-model.number="minSimilarity"
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div class="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.00</span>
                  <span>0.45 (default)</span>
                  <span>1.00</span>
                </div>
              </div>
            </div>

            <!-- Search Results -->
            <div v-if="searchResults" class="mt-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-medium text-gray-700">
                  Rezultati: <span class="text-indigo-600">{{ searchResults.products_count }}</span> proizvoda
                </h4>
                <span class="text-xs text-gray-500">
                  min_similarity: {{ searchResults.min_similarity }}
                </span>
              </div>

              <div v-if="searchResults.products_count === 0" class="text-center py-8 text-gray-500">
                Nema rezultata za upit "{{ searchResults.query }}" sa minimalnom sličnošću {{ searchResults.min_similarity }}
              </div>

              <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sličnost</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Proizvod</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Kategorija</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cijena</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Biznis</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="product in searchResults.products" :key="product.id" class="hover:bg-gray-50">
                      <td class="px-3 py-2 whitespace-nowrap">
                        <span
                          class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                          :class="getSimilarityClass(product.similarity_score)"
                        >
                          {{ (product.similarity_score * 100).toFixed(1) }}%
                        </span>
                      </td>
                      <td class="px-3 py-2">
                        <div class="flex items-center">
                          <img
                            v-if="product.image_url"
                            :src="product.image_url"
                            class="w-10 h-10 rounded object-cover mr-3"
                            :alt="product.title"
                          />
                          <div class="max-w-xs truncate text-sm text-gray-900">{{ product.title }}</div>
                        </div>
                      </td>
                      <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ product.category }}</td>
                      <td class="px-3 py-2 whitespace-nowrap">
                        <span v-if="product.discount_price" class="text-green-600 font-medium">{{ product.discount_price }} KM</span>
                        <span v-else class="text-gray-900">{{ product.base_price }} KM</span>
                      </td>
                      <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ product.business?.name }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno korisnika</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_users || 0 }}</dd>
                </dl>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-sm text-gray-600">
                <span class="text-green-600 font-medium">+{{ stats.today_users || 0 }}</span> danas
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno biznisa</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_businesses || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            <div class="mt-3 space-y-1">
              <div class="text-sm" :class="stats.products_without_embeddings > 0 ? 'text-orange-600' : 'text-green-600'">
                <span class="font-medium">{{ stats.products_with_embeddings || 0 }}/{{ stats.total_products || 0 }}</span> s embeddingom
                <span v-if="stats.products_without_embeddings > 0" class="text-orange-600 font-medium ml-1">
                  ({{ stats.products_without_embeddings }} čeka)
                </span>
              </div>
              <div class="text-sm" :class="stats.expired_products > 0 ? 'text-red-600' : 'text-green-600'">
                <span class="font-medium">{{ stats.active_products || 0 }}</span> aktivnih
                <span v-if="stats.expired_products > 0" class="text-red-600 font-medium ml-1">
                  ({{ stats.expired_products }} isteklo)
                </span>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg border border-gray-200 p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Ukupno pretraga</dt>
                  <dd class="text-2xl font-semibold text-gray-900">{{ stats.total_searches || 0 }}</dd>
                </dl>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-sm text-gray-600">
                <span class="text-green-600 font-medium">+{{ stats.today_searches || 0 }}</span> danas
              </div>
            </div>
          </div>
        </div>

        <!-- Monthly Activity -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Mjesečna aktivnost</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <dt class="text-sm font-medium text-gray-500">Novi korisnici ovaj mjesec</dt>
              <dd class="text-xl font-semibold text-blue-600">{{ stats.monthly_users || 0 }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-500">Pretrage ovaj mjesec</dt>
              <dd class="text-xl font-semibold text-green-600">{{ stats.monthly_searches || 0 }}</dd>
            </div>
          </div>
        </div>

        <!-- Recent Searches - Full Width Table -->
        <div class="bg-white rounded-lg border border-gray-200 mb-8">
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-900">Zadnjih 30 pretraga</h3>
            <p class="text-sm text-gray-500 mt-1">Sve pretrage sa informacijama o uređaju</p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vrijeme</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Upit</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uređaj</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Browser</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OS</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="search in recentSearches" :key="search.id" class="hover:bg-gray-50">
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDateTime(search.created_at) }}
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <p class="text-sm text-gray-900 max-w-xs truncate" :title="search.query">{{ search.query }}</p>
                      <span v-if="search.only_discounted" class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800" title="Samo popusti filter">
                        %
                      </span>
                    </div>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span v-if="search.user_name" class="text-sm text-indigo-600">{{ search.user_name }}</span>
                    <span v-else class="text-sm text-gray-400 italic">Anonimni</span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span
                      v-if="search.device_type"
                      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                      :class="{
                        'bg-blue-100 text-blue-800': search.device_type === 'desktop',
                        'bg-green-100 text-green-800': search.device_type === 'mobile',
                        'bg-purple-100 text-purple-800': search.device_type === 'tablet'
                      }"
                    >
                      <svg v-if="search.device_type === 'desktop'" class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M21 14H3V4h18m0-2H3c-1.11 0-2 .89-2 2v10c0 1.1.9 2 2 2h7v2H8v2h8v-2h-2v-2h7c1.1 0 2-.9 2-2V4c0-1.11-.9-2-2-2z"/>
                      </svg>
                      <svg v-else-if="search.device_type === 'mobile'" class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M17 1H7c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-2-2-2zm0 18H7V5h10v14z"/>
                      </svg>
                      <svg v-else class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19 4H5c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H5V6h14v12z"/>
                      </svg>
                      {{ search.device_type }}
                    </span>
                    <span v-else class="text-xs text-gray-400">-</span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ search.browser || '-' }}
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ search.os || '-' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Recent Activity - Users and Businesses -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Recent Users -->
          <div class="bg-white rounded-lg border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">Najnoviji korisnici</h3>
            </div>
            <div class="divide-y divide-gray-200">
              <div v-for="user in recentUsers" :key="user.id" class="px-6 py-4">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ user.first_name || user.email }}</p>
                    <p class="text-sm text-gray-500">{{ user.email }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">{{ formatDate(user.created_at) }}</p>
                    <span v-if="user.is_admin" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Admin</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Businesses -->
          <div class="bg-white rounded-lg border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">Najnoviji biznisi</h3>
            </div>
            <div class="divide-y divide-gray-200">
              <div v-for="business in recentBusinesses" :key="business.id" class="px-6 py-4">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ business.name }}</p>
                    <p class="text-sm text-gray-500">{{ business.city || 'Nepoznato' }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-500">ID: {{ business.id }}</p>
                    <p v-if="business.contact_phone" class="text-xs text-gray-500">{{ business.contact_phone }}</p>
                  </div>
                </div>
              </div>
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

const { post, get } = useApi()

const isLoading = ref(true)
const stats = ref<any>({})
const recentUsers = ref<any[]>([])
const recentSearches = ref<any[]>([])
const recentBusinesses = ref<any[]>([])
const searchesPagination = ref<any>(null)

// Search tester state
const searchQuery = ref('')
const minSimilarity = ref(0.45)
const searchLoading = ref(false)
const searchResults = ref<any>(null)

onMounted(async () => {
  await loadDashboardData()
})

async function loadDashboardData() {
  isLoading.value = true

  try {
    const data = await get('/api/admin/stats')
    stats.value = data.stats || {}
    recentUsers.value = data.recent_users || []
    recentSearches.value = data.recent_searches || []
    recentBusinesses.value = data.recent_businesses || []
    searchesPagination.value = data.searches_pagination
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadSearches(page: number) {
  try {
    const data = await get(`/api/admin/dashboard?searches_page=${page}`)
    recentSearches.value = data.recent_searches || []
    searchesPagination.value = data.searches_pagination
  } catch (error) {
    console.error('Error loading searches:', error)
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
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

// Search tester functions
async function runSearchTest() {
  if (!searchQuery.value.trim()) return

  searchLoading.value = true
  try {
    const data = await post('/api/admin/search-test', {
      query: searchQuery.value,
      min_similarity: minSimilarity.value,
      k: 20
    })
    searchResults.value = data
  } catch (error) {
    console.error('Search test error:', error)
    searchResults.value = { error: 'Greška pri pretrazi', products: [], products_count: 0 }
  } finally {
    searchLoading.value = false
  }
}

function getSimilarityClass(score: number) {
  if (score >= 0.6) return 'bg-green-100 text-green-800'
  if (score >= 0.5) return 'bg-blue-100 text-blue-800'
  if (score >= 0.45) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

useSeoMeta({
  title: 'Admin Dashboard - Popust.ba',
  description: 'Admin dashboard za upravljanje Popust.ba platformom',
})
</script>
