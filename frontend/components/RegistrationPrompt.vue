<template>
  <div class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[100] p-4">
    <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8 relative">
      <!-- Close button -->
      <button
        @click="$emit('close')"
        class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <Icon name="mdi:close" class="w-6 h-6" />
      </button>

      <!-- Icon -->
      <div class="text-center mb-6">
        <div class="w-20 h-20 bg-gradient-to-br from-purple-500 to-purple-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <Icon name="mdi:tag-multiple" class="w-10 h-10 text-white" />
        </div>
        <h2 class="text-3xl font-bold text-gray-900 mb-2">Otkrijte stotine popusta!</h2>
        <p class="text-gray-600 text-lg">
          Registrujte se za <span class="font-bold text-purple-600">BESPLATNO</span> u samo 30 sekundi
        </p>
      </div>

      <!-- Benefits -->
      <div class="space-y-3 mb-8">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <Icon name="mdi:check-bold" class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">{{ productCount }}+ proizvoda sa popustom</h3>
            <p class="text-sm text-gray-600">Svakodnevno ažurirane akcije iz svih supermarketa</p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <Icon name="mdi:check-bold" class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Popust asistent za kupovinu</h3>
            <p class="text-sm text-gray-600">Brzo pronađite najjeftinije proizvode za vašu listu</p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <Icon name="mdi:check-bold" class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Uštedite do 40%</h3>
            <p class="text-sm text-gray-600">Uporedite cijene i izaberite najbolje ponude</p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <Icon name="mdi:check-bold" class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Obavještenja o akcijama</h3>
            <p class="text-sm text-gray-600">Budite prvi koji saznaju za nove popuste</p>
          </div>
        </div>
      </div>

      <!-- CTA Buttons -->
      <div class="space-y-3">
        <NuxtLink
          to="/registracija"
          class="block w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white text-center font-bold py-4 rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          Registrujte se BESPLATNO
        </NuxtLink>
        <NuxtLink
          to="/prijava"
          class="block w-full bg-gray-100 text-gray-700 text-center font-medium py-3 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Već imate nalog? Prijavite se
        </NuxtLink>
      </div>

      <!-- Trust badge -->
      <p class="text-center text-sm text-gray-500 mt-6">
        <Icon name="mdi:shield-check" class="w-4 h-4 inline mr-1" />
        100% besplatno. Bez kreditne kartice.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  productCount: number
}>()

defineEmits(['close'])
</script>
