<template>
  <div class="min-h-screen bg-white py-4 pb-20">
    <div class="max-w-2xl mx-auto px-4">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-900">Notifikacije</h1>
        <button
          v-if="notificationsStore.hasUnread"
          @click="handleMarkAllRead"
          class="text-sm text-purple-600 hover:text-purple-700"
        >
          Označi sve kao pročitano
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="notificationsStore.loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600"></div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="notificationsStore.items.length === 0"
        class="text-center py-12"
      >
        <svg class="w-20 h-20 mx-auto mb-4 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nemate notifikacija</h3>
        <p class="text-gray-500">Ovdje ćete vidjeti obavijesti o popustima na omiljenim proizvodima</p>
      </div>

      <!-- Notifications List -->
      <div v-else class="space-y-3">
        <div
          v-for="notification in notificationsStore.items"
          :key="notification.id"
          :class="[
            'p-4 rounded-lg border transition-colors cursor-pointer',
            !notification.is_read
              ? 'bg-purple-50 border-purple-200'
              : 'bg-white border-gray-200'
          ]"
          @click="handleNotificationClick(notification)"
        >
          <div class="flex items-start gap-3">
            <!-- Icon -->
            <div class="flex-shrink-0">
              <div
                v-if="notification.type === 'discount_alert'"
                class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center"
              >
                <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                </svg>
              </div>
              <div v-else class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                <svg class="w-5 h-5 text-gray-500" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
                </svg>
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <p class="font-semibold text-gray-900">{{ notification.title }}</p>
                <button
                  @click.stop="handleDelete(notification.id)"
                  class="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
              <p class="text-sm text-gray-600 mt-1">{{ notification.message }}</p>
              <p class="text-xs text-gray-400 mt-2">{{ formatTimeAgo(notification.created_at) }}</p>
            </div>

            <!-- Unread indicator -->
            <div
              v-if="!notification.is_read"
              class="w-2 h-2 bg-purple-600 rounded-full flex-shrink-0 mt-2"
            ></div>
          </div>
        </div>
      </div>

      <!-- Clear All Button -->
      <div v-if="notificationsStore.items.length > 0" class="mt-6 text-center">
        <button
          @click="handleClearAll"
          class="text-sm text-red-600 hover:text-red-700"
        >
          Obriši sve notifikacije
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNotificationsStore } from '~/stores/notifications'
import type { Notification } from '~/stores/notifications'

definePageMeta({
  middleware: 'auth'
})

const notificationsStore = useNotificationsStore()
const router = useRouter()

// Fetch notifications on mount
onMounted(async () => {
  await notificationsStore.fetchNotifications()
})

async function handleNotificationClick(notification: Notification) {
  if (!notification.is_read) {
    await notificationsStore.markAsRead(notification.id)
  }

  if (notification.action_url) {
    router.push(notification.action_url)
  }
}

async function handleMarkAllRead() {
  await notificationsStore.markAllAsRead()
}

async function handleDelete(notificationId: number) {
  await notificationsStore.deleteNotification(notificationId)
}

async function handleClearAll() {
  if (confirm('Da li ste sigurni da želite obrisati sve notifikacije?')) {
    await notificationsStore.clearAll()
  }
}

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
</script>
