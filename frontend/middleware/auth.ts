export default defineNuxtRouteMiddleware(async (to, from) => {
  // Only run auth check on client-side to prevent hydration mismatch
  // Server doesn't have access to localStorage where token is stored
  if (process.server) {
    return
  }

  const { isAuthenticated, authReady, checkAuth } = useAuth()

  // Wait for auth to be ready on client-side
  if (!authReady.value) {
    await checkAuth()
  }

  if (!isAuthenticated.value) {
    // Pass the original path as redirect query parameter
    return navigateTo({
      path: '/prijava',
      query: { redirect: to.fullPath }
    })
  }
})
