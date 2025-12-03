<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-100 via-white to-purple-50 flex items-center justify-center px-4">
    <div class="max-w-2xl mx-auto text-center">
      <!-- Logo -->
      <NuxtLink to="/" class="inline-block mb-8">
        <img
          src="/logo.svg"
          alt="Popust.ba"
          class="h-16 mx-auto"
        />
      </NuxtLink>

      <!-- Animated 404 -->
      <div class="mb-8 relative">
        <h1 class="text-9xl md:text-[12rem] font-extrabold text-purple-200 select-none">
          {{ error?.statusCode || 404 }}
        </h1>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div class="text-6xl animate-bounce">🛒</div>
        </div>
      </div>

      <!-- Message -->
      <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
        Ups! Stranica nije pronađena
      </h2>
      <p class="text-lg text-gray-600 mb-8">
        Izgleda da je ova stranica otišla na sniženje i nije se vratila! 😄
      </p>

      <!-- Funny messages -->
      <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
        <p class="text-gray-700 italic mb-4">
          {{ funnyMessage }}
        </p>
        <button
          @click="getNewMessage"
          class="text-purple-600 hover:text-purple-700 text-sm font-medium"
        >
          Pokaži drugu poruku →
        </button>
      </div>

      <!-- Actions -->
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <NuxtLink
          to="/"
          class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Nazad na početnu
        </NuxtLink>
        <NuxtLink
          to="/proizvodi"
          class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Pretraži proizvode
        </NuxtLink>
      </div>

      <!-- Footer message -->
      <p class="mt-12 text-sm text-gray-500">
        Ako mislite da ovdje treba da bude nešto,
        <NuxtLink to="/kontakt" class="text-purple-600 hover:underline">
          kontaktirajte nas
        </NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  error: {
    statusCode: number
    message: string
  }
}>()

const funnyMessages = [
  'Možda je ova stranica na akciji, ali u drugoj pijaci! 🏪',
  'Stranica je otišla da provjeri cijene kod konkurencije! 💸',
  'Ova stranica je vjerovatno u redu na kasi... 🛒',
  'Ups! Ova stranica je istekla kao jogurt! 🥛',
  'Stranica nije pronađena - možda je rasprodana? 🤷',
  'Izgleda da smo ostali bez stoka ove stranice! 📦',
  'Ova stranica je otišla na godišnji odmor! 🏖️',
  'Stranica je ukradena - ali pronašli smo najbolju cijenu! 😄'
]

const funnyMessage = ref(funnyMessages[Math.floor(Math.random() * funnyMessages.length)])

function getNewMessage() {
  const currentMessage = funnyMessage.value
  let newMessage = currentMessage

  while (newMessage === currentMessage) {
    newMessage = funnyMessages[Math.floor(Math.random() * funnyMessages.length)]
  }

  funnyMessage.value = newMessage
}

useSeoMeta({
  title: '404 - Stranica nije pronađena - Popust.ba',
  description: 'Stranica koju tražite ne postoji ili je promijenjena.'
})
</script>
