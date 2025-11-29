<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
    <div class="text-center">
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
        <h2 class="text-lg font-semibold text-red-700 mb-2">Greška pri prijavi</h2>
        <p class="text-red-600">{{ error }}</p>
        <NuxtLink to="/prijava" class="mt-4 inline-block text-purple-600 hover:text-purple-700">
          Pokušaj ponovo
        </NuxtLink>
      </div>
      <div v-else class="flex flex-col items-center gap-4">
        <div class="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-gray-600">Prijavljivanje...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const route = useRoute()
const router = useRouter()
const { user } = useAuth()

const error = ref('')

onMounted(async () => {
  const token = route.query.token as string

  if (!token) {
    error.value = 'Token nije pronađen'
    return
  }

  try {
    // Store the token
    if (process.client) {
      localStorage.setItem('token', token)
    }

    // Fetch user data with the token
    const { get } = useApi()
    const userData = await get('/auth/verify')

    if (userData && userData.user) {
      user.value = userData.user

      // Redirect to home page
      await router.push('/')
    } else {
      error.value = 'Greška pri dohvatanju korisničkih podataka'
    }
  } catch (e: any) {
    console.error('Auth callback error:', e)
    error.value = e.message || 'Greška pri prijavi'
    // Clear invalid token
    if (process.client) {
      localStorage.removeItem('token')
    }
  }
})
</script>
