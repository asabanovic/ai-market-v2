export default defineNuxtRouteMiddleware((to, from) => {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated.value) {
    return navigateTo('/prijava')
  }

  if (!user.value?.is_admin) {
    return navigateTo('/')
  }
})
