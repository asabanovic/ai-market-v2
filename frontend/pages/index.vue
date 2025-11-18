<template>
  <div>
    <!-- Dynamic Savings Banner -->
    <div v-if="savingsStats" class="bg-gradient-to-r from-purple-600 to-purple-800 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center justify-center space-x-6 text-sm">
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-yellow-300" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
            </svg>
            <span>Korisnici su ukupno uštedili: <strong>{{ savingsStats.total_savings || 0 }} KM</strong></span>
          </div>
          <div class="hidden md:flex items-center space-x-2">
            <svg class="w-5 h-5 text-green-300" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <span>Prosječno štedite: <strong>{{ savingsStats.average_savings || 0 }} KM</strong> po proizvodu</span>
          </div>
          <div class="hidden lg:flex items-center space-x-2">
            <svg class="w-5 h-5 text-blue-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span><strong>{{ savingsStats.total_products || 0 }}</strong> proizvoda pronađeno s popustom</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Hero Section with Chat -->
    <div class="gradient-bg py-12">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 class="typography-display-responsive text-white mb-4">
          Pronađite najbolje popuste u vašem gradu
        </h1>
        <p class="typography-body text-gray-200 mb-6">
          Koristite naš AI asistent da brzo pronađete gdje su danas najjeftiniji proizvodi i najbolje akcije
        </p>

        <!-- Chat Interface -->
        <div class="bg-white rounded-xl shadow-2xl p-6 max-w-3xl mx-auto">
          <div class="mb-4">
            <label for="chat-input" class="block text-left typography-label text-gray-700 mb-2">
              Pitajte našeg AI asistenta ili unesite listu za kupovinu:
            </label>
            <textarea
              id="chat-input"
              v-model="searchQuery"
              rows="6"
              placeholder="Primjeri:&#10;&#10;• Želim da pravim jelo sa piletinom. Pokaži mi najjeftiniju piletinu u gradu&#10;&#10;• Lista za kupovinu:&#10;  - 1kg piletine&#10;  - 2kg paradajza&#10;  - Milka čokolada&#10;  - Deterdžent za pranje&#10;&#10;(Pokazaćemo vam gdje možete uštedjeti novac!)"
              class="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-y chat-input"
              @keydown.enter.exact.prevent="performSearch"
            />
            <p class="mt-2 text-sm text-gray-600">
              💡 <strong>Tip:</strong> Unesite listu proizvoda koje želite kupiti i vidite gdje možete najviše uštedjeti!
            </p>
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
              <span class="typography-body">Pretražujem...</span>
            </div>
          </div>

          <!-- Results area -->
          <div v-if="searchResults" class="mt-6">

            <!-- Explanation/Response -->
            <div v-if="searchResults.response" class="bg-gray-50 rounded-lg p-4 mb-4">
              <p class="typography-body text-gray-800" v-html="sanitizeResponse(searchResults.response)" />
            </div>

            <!-- Product Results -->
            <div v-if="searchResults.products && searchResults.products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              <ProductCard v-for="product in searchResults.products" :key="product.id" :product="product" />
            </div>

            <!-- No results message -->
            <div v-else-if="!isSearching && searchResults.intent !== 'general'" class="text-gray-500 text-center py-4">
              Nema proizvoda za prikaz.
            </div>
          </div>
        </div>

        <!-- Compact Chat Examples -->
        <div class="mt-6 max-w-3xl mx-auto">
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
                    <span class="text-xs text-gray-300">AI:</span>
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
          <p class="typography-body text-gray-600">Trgovine sa aktivnim proizvodima</p>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
          <NuxtLink
            v-for="business in featuredBusinesses"
            :key="business.id"
            :to="`/proizvodi?business=${business.id}`"
            class="flex flex-col items-center group"
          >
            <div class="w-20 h-20 rounded-full bg-white shadow-md flex items-center justify-center mb-3 group-hover:shadow-lg transition-shadow duration-200 overflow-hidden border-2 border-gray-200 p-2">
              <img
                v-if="business.logo_path"
                :src="`${config.public.apiBase}/static/${business.logo_path}`"
                :alt="business.name"
                class="w-full h-full object-contain"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="w-full h-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center rounded-full">
                <span class="text-white text-2xl font-bold">{{ business.name[0] }}</span>
              </div>
            </div>
            <span class="text-sm font-medium text-gray-900 text-center group-hover:text-purple-600 transition-colors duration-200">
              {{ business.name }}
            </span>
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

        <div class="text-center mt-12">
          <NuxtLink
            to="/proizvodi"
            class="bg-purple-600 text-white px-8 py-3 rounded-lg btn-text hover:bg-purple-700 transition duration-200 purple-pattern-overlay inline-block"
          >
            Pogledajte sve proizvode
          </NuxtLink>
        </div>
      </div>
    </section>

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
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const { get, post } = useApi()

// Reactive state
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref<any>(null)
const savingsStats = ref<any>(null)
const featuredBusinesses = ref<any[]>([])
const featuredProducts = ref<any[]>([])
const showRegistrationModal = ref(false)
const registrationMessage = ref('')

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

// Load initial data
onMounted(async () => {
  await loadSavingsStats()
  await loadFeaturedData()
})

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
    featuredBusinesses.value = data.businesses || []
    featuredProducts.value = data.products || []
  } catch (error) {
    console.error('Error loading featured data:', error)
  }
}

async function performSearch() {
  const query = searchQuery.value.trim()
  if (!query) {
    return
  }

  isSearching.value = true
  searchResults.value = null

  try {
    // Use new agent endpoint with multi-agent system
    const data = await post('/api/search', { query })

    if (data.error) {
      if (data.error === 'registration_required') {
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
        metadata: data.metadata
      }
    }
  } catch (error) {
    console.error('Search error:', error)
    searchResults.value = { response: 'Došlo je do greške. Molim vas pokušajte ponovo.', products: [] }
  } finally {
    isSearching.value = false
  }
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
  title: 'AI Pijaca - Pronađite najbolje popuste',
  description: 'Koristite naš AI asistent da brzo pronađete gdje su danas najjeftiniji proizvodi i najbolje akcije u vašem gradu',
  ogTitle: 'AI Pijaca',
  ogDescription: 'Vaš inteligentni asistent za kupovinu',
  twitterCard: 'summary_large_image',
})
</script>

<style scoped>
.gradient-bg {
  background:
    linear-gradient(135deg, rgba(103, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%),
    url('/static/images/gradient-background.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
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
</style>
