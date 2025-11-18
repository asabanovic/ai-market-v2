<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Registrujte se besplatno
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Ili
          <NuxtLink to="/prijava" class="font-medium text-purple-600 hover:text-purple-500">
            se prijavite ako već imate račun
          </NuxtLink>
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <!-- Error message display -->
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-4">
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

        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="first_name" class="block text-sm font-medium text-gray-700">Ime</label>
              <input
                id="first_name"
                v-model="formData.first_name"
                type="text"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm"
                placeholder="Vaše ime"
              >
            </div>

            <div>
              <label for="last_name" class="block text-sm font-medium text-gray-700">Prezime</label>
              <input
                id="last_name"
                v-model="formData.last_name"
                type="text"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm"
                placeholder="Vaše prezime"
              >
            </div>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">Email adresa</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm"
              placeholder="email@example.com"
            >
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Lozinka</label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm"
              placeholder="Unesite lozinku"
            >
          </div>

          <div>
            <label for="preferences" class="block text-sm font-medium text-gray-700">Vaše preferencije</label>
            <textarea
              id="preferences"
              v-model="formData.preferences"
              rows="3"
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 focus:z-10 sm:text-sm"
              placeholder="Npr: Iz Tuzle, zanimaju me auto dijelovi i meso na akciji"
            ></textarea>
            <p class="mt-1 text-xs text-gray-500">Opišite iz kojeg ste grada i što vas zanima - ovo će nam pomoći da vam damo bolje preporuke</p>
          </div>
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoading ? 'Učitavanje...' : 'Registruj se' }}
          </button>
        </div>

        <div v-if="config.public.googleOAuthEnabled" class="text-center">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-300"></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-gray-50 text-gray-500">ili</span>
            </div>
          </div>

          <div class="mt-4">
            <a
              :href="googleOAuthUrl"
              class="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg class="w-5 h-5 text-red-500 mr-2" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Nastavi sa Google
            </a>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
// Define page metadata with middleware
definePageMeta({
  middleware: ['auth-redirect']
})

const { post } = useApi()
const { login, isAuthenticated } = useAuth()
const config = useRuntimeConfig()

const formData = ref({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  preferences: ''
})

const errorMessage = ref('')
const isLoading = ref(false)

const googleOAuthUrl = computed(() => {
  return `${config.public.apiBase || 'http://localhost:5001'}/auth/google`
})

async function handleRegister() {
  errorMessage.value = ''

  // Validate fields
  if (!formData.value.first_name.trim() || !formData.value.last_name.trim() || !formData.value.email.trim() || !formData.value.password.trim()) {
    errorMessage.value = 'Sva polja su obavezna'
    return
  }

  isLoading.value = true

  try {
    const response = await post('/auth/register', formData.value)

    // Check if registration was successful (either success: true or has token)
    if (response.success || response.token) {
      // Auto-login after successful registration
      await login(formData.value.email, formData.value.password)
      // Redirect to home page
      navigateTo('/')
    } else {
      errorMessage.value = response.error || response.message || 'Došlo je do greške prilikom registracije'
      console.error('Registration failed:', response)
    }
  } catch (error: any) {
    console.error('Registration error:', error)
    errorMessage.value = error.message || 'Došlo je do greške prilikom registracije'
  } finally {
    isLoading.value = false
  }
}
</script>
