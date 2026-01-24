<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="dismiss"
    >
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"></div>

      <!-- Modal -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div
          class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all animate-bounce-in"
          @click.stop
        >
          <!-- Close button -->
          <button
            @click="dismiss"
            class="absolute top-4 right-4 text-white/80 hover:text-white z-10"
          >
            <Icon name="mdi:close" class="w-6 h-6" />
          </button>

          <!-- Header with gradient and animation -->
          <div class="bg-gradient-to-r from-purple-600 to-blue-600 px-8 py-8 text-center relative overflow-hidden">
            <!-- Animated phone taking photo illustration -->
            <div class="relative w-36 h-32 mx-auto mb-4">
              <!-- Product/Price tag -->
              <div class="absolute left-0 top-1/2 -translate-y-1/2 animate-bounce-slow">
                <div class="bg-yellow-400 rounded-lg px-4 py-3 shadow-lg transform -rotate-6">
                  <div class="text-red-600 font-bold text-base line-through opacity-70">15.00 KM</div>
                  <div class="text-green-700 font-bold text-2xl">8.00 KM</div>
                </div>
              </div>

              <!-- Phone -->
              <div class="absolute right-0 top-1/2 -translate-y-1/2 animate-phone-capture">
                <div class="bg-gray-800 rounded-xl p-1 shadow-2xl w-16 h-24 flex flex-col">
                  <div class="bg-gray-900 rounded-lg flex-1 flex items-center justify-center relative overflow-hidden">
                    <!-- Camera lens -->
                    <div class="w-4 h-4 bg-gray-700 rounded-full border-2 border-gray-600"></div>
                    <!-- Flash effect -->
                    <div class="flash-effect absolute inset-0 bg-white rounded-lg"></div>
                  </div>
                  <!-- Home button -->
                  <div class="w-3 h-3 bg-gray-700 rounded-full mx-auto my-1"></div>
                </div>
              </div>

              <!-- Camera click sparkles -->
              <div class="absolute inset-0 pointer-events-none">
                <Icon name="mdi:star-four-points" class="w-4 h-4 text-yellow-300 absolute top-2 right-8 animate-sparkle-1" />
                <Icon name="mdi:star-four-points" class="w-3 h-3 text-white absolute top-6 right-4 animate-sparkle-2" />
                <Icon name="mdi:star-four-points" class="w-5 h-5 text-yellow-200 absolute top-0 right-12 animate-sparkle-3" />
              </div>
            </div>

            <h3 class="text-2xl font-bold text-white mb-2">
              Našli ste fenomenalnu ponudu?
            </h3>
            <p class="text-white/90">
              Podijelite je sa drugima na popust.ba!
            </p>
          </div>

          <!-- Content -->
          <div class="px-8 py-6">
            <p class="text-gray-600 text-center mb-6">
              Vidjeli ste lud popust u radnji? Slikajte proizvod i podijelite sa zajednicom!
            </p>

            <!-- Benefits -->
            <div class="space-y-3 mb-6">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Icon name="mdi:gift" class="w-5 h-5 text-green-600" />
                </div>
                <span class="text-sm text-gray-700">Zaradite kredite za svaku objavljenu ponudu</span>
              </div>
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Icon name="mdi:account-group" class="w-5 h-5 text-blue-600" />
                </div>
                <span class="text-sm text-gray-700">Pomozite zajednici da uštedi novac</span>
              </div>
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Icon name="mdi:star" class="w-5 h-5 text-purple-600" />
                </div>
                <span class="text-sm text-gray-700">Vaše ime će biti prikazano uz ponudu</span>
              </div>
            </div>

            <!-- CTA Buttons -->
            <div class="space-y-3">
              <button
                @click="goToSubmit"
                class="block w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-lg font-bold text-center hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                🚀 Prijavi ponudu
              </button>

              <button
                @click="dismiss"
                class="block w-full text-gray-500 py-2 px-6 text-sm hover:text-gray-700 transition-colors"
              >
                Možda kasnije
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  dismiss: []
  navigate: []
}>()

const { post } = useApi()

function dismiss() {
  trackAction('dismissed')
  emit('dismiss')
}

function goToSubmit() {
  trackAction('clicked')
  emit('dismiss')
  // Trigger the submission modal via global event
  if (process.client) {
    window.dispatchEvent(new Event('open-submission-modal'))
  }
}

async function trackAction(action: string) {
  try {
    await post('/api/user/track-event', {
      event: 'promo_submission_popup',
      data: { action },
      timestamp: new Date().toISOString()
    })
  } catch {
    // Silent fail
  }
}

// Close on Escape key
onMounted(() => {
  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && props.show) dismiss()
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

/* Phone capture animation */
@keyframes phone-capture {
  0%, 100% {
    transform: translateY(-50%) rotate(0deg);
  }
  10% {
    transform: translateY(-50%) rotate(-5deg);
  }
  20% {
    transform: translateY(-50%) rotate(0deg) scale(1.05);
  }
  30% {
    transform: translateY(-50%) rotate(0deg) scale(1);
  }
}

.animate-phone-capture {
  animation: phone-capture 2.5s ease-in-out infinite;
}

/* Flash effect */
@keyframes flash {
  0%, 15%, 100% {
    opacity: 0;
  }
  20%, 25% {
    opacity: 0.9;
  }
}

.flash-effect {
  animation: flash 2.5s ease-in-out infinite;
}

/* Price tag bounce */
@keyframes bounce-slow {
  0%, 100% {
    transform: translateY(-50%) rotate(-6deg);
  }
  50% {
    transform: translateY(-55%) rotate(-6deg);
  }
}

.animate-bounce-slow {
  animation: bounce-slow 2s ease-in-out infinite;
}

/* Sparkle animations */
@keyframes sparkle-1 {
  0%, 100% {
    opacity: 0;
    transform: scale(0);
  }
  20%, 30% {
    opacity: 1;
    transform: scale(1);
  }
  40% {
    opacity: 0;
    transform: scale(0);
  }
}

@keyframes sparkle-2 {
  0%, 100% {
    opacity: 0;
    transform: scale(0);
  }
  25%, 35% {
    opacity: 1;
    transform: scale(1);
  }
  45% {
    opacity: 0;
    transform: scale(0);
  }
}

@keyframes sparkle-3 {
  0%, 100% {
    opacity: 0;
    transform: scale(0);
  }
  22%, 32% {
    opacity: 1;
    transform: scale(1);
  }
  42% {
    opacity: 0;
    transform: scale(0);
  }
}

.animate-sparkle-1 {
  animation: sparkle-1 2.5s ease-in-out infinite;
}

.animate-sparkle-2 {
  animation: sparkle-2 2.5s ease-in-out infinite;
}

.animate-sparkle-3 {
  animation: sparkle-3 2.5s ease-in-out infinite;
}
</style>
