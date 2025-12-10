/**
 * Composable for tracking user activity (page views, filters, pagination, etc.)
 */
export function useActivityTracking() {
  const { post } = useApi()
  const { user } = useAuth()

  /**
   * Track a single activity
   */
  const trackActivity = async (
    activityType: string,
    page: string,
    data: Record<string, any> = {}
  ) => {
    // Only track for logged-in users
    if (!user.value) return

    try {
      await post('/api/activity/track', {
        activity_type: activityType,
        page,
        data
      })
    } catch (error) {
      // Silently fail - tracking shouldn't break the app
      console.debug('Activity tracking failed:', error)
    }
  }

  /**
   * Track a page view
   */
  const trackPageView = (page: string, data: Record<string, any> = {}) => {
    return trackActivity('page_view', page, data)
  }

  /**
   * Track filter change
   */
  const trackFilter = (page: string, filterType: string, value: any) => {
    return trackActivity('filter', page, {
      filter_type: filterType,
      value
    })
  }

  /**
   * Track pagination
   */
  const trackPagination = (page: string, pageNumber: number) => {
    return trackActivity('pagination', page, {
      page_number: pageNumber
    })
  }

  /**
   * Track search
   */
  const trackSearch = (page: string, query: string, resultCount: number) => {
    return trackActivity('search', page, {
      query,
      result_count: resultCount
    })
  }

  /**
   * Track product click/interaction
   */
  const trackProductClick = (page: string, productId: number) => {
    return trackActivity('product_click', page, {
      product_id: productId
    })
  }

  return {
    trackActivity,
    trackPageView,
    trackFilter,
    trackPagination,
    trackSearch,
    trackProductClick
  }
}
