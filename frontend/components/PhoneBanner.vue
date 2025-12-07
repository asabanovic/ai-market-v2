<template>
  <div
    v-if="shouldShowBanner"
    class="bg-gradient-to-r from-orange-50 to-amber-50 border-b border-orange-100 py-2 px-4 shadow-sm"
  >
    <div class="max-w-7xl mx-auto">
      <!-- Desktop: horizontal layout -->
      <div class="hidden sm:flex items-center justify-center gap-4">
        <Icon name="mdi:phone" class="w-5 h-5 flex-shrink-0 text-orange-600" />
        <p class="text-sm font-medium text-gray-700">
          Dodajte vaš broj telefona za SMS notifikacije o popustima
        </p>

        <form @submit.prevent="savePhoneNumber" class="flex items-center gap-2">
          <div class="relative">
            <input
              v-model="phoneNumber"
              type="tel"
              placeholder="+387 XX XXX XXX"
              :class="[
                'px-3 py-1.5 text-sm rounded-md border-2 text-gray-900 focus:outline-none w-48',
                phoneNumber && !isValid ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-orange-200 focus:ring-orange-500 focus:border-orange-500'
              ]"
              :disabled="isSaving"
              @input="formatPhoneNumber"
              @blur="validatePhoneNumber"
              maxlength="20"
            />
            <div v-if="phoneNumber && isValid" class="absolute right-2 top-1/2 -translate-y-1/2">
              <Icon name="mdi:check-circle" class="w-4 h-4 text-green-500" />
            </div>
          </div>
          <button
            type="submit"
            :disabled="isSaving || !phoneNumber || !isValid"
            class="bg-orange-600 text-white px-4 py-1.5 rounded-md text-sm font-medium hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-sm"
          >
            {{ isSaving ? 'Čuvanje...' : 'Sačuvaj' }}
          </button>
          <button
            type="button"
            @click="dismissBanner"
            class="text-gray-500 hover:text-gray-700 transition-colors"
            title="Zatvori za danas"
          >
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>
        </form>
      </div>

      <!-- Mobile: stacked layout -->
      <div class="sm:hidden">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <Icon name="mdi:phone" class="w-5 h-5 flex-shrink-0 text-orange-600" />
            <p class="text-sm font-medium text-gray-700">
              SMS notifikacije o popustima
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
        <form @submit.prevent="savePhoneNumber" class="flex items-center gap-2">
          <div class="relative flex-1">
            <input
              v-model="phoneNumber"
              type="tel"
              placeholder="+387 XX XXX XXX"
              :class="[
                'w-full px-3 py-1.5 text-sm rounded-md border-2 text-gray-900 focus:outline-none',
                phoneNumber && !isValid ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-orange-200 focus:ring-orange-500 focus:border-orange-500'
              ]"
              :disabled="isSaving"
              @input="formatPhoneNumber"
              @blur="validatePhoneNumber"
              maxlength="20"
            />
            <div v-if="phoneNumber && isValid" class="absolute right-2 top-1/2 -translate-y-1/2">
              <Icon name="mdi:check-circle" class="w-4 h-4 text-green-500" />
            </div>
          </div>
          <button
            type="submit"
            :disabled="isSaving || !phoneNumber || !isValid"
            class="bg-orange-600 text-white px-4 py-1.5 rounded-md text-sm font-medium hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-sm"
          >
            {{ isSaving ? 'Čuvanje...' : 'Sačuvaj' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { user, refreshUser } = useAuth()
const { post } = useApi()
const { handleApiError, showSuccess } = useCreditsToast()

const phoneNumber = ref('')
const isSaving = ref(false)
const isDismissed = ref(false)
const isValid = ref(false)

// Only show banner if user is logged in and doesn't have a phone number
const shouldShowBanner = computed(() => {
  return user.value && !user.value.phone && !isDismissed.value
})

// Format phone number as user types
function formatPhoneNumber(event: any) {
  let value = event.target.value

  // Remove all non-digit characters except +
  value = value.replace(/[^\d+]/g, '')

  // Ensure it starts with +
  if (value && !value.startsWith('+')) {
    value = '+' + value
  }

  // Limit to reasonable phone number length
  if (value.length > 20) {
    value = value.substring(0, 20)
  }

  phoneNumber.value = value

  // Validate on every input
  validatePhoneNumber()
}

// Validate phone number
function validatePhoneNumber() {
  const value = phoneNumber.value.trim()

  if (!value) {
    isValid.value = false
    return
  }

  // Basic international phone number validation
  // Must start with + and have at least 8 digits total (e.g., +38761234567 = 12 chars)
  const phoneRegex = /^\+\d{8,19}$/

  const isValidFormat = phoneRegex.test(value)
  isValid.value = isValidFormat

  console.log('Validating phone:', value, 'Valid:', isValidFormat)
}

async function savePhoneNumber() {
  if (!phoneNumber.value.trim()) {
    console.log('Phone number is empty')
    return
  }

  if (!isValid.value) {
    console.log('Phone number is not valid:', phoneNumber.value)
    handleApiError('Molimo unesite ispravan broj telefona u formatu +387XXXXXXXXX')
    return
  }

  console.log('Saving phone number:', phoneNumber.value)
  isSaving.value = true

  try {
    const response = await post('/auth/user/phone', {
      phone: phoneNumber.value
    })

    console.log('Phone save response:', response)

    if (response.success) {
      showSuccess('Broj telefona je uspješno sačuvan!')
      // Refresh user data to update the phone number
      await refreshUser()
      phoneNumber.value = ''
    } else {
      handleApiError(response.error || 'Greška pri čuvanju broja telefona')
    }
  } catch (error: any) {
    console.error('Phone save error:', error)
    handleApiError(error.message || 'Greška pri čuvanju broja telefona')
  } finally {
    isSaving.value = false
  }
}

function dismissBanner() {
  isDismissed.value = true
  // Store dismissal with today's date in localStorage
  if (process.client) {
    const today = new Date().toDateString()
    localStorage.setItem('phoneBannerDismissedDate', today)
  }
}

// Check if banner was dismissed today
onMounted(() => {
  if (process.client) {
    const dismissedDate = localStorage.getItem('phoneBannerDismissedDate')
    const today = new Date().toDateString()

    // Only keep dismissed if it was dismissed today
    if (dismissedDate === today) {
      isDismissed.value = true
    } else {
      // Clear old dismissal if it's a new day
      localStorage.removeItem('phoneBannerDismissedDate')
      isDismissed.value = false
    }
  }
})
</script>
