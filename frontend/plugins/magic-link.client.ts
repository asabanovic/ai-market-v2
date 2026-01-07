/**
 * Magic Link Authentication Plugin
 *
 * Handles auth_token query parameters from email links.
 * When a user clicks a link in an email, they may be opening it in an
 * embedded browser (Gmail, Outlook) that doesn't have their session.
 * This plugin detects the auth_token param and automatically logs them in.
 */
export default defineNuxtPlugin(async () => {
  // Only run on client side
  if (!process.client) return

  const route = useRoute()
  const router = useRouter()
  const config = useRuntimeConfig()

  // Check for auth_token in URL query parameters
  const authToken = route.query.auth_token as string

  if (!authToken) return

  // Don't process if user is already logged in
  const existingToken = localStorage.getItem('token')
  if (existingToken) {
    // Remove auth_token from URL but keep other params
    const { auth_token, ...otherParams } = route.query
    router.replace({ query: otherParams })
    return
  }

  try {
    // Call backend to validate and exchange the magic link token for a JWT
    const apiBase = config.public.apiBase || 'http://localhost:5001/api'
    const response = await fetch(`${apiBase}/auth/magic-link/${authToken}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const data = await response.json()

    if (data.success && data.token) {
      // Store the JWT token
      localStorage.setItem('token', data.token)

      // Store user data for immediate access
      if (data.user) {
        useState<any>('user').value = data.user
      }

      console.log('Magic link login successful')

      // Remove auth_token from URL to prevent re-processing on refresh
      const { auth_token, ...otherParams } = route.query
      router.replace({ query: otherParams })

      // Force a page refresh to ensure all components pick up the auth state
      // This is important because some components may have already rendered
      // as "unauthenticated"
      window.location.reload()
    } else {
      // Token invalid or expired - just remove it from URL
      console.warn('Magic link validation failed:', data.error)
      const { auth_token, ...otherParams } = route.query
      router.replace({ query: otherParams })
    }
  } catch (error) {
    console.error('Magic link authentication error:', error)
    // Remove auth_token from URL on error
    const { auth_token, ...otherParams } = route.query
    router.replace({ query: otherParams })
  }
})
