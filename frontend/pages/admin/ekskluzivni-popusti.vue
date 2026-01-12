<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Ekskluzivni Popusti</h1>
          <p class="mt-1 text-sm text-gray-600">Upravljanje kuponima i biznisima</p>
        </div>
        <NuxtLink
          to="/admin"
          class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          ← Nazad
        </NuxtLink>
      </div>

      <!-- Feature Flag Toggle -->
      <div class="mb-6 bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-medium text-gray-900">Status feature-a</h3>
            <p class="text-sm text-gray-500">Kontroliši vidljivost ekskluzivnih popusta za korisnike</p>
          </div>
          <div class="flex items-center gap-4">
            <span :class="featureEnabled ? 'text-green-600' : 'text-gray-500'" class="text-sm font-medium">
              {{ featureEnabled ? 'UKLJUČENO' : 'ISKLJUČENO' }}
            </span>
            <button
              @click="toggleFeature"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2',
                featureEnabled ? 'bg-orange-500' : 'bg-gray-200'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  featureEnabled ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>
        </div>
        <p v-if="!featureEnabled" class="mt-3 text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
          ⚠️ Feature je isključen - samo admin korisnici mogu vidjeti ekskluzivne popuste
        </p>
      </div>

      <!-- Stats -->
      <div v-if="stats" class="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ stats.total_coupons }}</div>
          <div class="text-sm text-gray-500">Ukupno kupona</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div class="text-2xl font-bold text-green-600">{{ stats.active_coupons }}</div>
          <div class="text-sm text-gray-500">Aktivnih</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ stats.total_sold }}</div>
          <div class="text-sm text-gray-500">Prodano</div>
        </div>
        <div class="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div class="text-2xl font-bold text-purple-600">{{ stats.redemption_rate }}%</div>
          <div class="text-sm text-gray-500">Iskorišteno</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mb-6 border-b border-gray-200">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              activeTab === tab.id
                ? 'border-orange-500 text-orange-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            {{ tab.name }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-orange-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Businesses Tab -->
      <div v-else-if="activeTab === 'businesses'" class="space-y-6">
        <!-- Enable Business Modal Trigger -->
        <div class="flex justify-end">
          <button
            @click="showEnableModal = true"
            class="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Omogući biznis
          </button>
        </div>

        <!-- Businesses List -->
        <div v-if="businesses.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Nema biznisa sa ekskluzivnim kuponima</h3>
          <p class="mt-1 text-sm text-gray-500">Klikni "Omogući biznis" da dodaš prvi.</p>
        </div>

        <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Biznis</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tip</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kuponi</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ocjena</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="business in businesses" :key="business.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="text-sm font-medium text-gray-900">{{ business.name }}</div>
                  </div>
                  <div class="text-sm text-gray-500">{{ business.city }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full" :class="business.business_type === 'local_business' ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800'">
                    {{ business.business_type === 'local_business' ? 'Lokalni' : 'Supermarket' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ business.active_coupons }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <input
                    type="number"
                    :value="business.max_coupons_allowed"
                    @change="updateMaxCoupons(business.id, $event)"
                    class="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                    min="1"
                    max="100"
                  />
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <span class="text-sm text-gray-900">{{ business.average_rating.toFixed(1) }}</span>
                    <svg class="w-4 h-4 text-yellow-400 ml-1" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <span class="text-xs text-gray-500 ml-1">({{ business.total_reviews }})</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span v-if="business.is_open" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-1.5 animate-pulse"></span>
                    Otvoreno
                  </span>
                  <span v-else-if="business.is_open === false" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Zatvoreno
                  </span>
                  <span v-else class="text-xs text-gray-400">-</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    @click="manageBusiness(business)"
                    class="text-orange-600 hover:text-orange-900 mr-3"
                  >
                    Upravljaj
                  </button>
                  <button
                    @click="disableBusiness(business.id)"
                    class="text-red-600 hover:text-red-900"
                  >
                    Onemogući
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Coupons Tab -->
      <div v-else-if="activeTab === 'coupons'" class="space-y-6">
        <div v-if="allCoupons.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Nema kupona</h3>
          <p class="mt-1 text-sm text-gray-500">Prvo omogući biznise pa kreiraj kupone.</p>
        </div>

        <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Artikal</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Biznis</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Popust</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cijena</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Preostalo</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="coupon in allCoupons" :key="coupon.id" class="hover:bg-gray-50">
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{{ coupon.article_name }}</div>
                  <div class="text-xs text-gray-500">{{ coupon.valid_days }} dana validnosti</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ coupon.business.name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-lg font-bold text-orange-600">{{ coupon.discount_percent }}%</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-500 line-through">{{ coupon.normal_price }} KM</div>
                  <div class="text-sm font-medium text-green-600">{{ coupon.final_price }} KM</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm">{{ coupon.remaining_quantity }}/{{ coupon.total_quantity }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span v-if="coupon.is_active && coupon.remaining_quantity > 0" class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Aktivan</span>
                  <span v-else-if="coupon.remaining_quantity === 0" class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">Rasprodan</span>
                  <span v-else class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">Neaktivan</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    @click="toggleCouponActive(coupon)"
                    :class="coupon.is_active ? 'text-gray-600 hover:text-gray-900' : 'text-green-600 hover:text-green-900'"
                  >
                    {{ coupon.is_active ? 'Deaktiviraj' : 'Aktiviraj' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Transactions Tab -->
      <div v-else-if="activeTab === 'transactions'" class="space-y-6">
        <!-- Status Filter -->
        <div class="flex justify-end">
          <select v-model="transactionFilter" @change="loadTransactions" class="px-3 py-2 border border-gray-300 rounded-md text-sm">
            <option value="">Sve transakcije</option>
            <option value="active">Aktivne</option>
            <option value="redeemed">Iskorištene</option>
            <option value="expired">Istekle</option>
          </select>
        </div>

        <div v-if="transactions.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Nema transakcija</h3>
          <p class="mt-1 text-sm text-gray-500">Još nema kupljenih kupona.</p>
        </div>

        <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kupon</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Biznis</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kod</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kupljeno</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="tx in transactions" :key="tx.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900" data-pii>{{ tx.user?.display_name || 'N/A' }}</div>
                  <div class="text-xs text-gray-500" data-pii>{{ tx.user?.email }}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="text-sm font-medium text-gray-900">{{ tx.coupon?.article_name }}</div>
                  <div class="text-xs text-gray-500">{{ tx.coupon?.discount_percent }}% popust · {{ tx.coupon?.final_price }} KM</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ tx.business?.name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <code class="px-2 py-1 bg-gray-100 rounded text-xs font-mono">{{ tx.redemption_code }}</code>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(tx.purchased_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span v-if="tx.status === 'active'" class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Aktivan</span>
                  <span v-else-if="tx.status === 'redeemed'" class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">Iskorišten</span>
                  <span v-else-if="tx.status === 'expired'" class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">Istekao</span>
                  <span v-else class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600">{{ tx.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div v-if="transactionsPagination && transactionsPagination.pages > 1" class="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
            <div class="text-sm text-gray-500">
              Prikazano {{ transactions.length }} od {{ transactionsPagination.total }} transakcija
            </div>
            <div class="flex gap-2">
              <button
                @click="loadTransactions(transactionsPagination.page - 1)"
                :disabled="!transactionsPagination.has_prev"
                class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Prethodna
              </button>
              <button
                @click="loadTransactions(transactionsPagination.page + 1)"
                :disabled="!transactionsPagination.has_next"
                class="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Sljedeća
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Enable Business Modal -->
      <div v-if="showEnableModal" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="showEnableModal = false"></div>
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
          <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
            <div>
              <h3 class="text-lg font-medium text-gray-900 mb-4">Omogući biznis za ekskluzivne kupone</h3>

              <!-- Search businesses -->
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">Pretraži biznise</label>
                <input
                  v-model="businessSearch"
                  type="text"
                  placeholder="Naziv biznisa..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                  @input="searchBusinesses"
                />
              </div>

              <!-- Business results -->
              <div v-if="searchResults.length > 0" class="mb-4 max-h-48 overflow-y-auto border border-gray-200 rounded-md">
                <button
                  v-for="b in searchResults"
                  :key="b.id"
                  @click="selectBusiness(b)"
                  class="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
                  :class="selectedBusiness?.id === b.id ? 'bg-orange-50' : ''"
                >
                  <div>
                    <div class="text-sm font-medium text-gray-900">{{ b.name }}</div>
                    <div class="text-xs text-gray-500">{{ b.city }}</div>
                  </div>
                  <svg v-if="selectedBusiness?.id === b.id" class="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>

              <!-- Business settings -->
              <div v-if="selectedBusiness" class="space-y-4 border-t pt-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Tip biznisa</label>
                  <select v-model="newBusinessSettings.business_type" class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white">
                    <option value="local_business">Lokalni biznis (mesnica, pekara...)</option>
                    <option value="supermarket">Supermarket</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Maksimalan broj kupona</label>
                  <input
                    v-model.number="newBusinessSettings.max_coupons_allowed"
                    type="number"
                    min="1"
                    max="100"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Opis biznisa</label>
                  <textarea
                    v-model="newBusinessSettings.description"
                    rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                    placeholder="Kratki opis biznisa..."
                  ></textarea>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Adresa</label>
                  <input
                    v-model="newBusinessSettings.address"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                    placeholder="Ulica i broj, grad"
                  />
                </div>
              </div>
            </div>
            <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
              <button
                @click="enableBusiness"
                :disabled="!selectedBusiness"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-orange-500 text-base font-medium text-white hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 sm:col-start-2 sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Omogući
              </button>
              <button
                @click="showEnableModal = false"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 sm:mt-0 sm:col-start-1 sm:text-sm"
              >
                Otkaži
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Manage Business Modal -->
      <div v-if="showManageModal && managingBusiness" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="showManageModal = false"></div>
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
          <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
            <div>
              <h3 class="text-lg font-medium text-gray-900 mb-4">{{ managingBusiness.name }}</h3>

              <!-- Business Coupons -->
              <div class="mb-6">
                <div class="flex items-center justify-between mb-4">
                  <h4 class="font-medium text-gray-700">Kuponi biznisa</h4>
                  <button
                    @click="showCreateCouponForm = !showCreateCouponForm"
                    class="text-sm text-orange-600 hover:text-orange-700"
                  >
                    {{ showCreateCouponForm ? 'Otkaži' : '+ Kreiraj kupon' }}
                  </button>
                </div>

                <!-- Campaign Section -->
                <div v-if="showCreateCouponForm" class="bg-blue-50 rounded-lg p-4 mb-4">
                  <div class="flex items-center justify-between mb-3">
                    <h5 class="font-medium text-gray-700">Kampanja *</h5>
                    <button
                      v-if="!showCreateCampaignForm"
                      @click="showCreateCampaignForm = true"
                      class="text-sm text-blue-600 hover:text-blue-700"
                    >
                      + Nova kampanja
                    </button>
                  </div>

                  <!-- Create Campaign Form -->
                  <div v-if="showCreateCampaignForm" class="mb-3">
                    <div class="flex gap-2">
                      <input
                        v-model="newCampaignName"
                        type="text"
                        placeholder="Naziv kampanje (npr. Božićna akcija)"
                        class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                      />
                      <button
                        @click="createCampaign"
                        :disabled="!newCampaignName.trim()"
                        class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
                      >
                        Kreiraj
                      </button>
                      <button
                        @click="showCreateCampaignForm = false; newCampaignName = ''"
                        class="px-3 py-2 text-gray-600 hover:text-gray-800"
                      >
                        Otkaži
                      </button>
                    </div>
                  </div>

                  <!-- Campaign Selector -->
                  <div v-if="campaigns.length > 0">
                    <select
                      v-model="newCoupon.campaign_id"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                    >
                      <option :value="null" disabled>Odaberi kampanju</option>
                      <option v-for="c in campaigns" :key="c.id" :value="c.id">
                        {{ c.name }}
                      </option>
                    </select>
                  </div>

                  <!-- No Campaigns -->
                  <div v-else-if="!showCreateCampaignForm" class="text-sm text-gray-500">
                    Nema kampanja. Kreirajte novu kampanju da biste mogli dodati kupone.
                  </div>
                </div>

                <!-- Create Coupon Form -->
                <div v-if="showCreateCouponForm && newCoupon.campaign_id" class="bg-gray-50 rounded-lg p-4 mb-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div class="col-span-2">
                      <label class="block text-sm font-medium text-gray-700 mb-1">Naziv artikla *</label>
                      <input
                        v-model="newCoupon.article_name"
                        type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                        placeholder="npr. 1kg Mljeveno meso"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Normalna cijena (KM) *</label>
                      <input
                        v-model.number="newCoupon.normal_price"
                        type="number"
                        step="0.01"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Popust (%) *</label>
                      <input
                        v-model.number="newCoupon.discount_percent"
                        type="number"
                        min="1"
                        max="99"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Broj kupona *</label>
                      <input
                        v-model.number="newCoupon.total_quantity"
                        type="number"
                        min="1"
                        max="100"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Validnost (dana) *</label>
                      <select v-model.number="newCoupon.valid_days" class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white">
                        <option v-for="d in 30" :key="d" :value="d">{{ d }} {{ d === 1 ? 'dan' : 'dana' }}</option>
                      </select>
                      <p v-if="newCoupon.valid_days" class="text-xs text-gray-500 mt-1">
                        Ističe: {{ getExpiryDate(newCoupon.valid_days) }}
                        <span v-if="isSunday(newCoupon.valid_days)" class="text-amber-600">
                          (Nedjelja - razmisli o ponedjeljku)
                        </span>
                      </p>
                    </div>
                    <div class="col-span-2">
                      <label class="block text-sm font-medium text-gray-700 mb-1">Količina (opis)</label>
                      <input
                        v-model="newCoupon.quantity_description"
                        type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                        placeholder="npr. 1kg, 500g, 1 komad"
                      />
                    </div>
                    <div class="col-span-2">
                      <label class="block text-sm font-medium text-gray-700 mb-1">Opis</label>
                      <textarea
                        v-model="newCoupon.description"
                        rows="2"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                        placeholder="Dodatne informacije o ponudi..."
                      ></textarea>
                    </div>
                  </div>
                  <div class="mt-4 flex justify-end">
                    <button
                      @click="createCoupon"
                      :disabled="!isValidCoupon"
                      class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Kreiraj kupon
                    </button>
                  </div>
                </div>

                <!-- Existing Coupons -->
                <div v-if="businessCoupons.length > 0" class="space-y-2">
                  <div
                    v-for="coupon in businessCoupons"
                    :key="coupon.id"
                    class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div class="font-medium text-gray-900">{{ coupon.article_name }}</div>
                      <div class="text-sm text-gray-500">
                        {{ coupon.discount_percent }}% popust · {{ coupon.remaining_quantity }}/{{ coupon.total_quantity }} preostalo
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <span v-if="coupon.is_active" class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">Aktivan</span>
                      <span v-else class="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">Neaktivan</span>
                    </div>
                  </div>
                </div>
                <div v-else class="text-center py-4 text-gray-500 text-sm">
                  Nema kupona za ovaj biznis
                </div>
              </div>
            </div>
            <div class="mt-5 sm:mt-6">
              <button
                @click="showManageModal = false"
                class="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50"
              >
                Zatvori
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin']
})

const { get, post, put } = useApi()

const isLoading = ref(true)
const featureEnabled = ref(false)
const stats = ref<any>(null)
const businesses = ref<any[]>([])
const allCoupons = ref<any[]>([])
const businessCoupons = ref<any[]>([])
const transactions = ref<any[]>([])
const transactionFilter = ref('')
const transactionsPagination = ref<any>(null)

const activeTab = ref('businesses')
const tabs = [
  { id: 'businesses', name: 'Biznisi' },
  { id: 'coupons', name: 'Svi kuponi' },
  { id: 'transactions', name: 'Transakcije' }
]

// Modals
const showEnableModal = ref(false)
const showManageModal = ref(false)
const showCreateCouponForm = ref(false)

// Enable business
const businessSearch = ref('')
const searchResults = ref<any[]>([])
const selectedBusiness = ref<any>(null)
const newBusinessSettings = ref({
  business_type: 'local_business',
  max_coupons_allowed: 20,
  description: '',
  address: ''
})

// Manage business
const managingBusiness = ref<any>(null)

// Campaigns
const campaigns = ref<any[]>([])
const selectedCampaignId = ref<number | null>(null)
const showCreateCampaignForm = ref(false)
const newCampaignName = ref('')

// New coupon
const newCoupon = ref({
  article_name: '',
  normal_price: 0,
  discount_percent: 50,
  total_quantity: 5,
  valid_days: 7,
  quantity_description: '',
  description: '',
  campaign_id: null as number | null
})

const isValidCoupon = computed(() => {
  return newCoupon.value.article_name &&
    newCoupon.value.normal_price > 0 &&
    newCoupon.value.discount_percent >= 1 &&
    newCoupon.value.discount_percent <= 99 &&
    newCoupon.value.total_quantity >= 1 &&
    newCoupon.value.valid_days >= 1 &&
    newCoupon.value.campaign_id
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  isLoading.value = true
  try {
    const [flagsRes, statsRes, businessesRes, couponsRes, transactionsRes] = await Promise.all([
      get('/api/admin/feature-flags'),
      get('/api/admin/coupons/stats'),
      get('/api/admin/businesses/with-coupons'),
      get('/api/admin/all-coupons'),
      get('/api/admin/all-transactions')
    ])

    const flag = flagsRes.flags?.find((f: any) => f.key === 'exclusive_coupons_enabled')
    featureEnabled.value = flag?.value || false
    stats.value = statsRes.stats
    businesses.value = businessesRes.businesses || []
    allCoupons.value = couponsRes.coupons || []
    transactions.value = transactionsRes.transactions || []
    transactionsPagination.value = transactionsRes.pagination
  } catch (error) {
    console.error('Error loading data:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadTransactions(page: number = 1) {
  try {
    let url = `/api/admin/all-transactions?page=${page}`
    if (transactionFilter.value) {
      url += `&status=${transactionFilter.value}`
    }
    const res = await get(url)
    transactions.value = res.transactions || []
    transactionsPagination.value = res.pagination
  } catch (error) {
    console.error('Error loading transactions:', error)
    transactions.value = []
  }
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function toggleFeature() {
  try {
    await put('/api/admin/feature-flags/exclusive_coupons_enabled', {
      value: !featureEnabled.value
    })
    featureEnabled.value = !featureEnabled.value
  } catch (error) {
    console.error('Error toggling feature:', error)
  }
}

async function searchBusinesses() {
  if (businessSearch.value.length < 2) {
    searchResults.value = []
    return
  }
  try {
    // Search all businesses
    const res = await get(`/api/businesses?search=${encodeURIComponent(businessSearch.value)}`)
    // Filter out ones that already have coupons enabled
    const enabledIds = new Set(businesses.value.map((b: any) => b.id))
    searchResults.value = (res.businesses || []).filter((b: any) => !enabledIds.has(b.id))
  } catch (error) {
    console.error('Error searching businesses:', error)
  }
}

function selectBusiness(business: any) {
  selectedBusiness.value = business
}

async function enableBusiness() {
  if (!selectedBusiness.value) return
  try {
    await post(`/api/admin/businesses/${selectedBusiness.value.id}/enable-coupons`, newBusinessSettings.value)
    showEnableModal.value = false
    selectedBusiness.value = null
    businessSearch.value = ''
    searchResults.value = []
    newBusinessSettings.value = {
      business_type: 'local_business',
      max_coupons_allowed: 20,
      description: '',
      address: ''
    }
    await loadData()
  } catch (error) {
    console.error('Error enabling business:', error)
  }
}

async function disableBusiness(businessId: number) {
  if (!confirm('Jesi li siguran da želiš onemogućiti ekskluzivne kupone za ovaj biznis?')) return
  try {
    await post(`/api/admin/businesses/${businessId}/disable-coupons`, {})
    await loadData()
  } catch (error) {
    console.error('Error disabling business:', error)
  }
}

async function updateMaxCoupons(businessId: number, event: Event) {
  const value = parseInt((event.target as HTMLInputElement).value)
  if (isNaN(value) || value < 1) return
  try {
    await post(`/api/admin/businesses/${businessId}/enable-coupons`, {
      max_coupons_allowed: value
    })
  } catch (error) {
    console.error('Error updating max coupons:', error)
  }
}

async function manageBusiness(business: any) {
  managingBusiness.value = business
  showManageModal.value = true
  showCreateCouponForm.value = false
  showCreateCampaignForm.value = false
  selectedCampaignId.value = null
  newCampaignName.value = ''

  try {
    // Load campaigns and coupons in parallel
    const [couponsRes, campaignsRes] = await Promise.all([
      get(`/api/business/${business.id}/coupons`),
      get(`/api/business/${business.id}/campaigns`)
    ])
    businessCoupons.value = couponsRes.coupons || []
    campaigns.value = campaignsRes.campaigns || []

    // Auto-select first campaign if exists
    if (campaigns.value.length > 0) {
      selectedCampaignId.value = campaigns.value[0].id
      newCoupon.value.campaign_id = campaigns.value[0].id
    }
  } catch (error) {
    console.error('Error loading business data:', error)
    businessCoupons.value = []
    campaigns.value = []
  }
}

async function createCampaign() {
  if (!managingBusiness.value || !newCampaignName.value.trim()) return
  try {
    const res = await post(`/api/business/${managingBusiness.value.id}/campaigns`, {
      name: newCampaignName.value.trim()
    })

    // Add to campaigns list and select it
    campaigns.value.push(res.campaign)
    selectedCampaignId.value = res.campaign.id
    newCoupon.value.campaign_id = res.campaign.id

    // Reset form
    newCampaignName.value = ''
    showCreateCampaignForm.value = false
  } catch (error) {
    console.error('Error creating campaign:', error)
  }
}

async function createCoupon() {
  if (!managingBusiness.value || !isValidCoupon.value) return
  try {
    await post(`/api/business/${managingBusiness.value.id}/coupons`, newCoupon.value)

    // Reset form but keep campaign_id
    const currentCampaignId = newCoupon.value.campaign_id
    newCoupon.value = {
      article_name: '',
      normal_price: 0,
      discount_percent: 50,
      total_quantity: 5,
      valid_days: 7,
      quantity_description: '',
      description: '',
      campaign_id: currentCampaignId
    }
    showCreateCouponForm.value = false

    // Reload coupons
    const res = await get(`/api/business/${managingBusiness.value.id}/coupons`)
    businessCoupons.value = res.coupons || []
    await loadData()
  } catch (error: any) {
    console.error('Error creating coupon:', error)
    alert(error.response?.data?.error || 'Greška pri kreiranju kupona')
  }
}

async function toggleCouponActive(coupon: any) {
  try {
    await put(`/api/business/${coupon.business.id}/coupons/${coupon.id}`, {
      is_active: !coupon.is_active
    })
    await loadData()
  } catch (error) {
    console.error('Error toggling coupon:', error)
  }
}

function getExpiryDate(days: number): string {
  const date = new Date()
  date.setDate(date.getDate() + days)

  const dani = ['Nedjelja', 'Ponedjeljak', 'Utorak', 'Srijeda', 'Četvrtak', 'Petak', 'Subota']
  const mjeseci = ['Januar', 'Februar', 'Mart', 'April', 'Maj', 'Juni', 'Juli', 'August', 'Septembar', 'Oktobar', 'Novembar', 'Decembar']

  const dan = dani[date.getDay()]
  const datum = date.getDate()
  const mjesec = mjeseci[date.getMonth()]
  const godina = date.getFullYear()

  return `${dan}, ${datum}. ${mjesec}, ${godina}`
}

function isSunday(days: number): boolean {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.getDay() === 0
}

useSeoMeta({
  title: 'Ekskluzivni Popusti - Admin - Popust.ba',
})
</script>
