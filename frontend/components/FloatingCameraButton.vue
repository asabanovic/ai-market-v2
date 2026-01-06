<template>
  <!-- Mobile floating camera button - only show on mobile -->
  <div class="fixed left-4 bottom-20 z-50 md:hidden">
    <!-- Expanded options -->
    <transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-4"
    >
      <div v-if="isExpanded" class="flex flex-col gap-3 mb-3">
        <!-- Gallery upload button -->
        <button
          @click.stop="openGallery"
          class="flex items-center gap-3 pl-1 pr-4 py-1 bg-white text-gray-700 rounded-full shadow-lg hover:bg-gray-50 transition-colors"
        >
          <div class="w-12 h-12 flex items-center justify-center bg-purple-100 rounded-full">
            <svg class="w-6 h-6 text-purple-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <span class="text-sm font-medium text-gray-800 whitespace-nowrap">Iz galerije</span>
        </button>

        <!-- Camera button -->
        <button
          @click.stop="openCamera"
          class="flex items-center gap-3 pl-1 pr-4 py-1 bg-white text-gray-700 rounded-full shadow-lg hover:bg-gray-50 transition-colors"
        >
          <div class="w-12 h-12 flex items-center justify-center bg-purple-100 rounded-full">
            <svg class="w-6 h-6 text-purple-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span class="text-sm font-medium text-gray-800 whitespace-nowrap">Slikaj uživo</span>
        </button>
      </div>
    </transition>

    <!-- Main button -->
    <button
      @click.stop="toggleExpanded"
      class="flex items-center gap-2 pl-1 pr-4 py-1 bg-purple-600 text-white rounded-full shadow-lg hover:bg-purple-700 transition-all"
    >
      <div class="w-12 h-12 flex items-center justify-center bg-purple-500 rounded-full">
        <svg v-if="!isExpanded" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <svg v-else class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
      <span class="text-sm font-medium whitespace-nowrap">Traži slikom</span>
    </button>

    <!-- Hidden file inputs -->
    <input
      ref="cameraInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden"
      @change="handleFileSelect"
    />
    <input
      ref="galleryInput"
      type="file"
      accept="image/*"
      class="hidden"
      @change="handleFileSelect"
    />
  </div>

  <!-- Results Modal -->
  <Teleport to="body">
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
      @click.self="closeModal"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl max-w-lg w-full max-h-[90vh] overflow-hidden shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ isLoading ? 'Tražim...' : 'Rezultati pretrage' }}
          </h3>
          <button
            @click="closeModal"
            class="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="p-4 overflow-y-auto max-h-[calc(90vh-120px)]">
          <!-- Loading State -->
          <div v-if="isLoading" class="flex flex-col items-center py-8">
            <div class="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p class="text-gray-600 dark:text-gray-400 text-center px-4">{{ currentJoke }}</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="text-center py-8">
            <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-red-600 dark:text-red-400">{{ error }}</p>
            <button
              @click="closeModal"
              class="mt-4 px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Zatvori
            </button>
          </div>

          <!-- Results -->
          <div v-else-if="result">
            <!-- Identified Product Info -->
            <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 mb-4">
              <div class="flex items-start gap-3">
                <svg class="w-6 h-6 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ result.identified_product?.title || 'Proizvod prepoznat' }}
                  </p>
                  <p v-if="result.identified_product?.brand" class="text-sm text-gray-600 dark:text-gray-400">
                    Brend: {{ result.identified_product.brand }}
                  </p>
                  <p v-if="result.interest_added" class="text-sm text-green-600 dark:text-green-400 mt-1">
                    Dodano na listu interesa
                  </p>
                </div>
              </div>
            </div>

            <!-- Products Found -->
            <div v-if="result.products?.length > 0">
              <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Pronađeno {{ result.products.length }} proizvoda:
              </h4>
              <div class="space-y-3">
                <div
                  v-for="product in result.products"
                  :key="product.id"
                  class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                  @click="goToProduct(product)"
                >
                  <img
                    v-if="product.image_path"
                    :src="getProductImageUrl(product.image_path)"
                    :alt="product.title"
                    class="w-14 h-14 object-cover rounded-lg"
                  />
                  <div v-else class="w-14 h-14 bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center">
                    <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="font-medium text-gray-900 dark:text-white truncate">{{ product.title }}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">{{ product.business?.name }}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <span v-if="product.has_discount" class="text-sm line-through text-gray-400">
                        {{ formatPrice(product.base_price) }}
                      </span>
                      <span :class="product.has_discount ? 'text-red-600 font-bold' : 'text-gray-900 dark:text-white'">
                        {{ formatPrice(product.discount_price || product.base_price) }}
                      </span>
                    </div>
                  </div>
                  <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>

            <!-- No Products Found -->
            <div v-else class="text-center py-4">
              <p class="text-gray-600 dark:text-gray-400">
                Nismo pronašli ovaj proizvod u bazi. Dodali smo ga na vašu listu interesa i obavijestit ćemo vas kada bude dostupan na akciji.
              </p>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div v-if="result && !isLoading" class="p-4 border-t dark:border-gray-700">
          <button
            @click="closeModal"
            class="w-full py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
          >
            Zatvori
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
interface Product {
  id: number
  title: string
  brand: string | null
  base_price: number | null
  discount_price: number | null
  image_path: string | null
  has_discount: boolean
  business: {
    id: number
    name: string
  }
}

interface CameraSearchResult {
  success: boolean
  identified_product: {
    title: string | null
    brand: string | null
    product_type: string | null
    confidence: string
  }
  products: Product[]
  interest_added: boolean
  search_terms: string[]
}

const config = useRuntimeConfig()
const router = useRouter()
const { isAuthenticated, token } = useAuth()

const cameraInput = ref<HTMLInputElement | null>(null)
const galleryInput = ref<HTMLInputElement | null>(null)
const showModal = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)
const result = ref<CameraSearchResult | null>(null)
const isExpanded = ref(false)

// Fun jokes to show during loading
const jokes = [
  'Učitavam sve svoje filmove o hrani...',
  'Konsultujem svoju baku o cijenama...',
  'Pretražujem sve kataloge od 1995...',
  'Pitam komšiju da li je ovo na akciji...',
  'Provjeravam da li je ovo skuplje od aviona...',
  'Računam koliko ćevapa možeš kupiti za ovu cijenu...',
  'Guglam "kako prepoznati dobar popust"...',
  'Pijem kafu dok razmišljam...',
  'Gledam gdje je Mujo kupio jeftinije...',
  'Provjeravam cijene na pijaci za svaki slučaj...',
  // 40 more jokes
  'Zovem mamu da pita komšinicu...',
  'Preračunavam cijene u burek jedinice...',
  'Provjeravam koliko bi ovo koštalo u Jugoslaviji...',
  'Pitam tatu, ali on kaže "pitaj mamu"...',
  'Tražim kupon koji sam izrezao 2003. godine...',
  'Računam koliko kafa mogu kupiti za ovu cijenu...',
  'Provjeravam da li ima jeftinije u Austriji...',
  'Pitam Hasu šta misli o ovoj cijeni...',
  'Gledam da li je ovo skuplje od goriva...',
  'Čekam da mi se učita internet iz 1999...',
  'Listam staru enciklopediju cijena...',
  'Pitam djeda kako su oni kupovali bez akcija...',
  'Uspoređujem sa cijenama iz Avazovog kataloga...',
  'Tražim po svim ladicama stare račune...',
  'Provjeravam da li ovo mogu platiti u ratama do 2050...',
  'Računam koliko sati moram raditi za ovo...',
  'Gledam gdje je Suljo našao jeftinije...',
  'Provjeravam cijene na svim kontinentima...',
  'Zovem rođaka iz Njemačke da uporedi...',
  'Računam u starim njemačkim markama...',
  'Pretražujem arhive svih kataloga ikada...',
  'Pitam prodavačicu da li zna za bolju cijenu...',
  'Provjeravam mjesečeve faze za najbolju kupovinu...',
  'Konsultujem horoskop za finansijske odluke...',
  'Tražim onaj letak koji sam bacio prošle sedmice...',
  'Računam koliko bureka mogu kupiti za ovo...',
  'Zovem call centar, ali sam 47. u redu...',
  'Provjeravam da li je skuplje od kvadrata stana...',
  'Gledam recenzije od 1987. godine...',
  'Pitam Google, ali i on razmišlja...',
  'Uspoređujem sa cijenom moje prve plaće...',
  'Provjeravam da li je ovo legalno skupo...',
  'Tražim alternativu na OLX-u...',
  'Računam koliko sendviča mogu napraviti za ovo...',
  'Zovem prijatelja koji "poznaje nekog"...',
  'Provjeravam da li je jeftinije napraviti sam...',
  'Čekam da istekne akcija pa da se kajem...',
  'Analiziram tržište kao pravi ekonomista...',
  'Pravim Excel tabelu za usporedbu cijena...',
  'Pitam ChatGPT za drugo mišljenje...'
]

const jokeIndex = ref(0)
const jokeInterval = ref<NodeJS.Timeout | null>(null)

const currentJoke = computed(() => jokes[jokeIndex.value])

// Start/stop joke cycling when loading changes
watch(isLoading, (loading) => {
  if (loading) {
    // Start with random joke
    jokeIndex.value = Math.floor(Math.random() * jokes.length)
    // Cycle every 2.5 seconds
    jokeInterval.value = setInterval(() => {
      jokeIndex.value = (jokeIndex.value + 1) % jokes.length
    }, 2500)
  } else {
    if (jokeInterval.value) {
      clearInterval(jokeInterval.value)
      jokeInterval.value = null
    }
  }
})

// Generate or get session ID for analytics
const sessionId = ref<string>('')
onMounted(() => {
  sessionId.value = localStorage.getItem('camera_session_id') || `cam_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  localStorage.setItem('camera_session_id', sessionId.value)
})

// Track camera button actions for analytics
async function trackCameraAction(action: string) {
  try {
    const apiBase = config.public.apiBase || 'http://localhost:5001'
    await fetch(`${apiBase}/api/track/camera-button`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token.value ? { 'Authorization': `Bearer ${token.value}` } : {})
      },
      body: JSON.stringify({
        action,
        session_id: sessionId.value,
        page_url: window.location.pathname
      })
    })
  } catch (e) {
    // Silently fail - analytics shouldn't break the app
  }
}

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    trackCameraAction('expand')
  }
}

function openCamera() {
  if (!isAuthenticated.value) {
    navigateTo('/prijava?redirect=' + encodeURIComponent(window.location.pathname))
    return
  }
  trackCameraAction('camera_click')
  isExpanded.value = false
  cameraInput.value?.click()
}

function openGallery() {
  if (!isAuthenticated.value) {
    navigateTo('/prijava?redirect=' + encodeURIComponent(window.location.pathname))
    return
  }
  trackCameraAction('gallery_click')
  isExpanded.value = false
  galleryInput.value?.click()
}

// Close expanded menu when clicking outside
onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  // Clean up joke interval
  if (jokeInterval.value) {
    clearInterval(jokeInterval.value)
  }
})

function handleOutsideClick() {
  isExpanded.value = false
}

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  // Track upload start
  trackCameraAction('upload_start')

  // Reset state
  showModal.value = true
  isLoading.value = true
  error.value = null
  result.value = null

  try {
    // Convert to base64
    const base64 = await fileToBase64(file)

    // Call API
    const apiBase = config.public.apiBase || 'http://localhost:5001'
    const response = await fetch(`${apiBase}/api/camera/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify({
        image_base64: base64
      })
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || 'Greška pri pretrazi')
    }

    result.value = await response.json()
    // Track successful upload/search
    trackCameraAction('upload_complete')
  } catch (err: any) {
    error.value = err.message || 'Došlo je do greške'
  } finally {
    isLoading.value = false
    // Reset file input
    if (input) input.value = ''
  }
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // Remove data URL prefix
      const base64 = result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function closeModal() {
  showModal.value = false
  result.value = null
  error.value = null
}

function getProductImageUrl(imagePath: string | null): string {
  if (!imagePath) return ''
  if (imagePath.startsWith('http')) return imagePath
  const apiBase = config.public.apiBase || 'http://localhost:5001'
  if (imagePath.startsWith('/static/')) {
    return `${apiBase}${imagePath}`
  }
  if (imagePath.startsWith('uploads/')) {
    return `${apiBase}/static/${imagePath}`
  }
  return `https://popust-ba.s3.eu-central-1.amazonaws.com/${imagePath}`
}

function formatPrice(price: number | null): string {
  if (price === null) return ''
  return price.toFixed(2) + ' KM'
}

function goToProduct(product: Product) {
  closeModal()
  router.push(`/proizvodi/${product.id}`)
}
</script>
