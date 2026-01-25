<template>
  <Teleport to="body">
    <div
      v-if="isVisible"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
      @click.self="close"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in">
        <!-- Header with gradient -->
        <div class="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-5 text-white">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="bg-white/20 rounded-full p-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h2 class="text-xl font-bold">Krediti iskorišteni</h2>
                <p class="text-purple-100 text-sm">Ova sedmica: {{ creditsRemaining }} preostalo</p>
              </div>
            </div>
            <button
              @click="close"
              class="text-white/80 hover:text-white p-1 rounded-full hover:bg-white/10 transition"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="px-6 py-5">
          <p class="text-gray-700 mb-5">
            Za pregled više proizvoda potrebno je <span class="font-semibold text-purple-600">{{ creditsNeeded }} kredita</span>.
            Zaradite kredite nazad dok pomažete drugima!
          </p>

          <!-- Earn credits options -->
          <div class="space-y-3 mb-5">
            <div class="flex items-center gap-3 p-3 bg-green-50 rounded-xl border border-green-100">
              <div class="bg-green-500 text-white rounded-full p-2 flex-shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-gray-900">Ostavi komentar</span>
                  <span class="text-green-600 font-bold">+5 kredita</span>
                </div>
                <p class="text-sm text-gray-600">Podijeli iskustvo o proizvodu</p>
              </div>
            </div>

            <div class="flex items-center gap-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
              <div class="bg-blue-500 text-white rounded-full p-2 flex-shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                </svg>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-gray-900">Glasaj za proizvod</span>
                  <span class="text-blue-600 font-bold">+2 kredita</span>
                </div>
                <p class="text-sm text-gray-600">Preporuči ili ne preporuči</p>
              </div>
            </div>
          </div>

          <!-- Motivational message -->
          <div class="bg-amber-50 border border-amber-100 rounded-xl p-4 mb-5">
            <div class="flex gap-3">
              <div class="text-2xl">💡</div>
              <p class="text-sm text-amber-800">
                <span class="font-medium">Vaš glas je važan!</span> Jednostavan komentar ili preporuka može pomoći nekome da donese bolju odluku pri kupovini.
              </p>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-3">
            <button
              @click="close"
              class="flex-1 px-4 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition"
            >
              Ostani na stranici 1
            </button>
            <button
              @click="goToProducts"
              class="flex-1 px-4 py-3 bg-purple-600 text-white font-medium rounded-xl hover:bg-purple-700 transition flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
              Zaradi kredite
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  isVisible: boolean
  creditsNeeded: number
  creditsRemaining: number
}>()

const emit = defineEmits<{
  close: []
  goToProducts: []
}>()

function close() {
  emit('close')
}

function goToProducts() {
  emit('goToProducts')
  emit('close')
}
</script>

<style scoped>
.animate-scale-in {
  animation: scaleIn 0.2s ease-out;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
