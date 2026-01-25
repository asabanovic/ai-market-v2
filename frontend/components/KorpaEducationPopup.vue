<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isVisible"
        class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
        @click.self="close"
      >
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
          <!-- Header with icon -->
          <div class="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-5 text-white">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-xl font-bold">Uporedite cijene u svim marketima</h2>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="px-6 py-5">
            <p class="text-gray-700 text-base leading-relaxed">
              Pronašli ste proizvod? Dodajte ga u korpu zajedno sa ostalim stvarima sa vašeg spiska.
              Kada završite, pokazat ćemo vam <span class="font-semibold text-purple-700">u kojem marketu možete sve kupiti najpovoljnije</span>.
            </p>

            <!-- Visual guide -->
            <div class="mt-5 bg-purple-50 rounded-xl p-4">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</div>
                <div class="text-sm text-gray-700">Pretražite proizvode koje trebate</div>
              </div>
              <div class="flex items-start gap-3 mt-3">
                <div class="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
                <div class="text-sm text-gray-700">Dodajte ih u korpu klikom na dugme <span class="inline-flex items-center gap-1 bg-green-600 text-white px-2 py-0.5 rounded text-xs font-medium"><svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4v16m8-8H4"/></svg> Korpa</span></div>
              </div>
              <div class="flex items-start gap-3 mt-3">
                <div class="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
                <div class="text-sm text-gray-700">Otvorite korpu i vidite najbolju ukupnu cijenu po marketu</div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-100">
            <button
              @click="close"
              class="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
            >
              Razumijem
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  isVisible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function close() {
  // Mark as seen in localStorage
  if (process.client) {
    localStorage.setItem('korpa_education_seen', 'true')
  }
  emit('close')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
