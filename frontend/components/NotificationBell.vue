<template>
  <div class="relative">
    <!-- Notification Bell Button -->
    <button
      @click="handleClick"
      class="relative p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
      aria-label="Notifications"
      title="Notifikacije"
    >
      <!-- Bell Icon -->
      <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>

      <!-- Unread Badge -->
      <span
        v-if="notificationsStore.unreadCount > 0"
        class="absolute -top-1 -right-1 bg-purple-600 text-white text-xs font-bold rounded-full min-w-[20px] h-5 flex items-center justify-center px-1 animate-pulse"
      >
        {{ displayCount }}
      </span>
    </button>

    <!-- Notifications Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="notificationsStore.isOpen"
        class="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 z-50 max-h-[600px] overflow-hidden flex flex-col"
        @click.stop
      >
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Notifikacije
          </h3>
          <div class="flex items-center gap-2">
            <button
              v-if="notificationsStore.hasUnread"
              @click="handleMarkAllRead"
              class="text-xs text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
              title="Označi sve kao pročitano"
            >
              Označi sve
            </button>
            <button
              @click="notificationsStore.closeDropdown"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Notifications List -->
        <div class="overflow-y-auto flex-1">
          <template v-if="notificationsStore.loading">
            <div class="flex items-center justify-center py-12">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          </template>

          <template v-else-if="notificationsStore.items.length === 0">
            <div class="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
              <svg class="w-16 h-16 mb-4 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <p class="text-sm">Nemate notifikacija</p>
            </div>
          </template>

          <template v-else>
            <div
              v-for="notification in notificationsStore.items"
              :key="notification.id"
              :class="[
                'p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors cursor-pointer',
                !notification.is_read ? 'bg-purple-50 dark:bg-purple-900/20' : ''
              ]"
              @click="handleNotificationClick(notification)"
            >
              <div class="flex items-start gap-3">
                <!-- Notification Icon -->
                <div class="flex-shrink-0 mt-1">
                  <div v-if="notification.type === 'discount_alert'" class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                    </svg>
                  </div>
                </div>

                <!-- Notification Content -->
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                    {{ notification.title }}
                  </p>
                  <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    {{ notification.message }}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    {{ formatTimeAgo(notification.created_at) }}
                  </p>
                </div>

                <!-- Unread Indicator & Delete -->
                <div class="flex flex-col items-end gap-2">
                  <div
                    v-if="!notification.is_read"
                    class="w-2 h-2 bg-purple-600 rounded-full"
                    title="Nepročitano"
                  ></div>
                  <button
                    @click.stop="handleDelete(notification.id)"
                    class="text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    title="Obriši"
                  >
                    <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Footer -->
        <div
          v-if="notificationsStore.items.length > 0"
          class="p-3 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center"
        >
          <button
            @click="handleClearAll"
            class="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          >
            Obriši sve
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { useNotificationsStore } from '~/stores/notifications'
import type { Notification } from '~/stores/notifications'

const notificationsStore = useNotificationsStore()
const router = useRouter()

// Display count with 99+ limit
const displayCount = computed(() => {
  return notificationsStore.unreadCount > 99 ? '99+' : notificationsStore.unreadCount
})

// Handle bell click
async function handleClick() {
  notificationsStore.toggleDropdown()
  if (notificationsStore.isOpen && notificationsStore.items.length === 0) {
    await notificationsStore.fetchNotifications()
  }
}

// Handle notification click
async function handleNotificationClick(notification: Notification) {
  // Mark as read if unread
  if (!notification.is_read) {
    await notificationsStore.markAsRead(notification.id)
  }

  // Navigate to action URL if available
  if (notification.action_url) {
    notificationsStore.closeDropdown()
    router.push(notification.action_url)
  }
}

// Mark all as read
async function handleMarkAllRead() {
  await notificationsStore.markAllAsRead()
}

// Delete notification
async function handleDelete(notificationId: number) {
  await notificationsStore.deleteNotification(notificationId)
}

// Clear all notifications
async function handleClearAll() {
  if (confirm('Da li ste sigurni da želite obrisati sve notifikacije?')) {
    await notificationsStore.clearAll()
  }
}

// Format time ago
function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Upravo sada'
  if (diffMins < 60) return `Prije ${diffMins} min`
  if (diffHours < 24) return `Prije ${diffHours}h`
  if (diffDays === 1) return 'Jučer'
  if (diffDays < 7) return `Prije ${diffDays} dana`

  return date.toLocaleDateString('bs-BA', {
    day: 'numeric',
    month: 'short'
  })
}

// Close dropdown when clicking outside
onMounted(() => {
  // Fetch unread count on mount
  notificationsStore.fetchUnreadCount()

  // Set up polling for new notifications (every 2 minutes)
  const pollInterval = setInterval(() => {
    notificationsStore.fetchUnreadCount()
  }, 120000)

  // Click outside handler
  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (notificationsStore.isOpen && !target.closest('.relative')) {
      notificationsStore.closeDropdown()
    }
  }

  document.addEventListener('click', handleClickOutside)

  onBeforeUnmount(() => {
    clearInterval(pollInterval)
    document.removeEventListener('click', handleClickOutside)
  })
})
</script>
