<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100] p-4 overflow-y-auto" @click.self="$emit('close')">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md md:max-w-xl lg:max-w-2xl p-6 md:p-8 relative animate-slide-up my-auto max-h-[90vh] overflow-y-auto">
          <!-- Close button -->
          <button
            @click="$emit('close')"
            class="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors p-1"
          >
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>

          <!-- Header -->
          <div class="text-center mb-6">
            <img
              src="/logo.png"
              alt="Popust.ba"
              class="w-20 h-20 mx-auto mb-3 object-contain"
            />
            <h2 class="text-xl font-bold text-gray-900 mb-2">
              {{ isNewUser ? 'Dobrodošli na Popust.ba!' : 'Ovo je najvažniji korak!' }}
            </h2>
            <div class="bg-purple-50 border border-purple-200 rounded-lg p-3 text-left">
              <p class="text-purple-900 text-sm font-medium mb-1">
                🎯 Ovo je razlog zašto ste ovdje!
              </p>
              <p class="text-purple-700 text-sm">
                Recite nam koje namirnice kupujete, a mi ćemo vas <strong>obavijestiti čim budu na popustu</strong> u vašem gradu.
              </p>
            </div>
          </div>

          <!-- Form -->
          <form @submit.prevent="submitForm">
            <!-- Phone Number -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1.5">
                <Icon name="mdi:phone" class="w-4 h-4 inline mr-1" />
                Broj telefona
              </label>
              <input
                v-model="form.phone"
                type="tel"
                placeholder="+387 6X XXX XXX"
                class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900"
                :class="{ 'border-red-300': phoneError }"
                @input="handlePhoneInput"
              />
              <p v-if="phoneError" class="mt-1 text-xs text-red-500">{{ phoneError }}</p>
            </div>

            <!-- Grocery Interests -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1.5">
                <Icon name="mdi:cart" class="w-4 h-4 inline mr-1" />
                Koje namirnice najčešće kupujete?
              </label>

              <!-- Quick Select Chips -->
              <div class="flex flex-wrap gap-2 mb-3">
                <button
                  v-for="item in suggestedItems"
                  :key="item"
                  type="button"
                  @click="toggleSuggestion(item)"
                  class="px-3 py-1.5 text-sm rounded-full border transition-all"
                  :class="selectedSuggestions.includes(item)
                    ? 'bg-purple-600 text-white border-purple-600'
                    : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-purple-300 hover:bg-purple-50'"
                >
                  {{ item }}
                </button>
              </div>

              <!-- Custom Input -->
              <textarea
                v-model="form.customInterests"
                rows="4"
                placeholder="Upišite dodatne proizvode koje kupujete, odvojene zarezom:&#10;npr. jogurt, sok, keks, maslac, tjestenina..."
                class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900 text-sm resize-y min-h-[100px]"
              ></textarea>
              <p class="mt-1 text-xs text-gray-500">
                Pratit ćemo cijene i obavijestiti vas kada budu na akciji
              </p>
            </div>

            <!-- Error message -->
            <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-sm text-red-600">{{ error }}</p>
            </div>

            <!-- Benefits reminder -->
            <div class="bg-purple-50 rounded-lg p-3 mb-4">
              <div class="flex items-start gap-2">
                <Icon name="mdi:gift" class="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                <div class="text-sm">
                  <p class="font-medium text-purple-900">Zašto ovo popuniti?</p>
                  <ul class="text-purple-700 mt-1 space-y-0.5">
                    <li>• Personalizirane obavijesti o popustima</li>
                    <li>• Brže pronalaženje proizvoda</li>
                    <li>• Nikada ne propustite akciju</li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- Buttons -->
            <div class="flex gap-3">
              <button
                type="button"
                @click="skipForNow"
                class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Preskoči
              </button>
              <button
                type="submit"
                :disabled="isSubmitting"
                class="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Icon v-if="isSubmitting" name="mdi:loading" class="w-4 h-4 animate-spin" />
                {{ isSubmitting ? 'Spremam...' : 'Sačuvaj' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  show: boolean
  isNewUser?: boolean
}>()

const emit = defineEmits(['close', 'complete', 'skip'])

const { post, put } = useApi()
const { user, checkAuth } = useAuth()

// Suggested grocery items (common in Bosnia)
const suggestedItems = [
  'Mlijeko',
  'Hljeb',
  'Jaja',
  'Piletina',
  'Mljeveno meso',
  'Kafa',
  'Deterdžent',
  'Jogurt',
  'Sir',
  'Šećer',
  'Ulje',
  'Brašno'
]

const selectedSuggestions = ref<string[]>([])
const form = ref({
  phone: '',
  customInterests: ''
})

const isSubmitting = ref(false)
const error = ref('')
const phoneError = ref('')

// Pre-fill form with existing user data when popup opens
watch(() => props.show, (show) => {
  if (show && user.value) {
    // Pre-fill phone
    if (user.value.phone) {
      form.value.phone = user.value.phone
    }

    // Pre-fill grocery interests from database
    const preferences = user.value.preferences as Record<string, any> | null
    if (preferences?.grocery_interests && Array.isArray(preferences.grocery_interests)) {
      const existingInterests = preferences.grocery_interests as string[]

      // Separate into suggested items (chips) and custom items (textarea)
      const suggestedSet = new Set(suggestedItems.map(s => s.toLowerCase()))
      const matchedSuggestions: string[] = []
      const customItems: string[] = []

      existingInterests.forEach(interest => {
        // Check if this interest matches any suggested item (case-insensitive)
        const matchedSuggestion = suggestedItems.find(s => s.toLowerCase() === interest.toLowerCase())
        if (matchedSuggestion) {
          matchedSuggestions.push(matchedSuggestion)
        } else {
          customItems.push(interest)
        }
      })

      selectedSuggestions.value = matchedSuggestions
      form.value.customInterests = customItems.join(', ')
    } else {
      // Reset if no existing interests
      selectedSuggestions.value = []
      form.value.customInterests = ''
    }
  }
}, { immediate: true })

function toggleSuggestion(item: string) {
  const index = selectedSuggestions.value.indexOf(item)
  if (index > -1) {
    selectedSuggestions.value.splice(index, 1)
  } else {
    selectedSuggestions.value.push(item)
  }
}

function handlePhoneInput() {
  form.value.phone = form.value.phone.replace(/[^\d\+\s\-\(\)]/g, '')
  validatePhone()
}

function validatePhone(): boolean {
  const phone = form.value.phone.trim()

  if (!phone) {
    phoneError.value = ''
    return true
  }

  const cleanPhone = phone.replace(/[\s\-\(\)]/g, '')

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
    phoneError.value = 'Unesite ispravan broj telefona'
    return false
  }

  phoneError.value = ''
  return true
}

async function submitForm() {
  if (!validatePhone()) return

  // Combine selected suggestions with custom input
  const allInterests = [
    ...selectedSuggestions.value,
    ...form.value.customInterests.split(',').map(s => s.trim()).filter(s => s)
  ]

  if (allInterests.length === 0 && !form.value.phone) {
    error.value = 'Molimo unesite broj telefona ili odaberite barem jednu namirnicu'
    return
  }

  isSubmitting.value = true
  error.value = ''

  try {
    const result = await put('/auth/user/interests', {
      phone: form.value.phone || undefined,
      grocery_interests: allInterests
    })

    // Refresh user data to get updated preferences
    await checkAuth()

    // If processing was started, redirect to moji-proizvodi with processing flag
    if (result.processing_started) {
      emit('complete')
      // Navigate to moji-proizvodi with a query param to trigger processing notification
      navigateTo('/moji-proizvodi?processing=true')
    } else {
      emit('complete')
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Došlo je do greške'
  } finally {
    isSubmitting.value = false
  }
}

function skipForNow() {
  // Just close the popup
  emit('skip')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.animate-slide-up {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
