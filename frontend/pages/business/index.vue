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
          class="bg-white rounded-lg shadow-md p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-start space-x-4 flex-1">
              <!-- Business Logo -->
              <div class="flex-shrink-0">
                <img
                  v-if="business.logo_path"
                  :src="`${apiBaseUrl}${business.logo_path}`"
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
                    <strong>Google Business:</strong>
                    <a :href="business.google_link" target="_blank" class="text-indigo-600 hover:text-indigo-800">
                      Pogledaj →
                    </a>
                  </p>
                </div>
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-500">
                <p>{{ business.product_count || 0 }} proizvoda</p>
                <p>{{ business.views || 0 }} pregleda</p>
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
      <div class="relative top-20 mx-auto p-6 border w-96 shadow-lg rounded-lg bg-white">
        <div class="mt-3">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Uredi biznis</h3>
          <form @submit.prevent="handleEditBusiness">
            <div class="mb-4">
              <label for="edit-business-name" class="block text-sm font-medium text-gray-700 mb-2">Naziv biznisa</label>
              <input type="text" id="edit-business-name" v-model="editForm.name" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
            </div>

            <div class="mb-4">
              <label for="edit-business-phone" class="block text-sm font-medium text-gray-700 mb-2">Telefon</label>
              <input type="tel" id="edit-business-phone" v-model="editForm.phone" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
            </div>

            <div class="mb-4">
              <label for="edit-business-city" class="block text-sm font-medium text-gray-700 mb-2">Grad</label>
              <input type="text" id="edit-business-city" v-model="editForm.city" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
            </div>

            <div class="mb-4">
              <label for="edit-business-google-link" class="block text-sm font-medium text-gray-700 mb-2">Google Business link</label>
              <input type="url" id="edit-business-google-link" v-model="editForm.google_link" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
            </div>

            <div class="flex space-x-3">
              <button type="submit" :disabled="isSubmittingEdit" class="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50">
                {{ isSubmittingEdit ? 'Čuva se...' : 'Sačuvaj izmjene' }}
              </button>
              <button type="button" @click="closeEditModal" class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400">
                Otkaži
              </button>
            </div>
          </form>
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
              <input type="email" id="invitation-email" v-model="inviteForm.email" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm">
            </div>

            <div class="mb-4">
              <label for="invitation-role" class="block text-sm font-medium text-gray-700 mb-2">Uloga</label>
              <select id="invitation-role" v-model="inviteForm.role" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm">
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
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'admin'
})

const { user } = useAuth()
const { get, post } = useApi()
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
const pdfFile = ref<File | null>(null)
const isSavingPdfUrl = ref(false)
const isSyncingPdf = ref(false)
const isUploadingPdf = ref(false)
const pdfResults = ref<{ type: 'success' | 'error', message: string } | null>(null)

onMounted(async () => {
  await loadBusinesses()
})

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

    const response = await post(`/api/businesses/${currentBusinessId.value}/logo`, formData)

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

useSeoMeta({
  title: 'Upravljanje biznisom - Rabat.ba',
  description: 'Dodajte i upravljajte vašim radnjama i proizvodima',
})
</script>
