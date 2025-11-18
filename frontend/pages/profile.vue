<template>
  <div class="bg-gray-50 py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Moj profil</h1>
        <p class="text-gray-600">Upravljajte vašim nalogom i preferencijama</p>
      </div>

      <!-- Success Message -->
      <div v-if="showSuccess" class="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-green-700">Profil je uspješno ažuriran</p>
          </div>
        </div>
      </div>

      <!-- Profile Edit Form -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-gray-900">Osnovne informacije</h2>
          <button
            v-if="!isEditMode"
            @click="isEditMode = true"
            type="button"
            class="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700"
          >
            Uredi profil
          </button>
        </div>

        <!-- View Mode -->
        <div v-if="!isEditMode">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Ime</label>
              <p class="text-gray-900">{{ user?.first_name || 'Nije uneseno' }}</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Prezime</label>
              <p class="text-gray-900">{{ user?.last_name || 'Nije uneseno' }}</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <p class="text-gray-900">{{ user?.email || 'Nije uneseno' }}</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Grad</label>
              <p class="text-gray-900">{{ user?.city || 'Nije uneseno' }}</p>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else>
          <form @submit.prevent="handleSubmit">
            <!-- Error Message -->
            <div v-if="showError" class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <div class="flex">
                <div class="flex-shrink-0">
                  <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-red-700">{{ errorMessage }}</p>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="first_name" class="block text-sm font-medium text-gray-700 mb-1">Ime *</label>
                <input
                  type="text"
                  id="first_name"
                  v-model="formData.first_name"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label for="last_name" class="block text-sm font-medium text-gray-700 mb-1">Prezime</label>
                <input
                  type="text"
                  id="last_name"
                  v-model="formData.last_name"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p class="text-gray-900 py-2">{{ user?.email || 'Nije uneseno' }}</p>
                <p class="text-xs text-gray-500">Email se ne može mijenjati</p>
              </div>

              <div>
                <label for="city" class="block text-sm font-medium text-gray-700 mb-1">Grad</label>
                <input
                  type="text"
                  id="city"
                  v-model="formData.city"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            <div class="mt-6 flex space-x-4">
              <button
                type="submit"
                :disabled="isSubmitting"
                class="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {{ isSubmitting ? 'Čuva se...' : 'Sačuvaj promjene' }}
              </button>
              <button
                type="button"
                @click="cancelEdit"
                class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400"
              >
                Otkaži
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Package Info -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Vaš paket</h2>
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-medium text-gray-900">{{ packageInfo?.name || 'Free' }}</h3>
            <p class="text-gray-600">
              {{ packageInfo?.daily_limit || 10 }} pretaga dnevno
            </p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-600">Danas ste koristili:</p>
            <p class="text-2xl font-bold text-indigo-600">
              {{ searchCounts?.used || 0 }}/{{ searchCounts?.daily_limit || 10 }}
            </p>
          </div>
        </div>

        <div
          v-if="searchCounts && searchCounts.remaining === 0"
          class="mt-4 p-3 bg-yellow-100 text-yellow-800 rounded-md"
        >
          <p class="text-sm">
            Iskoristili ste sve dnevne pretrage. Nadogradite paket ili se vratite sutra za nove pretrage.
          </p>
        </div>
      </div>

      <!-- Recent Searches -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Nedavne pretrage</h2>
        <div v-if="recentSearches && recentSearches.length > 0" class="space-y-4">
          <div
            v-for="search in recentSearches"
            :key="search.id"
            class="border-b border-gray-200 pb-4"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <p class="text-gray-900 font-medium">{{ search.query }}</p>
                <p class="text-sm text-gray-500">{{ formatDate(search.created_at) }}</p>
              </div>
              <div v-if="search.result_count !== undefined" class="text-sm text-gray-600">
                {{ search.result_count }} rezultata
              </div>
            </div>
          </div>
        </div>
        <p v-else class="text-gray-500">Nemate još uvek pretaga</p>
      </div>

      <!-- Action Buttons -->
      <div class="mt-8 flex space-x-4">
        <NuxtLink
          to="/"
          class="bg-indigo-600 text-white px-6 py-3 rounded-md font-medium hover:bg-indigo-700 transition duration-200"
        >
          Nazad na pretraživanje
        </NuxtLink>
        <button
          @click="handleLogout"
          class="bg-gray-300 text-gray-700 px-6 py-3 rounded-md font-medium hover:bg-gray-400 transition duration-200"
        >
          Odjava
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { user, logout } = useAuth()
const { get, post } = useApi()

const isEditMode = ref(false)
const isSubmitting = ref(false)
const showSuccess = ref(false)
const showError = ref(false)
const errorMessage = ref('')

const formData = ref({
  first_name: '',
  last_name: '',
  city: ''
})

const packageInfo = ref<any>(null)
const searchCounts = ref<any>(null)
const recentSearches = ref<any[]>([])

onMounted(async () => {
  await loadProfileData()
})

async function loadProfileData() {
  try {
    const data = await get('/api/profile')
    packageInfo.value = data.package
    searchCounts.value = data.search_counts
    recentSearches.value = data.recent_searches || []

    // Set form data
    formData.value = {
      first_name: user.value?.first_name || '',
      last_name: user.value?.last_name || '',
      city: user.value?.city || ''
    }
  } catch (error) {
    console.error('Error loading profile data:', error)
  }
}

async function handleSubmit() {
  isSubmitting.value = true
  showError.value = false
  showSuccess.value = false

  try {
    const response = await post('/api/profile', formData.value)

    if (response.success) {
      showSuccess.value = true
      isEditMode.value = false

      // Update user data
      if (user.value) {
        user.value.first_name = formData.value.first_name
        user.value.last_name = formData.value.last_name
        user.value.city = formData.value.city
      }

      // Scroll to top to show success message
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      errorMessage.value = response.error || 'Došlo je do greške prilikom ažuriranja profila'
      showError.value = true
    }
  } catch (error: any) {
    console.error('Error updating profile:', error)
    errorMessage.value = error.message || 'Došlo je do greške prilikom ažuriranja profila'
    showError.value = true
  } finally {
    isSubmitting.value = false
  }
}

function cancelEdit() {
  isEditMode.value = false
  showError.value = false

  // Reset form data
  formData.value = {
    first_name: user.value?.first_name || '',
    last_name: user.value?.last_name || '',
    city: user.value?.city || ''
  }
}

async function handleLogout() {
  await logout()
  navigateTo('/')
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

useSeoMeta({
  title: 'Moj profil - AI Pijaca',
  description: 'Upravljajte vašim nalogom i preferencijama na AI Pijaca platformi',
})
</script>
