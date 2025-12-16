<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6 flex justify-between items-start">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Product Matching</h1>
          <p class="mt-1 text-sm text-gray-600">Pregled proizvoda grupiranih po match_key - uporedi cijene iste robe u različitim trgovinama</p>
        </div>
        <div class="flex gap-3">
          <NuxtLink
            to="/admin"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            Nazad
          </NuxtLink>
          <button
            @click="runMatchingJob"
            :disabled="isRunningJob"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="isRunningJob" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            {{ isRunningJob ? 'Pokrenuto...' : 'Pokreni Matching' }}
          </button>
        </div>
      </div>

      <!-- Job Status Alert -->
      <div v-if="jobStatus" class="mb-6 rounded-md p-4" :class="jobStatusClass">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg v-if="jobStatus.status === 'completed'" class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <svg v-else-if="jobStatus.status === 'error'" class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            <svg v-else class="animate-spin h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium" :class="jobStatusTextClass">
              {{ jobStatusTitle }}
            </h3>
            <div v-if="jobStatus.processed !== undefined" class="mt-1 text-sm" :class="jobStatusTextClass">
              Obrađeno: {{ jobStatus.processed }} / {{ jobStatus.total }} proizvoda
              <span v-if="jobStatus.matches_found">({{ jobStatus.matches_found }} matcheva pronađeno)</span>
            </div>
            <div v-if="jobStatus.error" class="mt-1 text-sm text-red-700">{{ jobStatus.error }}</div>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm font-medium text-gray-500">Proizvoda s match_key</div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">{{ stats.products_with_match_key || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm font-medium text-gray-500">Jedinstvenih ključeva</div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">{{ stats.unique_match_keys || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm font-medium text-gray-500">Ukupno matcheva</div>
          <div class="mt-1 text-2xl font-semibold text-indigo-600">{{ stats.total_matches || 0 }}</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm font-medium text-gray-500">Bez kategoriz.</div>
          <div class="mt-1 text-2xl font-semibold text-orange-600">{{ stats.products_missing_fields || 0 }}</div>
        </div>
      </div>

      <!-- Match Type Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          @click="setViewMode('clone')"
          class="bg-white rounded-lg border-2 p-4 text-left transition-colors"
          :class="viewMode === 'clone' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-gray-500">Clones</div>
              <div class="mt-1 text-xl font-semibold text-green-600">{{ stats.matches_by_type?.clone || 0 }}</div>
              <div class="text-xs text-gray-400 mt-1">Isti proizvod u različitim trgovinama</div>
            </div>
            <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
          </div>
        </button>
        <button
          @click="setViewMode('brand_variant')"
          class="bg-white rounded-lg border-2 p-4 text-left transition-colors"
          :class="viewMode === 'brand_variant' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-gray-500">Brand Variants</div>
              <div class="mt-1 text-xl font-semibold text-blue-600">{{ stats.matches_by_type?.brand_variant || 0 }}</div>
              <div class="text-xs text-gray-400 mt-1">Isti tip, različiti brand</div>
            </div>
            <svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
            </svg>
          </div>
        </button>
        <button
          @click="setViewMode('sibling')"
          class="bg-white rounded-lg border-2 p-4 text-left transition-colors"
          :class="viewMode === 'sibling' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-purple-300'"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-gray-500">Siblings</div>
              <div class="mt-1 text-xl font-semibold text-purple-600">{{ stats.matches_by_type?.sibling || 0 }}</div>
              <div class="text-xs text-gray-400 mt-1">Isti brand, različite veličine</div>
            </div>
            <svg class="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
          </div>
        </button>
      </div>

      <!-- View Mode Toggle -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex gap-2">
            <button
              @click="setViewMode('groups')"
              class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
              :class="viewMode === 'groups' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              Match Groups (po match_key)
            </button>
            <button
              @click="setViewMode('clone')"
              class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
              :class="viewMode === 'clone' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              Clones
            </button>
            <button
              @click="setViewMode('brand_variant')"
              class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
              :class="viewMode === 'brand_variant' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              Brand Variants
            </button>
            <button
              @click="setViewMode('sibling')"
              class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
              :class="viewMode === 'sibling' ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              Siblings
            </button>
          </div>
        </div>
      </div>

      <!-- Filters (only for groups view) -->
      <div v-if="viewMode === 'groups'" class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-[200px]">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Pretraži po match_key (npr. milka:čokolada:100g)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
              @keyup.enter="loadGroups"
            />
          </div>
          <label class="inline-flex items-center">
            <input
              v-model="onlyCrossStore"
              type="checkbox"
              class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span class="ml-2 text-sm text-gray-700">Samo cross-store (različite trgovine)</span>
          </label>
          <button
            @click="loadGroups"
            class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700"
          >
            Filtriraj
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Match Type View (clone, brand_variant, sibling) -->
      <div v-else-if="viewMode !== 'groups'" class="space-y-4">
        <div v-if="matches.length === 0" class="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Nema {{ viewModeLabel }} matcheva</h3>
          <p class="mt-1 text-sm text-gray-500">Pokrenite matching job da pronađete matcheve.</p>
        </div>

        <div v-for="match in matches" :key="match.id" class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span
                class="px-2 py-1 rounded text-xs font-medium"
                :class="{
                  'bg-green-100 text-green-800': match.match_type === 'clone',
                  'bg-blue-100 text-blue-800': match.match_type === 'brand_variant',
                  'bg-purple-100 text-purple-800': match.match_type === 'sibling'
                }"
              >
                {{ match.match_type }}
              </span>
              <span class="text-xs text-gray-500">Confidence: {{ match.confidence }}%</span>
            </div>
            <span class="text-xs text-gray-400">{{ formatDate(match.created_at) }}</span>
          </div>
          <div class="grid grid-cols-2 divide-x divide-gray-200">
            <div
              class="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              @click="openProductDetail(match.product_a)"
            >
              <div class="flex items-start gap-3">
                <img
                  v-if="match.product_a?.image_url"
                  :src="match.product_a.image_url"
                  :alt="match.product_a.title"
                  class="h-16 w-16 rounded object-cover flex-shrink-0"
                />
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-medium text-gray-900 truncate">{{ match.product_a?.title }}</div>
                  <div class="text-xs text-gray-500">{{ match.product_a?.business_name }}</div>
                  <div class="mt-1 flex items-center gap-2">
                    <span v-if="match.product_a?.discount_price" class="text-sm font-bold text-green-600">
                      {{ match.product_a.discount_price.toFixed(2) }} KM
                    </span>
                    <span v-else class="text-sm font-medium text-gray-900">
                      {{ match.product_a?.base_price?.toFixed(2) || '-' }} KM
                    </span>
                  </div>
                  <div class="text-xs text-gray-400 mt-1">
                    {{ match.product_a?.brand }} · {{ match.product_a?.size_value }}{{ match.product_a?.size_unit }}
                  </div>
                </div>
              </div>
            </div>
            <div
              class="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              @click="openProductDetail(match.product_b)"
            >
              <div class="flex items-start gap-3">
                <img
                  v-if="match.product_b?.image_url"
                  :src="match.product_b.image_url"
                  :alt="match.product_b.title"
                  class="h-16 w-16 rounded object-cover flex-shrink-0"
                />
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-medium text-gray-900 truncate">{{ match.product_b?.title }}</div>
                  <div class="text-xs text-gray-500">{{ match.product_b?.business_name }}</div>
                  <div class="mt-1 flex items-center gap-2">
                    <span v-if="match.product_b?.discount_price" class="text-sm font-bold text-green-600">
                      {{ match.product_b.discount_price.toFixed(2) }} KM
                    </span>
                    <span v-else class="text-sm font-medium text-gray-900">
                      {{ match.product_b?.base_price?.toFixed(2) || '-' }} KM
                    </span>
                  </div>
                  <div class="text-xs text-gray-400 mt-1">
                    {{ match.product_b?.brand }} · {{ match.product_b?.size_value }}{{ match.product_b?.size_unit }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Matches Pagination -->
        <div v-if="matches.length > 0" class="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3">
          <div class="text-sm text-gray-700">
            Prikazano <span class="font-medium">{{ (matchesPage - 1) * matchesPerPage + 1 }}</span> -
            <span class="font-medium">{{ Math.min(matchesPage * matchesPerPage, matchesTotal) }}</span> od
            <span class="font-medium">{{ matchesTotal }}</span> matcheva
          </div>
          <div class="flex gap-2">
            <button
              @click="matchesPage--; loadMatches()"
              :disabled="matchesPage <= 1"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Prethodna
            </button>
            <span class="px-3 py-1 text-sm text-gray-700">
              {{ matchesPage }} / {{ matchesTotalPages }}
            </span>
            <button
              @click="matchesPage++; loadMatches()"
              :disabled="matchesPage >= matchesTotalPages"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Sljedeća
            </button>
          </div>
        </div>
      </div>

      <!-- Match Groups -->
      <div v-else-if="groups.length > 0" class="space-y-6">
        <div v-for="group in groups" :key="group.match_key" class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <!-- Group Header -->
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="font-mono text-sm bg-indigo-100 text-indigo-800 px-2 py-1 rounded">{{ group.match_key }}</span>
                <span class="text-sm text-gray-500">
                  {{ group.product_count }} proizvod{{ group.product_count > 1 ? 'a' : '' }}
                  u {{ group.store_count }} trgovin{{ group.store_count > 1 ? 'e' : 'i' }}
                </span>
              </div>
              <div class="flex items-center gap-4">
                <div v-if="group.price_spread > 0" class="text-sm">
                  <span class="text-gray-500">Razlika:</span>
                  <span class="font-medium text-orange-600">{{ group.price_spread.toFixed(2) }} KM</span>
                </div>
                <div class="text-sm">
                  <span class="text-green-600 font-medium">{{ group.lowest_price?.toFixed(2) }} KM</span>
                  <span v-if="group.lowest_price !== group.highest_price" class="text-gray-400">
                    - {{ group.highest_price?.toFixed(2) }} KM
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Products Table -->
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Slika</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Proizvod</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Trgovina</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cijena</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Info</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr
                  v-for="product in group.products"
                  :key="product.id"
                  :class="{'bg-green-50': isLowestPrice(product, group)}"
                  class="cursor-pointer hover:bg-gray-100 transition-colors"
                  @click="openProductDetail(product)"
                >
                  <td class="px-4 py-3 whitespace-nowrap">
                    <img
                      v-if="product.image_url"
                      :src="product.image_url"
                      :alt="product.title"
                      class="h-12 w-12 rounded object-cover"
                    />
                    <div v-else class="h-12 w-12 rounded bg-gray-200 flex items-center justify-center">
                      <svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                      </svg>
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-sm font-medium text-gray-900 max-w-xs truncate" :title="product.title">
                      {{ product.title }}
                    </div>
                    <div v-if="product.variant" class="text-xs text-gray-500">{{ product.variant }}</div>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span class="text-sm font-medium text-gray-900">{{ product.business_name }}</span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <div v-if="product.discount_price" class="space-y-1">
                      <div class="text-sm font-bold text-green-600">{{ product.discount_price.toFixed(2) }} KM</div>
                      <div class="text-xs text-gray-400 line-through">{{ product.base_price?.toFixed(2) }} KM</div>
                    </div>
                    <div v-else class="text-sm font-medium text-gray-900">
                      {{ product.base_price?.toFixed(2) || '-' }} KM
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-xs text-gray-500 space-y-0.5">
                      <div v-if="product.brand"><span class="text-gray-400">Brand:</span> {{ product.brand }}</div>
                      <div v-if="product.size_value">
                        <span class="text-gray-400">Veličina:</span> {{ product.size_value }}{{ product.size_unit }}
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pagination -->
        <div class="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3">
          <div class="text-sm text-gray-700">
            Prikazano <span class="font-medium">{{ (page - 1) * perPage + 1 }}</span> -
            <span class="font-medium">{{ Math.min(page * perPage, total) }}</span> od
            <span class="font-medium">{{ total }}</span> grupa
          </div>
          <div class="flex gap-2">
            <button
              @click="page--; loadGroups()"
              :disabled="page <= 1"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Prethodna
            </button>
            <span class="px-3 py-1 text-sm text-gray-700">
              {{ page }} / {{ totalPages }}
            </span>
            <button
              @click="page++; loadGroups()"
              :disabled="page >= totalPages"
              class="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Sljedeća
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Nema matcheva</h3>
        <p class="mt-1 text-sm text-gray-500">
          {{ onlyCrossStore ? 'Nema proizvoda koji se pojavljuju u više trgovina.' : 'Nema matchanih proizvoda. Pokrenite AI kategorizaciju i matching job.' }}
        </p>
      </div>

      <!-- Product Detail Modal -->
      <div v-if="selectedProduct" class="fixed inset-0 z-50 overflow-y-auto" @click.self="selectedProduct = null">
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
          <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="selectedProduct = null"></div>

          <div class="relative inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
            <!-- Modal Header -->
            <div class="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 class="text-lg font-medium text-gray-900">Detalji proizvoda</h3>
              <button @click="selectedProduct = null" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <!-- Modal Content -->
            <div class="px-6 py-4">
              <div class="flex gap-6">
                <!-- Product Image -->
                <div class="flex-shrink-0">
                  <img
                    v-if="selectedProduct.image_url"
                    :src="selectedProduct.image_url"
                    :alt="selectedProduct.title"
                    class="h-40 w-40 rounded-lg object-cover"
                  />
                  <div v-else class="h-40 w-40 rounded-lg bg-gray-200 flex items-center justify-center">
                    <svg class="h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                </div>

                <!-- Product Info -->
                <div class="flex-1 min-w-0">
                  <h4 class="text-lg font-semibold text-gray-900">{{ selectedProduct.title }}</h4>
                  <p class="text-sm text-gray-500 mt-1">{{ selectedProduct.business_name }}</p>

                  <!-- Price -->
                  <div class="mt-3">
                    <span v-if="selectedProduct.discount_price" class="text-2xl font-bold text-green-600">
                      {{ selectedProduct.discount_price.toFixed(2) }} KM
                    </span>
                    <span v-if="selectedProduct.discount_price && selectedProduct.base_price" class="ml-2 text-lg text-gray-400 line-through">
                      {{ selectedProduct.base_price.toFixed(2) }} KM
                    </span>
                    <span v-if="!selectedProduct.discount_price && selectedProduct.base_price" class="text-2xl font-bold text-gray-900">
                      {{ selectedProduct.base_price.toFixed(2) }} KM
                    </span>
                  </div>

                  <!-- Product ID -->
                  <div class="mt-2 text-xs text-gray-400">ID: {{ selectedProduct.id }}</div>
                </div>
              </div>

              <!-- Matching Fields Section -->
              <div class="mt-6 border-t border-gray-200 pt-4">
                <h5 class="text-sm font-semibold text-gray-900 mb-3">Matching polja</h5>
                <div class="grid grid-cols-2 gap-4">
                  <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-xs font-medium text-gray-500 uppercase">Brand</div>
                    <div class="mt-1 text-sm font-medium text-gray-900">{{ selectedProduct.brand || '-' }}</div>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-xs font-medium text-gray-500 uppercase">Product Type</div>
                    <div class="mt-1 text-sm font-medium text-gray-900">{{ selectedProduct.product_type || '-' }}</div>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-xs font-medium text-gray-500 uppercase">Size</div>
                    <div class="mt-1 text-sm font-medium text-gray-900">
                      {{ selectedProduct.size_value ? `${selectedProduct.size_value}${selectedProduct.size_unit || ''}` : '-' }}
                    </div>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-xs font-medium text-gray-500 uppercase">Variant</div>
                    <div class="mt-1 text-sm font-medium text-gray-900">{{ selectedProduct.variant || '-' }}</div>
                  </div>
                </div>

                <!-- Match Key -->
                <div class="mt-4 bg-indigo-50 rounded-lg p-3">
                  <div class="text-xs font-medium text-indigo-600 uppercase">Match Key</div>
                  <div class="mt-1 font-mono text-sm text-indigo-800">{{ selectedProduct.match_key || '-' }}</div>
                </div>
              </div>

              <!-- Related Products Section -->
              <div v-if="relatedProducts" class="mt-6 border-t border-gray-200 pt-4">
                <h5 class="text-sm font-semibold text-gray-900 mb-3">Povezani proizvodi</h5>

                <!-- Clones -->
                <div v-if="relatedProducts.clones?.length > 0" class="mb-4">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded">Clone</span>
                    <span class="text-xs text-gray-500">Isti proizvod u drugim trgovinama ({{ relatedProducts.clones.length }})</span>
                  </div>
                  <div class="space-y-2">
                    <div
                      v-for="clone in relatedProducts.clones.slice(0, 3)"
                      :key="clone.id"
                      class="flex items-center justify-between bg-gray-50 rounded p-2 text-sm cursor-pointer hover:bg-gray-100"
                      @click="openProductDetail(clone)"
                    >
                      <div class="flex items-center gap-2">
                        <img v-if="clone.image_url" :src="clone.image_url" class="h-8 w-8 rounded object-cover" />
                        <div>
                          <div class="font-medium text-gray-900 truncate max-w-[200px]">{{ clone.title }}</div>
                          <div class="text-xs text-gray-500">{{ clone.business_name }}</div>
                        </div>
                      </div>
                      <span class="font-bold" :class="clone.discount_price ? 'text-green-600' : 'text-gray-900'">
                        {{ (clone.discount_price || clone.base_price)?.toFixed(2) }} KM
                      </span>
                    </div>
                    <div v-if="relatedProducts.clones.length > 3" class="text-xs text-gray-500 text-center">
                      + još {{ relatedProducts.clones.length - 3 }} proizvoda
                    </div>
                  </div>
                </div>

                <!-- Brand Variants -->
                <div v-if="relatedProducts.brand_variants?.length > 0" class="mb-4">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">Brand Variant</span>
                    <span class="text-xs text-gray-500">Isti tip, drugi brand ({{ relatedProducts.brand_variants.length }})</span>
                  </div>
                  <div class="space-y-2">
                    <div
                      v-for="bv in relatedProducts.brand_variants.slice(0, 3)"
                      :key="bv.id"
                      class="flex items-center justify-between bg-gray-50 rounded p-2 text-sm cursor-pointer hover:bg-gray-100"
                      @click="openProductDetail(bv)"
                    >
                      <div class="flex items-center gap-2">
                        <img v-if="bv.image_url" :src="bv.image_url" class="h-8 w-8 rounded object-cover" />
                        <div>
                          <div class="font-medium text-gray-900 truncate max-w-[200px]">{{ bv.title }}</div>
                          <div class="text-xs text-gray-500">{{ bv.brand }} · {{ bv.business_name }}</div>
                        </div>
                      </div>
                      <span class="font-bold" :class="bv.discount_price ? 'text-green-600' : 'text-gray-900'">
                        {{ (bv.discount_price || bv.base_price)?.toFixed(2) }} KM
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Siblings -->
                <div v-if="relatedProducts.siblings?.length > 0">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 rounded">Sibling</span>
                    <span class="text-xs text-gray-500">Isti brand, druge veličine ({{ relatedProducts.siblings.length }})</span>
                  </div>
                  <div class="space-y-2">
                    <div
                      v-for="sib in relatedProducts.siblings.slice(0, 3)"
                      :key="sib.id"
                      class="flex items-center justify-between bg-gray-50 rounded p-2 text-sm cursor-pointer hover:bg-gray-100"
                      @click="openProductDetail(sib)"
                    >
                      <div class="flex items-center gap-2">
                        <img v-if="sib.image_url" :src="sib.image_url" class="h-8 w-8 rounded object-cover" />
                        <div>
                          <div class="font-medium text-gray-900 truncate max-w-[200px]">{{ sib.title }}</div>
                          <div class="text-xs text-gray-500">{{ sib.size_value }}{{ sib.size_unit }} · {{ sib.business_name }}</div>
                        </div>
                      </div>
                      <span class="font-bold" :class="sib.discount_price ? 'text-green-600' : 'text-gray-900'">
                        {{ (sib.discount_price || sib.base_price)?.toFixed(2) }} KM
                      </span>
                    </div>
                  </div>
                </div>

                <!-- No related products -->
                <div v-if="!relatedProducts.clones?.length && !relatedProducts.brand_variants?.length && !relatedProducts.siblings?.length" class="text-sm text-gray-500 text-center py-4">
                  Nema povezanih proizvoda
                </div>

                <!-- Loading related -->
                <div v-if="isLoadingRelated" class="flex items-center justify-center py-4">
                  <svg class="animate-spin h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="ml-2 text-sm text-gray-500">Učitavanje povezanih...</span>
                </div>
              </div>
            </div>

            <!-- Modal Footer -->
            <div class="bg-gray-50 px-6 py-3 flex justify-end">
              <button
                @click="selectedProduct = null"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
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

const { get, post } = useApi()

const isLoading = ref(true)
const isRunningJob = ref(false)
const stats = ref<any>({})
const groups = ref<any[]>([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)
const totalPages = ref(0)
const searchQuery = ref('')
const onlyCrossStore = ref(true)
const jobStatus = ref<any>(null)
const jobPollingInterval = ref<any>(null)

// View mode: 'groups' | 'clone' | 'brand_variant' | 'sibling'
const viewMode = ref<string>('groups')
const matches = ref<any[]>([])
const matchesPage = ref(1)
const matchesPerPage = ref(20)
const matchesTotal = ref(0)
const matchesTotalPages = ref(0)

// Product detail modal
const selectedProduct = ref<any>(null)
const relatedProducts = ref<any>(null)
const isLoadingRelated = ref(false)

const viewModeLabel = computed(() => {
  switch (viewMode.value) {
    case 'clone': return 'Clone'
    case 'brand_variant': return 'Brand Variant'
    case 'sibling': return 'Sibling'
    default: return ''
  }
})

const jobStatusClass = computed(() => {
  if (!jobStatus.value) return ''
  switch (jobStatus.value.status) {
    case 'completed': return 'bg-green-50'
    case 'error': return 'bg-red-50'
    default: return 'bg-blue-50'
  }
})

const jobStatusTextClass = computed(() => {
  if (!jobStatus.value) return ''
  switch (jobStatus.value.status) {
    case 'completed': return 'text-green-800'
    case 'error': return 'text-red-800'
    default: return 'text-blue-800'
  }
})

const jobStatusTitle = computed(() => {
  if (!jobStatus.value) return ''
  switch (jobStatus.value.status) {
    case 'completed': return 'Matching završen'
    case 'error': return 'Greška'
    case 'running': return 'Matching u toku...'
    case 'starting': return 'Pokrećem...'
    default: return jobStatus.value.status
  }
})

onMounted(async () => {
  await Promise.all([loadStats(), loadGroups()])
})

onUnmounted(() => {
  if (jobPollingInterval.value) {
    clearInterval(jobPollingInterval.value)
  }
})

async function loadStats() {
  try {
    const data = await get('/api/admin/products/match-stats')
    stats.value = data
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

async function loadGroups() {
  isLoading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value.toString(),
      per_page: perPage.value.toString(),
      only_cross_store: onlyCrossStore.value.toString()
    })
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    const data = await get(`/api/admin/products/match-groups?${params}`)
    groups.value = data.groups
    total.value = data.total
    totalPages.value = data.total_pages
  } catch (error) {
    console.error('Error loading groups:', error)
  } finally {
    isLoading.value = false
  }
}

async function runMatchingJob() {
  isRunningJob.value = true
  jobStatus.value = null

  try {
    const data = await post('/api/admin/products/match', {})

    if (data.status === 'already_running') {
      jobStatus.value = { status: 'running', ...data }
      startPolling(data.job_id)
    } else if (data.status === 'no_products') {
      jobStatus.value = { status: 'error', error: data.message }
      isRunningJob.value = false
    } else if (data.job_id) {
      jobStatus.value = { status: 'starting' }
      startPolling(data.job_id)
    }
  } catch (error) {
    console.error('Error starting job:', error)
    jobStatus.value = { status: 'error', error: 'Greška pri pokretanju job-a' }
    isRunningJob.value = false
  }
}

function startPolling(jobId: string) {
  if (jobPollingInterval.value) {
    clearInterval(jobPollingInterval.value)
  }

  jobPollingInterval.value = setInterval(async () => {
    try {
      const data = await get(`/api/admin/products/match/status/${jobId}`)
      jobStatus.value = data

      if (data.status === 'completed' || data.status === 'error') {
        clearInterval(jobPollingInterval.value)
        jobPollingInterval.value = null
        isRunningJob.value = false

        if (data.status === 'completed') {
          await Promise.all([loadStats(), loadGroups()])
        }
      }
    } catch (error) {
      console.error('Error polling job status:', error)
    }
  }, 2000)
}

function isLowestPrice(product: any, group: any): boolean {
  const price = product.discount_price || product.base_price
  return price !== null && price === group.lowest_price && group.store_count > 1
}

async function setViewMode(mode: string) {
  viewMode.value = mode
  isLoading.value = true

  if (mode === 'groups') {
    await loadGroups()
  } else {
    matchesPage.value = 1
    await loadMatches()
  }
}

async function loadMatches() {
  isLoading.value = true
  try {
    const params = new URLSearchParams({
      page: matchesPage.value.toString(),
      per_page: matchesPerPage.value.toString(),
      match_type: viewMode.value
    })
    const data = await get(`/api/admin/products/matches?${params}`)
    matches.value = data.matches || []
    matchesTotal.value = data.total || 0
    matchesTotalPages.value = Math.ceil(matchesTotal.value / matchesPerPage.value)
  } catch (error) {
    console.error('Error loading matches:', error)
    matches.value = []
  } finally {
    isLoading.value = false
  }
}

function formatDate(dateString: string): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function openProductDetail(product: any) {
  selectedProduct.value = product
  relatedProducts.value = null
  isLoadingRelated.value = true

  try {
    const data = await get(`/api/products/${product.id}/related`)
    relatedProducts.value = data
  } catch (error) {
    console.error('Error loading related products:', error)
    relatedProducts.value = { clones: [], brand_variants: [], siblings: [] }
  } finally {
    isLoadingRelated.value = false
  }
}

useSeoMeta({
  title: 'Product Matching - Admin - Popust.ba',
  description: 'Pregled i upravljanje product matching sistemom',
})
</script>
