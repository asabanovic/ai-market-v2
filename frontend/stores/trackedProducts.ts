import { defineStore } from 'pinia'

export const useTrackedProductsStore = defineStore('trackedProducts', () => {
  const { get } = useApi()

  const count = ref(0)
  const isLoading = ref(false)

  async function fetchCount() {
    try {
      isLoading.value = true
      const data = await get('/api/user/tracked-products')
      count.value = data.tracked_products?.length || 0
    } catch (error) {
      console.debug('Failed to fetch tracked products count:', error)
    } finally {
      isLoading.value = false
    }
  }

  function setCount(newCount: number) {
    count.value = newCount
  }

  function increment() {
    count.value++
  }

  function decrement() {
    if (count.value > 0) count.value--
  }

  return {
    count,
    isLoading,
    fetchCount,
    setCount,
    increment,
    decrement
  }
})
