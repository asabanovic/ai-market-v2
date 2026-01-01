/**
 * Attribution Tracking Plugin
 *
 * For anonymous users: Captures first-touch attribution in localStorage → sent on registration
 * For logged-in users: Tracks return visits from email campaigns (UTM params)
 *
 * Runs client-side only (*.client.ts naming convention).
 */
export default defineNuxtPlugin(async () => {
  const { captureAttribution } = useAttribution()
  const { $api } = useNuxtApp()

  const token = localStorage.getItem('token')

  if (!token) {
    // Anonymous user: capture first-touch attribution
    captureAttribution()
    return
  }

  // Logged-in user: check if they came from an email campaign
  const url = new URL(window.location.href)
  const utmSource = url.searchParams.get('utm_source')
  const utmCampaign = url.searchParams.get('utm_campaign')

  // Only track if they came from an email (has utm_source=email)
  if (utmSource === 'email' && utmCampaign) {
    try {
      // Send return visit tracking to backend
      await $api.post('/api/user/track-email-visit', {
        campaign: utmCampaign,
        medium: url.searchParams.get('utm_medium') || 'email',
        landing_page: window.location.pathname
      })
    } catch (error) {
      // Silent fail - don't disrupt user experience
      console.error('[Attribution] Failed to track email visit:', error)
    }
  }
})
