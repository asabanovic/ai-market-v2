<template>
  <Teleport to="body">
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="closeModal"
    >
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"></div>

      <!-- Modal -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div
          class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 transform transition-all animate-bounce-in"
          @click.stop
        >
          <!-- Close button -->
          <button
            @click="closeModal"
            class="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <Icon name="mdi:close" class="w-6 h-6" />
          </button>

          <!-- Logo -->
          <div class="flex justify-center mb-4">
            <img src="/logo.svg" alt="Popust.ba" class="h-12 w-auto" />
          </div>

          <!-- Content -->
          <h3 class="text-2xl font-bold text-gray-900 text-center mb-3">
            Čekajte! Ne gubite popuste! 🎁
          </h3>

          <p class="text-gray-600 text-center mb-6">
            Svaki dan pratimo stotine proizvoda na popustu u trgovinama širom BiH!
          </p>

          <!-- Benefits -->
          <div class="bg-purple-50 rounded-lg p-4 mb-6">
            <p class="font-semibold text-purple-900 mb-3 text-center">
              Registrujte se za 10 sekundi i dobijate:
            </p>
            <ul class="space-y-2 text-sm text-purple-700">
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>40 BESPLATNIH pretraga SEDMIČNO</span>
              </li>
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>Pratimo cijene vaših omiljenih proizvoda</span>
              </li>
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>SMS obavještenja kada su proizvodi na popustu</span>
              </li>
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>Liste za kupovinu koje ne gubite</span>
              </li>
            </ul>
          </div>

          <!-- CTA Buttons -->
          <div class="space-y-3">
            <NuxtLink
              to="/registracija"
              class="block w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-lg font-bold text-center hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              🚀 Registruj se BESPLATNO
            </NuxtLink>

            <NuxtLink
              to="/prijava"
              class="block w-full bg-white border-2 border-purple-600 text-purple-600 py-3 px-6 rounded-lg font-semibold text-center hover:bg-purple-50 transition-all"
            >
              Ili se prijavi
            </NuxtLink>
          </div>

          <p class="text-xs text-center text-gray-500 mt-4">
            Bez kreditne kartice. Bez obaveza. Uvijek besplatno.
          </p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">

const emit = defineEmits<{
  close: []
}>()

const showModal = ref(true)

function closeModal() {
  showModal.value = false
  emit('close')

  // Store that user has seen exit intent
  localStorage.setItem('exit_intent_shown', Date.now().toString())
}

// Close on Escape key
onMounted(() => {
  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape') closeModal()
  }
  window.addEventListener('keydown', handleEsc)
  onUnmounted(() => window.removeEventListener('keydown', handleEsc))
})
</script>

<style scoped>
@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-bounce-in {
  animation: bounce-in 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
</style>
