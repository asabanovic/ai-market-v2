<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- No Business Access -->
      <div v-if="!isLoading && !business" class="bg-white rounded-lg shadow-md p-12 text-center">
        <svg class="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
        </svg>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Nemate pristup biznisu</h2>
        <p class="text-gray-600">Kontaktirajte administratora da vam dodijeli pristup biznisu.</p>
      </div>

      <!-- Loading -->
      <div v-else-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-orange-600">
          <svg class="animate-spin h-8 w-8" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Business Dashboard -->
      <template v-else>
        <!-- Header -->
        <div class="mb-8">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden">
              <img
                v-if="business.logo_path"
                :src="business.logo_path"
                :alt="business.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-2xl font-bold text-gray-400">{{ business.name?.charAt(0) }}</span>
            </div>
            <div>
              <h1 class="text-2xl font-bold text-gray-900">{{ business.name }}</h1>
              <div class="flex items-center gap-2 text-gray-500">
                <span>{{ business.city }}</span>
                <span v-if="business.is_open" class="flex items-center text-green-600">
                  <span class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                  Otvoreno
                </span>
              </div>
            </div>
          </div>
          <p v-if="business.description" class="text-gray-600">{{ business.description }}</p>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="bg-white rounded-lg shadow-md p-4 text-center">
            <div class="text-2xl font-bold text-orange-600">{{ businessStats.active_coupons }}</div>
            <div class="text-sm text-gray-500">Aktivnih kupona</div>
          </div>
          <div class="bg-white rounded-lg shadow-md p-4 text-center">
            <div class="text-2xl font-bold text-green-600">{{ businessStats.total_sold }}</div>
            <div class="text-sm text-gray-500">Prodano</div>
          </div>
          <div class="bg-white rounded-lg shadow-md p-4 text-center">
            <div class="text-2xl font-bold text-blue-600">{{ businessStats.pending_redemptions }}</div>
            <div class="text-sm text-gray-500">Čeka redempciju</div>
          </div>
          <div class="bg-white rounded-lg shadow-md p-4 text-center">
            <div class="text-2xl font-bold text-purple-600">{{ business.average_rating?.toFixed(1) || '0.0' }}</div>
            <div class="text-sm text-gray-500">Prosječna ocjena</div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="bg-white rounded-lg shadow-md mb-6">
          <div class="border-b border-gray-200">
            <nav class="flex -mb-px">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                  'flex-1 py-4 px-4 text-center border-b-2 font-medium text-sm',
                  activeTab === tab.id
                    ? 'border-orange-500 text-orange-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                {{ tab.name }}
              </button>
            </nav>
          </div>
        </div>

        <!-- Tab: My Coupons -->
        <div v-if="activeTab === 'coupons'" class="space-y-6">
          <!-- Create Coupon Button -->
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold text-gray-900">Moji Kuponi</h2>
            <button
              v-if="business.can_create_coupon"
              @click="showCreateModal = true"
              class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              Novi kupon
            </button>
            <span v-else class="text-sm text-gray-500">
              Maksimalan broj kupona ({{ business.max_coupons_allowed }}) dostignut
            </span>
          </div>

          <!-- Coupons List -->
          <div v-if="coupons.length > 0" class="space-y-4">
            <div
              v-for="coupon in coupons"
              :key="coupon.id"
              class="bg-white rounded-lg shadow-md p-6"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="text-2xl font-bold text-orange-600">{{ coupon.discount_percent }}%</span>
                    <h3 class="text-lg font-semibold text-gray-900">{{ coupon.article_name }}</h3>
                    <span
                      :class="[
                        'px-2 py-0.5 text-xs font-medium rounded-full',
                        coupon.is_active && coupon.remaining_quantity > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      ]"
                    >
                      {{ coupon.is_active && coupon.remaining_quantity > 0 ? 'Aktivan' : 'Neaktivan' }}
                    </span>
                  </div>

                  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span class="text-gray-500">Cijena:</span>
                      <span class="font-medium text-green-600 ml-1">{{ coupon.final_price.toFixed(2) }} KM</span>
                    </div>
                    <div>
                      <span class="text-gray-500">Preostalo:</span>
                      <span class="font-medium ml-1">{{ coupon.remaining_quantity }}/{{ coupon.total_quantity }}</span>
                    </div>
                    <div>
                      <span class="text-gray-500">Prodano:</span>
                      <span class="font-medium ml-1">{{ coupon.stats.sold }}</span>
                    </div>
                    <div>
                      <span class="text-gray-500">Iskorišteno:</span>
                      <span class="font-medium ml-1">{{ coupon.stats.redeemed }}</span>
                    </div>
                  </div>
                </div>

                <button
                  @click="toggleCouponActive(coupon)"
                  :class="[
                    'px-3 py-1 text-sm rounded',
                    coupon.is_active ? 'text-gray-600 hover:bg-gray-100' : 'text-green-600 hover:bg-green-50'
                  ]"
                >
                  {{ coupon.is_active ? 'Deaktiviraj' : 'Aktiviraj' }}
                </button>
              </div>
            </div>
          </div>

          <div v-else class="bg-white rounded-lg shadow-md p-12 text-center">
            <p class="text-gray-500">Nemate kreirane kupone.</p>
          </div>
        </div>

        <!-- Tab: Pending Redemptions -->
        <div v-else-if="activeTab === 'pending'" class="space-y-6">
          <h2 class="text-lg font-semibold text-gray-900">Kuponi koji čekaju redempciju</h2>

          <!-- Redemption Input -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="font-medium text-gray-900 mb-4">Unesi kod kupona</h3>
            <div class="flex gap-3">
              <input
                v-model="redemptionCode"
                type="text"
                maxlength="6"
                placeholder="6-cifreni kod"
                class="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-2xl font-mono tracking-widest text-center"
                @input="redemptionCode = redemptionCode.replace(/\D/g, '')"
              />
              <button
                @click="redeemCoupon"
                :disabled="redemptionCode.length !== 6"
                class="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 font-medium"
              >
                Potvrdi
              </button>
            </div>
            <p v-if="redemptionError" class="text-red-600 text-sm mt-2">{{ redemptionError }}</p>
            <p v-if="redemptionSuccess" class="text-green-600 text-sm mt-2">{{ redemptionSuccess }}</p>
          </div>

          <!-- Pending List -->
          <div v-if="pendingRedemptions.length > 0" class="space-y-4">
            <div
              v-for="pending in pendingRedemptions"
              :key="pending.id"
              class="bg-white rounded-lg shadow-md p-4 flex items-center justify-between"
            >
              <div>
                <div class="font-medium text-gray-900">{{ pending.coupon.article_name }}</div>
                <div class="text-sm text-gray-500">
                  {{ pending.user.name }} · Kod: <span class="font-mono font-bold">{{ pending.redemption_code }}</span>
                </div>
                <div class="text-xs text-gray-400">Kupljeno: {{ formatDate(pending.purchased_at) }}</div>
              </div>
              <button
                @click="quickRedeem(pending.redemption_code)"
                class="px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600"
              >
                Potvrdi
              </button>
            </div>
          </div>

          <div v-else class="bg-white rounded-lg shadow-md p-12 text-center">
            <p class="text-gray-500">Nema kupona koji čekaju redempciju.</p>
          </div>
        </div>

        <!-- Tab: Completed -->
        <div v-else-if="activeTab === 'completed'" class="bg-white rounded-lg shadow-md p-12 text-center">
          <p class="text-gray-500">Pregled završenih transakcija uskoro...</p>
        </div>

        <!-- Create Coupon Modal -->
        <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
          <div class="flex items-center justify-center min-h-screen px-4">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreateModal = false"></div>
            <div class="relative bg-white rounded-lg max-w-md w-full p-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">Kreiraj novi kupon</h3>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Naziv artikla *</label>
                  <input
                    v-model="newCoupon.article_name"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="npr. 1kg Mljeveno meso"
                  />
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Cijena (KM) *</label>
                    <input
                      v-model.number="newCoupon.normal_price"
                      type="number"
                      step="0.01"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Popust (%) *</label>
                    <input
                      v-model.number="newCoupon.discount_percent"
                      type="number"
                      min="1"
                      max="99"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Broj kupona *</label>
                    <input
                      v-model.number="newCoupon.total_quantity"
                      type="number"
                      min="1"
                      max="100"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Validnost (dana) *</label>
                    <select v-model.number="newCoupon.valid_days" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                      <option v-for="d in 10" :key="d" :value="d">{{ d }}</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Količina</label>
                  <input
                    v-model="newCoupon.quantity_description"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="npr. 1kg, 500g"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Opis</label>
                  <textarea
                    v-model="newCoupon.description"
                    rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  ></textarea>
                </div>

                <!-- Preview -->
                <div v-if="newCoupon.normal_price && newCoupon.discount_percent" class="bg-orange-50 rounded-lg p-3 text-sm">
                  <div class="font-medium text-orange-800">Pregled:</div>
                  <div>Finalna cijena: <span class="font-bold text-green-600">{{ calculateFinalPrice() }} KM</span></div>
                  <div>Ušteda: {{ calculateSavings() }} KM</div>
                </div>
              </div>

              <div class="mt-6 flex gap-3 justify-end">
                <button
                  @click="showCreateModal = false"
                  class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Otkaži
                </button>
                <button
                  @click="createCoupon"
                  :disabled="!isValidCoupon"
                  class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
                >
                  Kreiraj
                </button>
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
  middleware: ['auth']
})

const { get, post, put } = useApi()

const isLoading = ref(true)
const business = ref<any>(null)
const coupons = ref<any[]>([])
const pendingRedemptions = ref<any[]>([])
const businessStats = ref({
  active_coupons: 0,
  total_sold: 0,
  pending_redemptions: 0
})

const activeTab = ref('coupons')
const tabs = [
  { id: 'coupons', name: 'Moji Kuponi' },
  { id: 'pending', name: 'Čekaju Redempciju' },
  { id: 'completed', name: 'Završeno' }
]

// Redemption
const redemptionCode = ref('')
const redemptionError = ref('')
const redemptionSuccess = ref('')

// Create coupon
const showCreateModal = ref(false)
const newCoupon = ref({
  article_name: '',
  normal_price: 0,
  discount_percent: 50,
  total_quantity: 5,
  valid_days: 7,
  quantity_description: '',
  description: ''
})

const isValidCoupon = computed(() => {
  return newCoupon.value.article_name &&
    newCoupon.value.normal_price > 0 &&
    newCoupon.value.discount_percent >= 1 &&
    newCoupon.value.discount_percent <= 99 &&
    newCoupon.value.total_quantity >= 1
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  isLoading.value = true
  try {
    // Get user's business membership
    const membershipRes = await get('/api/user/business-membership')
    if (!membershipRes.business) {
      business.value = null
      return
    }

    business.value = membershipRes.business

    // Load coupons
    const couponsRes = await get(`/api/business/${business.value.id}/coupons`)
    coupons.value = couponsRes.coupons || []
    business.value = { ...business.value, ...couponsRes.business }

    // Calculate stats
    businessStats.value.active_coupons = coupons.value.filter(c => c.is_active && c.remaining_quantity > 0).length
    businessStats.value.total_sold = coupons.value.reduce((acc, c) => acc + c.stats.sold, 0)
    businessStats.value.pending_redemptions = coupons.value.reduce((acc, c) => acc + c.stats.pending, 0)

    // Load pending redemptions
    const pendingRes = await get(`/api/business/${business.value.id}/pending-coupons`)
    pendingRedemptions.value = pendingRes.pending || []
  } catch (error) {
    console.error('Error loading data:', error)
    business.value = null
  } finally {
    isLoading.value = false
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('bs-BA', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function calculateFinalPrice() {
  const price = newCoupon.value.normal_price * (1 - newCoupon.value.discount_percent / 100)
  return price.toFixed(2)
}

function calculateSavings() {
  const savings = newCoupon.value.normal_price - parseFloat(calculateFinalPrice())
  return savings.toFixed(2)
}

async function createCoupon() {
  if (!isValidCoupon.value || !business.value) return

  try {
    await post(`/api/business/${business.value.id}/coupons`, newCoupon.value)
    showCreateModal.value = false
    newCoupon.value = {
      article_name: '',
      normal_price: 0,
      discount_percent: 50,
      total_quantity: 5,
      valid_days: 7,
      quantity_description: '',
      description: ''
    }
    await loadData()
  } catch (error: any) {
    alert(error.response?.data?.error || 'Greška pri kreiranju kupona')
  }
}

async function toggleCouponActive(coupon: any) {
  try {
    await put(`/api/business/${business.value.id}/coupons/${coupon.id}`, {
      is_active: !coupon.is_active
    })
    await loadData()
  } catch (error) {
    console.error('Error toggling coupon:', error)
  }
}

async function redeemCoupon() {
  if (redemptionCode.value.length !== 6 || !business.value) return

  redemptionError.value = ''
  redemptionSuccess.value = ''

  try {
    const res = await post(`/api/business/${business.value.id}/redeem`, {
      code: redemptionCode.value
    })
    redemptionSuccess.value = `Kupon uspješno iskorišten! ${res.user_coupon.user_name} - ${res.user_coupon.article_name}`
    redemptionCode.value = ''
    await loadData()
  } catch (error: any) {
    redemptionError.value = error.response?.data?.error || 'Greška pri redempciji'
  }
}

async function quickRedeem(code: string) {
  redemptionCode.value = code
  await redeemCoupon()
}

useSeoMeta({
  title: 'Moj Biznis - Popust.ba',
})
</script>
