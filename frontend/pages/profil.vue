<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Moj profil</h1>
        <p class="text-gray-600">Uredite svoje lične podatke</p>
      </div>

      <!-- Quick Navigation -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <NuxtLink
          to="/profil/liste-istorija"
          class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow flex items-center gap-4"
        >
          <div class="bg-purple-100 p-3 rounded-lg">
            <Icon name="mdi:history" class="w-8 h-8 text-purple-600" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">Istorija Lista</h3>
            <p class="text-sm text-gray-600">Pregled vaših prethodnih shopping lista</p>
          </div>
        </NuxtLink>

        <NuxtLink
          to="/moje-liste"
          class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow flex items-center gap-4"
        >
          <div class="bg-green-100 p-3 rounded-lg">
            <Icon name="mdi:cart" class="w-8 h-8 text-green-600" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">Aktivna Lista</h3>
            <p class="text-sm text-gray-600">Pogledajte trenutnu shopping listu</p>
          </div>
        </NuxtLink>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-purple-600">
          <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Profile Form -->
      <div v-else class="bg-white rounded-lg shadow-md p-6">
        <!-- Success Message -->
        <div v-if="successMessage" class="mb-6 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          <p>{{ successMessage }}</p>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{{ errorMessage }}</p>
        </div>

        <form @submit.prevent="saveProfile" class="space-y-6">
          <!-- Email (read-only) -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Email adresa
            </label>
            <input
              id="email"
              v-model="profile.email"
              type="email"
              disabled
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
            />
            <p class="mt-1 text-xs text-gray-500">Email adresa se ne može mijenjati</p>
          </div>

          <!-- First Name -->
          <div>
            <label for="first_name" class="block text-sm font-medium text-gray-700 mb-1">
              Ime
            </label>
            <input
              id="first_name"
              v-model="profile.first_name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="Unesite vaše ime"
            />
          </div>

          <!-- Last Name -->
          <div>
            <label for="last_name" class="block text-sm font-medium text-gray-700 mb-1">
              Prezime
            </label>
            <input
              id="last_name"
              v-model="profile.last_name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="Unesite vaše prezime"
            />
          </div>

          <!-- Phone -->
          <div>
            <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">
              Broj telefona
            </label>
            <div class="relative">
              <input
                id="phone"
                v-model="profile.phone"
                type="tel"
                :class="[
                  'w-full px-3 py-2 border-2 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none',
                  profile.phone && !isPhoneValid ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-purple-500 focus:border-purple-500'
                ]"
                placeholder="+387 XX XXX XXX"
                @input="formatPhoneNumber"
                @blur="validatePhone"
                maxlength="20"
              />
              <div v-if="profile.phone && isPhoneValid" class="absolute right-3 top-1/2 -translate-y-1/2">
                <Icon name="mdi:check-circle" class="w-5 h-5 text-green-500" />
              </div>
            </div>
            <p class="mt-1 text-xs text-gray-500">Format: +387XXXXXXXXX (sa pozivnim brojem)</p>
          </div>

          <!-- City -->
          <div>
            <label for="city" class="block text-sm font-medium text-gray-700 mb-1">
              Grad
            </label>
            <select
              id="city"
              v-model="profile.city"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            >
              <option value="">Odaberite grad</option>
              <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
            </select>
          </div>

          <!-- Notification Preferences -->
          <div class="border border-gray-200 rounded-md p-4 bg-gray-50">
            <label class="flex items-start cursor-pointer">
              <input
                type="checkbox"
                :checked="profile.notification_preferences === 'favorites' || profile.notification_preferences === 'all'"
                @change="toggleNotifications"
                class="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">
                  Želim primati notifikacije o proizvodima koje pratim
                </p>
                <p class="text-xs text-gray-600 mt-1">
                  Primiću SMS/Viber notifikacije kada proizvodi koje sam dodao u favorite dobiju popust ili promijene cijenu
                </p>
              </div>
            </label>
          </div>

          <!-- Admin Badge (if admin) -->
          <div v-if="profile.is_admin" class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex items-center">
              <Icon name="mdi:shield-account" class="w-6 h-6 text-red-600 mr-2" />
              <div>
                <p class="text-sm font-semibold text-red-900">Administrator</p>
                <p class="text-xs text-red-700">Imate administratorski pristup platformi</p>
              </div>
            </div>
          </div>

          <!-- Save Button -->
          <div class="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              @click="loadProfile"
              :disabled="isSaving"
              class="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Odustani
            </button>
            <button
              type="submit"
              :disabled="isSaving || (profile.phone && !isPhoneValid)"
              class="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isSaving ? 'Čuvanje...' : 'Sačuvaj promjene' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth']
})

const { get, put } = useApi()
const { refreshUser } = useAuth()

const isLoading = ref(true)
const isSaving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const isPhoneValid = ref(true)

const profile = ref({
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  city: '',
  notification_preferences: 'none',
  is_admin: false
})

const cities = ref<string[]>([])

async function loadProfile() {
  isLoading.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const data = await get('/auth/user/profile')
    profile.value = {
      email: data.email || '',
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      phone: data.phone || '',
      city: data.city || '',
      notification_preferences: data.notification_preferences || 'none',
      is_admin: data.is_admin || false
    }

    // Validate phone if it exists
    if (profile.value.phone) {
      validatePhone()
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Greška pri učitavanju profila'
  } finally {
    isLoading.value = false
  }
}

async function loadCities() {
  try {
    const data = await get('/auth/cities')
    cities.value = data.cities || []
  } catch (error) {
    console.error('Error loading cities:', error)
  }
}

function formatPhoneNumber(event: any) {
  let value = event.target.value

  // Remove all non-digit characters except +
  value = value.replace(/[^\d+]/g, '')

  // Ensure it starts with +
  if (value && !value.startsWith('+')) {
    value = '+' + value
  }

  // Limit to reasonable phone number length
  if (value.length > 20) {
    value = value.substring(0, 20)
  }

  profile.value.phone = value
  validatePhone()
}

function validatePhone() {
  const value = profile.value.phone?.trim()

  if (!value) {
    isPhoneValid.value = true // Empty is valid
    return
  }

  // Basic international phone number validation
  const phoneRegex = /^\+\d{8,19}$/
  isPhoneValid.value = phoneRegex.test(value)
}

function toggleNotifications(event: any) {
  // Toggle between 'favorites' and 'none'
  profile.value.notification_preferences = event.target.checked ? 'favorites' : 'none'
}

async function saveProfile() {
  successMessage.value = ''
  errorMessage.value = ''

  // Validate phone if provided
  if (profile.value.phone) {
    validatePhone()
    if (!isPhoneValid.value) {
      errorMessage.value = 'Molimo unesite ispravan broj telefona u formatu +387XXXXXXXXX'
      return
    }
  }

  isSaving.value = true

  try {
    const response = await put('/auth/user/profile', {
      first_name: profile.value.first_name,
      last_name: profile.value.last_name,
      phone: profile.value.phone,
      city: profile.value.city,
      notification_preferences: profile.value.notification_preferences
    })

    if (response.success) {
      successMessage.value = response.message || 'Profil uspješno ažuriran!'
      // Refresh user data in auth store
      await refreshUser()

      // Scroll to top to show success message
      window.scrollTo({ top: 0, behavior: 'smooth' })

      // Clear success message after 5 seconds
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    } else {
      errorMessage.value = response.error || 'Greška pri čuvanju profila'
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Greška pri čuvanju profila'
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadCities()
})

useSeoMeta({
  title: 'Moj profil - AI Pijaca',
  description: 'Uredite svoje lične podatke',
})
</script>
