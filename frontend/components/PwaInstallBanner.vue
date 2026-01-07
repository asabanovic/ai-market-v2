<template>
  <Teleport to="body">
    <!-- Install Banner -->
    <Transition name="slide-up">
      <div
        v-if="showBanner"
        class="fixed bottom-0 left-0 right-0 z-[9999] p-4 safe-area-inset-bottom"
      >
        <div class="max-w-lg mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <!-- iOS Instructions -->
          <div v-if="pwa.state.isIOS" class="p-4">
            <div class="flex items-start gap-3">
              <div class="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900 flex items-center justify-center flex-shrink-0">
                <img src="/apple-touch-icon.png" alt="Popust.ba" class="w-10 h-10 rounded-lg" />
              </div>
              <div class="flex-1">
                <h3 class="font-semibold text-gray-900 dark:text-white">Instalirajte Popust.ba</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Dodajte aplikaciju na svoj ekran za brzi pristup popustima
                </p>
              </div>
              <button
                @click="dismiss"
                class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="mt-4 space-y-2">
              <div v-for="(step, index) in iosInstructions.steps" :key="index" class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <span class="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 flex items-center justify-center text-xs font-bold">
                  {{ index + 1 }}
                </span>
                <span>{{ step }}</span>
              </div>
            </div>

            <div class="mt-4 flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              <span class="text-sm">Dodirnite ikonu dijeljenja</span>
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </div>
          </div>

          <!-- Standard Install Banner -->
          <div v-else class="p-4">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900 flex items-center justify-center flex-shrink-0">
                <img src="/android-chrome-192x192.png" alt="Popust.ba" class="w-10 h-10 rounded-lg" />
              </div>
              <div class="flex-1">
                <h3 class="font-semibold text-gray-900 dark:text-white">Instalirajte Popust.ba</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  Brzi pristup akcijama bez otvaranja browsera
                </p>
              </div>
            </div>

            <div class="mt-4 flex gap-2">
              <button
                @click="dismiss"
                class="flex-1 px-4 py-2.5 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Ne sad
              </button>
              <button
                @click="install"
                class="flex-1 px-4 py-2.5 text-white bg-primary-600 rounded-lg font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Instaliraj
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const pwa = usePwaInstall()
const { isAuthenticated } = useAuth()
const showBanner = ref(false)

const iosInstructions = computed(() => pwa.getIOSInstructions())

// Show banner after delay if conditions are met (only for logged in users)
onMounted(() => {
  setTimeout(() => {
    if (isAuthenticated.value && pwa.shouldShowPrompt()) {
      showBanner.value = true
    }
  }, 3000) // Show after 3 seconds
})

function dismiss() {
  showBanner.value = false
  pwa.dismissPrompt()
}

async function install() {
  const success = await pwa.promptInstall()
  if (success) {
    showBanner.value = false
  }
}
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

.safe-area-inset-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}
</style>
