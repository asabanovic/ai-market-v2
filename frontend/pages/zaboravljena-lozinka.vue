<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-2xl">
      <!-- Header -->
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Zaboravili ste lozinku?
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Unesite email adresu i poslat ćemo vam link za resetiranje lozinke.
        </p>
      </div>

      <!-- Success Message -->
      <div v-if="success" class="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="font-semibold text-green-800 mb-2">Email poslan!</h3>
        <p class="text-green-700 text-sm">
          Ako je email registrovan, poslat je link za resetiranje lozinke. Provjerite inbox (i spam folder).
        </p>
        <NuxtLink
          to="/prijava"
          class="mt-4 inline-block text-purple-600 hover:text-purple-500 font-medium"
        >
          ← Nazad na prijavu
        </NuxtLink>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSubmit" class="space-y-6">
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-sm text-red-700">{{ errorMessage }}</p>
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">Email adresa</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
            placeholder="email@example.com"
          />
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isLoading ? 'Šaljem...' : 'Pošalji link za resetiranje' }}
        </button>

        <div class="text-center">
          <NuxtLink to="/prijava" class="text-sm text-purple-600 hover:text-purple-500">
            ← Nazad na prijavu
          </NuxtLink>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()

const email = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const success = ref(false)

async function handleSubmit() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const response = await $fetch(`${config.public.apiBase}/forgot-password`, {
      method: 'POST',
      body: { email: email.value }
    })

    if ((response as any).success) {
      success.value = true
    }
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greška prilikom slanja emaila. Pokušajte ponovo.'
  } finally {
    isLoading.value = false
  }
}

useSeoMeta({
  title: 'Zaboravljena lozinka - Popust.ba',
  description: 'Resetirajte vašu lozinku za Popust.ba'
})
</script>
