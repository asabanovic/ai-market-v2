<template>
  <!-- Speed Dial FAB - Mobile only -->
  <ClientOnly>
    <div v-if="showButton" class="md:hidden">
      <!-- Backdrop overlay when expanded -->
      <Transition
        enter-active-class="transition-opacity duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isExpanded"
          class="fixed inset-0 bg-black/30 z-40"
          @click="closeMenu"
        />
      </Transition>

      <!-- FAB Container -->
      <div class="fixed right-4 bottom-20 z-50 flex flex-col items-end">
        <!-- Action buttons (shown when expanded) -->
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-4 scale-95"
          enter-to-class="opacity-100 translate-y-0 scale-100"
          leave-active-class="transition-all duration-150 ease-in"
          leave-from-class="opacity-100 translate-y-0 scale-100"
          leave-to-class="opacity-0 translate-y-4 scale-95"
        >
          <div v-if="isExpanded" class="flex flex-col gap-3 mb-4">
            <!-- Option 1: Traži slikom (Search by image) -->
            <button
              @click="handleSearchByImage"
              class="flex items-center gap-3 pl-1 pr-4 py-1 bg-white rounded-full shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
              style="animation-delay: 0ms"
            >
              <div class="w-12 h-12 flex items-center justify-center bg-purple-500 rounded-full">
                <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <span class="text-sm font-medium text-gray-800 whitespace-nowrap pr-1">Traži slikom</span>
            </button>

            <!-- Option 2: Slikaj račun (Upload receipt) -->
            <button
              @click="handleReceiptCapture"
              class="flex items-center gap-3 pl-1 pr-4 py-1 bg-white rounded-full shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
              style="animation-delay: 50ms"
            >
              <div class="w-12 h-12 flex items-center justify-center bg-blue-500 rounded-full">
                <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span class="text-sm font-medium text-gray-800 whitespace-nowrap pr-1">Slikaj račun</span>
            </button>

            <!-- Option 3: Dodaj artikal (Add product) -->
            <button
              @click="handleAddProduct"
              class="flex items-center gap-3 pl-1 pr-4 py-1 bg-white rounded-full shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
              style="animation-delay: 100ms"
            >
              <div class="w-12 h-12 flex items-center justify-center bg-green-500 rounded-full relative">
                <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <!-- Plus badge -->
                <div class="absolute -top-1 -right-1 w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-sm">
                  <svg class="w-3.5 h-3.5 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </div>
              </div>
              <span class="text-sm font-medium text-gray-800 whitespace-nowrap pr-1">Dodaj artikal</span>
            </button>
          </div>
        </Transition>

        <!-- Main FAB button -->
        <button
          @click="toggleMenu"
          class="w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 transform hover:scale-110"
          :class="isExpanded ? 'bg-gray-700 rotate-45' : 'bg-gradient-to-br from-purple-500 via-blue-500 to-green-500'"
        >
          <svg
            class="w-7 h-7 text-white transition-transform duration-300"
            :class="{ 'rotate-90': isExpanded }"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      <!-- Hidden file inputs for image search -->
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

      <!-- Hidden file input for receipt capture -->
      <input
        ref="receiptCameraInput"
        type="file"
        accept="image/*"
        capture="environment"
        class="hidden"
        @change="handleReceiptFileSelect"
      />
    </div>

    <!-- Image Search Sub-menu -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showImageOptions"
          class="fixed inset-0 bg-black/50 z-[100] flex items-end justify-center md:items-center"
          @click.self="showImageOptions = false"
        >
          <div class="bg-white rounded-t-2xl md:rounded-2xl w-full max-w-sm p-4 pb-8 md:pb-4 transform transition-transform">
            <div class="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-4 md:hidden" />
            <h3 class="text-lg font-semibold text-gray-900 text-center mb-4">Traži slikom</h3>
            <div class="grid grid-cols-2 gap-3">
              <button
                @click="openCamera"
                class="flex flex-col items-center gap-2 p-4 border-2 border-gray-200 rounded-xl hover:border-purple-400 hover:bg-purple-50 transition-colors"
              >
                <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <svg class="w-6 h-6 text-purple-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <span class="text-sm font-medium text-gray-700">Slikaj uživo</span>
              </button>
              <button
                @click="openGallery"
                class="flex flex-col items-center gap-2 p-4 border-2 border-gray-200 rounded-xl hover:border-purple-400 hover:bg-purple-50 transition-colors"
              >
                <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg class="w-6 h-6 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <span class="text-sm font-medium text-gray-700">Iz galerije</span>
              </button>
            </div>
            <button
              @click="showImageOptions = false"
              class="w-full mt-4 py-3 text-gray-600 font-medium hover:bg-gray-100 rounded-xl transition-colors"
            >
              Otkaži
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Image Search Results Modal -->
    <Teleport to="body">
      <div
        v-if="showSearchModal"
        class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
        @click.self="closeSearchModal"
      >
        <div class="bg-white rounded-xl max-w-[95vw] sm:max-w-2xl w-full max-h-[95vh] overflow-hidden shadow-2xl">
          <!-- Header -->
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="text-lg font-semibold text-gray-900">
              {{ isSearching ? 'Tražim...' : 'Rezultati pretrage' }}
            </h3>
            <button @click="closeSearchModal" class="p-1 text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="p-4 overflow-y-auto max-h-[calc(95vh-140px)]">
            <!-- Loading State -->
            <div v-if="isSearching" class="flex flex-col items-center py-8">
              <div class="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p class="text-gray-600 text-center px-4">{{ currentJoke }}</p>
            </div>

            <!-- Error State -->
            <div v-else-if="searchError" class="text-center py-8">
              <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-red-600">{{ searchError }}</p>
            </div>

            <!-- Results -->
            <div v-else-if="searchResult">
              <!-- Identified Product Info -->
              <div class="bg-purple-50 rounded-lg p-4 mb-4">
                <div class="flex items-start gap-3">
                  <svg class="w-6 h-6 text-purple-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p class="font-medium text-gray-900">
                      {{ searchResult.identified_product?.title || 'Proizvod prepoznat' }}
                    </p>
                    <p v-if="searchResult.identified_product?.brand" class="text-sm text-gray-600">
                      Brend: {{ searchResult.identified_product.brand }}
                    </p>
                    <p v-if="searchResult.interest_added" class="text-sm text-green-600 mt-1">
                      Dodano na listu interesa
                    </p>
                    <p v-else-if="searchResult.already_tracked" class="text-sm text-blue-600 mt-1">
                      Već pratite ovaj proizvod
                    </p>
                  </div>
                </div>
              </div>

              <!-- Products Found -->
              <div v-if="searchResult.products?.length > 0">
                <h4 class="text-sm font-medium text-gray-700 mb-3">
                  Pronađeno {{ searchResult.products.length }} proizvoda:
                </h4>
                <div class="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide py-2 gap-4 -mx-4 px-4">
                  <ProductCardMobile
                    v-for="product in searchResult.products"
                    :key="product.id"
                    :product="formatProductForCard(product)"
                  />
                </div>
                <p v-if="searchResult.products.length > 1" class="text-center text-xs text-gray-400 mt-2">
                  ← Prevuci za više →
                </p>
              </div>

              <!-- No Products Found -->
              <div v-else class="text-center py-4">
                <p class="text-gray-600">
                  Nismo pronašli ovaj proizvod u bazi. Dodali smo ga na vašu listu interesa i obavijestit ćemo vas kada bude dostupan na akciji.
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div v-if="searchResult && !isSearching" class="p-4 border-t">
            <button
              @click="closeSearchModal"
              class="w-full py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
            >
              Zatvori
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Receipt Upload Loading Modal -->
    <Teleport to="body">
      <div
        v-if="isUploadingReceipt"
        class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
      >
        <div class="bg-white rounded-2xl p-6 text-center max-w-sm w-full">
          <div class="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-gray-700 font-medium">Učitavam račun...</p>
          <p class="text-gray-500 text-sm mt-1">Ovo može potrajati nekoliko sekundi</p>
        </div>
      </div>
    </Teleport>

    <!-- Receipt Success Modal with Confetti -->
    <Teleport to="body">
      <div
        v-if="showReceiptSuccess"
        class="fixed inset-0 z-[9998] flex items-center justify-center p-4 bg-black/50"
      >
        <!-- Confetti canvas -->
        <canvas ref="confettiCanvas" class="fixed inset-0 pointer-events-none z-[10000]"></canvas>

        <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 text-center relative z-[9999]">
          <!-- Success icon -->
          <div class="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-10 h-10 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h3 class="text-xl font-bold text-gray-900 mb-2">Hvala ti!</h3>
          <p class="text-gray-600 mb-3">Tvoj račun je uspješno učitan.</p>

          <!-- Feature explanation -->
          <div class="bg-blue-50 rounded-xl p-4 mb-4 text-left">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p class="font-medium text-blue-900">Pratimo tvoje troškove!</p>
                <p class="text-sm text-blue-700 mt-1">
                  Automatski analiziramo račune i pomažemo ti da uštediš. Vidjećeš gdje možeš kupiti jeftinije!
                </p>
              </div>
            </div>
          </div>

          <button
            @click="goToReceipts"
            class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors"
          >
            Pogledaj moje račune
          </button>
        </div>
      </div>
    </Teleport>
  </ClientOnly>
</template>

<script setup lang="ts">
const { isAuthenticated, token } = useAuth()
const config = useRuntimeConfig()

const router = useRouter()

// State
const isExpanded = ref(false)
const showImageOptions = ref(false)
const showSearchModal = ref(false)
const isSearching = ref(false)
const searchError = ref<string | null>(null)
const searchResult = ref<any>(null)

// Receipt state
const isUploadingReceipt = ref(false)
const showReceiptSuccess = ref(false)
const confettiCanvas = ref<HTMLCanvasElement | null>(null)

// File inputs
const cameraInput = ref<HTMLInputElement | null>(null)
const galleryInput = ref<HTMLInputElement | null>(null)
const receiptCameraInput = ref<HTMLInputElement | null>(null)

// Always show on all pages
const showButton = computed(() => true)

// Toggle menu
function toggleMenu() {
  isExpanded.value = !isExpanded.value
}

function closeMenu() {
  isExpanded.value = false
}

// Handle search by image
function handleSearchByImage() {
  closeMenu()
  if (!isAuthenticated.value) {
    navigateTo('/prijava?redirect=' + encodeURIComponent(window.location.pathname))
    return
  }
  showImageOptions.value = true
}

// Handle add product
function handleAddProduct() {
  closeMenu()
  // Dispatch global event to open submission modal
  if (process.client) {
    window.dispatchEvent(new CustomEvent('open-submission-modal'))
  }
}

// Handle receipt capture
function handleReceiptCapture() {
  closeMenu()
  if (!isAuthenticated.value) {
    navigateTo('/prijava?redirect=' + encodeURIComponent(window.location.pathname))
    return
  }
  // Open camera directly
  receiptCameraInput.value?.click()
}

// Handle receipt file selection
async function handleReceiptFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  isUploadingReceipt.value = true

  try {
    // Compress image before upload
    const compressedFile = await compressImageToFile(file, 1200, 0.85)

    // Create form data
    const formData = new FormData()
    formData.append('image', compressedFile)

    // Upload receipt
    const apiBase = config.public.apiBase || 'http://localhost:5001'
    const response = await fetch(`${apiBase}/api/receipts/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token.value}`
      },
      body: formData
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || 'Greška pri učitavanju računa')
    }

    // Success - show confetti and popup
    isUploadingReceipt.value = false
    showReceiptSuccess.value = true

    // Trigger confetti
    await nextTick()
    startConfetti()

  } catch (err: any) {
    console.error('Receipt upload error:', err)
    isUploadingReceipt.value = false
    alert(err.message || 'Greška pri učitavanju računa. Pokušaj ponovo.')
  } finally {
    // Reset file input
    if (input) input.value = ''
  }
}

// Compress image and return as File
function compressImageToFile(file: File, maxDimension: number = 1200, quality: number = 0.85): Promise<File> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    img.onload = () => {
      let width = img.width
      let height = img.height

      if (width > height) {
        if (width > maxDimension) {
          height = Math.round((height * maxDimension) / width)
          width = maxDimension
        }
      } else {
        if (height > maxDimension) {
          width = Math.round((width * maxDimension) / height)
          height = maxDimension
        }
      }

      canvas.width = width
      canvas.height = height
      ctx?.drawImage(img, 0, 0, width, height)

      canvas.toBlob(
        (blob) => {
          if (blob) {
            const compressedFile = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), {
              type: 'image/jpeg',
              lastModified: Date.now()
            })
            resolve(compressedFile)
          } else {
            reject(new Error('Failed to compress image'))
          }
        },
        'image/jpeg',
        quality
      )
    }

    img.onerror = () => reject(new Error('Failed to load image'))

    const reader = new FileReader()
    reader.onload = (e) => { img.src = e.target?.result as string }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// Confetti animation
function startConfetti() {
  const canvas = confettiCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles: any[] = []
  const colors = ['#3B82F6', '#60A5FA', '#93C5FD', '#10B981', '#34D399', '#FBBF24', '#F59E0B', '#EC4899']

  // Create particles
  for (let i = 0; i < 200; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: -20 - Math.random() * 200,
      vx: (Math.random() - 0.5) * 8,
      vy: Math.random() * 3 + 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 12 + 6,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 15,
      wobble: Math.random() * Math.PI * 2,
      wobbleSpeed: 0.05 + Math.random() * 0.05
    })
  }

  let frame = 0
  const maxFrames = 180

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    particles.forEach(p => {
      p.wobble += p.wobbleSpeed
      p.x += p.vx + Math.sin(p.wobble) * 2
      p.y += p.vy
      p.vy += 0.08
      p.rotation += p.rotationSpeed

      const alpha = frame > maxFrames - 30 ? (maxFrames - frame) / 30 : 1

      ctx.save()
      ctx.globalAlpha = alpha
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rotation * Math.PI / 180)
      ctx.fillStyle = p.color

      if (Math.random() > 0.5) {
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6)
      } else {
        ctx.beginPath()
        ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.restore()
    })

    frame++
    if (frame < maxFrames) {
      requestAnimationFrame(animate)
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
  }

  animate()
}

// Navigate to receipts page
function goToReceipts() {
  showReceiptSuccess.value = false
  router.push('/racuni')
}

function openCamera() {
  showImageOptions.value = false
  cameraInput.value?.click()
}

function openGallery() {
  showImageOptions.value = false
  galleryInput.value?.click()
}

// Image search logic (from FloatingCameraButton)
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
  'Zovem mamu da pita komšinicu...',
  'Preračunavam cijene u burek jedinice...',
  'Provjeravam koliko bi ovo koštalo u Jugoslaviji...',
  'Pitam tatu, ali on kaže "pitaj mamu"...',
]

const jokeIndex = ref(0)
const jokeInterval = ref<NodeJS.Timeout | null>(null)
const currentJoke = computed(() => jokes[jokeIndex.value])

watch(isSearching, (loading) => {
  if (loading) {
    jokeIndex.value = Math.floor(Math.random() * jokes.length)
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

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  showSearchModal.value = true
  isSearching.value = true
  searchError.value = null
  searchResult.value = null

  try {
    const base64 = await compressImage(file)
    const apiBase = config.public.apiBase || 'http://localhost:5001'
    const response = await fetch(`${apiBase}/api/camera/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.value}`
      },
      body: JSON.stringify({ image_base64: base64 })
    })

    if (!response.ok) {
      if (response.status === 413) {
        throw new Error('Slika je prevelika. Molimo pokušajte sa manjom slikom.')
      }
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || 'Greška pri pretrazi')
    }

    searchResult.value = await response.json()
  } catch (err: any) {
    searchError.value = err.message || 'Došlo je do greške'
  } finally {
    isSearching.value = false
    if (input) input.value = ''
  }
}

function compressImage(file: File, maxDimension: number = 1200, quality: number = 0.8): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    img.onload = () => {
      let width = img.width
      let height = img.height

      if (width > height) {
        if (width > maxDimension) {
          height = Math.round((height * maxDimension) / width)
          width = maxDimension
        }
      } else {
        if (height > maxDimension) {
          width = Math.round((width * maxDimension) / height)
          height = maxDimension
        }
      }

      canvas.width = width
      canvas.height = height
      ctx?.drawImage(img, 0, 0, width, height)
      const dataUrl = canvas.toDataURL('image/jpeg', quality)
      const base64 = dataUrl.split(',')[1]
      resolve(base64)
    }

    img.onerror = () => reject(new Error('Failed to load image'))

    const reader = new FileReader()
    reader.onload = (e) => { img.src = e.target?.result as string }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function closeSearchModal() {
  showSearchModal.value = false
  searchResult.value = null
  searchError.value = null
}

function formatProductForCard(product: any) {
  let hasDiscount = product.has_discount
  if (hasDiscount === undefined) {
    hasDiscount = product.discount_price && product.discount_price < product.base_price
    if (hasDiscount && product.discount_starts) {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const startDate = new Date(product.discount_starts)
      startDate.setHours(0, 0, 0, 0)
      if (startDate > today) {
        hasDiscount = false
      }
    }
  }

  return {
    id: product.id,
    title: product.title,
    base_price: product.base_price,
    discount_price: product.discount_price,
    discount_starts: product.discount_starts,
    expires: product.expires,
    image_path: product.image_path || product.image_url,
    product_image_url: product.image_path || product.image_url,
    business: product.business || { id: null, name: 'Nepoznato' },
    has_discount: hasDiscount,
    similarity_score: product.similarity_score || product._score
  }
}

// Close menu when clicking outside
onMounted(() => {
  if (process.client) {
    document.addEventListener('click', handleOutsideClick)
  }
})

onUnmounted(() => {
  if (process.client) {
    document.removeEventListener('click', handleOutsideClick)
  }
  if (jokeInterval.value) {
    clearInterval(jokeInterval.value)
  }
})

function handleOutsideClick(e: MouseEvent) {
  // Don't close if clicking inside the FAB container
  const target = e.target as HTMLElement
  if (target.closest('.z-50')) return
  isExpanded.value = false
}
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
