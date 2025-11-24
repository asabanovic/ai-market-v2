/**
 * Notifications Store
 * Manages user notifications for discount alerts and other events
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Notification {
  id: number
  type: string
  title: string
  message: string
  product_id?: number
  is_read: boolean
  action_url?: string
  created_at: string
}

export const useNotificationsStore = defineStore('notifications', () => {
  // State
  const items = ref<Notification[]>([])
  const unreadCount = ref<number>(0)
  const loading = ref<boolean>(false)
  const isOpen = ref<boolean>(false)

  // Getters
  const unreadNotifications = computed(() => {
    return items.value.filter(item => !item.is_read)
  })

  const hasUnread = computed(() => unreadCount.value > 0)

  // Actions
  async function fetchNotifications(unreadOnly: boolean = false) {
    const { $api } = useNuxtApp()
    loading.value = true

    try {
      const params = new URLSearchParams()
      if (unreadOnly) {
        params.append('unread_only', 'true')
      }
      params.append('limit', '50')

      const response = await $api.get(`/notifications?${params.toString()}`)

      if (response.success) {
        items.value = response.notifications || []
      }
    } catch (error: any) {
      console.error('Failed to fetch notifications:', error)
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    const { $api } = useNuxtApp()

    try {
      const response = await $api.get('/notifications/unread-count')

      if (response.success) {
        unreadCount.value = response.unread_count || 0
      }
    } catch (error: any) {
      console.error('Failed to fetch unread count:', error)
      unreadCount.value = 0
    }
  }

  async function markAsRead(notificationId: number) {
    const { $api } = useNuxtApp()

    // Optimistic update
    const notification = items.value.find(item => item.id === notificationId)
    if (notification && !notification.is_read) {
      notification.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }

    try {
      await $api.post(`/notifications/${notificationId}/read`)
      return { success: true }
    } catch (error: any) {
      console.error('Failed to mark notification as read:', error)

      // Revert optimistic update on error
      if (notification) {
        notification.is_read = false
        unreadCount.value += 1
      }

      return { success: false, error }
    }
  }

  async function markAllAsRead() {
    const { $api } = useNuxtApp()

    // Store old values for potential rollback
    const oldItems = [...items.value]
    const oldCount = unreadCount.value

    // Optimistic update
    items.value.forEach(item => {
      item.is_read = true
    })
    unreadCount.value = 0

    try {
      await $api.post('/notifications/mark-all-read')
      return { success: true }
    } catch (error: any) {
      console.error('Failed to mark all as read:', error)

      // Revert optimistic update on error
      items.value = oldItems
      unreadCount.value = oldCount

      return { success: false, error }
    }
  }

  async function deleteNotification(notificationId: number) {
    const { $api } = useNuxtApp()

    // Optimistic update
    const index = items.value.findIndex(item => item.id === notificationId)
    let removedItem: Notification | null = null
    if (index !== -1) {
      removedItem = items.value[index]
      if (!removedItem.is_read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      items.value.splice(index, 1)
    }

    try {
      await $api.delete(`/notifications/${notificationId}`)
      return { success: true }
    } catch (error: any) {
      console.error('Failed to delete notification:', error)

      // Revert optimistic update on error
      if (removedItem && index !== -1) {
        items.value.splice(index, 0, removedItem)
        if (!removedItem.is_read) {
          unreadCount.value += 1
        }
      }

      return { success: false, error }
    }
  }

  async function clearAll() {
    const { $api } = useNuxtApp()

    // Store old values for potential rollback
    const oldItems = [...items.value]
    const oldCount = unreadCount.value

    // Optimistic update
    items.value = []
    unreadCount.value = 0

    try {
      await $api.delete('/notifications/clear-all')
      return { success: true }
    } catch (error: any) {
      console.error('Failed to clear all notifications:', error)

      // Revert optimistic update on error
      items.value = oldItems
      unreadCount.value = oldCount

      return { success: false, error }
    }
  }

  function toggleDropdown() {
    isOpen.value = !isOpen.value
  }

  function closeDropdown() {
    isOpen.value = false
  }

  function reset() {
    items.value = []
    unreadCount.value = 0
    loading.value = false
    isOpen.value = false
  }

  return {
    // State
    items,
    unreadCount,
    loading,
    isOpen,

    // Getters
    unreadNotifications,
    hasUnread,

    // Actions
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
    toggleDropdown,
    closeDropdown,
    reset
  }
})
