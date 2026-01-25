<template>
  <div class="relative">
    <!-- Camera Button -->
    <button
      @click="openCamera"
      class="flex items-center gap-1.5 px-2.5 py-1.5 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
      aria-label="Trazi po slici"
      title="Slikaj proizvod da ga pronadjes"
    >
      <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <span class="text-sm font-medium whitespace-nowrap">Trazi slikom</span>
    </button>

    <!-- Hidden File Input -->
    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden"
      @change="handleFileSelect"
    />

    <!-- Results Modal -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 bg-black/50 z-[100] flex items-end sm:items-center justify-center"
        @click.self="closeModal"
      >
        <div class="bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-xl w-full sm:max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl">
          <!-- Header -->
          <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ isLoading ? 'AI trazi...' : 'Rezultati pretrage' }}
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
          <div class="overflow-y-auto max-h-[calc(90vh-120px)]">
            <!-- Image Preview Section - Always show when we have an image -->
            <div v-if="capturedImageUrl" class="p-4 bg-gray-100 dark:bg-gray-900 border-b dark:border-gray-700">
              <div class="flex items-start gap-4">
                <div class="w-28 h-28 flex-shrink-0 rounded-xl overflow-hidden bg-white dark:bg-gray-800 shadow-lg ring-2 ring-primary-500/20">
                  <img
                    :src="capturedImageUrl"
                    alt="Vasa slika"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div class="flex-1 min-w-0 pt-1">
                  <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2 font-medium">Vasa slika</p>
                  <div v-if="isLoading">
                    <p class="text-sm text-primary-600 dark:text-primary-400 font-medium">
                      AI analizira...
                    </p>
                  </div>
                  <div v-else-if="result?.identified_product?.title">
                    <p class="font-semibold text-gray-900 dark:text-white text-lg leading-tight">
                      {{ result.identified_product.title }}
                    </p>
                    <p v-if="result?.identified_product?.brand" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {{ result.identified_product.brand }}
                    </p>
                  </div>
                  <p v-else-if="error" class="text-sm text-red-500">
                    Greska pri analizi
                  </p>
                </div>
              </div>
            </div>

            <!-- Loading State with Fun Jokes -->
            <div v-if="isLoading" class="flex flex-col items-center py-10 px-4">
              <div class="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mb-6"></div>
              <p class="text-gray-900 dark:text-white font-medium text-center mb-2">{{ currentJoke }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">Trazim slicne proizvode...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="text-center py-8 px-4">
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
            <div v-else-if="result" class="pb-4">
              <!-- Interest Added Notice -->
              <div v-if="result.interest_added" class="mx-4 mt-4 bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                <div class="flex items-center gap-2 text-green-700 dark:text-green-400">
                  <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span class="text-sm">Dodano na listu interesa - obavijestit cemo vas kada bude na akciji</span>
                </div>
              </div>

              <!-- Products Found - Horizontal Scroll like moji-proizvodi -->
              <div v-if="result.products?.length > 0" class="mt-4">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 px-4 mb-3">
                  Pronadeno {{ result.products.length }} proizvoda:
                </h4>

                <!-- Horizontal Scroll Container - matches moji-proizvodi style -->
                <div
                  class="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide py-4 gap-4"
                  style="padding-left: calc((100vw - 78vw) / 2); padding-right: calc((100vw - 78vw) / 2);"
                >
                  <ProductCardMobile
                    v-for="product in result.products"
                    :key="product.id"
                    :product="formatProductForCard(product)"
                  />
                </div>

                <!-- Swipe hint -->
                <p v-if="result.products.length > 1" class="text-center text-xs text-gray-400 pb-2">
                  ← Prevuci za više →
                </p>
              </div>

              <!-- No Products Found -->
              <div v-else class="text-center py-8 px-4">
                <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p class="text-gray-600 dark:text-gray-400">
                  Nismo pronasli ovaj proizvod u nasoj bazi.
                </p>
                <p v-if="result.interest_added" class="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  Dodali smo ga na vasu listu interesa i obavijestit cemo vas kada bude dostupan na akciji.
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div v-if="!isLoading" class="p-4 border-t dark:border-gray-700 bg-white dark:bg-gray-800">
            <div class="flex gap-3">
              <button
                @click="retakePhoto"
                class="flex-1 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center justify-center gap-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Nova slika
              </button>
              <button
                @click="closeModal"
                class="flex-1 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
              >
                Zatvori
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
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

// Fun jokes about saving money, being cheap, discounts, etc.
const savingsJokes = [
  "Zasto stedljivi ljudi nikad ne igraju poker? Jer ne vole gubiti ni lipe!",
  "Moj djed je toliko stedljiv da WiFi zove 'besplatna struja'.",
  "Stedim toliko da imam racun na banci... za sitnis.",
  "Zasto nikad ne pozajmljujem novac? Jer ga nikad nemam!",
  "Kupio sam patike na akciji. Sad imam 3 lijeve noge.",
  "Moja zena kaze da sam skrt. Rekao sam joj da to kosta 5 KM.",
  "Akcija 1+1 gratis? Uzeo sam samo gratis.",
  "Stedim na struji - spavam po cijeli dan.",
  "Zasto volim popuste? Jer puna cijena boli.",
  "Nisam skrt, samo finansijski oprezan.",
  "Kupio sam auto na akciji. Samo nema motor.",
  "Stedim vodu - tuširam se na kisi.",
  "Popust od 50%? To je kao da mi placaju da kupujem!",
  "Moj novcanik je kao frizider - uvijek prazan.",
  "Zasto ne kupujem kafu vani? Jer je kod kuce besplatna.",
  "Akcija! Kupi 3, plati 2. Kupio sam 0, platio 0.",
  "Stedim na gorivu - vozim nizbrdo.",
  "Zasto volim zimske akcije? Grijanje je skupo.",
  "Moja banka me zove - da pitaju jesam li dobro.",
  "Kupio sam TV na rate. Otplatio cu do penzije.",
  "Stedim na hrani - jedem kod mame.",
  "Zasto ne idem u teretanu? Trcanje je besplatno!",
  "Popust mi je najdraza rijec poslije 'besplatno'.",
  "Imam app za stednju. Zove se 'prazan novcanik'.",
  "Zasto volim BOGO ponude? Jer B je besplatno!",
  "Stedim na odjeći - nosim istu 10 godina.",
  "Moj budzet je kao dijeta - nikad ne uspije.",
  "Zasto kupujem na akciji? Jer sam pametan!",
  "Stedljiv sam od malena. Cuvao sam mlijecne zube.",
  "Kupio sam cipele na popustu. Samo 2 broja vece.",
  "Zasto stedim? Da mogu vise stediti!",
  "Moja zena trosi. Ja racunam. Dobar smo tim.",
  "Akcija istice? Sad je pravi trenutak!",
  "Stedim na izlascima - Netflix je jeftiniji.",
  "Zasto volim kupone? Besplatni su!",
  "Moj moto: Zasto platiti vise kad mozes manje?",
  "Kupio sam naocale na akciji. Sad vidim ustede svuda!",
  "Stedljiv sam - koristim obe strane toalet papira.",
  "Popust od 70%? Prakticki me placaju!",
  "Zasto ne kupujem brendove? Etiketa ne grije.",
  "Moj otac je bio stedljiv. Naslijedio sam to i dug.",
  "Stedim na poklonima - moja ljubav je besplatna.",
  "Akcije su moj hobi. Usteda je moj sport.",
  "Zasto volim outlet? Jer nisam lud platiti punu cijenu!",
  "Kupio sam frizider na akciji. Hladan je dil!",
  "Stedim na frizerima - sijecam se sam.",
  "Moj budzet za zabavu: 0 KM. Zabavljam se odlicno!",
  "Zasto pratim popuste? Jer me puni cijena deprimira.",
  "Nisam siromasan, samo izrazito stedljiv.",
  "Kupio sam sat na akciji. Vec 5 godina kasni.",
  "Stedim na pranju - cekam kisu.",
  "Zasto volim rasprodaje? Jer volim sebe!",
  "Moj auto trosi malo. Jer ga ne vozim.",
  "Popust + popust = dupla sreca!",
  "Stedljivi ljudi zive duze. Nemamo za groblje.",
  "Zasto ne bacam hranu? Jer kosta!",
  "Kupio sam kauc na akciji. Spavam na njemu. Udobno!",
  "Stedim na kavi - pijem vodu. S okusom kave.",
  "Moja tajne stednje: Nemam tajni. Nemam ni para.",
  "Zasto volim popuste? Jer mrzim bacati novac!",
  "Stedljiv sam - racunam i kalorije i pare.",
  "Akcija na akciji? To je raj!",
  "Zasto kupujem rabljeno? Jer novo je precijenjeno!",
  "Moj djed je stedljiv. Grijanje pali u martu.",
  "Stedim na telefonu - saljem golubove.",
  "Popust je jedina matematika koju volim.",
  "Zasto ne igram loto? Vjerovatnoca je losa investicija.",
  "Kupio sam jaknu na snizenju. Za sljedece godine.",
  "Stedim na sportu - navijam od kuce.",
  "Moj savjet: Nemoj trositi ako ne moras!",
  "Zasto volim second hand? Prvi vlasnik platio premiju!",
  "Stedljiv sam od rodjenja - nisam plakao mnogo.",
  "Akcija istekla? Cekam novu!",
  "Zasto stedim? Penzija dolazi!",
  "Kupio sam mobitel na rate. I dalje ga otplacujem.",
  "Stedim na osvjetljenju - idem spavati rano.",
  "Moj hobi: Uporedivanje cijena. Besplatno!",
  "Zasto volim Black Friday? Jednom godisnje zivim!",
  "Stedljiv sam - pamtim svaku potrosenu paru.",
  "Popust od 90%? Uzimam 10 komada!",
  "Zasto ne putujem? Jer je doma besplatno.",
  "Kupio sam bicikl na akciji. Stedim na gorivu!",
  "Moj budzet: Excel tabela od 47 kartica.",
  "Stedim na darovima - darujem savjete.",
  "Zasto volim e-kupovinu? Manje kusura u dzepu!",
  "Stedljiv sam - jos uvijek nosim odjecu iz srednje.",
  "Akcija + kupon = financijski genije!",
  "Zasto ne jedem vani? Kuvam kao mama. Jeftino!",
  "Moja stednja: Cekam da sve bude na akciji.",
  "Stedim na hobijima - gledam kako drugi trose.",
  "Popust mi je kao droga - zelim vise!",
  "Zasto volim rasprodaje? Jer volim jeftino!",
  "Kupio sam TV 55 inca. Na rate do 2055.",
  "Stedljiv sam - dijelim Netflix sa 7 ljudi.",
  "Moj savjet za stednju: Nemoj imati djecu.",
  "Zasto ne kupujem novo? Jer rabljeno radi!",
  "Stedim na benzinu - hodam. Svuda.",
  "Popust je najbolji poklon. I sam sebi!",
  "Zasto pratim akcije? Jer sam profesionalac!",
  "Moja filozofija: Usteda danas, bogatstvo sutra!",
  "Stedim toliko da me banka zove 'gospodin Nula'.",
]

const config = useRuntimeConfig()

const fileInput = ref<HTMLInputElement | null>(null)
const showModal = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)
const result = ref<CameraSearchResult | null>(null)
const capturedImageUrl = ref<string | null>(null)
const currentJokeIndex = ref(0)
const jokeInterval = ref<ReturnType<typeof setInterval> | null>(null)

const currentJoke = computed(() => savingsJokes[currentJokeIndex.value])

function startJokeRotation() {
  // Pick a random starting joke
  currentJokeIndex.value = Math.floor(Math.random() * savingsJokes.length)

  // Rotate every 2.5 seconds
  jokeInterval.value = setInterval(() => {
    currentJokeIndex.value = Math.floor(Math.random() * savingsJokes.length)
  }, 2500)
}

function stopJokeRotation() {
  if (jokeInterval.value) {
    clearInterval(jokeInterval.value)
    jokeInterval.value = null
  }
}

function openCamera() {
  fileInput.value?.click()
}

function retakePhoto() {
  // Reset state and open camera again
  error.value = null
  result.value = null
  isLoading.value = false
  stopJokeRotation()
  fileInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  // Revoke old URL if exists
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
  }

  // Create preview URL for the captured image
  capturedImageUrl.value = URL.createObjectURL(file)

  // Reset state
  showModal.value = true
  isLoading.value = true
  error.value = null
  result.value = null

  // Start joke rotation
  startJokeRotation()

  try {
    // Convert to base64
    const base64 = await fileToBase64(file)

    // Get auth token
    const token = localStorage.getItem('auth_token')
    if (!token) {
      error.value = 'Morate biti prijavljeni da koristite ovu funkciju'
      isLoading.value = false
      stopJokeRotation()
      return
    }

    // Call API
    const apiBase = config.public.apiBase || 'http://localhost:5001'
    const response = await fetch(`${apiBase}/api/camera/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        image_base64: base64
      })
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || 'Greska pri pretrazi')
    }

    result.value = await response.json()
  } catch (err: any) {
    error.value = err.message || 'Doslo je do greske'
  } finally {
    isLoading.value = false
    stopJokeRotation()
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
  stopJokeRotation()
  // Revoke the object URL to free memory
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
    capturedImageUrl.value = null
  }
}

// Format product data for ProductCardMobile component (matches moji-proizvodi)
function formatProductForCard(product: any) {
  return {
    id: product.id,
    title: product.title,
    base_price: product.base_price,
    discount_price: product.discount_price,
    image_path: product.image_path || product.image_url,
    product_image_url: product.image_path || product.image_url,
    business: product.business || {
      id: null,
      name: 'Nepoznato'
    },
    has_discount: product.has_discount || (product.discount_price && product.discount_price < product.base_price),
    similarity_score: product.similarity_score || product._score
  }
}

// Clean up on unmount
onUnmounted(() => {
  stopJokeRotation()
  if (capturedImageUrl.value) {
    URL.revokeObjectURL(capturedImageUrl.value)
  }
})
</script>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
