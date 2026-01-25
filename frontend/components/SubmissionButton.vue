<template>
  <!-- Floating "Dodaj" button - visible to everyone on mobile, requires login on click -->
  <div v-if="showButton && !props.hideButton" class="fixed right-4 bottom-20 z-50 md:hidden">
    <button
      @click="openModal"
      class="flex items-center gap-2 pl-1 pr-4 py-1 bg-green-600 text-white rounded-full shadow-lg hover:bg-green-700 transition-all"
    >
      <div class="w-12 h-12 flex items-center justify-center bg-green-500 rounded-full relative text-white">
        <!-- Camera icon -->
        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
      <span class="text-sm font-medium whitespace-nowrap">Dodaj artikal</span>
    </button>
  </div>

  <!-- Submission Modal -->
  <Teleport to="body">
    <div
      v-if="showModal"
      class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50"
      @click.self="closeModal"
    >
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b">
          <h2 class="text-lg font-semibold text-gray-900">
            {{ step === 1 ? 'Dodaj proizvod' : step === 2 ? 'Odaberi radnju' : 'Fotografiraj artikal' }}
          </h2>
          <button @click="closeModal" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>

        <!-- Step indicator -->
        <div class="flex items-center justify-center gap-2 py-3 bg-gray-50">
          <div
            v-for="s in 3"
            :key="s"
            class="w-2.5 h-2.5 rounded-full transition-colors"
            :class="s <= step ? 'bg-green-600' : 'bg-gray-300'"
          />
        </div>

        <!-- Content -->
        <div class="p-4">
          <!-- Step 1: Instructions -->
          <div v-if="step === 1" class="space-y-4">
            <div class="text-center mb-4">
              <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-green-600" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
                </svg>
              </div>
              <p class="text-gray-600">Pomozi zajednici i zaradi kredite!</p>
            </div>

            <div class="bg-gray-50 rounded-xl p-4 space-y-3">
              <h3 class="font-medium text-gray-900">Kako funkcioniše:</h3>
              <ul class="space-y-2 text-sm text-gray-600">
                <li class="flex items-start gap-2">
                  <span class="text-green-600 font-bold">1.</span>
                  <span>Odaberi radnju gdje si</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-green-600 font-bold">2.</span>
                  <span>Fotografiraj proizvod izbliza i etiketu na kojoj stoji cijena</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-green-600 font-bold">3.</span>
                  <span>Pošalji fotografiju</span>
                </li>
              </ul>
            </div>

            <div class="bg-green-50 border border-green-200 rounded-xl p-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <span class="text-white font-bold">+10</span>
                </div>
                <div>
                  <p class="font-medium text-green-800">Zaradi 10 kredita!</p>
                  <p class="text-sm text-green-600">Za svaki prihvaćeni prijedlog</p>
                </div>
              </div>
            </div>

            <button
              @click="step = 2"
              class="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-xl transition-colors"
            >
              Nastavi
            </button>
          </div>

          <!-- Step 2: Select Store -->
          <div v-else-if="step === 2" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Odaberi radnju:</label>
              <div class="relative">
                <input
                  v-model="storeSearch"
                  type="text"
                  placeholder="Pretraži radnje..."
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 text-gray-900"
                />
              </div>
            </div>

            <div class="max-h-60 overflow-y-auto space-y-2">
              <button
                v-for="store in filteredStores"
                :key="store.id"
                @click="selectedStore = store"
                class="w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-colors"
                :class="selectedStore?.id === store.id ? 'border-green-600 bg-green-50' : 'border-gray-200 hover:border-gray-300'"
              >
                <img
                  :src="store.logo_path || '/placeholder-store.png'"
                  :alt="store.name"
                  class="w-10 h-10 rounded-lg object-contain bg-white"
                />
                <span class="font-medium text-gray-900">{{ store.name }}</span>
                <svg
                  v-if="selectedStore?.id === store.id"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 text-green-600 ml-auto"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>

            <div class="flex gap-3 pt-2">
              <button
                @click="step = 1"
                class="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
              >
                Nazad
              </button>
              <button
                @click="step = 3"
                :disabled="!selectedStore"
                class="flex-1 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors"
              >
                Nastavi
              </button>
            </div>
          </div>

          <!-- Step 3: Upload Photo -->
          <div v-else-if="step === 3" class="space-y-4">
            <div class="text-center text-sm text-gray-600 mb-2">
              Radnja: <strong class="text-gray-900">{{ selectedStore?.name }}</strong>
            </div>

            <!-- Image preview or upload buttons -->
            <div v-if="previewUrl" class="relative border-2 border-green-500 rounded-xl p-4">
              <img :src="previewUrl" class="max-h-48 mx-auto rounded-lg" alt="Preview" />
              <button
                @click.stop="clearImage"
                class="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
              <!-- Processing indicator -->
              <div v-if="isProcessingImage" class="absolute inset-0 bg-white/80 flex items-center justify-center rounded-xl">
                <div class="flex items-center gap-2 text-green-600">
                  <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="text-sm font-medium">Obrađujem...</span>
                </div>
              </div>
            </div>

            <!-- Two buttons for camera and gallery -->
            <div v-else class="grid grid-cols-2 gap-3">
              <!-- Camera button -->
              <button
                @click="openCamera"
                class="flex flex-col items-center gap-2 p-6 border-2 border-dashed border-gray-300 rounded-xl hover:border-green-400 hover:bg-green-50 transition-colors"
              >
                <div class="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-green-600" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
                  </svg>
                </div>
                <span class="text-sm font-medium text-gray-700">Fotografiraj</span>
              </button>

              <!-- Gallery button -->
              <button
                @click="openGallery"
                class="flex flex-col items-center gap-2 p-6 border-2 border-dashed border-gray-300 rounded-xl hover:border-green-400 hover:bg-green-50 transition-colors"
              >
                <div class="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
                  </svg>
                </div>
                <span class="text-sm font-medium text-gray-700">Iz galerije</span>
              </button>
            </div>

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

            <!-- Tips -->
            <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm">
              <p class="font-medium text-amber-800 mb-1">Savjet:</p>
              <p class="text-amber-700">Fotografiši proizvod izbliza zajedno sa etiketom na kojoj se vidi cijena.</p>
            </div>

            <div class="flex gap-3 pt-2">
              <button
                @click="step = 2"
                class="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
              >
                Nazad
              </button>
              <button
                @click="submitPhoto"
                :disabled="!selectedFile || isSubmitting"
                class="flex-1 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <svg v-if="isSubmitting" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ isSubmitting ? 'Šaljem...' : 'Pošalji' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Success Modal with Confetti -->
  <Teleport to="body">
    <div
      v-if="showSuccess"
      class="fixed inset-0 z-[9998] flex items-center justify-center p-4 bg-black/50"
    >
      <!-- Confetti canvas - highest z-index to be on top of everything -->
      <canvas ref="confettiCanvas" class="fixed inset-0 pointer-events-none z-[10000]"></canvas>

      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 text-center relative z-[9999]">
        <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-green-600" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Hvala!</h3>
        <p class="text-gray-600 mb-2">Tvoj prijedlog je primljen i trenutno se pregledava.</p>
        <p class="text-gray-500 text-sm mb-4">Obavijestit cemo te putem email-a kada bude odobren. Za svaki prihvaceni prijedlog dobijas <span class="font-semibold text-green-600">+10 kredita</span>!</p>
        <button
          @click="showSuccess = false"
          class="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-xl transition-colors"
        >
          Super!
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

// Props
const props = defineProps({
  hideButton: {
    type: Boolean,
    default: false
  }
})

const { isAuthenticated, token, user } = useAuth()
const config = useRuntimeConfig()

const route = useRoute()

// Show button for everyone on mobile, but hide on /racuni page
const showButton = computed(() => {
  return route.path !== '/racuni'
})

// Modal state
const showModal = ref(false)

// Listen for global event to open modal (from promo popup, etc.)
onMounted(() => {
  if (process.client) {
    window.addEventListener('open-submission-modal', openModal)
  }
})

onUnmounted(() => {
  if (process.client) {
    window.removeEventListener('open-submission-modal', openModal)
  }
})
const showSuccess = ref(false)
const step = ref(1)

// Store selection
const stores = ref([])
const storeSearch = ref('')
const selectedStore = ref(null)

// File upload
const cameraInput = ref(null)
const galleryInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const isProcessingImage = ref(false)
const isSubmitting = ref(false)

// Confetti
const confettiCanvas = ref(null)

const filteredStores = computed(() => {
  if (!storeSearch.value) return stores.value
  const search = storeSearch.value.toLowerCase()
  return stores.value.filter(s => s.name.toLowerCase().includes(search))
})

const openModal = async () => {
  // Require login to submit
  if (!isAuthenticated.value) {
    navigateTo('/prijava?redirect=' + encodeURIComponent(useRoute().fullPath))
    return
  }

  showModal.value = true
  step.value = 1
  selectedStore.value = null
  clearImage()

  // Fetch stores if not loaded
  if (stores.value.length === 0) {
    await fetchStores()
  }
}

const closeModal = () => {
  showModal.value = false
  step.value = 1
  selectedStore.value = null
  clearImage()
}

const fetchStores = async () => {
  try {
    const response = await fetch(`${config.public.apiBase}/api/businesses`)
    const data = await response.json()
    stores.value = data.businesses || data || []
  } catch (err) {
    console.error('Failed to fetch stores:', err)
  }
}

const openCamera = () => {
  cameraInput.value?.click()
}

const openGallery = () => {
  galleryInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    processFile(file)
  }
}

const processFile = async (file) => {
  if (file.size > 10 * 1024 * 1024) {
    alert('Datoteka je prevelika. Maksimalno 10MB.')
    return
  }

  isProcessingImage.value = true

  try {
    // Resize image client-side before upload (600px max for fast upload)
    const resizedFile = await resizeImage(file, 600, 0.85)
    selectedFile.value = resizedFile
    previewUrl.value = URL.createObjectURL(resizedFile)
  } catch (err) {
    console.error('Error processing image:', err)
    // Fallback to original file if resize fails
    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
  } finally {
    isProcessingImage.value = false
  }
}

// Resize image to max width while maintaining aspect ratio
const resizeImage = (file, maxWidth, quality) => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const tempUrl = URL.createObjectURL(file)

    img.onload = () => {
      // Revoke temp URL after image loads
      URL.revokeObjectURL(tempUrl)

      // Calculate new dimensions
      let width = img.width
      let height = img.height

      if (width > maxWidth) {
        height = Math.round((height * maxWidth) / width)
        width = maxWidth
      }

      // Create canvas and draw resized image
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)

      // Convert to blob
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const resizedFile = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), {
              type: 'image/jpeg',
              lastModified: Date.now()
            })
            resolve(resizedFile)
          } else {
            reject(new Error('Failed to create blob'))
          }
        },
        'image/jpeg',
        quality
      )
    }
    img.onerror = () => {
      URL.revokeObjectURL(tempUrl)
      reject(new Error('Failed to load image'))
    }
    img.src = tempUrl
  })
}

const clearImage = () => {
  selectedFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
  if (cameraInput.value) {
    cameraInput.value.value = ''
  }
  if (galleryInput.value) {
    galleryInput.value.value = ''
  }
}

const submitPhoto = async () => {
  if (!selectedFile.value || !selectedStore.value || isSubmitting.value) return

  isSubmitting.value = true

  try {
    const formData = new FormData()
    formData.append('image', selectedFile.value)
    formData.append('business_id', selectedStore.value.id.toString())

    const response = await fetch(`${config.public.apiBase}/api/submissions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token.value}`
      },
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Greška pri slanju')
    }

    // Success!
    showModal.value = false
    showSuccess.value = true

    // Trigger confetti
    await nextTick()
    startConfetti()

    // Auto-close after 5 seconds
    setTimeout(() => {
      showSuccess.value = false
    }, 5000)

  } catch (err) {
    console.error('Submission error:', err)
    alert(err.message || 'Greška pri slanju. Pokušaj ponovo.')
  } finally {
    isSubmitting.value = false
  }
}

// Fullscreen confetti animation - 3 seconds, bigger particles
const startConfetti = () => {
  const canvas = confettiCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles = []
  const colors = ['#10B981', '#34D399', '#6EE7B7', '#FBBF24', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#3B82F6']

  // Create many particles across the entire screen width
  for (let i = 0; i < 300; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: -20 - Math.random() * 200, // Start above screen
      vx: (Math.random() - 0.5) * 8,
      vy: Math.random() * 3 + 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 14 + 8, // Bigger: 8-22px
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 15,
      wobble: Math.random() * Math.PI * 2,
      wobbleSpeed: 0.05 + Math.random() * 0.05
    })
  }

  let frame = 0
  const maxFrames = 180 // 3 seconds at 60fps

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    particles.forEach(p => {
      // Wobble effect for floating feel
      p.wobble += p.wobbleSpeed
      p.x += p.vx + Math.sin(p.wobble) * 2
      p.y += p.vy
      p.vy += 0.08 // Slower gravity for longer float
      p.rotation += p.rotationSpeed

      // Fade out towards the end
      const alpha = frame > maxFrames - 30 ? (maxFrames - frame) / 30 : 1

      ctx.save()
      ctx.globalAlpha = alpha
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rotation * Math.PI / 180)
      ctx.fillStyle = p.color
      // Mix of rectangles and circles for variety
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
</script>
