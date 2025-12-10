<template>
  <Teleport to="body">
    <Transition name="bounce">
      <button
        v-if="shouldShow"
        @click="handleClick"
        class="fixed bottom-20 right-4 md:bottom-6 md:right-6 z-50 group"
        aria-label="Postavite profil interesa"
      >
        <!-- Pulsing ring effect -->
        <span class="absolute inset-0 rounded-full bg-purple-400 animate-ping opacity-50"></span>

        <!-- Main button with logo -->
        <div class="relative w-14 h-14 bg-white rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-transform duration-200 hover:shadow-xl border-2 border-purple-500">
          <img src="/logo.png" alt="Popust.ba" class="w-10 h-10 object-contain" />

          <!-- Notification badge -->
          <span class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-bounce">
            !
          </span>
        </div>

        <!-- Tooltip -->
        <div class="absolute bottom-full right-0 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
          <div class="bg-gray-900 text-white text-sm px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">
            Recite nam šta kupujete
            <div class="absolute bottom-0 right-4 transform translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>
      </button>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const emit = defineEmits(['click'])

const { user } = useAuth()

const shouldShow = computed(() => {
  // Don't show if not logged in
  if (!user.value) return false

  // Check if user already has grocery interests set in database
  const preferences = user.value.preferences as Record<string, any> | null
  if (preferences?.grocery_interests && preferences.grocery_interests.length > 0) {
    // User has interests - don't show floating button
    return false
  }

  // Show for users without interests set
  return true
})

function handleClick() {
  emit('click')
}
</script>

<style scoped>
.bounce-enter-active {
  animation: bounceIn 0.5s ease-out;
}

.bounce-leave-active {
  animation: bounceOut 0.3s ease-in;
}

@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.1);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounceOut {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0.3);
  }
}

/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  .animate-ping,
  .animate-bounce {
    animation: none;
  }

  .bounce-enter-active,
  .bounce-leave-active {
    animation: none;
    transition: opacity 0.2s;
  }
}
</style>
