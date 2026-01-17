<template>
  <div class="min-h-screen bg-white pb-20 md:pb-0">
    <div class="container mx-auto px-4 py-8 md:py-12">
      <div v-if="product" class="max-w-4xl mx-auto">
        <!-- Back button -->
        <button
          @click="$router.back()"
          class="flex items-center gap-2 text-gray-600 hover:text-purple-600 mb-6 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-5 h-5" />
          <span>Nazad</span>
        </button>

        <!-- Hero Section: Title + Prices + Voting -->
        <div class="mb-8">
          <div class="flex items-start justify-between gap-4 mb-4">
            <h1 class="text-2xl md:text-3xl font-bold text-gray-900">{{ product.title }}</h1>
            <!-- Compact Voting -->
            <div class="flex items-center gap-2 shrink-0">
              <button
                @click="handleVote('up')"
                :disabled="isVoting"
                :class="[
                  'flex items-center gap-1 px-3 py-1.5 rounded-lg transition-all text-sm',
                  userVote === 'up' ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-green-50'
                ]"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.08-.66-.23-.45-.52-.86-.88-1.22L14 2 7.59 8.41C7.21 8.79 7 9.3 7 9.83v7.84C7 18.95 8.05 20 9.34 20h8.11c.7 0 1.36-.37 1.72-.97l2.66-6.15z"/>
                </svg>
                <span class="font-bold">{{ voteStats.upvotes }}</span>
              </button>
              <button
                @click="handleVote('down')"
                :disabled="isVoting"
                :class="[
                  'flex items-center gap-1 px-3 py-1.5 rounded-lg transition-all text-sm',
                  userVote === 'down' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-red-50'
                ]"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M22 4h-2c-.55 0-1 .45-1 1v9c0 .55.45 1 1 1h2V4zM2.17 11.12c-.11.25-.17.52-.17.8V13c0 1.1.9 2 2 2h5.5l-.92 4.65c-.05.22-.02.46.08.66.23.45.52.86.88 1.22L10 22l6.41-6.41c.38-.38.59-.89.59-1.42V6.34C17 5.05 15.95 4 14.66 4h-8.1c-.71 0-1.36.37-1.72.97l-2.67 6.15z"/>
                </svg>
                <span class="font-bold">{{ voteStats.downvotes }}</span>
              </button>
            </div>
          </div>

          <!-- Prices -->
          <div class="flex items-center flex-wrap gap-4">
            <div class="flex items-baseline gap-3">
              <span
                v-if="product.has_discount && product.discount_price"
                class="text-3xl md:text-4xl font-bold text-purple-600"
              >
                {{ formatPrice(product.discount_price) }} KM
              </span>
              <span
                :class="[
                  'text-xl md:text-2xl font-bold',
                  (product.has_discount && product.discount_price) ? 'line-through text-gray-400' : 'text-purple-600 text-3xl md:text-4xl'
                ]"
              >
                {{ formatPrice(product.base_price) }} KM
              </span>
            </div>
            <div v-if="product.has_discount" class="bg-red-500 text-white px-3 py-1 rounded-full font-bold text-sm">
              -{{ product.discount_percentage }}%
            </div>
          </div>
        </div>

        <!-- Image and Chart Side by Side -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
          <!-- Product image -->
          <div class="bg-gray-50 rounded-2xl p-4 flex items-center justify-center relative">
            <!-- Best Price Stamp - shows when this product is cheapest among clones -->
            <div
              v-if="hasBestPrice"
              class="absolute top-4 left-4 z-10 bg-red-600 text-white px-3 py-1.5 rounded-lg shadow-lg transform -rotate-12"
            >
              <div class="flex items-center gap-1.5">
                <Icon name="mdi:trophy" class="w-5 h-5" />
                <span class="font-bold text-sm uppercase tracking-wide">Najbolja cijena</span>
              </div>
            </div>
            <img
              v-if="product.image_path"
              :src="product.image_path"
              :alt="product.title"
              class="max-h-80 w-auto rounded-xl object-contain"
            />
            <div v-else class="w-full aspect-square bg-gray-100 rounded-xl flex items-center justify-center">
              <Icon name="mdi:image-off" class="w-24 h-24 text-gray-300" />
            </div>
          </div>

          <!-- Price History Chart -->
          <div v-if="priceHistory.length > 1" class="bg-gray-50 rounded-2xl p-4">
            <h3 class="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Icon name="mdi:chart-line" class="w-5 h-5 text-purple-600" />
              Historija cijena
            </h3>
            <div class="h-64">
              <ClientOnly>
                <Line :data="chartData" :options="chartOptions" />
              </ClientOnly>
            </div>
          </div>

          <!-- If no price history, show product details in the second column -->
          <div v-else class="bg-gray-50 rounded-2xl p-6">
            <h3 class="text-lg font-bold text-gray-900 mb-4">Detalji proizvoda</h3>
            <div class="space-y-4 text-gray-700">
              <div v-if="product.category" class="flex items-center space-x-2">
                <Icon name="mdi:tag" class="w-5 h-5 text-gray-400" />
                <span>{{ product.category }}</span>
              </div>
              <div v-if="product.business" class="flex items-center space-x-2">
                <Icon name="mdi:store" class="w-5 h-5 text-gray-400" />
                <span class="font-medium">{{ product.business.name }}</span>
              </div>
              <div v-if="product.expires && product.has_discount" class="flex items-center space-x-2">
                <Icon name="mdi:calendar" class="w-5 h-5 text-gray-400" />
                <span>Popust važi do: {{ formatDate(product.expires) }}</span>
              </div>
            </div>

            <!-- Description inside Detalji -->
            <div v-if="product.enriched_description" class="mt-6 pt-4 border-t border-gray-200">
              <p class="text-gray-700 leading-relaxed text-sm">
                {{ product.enriched_description }}
              </p>
            </div>
          </div>
        </div>

        <!-- Product Description (below image/chart) - shows when there IS price history -->
        <div v-if="priceHistory.length > 1 && product.enriched_description" class="mb-8 bg-gray-50 rounded-2xl p-6">
          <h3 class="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <Icon name="mdi:text-box-outline" class="w-5 h-5 text-purple-600" />
            Opis proizvoda
          </h3>
          <p class="text-gray-700 leading-relaxed">
            {{ product.enriched_description }}
          </p>
        </div>

        <!-- Product Meta Info -->
        <div class="bg-white border border-gray-200 rounded-2xl p-6 mb-8">
          <!-- Business Info with Logo -->
          <div
            v-if="product.business"
            class="flex items-center gap-3 mb-4"
          >
            <div
              v-if="product.business.logo || product.business.logo_path"
              class="w-12 h-12 rounded-lg overflow-hidden border border-gray-200"
            >
              <img
                :src="getImageUrl(product.business.logo || product.business.logo_path)"
                :alt="`${product.business.name} logo`"
                class="w-full h-full object-contain"
              />
            </div>
            <div v-else class="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
              <span class="text-white text-lg font-bold">
                {{ product.business.name?.[0] || '' }}
              </span>
            </div>

            <div>
              <span class="text-gray-900 font-semibold text-lg">
                {{ product.business.name }}
              </span>
              <div v-if="product.city || product.business.city" class="text-gray-500 text-sm flex items-center gap-1">
                <Icon name="mdi:map-marker" class="w-4 h-4" />
                {{ product.city || product.business.city }}
              </div>
            </div>
          </div>

          <!-- Category and Expiry -->
          <div class="flex flex-wrap gap-3 mb-6">
            <div v-if="product.category" class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-gray-700">
              <Icon name="mdi:tag" class="w-4 h-4 text-gray-500" />
              <span class="text-sm font-medium">{{ product.category }}</span>
            </div>
            <div
              v-if="product.expires && product.has_discount"
              class="flex items-center gap-2 px-3 py-2 bg-yellow-100 rounded-lg text-yellow-700"
            >
              <Icon name="mdi:calendar-clock" class="w-4 h-4" />
              <span class="text-sm font-medium">Popust do: {{ formatBosnianDateWithRelative(product.expires) }}</span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-wrap gap-3">
            <!-- Add to Shopping List (only for logged-in users) -->
            <button
              v-if="isAuthenticated"
              @click="addToShoppingList"
              :disabled="isAddingToList"
              class="inline-flex items-center gap-2 py-2.5 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all duration-200 font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Icon name="mdi:cart-plus" class="w-5 h-5 flex-shrink-0" />
              <span class="whitespace-nowrap">Dodaj u korpu</span>
            </button>

            <!-- Favorite Button -->
            <FavoriteButton
              :product-id="product.id"
              :size="20"
              :show-label="true"
              @updated="handleFavoriteUpdate"
              class="!flex-none"
            />

          </div>
        </div>

        <!-- Related Products Section -->
        <div v-if="!loadingRelated && (relatedProducts.clones.length > 0 || relatedProducts.siblings.length > 0 || relatedProducts.brand_variants.length > 0)" class="mt-8 space-y-6">

          <!-- Price Alert Card (if cheaper clone exists) -->
          <div
            v-if="relatedProducts.clones.length > 0 && relatedProducts.clones.some((c: any) => c.is_cheaper)"
            class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-4"
          >
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="mdi:piggy-bank" class="w-6 h-6 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="text-lg font-semibold text-green-800">Uštedi novac!</h4>
                <p class="text-sm text-green-700 mt-1">
                  Pronašli smo ovaj proizvod jeftinije u drugoj prodavnici.
                  <span v-if="cheapestClone" class="font-medium">
                    Uštedi {{ Math.abs(cheapestClone.price_diff).toFixed(2) }} KM u {{ cheapestClone.business_name }}!
                  </span>
                </p>
              </div>
            </div>
          </div>

          <!-- Clones Section (Same product, different stores) -->
          <div v-if="relatedProducts.clones.length > 0" class="bg-gray-50 rounded-2xl p-6">
            <div class="flex items-center gap-2 mb-2">
              <Icon name="mdi:store-search" class="w-5 h-5 text-blue-500" />
              <h3 class="text-lg font-bold text-gray-900">Uporedi cijene</h3>
              <span class="text-sm text-gray-400">({{ relatedProducts.clones.length }} {{ formatProdavnica(relatedProducts.clones.length) }})</span>
            </div>
            <!-- Clone Summary Text -->
            <p class="text-sm text-gray-600 mb-4">
              <template v-if="hasBestPrice">
                <Icon name="mdi:check-circle" class="w-4 h-4 text-green-600 inline mr-1" />
                <span class="text-green-700 font-medium">Ovo je trenutno najbolja cijena!</span>
                Isti proizvod se prodaje u još {{ relatedProducts.clones.length }} {{ formatProdavnici(relatedProducts.clones.length) }},
                ali po višim cijenama (do {{ Math.max(...relatedProducts.clones.map((c: any) => c.price_diff_pct || 0)) }}% skuplje).
              </template>
              <template v-else-if="cheapestClone">
                <Icon name="mdi:alert-circle" class="w-4 h-4 text-orange-500 inline mr-1" />
                Pronašli smo ovaj proizvod <span class="text-green-700 font-medium">{{ Math.abs(cheapestClone.price_diff_pct) }}% jeftinije</span>
                u prodavnici <span class="font-medium">{{ cheapestClone.business_name }}</span>.
                Možete uštedjeti <span class="font-medium text-green-700">{{ Math.abs(cheapestClone.price_diff).toFixed(2) }} KM</span>!
              </template>
              <template v-else>
                Ovaj proizvod je dostupan u još {{ relatedProducts.clones.length }} {{ formatProdavnici(relatedProducts.clones.length) }} po sličnim cijenama.
              </template>
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="clone in relatedProducts.clones.slice(0, 6)"
                :key="clone.id"
                class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all cursor-pointer"
                @click="navigateTo(`/proizvodi/${clone.id}`)"
              >
                <!-- Product Image -->
                <div class="relative h-36 bg-gray-50">
                  <img
                    v-if="clone.image_path"
                    :src="getImageUrl(clone.image_path)"
                    :alt="clone.title"
                    class="w-full h-full object-contain p-2"
                  />
                  <div v-else class="flex items-center justify-center h-full text-gray-300">
                    <Icon name="mdi:image-off" class="w-10 h-10" />
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
                      {{ clone.effective_price?.toFixed(2) }} KM
                    </span>
                    <span
                      v-if="clone.discount_price && clone.base_price > clone.discount_price"
                      class="text-xs text-gray-400 line-through"
                    >
                      {{ clone.base_price?.toFixed(2) }} KM
                    </span>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center justify-between">
                    <div class="flex gap-1">
                      <button
                        @click.stop="handleRelatedFavorite(clone.id)"
                        class="p-1.5 rounded-lg hover:bg-pink-50 transition-colors"
                        title="Dodaj u favorite"
                      >
                        <Icon
                          :name="isRelatedFavorited(clone.id) ? 'mdi:heart' : 'mdi:heart-outline'"
                          class="w-4 h-4"
                          :class="isRelatedFavorited(clone.id) ? 'text-pink-600' : 'text-gray-400 hover:text-pink-600'"
                        />
                      </button>
                      <button
                        @click.stop="handleRelatedVote(clone.id, 'up')"
                        class="p-1.5 rounded-lg hover:bg-green-50 transition-colors text-gray-400 hover:text-green-600"
                        title="Preporuči"
                      >
                        <Icon name="mdi:thumb-up-outline" class="w-4 h-4" />
                      </button>
                    </div>
                    <button
                      @click.stop="handleRelatedAddToList(clone)"
                      class="flex items-center gap-1 px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg transition-colors"
                      title="Dodaj u korpu"
                    >
                      <Icon name="mdi:cart-plus" class="w-4 h-4" />
                      <span>Korpa</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Siblings Section (Same brand, different variants/sizes) -->
          <div v-if="relatedProducts.siblings.length > 0" class="bg-gray-50 rounded-2xl p-6">
            <div class="flex items-center gap-2 mb-2">
              <Icon name="mdi:resize" class="w-5 h-5 text-purple-500" />
              <h3 class="text-lg font-bold text-gray-900">Isti brend, druge varijante</h3>
              <span class="text-sm text-gray-400">({{ relatedProducts.siblings.length }})</span>
            </div>
            <!-- Siblings Summary Text -->
            <p class="text-sm text-gray-600 mb-4">
              <Icon name="mdi:information-outline" class="w-4 h-4 text-purple-500 inline mr-1" />
              Ovaj brend nudi i druge varijante ovog proizvoda (različite veličine ili tipove).
            </p>
            <div class="flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory">
              <div
                v-for="sibling in relatedProducts.siblings"
                :key="sibling.id"
                class="flex-shrink-0 w-[200px] bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
                @click="navigateTo(`/proizvodi/${sibling.id}`)"
              >
                <!-- Product Image -->
                <div class="relative h-32 bg-gray-50">
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
                <div class="p-3">
                  <h4 class="text-xs font-medium text-gray-900 line-clamp-2 min-h-[2rem] mb-2">
                    {{ sibling.title }}
                  </h4>

                  <!-- Price -->
                  <div class="flex items-baseline gap-1 mb-2">
                    <span class="text-base font-bold text-gray-900">
                      {{ sibling.effective_price?.toFixed(2) }} KM
                    </span>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center justify-between">
                    <button
                      @click.stop="handleRelatedFavorite(sibling.id)"
                      class="p-1 rounded hover:bg-pink-50 transition-colors"
                    >
                      <Icon
                        :name="isRelatedFavorited(sibling.id) ? 'mdi:heart' : 'mdi:heart-outline'"
                        class="w-4 h-4"
                        :class="isRelatedFavorited(sibling.id) ? 'text-pink-600' : 'text-gray-400'"
                      />
                    </button>
                    <button
                      @click.stop="handleRelatedAddToList(sibling)"
                      class="p-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                      title="Dodaj u korpu"
                    >
                      <Icon name="mdi:cart-plus" class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Brand Variants Section (Same product type, different brands) -->
          <div v-if="relatedProducts.brand_variants.length > 0" class="bg-gray-50 rounded-2xl p-6">
            <div class="flex items-center gap-2 mb-2">
              <Icon name="mdi:tag-multiple" class="w-5 h-5 text-orange-500" />
              <h3 class="text-lg font-bold text-gray-900">Alternativni brendovi</h3>
              <span class="text-sm text-gray-400">({{ relatedProducts.brand_variants.length }})</span>
            </div>
            <!-- Brand Variants Summary Text -->
            <p class="text-sm text-gray-600 mb-4">
              <Icon name="mdi:lightbulb-outline" class="w-4 h-4 text-orange-500 inline mr-1" />
              <template v-if="brandVariantSummary.hasCheaper">
                Ako niste vezani za brend, postoje <span class="text-green-700 font-medium">jeftinije alternative</span>!
                Pronašli smo {{ brandVariantSummary.cheaperCount }} {{ brandVariantSummary.cheaperCount === 1 ? 'proizvod' : 'proizvoda' }}
                sličnog tipa po nižim cijenama (do {{ brandVariantSummary.maxSavingPct }}% jeftinije).
              </template>
              <template v-else-if="brandVariantSummary.hasMoreExpensive">
                Ovaj brend nudi dobru vrijednost! Slični proizvodi drugih brendova su skuplji
                (do {{ brandVariantSummary.maxExpensivePct }}% više).
              </template>
              <template v-else>
                Pronašli smo {{ relatedProducts.brand_variants.length }} sličnih proizvoda drugih brendova po sličnim cijenama.
              </template>
            </p>
            <div class="flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory">
              <div
                v-for="variant in relatedProducts.brand_variants"
                :key="variant.id"
                class="flex-shrink-0 w-[200px] bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
                @click="navigateTo(`/proizvodi/${variant.id}`)"
              >
                <!-- Product Image -->
                <div class="relative h-32 bg-gray-50">
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
                <div class="p-3">
                  <h4 class="text-xs font-medium text-gray-900 line-clamp-2 min-h-[2rem] mb-2">
                    {{ variant.title }}
                  </h4>

                  <!-- Price -->
                  <div class="flex items-baseline gap-1 mb-2">
                    <span :class="[
                      'text-base font-bold',
                      variant.is_cheaper ? 'text-green-600' : 'text-gray-900'
                    ]">
                      {{ variant.effective_price?.toFixed(2) }} KM
                    </span>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center justify-between">
                    <button
                      @click.stop="handleRelatedFavorite(variant.id)"
                      class="p-1 rounded hover:bg-pink-50 transition-colors"
                    >
                      <Icon
                        :name="isRelatedFavorited(variant.id) ? 'mdi:heart' : 'mdi:heart-outline'"
                        class="w-4 h-4"
                        :class="isRelatedFavorited(variant.id) ? 'text-pink-600' : 'text-gray-400'"
                      />
                    </button>
                    <button
                      @click.stop="handleRelatedAddToList(variant)"
                      class="p-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                      title="Dodaj u korpu"
                    >
                      <Icon name="mdi:cart-plus" class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Loading Related Products -->
        <div v-if="loadingRelated" class="mt-8 flex items-center justify-center py-8">
          <Icon name="mdi:loading" class="w-6 h-6 animate-spin text-gray-400" />
          <span class="ml-2 text-gray-500">Tražimo povezane proizvode...</span>
        </div>

        <!-- Comments Section - Full Width -->
        <div class="mt-12 bg-gray-50 rounded-2xl p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">Komentari</h2>

          <!-- Add Comment Form -->
          <div v-if="isAuthenticated" class="mb-6">
            <textarea
              v-model="newComment"
              :disabled="isSubmittingComment"
              placeholder="Podijelite svoje iskustvo s ovim proizvodom! Da li ste zadovoljni kvalitetom? Je li cijena bila dobra? Pomozite drugima da donesu bolju odluku..."
              rows="3"
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all resize-none text-gray-900"
            ></textarea>
            <div class="flex items-center justify-between mt-2">
              <span :class="['text-sm', commentLength >= 20 && commentLength <= 1000 ? 'text-gray-500' : 'text-red-500']">
                {{ commentLength }} / 1000
                <span v-if="commentLength > 0 && commentLength < 20" class="ml-2">(min 20)</span>
              </span>
              <button
                @click="submitComment"
                :disabled="commentLength < 20 || commentLength > 1000 || isSubmittingComment"
                class="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
              >
                <span v-if="!isSubmittingComment">Objavi (+2 kredita)</span>
                <span v-else>Objavljivanje...</span>
              </button>
            </div>
          </div>
          <div v-else class="mb-6 p-4 bg-purple-100 rounded-xl text-center">
            <p class="text-gray-700 mb-2">Prijavite se da ostavite komentar i zaradite 2 kredita!</p>
            <NuxtLink to="/registracija" class="text-purple-600 hover:underline font-medium">
              Registrujte se besplatno
            </NuxtLink>
          </div>

          <!-- Comments List -->
          <div class="space-y-4 max-h-96 overflow-y-auto pr-2">
            <div v-if="loadingComments" class="text-center py-8">
              <Icon name="mdi:loading" class="w-8 h-8 animate-spin text-purple-600 mx-auto" />
              <p class="text-gray-600 mt-2">Učitavanje komentara...</p>
            </div>

            <div v-else-if="comments.length === 0" class="text-center py-8">
              <Icon name="mdi:comment-off-outline" class="w-12 h-12 text-gray-300 mx-auto mb-2" />
              <p class="text-gray-500">Budite prvi koji će ostaviti komentar!</p>
            </div>

            <div
              v-else
              v-for="comment in comments"
              :key="comment.id"
              class="bg-white rounded-xl p-4 w-full"
            >
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                  {{ comment.user.first_name?.[0] || '?' }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-baseline gap-2 mb-1">
                    <span class="font-semibold text-gray-900">
                      {{ comment.user.first_name }} {{ comment.user.last_name }}
                    </span>
                    <span class="text-xs text-gray-500">
                      {{ formatCommentDate(comment.created_at) }}
                    </span>
                  </div>
                  <p class="text-gray-700 whitespace-pre-wrap break-words">{{ comment.comment_text }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Loading state -->
      <div v-else-if="isLoading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>

      <!-- Error state -->
      <div v-else class="text-center py-12">
        <Icon name="mdi:alert-circle" class="w-24 h-24 mx-auto mb-4 text-red-500" />
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Proizvod nije pronađen</h2>
        <p class="text-gray-600 mb-6">Ovaj proizvod više nije dostupan ili je uklonjen.</p>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-5 h-5" />
          <span>Nazad na proizvode</span>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const route = useRoute()
const config = useRuntimeConfig()
const api = useApi()
const cartStore = useCartStore()

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
const favoritesStore = useFavoritesStore()
const { handleApiError, showSuccess } = useCreditsToast()
const { isAuthenticated, refreshUser } = useAuth()
const { triggerCreditAnimation } = useCreditAnimation()
const { refreshCredits } = useSearchCredits()

const product = ref<any>(null)
const isLoading = ref(false)
const priceHistory = ref<any[]>([])
const isAddingToList = ref(false)

// Voting state
const voteStats = ref({ upvotes: 0, downvotes: 0 })
const userVote = ref<string | null>(null)
const isVoting = ref(false)

// Comments state
const comments = ref<any[]>([])
const loadingComments = ref(false)
const newComment = ref('')
const isSubmittingComment = ref(false)

// Related products state
const relatedProducts = ref<{ clones: any[], siblings: any[], brand_variants: any[] }>({
  clones: [],
  siblings: [],
  brand_variants: []
})
const loadingRelated = ref(false)

// Cheapest clone computed
const cheapestClone = computed(() => {
  const cheaper = relatedProducts.value.clones.filter(c => c.is_cheaper)
  return cheaper.length > 0 ? cheaper[0] : null
})

// Has best price - true if no cheaper clones exist (this product is the cheapest)
const hasBestPrice = computed(() => {
  if (relatedProducts.value.clones.length === 0) return false
  // If no clone is cheaper, this product has the best price
  return !relatedProducts.value.clones.some(c => c.is_cheaper)
})

// Siblings summary for text description
const siblingSummary = computed(() => {
  const siblings = relatedProducts.value.siblings
  if (siblings.length === 0) return { hasSmaller: false, hasLarger: false }

  const currentSize = product.value?.size_value || 0
  const hasSmaller = siblings.some(s => (s.size_value || 0) < currentSize)
  const hasLarger = siblings.some(s => (s.size_value || 0) > currentSize)

  return { hasSmaller, hasLarger }
})

// Brand variants summary for text description
const brandVariantSummary = computed(() => {
  const variants = relatedProducts.value.brand_variants
  if (variants.length === 0) return { hasCheaper: false, hasMoreExpensive: false, cheaperCount: 0, maxSavingPct: 0, maxExpensivePct: 0 }

  const cheaper = variants.filter(v => v.is_cheaper)
  const moreExpensive = variants.filter(v => v.is_more_expensive)

  const maxSavingPct = cheaper.length > 0
    ? Math.max(...cheaper.map(v => Math.abs(v.price_diff_pct || 0)))
    : 0

  const maxExpensivePct = moreExpensive.length > 0
    ? Math.max(...moreExpensive.map(v => v.price_diff_pct || 0))
    : 0

  return {
    hasCheaper: cheaper.length > 0,
    hasMoreExpensive: moreExpensive.length > 0,
    cheaperCount: cheaper.length,
    maxSavingPct,
    maxExpensivePct
  }
})

const commentLength = computed(() => newComment.value.trim().length)

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('bs-BA')
}

const formatBosnianDateWithRelative = (dateString: string): string => {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const months = ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli', 'august', 'septembar', 'oktobar', 'novembar', 'decembar']

  const day = date.getDate()
  const month = months[date.getMonth()]
  const year = date.getFullYear()

  // Calculate days difference
  const diffTime = date.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  let relativePart = ''
  if (diffDays === 0) {
    relativePart = ' (danas)'
  } else if (diffDays === 1) {
    relativePart = ' (sutra)'
  } else if (diffDays > 1 && diffDays <= 30) {
    relativePart = ` (za ${diffDays} dana)`
  } else if (diffDays < 0) {
    relativePart = ' (isteklo)'
  }

  return `${day}. ${month.charAt(0).toUpperCase() + month.slice(1)} ${year}${relativePart}`
}

const getImageUrl = (path: string): string => {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `${config.public.apiBase}/static/${path}`
}

const formatChartDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA', { day: '2-digit', month: '2-digit' })
}

// Chart data computed from price history
const chartData = computed(() => {
  // Reverse to show oldest first
  const sortedHistory = [...priceHistory.value].reverse()

  return {
    labels: sortedHistory.map(h => formatChartDate(h.recorded_at)),
    datasets: [
      {
        label: 'Osnovna cijena (KM)',
        data: sortedHistory.map(h => h.base_price),
        borderColor: '#9333ea',
        backgroundColor: 'rgba(147, 51, 234, 0.1)',
        borderWidth: 3,
        tension: 0.3,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6
      },
      {
        label: 'Akcijska cijena (KM)',
        data: sortedHistory.map(h => h.discount_price ?? h.base_price),
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 3,
        tension: 0.3,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
        spanGaps: true
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      callbacks: {
        label: (context: any) => {
          const value = context.raw
          if (value === null) return null
          return `${context.dataset.label}: ${value.toFixed(2)} KM`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: false,
      ticks: {
        callback: (value: any) => `${value} KM`
      }
    }
  },
  interaction: {
    mode: 'nearest' as const,
    axis: 'x' as const,
    intersect: false
  }
}

async function addToShoppingList() {
  if (!product.value) return

  isAddingToList.value = true
  try {
    const result = await cartStore.addItem(
      product.value.id,
      product.value.business?.id || 1,
      1
    )

    if (result.success) {
      showSuccess(`"${product.value.title}" dodano u korpu!`)
    } else if (result.error) {
      handleApiError(result.error)
    }
  } finally {
    isAddingToList.value = false
  }
}

function handleFavoriteUpdate() {
  favoritesStore.fetchFavorites()
}

// Voting functions
async function loadVotes() {
  try {
    const response = await fetch(`${config.public.apiBase}/api/products/${route.params.id}/votes`)
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

async function handleVote(voteType: 'up' | 'down') {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
    return
  }

  isVoting.value = true
  try {
    const response = await api.post(`/api/products/${route.params.id}/vote`, { vote_type: voteType })

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

// Comments functions
async function loadComments() {
  loadingComments.value = true
  try {
    const response = await fetch(`${config.public.apiBase}/api/products/${route.params.id}/comments`)
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

async function submitComment() {
  if (commentLength.value < 20 || commentLength.value > 1000) return

  isSubmittingComment.value = true
  try {
    const response = await api.post(`/api/products/${route.params.id}/comments`, {
      comment_text: newComment.value.trim()
    })

    if (response.success) {
      comments.value.unshift(response.comment)
      newComment.value = ''
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

const formatCommentDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Upravo sada'
  if (minutes < 60) return `Prije ${minutes} min`
  if (hours < 24) return `Prije ${hours}h`
  if (days < 7) return `Prije ${days} dana`

  return date.toLocaleDateString('bs-BA', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// Related products functions
async function loadRelatedProducts() {
  if (!route.params.id) return

  loadingRelated.value = true
  try {
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${config.public.apiBase}/api/products/${route.params.id}/related`, { headers })
    const data = await response.json()

    if (data.success) {
      relatedProducts.value = {
        clones: data.clones || [],
        siblings: data.siblings || [],
        brand_variants: data.brand_variants || []
      }
    }
  } catch (error) {
    console.error('Error loading related products:', error)
  } finally {
    loadingRelated.value = false
  }
}

function isRelatedFavorited(productId: number): boolean {
  if (!isAuthenticated.value) return false
  return favoritesStore.isFavorited(productId)
}

async function handleRelatedFavorite(productId: number) {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
    return
  }

  try {
    await favoritesStore.toggleFavorite(productId)
  } catch (error) {
    console.error('Error toggling favorite:', error)
  }
}

async function handleRelatedVote(productId: number, voteType: 'up' | 'down') {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
    return
  }

  try {
    const response = await api.post(`/api/products/${productId}/vote`, { vote_type: voteType })
    if (response.success && response.credits_earned > 0) {
      triggerCreditAnimation(response.credits_earned)
      await refreshUser()
      await refreshCredits()
    }
  } catch (error) {
    console.error('Error voting:', error)
  }
}

async function handleRelatedAddToList(product: any) {
  if (!isAuthenticated.value) {
    navigateTo('/registracija')
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
    console.error('Error adding to list:', error)
  }
}

// Load product using useAsyncData for SSR (required for OG meta tags)
const { data: productData, pending: isLoadingProduct } = await useAsyncData(
  `product-${route.params.id}`,
  async () => {
    const response = await $fetch(`${config.public.apiBase}/api/product/${route.params.id}`)
    return response
  },
  { server: true }  // Ensure it runs on server for SSR meta tags
)

// Sync with reactive ref
watch(productData, (newData) => {
  if (newData) {
    product.value = newData
  }
}, { immediate: true })

// Load price history, votes, comments and related products on mount (client-side only)
onMounted(async () => {
  // Mark that user has visited proizvodi (for feedback popup precondition)
  if (process.client) {
    localStorage.setItem('visited_proizvodi', 'true')
  }

  isLoading.value = isLoadingProduct.value

  try {
    // Load price history
    const historyResponse = await api.get(`/api/products/${route.params.id}/price-history`)
    priceHistory.value = historyResponse || []

    // Load votes, comments and related products in parallel
    await Promise.all([loadVotes(), loadComments(), loadRelatedProducts()])
  } catch (error) {
    console.error('Failed to load additional data:', error)
  } finally {
    isLoading.value = false
  }
})

// Helper function to format price for meta description
const formatPriceForMeta = (price: number) => price.toFixed(2)

// Computed values for SEO meta tags (uses SSR data)
const productTitle = computed(() => productData.value?.title || 'Proizvod')
const productDescription = computed(() => {
  const p = productData.value
  if (!p) return 'Pogledajte ovu ponudu na Popust.ba'

  const price = p.has_discount && p.discount_price
    ? `${formatPriceForMeta(p.discount_price)} KM (popust ${p.discount_percentage}%)`
    : `${formatPriceForMeta(p.base_price)} KM`

  const store = p.business?.name || ''
  return `${p.title} - ${price}${store ? ` | ${store}` : ''} | Popust.ba`
})

const productImage = computed(() => {
  const p = productData.value
  if (!p?.image_path) return 'https://popust.ba/og-default.png'
  const path = p.image_path
  // Return absolute URL for OG image
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `https://api.popust.ba/static/${path}`
})

const productUrl = computed(() => `https://popust.ba/proizvodi/${route.params.id}`)

// SEO Meta Tags - will be rendered on server for Facebook/social crawlers
useSeoMeta({
  title: computed(() => `${productTitle.value} - Popust.ba`),
  description: productDescription,
  // Open Graph tags for Facebook sharing
  ogTitle: computed(() => productTitle.value),
  ogDescription: productDescription,
  ogImage: productImage,
  ogUrl: productUrl,
  ogType: 'product',
  ogSiteName: 'Popust.ba',
  ogLocale: 'bs_BA',
  // Twitter Card tags
  twitterCard: 'summary_large_image',
  twitterTitle: computed(() => productTitle.value),
  twitterDescription: productDescription,
  twitterImage: productImage,
})

// Canonical URL
useHead({
  link: [
    { rel: 'canonical', href: productUrl.value }
  ]
})

// JSON-LD Structured Data for Google (Schema.org Product)
const jsonLd = computed(() => {
  const p = productData.value
  if (!p) return null

  const price = p.has_discount && p.discount_price ? p.discount_price : p.base_price
  const availability = p.has_discount ? 'https://schema.org/InStock' : 'https://schema.org/InStock'

  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    'name': p.title,
    'description': p.enriched_description || productDescription.value,
    'image': productImage.value,
    'url': productUrl.value,
    'brand': p.brand ? { '@type': 'Brand', 'name': p.brand } : undefined,
    'category': p.category || undefined,
    'offers': {
      '@type': 'Offer',
      'url': productUrl.value,
      'priceCurrency': 'BAM',
      'price': price.toFixed(2),
      'priceValidUntil': p.expires || undefined,
      'availability': availability,
      'seller': p.business ? {
        '@type': 'Organization',
        'name': p.business.name
      } : undefined
    },
    'aggregateRating': (voteStats.value.upvotes + voteStats.value.downvotes) > 0 ? {
      '@type': 'AggregateRating',
      'ratingValue': voteStats.value.upvotes > 0 ? Math.round((voteStats.value.upvotes / (voteStats.value.upvotes + voteStats.value.downvotes)) * 5) : 3,
      'reviewCount': voteStats.value.upvotes + voteStats.value.downvotes
    } : undefined
  }
})

// Inject JSON-LD script
useHead({
  script: computed(() => jsonLd.value ? [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify(jsonLd.value)
    }
  ] : [])
})
</script>
