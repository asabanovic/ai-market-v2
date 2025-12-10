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

    <!-- Interest Popup (for grocery preferences) -->
    <InterestPopup
      :show="showInterestPopup"
      :is-new-user="isNewUserForInterest"
      @close="showInterestPopup = false"
      @complete="handleInterestComplete"
      @skip="handleInterestSkip"
    />

    <!-- Floating Interest Button -->
    <FloatingInterestButton @click="openInterestPopup" />
  </div>
</template>

<script setup lang="ts">
// Global app setup
const colorMode = useColorMode()
const { user, checkAuth } = useAuth()

const showOnboardingModal = ref(false)
const showInterestPopup = ref(false)
const isNewUserForInterest = ref(false)

// Check auth and onboarding status on mount
onMounted(async () => {
  await checkAuth()

  // Show onboarding modal if user is logged in but hasn't completed onboarding
  if (user.value && !user.value.onboarding_completed) {
    setTimeout(() => {
      showOnboardingModal.value = true
    }, 1000) // Delay 1 second to let the page load
  } else if (user.value) {
    // Check if we should show interest popup after onboarding is complete
    checkInterestPopup()
  }

  // Listen for custom event to open interest popup from other pages
  if (process.client) {
    window.addEventListener('open-interest-popup', openInterestPopup)
  }
})

// Cleanup event listener
onUnmounted(() => {
  if (process.client) {
    window.removeEventListener('open-interest-popup', openInterestPopup)
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

  // After onboarding, show interest popup if not completed
  setTimeout(() => {
    isNewUserForInterest.value = true
    checkInterestPopup()
  }, 1500)
}

function handleStoresSelected(storeIds: number[]) {
  // Store preferences have been saved via API in OnboardingModal
  // The page will reload when onboarding is complete to pick up the new preferences
  console.log('Stores selected during onboarding:', storeIds)
}

// Interest popup logic - show for new users who haven't set interests yet
function checkInterestPopup() {
  if (!user.value) return

  // Check if user already has grocery interests in database
  const preferences = user.value.preferences as Record<string, any> | null
  if (preferences?.grocery_interests && preferences.grocery_interests.length > 0) {
    // User already has interests set, don't auto-show popup
    return
  }

  // Show popup after a short delay for users without interests
  setTimeout(() => {
    showInterestPopup.value = true
  }, 2000)
}

function openInterestPopup() {
  isNewUserForInterest.value = false
  showInterestPopup.value = true
}

function handleInterestComplete() {
  showInterestPopup.value = false
  // Refresh user data
  checkAuth()
}

function handleInterestSkip() {
  showInterestPopup.value = false
}
</script>
