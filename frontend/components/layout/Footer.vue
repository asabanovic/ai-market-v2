<template>
  <footer class="bg-white border-t border-gray-200">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <div class="mb-6">
          <h3 class="text-lg font-medium text-gray-900 mb-3">Popust.ba</h3>
          <p class="text-sm text-gray-600 max-w-md mx-auto">
            Pronađite najbolje akcije i popuste u vašem gradu uz pomoć Popust asistenta.
          </p>
        </div>

        <div class="flex justify-center items-center space-x-6 mb-6">
          <NuxtLink to="/kako-radimo" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
            Kako radimo
          </NuxtLink>
          <NuxtLink to="/kontakt" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
            Kontakt
          </NuxtLink>
          <NuxtLink to="/proizvodi" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
            Proizvodi
          </NuxtLink>
        </div>

        <div class="pt-6">
          <p class="text-xs text-gray-500">&copy; {{ currentYear }} Popust.ba. Sva prava zadržana.</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>
