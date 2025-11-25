export default defineNuxtRouteMiddleware(async (to, from) => {
  // Only run auth check on client-side to prevent hydration mismatch
  if (process.server) {
    return
  }

  const { isAuthenticated, user, checkAuth } = useAuth()

  // Ensure auth is checked before proceeding
  if (!user.value) {
    await checkAuth()
  }

  // If user is already logged in, redirect to intended page or home
  if (isAuthenticated.value && user.value) {
    const redirect = to.query.redirect as string
    if (redirect && redirect !== '/prijava' && redirect !== '/registracija') {
      return navigateTo(redirect)
    }
    return navigateTo('/')
  }
})
