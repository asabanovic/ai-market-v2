/**
 * Shopping Cart Store
 * Manages shopping list state with 24-hour TTL
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ShoppingListItem {
  item_id: number
  product_id: number
  name: string
  qty: number
  unit_price: number
  subtotal: number
  old_price?: number
  estimated_saving: number
}

export interface ShoppingListGroup {
  store: {
    id: number
    name: string
    logo?: string
  }
  items: ShoppingListItem[]
  group_subtotal: number
  group_saving: number
}

export interface SidebarData {
  list_id: number | null
  ttl_seconds: number | null
  groups: ShoppingListGroup[]
  total_items: number
  grand_total: number
  grand_saving: number
}

export const useCartStore = defineStore('cart', () => {
  // State
  const listId = ref<number | null>(null)
  const ttlSeconds = ref<number | null>(null)
  const itemCount = ref<number>(0)
  const sidebar = ref<SidebarData | null>(null)
  const loading = ref<boolean>(false)

  let ttlInterval: NodeJS.Timeout | null = null

  // Getters
  const isActive = computed(() => {
    return ttlSeconds.value !== null && ttlSeconds.value > 0
  })

  const ttlFormatted = computed(() => {
    if (!ttlSeconds.value || ttlSeconds.value <= 0) return '00:00'

    const hours = Math.floor(ttlSeconds.value / 3600)
    const minutes = Math.floor((ttlSeconds.value % 3600) / 60)
    const seconds = ttlSeconds.value % 60

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  })

  // Actions
  async function fetchHeader() {
    const { $api } = useNuxtApp()

    try {
      const data = await $api.get('/shopping-list/header/ttl')
      ttlSeconds.value = data.ttl_seconds
      itemCount.value = data.item_count

      // Start TTL countdown if active
      if (isActive.value) {
        startTtlTicker()
      }
    } catch (error: any) {
      console.error('Failed to fetch cart header:', error)
    }
  }

  async function fetchSidebar() {
    const { $api } = useNuxtApp()
    loading.value = true

    try {
      const data = await $api.get('/shopping-list/sidebar')
      sidebar.value = data
      listId.value = data.list_id
      ttlSeconds.value = data.ttl_seconds
      itemCount.value = data.total_items

      // Start TTL countdown if active
      if (isActive.value) {
        startTtlTicker()
      }
    } catch (error: any) {
      console.error('Failed to fetch cart sidebar:', error)
      sidebar.value = null
    } finally {
      loading.value = false
    }
  }

  async function addItem(productId: number, offerId: number, qty: number = 1) {
    const { $api } = useNuxtApp()
    loading.value = true

    try {
      const data = await $api.post('/shopping-list/items', {
        product_id: productId,
        offer_id: offerId,
        qty
      })

      // Update state
      listId.value = data.list_id
      ttlSeconds.value = data.ttl_seconds

      // Refresh sidebar if it's open
      if (sidebar.value) {
        await fetchSidebar()
      } else {
        await fetchHeader()
      }

      return { success: true, data }
    } catch (error: any) {
      console.error('Failed to add item to cart:', error)
      return { success: false, error }
    } finally {
      loading.value = false
    }
  }

  async function updateQty(itemId: number, qty: number) {
    const { $api } = useNuxtApp()
    console.log("API: ", $api, qty)
    try {
      if (qty === 0) {
        await $api.delete(`/shopping-list/items/${itemId}`)
      } else {
        await $api.patch(`/shopping-list/items/${itemId}`, { qty })
      }

      // Refresh sidebar
      await fetchSidebar()

      return { success: true }
    } catch (error: any) {
      console.error('Failed to update item qty:', error)
      return { success: false, error }
    }
  }

  async function removeItem(itemId: number) {
    const { $api } = useNuxtApp()

    try {
      await $api.delete(`/shopping-list/items/${itemId}`)

      // Refresh sidebar
      await fetchSidebar()

      return { success: true }
    } catch (error: any) {
      console.error('Failed to remove item:', error)
      return { success: false, error }
    }
  }

  async function checkout(phone?: string) {
    const { $api } = useNuxtApp()

    if (!listId.value) {
      return { success: false, error: { message: 'No active shopping list' } }
    }

    loading.value = true

    try {
      const data = await $api.post(`/shopping-list/${listId.value}/checkout`, {
        phone
      })

      // Keep sidebar data but mark as sent
      // The list is still valid until expiry

      return { success: true, data }
    } catch (error: any) {
      console.error('Failed to checkout:', error)
      return { success: false, error }
    } finally {
      loading.value = false
    }
  }

  function startTtlTicker() {
    // Clear existing interval
    if (ttlInterval) {
      clearInterval(ttlInterval)
    }

    // Start new interval
    ttlInterval = setInterval(() => {
      if (ttlSeconds.value !== null && ttlSeconds.value > 0) {
        ttlSeconds.value--
      } else {
        // TTL expired
        stopTtlTicker()
        ttlSeconds.value = null
        itemCount.value = 0
        sidebar.value = null
        listId.value = null
      }
    }, 1000)
  }

  function stopTtlTicker() {
    if (ttlInterval) {
      clearInterval(ttlInterval)
      ttlInterval = null
    }
  }

  function reset() {
    stopTtlTicker()
    listId.value = null
    ttlSeconds.value = null
    itemCount.value = 0
    sidebar.value = null
    loading.value = false
  }

  return {
    // State
    listId,
    ttlSeconds,
    itemCount,
    sidebar,
    loading,

    // Getters
    isActive,
    ttlFormatted,

    // Actions
    fetchHeader,
    fetchSidebar,
    addItem,
    updateQty,
    removeItem,
    checkout,
    startTtlTicker,
    stopTtlTicker,
    reset
  }
})
