/**
 * Favorites Store
 * Manages user's favorited products
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface FavoriteSummary {
  favorite_id: number
  product_id: number
  name: string
  image_url?: string
  category?: string
  price: number
  old_price?: number
  discount_percent?: number
  expires?: string
  business: {
    id: number
    name: string
    logo?: string
  }
  created_at: string
}

export const useFavoritesStore = defineStore('favorites', () => {
  // State
  const items = ref<FavoriteSummary[]>([])
  const loading = ref<boolean>(false)

  // Getters
  const count = computed(() => items.value.length)

  // Count only items with active discounts
  const discountedCount = computed(() => {
    return items.value.filter(item => item.discount_percent && item.discount_percent > 0).length
  })

  const isFavorited = computed(() => {
    return (productId: number) => {
      return items.value.some(item => item.product_id === productId)
    }
  })

  const getFavoriteId = computed(() => {
    return (productId: number) => {
      const favorite = items.value.find(item => item.product_id === productId)
      return favorite?.favorite_id || null
    }
  })

  // Actions
  async function fetchFavorites() {
    const { $api } = useNuxtApp()
    loading.value = true

    try {
      const data = await $api.get('/favorites')
      items.value = data
    } catch (error: any) {
      console.error('Failed to fetch favorites:', error)
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function addFavorite(productId: number) {
    const { $api } = useNuxtApp()

    // Optimistic update
    const alreadyFavorited = isFavorited.value(productId)
    if (alreadyFavorited) {
      return { success: true, already: true }
    }

    try {
      const data = await $api.post('/favorites', {
        product_id: productId
      })

      // If it was already favorited server-side
      if (data.already) {
        await fetchFavorites() // Sync with server
        return { success: true, already: true }
      }

      // Add to local state (will be synced on next fetch)
      await fetchFavorites()

      return { success: true, data }
    } catch (error: any) {
      console.error('Failed to add favorite:', error)
      return { success: false, error }
    }
  }

  async function removeFavorite(favoriteId: number) {
    const { $api } = useNuxtApp()

    // Optimistic update
    const index = items.value.findIndex(item => item.favorite_id === favoriteId)
    let removedItem: FavoriteSummary | null = null
    if (index !== -1) {
      removedItem = items.value[index]
      items.value.splice(index, 1)
    }

    try {
      await $api.delete(`/favorites/${favoriteId}`)
      return { success: true }
    } catch (error: any) {
      console.error('Failed to remove favorite:', error)

      // Revert optimistic update on error
      if (removedItem) {
        items.value.push(removedItem)
      }

      return { success: false, error }
    }
  }

  async function toggleFavorite(productId: number) {
    if (isFavorited.value(productId)) {
      const favoriteId = getFavoriteId.value(productId)
      if (favoriteId) {
        return await removeFavorite(favoriteId)
      }
    } else {
      return await addFavorite(productId)
    }
  }

  function reset() {
    items.value = []
    loading.value = false
  }

  return {
    // State
    items,
    loading,

    // Getters
    count,
    discountedCount,
    isFavorited,
    getFavoriteId,

    // Actions
    fetchFavorites,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    reset
  }
})
