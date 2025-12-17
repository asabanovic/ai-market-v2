<template>
  <div class="fixed top-2 right-2 md:top-4 md:right-4 z-[100] space-y-2 pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="pointer-events-auto w-72 md:w-96 max-w-[calc(100vw-1rem)] bg-white dark:bg-gray-800 rounded-lg shadow-lg border overflow-hidden"
        :class="toastBorderClass(toast.type)"
      >
        <div class="p-3 md:p-4">
          <!-- Header -->
          <div class="flex items-start justify-between mb-1 md:mb-2">
            <div class="flex items-center gap-2">
              <!-- Icon -->
              <div class="flex-shrink-0">
                <Icon
                  :name="toastIcon(toast.type)"
                  :class="toastIconClass(toast.type)"
                  class="w-4 h-4 md:w-5 md:h-5"
                />
              </div>

              <!-- Title -->
              <h4 v-if="toast.title" class="font-semibold text-sm md:text-base text-gray-900 dark:text-white">
                {{ toast.title }}
              </h4>
            </div>

            <!-- Close button -->
            <button
              @click="dismissToast(toast.id)"
              class="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <Icon name="mdi:close" class="w-4 h-4 md:w-5 md:h-5" />
            </button>
          </div>

          <!-- Message -->
          <p class="text-xs md:text-sm text-gray-700 dark:text-gray-300 mb-2 md:mb-3">
            {{ toast.message }}
          </p>

          <!-- Action button -->
          <button
            v-if="toast.action"
            @click="toast.action.onClick(); dismissToast(toast.id)"
            class="w-full py-1.5 md:py-2 px-3 md:px-4 rounded-md font-medium text-xs md:text-sm transition-colors"
            :class="actionButtonClass(toast.type)"
          >
            {{ toast.action.label }}
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
const { toasts, dismissToast } = useCreditsToast()

function toastBorderClass(type: string) {
  switch (type) {
    case 'success':
      return 'border-l-4 border-green-500'
    case 'warning':
      return 'border-l-4 border-yellow-500'
    case 'error':
      return 'border-l-4 border-red-500'
    default:
      return 'border-l-4 border-blue-500'
  }
}

function toastIcon(type: string) {
  switch (type) {
    case 'success':
      return 'mdi:check-circle'
    case 'warning':
      return 'mdi:alert-circle'
    case 'error':
      return 'mdi:alert-circle-outline'
    default:
      return 'mdi:information'
  }
}

function toastIconClass(type: string) {
  switch (type) {
    case 'success':
      return 'text-green-500'
    case 'warning':
      return 'text-yellow-500'
    case 'error':
      return 'text-red-500'
    default:
      return 'text-blue-500'
  }
}

function actionButtonClass(type: string) {
  switch (type) {
    case 'success':
      return 'bg-green-500 hover:bg-green-600 text-white'
    case 'warning':
      return 'bg-yellow-500 hover:bg-yellow-600 text-white'
    case 'error':
      return 'bg-red-500 hover:bg-red-600 text-white'
    default:
      return 'bg-blue-500 hover:bg-blue-600 text-white'
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px) scale(0.95);
}
</style>
