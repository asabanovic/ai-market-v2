<template>
  <button
    @click="navigateTo('/notifikacije')"
    class="flex flex-col items-center justify-center w-full h-full text-gray-500"
  >
    <div class="relative">
      <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <span
        v-if="notificationsStore.unreadCount > 0"
        class="absolute -top-2 -right-2 bg-purple-600 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 animate-pulse"
      >
        {{ displayCount }}
      </span>
    </div>
    <span class="text-xs mt-1">Obavijesti</span>
  </button>
</template>

<script setup lang="ts">
import { useNotificationsStore } from '~/stores/notifications'

const notificationsStore = useNotificationsStore()

const displayCount = computed(() => {
  return notificationsStore.unreadCount > 99 ? '99+' : notificationsStore.unreadCount
})

onMounted(() => {
  notificationsStore.fetchUnreadCount()
})
</script>
