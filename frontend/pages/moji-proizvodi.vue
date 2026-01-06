<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <!-- Sticky Interest Navigation (Mobile Only) -->
    <div
      v-if="!loading && sortedTrackedProducts.length > 1"
      class="sticky top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 shadow-md md:hidden -mx-4 -mt-8 mb-4"
    >
      <div ref="navScrollContainer" class="flex overflow-x-auto scrollbar-hide gap-2.5 px-4 py-3">
        <button
          v-for="tracked in sortedTrackedProducts"
          :key="'nav-' + tracked.id"
          :ref="(el) => setNavChipRef(tracked.id, el)"
          @click="scrollToSection(tracked.id)"
          class="flex-shrink-0 px-4 py-2 rounded-full text-base font-medium transition-all whitespace-nowrap shadow-sm"
          :class="activeSection === tracked.id
            ? 'bg-purple-600 text-white shadow-purple-200'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
        >
          {{ tracked.search_term }}
        </button>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Install App Banner -->
      <div v-if="showInstallOption" class="mb-4 bg-gradient-to-r from-violet-500 to-purple-600 rounded-xl p-4 text-white">
        <div class="flex items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="bg-white/20 p-2 rounded-lg flex-shrink-0">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-sm sm:text-base">Instalirajte Aplikaciju</h3>
              <p class="text-xs text-white/80 hidden sm:block">Brzi pristup popustima bez browsera</p>
            </div>
          </div>
          <button
            @click="handleInstallClick"
            class="bg-white text-purple-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors flex-shrink-0"
          >
            Instaliraj
          </button>
        </div>
        <!-- iOS Instructions -->
        <div v-if="showIOSInstructions" class="mt-3 pt-3 border-t border-white/20 text-sm">
          <p class="font-medium mb-1">Kako instalirati:</p>
          <ol class="text-white/80 space-y-0.5 text-xs">
            <li>1. Dodirnite ikonu za dijeljenje</li>
            <li>2. "Dodaj na pocetni ekran"</li>
            <li>3. Dodirnite "Dodaj"</li>
          </ol>
        </div>
      </div>

      <!-- Header -->
      <div class="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Moji Proizvodi</h1>
          <p class="mt-2 text-gray-600">Praćeni proizvodi i pronađene ponude</p>
        </div>
        <button
          @click="showAddModal = true"
          class="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-all duration-200"
        >
          <Icon name="mdi:plus" class="w-5 h-5 mr-2" />
          Dodaj proizvod
        </button>
      </div>

      <!-- Stats Widget -->
      <div
        v-if="!loading && hasTracking && totalStats.productsOnSale > 0"
        class="mb-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200"
      >
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p class="text-green-800 font-semibold text-sm">Potencijalna ušteda danas</p>
            <p class="text-green-600 text-xs">Na osnovu trenutnih akcija</p>
          </div>
          <div class="flex items-center gap-4 sm:gap-6">
            <div class="text-center">
              <p class="text-2xl font-bold text-green-700">{{ totalStats.totalSavings.toFixed(2) }} <span class="text-sm font-normal">KM</span></p>
              <p class="text-xs text-green-600">ukupno</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-green-700">{{ maxDiscountPercent }}%</p>
              <p class="text-xs text-green-600">max popust</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-green-700">{{ totalStats.productsOnSale }}</p>
              <p class="text-xs text-green-600">na akciji</p>
            </div>
          </div>
        </div>
        <p class="text-green-600 text-xs mt-2 border-t border-green-200 pt-2">
          Cijene se često mijenjaju — mi ih provjeravamo umjesto Vas.
        </p>
      </div>

      <!-- No Discounts Info Bar -->
      <div
        v-else-if="!loading && hasTracking && totalStats.productsOnSale === 0"
        class="mb-4 bg-gradient-to-r from-gray-50 to-slate-50 rounded-xl p-4 border border-gray-200"
      >
        <div class="flex items-start gap-3">
          <span class="text-xl flex-shrink-0">⏳</span>
          <div>
            <p class="text-gray-900 font-medium text-sm md:text-base">Danas nema većih popusta, ali pratimo cijene za Vas</p>
            <p class="text-gray-500 text-xs mt-1">Obavijestit ćemo Vas čim se pojavi dobra ponuda.</p>
          </div>
        </div>
      </div>

      <!-- Processing Preferences Banner -->
      <div
        v-if="isProcessingPreferences"
        class="mb-6 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-4 md:p-5 border border-purple-200"
      >
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center animate-pulse">
              <Icon name="mdi:cog" class="w-6 h-6 text-purple-600 animate-spin" />
            </div>
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-purple-900">Analiziramo vaše preferencije...</h3>
            <p class="text-purple-700 text-sm mt-1">
              Tražimo proizvode prema vašim interesima. Ovo obično traje 15-30 sekundi.
            </p>
          </div>
        </div>
      </div>

      <!-- Processing Complete Popup -->
      <Teleport to="body">
        <Transition name="fade">
          <div
            v-if="showProcessingComplete"
            class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            @click.self="showProcessingComplete = false"
          >
            <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-slide-up">
              <div class="text-center">
                <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Icon name="mdi:check-circle" class="w-10 h-10 text-green-600" />
                </div>
                <h2 class="text-xl font-bold text-gray-900 mb-2">Pronašli smo proizvode za vas!</h2>
                <p class="text-gray-600 mb-6">
                  Na osnovu vaših preferencija, pronašli smo proizvode koji su trenutno na akciji.
                  Pregledajte ih ispod!
                </p>
                <button
                  @click="showProcessingComplete = false"
                  class="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
                >
                  Pogledaj proizvode
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Scan Info Banner -->
      <div
        v-if="latestScan"
        class="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 md:p-5 border border-green-200"
      >
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600" />
              <h3 class="font-bold text-gray-900">Posljednje skeniranje: {{ formatDate(latestScan.date) }}</h3>
            </div>
            <p class="text-gray-600 text-sm mt-1">
              {{ latestScan.summary || `Pronađeno ${latestScan.total_products} ${pluralBs(latestScan.total_products, 'proizvod', 'proizvoda', 'proizvoda')}` }}
            </p>
          </div>
          <div class="flex items-center gap-4">
            <div v-if="latestScan.new_products > 0" class="flex items-center gap-1.5">
              <span class="bg-green-100 text-green-700 px-2.5 py-1 rounded-full text-sm font-medium">
                {{ latestScan.new_products }} {{ pluralBs(latestScan.new_products, 'novi', 'nova', 'novih') }}
              </span>
            </div>
            <div v-if="latestScan.new_discounts > 0" class="flex items-center gap-1.5">
              <span class="bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full text-sm font-medium">
                {{ latestScan.new_discounts }} {{ pluralBs(latestScan.new_discounts, 'snižen', 'snižena', 'sniženih') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- My Preferences Section -->
      <UserPreferencesSection :key="preferencesKey" allow-remove @edit="openEditPreferences" @preference-removed="handlePreferenceRemoved" />

      <!-- Interest/Preferences Popup -->
      <InterestPopup
        :show="showInterestPopup"
        @close="showInterestPopup = false"
        @skip="showInterestPopup = false"
        @complete="handleInterestComplete"
      />

      <!-- Empty State (no tracking) -->
      <div v-if="!loading && !hasTracking" class="text-center py-12 bg-white rounded-lg shadow-sm">
        <Icon name="mdi:magnify-scan" class="w-24 h-24 text-gray-400 mx-auto mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Nemate praćenih proizvoda</h3>
        <p class="text-gray-600 mb-6 max-w-md mx-auto">
          Dodajte proizvode koje želite pratiti i automatski ćemo ih tražiti u svim radnjama.
          Obavijestit ćemo vas o novim ponudama i popustima!
        </p>
        <button
          @click="showAddModal = true"
          class="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          <Icon name="mdi:plus" class="w-5 h-5 mr-2" />
          Dodaj prvi proizvod
        </button>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>

      <!-- Tracked Products List (sorted by best discount) -->
      <div v-else class="space-y-6">
        <div
          v-for="tracked in sortedTrackedProducts"
          :key="tracked.id"
          :ref="(el) => setSectionRef(tracked.id, el)"
          :data-section-id="tracked.id"
          class="bg-white rounded-lg shadow-md overflow-hidden"
        >
          <!-- Tracked Term Header -->
          <div class="bg-purple-600 px-4 md:px-6 py-3 md:py-4 border-b border-purple-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div>
                  <div class="flex items-center gap-2">
                    <h3 class="text-base md:text-lg font-semibold text-white">{{ tracked.search_term }}</h3>
                    <!-- + Dodaj još - hidden on mobile -->
                    <button
                      @click="showAddModal = true; newProductTerm = tracked.search_term + ' '"
                      class="hidden md:inline text-xs text-white/80 hover:text-white font-medium"
                    >
                      + Dodaj još
                    </button>
                  </div>
                  <p v-if="tracked.original_text && tracked.original_text !== tracked.search_term" class="text-sm text-white/70 hidden md:block">
                    iz: {{ tracked.original_text }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-2 md:gap-3">
                <!-- Show spinner if searching, otherwise show count -->
                <span v-if="isSearching(tracked.search_term)" class="text-sm text-white flex items-center gap-1.5">
                  <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="hidden md:inline">Tražim...</span>
                </span>
                <span v-else class="text-sm text-white/80">{{ tracked.products.length }} <span class="hidden md:inline">pronađeno</span></span>
                <!-- Sort Dropdown - hidden on mobile -->
                <select
                  v-if="tracked.products.length > 1"
                  v-model="sortOrder[tracked.id]"
                  @change="sortProducts(tracked)"
                  class="hidden md:block text-sm border border-white/30 rounded-md px-2 py-1 bg-white/10 text-white focus:outline-none focus:ring-1 focus:ring-white/50"
                >
                  <option value="" class="text-gray-900">Sortiraj</option>
                  <option value="price_asc" class="text-gray-900">Cijena: najniža</option>
                  <option value="price_desc" class="text-gray-900">Cijena: najviša</option>
                </select>
                <button
                  @click="confirmRemoveTracked(tracked)"
                  class="p-1.5 rounded-full bg-white/20 text-white hover:bg-white/30 transition-colors"
                  title="Ukloni praćenje"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Products - Mobile Horizontal Scroll -->
          <div v-if="tracked.products.length > 0" class="md:hidden relative overflow-visible">
            <!-- Scroll Arrows -->
            <button
              v-if="tracked.products.length > 1"
              @click="scrollTracked(tracked.id, 'left')"
              class="absolute left-1 top-1/2 -translate-y-1/2 z-50 w-9 h-9 bg-white rounded-full flex items-center justify-center text-purple-600 hover:bg-gray-50 transition-all animate-bounce-horizontal-left border border-purple-200"
              style="box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              v-if="tracked.products.length > 1"
              @click="scrollTracked(tracked.id, 'right')"
              class="absolute right-1 top-1/2 -translate-y-1/2 z-50 w-9 h-9 bg-white rounded-full flex items-center justify-center text-purple-600 hover:bg-gray-50 transition-all animate-bounce-horizontal-right border border-purple-200"
              style="box-shadow: 0 2px 8px rgba(0,0,0,0.15);"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <!-- Horizontal Scroll Container -->
            <div
              :ref="(el) => setScrollRef(tracked.id, el)"
              class="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide py-4 gap-4"
              style="padding-left: calc((100vw - 78vw) / 2); padding-right: calc((100vw - 78vw) / 2);"
            >
              <ProductCardMobile
                v-for="product in tracked.products"
                :key="'mobile-' + product.id"
                :product="formatProductForCard(product)"
              />
            </div>

            <!-- Swipe hint -->
            <p v-if="tracked.products.length > 1" class="text-center text-xs text-gray-400 pb-2">
              ← Prevuci za više →
            </p>
          </div>

          <!-- Products - Desktop Grid -->
          <div v-if="tracked.products.length > 0" class="hidden md:block p-4">
            <div class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <div
                v-for="product in tracked.products.slice(0, showAllProducts[tracked.id] ? undefined : 4)"
                :key="product.id"
                class="group rounded-lg overflow-hidden transition-colors relative flex flex-col"
                :class="product.discount_price ? 'bg-green-50/70 hover:bg-green-100/70' : 'bg-gray-50 hover:bg-gray-100'"
              >
                <!-- Social Interaction Header -->
                <div class="bg-gradient-to-b from-black/70 via-black/40 to-transparent px-2 py-2 absolute top-0 left-0 right-0 z-10">
                  <div class="flex items-center justify-between">
                    <!-- Favorite (Heart) -->
                    <button
                      @click.stop="toggleFavorite(product)"
                      class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
                      :class="isFavorited(product.id) ? 'text-red-500' : 'text-white hover:text-red-400'"
                      :title="isFavorited(product.id) ? 'Ukloni iz favorita' : 'Dodaj u favorite'"
                    >
                      <svg class="w-5 h-5" :fill="isFavorited(product.id) ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                    </button>

                    <!-- Vote Buttons & Comment -->
                    <div class="flex items-center gap-2">
                      <!-- Thumbs Up -->
                      <button
                        @click.stop="vote(product, 'up')"
                        class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
                        :class="productVotes[product.id] === 'up' ? 'text-green-400 bg-green-500/20' : 'text-white hover:text-green-400'"
                        title="Preporuči"
                      >
                        <svg class="w-5 h-5" :fill="productVotes[product.id] === 'up' ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                        </svg>
                      </button>

                      <!-- Thumbs Down -->
                      <button
                        @click.stop="vote(product, 'down')"
                        class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer"
                        :class="productVotes[product.id] === 'down' ? 'text-red-400 bg-red-500/20' : 'text-white hover:text-red-400'"
                        title="Ne preporučujem"
                      >
                        <svg class="w-5 h-5" :fill="productVotes[product.id] === 'down' ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                        </svg>
                      </button>

                      <!-- Comment Button -->
                      <button
                        @click.stop="openCommentModal(product)"
                        class="flex items-center gap-1 px-2 py-1 rounded-full transition-all cursor-pointer text-white hover:text-purple-400"
                        title="Ostavi komentar"
                      >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Product Link (clickable area) -->
                <NuxtLink :to="`/proizvodi/${product.id}`" class="block p-3 pt-12 flex-1">
                  <!-- Product Image -->
                  <div class="aspect-square mb-3 bg-white rounded-lg overflow-hidden">
                    <img
                      v-if="product.image_url"
                      :src="product.image_url"
                      :alt="product.title"
                      class="w-full h-full object-contain group-hover:scale-105 transition-transform"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <Icon name="mdi:image-off" class="w-12 h-12 text-gray-300" />
                    </div>
                  </div>

                  <!-- Badges -->
                  <div class="flex flex-wrap items-center gap-1.5 mb-2">
                    <!-- Best Price Label (only for ≥90% match confidence with discount) -->
                    <span
                      v-if="product.similarity_score >= 0.90 && product.discount_price && isBestPriceInCategory(tracked, product)"
                      class="bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded text-xs font-medium"
                    >
                      Najbolja cijena
                    </span>
                    <span
                      v-if="product.is_new_today"
                      class="bg-green-100 text-green-700 px-1.5 py-0.5 rounded text-xs font-medium"
                    >
                      NOVO
                    </span>
                    <span
                      v-if="product.price_dropped_today"
                      class="bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-xs font-medium"
                    >
                      SNIŽENO
                    </span>
                    <span
                      v-if="product.discount_price"
                      class="bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded text-xs font-medium"
                    >
                      AKCIJA
                    </span>
                  </div>

                  <!-- Title -->
                  <h4 class="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-purple-600 transition-colors">
                    {{ product.title }}
                  </h4>

                  <!-- Store -->
                  <p class="text-xs text-gray-500 mt-1">{{ product.business }}</p>

                  <!-- Price -->
                  <div class="mt-2 flex items-center gap-2">
                    <span class="text-lg font-bold text-purple-600">
                      {{ (product.discount_price || product.base_price)?.toFixed(2) }} KM
                    </span>
                    <span v-if="product.discount_price && product.base_price && product.base_price > 0" class="text-xs text-gray-500 line-through">
                      {{ product.base_price.toFixed(2) }} KM
                    </span>
                  </div>

                  <!-- Relevance Score -->
                  <div v-if="product.similarity_score" class="mt-1">
                    <span class="text-xs text-gray-400">
                      {{ Math.round(product.similarity_score * 100) }}% podudaranje
                    </span>
                  </div>
                </NuxtLink>

                <!-- Add to List Button -->
                <div class="px-3 pb-3 mt-auto">
                  <button
                    @click.stop="addToShoppingList(product)"
                    :disabled="addingToList[product.id]"
                    class="w-full py-2 px-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all text-sm font-medium inline-flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Icon name="mdi:playlist-plus" class="w-4 h-4" />
                    <span>Dodaj u listu</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Show More Button -->
            <div v-if="tracked.products.length > 4" class="mt-4 text-center">
              <button
                @click="showAllProducts[tracked.id] = !showAllProducts[tracked.id]"
                class="text-purple-600 hover:text-purple-700 text-sm font-medium"
              >
                {{ showAllProducts[tracked.id] ? 'Prikaži manje' : `Prikaži sve (${tracked.products.length})` }}
              </button>
            </div>
          </div>

          <!-- No Products Found / Searching -->
          <div v-else class="p-6 text-center">
            <!-- Show searching animation if currently searching -->
            <template v-if="isSearching(tracked.search_term)">
              <div class="flex flex-col items-center justify-center py-4">
                <div class="w-12 h-12 mb-3 relative">
                  <div class="w-12 h-12 rounded-full border-4 border-purple-200"></div>
                  <div class="w-12 h-12 rounded-full border-4 border-purple-600 border-t-transparent absolute top-0 left-0 animate-spin"></div>
                </div>
                <p class="text-purple-700 font-medium">Tražim ponude za "{{ tracked.search_term }}"</p>
                <p class="text-gray-500 text-sm mt-1">Provjeravamo sve radnje, ovo traje do 30 sekundi...</p>
              </div>
            </template>
            <!-- Show empty state if not searching -->
            <template v-else>
              <Icon name="mdi:clock-outline" class="w-10 h-10 mx-auto mb-2 text-gray-300" />
              <p class="text-gray-600 font-medium">Trenutno nema ponuda za "{{ tracked.search_term }}"</p>
              <p class="text-gray-400 text-sm mt-1">Pratimo cijene — obavijestit ćemo Vas čim se pojavi popust.</p>
              <button
                @click="showAddModal = true; newProductTerm = ''"
                class="mt-3 text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                + Dodajte još brendova za više ponuda
              </button>
            </template>
          </div>
        </div>

        <!-- Bottom Nudge -->
        <div v-if="trackedProducts.length > 0" class="mt-8 text-center py-4 border-t border-gray-100">
          <p class="text-sm text-gray-400">
            Što više proizvoda pratite, veća je šansa da uhvatite najbolje popuste.
          </p>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div
        v-if="deleteConfirmTracked"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="deleteConfirmTracked = null"
      >
        <div class="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl">
          <div class="flex items-center justify-center mb-4">
            <div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <Icon name="mdi:trash-can-outline" class="w-6 h-6 text-red-600" />
            </div>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 text-center mb-2">Ukloni praćenje?</h3>
          <p class="text-sm text-gray-600 text-center mb-1">
            {{ deleteConfirmTracked.search_term }}
          </p>
          <p class="text-xs text-gray-500 text-center mb-6">
            Ova akcija će ukloniti proizvod iz praćenja i izbrisati historiju cijena.
          </p>
          <div class="flex gap-3">
            <button
              @click="deleteConfirmTracked = null"
              class="flex-1 px-4 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
            >
              Odustani
            </button>
            <button
              @click="removeTracked(deleteConfirmTracked.id)"
              :disabled="isRemovingTracked"
              class="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {{ isRemovingTracked ? 'Brišem...' : 'Ukloni' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Comment Modal -->
      <div
        v-if="commentModalProduct"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="closeCommentModal"
      >
        <div class="bg-white rounded-xl p-6 max-w-md w-full shadow-xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">Ostavi komentar</h3>
            <button @click="closeCommentModal" class="text-gray-400 hover:text-gray-600">
              <Icon name="mdi:close" class="w-5 h-5" />
            </button>
          </div>

          <p class="text-sm text-gray-600 mb-3">{{ commentModalProduct.title }}</p>
          <p class="text-xs text-purple-700 mb-3 font-medium">Podijelite vaše iskustvo i zaradite +5 kredita!</p>

          <textarea
            v-model="commentText"
            rows="3"
            maxlength="280"
            class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-gray-900 bg-white"
            placeholder="Vaš komentar... (min 5 karaktera)"
          />
          <p class="text-xs text-gray-500 mt-1 mb-4">{{ commentText.length }}/280</p>

          <div class="flex justify-end gap-3">
            <button
              type="button"
              @click="closeCommentModal"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
            >
              Odustani
            </button>
            <button
              @click="submitComment"
              :disabled="commentText.trim().length < 5 || isSubmittingComment"
              class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {{ isSubmittingComment ? 'Slanje...' : 'Pošalji (+5)' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Add Product Modal -->
      <div
        v-if="showAddModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="showAddModal = false"
      >
        <div class="bg-white rounded-xl p-6 max-w-md w-full shadow-xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900">Dodaj proizvod za praćenje</h3>
            <button @click="showAddModal = false" class="text-gray-400 hover:text-gray-600">
              <Icon name="mdi:close" class="w-5 h-5" />
            </button>
          </div>

          <form @submit.prevent="addTrackedProduct">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda</label>
              <input
                v-model="newProductTerm"
                type="text"
                placeholder="npr. mlijeko, nutella, coca cola..."
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                required
                minlength="2"
              />
              <p class="text-xs text-gray-500 mt-1">Unesite naziv proizvoda koji želite pratiti</p>
            </div>

            <div class="flex justify-end gap-3">
              <button
                type="button"
                @click="showAddModal = false"
                class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
              >
                Odustani
              </button>
              <button
                type="submit"
                :disabled="isAdding || !newProductTerm.trim()"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {{ isAdding ? 'Dodavanje...' : 'Dodaj' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'
import { useTrackedProductsStore } from '~/stores/trackedProducts'

const { pluralBs } = usePluralBs()
const { checkAuth } = useAuth()
const pwa = usePwaInstall()

// PWA install state
const showIOSInstructions = ref(false)
const showInstallOption = computed(() => {
  // Always show on this page unless already installed
  return !pwa.state.isInstalled && !pwa.state.isStandalone
})

async function handleInstallClick() {
  if (pwa.state.isIOS) {
    showIOSInstructions.value = !showIOSInstructions.value
  } else {
    await pwa.promptInstall()
  }
}

definePageMeta({
  middleware: 'auth'
})

const route = useRoute()
const router = useRouter()
const api = useApi()
const { get, post } = api
const { trackPageView } = useActivityTracking()
const trackedProductsStore = useTrackedProductsStore()
const { handleApiError, showSuccess, showWarning } = useCreditsToast()
const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()

const loading = ref(true)
const trackedProducts = ref<any[]>([])
const latestScan = ref<any>(null)
const hasTracking = ref(false)
const showAllProducts = ref<Record<number, boolean>>({})
const sortOrder = ref<Record<number, string>>({})

// Processing state
const isProcessingPreferences = ref(false)
const showProcessingComplete = ref(false)
const processingPollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

// Interest popup state
const showInterestPopup = ref(false)
const preferencesKey = ref(0)

// Add modal
const showAddModal = ref(false)
const newProductTerm = ref('')
const isAdding = ref(false)

// Product actions state
const productVotes = ref<Record<number, string | null>>({})
const addingToList = ref<Record<number, boolean>>({})

// Comment modal
const commentModalProduct = ref<any>(null)
const commentText = ref('')
const isSubmittingComment = ref(false)

// Delete confirmation modal
const deleteConfirmTracked = ref<any>(null)
const isRemovingTracked = ref(false)

// Track which terms are being searched (for loading state)
const searchingTerms = ref<Set<string>>(new Set())

// Scroll refs for horizontal scroll
const scrollRefs = ref<Record<number, HTMLElement | null>>({})

// Section refs for floating navigation
const sectionRefs = ref<Record<number, HTMLElement | null>>({})
const activeSection = ref<number | null>(null)
const intersectionObserver = ref<IntersectionObserver | null>(null)

// Navigation chip refs for auto-scrolling
const navScrollContainer = ref<HTMLElement | null>(null)
const navChipRefs = ref<Record<number, HTMLElement | null>>({})

// Computed: max discount percentage across all tracked products
const maxDiscountPercent = computed(() => {
  let maxDiscount = 0
  for (const tracked of trackedProducts.value) {
    for (const product of tracked.products) {
      if (product.discount_price && product.base_price && product.base_price > 0) {
        const discount = Math.round(((product.base_price - product.discount_price) / product.base_price) * 100)
        if (discount > maxDiscount) {
          maxDiscount = discount
        }
      }
    }
  }
  return maxDiscount
})

// Computed: total stats for the widget
const totalStats = computed(() => {
  let productsOnSale = 0
  let totalSavings = 0

  for (const tracked of trackedProducts.value) {
    for (const product of tracked.products) {
      if (product.discount_price && product.base_price && product.base_price > product.discount_price) {
        productsOnSale++
        totalSavings += (product.base_price - product.discount_price)
      }
    }
  }

  return {
    productsOnSale,
    totalSavings
  }
})

// Computed: sorted tracked products by best discount (descending)
const sortedTrackedProducts = computed(() => {
  // Calculate max discount for each tracked category
  const withMaxDiscount = trackedProducts.value.map(tracked => {
    let maxDiscount = 0
    let productsWithDiscount = 0

    for (const product of tracked.products) {
      if (product.discount_price && product.base_price && product.base_price > 0) {
        const discount = Math.round(((product.base_price - product.discount_price) / product.base_price) * 100)
        if (discount > maxDiscount) {
          maxDiscount = discount
        }
        productsWithDiscount++
      }
    }

    return {
      ...tracked,
      _maxDiscount: maxDiscount,
      _productsWithDiscount: productsWithDiscount
    }
  })

  // Sort by max discount (descending), then by products with discount count
  return withMaxDiscount.sort((a, b) => {
    if (b._maxDiscount !== a._maxDiscount) {
      return b._maxDiscount - a._maxDiscount
    }
    return b._productsWithDiscount - a._productsWithDiscount
  })
})

// Check if product is the best (lowest) price in its tracked category
function isBestPriceInCategory(tracked: any, product: any): boolean {
  if (!product.discount_price) return false
  const currentPrice = product.discount_price

  // Check against all other products with ≥90% confidence in same category
  for (const p of tracked.products) {
    if (p.id === product.id) continue
    if (p.similarity_score < 0.90) continue
    const price = p.discount_price || p.base_price
    if (price && price < currentPrice) {
      return false
    }
  }
  return true
}

function setScrollRef(trackedId: number, el: any) {
  scrollRefs.value[trackedId] = el as HTMLElement | null
}

// Set section ref for floating navigation
function setSectionRef(trackedId: number, el: any) {
  sectionRefs.value[trackedId] = el as HTMLElement | null
}

// Set nav chip ref for auto-scrolling
function setNavChipRef(trackedId: number, el: any) {
  navChipRefs.value[trackedId] = el as HTMLElement | null
}

// Scroll the navigation bar to keep active chip in view
function scrollNavToActiveChip(chipId: number) {
  const chip = navChipRefs.value[chipId]
  const container = navScrollContainer.value
  if (!chip || !container) return

  // Calculate if chip is outside visible area
  const chipRect = chip.getBoundingClientRect()
  const containerRect = container.getBoundingClientRect()

  // If chip is to the left of visible area
  if (chipRect.left < containerRect.left) {
    const scrollAmount = chip.offsetLeft - 12 // 12px padding
    container.scrollTo({ left: scrollAmount, behavior: 'smooth' })
  }
  // If chip is to the right of visible area
  else if (chipRect.right > containerRect.right) {
    const scrollAmount = chip.offsetLeft - container.offsetWidth + chip.offsetWidth + 12
    container.scrollTo({ left: scrollAmount, behavior: 'smooth' })
  }
}

// Scroll to a section when clicking on nav chip
function scrollToSection(trackedId: number) {
  const section = sectionRefs.value[trackedId]
  if (section) {
    // Account for sticky nav height (~60px) + some padding
    const offset = 70
    const elementPosition = section.getBoundingClientRect().top + window.scrollY
    window.scrollTo({
      top: elementPosition - offset,
      behavior: 'smooth'
    })
  }
}

// Get count of products with discount for a tracked item
function getDiscountCount(tracked: any): number {
  return tracked.products.filter((p: any) =>
    p.discount_price && p.base_price && p.discount_price < p.base_price
  ).length
}

// Setup intersection observer for section visibility
function setupIntersectionObserver() {
  if (!process.client) return

  // Disconnect existing observer
  if (intersectionObserver.value) {
    intersectionObserver.value.disconnect()
  }

  intersectionObserver.value = new IntersectionObserver(
    (entries) => {
      // Find the most visible section
      let mostVisible: { id: number; ratio: number } | null = null

      entries.forEach((entry) => {
        const sectionId = parseInt(entry.target.getAttribute('data-section-id') || '0')
        if (entry.isIntersecting && (!mostVisible || entry.intersectionRatio > mostVisible.ratio)) {
          mostVisible = { id: sectionId, ratio: entry.intersectionRatio }
        }
      })

      if (mostVisible) {
        activeSection.value = mostVisible.id
      }
    },
    {
      // Account for sticky header (~60px)
      rootMargin: '-70px 0px -50% 0px',
      threshold: [0, 0.25, 0.5, 0.75, 1]
    }
  )

  // Observe all sections
  Object.values(sectionRefs.value).forEach((el) => {
    if (el) {
      intersectionObserver.value?.observe(el)
    }
  })
}

function scrollTracked(trackedId: number, direction: 'left' | 'right') {
  const container = scrollRefs.value[trackedId]
  if (!container) return

  const cardWidth = container.offsetWidth * 0.78 // 78vw card width
  const scrollAmount = direction === 'left' ? -cardWidth : cardWidth

  container.scrollBy({
    left: scrollAmount,
    behavior: 'smooth'
  })
}

// Format product data for ProductCardMobile component
function formatProductForCard(product: any) {
  return {
    id: product.id,
    title: product.title,
    base_price: product.base_price,
    discount_price: product.discount_price,
    image_path: product.image_url,
    product_image_url: product.image_url,
    business: {
      id: product.business_id,
      name: product.business
    },
    is_new_today: product.is_new_today,
    price_dropped_today: product.price_dropped_today,
    has_discount: !!product.discount_price,
    similarity_score: product.similarity_score
  }
}

async function fetchTrackedProducts() {
  loading.value = true
  try {
    const data = await get('/api/user/tracked-products')
    trackedProducts.value = data.tracked_products || []
    latestScan.value = data.latest_scan
    hasTracking.value = data.has_tracking
  } catch (error) {
    console.error('Error fetching tracked products:', error)
    handleApiError(error)
  } finally {
    loading.value = false
  }
}

async function addTrackedProduct() {
  if (!newProductTerm.value.trim()) return

  const termToAdd = newProductTerm.value.trim()

  isAdding.value = true
  try {
    const response = await post('/api/user/tracked-products', {
      search_term: termToAdd
    })
    if (response.success) {
      showSuccess('Proizvod dodan za praćenje')
      showAddModal.value = false
      newProductTerm.value = ''

      // Mark as searching
      searchingTerms.value.add(termToAdd.toLowerCase())

      // Refresh the list
      await fetchTrackedProducts()
      trackedProductsStore.setCount(trackedProducts.value.length)

      // Start polling for results
      isProcessingPreferences.value = true
      startPolling()
    }
  } catch (error: any) {
    handleApiError(error)
  } finally {
    isAdding.value = false
  }
}

function confirmRemoveTracked(tracked: any) {
  deleteConfirmTracked.value = tracked
}

async function removeTracked(trackedId: number) {
  isRemovingTracked.value = true

  try {
    const response = await api.del(`/api/user/tracked-products/${trackedId}`)
    if (response.success) {
      showSuccess('Praćenje ukinuto')
      trackedProducts.value = trackedProducts.value.filter(t => t.id !== trackedId)
      trackedProductsStore.setCount(trackedProducts.value.length)
      if (trackedProducts.value.length === 0) {
        hasTracking.value = false
      }
      deleteConfirmTracked.value = null

      // If preference was also removed, refresh the preferences section
      if (response.preference_removed) {
        preferencesKey.value++
      }
    }
  } catch (error) {
    handleApiError(error)
  } finally {
    isRemovingTracked.value = false
  }
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return 'Danas'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Jučer'
  }

  const months = ['januar', 'februar', 'mart', 'april', 'maj', 'juni', 'juli', 'august', 'septembar', 'oktobar', 'novembar', 'decembar']
  return `${date.getDate()}. ${months[date.getMonth()]}`
}

// Sort products by price
function sortProducts(tracked: any) {
  const order = sortOrder.value[tracked.id]
  if (!order) return

  const getPrice = (p: any) => p.discount_price || p.base_price || 0

  if (order === 'price_asc') {
    tracked.products.sort((a: any, b: any) => getPrice(a) - getPrice(b))
  } else if (order === 'price_desc') {
    tracked.products.sort((a: any, b: any) => getPrice(b) - getPrice(a))
  }
}

// Check if product is favorited
function isFavorited(productId: number): boolean {
  return favoritesStore.isFavorited(productId)
}

// Toggle favorite
async function toggleFavorite(product: any) {
  try {
    if (isFavorited(product.id)) {
      const favoriteId = favoritesStore.getFavoriteId(product.id)
      if (favoriteId) {
        await favoritesStore.removeFavorite(favoriteId)
        showSuccess('Uklonjeno iz favorita')
      }
    } else {
      await favoritesStore.addFavorite(product.id)
      showSuccess('Dodano u favorite!')
    }
  } catch (error) {
    console.error('Error toggling favorite:', error)
    handleApiError(error)
  }
}

// Vote on product
async function vote(product: any, voteType: 'up' | 'down') {
  try {
    const response = await post(`/api/products/${product.id}/vote`, {
      vote_type: voteType
    })

    if (response.success) {
      if (response.message === 'Vote removed') {
        productVotes.value[product.id] = null
      } else {
        productVotes.value[product.id] = voteType
      }

      if (response.credits_earned > 0) {
        showSuccess(`+${response.credits_earned} kredita za glasanje!`)
      }
    }
  } catch (error: any) {
    console.error('Error voting:', error)
    handleApiError(error)
  }
}

// Open comment modal
function openCommentModal(product: any) {
  commentModalProduct.value = product
  commentText.value = ''
}

// Close comment modal
function closeCommentModal() {
  commentModalProduct.value = null
  commentText.value = ''
}

// Submit comment
async function submitComment() {
  if (!commentModalProduct.value || commentText.value.trim().length < 5 || isSubmittingComment.value) return

  isSubmittingComment.value = true

  try {
    const response = await post(`/api/products/${commentModalProduct.value.id}/quick-comment`, {
      comment_text: commentText.value.trim()
    })

    if (response.success) {
      showSuccess(`+${response.credits_earned} kredita za komentar!`)
      closeCommentModal()
    }
  } catch (error: any) {
    console.error('Error adding comment:', error)
    if (error.message) {
      showWarning(error.message)
    } else {
      handleApiError(error)
    }
  } finally {
    isSubmittingComment.value = false
  }
}

// Add to shopping list
async function addToShoppingList(product: any) {
  addingToList.value[product.id] = true

  try {
    const result = await cartStore.addItem(
      product.id,
      product.business_id || 1,
      1
    )

    if (result.success) {
      showSuccess(`"${product.title}" dodano na listu!`)
    } else if (result.error) {
      handleApiError(result.error)
    }
  } catch (error) {
    console.error('Error adding to shopping list:', error)
    handleApiError(error)
  } finally {
    addingToList.value[product.id] = false
  }
}

// Poll for processing status
async function checkProcessingStatus() {
  try {
    const status = await get('/auth/user/preferences-status')

    // Check if scan is complete (scanned_today) or if we have tracked products
    const scanComplete = status.scanned_today === true

    // For new users, check tracked_products_count
    // For existing users with new terms, check if scan is complete
    if (status.tracked_products_count > 0 && (scanComplete || searchingTerms.value.size === 0)) {
      // Fetch updated products
      await fetchTrackedProducts()

      // Check if any of the searching terms now have products
      let allTermsHaveResults = true
      for (const term of searchingTerms.value) {
        const tracked = trackedProducts.value.find(
          (t: any) => t.search_term.toLowerCase() === term
        )
        if (!tracked || tracked.products.length === 0) {
          allTermsHaveResults = false
          break
        }
      }

      // If scan is complete OR all searching terms have results, we're done
      if (scanComplete || allTermsHaveResults || searchingTerms.value.size === 0) {
        // Processing complete
        stopPolling()
        isProcessingPreferences.value = false

        // Clear searching terms
        searchingTerms.value.clear()

        // Show success popup only if we found products
        if (trackedProducts.value.some((t: any) => t.products.length > 0)) {
          showProcessingComplete.value = true
        }

        // Remove query param from URL
        router.replace({ path: route.path })

        // Force re-render of preferences section
        preferencesKey.value++

        trackedProductsStore.setCount(trackedProducts.value.length)
      }
    }
  } catch (error) {
    console.error('Error checking processing status:', error)
  }
}

function startPolling() {
  if (processingPollingInterval.value) return

  // Poll every 3 seconds
  processingPollingInterval.value = setInterval(checkProcessingStatus, 3000)
}

function stopPolling() {
  if (processingPollingInterval.value) {
    clearInterval(processingPollingInterval.value)
    processingPollingInterval.value = null
  }
}

// Check if a tracked term is being searched
function isSearching(searchTerm: string): boolean {
  return searchingTerms.value.has(searchTerm.toLowerCase())
}

// Open edit preferences popup - refresh user data first to get latest preferences
async function openEditPreferences() {
  await checkAuth()  // Refresh user data to get latest preferences
  showInterestPopup.value = true
}

// Handle interest popup completion - this is called when the InterestPopup emits 'complete'
// but doesn't redirect (e.g., when editing existing interests)
async function handleInterestComplete(data?: { processing_started?: boolean }) {
  showInterestPopup.value = false
  // Force re-render of preferences section
  preferencesKey.value++

  // If new interests are being processed, start polling
  if (data?.processing_started) {
    isProcessingPreferences.value = true

    // Fetch the tracked products first to get the new terms
    await fetchTrackedProducts()

    // Mark all tracked products with 0 products as "searching"
    for (const tracked of trackedProducts.value) {
      if (tracked.products.length === 0) {
        searchingTerms.value.add(tracked.search_term.toLowerCase())
      }
    }

    // Start polling for completion
    startPolling()
    checkProcessingStatus()
  } else {
    // Just refresh the data
    fetchTrackedProducts()
  }
}

async function handlePreferenceRemoved(deletedCount: number) {
  // Refresh tracked products list since some were deleted
  await fetchTrackedProducts()
  // Update the store count
  trackedProductsStore.setCount(trackedProducts.value.length)
}

// Watch for query param changes (when we're already on this page and navigate to it with ?processing=true)
watch(() => route.query.processing, (newVal) => {
  if (newVal === 'true' && !isProcessingPreferences.value) {
    isProcessingPreferences.value = true
    startPolling()
    checkProcessingStatus()
  }
})

// Watch for tracked products changes to re-setup intersection observer
watch(trackedProducts, () => {
  nextTick(() => {
    setupIntersectionObserver()
  })
}, { deep: true })

// Watch for active section changes to scroll navigation
watch(activeSection, (newSection) => {
  if (newSection) {
    scrollNavToActiveChip(newSection)
  }
})

onMounted(async () => {
  // Track page view
  trackPageView('moji-proizvodi')

  // Mark that user has visited moji-proizvodi (for feedback popup precondition)
  if (process.client) {
    localStorage.setItem('visited_moji_proizvodi', 'true')
  }

  // Check if we're coming from preferences processing
  if (route.query.processing === 'true') {
    isProcessingPreferences.value = true
    startPolling()
    // Also do an initial check immediately
    checkProcessingStatus()
  }

  // Fetch products
  await fetchTrackedProducts()

  // Update the store count for navbar badges
  trackedProductsStore.setCount(trackedProducts.value.length)

  // Setup intersection observer after a tick to ensure refs are set
  nextTick(() => {
    setupIntersectionObserver()
    // Set initial active section to first one
    if (sortedTrackedProducts.value.length > 0) {
      activeSection.value = sortedTrackedProducts.value[0].id
    }
  })
})

onUnmounted(() => {
  stopPolling()
  // Clean up intersection observer
  if (intersectionObserver.value) {
    intersectionObserver.value.disconnect()
  }
})
</script>

<style scoped>
@keyframes bounce-left {
  0%, 100% {
    transform: translateY(-50%) translateX(0);
  }
  50% {
    transform: translateY(-50%) translateX(-6px);
  }
}

@keyframes bounce-right {
  0%, 100% {
    transform: translateY(-50%) translateX(0);
  }
  50% {
    transform: translateY(-50%) translateX(6px);
  }
}

.animate-bounce-horizontal-left {
  animation: bounce-left 1.5s ease-in-out 3;
}

.animate-bounce-horizontal-right {
  animation: bounce-right 1.5s ease-in-out 3;
}

/* Fade transition for popup */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide up animation for popup content */
.animate-slide-up {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Hide scrollbar for floating nav */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
