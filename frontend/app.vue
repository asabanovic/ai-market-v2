<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <!-- Onboarding Modal -->
    <OnboardingModal
      :show="showOnboardingModal"
      @close="showOnboardingModal = false"
      @complete="handleOnboardingComplete"
      @storesSelected="handleStoresSelected"
    />
  </div>
</template>

<script setup lang="ts">
// Global app setup
const colorMode = useColorMode()
const { user, checkAuth } = useAuth()

const showOnboardingModal = ref(false)

// Check auth and onboarding status on mount
onMounted(async () => {
  await checkAuth()

  // Show onboarding modal if user is logged in but hasn't completed onboarding
  if (user.value && !user.value.onboarding_completed) {
    setTimeout(() => {
      showOnboardingModal.value = true
    }, 1000) // Delay 1 second to let the page load
  }
})

// Watch user changes to show modal after login
watch(user, (newUser) => {
  if (newUser && !newUser.onboarding_completed && !showOnboardingModal.value) {
    setTimeout(() => {
      showOnboardingModal.value = true
    }, 500)
  }
})

function handleOnboardingComplete() {
  showOnboardingModal.value = false
  // Refresh user data to update onboarding_completed flag
  checkAuth()
  // Reload page to refresh store preferences on homepage
  if (process.client) {
    window.location.reload()
  }
}

function handleStoresSelected(storeIds: number[]) {
  // Store preferences have been saved via API in OnboardingModal
  // The page will reload when onboarding is complete to pick up the new preferences
  console.log('Stores selected during onboarding:', storeIds)
}
</script>
