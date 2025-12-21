<template>
  <div
    v-if="shouldShowBanner"
    class="bg-gradient-to-r from-yellow-50 to-amber-50 border-b border-yellow-200 py-2 px-4 shadow-sm"
  >
    <div class="max-w-7xl mx-auto">
      <!-- Desktop: horizontal layout -->
      <div class="hidden sm:flex items-center justify-center gap-4">
        <Icon name="mdi:email-alert" class="w-5 h-5 flex-shrink-0 text-yellow-600" />
        <p class="text-sm font-medium text-gray-700">
          Vaš email nije verifikovan. Provjerite inbox i kliknite na link za verifikaciju.
        </p>

        <button
          @click="resendEmail"
          :disabled="isSending || cooldownSeconds > 0"
          class="bg-yellow-600 text-white px-4 py-1.5 rounded-md text-sm font-medium hover:bg-yellow-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-sm"
        >
          <span v-if="isSending">Slanje...</span>
          <span v-else-if="cooldownSeconds > 0">Pošalji ponovo ({{ cooldownSeconds }}s)</span>
          <span v-else>Pošalji ponovo</span>
        </button>
        <button
          type="button"
          @click="dismissBanner"
          class="text-gray-500 hover:text-gray-700 transition-colors"
          title="Zatvori za danas"
        >
          <Icon name="mdi:close" class="w-5 h-5" />
        </button>
      </div>

      <!-- Mobile: stacked layout -->
      <div class="sm:hidden">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <Icon name="mdi:email-alert" class="w-5 h-5 flex-shrink-0 text-yellow-600" />
            <p class="text-sm font-medium text-gray-700">
              Email nije verifikovan
            </p>
          </div>
          <button
            type="button"
            @click="dismissBanner"
            class="text-gray-500 hover:text-gray-700 transition-colors"
            title="Zatvori za danas"
          >
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>
        </div>
        <div class="flex items-center gap-2">
          <p class="text-xs text-gray-600 flex-1">
            Provjerite inbox za link
          </p>
          <button
            @click="resendEmail"
            :disabled="isSending || cooldownSeconds > 0"
            class="bg-yellow-600 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-yellow-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-sm"
          >
            <span v-if="isSending">Slanje...</span>
            <span v-else-if="cooldownSeconds > 0">{{ cooldownSeconds }}s</span>
            <span v-else>Pošalji ponovo</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { user, resendVerificationEmail, refreshUser } = useAuth()
const { handleApiError, showSuccess } = useCreditsToast()

const isSending = ref(false)
const isDismissed = ref(false)
const cooldownSeconds = ref(0)
let cooldownInterval: NodeJS.Timeout | null = null

// Show banner if user is logged in, has email registration method, and is not verified
const shouldShowBanner = computed(() => {
  console.log('EmailVerificationBanner - user:', user.value)
  console.log('EmailVerificationBanner - is_verified:', user.value?.is_verified)
  console.log('EmailVerificationBanner - isDismissed:', isDismissed.value)
  if (!user.value) return false
  if (isDismissed.value) return false
  // Only show for email registrations that are not verified
  // Google and phone users are auto-verified, so is_verified should be true for them
  return user.value.is_verified === false
})

async function resendEmail() {
  if (isSending.value || cooldownSeconds.value > 0) return

  isSending.value = true

  try {
    const response = await resendVerificationEmail()

    if (response.success) {
      showSuccess('Email za verifikaciju je poslan! Provjerite vaš inbox.')
      // Start cooldown
      startCooldown(60)
    } else {
      handleApiError(response.error || 'Greška pri slanju emaila')
    }
  } catch (error: any) {
    console.error('Resend verification error:', error)
    handleApiError(error.message || 'Greška pri slanju emaila za verifikaciju')
  } finally {
    isSending.value = false
  }
}

function startCooldown(seconds: number) {
  cooldownSeconds.value = seconds

  if (cooldownInterval) {
    clearInterval(cooldownInterval)
  }

  cooldownInterval = setInterval(() => {
    cooldownSeconds.value--
    if (cooldownSeconds.value <= 0) {
      if (cooldownInterval) {
        clearInterval(cooldownInterval)
        cooldownInterval = null
      }
    }
  }, 1000)
}

function dismissBanner() {
  isDismissed.value = true
  // Store dismissal with today's date in localStorage
  if (process.client) {
    const today = new Date().toDateString()
    localStorage.setItem('emailVerificationBannerDismissedDate', today)
  }
}

// Check if banner was dismissed today
onMounted(() => {
  if (process.client) {
    const dismissedDate = localStorage.getItem('emailVerificationBannerDismissedDate')
    const today = new Date().toDateString()

    // Only keep dismissed if it was dismissed today
    if (dismissedDate === today) {
      isDismissed.value = true
    } else {
      // Clear old dismissal if it's a new day
      localStorage.removeItem('emailVerificationBannerDismissedDate')
      isDismissed.value = false
    }
  }
})

onUnmounted(() => {
  if (cooldownInterval) {
    clearInterval(cooldownInterval)
  }
})
</script>
