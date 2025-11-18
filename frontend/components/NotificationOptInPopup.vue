<template>
  <Teleport to="body">
    <div
      v-if="isVisible"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4"
      @click.self="handleDecline"
    >
      <div class="relative mx-auto p-6 border w-full max-w-md shadow-2xl rounded-xl bg-white" @click.stop>
        <!-- Close button -->
        <button
          @click="handleDecline"
          class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <Icon name="mdi:close" class="w-6 h-6" />
        </button>

        <!-- Icon -->
        <div class="flex justify-center mb-4">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center">
            <Icon name="mdi:bell-ring" class="w-8 h-8 text-white" />
          </div>
        </div>

        <!-- Content -->
        <div class="text-center mb-6">
          <h3 class="text-xl font-bold text-gray-900 mb-3">
            Primajte notifikacije o popustima!
          </h3>
          <p class="text-gray-600 text-sm leading-relaxed mb-4">
            Omogućite SMS i Viber notifikacije kako biste bili obaviješteni kada proizvodi koje pratite dobiju popust ili promijene cijenu.
          </p>
          <div class="bg-purple-50 border border-purple-200 rounded-lg p-4 text-left">
            <p class="text-sm text-purple-900 font-medium mb-2">Prednosti:</p>
            <ul class="text-sm text-purple-800 space-y-1">
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-4 h-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Budite prvi koji sazna za nove popuste</span>
              </li>
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-4 h-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Pratite cijene omiljenih proizvoda</span>
              </li>
              <li class="flex items-start">
                <Icon name="mdi:check-circle" class="w-4 h-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Uštedite više novca i vremena</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Phone Number Input (if not provided) -->
        <div v-if="!hasPhoneNumber" class="mb-6">
          <label for="phone-input" class="block text-sm font-medium text-gray-700 mb-2">
            Broj telefona
          </label>
          <div class="relative">
            <input
              id="phone-input"
              v-model="phoneNumber"
              type="tel"
              :class="[
                'w-full px-3 py-2 border-2 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none',
                phoneNumber && !isPhoneValid ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-purple-500 focus:border-purple-500'
              ]"
              placeholder="+387 XX XXX XXX"
              @input="formatPhoneNumber"
              @blur="validatePhone"
              maxlength="20"
            />
            <div v-if="phoneNumber && isPhoneValid" class="absolute right-3 top-1/2 -translate-y-1/2">
              <Icon name="mdi:check-circle" class="w-5 h-5 text-green-500" />
            </div>
          </div>
          <p class="mt-1 text-xs text-gray-500">Format: +387XXXXXXXXX (sa pozivnim brojem)</p>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col gap-3">
          <button
            @click="handleAccept"
            :disabled="isSaving || (!hasPhoneNumber && phoneNumber && !isPhoneValid)"
            class="w-full px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
          >
            {{ isSaving ? 'Čuvanje...' : (hasPhoneNumber ? 'Omogući notifikacije' : 'Sačuvaj i omogući') }}
          </button>
          <button
            @click="handleDecline"
            :disabled="isSaving"
            class="w-full px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Ne želim notifikacije
          </button>
        </div>

        <!-- Privacy Note -->
        <p class="mt-4 text-xs text-gray-500 text-center">
          Možete promijeniti ove postavke u bilo kojem trenutku na stranici vašeg profila.
        </p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const { put } = useApi()
const { user, refreshUser } = useAuth()

const isVisible = ref(false)
const isSaving = ref(false)
const phoneNumber = ref('')
const isPhoneValid = ref(true)

const hasPhoneNumber = computed(() => {
  return !!user.value?.phone
})

// Show popup for newly registered users who haven't set notification preferences
function checkAndShow() {
  if (!user.value) return

  // Check if user just registered (created within last 5 minutes) and hasn't set preferences
  const hasSetPreferences = localStorage.getItem('notification_preferences_set')
  const notificationPref = user.value.notification_preferences || 'none'

  if (!hasSetPreferences && notificationPref === 'none') {
    // Show popup after a short delay
    setTimeout(() => {
      isVisible.value = true
    }, 1000)
  }
}

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
  validatePhone()
}

function validatePhone() {
  const value = phoneNumber.value?.trim()

  if (!value) {
    isPhoneValid.value = true // Empty is valid
    return
  }

  // Basic international phone number validation
  const phoneRegex = /^\+\d{8,19}$/
  isPhoneValid.value = phoneRegex.test(value)
}

async function handleAccept() {
  isSaving.value = true

  try {
    const updateData: any = {
      notification_preferences: 'favorites'
    }

    // If phone number was provided and is valid, include it
    if (!hasPhoneNumber.value && phoneNumber.value) {
      if (!isPhoneValid.value) {
        return
      }
      updateData.phone = phoneNumber.value
    }

    await put('/auth/user/profile', updateData)

    // Mark as set in localStorage
    localStorage.setItem('notification_preferences_set', 'true')

    // Refresh user data
    await refreshUser()

    isVisible.value = false
  } catch (error) {
    console.error('Error saving notification preferences:', error)
  } finally {
    isSaving.value = false
  }
}

function handleDecline() {
  // Mark as set even if declined
  localStorage.setItem('notification_preferences_set', 'true')
  isVisible.value = false
}

// Expose method to parent components
defineExpose({
  checkAndShow
})

// Check on mount
onMounted(() => {
  checkAndShow()
})
</script>
