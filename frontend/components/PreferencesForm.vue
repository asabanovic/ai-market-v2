<template>
  <div>
    <!-- Header -->
    <div class="text-center mb-6">
      <h2 class="text-xl md:text-2xl font-bold text-gray-900 mb-2">
        Recite nam šta kupujete
      </h2>
      <p class="text-gray-600 text-sm">
        To traje 10 sekundi — mi Vas obavijestimo čim bude na popustu u Vašem gradu.
      </p>
    </div>

    <!-- Form -->
    <form @submit.prevent="handleSubmit">
      <!-- Grocery Interests - Quick Select Chips -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Brzi odabir
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="item in suggestedItems"
            :key="item"
            type="button"
            @click="toggleChip(item)"
            class="px-3 py-1.5 text-sm rounded-full border transition-all"
            :class="selectedChips.includes(item)
              ? 'bg-purple-600 text-white border-purple-600'
              : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-purple-300 hover:bg-purple-50'"
          >
            {{ item }}
          </button>
        </div>
      </div>

      <!-- Custom Products Textarea -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1.5">
          Dodajte svoje
        </label>
        <textarea
          v-model="customProducts"
          rows="3"
          placeholder="Npr: mlijeko, kafa, deterdžent, Nutella, Milka, Ariel… (brendovi su OK)"
          class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900 text-sm resize-none"
          @input="handleTextInput"
        ></textarea>
        <p class="mt-1 text-xs text-gray-500">
          Dovoljno je 3–5 stvari. Dodajte i brendove koje često kupujete.
        </p>
      </div>

      <!-- Phone Number (Optional) - BELOW preferences -->
      <div class="mb-5">
        <label class="block text-sm font-medium text-gray-700 mb-1.5">
          Broj telefona (opciono)
        </label>
        <input
          v-model="phone"
          type="tel"
          placeholder="+387 6X XXX XXX"
          class="w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900"
          :class="phoneError ? 'border-red-300' : 'border-gray-300'"
          @input="handlePhoneInput"
        />
        <p v-if="phoneError" class="mt-1 text-xs text-red-500">{{ phoneError }}</p>
        <p v-else class="mt-1 text-xs text-gray-500">
          Za sada obavijesti stižu na email. Telefon ostavite samo ako želite kasnije SMS/Viber.
        </p>
      </div>

      <!-- Error message -->
      <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-600">{{ error }}</p>
      </div>

      <!-- Buttons -->
      <div class="flex gap-3">
        <button
          v-if="showBackButton"
          type="button"
          @click="$emit('back')"
          class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Nazad
        </button>
        <button
          v-if="showSkipButton"
          type="button"
          @click="handleSkip"
          class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Preskoči
        </button>
        <button
          type="submit"
          :disabled="isSubmitting"
          class="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Icon v-if="isSubmitting" name="mdi:loading" class="w-4 h-4 animate-spin" />
          {{ isSubmitting ? 'Čuvam...' : 'Sačuvaj i pokaži ponude' }}
        </button>
      </div>

      <!-- Reassurance text -->
      <p class="text-center text-xs text-gray-500 mt-4">
        Možete promijeniti ili obrisati listu bilo kada.
      </p>
    </form>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  showSkipButton?: boolean
  showBackButton?: boolean
  source?: 'onboarding' | 'profile'
  initialPhone?: string
  initialInterests?: string[]
}>()

const emit = defineEmits(['complete', 'skip', 'back'])

const { put, post } = useApi()
const { user, checkAuth } = useAuth()

// Default chips to auto-select for new users
const defaultChips = ['Mlijeko', 'Hljeb', 'Jaja', 'Kafa', 'Deterdžent']

// All suggested items (common in Bosnia)
const suggestedItems = [
  'Mlijeko',
  'Hljeb',
  'Jaja',
  'Kafa',
  'Deterdžent',
  'Jogurt',
  'Sir',
  'Šećer',
  'Ulje',
  'Brašno',
  'Piletina',
  'Mljeveno meso'
]

const selectedChips = ref<string[]>([])
const customProducts = ref('')
const phone = ref('')
const phoneError = ref('')
const error = ref('')
const isSubmitting = ref(false)
const hasInitialized = ref(false)

// Track when form is shown
onMounted(() => {
  trackEvent('preferences_shown', { source: props.source || 'unknown' })
  initializeForm()
})

function initializeForm() {
  if (hasInitialized.value) return
  hasInitialized.value = true

  // Initialize phone
  phone.value = props.initialPhone || user.value?.phone || ''

  // Initialize interests
  const existingInterests = props.initialInterests ||
    (user.value?.preferences as Record<string, any>)?.grocery_interests || []

  if (existingInterests.length > 0) {
    // User has existing interests - load them
    const suggestedSet = new Set(suggestedItems.map(s => s.toLowerCase()))
    const matchedChips: string[] = []
    const customItems: string[] = []

    existingInterests.forEach((interest: string) => {
      const matchedSuggestion = suggestedItems.find(s => s.toLowerCase() === interest.toLowerCase())
      if (matchedSuggestion) {
        matchedChips.push(matchedSuggestion)
      } else {
        customItems.push(interest)
      }
    })

    selectedChips.value = matchedChips
    customProducts.value = customItems.join(', ')
  } else {
    // New user - auto-select default chips
    selectedChips.value = [...defaultChips]
    customProducts.value = ''
  }
}

function toggleChip(item: string) {
  const index = selectedChips.value.indexOf(item)
  if (index > -1) {
    selectedChips.value.splice(index, 1)
  } else {
    selectedChips.value.push(item)
  }
}

// Auto-match text to chips
function handleTextInput() {
  const text = customProducts.value.toLowerCase()
  const words = text.split(/[,\s]+/).map(w => w.trim()).filter(w => w.length > 2)

  // Check if any typed words match suggested items
  suggestedItems.forEach(item => {
    const itemLower = item.toLowerCase()
    if (words.some(word => itemLower.includes(word) || word.includes(itemLower))) {
      // Auto-select the chip if text matches
      if (!selectedChips.value.includes(item)) {
        selectedChips.value.push(item)
        // Remove the matched word from textarea to avoid duplication
        const regex = new RegExp(`\\b${item}\\b`, 'gi')
        customProducts.value = customProducts.value.replace(regex, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '').trim()
      }
    }
  })
}

function handlePhoneInput() {
  phone.value = phone.value.replace(/[^\d\+\s\-\(\)]/g, '')
  validatePhone()
}

function validatePhone(): boolean {
  const phoneVal = phone.value.trim()

  // Empty is OK (field is optional)
  if (!phoneVal) {
    phoneError.value = ''
    return true
  }

  const cleanPhone = phoneVal.replace(/[\s\-\(\)]/g, '')

  const patterns = [
    /^\+3876\d{7,8}$/,
    /^003876\d{7,8}$/,
    /^06\d{7,8}$/,
    /^\+3873\d{7,8}$/,
    /^003873\d{7,8}$/,
    /^03\d{7,8}$/,
  ]

  const isValid = patterns.some(pattern => pattern.test(cleanPhone))

  if (!isValid) {
    phoneError.value = 'Unesite ispravan broj telefona (npr. +387 61 234 567)'
    return false
  }

  phoneError.value = ''
  return true
}

async function handleSubmit() {
  if (!validatePhone()) return

  // Combine chips with custom input
  const customList = customProducts.value
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)

  const allInterests = [...new Set([...selectedChips.value, ...customList])]

  isSubmitting.value = true
  error.value = ''

  try {
    const result = await put('/auth/user/interests', {
      phone: phone.value || undefined,
      grocery_interests: allInterests
    })

    // Track save event
    trackEvent('preferences_saved', {
      source: props.source || 'unknown',
      terms_count: allInterests.length,
      chips_count: selectedChips.value.length,
      phone_provided: !!phone.value.trim()
    })

    // If onboarding, also mark onboarding as completed
    if (props.source === 'onboarding') {
      try {
        await post('/auth/user/onboarding', {
          phone: phone.value || '',
          typical_products: allInterests.join(', ')
        })
      } catch (err) {
        // Ignore errors - interests were saved successfully
        console.error('Error marking onboarding complete:', err)
      }
    }

    // Refresh user data
    await checkAuth()

    // If processing started (new interests added), handle navigation/polling
    if (result.processing_started) {
      if (props.source === 'onboarding') {
        // Onboarding: navigate to moji-proizvodi with processing flag
        navigateTo('/moji-proizvodi?processing=true')
      } else {
        // Profile editing: emit complete with processing flag so parent can poll
        emit('complete', { processing_started: true })
        return
      }
    } else {
      if (props.source === 'onboarding') {
        navigateTo('/moji-proizvodi')
      }
    }

    emit('complete', { processing_started: false })
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Došlo je do greške prilikom čuvanja'
  } finally {
    isSubmitting.value = false
  }
}

async function handleSkip() {
  // Track skip event
  trackEvent('preferences_skipped', {
    source: props.source || 'unknown'
  })

  // If onboarding, mark as completed
  if (props.source === 'onboarding') {
    try {
      await post('/auth/user/onboarding', {
        phone: '',
        typical_products: ''
      })
    } catch (err) {
      // Ignore errors
    }
  }

  emit('skip')
}

function trackEvent(event: string, data: Record<string, any>) {
  // Console log for now (can be replaced with analytics SDK later)
  console.log(`[Preferences] ${event}:`, data)

  // Also send to backend for logging
  try {
    post('/api/user/track-event', {
      event,
      data,
      timestamp: new Date().toISOString()
    }).catch(() => {
      // Silent fail - don't disrupt UX
    })
  } catch {
    // Ignore
  }
}
</script>
