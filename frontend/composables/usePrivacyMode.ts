/**
 * Privacy Mode - Blur PII data for screen sharing/demos
 * Only available to admin users
 *
 * Usage: Add data-pii attribute to any element containing PII
 * Example: <span data-pii>user@email.com</span>
 */

const privacyModeEnabled = ref(false)

export function usePrivacyMode() {
  const { user } = useAuth()

  const isAdmin = computed(() => user.value?.is_admin === true)

  const togglePrivacyMode = () => {
    if (!isAdmin.value) return
    privacyModeEnabled.value = !privacyModeEnabled.value

    // Apply/remove class to body for CSS-based blurring
    if (typeof document !== 'undefined') {
      if (privacyModeEnabled.value) {
        document.body.classList.add('privacy-mode')
      } else {
        document.body.classList.remove('privacy-mode')
      }
    }
  }

  const setPrivacyMode = (enabled: boolean) => {
    if (!isAdmin.value) return
    privacyModeEnabled.value = enabled

    if (typeof document !== 'undefined') {
      if (enabled) {
        document.body.classList.add('privacy-mode')
      } else {
        document.body.classList.remove('privacy-mode')
      }
    }
  }

  return {
    privacyModeEnabled: readonly(privacyModeEnabled),
    isAdmin,
    togglePrivacyMode,
    setPrivacyMode
  }
}
