<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Fotografije proizvoda</h2>
        <p class="text-sm text-gray-600 mt-1">Slikajte proizvode koje želite pratiti - mi ćemo vas obavijestiti kada budu na akciji</p>
      </div>
    </div>

    <!-- Upload Area -->
    <div class="mb-6">
      <div
        class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors cursor-pointer"
        :class="{ 'border-purple-500 bg-purple-50': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="openFileDialog"
      >
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          multiple
          class="hidden"
          @change="handleFileSelect"
        />

        <!-- Camera/Upload buttons -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
          <!-- Camera button (mobile prominent) -->
          <button
            type="button"
            @click.stop="openCamera"
            class="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
          >
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>Slikaj proizvod</span>
          </button>

          <!-- Upload button -->
          <button
            type="button"
            @click.stop="openFileDialog"
            class="flex items-center gap-2 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:border-purple-500 hover:text-purple-600 transition-colors font-medium"
          >
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>Izaberi iz galerije</span>
          </button>
        </div>

        <p class="text-sm text-gray-500 mt-4">ili prevucite slike ovdje</p>
        <p class="text-xs text-gray-400 mt-1">Maksimalno {{ maxImages }} slika ({{ images.length }}/{{ maxImages }})</p>
      </div>

      <!-- Camera input for mobile -->
      <input
        ref="cameraInput"
        type="file"
        accept="image/*"
        capture="environment"
        class="hidden"
        @change="handleCameraCapture"
      />
    </div>

    <!-- Preview uploading images -->
    <div v-if="pendingUploads.length > 0" class="mb-6">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Učitavanje...</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        <div
          v-for="(upload, index) in pendingUploads"
          :key="'pending-' + index"
          class="relative aspect-square bg-gray-100 rounded-lg overflow-hidden"
        >
          <img
            :src="upload.preview"
            class="w-full h-full object-cover opacity-50"
            alt="Uploading..."
          />
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Uploaded images -->
    <div v-if="images.length > 0">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Vaše slike ({{ images.length }})</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        <div
          v-for="image in images"
          :key="image.id"
          class="relative aspect-square bg-gray-100 rounded-lg overflow-hidden group"
        >
          <img
            :src="image.thumbnail_url || image.image_url"
            class="w-full h-full object-cover"
            :alt="image.extracted_name || 'Product image'"
          />

          <!-- Status badge -->
          <div class="absolute top-2 left-2">
            <span
              v-if="image.status === 'pending'"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
            >
              Na čekanju
            </span>
            <span
              v-else-if="image.status === 'processing'"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              Obrađuje se
            </span>
            <span
              v-else-if="image.status === 'processed'"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
            >
              Praćeno
            </span>
          </div>

          <!-- Extracted name -->
          <div v-if="image.extracted_name" class="absolute bottom-0 left-0 right-0 bg-black/60 p-2">
            <p class="text-white text-xs truncate">{{ image.extracted_name }}</p>
          </div>

          <!-- Delete button -->
          <button
            @click="deleteImage(image.id)"
            class="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
            :disabled="deletingIds.includes(image.id)"
          >
            <svg v-if="!deletingIds.includes(image.id)" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <div v-else class="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading && pendingUploads.length === 0" class="text-center py-8">
      <svg class="mx-auto h-12 w-12 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">Nema slika</h3>
      <p class="mt-1 text-sm text-gray-500">Slikajte proizvode koje želite pratiti</p>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
      <p class="text-gray-600 mt-2">Učitavanje slika...</p>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
      <p class="text-sm text-red-700">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ProductImage {
  id: number
  image_url: string
  thumbnail_url: string | null
  status: string
  extracted_name: string | null
  extracted_price: number | null
  matched_product_id: number | null
  user_notes: string | null
  created_at: string
  processed_at: string | null
}

interface PendingUpload {
  file: File
  preview: string
}

const { get, del, upload: apiUpload } = useApi()
const { isNative, takePhoto } = useCamera()

const maxImages = 10
const fileInput = ref<HTMLInputElement | null>(null)
const cameraInput = ref<HTMLInputElement | null>(null)
const images = ref<ProductImage[]>([])
const pendingUploads = ref<PendingUpload[]>([])
const deletingIds = ref<number[]>([])
const loading = ref(true)
const isDragging = ref(false)
const errorMessage = ref('')

// Load images on mount
onMounted(async () => {
  await loadImages()
})

async function loadImages() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await get('/auth/user/product-images')
    images.value = response.images || []
  } catch (error: any) {
    console.error('Failed to load images:', error)
    errorMessage.value = error.message || 'Greška pri učitavanju slika'
  } finally {
    loading.value = false
  }
}

function openFileDialog() {
  fileInput.value?.click()
}

async function openCamera() {
  // Use native camera on mobile (with back camera), fallback to HTML input on web
  if (isNative) {
    try {
      const photo = await takePhoto()
      if (photo) {
        uploadFiles([photo.file])
      }
    } catch (error) {
      console.error('Camera error:', error)
      errorMessage.value = 'Greška pri otvaranju kamere'
    }
  } else {
    // Web fallback - use HTML input
    cameraInput.value?.click()
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    uploadFiles(Array.from(input.files))
  }
  // Reset input so same file can be selected again
  input.value = ''
}

function handleCameraCapture(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    uploadFiles([input.files[0]])
  }
  input.value = ''
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    uploadFiles(Array.from(files).filter(f => f.type.startsWith('image/')))
  }
}

async function uploadFiles(files: File[]) {
  // Check limit
  const availableSlots = maxImages - images.value.length - pendingUploads.value.length
  if (availableSlots <= 0) {
    errorMessage.value = `Maksimalno ${maxImages} slika. Obrišite neke da biste dodali nove.`
    return
  }

  const filesToUpload = files.slice(0, availableSlots)
  errorMessage.value = ''

  // Add to pending with previews
  for (const file of filesToUpload) {
    const preview = URL.createObjectURL(file)
    pendingUploads.value.push({ file, preview })
  }

  // Upload each file
  for (let i = 0; i < pendingUploads.value.length; i++) {
    const pendingItem = pendingUploads.value[i]

    try {
      const formData = new FormData()
      formData.append('image', pendingItem.file)

      const response = await apiUpload('/auth/user/product-images', formData)

      if (response.success && response.image) {
        images.value.unshift(response.image)
      }
    } catch (error: any) {
      console.error('Upload failed:', error)
      errorMessage.value = error.message || 'Greška pri uploadu slike'
    }

    // Remove from pending
    URL.revokeObjectURL(pendingItem.preview)
    pendingUploads.value = pendingUploads.value.filter(u => u !== pendingItem)
  }
}

async function deleteImage(imageId: number) {
  if (deletingIds.value.includes(imageId)) return

  deletingIds.value.push(imageId)
  errorMessage.value = ''

  try {
    await del(`/auth/user/product-images/${imageId}`)
    images.value = images.value.filter(img => img.id !== imageId)
  } catch (error: any) {
    console.error('Delete failed:', error)
    errorMessage.value = error.message || 'Greška pri brisanju slike'
  } finally {
    deletingIds.value = deletingIds.value.filter(id => id !== imageId)
  }
}
</script>
