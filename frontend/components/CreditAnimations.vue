<template>
  <Teleport to="body">
    <div class="fixed top-0 right-0 w-full h-full pointer-events-none z-[9999]">
      <TransitionGroup name="credit-fade">
        <div
          v-for="animation in animations"
          :key="animation.id"
          class="absolute credit-float"
          :style="getAnimationStyle()"
        >
          <div class="text-2xl font-bold text-green-500 drop-shadow-lg flex items-center gap-1">
            <span>+{{ animation.amount }}</span>
            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const { animations } = useCreditAnimation()

// Get random starting position near the top-right where credits are displayed
const getAnimationStyle = () => {
  // Start from right side near header credit display
  const startX = window.innerWidth - 150 + (Math.random() * 50 - 25)
  const startY = 20 + (Math.random() * 20 - 10)

  return {
    left: `${startX}px`,
    top: `${startY}px`
  }
}
</script>

<style scoped>
.credit-float {
  animation: float-up 2s ease-out forwards;
}

@keyframes float-up {
  0% {
    opacity: 0;
    transform: translateY(0) scale(0.5);
  }
  15% {
    opacity: 1;
    transform: translateY(-20px) scale(1.2);
  }
  50% {
    opacity: 1;
    transform: translateY(-60px) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateY(-100px) scale(0.8);
  }
}

.credit-fade-enter-active,
.credit-fade-leave-active {
  transition: opacity 0.3s ease;
}

.credit-fade-enter-from,
.credit-fade-leave-to {
  opacity: 0;
}
</style>
