<template>
  <div class="flex items-center gap-4">
    <!-- Notifications Bell -->
    <NotificationBell />

    <!-- Favorites Icon -->
    <button
      @click="navigateTo('/favorites')"
      class="relative p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
      aria-label="Favorites"
    >
      <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
      </svg>
      <span
        v-if="favoritesStore.discountedCount > 0"
        class="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
      >
        {{ favoritesStore.discountedCount }}
      </span>
    </button>

    <!-- My Products Icon (tracked products) -->
    <button
      @click="navigateTo('/moji-proizvodi')"
      class="relative p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
      aria-label="Moji proizvodi"
      title="Moji praćeni proizvodi"
    >
      <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
      </svg>
      <span
        v-if="trackedProductsStore.count > 0"
        class="absolute -top-1 -right-1 bg-purple-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
      >
        {{ trackedProductsStore.count > 9 ? '9+' : trackedProductsStore.count }}
      </span>
    </button>

    <!-- Shopping Cart Icon -->
    <button
      @click="toggleSidebar"
      class="relative p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
      aria-label="Shopping Cart"
    >
      <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
      </svg>

      <!-- Item count badge (green) -->
      <span
        v-if="cartStore.itemCount > 0"
        class="absolute -top-1 -right-1 bg-green-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
      >
        {{ cartStore.itemCount }}
      </span>

      <!-- TTL countdown (green theme with urgency states) -->
      <span
        v-if="cartStore.isActive && cartStore.ttlFormatted"
        :class="[
          'absolute -bottom-3 left-1/2 -translate-x-1/2 text-xs font-mono font-bold whitespace-nowrap px-2 py-0.5 rounded shadow-sm',
          isTimeCritical
            ? 'bg-red-500 text-white animate-pulse'
            : isTimeWarning
            ? 'bg-orange-500 text-white'
            : 'bg-green-600 text-white'
        ]"
      >
        {{ cartStore.ttlFormatted }}
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'
import { useTrackedProductsStore } from '~/stores/trackedProducts'

const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()
const trackedProductsStore = useTrackedProductsStore()

const emit = defineEmits<{
  'toggle-sidebar': []
}>()

// Time warning states
const isTimeCritical = computed(() => {
  return cartStore.ttlSeconds !== null && cartStore.ttlSeconds < 1800 // Less than 30 minutes
})

const isTimeWarning = computed(() => {
  return cartStore.ttlSeconds !== null && cartStore.ttlSeconds < 3600 && cartStore.ttlSeconds >= 1800 // Between 30min and 1 hour
})

function toggleSidebar() {
  emit('toggle-sidebar')
}

// Fetch data on mount
onMounted(async () => {
  await Promise.all([
    favoritesStore.fetchFavorites(),
    cartStore.fetchHeader(),
    trackedProductsStore.fetchCount()
  ])

  // Start TTL ticker if cart is active
  if (cartStore.isActive) {
    cartStore.startTtlTicker()
  }
})

// Cleanup on unmount
onBeforeUnmount(() => {
  cartStore.stopTtlTicker()
})
</script>
