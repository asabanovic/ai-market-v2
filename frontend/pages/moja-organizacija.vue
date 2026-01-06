<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header -->
      <div class="mb-8">
        <NuxtLink
          to="/profile"
          class="inline-flex items-center text-sm text-gray-500 hover:text-purple-600 mb-4 transition-colors"
        >
          <Icon name="mdi:arrow-left" class="w-4 h-4 mr-1" />
          Nazad na profil
        </NuxtLink>

        <div v-if="organization" class="flex items-center gap-4">
          <div v-if="organization.logo_path" class="w-16 h-16 rounded-lg overflow-hidden bg-gray-100">
            <img :src="getImageUrl(organization.logo_path)" :alt="organization.name" class="w-full h-full object-contain" />
          </div>
          <div v-else class="w-16 h-16 rounded-lg bg-purple-600 flex items-center justify-center">
            <span class="text-white text-2xl font-bold">{{ organization.name?.[0] || '?' }}</span>
          </div>
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ organization.name }}</h1>
            <p class="text-gray-600">
              {{ organization.city }} |
              <span class="capitalize">{{ userRole }}</span> |
              {{ organization.product_count }} proizvoda
            </p>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center py-16">
        <Icon name="mdi:loading" class="w-12 h-12 text-purple-600 animate-spin" />
      </div>

      <!-- No Organization -->
      <div v-else-if="!organization" class="bg-white rounded-xl shadow-md p-8 text-center">
        <Icon name="mdi:store-off" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Niste povezani sa organizacijom</h2>
        <p class="text-gray-600">Kontaktirajte administratora za dodavanje u poslovnicu.</p>
      </div>

      <!-- Organization Content -->
      <div v-else>
        <!-- Bulk Upload Section -->
        <div class="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Icon name="mdi:cloud-upload" class="w-6 h-6 text-purple-600" />
            Bulk Upload Slika
          </h2>

          <div
            class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
            :class="isDragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-purple-400'"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              accept="image/*"
              class="hidden"
              @change="handleFileSelect"
            />

            <Icon name="mdi:image-multiple" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p class="text-gray-600 mb-2">
              Prevucite slike ovdje ili
              <button
                @click="$refs.fileInput.click()"
                class="text-purple-600 hover:text-purple-700 font-medium underline"
              >
                odaberite iz galerije
              </button>
            </p>
            <p class="text-sm text-gray-500">
              AI automatski prepoznaje proizvode sa slika i popunjava informacije
            </p>
          </div>

          <!-- Upload Progress -->
          <div v-if="uploadingFiles.length > 0" class="mt-4 space-y-3">
            <div
              v-for="file in uploadingFiles"
              :key="file.name"
              class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
            >
              <div class="w-12 h-12 rounded overflow-hidden bg-gray-200 flex-shrink-0">
                <img :src="file.preview" :alt="file.name" class="w-full h-full object-cover" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ file.name }}</p>
                <div v-if="file.status === 'uploading'" class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-purple-600 transition-all" :style="{ width: `${file.progress}%` }"></div>
                  </div>
                  <span class="text-xs text-gray-500">{{ file.progress }}%</span>
                </div>
                <p v-else-if="file.status === 'processing'" class="text-sm text-blue-600 flex items-center gap-1">
                  <Icon name="mdi:loading" class="w-4 h-4 animate-spin" />
                  AI procesira sliku...
                </p>
                <p v-else-if="file.status === 'done'" class="text-sm text-green-600 flex items-center gap-1">
                  <Icon name="mdi:check" class="w-4 h-4" />
                  {{ file.result?.title || 'Uspjesno' }}
                </p>
                <p v-else-if="file.status === 'error'" class="text-sm text-red-600 flex items-center gap-1">
                  <Icon name="mdi:alert" class="w-4 h-4" />
                  {{ file.error }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Products Section -->
        <div class="bg-white rounded-xl shadow-md p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Icon name="mdi:package-variant" class="w-6 h-6 text-purple-600" />
              Proizvodi ({{ totalProducts }})
            </h2>
            <div class="flex gap-2">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Pretrazi proizvode..."
                class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                @input="debouncedSearch"
              />
            </div>
          </div>

          <!-- Products Loading -->
          <div v-if="isLoadingProducts" class="flex justify-center py-8">
            <Icon name="mdi:loading" class="w-8 h-8 text-purple-600 animate-spin" />
          </div>

          <!-- Products Grid -->
          <div v-else-if="products.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            <div
              v-for="product in products"
              :key="product.id"
              class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <!-- Product Image -->
              <div class="aspect-square bg-gray-100 rounded-lg mb-3 overflow-hidden relative group">
                <img
                  v-if="product.image_path"
                  :src="getImageUrl(product.image_path)"
                  :alt="product.title"
                  class="w-full h-full object-contain"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <Icon name="mdi:image-off" class="w-12 h-12" />
                </div>

                <!-- Hover Actions -->
                <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 transition-opacity">
                  <button
                    @click="openEditModal(product)"
                    class="p-2 bg-white rounded-full text-purple-600 hover:bg-purple-50"
                    title="Uredi"
                  >
                    <Icon name="mdi:pencil" class="w-5 h-5" />
                  </button>
                  <button
                    v-if="canDelete"
                    @click="confirmDelete(product)"
                    class="p-2 bg-white rounded-full text-red-600 hover:bg-red-50"
                    title="Obrisi"
                  >
                    <Icon name="mdi:trash-can" class="w-5 h-5" />
                  </button>
                </div>
              </div>

              <!-- Product Info -->
              <h3 class="font-medium text-gray-900 line-clamp-2 mb-2" :title="product.title">
                {{ product.title }}
              </h3>
              <div class="flex items-baseline gap-2 mb-1">
                <span class="text-lg font-bold text-gray-900">
                  {{ formatPrice(product.discount_price || product.base_price) }} KM
                </span>
                <span
                  v-if="product.discount_price && product.base_price > product.discount_price"
                  class="text-sm text-gray-400 line-through"
                >
                  {{ formatPrice(product.base_price) }} KM
                </span>
              </div>
              <p class="text-sm text-gray-500">
                {{ product.brand }} | {{ product.size_value }}{{ product.size_unit }}
              </p>
            </div>
          </div>

          <!-- No Products -->
          <div v-else class="text-center py-8 text-gray-500">
            <Icon name="mdi:package-variant-remove" class="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>Nema proizvoda. Uploadajte slike za dodavanje proizvoda.</p>
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-6">
            <button
              @click="loadProducts(currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-3 py-1 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Icon name="mdi:chevron-left" class="w-5 h-5" />
            </button>
            <span class="px-4 py-1 text-sm text-gray-600">
              Stranica {{ currentPage }} od {{ totalPages }}
            </span>
            <button
              @click="loadProducts(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Icon name="mdi:chevron-right" class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Product Modal -->
      <div v-if="showEditModal && editingProduct" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-center justify-center min-h-screen px-4 py-8">
          <div class="fixed inset-0 bg-black/50" @click="closeEditModal"></div>

          <div class="relative z-10 w-full max-w-2xl bg-white rounded-xl shadow-xl overflow-hidden">
            <!-- Modal Header -->
            <div class="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Uredi proizvod</h3>
              <button @click="closeEditModal" class="text-gray-400 hover:text-gray-600">
                <Icon name="mdi:close" class="w-6 h-6" />
              </button>
            </div>

            <!-- Modal Body -->
            <div class="px-6 py-4 max-h-[70vh] overflow-y-auto">
              <!-- Image Section -->
              <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Slika proizvoda</label>
                <div class="flex gap-4">
                  <!-- Current Image -->
                  <div class="w-32 h-32 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                    <img
                      v-if="editingProduct.image_path"
                      :src="getImageUrl(editingProduct.image_path)"
                      :alt="editingProduct.title"
                      class="w-full h-full object-contain"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                      <Icon name="mdi:image-off" class="w-10 h-10" />
                    </div>
                  </div>

                  <!-- Upload Options -->
                  <div class="flex-1 space-y-3">
                    <input
                      ref="productImageInput"
                      type="file"
                      accept="image/*"
                      class="hidden"
                      @change="handleProductImageUpload"
                    />
                    <button
                      @click="$refs.productImageInput.click()"
                      :disabled="isUploadingProductImage"
                      class="w-full py-2 px-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      <Icon v-if="isUploadingProductImage" name="mdi:loading" class="w-5 h-5 animate-spin" />
                      <Icon v-else name="mdi:upload" class="w-5 h-5" />
                      Upload sa uredaja
                    </button>

                    <!-- Online Image Search -->
                    <div class="flex gap-2">
                      <input
                        v-model="imageSearchQuery"
                        type="text"
                        placeholder="Pretrazi slike online..."
                        class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                        @keyup.enter="searchOnlineImages"
                      />
                      <button
                        @click="searchOnlineImages"
                        :disabled="isSearchingImages"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        <Icon v-if="isSearchingImages" name="mdi:loading" class="w-5 h-5 animate-spin" />
                        <Icon v-else name="mdi:magnify" class="w-5 h-5" />
                      </button>
                    </div>

                    <!-- Online Image Results -->
                    <div v-if="onlineImages.length > 0" class="grid grid-cols-4 gap-2 max-h-24 overflow-y-auto">
                      <div
                        v-for="(img, idx) in onlineImages"
                        :key="idx"
                        @click="selectOnlineImage(img)"
                        class="aspect-square bg-gray-100 rounded cursor-pointer hover:ring-2 ring-purple-500 overflow-hidden"
                      >
                        <img :src="img" :alt="`Result ${idx + 1}`" class="w-full h-full object-cover" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Title -->
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda</label>
                <input
                  v-model="editForm.title"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <!-- Price Fields -->
              <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Osnovna cijena (KM)</label>
                  <input
                    v-model.number="editForm.base_price"
                    type="number"
                    step="0.01"
                    min="0"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Akcijska cijena (KM)</label>
                  <input
                    v-model.number="editForm.discount_price"
                    type="number"
                    step="0.01"
                    min="0"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <p class="text-xs text-gray-500 mt-1">Ostavite prazno ako nema akcije</p>
                </div>
              </div>

              <!-- Brand and Product Type -->
              <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Brend</label>
                  <input
                    v-model="editForm.brand"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Tip proizvoda</label>
                  <input
                    v-model="editForm.product_type"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <!-- Size -->
              <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Velicina</label>
                  <input
                    v-model.number="editForm.size_value"
                    type="number"
                    step="0.01"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Jedinica</label>
                  <input
                    v-model="editForm.size_unit"
                    type="text"
                    placeholder="g, ml, kom"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <!-- Category -->
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">Kategorija</label>
                <select
                  v-model="editForm.category_group"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">-</option>
                  <option value="meso">Meso</option>
                  <option value="mlijeko">Mlijeko</option>
                  <option value="pica">Pica</option>
                  <option value="voce_povrce">Voce i povrce</option>
                  <option value="kuhinja">Kuhinja</option>
                  <option value="ves">Ves</option>
                  <option value="ciscenje">Ciscenje</option>
                  <option value="higijena">Higijena</option>
                  <option value="slatkisi">Slatkisi</option>
                  <option value="kafa">Kafa</option>
                  <option value="smrznuto">Smrznuto</option>
                  <option value="pekara">Pekara</option>
                  <option value="ljubimci">Ljubimci</option>
                  <option value="bebe">Bebe</option>
                  <option value="ostalo">Ostalo</option>
                </select>
              </div>

              <!-- Price History -->
              <div v-if="editingProduct.price_history && editingProduct.price_history.length > 0" class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">Historija cijena</label>
                <div class="border border-gray-200 rounded-lg max-h-32 overflow-y-auto">
                  <div
                    v-for="(history, idx) in editingProduct.price_history"
                    :key="idx"
                    class="px-3 py-2 border-b border-gray-100 last:border-b-0 text-sm"
                  >
                    <span class="text-gray-500">{{ formatDate(history.changed_at) }}</span>
                    <span class="mx-2">-</span>
                    <span class="font-medium">{{ formatPrice(history.base_price) }} KM</span>
                    <span v-if="history.discount_price" class="text-green-600 ml-1">
                      ({{ formatPrice(history.discount_price) }} KM)
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Modal Footer -->
            <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
              <button
                @click="closeEditModal"
                class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Odustani
              </button>
              <button
                @click="saveProduct"
                :disabled="isSavingProduct"
                class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Icon v-if="isSavingProduct" name="mdi:loading" class="w-5 h-5 animate-spin" />
                Sacuvaj
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div v-if="productToDelete" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="fixed inset-0 bg-black/50" @click="productToDelete = null"></div>
        <div class="relative z-10 bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
          <h3 class="text-lg font-bold text-gray-900 mb-2">Obrisi proizvod?</h3>
          <p class="text-gray-600 mb-4">
            Da li ste sigurni da zelite obrisati proizvod <strong>"{{ productToDelete.title }}"</strong>?
            Ova akcija se ne moze ponistiti.
          </p>
          <div class="flex gap-3 justify-end">
            <button
              @click="productToDelete = null"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Odustani
            </button>
            <button
              @click="deleteProduct"
              :disabled="isDeletingProduct"
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Icon v-if="isDeletingProduct" name="mdi:loading" class="w-4 h-4 animate-spin" />
              Obrisi
            </button>
          </div>
        </div>
      </div>

      <!-- Success/Error Messages -->
      <div v-if="successMessage" class="fixed bottom-4 right-4 bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg z-50">
        <div class="flex items-center gap-3">
          <Icon name="mdi:check-circle" class="w-6 h-6 text-green-600" />
          <p class="font-medium text-green-800">{{ successMessage }}</p>
          <button @click="successMessage = ''" class="text-green-600 hover:text-green-800">
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>
        </div>
      </div>

      <div v-if="errorMessage" class="fixed bottom-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg z-50">
        <div class="flex items-center gap-3">
          <Icon name="mdi:alert-circle" class="w-6 h-6 text-red-600" />
          <p class="font-medium text-red-800">{{ errorMessage }}</p>
          <button @click="errorMessage = ''" class="text-red-600 hover:text-red-800">
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>
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

interface Organization {
  id: number
  name: string
  slug: string
  city: string
  logo_path: string | null
  product_count: number
}

interface Product {
  id: number
  title: string
  brand: string
  product_type: string
  size_value: number | null
  size_unit: string | null
  base_price: number
  discount_price: number | null
  image_path: string | null
  category_group: string | null
  price_history?: Array<{
    base_price: number
    discount_price: number | null
    changed_at: string
  }>
}

interface UploadingFile {
  name: string
  preview: string
  file: File
  status: 'uploading' | 'processing' | 'done' | 'error'
  progress: number
  result?: any
  error?: string
}

// State
const isLoading = ref(true)
const organization = ref<Organization | null>(null)
const userRole = ref('')
const products = ref<Product[]>([])
const isLoadingProducts = ref(false)
const currentPage = ref(1)
const totalProducts = ref(0)
const totalPages = ref(1)
const searchQuery = ref('')

// Upload state
const isDragging = ref(false)
const uploadingFiles = ref<UploadingFile[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

// Edit modal state
const showEditModal = ref(false)
const editingProduct = ref<Product | null>(null)
const editForm = ref({
  title: '',
  base_price: 0,
  discount_price: null as number | null,
  brand: '',
  product_type: '',
  size_value: null as number | null,
  size_unit: '',
  category_group: ''
})
const isSavingProduct = ref(false)
const isUploadingProductImage = ref(false)
const productImageInput = ref<HTMLInputElement | null>(null)

// Online image search
const imageSearchQuery = ref('')
const isSearchingImages = ref(false)
const onlineImages = ref<string[]>([])

// Delete state
const productToDelete = ref<Product | null>(null)
const isDeletingProduct = ref(false)

// Messages
const successMessage = ref('')
const errorMessage = ref('')

// Computed
const canDelete = computed(() => userRole.value === 'manager' || userRole.value === 'owner')

// Methods
function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `${config.public.apiBase}/static/${path}`
}

function formatPrice(price: number | null): string {
  if (price === null || price === undefined) return '0.00'
  return price.toFixed(2)
}

function formatDate(dateString: string): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('bs-BA')
}

// Debounced search
let searchTimeout: NodeJS.Timeout

function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadProducts(1)
  }, 300)
}

async function loadOrganization() {
  isLoading.value = true

  try {
    const data = await get('/api/my-organization')
    organization.value = data.organization
    userRole.value = data.role
    await loadProducts(1)
  } catch (error: any) {
    if (error.statusCode === 404) {
      organization.value = null
    } else {
      errorMessage.value = error.data?.error || 'Greska pri ucitavanju organizacije'
    }
  } finally {
    isLoading.value = false
  }
}

async function loadProducts(page = 1) {
  isLoadingProducts.value = true
  currentPage.value = page

  try {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: '30'
    })
    if (searchQuery.value.trim()) {
      params.append('search', searchQuery.value.trim())
    }

    const data = await get(`/api/my-organization/products?${params}`)
    products.value = data.products
    totalProducts.value = data.total
    totalPages.value = data.pages
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greska pri ucitavanju proizvoda'
  } finally {
    isLoadingProducts.value = false
  }
}

// File upload handling
function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    processFiles(Array.from(files))
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    processFiles(Array.from(input.files))
    input.value = '' // Reset input
  }
}

function processFiles(files: File[]) {
  const imageFiles = files.filter(f => f.type.startsWith('image/'))

  for (const file of imageFiles) {
    const uploadFile: UploadingFile = {
      name: file.name,
      preview: URL.createObjectURL(file),
      file,
      status: 'uploading',
      progress: 0
    }
    uploadingFiles.value.push(uploadFile)
    uploadSingleFile(uploadFile)
  }
}

async function uploadSingleFile(uploadFile: UploadingFile) {
  try {
    const formData = new FormData()
    formData.append('images', uploadFile.file)

    // Simulate progress
    const progressInterval = setInterval(() => {
      if (uploadFile.progress < 90) {
        uploadFile.progress += 10
      }
    }, 200)

    uploadFile.status = 'uploading'

    const response = await fetch(`${config.public.apiBase}/api/my-organization/upload-images`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.value?.token}`
      },
      body: formData
    })

    clearInterval(progressInterval)
    uploadFile.progress = 100

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'Upload failed')
    }

    uploadFile.status = 'processing'

    const data = await response.json()

    if (data.results && data.results.length > 0) {
      const result = data.results[0]
      if (result.success) {
        uploadFile.status = 'done'
        uploadFile.result = result.product

        // Refresh products list
        await loadProducts(1)

        // Clear completed uploads after a delay
        setTimeout(() => {
          const idx = uploadingFiles.value.indexOf(uploadFile)
          if (idx !== -1) {
            uploadingFiles.value.splice(idx, 1)
          }
        }, 3000)
      } else {
        uploadFile.status = 'error'
        uploadFile.error = result.error
      }
    }
  } catch (error: any) {
    uploadFile.status = 'error'
    uploadFile.error = error.message || 'Upload failed'
  }
}

// Edit modal
function openEditModal(product: Product) {
  editingProduct.value = { ...product }
  editForm.value = {
    title: product.title,
    base_price: product.base_price,
    discount_price: product.discount_price,
    brand: product.brand || '',
    product_type: product.product_type || '',
    size_value: product.size_value,
    size_unit: product.size_unit || '',
    category_group: product.category_group || ''
  }
  imageSearchQuery.value = product.title || ''
  onlineImages.value = []
  showEditModal.value = true

  // Load full product details with price history
  loadProductDetails(product.id)
}

async function loadProductDetails(productId: number) {
  try {
    const data = await get(`/api/my-organization/products/${productId}`)
    if (editingProduct.value?.id === productId) {
      editingProduct.value = data.product
    }
  } catch (error) {
    console.error('Error loading product details:', error)
  }
}

function closeEditModal() {
  showEditModal.value = false
  editingProduct.value = null
  onlineImages.value = []
}

async function saveProduct() {
  if (!editingProduct.value) return

  isSavingProduct.value = true

  try {
    await put(`/api/my-organization/products/${editingProduct.value.id}`, editForm.value)
    successMessage.value = 'Proizvod uspjesno sacuvan'
    closeEditModal()
    await loadProducts(currentPage.value)
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greska pri spremanju proizvoda'
  } finally {
    isSavingProduct.value = false
  }
}

async function handleProductImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0] || !editingProduct.value) return

  isUploadingProductImage.value = true

  try {
    const formData = new FormData()
    formData.append('image', input.files[0])

    const response = await fetch(`${config.public.apiBase}/api/my-organization/products/${editingProduct.value.id}/upload-image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.value?.token}`
      },
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'Upload failed')
    }

    const data = await response.json()
    if (editingProduct.value) {
      editingProduct.value.image_path = data.image_path
    }
    successMessage.value = 'Slika uspjesno uploadana'
  } catch (error: any) {
    errorMessage.value = error.message || 'Greska pri uploadu slike'
  } finally {
    isUploadingProductImage.value = false
    input.value = ''
  }
}

async function searchOnlineImages() {
  if (!imageSearchQuery.value.trim()) return

  isSearchingImages.value = true
  onlineImages.value = []

  try {
    const response = await get(`/api/admin/products/${editingProduct.value?.id}/suggest-images`)
    if (response.images) {
      onlineImages.value = response.images.slice(0, 8)
    }
  } catch (error: any) {
    // Fallback - no images found
    console.error('Error searching images:', error)
  } finally {
    isSearchingImages.value = false
  }
}

async function selectOnlineImage(imageUrl: string) {
  if (!editingProduct.value) return

  isUploadingProductImage.value = true

  try {
    await put(`/api/my-organization/products/${editingProduct.value.id}`, {
      image_url: imageUrl
    })
    editingProduct.value.image_path = imageUrl
    onlineImages.value = []
    successMessage.value = 'Slika uspjesno odabrana'
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greska pri odabiru slike'
  } finally {
    isUploadingProductImage.value = false
  }
}

// Delete
function confirmDelete(product: Product) {
  productToDelete.value = product
}

async function deleteProduct() {
  if (!productToDelete.value) return

  isDeletingProduct.value = true

  try {
    await del(`/api/my-organization/products/${productToDelete.value.id}`)
    successMessage.value = 'Proizvod uspjesno obrisan'
    productToDelete.value = null
    await loadProducts(currentPage.value)
  } catch (error: any) {
    errorMessage.value = error.data?.error || 'Greska pri brisanju proizvoda'
  } finally {
    isDeletingProduct.value = false
  }
}

// Initialize
onMounted(() => {
  loadOrganization()
})

// Auto-hide messages
watch([successMessage, errorMessage], ([success, error]) => {
  if (success) {
    setTimeout(() => { successMessage.value = '' }, 5000)
  }
  if (error) {
    setTimeout(() => { errorMessage.value = '' }, 5000)
  }
})

useSeoMeta({
  title: 'Moja Organizacija - Popust.ba',
  description: 'Upravljajte proizvodima vase organizacije'
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
