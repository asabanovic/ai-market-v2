export default defineNuxtRouteMiddleware(async (to, from) => {
  const { isAuthenticated, authReady, checkAuth } = useAuth()

  // Wait for auth to be ready on client-side
  if (process.client && !authReady.value) {
    await checkAuth()
  }

  if (!isAuthenticated.value) {
    return navigateTo('/prijava')
  }
})
