<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center px-4">
    <div class="max-w-md w-full">
      <!-- Loading State -->
      <div v-if="loading" class="bg-white rounded-lg shadow-lg p-8 text-center">
        <Icon name="mdi:loading" class="w-16 h-16 text-purple-600 animate-spin mx-auto mb-4" />
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Provjera koda...</h2>
        <p class="text-gray-600">Molimo sačekajte</p>
      </div>

      <!-- Invalid Code -->
      <div v-else-if="error" class="bg-white rounded-lg shadow-lg p-8">
        <div class="text-center mb-6">
          <Icon name="mdi:alert-circle" class="w-16 h-16 text-red-600 mx-auto mb-4" />
          <h2 class="text-2xl font-bold text-gray-900 mb-2">Neispravan kod</h2>
          <p class="text-gray-600">{{ error }}</p>
        </div>
        <NuxtLink
          to="/registracija"
          class="block w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors text-center"
        >
          Registrujte se bez koda
        </NuxtLink>
      </div>

      <!-- Valid Code - Show Referrer Info -->
      <div v-else-if="referrerInfo" class="bg-white rounded-lg shadow-lg p-8">
        <div class="text-center mb-6">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">
            {{ getInitials(referrerInfo.referrer_name) }}
          </div>
          <h2 class="text-2xl font-bold text-gray-900 mb-2">
            {{ referrerInfo.referrer_name }} vas je pozvao!
          </h2>
          <div class="inline-flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-full">
            <Icon name="mdi:gift" class="w-5 h-5" />
            <span class="font-semibold">+{{ referrerInfo.bonus_credits }} bonus kredita</span>
          </div>
        </div>

        <div class="bg-purple-50 rounded-lg p-6 mb-6">
          <h3 class="font-semibold text-purple-900 mb-3">Vaši benefiti:</h3>
          <ul class="space-y-2 text-purple-800">
            <li class="flex items-start">
              <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <span>{{ referrerInfo.bonus_credits }} bonus kredita odmah po registraciji</span>
            </li>
            <li class="flex items-start">
              <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <span>10 kredita sedmično - obnavljaju se svakog ponedjeljka</span>
            </li>
            <li class="flex items-start">
              <Icon name="mdi:check-circle" class="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <span>Bonus krediti se ne resetuju - ostaju zauvijek!</span>
            </li>
          </ul>
        </div>

        <div class="space-y-3">
          <button
            @click="register"
            class="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold py-3 px-4 rounded-lg transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
          >
            <Icon name="mdi:account-plus" class="w-5 h-5" />
            Registruj se i dobij {{ referrerInfo.bonus_credits }} kredita
          </button>
          <p class="text-xs text-gray-500 text-center">
            Registracijom prihvatate naše uslove korištenja
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { post } = useApi()

const code = computed(() => route.params.code as string)
const loading = ref(true)
const error = ref('')
const referrerInfo = ref<any>(null)

// Validate code on mount
onMounted(async () => {
  await validateCode()
})

async function validateCode() {
  try {
    loading.value = true
    error.value = ''

    const response = await post('/validate-referral-code', {
      referral_code: code.value
    })

    if (response.valid) {
      referrerInfo.value = response
      loading.value = false
    } else {
      error.value = response.error || 'Referral kod nije validan'
      loading.value = false
    }
  } catch (e: any) {
    console.error('Error validating code:', e)
    error.value = 'Greška pri provjeri koda. Pokušajte ponovo.'
    loading.value = false
  }
}

function register() {
  // Redirect to registration with the code
  router.push(`/registracija?ref=${code.value}`)
}

function getInitials(name: string): string {
  if (!name) return 'U'
  const parts = name.trim().split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

useSeoMeta({
  title: 'Referral Link - Rabat.ba',
  description: `Registrujte se preko referral linka i dobijte bonus kredite!`
})
</script>
