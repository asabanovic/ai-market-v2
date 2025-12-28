<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
    <div class="max-w-md w-full">
      <!-- Loading State -->
      <div v-if="isVerifying" class="text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-6">
          <div class="w-8 h-8 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Verifikacija u toku...</h1>
        <p class="text-gray-600">Molimo pričekajte dok verificiramo Vašu email adresu.</p>
      </div>

      <!-- Success State -->
      <div v-else-if="success" class="text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-6">
          <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Email uspješno verificiran!</h1>
        <p class="text-gray-600 mb-6">Vaš račun je sada aktivan. Možete se prijaviti i koristiti sve funkcionalnosti.</p>
        <NuxtLink
          to="/prijava"
          class="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          Prijavite se
        </NuxtLink>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-6">
          <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Verifikacija nije uspjela</h1>
        <p class="text-gray-600 mb-6">{{ errorMessage }}</p>
        <div class="space-y-3">
          <NuxtLink
            to="/registracija"
            class="block w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors text-center"
          >
            Registrujte se ponovo
          </NuxtLink>
          <NuxtLink
            to="/prijava"
            class="block w-full px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors text-center"
          >
            Već imate račun? Prijavite se
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'default'
})

const route = useRoute()
const config = useRuntimeConfig()

const isVerifying = ref(true)
const success = ref(false)
const error = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  const token = route.params.token as string

  if (!token) {
    error.value = true
    errorMessage.value = 'Link za verifikaciju je nevažeći.'
    isVerifying.value = false
    return
  }

  try {
    // Call backend verification API
    const response = await $fetch(`${config.public.apiBase}/auth/verify-email/${token}`, {
      method: 'POST'
    })

    if (response.success) {
      success.value = true
    } else {
      error.value = true
      errorMessage.value = response.message || 'Verifikacija nije uspjela.'
    }
  } catch (e: any) {
    error.value = true
    if (e.data?.message) {
      errorMessage.value = e.data.message
    } else if (e.data?.error) {
      errorMessage.value = e.data.error
    } else {
      errorMessage.value = 'Link za verifikaciju je nevažeći ili je istekao.'
    }
  } finally {
    isVerifying.value = false
  }
})
</script>
