<template>
  <Teleport to="body">
    <Transition name="bounce">
      <button
        v-if="shouldShow"
        @click="openFeedback"
        class="fixed bottom-4 right-4 md:bottom-6 md:right-6 z-50 group"
        aria-label="Ostavite povratne informacije"
      >
        <!-- Pulsing ring effect -->
        <span class="absolute inset-0 rounded-full bg-purple-400 animate-ping opacity-50"></span>

        <!-- Label next to button -->
        <div class="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-purple-600 text-white text-sm font-medium px-3 py-1.5 rounded-lg shadow-lg whitespace-nowrap">
          Pomozite nam
          <div class="absolute right-0 top-1/2 transform translate-x-1/2 -translate-y-1/2 rotate-45 w-2 h-2 bg-purple-600"></div>
        </div>

        <!-- Main button -->
        <div class="relative w-14 h-14 bg-purple-600 rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-transform duration-200 hover:shadow-xl hover:bg-purple-700">
          <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>

          <!-- Notification badge -->
          <span class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-bounce">
            ?
          </span>
        </div>
      </button>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const { user } = useAuth()

const emit = defineEmits(['open-feedback'])

// Only show for logged-in users who haven't given feedback yet
const shouldShow = computed(() => {
  if (!user.value) return false
  // Check localStorage if user already submitted feedback
  if (process.client && localStorage.getItem('feedback_submitted')) return false
  return true
})

function openFeedback() {
  emit('open-feedback')
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
