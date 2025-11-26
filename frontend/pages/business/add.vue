<template>
  <div class="bg-gray-50 py-8 min-h-screen">
    <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="mb-8">
        <NuxtLink to="/business" class="text-indigo-600 hover:text-indigo-800 text-sm font-medium mb-4 inline-block">
          ← Nazad na listu
        </NuxtLink>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Dodaj novu radnju</h1>
        <p class="text-gray-600">Unesite podatke o vašoj radnji</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <!-- Success Message -->
        <div v-if="successMessage" class="mb-6 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          <p>{{ successMessage }}</p>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{{ errorMessage }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Business Name -->
          <div>
            <label for="name" class="block text-sm font-medium text-gray-700 mb-1">
              Naziv radnje *
            </label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Npr. Moja Radnja"
            />
          </div>

          <!-- City -->
          <div>
            <label for="city" class="block text-sm font-medium text-gray-700 mb-1">
              Grad *
            </label>
            <select
              id="city"
              v-model="form.city"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Odaberite grad</option>
              <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
            </select>
          </div>

          <!-- Contact Phone -->
          <div>
            <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">
              Kontakt telefon
            </label>
            <input
              id="phone"
              v-model="form.contact_phone"
              type="tel"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="+387 XX XXX XXX"
            />
          </div>

          <!-- Google Maps Link -->
          <div>
            <label for="google_link" class="block text-sm font-medium text-gray-700 mb-1">
              Google Maps link
            </label>
            <input
              id="google_link"
              v-model="form.google_link"
              type="url"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="https://www.google.com/maps/search/..."
            />
            <p class="mt-1 text-xs text-gray-500">
              Link na Google Maps sa svim lokacijama radnje (opcionalno)
            </p>

            <!-- Map Preview -->
            <div v-if="mapEmbedUrl" class="mt-3">
              <p class="text-xs text-gray-500 mb-2">Pregled mape:</p>
              <div class="relative w-full h-48 rounded-lg overflow-hidden border border-gray-200">
                <iframe
                  :src="mapEmbedUrl"
                  width="100%"
                  height="100%"
                  style="border:0;"
                  allowfullscreen=""
                  loading="lazy"
                  referrerpolicy="no-referrer-when-downgrade"
                ></iframe>
              </div>
            </div>
          </div>

          <!-- Logo Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Logo radnje
            </label>
            <div class="flex items-center gap-4">
              <!-- Logo Preview -->
              <div class="w-20 h-20 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 overflow-hidden">
                <img
                  v-if="logoPreview"
                  :src="logoPreview"
                  alt="Logo preview"
                  class="w-full h-full object-contain"
                />
                <Icon v-else name="mdi:store" class="w-10 h-10 text-gray-400" />
              </div>

              <!-- Upload Button -->
              <div class="flex-1">
                <label
                  for="logo"
                  class="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <Icon name="mdi:upload" class="w-5 h-5" />
                  {{ logoFile ? 'Promijeni logo' : 'Odaberi logo' }}
                </label>
                <input
                  id="logo"
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                  class="hidden"
                  @change="handleLogoChange"
                />
                <p class="mt-1 text-xs text-gray-500">PNG, JPG, GIF ili WebP. Max 5MB.</p>
                <p v-if="logoFile" class="mt-1 text-xs text-green-600">
                  {{ logoFile.name }} ({{ formatFileSize(logoFile.size) }})
                </p>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <NuxtLink
              to="/business"
              class="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Odustani
            </NuxtLink>
            <button
              type="submit"
              :disabled="isSubmitting"
              class="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isSubmitting ? 'Dodaje se...' : 'Dodaj radnju' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'admin'
})

const router = useRouter()
const { get, post, upload } = useApi()

const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const cities = ref<string[]>([])
const logoFile = ref<File | null>(null)
const logoPreview = ref<string | null>(null)

const form = ref({
  name: '',
  city: '',
  contact_phone: '',
  google_link: ''
})

function handleLogoChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (file) {
    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      errorMessage.value = 'Logo ne smije biti veći od 5MB'
      return
    }

    logoFile.value = file

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      logoPreview.value = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Convert Google Maps URL to embeddable URL
const mapEmbedUrl = computed(() => {
  const url = form.value.google_link.trim()
  if (!url) return null

  try {
    // Handle various Google Maps URL formats
    if (url.includes('google.com/maps')) {
      // Extract search query or place from URL
      const urlObj = new URL(url)

      // Format: /maps/search/query/@lat,lng,zoom
      const searchMatch = url.match(/\/maps\/search\/([^/@]+)/)
      if (searchMatch) {
        const query = decodeURIComponent(searchMatch[1].replace(/\+/g, ' '))
        return `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(query)}`
      }

      // Format: /maps/place/name/@lat,lng
      const placeMatch = url.match(/\/maps\/place\/([^/@]+)/)
      if (placeMatch) {
        const place = decodeURIComponent(placeMatch[1].replace(/\+/g, ' '))
        return `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(place)}`
      }

      // Format with coordinates: @lat,lng,zoom
      const coordMatch = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+)z/)
      if (coordMatch) {
        const [, lat, lng, zoom] = coordMatch
        // Try to extract query from path
        const pathQuery = url.match(/\/maps\/[^/]+\/([^/@]+)/)
        if (pathQuery) {
          const query = decodeURIComponent(pathQuery[1].replace(/\+/g, ' '))
          return `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(query)}&center=${lat},${lng}&zoom=${zoom}`
        }
        return `https://www.google.com/maps/embed/v1/view?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&center=${lat},${lng}&zoom=${zoom}`
      }
    }

    // Handle g.page short URLs - just show as link
    if (url.includes('g.page') || url.includes('goo.gl')) {
      return null // Can't embed short URLs directly
    }

    return null
  } catch (e) {
    return null
  }
})

async function loadCities() {
  try {
    const data = await get('/auth/cities')
    cities.value = data.cities || []
  } catch (error) {
    console.error('Error loading cities:', error)
    // Fallback cities
    cities.value = ['Sarajevo', 'Tuzla', 'Zenica', 'Mostar', 'Banja Luka', 'Bijeljina', 'Brčko']
  }
}

async function handleSubmit() {
  successMessage.value = ''
  errorMessage.value = ''

  if (!form.value.name.trim()) {
    errorMessage.value = 'Naziv radnje je obavezan'
    return
  }

  if (!form.value.city) {
    errorMessage.value = 'Grad je obavezan'
    return
  }

  isSubmitting.value = true

  try {
    const response = await post('/api/businesses', {
      name: form.value.name.trim(),
      city: form.value.city,
      contact_phone: form.value.contact_phone.trim() || null,
      google_link: form.value.google_link.trim() || null
    })

    if (response.success) {
      const businessId = response.business.id

      // Upload logo if selected
      if (logoFile.value && businessId) {
        try {
          const formData = new FormData()
          formData.append('logo', logoFile.value)
          await upload(`/api/businesses/${businessId}/logo`, formData)
        } catch (logoError) {
          console.error('Error uploading logo:', logoError)
          // Business was created, but logo upload failed - continue anyway
        }
      }

      successMessage.value = 'Radnja uspješno dodana!'

      // Redirect to business list after short delay
      setTimeout(() => {
        router.push('/business')
      }, 1500)
    } else {
      errorMessage.value = response.error || 'Greška prilikom dodavanja radnje'
    }
  } catch (error: any) {
    console.error('Error creating business:', error)
    errorMessage.value = error.message || 'Greška prilikom dodavanja radnje'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  loadCities()
})

useSeoMeta({
  title: 'Dodaj radnju - Popust.ba',
  description: 'Dodajte novu radnju na Popust.ba',
})
</script>
