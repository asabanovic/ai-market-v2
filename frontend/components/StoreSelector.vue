<template>
  <div class="store-selector">
    <!-- Toggle Button -->
    <button
      @click="!disabled && (isOpen = !isOpen)"
      :disabled="disabled"
      :class="[
        'flex items-center gap-2 px-3 py-2 text-sm font-medium bg-white border rounded-lg transition-colors',
        disabled
          ? 'text-gray-400 border-gray-200 cursor-not-allowed'
          : 'text-gray-700 border-gray-300 hover:bg-gray-50'
      ]"
    >
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9,22 9,12 15,12 15,22" />
      </svg>
      <span>Prodavnice</span>
      <span v-if="selectedCount > 0" class="bg-purple-600 text-white text-xs px-1.5 py-0.5 rounded-full">
        {{ selectedCount }}
      </span>
      <svg
        :class="['w-4 h-4 transition-transform', isOpen ? 'rotate-180' : '']"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Dropdown -->
    <div
      v-if="isOpen"
      class="absolute z-50 mt-2 w-72 max-h-80 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg"
    >
      <!-- Header -->
      <div class="sticky top-0 bg-white border-b border-gray-200 px-3 py-2">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700">Filtriraj po prodavnicama</span>
          <button
            v-if="selectedCount > 0"
            @click="clearAll"
            class="text-xs text-purple-600 hover:text-purple-700"
          >
            Poništi sve
          </button>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          {{ selectedCount === 0 ? 'Sve prodavnice' : `${selectedCount} odabrano` }}
        </p>
      </div>

      <!-- Store List -->
      <div class="p-2">
        <label
          v-for="store in stores"
          :key="store.id"
          class="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-50 cursor-pointer"
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
          <div v-else class="w-6 h-6 bg-gray-200 rounded flex items-center justify-center">
            <svg class="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            </svg>
          </div>
          <span class="text-sm text-gray-700 flex-1">{{ store.name }}</span>
        </label>

        <div v-if="stores.length === 0" class="text-center py-4 text-sm text-gray-500">
          Učitavanje prodavnica...
        </div>
      </div>

      <!-- Footer with Save Button (for logged in users) -->
      <div v-if="isAuthenticated" class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-3 py-2">
        <button
          @click="savePreferences"
          :disabled="isSaving"
          class="w-full text-sm text-purple-600 hover:text-purple-700 font-medium"
        >
          {{ isSaving ? 'Čuvanje...' : 'Sačuvaj kao default' }}
        </button>
      </div>
    </div>

    <!-- Backdrop -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40"
      @click="isOpen = false"
    ></div>
  </div>
</template>

<script setup lang="ts">
interface Store {
  id: number
  name: string
  logo?: string
  city?: string
}

const props = defineProps<{
  modelValue: number[]
  stores: Store[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
}>()

const { isAuthenticated } = useAuth()
const { put } = useApi()

const isOpen = ref(false)
const isSaving = ref(false)

const selectedStores = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const selectedCount = computed(() => selectedStores.value.length)

function toggleStore(storeId: number) {
  const current = [...selectedStores.value]
  const index = current.indexOf(storeId)

  if (index > -1) {
    current.splice(index, 1)
  } else {
    current.push(storeId)
  }

  selectedStores.value = current
}

function clearAll() {
  selectedStores.value = []
}

async function savePreferences() {
  if (!isAuthenticated.value) return

  isSaving.value = true
  try {
    await put('/auth/user/store-preferences', {
      preferred_stores: selectedStores.value
    })
  } catch (error) {
    console.error('Failed to save store preferences:', error)
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.store-selector {
  position: relative;
}
</style>
