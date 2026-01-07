<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- No Business Access -->
      <div v-if="!isLoading && !business" class="bg-white rounded-lg shadow-md p-12 text-center">
        <svg class="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
        </svg>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Nemate pristup biznisu</h2>
        <p class="text-gray-600">Kontaktirajte administratora da vam dodijeli pristup biznisu.</p>
      </div>

      <!-- Loading -->
      <div v-else-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-orange-600">
          <svg class="animate-spin h-8 w-8" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Business Dashboard -->
      <template v-else>
        <!-- Header -->
        <div class="mb-8">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden">
              <img
                v-if="business.logo_path"
                :src="business.logo_path"
                :alt="business.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-2xl font-bold text-gray-400">{{ business.name?.charAt(0) }}</span>
            </div>
            <div>
              <h1 class="text-2xl font-bold text-gray-900">{{ business.name }}</h1>
              <div class="flex items-center gap-2 text-gray-500">
                <span>{{ business.city }}</span>
                <span v-if="business.is_open" class="flex items-center text-green-600">
                  <span class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                  Otvoreno
                </span>
              </div>
            </div>
          </div>
          <p v-if="business.description" class="text-gray-600">{{ business.description }}</p>
        </div>

        <!-- Simple Underline Tabs -->
        <div class="border-b border-gray-200 mb-6">
          <nav class="flex gap-6">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="tab.id !== 'coupons' && (activeTab = tab.id)"
              :disabled="tab.id === 'coupons'"
              :class="[
                'pb-3 text-sm font-medium border-b-2 transition-colors',
                tab.id === 'coupons'
                  ? 'border-transparent text-gray-300 cursor-not-allowed'
                  : activeTab === tab.id
                    ? 'border-orange-500 text-orange-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ tab.name }}
              <span v-if="tab.id === 'coupons'" class="ml-1 text-xs text-gray-400">(USKORO)</span>
            </button>
          </nav>
        </div>

        <!-- Tab: Products -->
        <div v-if="activeTab === 'products'" class="space-y-6">
          <!-- Subscriber Stats Widget with Chart -->
          <div class="bg-white rounded-xl shadow-lg p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">Pratitelji prodavnice</h3>
                <p class="text-sm text-gray-500">Korisnici koji prate vaše akcije</p>
              </div>
              <div class="text-right">
                <div class="text-3xl font-bold text-purple-600">{{ subscriberCount }}</div>
                <div class="text-xs text-gray-500">ukupno pratitelja</div>
              </div>
            </div>
            <!-- Line Chart -->
            <div class="h-48">
              <Line v-if="subscriberChartData" :data="subscriberChartData" :options="subscriberChartOptions" />
            </div>
          </div>

          <!-- Product Stats Widgets -->
          <div v-if="products.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <!-- Total Products -->
            <div class="bg-white rounded-lg shadow-md p-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                  </svg>
                </div>
                <div>
                  <div class="text-2xl font-bold text-gray-900">{{ productStats.totalCount }}</div>
                  <div class="text-xs text-gray-600">Ukupno proizvoda</div>
                </div>
              </div>
            </div>

            <!-- Discounted Products -->
            <div class="bg-white rounded-lg shadow-md p-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                  </svg>
                </div>
                <div>
                  <div class="text-2xl font-bold text-green-600">{{ productStats.discountedCount }}</div>
                  <div class="text-xs text-gray-600">Na popustu</div>
                </div>
              </div>
            </div>

            <!-- Average Price -->
            <div class="bg-white rounded-lg shadow-md p-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <div>
                  <div class="text-2xl font-bold text-gray-900">{{ productStats.avgPrice.toFixed(2) }}</div>
                  <div class="text-xs text-gray-600">Prosječna cijena (KM)</div>
                </div>
              </div>
            </div>

            <!-- Average Discount -->
            <div class="bg-white rounded-lg shadow-md p-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2zM10 8.5a.5.5 0 11-1 0 .5.5 0 011 0zm5 5a.5.5 0 11-1 0 .5.5 0 011 0z"></path>
                  </svg>
                </div>
                <div>
                  <div class="text-2xl font-bold text-orange-600">{{ productStats.avgDiscountPercent.toFixed(0) }}%</div>
                  <div class="text-xs text-gray-600">Prosječni popust</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Header with Add Button -->
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-lg font-semibold text-gray-900">Moji Proizvodi</h2>
            <div class="flex gap-3 w-full sm:w-auto">
              <input
                v-model="productSearch"
                type="text"
                placeholder="Pretraži..."
                class="flex-1 sm:w-48 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 bg-white"
                @keyup.enter="searchProducts"
              />
              <button
                @click="showAiUploadModal = true"
                class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm whitespace-nowrap"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                MEDIA
              </button>
              <button
                @click="openAddProduct"
                class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center gap-2 text-sm whitespace-nowrap"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                Dodaj
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="productsLoading" class="text-center py-8">
            <svg class="animate-spin h-8 w-8 mx-auto text-orange-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>

          <!-- Products Grid -->
          <div v-else-if="products.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div
              v-for="product in products"
              :key="product.id"
              class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow flex flex-col"
            >
              <!-- Product Image -->
              <div class="relative h-36 bg-white flex items-center justify-center flex-shrink-0">
                <img
                  v-if="product.image_path && !failedImageProducts.has(product.id)"
                  :src="getProductImageUrl(product.image_path)"
                  :alt="product.title"
                  class="h-full w-full object-contain p-2"
                  @error="failedImageProducts.add(product.id)"
                />
                <!-- Processing placeholder for failed/loading images -->
                <div v-else-if="product.image_path && failedImageProducts.has(product.id)" class="w-full h-full flex flex-col items-center justify-center text-orange-500 bg-orange-50">
                  <svg class="w-8 h-8 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                  <span class="text-xs mt-1">Slika se obrađuje...</span>
                </div>
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                </div>
                <!-- Discount badge -->
                <span
                  v-if="product.has_discount"
                  class="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded"
                >
                  -{{ Math.round((1 - product.discount_price / product.base_price) * 100) }}%
                </span>
              </div>

              <!-- Product Info -->
              <div class="p-3 flex flex-col flex-1">
                <h3 class="font-medium text-gray-900 text-sm leading-tight line-clamp-2 h-10">{{ product.title }}</h3>
                <div class="mt-1 flex items-baseline gap-1.5">
                  <span v-if="product.has_discount" class="text-base font-bold text-green-600">
                    {{ product.discount_price.toFixed(2) }} KM
                  </span>
                  <span
                    :class="product.has_discount ? 'text-xs text-gray-400 line-through' : 'text-base font-bold text-gray-900'"
                  >
                    {{ product.base_price.toFixed(2) }} KM
                  </span>
                </div>
                <div v-if="product.expires" class="text-xs text-gray-500 mt-1">
                  Ističe: {{ product.expires }}
                </div>

                <!-- Actions -->
                <div class="mt-auto pt-2 flex gap-1.5">
                  <button
                    @click="openEditProduct(product)"
                    class="flex-1 px-2 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-1"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                    Uredi
                  </button>
                  <button
                    @click="deleteProduct(product)"
                    class="px-2 py-1.5 bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="bg-white rounded-lg shadow-md p-12 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
            </svg>
            <p class="text-gray-500 mb-4">Nemate dodane proizvode.</p>
            <button
              @click="openAddProduct"
              class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
            >
              Dodaj prvi proizvod
            </button>
          </div>

          <!-- Pagination -->
          <div v-if="productsPagination.pages > 1" class="flex justify-center gap-2">
            <button
              v-for="page in productsPagination.pages"
              :key="page"
              @click="productsPagination.page = page; loadProducts()"
              :class="[
                'px-3 py-1 rounded',
                productsPagination.page === page
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              {{ page }}
            </button>
          </div>
        </div>

        <!-- Tab: KUPONI -->
        <div v-if="activeTab === 'coupons'" class="space-y-6">
          <!-- Sub-tabs for Kuponi -->
          <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="flex border-b border-gray-200">
              <button
                @click="couponSubTab = 'list'"
                :class="[
                  'flex-1 py-3 px-4 text-center font-medium text-sm transition-colors',
                  couponSubTab === 'list'
                    ? 'bg-orange-50 text-orange-600 border-b-2 border-orange-500'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                ]"
              >
                <div class="flex items-center justify-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                  </svg>
                  Moji Kuponi
                  <span v-if="coupons.length > 0" class="bg-gray-200 text-gray-700 text-xs px-1.5 py-0.5 rounded-full">
                    {{ coupons.length }}
                  </span>
                </div>
              </button>
              <button
                @click="couponSubTab = 'pending'"
                :class="[
                  'flex-1 py-3 px-4 text-center font-medium text-sm transition-colors relative',
                  couponSubTab === 'pending'
                    ? 'bg-orange-50 text-orange-600 border-b-2 border-orange-500'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                ]"
              >
                <div class="flex items-center justify-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  Redempcija
                  <span
                    v-if="pendingRedemptions.length > 0"
                    class="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full animate-pulse"
                  >
                    {{ pendingRedemptions.length }}
                  </span>
                </div>
              </button>
            </div>
          </div>

          <!-- Sub-tab: Coupons List -->
          <div v-if="couponSubTab === 'list'" class="space-y-6">
            <!-- Coupon Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-white rounded-lg shadow-md p-4 text-center">
                <div class="text-2xl font-bold text-orange-600">{{ businessStats.active_coupons }}</div>
                <div class="text-sm text-gray-600">Aktivnih kupona</div>
              </div>
              <div class="bg-white rounded-lg shadow-md p-4 text-center">
                <div class="text-2xl font-bold text-green-600">{{ businessStats.total_sold }}</div>
                <div class="text-sm text-gray-600">Prodano</div>
              </div>
              <div class="bg-white rounded-lg shadow-md p-4 text-center">
                <div class="text-2xl font-bold text-blue-600">{{ businessStats.pending_redemptions }}</div>
                <div class="text-sm text-gray-600">Čeka redempciju</div>
              </div>
              <div class="bg-white rounded-lg shadow-md p-4 text-center">
                <div class="text-2xl font-bold text-purple-600">{{ business.average_rating?.toFixed(1) || '0.0' }}</div>
                <div class="text-sm text-gray-600">Prosječna ocjena</div>
              </div>
            </div>

            <!-- Create Coupon Button -->
            <div class="flex justify-between items-center">
              <h2 class="text-lg font-semibold text-gray-900">Moji Kuponi</h2>
              <button
                v-if="business.can_create_coupon"
                @click="showCreateModal = true"
                class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center gap-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                Novi kupon
              </button>
              <span v-else class="text-sm text-gray-500">
                Maksimalan broj kupona ({{ business.max_coupons_allowed }}) dostignut
              </span>
            </div>

            <!-- Coupons List -->
            <div v-if="coupons.length > 0" class="space-y-4">
              <div
                v-for="coupon in coupons"
                :key="coupon.id"
                class="bg-white rounded-lg shadow-md p-6"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-2xl font-bold text-orange-600">{{ coupon.discount_percent }}%</span>
                      <h3 class="text-lg font-semibold text-gray-900">{{ coupon.article_name }}</h3>
                      <span
                        :class="[
                          'px-2 py-0.5 text-xs font-medium rounded-full',
                          coupon.is_active && coupon.remaining_quantity > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        ]"
                      >
                        {{ coupon.is_active && coupon.remaining_quantity > 0 ? 'Aktivan' : 'Neaktivan' }}
                      </span>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span class="text-gray-500">Cijena:</span>
                        <span class="font-medium text-green-600 ml-1">{{ coupon.final_price.toFixed(2) }} KM</span>
                      </div>
                      <div>
                        <span class="text-gray-500">Preostalo:</span>
                        <span class="font-medium ml-1">{{ coupon.remaining_quantity }}/{{ coupon.total_quantity }}</span>
                      </div>
                      <div>
                        <span class="text-gray-500">Prodano:</span>
                        <span class="font-medium ml-1">{{ coupon.stats.sold }}</span>
                      </div>
                      <div>
                        <span class="text-gray-500">Iskorišteno:</span>
                        <span class="font-medium ml-1">{{ coupon.stats.redeemed }}</span>
                      </div>
                    </div>
                  </div>

                  <button
                    @click="toggleCouponActive(coupon)"
                    :class="[
                      'px-3 py-1 text-sm rounded',
                      coupon.is_active ? 'text-gray-600 hover:bg-gray-100' : 'text-green-600 hover:bg-green-50'
                    ]"
                  >
                    {{ coupon.is_active ? 'Deaktiviraj' : 'Aktiviraj' }}
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="bg-white rounded-lg shadow-md p-12 text-center">
              <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
              </svg>
              <p class="text-gray-500 mb-4">Nemate kreirane kupone.</p>
              <button
                v-if="business.can_create_coupon"
                @click="showCreateModal = true"
                class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
              >
                Kreiraj prvi kupon
              </button>
            </div>
          </div>

          <!-- Sub-tab: Pending Redemptions -->
          <div v-if="couponSubTab === 'pending'" class="space-y-6">
            <!-- Redemption Input -->
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="font-medium text-gray-900 mb-4">Unesi kod kupona</h3>
              <div class="flex gap-3">
                <input
                  v-model="redemptionCode"
                  type="text"
                  maxlength="6"
                  placeholder="6-cifreni kod"
                  class="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-2xl font-mono tracking-widest text-center text-gray-900 bg-white"
                  @input="redemptionCode = redemptionCode.replace(/\D/g, '')"
                />
                <button
                  @click="redeemCoupon"
                  :disabled="redemptionCode.length !== 6"
                  class="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 font-medium"
                >
                  Potvrdi
                </button>
              </div>
              <p v-if="redemptionError" class="text-red-600 text-sm mt-2">{{ redemptionError }}</p>
              <p v-if="redemptionSuccess" class="text-green-600 text-sm mt-2">{{ redemptionSuccess }}</p>
            </div>

            <!-- Pending List -->
            <div v-if="pendingRedemptions.length > 0">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Kuponi koji čekaju redempciju</h3>
              <div class="space-y-4">
                <div
                  v-for="pending in pendingRedemptions"
                  :key="pending.id"
                  class="bg-white rounded-lg shadow-md p-4 flex items-center justify-between"
                >
                  <div>
                    <div class="font-medium text-gray-900">{{ pending.coupon.article_name }}</div>
                    <div class="text-sm text-gray-500">
                      {{ pending.user.name }} · Kod: <span class="font-mono font-bold">{{ pending.redemption_code }}</span>
                    </div>
                    <div class="text-xs text-gray-400">Kupljeno: {{ formatDate(pending.purchased_at) }}</div>
                  </div>
                  <button
                    @click="quickRedeem(pending.redemption_code)"
                    class="px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600"
                  >
                    Potvrdi
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="bg-white rounded-lg shadow-md p-12 text-center">
              <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <p class="text-gray-500">Nema kupona koji čekaju redempciju.</p>
            </div>
          </div>
        </div>

        <!-- Create Coupon Modal -->
        <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
          <div class="flex items-center justify-center min-h-screen px-4">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreateModal = false"></div>
            <div class="relative bg-white rounded-lg max-w-md w-full p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Kreiraj novi kupon</h3>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Naziv artikla *</label>
                  <input
                    v-model="newCoupon.article_name"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                    placeholder="npr. 1kg Mljeveno meso"
                  />
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Osnovna cijena (KM) *</label>
                    <input
                      v-model.number="newCoupon.normal_price"
                      type="number"
                      step="0.01"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Popust (%) *</label>
                    <input
                      v-model.number="newCoupon.discount_percent"
                      type="number"
                      min="1"
                      max="99"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Broj kupona *</label>
                    <input
                      v-model.number="newCoupon.total_quantity"
                      type="number"
                      min="1"
                      max="100"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Validnost (dana) *</label>
                    <select v-model.number="newCoupon.valid_days" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white">
                      <option v-for="d in 10" :key="d" :value="d">{{ d }}</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Količina</label>
                  <input
                    v-model="newCoupon.quantity_description"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                    placeholder="npr. 1kg, 500g"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Opis</label>
                  <textarea
                    v-model="newCoupon.description"
                    rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                  ></textarea>
                </div>

                <!-- Preview -->
                <div v-if="newCoupon.normal_price && newCoupon.discount_percent" class="bg-orange-50 rounded-lg p-3 text-sm">
                  <div class="font-medium text-orange-800">Pregled:</div>
                  <div>Finalna cijena: <span class="font-bold text-green-600">{{ calculateFinalPrice() }} KM</span></div>
                  <div>Ušteda: {{ calculateSavings() }} KM</div>
                </div>
              </div>

              <div class="mt-6 flex gap-3 justify-end">
                <button
                  @click="showCreateModal = false"
                  class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Otkaži
                </button>
                <button
                  @click="createCoupon"
                  :disabled="!isValidCoupon"
                  class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
                >
                  Kreiraj
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Product Modal (Add/Edit) - LARGE with AI Image Search -->
        <div v-if="showProductModal" class="fixed inset-0 z-50 overflow-y-auto">
          <div class="flex items-center justify-center min-h-screen px-4 py-6">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showProductModal = false"></div>
            <div class="relative bg-white rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden">
              <!-- Header -->
              <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <div class="flex items-center justify-between">
                  <h3 class="text-xl font-bold text-gray-900">
                    {{ editingProduct ? 'Uredi proizvod' : 'Dodaj novi proizvod' }}
                  </h3>
                  <button @click="showProductModal = false" class="text-gray-400 hover:text-gray-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Body -->
              <div class="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
                <!-- Image Section (only when editing) -->
                <div v-if="editingProduct" class="bg-gray-50 rounded-lg p-4">
                  <label class="block text-sm font-medium text-gray-700 mb-3">Slika proizvoda</label>
                  <div class="flex gap-4">
                    <!-- Current Image -->
                    <div class="flex-shrink-0">
                      <div class="w-32 h-32 bg-white rounded-lg border-2 border-dashed border-gray-300 overflow-hidden flex items-center justify-center">
                        <img
                          v-if="editingProduct.image_path"
                          :src="getProductImageUrl(editingProduct.image_path)"
                          :alt="editingProduct.title"
                          class="w-full h-full object-contain"
                        />
                        <div v-else class="text-gray-400 text-center">
                          <svg class="w-10 h-10 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span class="text-xs">Nema slike</span>
                        </div>
                      </div>
                    </div>

                    <!-- AI Search Button & Upload -->
                    <div class="flex-1 space-y-3">
                      <button
                        @click="loadImageSuggestionsInModal"
                        :disabled="isLoadingImageSuggestions"
                        class="w-full px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors flex items-center justify-center gap-2 disabled:bg-gray-400"
                      >
                        <svg v-if="isLoadingImageSuggestions" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        {{ isLoadingImageSuggestions ? 'Tražim...' : 'AI Traži sliku' }}
                      </button>

                      <label class="block cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          class="hidden"
                          @change="uploadProductImageInModal($event)"
                        />
                        <span class="block text-center px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
                          {{ modalImageUploading ? 'Uploadujem...' : 'Ili upload sa uređaja' }}
                        </span>
                      </label>
                    </div>
                  </div>

                  <!-- Image Suggestions Grid -->
                  <div v-if="imageSuggestions.length > 0" class="mt-4">
                    <p class="text-sm text-gray-600 mb-2">Klikni na sliku da je postaviš:</p>
                    <div class="grid grid-cols-4 gap-2">
                      <div
                        v-for="(img, idx) in imageSuggestions"
                        :key="idx"
                        class="aspect-square bg-white rounded-lg border-2 border-gray-200 overflow-hidden cursor-pointer hover:border-purple-500 hover:shadow-md transition-all"
                        :class="{ 'border-green-500 ring-2 ring-green-200': settingImageIndex === idx }"
                        @click="selectSuggestedImage(img, idx)"
                      >
                        <img
                          :src="img"
                          :alt="'Suggestion ' + (idx + 1)"
                          class="w-full h-full object-contain"
                          @error="handleSuggestionImageError($event, idx)"
                        />
                      </div>
                      <!-- Refresh button -->
                      <div
                        class="aspect-square bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 cursor-pointer hover:bg-gray-200 transition-colors flex flex-col items-center justify-center"
                        @click="loadImageSuggestionsInModal"
                      >
                        <svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span class="text-xs text-gray-500 mt-1">Druge</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Product Details Form -->
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda *</label>
                    <input
                      v-model="newProduct.title"
                      type="text"
                      class="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      placeholder="npr. Meggle Mlijeko 1L"
                    />
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Osnovna cijena (KM) *</label>
                      <input
                        v-model.number="newProduct.base_price"
                        type="number"
                        step="0.01"
                        min="0"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Cijena na popustu</label>
                      <input
                        v-model.number="newProduct.discount_price"
                        type="number"
                        step="0.01"
                        min="0"
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                        placeholder="Ostavi prazno ako nema"
                      />
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Datum isteka (opciono)</label>
                    <input
                      v-model="newProduct.expires"
                      type="date"
                      class="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    />
                    <p class="mt-1 text-xs text-gray-500">Kategorija će se automatski odrediti nakon spremanja.</p>
                  </div>

                  <!-- Product Meta Fields (only when editing) -->
                  <div v-if="editingProduct" class="border-t border-gray-200 pt-4 mt-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-3">Detalji proizvoda</h4>

                    <div class="grid grid-cols-2 gap-4">
                      <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Brend</label>
                        <input
                          v-model="newProduct.brand"
                          type="text"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          placeholder="npr. Milka, Coca Cola"
                        />
                      </div>
                      <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Tip proizvoda</label>
                        <input
                          v-model="newProduct.product_type"
                          type="text"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          placeholder="npr. mlijeko, čokolada"
                        />
                      </div>
                    </div>

                    <div class="grid grid-cols-3 gap-4 mt-3">
                      <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Veličina</label>
                        <input
                          v-model.number="newProduct.size_value"
                          type="number"
                          step="0.01"
                          min="0"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          placeholder="1.5"
                        />
                      </div>
                      <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Jedinica</label>
                        <select
                          v-model="newProduct.size_unit"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                        >
                          <option value="">-</option>
                          <option value="L">L</option>
                          <option value="ml">ml</option>
                          <option value="kg">kg</option>
                          <option value="g">g</option>
                          <option value="kom">kom</option>
                        </select>
                      </div>
                      <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Varijanta</label>
                        <input
                          v-model="newProduct.variant"
                          type="text"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          placeholder="npr. lješnjak"
                        />
                      </div>
                    </div>
                  </div>

                  <!-- Error -->
                  <div v-if="productError" class="bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm">
                    {{ productError }}
                  </div>

                  <!-- Discount Preview -->
                  <div v-if="newProduct.base_price && newProduct.discount_price && newProduct.discount_price < newProduct.base_price" class="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div class="flex items-center gap-3">
                      <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">
                        -{{ Math.round((1 - newProduct.discount_price / newProduct.base_price) * 100) }}%
                      </div>
                      <div>
                        <div class="font-medium text-green-800">Popust aktivan</div>
                        <div class="text-sm text-green-700">
                          Ušteda: {{ (newProduct.base_price - newProduct.discount_price).toFixed(2) }} KM
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Footer -->
              <div class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex gap-3 justify-end">
                <button
                  @click="showProductModal = false"
                  class="px-6 py-2.5 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-100"
                >
                  Otkaži
                </button>
                <button
                  @click="saveProduct"
                  :disabled="isSavingProduct"
                  class="px-6 py-2.5 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 disabled:bg-gray-400 flex items-center gap-2"
                >
                  <svg v-if="isSavingProduct" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {{ editingProduct ? 'Sačuvaj promjene' : 'Dodaj proizvod' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Upload Modal with Drag & Drop -->
        <div v-if="showAiUploadModal" class="fixed inset-0 z-50 overflow-y-auto">
          <div class="flex items-center justify-center min-h-screen px-4 py-6">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="closeAiUploadModal"></div>
            <div class="relative bg-white rounded-xl max-w-4xl w-full shadow-2xl overflow-hidden">
              <!-- Header -->
              <div class="bg-purple-600 px-6 py-4">
                <div class="flex items-center justify-between">
                  <h3 class="text-xl font-bold text-white flex items-center gap-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    MEDIA Upload
                  </h3>
                  <button @click="closeAiUploadModal" class="text-white hover:text-purple-200">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Body -->
              <div class="p-6">
                <!-- Upload Zone (before upload) -->
                <div v-if="aiUploadResults.length === 0 && !aiUploadProcessing">
                  <div
                    class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center transition-all"
                    :class="{ 'border-purple-500 bg-purple-50': isDragging }"
                    @dragover.prevent="isDragging = true"
                    @dragleave.prevent="isDragging = false"
                    @drop.prevent="handleDrop"
                  >
                    <input
                      ref="aiUploadInput"
                      type="file"
                      multiple
                      accept="image/*"
                      class="hidden"
                      @change="handleFileSelect"
                    />
                    <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                    </svg>
                    <p class="text-lg font-medium text-gray-700 mb-2">
                      Prevuci slike ovdje
                    </p>
                    <p class="text-sm text-gray-500 mb-4">
                      ili
                    </p>
                    <button
                      @click="$refs.aiUploadInput.click()"
                      class="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                    >
                      Izaberi slike
                    </button>
                    <p class="text-xs text-gray-400 mt-4">
                      Maksimalno 10 slika (JPG, PNG, WebP)
                    </p>
                  </div>
                </div>

                <!-- Processing State -->
                <div v-else-if="aiUploadProcessing" class="text-center py-12">
                  <svg class="animate-spin h-16 w-16 mx-auto text-purple-600 mb-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <p class="text-lg font-medium text-gray-700">AI analizira slike...</p>
                  <p class="text-sm text-gray-500 mt-2">{{ aiUploadProgress }}</p>
                </div>

                <!-- Results -->
                <div v-else class="space-y-4 max-h-[60vh] overflow-y-auto">
                  <div class="flex items-center justify-between mb-4">
                    <p class="text-sm text-gray-600">
                      Uspješno: {{ aiUploadResults.filter(r => r.success).length }} / {{ aiUploadResults.length }}
                    </p>
                    <button
                      @click="resetAiUpload"
                      class="text-sm text-purple-600 hover:text-purple-700"
                    >
                      Upload nove slike
                    </button>
                  </div>

                  <div
                    v-for="(result, idx) in aiUploadResults"
                    :key="idx"
                    class="bg-gray-50 rounded-lg p-4 flex gap-4"
                    :class="{ 'border-l-4 border-red-500': !result.success }"
                  >
                    <!-- Image Preview -->
                    <div class="flex-shrink-0 w-40 h-40 bg-white rounded-lg overflow-hidden border border-gray-200">
                      <img
                        v-if="result.image_base64"
                        :src="'data:image/jpeg;base64,' + result.image_base64"
                        class="w-full h-full object-contain"
                      />
                      <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    </div>

                    <!-- Product Data -->
                    <div class="flex-1 min-w-0">
                      <div v-if="result.success && result.data">
                        <input
                          v-model="result.data.title"
                          type="text"
                          class="w-full px-3 py-1.5 border border-gray-300 rounded text-sm font-medium text-gray-900 mb-2"
                          placeholder="Naziv proizvoda"
                        />
                        <div class="flex gap-2">
                          <div class="flex-1">
                            <label class="text-xs text-gray-500">Cijena (KM)</label>
                            <input
                              v-model.number="result.data.base_price"
                              type="number"
                              step="0.01"
                              class="w-full px-2 py-1 border border-gray-300 rounded text-sm text-gray-900"
                            />
                          </div>
                          <div class="flex-1">
                            <label class="text-xs text-gray-500">Akcijska cijena</label>
                            <input
                              v-model.number="result.data.discount_price"
                              type="number"
                              step="0.01"
                              class="w-full px-2 py-1 border border-gray-300 rounded text-sm text-gray-900"
                              placeholder="Opciono"
                            />
                          </div>
                        </div>
                        <div class="mt-2 flex flex-wrap items-center gap-2">
                          <span v-if="result.data.brand" class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{{ result.data.brand }}</span>
                          <span v-if="result.data.product_type" class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">{{ result.data.product_type }}</span>
                          <span v-if="result.data.size_value && result.data.size_unit" class="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">{{ result.data.size_value }}{{ result.data.size_unit }}</span>
                          <span v-else-if="result.data.weight_volume" class="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded">{{ result.data.weight_volume }}</span>
                          <span v-if="result.data.variant" class="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">{{ result.data.variant }}</span>
                          <span v-if="result.data.category" class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">{{ result.data.category }}</span>
                        </div>
                        <div v-if="result.data.description" class="mt-2">
                          <p class="text-xs text-gray-600 line-clamp-2">{{ result.data.description }}</p>
                        </div>
                        <div v-if="result.data.tags && result.data.tags.length" class="mt-2 flex flex-wrap gap-1">
                          <span v-for="tag in result.data.tags.slice(0, 6)" :key="tag" class="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{{ tag }}</span>
                          <span v-if="result.data.tags.length > 6" class="text-[10px] text-gray-400">+{{ result.data.tags.length - 6 }}</span>
                        </div>
                        <div class="mt-3 flex justify-end">
                          <button
                            @click="createProductFromAi(result)"
                            :disabled="result.creating"
                            class="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
                          >
                            {{ result.creating ? 'Kreiram...' : 'Kreiraj proizvod' }}
                          </button>
                        </div>
                      </div>
                      <div v-else class="text-red-600">
                        <p class="text-sm font-medium">Greška: {{ result.error || 'Nepoznata greška' }}</p>
                        <p class="text-xs text-gray-500">{{ result.filename }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Delete Confirmation Modal -->
      <div v-if="showDeleteModal" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-center justify-center min-h-screen px-4">
          <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="cancelDelete"></div>
          <div class="relative bg-white rounded-xl max-w-md w-full shadow-2xl p-6">
            <div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
              <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 text-center mb-2">Obrisati proizvod?</h3>
            <p class="text-gray-600 text-center mb-6">
              Da li ste sigurni da zelite obrisati "<strong>{{ productToDelete?.title }}</strong>"? Ova akcija se ne moze ponistiti.
            </p>
            <div class="flex gap-3">
              <button
                @click="cancelDelete"
                :disabled="isDeleting"
                class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-100 disabled:opacity-50"
              >
                Otkazi
              </button>
              <button
                @click="confirmDelete"
                :disabled="isDeleting"
                class="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <svg v-if="isDeleting" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {{ isDeleting ? 'Brisanje...' : 'Obrisi' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

definePageMeta({
  middleware: ['auth']
})

const { get, post, put, del, upload } = useApi()

const isLoading = ref(true)
const business = ref<any>(null)
const coupons = ref<any[]>([])
const pendingRedemptions = ref<any[]>([])
const businessStats = ref({
  active_coupons: 0,
  total_sold: 0,
  pending_redemptions: 0
})
const subscriberCount = ref(0)
const subscriberGrowthData = ref<{date: string, total: number}[]>([])

// Chart configuration
const subscriberChartData = computed(() => {
  if (!subscriberGrowthData.value.length) return null

  return {
    labels: subscriberGrowthData.value.map(d => {
      const date = new Date(d.date)
      return `${date.getDate()}.${date.getMonth() + 1}`
    }),
    datasets: [{
      label: 'Pratitelji',
      data: subscriberGrowthData.value.map(d => d.total),
      borderColor: '#7C3AED',
      backgroundColor: 'rgba(124, 58, 237, 0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 2,
      pointHoverRadius: 5
    }]
  }
})

const subscriberChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1f2937',
      titleColor: '#fff',
      bodyColor: '#fff',
      padding: 12,
      displayColors: false
    }
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#9CA3AF', font: { size: 11 } }
    },
    y: {
      beginAtZero: true,
      grid: { color: '#F3F4F6' },
      ticks: { color: '#9CA3AF', font: { size: 11 }, precision: 0 }
    }
  }
}

const activeTab = ref('products')
const tabs = [
  { id: 'products', name: 'PRODUKTI', icon: 'box' },
  { id: 'coupons', name: 'KUPONI', icon: 'ticket' }
]

// Sub-tabs for Kuponi section
const couponSubTab = ref<'list' | 'pending'>('list')

// Products state
const products = ref<any[]>([])
const productsLoading = ref(false)
const productsPagination = ref({
  page: 1,
  per_page: 20,
  total: 0,
  pages: 0
})
const productSearch = ref('')
const showProductModal = ref(false)
const showDeleteModal = ref(false)
const productToDelete = ref<any>(null)
const isDeleting = ref(false)
const editingProduct = ref<any>(null)
const newProduct = ref({
  title: '',
  base_price: 0,
  discount_price: null as number | null,
  expires: '',
  brand: '',
  product_type: '',
  size_value: null as number | null,
  size_unit: '',
  variant: ''
})
const productError = ref('')
const productUploading = ref(false)
const isSavingProduct = ref(false)

// Image suggestions for modal
const imageSuggestions = ref<string[]>([])
const isLoadingImageSuggestions = ref(false)
const settingImageIndex = ref<number | null>(null)
const modalImageUploading = ref(false)
const imageSearchAttempt = ref(0)

// AI Upload state
const showAiUploadModal = ref(false)
const aiUploadProcessing = ref(false)
const aiUploadProgress = ref('')
const aiUploadResults = ref<any[]>([])
const isDragging = ref(false)
const aiUploadInput = ref<HTMLInputElement | null>(null)

// Track products with failed image loads (S3 still processing)
const failedImageProducts = ref<Set<number>>(new Set())

// Redemption
const redemptionCode = ref('')
const redemptionError = ref('')
const redemptionSuccess = ref('')

// Create coupon
const showCreateModal = ref(false)
const newCoupon = ref({
  article_name: '',
  normal_price: 0,
  discount_percent: 50,
  total_quantity: 5,
  valid_days: 7,
  quantity_description: '',
  description: ''
})

const isValidCoupon = computed(() => {
  return newCoupon.value.article_name &&
    newCoupon.value.normal_price > 0 &&
    newCoupon.value.discount_percent >= 1 &&
    newCoupon.value.discount_percent <= 99 &&
    newCoupon.value.total_quantity >= 1
})

// Computed product stats
const productStats = computed(() => {
  const allProducts = products.value
  const totalCount = productsPagination.value.total || allProducts.length
  const discountedProducts = allProducts.filter(p => p.has_discount)
  const discountedCount = discountedProducts.length

  // Average base price
  const avgPrice = allProducts.length > 0
    ? allProducts.reduce((sum, p) => sum + p.base_price, 0) / allProducts.length
    : 0

  // Average discount percentage for discounted products
  const avgDiscountPercent = discountedProducts.length > 0
    ? discountedProducts.reduce((sum, p) => {
        const discountPercent = ((p.base_price - p.discount_price) / p.base_price) * 100
        return sum + discountPercent
      }, 0) / discountedProducts.length
    : 0

  // Price range
  const minPrice = allProducts.length > 0
    ? Math.min(...allProducts.map(p => p.has_discount ? p.discount_price : p.base_price))
    : 0
  const maxPrice = allProducts.length > 0
    ? Math.max(...allProducts.map(p => p.base_price))
    : 0

  return {
    totalCount,
    discountedCount,
    avgPrice,
    avgDiscountPercent,
    minPrice,
    maxPrice
  }
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  isLoading.value = true
  try {
    // Get user's business membership
    const membershipRes = await get('/api/user/business-membership')
    if (!membershipRes.business) {
      business.value = null
      return
    }

    business.value = membershipRes.business

    // Load products (default tab)
    await loadProducts()

    // Load subscriber count and growth data
    try {
      const subRes = await get(`/api/business/${business.value.id}/subscriber-count`)
      subscriberCount.value = subRes.subscriber_count || 0
      subscriberGrowthData.value = subRes.growth_data || []
    } catch (e) {
      console.error('Error loading subscriber count:', e)
    }

    // Load coupons
    const couponsRes = await get(`/api/business/${business.value.id}/coupons`)
    coupons.value = couponsRes.coupons || []
    business.value = { ...business.value, ...couponsRes.business }

    // Calculate stats
    businessStats.value.active_coupons = coupons.value.filter(c => c.is_active && c.remaining_quantity > 0).length
    businessStats.value.total_sold = coupons.value.reduce((acc, c) => acc + c.stats.sold, 0)
    businessStats.value.pending_redemptions = coupons.value.reduce((acc, c) => acc + c.stats.pending, 0)

    // Load pending redemptions
    const pendingRes = await get(`/api/business/${business.value.id}/pending-coupons`)
    pendingRedemptions.value = pendingRes.pending || []
  } catch (error) {
    console.error('Error loading data:', error)
    business.value = null
  } finally {
    isLoading.value = false
  }
}

// ==================== PRODUCTS FUNCTIONS ====================

async function loadProducts() {
  if (!business.value) return
  productsLoading.value = true
  // Clear failed images set to retry loading on refresh
  failedImageProducts.value.clear()
  try {
    const params = new URLSearchParams({
      page: productsPagination.value.page.toString(),
      per_page: productsPagination.value.per_page.toString()
    })
    if (productSearch.value) {
      params.append('search', productSearch.value)
    }
    const res = await get(`/api/business/${business.value.id}/products?${params}`)
    products.value = res.products || []
    productsPagination.value = res.pagination || productsPagination.value
  } catch (error) {
    console.error('Error loading products:', error)
  } finally {
    productsLoading.value = false
  }
}

function openAddProduct() {
  editingProduct.value = null
  newProduct.value = {
    title: '',
    base_price: 0,
    discount_price: null,
    expires: '',
    brand: '',
    product_type: '',
    size_value: null,
    size_unit: '',
    variant: ''
  }
  productError.value = ''
  showProductModal.value = true
}

function openEditProduct(product: any) {
  editingProduct.value = product
  newProduct.value = {
    title: product.title,
    base_price: product.base_price,
    discount_price: product.discount_price,
    expires: product.expires || '',
    brand: product.brand || '',
    product_type: product.product_type || '',
    size_value: product.size_value || null,
    size_unit: product.size_unit || '',
    variant: product.variant || ''
  }
  productError.value = ''
  // Reset image suggestion state
  imageSuggestions.value = []
  isLoadingImageSuggestions.value = false
  settingImageIndex.value = null
  imageSearchAttempt.value = 0
  showProductModal.value = true
}

async function saveProduct() {
  if (!business.value) return
  productError.value = ''

  if (!newProduct.value.title) {
    productError.value = 'Naziv proizvoda je obavezan'
    return
  }
  if (!newProduct.value.base_price || newProduct.value.base_price <= 0) {
    productError.value = 'Cijena mora biti veća od 0'
    return
  }

  try {
    const payload = {
      title: newProduct.value.title,
      base_price: newProduct.value.base_price,
      discount_price: newProduct.value.discount_price || null,
      expires: newProduct.value.expires || null,
      brand: newProduct.value.brand || null,
      product_type: newProduct.value.product_type || null,
      size_value: newProduct.value.size_value || null,
      size_unit: newProduct.value.size_unit || null,
      variant: newProduct.value.variant || null
    }

    if (editingProduct.value) {
      await put(`/api/business/${business.value.id}/products/${editingProduct.value.id}`, payload)
    } else {
      await post(`/api/business/${business.value.id}/products`, payload)
    }

    showProductModal.value = false
    await loadProducts()
  } catch (error: any) {
    productError.value = error.response?.data?.error || 'Greška pri spremanju proizvoda'
  }
}

function deleteProduct(product: any) {
  productToDelete.value = product
  showDeleteModal.value = true
}

async function confirmDelete() {
  if (!business.value || !productToDelete.value) return

  isDeleting.value = true
  try {
    await del(`/api/business/${business.value.id}/products/${productToDelete.value.id}`)
    showDeleteModal.value = false
    productToDelete.value = null
    await loadProducts()
  } catch (error: any) {
    alert(error.response?.data?.error || 'Greška pri brisanju proizvoda')
  } finally {
    isDeleting.value = false
  }
}

function cancelDelete() {
  showDeleteModal.value = false
  productToDelete.value = null
}

async function uploadProductImage(product: any, event: Event) {
  if (!business.value) return
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  const formData = new FormData()
  formData.append('file', file)

  productUploading.value = true
  try {
    await upload(`/api/business/${business.value.id}/products/${product.id}/image`, formData)
    await loadProducts()
  } catch (error: any) {
    alert(error.response?.data?.error || 'Greška pri uploadu slike')
  } finally {
    productUploading.value = false
    input.value = ''
  }
}

// Image URL helper
function getProductImageUrl(imagePath: string | null): string {
  if (!imagePath) return ''
  if (imagePath.startsWith('http')) return imagePath
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase || 'http://localhost:5001'
  // Local dev: serve /static/ paths from backend
  if (imagePath.startsWith('/static/')) {
    return `${apiBase}${imagePath}`
  }
  // Handle paths without /static/ prefix (e.g., uploads/product_images/...)
  if (imagePath.startsWith('uploads/')) {
    return `${apiBase}/static/${imagePath}`
  }
  return `https://aipijaca.s3.eu-central-1.amazonaws.com/${imagePath}`
}

// AI Upload functions
function closeAiUploadModal() {
  showAiUploadModal.value = false
  resetAiUpload()
}

function resetAiUpload() {
  aiUploadResults.value = []
  aiUploadProcessing.value = false
  aiUploadProgress.value = ''
  isDragging.value = false
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    processFiles(Array.from(files))
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    processFiles(Array.from(input.files))
  }
}

async function processFiles(files: File[]) {
  if (!business.value) return

  const imageFiles = files.filter(f => f.type.startsWith('image/'))
  if (imageFiles.length === 0) {
    alert('Nema odabranih slika')
    return
  }
  if (imageFiles.length > 10) {
    alert('Maksimalno 10 slika')
    return
  }

  aiUploadProcessing.value = true
  aiUploadProgress.value = `Pripremam ${imageFiles.length} slika...`

  const formData = new FormData()
  imageFiles.forEach(file => {
    formData.append('files', file)
  })

  try {
    aiUploadProgress.value = `AI analizira ${imageFiles.length} slika...`
    const response = await upload(`/api/business/${business.value.id}/products/bulk-ai-upload`, formData)
    aiUploadResults.value = response.results || []
    aiUploadProcessing.value = false
  } catch (error: any) {
    console.error('AI upload error:', error)
    aiUploadProcessing.value = false
    alert(error.response?.data?.error || 'Greška pri AI obradi slika')
  }
}

async function createProductFromAi(result: any) {
  if (!business.value || !result.data) return

  result.creating = true

  try {
    const productData = {
      title: result.data.title || 'Nepoznat proizvod',
      base_price: result.data.base_price || 0,
      discount_price: result.data.discount_price || null,
      expires: '',
      category: result.data.category || null,
      tags: result.data.tags || [],
      description: result.data.description || null,
      brand: result.data.brand || null,
      product_type: result.data.product_type || null,
      size_value: result.data.size_value || null,
      size_unit: result.data.size_unit || null,
      variant: result.data.variant || null,
      // Include image_base64 for direct S3 upload on backend
      image_base64: result.image_base64 || null
    }

    await post(`/api/business/${business.value.id}/products`, productData)

    result.created = true
    result.creating = false

    // Close the MEDIA upload modal
    showAiUploadModal.value = false
    aiUploadResults.value = []

    // Reload products
    await loadProducts()
  } catch (error: any) {
    console.error('Error creating product:', error)
    result.creating = false
    alert(error.response?.data?.error || 'Greška pri kreiranju proizvoda')
  }
}

// AI Image suggestion functions for modal
async function loadImageSuggestionsInModal() {
  if (!editingProduct.value || !business.value) return
  const businessId = business.value.id
  const productId = editingProduct.value.id

  imageSearchAttempt.value++
  isLoadingImageSuggestions.value = true
  imageSuggestions.value = []

  try {
    const data = await get(`/api/business/${businessId}/products/${productId}/suggest-images?attempt=${imageSearchAttempt.value}`)
    imageSuggestions.value = data.images || []
  } catch (error: any) {
    console.error('Error loading image suggestions:', error)
    alert(error.message || 'Greška pri učitavanju slika')
    imageSuggestions.value = []
  } finally {
    isLoadingImageSuggestions.value = false
  }
}

async function selectSuggestedImage(imageUrl: string, idx: number) {
  if (!editingProduct.value || !business.value) return
  const businessId = business.value.id
  const productId = editingProduct.value.id
  settingImageIndex.value = idx

  try {
    const response = await post(`/api/business/${businessId}/products/${productId}/set-image`, { image_url: imageUrl })

    // Update the editing product with the S3 path returned by backend
    if (response.image_path) {
      editingProduct.value.image_path = response.image_path
    }
    await loadProducts()

    // Clear suggestions after successful set
    imageSuggestions.value = []
  } catch (error: any) {
    console.error('Error setting product image:', error)
    alert(error.message || 'Greška pri postavljanju slike')
  } finally {
    settingImageIndex.value = null
  }
}

function handleSuggestionImageError(event: Event, idx: number) {
  // Remove the broken image from suggestions
  if (imageSuggestions.value[idx]) {
    imageSuggestions.value.splice(idx, 1)
  }
}

async function uploadProductImageInModal(event: Event) {
  if (!editingProduct.value || !business.value) return
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const file = input.files[0]
  const formData = new FormData()
  formData.append('file', file)

  modalImageUploading.value = true
  try {
    await upload(`/api/business/${business.value.id}/products/${editingProduct.value.id}/image`, formData)
    await loadProducts()
    // Update the editing product's image_path from the reloaded products
    const updatedProduct = products.value.find(p => p.id === editingProduct.value?.id)
    if (updatedProduct) {
      editingProduct.value.image_path = updatedProduct.image_path
    }
  } catch (error: any) {
    alert(error.response?.data?.error || 'Greška pri uploadu slike')
  } finally {
    modalImageUploading.value = false
    input.value = ''
  }
}

function searchProducts() {
  productsPagination.value.page = 1
  loadProducts()
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('bs-BA', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function calculateFinalPrice() {
  const price = newCoupon.value.normal_price * (1 - newCoupon.value.discount_percent / 100)
  return price.toFixed(2)
}

function calculateSavings() {
  const savings = newCoupon.value.normal_price - parseFloat(calculateFinalPrice())
  return savings.toFixed(2)
}

async function createCoupon() {
  if (!isValidCoupon.value || !business.value) return

  try {
    await post(`/api/business/${business.value.id}/coupons`, newCoupon.value)
    showCreateModal.value = false
    newCoupon.value = {
      article_name: '',
      normal_price: 0,
      discount_percent: 50,
      total_quantity: 5,
      valid_days: 7,
      quantity_description: '',
      description: ''
    }
    await loadData()
  } catch (error: any) {
    alert(error.response?.data?.error || 'Greška pri kreiranju kupona')
  }
}

async function toggleCouponActive(coupon: any) {
  try {
    await put(`/api/business/${business.value.id}/coupons/${coupon.id}`, {
      is_active: !coupon.is_active
    })
    await loadData()
  } catch (error) {
    console.error('Error toggling coupon:', error)
  }
}

async function redeemCoupon() {
  if (redemptionCode.value.length !== 6 || !business.value) return

  redemptionError.value = ''
  redemptionSuccess.value = ''

  try {
    const res = await post(`/api/business/${business.value.id}/redeem`, {
      code: redemptionCode.value
    })
    redemptionSuccess.value = `Kupon uspješno iskorišten! ${res.user_coupon.user_name} - ${res.user_coupon.article_name}`
    redemptionCode.value = ''
    await loadData()
  } catch (error: any) {
    redemptionError.value = error.response?.data?.error || 'Greška pri redempciji'
  }
}

async function quickRedeem(code: string) {
  redemptionCode.value = code
  await redeemCoupon()
}

useSeoMeta({
  title: 'Moj Biznis - Popust.ba',
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
