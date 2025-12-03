export default defineNuxtRouteMiddleware(async (to, from) => {
  // Only run on client-side to prevent hydration mismatch
  // Server doesn't have access to localStorage where token is stored
  if (process.server) {
    return
  }

  const { user, isAuthenticated, authReady, checkAuth } = useAuth()

  // Wait for auth to be ready on client-side
  if (!authReady.value) {
    await checkAuth()
  }

  if (!isAuthenticated.value) {
    return navigateTo({
      path: '/prijava',
      query: { redirect: to.fullPath }
    })
  }

  if (!user.value?.is_admin) {
    return navigateTo('/')
  }
})
