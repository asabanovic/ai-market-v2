<template>
  <div class="bg-gray-50 py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Moj profil</h1>
        <p class="text-gray-600">Upravljajte vašim nalogom i preferencijama</p>
      </div>

      <!-- Success Message -->
      <div v-if="showSuccess" class="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-green-700">Profil je uspješno ažuriran</p>
          </div>
        </div>
      </div>

      <!-- Profile Edit Form -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-gray-900">Osnovne informacije</h2>
          <button
            v-if="!isEditMode"
            @click="isEditMode = true"
            type="button"
            class="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700"
          >
            Uredi profil
          </button>
        </div>

        <!-- View Mode -->
        <div v-if="!isEditMode">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Ime</label>
              <p class="text-gray-900">{{ user?.first_name || 'Nije uneseno' }}</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Prezime</label>
              <p class="text-gray-900">{{ user?.last_name || 'Nije uneseno' }}</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <p class="text-gray-900">{{ user?.email || 'Nije uneseno' }}</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Grad</label>
              <p class="text-gray-900">{{ user?.city || 'Nije uneseno' }}</p>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else>
          <form @submit.prevent="handleSubmit">
            <!-- Error Message -->
            <div v-if="showError" class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <div class="flex">
                <div class="flex-shrink-0">
                  <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-red-700">{{ errorMessage }}</p>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="first_name" class="block text-sm font-medium text-gray-700 mb-1">Ime *</label>
                <input
                  type="text"
                  id="first_name"
                  v-model="formData.first_name"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label for="last_name" class="block text-sm font-medium text-gray-700 mb-1">Prezime</label>
                <input
                  type="text"
                  id="last_name"
                  v-model="formData.last_name"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p class="text-gray-900 py-2">{{ user?.email || 'Nije uneseno' }}</p>
                <p class="text-xs text-gray-500">Email se ne može mijenjati</p>
              </div>

              <div>
                <label for="city" class="block text-sm font-medium text-gray-700 mb-1">Grad *</label>
                <select
                  id="city"
                  v-model="formData.city"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="">Odaberite grad</option>
                  <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
                </select>
                <p class="text-xs text-gray-500 mt-1">Grad je obavezan za personalizirane rezultate pretrage</p>
              </div>
            </div>

            <div class="mt-6 flex space-x-4">
              <button
                type="submit"
                :disabled="isSubmitting"
                class="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {{ isSubmitting ? 'Čuva se...' : 'Sačuvaj promjene' }}
              </button>
              <button
                type="button"
                @click="cancelEdit"
                class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400"
              >
                Otkaži
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Package Info -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Vaš paket</h2>
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-medium text-gray-900">{{ packageInfo?.name || 'Free' }}</h3>
            <p class="text-gray-600">
              {{ packageInfo?.daily_limit || 10 }} pretraga sedmično
            </p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-600">Danas ste koristili:</p>
            <p class="text-2xl font-bold text-indigo-600">
              {{ searchCounts?.used || 0 }}/{{ searchCounts?.daily_limit || 10 }}
            </p>
          </div>
        </div>

        <div
          v-if="searchCounts && searchCounts.remaining === 0"
          class="mt-4 p-3 bg-yellow-100 text-yellow-800 rounded-md"
        >
          <p class="text-sm">
            Iskoristili ste sve sedmične pretrage. Nadogradite paket ili se vratite sljedeće sedmice za nove pretrage.
          </p>
        </div>
      </div>

      <!-- Organization Section -->
      <div v-if="hasOrganization" class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
              <Icon name="mdi:store" class="w-7 h-7 text-purple-600" />
            </div>
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ organizationName }}</h2>
              <p class="text-gray-600">Upravljajte proizvodima vaše organizacije</p>
            </div>
          </div>
          <NuxtLink
            to="/moja-organizacija"
            class="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 flex items-center gap-2"
          >
            <Icon name="mdi:arrow-right" class="w-4 h-4" />
            Otvori
          </NuxtLink>
        </div>
      </div>

      <!-- Store Preferences -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Omiljene prodavnice</h2>
            <p class="text-sm text-gray-600 mt-1">Odaberite prodavnice koje želite uključiti u pretragu</p>
          </div>
          <button
            v-if="hasStoreChanges"
            @click="saveStorePreferences"
            :disabled="isSavingStores"
            class="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
          >
            {{ isSavingStores ? 'Čuvanje...' : 'Sačuvaj' }}
          </button>
        </div>

        <div v-if="loadingStores" class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
          <p class="text-gray-600 mt-2">Učitavanje prodavnica...</p>
        </div>

        <div v-else-if="allStores.length > 0" class="space-y-3">
          <!-- Filter Controls -->
          <div class="flex flex-col sm:flex-row gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
            <div class="flex-1">
              <div class="relative">
                <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
                <input
                  v-model="storeSearchQuery"
                  type="text"
                  placeholder="Pretraži prodavnice..."
                  class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
            </div>
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="showOnlyMyCity"
                  type="checkbox"
                  class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <span class="text-sm text-gray-700">Samo u mom gradu</span>
                <span v-if="user?.city" class="text-xs text-purple-600 font-medium">({{ user.city }})</span>
              </label>
            </div>
          </div>

          <p class="text-sm text-gray-500 mb-4">
            <template v-if="filteredStores.length !== allStores.length">
              Prikazano: {{ filteredStores.length }} od {{ allStores.length }} prodavnica
              <span v-if="selectedStoreIds.length > 0" class="ml-2">• Odabrano: {{ selectedStoreIds.length }}</span>
            </template>
            <template v-else>
              {{ selectedStoreIds.length === 0 ? 'Nijedna prodavnica nije odabrana - pretraga će uključiti sve prodavnice' : `Odabrano: ${selectedStoreIds.length} od ${allStores.length} prodavnica` }}
            </template>
          </p>

          <div v-if="filteredStores.length === 0" class="text-center py-8 text-gray-500">
            <svg class="w-12 h-12 mx-auto text-gray-300 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
            <p>Nema prodavnica koje odgovaraju filteru</p>
            <button @click="clearFilters" class="mt-2 text-sm text-purple-600 hover:text-purple-700 font-medium">
              Očisti filter
            </button>
          </div>

          <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div
              v-for="store in filteredStores"
              :key="store.id"
              class="border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              :class="{ 'border-purple-500 bg-purple-50': selectedStoreIds.includes(store.id) }"
            >
              <label class="flex items-center gap-3 p-3 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="selectedStoreIds.includes(store.id)"
                  @change="toggleStore(store.id)"
                  class="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <img
                  v-if="store.logo"
                  :src="store.logo"
                  :alt="store.name"
                  class="w-8 h-8 object-contain"
                  @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
                />
                <div v-else class="w-8 h-8 bg-gray-200 rounded flex items-center justify-center flex-shrink-0">
                  <svg class="w-5 h-5 text-gray-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <span class="font-medium text-gray-900 block truncate">{{ store.name }}</span>
                  <span v-if="store.city" class="text-xs text-gray-500">{{ store.city }}</span>
                </div>
              </label>
              <!-- Pogledaj lokaciju button -->
              <div class="px-3 pb-3 pt-0">
                <button
                  @click.prevent="openStoreMapModal(store)"
                  class="w-full text-xs text-purple-600 hover:text-purple-800 font-medium flex items-center justify-center gap-1 py-1.5 border border-purple-200 rounded hover:bg-purple-50 transition-colors"
                >
                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                  </svg>
                  Pogledaj lokaciju
                </button>
              </div>
            </div>
          </div>

          <div class="flex gap-3 mt-4 pt-4 border-t border-gray-200">
            <button
              @click="selectAllStores"
              class="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              Odaberi sve
            </button>
            <button
              @click="clearAllStores"
              class="text-sm text-gray-600 hover:text-gray-700 font-medium"
            >
              Poništi izbor
            </button>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
          Nema dostupnih prodavnica
        </div>

        <!-- Success/Error messages -->
        <div v-if="storesSaveSuccess" class="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p class="text-sm text-green-700">Postavke prodavnica su uspješno sačuvane!</p>
        </div>
        <div v-if="storesSaveError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p class="text-sm text-red-700">{{ storesSaveError }}</p>
        </div>
      </div>

      <!-- Recent Searches -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Nedavne pretrage</h2>
        <div v-if="recentSearches && recentSearches.length > 0" class="space-y-4">
          <div
            v-for="search in recentSearches"
            :key="search.id"
            class="border-b border-gray-200 pb-4"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <p class="text-gray-900 font-medium">{{ search.query }}</p>
                <p class="text-sm text-gray-500">{{ formatDate(search.created_at) }}</p>
              </div>
              <div v-if="search.result_count !== undefined" class="text-sm text-gray-600">
                {{ search.result_count }} rezultata
              </div>
            </div>
          </div>
        </div>
        <p v-else class="text-gray-500">Nemate još uvek pretaga</p>
      </div>

      <!-- Engagement History -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-gray-900">Istorija Aktivnosti</h2>
          <div class="text-sm text-gray-600">
            Ukupno kredita zaradeno: <span class="font-bold text-green-600">{{ totalCreditsEarned }}</span> 💰
          </div>
        </div>

        <div v-if="loadingEngagements" class="text-center py-8">
          <Icon name="mdi:loading" class="w-8 h-8 animate-spin text-purple-600 mx-auto" />
          <p class="text-gray-600 mt-2">Učitavanje...</p>
        </div>

        <div v-else-if="engagements && engagements.length > 0" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Datum
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Aktivnost
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Proizvod
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Krediti
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="engagement in engagements" :key="engagement.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {{ formatEngagementDate(engagement.date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getActivityBadgeClass(engagement.activity)">
                    {{ getActivityLabel(engagement.activity) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                  {{ engagement.product?.title || 'Nepoznat proizvod' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                  +{{ engagement.credits_earned }}
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div v-if="engagementsPagination" class="flex items-center justify-between mt-6">
            <div class="text-sm text-gray-600">
              Stranica {{ engagementsPagination.page }} od {{ engagementsPagination.pages }}
            </div>
            <div class="flex gap-2">
              <button
                @click="loadEngagements(engagementsPagination.page - 1)"
                :disabled="!engagementsPagination.has_prev"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Prethodna
              </button>
              <button
                @click="loadEngagements(engagementsPagination.page + 1)"
                :disabled="!engagementsPagination.has_next"
                class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Sljedeća
              </button>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-12">
          <Icon name="mdi:history" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p class="text-gray-500 mb-2">Još uvijek nemate aktivnosti</p>
          <p class="text-sm text-gray-400">Počnite glasati i komentarisati proizvode da zaradite kredite!</p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mt-8 flex space-x-4">
        <NuxtLink
          to="/"
          class="bg-indigo-600 text-white px-6 py-3 rounded-md font-medium hover:bg-indigo-700 transition duration-200"
        >
          Nazad na pretraživanje
        </NuxtLink>
        <button
          @click="handleLogout"
          class="bg-gray-300 text-gray-700 px-6 py-3 rounded-md font-medium hover:bg-gray-400 transition duration-200"
        >
          Odjava
        </button>
      </div>
    </div>

    <!-- Store Map Modal -->
    <Teleport to="body">
      <div
        v-if="showStoreMapModal"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
        @click.self="closeStoreMapModal"
      >
        <div class="bg-white rounded-xl shadow-2xl max-w-3xl w-full overflow-hidden">
          <!-- Header -->
          <div class="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 text-white flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="bg-white/20 rounded-full p-2">
                <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-bold">{{ selectedMapStore?.name }}</h2>
                <p class="text-sm text-purple-100">Lokacija u vašem gradu ({{ user?.city || 'Tuzla' }})</p>
              </div>
            </div>
            <button @click="closeStoreMapModal" class="text-white/80 hover:text-white p-1">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Map -->
          <div class="aspect-video bg-gray-100">
            <iframe
              v-if="storeMapEmbedUrl"
              :src="storeMapEmbedUrl"
              width="100%"
              height="100%"
              style="border:0;"
              allowfullscreen
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
            ></iframe>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <p class="text-sm text-gray-500">
              Prikazane su lokacije prodavnice "{{ selectedMapStore?.name }}" u gradu {{ user?.city || 'Tuzla' }}
            </p>
            <div class="flex gap-3">
              <button
                @click="openGoogleMapsLink"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7zm-2 16H5V5h7V3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7h-7z"/>
                </svg>
                Otvori u Google Maps
              </button>
              <button
                @click="closeStoreMapModal"
                class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium rounded-lg transition-colors"
              >
                Zatvori
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { user, logout } = useAuth()
const { get, post, put } = useApi()

const isEditMode = ref(false)
const isSubmitting = ref(false)
const showSuccess = ref(false)
const showError = ref(false)
const errorMessage = ref('')

const formData = ref({
  first_name: '',
  last_name: '',
  city: ''
})

const cities = ref<string[]>([])
const packageInfo = ref<any>(null)
const searchCounts = ref<any>(null)
const recentSearches = ref<any[]>([])

// Store preferences
const allStores = ref<any[]>([])
const selectedStoreIds = ref<number[]>([])
const originalSelectedStoreIds = ref<number[]>([])
const loadingStores = ref(false)
const isSavingStores = ref(false)
const storesSaveSuccess = ref(false)
const storesSaveError = ref('')

// Store filter
const storeSearchQuery = ref('')
const showOnlyMyCity = ref(false)

const filteredStores = computed(() => {
  let stores = allStores.value

  // Filter by search query
  if (storeSearchQuery.value.trim()) {
    const query = storeSearchQuery.value.toLowerCase().trim()
    stores = stores.filter(store =>
      store.name.toLowerCase().includes(query) ||
      (store.city && store.city.toLowerCase().includes(query))
    )
  }

  // Filter by user's city
  if (showOnlyMyCity.value && user.value?.city) {
    stores = stores.filter(store =>
      store.city && store.city.toLowerCase() === user.value!.city!.toLowerCase()
    )
  }

  return stores
})

function clearFilters() {
  storeSearchQuery.value = ''
  showOnlyMyCity.value = false
}

// Store map modal
const showStoreMapModal = ref(false)
const selectedMapStore = ref<any>(null)
const storeMapEmbedUrl = ref('')
const citiesWithCoords = ref<any[]>([])

const hasStoreChanges = computed(() => {
  if (selectedStoreIds.value.length !== originalSelectedStoreIds.value.length) return true
  const sorted1 = [...selectedStoreIds.value].sort()
  const sorted2 = [...originalSelectedStoreIds.value].sort()
  return sorted1.some((v, i) => v !== sorted2[i])
})

// Engagement history
const engagements = ref<any[]>([])

// Organization
const hasOrganization = ref(false)
const organizationName = ref('')
const engagementsPagination = ref<any>(null)
const loadingEngagements = ref(false)
const totalCreditsEarned = computed(() => {
  return engagements.value.reduce((sum, eng) => sum + eng.credits_earned, 0)
})

onMounted(async () => {
  await loadCities()
  await loadProfileData()
  await loadStorePreferences()
  await loadEngagements(1)
  await checkOrganizationMembership()
})

async function checkOrganizationMembership() {
  try {
    const data = await get('/api/my-organization')
    if (data.organization) {
      hasOrganization.value = true
      organizationName.value = data.organization.name
    }
  } catch (error: any) {
    // 404 means user is not a member of any organization - that's fine
    hasOrganization.value = false
  }
}

async function loadCities() {
  try {
    // Load simple city list for dropdown
    const data = await get('/auth/cities')
    cities.value = data.cities || []

    // Also load cities with coordinates for map functionality
    const coordsData = await get('/auth/cities?coords=true')
    citiesWithCoords.value = coordsData.cities || []
  } catch (error) {
    console.error('Error loading cities:', error)
  }
}

async function loadProfileData() {
  try {
    const data = await get('/auth/user/profile')
    packageInfo.value = data.package
    searchCounts.value = data.search_counts
    recentSearches.value = data.recent_searches || []

    // Set form data
    formData.value = {
      first_name: user.value?.first_name || '',
      last_name: user.value?.last_name || '',
      city: user.value?.city || ''
    }
  } catch (error) {
    console.error('Error loading profile data:', error)
  }
}

async function handleSubmit() {
  isSubmitting.value = true
  showError.value = false
  showSuccess.value = false

  try {
    const response = await put('/auth/user/profile', formData.value)

    if (response.success) {
      showSuccess.value = true
      isEditMode.value = false

      // Update user data
      if (user.value) {
        user.value.first_name = formData.value.first_name
        user.value.last_name = formData.value.last_name
        user.value.city = formData.value.city
      }

      // Scroll to top to show success message
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      errorMessage.value = response.error || 'Došlo je do greške prilikom ažuriranja profila'
      showError.value = true
    }
  } catch (error: any) {
    console.error('Error updating profile:', error)
    errorMessage.value = error.message || 'Došlo je do greške prilikom ažuriranja profila'
    showError.value = true
  } finally {
    isSubmitting.value = false
  }
}

function cancelEdit() {
  isEditMode.value = false
  showError.value = false

  // Reset form data
  formData.value = {
    first_name: user.value?.first_name || '',
    last_name: user.value?.last_name || '',
    city: user.value?.city || ''
  }
}

async function loadEngagements(page = 1) {
  loadingEngagements.value = true
  try {
    const response = await get(`/user/engagement-history?page=${page}&per_page=20`)
    if (response.success) {
      engagements.value = response.engagements
      engagementsPagination.value = response.pagination
    }
  } catch (error) {
    console.error('Error loading engagements:', error)
  } finally {
    loadingEngagements.value = false
  }
}

function getActivityLabel(activity: string): string {
  const labels: Record<string, string> = {
    'vote_up': '👍 Thumbs Up',
    'vote_down': '👎 Thumbs Down',
    'comment': '💬 Komentar'
  }
  return labels[activity] || activity
}

function getActivityBadgeClass(activity: string): string {
  const classes: Record<string, string> = {
    'vote_up': 'px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800',
    'vote_down': 'px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800',
    'comment': 'px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800'
  }
  return classes[activity] || 'px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800'
}

function formatEngagementDate(dateString: string): string {
  const date = new Date(dateString)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${day}. ${getMonthName(date.getMonth())} ${year}. ${hours}:${minutes}`
}

function getMonthName(month: number): string {
  const months = ['Januar', 'Februar', 'Mart', 'April', 'Maj', 'Juni', 'Juli', 'August', 'Septembar', 'Oktobar', 'Novembar', 'Decembar']
  return months[month]
}

async function handleLogout() {
  await logout()
  navigateTo('/')
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString('sr-RS', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Store preference functions
async function loadStorePreferences() {
  loadingStores.value = true
  try {
    // Load all stores
    const storesData = await get('/api/businesses?all=true')
    allStores.value = storesData.businesses || []

    // Load user's selected stores from preferences
    const prefsData = await get('/auth/user/store-preferences')
    if (prefsData.preferred_store_ids && prefsData.preferred_store_ids.length > 0) {
      selectedStoreIds.value = prefsData.preferred_store_ids
    } else {
      // Default: all stores selected
      selectedStoreIds.value = allStores.value.map((s: any) => s.id)
    }
    originalSelectedStoreIds.value = [...selectedStoreIds.value]
  } catch (error) {
    console.error('Error loading store preferences:', error)
  } finally {
    loadingStores.value = false
  }
}

async function saveStorePreferences() {
  isSavingStores.value = true
  storesSaveSuccess.value = false
  storesSaveError.value = ''

  try {
    await put('/auth/user/store-preferences', {
      preferred_store_ids: selectedStoreIds.value
    })
    originalSelectedStoreIds.value = [...selectedStoreIds.value]
    storesSaveSuccess.value = true

    // Hide success message after 3 seconds
    setTimeout(() => {
      storesSaveSuccess.value = false
    }, 3000)
  } catch (error: any) {
    console.error('Error saving store preferences:', error)
    storesSaveError.value = error.message || 'Greška prilikom čuvanja postavki'
  } finally {
    isSavingStores.value = false
  }
}

function toggleStore(storeId: number) {
  const index = selectedStoreIds.value.indexOf(storeId)
  if (index === -1) {
    selectedStoreIds.value.push(storeId)
  } else {
    selectedStoreIds.value.splice(index, 1)
  }
}

function selectAllStores() {
  selectedStoreIds.value = allStores.value.map((s: any) => s.id)
}

function clearAllStores() {
  selectedStoreIds.value = []
}

// Store map modal functions
function openStoreMapModal(store: any) {
  selectedMapStore.value = store

  // Get user's city coordinates
  const userCity = user.value?.city || 'Tuzla'
  const cityData = citiesWithCoords.value.find(c => c.name === userCity)

  if (cityData && cityData.latitude && cityData.longitude) {
    // Generate Google Maps embed URL with store name and user's city coordinates
    const searchQuery = encodeURIComponent(store.name)
    storeMapEmbedUrl.value = `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${searchQuery}&center=${cityData.latitude},${cityData.longitude}&zoom=12`
  } else {
    // Fallback to Tuzla coordinates
    const searchQuery = encodeURIComponent(store.name)
    storeMapEmbedUrl.value = `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${searchQuery}&center=44.5391,18.6752&zoom=12`
  }

  showStoreMapModal.value = true
}

function closeStoreMapModal() {
  showStoreMapModal.value = false
  selectedMapStore.value = null
  storeMapEmbedUrl.value = ''
}

function openGoogleMapsLink() {
  if (!selectedMapStore.value) return

  // Get user's city coordinates
  const userCity = user.value?.city || 'Tuzla'
  const cityData = citiesWithCoords.value.find(c => c.name === userCity)

  let lat = 44.5391
  let lng = 18.6752

  if (cityData && cityData.latitude && cityData.longitude) {
    lat = cityData.latitude
    lng = cityData.longitude
  }

  const searchQuery = encodeURIComponent(selectedMapStore.value.name)
  const googleMapsUrl = `https://www.google.com/maps/search/${searchQuery}/@${lat},${lng},12z`
  window.open(googleMapsUrl, '_blank')
}

useSeoMeta({
  title: 'Moj profil - Popust.ba',
  description: 'Upravljajte vašim nalogom i preferencijama na Popust.ba platformi',
})
</script>
