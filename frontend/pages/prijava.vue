<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-2xl">
      <!-- Header -->
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Prijavite se
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Ili
          <NuxtLink to="/registracija" class="font-medium text-purple-600 hover:text-purple-500">
            se registrujte besplatno
          </NuxtLink>
        </p>
      </div>

      <!-- Login Method Toggle -->
      <div class="flex bg-gray-100 rounded-lg p-1">
        <button
          type="button"
          @click="loginMethod = 'phone'"
          :class="[
            'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
            loginMethod === 'phone'
              ? 'bg-white text-purple-600 shadow'
              : 'text-gray-600 hover:text-gray-900'
          ]"
        >
          📱 Telefon
        </button>
        <button
          type="button"
          @click="loginMethod = 'email'"
          :class="[
            'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
            loginMethod === 'email'
              ? 'bg-white text-purple-600 shadow'
              : 'text-gray-600 hover:text-gray-900'
          ]"
        >
          ✉️ Email
        </button>
      </div>

      <!-- Phone Login (Passwordless) -->
      <form v-if="loginMethod === 'phone'" @submit.prevent="handlePhoneSubmit" class="space-y-6">
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
            📱 Broj telefona
          </label>
          <input
            id="phone"
            v-model="phoneNumber"
            type="tel"
            placeholder="+387 6X XXX XXX"
            :class="[
              'appearance-none relative block w-full px-4 py-3 border placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-lg',
              phoneNumber && !isPhoneNumberValid ? 'border-red-300 bg-red-50' : 'border-gray-300'
            ]"
            required
            @blur="phoneNumberTouched = true"
          />
          <p class="mt-2 text-xs text-gray-500">
            Format: +387 6X XXX XXX ili 06X XXX XXX
          </p>
          <p v-if="phoneNumberTouched && phoneNumber && !isPhoneNumberValid" class="mt-2 text-xs text-red-600">
            ⚠️ Neispravan format broja telefona. Molimo koristite format: +387 6X XXX XXX ili 06X XXX XXX
          </p>

          <!-- WhatsApp Preference -->
          <div class="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <div class="flex items-start">
              <div class="flex items-center h-5">
                <input
                  id="whatsapp-login"
                  v-model="whatsappAvailable"
                  type="checkbox"
                  class="w-4 h-4 text-green-600 bg-white border-gray-300 rounded focus:ring-green-500 focus:ring-2"
                />
              </div>
              <label for="whatsapp-login" class="ml-3 text-sm">
                <span class="font-medium text-gray-900">Imam WhatsApp 📱</span>
                <p class="text-xs text-gray-600 mt-1">
                  Kod će stići preko WhatsApp-a. Ako nemate WhatsApp, poslaćemo SMS.
                </p>
              </label>
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading || !phoneNumber || !isPhoneNumberValid"
            class="mt-4 w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <span v-if="!isLoading">Pošalji kod za prijavu 📲</span>
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
              Poslali smo kod za prijavu na <strong>{{ phoneNumber }}</strong>
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
            🔑 Unesite 6-cifreni kod
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
              <span v-if="!isLoading">Prijavi se ✓</span>
              <span v-else>Prijavljivanje...</span>
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
              📲 Ponovo pošalji kod
            </span>
          </button>
        </div>
      </form>

      <!-- Email Login (With Password) -->
      <form v-else @submit.prevent="handleEmailLogin" class="space-y-6">
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-sm text-red-700">{{ errorMessage }}</p>
        </div>

        <div class="space-y-4">
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
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isLoading ? 'Prijavljivanje...' : 'Prijavi se' }}
        </button>
      </form>

      <!-- Google OAuth Button -->
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-white text-gray-500">Ili</span>
        </div>
      </div>

      <a
        :href="`${config.public.apiBase}/auth/google`"
        class="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        <span class="font-medium">Prijavi se sa Google</span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth-redirect']
})

const { post } = useApi()
const { login, user } = useAuth()
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

const loginMethod = ref('phone') // Default to phone
const phoneNumber = ref('')
const whatsappAvailable = ref(true) // Default to WhatsApp enabled
const otpCode = ref('')
const otpSent = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const resendCooldown = ref(0)
const phoneNumberTouched = ref(false)

const emailFormData = ref({
  email: '',
  password: ''
})

// Phone validation - accepts Bosnian mobile formats
// +387 6X XXX XXX, 00387 6X XXX XXX, 06X XXX XXX
const isPhoneNumberValid = computed(() => {
  const phone = phoneNumber.value.trim()
  if (!phone) return false

  // Remove spaces, dashes, and parentheses for validation
  const cleanPhone = phone.replace(/[\s\-\(\)]/g, '')

  const patterns = [
    /^\+3876\d{7,8}$/,      // +387 6X XXX XXX(X)
    /^003876\d{7,8}$/,      // 00387 6X XXX XXX(X)
    /^06\d{7,8}$/,          // 06X XXX XXX(X)
    /^\+3873\d{7,8}$/,      // +387 3X XXX XXX(X) landline
    /^003873\d{7,8}$/,      // 00387 3X XXX XXX(X) landline
    /^03\d{7,8}$/,          // 03X XXX XXX(X) landline
  ]

  return patterns.some(pattern => pattern.test(cleanPhone))
})

// Handle phone login
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

      successMessage.value = 'Uspješno prijavljeni! ✅'

      // Redirect logic
      setTimeout(() => {
        const redirect = route.query.redirect as string
        if (redirect) {
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

// Email login handler
async function handleEmailLogin() {
  errorMessage.value = ''

  if (!emailFormData.value.email.trim() || !emailFormData.value.password.trim()) {
    errorMessage.value = 'Email i lozinka su obavezni'
    return
  }

  isLoading.value = true

  try {
    await login(emailFormData.value.email, emailFormData.value.password)

    const redirect = route.query.redirect as string
    if (redirect) {
      router.push(redirect)
    } else {
      router.push('/')
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Pogrešan email ili lozinka'
  } finally {
    isLoading.value = false
  }
}

useSeoMeta({
  title: 'Prijava - Popust.ba',
  description: 'Prijavite se na Popust.ba'
})
</script>
