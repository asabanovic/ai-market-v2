<template>
  <div>
    <!-- Hero Section with Chat -->
    <div class="gradient-bg py-12">
      <div class="mx-auto px-6 sm:px-6 lg:px-12 text-center">
        <h1 class="typography-display-responsive text-white mb-4">
          Pronađite najbolje popuste u vašem gradu
        </h1>
        <ClientOnly>
          <template v-if="!user">
            <p class="typography-body text-gray-200 mb-6">
              🎁 <strong>POKLON:</strong> Isprobajte BESPLATNO! Jednu pretragu možete testirati bez registracije
            </p>
          </template>
        </ClientOnly>

        <!-- Chat Interface -->
        <div class="bg-white rounded-xl shadow-2xl p-6 w-full mx-auto" style="max-width: 95vw;">
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
          <div v-if="searchResults" class="mt-6">

            <!-- Explanation/Response -->
            <div v-if="searchResults.response" class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 rounded-lg p-5 mb-6 shadow-md">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0">
                  <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="text-base text-gray-800 leading-relaxed font-medium" v-html="sanitizeResponse(searchResults.response)" />
                </div>
              </div>
            </div>

            <!-- Search Results (for both logged-in and anonymous users) -->
            <div v-if="searchResults.products">
              <!-- Grouped Results with Collapsible Sections -->
              <div v-if="isGroupedResults(searchResults.products)" class="space-y-4">
                <div
                  v-for="(products, groupName) in searchResults.products"
                  :key="groupName"
                  class="border border-gray-200 rounded-lg overflow-hidden"
                >
                  <!-- Group Header (Collapsible) -->
                  <button
                    @click="toggleGroup(groupName)"
                    class="w-full px-4 py-3 flex items-center gap-3 bg-gray-50 hover:bg-gray-100 transition-colors"
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
                  <div v-if="expandedGroups.has(groupName)" class="p-4">
                    <div v-if="products && products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
                      <ProductCard v-for="product in products" :key="product.id" :product="product" />
                    </div>
                    <div v-else class="text-gray-500 text-sm text-center py-4">
                      Nema pronađenih proizvoda za ovu stavku.
                    </div>
                  </div>
                </div>
              </div>

              <!-- Flat Results (legacy) -->
              <div v-else-if="searchResults.products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                <ProductCard v-for="product in searchResults.products" :key="product.id" :product="product" />
              </div>

              <!-- No results message -->
              <div v-else-if="!isSearching && searchResults.intent !== 'general'" class="text-gray-500 text-center py-4">
                Nema proizvoda za prikaz.
              </div>
            </div>
          </div>
        </div>

        <!-- Compact Chat Examples -->
        <div class="mt-6 w-full mx-auto" style="max-width: 95vw;">
          <h3 class="text-white text-sm font-medium mb-3 text-center">Primjeri pretraga:</h3>
          <div class="space-y-2">
            <div v-for="(example, idx) in chatExamples" :key="idx" class="chat-example bg-white/10 backdrop-blur-sm rounded-lg p-3 text-left">
              <div class="flex items-start space-x-3">
                <div class="flex-1">
                  <div class="mb-1">
                    <span class="text-xs text-gray-300">Vi:</span>
                    <span class="text-sm text-white font-medium ml-1">{{ example.user }}</span>
                  </div>
                  <div>
                    <span class="text-xs text-gray-300">Popust:</span>
                    <span class="text-sm text-gray-200 ml-1">{{ example.assistant }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Featured Businesses Section -->
    <section v-if="featuredBusinesses && featuredBusinesses.length > 0" class="py-12 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-8">
          <h2 class="typography-heading-1 text-gray-900 mb-2">SUPERMARKETI</h2>
          <p class="typography-body text-gray-600">Koristite naš Popust asistent da brzo pronađete gdje su danas najjeftiniji proizvodi i najbolje akcije</p>
        </div>

        <div class="flex flex-wrap justify-center items-center gap-6">
          <NuxtLink
            v-for="business in featuredBusinesses"
            :key="business.id"
            :to="`/proizvodi?business=${business.id}`"
            class="hover:opacity-75 transition-opacity"
          >
            <img
              v-if="business.logo"
              :src="business.logo"
              :alt="business.name"
              :title="business.name"
              class="h-10 object-contain"
              @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
            />
          </NuxtLink>
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
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const { get, post, put } = useApi()
const { user, isAuthenticated, authReady, checkAuth } = useAuth()

// Reactive state
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref<any>(null)
const savingsStats = ref<any>(null)
const featuredBusinesses = ref<any[]>([])
const featuredProducts = ref<any[]>([])
const showRegistrationModal = ref(false)
const registrationMessage = ref('')
const expandedGroups = ref<Set<string>>(new Set())
const currentLoadingMessage = ref('')
const loadingMessageInterval = ref<any>(null)

// Store filter state
const allStores = ref<any[]>([])
const selectedStoreIds = ref<number[]>([])

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

// URL product modal state (for direct links)
const urlProduct = ref<any>(null)
const showUrlProductModal = ref(false)

// Computed placeholder text based on authentication
const searchPlaceholder = computed(() => {
  if (user.value) {
    // Logged-in user - simple, no promotional text
    return `Primjeri (unesite bilo šta slično):

• Trebam brasno, mlijeko i čokoladu

• Gdje ima najjeftinija piletina?

• Lista: hljeb, jaja, kafa, deterdžent`
  } else {
    // Anonymous user - promotional text
    return `🎯 BESPLATNI TEST - Probajte sada!

Primjeri (unesite bilo šta slično):

• Trebam brasno, mlijeko i čokoladu

• Gdje ima najjeftinija piletina?

• Lista: hljeb, jaja, kafa, deterdžent

Registracijom dobijate 40 BESPLATNIH pretraga SEDMIČNO i pristup listama za kupovinu!`
  }
})

// Chat examples
const chatExamples = [
  {
    user: 'Trebam nabaviti losos i piletinu',
    assistant: 'Pronađeno: Losos u Mercatoru za 15 KM/kg (-20%), piletina u Bingu za 8 KM/kg'
  },
  {
    user: 'Lista: hljeb, mlijeko, jaja, deterdžent',
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
    '🔍 Popust pretraživač na djelu...',
    '🤖 Analiziram hiljade proizvoda...',
    '💰 Tražim gdje možete uštedjeti...',
    '🎯 Skeniram sve trgovine grada...',
    '⚡ Brža pretraga od Googla!',
    '🛒 Vaš personalni shopping asistent radi...',
    '💎 Tražim skrivene popuste...',
    '🏪 Provjeravam sve supermarkete...',
    '📊 Popust mašina procesuje podatke...',
    '🎁 Možda naletim na iznenađenje...',
    '🚀 Turbo pretraga aktivna...',
    '🧠 Popust mozak razmišlja...',
    '💡 Genijalna ideja: potražimo popust!',
    '🎪 Show počinje... tražim ponude!',
    '🌟 Magija Popust pretrage u toku...'
  ]
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

  await loadSavingsStats()
  await loadFeaturedData()
  await loadStorePreferences()
  await checkForNewStores()

  // Auto-search if autoSearch query param is present (from login/register redirect)
  const route = useRoute()
  const autoSearchQuery = route.query.autoSearch as string
  if (autoSearchQuery) {
    searchQuery.value = autoSearchQuery
    // Wait a bit for UI to load, then trigger search
    setTimeout(() => {
      performSearch()
    }, 500)
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
  }
})

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

// Watch for store selection changes (for anonymous users)
watch(selectedStoreIds, (newVal) => {
  if (!isAuthenticated.value) {
    localStorage.setItem('preferred_stores', JSON.stringify(newVal))
  }
})

async function performSearch() {
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
        products: data.results || [],  // Agent uses 'results' not 'products'
        intent: data.intent,
        metadata: data.metadata,
        credits_remaining: data.credits_remaining,
        is_anonymous: data.is_anonymous,  // Show teasers if true
        original_query: query  // Save query for login redirect
      }

      // If this was an anonymous search, mark it as used in localStorage
      if (data.is_anonymous) {
        localStorage.setItem('anonymous_search_used', 'true')
      }

      // Expand all groups by default when new results come in
      if (isGroupedResults(data.results)) {
        expandedGroups.value = new Set(Object.keys(data.results))
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
</style>
