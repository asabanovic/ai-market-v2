<template>
  <Teleport to="body">
    <div
      v-if="isVisible"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
    >
      <div class="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 text-white">
          <div class="flex items-center gap-3">
            <div class="bg-white/20 rounded-full p-2">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-bold">Odaberite vaš grad</h2>
              <p class="text-sm text-purple-100">Za personalizirane rezultate pretrage</p>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="px-6 py-6">
          <p class="text-gray-600 mb-4">
            Molimo vas da odaberete grad u kojem živite. Ovo će nam pomoći da vam prikažemo relevantne prodavnice i lokacije u vašoj blizini.
          </p>

          <div class="mb-4">
            <label for="city-select" class="block text-sm font-medium text-gray-700 mb-2">
              Grad *
            </label>
            <select
              id="city-select"
              v-model="selectedCity"
              class="w-full px-3 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            >
              <option value="">Odaberite grad...</option>
              <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
            </select>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
            <div class="flex items-start gap-2">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
              </svg>
              <span>
                Nakon odabira grada, automatski ćemo prilagoditi rezultate pretrage i prikazati vam lokacije prodavnica u vašoj blizini.
              </span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            @click="saveCity"
            :disabled="!selectedCity || isSaving"
            class="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isSaving ? 'Čuvanje...' : 'Sačuvaj i nastavi' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'city-saved': [city: string]
}>()

const { user } = useAuth()
const { get, post } = useApi()

const cities = ref<string[]>([])
const selectedCity = ref('')
const isSaving = ref(false)

const isVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

onMounted(async () => {
  await loadCities()
})

async function loadCities() {
  try {
    const data = await get('/auth/cities')
    cities.value = data.cities || []
  } catch (error) {
    console.error('Error loading cities:', error)
  }
}

async function saveCity() {
  if (!selectedCity.value) return

  isSaving.value = true
  try {
    const response = await post('/api/profile', {
      city: selectedCity.value
    })

    if (response.success) {
      // Update user object
      if (user.value) {
        user.value.city = selectedCity.value
      }

      emit('city-saved', selectedCity.value)
      isVisible.value = false
    }
  } catch (error) {
    console.error('Error saving city:', error)
  } finally {
    isSaving.value = false
  }
}
</script>
