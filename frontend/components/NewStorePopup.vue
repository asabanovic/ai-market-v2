<template>
  <Teleport to="body">
    <!-- Main Store Popup -->
    <div
      v-if="isVisible && newStores.length > 0 && !showMapPopup"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
    >
      <div class="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[80vh] overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 text-white">
          <div class="flex items-center gap-3">
            <div class="bg-white/20 rounded-full p-2">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9,22 9,12 15,12 15,22" />
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-bold">
                {{ newStores.length === 1 ? 'Nova prodavnica!' : 'Nove prodavnice!' }}
              </h2>
              <p class="text-sm text-purple-100">
                {{ newStores.length === 1 ? 'Dodali smo novu prodavnicu' : `Dodali smo ${newStores.length} nove prodavnice` }}
              </p>
            </div>
          </div>
        </div>

        <!-- Store List -->
        <div class="px-6 py-4 max-h-60 overflow-y-auto">
          <p class="text-sm text-gray-600 mb-4">
            Da li {{ newStores.length === 1 ? 'ova prodavnica postoji' : 'ove prodavnice postoje' }} u vašem gradu?
            Označite one koje želite uključiti u pretragu.
          </p>

          <div class="space-y-3">
            <label
              v-for="store in newStores"
              :key="store.id"
              class="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                v-model="selectedStoreIds"
                :value="store.id"
                class="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
              />
              <img
                v-if="store.logo"
                :src="getLogoUrl(store.logo)"
                :alt="store.name"
                class="w-10 h-10 object-contain"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="w-10 h-10 bg-gray-200 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-gray-400" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                </svg>
              </div>
              <div class="flex-1">
                <span class="font-medium text-gray-900">{{ store.name }}</span>
                <span v-if="store.city" class="text-xs text-gray-500 block">{{ store.city }}</span>
                <button
                  v-if="store.google_link"
                  @click.stop.prevent="openMapPopup(store)"
                  class="text-xs text-purple-600 hover:text-purple-800 mt-1 inline-flex items-center gap-1"
                >
                  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                  </svg>
                  Pogledaj lokacije
                </button>
              </div>
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
          <button
            @click="skipAll"
            class="flex-1 px-4 py-2 text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors"
          >
            Preskoči
          </button>
          <button
            @click="confirmSelection"
            :disabled="isSaving"
            class="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {{ isSaving ? 'Čuvanje...' : 'Potvrdi' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Map Popup (Full Screen Overlay) -->
    <div
      v-if="showMapPopup && selectedMapStore"
      class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/70"
      @click.self="closeMapPopup"
    >
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <!-- Map Header -->
        <div class="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 text-white flex items-center justify-between">
          <div class="flex items-center gap-3">
            <img
              v-if="selectedMapStore.logo"
              :src="getLogoUrl(selectedMapStore.logo)"
              :alt="selectedMapStore.name"
              class="w-10 h-10 object-contain bg-white rounded-lg p-1"
            />
            <div>
              <h2 class="text-lg font-bold">{{ selectedMapStore.name }}</h2>
              <p class="text-sm text-purple-100">Lokacije u {{ selectedMapStore.city || 'BiH' }}</p>
            </div>
          </div>
          <button
            @click="closeMapPopup"
            class="text-white/80 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Map Content -->
        <div class="relative" style="height: 60vh;">
          <iframe
            v-if="mapEmbedUrl"
            :src="mapEmbedUrl"
            width="100%"
            height="100%"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>
          <div v-else class="w-full h-full flex items-center justify-center bg-gray-100">
            <div class="text-center text-gray-500">
              <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              <p>Mapa nije dostupna</p>
            </div>
          </div>
        </div>

        <!-- Map Footer -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
          <a
            v-if="selectedMapStore.google_link"
            :href="selectedMapStore.google_link"
            target="_blank"
            class="text-purple-600 hover:text-purple-800 text-sm font-medium inline-flex items-center gap-2"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            Otvori u Google Maps
          </a>
          <button
            @click="closeMapPopup"
            class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium rounded-lg transition-colors"
          >
            Zatvori
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
interface NewStore {
  id: number
  name: string
  logo?: string
  city?: string
  google_link?: string
}

const props = defineProps<{
  modelValue: boolean
  newStores: NewStore[]
  latestStoreId: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'stores-selected': [storeIds: number[]]
  'dismissed': []
}>()

const { isAuthenticated } = useAuth()
const { put } = useApi()
const config = useRuntimeConfig()

const selectedStoreIds = ref<number[]>([])
const isSaving = ref(false)

// Map popup state
const showMapPopup = ref(false)
const selectedMapStore = ref<NewStore | null>(null)

function getLogoUrl(logoPath: string): string {
  if (!logoPath) return ''
  if (logoPath.startsWith('http')) return logoPath
  return `${config.public.apiBase}${logoPath}`
}

// Convert Google Maps URL to embeddable URL
const mapEmbedUrl = computed(() => {
  if (!selectedMapStore.value?.google_link) return null
  return getMapEmbedUrl(selectedMapStore.value.google_link)
})

function getMapEmbedUrl(url: string): string | null {
  if (!url) return null

  try {
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

      // Format with coordinates
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

function openMapPopup(store: NewStore) {
  selectedMapStore.value = store
  showMapPopup.value = true
}

function closeMapPopup() {
  showMapPopup.value = false
  selectedMapStore.value = null
}

const isVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Pre-select all stores by default
watch(() => props.newStores, (stores) => {
  if (stores.length > 0) {
    selectedStoreIds.value = stores.map(s => s.id)
  }
}, { immediate: true })

async function confirmSelection() {
  isSaving.value = true

  try {
    if (isAuthenticated.value) {
      await put('/auth/user/store-preferences', {
        last_seen_store_id: props.latestStoreId
      })
    } else {
      localStorage.setItem('last_seen_store_id', props.latestStoreId.toString())
    }

    emit('stores-selected', selectedStoreIds.value)
    isVisible.value = false
  } catch (error) {
    console.error('Failed to save store preferences:', error)
  } finally {
    isSaving.value = false
  }
}

async function skipAll() {
  isSaving.value = true

  try {
    if (isAuthenticated.value) {
      await put('/auth/user/store-preferences', {
        last_seen_store_id: props.latestStoreId
      })
    } else {
      localStorage.setItem('last_seen_store_id', props.latestStoreId.toString())
    }

    emit('dismissed')
    isVisible.value = false
  } catch (error) {
    console.error('Failed to update last seen store:', error)
  } finally {
    isSaving.value = false
  }
}
</script>
