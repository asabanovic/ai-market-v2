<template>
  <div class="flex items-center gap-4">
    <!-- Favorites Icon -->
    <button
      @click="navigateTo('/favorites')"
      class="relative p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
      aria-label="Favorites"
    >
      <Icon name="mdi:heart" class="w-6 h-6" />
      <span
        v-if="favoritesStore.count > 0"
        class="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
      >
        {{ favoritesStore.count }}
      </span>
    </button>

    <!-- Shopping Cart Icon -->
    <button
      @click="toggleSidebar"
      class="relative p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
      aria-label="Shopping Cart"
    >
      <Icon name="mdi:cart" class="w-6 h-6" />

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

const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()

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
    cartStore.fetchHeader()
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
