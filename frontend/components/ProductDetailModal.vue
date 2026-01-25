<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/60 overflow-y-auto h-full w-full z-[100] flex items-start justify-center p-2 md:p-6"
      @click.self="closeModal"
    >
      <div class="relative bg-white rounded-lg shadow-xl max-w-5xl w-full my-2 md:my-6 animate-modal-in" @click.stop>
        <!-- Close Button -->
        <button
          @click="closeModal"
          class="absolute top-2 right-2 text-gray-400 hover:text-gray-600 transition-colors z-10 p-1 hover:bg-gray-100 rounded"
        >
          <Icon name="mdi:close" class="w-5 h-5" />
        </button>

        <!-- Header Row: Image + Product Info Side by Side -->
        <div class="p-4 border-b border-gray-100">
          <div class="flex gap-4">
            <!-- Square Image - Left Side -->
            <div class="relative w-28 h-28 md:w-36 md:h-36 flex-shrink-0 rounded-lg overflow-hidden bg-gray-50 border border-gray-100">
              <img
                v-if="product.image_path || product.product_image_url"
                :src="getImageUrl(product.image_path || product.product_image_url)"
                :alt="product.title"
                class="w-full h-full object-contain"
              />
              <div v-else class="flex items-center justify-center h-full text-gray-300">
                <Icon name="mdi:image-off" class="w-10 h-10" />
              </div>
              <!-- Discount Badge -->
              <div
                v-if="discountPercentage > 0"
                class="absolute top-1 right-1 bg-red-500 text-white px-1.5 py-0.5 rounded text-xs font-bold"
              >
                -{{ discountPercentage }}%
              </div>
              <!-- Contributor Badge Overlay (bottom of image) -->
              <div
                v-if="product.contributor_name"
                class="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-purple-900/90 via-purple-800/70 to-transparent px-1.5 py-1.5"
              >
                <div class="flex items-center gap-1.5 text-white text-[10px]">
                  <div class="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 ring-1 ring-white/50">
                    <Icon name="mdi:account" class="w-2.5 h-2.5 text-white" />
                  </div>
                  <span class="truncate">
                    Dodao/la <span class="font-semibold">{{ product.contributor_name }}</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- Product Info - Right Side -->
            <div class="flex-1 min-w-0">
              <!-- Title -->
              <h2 class="text-base md:text-lg font-semibold text-gray-900 leading-tight mb-2 line-clamp-2">
                {{ product.title }}
              </h2>

              <!-- Price Row -->
              <div class="flex items-baseline gap-2 mb-2">
                <span class="text-xl md:text-2xl font-bold text-green-600">
                  {{ formatPrice(product.discount_price || product.base_price) }} KM
                </span>
                <span
                  v-if="product.discount_price && product.base_price > product.discount_price"
                  class="text-sm text-gray-400 line-through"
                >
                  {{ formatPrice(product.base_price) }} KM
                </span>
                <span v-if="product.expires" class="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded ml-1">
                  do {{ formatBosnianDate(product.expires) }}
                </span>
              </div>

              <!-- Store + Actions Row -->
              <div class="flex flex-wrap items-center gap-2">
                <!-- Store Badge -->
                <div class="flex items-center gap-1.5 bg-gray-50 rounded px-2 py-1">
                  <div v-if="businessLogo && !businessLogoError" class="w-4 h-4 rounded overflow-hidden bg-white flex-shrink-0">
                    <img
                      :src="businessLogo"
                      :alt="product.business?.name"
                      class="w-full h-full object-contain"
                      @error="businessLogoError = true"
                    />
                  </div>
                  <div v-else class="w-4 h-4 bg-green-600 rounded flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
                    {{ product.business?.name?.[0] || '?' }}
                  </div>
                  <span class="text-xs font-medium text-gray-700">{{ product.business?.name || 'Nepoznato' }}</span>
                  <span class="text-[10px] text-gray-400">{{ product.city || product.business?.city || '' }}</span>
                </div>

                <!-- Voting -->
                <div class="flex items-center gap-1 bg-gray-100 rounded-lg px-2 py-1">
                  <button
                    @click="handleVote('up')"
                    :disabled="isVoting"
                    :class="[
                      'flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium transition-all',
                      userVote === 'up' ? 'bg-green-500 text-white' : 'bg-white text-gray-700 hover:bg-green-50 border border-gray-200'
                    ]"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                      <path d="M7.493 18.75c-.425 0-.82-.236-.975-.632A7.48 7.48 0 016 15.375c0-1.75.599-3.358 1.602-4.634.151-.192.373-.309.6-.397.473-.183.89-.514 1.212-.924a9.042 9.042 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75 2.25 2.25 0 012.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23h-.777zM2.331 10.977a11.969 11.969 0 00-.831 4.398 12 12 0 00.52 3.507c.26.85 1.084 1.368 1.973 1.368H4.9c.445 0 .72-.498.523-.898a8.963 8.963 0 01-.924-3.977c0-1.708.476-3.305 1.302-4.666.245-.403-.028-.959-.5-.959H4.25c-.832 0-1.612.453-1.918 1.227z" />
                    </svg>
                    <span>{{ voteStats.upvotes }}</span>
                  </button>
                  <button
                    @click="handleVote('down')"
                    :disabled="isVoting"
                    :class="[
                      'flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium transition-all',
                      userVote === 'down' ? 'bg-red-500 text-white' : 'bg-white text-gray-700 hover:bg-red-50 border border-gray-200'
                    ]"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                      <path d="M16.507 5.25c.425 0 .82.236.975.632A7.48 7.48 0 0118 8.625c0 1.75-.599 3.358-1.602 4.634-.151.192-.373.309-.6.397-.473.183-.89.514-1.212.924a9.042 9.042 0 01-2.861 2.4c-.723.384-1.35.956-1.653 1.715a4.498 4.498 0 00-.322 1.672V21a.75.75 0 01-.75.75 2.25 2.25 0 01-2.25-2.25c0-1.152.26-2.243.723-3.218.266-.558-.107-1.282-.725-1.282H3.622c-1.026 0-1.945-.694-2.054-1.715A12.137 12.137 0 011.5 12.375c0-2.767.94-5.313 2.649-7.521.388-.482.987-.729 1.605-.729h4.246c.483 0 .964.078 1.423.23l3.114 1.04a4.501 4.501 0 001.423.23h.777zM21.669 13.023a11.969 11.969 0 00.831-4.398 12 12 0 00-.52-3.507c-.26-.85-1.084-1.368-1.973-1.368H19.1c-.445 0-.72.498-.523.898.591 1.2.924 2.55.924 3.977a8.959 8.959 0 01-1.302 4.666c-.245.403.028.959.5.959h1.053c.832 0 1.612-.453 1.918-1.227z" />
                    </svg>
                    <span>{{ voteStats.downvotes }}</span>
                  </button>
                </div>

                <!-- Report -->
                <button
                  @click="openReportModal"
                  class="text-xs text-gray-400 hover:text-red-500 transition-colors px-1"
                  :class="{ 'cursor-not-allowed opacity-50': hasReported }"
                  :disabled="hasReported"
                  :title="hasReported ? 'Već prijavljeno' : 'Prijavi grešku'"
                >
                  <Icon name="mdi:flag-outline" class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Product Match Summary (shown when any matches found) -->
        <div
          v-if="matchSummary && !loadingRelated"
          class="px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-purple-50"
        >
          <div class="flex items-start gap-3">
            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
              <Icon name="mdi:magnify-scan" class="w-4 h-4 text-white" />
            </div>
            <div class="flex-1">
              <h4 class="text-sm font-semibold text-gray-800 mb-1">Šta smo pronašli</h4>
              <p class="text-sm text-gray-700 leading-relaxed">{{ matchSummary }}</p>
            </div>
          </div>
        </div>

        <!-- Price Comparison Chart (shown when 2+ clones exist) -->
        <div
          v-if="shouldShowPriceChart && !loadingRelated"
          class="px-4 py-3 border-b border-gray-100 bg-gray-50"
        >
          <div class="flex items-center gap-2 mb-2">
            <Icon name="mdi:chart-bar" class="w-4 h-4 text-blue-500" />
            <h3 class="text-sm font-medium text-gray-700">Uporedi cijene</h3>
            <span class="text-xs text-gray-400">({{ chartProducts.length }} {{ formatProdavnica(chartProducts.length) }})</span>
          </div>
          <div class="h-72 w-full">
            <canvas ref="priceChartCanvas"></canvas>
          </div>
        </div>

        <!-- Dashboard Content Area -->
        <div class="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
          <!-- Loading State -->
          <div v-if="loadingRelated" class="flex items-center justify-center py-6">
            <Icon name="mdi:loading" class="w-5 h-5 animate-spin text-gray-400" />
            <span class="ml-2 text-sm text-gray-500">Tražimo povezane proizvode...</span>
          </div>

          <!-- Price Alert Card (if cheaper clone exists) -->
          <div
            v-if="relatedProducts.clones.length > 0 && relatedProducts.clones.some(c => c.is_cheaper)"
            class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3"
          >
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="mdi:piggy-bank" class="w-4 h-4 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-semibold text-green-800">Uštedi novac!</h4>
                <p class="text-xs text-green-700 mt-0.5">
                  Pronašli smo ovaj proizvod jeftinije u drugoj prodavnici.
                  <span v-if="cheapestClone" class="font-medium">
                    Uštedi {{ Math.abs(cheapestClone.price_diff).toFixed(2) }} KM u {{ cheapestClone.business_name }}!
                  </span>
                </p>
              </div>
            </div>
          </div>

          <!-- Clones Section (Same product, different stores) -->
          <div v-if="relatedProducts.clones.length > 0" class="space-y-2">
            <div class="flex items-center gap-2">
              <Icon name="mdi:store-search" class="w-4 h-4 text-blue-500" />
              <h3 class="text-sm font-medium text-gray-700">Uporedi cijene</h3>
              <span class="text-xs text-gray-400">({{ relatedProducts.clones.length }} {{ formatProdavnica(relatedProducts.clones.length) }})</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div
                v-for="clone in relatedProducts.clones.slice(0, 6)"
                :key="clone.id"
                class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all cursor-pointer"
                @click="openProduct(clone.id)"
              >
                <!-- Product Image with overlay actions -->
                <div class="relative h-32 bg-gray-50">
                  <img
                    v-if="clone.image_path"
                    :src="getImageUrl(clone.image_path)"
                    :alt="clone.title"
                    class="w-full h-full object-contain p-2"
                  />
                  <div v-else class="flex items-center justify-center h-full text-gray-300">
                    <Icon name="mdi:image-off" class="w-8 h-8" />
                  </div>

                  <!-- Price diff badge -->
                  <div
                    v-if="clone.is_cheaper"
                    class="absolute top-2 left-2 bg-green-500 text-white px-2 py-0.5 rounded-full text-xs font-bold shadow-sm"
                  >
                    {{ Math.abs(clone.price_diff_pct) }}% jeftinije
                  </div>
                  <div
                    v-else-if="clone.is_more_expensive"
                    class="absolute top-2 left-2 bg-red-400 text-white px-2 py-0.5 rounded-full text-xs font-bold shadow-sm"
                  >
                    {{ clone.price_diff_pct }}% skuplje
                  </div>

                  <!-- Store badge -->
                  <div class="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-0.5 rounded text-xs font-medium">
                    {{ clone.business_name }}
                  </div>
                </div>

                <!-- Product Info -->
                <div class="p-3">
                  <h4 class="text-sm font-medium text-gray-900 line-clamp-2 min-h-[2.5rem] mb-2">
                    {{ clone.title }}
                  </h4>

                  <!-- Price Row -->
                  <div class="flex items-baseline gap-2 mb-3">
                    <span :class="[
                      'text-lg font-bold',
                      clone.is_cheaper ? 'text-green-600' : clone.is_more_expensive ? 'text-red-500' : 'text-gray-900'
                    ]">
                      {{ formatPrice(clone.effective_price) }} KM
                    </span>
                    <span
                      v-if="clone.discount_price && clone.base_price > clone.discount_price"
                      class="text-xs text-gray-400 line-through"
                    >
                      {{ formatPrice(clone.base_price) }} KM
                    </span>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center justify-between">
                    <div class="flex gap-1">
                      <!-- Favorite -->
                      <button
                        @click.stop="handleFavorite(clone.id)"
                        class="p-1.5 rounded-lg hover:bg-pink-50 transition-colors"
                        :class="{ 'bg-pink-100': isFavorited(clone.id) }"
                        title="Dodaj u favorite"
                      >
                        <Icon
                          :name="isFavorited(clone.id) ? 'mdi:heart' : 'mdi:heart-outline'"
                          class="w-4 h-4"
                          :class="isFavorited(clone.id) ? 'text-pink-600' : 'text-gray-400 hover:text-pink-600'"
                        />
                      </button>

                      <!-- Vote buttons -->
                      <button
                        @click.stop="handleQuickVote(clone.id, 'up')"
                        class="p-1.5 rounded-lg hover:bg-green-50 transition-colors text-gray-400 hover:text-green-600"
                        title="Preporuči"
                      >
                        <Icon name="mdi:thumb-up-outline" class="w-4 h-4" />
                      </button>
                      <button
                        @click.stop="handleQuickVote(clone.id, 'down')"
                        class="p-1.5 rounded-lg hover:bg-red-50 transition-colors text-gray-400 hover:text-red-600"
                        title="Ne preporučujem"
                      >
                        <Icon name="mdi:thumb-down-outline" class="w-4 h-4" />
                      </button>
                    </div>

                    <!-- Add to list -->
                    <button
                      @click.stop="handleAddToList(clone)"
                      class="flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg transition-colors"
                      title="Dodaj u korpu"
                    >
                      <Icon name="mdi:cart-plus" class="w-4 h-4" />
                      <span class="hidden sm:inline">Korpa</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Siblings Section (Same brand, different variants/sizes) -->
          <div v-if="relatedProducts.siblings.length > 0" class="space-y-2">
            <div class="flex items-center gap-2">
              <Icon name="mdi:resize" class="w-4 h-4 text-purple-500" />
              <h3 class="text-sm font-medium text-gray-700">Isti brend, druge varijante</h3>
              <span class="text-xs text-gray-400">({{ relatedProducts.siblings.length }})</span>
            </div>
            <div class="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory">
              <div
                v-for="sibling in relatedProducts.siblings"
                :key="sibling.id"
                class="flex-shrink-0 w-[180px] bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
                @click="openProduct(sibling.id)"
              >
                <!-- Product Image -->
                <div class="relative h-28 bg-gray-50">
                  <img
                    v-if="sibling.image_path"
                    :src="getImageUrl(sibling.image_path)"
                    :alt="sibling.title"
                    class="w-full h-full object-contain p-2"
                  />
                  <div v-else class="flex items-center justify-center h-full text-gray-300">
                    <Icon name="mdi:image-off" class="w-8 h-8" />
                  </div>

                  <!-- Size badge -->
                  <div class="absolute top-2 left-2 bg-purple-500 text-white px-2 py-0.5 rounded-full text-xs font-bold shadow-sm">
                    {{ sibling.size_value }}{{ sibling.size_unit || 'g' }}
                  </div>

                  <!-- Store badge -->
                  <div class="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-0.5 rounded text-xs">
                    {{ sibling.business_name }}
                  </div>
                </div>

                <!-- Product Info -->
                <div class="p-2">
                  <h4 class="text-xs font-medium text-gray-900 line-clamp-2 min-h-[2rem] mb-1">
                    {{ sibling.title }}
                  </h4>

                  <!-- Price -->
                  <div class="flex items-baseline gap-1 mb-2">
                    <span class="text-base font-bold text-gray-900">
                      {{ formatPrice(sibling.effective_price) }} KM
                    </span>
                    <span
                      v-if="sibling.discount_price && sibling.base_price > sibling.discount_price"
                      class="text-[10px] text-gray-400 line-through"
                    >
                      {{ formatPrice(sibling.base_price) }}
                    </span>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center justify-between">
                    <div class="flex gap-0.5">
                      <button
                        @click.stop="handleFavorite(sibling.id)"
                        class="p-1 rounded hover:bg-pink-50 transition-colors"
                        title="Favorite"
                      >
                        <Icon
                          :name="isFavorited(sibling.id) ? 'mdi:heart' : 'mdi:heart-outline'"
                          class="w-3.5 h-3.5"
                          :class="isFavorited(sibling.id) ? 'text-pink-600' : 'text-gray-400'"
                        />
                      </button>
                      <button
                        @click.stop="handleQuickVote(sibling.id, 'up')"
                        class="p-1 rounded hover:bg-green-50 transition-colors text-gray-400 hover:text-green-600"
                      >
                        <Icon name="mdi:thumb-up-outline" class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <button
                      @click.stop="handleAddToList(sibling)"
                      class="p-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                      title="Dodaj u korpu"
                    >
                      <Icon name="mdi:cart-plus" class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Brand Variants Section (Same product type, different brands) -->
          <div v-if="relatedProducts.brand_variants.length > 0" class="space-y-2">
            <div class="flex items-center gap-2">
              <Icon name="mdi:tag-multiple" class="w-4 h-4 text-orange-500" />
              <h3 class="text-sm font-medium text-gray-700">Alternativni brendovi</h3>
              <span class="text-xs text-gray-400">({{ relatedProducts.brand_variants.length }})</span>
            </div>
            <div class="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory">
              <div
                v-for="variant in relatedProducts.brand_variants"
                :key="variant.id"
                class="flex-shrink-0 w-[180px] bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
                @click="openProduct(variant.id)"
              >
                <!-- Product Image -->
                <div class="relative h-28 bg-gray-50">
                  <img
                    v-if="variant.image_path"
                    :src="getImageUrl(variant.image_path)"
                    :alt="variant.title"
                    class="w-full h-full object-contain p-2"
                  />
                  <div v-else class="flex items-center justify-center h-full text-gray-300">
                    <Icon name="mdi:image-off" class="w-8 h-8" />
                  </div>

                  <!-- Brand badge -->
                  <div class="absolute top-2 left-2 bg-orange-500 text-white px-2 py-0.5 rounded-full text-xs font-bold shadow-sm truncate max-w-[80%]">
                    {{ variant.brand || 'Drugi brend' }}
                  </div>

                  <!-- Price diff badge if cheaper -->
                  <div
                    v-if="variant.is_cheaper"
                    class="absolute top-2 right-2 bg-green-500 text-white px-1.5 py-0.5 rounded-full text-[10px] font-bold shadow-sm"
                  >
                    ↓{{ Math.abs(variant.price_diff_pct || 0) }}%
                  </div>

                  <!-- Store badge -->
                  <div class="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-0.5 rounded text-xs">
                    {{ variant.business_name }}
                  </div>
                </div>

                <!-- Product Info -->
                <div class="p-2">
                  <h4 class="text-xs font-medium text-gray-900 line-clamp-2 min-h-[2rem] mb-1">
                    {{ variant.title }}
                  </h4>

                  <!-- Price -->
                  <div class="flex items-baseline gap-1 mb-2">
                    <span :class="[
                      'text-base font-bold',
                      variant.is_cheaper ? 'text-green-600' : 'text-gray-900'
                    ]">
                      {{ formatPrice(variant.effective_price) }} KM
                    </span>
                    <span
                      v-if="variant.discount_price && variant.base_price > variant.discount_price"
                      class="text-[10px] text-gray-400 line-through"
                    >
                      {{ formatPrice(variant.base_price) }}
                    </span>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center justify-between">
                    <div class="flex gap-0.5">
                      <button
                        @click.stop="handleFavorite(variant.id)"
                        class="p-1 rounded hover:bg-pink-50 transition-colors"
                        title="Favorite"
                      >
                        <Icon
                          :name="isFavorited(variant.id) ? 'mdi:heart' : 'mdi:heart-outline'"
                          class="w-3.5 h-3.5"
                          :class="isFavorited(variant.id) ? 'text-pink-600' : 'text-gray-400'"
                        />
                      </button>
                      <button
                        @click.stop="handleQuickVote(variant.id, 'up')"
                        class="p-1 rounded hover:bg-green-50 transition-colors text-gray-400 hover:text-green-600"
                      >
                        <Icon name="mdi:thumb-up-outline" class="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <button
                      @click.stop="handleAddToList(variant)"
                      class="p-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                      title="Dodaj u korpu"
                    >
                      <Icon name="mdi:cart-plus" class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- No matches found -->
          <div
            v-if="!loadingRelated && relatedProducts.clones.length === 0 && relatedProducts.siblings.length === 0 && relatedProducts.brand_variants.length === 0"
            class="text-center py-4 text-gray-400"
          >
            <Icon name="mdi:information-outline" class="w-6 h-6 mx-auto mb-1" />
            <p class="text-xs">Nema povezanih proizvoda za prikaz</p>
          </div>

          <!-- Comments Section -->
          <div class="border-t border-gray-100 pt-4">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <Icon name="mdi:comment-text-outline" class="w-4 h-4 text-gray-400" />
                <h3 class="text-sm font-medium text-gray-700">Komentari</h3>
                <span class="text-xs text-gray-400">({{ comments.length }})</span>
              </div>
            </div>

            <!-- Add Comment -->
            <div v-if="isAuthenticated" class="mb-3">
              <textarea
                v-model="newComment"
                :disabled="isSubmittingComment"
                placeholder="Ostavite komentar (min 10 karaktera)..."
                rows="2"
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:border-purple-400 focus:ring-1 focus:ring-purple-200 outline-none transition-all resize-none"
                @input="validateComment"
              ></textarea>
              <div class="flex items-center justify-between mt-1">
                <span class="text-[10px] text-gray-400">{{ newComment.length }}/1000</span>
                <button
                  @click="submitComment"
                  :disabled="!commentValidation.isValid || isSubmittingComment"
                  class="px-3 py-1 text-xs bg-purple-600 text-white rounded font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  Objavi (+5 kredita)
                </button>
              </div>
            </div>
            <div v-else class="mb-3 p-2 bg-gray-50 rounded-lg text-center">
              <p class="text-xs text-gray-500">
                <NuxtLink to="/registracija" class="text-purple-600 hover:underline font-medium">Registrujte se</NuxtLink>
                da ostavite komentar
              </p>
            </div>

            <!-- Comments List -->
            <div class="space-y-2 max-h-40 overflow-y-auto">
              <div v-if="loadingComments" class="text-center py-3">
                <Icon name="mdi:loading" class="w-4 h-4 animate-spin text-gray-400 mx-auto" />
              </div>
              <div v-else-if="comments.length === 0" class="text-center py-3">
                <p class="text-xs text-gray-400">Budite prvi koji će ostaviti komentar</p>
              </div>
              <div
                v-else
                v-for="comment in comments"
                :key="comment.id"
                class="bg-gray-50 rounded-lg p-2"
              >
                <div class="flex items-start gap-2">
                  <div class="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
                    {{ comment.user.first_name?.[0] || '?' }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-0.5">
                      <span class="text-xs font-medium text-gray-700 truncate">{{ comment.user.first_name }}</span>
                      <span class="text-[10px] text-gray-400">{{ formatCommentDate(comment.created_at) }}</span>
                    </div>
                    <p class="text-xs text-gray-600 break-words">{{ comment.comment_text }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Report Modal -->
    <div
      v-if="showReportModal"
      class="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4"
      @click.self="closeReportModal"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-sm w-full p-4 animate-modal-in" @click.stop>
        <div class="text-center mb-4">
          <Icon name="mdi:flag" class="w-8 h-8 text-red-500 mx-auto mb-2" />
          <h3 class="text-base font-semibold text-gray-900">Prijavi grešku</h3>
          <p class="text-xs text-gray-500 mt-1">Pogrešna slika, cijena ili istekla akcija?</p>
        </div>

        <div v-if="!reportSubmitted">
          <textarea
            v-model="reportReason"
            placeholder="Opišite problem (opcionalno)..."
            rows="2"
            class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:border-red-400 focus:ring-1 focus:ring-red-200 outline-none transition-all resize-none mb-3"
          ></textarea>

          <div class="flex gap-2">
            <button
              @click="closeReportModal"
              class="flex-1 px-3 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Odustani
            </button>
            <button
              @click="submitReport"
              :disabled="isSubmittingReport"
              class="flex-1 px-3 py-2 text-sm bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 disabled:opacity-50 transition-colors"
            >
              {{ isSubmittingReport ? '...' : 'Prijavi (+5)' }}
            </button>
          </div>
        </div>

        <div v-else class="text-center">
          <Icon name="mdi:check-circle" class="w-10 h-10 text-green-500 mx-auto mb-2" />
          <p class="text-sm text-gray-700 mb-3">Hvala na prijavi! +5 kredita</p>
          <button
            @click="closeReportModal"
            class="px-4 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Zatvori
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { Chart, registerables } from 'chart.js'
import ChartDataLabels from 'chartjs-plugin-datalabels'
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'

// Register Chart.js components
Chart.register(...registerables, ChartDataLabels)

const props = defineProps<{
  show: boolean
  product: any
}>()

const emit = defineEmits<{
  close: []
}>()

const config = useRuntimeConfig()
const router = useRouter()
const { get, post, put } = useApi()
const { isAuthenticated, user, refreshUser } = useAuth()
const { triggerCreditAnimation } = useCreditAnimation()
const { refreshCredits, deductCredits } = useSearchCredits()
const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()
const { showSuccess, handleApiError } = useCreditsToast()

// State
const comments = ref<any[]>([])
const loadingComments = ref(false)
const voteStats = ref({ upvotes: 0, downvotes: 0 })
const userVote = ref<string | null>(null)
const isVoting = ref(false)

const newComment = ref('')
const isSubmittingComment = ref(false)
const commentValidation = ref({ isValid: false, message: '' })
const businessLogoError = ref(false)

// Report state
const showReportModal = ref(false)
const reportReason = ref('')
const isSubmittingReport = ref(false)
const reportSubmitted = ref(false)
const hasReported = ref(false)

// Related products state
const relatedProducts = ref<{
  clones: any[]
  brand_variants: any[]
  siblings: any[]
  source_product: any
}>({
  clones: [],
  brand_variants: [],
  siblings: [],
  source_product: null
})
const loadingRelated = ref(false)
const creditDeducted = ref(false)

// Price comparison chart state
const priceChartCanvas = ref<HTMLCanvasElement | null>(null)
let priceChartInstance: Chart | null = null
const logoImages = ref<Map<string, HTMLImageElement>>(new Map())

// Helper for Serbian/Bosnian noun declension (prodavnica/prodavnice/prodavnica)
function formatProdavnica(count: number): string {
  if (count === 1) return 'prodavnica'
  if (count >= 2 && count <= 4) return 'prodavnice'
  return 'prodavnica' // 5+, 0
}

function formatProdavnici(count: number): string {
  if (count === 1) return 'prodavnici'
  if (count >= 2 && count <= 4) return 'prodavnice'
  return 'prodavnica' // 5+, 0
}

// Computed
const discountPercentage = computed(() => {
  if (props.product.discount_price && props.product.base_price > props.product.discount_price) {
    return Math.round(((props.product.base_price - props.product.discount_price) / props.product.base_price) * 100)
  }
  return 0
})

const businessLogo = computed(() => {
  const logo = props.product.business?.logo || props.product.business?.logo_path
  if (!logo) return null
  if (logo.startsWith('http://') || logo.startsWith('https://')) return logo
  return `${config.public.apiBase}/static/${logo}`
})

const cheapestClone = computed(() => {
  const cheaper = relatedProducts.value.clones.filter(c => c.is_cheaper)
  return cheaper.length > 0 ? cheaper[0] : null
})

// Generate a human-readable summary of what matches were found
const matchSummary = computed(() => {
  const clones = relatedProducts.value.clones.length
  const siblings = relatedProducts.value.siblings.length
  const brandVariants = relatedProducts.value.brand_variants.length

  if (clones === 0 && siblings === 0 && brandVariants === 0) {
    return ''
  }

  const parts: string[] = []
  const productName = props.product?.title || 'Ovaj proizvod'
  const shortName = productName.length > 40 ? productName.substring(0, 40) + '...' : productName

  // Clones - same product in other stores
  if (clones > 0) {
    const cheaper = relatedProducts.value.clones.filter(c => c.is_cheaper)
    if (cheaper.length > 0) {
      const savings = Math.abs(cheaper[0].price_diff).toFixed(2)
      parts.push(`Isti proizvod je dostupan u još ${clones} ${formatProdavnici(clones)}, a u ${cheaper[0].business_name} možete uštediti ${savings} KM`)
    } else {
      parts.push(`Isti proizvod je dostupan u još ${clones} ${formatProdavnici(clones)}`)
    }
  }

  // Siblings - same brand, different variants
  if (siblings > 0) {
    parts.push(`Dostupno je još ${siblings} ${siblings === 1 ? 'druga varijanta' : 'druge varijante'} istog brenda`)
  }

  // Brand variants - alternative brands with price context
  if (brandVariants > 0) {
    const cheaperBrands = relatedProducts.value.brand_variants.filter(bv => bv.is_cheaper)
    const moreExpensiveBrands = relatedProducts.value.brand_variants.filter(bv => bv.is_more_expensive)

    if (cheaperBrands.length > 0 && moreExpensiveBrands.length > 0) {
      parts.push(`Pronašli smo ${brandVariants} alternativnih brendova - ${cheaperBrands.length} jeftinijih i ${moreExpensiveBrands.length} skupljih`)
    } else if (cheaperBrands.length > 0) {
      const bestSavings = Math.abs(cheaperBrands[0].price_diff).toFixed(2)
      parts.push(`Pronašli smo ${cheaperBrands.length} jeftinijih alternativnih brendova, ušteda do ${bestSavings} KM`)
    } else if (moreExpensiveBrands.length > 0) {
      parts.push(`Pronašli smo ${moreExpensiveBrands.length} alternativnih brendova, ali su svi skuplji`)
    } else {
      parts.push(`Pronašli smo ${brandVariants} alternativnih brendova po sličnoj cijeni`)
    }
  }

  return parts.join('. ') + '.'
})

// Check if we should show the price comparison chart (clones + siblings + brand_variants >= 2)
const shouldShowPriceChart = computed(() => {
  const totalComparableProducts = relatedProducts.value.clones.length + relatedProducts.value.siblings.length + relatedProducts.value.brand_variants.length
  return totalComparableProducts >= 2
})

// Get all products for the chart (current product + clones + siblings + brand_variants with same size)
const chartProducts = computed(() => {
  if (!props.product) return []

  const currentPrice = props.product.discount_price || props.product.base_price
  const currentSizeValue = props.product.size_value
  const currentSizeUnit = (props.product.size_unit || '').toLowerCase()

  const currentProduct = {
    id: props.product.id,
    title: props.product.title,
    effective_price: currentPrice,
    base_price: props.product.base_price,
    discount_price: props.product.discount_price,
    business_name: props.product.business?.name || 'Nepoznato',
    business_logo: props.product.business?.logo || props.product.business?.logo_path,
    is_current: true
  }

  // Helper to check if product has same size as current product
  const hasSameSize = (p: any) => {
    if (!currentSizeValue || !currentSizeUnit) return true // If no size info, include all
    const pSizeValue = p.size_value
    const pSizeUnit = (p.size_unit || '').toLowerCase()
    return pSizeValue === currentSizeValue && pSizeUnit === currentSizeUnit
  }

  // Clones should always have the same size (by definition), but filter just in case
  const clones = relatedProducts.value.clones
    .filter(hasSameSize)
    .map(c => ({
      ...c,
      is_current: false,
      business_logo: c.business_logo || null
    }))

  // Siblings - filter to only same size (different variant products)
  const siblings = relatedProducts.value.siblings
    .filter(hasSameSize)
    .map(s => ({
      ...s,
      is_current: false,
      business_logo: s.business_logo || null
    }))

  // Brand variants - filter to only same size
  const brandVariants = relatedProducts.value.brand_variants
    .filter(hasSameSize)
    .map(bv => ({
      ...bv,
      is_current: false,
      business_logo: bv.business_logo || null
    }))

  return [currentProduct, ...clones, ...siblings, ...brandVariants]
})

// Methods
const closeModal = () => {
  emit('close')
}

const getImageUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${config.public.apiBase}/static/${path}`
}

const formatPrice = (price: number) => {
  return price?.toFixed(2) || '0.00'
}

const formatBosnianDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const day = date.getDate()
  const month = date.getMonth() + 1
  const year = date.getFullYear()
  return `${day}.${month}.${year}.`
}

const formatCommentDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'sada'
  if (minutes < 60) return `${minutes}min`
  if (hours < 24) return `${hours}h`
  if (days < 7) return `${days}d`

  return date.toLocaleDateString('bs-BA', { day: '2-digit', month: '2-digit' })
}

const validateComment = () => {
  const length = newComment.value.trim().length
  commentValidation.value.isValid = length >= 10 && length <= 1000
}

const loadComments = async () => {
  loadingComments.value = true
  try {
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const response = await fetch(`${config.public.apiBase}/api/products/${props.product.id}/comments`, { headers })
    const data = await response.json()
    if (data.success) {
      comments.value = data.comments
    }
  } catch (error) {
    console.error('Error loading comments:', error)
  } finally {
    loadingComments.value = false
  }
}

const loadVotes = async () => {
  try {
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const response = await fetch(`${config.public.apiBase}/api/products/${props.product.id}/votes`, { headers })
    const data = await response.json()
    if (data.success) {
      voteStats.value = {
        upvotes: data.upvotes,
        downvotes: data.downvotes
      }
      userVote.value = data.user_vote
    }
  } catch (error) {
    console.error('Error loading votes:', error)
  }
}

const loadRelatedProducts = async () => {
  loadingRelated.value = true
  try {
    // Include auth header to filter by user's preferred stores
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${config.public.apiBase}/api/products/${props.product.id}/related`, { headers })
    const data = await response.json()
    if (data.success) {
      relatedProducts.value = {
        clones: data.clones || [],
        brand_variants: data.brand_variants || [],
        siblings: data.siblings || [],
        source_product: data.source_product
      }
    }
  } catch (error) {
    console.error('Error loading related products:', error)
  } finally {
    loadingRelated.value = false
  }
}

// Price comparison chart functions
const loadChartLogoImages = async () => {
  const products = chartProducts.value
  const storeLogos = new Map<string, string | null>()

  products.forEach(p => {
    if (!storeLogos.has(p.business_name) && p.business_logo) {
      let logoUrl = p.business_logo
      if (!logoUrl.startsWith('http')) {
        logoUrl = `${config.public.apiBase}/static/${logoUrl}`
      }
      storeLogos.set(p.business_name, logoUrl)
    }
  })

  const loadPromises: Promise<void>[] = []
  storeLogos.forEach((logo, storeName) => {
    if (logo && !logoImages.value.has(storeName)) {
      const promise = new Promise<void>((resolve) => {
        const img = new Image()
        img.onload = () => {
          logoImages.value.set(storeName, img)
          resolve()
        }
        img.onerror = () => resolve()
        img.src = logo
      })
      loadPromises.push(promise)
    }
  })

  await Promise.all(loadPromises)
}

const updatePriceChart = () => {
  if (!priceChartCanvas.value) return

  if (priceChartInstance) {
    priceChartInstance.destroy()
  }

  const products = chartProducts.value
  if (products.length < 2) return

  // Detect mobile (under 768px)
  const isMobile = window.innerWidth < 768

  // Build allProducts array - sort by price ASC for vertical chart, group by store for horizontal
  let allProducts: any[] = []
  let storeStartIndices: { storeName: string; startIdx: number; endIdx: number }[] = []

  if (isMobile) {
    // Mobile (horizontal): Sort all products by price ASC
    allProducts = [...products].sort((a, b) => a.effective_price - b.effective_price)
  } else {
    // Desktop (vertical): Sort all products by price ASC
    allProducts = [...products].sort((a, b) => a.effective_price - b.effective_price)

    // Build store indices for logo drawing (group consecutive products from same store)
    let currentStore = ''
    let startIdx = 0
    allProducts.forEach((p, idx) => {
      if (p.business_name !== currentStore) {
        if (currentStore !== '') {
          storeStartIndices.push({ storeName: currentStore, startIdx, endIdx: idx - 1 })
        }
        currentStore = p.business_name
        startIdx = idx
      }
    })
    if (currentStore !== '') {
      storeStartIndices.push({ storeName: currentStore, startIdx, endIdx: allProducts.length - 1 })
    }
  }

  if (allProducts.length === 0) return

  // Find current product price for comparison
  const currentProductPrice = props.product.discount_price || props.product.base_price

  // Create colors based on whether product is cheaper or more expensive than current
  const backgroundColors = allProducts.map(p => {
    if (p.is_current) {
      // Current product: purple/highlighted
      return 'rgba(147, 51, 234, 0.9)' // Purple
    }
    // Color based on price comparison to current product
    if (p.effective_price < currentProductPrice) {
      return 'rgba(34, 197, 94, 0.8)' // Green - cheaper
    } else if (p.effective_price > currentProductPrice) {
      return 'rgba(239, 68, 68, 0.8)' // Red - more expensive
    }
    return 'rgba(156, 163, 175, 0.8)' // Gray - same price
  })

  const borderColors = allProducts.map(p => {
    if (p.is_current) {
      return 'rgb(147, 51, 234)' // Purple
    }
    if (p.effective_price < currentProductPrice) {
      return 'rgb(34, 197, 94)' // Green
    } else if (p.effective_price > currentProductPrice) {
      return 'rgb(239, 68, 68)' // Red
    }
    return 'rgb(156, 163, 175)' // Gray
  })

  // Calculate percentile of current product (what % of products are cheaper)
  const sortedPrices = [...allProducts].map(p => p.effective_price).sort((a, b) => a - b)
  const currentIndex = sortedPrices.findIndex(p => p >= currentProductPrice)
  const percentile = (currentIndex / sortedPrices.length) * 100

  // Custom plugin to draw store logos and separators (desktop only)
  const storeGroupPlugin = {
    id: 'storeGroupPlugin',
    afterDraw: (chart: any) => {
      if (isMobile) return // Skip plugin on mobile - we use Y-axis labels instead

      const ctx = chart.ctx
      const xAxis = chart.scales.x
      const yAxis = chart.scales.y
      const chartArea = chart.chartArea

      storeStartIndices.forEach((group, groupIdx) => {
        const { storeName, startIdx, endIdx } = group

        const startX = xAxis.getPixelForValue(startIdx)
        const endX = xAxis.getPixelForValue(endIdx)
        const centerX = (startX + endX) / 2
        const y = yAxis.bottom + 8

        // Draw separator line before each store (except first)
        if (groupIdx > 0) {
          const prevEndX = xAxis.getPixelForValue(startIdx - 1)
          const separatorX = (prevEndX + startX) / 2
          ctx.save()
          ctx.strokeStyle = '#d1d5db'
          ctx.lineWidth = 1
          ctx.setLineDash([3, 3])
          ctx.beginPath()
          ctx.moveTo(separatorX, chartArea.top)
          ctx.lineTo(separatorX, chartArea.bottom + 70)
          ctx.stroke()
          ctx.restore()
        }

        const logoImg = logoImages.value.get(storeName)

        if (logoImg) {
          const logoSize = 40
          ctx.drawImage(logoImg, centerX - logoSize / 2, y, logoSize, logoSize)
          ctx.fillStyle = '#374151'
          ctx.font = 'bold 11px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(storeName, centerX, y + logoSize + 14)
        } else {
          ctx.fillStyle = '#374151'
          ctx.font = 'bold 12px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(storeName, centerX, y + 24)
        }
      })
    }
  }

  // Mobile: horizontal bars with store names on Y-axis
  // Desktop: vertical bars with custom logo plugin
  const chartConfig: any = {
    type: 'bar',
    data: {
      labels: allProducts.map(p => {
        // On mobile, show store name as label
        if (isMobile) {
          return p.is_current ? `${p.business_name} ★` : p.business_name
        }
        return p.business_name
      }),
      datasets: [
        {
          label: 'Cijena (KM)',
          data: allProducts.map(p => p.effective_price),
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 2,
          borderRadius: isMobile ? 4 : 0
        }
      ]
    },
    options: {
      indexAxis: isMobile ? 'y' : 'x', // Horizontal on mobile
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: isMobile ? { right: 40 } : { bottom: 70 }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            title: (context: any) => {
              const idx = context[0].dataIndex
              return allProducts[idx].title
            },
            label: (context: any) => {
              const idx = context.dataIndex
              const product = allProducts[idx]
              let label = `Cijena: ${product.effective_price.toFixed(2)} KM`
              if (product.is_current) {
                label += ' (ovaj proizvod)'
              }
              return label
            },
            afterLabel: (context: any) => {
              const idx = context.dataIndex
              const product = allProducts[idx]
              const lines = [`Trgovina: ${product.business_name}`]
              if (product.discount_price && product.discount_price < product.base_price) {
                lines.push(`Redovna: ${product.base_price.toFixed(2)} KM`)
              }
              return lines
            }
          }
        },
        datalabels: {
          display: true,
          color: '#1f2937',
          anchor: isMobile ? 'end' : 'end',
          align: isMobile ? 'right' : 'top',
          rotation: isMobile ? 0 : -45,
          font: {
            weight: 'bold',
            size: isMobile ? 11 : 10
          },
          formatter: (value: number) => value.toFixed(2) + ' KM'
        }
      },
      scales: isMobile ? {
        x: {
          beginAtZero: true,
          suggestedMax: Math.max(...allProducts.map(p => p.effective_price)) * 1.3,
          ticks: {
            font: { size: 10 },
            callback: (value: number) => value.toFixed(0) + ' KM'
          }
        },
        y: {
          ticks: {
            font: { size: 11, weight: 'bold' },
            color: (context: any) => {
              const product = allProducts[context.index]
              if (product?.is_current) {
                return percentile <= 50 ? '#16a34a' : '#dc2626'
              }
              return '#374151'
            }
          }
        }
      } : {
        y: {
          beginAtZero: true,
          suggestedMax: Math.max(...allProducts.map(p => p.effective_price)) * 1.25,
          title: {
            display: false
          },
          ticks: {
            font: { size: 10 }
          }
        },
        x: {
          ticks: {
            display: false
          }
        }
      }
    },
    plugins: isMobile ? [] : [storeGroupPlugin]
  }

  priceChartInstance = new Chart(priceChartCanvas.value, chartConfig)
}

const deductViewCredit = async () => {
  if (!isAuthenticated.value || creditDeducted.value) return

  try {
    const result = await deductCredits(1, 'product_view', props.product?.id)
    if (result) {
      creditDeducted.value = true
    }
  } catch (error) {
    console.error('Error deducting view credit:', error)
  }
}

const handleVote = async (voteType: 'up' | 'down') => {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
    return
  }

  isVoting.value = true
  try {
    const response = await post(`/api/products/${props.product.id}/vote`, { vote_type: voteType })

    if (response.success) {
      voteStats.value = response.vote_stats

      if (response.message === 'Vote removed') {
        userVote.value = null
      } else {
        userVote.value = voteType
      }

      if (response.credits_earned > 0) {
        triggerCreditAnimation(response.credits_earned)
        await refreshUser()
        await refreshCredits()
      }
    }
  } catch (error: any) {
    console.error('Error voting:', error)
  } finally {
    isVoting.value = false
  }
}

const submitComment = async () => {
  if (!commentValidation.value.isValid) return

  isSubmittingComment.value = true
  try {
    const response = await post(`/api/products/${props.product.id}/comments`, {
      comment_text: newComment.value.trim()
    })

    if (response.success) {
      comments.value.unshift(response.comment)
      newComment.value = ''
      commentValidation.value = { isValid: false, message: '' }

      if (response.credits_earned > 0) {
        triggerCreditAnimation(response.credits_earned)
        await refreshUser()
        await refreshCredits()
      }
    }
  } catch (error: any) {
    console.error('Error submitting comment:', error)
  } finally {
    isSubmittingComment.value = false
  }
}

const checkReportStatus = async () => {
  if (!isAuthenticated.value || !props.product?.id) return

  const token = localStorage.getItem('token')
  if (!token) return

  try {
    const response = await fetch(`${config.public.apiBase}/api/products/${props.product.id}/report/status`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success && data.has_reported) {
        hasReported.value = true
      }
    }
  } catch (error) {
    console.error('Error checking report status:', error)
  }
}

const openReportModal = () => {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
    return
  }
  if (hasReported.value) return
  showReportModal.value = true
}

const closeReportModal = () => {
  showReportModal.value = false
  setTimeout(() => {
    if (!hasReported.value) {
      reportReason.value = ''
      reportSubmitted.value = false
    }
  }, 300)
}

const submitReport = async () => {
  isSubmittingReport.value = true
  try {
    const response = await post(`/api/products/${props.product.id}/report`, {
      reason: reportReason.value.trim() || null
    })

    if (response.success) {
      reportSubmitted.value = true
      hasReported.value = true

      if (response.credits_earned > 0) {
        triggerCreditAnimation(response.credits_earned)
        await refreshUser()
        await refreshCredits()
      }
    }
  } catch (error: any) {
    console.error('Error submitting report:', error)
    if (error.message?.includes('Vec ste prijavili') || error.message?.includes('already')) {
      hasReported.value = true
      showReportModal.value = false
    }
  } finally {
    isSubmittingReport.value = false
  }
}

// Related product tile actions
const isFavorited = (productId: number) => {
  if (!isAuthenticated.value) return false
  return favoritesStore.isFavorited(productId)
}

const handleFavorite = async (productId: number) => {
  if (!isAuthenticated.value) {
    router.push('/registracija')
    return
  }

  try {
    if (favoritesStore.isFavorited(productId)) {
      const favoriteId = favoritesStore.getFavoriteId(productId)
      if (favoriteId) {
        await favoritesStore.removeFavorite(favoriteId)
        showSuccess('Uklonjeno iz favorita')
      }
    } else {
      await favoritesStore.addFavorite(productId)
      showSuccess('Dodano u favorite!')
    }
  } catch (error) {
    console.error('Error toggling favorite:', error)
  }
}

const handleQuickVote = async (productId: number, voteType: 'up' | 'down') => {
  if (!isAuthenticated.value) {
    router.push('/registracija')
    return
  }

  try {
    const response = await post(`/api/products/${productId}/vote`, { vote_type: voteType })
    if (response.success && response.credits_earned > 0) {
      triggerCreditAnimation(response.credits_earned)
      await refreshUser()
      await refreshCredits()
    }
  } catch (error: any) {
    console.error('Error voting:', error)
    handleApiError(error)
  }
}

const handleAddToList = async (product: any) => {
  if (!isAuthenticated.value) {
    router.push('/registracija')
    return
  }

  try {
    const result = await cartStore.addItem(
      product.id,
      product.business_id || 1,
      1
    )

    if (result.success) {
      showSuccess(`"${product.title}" dodano u korpu!`)
    } else if (result.error) {
      handleApiError(result.error)
    }
  } catch (error) {
    console.error('Error adding to shopping list:', error)
  }
}

const openProduct = (productId: number) => {
  // Close current modal and open new product
  emit('close')
  // Update URL with new product ID
  const url = new URL(window.location.href)
  url.searchParams.set('product', productId.toString())
  window.history.pushState({}, '', url.toString())
  // Reload to show new product
  window.location.reload()
}

// Watch for modal opening
watch(() => props.show, async (newValue) => {
  if (newValue) {
    businessLogoError.value = false
    showReportModal.value = false
    reportReason.value = ''
    reportSubmitted.value = false
    hasReported.value = false
    creditDeducted.value = false

    // Reset related products
    relatedProducts.value = {
      clones: [],
      brand_variants: [],
      siblings: [],
      source_product: null
    }

    // Load all data in parallel
    // Note: Product view is now FREE - no credit deduction
    await Promise.all([
      loadComments(),
      loadVotes(),
      loadRelatedProducts(),
      checkReportStatus()
    ])
  } else {
    // Destroy chart when modal closes
    if (priceChartInstance) {
      priceChartInstance.destroy()
      priceChartInstance = null
    }
  }
}, { immediate: true })

// Watch for related products to render chart
watch(() => [relatedProducts.value.clones, relatedProducts.value.siblings, relatedProducts.value.brand_variants], async ([clones, siblings, brandVariants]) => {
  const totalProducts = clones.length + siblings.length + brandVariants.length
  if (totalProducts >= 2 && props.show) {
    // Wait for DOM to update with the canvas
    await nextTick()
    await loadChartLogoImages()
    await nextTick()
    updatePriceChart()
  }
}, { deep: true })
</script>

<style scoped>
@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.98) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-modal-in {
  animation: modal-in 0.2s ease-out;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Thin scrollbar */
.overflow-y-auto::-webkit-scrollbar,
.overflow-x-auto::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.overflow-y-auto::-webkit-scrollbar-track,
.overflow-x-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb,
.overflow-x-auto::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 10px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover,
.overflow-x-auto::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
