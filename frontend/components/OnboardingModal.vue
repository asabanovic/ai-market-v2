<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <div class="text-center mb-6">
        <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Icon name="mdi:bell-outline" class="w-8 h-8 text-purple-600" />
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Dobrodošli!</h2>
        <p class="text-gray-600 text-sm">
          Pomozite nam da vas obavijestimo kada vaši omiljeni proizvodi budu na akciji
        </p>
      </div>

      <form @submit.prevent="submitOnboarding">
        <!-- Phone Number -->
        <div class="mb-4">
          <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">
            Broj telefona (opciono)
          </label>
          <input
            v-model="form.phone"
            type="tel"
            id="phone"
            placeholder="+387 XX XXX XXX"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900"
          />
        </div>

        <!-- Typical Products -->
        <div class="mb-6">
          <label for="typical_products" class="block text-sm font-medium text-gray-700 mb-1">
            Lista proizvoda koje kupujete svaki mjesec
          </label>
          <textarea
            v-model="form.typical_products"
            id="typical_products"
            rows="3"
            placeholder="Npr: mlijeko, hljeb, jaja, kafa..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm text-gray-900"
          ></textarea>
          <p class="mt-1 text-xs text-gray-500">
            Pratit ćemo cijene ovih proizvoda i obavijestiti vas kada budu na popustu
          </p>
        </div>

        <!-- Error message -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p class="text-sm text-red-600">{{ error }}</p>
        </div>

        <!-- Buttons -->
        <div class="flex gap-3">
          <button
            type="button"
            @click="skipOnboarding"
            class="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Preskoči
          </button>
          <button
            type="submit"
            :disabled="isSubmitting"
            class="flex-1 px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            {{ isSubmitting ? 'Čuvam...' : 'Sačuvaj' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['close', 'complete'])

const { post } = useApi()

const form = ref({
  phone: '',
  typical_products: ''
})

const isSubmitting = ref(false)
const error = ref('')

async function submitOnboarding() {
  isSubmitting.value = true
  error.value = ''

  try {
    await post('/auth/user/onboarding', form.value)
    emit('complete')
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Došlo je do greške'
  } finally {
    isSubmitting.value = false
  }
}

async function skipOnboarding() {
  // Mark as completed without saving data
  try {
    await post('/auth/user/onboarding', {
      phone: '',
      typical_products: ''
    })
    emit('close')
  } catch (err) {
    // Just close on error
    emit('close')
  }
}
</script>
