<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
      <!-- Step 1: Store Selection -->
      <div v-if="step === 1">
        <div class="text-center mb-6">
          <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Icon name="mdi:store" class="w-8 h-8 text-purple-600" />
          </div>
          <h2 class="text-2xl font-bold text-gray-900 mb-2">Dobrodošli!</h2>
          <p class="text-gray-600 text-sm">
            Odaberite prodavnice u vašem gradu da bismo vam prikazali relevantne popuste
          </p>
        </div>

        <!-- Store Selection -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-3">
            Odaberite prodavnice koje posjećujete <span class="text-red-500">*</span>
          </label>

          <div v-if="isLoadingStores" class="text-center py-8">
            <Icon name="mdi:loading" class="w-8 h-8 animate-spin text-purple-600 mx-auto" />
            <p class="text-gray-600 mt-2 text-sm">Učitavanje prodavnica...</p>
          </div>

          <div v-else class="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
            <label
              v-for="store in stores"
              :key="store.id"
              class="flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all"
              :class="selectedStores.includes(store.id) ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <input
                type="checkbox"
                :checked="selectedStores.includes(store.id)"
                @change="toggleStore(store.id)"
                class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
              />
              <img
                v-if="store.logo"
                :src="store.logo"
                :alt="store.name"
                class="w-6 h-6 object-contain"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <span class="text-sm text-gray-700 truncate">{{ store.name }}</span>
            </label>
          </div>

          <p v-if="storeError" class="mt-2 text-xs text-red-500">{{ storeError }}</p>
          <p v-else class="mt-2 text-xs text-gray-500">
            Odabrano: {{ selectedStores.length }} {{ selectedStores.length === 1 ? 'prodavnica' : 'prodavnice' }}
          </p>
        </div>

        <!-- Quick select all button -->
        <div class="flex gap-2 mb-4">
          <button
            type="button"
            @click="selectAllStores"
            class="flex-1 px-3 py-2 text-xs font-medium text-purple-600 bg-purple-50 rounded-md hover:bg-purple-100 transition-colors"
          >
            Odaberi sve
          </button>
          <button
            type="button"
            @click="clearAllStores"
            class="flex-1 px-3 py-2 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Poništi izbor
          </button>
        </div>

        <button
          @click="goToStep2"
          :disabled="selectedStores.length === 0"
          class="w-full px-4 py-3 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Nastavi
        </button>
      </div>

      <!-- Step 2: Preferences (using unified component) -->
      <div v-else-if="step === 2">
        <PreferencesForm
          :show-skip-button="true"
          :show-back-button="true"
          source="onboarding"
          @complete="handlePreferencesComplete"
          @skip="skipOnboarding"
          @back="step = 1"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Store {
  id: number
  name: string
  logo?: string
}

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['close', 'complete', 'storesSelected'])

const { post, get, put } = useApi()
const config = useRuntimeConfig()

const step = ref(1)
const storeError = ref('')

// Store selection state
const stores = ref<Store[]>([])
const selectedStores = ref<number[]>([])
const isLoadingStores = ref(false)

// Load stores when modal opens
watch(() => props.show, async (show) => {
  if (show && stores.value.length === 0) {
    await loadStores()
  }
}, { immediate: true })

async function loadStores() {
  isLoadingStores.value = true
  try {
    const response = await get('/api/businesses?all=true')
    stores.value = (response.businesses || []).map((b: any) => ({
      id: b.id,
      name: b.name,
      logo: b.logo_path ? (b.logo_path.startsWith('http') ? b.logo_path : `${config.public.apiBase}/static/${b.logo_path}`) : null
    }))

    // If no stores available, skip onboarding entirely
    if (stores.value.length === 0) {
      await skipOnboardingQuietly()
    }
  } catch (error) {
    console.error('Error loading stores:', error)
    // On error, also skip onboarding to avoid blocking user
    await skipOnboardingQuietly()
  } finally {
    isLoadingStores.value = false
  }
}

async function skipOnboardingQuietly() {
  try {
    await post('/auth/user/onboarding', {
      phone: '',
      typical_products: ''
    })
  } catch (err) {
    // Ignore errors
  }
  emit('complete')
}

function toggleStore(storeId: number) {
  const index = selectedStores.value.indexOf(storeId)
  if (index > -1) {
    selectedStores.value.splice(index, 1)
  } else {
    selectedStores.value.push(storeId)
  }
  storeError.value = ''
}

function selectAllStores() {
  selectedStores.value = stores.value.map(s => s.id)
  storeError.value = ''
}

function clearAllStores() {
  selectedStores.value = []
}

async function goToStep2() {
  if (selectedStores.value.length === 0) {
    storeError.value = 'Molimo odaberite barem jednu prodavnicu'
    return
  }

  // Save store preferences immediately
  try {
    await put('/auth/user/store-preferences', {
      preferred_stores: selectedStores.value
    })
    // Emit event to update parent component
    emit('storesSelected', selectedStores.value)
  } catch (error) {
    console.error('Error saving store preferences:', error)
  }

  step.value = 2
}

function handlePreferencesComplete() {
  emit('complete')
}

async function skipOnboarding() {
  // Mark as completed without saving additional data
  // Store preferences were already saved in step 1
  try {
    await post('/auth/user/onboarding', {
      phone: '',
      typical_products: ''
    })
    emit('complete')
  } catch (err) {
    // Still complete on error since stores were saved
    emit('complete')
  }
}
</script>
