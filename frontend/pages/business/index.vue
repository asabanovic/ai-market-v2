<template>
  <div class="bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-4">Upravljanje biznisom</h1>
        <p class="text-gray-600">Dodajte i upravljajte vašim radnjama i proizvodima</p>
      </div>

      <!-- Add Business Button -->
      <div class="mb-8">
        <NuxtLink
          to="/business/add"
          class="bg-indigo-600 text-white px-6 py-3 rounded-md font-medium hover:bg-indigo-700 transition duration-200 inline-block"
        >
          + Dodaj novu radnju
        </NuxtLink>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Učitavanje...</span>
        </div>
      </div>

      <!-- Businesses List -->
      <div v-else-if="businesses && businesses.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div
          v-for="business in businesses"
          :key="business.id"
          :class="[
            'rounded-lg shadow-md p-6',
            business.expiry_dates?.length ? 'bg-white' : 'bg-red-50 border-2 border-red-200'
          ]"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-start space-x-4 flex-1">
              <!-- Business Logo -->
              <div class="flex-shrink-0">
                <img
                  v-if="business.logo_path"
                  :src="business.logo_path"
                  :alt="`${business.name} logo`"
                  class="w-16 h-16 object-cover rounded-lg border border-gray-200"
                />
                <div v-else class="w-16 h-16 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
                  <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                  </svg>
                </div>
              </div>
              <div class="flex-1">
                <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ business.name }}</h3>
                <div class="text-sm text-gray-600 space-y-1">
                  <p><strong>Grad:</strong> {{ business.city }}</p>
                  <p v-if="business.contact_phone"><strong>Telefon:</strong> {{ business.contact_phone }}</p>
                  <p v-if="business.google_link">
                    <strong>Google Maps:</strong>
                    <a :href="business.google_link" target="_blank" class="text-indigo-600 hover:text-indigo-800">
                      Otvori u Google Maps →
                    </a>
                  </p>
                </div>
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-500 space-y-1">
                <p>{{ business.product_count || 0 }} proizvoda</p>
                <p class="flex items-center justify-end gap-1">
                  <span :class="business.categorized_count === business.product_count ? 'text-green-600' : 'text-amber-600'">
                    {{ business.categorized_count || 0 }}/{{ business.product_count || 0 }}
                  </span>
                  <span>kategoriz.</span>
                </p>
                <p>{{ business.views || 0 }} pregleda</p>
                <!-- Follower count -->
                <p class="text-indigo-600 font-medium">
                  {{ business.follower_count || 0 }} {{ business.follower_count === 1 ? 'pratilac' : 'pratilaca' }}
                </p>
                <!-- Expiry dates -->
                <div v-if="business.expiry_dates?.length" class="mt-2 pt-2 border-t border-gray-100">
                  <p class="text-xs font-medium text-gray-600 mb-1">Istječe:</p>
                  <div class="flex flex-wrap gap-1 justify-end">
                    <span
                      v-for="expiry in business.expiry_dates.slice(0, 5)"
                      :key="expiry"
                      :class="[
                        'text-xs px-1.5 py-0.5 rounded',
                        isExpiringSoon(expiry) ? 'bg-red-100 text-red-700 font-medium' : 'bg-gray-100 text-gray-600'
                      ]"
                    >
                      {{ formatExpiryDate(expiry) }}
                    </span>
                    <span v-if="business.expiry_dates.length > 5" class="text-xs text-gray-400">
                      +{{ business.expiry_dates.length - 5 }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="border-t pt-4">
            <div class="flex flex-wrap gap-3">
              <NuxtLink
                :to="`/business/${business.id}/products`"
                class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition duration-200"
              >
                Upravljaj proizvodima
              </NuxtLink>
              <button
                @click="openEditModal(business)"
                class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400 transition duration-200"
              >
                Uredi
              </button>
              <button
                @click="openLogoUploadModal(business.id)"
                class="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 transition duration-200"
              >
                {{ business.logo_path ? 'Promijeni logo' : 'Dodaj logo' }}
              </button>
              <button
                v-if="business.google_link"
                @click="openMapModal(business)"
                class="bg-teal-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-teal-700 transition duration-200"
              >
                Prikaži mapu
              </button>
              <button
                v-if="user?.is_admin || business.user_role === 'owner'"
                @click="openInviteModal(business.id)"
                class="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 transition duration-200"
              >
                Pozovi korisnika
              </button>
              <button
                v-if="user?.is_admin || business.user_role === 'manager' || business.user_role === 'owner'"
                @click="openPdfModal(business)"
                class="bg-orange-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-orange-700 transition duration-200"
              >
                Upravljaj PDF-ima
              </button>
              <button
                v-if="user?.is_admin"
                @click="openLocationsModal(business)"
                class="bg-cyan-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-cyan-700 transition duration-200"
              >
                Lokacije
              </button>
              <button
                v-if="user?.is_admin"
                @click="categorizeBusinessProducts(business.id)"
                :disabled="isCategorizingBusiness.has(business.id)"
                class="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition duration-200 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {{ isCategorizingBusiness.has(business.id) ? 'Kategoriziram...' : 'AI Kategoriziraj' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <div class="bg-gray-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Nema radnji</h3>
        <p class="text-gray-600 mb-6">Počnite dodavanjem vaše prve radnje</p>
        <NuxtLink
          to="/business/add"
          class="bg-indigo-600 text-white px-6 py-3 rounded-md font-medium hover:bg-indigo-700 transition duration-200 inline-block"
        >
          Dodaj radnju
        </NuxtLink>
      </div>
    </div>

    <!-- Logo Upload Modal -->
    <div v-if="showLogoModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeLogoModal">
      <div class="relative top-20 mx-auto p-6 border w-96 shadow-lg rounded-lg bg-white">
        <div class="mt-3">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Postavite logo</h3>
          <form @submit.prevent="handleLogoUpload">
            <div class="mb-6 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <div v-if="!logoPreview">
                <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div>
                  <p class="text-sm text-gray-600 mb-2">Povucite i otpustite ili</p>
                  <label for="logo-file" class="cursor-pointer text-blue-500 hover:text-blue-600 font-medium">
                    kliknite da odaberete
                  </label>
                </div>
                <p class="text-xs text-gray-500 mt-2">PNG, JPG, GIF do 5MB</p>
              </div>
              <div v-else class="relative">
                <img :src="logoPreview" class="max-w-full max-h-48 mx-auto rounded-lg shadow-md" alt="Preview">
                <button type="button" @click="removeLogoPreview" class="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600">
                  ✕
                </button>
              </div>
              <input type="file" id="logo-file" @change="handleLogoFileChange" accept="image/*" class="hidden">
            </div>

            <div class="flex space-x-3">
              <button type="submit" :disabled="!logoFile || isUploadingLogo" class="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed">
                {{ isUploadingLogo ? 'Postavlja se...' : 'Postavite' }}
              </button>
              <button type="button" @click="closeLogoModal" class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400">
                Otkaži
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Edit Business Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeEditModal">
      <div class="relative top-10 mx-auto p-6 border max-w-2xl shadow-lg rounded-lg bg-white">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">Uredi radnju</h3>
          <button @click="closeEditModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleEditBusiness" class="space-y-6">
          <!-- Business Name -->
          <div>
            <label for="edit-business-name" class="block text-sm font-medium text-gray-700 mb-1">
              Naziv radnje *
            </label>
            <input
              type="text"
              id="edit-business-name"
              v-model="editForm.name"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Npr. Moja Radnja"
            />
          </div>

          <!-- City -->
          <div>
            <label for="edit-business-city" class="block text-sm font-medium text-gray-700 mb-1">
              Grad *
            </label>
            <select
              id="edit-business-city"
              v-model="editForm.city"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Odaberite grad</option>
              <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
            </select>
          </div>

          <!-- Contact Phone -->
          <div>
            <label for="edit-business-phone" class="block text-sm font-medium text-gray-700 mb-1">
              Kontakt telefon
            </label>
            <input
              type="tel"
              id="edit-business-phone"
              v-model="editForm.phone"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="+387 XX XXX XXX"
            />
          </div>

          <!-- Google Maps Link -->
          <div>
            <label for="edit-business-google-link" class="block text-sm font-medium text-gray-700 mb-1">
              Google Maps link
            </label>
            <input
              type="url"
              id="edit-business-google-link"
              v-model="editForm.google_link"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="https://www.google.com/maps/search/..."
            />
            <p class="mt-1 text-xs text-gray-500">
              Link na Google Maps sa svim lokacijama radnje (opcionalno)
            </p>

            <!-- Map Preview -->
            <div v-if="editMapEmbedUrl" class="mt-3">
              <p class="text-xs text-gray-500 mb-2">Pregled mape:</p>
              <div class="relative w-full h-48 rounded-lg overflow-hidden border border-gray-200">
                <iframe
                  :src="editMapEmbedUrl"
                  width="100%"
                  height="100%"
                  style="border:0;"
                  allowfullscreen=""
                  loading="lazy"
                  referrerpolicy="no-referrer-when-downgrade"
                ></iframe>
              </div>
            </div>
          </div>

          <!-- Buttons -->
          <div class="flex items-center justify-between pt-4 border-t border-gray-200">
            <!-- Delete Button -->
            <button
              type="button"
              @click="confirmDeleteBusiness"
              class="px-4 py-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors text-sm font-medium"
            >
              Obriši radnju
            </button>

            <div class="flex items-center space-x-3">
              <button
                type="button"
                @click="closeEditModal"
                class="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Odustani
              </button>
              <button
                type="submit"
                :disabled="isSubmittingEdit"
                class="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ isSubmittingEdit ? 'Čuva se...' : 'Sačuvaj izmjene' }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[60]" @click.self="showDeleteConfirm = false">
      <div class="relative top-20 mx-auto p-6 border max-w-md shadow-lg rounded-lg bg-white">
        <div class="text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Obriši radnju?</h3>
          <p class="text-sm text-gray-500 mb-6">
            Jeste li sigurni da želite obrisati radnju "{{ editForm.name }}"? Ova akcija će obrisati i sve proizvode povezane s ovom radnjom i ne može se poništiti.
          </p>
          <div class="flex space-x-3">
            <button
              @click="showDeleteConfirm = false"
              class="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Odustani
            </button>
            <button
              @click="handleDeleteBusiness"
              :disabled="isDeletingBusiness"
              class="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
            >
              {{ isDeletingBusiness ? 'Briše se...' : 'Obriši' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Invite Modal -->
    <div v-if="showInviteModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeInviteModal">
      <div class="relative top-20 mx-auto p-6 border w-96 shadow-lg rounded-lg bg-white">
        <div class="mt-3">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Pozovi korisnika</h3>
          <form @submit.prevent="handleInviteUser">
            <div class="mb-4">
              <label for="invitation-email" class="block text-sm font-medium text-gray-700 mb-2">Email adresa</label>
              <input type="email" id="invitation-email" v-model="inviteForm.email" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm text-gray-900">
            </div>

            <div class="mb-4">
              <label for="invitation-role" class="block text-sm font-medium text-gray-700 mb-2">Uloga</label>
              <select id="invitation-role" v-model="inviteForm.role" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm text-gray-900 bg-white">
                <option value="staff">Zaposleni - Može dodavati proizvode</option>
                <option value="manager">Menadžer - Može upravljati proizvodima i biznisом</option>
                <option value="owner">Vlasnik - Puna kontrola uključujući pozive</option>
              </select>
            </div>

            <div class="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
              <div class="flex">
                <svg class="w-5 h-5 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div class="text-sm text-blue-700">
                  <p class="font-medium">Poziv će biti poslan na email adresu</p>
                  <p>Korisnik će moći pristupiti biznisu nakon klika na link u email-u.</p>
                </div>
              </div>
            </div>

            <div class="flex space-x-3">
              <button type="submit" :disabled="isSubmittingInvite" class="flex-1 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50">
                {{ isSubmittingInvite ? 'Šalje se...' : 'Pošalji poziv' }}
              </button>
              <button type="button" @click="closeInviteModal" class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400">
                Otkaži
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- PDF Management Modal -->
    <div v-if="showPdfModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closePdfModal">
      <div class="relative top-20 mx-auto p-6 border w-[32rem] shadow-lg rounded-lg bg-white">
        <div class="mt-3">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Upravljanje PDF-ima</h3>

          <!-- PDF URL Section -->
          <div class="mb-6">
            <h4 class="text-md font-medium text-gray-800 mb-3">Automatska sinhronizacija</h4>
            <div class="bg-blue-50 border border-blue-200 rounded-md p-3 mb-3">
              <div class="flex">
                <svg class="w-5 h-5 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div class="text-sm text-blue-700">
                  <p>Postavite URL ka PDF-u sa katalogom. Sistem će automatski preuzimati proizvode.</p>
                </div>
              </div>
            </div>

            <div class="flex space-x-2 mb-3">
              <input
                type="url"
                v-model="pdfForm.pdf_url"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
                placeholder="https://example.com/katalog.pdf"
              >
              <button
                @click="savePdfUrl"
                :disabled="isSavingPdfUrl"
                class="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm font-medium disabled:opacity-50"
              >
                {{ isSavingPdfUrl ? 'Čuva se...' : 'Sačuvaj' }}
              </button>
            </div>

            <div v-if="pdfForm.last_sync" class="text-xs text-gray-600 mb-2">
              Posljednja sinhronizacija: {{ formatDateTime(pdfForm.last_sync) }}
            </div>

            <button
              @click="syncFromPdfUrl"
              :disabled="!pdfForm.pdf_url || isSyncingPdf"
              class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm font-medium disabled:opacity-50 w-full"
            >
              {{ isSyncingPdf ? 'Sinhronizuje se...' : 'Sinhronizuj sada' }}
            </button>
          </div>

          <hr class="my-4">

          <!-- PDF Upload Section -->
          <div class="mb-6">
            <h4 class="text-md font-medium text-gray-800 mb-3">Učitaj PDF na zahtjev</h4>
            <div class="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-3">
              <div class="flex">
                <svg class="w-5 h-5 text-yellow-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                <div class="text-sm text-yellow-700">
                  <p>Učitajte PDF sa katalogom proizvoda za jednokratnu obradu.</p>
                </div>
              </div>
            </div>

            <form @submit.prevent="uploadPdf">
              <div class="flex items-center space-x-2">
                <input
                  type="file"
                  @change="handlePdfFileChange"
                  accept=".pdf"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
                >
                <button
                  type="submit"
                  :disabled="!pdfFile || isUploadingPdf"
                  class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 text-sm font-medium disabled:opacity-50"
                >
                  {{ isUploadingPdf ? 'Obrađuje...' : 'Učitaj i obradi' }}
                </button>
              </div>
            </form>

            <div class="text-xs text-gray-500 mt-1">
              Podržani formati: PDF • Maksimalna veličina: 20MB
            </div>
          </div>

          <!-- Processing Results -->
          <div v-if="pdfResults" class="mb-4">
            <div :class="['border rounded-md p-3', pdfResults.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200']">
              <h5 class="text-sm font-medium mb-2" :class="pdfResults.type === 'success' ? 'text-green-800' : 'text-red-800'">
                Rezultati obrade:
              </h5>
              <div class="text-sm" :class="pdfResults.type === 'success' ? 'text-green-600' : 'text-red-600'">
                {{ pdfResults.message }}
              </div>
            </div>
          </div>

          <div class="flex space-x-3">
            <button
              type="button"
              @click="closePdfModal"
              class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400"
            >
              Zatvori
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Map Modal -->
    <div v-if="showMapModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeMapModal">
      <div class="relative top-10 mx-auto p-6 border max-w-4xl shadow-lg rounded-lg bg-white">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-medium text-gray-900">
            Lokacije: {{ mapBusiness?.name }}
          </h3>
          <button @click="closeMapModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Embedded Map -->
        <div v-if="currentMapEmbedUrl" class="w-full h-96 rounded-lg overflow-hidden border border-gray-200">
          <iframe
            :src="currentMapEmbedUrl"
            width="100%"
            height="100%"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>
        </div>
        <div v-else class="w-full h-96 rounded-lg border border-gray-200 flex items-center justify-center bg-gray-50">
          <div class="text-center text-gray-500">
            <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            <p>Mapa se ne može prikazati za ovaj link</p>
          </div>
        </div>

        <!-- Link to Google Maps -->
        <div class="mt-4 flex justify-between items-center">
          <a
            :href="mapBusiness?.google_link"
            target="_blank"
            class="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
          >
            Otvori u Google Maps →
          </a>
          <button
            @click="closeMapModal"
            class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 text-sm"
          >
            Zatvori
          </button>
        </div>
      </div>
    </div>

    <!-- Locations Modal -->
    <div v-if="showLocationsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click.self="closeLocationsModal">
      <div class="relative top-10 mx-auto p-6 border max-w-3xl shadow-lg rounded-lg bg-white max-h-[85vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">
            Lokacije: {{ locationsBusiness?.name }}
          </h3>
          <button @click="closeLocationsModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Add Location Button -->
        <div class="mb-4">
          <button
            @click="showAddLocationForm = true"
            v-if="!showAddLocationForm"
            class="flex items-center gap-2 bg-cyan-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-cyan-700 transition duration-200"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Dodaj lokaciju
          </button>
        </div>

        <!-- Add Location Form -->
        <div v-if="showAddLocationForm" class="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
          <h4 class="text-md font-semibold text-gray-800 mb-4">Nova lokacija</h4>
          <form @submit.prevent="handleAddLocation" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Naziv lokacije *</label>
                <input
                  type="text"
                  v-model="newLocation.name"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  placeholder="Npr. Bingo Centar Tuzla"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Grad</label>
                <input
                  type="text"
                  v-model="newLocation.city"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  placeholder="Npr. Tuzla"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Adresa</label>
              <input
                type="text"
                v-model="newLocation.address"
                class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                placeholder="Npr. Ulica 123, Tuzla"
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
                <input
                  type="tel"
                  v-model="newLocation.phone"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                  placeholder="+387 XX XXX XXX"
                />
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Latitude</label>
                  <input
                    type="number"
                    step="any"
                    v-model.number="newLocation.latitude"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="44.5380"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Longitude</label>
                  <input
                    type="number"
                    step="any"
                    v-model.number="newLocation.longitude"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                    placeholder="18.6669"
                  />
                </div>
              </div>
            </div>
            <div class="flex items-center gap-3 pt-2">
              <button
                type="button"
                @click="geocodeNewLocation"
                :disabled="isGeocodingNew || (!newLocation.address && !newLocation.city)"
                class="bg-blue-500 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition duration-200 flex items-center gap-2"
              >
                <svg v-if="isGeocodingNew" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {{ isGeocodingNew ? 'Traži...' : 'Dohvati GPS' }}
              </button>
              <button
                type="submit"
                :disabled="isAddingLocation || !newLocation.name"
                class="bg-cyan-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-cyan-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition duration-200"
              >
                {{ isAddingLocation ? 'Dodaje se...' : 'Dodaj lokaciju' }}
              </button>
              <button
                type="button"
                @click="cancelAddLocation"
                class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400 transition duration-200"
              >
                Otkaži
              </button>
            </div>
          </form>
        </div>

        <!-- Loading State -->
        <div v-if="isLoadingLocations" class="text-center py-8">
          <div class="inline-flex items-center text-cyan-600">
            <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span class="ml-2">Učitavanje lokacija...</span>
          </div>
        </div>

        <!-- Locations List -->
        <div v-else-if="businessLocations.length > 0" class="space-y-3">
          <div
            v-for="location in businessLocations"
            :key="location.id"
            class="bg-white border border-gray-200 rounded-lg p-4 hover:border-cyan-300 transition-colors"
          >
            <!-- View Mode -->
            <div v-if="editingLocationId !== location.id">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="text-md font-semibold text-gray-900">{{ location.name }}</h4>
                  <div class="text-sm text-gray-600 mt-1 space-y-1">
                    <p v-if="location.address">
                      <span class="font-medium">Adresa:</span> {{ location.address }}
                    </p>
                    <p v-if="location.city">
                      <span class="font-medium">Grad:</span> {{ location.city }}
                    </p>
                    <p v-if="location.phone">
                      <span class="font-medium">Telefon:</span> {{ location.phone }}
                    </p>
                    <p v-if="location.latitude && location.longitude" class="text-xs text-gray-500">
                      GPS: {{ location.latitude }}, {{ location.longitude }}
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button
                    @click="startEditLocation(location)"
                    class="text-gray-500 hover:text-cyan-600 p-1"
                    title="Uredi"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    @click="handleDeleteLocation(location)"
                    class="text-gray-500 hover:text-red-600 p-1"
                    title="Obriši"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Edit Mode -->
            <div v-else>
              <form @submit.prevent="handleUpdateLocation" class="space-y-3">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Naziv *</label>
                    <input
                      type="text"
                      v-model="editLocationForm.name"
                      required
                      class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Grad</label>
                    <input
                      type="text"
                      v-model="editLocationForm.city"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700 mb-1">Adresa</label>
                  <input
                    type="text"
                    v-model="editLocationForm.address"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Telefon</label>
                    <input
                      type="tel"
                      v-model="editLocationForm.phone"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Latitude</label>
                    <input
                      type="number"
                      step="any"
                      v-model.number="editLocationForm.latitude"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Longitude</label>
                    <input
                      type="number"
                      step="any"
                      v-model.number="editLocationForm.longitude"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                </div>
                <div class="flex items-center gap-2 pt-2">
                  <button
                    type="button"
                    @click="geocodeEditLocation"
                    :disabled="isGeocodingEdit || (!editLocationForm.address && !editLocationForm.city)"
                    class="bg-blue-500 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-blue-600 disabled:bg-gray-400 flex items-center gap-1"
                  >
                    <svg v-if="isGeocodingEdit" class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    </svg>
                    GPS
                  </button>
                  <button
                    type="submit"
                    :disabled="isUpdatingLocation"
                    class="bg-cyan-600 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-cyan-700 disabled:bg-gray-400"
                  >
                    {{ isUpdatingLocation ? 'Čuva se...' : 'Sačuvaj' }}
                  </button>
                  <button
                    type="button"
                    @click="cancelEditLocation"
                    class="bg-gray-300 text-gray-700 px-3 py-1.5 rounded-md text-sm font-medium hover:bg-gray-400"
                  >
                    Otkaži
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-8">
          <div class="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h4 class="text-md font-medium text-gray-900 mb-1">Nema lokacija</h4>
          <p class="text-sm text-gray-500 mb-4">Dodajte prvu lokaciju za ovaj biznis</p>
        </div>

        <!-- Close Button -->
        <div class="mt-6 pt-4 border-t border-gray-200 flex justify-end">
          <button
            @click="closeLocationsModal"
            class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 text-sm font-medium"
          >
            Zatvori
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'admin'
})

const { user } = useAuth()
const { get, post, put, upload, delete: del } = useApi()
const config = useRuntimeConfig()

const apiBaseUrl = config.public.apiBase || 'http://localhost:5001'

const isLoading = ref(true)
const businesses = ref<any[]>([])

// Logo upload modal
const showLogoModal = ref(false)
const currentBusinessId = ref<number | null>(null)
const logoFile = ref<File | null>(null)
const logoPreview = ref<string | null>(null)
const isUploadingLogo = ref(false)

// Edit modal
const showEditModal = ref(false)
const isSubmittingEdit = ref(false)
const editForm = ref({
  id: null as number | null,
  name: '',
  phone: '',
  city: '',
  google_link: ''
})

// Delete business
const showDeleteConfirm = ref(false)
const isDeletingBusiness = ref(false)

// Cities for dropdown
const cities = ref<string[]>([])

// Map modal
const showMapModal = ref(false)
const mapBusiness = ref<any>(null)
const currentMapEmbedUrl = ref<string | null>(null)

// Invite modal
const showInviteModal = ref(false)
const isSubmittingInvite = ref(false)
const inviteForm = ref({
  business_id: null as number | null,
  email: '',
  role: 'staff'
})

// PDF modal
const showPdfModal = ref(false)
const pdfForm = ref({
  business_id: null as number | null,
  pdf_url: '',
  last_sync: null as string | null
})

// Locations modal
const showLocationsModal = ref(false)
const locationsBusiness = ref<any>(null)
const businessLocations = ref<any[]>([])
const isLoadingLocations = ref(false)
const showAddLocationForm = ref(false)
const isAddingLocation = ref(false)
const editingLocationId = ref<number | null>(null)
const isUpdatingLocation = ref(false)

interface LocationForm {
  name: string
  address: string
  city: string
  phone: string
  latitude: number | null
  longitude: number | null
}

const newLocation = ref<LocationForm>({
  name: '',
  address: '',
  city: '',
  phone: '',
  latitude: null,
  longitude: null
})

const editLocationForm = ref<LocationForm>({
  name: '',
  address: '',
  city: '',
  phone: '',
  latitude: null,
  longitude: null
})

// Geocoding state
const isGeocodingNew = ref(false)
const isGeocodingEdit = ref(false)

// AI Categorization
const isCategorizingBusiness = ref<Set<number>>(new Set())
const pdfFile = ref<File | null>(null)
const isSavingPdfUrl = ref(false)
const isSyncingPdf = ref(false)
const isUploadingPdf = ref(false)
const pdfResults = ref<{ type: 'success' | 'error', message: string } | null>(null)

onMounted(async () => {
  await Promise.all([loadBusinesses(), loadCities()])
})

// Computed map embed URL for edit modal
const editMapEmbedUrl = computed(() => {
  if (!editForm.value.google_link) return null
  return getMapEmbedUrl(editForm.value.google_link)
})

async function loadCities() {
  try {
    const data = await get('/auth/cities')
    cities.value = data.cities || []
  } catch (error) {
    console.error('Error loading cities:', error)
    cities.value = ['Sarajevo', 'Tuzla', 'Zenica', 'Mostar', 'Banja Luka', 'Bijeljina', 'Brčko']
  }
}

async function loadBusinesses() {
  isLoading.value = true
  try {
    const data = await get('/api/businesses/my')
    businesses.value = data.businesses || []
  } catch (error) {
    console.error('Error loading businesses:', error)
  } finally {
    isLoading.value = false
  }
}

function openLogoUploadModal(businessId: number) {
  currentBusinessId.value = businessId
  showLogoModal.value = true
}

function closeLogoModal() {
  showLogoModal.value = false
  currentBusinessId.value = null
  logoFile.value = null
  logoPreview.value = null
}

// Map modal functions
function openMapModal(business: any) {
  mapBusiness.value = business
  currentMapEmbedUrl.value = getMapEmbedUrl(business.google_link)
  showMapModal.value = true
}

function closeMapModal() {
  showMapModal.value = false
  mapBusiness.value = null
  currentMapEmbedUrl.value = null
}

function getMapEmbedUrl(url: string): string | null {
  if (!url) return null

  try {
    // Handle various Google Maps URL formats
    if (url.includes('google.com/maps')) {
      // Format: /maps/search/query/@lat,lng,zoom
      const searchMatch = url.match(/\/maps\/search\/([^/@]+)/)
      if (searchMatch) {
        const query = decodeURIComponent(searchMatch[1].replace(/\+/g, ' '))
        return `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(query)}`
      }

      // Format: /maps/place/name/@lat,lng
      const placeMatch = url.match(/\/maps\/place\/([^/@]+)/)
      if (placeMatch) {
        const place = decodeURIComponent(placeMatch[1].replace(/\+/g, ' '))
        return `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(place)}`
      }

      // Format with coordinates: @lat,lng,zoom
      const coordMatch = url.match(/@(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+)z/)
      if (coordMatch) {
        const [, lat, lng, zoom] = coordMatch
        const pathQuery = url.match(/\/maps\/[^/]+\/([^/@]+)/)
        if (pathQuery) {
          const query = decodeURIComponent(pathQuery[1].replace(/\+/g, ' '))
          return `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(query)}&center=${lat},${lng}&zoom=${zoom}`
        }
        return `https://www.google.com/maps/embed/v1/view?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&center=${lat},${lng}&zoom=${zoom}`
      }
    }

    return null
  } catch (e) {
    return null
  }
}

function handleLogoFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    logoFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      logoPreview.value = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

function removeLogoPreview() {
  logoFile.value = null
  logoPreview.value = null
  const fileInput = document.getElementById('logo-file') as HTMLInputElement
  if (fileInput) fileInput.value = ''
}

async function handleLogoUpload() {
  if (!logoFile.value || !currentBusinessId.value) return

  isUploadingLogo.value = true
  try {
    const formData = new FormData()
    formData.append('logo', logoFile.value)

    const response = await upload(`/api/businesses/${currentBusinessId.value}/logo`, formData)

    if (response.success) {
      await loadBusinesses()
      closeLogoModal()
    }
  } catch (error: any) {
    console.error('Error uploading logo:', error)
    alert('Greška prilikom postavljanja loga: ' + error.message)
  } finally {
    isUploadingLogo.value = false
  }
}

function openEditModal(business: any) {
  editForm.value = {
    id: business.id,
    name: business.name,
    phone: business.contact_phone || '',
    city: business.city,
    google_link: business.google_link || ''
  }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  isSubmittingEdit.value = false
}

async function handleEditBusiness() {
  if (!editForm.value.id) return

  isSubmittingEdit.value = true
  try {
    const response = await post(`/api/businesses/${editForm.value.id}`, {
      name: editForm.value.name,
      contact_phone: editForm.value.phone,
      city: editForm.value.city,
      google_link: editForm.value.google_link
    })

    if (response.success) {
      await loadBusinesses()
      closeEditModal()
    }
  } catch (error: any) {
    console.error('Error updating business:', error)
    alert('Greška prilikom ažuriranja biznisa: ' + error.message)
  } finally {
    isSubmittingEdit.value = false
  }
}

function confirmDeleteBusiness() {
  showDeleteConfirm.value = true
}

async function handleDeleteBusiness() {
  if (!editForm.value.id) return

  isDeletingBusiness.value = true
  try {
    const response = await del(`/api/businesses/${editForm.value.id}`)

    if (response.success) {
      showDeleteConfirm.value = false
      closeEditModal()
      await loadBusinesses()
    }
  } catch (error: any) {
    console.error('Error deleting business:', error)
    alert('Greška prilikom brisanja radnje: ' + error.message)
  } finally {
    isDeletingBusiness.value = false
  }
}

function openInviteModal(businessId: number) {
  inviteForm.value = {
    business_id: businessId,
    email: '',
    role: 'staff'
  }
  showInviteModal.value = true
}

function closeInviteModal() {
  showInviteModal.value = false
  isSubmittingInvite.value = false
}

async function handleInviteUser() {
  if (!inviteForm.value.business_id) return

  isSubmittingInvite.value = true
  try {
    const response = await post(`/api/businesses/${inviteForm.value.business_id}/invite`, {
      email: inviteForm.value.email,
      role: inviteForm.value.role
    })

    if (response.success) {
      alert('Poziv uspješno poslan!')
      closeInviteModal()
    }
  } catch (error: any) {
    console.error('Error inviting user:', error)
    alert('Greška prilikom slanja poziva: ' + error.message)
  } finally {
    isSubmittingInvite.value = false
  }
}

function openPdfModal(business: any) {
  pdfForm.value = {
    business_id: business.id,
    pdf_url: business.pdf_url || '',
    last_sync: business.last_sync || null
  }
  pdfResults.value = null
  pdfFile.value = null
  showPdfModal.value = true
}

function closePdfModal() {
  showPdfModal.value = false
  pdfResults.value = null
}

// Track categorization job IDs per business
const categorizationJobs = ref<Map<number, string>>(new Map())

// AI Categorization function - runs in background with status polling
async function categorizeBusinessProducts(businessId: number) {
  if (isCategorizingBusiness.value.has(businessId)) return

  isCategorizingBusiness.value.add(businessId)
  isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)

  try {
    const response = await post('/api/admin/products/categorize', {
      business_id: businessId
    })

    if (response.status === 'no_products') {
      alert('Nema proizvoda za kategorizaciju')
      isCategorizingBusiness.value.delete(businessId)
      isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
      return
    }

    if (response.status === 'already_running') {
      alert('Kategorizacija je već u toku za ovaj biznis')
      categorizationJobs.value.set(businessId, response.job_id)
      return
    }

    if (response.job_id) {
      alert(`Kategorizacija pokrenuta u pozadini za ${response.remaining} proizvoda. Ne blokira server - možete nastaviti sa radom.`)
      categorizationJobs.value.set(businessId, response.job_id)
      // Start polling for status
      pollCategorizationStatus(businessId, response.job_id)
    }

  } catch (error: any) {
    console.error(`Error starting categorization for business ${businessId}:`, error)
    alert('Greška pri pokretanju kategorizacije')
    isCategorizingBusiness.value.delete(businessId)
    isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
  }
}

async function pollCategorizationStatus(businessId: number, jobId: string) {
  try {
    const response = await get(`/api/admin/products/categorize/status/${jobId}`)

    if (response.status === 'running') {
      const processed = response.processed || 0
      const remaining = response.remaining || 0
      console.log(`Kategorization progress: ${processed} processed, ${remaining} remaining`)

      // Continue polling every 10 seconds
      setTimeout(() => pollCategorizationStatus(businessId, jobId), 10000)
    } else if (response.status === 'completed') {
      alert(`Kategorizacija završena! Obrađeno ${response.processed} proizvoda.`)
      isCategorizingBusiness.value.delete(businessId)
      isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
      categorizationJobs.value.delete(businessId)
    } else if (response.status === 'error' || response.status === 'cancelled') {
      console.log(`Kategorization ${response.status} for business ${businessId}`)
      isCategorizingBusiness.value.delete(businessId)
      isCategorizingBusiness.value = new Set(isCategorizingBusiness.value)
      categorizationJobs.value.delete(businessId)
    }
  } catch (error) {
    console.error('Error polling categorization status:', error)
    // Continue polling even on error
    setTimeout(() => pollCategorizationStatus(businessId, jobId), 10000)
  }
}

async function savePdfUrl() {
  if (!pdfForm.value.business_id) return

  isSavingPdfUrl.value = true
  pdfResults.value = null

  try {
    const response = await post(`/biznisi/${pdfForm.value.business_id}/set-pdf-url`, {
      pdf_url: pdfForm.value.pdf_url
    })

    if (response.success) {
      pdfResults.value = {
        type: 'success',
        message: response.message || 'PDF URL je uspješno ažuriran'
      }
      await loadBusinesses()
    } else {
      pdfResults.value = {
        type: 'error',
        message: response.error || 'Greška pri ažuriranju PDF URL-a'
      }
    }
  } catch (error: any) {
    console.error('Error saving PDF URL:', error)
    pdfResults.value = {
      type: 'error',
      message: 'Greška pri ažuriranju PDF URL-a'
    }
  } finally {
    isSavingPdfUrl.value = false
  }
}

async function syncFromPdfUrl() {
  if (!pdfForm.value.business_id || !pdfForm.value.pdf_url) return

  isSyncingPdf.value = true
  pdfResults.value = null

  try {
    const response = await post(`/biznisi/${pdfForm.value.business_id}/sync-pdf`, {})

    if (response.success) {
      pdfForm.value.last_sync = new Date().toISOString()
      pdfResults.value = {
        type: 'success',
        message: response.message || `Uspješno sinhronizovano ${response.products_added || 0} proizvoda`
      }
      await loadBusinesses()
    } else {
      pdfResults.value = {
        type: 'error',
        message: response.error || 'Greška pri sinhronizaciji PDF-a'
      }
    }
  } catch (error: any) {
    console.error('Error syncing PDF:', error)
    pdfResults.value = {
      type: 'error',
      message: 'Greška pri sinhronizaciji PDF-a'
    }
  } finally {
    isSyncingPdf.value = false
  }
}

function handlePdfFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    pdfFile.value = file
  }
}

async function uploadPdf() {
  if (!pdfFile.value || !pdfForm.value.business_id) return

  isUploadingPdf.value = true
  pdfResults.value = null

  try {
    const formData = new FormData()
    formData.append('pdf_file', pdfFile.value)

    // Get auth token from localStorage
    const token = process.client ? localStorage.getItem('token') : null
    const headers: HeadersInit = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${config.public.apiBase}/biznisi/${pdfForm.value.business_id}/upload-pdf`, {
      method: 'POST',
      headers,
      body: formData
    })

    const data = await response.json()

    if (data.success) {
      pdfForm.value.last_sync = new Date().toISOString()
      pdfResults.value = {
        type: 'success',
        message: data.message || `Uspješno obrađeno ${data.products_added || 0} proizvoda`
      }
      pdfFile.value = null
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      await loadBusinesses()
    } else {
      pdfResults.value = {
        type: 'error',
        message: data.error || 'Greška pri obradi PDF fajla'
      }
    }
  } catch (error: any) {
    console.error('Error uploading PDF:', error)
    pdfResults.value = {
      type: 'error',
      message: 'Greška pri obradi PDF fajla'
    }
  } finally {
    isUploadingPdf.value = false
  }
}

// ==================== LOCATIONS FUNCTIONS ====================

async function openLocationsModal(business: any) {
  locationsBusiness.value = business
  showLocationsModal.value = true
  showAddLocationForm.value = false
  editingLocationId.value = null
  await loadBusinessLocations(business.id)
}

function closeLocationsModal() {
  showLocationsModal.value = false
  locationsBusiness.value = null
  businessLocations.value = []
  showAddLocationForm.value = false
  editingLocationId.value = null
  resetNewLocationForm()
}

async function loadBusinessLocations(businessId: number) {
  isLoadingLocations.value = true
  try {
    const data = await get(`/api/admin/businesses/${businessId}/locations`)
    businessLocations.value = data.locations || []
  } catch (error) {
    console.error('Error loading locations:', error)
    businessLocations.value = []
  } finally {
    isLoadingLocations.value = false
  }
}

function resetNewLocationForm() {
  newLocation.value = {
    name: '',
    address: '',
    city: '',
    phone: '',
    latitude: null,
    longitude: null
  }
}

function cancelAddLocation() {
  showAddLocationForm.value = false
  resetNewLocationForm()
}

async function handleAddLocation() {
  if (!locationsBusiness.value || !newLocation.value.name) return

  isAddingLocation.value = true
  try {
    // Auto-geocode if address/city provided but no coordinates
    if ((newLocation.value.address || newLocation.value.city) &&
        (!newLocation.value.latitude || !newLocation.value.longitude)) {
      try {
        const geoResponse = await post('/api/admin/businesses/geocode', {
          address: newLocation.value.address,
          city: newLocation.value.city
        })
        if (geoResponse.success) {
          newLocation.value.latitude = geoResponse.latitude
          newLocation.value.longitude = geoResponse.longitude
        }
      } catch (geoError) {
        console.log('Auto-geocoding failed, continuing without coordinates')
      }
    }

    const response = await post(`/api/admin/businesses/${locationsBusiness.value.id}/locations`, {
      name: newLocation.value.name,
      address: newLocation.value.address || null,
      city: newLocation.value.city || null,
      phone: newLocation.value.phone || null,
      latitude: newLocation.value.latitude,
      longitude: newLocation.value.longitude
    })

    if (response.success) {
      await loadBusinessLocations(locationsBusiness.value.id)
      showAddLocationForm.value = false
      resetNewLocationForm()
    }
  } catch (error: any) {
    console.error('Error adding location:', error)
    alert('Greška pri dodavanju lokacije: ' + (error.message || 'Nepoznata greška'))
  } finally {
    isAddingLocation.value = false
  }
}

function startEditLocation(location: any) {
  editingLocationId.value = location.id
  editLocationForm.value = {
    name: location.name || '',
    address: location.address || '',
    city: location.city || '',
    phone: location.phone || '',
    latitude: location.latitude,
    longitude: location.longitude
  }
}

function cancelEditLocation() {
  editingLocationId.value = null
}

async function handleUpdateLocation() {
  if (!locationsBusiness.value || !editingLocationId.value) return

  isUpdatingLocation.value = true
  try {
    // Auto-geocode if address/city provided but no coordinates
    if ((editLocationForm.value.address || editLocationForm.value.city) &&
        (!editLocationForm.value.latitude || !editLocationForm.value.longitude)) {
      try {
        const geoResponse = await post('/api/admin/businesses/geocode', {
          address: editLocationForm.value.address,
          city: editLocationForm.value.city
        })
        if (geoResponse.success) {
          editLocationForm.value.latitude = geoResponse.latitude
          editLocationForm.value.longitude = geoResponse.longitude
        }
      } catch (geoError) {
        console.log('Auto-geocoding failed, continuing without coordinates')
      }
    }

    const response = await put(`/api/admin/businesses/${locationsBusiness.value.id}/locations/${editingLocationId.value}`, {
      name: editLocationForm.value.name,
      address: editLocationForm.value.address || null,
      city: editLocationForm.value.city || null,
      phone: editLocationForm.value.phone || null,
      latitude: editLocationForm.value.latitude,
      longitude: editLocationForm.value.longitude
    })

    if (response.success) {
      await loadBusinessLocations(locationsBusiness.value.id)
      editingLocationId.value = null
    }
  } catch (error: any) {
    console.error('Error updating location:', error)
    alert('Greška pri ažuriranju lokacije: ' + (error.message || 'Nepoznata greška'))
  } finally {
    isUpdatingLocation.value = false
  }
}

async function handleDeleteLocation(location: any) {
  if (!locationsBusiness.value) return

  if (!confirm(`Jeste li sigurni da želite obrisati lokaciju "${location.name}"?`)) {
    return
  }

  try {
    const response = await del(`/api/admin/businesses/${locationsBusiness.value.id}/locations/${location.id}`)

    if (response.success) {
      await loadBusinessLocations(locationsBusiness.value.id)
    }
  } catch (error: any) {
    console.error('Error deleting location:', error)
    alert('Greška pri brisanju lokacije: ' + (error.message || 'Nepoznata greška'))
  }
}

// Geocoding functions
async function geocodeNewLocation() {
  if (!newLocation.value.address && !newLocation.value.city) return

  isGeocodingNew.value = true
  try {
    const response = await post('/api/admin/businesses/geocode', {
      address: newLocation.value.address,
      city: newLocation.value.city
    })

    if (response.success) {
      newLocation.value.latitude = response.latitude
      newLocation.value.longitude = response.longitude
    } else {
      alert(response.error || 'Nije moguće pronaći koordinate za ovu adresu')
    }
  } catch (error: any) {
    console.error('Geocoding error:', error)
    alert('Greška pri dohvaćanju koordinata: ' + (error.message || 'Nepoznata greška'))
  } finally {
    isGeocodingNew.value = false
  }
}

async function geocodeEditLocation() {
  if (!editLocationForm.value.address && !editLocationForm.value.city) return

  isGeocodingEdit.value = true
  try {
    const response = await post('/api/admin/businesses/geocode', {
      address: editLocationForm.value.address,
      city: editLocationForm.value.city
    })

    if (response.success) {
      editLocationForm.value.latitude = response.latitude
      editLocationForm.value.longitude = response.longitude
    } else {
      alert(response.error || 'Nije moguće pronaći koordinate za ovu adresu')
    }
  } catch (error: any) {
    console.error('Geocoding error:', error)
    alert('Greška pri dohvaćanju koordinata: ' + (error.message || 'Nepoznata greška'))
  } finally {
    isGeocodingEdit.value = false
  }
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('sr-Latn-BA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatExpiryDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('sr-Latn-BA', {
    day: '2-digit',
    month: '2-digit'
  })
}

function isExpiringSoon(dateString: string): boolean {
  const date = new Date(dateString)
  const today = new Date()
  const diffDays = Math.ceil((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diffDays <= 3
}

useSeoMeta({
  title: 'Upravljanje biznisom - Popust.ba',
  description: 'Dodajte i upravljajte vašim radnjama i proizvodima',
})
</script>
