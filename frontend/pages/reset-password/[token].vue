<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-2xl">
      <!-- Loading -->
      <div v-if="loading" class="text-center">
        <svg class="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-gray-600">Učitavanje...</p>
      </div>

      <!-- Success -->
      <div v-else-if="success" class="text-center">
        <svg class="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Lozinka uspješno resetirana!</h2>
        <p class="text-gray-600 mb-6">Sada se možete prijaviti sa novom lozinkom.</p>
        <NuxtLink
          to="/prijava"
          class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700"
        >
          Prijavi se
        </NuxtLink>
      </div>

      <!-- Form -->
      <template v-else>
        <div>
          <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Postavite novu lozinku
          </h2>
          <p class="mt-2 text-center text-sm text-gray-600">
            Unesite novu lozinku za vaš račun.
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-4">
            <p class="text-sm text-red-700">{{ errorMessage }}</p>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Nova lozinka</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              minlength="6"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
              placeholder="Najmanje 6 karaktera"
            />
          </div>

          <div>
            <label for="confirm_password" class="block text-sm font-medium text-gray-700">Potvrdi lozinku</label>
            <input
              id="confirm_password"
              v-model="confirmPassword"
              type="password"
              required
              :class="[
                'mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm',
                passwordMismatch ? 'border-red-300 bg-red-50' : 'border-gray-300'
              ]"
              placeholder="Ponovite lozinku"
            />
            <p v-if="passwordMismatch" class="mt-1 text-sm text-red-600">
              Lozinke se ne poklapaju
            </p>
          </div>

          <button
            type="submit"
            :disabled="isLoading || passwordMismatch || password.length < 6"
            class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoading ? 'Spremam...' : 'Postavi novu lozinku' }}
          </button>
        </form>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const config = useRuntimeConfig()

const token = computed(() => route.params.token as string)
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const success = ref(false)

const passwordMismatch = computed(() => {
  return confirmPassword.value.length > 0 && password.value !== confirmPassword.value
})

async function handleSubmit() {
  if (passwordMismatch.value) return
  if (password.value.length < 6) {
    errorMessage.value = 'Lozinka mora imati najmanje 6 karaktera'
    return
  }

  errorMessage.value = ''
  isLoading.value = true

  try {
    const response = await $fetch(`${config.public.apiBase}/reset-password/${token.value}`, {
      method: 'POST',
      body: {
        password: password.value,
        confirm_password: confirmPassword.value
      }
    })

    if ((response as any).success) {
      success.value = true
    }
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greška prilikom resetiranja lozinke. Link je možda istekao.'
  } finally {
    isLoading.value = false
  }
}

useSeoMeta({
  title: 'Resetiranje lozinke - Popust.ba',
  description: 'Postavite novu lozinku za vaš Popust.ba račun'
})
</script>
