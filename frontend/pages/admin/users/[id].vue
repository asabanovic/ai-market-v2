<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <NuxtLink
            to="/admin/users"
            class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <Icon name="mdi:arrow-left" class="w-4 h-4 mr-2" />
            Nazad
          </NuxtLink>
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">Profil korisnika</h1>
            <p class="mt-1 text-sm text-gray-600">Detaljan pregled korisnickog profila</p>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <Icon name="mdi:loading" class="w-8 h-8 animate-spin" />
          <span class="ml-3 text-lg">Ucitavanje...</span>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <Icon name="mdi:alert-circle" class="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900">Greska</h3>
        <p class="text-gray-500">{{ error }}</p>
      </div>

      <template v-else-if="userData">
        <!-- User Header Card -->
        <div class="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div class="flex items-start gap-6">
            <!-- Avatar -->
            <div class="flex-shrink-0">
              <div class="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold">
                {{ getInitials(userData.first_name, userData.last_name, userData.email) }}
              </div>
            </div>

            <!-- User Info -->
            <div class="flex-1">
              <div class="flex items-center gap-3">
                <h2 class="text-xl font-semibold text-gray-900">
                  {{ userData.first_name || 'Nepoznato' }} {{ userData.last_name || '' }}
                </h2>
                <span v-if="userData.is_admin" class="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800">
                  Admin
                </span>
                <span :class="userData.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'" class="px-2 py-1 text-xs font-medium rounded-full">
                  {{ userData.is_verified ? 'Verifikovan' : 'Nije verifikovan' }}
                </span>
              </div>

              <div class="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div v-if="userData.email" class="flex items-center gap-2 text-gray-600">
                  <Icon name="mdi:email" class="w-4 h-4" />
                  <span>{{ userData.email }}</span>
                </div>
                <div v-if="userData.phone" class="flex items-center gap-2 text-gray-600">
                  <Icon name="mdi:phone" class="w-4 h-4" />
                  <span>{{ userData.phone }}</span>
                </div>
                <div v-if="userData.city" class="flex items-center gap-2 text-gray-600">
                  <Icon name="mdi:map-marker" class="w-4 h-4" />
                  <span>{{ userData.city }}</span>
                </div>
                <div class="flex items-center gap-2 text-gray-600">
                  <Icon name="mdi:calendar" class="w-4 h-4" />
                  <span>Registrovan: {{ formatDate(userData.created_at) }}</span>
                </div>
                <div class="flex items-center gap-2 text-gray-600">
                  <Icon name="mdi:account-circle" class="w-4 h-4" />
                  <span>{{ userData.registration_method === 'phone' ? 'Telefon' : 'Email' }} registracija</span>
                </div>
                <div v-if="userData.referral_code" class="flex items-center gap-2 text-gray-600">
                  <Icon name="mdi:gift" class="w-4 h-4" />
                  <span>Referral: {{ userData.referral_code }}</span>
                </div>
              </div>
            </div>

            <!-- Credits Summary -->
            <div class="flex-shrink-0 text-right">
              <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-4 border border-indigo-100">
                <div class="text-sm text-gray-500">Krediti</div>
                <div class="text-2xl font-bold text-indigo-600">
                  {{ userData.weekly_credits - userData.weekly_credits_used + userData.extra_credits }}
                </div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ userData.weekly_credits_used }}/{{ userData.weekly_credits }} tjedno
                  <span v-if="userData.extra_credits"> + {{ userData.extra_credits }} ekstra</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-2xl font-bold text-blue-600">{{ stats.total_searches }}</div>
            <div class="text-sm text-gray-500">Pretrage</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-2xl font-bold text-purple-600">{{ stats.total_engagements }}</div>
            <div class="text-sm text-gray-500">Interakcije</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-2xl font-bold text-pink-600">{{ stats.total_favorites }}</div>
            <div class="text-sm text-gray-500">Omiljeni</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-2xl font-bold text-green-600">{{ stats.total_shopping_lists }}</div>
            <div class="text-sm text-gray-500">Liste kupovine</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-2xl font-bold text-orange-600">{{ stats.total_comments }}</div>
            <div class="text-sm text-gray-500">Komentari</div>
          </div>
          <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="text-2xl font-bold text-teal-600">{{ stats.total_credits_earned }}</div>
            <div class="text-sm text-gray-500">Zaradjeni krediti</div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div class="border-b border-gray-200">
            <nav class="flex -mb-px overflow-x-auto">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                  'px-6 py-4 text-sm font-medium border-b-2 whitespace-nowrap transition-colors',
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                <Icon :name="tab.icon" class="w-4 h-4 mr-2 inline" />
                {{ tab.label }}
              </button>
            </nav>
          </div>

          <div class="p-6">
            <!-- Activity Tab -->
            <div v-if="activeTab === 'activity'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Aktivnost (posljednjih 30 dana)</h3>

              <!-- Activity Chart -->
              <div class="bg-gray-50 rounded-lg p-4 mb-6">
                <div class="flex items-end gap-1 h-40 overflow-x-auto">
                  <div
                    v-for="(day, index) in activityChart"
                    :key="index"
                    class="flex flex-col items-center min-w-[24px]"
                  >
                    <div class="flex gap-0.5 items-end h-32">
                      <!-- Searches bar (blue) -->
                      <div
                        class="w-2 bg-blue-400 rounded-t transition-all"
                        :style="{ height: `${Math.min(day.searches * 8, 128)}px` }"
                        :title="`${day.day}: ${day.searches} pretraga`"
                      ></div>
                      <!-- Engagements bar (purple) -->
                      <div
                        class="w-2 bg-purple-400 rounded-t transition-all"
                        :style="{ height: `${Math.min(day.engagements * 8, 128)}px` }"
                        :title="`${day.day}: ${day.engagements} interakcija`"
                      ></div>
                    </div>
                    <span class="text-[10px] text-gray-400 mt-1 rotate-45 origin-left">{{ day.day }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-6 mt-4 text-sm">
                  <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-blue-400 rounded"></div>
                    <span class="text-gray-600">Pretrage</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-purple-400 rounded"></div>
                    <span class="text-gray-600">Interakcije</span>
                  </div>
                </div>
              </div>

              <!-- Recent Activity Summary -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="border border-gray-200 rounded-lg p-4">
                  <h4 class="font-medium text-gray-900 mb-2">Posljednjih 30 dana</h4>
                  <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                      <span class="text-gray-500">Pretrage</span>
                      <span class="font-medium">{{ stats.recent_searches }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-500">Interakcije</span>
                      <span class="font-medium">{{ stats.recent_engagements }}</span>
                    </div>
                  </div>
                </div>
                <div class="border border-gray-200 rounded-lg p-4">
                  <h4 class="font-medium text-gray-900 mb-2">Ukupno</h4>
                  <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                      <span class="text-gray-500">Glasovi (gore/dolje)</span>
                      <span class="font-medium">{{ stats.upvotes }} / {{ stats.downvotes }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-500">Prijave proizvoda</span>
                      <span class="font-medium">{{ stats.total_reports }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Credits Tab -->
            <div v-if="activeTab === 'credits'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Krediti i transakcije</h3>

              <!-- Credit Breakdown Chart -->
              <div class="bg-gray-50 rounded-lg p-4 mb-6">
                <h4 class="font-medium text-gray-900 mb-3">Potrosnja po kategoriji</h4>
                <div class="space-y-3">
                  <div v-for="(value, action) in creditBreakdown" :key="action" class="flex items-center gap-3">
                    <div class="w-32 text-sm text-gray-600">{{ formatAction(action) }}</div>
                    <div class="flex-1 bg-gray-200 rounded-full h-4 overflow-hidden">
                      <div
                        :class="value < 0 ? 'bg-red-400' : 'bg-green-400'"
                        class="h-full rounded-full transition-all"
                        :style="{ width: `${Math.min(Math.abs(value) / maxCredit * 100, 100)}%` }"
                      ></div>
                    </div>
                    <div :class="value < 0 ? 'text-red-600' : 'text-green-600'" class="w-16 text-right font-medium">
                      {{ value > 0 ? '+' : '' }}{{ value }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Recent Transactions -->
              <h4 class="font-medium text-gray-900 mb-3">Posljednje transakcije</h4>
              <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Datum</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Akcija</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Promjena</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Stanje</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="tx in creditTransactions" :key="tx.id" class="hover:bg-gray-50">
                      <td class="px-4 py-3 text-sm text-gray-500">{{ formatDateTime(tx.created_at) }}</td>
                      <td class="px-4 py-3 text-sm text-gray-900">{{ formatAction(tx.action) }}</td>
                      <td class="px-4 py-3 text-sm text-right" :class="tx.delta < 0 ? 'text-red-600' : 'text-green-600'">
                        {{ tx.delta > 0 ? '+' : '' }}{{ tx.delta }}
                      </td>
                      <td class="px-4 py-3 text-sm text-right text-gray-900">{{ tx.balance_after }}</td>
                    </tr>
                    <tr v-if="!creditTransactions.length">
                      <td colspan="4" class="px-4 py-8 text-center text-gray-500">Nema transakcija</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Searches Tab -->
            <div v-if="activeTab === 'searches'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Posljednje pretrage</h3>
              <div class="space-y-2">
                <div
                  v-for="search in recentSearches"
                  :key="search.id"
                  class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div class="flex items-center gap-3">
                    <Icon name="mdi:magnify" class="w-5 h-5 text-gray-400" />
                    <span class="text-gray-900">{{ search.query }}</span>
                  </div>
                  <span class="text-sm text-gray-500">{{ formatDateTime(search.created_at) }}</span>
                </div>
                <div v-if="!recentSearches.length" class="text-center py-8 text-gray-500">
                  Nema pretraga
                </div>
              </div>
            </div>

            <!-- Engagements Tab -->
            <div v-if="activeTab === 'engagements'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Posljednje interakcije</h3>
              <div class="space-y-2">
                <div
                  v-for="engagement in recentEngagements"
                  :key="engagement.id"
                  class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div class="flex items-center gap-3">
                    <Icon
                      :name="getEngagementIcon(engagement.activity_type)"
                      :class="getEngagementColor(engagement.activity_type)"
                      class="w-5 h-5"
                    />
                    <div>
                      <span class="text-gray-900">{{ engagement.product_title }}</span>
                      <span class="text-gray-500 text-sm ml-2">({{ formatEngagementType(engagement.activity_type) }})</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <span class="text-green-600 text-sm">+{{ engagement.credits_earned }}</span>
                    <span class="text-sm text-gray-500">{{ formatDateTime(engagement.created_at) }}</span>
                  </div>
                </div>
                <div v-if="!recentEngagements.length" class="text-center py-8 text-gray-500">
                  Nema interakcija
                </div>
              </div>
            </div>

            <!-- Favorites Tab -->
            <div v-if="activeTab === 'favorites'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Omiljeni proizvodi</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div
                  v-for="fav in recentFavorites"
                  :key="fav.id"
                  class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div class="w-12 h-12 rounded-lg bg-gray-200 overflow-hidden flex-shrink-0">
                    <img
                      v-if="fav.product_image"
                      :src="getImageUrl(fav.product_image)"
                      :alt="fav.product_title"
                      class="w-full h-full object-cover"
                    />
                    <div v-else class="flex items-center justify-center h-full text-gray-400">
                      <Icon name="mdi:image-off" class="w-6 h-6" />
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900 truncate">{{ fav.product_title }}</div>
                    <div class="text-xs text-gray-500">{{ formatDate(fav.created_at) }}</div>
                  </div>
                </div>
              </div>
              <div v-if="!recentFavorites.length" class="text-center py-8 text-gray-500">
                Nema omiljenih proizvoda
              </div>
            </div>

            <!-- Business Tab -->
            <div v-if="activeTab === 'business'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Clanstvo u biznisima</h3>
              <div class="space-y-3">
                <div
                  v-for="membership in businessMemberships"
                  :key="membership.business_id"
                  class="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div class="flex items-center gap-3">
                    <Icon name="mdi:store" class="w-6 h-6 text-gray-400" />
                    <div>
                      <div class="font-medium text-gray-900">{{ membership.business_name }}</div>
                      <div class="text-sm text-gray-500">Od {{ formatDate(membership.created_at) }}</div>
                    </div>
                  </div>
                  <span :class="getRoleBadgeClass(membership.role)" class="px-3 py-1 text-xs font-medium rounded-full">
                    {{ formatRole(membership.role) }}
                  </span>
                </div>
              </div>
              <div v-if="!businessMemberships.length" class="text-center py-8 text-gray-500">
                Nije clan nijednog biznisa
              </div>
            </div>

            <!-- OTP Tab -->
            <div v-if="activeTab === 'otp'">
              <h3 class="text-lg font-medium text-gray-900 mb-4">OTP Informacije</h3>
              <div v-if="latestOtp" class="bg-gray-50 rounded-lg p-6">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <div class="text-sm text-gray-500">Posljednji kod</div>
                    <div class="text-3xl font-mono font-bold text-indigo-600">{{ latestOtp.code }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">Status</div>
                    <div class="mt-1">
                      <span v-if="latestOtp.is_used" class="px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-600">
                        Iskoristen
                      </span>
                      <span v-else-if="latestOtp.expired" class="px-3 py-1 rounded-full text-sm bg-red-100 text-red-600">
                        Istekao
                      </span>
                      <span v-else class="px-3 py-1 rounded-full text-sm bg-green-100 text-green-600">
                        Aktivan
                      </span>
                    </div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">Kreiran</div>
                    <div class="font-medium text-gray-900">{{ formatDateTime(latestOtp.created_at) }}</div>
                  </div>
                  <div>
                    <div class="text-sm text-gray-500">Istice</div>
                    <div class="font-medium text-gray-900">{{ formatDateTime(latestOtp.expires_at) }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-8 text-gray-500">
                Nema OTP podataka (korisnik nije registrovan putem telefona)
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const route = useRoute()
const config = useRuntimeConfig()
const { get } = useApi()

const userId = route.params.id as string
const isLoading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref('activity')

// Data
const userData = ref<any>(null)
const stats = ref<any>({})
const activityChart = ref<any[]>([])
const creditTransactions = ref<any[]>([])
const creditBreakdown = ref<Record<string, number>>({})
const recentSearches = ref<any[]>([])
const recentEngagements = ref<any[]>([])
const recentFavorites = ref<any[]>([])
const businessMemberships = ref<any[]>([])
const latestOtp = ref<any>(null)

const tabs = [
  { id: 'activity', label: 'Aktivnost', icon: 'mdi:chart-line' },
  { id: 'credits', label: 'Krediti', icon: 'mdi:currency-usd' },
  { id: 'searches', label: 'Pretrage', icon: 'mdi:magnify' },
  { id: 'engagements', label: 'Interakcije', icon: 'mdi:thumb-up' },
  { id: 'favorites', label: 'Omiljeni', icon: 'mdi:heart' },
  { id: 'business', label: 'Biznisi', icon: 'mdi:store' },
  { id: 'otp', label: 'OTP', icon: 'mdi:cellphone-key' },
]

const maxCredit = computed(() => {
  const values = Object.values(creditBreakdown.value).map(Math.abs)
  return Math.max(...values, 1)
})

onMounted(async () => {
  await loadUserProfile()
})

async function loadUserProfile() {
  isLoading.value = true
  error.value = null

  try {
    const data = await get(`/api/admin/users/${userId}/profile`)
    userData.value = data.user
    stats.value = data.stats
    activityChart.value = data.activity_chart
    creditTransactions.value = data.credit_transactions
    creditBreakdown.value = data.credit_breakdown
    recentSearches.value = data.recent_searches
    recentEngagements.value = data.recent_engagements
    recentFavorites.value = data.recent_favorites
    businessMemberships.value = data.business_memberships
    latestOtp.value = data.latest_otp
  } catch (err: any) {
    error.value = err.message || 'Greska pri ucitavanju profila'
    console.error('Error loading user profile:', err)
  } finally {
    isLoading.value = false
  }
}

function getInitials(firstName?: string, lastName?: string, email?: string): string {
  if (firstName) {
    return (firstName[0] + (lastName?.[0] || '')).toUpperCase()
  }
  if (email) {
    return email[0].toUpperCase()
  }
  return '?'
}

function formatDate(dateString: string): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

function formatDateTime(dateString: string): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatAction(action: string): string {
  const actionLabels: Record<string, string> = {
    'ADD_TO_CART': 'Dodaj u korpu',
    'ADD_FAVORITE': 'Dodaj u omiljene',
    'CHECKOUT_SMS': 'SMS checkout',
    'TOP_UP': 'Dopuna',
    'WEEKLY_RESET': 'Tjedni reset',
    'ENGAGEMENT_REWARD': 'Nagrada za interakciju',
    'REFERRAL_BONUS': 'Referral bonus',
    'ADMIN_GRANT': 'Admin dodjela',
  }
  return actionLabels[action] || action
}

function formatEngagementType(type: string): string {
  const types: Record<string, string> = {
    'vote_up': 'Pozitivan glas',
    'vote_down': 'Negativan glas',
    'comment': 'Komentar',
    'report': 'Prijava',
  }
  return types[type] || type
}

function getEngagementIcon(type: string): string {
  const icons: Record<string, string> = {
    'vote_up': 'mdi:thumb-up',
    'vote_down': 'mdi:thumb-down',
    'comment': 'mdi:comment',
    'report': 'mdi:flag',
  }
  return icons[type] || 'mdi:star'
}

function getEngagementColor(type: string): string {
  const colors: Record<string, string> = {
    'vote_up': 'text-green-500',
    'vote_down': 'text-red-500',
    'comment': 'text-blue-500',
    'report': 'text-orange-500',
  }
  return colors[type] || 'text-gray-500'
}

function formatRole(role: string): string {
  const roles: Record<string, string> = {
    'owner': 'Vlasnik',
    'manager': 'Menadzer',
    'staff': 'Osoblje',
  }
  return roles[role] || role
}

function getRoleBadgeClass(role: string): string {
  const classes: Record<string, string> = {
    'owner': 'bg-purple-100 text-purple-800',
    'manager': 'bg-blue-100 text-blue-800',
    'staff': 'bg-gray-100 text-gray-800',
  }
  return classes[role] || 'bg-gray-100 text-gray-800'
}

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${config.public.apiBase}/static/${path}`
}

useSeoMeta({
  title: 'Profil korisnika - Admin - Popust.ba',
  description: 'Detaljan pregled korisnickog profila'
})
</script>
