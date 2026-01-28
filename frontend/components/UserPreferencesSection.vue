<template>
  <div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Moje preference</h2>
        <p class="text-sm text-gray-600 mt-1">Proizvodi koje pratimo za Vas</p>
      </div>
      <button
        @click="$emit('edit')"
        class="text-purple-600 hover:text-purple-700 text-sm font-medium"
      >
        Uredi
      </button>
    </div>

    <div v-if="loading" class="text-center py-4">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600 mx-auto"></div>
    </div>

    <div v-else-if="preferences.length > 0" class="flex flex-wrap gap-2">
      <span
        v-for="(pref, index) in preferences"
        :key="index"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-full text-sm font-medium"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        {{ pref }}
        <button
          v-if="allowRemove"
          @click="removePreference(pref)"
          class="ml-1 text-purple-500 hover:text-purple-700"
          :disabled="removing === pref"
        >
          <svg v-if="removing !== pref" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <div v-else class="w-4 h-4 animate-spin rounded-full border-2 border-purple-500 border-t-transparent"></div>
        </button>
      </span>
    </div>

    <div v-else class="text-center py-4 text-gray-500">
      <p class="text-sm">Nemate praćenih proizvoda</p>
      <p class="text-xs mt-1">Slikajte proizvode ili dodajte ih ručno</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  allowRemove?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit'): void
  (e: 'preference-removed', deleted_count: number): void
}>()

const { get, put } = useApi()

const loading = ref(true)
const preferences = ref<string[]>([])
const removing = ref<string | null>(null)

async function loadPreferences() {
  loading.value = true
  try {
    const data = await get('/auth/user/profile')
    preferences.value = data.preferences?.grocery_interests || []
  } catch (error) {
    console.error('Error loading preferences:', error)
  } finally {
    loading.value = false
  }
}

async function removePreference(pref: string) {
  if (removing.value) return
  removing.value = pref

  try {
    const updatedPreferences = preferences.value.filter(p => p !== pref)
    const response = await put('/auth/user/interests', {
      grocery_interests: updatedPreferences
    })
    preferences.value = updatedPreferences

    // Emit event so parent can refresh tracked products
    const deletedCount = response?.deleted_tracked_count || 0
    if (deletedCount > 0) {
      emit('preference-removed', deletedCount)
    }
  } catch (error) {
    console.error('Error removing preference:', error)
  } finally {
    removing.value = null
  }
}

onMounted(() => {
  loadPreferences()
})
</script>
