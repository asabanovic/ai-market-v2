<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header with Back Button -->
      <div class="mb-8">
        <NuxtLink
          to="/admin"
          class="inline-flex items-center text-sm text-gray-500 hover:text-purple-600 mb-4 transition-colors"
        >
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
          </svg>
          Nazad na Dashboard
        </NuxtLink>
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Social Media</h1>
            <p class="text-gray-600">Automatsko objavljivanje na Facebook stranici</p>
          </div>
          <button
            @click="generatePosts"
            :disabled="generating"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
          >
            <svg v-if="generating" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Generiši postove
          </button>
        </div>
      </div>

      <!-- Config Status -->
      <div class="bg-white rounded-lg shadow p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
                <span class="text-white text-sm font-bold">f</span>
              </div>
              <span class="font-medium text-gray-900">Facebook</span>
            </div>
            <span
              :class="[
                'px-2 py-1 rounded-full text-xs font-medium',
                config.facebook?.enabled
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-700'
              ]"
            >
              {{ config.facebook?.enabled ? 'Aktivno' : 'DEV MODE' }}
            </span>
          </div>
          <div class="text-sm text-gray-500">
            Postovi: {{ config.posting_times?.join(', ') || '09:00, 12:00, 15:00, 18:00' }}
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Zakazano</p>
              <p class="text-3xl font-bold text-blue-600">{{ stats.scheduled }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Objavljeno</p>
              <p class="text-3xl font-bold text-green-600">{{ stats.published }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-500 text-sm">Neuspjelo</p>
              <p class="text-3xl font-bold text-red-600">{{ stats.failed }}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-12">
        <svg class="w-8 h-8 text-purple-600 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>

      <!-- Schedule View -->
      <div v-else class="space-y-6">
        <div v-for="day in days" :key="day.date" class="bg-white rounded-lg shadow overflow-hidden">
          <!-- Day Header -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">
                  {{ formatDayName(day.day_name) }}, {{ formatDate(day.date) }}
                </h3>
              </div>
              <span class="text-sm text-gray-500">
                {{ day.posts.length }} post{{ day.posts.length !== 1 ? 'a' : '' }}
              </span>
            </div>
          </div>

          <!-- Posts Grid -->
          <div v-if="day.posts.length > 0" class="p-6 grid gap-4 md:grid-cols-2">
            <div
              v-for="post in day.posts"
              :key="post.id"
              class="border rounded-lg p-4 relative"
              :class="{
                'border-blue-200 bg-blue-50': post.status === 'scheduled',
                'border-green-200 bg-green-50': post.status === 'published',
                'border-red-200 bg-red-50': post.status === 'failed',
                'border-gray-200 bg-gray-50': post.status === 'cancelled'
              }"
            >
              <!-- Time & Status -->
              <div class="flex items-center justify-between mb-3">
                <span class="font-medium text-gray-900 text-lg">
                  {{ formatTime(post.scheduled_time) }}
                </span>
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-xs font-medium',
                    {
                      'bg-blue-100 text-blue-700': post.status === 'scheduled',
                      'bg-green-100 text-green-700': post.status === 'published',
                      'bg-red-100 text-red-700': post.status === 'failed',
                      'bg-gray-100 text-gray-700': post.status === 'cancelled'
                    }
                  ]"
                >
                  {{ statusLabel(post.status) }}
                </span>
              </div>

              <!-- Products with Images -->
              <div class="space-y-3 mb-4">
                <div
                  v-for="(product, idx) in post.products"
                  :key="idx"
                  class="flex items-center gap-3 p-2 bg-white rounded-lg border border-gray-100 cursor-pointer hover:border-purple-300 hover:shadow-sm transition-all"
                  @click="openProductEdit(product.id)"
                >
                  <img
                    v-if="product.image_url"
                    :src="product.image_url"
                    :alt="product.title"
                    class="w-12 h-12 object-cover rounded"
                  />
                  <div v-else class="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                    <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-800 text-sm truncate">{{ product.title }}</div>
                    <div class="text-xs text-gray-500">{{ product.store }}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-green-600 font-bold">{{ product.discount_price?.toFixed(2) }} KM</div>
                    <div class="text-xs">
                      <span class="line-through text-gray-400">{{ product.base_price?.toFixed(2) }}</span>
                      <span class="text-red-500 font-medium ml-1">-{{ product.discount_pct }}%</span>
                    </div>
                  </div>
                  <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                  </svg>
                </div>
              </div>

              <!-- Full Post Content Preview -->
              <div class="mb-4">
                <button
                  @click="showPostContent(post)"
                  class="text-xs text-purple-600 hover:text-purple-800 flex items-center gap-1"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                  </svg>
                  Prikaži sadržaj posta
                </button>
              </div>

              <!-- Actions -->
              <div v-if="post.status === 'scheduled'" class="flex gap-2">
                <button
                  @click="regeneratePost(post.id)"
                  class="flex-1 px-3 py-2 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 flex items-center justify-center gap-1 text-gray-700 font-medium"
                  title="Regeneriši"
                >
                  <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                  </svg>
                  Regeneriši
                </button>
                <button
                  @click="publishPost(post.id)"
                  class="flex-1 px-3 py-2 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center justify-center gap-1"
                  title="Objavi sad"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                  </svg>
                  Objavi
                </button>
                <button
                  @click="deletePost(post.id)"
                  class="px-3 py-2 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200 flex items-center justify-center"
                  title="Obriši"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </button>
              </div>

              <!-- Error message -->
              <div v-if="post.status === 'failed' && post.error_message" class="mt-2 text-xs text-red-600">
                {{ post.error_message }}
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-else class="p-6 text-center text-gray-500">
            <svg class="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <p>Nema zakazanih postova</p>
          </div>
        </div>
      </div>

      <!-- Post Preview Modal -->
      <div
        v-if="selectedPost"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="selectedPost = null"
      >
        <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">Pregled posta</h3>
              <button @click="selectedPost = null" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <!-- Product Images -->
            <div class="mb-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Slike proizvoda:</h4>
              <div class="flex gap-2 overflow-x-auto pb-2">
                <div
                  v-for="(product, idx) in selectedPost.products"
                  :key="idx"
                  class="flex-shrink-0"
                >
                  <img
                    v-if="product.image_url"
                    :src="product.image_url"
                    :alt="product.title"
                    class="w-20 h-20 object-cover rounded-lg border border-gray-200"
                  />
                  <div v-else class="w-20 h-20 bg-gray-200 rounded-lg flex items-center justify-center">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- Post Content -->
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <pre class="whitespace-pre-wrap text-sm text-black font-normal leading-relaxed">{{ selectedPost.content }}</pre>
            </div>
          </div>
        </div>
      </div>

      <!-- Product Edit Modal -->
      <div
        v-if="editingProduct"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        @click.self="closeProductEdit"
      >
        <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold">Uredi proizvod #{{ editingProduct.id }}</h3>
              <button @click="closeProductEdit" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <!-- Product Info -->
            <div class="flex gap-4 mb-6">
              <div class="w-32 h-32 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                <img
                  v-if="editingProduct.image_path"
                  :src="getImageUrl(editingProduct.image_path)"
                  :alt="editingProduct.title"
                  class="w-full h-full object-contain"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                  <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                </div>
              </div>
              <div class="flex-grow">
                <h4 class="text-lg font-medium text-gray-900 mb-2">{{ editingProduct.title }}</h4>
                <div class="text-sm text-gray-500 mb-1">
                  <span class="font-medium">Prodavnica:</span> {{ editingProduct.business?.name }}
                </div>
                <div class="text-sm text-gray-500 mb-1">
                  <span class="font-medium">Cijena:</span> {{ editingProduct.base_price?.toFixed(2) }} KM
                  <span v-if="editingProduct.discount_price" class="ml-2 text-green-600 font-medium">
                    → {{ editingProduct.discount_price?.toFixed(2) }} KM
                  </span>
                </div>
                <div class="text-sm text-gray-500">
                  <span class="font-medium">Kategorija:</span> {{ editingProduct.category || 'N/A' }}
                </div>
              </div>
            </div>

            <!-- AI Image Suggestions -->
            <div class="mb-6">
              <div class="flex items-center justify-between mb-3">
                <h4 class="font-medium text-gray-900">AI Preporuke slika</h4>
                <button
                  @click="suggestImages"
                  :disabled="loadingSuggestions"
                  class="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1"
                >
                  <svg v-if="loadingSuggestions" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                  </svg>
                  Predloži slike
                </button>
              </div>

              <div v-if="imageSuggestions.length > 0" class="grid grid-cols-4 gap-2">
                <div
                  v-for="(img, idx) in imageSuggestions"
                  :key="idx"
                  class="relative cursor-pointer rounded-lg overflow-hidden border-2 hover:border-purple-500 transition-all"
                  :class="selectedImageUrl === img.url ? 'border-purple-500 ring-2 ring-purple-300' : 'border-gray-200'"
                  @click="selectImage(img.url)"
                >
                  <img :src="img.url" :alt="img.title" class="w-full h-20 object-cover" />
                  <div v-if="selectedImageUrl === img.url" class="absolute inset-0 bg-purple-500 bg-opacity-20 flex items-center justify-center">
                    <svg class="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                  </div>
                </div>
              </div>
              <p v-else class="text-sm text-gray-500">Klikni "Predloži slike" za AI preporuke</p>
            </div>

            <!-- Actions -->
            <div class="flex justify-end gap-3 pt-4 border-t">
              <button
                @click="closeProductEdit"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Zatvori
              </button>
              <button
                v-if="selectedImageUrl"
                @click="saveProductImage"
                :disabled="savingImage"
                class="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {{ savingImage ? 'Spremam...' : 'Spremi sliku' }}
              </button>
              <a
                :href="`/admin/products?search=${encodeURIComponent(editingProduct.title)}`"
                target="_blank"
                class="px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100"
              >
                Otvori u Products
              </a>
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

const api = useApi()
const { get, post } = api

const loading = ref(true)
const generating = ref(false)
const days = ref<any[]>([])
const stats = ref({
  scheduled: 0,
  published: 0,
  failed: 0
})
const config = ref<any>({})
const selectedPost = ref<any>(null)

// Product edit modal state
const editingProduct = ref<any>(null)
const loadingSuggestions = ref(false)
const imageSuggestions = ref<any[]>([])
const selectedImageUrl = ref<string | null>(null)
const savingImage = ref(false)

// Day name translations
const dayNames: Record<string, string> = {
  'Monday': 'Ponedjeljak',
  'Tuesday': 'Utorak',
  'Wednesday': 'Srijeda',
  'Thursday': 'Cetvrtak',
  'Friday': 'Petak',
  'Saturday': 'Subota',
  'Sunday': 'Nedjelja'
}

function formatDayName(name: string): string {
  return dayNames[name] || name
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const day = date.getDate()
  const months = ['Januar', 'Februar', 'Mart', 'April', 'Maj', 'Juni', 'Juli', 'August', 'Septembar', 'Oktobar', 'Novembar', 'Decembar']
  return `${day}. ${months[date.getMonth()]}`
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  // Add 1 hour for Bosnia timezone
  date.setHours(date.getHours() + 1)
  return date.toLocaleTimeString('bs-BA', { hour: '2-digit', minute: '2-digit' })
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    'scheduled': 'Zakazano',
    'published': 'Objavljeno',
    'failed': 'Neuspjelo',
    'cancelled': 'Otkazano'
  }
  return labels[status] || status
}

async function loadPosts() {
  loading.value = true
  try {
    const response = await get('/api/admin/social/posts?days=5')
    days.value = response.days || []
    stats.value = response.stats || { scheduled: 0, published: 0, failed: 0 }
  } catch (error) {
    console.error('Failed to load posts:', error)
  } finally {
    loading.value = false
  }
}

async function loadConfig() {
  try {
    const response = await get('/api/admin/social/config')
    config.value = response
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function generatePosts() {
  generating.value = true
  try {
    const response = await post('/api/admin/social/generate')
    alert(`Kreirano ${response.created} postova`)
    await loadPosts()
  } catch (error) {
    console.error('Failed to generate posts:', error)
    alert('Greska pri generisanju postova')
  } finally {
    generating.value = false
  }
}

async function regeneratePost(postId: number) {
  try {
    await post(`/api/admin/social/posts/${postId}/regenerate`)
    await loadPosts()
  } catch (error) {
    console.error('Failed to regenerate post:', error)
    alert('Greska pri regenerisanju')
  }
}

async function publishPost(postId: number) {
  if (!confirm('Objavi ovaj post sada?')) return

  try {
    await post(`/api/admin/social/posts/${postId}/publish`)
    await loadPosts()
  } catch (error) {
    console.error('Failed to publish post:', error)
    alert('Greska pri objavljivanju')
  }
}

async function deletePost(postId: number) {
  if (!confirm('Obriši ovaj zakazani post?')) return

  try {
    await api.del(`/api/admin/social/posts/${postId}`)
    await loadPosts()
  } catch (error) {
    console.error('Failed to delete post:', error)
    alert('Greska pri brisanju')
  }
}

async function openProductEdit(productId: number) {
  if (!productId) return

  try {
    const product = await get(`/api/admin/products/${productId}`)
    editingProduct.value = product
    imageSuggestions.value = []
    selectedImageUrl.value = null
  } catch (error) {
    console.error('Failed to load product:', error)
    alert('Greška pri učitavanju proizvoda')
  }
}

function closeProductEdit() {
  editingProduct.value = null
  imageSuggestions.value = []
  selectedImageUrl.value = null
}

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return path
}

async function suggestImages() {
  if (!editingProduct.value) return

  loadingSuggestions.value = true
  try {
    const response = await get(`/api/admin/products/${editingProduct.value.id}/suggest-images`)
    imageSuggestions.value = response.suggestions || []
  } catch (error) {
    console.error('Failed to get image suggestions:', error)
    alert('Greška pri dohvatu preporuka')
  } finally {
    loadingSuggestions.value = false
  }
}

function selectImage(url: string) {
  selectedImageUrl.value = selectedImageUrl.value === url ? null : url
}

async function saveProductImage() {
  if (!editingProduct.value || !selectedImageUrl.value) return

  savingImage.value = true
  try {
    await post(`/api/admin/products/${editingProduct.value.id}/set-image`, {
      image_url: selectedImageUrl.value
    })
    // Update local state
    editingProduct.value.image_path = selectedImageUrl.value
    selectedImageUrl.value = null
    // Reload posts to update images
    await loadPosts()
    alert('Slika spremljena!')
  } catch (error) {
    console.error('Failed to save image:', error)
    alert('Greška pri spremanju slike')
  } finally {
    savingImage.value = false
  }
}

function showPostContent(post: any) {
  selectedPost.value = post
}

onMounted(() => {
  loadPosts()
  loadConfig()
})
</script>
