<template>
  <div class="bg-gray-50 min-h-screen py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Moj profil</h1>
        <p class="text-gray-600">Uredite svoje lične podatke</p>
      </div>

      <!-- Quick Navigation -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <NuxtLink
          to="/profil/liste"
          class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow flex items-center gap-4"
        >
          <div class="bg-purple-100 p-3 rounded-lg">
            <svg class="w-8 h-8 text-purple-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">Prethodne Liste</h3>
            <p class="text-sm text-gray-600">Pregled vaših prethodnih shopping lista</p>
          </div>
        </NuxtLink>

        <NuxtLink
          to="/moje-liste"
          class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow flex items-center gap-4"
        >
          <div class="bg-green-100 p-3 rounded-lg">
            <svg class="w-8 h-8 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">Aktivna Lista</h3>
            <p class="text-sm text-gray-600">Pogledajte trenutnu shopping listu</p>
          </div>
        </NuxtLink>

      </div>

      <!-- Install App Banner -->
      <div v-if="showInstallOption" class="bg-gradient-to-r from-violet-500 to-purple-600 rounded-lg shadow-md p-6 mb-8 text-white">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="bg-white/20 p-3 rounded-lg">
              <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold">Instalirajte Aplikaciju</h3>
              <p class="text-sm text-white/80">
                {{ pwa.state.isIOS ? 'Dodajte na pocetni ekran za brzi pristup' : 'Instalirajte aplikaciju za brzi pristup bez browsera' }}
              </p>
            </div>
          </div>
          <button
            @click="handleInstallClick"
            class="bg-white text-purple-600 px-5 py-2.5 rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Instaliraj
          </button>
        </div>
        <!-- iOS Instructions (shown when clicked on iOS) -->
        <div v-if="showIOSInstructions" class="mt-4 pt-4 border-t border-white/20">
          <p class="text-sm font-medium mb-2">Kako instalirati:</p>
          <ol class="text-sm text-white/80 space-y-1">
            <li>1. Dodirnite ikonu za dijeljenje na dnu ekrana</li>
            <li>2. Skrolajte dolje i dodirnite "Dodaj na pocetni ekran"</li>
            <li>3. Dodirnite "Dodaj" u gornjem desnom uglu</li>
          </ol>
        </div>
      </div>

      <!-- My Preferences Section (grocery interests) -->
      <UserPreferencesSection :key="preferencesKey" :allow-remove="true" @edit="showInterestPopup = true" />

      <!-- Interest/Preferences Popup -->
      <InterestPopup
        :show="showInterestPopup"
        @close="showInterestPopup = false"
        @skip="showInterestPopup = false"
        @complete="handleInterestComplete"
      />

      <!-- Store Preferences Section -->
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
          <p class="text-sm text-gray-500 mb-4">
            {{ selectedStoreIds.length === 0 ? 'Nijedna prodavnica nije odabrana - pretraga će uključiti sve prodavnice' : `Odabrano: ${selectedStoreIds.length} od ${allStores.length} prodavnica` }}
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <label
              v-for="store in allStores"
              :key="store.id"
              class="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              :class="{ 'border-purple-500 bg-purple-50': selectedStoreIds.includes(store.id) }"
            >
              <input
                type="checkbox"
                :checked="selectedStoreIds.includes(store.id)"
                @change="toggleStore(store.id)"
                class="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
              />
              <img
                v-if="store.logo_path"
                :src="store.logo_path"
                :alt="store.name"
                class="w-10 h-10 object-contain rounded"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="w-10 h-10 bg-gray-200 rounded flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-gray-400" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <span class="font-medium text-gray-900 block truncate">{{ store.name }}</span>
                <span v-if="store.city" class="text-xs text-gray-500">{{ store.city }}</span>
              </div>
            </label>
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

        <!-- Success/Error messages for stores -->
        <div v-if="storesSaveSuccess" class="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p class="text-sm text-green-700">Postavke prodavnica su uspješno sačuvane!</p>
        </div>
        <div v-if="storesSaveError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p class="text-sm text-red-700">{{ storesSaveError }}</p>
        </div>
      </div>

      <!-- Product Images Section -->
      <ProductImageUpload class="mb-8" />

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-purple-600">
          <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Profile Form -->
      <div v-else class="bg-white rounded-lg shadow-md p-6">
        <!-- Error Message -->
        <div v-if="errorMessage" class="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{{ errorMessage }}</p>
        </div>

        <form @submit.prevent="saveProfile" class="space-y-6">
          <!-- Email (read-only) -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
              Email adresa
            </label>
            <input
              id="email"
              v-model="profile.email"
              type="email"
              disabled
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
            />
            <p class="mt-1 text-xs text-gray-500">Email adresa se ne može mijenjati</p>
          </div>

          <!-- First Name -->
          <div>
            <label for="first_name" class="block text-sm font-medium text-gray-700 mb-1">
              Ime
            </label>
            <input
              id="first_name"
              v-model="profile.first_name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="Unesite vaše ime"
            />
          </div>

          <!-- Last Name -->
          <div>
            <label for="last_name" class="block text-sm font-medium text-gray-700 mb-1">
              Prezime
            </label>
            <input
              id="last_name"
              v-model="profile.last_name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              placeholder="Unesite vaše prezime"
            />
          </div>

          <!-- Phone -->
          <div>
            <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">
              Broj telefona
            </label>
            <div class="relative">
              <input
                id="phone"
                v-model="profile.phone"
                type="tel"
                :class="[
                  'w-full px-3 py-2 border-2 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none',
                  profile.phone && !isPhoneValid ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-purple-500 focus:border-purple-500'
                ]"
                placeholder="+387 XX XXX XXX"
                @input="formatPhoneNumber"
                @blur="validatePhone"
                maxlength="20"
              />
              <div v-if="profile.phone && isPhoneValid" class="absolute right-3 top-1/2 -translate-y-1/2">
                <svg class="w-5 h-5 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <div v-if="profile.phone && !isPhoneValid" class="absolute right-3 top-1/2 -translate-y-1/2">
                <svg class="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
              </div>
            </div>
            <p v-if="profile.phone && !isPhoneValid" class="mt-1 text-xs text-red-600 flex items-center gap-1">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
              </svg>
              Broj telefona nije ispravan. Format: +387XXXXXXXXX
            </p>
            <p v-else class="mt-1 text-xs text-gray-500">Format: +387XXXXXXXXX (sa pozivnim brojem)</p>
          </div>

          <!-- City -->
          <div>
            <label for="city" class="block text-sm font-medium text-gray-700 mb-1">
              Grad
            </label>
            <select
              id="city"
              v-model="profile.city"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            >
              <option value="">Odaberite grad</option>
              <option v-for="city in cities" :key="city.id" :value="city.name">{{ city.name }}</option>
            </select>
          </div>

          <!-- SMS/Viber Notification Preferences -->
          <div class="border border-gray-200 rounded-md p-4 bg-gray-50">
            <label class="flex items-start cursor-pointer">
              <input
                type="checkbox"
                :checked="profile.notification_preferences === 'favorites' || profile.notification_preferences === 'all'"
                @change="toggleNotifications"
                class="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">
                  Želim primati notifikacije o proizvodima koje pratim
                </p>
                <p class="text-xs text-gray-600 mt-1">
                  Primiću SMS/Viber notifikacije kada proizvodi koje sam dodao u favorite dobiju popust ili promijene cijenu
                </p>
              </div>
            </label>
          </div>

          <!-- Email Notification Preferences -->
          <div class="border border-gray-200 rounded-md p-4 bg-gray-50">
            <div class="mb-4">
              <h3 class="text-sm font-medium text-gray-900">Email obavijesti</h3>
              <p class="text-xs text-gray-600 mt-1">Odaberite koje email obavijesti želite primati</p>
            </div>

            <div class="space-y-3">
              <!-- Daily emails -->
              <label class="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  v-model="emailPreferences.daily_emails"
                  class="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <div class="ml-3">
                  <p class="text-sm font-medium text-gray-900">Dnevne obavijesti</p>
                  <p class="text-xs text-gray-600 mt-0.5">
                    Primajte email kada se pojave novi proizvodi ili nove akcije za artikle koje pratite
                  </p>
                </div>
              </label>

              <!-- Weekly summary -->
              <label class="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  v-model="emailPreferences.weekly_summary"
                  class="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <div class="ml-3">
                  <p class="text-sm font-medium text-gray-900">Sedmični pregled</p>
                  <p class="text-xs text-gray-600 mt-0.5">
                    Primajte sedmični pregled najboljih ponuda i promjena cijena vaših praćenih proizvoda
                  </p>
                </div>
              </label>

              <!-- Monthly summary -->
              <label class="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  v-model="emailPreferences.monthly_summary"
                  class="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <div class="ml-3">
                  <p class="text-sm font-medium text-gray-900">Mjesečni pregled</p>
                  <p class="text-xs text-gray-600 mt-0.5">
                    Primajte mjesečni pregled popularnih proizvoda i najboljih ponuda
                  </p>
                </div>
              </label>
            </div>
          </div>

          <!-- Account Deactivation Section -->
          <div class="border border-gray-200 rounded-md p-4 bg-gray-50">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900">Deaktivacija računa</h3>
                <p class="text-xs text-gray-600 mt-1">
                  Deaktivirajte svoj račun. Nećete više primati obavještenja i nećete se moći prijaviti.
                </p>
              </div>
              <button
                type="button"
                @click="showDeactivateModal = true"
                class="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 transition-colors"
              >
                Deaktiviraj račun
              </button>
            </div>
          </div>

          <!-- Admin Badge (if admin) -->
          <div v-if="profile.is_admin" class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex items-center">
              <svg class="w-6 h-6 text-red-600 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
              </svg>
              <div>
                <p class="text-sm font-semibold text-red-900">Administrator</p>
                <p class="text-xs text-red-700">Imate administratorski pristup platformi</p>
              </div>
            </div>
          </div>

          <!-- Save Button -->
          <div class="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              @click="loadProfile"
              :disabled="isSaving"
              class="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Odustani
            </button>
            <button
              type="submit"
              :disabled="isSaving || !hasProfileChanges"
              class="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isSaving ? 'Čuvanje...' : 'Sačuvaj promjene' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Success Toast Notification -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-300"
        enter-from-class="opacity-0 -translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-4"
      >
        <div
          v-if="successMessage"
          class="fixed top-4 left-1/2 -translate-x-1/2 z-[200] bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 max-w-md"
        >
          <div class="bg-white/20 rounded-full p-1">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <span class="font-medium">{{ successMessage }}</span>
          <button
            @click="successMessage = ''"
            class="ml-2 hover:bg-white/20 rounded p-1 transition-colors"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </Transition>
    </Teleport>

    <!-- Deactivate Account Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeactivateModal"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
        @click.self="showDeactivateModal = false"
      >
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
          <!-- Header -->
          <div class="bg-red-50 px-6 py-4 border-b border-red-100">
            <div class="flex items-center gap-3">
              <div class="bg-red-100 rounded-full p-2">
                <svg class="w-6 h-6 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-bold text-red-800">Deaktivacija računa</h2>
                <p class="text-sm text-red-600">Ova akcija se ne može poništiti</p>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="px-6 py-4">
            <p class="text-gray-700 mb-4">
              Jeste li sigurni da želite deaktivirati svoj račun?
            </p>
            <div class="bg-gray-50 rounded-lg p-4 space-y-2 text-sm text-gray-600">
              <div class="flex items-start gap-2">
                <svg class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span>Nećete više primati dnevne, sedmične ili mjesečne email izvještaje</span>
              </div>
              <div class="flex items-start gap-2">
                <svg class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span>Nakon isteka sesije, nećete se moći ponovo prijaviti</span>
              </div>
              <div class="flex items-start gap-2">
                <svg class="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                </svg>
                <span>Za reaktivaciju računa kontaktirajte podršku</span>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end gap-3">
            <button
              @click="showDeactivateModal = false"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Odustani
            </button>
            <button
              @click="deactivateAccount"
              :disabled="isDeactivating"
              class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <svg v-if="isDeactivating" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              {{ isDeactivating ? 'Deaktiviranje...' : 'Potvrdi deaktivaciju' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ['auth']
})

const { get, put, post } = useApi()
const { refreshUser, logout } = useAuth()
const pwa = usePwaInstall()

// PWA install state
const showIOSInstructions = ref(false)
const showInstallOption = computed(() => {
  // Show if not installed and (iOS or can install on Android/Desktop)
  return !pwa.state.isInstalled && !pwa.state.isStandalone && (pwa.state.isIOS || pwa.state.canInstall)
})

async function handleInstallClick() {
  if (pwa.state.isIOS) {
    showIOSInstructions.value = !showIOSInstructions.value
  } else {
    await pwa.promptInstall()
  }
}

const isLoading = ref(true)
const isSaving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const isPhoneValid = ref(true)

// Account deactivation state
const showDeactivateModal = ref(false)
const isDeactivating = ref(false)

// Interest popup state
const showInterestPopup = ref(false)
const preferencesKey = ref(0)

function handleInterestComplete() {
  showInterestPopup.value = false
  preferencesKey.value++ // Force re-render of preferences section
}

// Store preferences state
const allStores = ref<any[]>([])
const selectedStoreIds = ref<number[]>([])
const originalSelectedStoreIds = ref<number[]>([])
const loadingStores = ref(false)
const isSavingStores = ref(false)
const storesSaveSuccess = ref(false)
const storesSaveError = ref('')

const hasStoreChanges = computed(() => {
  if (selectedStoreIds.value.length !== originalSelectedStoreIds.value.length) return true
  const sorted1 = [...selectedStoreIds.value].sort()
  const sorted2 = [...originalSelectedStoreIds.value].sort()
  return sorted1.some((v, i) => v !== sorted2[i])
})

const profile = ref({
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  city: '',
  notification_preferences: 'none',
  is_admin: false
})

const originalProfile = ref({
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  city: '',
  notification_preferences: 'none',
  is_admin: false
})

// Email notification preferences (all enabled by default)
const emailPreferences = ref({
  daily_emails: true,
  weekly_summary: true,
  monthly_summary: true
})

const originalEmailPreferences = ref({
  daily_emails: true,
  weekly_summary: true,
  monthly_summary: true
})

const cities = ref<string[]>([])

// Check if profile has any changes
const hasProfileChanges = computed(() => {
  return (
    profile.value.first_name !== originalProfile.value.first_name ||
    profile.value.last_name !== originalProfile.value.last_name ||
    profile.value.phone !== originalProfile.value.phone ||
    profile.value.city !== originalProfile.value.city ||
    profile.value.notification_preferences !== originalProfile.value.notification_preferences ||
    emailPreferences.value.daily_emails !== originalEmailPreferences.value.daily_emails ||
    emailPreferences.value.weekly_summary !== originalEmailPreferences.value.weekly_summary ||
    emailPreferences.value.monthly_summary !== originalEmailPreferences.value.monthly_summary
  )
})

async function loadProfile() {
  isLoading.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const data = await get('/auth/user/profile')
    const profileData = {
      email: data.email || '',
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      phone: data.phone || '',
      city: data.city || '',
      notification_preferences: data.notification_preferences || 'none',
      is_admin: data.is_admin || false
    }
    profile.value = { ...profileData }
    originalProfile.value = { ...profileData }

    // Load email preferences from user preferences (default all enabled)
    const emailPrefs = data.preferences?.email_preferences || {}
    const emailPrefsData = {
      daily_emails: emailPrefs.daily_emails !== false, // default true
      weekly_summary: emailPrefs.weekly_summary !== false, // default true
      monthly_summary: emailPrefs.monthly_summary !== false // default true
    }
    emailPreferences.value = { ...emailPrefsData }
    originalEmailPreferences.value = { ...emailPrefsData }

    // Validate phone if it exists
    if (profile.value.phone) {
      validatePhone()
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Greška pri učitavanju profila'
  } finally {
    isLoading.value = false
  }
}

async function loadCities() {
  try {
    const data = await get('/auth/cities')
    cities.value = data.cities || []
  } catch (error) {
    console.error('Error loading cities:', error)
  }
}

function formatPhoneNumber(event: any) {
  let value = event.target.value

  // Remove all non-digit characters except +
  value = value.replace(/[^\d+]/g, '')

  // Ensure it starts with +
  if (value && !value.startsWith('+')) {
    value = '+' + value
  }

  // Limit to reasonable phone number length
  if (value.length > 20) {
    value = value.substring(0, 20)
  }

  profile.value.phone = value
  validatePhone()
}

function validatePhone() {
  const value = profile.value.phone?.trim()

  if (!value) {
    isPhoneValid.value = true // Empty is valid
    return
  }

  // Basic international phone number validation
  const phoneRegex = /^\+\d{8,19}$/
  isPhoneValid.value = phoneRegex.test(value)
}

function toggleNotifications(event: any) {
  // Toggle between 'favorites' and 'none'
  profile.value.notification_preferences = event.target.checked ? 'favorites' : 'none'
}

async function saveProfile() {
  successMessage.value = ''
  errorMessage.value = ''

  isSaving.value = true

  try {
    const response = await put('/auth/user/profile', {
      first_name: profile.value.first_name,
      last_name: profile.value.last_name,
      phone: profile.value.phone,
      city: profile.value.city,
      notification_preferences: profile.value.notification_preferences,
      email_preferences: {
        daily_emails: emailPreferences.value.daily_emails,
        weekly_summary: emailPreferences.value.weekly_summary,
        monthly_summary: emailPreferences.value.monthly_summary
      }
    })

    if (response.success) {
      successMessage.value = response.message || 'Profil uspješno ažuriran!'

      // Update original profile to match current (so hasProfileChanges becomes false)
      originalProfile.value = { ...profile.value }
      originalEmailPreferences.value = { ...emailPreferences.value }

      // Refresh user data in auth store
      await refreshUser()

      // Clear success message after 5 seconds
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    } else {
      errorMessage.value = response.error || 'Greška pri čuvanju profila'
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Greška pri čuvanju profila'
  } finally {
    isSaving.value = false
  }
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

// Account deactivation function
async function deactivateAccount() {
  isDeactivating.value = true
  try {
    const response = await post('/auth/deactivate', {})
    if (response.success) {
      // Close modal
      showDeactivateModal.value = false
      // Show success message briefly then logout
      successMessage.value = response.message || 'Račun je uspješno deaktiviran.'
      // Wait a moment then logout
      setTimeout(async () => {
        await logout()
        navigateTo('/')
      }, 2000)
    } else {
      errorMessage.value = response.error || 'Greška pri deaktivaciji računa'
      showDeactivateModal.value = false
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Greška pri deaktivaciji računa'
    showDeactivateModal.value = false
  } finally {
    isDeactivating.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadCities()
  loadStorePreferences()
})

useSeoMeta({
  title: 'Moj profil - Popust.ba',
  description: 'Uredite svoje lične podatke',
})
</script>
