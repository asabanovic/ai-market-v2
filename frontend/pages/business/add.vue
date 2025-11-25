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

          <!-- Google Business Link -->
          <div>
            <label for="google_link" class="block text-sm font-medium text-gray-700 mb-1">
              Google Business link
            </label>
            <input
              id="google_link"
              v-model="form.google_link"
              type="url"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="https://g.page/..."
            />
            <p class="mt-1 text-xs text-gray-500">Link na vašu Google Business stranicu (opcionalno)</p>
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
const { get, post } = useApi()

const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const cities = ref<string[]>([])

const form = ref({
  name: '',
  city: '',
  contact_phone: '',
  google_link: ''
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
