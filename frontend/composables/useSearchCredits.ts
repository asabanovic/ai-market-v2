/**
 * Search Credits Composable
 * Global state for user search credits - shared across all components
 */

// Global credits state (shared across all components)
const searchCounts = ref<any>(null)
const isLoading = ref(false)

export function useSearchCredits() {
  const { get, post } = useApi()

  async function refreshCredits() {
    if (isLoading.value) return // Prevent duplicate requests

    isLoading.value = true
    try {
      const data = await get('/auth/search-counts')
      searchCounts.value = data
      console.log('Credits refreshed:', data)
    } catch (error) {
      console.error('Error refreshing credits:', error)
    } finally {
      isLoading.value = false
    }
  }

  // Update credits directly (for immediate updates after search)
  function updateCreditsRemaining(remaining: number) {
    if (searchCounts.value) {
      searchCounts.value = {
        ...searchCounts.value,
        remaining
      }
      console.log('Credits updated to:', remaining)
    }
  }

  // Deduct credits for actions like viewing product details
  async function deductCredits(amount: number = 1, action: string = 'product_view', productId?: number): Promise<boolean> {
    try {
      const response = await post('/api/credits/deduct', {
        amount,
        action,
        product_id: productId
      })

      if (response.success) {
        // Update local credits count
        updateCreditsRemaining(response.credits_remaining)
        return true
      }
      return false
    } catch (error) {
      console.error('Error deducting credits:', error)
      return false
    }
  }

  // Clear credits (on logout)
  function clearCredits() {
    searchCounts.value = null
  }

  return {
    // State
    searchCounts: readonly(searchCounts),
    isLoading: readonly(isLoading),

    // Methods
    refreshCredits,
    updateCreditsRemaining,
    deductCredits,
    clearCredits
  }
}
