<template>
  <!-- Mobile Bottom Navigation - only visible on small screens -->
  <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 safe-area-bottom">
    <div class="flex items-center justify-around h-16">
      <!-- Home -->
      <NuxtLink
        to="/"
        class="flex flex-col items-center justify-center flex-1 h-full"
        :class="isActive('/') ? 'text-purple-600' : 'text-gray-500'"
      >
        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <span class="text-xs mt-1">Početna</span>
      </NuxtLink>

      <!-- Products -->
      <NuxtLink
        to="/proizvodi"
        class="flex flex-col items-center justify-center flex-1 h-full"
        :class="isActive('/proizvodi') ? 'text-purple-600' : 'text-gray-500'"
      >
        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z"/>
        </svg>
        <span class="text-xs mt-1">Proizvodi</span>
      </NuxtLink>

      <!-- Favorites -->
      <template v-if="isAuthenticated">
        <NuxtLink
          to="/favorites"
          class="flex flex-col items-center justify-center flex-1 h-full relative"
          :class="isActive('/favorites') ? 'text-purple-600' : 'text-gray-500'"
        >
          <div class="relative">
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
            <span
              v-if="favoritesStore.discountedCount > 0"
              class="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1"
            >
              {{ favoritesStore.discountedCount }}
            </span>
          </div>
          <span class="text-xs mt-1">Omiljeni</span>
        </NuxtLink>

        <!-- Shopping Lists -->
        <NuxtLink
          to="/liste"
          class="flex flex-col items-center justify-center flex-1 h-full"
          :class="isActive('/liste') ? 'text-purple-600' : 'text-gray-500'"
        >
          <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          <span class="text-xs mt-1">Liste</span>
        </NuxtLink>

        <!-- Cart -->
        <button
          @click="$emit('toggle-sidebar')"
          class="flex flex-col items-center justify-center flex-1 h-full text-gray-500"
        >
          <div class="relative">
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
            <span
              v-if="cartStore.itemCount > 0"
              class="absolute -top-2 -right-2 bg-green-600 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1"
            >
              {{ cartStore.itemCount }}
            </span>
          </div>
          <span class="text-xs mt-1">Korpa</span>
          <!-- TTL indicator -->
          <span
            v-if="cartStore.isActive && cartStore.ttlFormatted"
            :class="[
              'absolute bottom-14 text-xs font-mono font-bold whitespace-nowrap px-2 py-0.5 rounded shadow-sm',
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
      </template>

      <!-- Login/Register for non-authenticated users -->
      <template v-else>
        <NuxtLink
          to="/prijava"
          class="flex flex-col items-center justify-center flex-1 h-full"
          :class="isActive('/prijava') ? 'text-purple-600' : 'text-gray-500'"
        >
          <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
          <span class="text-xs mt-1">Prijava</span>
        </NuxtLink>
      </template>

      <!-- Notifications (authenticated only) -->
      <div v-if="isAuthenticated" class="flex flex-col items-center justify-center flex-1 h-full relative">
        <MobileNotificationBell />
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import { useFavoritesStore } from '~/stores/favorites'

const route = useRoute()
const { isAuthenticated } = useAuth()
const cartStore = useCartStore()
const favoritesStore = useFavoritesStore()

defineEmits<{
  'toggle-sidebar': []
}>()

// Check if current route matches
function isActive(path: string): boolean {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

// Time warning states for cart TTL
const isTimeCritical = computed(() => {
  return cartStore.ttlSeconds !== null && cartStore.ttlSeconds < 1800
})

const isTimeWarning = computed(() => {
  return cartStore.ttlSeconds !== null && cartStore.ttlSeconds < 3600 && cartStore.ttlSeconds >= 1800
})

// Fetch data on mount
onMounted(async () => {
  if (isAuthenticated.value) {
    await Promise.all([
      favoritesStore.fetchFavorites(),
      cartStore.fetchHeader()
    ])

    if (cartStore.isActive) {
      cartStore.startTtlTicker()
    }
  }
})

onBeforeUnmount(() => {
  cartStore.stopTtlTicker()
})
</script>

<style scoped>
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
