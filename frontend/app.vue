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

    <!-- Feedback Popup -->
    <FeedbackPopup
      :show="showFeedbackPopup"
      :trigger-type="feedbackTriggerType"
      @close="closeFeedbackPopup"
      @submitted="handleFeedbackSubmitted"
    />

    <!-- Welcome Guide Popup (shows after onboarding/interests) -->
    <WelcomeGuidePopup
      :show="showWelcomeGuide"
      @close="showWelcomeGuide = false"
      @started="handleWelcomeGuideStarted"
    />

    <!-- Floating Feedback Button (for logged-in users) -->
    <FloatingFeedbackButton @open-feedback="openFeedbackManually" />

    <!-- Floating Camera Button (for mobile product photo capture) -->
    <FloatingCameraButton />
  </div>
</template>

<script setup lang="ts">
// Global app setup
const colorMode = useColorMode()
const { user, checkAuth } = useAuth()
const { get } = useApi()

const showOnboardingModal = ref(false)
const showInterestPopup = ref(false)
const isNewUserForInterest = ref(false)

// Feedback state
const showFeedbackPopup = ref(false)
const feedbackTriggerType = ref('manual')
const hasGivenFeedback = ref(false)
const feedbackChecked = ref(false)

// Welcome Guide state
const showWelcomeGuide = ref(false)

// Check auth and onboarding status on mount
onMounted(async () => {
  await checkAuth()

  // Check if user has already set preferences (backup check for onboarding)
  const hasExistingPreferences = () => {
    if (!user.value) return false
    const preferences = user.value.preferences as Record<string, any> | null
    return preferences?.grocery_interests && preferences.grocery_interests.length > 0
  }

  // Show onboarding modal if user is logged in but hasn't completed onboarding
  // AND doesn't already have preferences (safety check)
  if (user.value && !user.value.onboarding_completed && !hasExistingPreferences()) {
    setTimeout(() => {
      showOnboardingModal.value = true
    }, 1000) // Delay 1 second to let the page load
  } else if (user.value) {
    // Check if we should show interest popup after onboarding is complete
    checkInterestPopup()

    // For existing users: show welcome guide if they haven't seen it
    // Only if they have grocery interests (interest popup won't show)
    const preferences = user.value.preferences as Record<string, any> | null
    if (preferences?.grocery_interests && preferences.grocery_interests.length > 0) {
      // User has interests, they won't see the interest popup, so check welcome guide
      setTimeout(() => {
        checkWelcomeGuide()
      }, 2000)
    }
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
  // Check if user has already set preferences (backup check)
  const hasExistingPreferences = () => {
    if (!newUser) return false
    const preferences = newUser.preferences as Record<string, any> | null
    return preferences?.grocery_interests && preferences.grocery_interests.length > 0
  }

  if (newUser && !newUser.onboarding_completed && !showOnboardingModal.value && !hasExistingPreferences()) {
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
  // Show welcome guide after interest selection (for new users)
  if (isNewUserForInterest.value) {
    setTimeout(() => {
      checkWelcomeGuide()
    }, 1000)
  }
}

function handleInterestSkip() {
  showInterestPopup.value = false
  // Even if skipped, show welcome guide for new users
  if (isNewUserForInterest.value) {
    setTimeout(() => {
      checkWelcomeGuide()
    }, 1000)
  }
}

// Welcome Guide logic - show for users who haven't seen it
function checkWelcomeGuide() {
  if (!user.value) return

  // Check if user has already seen the welcome guide
  if (user.value.welcome_guide_seen) {
    return
  }

  // Show the welcome guide
  showWelcomeGuide.value = true
}

function handleWelcomeGuideStarted() {
  // Refresh user data to update welcome_guide_seen flag
  checkAuth()
}

// ==================== FEEDBACK LOGIC ====================

// Check if user has visited moji-proizvodi
function hasVisitedMojiProizvodi(): boolean {
  if (!process.client) return false
  return localStorage.getItem('visited_moji_proizvodi') === 'true'
}

// Check if user has visited /proizvodi
function hasVisitedProizvodi(): boolean {
  if (!process.client) return false
  return localStorage.getItem('visited_proizvodi') === 'true'
}

// Check if user has set preferences
function hasPreferences(): boolean {
  if (!user.value) return false
  const preferences = user.value.preferences as Record<string, any> | null
  return !!(preferences?.grocery_interests && preferences.grocery_interests.length > 0)
}

// Check if we should show feedback popup for logged-in users
async function checkFeedbackStatus() {
  if (!user.value || feedbackChecked.value || hasGivenFeedback.value) return

  // PRECONDITION 1: User must have set preferences
  if (!hasPreferences()) {
    return
  }

  // PRECONDITION 2: User must have visited moji-proizvodi
  if (!hasVisitedMojiProizvodi()) {
    return
  }

  // PRECONDITION 3: User must have visited /proizvodi
  if (!hasVisitedProizvodi()) {
    return
  }

  // Check localStorage first
  if (process.client && localStorage.getItem('feedback_submitted')) {
    hasGivenFeedback.value = true
    feedbackChecked.value = true
    return
  }

  try {
    const response = await get('/api/feedback/check')
    feedbackChecked.value = true

    if (response.has_given_feedback) {
      hasGivenFeedback.value = true
      localStorage.setItem('feedback_submitted', 'true')
      return
    }

    // Show popup if credits trigger OR random chance (20%)
    const shouldShowRandom = Math.random() < 0.2 // 20% chance

    if (response.show_feedback || shouldShowRandom) {
      // Wait a bit before showing the popup
      setTimeout(() => {
        feedbackTriggerType.value = response.show_feedback ? 'credits_spent' : 'random'
        showFeedbackPopup.value = true
      }, 3000)
    }
  } catch (error) {
    console.error('Error checking feedback status:', error)
  }
}

function openFeedbackManually() {
  feedbackTriggerType.value = 'manual'
  showFeedbackPopup.value = true
}

function closeFeedbackPopup() {
  showFeedbackPopup.value = false
  // Store in localStorage to avoid showing again in this session (for anonymous trigger)
  if (feedbackTriggerType.value === 'scroll_bottom') {
    localStorage.setItem('feedback_popup_dismissed', 'true')
  }
}

function handleFeedbackSubmitted() {
  hasGivenFeedback.value = true
  localStorage.setItem('feedback_submitted', 'true')
}

// Expose function for anonymous scroll trigger (called from index.vue)
function showAnonymousFeedback() {
  // Check if already dismissed or submitted
  if (localStorage.getItem('feedback_popup_dismissed') || localStorage.getItem('feedback_submitted')) {
    return
  }
  feedbackTriggerType.value = 'scroll_bottom'
  showFeedbackPopup.value = true
}

// Make it available globally for index.vue to call
if (process.client) {
  (window as any).showAnonymousFeedback = showAnonymousFeedback
}

// Watch for user login to check feedback status
watch(user, async (newUser) => {
  if (newUser && !feedbackChecked.value) {
    // Delay to not overwhelm user right after login
    setTimeout(() => {
      checkFeedbackStatus()
    }, 5000)
  }
}, { immediate: true })
</script>
