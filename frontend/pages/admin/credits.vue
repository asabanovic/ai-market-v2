<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header with Back Button -->
      <div class="mb-8">
        <NuxtLink
          to="/admin"
          class="inline-flex items-center text-sm text-gray-500 hover:text-purple-600 mb-4 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-4 h-4 mr-1" />
          Nazad na Dashboard
        </NuxtLink>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Bonus Krediti</h1>
        <p class="text-gray-600">Dodijelite bonus kredite korisnicima kao nagradu</p>
      </div>

      <!-- Award Credits Form -->
      <div class="bg-white rounded-xl shadow-md p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
          <Icon name="mdi:gift" class="w-6 h-6 text-purple-600" />
          Dodjela kredita
        </h2>

        <form @submit.prevent="awardCredits" class="space-y-6">
          <!-- Target Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Kome dodijeliti kredite?</label>
            <div class="flex gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  v-model="targetType"
                  value="selected"
                  class="text-purple-600 focus:ring-purple-500"
                />
                <span>Odabrani korisnici</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  v-model="targetType"
                  value="all"
                  class="text-purple-600 focus:ring-purple-500"
                />
                <span class="text-orange-600 font-medium">Svi korisnici</span>
              </label>
            </div>
          </div>

          <!-- User Selection (if selected mode) -->
          <div v-if="targetType === 'selected'" class="space-y-4">
            <div class="flex gap-2">
              <input
                v-model="userSearch"
                type="text"
                placeholder="Pretraži korisnike po email ili telefonu..."
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                @input="debouncedSearchUsers"
              />
            </div>

            <!-- Search Results -->
            <div v-if="searchResults.length > 0" class="border border-gray-200 rounded-lg max-h-48 overflow-y-auto">
              <div
                v-for="user in searchResults"
                :key="user.id"
                @click="toggleUserSelection(user)"
                :class="[
                  'flex items-center justify-between px-4 py-3 cursor-pointer transition-colors',
                  isUserSelected(user.id) ? 'bg-purple-50 border-l-4 border-purple-600' : 'hover:bg-gray-50'
                ]"
              >
                <div>
                  <div class="font-medium text-gray-900">{{ user.name || user.email || user.phone }}</div>
                  <div class="text-sm text-gray-500">{{ user.email }} {{ user.phone ? `| ${user.phone}` : '' }}</div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-400">{{ user.total_credits }} kredita</span>
                  <Icon
                    :name="isUserSelected(user.id) ? 'mdi:check-circle' : 'mdi:circle-outline'"
                    :class="isUserSelected(user.id) ? 'text-purple-600' : 'text-gray-300'"
                    class="w-5 h-5"
                  />
                </div>
              </div>
            </div>

            <!-- Selected Users -->
            <div v-if="selectedUsers.length > 0" class="mt-4">
              <div class="text-sm font-medium text-gray-700 mb-2">
                Odabrano: {{ selectedUsers.length }} korisnik(a)
              </div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="user in selectedUsers"
                  :key="user.id"
                  class="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                >
                  {{ user.name || user.email || user.phone }}
                  <button @click="removeUser(user.id)" class="hover:text-purple-900">
                    <Icon name="mdi:close" class="w-4 h-4" />
                  </button>
                </span>
              </div>
            </div>
          </div>

          <!-- All Users Warning -->
          <div v-if="targetType === 'all'" class="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <Icon name="mdi:alert" class="w-6 h-6 text-orange-500 flex-shrink-0 mt-0.5" />
              <div>
                <p class="font-medium text-orange-800">Pažnja: Slanje svim korisnicima</p>
                <p class="text-sm text-orange-700 mt-1">
                  Krediti će biti dodijeljeni svim registrovanim korisnicima (osim admina) i svi će primiti email obavještenje.
                </p>
              </div>
            </div>
          </div>

          <!-- Amount -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Broj kredita</label>
            <div class="flex items-center gap-4">
              <div class="relative">
                <input
                  v-model.number="amount"
                  type="number"
                  min="1"
                  max="10000"
                  required
                  class="w-32 px-4 py-3 text-2xl font-bold text-center border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div class="flex gap-2">
                <button
                  type="button"
                  v-for="preset in [10, 25, 50, 100]"
                  :key="preset"
                  @click="amount = preset"
                  :class="[
                    'px-3 py-1 rounded-full text-sm font-medium transition-colors',
                    amount === preset ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  +{{ preset }}
                </button>
              </div>
            </div>
          </div>

          <!-- Reason -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Razlog / Naziv nagrade</label>
            <input
              v-model="reason"
              type="text"
              required
              placeholder="npr. Feedback nagrada, Posebna promocija, Beta tester bonus..."
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <p class="mt-1 text-xs text-gray-500">Ovo će se prikazati u email-u korisnika</p>
          </div>

          <!-- Custom Message -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Personalizirana poruka
              <span class="text-gray-400 font-normal">(opcionalno)</span>
            </label>
            <textarea
              v-model="message"
              rows="3"
              placeholder="Opcionalna poruka koja će se prikazati u email-u..."
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            ></textarea>
          </div>

          <!-- Email Toggle -->
          <div class="flex items-center gap-3">
            <input
              type="checkbox"
              v-model="sendEmail"
              id="send-email"
              class="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            />
            <label for="send-email" class="text-sm text-gray-700">
              Pošalji email obavještenje korisnicima
            </label>
          </div>

          <!-- Preview -->
          <div v-if="amount && reason" class="bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl p-6 text-white">
            <div class="text-center">
              <div class="text-sm opacity-80 mb-2">Preview email-a</div>
              <div class="text-5xl font-bold mb-2">+{{ amount }}</div>
              <div class="text-lg opacity-90 mb-1">bonus kredita</div>
              <div class="inline-block px-4 py-1 bg-white/20 rounded-full text-sm">
                {{ reason }}
              </div>
              <p v-if="message" class="mt-4 text-sm opacity-80 italic">"{{ message }}"</p>
            </div>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="isSubmitting || (targetType === 'selected' && selectedUsers.length === 0)"
            class="w-full py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Icon v-if="isSubmitting" name="mdi:loading" class="w-5 h-5 animate-spin" />
            <Icon v-else name="mdi:gift" class="w-5 h-5" />
            <span v-if="targetType === 'all'">Dodijeli svim korisnicima</span>
            <span v-else-if="selectedUsers.length > 0">Dodijeli {{ selectedUsers.length }} korisniku/ima</span>
            <span v-else>Odaberite korisnike</span>
          </button>
        </form>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-8">
        <div class="flex items-center gap-3">
          <Icon name="mdi:check-circle" class="w-6 h-6 text-green-600" />
          <div>
            <p class="font-medium text-green-800">{{ successMessage }}</p>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
        <div class="flex items-center gap-3">
          <Icon name="mdi:alert-circle" class="w-6 h-6 text-red-600" />
          <div>
            <p class="font-medium text-red-800">{{ errorMessage }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  layout: 'default'
})

const { get, post } = useApi()
const { user } = useAuth()

// Redirect non-admins
if (!user.value?.is_admin) {
  navigateTo('/')
}

// Form state
const targetType = ref<'selected' | 'all'>('selected')
const selectedUsers = ref<any[]>([])
const userSearch = ref('')
const searchResults = ref<any[]>([])
const amount = ref(25)
const reason = ref('')
const message = ref('')
const sendEmail = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// User search
let searchTimeout: NodeJS.Timeout

function debouncedSearchUsers() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    searchUsers()
  }, 300)
}

async function searchUsers() {
  if (!userSearch.value.trim()) {
    searchResults.value = []
    return
  }

  try {
    const data = await get(`/api/admin/credits/users?search=${encodeURIComponent(userSearch.value)}&per_page=10`)
    searchResults.value = data.users
  } catch (error) {
    console.error('Error searching users:', error)
  }
}

function isUserSelected(userId: string): boolean {
  return selectedUsers.value.some(u => u.id === userId)
}

function toggleUserSelection(user: any) {
  if (isUserSelected(user.id)) {
    removeUser(user.id)
  } else {
    selectedUsers.value.push(user)
  }
}

function removeUser(userId: string) {
  selectedUsers.value = selectedUsers.value.filter(u => u.id !== userId)
}

async function awardCredits() {
  if (!reason.value.trim()) {
    errorMessage.value = 'Unesite razlog za dodjelu kredita'
    return
  }

  if (!amount.value || amount.value < 1) {
    errorMessage.value = 'Unesite validan broj kredita'
    return
  }

  if (targetType.value === 'selected' && selectedUsers.value.length === 0) {
    errorMessage.value = 'Odaberite barem jednog korisnika'
    return
  }

  isSubmitting.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const payload: any = {
      amount: amount.value,
      reason: reason.value.trim(),
      message: message.value.trim(),
      send_email: sendEmail.value
    }

    if (targetType.value === 'all') {
      payload.all_users = true
    } else {
      payload.user_ids = selectedUsers.value.map(u => u.id)
    }

    const result = await post('/api/admin/credits/award', payload)

    successMessage.value = `Uspješno dodijeljeno ${result.amount} kredita za ${result.awarded_count} korisnika. Poslano ${result.email_sent_count} email-ova.`

    // Reset form
    selectedUsers.value = []
    reason.value = ''
    message.value = ''
    userSearch.value = ''
    searchResults.value = []

  } catch (error: any) {
    console.error('Error awarding credits:', error)
    errorMessage.value = error.data?.error || 'Greška prilikom dodjele kredita'
  } finally {
    isSubmitting.value = false
  }
}

useSeoMeta({
  title: 'Bonus Krediti - Admin - Popust.ba',
  description: 'Admin panel za dodjelu bonus kredita korisnicima'
})
</script>
