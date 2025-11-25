<template>
  <Teleport to="body">
    <div
      v-if="isVisible && newStores.length > 0"
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
                :src="store.logo"
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
  </Teleport>
</template>

<script setup lang="ts">
interface NewStore {
  id: number
  name: string
  logo?: string
  city?: string
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

const selectedStoreIds = ref<number[]>([])
const isSaving = ref(false)

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
    // Update last seen store ID
    if (isAuthenticated.value) {
      await put('/auth/user/store-preferences', {
        last_seen_store_id: props.latestStoreId
      })
    } else {
      // For anonymous users, store in localStorage
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
    // Still update last seen ID to prevent showing again
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
