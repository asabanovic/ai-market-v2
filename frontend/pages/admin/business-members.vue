<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header with Back Button -->
      <div class="mb-8">
        <NuxtLink
          to="/admin"
          class="inline-flex items-center text-sm text-gray-500 hover:text-purple-600 mb-4 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-4 h-4 mr-1" />
          Nazad na Dashboard
        </NuxtLink>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Upravljanje Poslovnicama</h1>
        <p class="text-gray-600">Povezivanje korisnika sa poslovnicama i upravljanje članstvima</p>
      </div>

      <!-- Business Selection -->
      <div class="bg-white rounded-xl shadow-md p-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Icon name="mdi:store" class="w-6 h-6 text-purple-600" />
          Odaberi Poslovnicu
        </h2>

        <div class="flex gap-4 mb-4">
          <input
            v-model="businessSearch"
            type="text"
            placeholder="Pretraži poslovnice po imenu..."
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            @input="debouncedSearchBusinesses"
          />
        </div>

        <!-- Business List -->
        <div v-if="isLoadingBusinesses" class="flex justify-center py-8">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <div v-else-if="businesses.length > 0" class="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
          <div
            v-for="business in businesses"
            :key="business.id"
            @click="selectBusiness(business)"
            :class="[
              'flex items-center justify-between px-4 py-3 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0',
              selectedBusiness?.id === business.id ? 'bg-purple-50 border-l-4 border-purple-600' : 'hover:bg-gray-50'
            ]"
          >
            <div class="flex items-center gap-3">
              <div v-if="business.logo_path" class="w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 bg-gray-100">
                <img :src="getImageUrl(business.logo_path)" :alt="business.name" class="w-full h-full object-contain" />
              </div>
              <div v-else class="w-10 h-10 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
                <span class="text-white font-bold">{{ business.name?.[0] || '?' }}</span>
              </div>
              <div>
                <div class="font-medium text-gray-900">{{ business.name }}</div>
                <div class="text-sm text-gray-500">{{ business.city }} | {{ business.status }}</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">{{ business.member_count }} članova</span>
              <button
                @click.stop="openEditBusinessModal(business)"
                class="px-2 py-1 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded transition-colors flex items-center gap-1"
                title="Uredi poslovnicu"
              >
                <Icon name="mdi:pencil" class="w-3.5 h-3.5" />
                Uredi
              </button>
              <Icon
                :name="selectedBusiness?.id === business.id ? 'mdi:check-circle' : 'mdi:chevron-right'"
                :class="selectedBusiness?.id === business.id ? 'text-purple-600' : 'text-gray-300'"
                class="w-5 h-5"
              />
            </div>
          </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
          Pretražite poslovnice za upravljanje članstvom
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-4">
          <button
            v-for="page in totalPages"
            :key="page"
            @click="loadBusinesses(page)"
            :class="[
              'px-3 py-1 rounded-lg text-sm font-medium transition-colors',
              currentPage === page ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            {{ page }}
          </button>
        </div>
      </div>

      <!-- Selected Business Members -->
      <div v-if="selectedBusiness" class="bg-white rounded-xl shadow-md p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Icon name="mdi:account-group" class="w-6 h-6 text-purple-600" />
            Članovi: {{ selectedBusiness.name }}
          </h2>
          <button
            @click="showAddMemberForm = !showAddMemberForm"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <Icon name="mdi:account-plus" class="w-5 h-5" />
            Dodaj člana
          </button>
        </div>

        <!-- Add Member Form -->
        <div v-if="showAddMemberForm" class="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 class="font-medium text-gray-900 mb-4">Dodaj novog člana</h3>
          <form @submit.prevent="addMember" class="flex flex-col sm:flex-row gap-4">
            <input
              v-model="newMemberEmail"
              type="email"
              placeholder="Email korisnika..."
              required
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
            />
            <select
              v-model="newMemberRole"
              class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
            >
              <option value="staff">Staff</option>
              <option value="manager">Manager</option>
              <option value="owner">Owner</option>
            </select>
            <button
              type="submit"
              :disabled="isAddingMember"
              class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              <Icon v-if="isAddingMember" name="mdi:loading" class="w-5 h-5 animate-spin" />
              <Icon v-else name="mdi:plus" class="w-5 h-5" />
              Dodaj
            </button>
          </form>
          <p class="mt-2 text-sm text-gray-500">
            Korisnik mora već biti registriran na platformi sa navedenim email-om.
          </p>
        </div>

        <!-- Members List -->
        <div v-if="isLoadingMembers" class="flex justify-center py-8">
          <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
        </div>

        <div v-else-if="members.length > 0" class="border border-gray-200 rounded-lg overflow-hidden">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">Korisnik</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">Email</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">Uloga</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">Dodano</th>
                <th class="px-4 py-3 text-right text-sm font-medium text-gray-700">Akcije</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="member in members" :key="member.id" class="hover:bg-gray-50">
                <td class="px-4 py-3">
                  <div class="font-medium text-gray-900">{{ member.name || 'Nepoznato' }}</div>
                </td>
                <td class="px-4 py-3 text-gray-600">{{ member.email }}</td>
                <td class="px-4 py-3">
                  <select
                    :value="member.role"
                    @change="updateMemberRole(member.id, ($event.target as HTMLSelectElement).value)"
                    class="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
                  >
                    <option value="staff">Staff</option>
                    <option value="manager">Manager</option>
                    <option value="owner">Owner</option>
                  </select>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500">
                  {{ formatDate(member.created_at) }}
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    @click="confirmRemoveMember(member)"
                    class="px-3 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded-lg transition-colors flex items-center gap-1 text-sm"
                    title="Ukloni člana"
                  >
                    <Icon name="mdi:trash-can" class="w-4 h-4" />
                    Ukloni
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
          Ova poslovnica nema članova. Dodajte prvog člana koristeći formu iznad.
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <div class="flex items-center gap-3">
          <Icon name="mdi:check-circle" class="w-6 h-6 text-green-600" />
          <p class="font-medium text-green-800">{{ successMessage }}</p>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <div class="flex items-center gap-3">
          <Icon name="mdi:alert-circle" class="w-6 h-6 text-red-600" />
          <p class="font-medium text-red-800">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- Remove Member Confirmation Modal -->
      <div v-if="memberToRemove" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="memberToRemove = null">
        <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
          <h3 class="text-lg font-bold text-gray-900 mb-2">Ukloni člana?</h3>
          <p class="text-gray-600 mb-4">
            Da li ste sigurni da želite ukloniti <strong>{{ memberToRemove.email }}</strong> iz poslovnice <strong>{{ selectedBusiness?.name }}</strong>?
          </p>
          <div class="flex gap-3 justify-end">
            <button
              @click="memberToRemove = null"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Odustani
            </button>
            <button
              @click="removeMember"
              :disabled="isRemovingMember"
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              <Icon v-if="isRemovingMember" name="mdi:loading" class="w-4 h-4 animate-spin" />
              Ukloni
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Business Modal -->
      <div v-if="editingBusiness" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="editingBusiness = null">
        <div class="bg-white rounded-xl p-6 max-w-lg w-full mx-4 shadow-xl max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Icon name="mdi:store-edit" class="w-6 h-6 text-purple-600" />
            Uredi poslovnicu
          </h3>

          <form @submit.prevent="saveBusinessDetails" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Naziv</label>
              <input
                v-model="editForm.name"
                type="text"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Slug (URL)
                <span class="text-gray-400 font-normal">- koristi se za javnu stranicu</span>
              </label>
              <div class="flex items-center gap-2">
                <span class="text-gray-500 text-sm">/prodavnica/</span>
                <input
                  v-model="editForm.slug"
                  type="text"
                  placeholder="moja-poslovnica"
                  class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
                />
              </div>
              <p class="text-xs text-gray-500 mt-1">Samo mala slova, brojevi i crtice (npr. "dm-drogerie")</p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Grad</label>
                <input
                  v-model="editForm.city"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
                <input
                  v-model="editForm.contact_phone"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Adresa</label>
              <input
                v-model="editForm.address"
                type="text"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Opis</label>
              <textarea
                v-model="editForm.description"
                rows="3"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Google Maps link</label>
              <input
                v-model="editForm.google_link"
                type="url"
                placeholder="https://maps.google.com/..."
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 bg-white"
              />
            </div>

            <div class="flex gap-3 justify-end pt-4">
              <button
                type="button"
                @click="editingBusiness = null"
                class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Odustani
              </button>
              <button
                type="submit"
                :disabled="isSavingBusiness"
                class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                <Icon v-if="isSavingBusiness" name="mdi:loading" class="w-4 h-4 animate-spin" />
                Spremi
              </button>
            </div>
          </form>
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

const config = useRuntimeConfig()
const { get, post, put, del } = useApi()
const { user } = useAuth()

// Redirect non-admins
if (!user.value?.is_admin) {
  navigateTo('/')
}

interface Business {
  id: number
  name: string
  slug: string
  city: string
  status: string
  logo_path: string | null
  member_count: number
}

interface Member {
  id: number
  user_id: string
  email: string
  name: string | null
  role: string
  is_active: boolean
  created_at: string
}

// State
const businessSearch = ref('')
const businesses = ref<Business[]>([])
const isLoadingBusinesses = ref(false)
const selectedBusiness = ref<Business | null>(null)
const currentPage = ref(1)
const totalPages = ref(1)

const members = ref<Member[]>([])
const isLoadingMembers = ref(false)
const showAddMemberForm = ref(false)
const newMemberEmail = ref('')
const newMemberRole = ref('staff')
const isAddingMember = ref(false)

const memberToRemove = ref<Member | null>(null)
const isRemovingMember = ref(false)

// Edit business state
const editingBusiness = ref<Business | null>(null)
const isSavingBusiness = ref(false)
const editForm = ref({
  name: '',
  slug: '',
  city: '',
  address: '',
  contact_phone: '',
  description: '',
  google_link: ''
})

const successMessage = ref('')
const errorMessage = ref('')

// Debounced search
let searchTimeout: NodeJS.Timeout

function debouncedSearchBusinesses() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadBusinesses(1)
  }, 300)
}

async function loadBusinesses(page = 1) {
  isLoadingBusinesses.value = true
  currentPage.value = page

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: '20'
    })
    if (businessSearch.value.trim()) {
      params.append('search', businessSearch.value.trim())
    }

    const data = await get(`/api/admin/businesses?${params}`)
    businesses.value = data.businesses
    totalPages.value = data.pages
  } catch (error: any) {
    console.error('Error loading businesses:', error)
    errorMessage.value = error.data?.error || 'Greška pri učitavanju poslovnica'
  } finally {
    isLoadingBusinesses.value = false
  }
}

async function selectBusiness(business: Business) {
  selectedBusiness.value = business
  showAddMemberForm.value = false
  await loadMembers()
}

async function loadMembers() {
  if (!selectedBusiness.value) return

  isLoadingMembers.value = true

  try {
    const data = await get(`/api/admin/businesses/${selectedBusiness.value.id}/members`)
    members.value = data.members
  } catch (error: any) {
    console.error('Error loading members:', error)
    errorMessage.value = error.data?.error || 'Greška pri učitavanju članova'
  } finally {
    isLoadingMembers.value = false
  }
}

async function addMember() {
  if (!selectedBusiness.value || !newMemberEmail.value.trim()) return

  isAddingMember.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await post(`/api/admin/businesses/${selectedBusiness.value.id}/members`, {
      email: newMemberEmail.value.trim(),
      role: newMemberRole.value
    })

    successMessage.value = result.message
    newMemberEmail.value = ''
    newMemberRole.value = 'staff'
    showAddMemberForm.value = false
    await loadMembers()
  } catch (error: any) {
    console.error('Error adding member:', error)
    errorMessage.value = error.data?.error || 'Greška pri dodavanju člana'
  } finally {
    isAddingMember.value = false
  }
}

async function updateMemberRole(memberId: number, newRole: string) {
  if (!selectedBusiness.value) return

  successMessage.value = ''
  errorMessage.value = ''

  try {
    await put(`/api/admin/businesses/${selectedBusiness.value.id}/members/${memberId}`, {
      role: newRole
    })
    successMessage.value = 'Uloga uspješno ažurirana'
    await loadMembers()
  } catch (error: any) {
    console.error('Error updating role:', error)
    errorMessage.value = error.data?.error || 'Greška pri ažuriranju uloge'
  }
}

function confirmRemoveMember(member: Member) {
  memberToRemove.value = member
}

async function removeMember() {
  if (!selectedBusiness.value || !memberToRemove.value) return

  isRemovingMember.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await del(`/api/admin/businesses/${selectedBusiness.value.id}/members/${memberToRemove.value.id}`)
    successMessage.value = result.message
    memberToRemove.value = null
    await loadMembers()
  } catch (error: any) {
    console.error('Error removing member:', error)
    errorMessage.value = error.data?.error || 'Greška pri uklanjanju člana'
  } finally {
    isRemovingMember.value = false
  }
}

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `${config.public.apiBase}/static/${path}`
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA')
}

async function openEditBusinessModal(business: Business) {
  editingBusiness.value = business

  // Fetch full business details
  try {
    const data = await get(`/api/admin/businesses/${business.id}`)
    editForm.value = {
      name: data.business.name || '',
      slug: data.business.slug || '',
      city: data.business.city || '',
      address: data.business.address || '',
      contact_phone: data.business.contact_phone || '',
      description: data.business.description || '',
      google_link: data.business.google_link || ''
    }
  } catch (error) {
    console.error('Error loading business details:', error)
    // Use basic info from list
    editForm.value = {
      name: business.name || '',
      slug: business.slug || '',
      city: business.city || '',
      address: '',
      contact_phone: '',
      description: '',
      google_link: ''
    }
  }
}

async function saveBusinessDetails() {
  if (!editingBusiness.value) return

  isSavingBusiness.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await put(`/api/admin/businesses/${editingBusiness.value.id}`, editForm.value)
    successMessage.value = 'Poslovnica uspješno ažurirana'
    editingBusiness.value = null
    // Refresh the businesses list
    await loadBusinesses(currentPage.value)
  } catch (error: any) {
    console.error('Error saving business:', error)
    errorMessage.value = error.data?.error || 'Greška pri spremanju poslovnice'
  } finally {
    isSavingBusiness.value = false
  }
}

// Load initial businesses
onMounted(() => {
  loadBusinesses()
})

useSeoMeta({
  title: 'Upravljanje Poslovnicama - Admin - Popust.ba',
  description: 'Admin panel za upravljanje članstvom poslovnica'
})
</script>
