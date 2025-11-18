export default defineNuxtRouteMiddleware(async (to, from) => {
  const { isAuthenticated, user, checkAuth } = useAuth()

  // Ensure auth is checked before proceeding
  if (process.client && !user.value) {
    await checkAuth()
  }

  // If user is already logged in, redirect to home page
  if (isAuthenticated.value && user.value) {
    console.log('User is already logged in, redirecting to home')
    return navigateTo('/')
  }
})
