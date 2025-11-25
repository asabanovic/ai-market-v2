<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
    <div class="max-w-4xl mx-auto px-4 py-12">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-4xl font-bold text-gray-900 mb-2">
          <Icon name="mdi:account-multiple" class="inline w-10 h-10 text-purple-600 mr-2" />
          Referral Program
        </h1>
        <p class="text-gray-600">Pozovite prijatelje i osvojite dodatne kredite!</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <Icon name="mdi:loading" class="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
        <p class="text-gray-600">Učitavanje...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
        <p class="text-red-700">{{ error }}</p>
      </div>

      <!-- Main Content -->
      <div v-else-if="referralInfo" class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Total Referrals -->
          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-600">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Ukupno referrala</p>
                <p class="text-3xl font-bold text-gray-900">{{ referralInfo.total_referrals }}</p>
              </div>
              <Icon name="mdi:account-group" class="w-12 h-12 text-purple-600 opacity-50" />
            </div>
          </div>

          <!-- Total Credits Earned -->
          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-600">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Zaradjeni krediti</p>
                <p class="text-3xl font-bold text-gray-900">{{ referralInfo.total_credits_earned }}</p>
              </div>
              <Icon name="mdi:star-circle" class="w-12 h-12 text-green-600 opacity-50" />
            </div>
          </div>

          <!-- Credits Per Referral -->
          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600 mb-1">Po referralu</p>
                <p class="text-3xl font-bold text-gray-900">100</p>
              </div>
              <Icon name="mdi:gift" class="w-12 h-12 text-blue-600 opacity-50" />
            </div>
          </div>
        </div>

        <!-- Referral Code Card -->
        <div class="bg-gradient-to-br from-purple-600 to-purple-800 rounded-lg shadow-lg p-8 text-white">
          <h2 class="text-2xl font-bold mb-4">Vaš referral kod</h2>
          <div class="bg-white/20 backdrop-blur-sm rounded-lg p-6 mb-4">
            <div class="flex items-center justify-between mb-4">
              <div class="flex-1">
                <p class="text-sm opacity-90 mb-2">Referral kod:</p>
                <p class="text-3xl font-bold tracking-wider font-mono">{{ referralInfo.display_code }}</p>
                <p v-if="!referralInfo.custom_code_changed" class="text-xs opacity-75 mt-2">
                  <Icon name="mdi:information" class="w-3 h-3 inline mr-1" />
                  Auto-generisan - možete ga prilagoditi ispod
                </p>
              </div>
              <button
                @click="copyCode"
                class="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <Icon :name="copied ? 'mdi:check' : 'mdi:content-copy'" class="w-5 h-5" />
                {{ copied ? 'Kopirano!' : 'Kopiraj' }}
              </button>
            </div>
            <div class="border-t border-white/20 pt-4">
              <p class="text-sm opacity-90 mb-2">Referral link:</p>
              <div class="flex items-center gap-2">
                <input
                  type="text"
                  :value="referralInfo.referral_url"
                  readonly
                  class="flex-1 bg-white/10 px-3 py-2 rounded text-sm font-mono truncate"
                />
                <button
                  @click="copyLink"
                  class="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap"
                >
                  <Icon :name="linkCopied ? 'mdi:check' : 'mdi:link'" class="w-5 h-5" />
                  {{ linkCopied ? 'Kopirano!' : 'Kopiraj link' }}
                </button>
              </div>
            </div>
          </div>
          <div class="text-sm opacity-90">
            <p>✓ Podijelite vaš kod sa prijateljima</p>
            <p>✓ Oni dobijaju 100 kredita bonus na registraciju</p>
            <p>✓ Vi dobijate 100 kredita za svaki uspješan referral</p>
          </div>
        </div>

        <!-- Custom Referral Code Section -->
        <div v-if="!referralInfo.custom_code_changed" class="bg-white rounded-lg shadow-md p-6">
          <!-- Warning Banner -->
          <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <div class="flex">
              <Icon name="mdi:alert" class="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <h4 class="text-sm font-semibold text-yellow-800 mb-1">
                  Prilagodite svoj kod prije dijeljenja!
                </h4>
                <p class="text-sm text-yellow-700">
                  Trenutno imate automatski generisan kod: <code class="bg-yellow-100 px-2 py-1 rounded font-mono">{{ referralInfo.custom_referral_code }}</code>
                </p>
                <p class="text-sm text-yellow-700 mt-1">
                  Možete ga promijeniti JEDNOM na neki koji je lakši za pamćenje. Nakon što podijelite link, nećete moći promijeniti kod.
                </p>
              </div>
            </div>
          </div>

          <h3 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Icon name="mdi:pencil" class="w-5 h-5 text-purple-600 mr-2" />
            Prilagodite vaš referral kod
          </h3>
          <p class="text-gray-600 mb-4">
            Napravite lako pamtljiv kod koji možete dijeliti sa prijateljima. Na primjer: <code class="bg-gray-100 px-2 py-1 rounded">rabat.ba/r/adnan</code>
          </p>

          <div v-if="!showCustomCodeForm">
            <button
              @click="showCustomCodeForm = true"
              class="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            >
              <Icon name="mdi:plus" class="w-5 h-5" />
              Kreiraj custom kod
            </button>
          </div>

          <div v-else class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Vaš custom kod (3-20 karaktera)
              </label>
              <div class="flex items-center gap-2">
                <span class="text-gray-500">rabat.ba/r/</span>
                <input
                  v-model="customCode"
                  type="text"
                  placeholder="adnan"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  :class="{ 'border-red-300': customCodeError }"
                  @input="validateCustomCode"
                />
              </div>
              <p v-if="customCodeError" class="text-sm text-red-600 mt-1">{{ customCodeError }}</p>
              <p v-else class="text-sm text-gray-500 mt-1">
                Samo mala slova, brojevi, crtice i podvlake
              </p>
            </div>

            <div class="flex gap-2">
              <button
                @click="setCustomCode"
                :disabled="!customCode || !!customCodeError || settingCode"
                class="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
              >
                <Icon v-if="settingCode" name="mdi:loading" class="w-5 h-5 animate-spin" />
                <Icon v-else name="mdi:check" class="w-5 h-5" />
                {{ settingCode ? 'Postavljanje...' : 'Postavi kod' }}
              </button>
              <button
                @click="showCustomCodeForm = false; customCode = ''; customCodeError = ''"
                class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors"
              >
                Otkaži
              </button>
            </div>
          </div>
        </div>

        <div v-else class="bg-green-50 border border-green-200 rounded-lg p-6">
          <div class="flex items-start gap-3">
            <Icon name="mdi:check-circle" class="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 class="font-semibold text-green-900 mb-1">Vaš referral kod je spreman!</h3>
              <p class="text-green-800 text-sm mb-2">
                Vaš referral link: <code class="bg-green-100 px-2 py-1 rounded font-mono">rabat.ba/r/{{ referralInfo.custom_referral_code }}</code>
              </p>
              <p class="text-green-700 text-xs">
                <Icon name="mdi:lock" class="w-4 h-4 inline mr-1" />
                Kod je finaliziran i ne može se više mijenjati
              </p>
            </div>
          </div>
        </div>

        <!-- Referrals List -->
        <div v-if="referrals && referrals.length > 0" class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Icon name="mdi:account-check" class="w-6 h-6 text-purple-600 mr-2" />
            Vaši referrali ({{ referrals.length }})
          </h2>
          <div class="space-y-4">
            <div
              v-for="referral in referrals"
              :key="referral.id"
              class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white font-semibold">
                  {{ getInitials(referral) }}
                </div>
                <div>
                  <p class="font-medium text-gray-900">
                    {{ referral.referred_user_email || referral.referred_user_phone || 'Korisnik' }}
                  </p>
                  <p class="text-sm text-gray-500">
                    Registrovan {{ formatDate(referral.created_at) }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-lg font-semibold text-green-600">+{{ referral.credits_awarded }}</p>
                <p class="text-xs text-gray-500">kredita</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="bg-white rounded-lg shadow-md p-12 text-center">
          <Icon name="mdi:account-multiple-plus" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Još nema referrala</h3>
          <p class="text-gray-600 mb-6">Podijelite vaš kod sa prijateljima i počnite zarađivati kredite!</p>
        </div>

        <!-- How it Works -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 class="text-lg font-semibold text-blue-900 mb-4 flex items-center">
            <Icon name="mdi:information" class="w-5 h-5 mr-2" />
            Kako funkcioniše?
          </h3>
          <ol class="space-y-2 text-blue-800">
            <li class="flex items-start">
              <span class="font-bold mr-2">1.</span>
              <span>Podijelite vaš referral kod ili link sa prijateljima</span>
            </li>
            <li class="flex items-start">
              <span class="font-bold mr-2">2.</span>
              <span>Kada se prijatelj registruje sa vašim kodom, automatski dobija 100 bonus kredita</span>
            </li>
            <li class="flex items-start">
              <span class="font-bold mr-2">3.</span>
              <span>Vi dobijate 100 ekstra kredita koji se dodaju u vaš saldo</span>
            </li>
            <li class="flex items-start">
              <span class="font-bold mr-2">4.</span>
              <span>Ekstra krediti se ne resetuju - ostaju zauvijek!</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { user } = useAuth()
const { get, post } = useApi()

const loading = ref(true)
const error = ref('')
const referralInfo = ref<any>(null)
const referrals = ref<any[]>([])
const copied = ref(false)
const linkCopied = ref(false)

// Custom code management
const showCustomCodeForm = ref(false)
const customCode = ref('')
const customCodeError = ref('')
const settingCode = ref(false)

// Load referral data
onMounted(async () => {
  await loadReferralData()
})

async function loadReferralData() {
  try {
    loading.value = true
    error.value = ''

    // Fetch referral info
    const info = await get('/user/referral-info')
    referralInfo.value = info

    // Fetch referrals list
    const referralsData = await get('/user/referrals')
    referrals.value = referralsData.referrals || []

    loading.value = false
  } catch (e: any) {
    console.error('Error loading referral data:', e)
    error.value = e.message || 'Greška pri učitavanju podataka'
    loading.value = false
  }
}

function copyCode() {
  if (referralInfo.value?.display_code) {
    navigator.clipboard.writeText(referralInfo.value.display_code)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}

function copyLink() {
  if (referralInfo.value?.referral_url) {
    navigator.clipboard.writeText(referralInfo.value.referral_url)
    linkCopied.value = true
    setTimeout(() => {
      linkCopied.value = false
    }, 2000)
  }
}

function getInitials(referral: any): string {
  const email = referral.referred_user_email || ''
  const phone = referral.referred_user_phone || ''

  if (email) {
    return email.substring(0, 2).toUpperCase()
  } else if (phone) {
    return 'U'
  }
  return 'U'
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return 'danas'
    } else if (diffDays === 1) {
      return 'juče'
    } else if (diffDays < 7) {
      return `prije ${diffDays} dana`
    } else {
      const day = date.getDate()
      const month = date.getMonth() + 1
      const year = date.getFullYear()
      return `${day}.${month}.${year}`
    }
  } catch (e) {
    return dateString
  }
}

function validateCustomCode() {
  const code = customCode.value.trim().toLowerCase()
  customCodeError.value = ''

  if (code.length === 0) return

  if (code.length < 3) {
    customCodeError.value = 'Kod mora imati najmanje 3 karaktera'
    return
  }

  if (code.length > 20) {
    customCodeError.value = 'Kod može imati maksimalno 20 karaktera'
    return
  }

  if (!/^[a-z0-9_-]+$/.test(code)) {
    customCodeError.value = 'Samo mala slova, brojevi, crtice i podvlake'
    return
  }

  // Check reserved words
  const reserved = ['admin', 'api', 'auth', 'login', 'register', 'registracija', 'prijava',
    'logout', 'profile', 'profil', 'user', 'korisnik', 'help', 'about',
    'contact', 'kontakt', 'home', 'proizvodi', 'products', 'kako-radimo',
    'code', 'r', 'ref', 'referral', 'referrali', 'krediti', 'credits',
    'moje-liste', 'favorites', 'omiljeni', 'rabat', 'settings', 'postavke']

  if (reserved.includes(code)) {
    customCodeError.value = 'Ovaj kod je rezervisan'
    return
  }
}

async function setCustomCode() {
  if (!customCode.value || customCodeError.value) return

  try {
    settingCode.value = true

    const response = await post('/user/custom-referral-code', {
      code: customCode.value.trim().toLowerCase()
    })

    if (response.success) {
      // Reload referral data to show new custom code
      await loadReferralData()
      showCustomCodeForm.value = false
      customCode.value = ''
    } else {
      customCodeError.value = response.error || 'Greška pri postavljanju koda'
    }
  } catch (e: any) {
    console.error('Error setting custom code:', e)
    customCodeError.value = e.message || 'Greška pri postavljanju koda'
  } finally {
    settingCode.value = false
  }
}

useSeoMeta({
  title: 'Referral Program - Popust.ba',
  description: 'Pozovite prijatelje i osvojite dodatne kredite! 100 kredita za svaki uspješan referral.'
})
</script>
