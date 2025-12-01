<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="text-center">
      <Icon name="mdi:store" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
      <h2 class="text-xl font-semibold text-gray-900 mb-2">Stranica u izradi</h2>
      <p class="text-gray-600 mb-4">Ova stranica će uskoro biti dostupna.</p>
      <NuxtLink to="/" class="text-purple-600 hover:text-purple-800">
        ← Nazad na početnu
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
// Redirect to home page
definePageMeta({
  middleware: () => {
    return navigateTo('/')
  }
})
</script>
