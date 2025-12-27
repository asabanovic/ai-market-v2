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
        <!-- Gallery upload button with label -->
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

        <!-- Camera button with label -->
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
          <span class="text-sm font-medium text-gray-800 whitespace-nowrap">Slikaj artikal</span>
        </button>

        <!-- Tracking hint -->
        <div class="bg-purple-600 text-white text-xs px-3 py-2 rounded-lg shadow-lg max-w-[180px]">
          <span class="font-medium">Prati artikal</span>
          <p class="opacity-90 mt-0.5">Dodaj proizvod na listu za praćenje cijena</p>
        </div>
      </div>
    </transition>

    <!-- Main button -->
    <button
      @click.stop="toggleExpanded"
      class="flex items-center justify-center w-14 h-14 bg-purple-600 text-white rounded-full shadow-lg hover:bg-purple-700 transition-all"
      :class="{ 'rotate-45': isExpanded }"
    >
      <svg v-if="!isExpanded" class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <svg v-else class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Hidden inputs -->
    <input
      ref="cameraInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden"
      @change="handleCapture"
    />
    <input
      ref="galleryInput"
      type="file"
      accept="image/*"
      multiple
      class="hidden"
      @change="handleGallerySelect"
    />
  </div>

  <!-- Upload preview modal -->
  <Teleport to="body">
    <transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="previewImages.length > 0" class="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-4">
        <div class="bg-white rounded-lg max-w-md w-full max-h-[80vh] overflow-hidden">
          <div class="p-4 border-b">
            <h3 class="text-lg font-semibold text-gray-900">Potvrdi upload</h3>
            <p class="text-sm text-gray-600">{{ previewImages.length }} slika za upload</p>
          </div>

          <!-- Image previews -->
          <div class="p-4 overflow-y-auto max-h-[50vh]">
            <div class="grid grid-cols-2 gap-3">
              <div
                v-for="(preview, index) in previewImages"
                :key="index"
                class="relative aspect-square bg-gray-100 rounded-lg overflow-hidden"
              >
                <img :src="preview.url" class="w-full h-full object-cover" alt="Preview" />
                <button
                  @click="removePreview(index)"
                  class="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full"
                >
                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="p-4 border-t flex gap-3">
            <button
              @click="cancelUpload"
              class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              :disabled="isUploading"
            >
              Odustani
            </button>
            <button
              @click="confirmUpload"
              class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              :disabled="isUploading"
            >
              <span v-if="isUploading" class="flex items-center justify-center gap-2">
                <div class="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                Učitava se...
              </span>
              <span v-else>Potvrdi ({{ previewImages.length }})</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
interface PreviewImage {
  file: File
  url: string
}

const { upload: apiUpload } = useApi()
const { isAuthenticated } = useAuth()

const isExpanded = ref(false)
const cameraInput = ref<HTMLInputElement | null>(null)
const galleryInput = ref<HTMLInputElement | null>(null)
const previewImages = ref<PreviewImage[]>([])
const isUploading = ref(false)

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}

function openCamera() {
  if (!isAuthenticated.value) {
    // Redirect to login
    navigateTo('/prijava?redirect=/profil')
    return
  }
  cameraInput.value?.click()
  isExpanded.value = false
}

function openGallery() {
  if (!isAuthenticated.value) {
    navigateTo('/prijava?redirect=/profil')
    return
  }
  galleryInput.value?.click()
  isExpanded.value = false
}

function handleCapture(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    addPreview(input.files[0])
  }
  input.value = ''
}

function handleGallerySelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    Array.from(input.files).forEach(file => addPreview(file))
  }
  input.value = ''
}

function addPreview(file: File) {
  if (previewImages.value.length >= 10) {
    alert('Maksimalno 10 slika odjednom')
    return
  }
  const url = URL.createObjectURL(file)
  previewImages.value.push({ file, url })
}

function removePreview(index: number) {
  URL.revokeObjectURL(previewImages.value[index].url)
  previewImages.value.splice(index, 1)
}

function cancelUpload() {
  previewImages.value.forEach(p => URL.revokeObjectURL(p.url))
  previewImages.value = []
}

async function confirmUpload() {
  if (previewImages.value.length === 0) return

  isUploading.value = true

  try {
    for (const preview of previewImages.value) {
      const formData = new FormData()
      formData.append('image', preview.file)

      await apiUpload('/auth/user/product-images', formData)
    }

    // Success - clear and redirect to profile
    cancelUpload()
    navigateTo('/profil')
  } catch (error: any) {
    console.error('Upload failed:', error)
    alert(error.message || 'Greška pri uploadu')
  } finally {
    isUploading.value = false
  }
}

// Close expanded when clicking outside
onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  // Clean up URLs
  previewImages.value.forEach(p => URL.revokeObjectURL(p.url))
})

function handleOutsideClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (isExpanded.value && !target.closest('.fixed.left-4')) {
    isExpanded.value = false
  }
}
</script>
