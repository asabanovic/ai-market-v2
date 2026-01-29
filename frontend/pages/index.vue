<template>
  <div>
    <!-- Discount Freshness Ticker -->
    <DiscountTicker :stores="discountFreshness" />

    <!-- Hero Section with Chat -->
    <div class="gradient-bg py-4 lg:py-12">
      <div class="mx-auto px-0 lg:px-12 text-center">
        <h1 class="typography-display-responsive text-white mb-4">
          Preplaćujete jer ne znate gdje je danas najjeftinije
        </h1>
        <ClientOnly>
          <template v-if="!user">
            <p class="typography-body text-gray-200 mb-6">
              🎁 <strong>POKLON:</strong> Isprobajte BESPLATNO! Jednu pretragu možete testirati bez registracije
            </p>
          </template>
        </ClientOnly>

        <!-- Chat Interface -->
        <div class="bg-white lg:rounded-xl shadow-2xl p-4 lg:p-6 w-full lg:max-w-[95vw] lg:mx-auto">
          <div class="mb-4">
            <label for="chat-input" class="block text-left typography-label text-gray-700 mb-2">
              ✨ Testirajte Popust asistenta - unesite proizvode koje trebate:
            </label>
            <textarea
              id="chat-input"
              v-model="searchQuery"
              rows="6"
              :placeholder="searchPlaceholder"
              class="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-y chat-input"
              @keydown.enter.exact.prevent="performSearch"
            />
            <ClientOnly>
              <template v-if="!user">
                <p class="mt-2 text-sm text-gray-600">
                  🎁 <strong>Posebna ponuda:</strong> Nakon registracije, pratimo cijene vaših omiljenih proizvoda i obavještavamo vas kada su na popustu!
                </p>
              </template>
            </ClientOnly>

            <!-- Store Filter -->
            <div class="mt-3 flex items-center gap-2 flex-wrap">
              <!-- Discounted Only Toggle -->
              <label class="flex items-center gap-2 cursor-pointer">
                <span class="text-xs text-gray-600">Samo popusti</span>
                <button
                  type="button"
                  @click="onlyDiscounted = !onlyDiscounted"
                  :class="[
                    'relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
                    onlyDiscounted ? 'bg-purple-600' : 'bg-gray-200'
                  ]"
                >
                  <span
                    :class="[
                      'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                      onlyDiscounted ? 'translate-x-4' : 'translate-x-0'
                    ]"
                  />
                </button>
              </label>

              <StoreSelector
                v-model="selectedStoreIds"
                :stores="allStores"
              />
              <span v-if="selectedStoreIds.length > 0" class="text-xs text-gray-500">
                Filtrirano: {{ selectedStoreIds.length }} {{ selectedStoreIds.length === 1 ? 'prodavnica' : 'prodavnice' }}
              </span>
              <span v-else class="text-xs text-gray-500">
                Sve prodavnice
              </span>
            </div>
          </div>

          <button
            @click="performSearch"
            :disabled="isSearching"
            class="w-full bg-purple-600 text-white py-3 px-6 rounded-lg btn-text hover:bg-purple-700 transition duration-200 flex items-center justify-center purple-pattern-overlay"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {{ isSearching ? 'Pretražujem...' : 'Pretražite' }}
          </button>

          <!-- Loading indicator -->
          <div v-if="isSearching" class="mt-4 text-center">
            <div class="inline-flex items-center text-purple-600">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span class="typography-body animate-fade-in">{{ currentLoadingMessage || 'Pretražujem...' }}</span>
            </div>
          </div>

          <!-- Results area -->
          <div v-if="searchResults" class="mt-4 lg:mt-6">

            <!-- Explanation/Response -->
            <div v-if="searchResults.response" class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 rounded-lg p-3 lg:p-5 mb-4 lg:mb-6 shadow-md">
              <div class="flex items-start gap-2 lg:gap-3">
                <div class="flex-shrink-0 hidden lg:block">
                  <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="text-sm lg:text-base text-gray-800 leading-relaxed font-medium" v-html="sanitizeResponse(searchResults.response)" />
                </div>
              </div>
            </div>

            <!-- Search Results (for both logged-in and anonymous users) -->
            <div v-if="searchResults.products">
              <!-- Grouped Results with Collapsible Sections -->
              <div v-if="isGroupedResults(searchResults.products)" class="space-y-0 lg:space-y-4">
                <!-- Mobile/Tablet: Quick Navigation Pills -->
                <div class="lg:hidden sticky top-0 z-20 bg-white py-2 px-4 border-b border-gray-200 shadow-sm">
                  <div class="relative">
                    <!-- Scroll hint gradient on right -->
                    <div class="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none"></div>
                    <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide pr-8">
                      <button
                        v-for="(products, groupName) in searchResults.products"
                        :key="'nav-' + groupName"
                        @click="scrollToGroup(groupName)"
                        :class="[
                          'flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap',
                          activeGroup === groupName
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        ]"
                      >
                        {{ capitalizeWords(groupName) }}
                        <span class="ml-1 text-xs opacity-75">({{ products?.length || 0 }})</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div
                  v-for="(products, groupName) in searchResults.products"
                  :key="groupName"
                  :ref="el => setGroupRef(groupName, el)"
                  class="border-b border-gray-200 lg:border lg:rounded-lg overflow-hidden bg-white"
                >
                  <!-- Group Header (Collapsible) -->
                  <button
                    @click="toggleGroup(groupName)"
                    class="w-full px-4 py-2 lg:py-3 flex items-center gap-3 bg-gray-50 hover:bg-gray-100 transition-colors z-10"
                  >
                    <!-- Collapse Icon -->
                    <svg
                      :class="[
                        'w-5 h-5 text-gray-600 transition-transform duration-200',
                        expandedGroups.has(groupName) ? 'transform rotate-180' : ''
                      ]"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>

                    <!-- Group Info -->
                    <div class="flex-1 text-left">
                      <h3 class="text-lg font-semibold text-gray-800">
                        {{ capitalizeWords(groupName) }}
                      </h3>
                      <p class="text-sm text-gray-600">
                        {{ products && products.length > 0 ? products.length : 0 }} {{ products && products.length === 1 ? 'proizvod' : 'proizvoda' }}
                      </p>
                    </div>
                  </button>

                  <!-- Products Grid (Collapsible) -->
                  <div v-if="expandedGroups.has(groupName)" class="py-3 lg:p-4">
                    <div v-if="products && products.length > 0">
                      <!-- Mobile/Tablet: Horizontal scroll cards -->
                      <div class="lg:hidden relative">
                        <!-- Left Arrow -->
                        <div class="absolute left-0 top-1/2 -translate-y-1/2 z-10 pointer-events-none">
                          <div class="w-8 h-16 bg-gradient-to-r from-white/90 to-transparent flex items-center justify-start pl-1">
                            <svg class="w-5 h-5 text-gray-400 animate-pulse-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                          </div>
                        </div>
                        <!-- Right Arrow -->
                        <div class="absolute right-0 top-1/2 -translate-y-1/2 z-10 pointer-events-none">
                          <div class="w-8 h-16 bg-gradient-to-l from-white/90 to-transparent flex items-center justify-end pr-1">
                            <svg class="w-5 h-5 text-gray-400 animate-pulse-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                        <div class="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide pb-4 gap-4" style="padding-left: calc((100vw - 78vw) / 2); padding-right: calc((100vw - 78vw) / 2);">
                          <ProductCardMobile v-for="product in products" :key="'mobile-' + product.id" :product="product" />
                        </div>
                        <!-- Swipe hint text -->
                        <div v-if="products.length > 1" class="flex justify-center items-center gap-2 text-xs text-gray-400 mt-1">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                          </svg>
                          <span>Prevucite za više</span>
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                          </svg>
                        </div>
                      </div>
                      <!-- Desktop: Regular grid -->
                      <div class="hidden lg:grid lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
                        <ProductCard v-for="product in products" :key="product.id" :product="product" />
                      </div>
                    </div>
                    <div v-else class="text-gray-500 text-sm text-center py-4">
                      Nema pronađenih proizvoda za ovu stavku.
                    </div>
                  </div>
                </div>
              </div>

              <!-- Flat Results (legacy) -->
              <div v-else-if="searchResults.products.length > 0">
                <!-- Mobile/Tablet: Horizontal scroll cards -->
                <div class="lg:hidden py-3">
                  <div class="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide pb-4 gap-4" style="padding-left: calc((100vw - 78vw) / 2); padding-right: calc((100vw - 78vw) / 2);">
                    <ProductCardMobile v-for="product in searchResults.products" :key="'mobile-' + product.id" :product="product" />
                  </div>
                </div>
                <!-- Desktop: Regular grid -->
                <div class="hidden lg:grid lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  <ProductCard v-for="product in searchResults.products" :key="product.id" :product="product" />
                </div>
              </div>

              <!-- No results message -->
              <div v-else-if="!isSearching && searchResults.intent !== 'general'" class="text-gray-500 text-center py-4">
                Nema proizvoda za prikaz.
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Featured Businesses Section - Animated Marquee -->
    <section v-if="featuredBusinesses && featuredBusinesses.length > 0" class="py-12 bg-gray-50 overflow-hidden">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-8">
          <h2 class="typography-heading-1 text-gray-900 mb-2">SUPERMARKETI</h2>
          <p class="typography-body text-gray-600">Koristite naš Popust asistent da brzo pronađete gdje su danas najjeftiniji proizvodi i najbolje akcije</p>
        </div>
      </div>

      <!-- Animated Scrolling Logos -->
      <div class="relative">
        <!-- Gradient overlays for smooth fade effect -->
        <div class="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-gray-50 to-transparent z-10 pointer-events-none"></div>
        <div class="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-gray-50 to-transparent z-10 pointer-events-none"></div>

        <!-- Scrolling container -->
        <div class="flex animate-marquee hover:[animation-play-state:paused]">
          <!-- Repeat logos 4 times to ensure no gaps -->
          <template v-for="repeat in 4" :key="'repeat-' + repeat">
            <div class="flex items-center gap-12 shrink-0">
              <div
                v-for="business in featuredBusinesses"
                :key="repeat + '-' + business.id"
                class="shrink-0 px-6"
              >
                <img
                  v-if="business.logo"
                  :src="business.logo"
                  :alt="business.name"
                  :title="business.name"
                  class="h-16 md:h-20 w-auto object-contain opacity-70 transition-all duration-300"
                  @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
                />
              </div>
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- Featured Products Section -->
    <section v-if="featuredProducts && featuredProducts.length > 0" class="py-16 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="typography-heading-1 text-gray-900 mb-4">Izdvojeni popusti</h2>
          <p class="typography-body text-gray-600">Najnoviji popusti iz različitih kategorija</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <ProductCard v-for="product in featuredProducts" :key="product.id" :product="product" />
        </div>

        <ClientOnly>
          <template v-if="user">
            <div class="text-center mt-12">
              <NuxtLink
                to="/proizvodi"
                class="bg-purple-600 text-white px-8 py-3 rounded-lg btn-text hover:bg-purple-700 transition duration-200 purple-pattern-overlay inline-block"
              >
                Pogledajte sve proizvode
              </NuxtLink>
            </div>
          </template>
          <template v-else>
            <div class="text-center mt-12">
              <NuxtLink
                to="/registracija"
                class="bg-purple-600 text-white px-8 py-3 rounded-lg btn-text hover:bg-purple-700 transition duration-200 purple-pattern-overlay inline-block"
              >
                Registrujte se da vidite sve proizvode
              </NuxtLink>
            </div>
          </template>
        </ClientOnly>
      </div>
    </section>

    <!-- Exit Intent Modal -->
    <ExitIntentModal
      v-if="showExitIntentModal"
      @close="closeExitModal"
    />

    <!-- Registration Modal -->
    <div v-if="showRegistrationModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showRegistrationModal = false">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-purple-100">
            <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="typography-heading-3 text-gray-900 mt-4">Registrujte se besplatno!</h3>
          <div class="mt-2 px-7 py-3">
            <p class="typography-body-small text-gray-500">
              {{ registrationMessage || 'Registrujte se besplatno da otključate najnovije akcije u svom gradu. Uštedite novac i vrijeme – pronađite gdje su danas najbolji popusti na meso, auto dijelove, tehniku i još mnogo toga.' }}
            </p>
          </div>
          <div class="items-center px-4 py-3">
            <NuxtLink
              to="/registracija"
              class="px-4 py-2 bg-purple-600 text-white btn-text rounded-md w-full shadow-sm hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-300 block text-center purple-pattern-overlay"
            >
              Registruj se sada
            </NuxtLink>
            <button
              @click="showRegistrationModal = false"
              class="mt-3 px-4 py-2 bg-gray-300 text-gray-800 btn-text rounded-md w-full shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
            >
              Kasnije
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- New Store Popup -->
    <NewStorePopup
      v-model="showNewStorePopup"
      :new-stores="newStores"
      :latest-store-id="latestStoreId"
      @stores-selected="handleNewStoresSelected"
      @dismissed="handleNewStoresDismissed"
    />

    <!-- Standalone Product Detail Modal (for direct URL access) -->
    <ProductDetailModal
      v-if="urlProduct"
      :show="showUrlProductModal"
      :product="urlProduct"
      @close="closeUrlProductModal"
    />

    <!-- City Required Modal (for users without city) -->
    <CityRequiredModal
      v-model="showCityRequiredModal"
      @city-saved="handleCitySaved"
    />

    <!-- Korpa Education Popup (one-time after first search) -->
    <KorpaEducationPopup
      :is-visible="showKorpaEducation"
      @close="showKorpaEducation = false"
    />
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const { get, post, put } = useApi()
const { user, isAuthenticated, authReady, checkAuth } = useAuth()
const { updateCreditsRemaining } = useSearchCredits()
const { showSuccess } = useCreditsToast()

// Reactive state
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref<any>(null)
const savingsStats = ref<any>(null)
const featuredBusinesses = ref<any[]>([])
const featuredProducts = ref<any[]>([])
const discountFreshness = ref<any[]>([])
const showRegistrationModal = ref(false)
const registrationMessage = ref('')
const expandedGroups = ref<Set<string>>(new Set())
const currentLoadingMessage = ref('')
const loadingMessageInterval = ref<any>(null)

// Mobile navigation state
const activeGroup = ref<string>('')
const groupRefs = ref<Record<string, HTMLElement | null>>({})

function setGroupRef(groupName: string, el: any) {
  if (el) {
    groupRefs.value[groupName] = el as HTMLElement
  }
}

function scrollToGroup(groupName: string) {
  const el = groupRefs.value[groupName]
  if (el) {
    // Ensure group is expanded
    if (!expandedGroups.value.has(groupName)) {
      expandedGroups.value.add(groupName)
      expandedGroups.value = new Set(expandedGroups.value)
    }
    // Scroll with offset for sticky header
    const offset = 60
    const elementPosition = el.getBoundingClientRect().top + window.scrollY
    window.scrollTo({
      top: elementPosition - offset,
      behavior: 'smooth'
    })
    activeGroup.value = groupName
  }
}

// Store filter state
const allStores = ref<any[]>([])
const selectedStoreIds = ref<number[]>([])
const onlyDiscounted = ref(false)

// Load onlyDiscounted from localStorage with 24-hour expiry
function loadOnlyDiscountedPreference() {
  if (!process.client) return
  const saved = localStorage.getItem('only_discounted_preference')
  if (saved) {
    try {
      const { value, timestamp } = JSON.parse(saved)
      const now = Date.now()
      const twentyFourHours = 24 * 60 * 60 * 1000
      if (now - timestamp < twentyFourHours) {
        onlyDiscounted.value = value
      } else {
        // Expired, remove it
        localStorage.removeItem('only_discounted_preference')
      }
    } catch {
      localStorage.removeItem('only_discounted_preference')
    }
  }
}

// Save onlyDiscounted to localStorage with timestamp
function saveOnlyDiscountedPreference(value: boolean) {
  if (!process.client) return
  localStorage.setItem('only_discounted_preference', JSON.stringify({
    value,
    timestamp: Date.now()
  }))
}

// Watch for changes to onlyDiscounted
watch(onlyDiscounted, (newVal) => {
  saveOnlyDiscountedPreference(newVal)
})

// New store popup state
const showNewStorePopup = ref(false)
const newStores = ref<any[]>([])
const latestStoreId = ref(0)

// Exit intent modal
const showExitIntentModal = ref(false)
const exitIntentTriggered = ref(false)

// City required modal (for users without city)
const showCityRequiredModal = ref(false)
const pendingSearchQuery = ref('')

// Korpa education popup (one-time after first search with results)
const showKorpaEducation = ref(false)

// URL product modal state (for direct links)
const urlProduct = ref<any>(null)
const showUrlProductModal = ref(false)

// Computed placeholder text based on authentication
const searchPlaceholder = computed(() => {
  if (user.value) {
    // Logged-in user - simple, no promotional text
    return `Pretraži i dodaj u korpu za poređenje cijena

Primjeri:
• Trebam brasno, mlijeko i čokoladu
• Gdje ima najjeftinija piletina?
• Korpa: hljeb, jaja, kafa, deterdžent`
  } else {
    // Anonymous user - promotional text
    return `🎯 Pretraži i dodaj u korpu za poređenje cijena

Primjeri:
• Trebam brasno, mlijeko i čokoladu
• Gdje ima najjeftinija piletina?
• Korpa: hljeb, jaja, kafa, deterdžent

Registracijom dobijate neograničenu pretragu i pristup korpi!`
  }
})

// Chat examples
const chatExamples = [
  {
    user: 'Trebam nabaviti losos i piletinu',
    assistant: 'Pronađeno: Losos u Mercatoru za 15 KM/kg (-20%), piletina u Bingu za 8 KM/kg'
  },
  {
    user: 'Korpa: hljeb, mlijeko, jaja, deterdžent',
    assistant: 'Najbolja opcija: Konzum - sve za 12.50 KM (ušteda 3 KM)'
  },
  {
    user: 'Gdje mogu kupiti najjeftiniju čokoladu i keks',
    assistant: 'Milka čokolada u Bingo za 2.50 KM (-30%), Plazma keks u Mercatoru za 1.80 KM'
  }
]

// Fun loading messages by category
const funMessages: Record<string, string[]> = {
  čokolada: [
    '🍫 Tražim najslađe ponude...',
    '🍫 Provjeravam ko ima najfiniju čokoladu...',
    '🍫 Čokolada? Odličan izbor! Pretražujem...',
    '🍫 Milka ili domaća? Vidim šta imamo...',
    '🍫 Sweet! Tražim najbolje cijene...'
  ],
  mlijeko: [
    '🥛 Tražim najsvježije mlijeko...',
    '🥛 Ko ima najbolje mliječne proizvode?',
    '🥛 Mlijeko? Ne zaboravi kekse! Pretražujem...',
    '🥛 Provjeravam litarže i cijene...',
    '🥛 Tražim kravlje, kozije... sve vrste!'
  ],
  hleb: [
    '🍞 Tražim svježi hljeb sa popustom...',
    '🍞 Peciva fresh iz pekare! Gledam...',
    '🍞 Hljeb naš svagdanji... tražim danas...',
    '🍞 Somun, kifle, razno... pretražujem...',
    '🍞 Najbolji hljeb u gradu? Odmah provjeravam!'
  ],
  meso: [
    '🥩 Tražim najkvalitetnije meso...',
    '🥩 Govedina, piletina, janjetina... gledam sve!',
    '🥩 Ko ima meso na akciji danas?',
    '🥩 Najbolje za roštilj! Pretražujem...',
    '🥩 Mesara ili market? Vidim šta nude...'
  ],
  piletina: [
    '🍗 Tražim najjeftiniju piletinu...',
    '🍗 File, bataci ili cijela? Gledam sve!',
    '🍗 Ko ima piletinu na popustu?',
    '🍗 Provjeravam sve ponude za piletinu...',
    '🍗 Fresh piletina? Odmah tražim!'
  ],
  riba: [
    '🐟 Tražim najbolje ribe grada...',
    '🐟 Losos, tuna, ili lokalna riba?',
    '🐟 Ko ima najsvježiju ribu danas?',
    '🐟 More dobrote! Pretražujem...',
    '🐟 Provjeravam ponude za ribu...'
  ],
  voće: [
    '🍎 Tražim najsvježije voće...',
    '🍊 Ko ima najbolje citruse?',
    '🍌 Vitamini na akciji! Pretražujem...',
    '🍇 Sezonsko voće? Vidim šta ima...',
    '🍓 Fresh iz bašte! Gledam ponude...'
  ],
  povrće: [
    '🥕 Tražim najkvalitetnije povrće...',
    '🥬 Zeleno i zdravo! Pretražujem...',
    '🍅 Ko ima najsvježije paradajze?',
    '🥒 Salata level: expert! Tražim...',
    '🌽 Provjeravam sve ponude za povrće...'
  ],
  sir: [
    '🧀 Tražim najbolje sireve...',
    '🧀 Trapist, gauda, ili kačkavalj?',
    '🧀 Ko ima sireve na popustu?',
    '🧀 Cheese lovers unite! Pretražujem...',
    '🧀 Mlječni specijaliteti! Gledam...'
  ],
  kafa: [
    '☕ Buđenje počinje ovdje! Tražim...',
    '☕ Ko ima najbolju kafu po cijeni?',
    '☕ Espresso, cappuccino... sve vrste!',
    '☕ Kafitza time! Pretražujem...',
    '☕ Najbolja kafa za jutro! Gledam...'
  ],
  čaj: [
    '🍵 Tražim najfiniji čaj...',
    '🍵 Zeleni, crni, ili voćni?',
    '🍵 Ko ima čajeve na akciji?',
    '🍵 Tea time! Pretražujem ponude...',
    '🍵 Opuštajući čaj? Odmah tražim!'
  ],
  sok: [
    '🧃 Tražim najukusnije sokove...',
    '🧃 Prirodni ili sa šećerom?',
    '🧃 Ko ima sokove na popustu danas?',
    '🧃 Vitamin boost! Pretražujem...',
    '🧃 Voćni freshness! Gledam ponude...'
  ],
  pivo: [
    '🍺 Tražim najbolje pivo po cijeni...',
    '🍺 Domaće ili import?',
    '🍺 Ko ima pivo na akciji?',
    '🍺 Cheers! Pretražujem ponude...',
    '🍺 Najbolje za žurku! Gledam...'
  ],
  vino: [
    '🍷 Tražim najbolja vina...',
    '🍷 Crveno, bijelo, ili rosé?',
    '🍷 Ko ima vina na popustu?',
    '🍷 Wine o\'clock! Pretražujem...',
    '🍷 Domaće ili import? Gledam sve!'
  ],
  deterdžent: [
    '🧼 Tražim najbolje deterdžente...',
    '🧼 Za bijelo, u boji, ili sve zajedno?',
    '🧼 Ko ima najpovoljnije cijene?',
    '🧼 Čistoća na prvom mjestu! Pretražujem...',
    '🧼 Mirisi i svježina! Gledam ponude...'
  ],
  šampon: [
    '🧴 Tražim najbolje šampone...',
    '🧴 Ko ima hair products na akciji?',
    '🧴 Provjeravam sve brendove...',
    '🧴 Good hair day incoming! Pretražujem...',
    '🧴 Za svaku kosu! Gledam ponude...'
  ],
  pasta: [
    '🍝 Tražim najbolje paste...',
    '🍝 Italiana style! Pretražujem...',
    '🍝 Ko ima paste na popustu?',
    '🍝 Spageti, penne, ili fusilli?',
    '🍝 Pasta la vista! Gledam ponude...'
  ],
  generic: [
    // === BOSNIA & HERZEGOVINA - Geography & Nature ===
    '🏔️ Jeste li znali? BiH ima 40% površine pokriveno šumama.',
    '🌊 Neretva je jedna od najhladnijih rijeka na svijetu.',
    '🏖️ Neum je jedini grad BiH na moru - samo 20km obale!',
    '⛰️ Maglić (2.386m) je najviši vrh Bosne i Hercegovine.',
    '🌲 Perućica je jedna od zadnjih prašuma u Evropi.',
    '💧 Rijeka Una ima 28 vrsta riba, neke teže i do 30kg!',
    '🗻 BiH ima oblik srca - zato se zove "zemlja u obliku srca".',
    '🌿 Sutjeska je najstariji nacionalni park u BiH (od 1962).',
    '🏞️ Kanjon Drine dubine je i do 1.000 metara!',
    '💦 Rijeka Bosna izvire podno planine Igman kod Sarajeva.',
    '🌳 Kozara se zove "Zelena ljepotica Krajine".',
    '🏔️ Bjelašnica je bila domaćin Zimskih olimpijskih igara 1984.',
    '🌊 Vrbas je dug 235 km i prolazi kroz Banju Luku.',
    '⛰️ Vranica je planina gdje izvire rijeka Vrbas.',
    '🌲 BiH ima 262 manje i veće rijeke!',
    '🏖️ Neum je omiljeno ljetovalište Bosanaca i Hercegovaca.',
    '💧 Rijeka Trebišnjica je najveća ponornica u Evropi.',
    '🗻 Jahorina je poznata po skijaškim stazama olimpijskog nivoa.',
    '🌿 Blidinje je najviše planinsko jezero u BiH.',
    '🏞️ Plitka jezera kod Jajca su poznata po čistoj vodi.',

    // === BOSNIA & HERZEGOVINA - History ===
    '📜 BiH je naseljena već 14.000 godina - pećina Badanj!',
    '🏰 Sarajevo je dobilo tramvaj 1885. - prije Beča!',
    '⚡ Sarajevo je imalo javnu rasvjetu već 1895. godine.',
    '📚 Gazi Husrev-begova biblioteka radi od 1537. godine!',
    '🕰️ Sarajevski sahat je jedini na svijetu koji mjeri lunarno vrijeme.',
    '🚽 Prvi javni WC u Sarajevu napravljen je 1526. godine!',
    '🏅 Sarajevo je 1984. bilo domaćin Zimskih olimpijskih igara.',
    '🌉 Stari most u Mostaru je izgrađen 1566. godine.',
    '📍 Atentat na Franca Ferdinanda u Sarajevu pokrenuo je 1. svjetski rat.',
    '🏛️ Stećci su srednjovjekovni nadgrobnici - UNESCO baština od 2016.',
    '🗿 Ima preko 60.000 stećaka širom BiH!',
    '🏰 Bihać je osnovan 1260. godine.',
    '⚔️ Bitka na Sutjesci 1943. bila je prelomna u 2. sv. ratu.',
    '🏛️ Travnik je bio glavni grad Bosne 150 godina.',
    '🌉 Most Mehmed-paše Sokolovića u Višegradu je UNESCO baština.',
    '📜 Sarajevo se zove "Jeruzalem Evrope" zbog vjerske raznolikosti.',
    '🏰 Tvrđava Kastel u Banjoj Luci datira iz rimskog perioda.',
    '⏳ Opsada Sarajeva trajala je 1.425 dana - najduža u modernoj historiji.',
    '🕌 Ferhadija džamija u Banjoj Luci izgrađena je 1579. godine.',
    '📖 Haggadah iz Sarajeva je jedna od najstarijih jevrejskih knjiga.',

    // === BOSNIA & HERZEGOVINA - Cities ===
    '🏙️ Sarajevo znači "dvorska ravnica" na turskom.',
    '🌆 Sarajevo je geografski centar trokutaste BiH.',
    '🏘️ Mostar je najveći grad u Hercegovini.',
    '🌇 Banja Luka se zove "Zeleni grad".',
    '🏙️ Tuzla je dobila ime po turskoj riječi za sol.',
    '🏭 Zenica ima najveću željezaru u BiH.',
    '🏔️ Lukomir je najviše stalno naseljeno selo u BiH (1.495m).',
    '🌉 Konjic ima most iz 1682. - spaja Bosnu i Hercegovinu.',
    '🏛️ Jajce ima vodopad usred grada gdje se spajaju Pliva i Vrbas.',
    '🏙️ Brčko je jedini "slobodni grad" u Evropi - skoro samoupravni.',
    '🌆 Trebinje je najjužniji grad u BiH.',
    '🏘️ Visoko je poznat po kontroverznim "piramidama".',
    '🌇 Bugojno je nekad imao GDP 98% jugoslavenskog prosjeka.',
    '🏙️ Bihać je bio slobodna teritorija 1942. godine.',

    // === BOSNIA & HERZEGOVINA - Food & Culture ===
    '🥘 Pravi burek je SAMO s mesom - ostalo je pita!',
    '🍖 Ćevapi su najpopularnije jelo u BiH.',
    '☕ Bosanska kafa se kuha u džezvi - to je ritual!',
    '🧀 Livanjski sir je zaštićeno geografsko porijeklo.',
    '🍯 Med iz BiH je jedan od najkvalitetnijih u Evropi.',
    '🥧 Tufahija je bosanski desert od jabuke i oraha.',
    '🍲 Bosanski lonac je tradicionalno jelo od povrća i mesa.',
    '🧈 Kajmak je mliječni specijalitet bez kojeg nema ćevapa!',
    '🍞 Somun je bosanski hljeb za ćevape.',
    '🥟 Klepe su bosanske knedla punjena mesom.',
    '🍬 Baklava u BiH se pravi s orasima.',
    '🍖 Banjalučki ćevap se razlikuje od sarajevskog.',
    '☕ U BiH se kafa pije iz fildžana.',
    '🍲 Begova čorba je tradicionalna bosanska supa.',
    '🥘 Japrak su punjeni listovi vinove loze.',

    // === FUN JOKES ===
    '😄 Zašto programeri nose naočale? Jer ne mogu C#!',
    '😂 Šta kaže 0 broju 8? "Lijep ti pojas!"',
    '🤣 Zašto su matematičari loši na zabavama? Jer uvijek dijele.',
    '😄 Kako se zove riba bez oka? Rba.',
    '😂 Zašto je knjiga išla doktoru? Jer joj je pukla kičma!',
    '🤣 Šta kaže more obali? Ništa, samo maše.',
    '😄 Zašto je bicikl pao? Bio je umoran - dva točka!',
    '😂 Kako nasmijati oktopoda? S deset škakljivki!',
    '🤣 Šta je rekao prozor vratima? "Šta zuriš?"',
    '😄 Zašto su planine smiješne? Jer su brdalaste.',
    '😂 Kako se zove lijeni kengur? Pouch potato.',
    '🤣 Zašto mjesec nije gladan? Jer je pun!',
    '😄 Šta kaže papir škarama? "Pokrivaš me!"',
    '😂 Zašto muha ima šest nogu? Da može letjeti i hodati!',
    '🤣 Kako astronauti slave rođendan? Uzimaju malo svemira.',
    '😄 Zašto su neki ljudi loši na odbojci? Jer ne znaju servirati.',
    '😂 Šta kaže telefon zubu? "Imaš dobar ton!"',
    '🤣 Zašto kornjača nosi kuću? Jer ne voli podstanare.',
    '😄 Kako nasmijati kamenje? Ispričaj im geo-logičan vic!',
    '😂 Šta kaže magnet drugom magnetu? "Privlačan si!"',
    '🤣 Zašto je kompas loš prijatelj? Uvijek pokazuje drugim.',
    '😄 Kako se zove pokvareni robot? Sir-kusni!',
    '😂 Zašto je balon sretan? Jer ga sve naduvava!',
    '🤣 Šta kaže voda ledu? "Samo polako, smrznut ćeš se!"',
    '😄 Zašto volim svoj sat? Jer je uvijek uz mene!',
    '😂 Kako se zove mačka bez repa? Skraćena verzija!',
    '🤣 Zašto stolovi ne igraju karte? Jer su uvijek presavijeni.',
    '😄 Šta kaže lampica drugoj? "Svijetliš mi dan!"',
    '😂 Zašto je petak najbolji dan? Jer je najbliži vikendu!',
    '🤣 Kako se zove pas koji radi manikir? Noktolog!',

    // === MORE BOSNIA FACTS ===
    '🌍 BiH je 61. najmirnija zemlja na svijetu (2024).',
    '📈 BiH je imala treći najveći rast turizma u svijetu 1995-2020.',
    '🎓 Glavni univerziteti su u Sarajevu, Mostaru, Banjoj Luci, Tuzli.',
    '🏛️ BiH ima 35 službenih gradova.',
    '🌉 Arslanagića most u Trebinju je remek-djelo osmanske arhitekture.',
    '🏔️ Olimpijske planine su Bjelašnica, Jahorina, Igman i Trebević.',
    '🎿 Jahorina ima preko 20km skijačkih staza.',
    '🌲 Nacionalni park Kozara osnovan je 1967. godine.',
    '🏛️ Kozara spomenik je visok 33 metra.',
    '📍 Titov bunker u Konjicu je danas turistička atrakcija.',
    '🌊 Neretva je duga 225 km, od čega 208 km u BiH.',
    '💎 Drina je najveća pritoka Save po površini sliva.',
    '🏞️ Una je poznata po slapovima i raftingu.',
    '🌉 Radimlja kod Stoca ima najbolje očuvane stećke.',
    '📜 Tvrdoš manastir kod Trebinja datira iz 15. vijeka.',
    '🏰 Stari grad Jajce ima katakombe ispod starog grada.',
    '⚔️ AVNOJ je zasjedao u Jajcu tokom 2. sv. rata.',
    '🏙️ Sefardski Jevreji stigli su u Sarajevo 1492. godine.',
    '🕌 Gazi Husrev-begova džamija je izgrađena 1532. godine.',
    '📚 Sarajevska vijećnica je obnovljena 2014. godine.',

    // === MORE JOKES ===
    '😄 Zašto pčele imaju ljepljivu kosu? Koriste saće!',
    '😂 Šta kaže vjetar oblaku? "Padaš mi na živce!"',
    '🤣 Zašto lav ne voli fast food? Ne može ga uloviti!',
    '😄 Kako se zove riba koja nosi krunu? Kralj-evska!',
    '😂 Zašto pilići ne igraju fudbal? Stalno udaraju jaje.',
    '🤣 Šta kaže banana kad je tužna? "Osjećam se oljušteno."',
    '😄 Zašto biciklisti nikad ne gube? Jer uvijek pedale!',
    '😂 Kako se zove morski pas koji pjeva? Tune-a!',
    '🤣 Zašto je frižider hladnokrvan? Jer je cool!',
    '😄 Šta kaže WiFi routeru korisnik? "Mi smo povezani!"',
    '😂 Zašto ne biste vjerovali atomu? Jer čine sve!',
    '🤣 Kako se zove jako spor dinosaur? Dino-saurus.',
    '😄 Zašto je rječnik tako pametan? Ima sve riječi!',
    '😂 Šta kaže stopalo cipeli? "Ti me pritišćeš!"',
    '🤣 Zašto je sunce dobro u školi? Ima sjajne ocjene!',

    // === EVEN MORE BOSNIA FACTS ===
    '🌊 Rijeka Bosna je najduža rijeka potpuno u BiH.',
    '🏔️ Igman je planina na kojoj se održavalo ski trčanje 1984.',
    '⛷️ Bjelašnica je bila domaćin alpskog skijanja 1984.',
    '🌉 Mostar znači "čuvar mosta" - od riječi "most" i "star".',
    '🏛️ Stari most u Mostaru srušen je 1993., obnovljen 2004.',
    '📜 Bosanski stećci imaju urezane scene lova i plesa.',
    '🌿 Hutovo blato je močvarno stanište ptica u Hercegovini.',
    '🐟 Neretva ima endemske vrste riba.',
    '🏔️ Vlašić je planina poznata po vlašićkom siru.',
    '🧀 Vlašićki sir je jedan od najpoznatijih u BiH.',
    '🌲 BiH ima mediteransku klimu na jugu, kontinentalnu na sjeveru.',
    '🏙️ Doboj je poznat po srednjovjekovnoj tvrđavi.',
    '🏛️ Stolac je jedan od najstarijih gradova u BiH.',
    '📍 Počitelj je srednjovjekovna utvrda iznad Neretve.',
    '🌉 Most na Drini u Višegradu inspirisao je Andrića za roman.',
    '📖 Ivo Andrić je dobitnik Nobelove nagrade za književnost.',
    '🎭 Sarajevo Film Festival je najveći filmski festival u regionu.',
    '🎵 Sevdalinka je tradicionalna bosanska ljubavna pjesma.',
    '🎻 Saz je tradicionalni instrument za sevdalinku.',
    '🏺 Bosanska keramika ima tradiciju od neolita.',

    // === FINAL JOKES ===
    '😄 Zašto je 6 uplašena od 7? Jer 7 8 9!',
    '😂 Šta kaže led kocki? "Baš si cool!"',
    '🤣 Zašto baterija nikad nije usamljena? Jer ima + i -.',
    '😄 Kako se zove lijeni kangaroo? Pouch-tato!',
    '😂 Zašto olovka ne može pobijediti? Jer uvijek ima šiljak!',
    '🤣 Šta kaže sat alarmu? "Budiš uspomene!"',
    '😄 Zašto je pas išao u ured? Htio je psa-osao!',
    '😂 Kako se zove lijen panda? Bam-zz-boo.',
    '🤣 Zašto pčele brzo lete? Jer su buzz-ne!',
    '😄 Šta kaže kaktus kad ga dodirneš? "Ouch-ita!"',

    // === BONUS BOSNIA FACTS ===
    '🌍 BiH graniči s Hrvatskom, Srbijom i Crnom Gorom.',
    '🗺️ BiH ima površinu od 51.197 km².',
    '👥 BiH ima oko 3,3 miliona stanovnika.',
    '💰 Službena valuta BiH je konvertibilna marka (KM).',
    '🏛️ BiH ima dva entiteta: FBiH i Republiku Srpsku.',
    '🌐 Glavni grad BiH je Sarajevo.',
    '📞 Pozivni broj za BiH je +387.',
    '🚗 Registarske oznake u BiH počinju slovima grada.',
    '✈️ Sarajevo ima međunarodni aerodrom.',
    '🚂 BiH ima željezničku mrežu koja povezuje glavne gradove.',
    '🏥 BiH ima javno zdravstvo.',
    '🎓 Obrazovanje u BiH je obavezno do 15. godine.',
    '🌡️ Prosječna temperatura u Sarajevu je 10°C.',
    '❄️ Zime u BiH mogu biti veoma hladne, do -20°C.',
    '☀️ Ljeta u Hercegovini dostižu i do 40°C.',
    '🌧️ Jesen je najkišovitije doba godine u BiH.',
    '🌸 Proljeće u BiH je posebno lijepo - cvjetaju voćnjaci!',
    '🍂 Jesen donosi berbu grožđa u Hercegovini.',
    '🎄 Božić se u BiH slavi i 25.12. i 7.1.',
    '🌙 Ramazan je značajan praznik za muslimane u BiH.'
  ]
}

// Common Bosnian household items for search suggestions
const commonSearchItems = [
  'mlijeko, hljeb, jaja',
  'piletina, povrće, riža',
  'kafa, šećer, mlijeko',
  'brasno, ulje, jaja',
  'jogurt, sir, kajmak',
  'banane, jabuke, narandže',
  'paradajz, paprika, krastavci',
  'šampon, sapun, pasta za zube',
  'deterdžent, omekšivač',
  'čokolada, keks, čips',
  'tjestenina, sos, parmezan',
  'mesni narezak, salama, šunka',
  'sok, mineralna voda',
  'maslac, margarin, pavlaka',
  'čaj, med, limun',
  'luk, bijeli luk, krompir',
  'pirinač, grah, leća',
  'konzerve, tunjevina',
  'pelene, maramice',
  'WC papir, ubrusi'
]

function getRandomSearchSuggestion(): string {
  const index = Math.floor(Math.random() * commonSearchItems.length)
  return commonSearchItems[index]
}

function getLoadingMessages(query: string): string[] {
  const lowerQuery = query.toLowerCase()

  // Check for keywords in the query
  for (const [category, messages] of Object.entries(funMessages)) {
    if (category !== 'generic' && lowerQuery.includes(category)) {
      return messages
    }
  }

  // Return generic messages if no category matches
  return funMessages.generic
}

function startLoadingMessages(query: string) {
  const messages = getLoadingMessages(query)
  let currentIndex = 0

  // Set initial message
  currentLoadingMessage.value = messages[0]

  // Clear any existing interval
  if (loadingMessageInterval.value) {
    clearInterval(loadingMessageInterval.value)
  }

  // Rotate messages every 3 seconds
  loadingMessageInterval.value = setInterval(() => {
    currentIndex = (currentIndex + 1) % messages.length
    currentLoadingMessage.value = messages[currentIndex]
  }, 3000)
}

function stopLoadingMessages() {
  if (loadingMessageInterval.value) {
    clearInterval(loadingMessageInterval.value)
    loadingMessageInterval.value = null
  }
  currentLoadingMessage.value = ''
}

// Helper to wait for auth to be ready
async function waitForAuth() {
  // If auth is already ready, return immediately
  if (authReady.value) return

  // Wait for auth to be ready (with timeout)
  return new Promise<void>((resolve) => {
    const unwatch = watch(authReady, (ready) => {
      if (ready) {
        unwatch()
        resolve()
      }
    }, { immediate: true })

    // Timeout after 3 seconds to prevent infinite wait
    setTimeout(() => {
      unwatch()
      resolve()
    }, 3000)
  })
}

// Load initial data
onMounted(async () => {
  // First ensure auth is checked/ready
  await checkAuth()
  await waitForAuth()

  // Load "only discounted" preference from localStorage
  loadOnlyDiscountedPreference()

  await loadSavingsStats()
  await loadFeaturedData()
  await loadStorePreferences()
  await checkForNewStores()
  await loadDiscountFreshness()

  // Auto-search if autoSearch query param is present (from login/register redirect)
  const route = useRoute()
  const autoSearchQuery = route.query.autoSearch as string
  if (autoSearchQuery) {
    searchQuery.value = autoSearchQuery
    // Wait a bit for UI to load, then trigger search
    setTimeout(() => {
      performSearch()
    }, 500)
  } else if (user.value && !user.value.first_search_reward_claimed) {
    // Pre-fill search with a random common item for new users who haven't searched yet
    // This encourages them to try their first search
    searchQuery.value = getRandomSearchSuggestion()
  }

  // Check for product ID in URL (for direct links)
  const productId = route.query.product as string
  if (productId) {
    await loadProductFromUrl(parseInt(productId))
  }

  // Setup exit intent detection for anonymous users
  setupExitIntent()
})

// Cleanup on unmount
onUnmounted(() => {
  stopLoadingMessages()
  // Clean up exit intent listener
  if (process.client) {
    document.removeEventListener('mouseout', handleMouseOut)
    window.removeEventListener('scroll', handleScrollForFeedback)
  }
})

// Scroll detection for anonymous feedback popup
const feedbackScrollTriggered = ref(false)

function setupScrollFeedbackDetection() {
  if (process.client && !user.value) {
    window.addEventListener('scroll', handleScrollForFeedback)
  }
}

function handleScrollForFeedback() {
  if (feedbackScrollTriggered.value || user.value) return

  // Check if search results exist
  if (!searchResults.value?.products) return

  // Get scroll position
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight

  // Trigger when user has scrolled 80% of the way down
  const scrollPercentage = (scrollTop + windowHeight) / documentHeight

  if (scrollPercentage > 0.8) {
    feedbackScrollTriggered.value = true
    window.removeEventListener('scroll', handleScrollForFeedback)

    // Call the global function exposed by app.vue
    if ((window as any).showAnonymousFeedback) {
      (window as any).showAnonymousFeedback()
    }
  }
}

function setupExitIntent() {
  // Don't show if user is logged in
  if (user.value) return

  // Don't show if already shown in last 24 hours
  const lastShown = localStorage.getItem('exit_intent_shown')
  if (lastShown && Date.now() - parseInt(lastShown) < 24 * 60 * 60 * 1000) {
    return
  }

  // Detect mouse leaving viewport
  document.addEventListener('mouseout', handleMouseOut)
}

function handleMouseOut(e: MouseEvent) {
  // Only trigger once
  if (exitIntentTriggered.value) return

  // Only on desktop (not on mobile where this doesn't work well)
  if (window.innerWidth < 768) return

  // Mouse moved to top of viewport (trying to close tab/go back)
  if (e.clientY < 10 && e.relatedTarget === null) {
    exitIntentTriggered.value = true
    showExitIntentModal.value = true
  }
}

function closeExitModal() {
  showExitIntentModal.value = false
}

// Load product from URL parameter
async function loadProductFromUrl(productId: number) {
  // First check if product is already in featured products
  const existingProduct = featuredProducts.value.find(p => p.id === productId)
  if (existingProduct) {
    // Product is already displayed, let ProductCard handle it
    return
  }

  // Fetch product from API
  try {
    const product = await get(`/api/products/${productId}`)
    if (product && product.id) {
      urlProduct.value = product
      showUrlProductModal.value = true
    }
  } catch (error) {
    console.error('Error loading product from URL:', error)
  }
}

function closeUrlProductModal() {
  showUrlProductModal.value = false
  urlProduct.value = null
  // Remove product ID from URL
  const url = new URL(window.location.href)
  url.searchParams.delete('product')
  window.history.pushState({}, '', url.toString())
}

async function loadSavingsStats() {
  try {
    const data = await get('/api/savings-stats')
    savingsStats.value = data
  } catch (error) {
    console.error('Error loading savings stats:', error)
  }
}

async function loadFeaturedData() {
  try {
    const data = await get('/api/featured-data')
    featuredProducts.value = data.products || []

    // Load active businesses separately
    featuredBusinesses.value = await get('/api/active-businesses')
  } catch (error) {
    console.error('Error loading featured data:', error)
  }
}

async function loadDiscountFreshness() {
  try {
    const data = await get('/api/store-discounts-freshness')
    discountFreshness.value = data.stores || []
  } catch (error) {
    console.error('Error loading discount freshness:', error)
  }
}

async function loadStorePreferences() {
  try {
    // Load all active businesses for the store filter (including those without products)
    const response = await get('/api/businesses?all=true')
    allStores.value = (response.businesses || []).map((b: any) => ({
      id: b.id,
      name: b.name,
      logo: b.logo_path,
      city: b.city
    }))

    // Load user's store preferences if authenticated
    if (isAuthenticated.value) {
      try {
        const prefs = await get('/auth/user/store-preferences')
        if (prefs.preferred_stores && prefs.preferred_stores.length > 0) {
          selectedStoreIds.value = prefs.preferred_stores
        }
      } catch (error) {
        console.error('Error loading store preferences:', error)
      }
    } else {
      // For anonymous users, check localStorage
      const savedStores = localStorage.getItem('preferred_stores')
      if (savedStores) {
        try {
          selectedStoreIds.value = JSON.parse(savedStores)
        } catch (e) {
          // Invalid JSON, ignore
        }
      }
    }
  } catch (error) {
    console.error('Error loading stores:', error)
  }
}

async function checkForNewStores() {
  try {
    let lastSeenId = 0

    // Get last seen store ID
    if (isAuthenticated.value) {
      // Will be fetched from user preferences via the API
      const lastSeenFromStorage = localStorage.getItem('last_seen_store_id')
      if (lastSeenFromStorage) {
        lastSeenId = parseInt(lastSeenFromStorage) || 0
      }
    } else {
      const lastSeenFromStorage = localStorage.getItem('last_seen_store_id')
      if (lastSeenFromStorage) {
        lastSeenId = parseInt(lastSeenFromStorage) || 0
      }
    }

    // Check for new stores
    const response = await get(`/auth/new-stores?last_seen_id=${lastSeenId}`)

    if (response.has_new_stores && response.new_stores.length > 0) {
      newStores.value = response.new_stores
      latestStoreId.value = response.latest_store_id
      showNewStorePopup.value = true
    }
  } catch (error) {
    console.error('Error checking for new stores:', error)
  }
}

function handleNewStoresSelected(storeIds: number[]) {
  // Add selected new stores to the filter
  const current = new Set(selectedStoreIds.value)
  storeIds.forEach(id => current.add(id))
  selectedStoreIds.value = Array.from(current)

  // Save for anonymous users
  if (!isAuthenticated.value) {
    localStorage.setItem('preferred_stores', JSON.stringify(selectedStoreIds.value))
  }
}

function handleNewStoresDismissed() {
  // User skipped - don't add new stores to filter
  console.log('New stores popup dismissed')
}

function handleCitySaved(city: string) {
  // City was saved, now perform the pending search
  showCityRequiredModal.value = false
  if (pendingSearchQuery.value) {
    searchQuery.value = pendingSearchQuery.value
    pendingSearchQuery.value = ''
    // Small delay to ensure user object is updated
    setTimeout(() => {
      performSearch()
    }, 100)
  }
}

// Watch for store selection changes - save preferences
watch(selectedStoreIds, async (newVal) => {
  if (isAuthenticated.value) {
    // Save to backend for authenticated users
    try {
      await put('/auth/user/store-preferences', {
        preferred_stores: newVal
      })
    } catch (error) {
      console.error('Error saving store preferences:', error)
    }
  } else {
    // Save to localStorage for anonymous users
    localStorage.setItem('preferred_stores', JSON.stringify(newVal))
  }
})

async function performSearch() {
  // Prevent duplicate calls from rapid taps on mobile
  if (isSearching.value) return

  const query = searchQuery.value.trim()
  if (!query) {
    return
  }

  // Check localStorage for anonymous search limit (double verification with backend)
  if (!user.value) {
    const hasUsedAnonymousSearch = localStorage.getItem('anonymous_search_used')
    if (hasUsedAnonymousSearch === 'true') {
      registrationMessage.value = 'Iskoristili ste besplatnu pretragu. Molimo registrujte se da nastavite koristiti platformu.'
      showRegistrationModal.value = true
      return
    }
  }

  // Check if logged-in user has a city set
  if (user.value && !user.value.city) {
    pendingSearchQuery.value = query
    showCityRequiredModal.value = true
    return
  }

  isSearching.value = true
  searchResults.value = null

  // Start fun loading messages
  startLoadingMessages(query)

  try {
    // Build search payload with optional store filter
    const searchPayload: any = { query }

    // Check if stores are loaded but none are selected
    if (allStores.value.length > 0 && selectedStoreIds.value.length === 0) {
      // User has explicitly deselected all stores - return no results
      stopLoadingMessages()
      searchResults.value = {
        response: 'Niste odabrali nijednu prodavnicu. Molimo odaberite barem jednu prodavnicu za pretragu.',
        products: []
      }
      isSearching.value = false
      return
    }

    if (selectedStoreIds.value.length > 0) {
      searchPayload.business_ids = selectedStoreIds.value
    }

    if (onlyDiscounted.value) {
      searchPayload.only_discounted = true
    }

    // Use new agent endpoint with multi-agent system
    const data = await post('/api/search', searchPayload)

    if (data.error) {
      if (data.error === 'anonymous_limit_reached') {
        // Anonymous user has used their free search - show registration modal
        registrationMessage.value = data.message
        showRegistrationModal.value = true
        // Set localStorage flag
        localStorage.setItem('anonymous_search_used', 'true')
      } else if (data.error === 'free_trial_expired') {
        // Show registration modal for anonymous users who used their free search
        registrationMessage.value = data.message
        showRegistrationModal.value = true
      } else if (data.error === 'credits_exhausted') {
        // Show credits exhausted message with link to "get more" page
        const message = data.message + ' <br><br><a href="/krediti-uskoro" class="text-purple-600 underline font-bold">Saznajte kako dobiti više kredita →</a>'
        searchResults.value = { response: message, products: [] }
      } else if (data.error === 'registration_required') {
        registrationMessage.value = data.message
        showRegistrationModal.value = true
      } else if (data.error === 'limit_exceeded' || data.error === 'no_results') {
        // Show message in results area
        searchResults.value = { response: data.message, products: [] }
      } else {
        // Show generic error message
        searchResults.value = { response: data.error, products: [] }
      }
    } else if (data.success) {
      // Transform new agent response format to match UI expectations
      searchResults.value = {
        response: data.explanation || 'Rezultati pretrage',
        products: data.products || data.results || [],  // Backend uses 'products', legacy uses 'results'
        intent: data.intent,
        metadata: data.metadata,
        credits_remaining: data.credits_remaining,
        is_anonymous: data.is_anonymous,  // Show teasers if true
        original_query: query  // Save query for login redirect
      }

      // Update credits in header immediately
      if (data.credits_remaining !== undefined) {
        updateCreditsRemaining(data.credits_remaining)
      }

      // Show celebration toast for first search bonus
      if (data.first_search_bonus) {
        showSuccess('Čestitamo! Dobili ste +3 bonus kredita za vašu prvu pretragu!', 'Bonus krediti!')
      }

      // If this was an anonymous search, mark it as used in localStorage
      if (data.is_anonymous) {
        localStorage.setItem('anonymous_search_used', 'true')
      }

      // Show korpa education popup (one-time) for logged-in users after getting results
      if (!data.is_anonymous && user.value) {
        const hasSeenKorpaEducation = localStorage.getItem('korpa_education_seen')
        if (!hasSeenKorpaEducation) {
          // Show popup with slight delay so user sees results first
          setTimeout(() => {
            showKorpaEducation.value = true
          }, 1500)
        }
      }

      // Expand all groups by default when new results come in
      const productsData = data.products || data.results
      if (isGroupedResults(productsData)) {
        const groupNames = Object.keys(productsData)
        expandedGroups.value = new Set(groupNames)
        // Set first group as active for mobile navigation
        if (groupNames.length > 0) {
          activeGroup.value = groupNames[0]
        }
        // Reset group refs for new results
        groupRefs.value = {}
      }

      // Setup scroll detection for anonymous feedback popup
      if (data.is_anonymous) {
        setupScrollFeedbackDetection()
      }

      // Track product impressions from search results (async, non-blocking)
      if (!data.is_anonymous) {
        const productsData = data.products || data.results
        trackSearchProductViews(productsData)
      }
    }
  } catch (error) {
    console.error('Search error:', error)
    searchResults.value = { response: 'Došlo je do greške. Molim vas pokušajte ponovo.', products: [] }
  } finally {
    isSearching.value = false
    // Stop fun loading messages
    stopLoadingMessages()
  }
}

function toggleGroup(groupName: string) {
  if (expandedGroups.value.has(groupName)) {
    expandedGroups.value.delete(groupName)
  } else {
    expandedGroups.value.add(groupName)
  }
  // Force reactivity update
  expandedGroups.value = new Set(expandedGroups.value)
}

// Track search result product views asynchronously (non-blocking)
function trackSearchProductViews(productsData: any) {
  if (!productsData || !process.client) return

  const token = localStorage.getItem('token')
  if (!token) return

  // Extract product IDs from grouped or flat results
  let productIds: number[] = []

  if (isGroupedResults(productsData)) {
    // Grouped results: iterate through each group
    for (const groupProducts of Object.values(productsData)) {
      if (Array.isArray(groupProducts)) {
        productIds.push(...(groupProducts as any[]).map((p: any) => p.id).filter(Boolean))
      }
    }
  } else if (Array.isArray(productsData)) {
    // Flat array of products
    productIds = productsData.map((p: any) => p.id).filter(Boolean)
  }

  if (productIds.length === 0) return

  try {
    // Fire and forget - don't await, don't block UI
    fetch(`${config.public.apiBase}/api/products/track-views`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ product_ids: productIds })
    }).catch(() => {
      // Silently ignore tracking errors
    })
  } catch {
    // Silently ignore tracking errors
  }
}

function isGroupedResults(products: any): boolean {
  // Check if products is an object (grouped) rather than an array (flat)
  return products && typeof products === 'object' && !Array.isArray(products)
}

function capitalizeWords(text: string): string {
  if (!text) return ''

  // Split by spaces and capitalize each word
  return text
    .split(' ')
    .map(word => {
      if (!word) return word
      // Capitalize first letter and keep the rest as is
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    })
    .join(' ')
}

function sanitizeResponse(html: string): string {
  // Sanitize HTML response - allow only spans with safe styles
  const spanPattern = /<span\s+style="([^"]*)"[^>]*>(.*?)<\/span>/gi

  let sanitized = html.replace(spanPattern, (match, styleAttr, content) => {
    const allowedStyles = ['background-color', 'color', 'padding', 'border-radius', 'font-weight', 'text-decoration']
    const styles = styleAttr.split(';').map((s: string) => s.trim()).filter((s: string) => s)
    const validStyles: string[] = []

    styles.forEach((style: string) => {
      const [prop, value] = style.split(':').map((s: string) => s.trim())
      if (prop && value && allowedStyles.includes(prop)) {
        if (!value.includes('javascript:') && !value.includes('expression(') && !value.includes('url(')) {
          validStyles.push(`${prop}: ${value}`)
        }
      }
    })

    if (validStyles.length > 0) {
      return `<span style="${validStyles.join('; ')}">${content}</span>`
    }
    return content
  })

  // Remove any other HTML tags
  sanitized = sanitized.replace(/<(?!span\s|\/span)[^>]*>/gi, '')

  return sanitized
}

useSeoMeta({
  title: 'Popust.ba - Pronađite najbolje popuste',
  description: 'Koristite naš Popust asistent da brzo pronađete gdje su danas najjeftiniji proizvodi i najbolje akcije u vašem gradu',
  ogTitle: 'Popust.ba',
  ogDescription: 'Vaš inteligentni asistent za kupovinu',
  twitterCard: 'summary_large_image',
})
</script>

<style scoped>
.gradient-bg {
  background: linear-gradient(135deg, rgba(103, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
  position: relative;
}

.chat-input {
  color: #111827 !important; /* gray-900 */
}

.chat-input::placeholder {
  color: #9ca3af; /* gray-400 */
}

.chat-example {
  transition: all 0.3s ease;
}

.chat-example:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.purple-pattern-overlay {
  position: relative;
  overflow: hidden;
}

.purple-pattern-overlay::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 1px, transparent 1px),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 1px, transparent 1px),
    radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 20px 20px, 25px 25px, 15px 15px;
  background-position: 0 0, 10px 10px, 5px 5px;
  pointer-events: none;
  z-index: 1;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

/* Hide scrollbar for navigation pills */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Subtle pulse animation for scroll arrows */
@keyframes pulse-subtle {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
}
.animate-pulse-subtle {
  animation: pulse-subtle 2s ease-in-out infinite;
}
</style>
