<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-2xl">
      <!-- Header -->
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Registrujte se za 10 sekundi! 🚀
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Ili
          <NuxtLink to="/prijava" class="font-medium text-purple-600 hover:text-purple-500">
            se prijavite ako već imate račun
          </NuxtLink>
        </p>
      </div>

      <!-- Google OAuth Button - Primary -->
      <a
        :href="`${config.public.apiBase}/auth/google`"
        class="w-full flex items-center justify-center gap-3 py-3 px-4 border-2 border-purple-500 rounded-lg text-gray-700 bg-white hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all shadow-sm"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        <span class="font-medium">Registruj se sa Google</span>
      </a>

      <!-- Divider -->
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-white text-gray-500">Ili sa emailom</span>
        </div>
      </div>

      <!-- Phone Registration - Hidden for now -->
      <form v-if="registrationMethod === 'phone'" @submit.prevent="handlePhoneSubmit" class="space-y-6">
        <!-- Error/Success Messages -->
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-sm text-red-700">{{ errorMessage }}</p>
        </div>

        <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-md p-4">
          <p class="text-sm text-green-700">{{ successMessage }}</p>
        </div>

        <!-- Step 1: Enter Phone Number -->
        <div v-if="!otpSent">
          <label for="phone" class="block text-sm font-medium text-gray-700 mb-2">
            Broj telefona
          </label>
          <input
            id="phone"
            v-model="phoneNumber"
            type="tel"
            placeholder="+387 6X XXX XXX"
            class="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-lg"
            required
          />
          <p class="mt-2 text-xs text-gray-500">
            Format: +387 6X XXX XXX ili 06X XXX XXX
          </p>

          <!-- WhatsApp Preference -->
          <div class="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <div class="flex items-start">
              <div class="flex items-center h-5">
                <input
                  id="whatsapp-available"
                  v-model="whatsappAvailable"
                  type="checkbox"
                  class="w-4 h-4 text-green-600 bg-white border-gray-300 rounded focus:ring-green-500 focus:ring-2"
                />
              </div>
              <label for="whatsapp-available" class="ml-3 text-sm">
                <span class="font-medium text-gray-900">Imam WhatsApp</span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading || !phoneNumber"
            class="mt-4 w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <span v-if="!isLoading">Pošalji kod</span>
            <span v-else class="flex items-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Šaljem...
            </span>
          </button>
        </div>

        <!-- Step 2: Enter OTP Code -->
        <div v-else>
          <div class="text-center mb-4">
            <p class="text-sm text-gray-600">
              Poslali smo kod na <strong>{{ phoneNumber }}</strong>
            </p>
            <button
              @click="resetPhone"
              type="button"
              class="text-xs text-purple-600 hover:text-purple-700 mt-1"
            >
              Promijeni broj
            </button>
          </div>

          <label for="otp" class="block text-sm font-medium text-gray-700 mb-2">
            Unesite 6-cifreni kod
          </label>
          <input
            id="otp"
            v-model="otpCode"
            type="text"
            inputmode="numeric"
            maxlength="6"
            placeholder="123456"
            class="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-center text-2xl font-mono tracking-widest"
            required
            @input="handleOTPInput"
          />

          <div class="flex gap-2 mt-4">
            <button
              type="submit"
              :disabled="isLoading || otpCode.length !== 6"
              class="flex-1 flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <span v-if="!isLoading">Verifikuj</span>
              <span v-else>Verificiram...</span>
            </button>
          </div>

          <button
            @click="resendOTP"
            type="button"
            :disabled="resendCooldown > 0"
            class="mt-3 w-full text-sm text-purple-600 hover:text-purple-700 disabled:text-gray-400"
          >
            <span v-if="resendCooldown > 0">
              Ponovo pošalji za {{ resendCooldown }}s
            </span>
            <span v-else>
              Ponovo pošalji kod
            </span>
          </button>
        </div>

        <!-- Benefits -->
        <div class="bg-purple-50 rounded-lg p-4 mt-6">
          <p class="text-sm font-semibold text-purple-900 mb-2">
            Dobijate BESPLATNO:
          </p>
          <ul class="text-xs text-purple-700 space-y-1">
            <li>10 pretraga SEDMICNO</li>
            <li>Liste za kupovinu</li>
            <li>Pracenje omiljenih proizvoda</li>
            <li>Email obavještenja o popustima</li>
          </ul>
        </div>
      </form>

      <!-- Email Registration (existing form) -->
      <form v-else @submit.prevent="handleEmailRegister" class="space-y-4">
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-sm text-red-700">{{ errorMessage }}</p>
        </div>

        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="first_name" class="block text-sm font-medium text-gray-700">Ime</label>
              <input
                id="first_name"
                v-model="emailFormData.first_name"
                type="text"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                placeholder="Ime"
              />
            </div>

            <div>
              <label for="last_name" class="block text-sm font-medium text-gray-700">Prezime</label>
              <input
                id="last_name"
                v-model="emailFormData.last_name"
                type="text"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                placeholder="Prezime"
              />
            </div>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">Email adresa</label>
            <input
              id="email"
              v-model="emailFormData.email"
              type="email"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
              placeholder="email@example.com"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Lozinka</label>
            <input
              id="password"
              v-model="emailFormData.password"
              type="password"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
              placeholder="Unesite lozinku"
            />
          </div>

          <div>
            <label for="confirm_password" class="block text-sm font-medium text-gray-700">Potvrda lozinke</label>
            <input
              id="confirm_password"
              v-model="emailFormData.confirm_password"
              type="password"
              required
              class="mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
              :class="passwordMismatch ? 'border-red-300 bg-red-50' : 'border-gray-300'"
              placeholder="Ponovite lozinku"
            />
            <p v-if="passwordMismatch" class="mt-1 text-xs text-red-600">
              Lozinke se ne podudaraju
            </p>
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isLoading ? 'Učitavanje...' : 'Registruj se' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth-redirect']
})

const { post } = useApi()
const { login, user } = useAuth()
const { getAttributionForApi, clearAttribution } = useAttribution()
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

const registrationMethod = ref('email') // Default to email (phone registration hidden for now)
const phoneNumber = ref('')
const whatsappAvailable = ref(true) // Default to WhatsApp enabled
const otpCode = ref('')
const otpSent = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const resendCooldown = ref(0)

const emailFormData = ref({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  confirm_password: ''
})

// Check if passwords match (only show error if confirm_password has content)
const passwordMismatch = computed(() => {
  return emailFormData.value.confirm_password.length > 0 &&
    emailFormData.value.password !== emailFormData.value.confirm_password
})

const searchQuery = route.query.search as string || ''

// Handle phone registration
async function handlePhoneSubmit() {
  if (!otpSent.value) {
    await sendOTP()
  } else {
    await verifyOTP()
  }
}

async function sendOTP() {
  errorMessage.value = ''
  successMessage.value = ''
  isLoading.value = true

  try {
    const response = await post('/api/auth/phone/send-otp', {
      phone: phoneNumber.value,
      whatsapp_available: whatsappAvailable.value
    })

    if (response.success) {
      otpSent.value = true

      // Show appropriate message based on channel
      if (response.channel === 'whatsapp') {
        successMessage.value = 'Kod poslan na WhatsApp! ✓'
      } else if (response.channel === 'sms') {
        if (response.fallback_used) {
          successMessage.value = 'Kod poslan kao SMS (WhatsApp nedostupan)'
        } else {
          successMessage.value = 'Kod poslan kao SMS! ✓'
        }
      } else {
        successMessage.value = 'Kod poslan!'
      }

      startResendCooldown()

      // In dev mode, show the OTP code
      if (response.dev_mode && response.otp_code) {
        successMessage.value = `🧪 DEV MODE: Vaš kod je ${response.otp_code} (${response.channel})`
      }
    } else {
      errorMessage.value = response.error || 'Greška prilikom slanja koda'
    }
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greška prilikom slanja koda'
  } finally {
    isLoading.value = false
  }
}

async function verifyOTP() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const response = await post('/api/auth/phone/verify-otp', {
      phone: phoneNumber.value,
      code: otpCode.value,
      whatsapp_available: whatsappAvailable.value
    })

    if (response.success && response.token) {
      // Login successful - store token and user directly
      if (process.client) {
        localStorage.setItem('token', response.token)
      }
      user.value = response.user

      successMessage.value = 'Uspješno registrovani! ✅'

      // Redirect logic
      setTimeout(() => {
        const redirect = route.query.redirect as string
        if (searchQuery) {
          router.push(`/?autoSearch=${encodeURIComponent(searchQuery)}`)
        } else if (redirect) {
          router.push(redirect)
        } else {
          router.push('/')
        }
      }, 500)
    } else {
      errorMessage.value = response.error || 'Pogrešan kod'
    }
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greška prilikom verifikacije'
  } finally {
    isLoading.value = false
  }
}

async function resendOTP() {
  if (resendCooldown.value > 0) return
  otpCode.value = ''
  await sendOTP()
}

function resetPhone() {
  otpSent.value = false
  otpCode.value = ''
  errorMessage.value = ''
  successMessage.value = ''
}

function handleOTPInput() {
  // Auto-submit when 6 digits entered
  if (otpCode.value.length === 6) {
    verifyOTP()
  }
}

function startResendCooldown() {
  resendCooldown.value = 60
  const interval = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      clearInterval(interval)
    }
  }, 1000)
}

// Email registration handler
async function handleEmailRegister() {
  errorMessage.value = ''

  if (!emailFormData.value.first_name.trim() || !emailFormData.value.last_name.trim() ||
      !emailFormData.value.email.trim() || !emailFormData.value.password.trim()) {
    errorMessage.value = 'Sva polja su obavezna'
    return
  }

  if (emailFormData.value.password !== emailFormData.value.confirm_password) {
    errorMessage.value = 'Lozinke se ne podudaraju'
    return
  }

  isLoading.value = true

  try {
    // Get first-touch attribution data from localStorage
    const attribution = getAttributionForApi()

    // Include attribution in registration payload (exclude confirm_password)
    const { confirm_password, ...formData } = emailFormData.value
    const registrationPayload = {
      ...formData,
      attribution
    }

    const response = await post('/auth/register', registrationPayload)

    if (response.success || response.token) {
      // Clear attribution after successful registration (it's now persisted in backend)
      clearAttribution()

      // Use the token from registration directly (no need to login again)
      if (process.client && response.token) {
        localStorage.setItem('token', response.token)
      }
      user.value = response.user

      if (searchQuery) {
        navigateTo(`/?autoSearch=${encodeURIComponent(searchQuery)}`)
      } else {
        navigateTo('/')
      }
    } else {
      errorMessage.value = response.error || response.message || 'Došlo je do greške prilikom registracije'
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Došlo je do greške prilikom registracije'
  } finally {
    isLoading.value = false
  }
}

useSeoMeta({
  title: 'Registracija - Popust.ba',
  description: 'Registrujte se za 10 sekundi i dobijte neograničenu pretragu!'
})
</script>
