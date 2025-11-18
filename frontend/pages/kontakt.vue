<template>
  <div class="bg-gray-50 py-16">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <h1 class="text-4xl font-bold text-gray-900 mb-4">Kontaktirajte nas</h1>
        <p class="text-lg text-gray-600">Imate pitanje ili predlog? Radujemo se vašoj poruci!</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-8">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label for="name" class="block text-sm font-medium text-gray-700 mb-2">Ime i prezime</label>
              <input
                type="text"
                id="name"
                v-model="formData.name"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Vaše ime i prezime"
              />
            </div>

            <div>
              <label for="email" class="block text-sm font-medium text-gray-700 mb-2">Email adresa</label>
              <input
                type="email"
                id="email"
                v-model="formData.email"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="email@example.com"
              />
            </div>
          </div>

          <div>
            <label for="message" class="block text-sm font-medium text-gray-700 mb-2">Poruka</label>
            <textarea
              id="message"
              v-model="formData.message"
              rows="6"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Unesite vašu poruku..."
            ></textarea>
          </div>

          <div>
            <button
              type="submit"
              :disabled="isSubmitting"
              class="w-full bg-indigo-600 text-white py-3 px-6 rounded-md font-medium hover:bg-indigo-700 transition duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="isSubmitting" class="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
              {{ isSubmitting ? 'Šalje se...' : 'Pošaljite poruku' }}
            </button>
          </div>
        </form>

        <!-- Success message -->
        <div v-if="showSuccess" class="mt-6 p-4 bg-green-100 text-green-800 rounded-md">
          <p class="font-medium">Hvala vam!</p>
          <p>Vaša poruka je uspješno poslana. Javićemo vam se uskoro.</p>
        </div>

        <!-- Error message -->
        <div v-if="showError" class="mt-6 p-4 bg-red-100 text-red-800 rounded-md">
          <p class="font-medium">Greška!</p>
          <p>{{ errorMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { post } = useApi()

const formData = ref({
  name: '',
  email: '',
  message: ''
})

const isSubmitting = ref(false)
const showSuccess = ref(false)
const showError = ref(false)
const errorMessage = ref('Došlo je do greške prilikom slanja poruke. Molim vas pokušajte ponovo.')

async function handleSubmit() {
  isSubmitting.value = true
  showSuccess.value = false
  showError.value = false

  try {
    const response = await post('/api/contact', formData.value)

    if (response.success) {
      showSuccess.value = true
      formData.value = {
        name: '',
        email: '',
        message: ''
      }
    } else {
      errorMessage.value = response.error || 'Došlo je do greške prilikom slanja poruke.'
      showError.value = true
    }
  } catch (error: any) {
    console.error('Error submitting contact form:', error)
    errorMessage.value = error.message || 'Došlo je do greške prilikom slanja poruke. Molim vas pokušajte ponovo.'
    showError.value = true
  } finally {
    isSubmitting.value = false
  }
}

useSeoMeta({
  title: 'Kontakt - AI Pijaca',
  description: 'Imate pitanje ili predlog? Kontaktirajte AI Pijaca tim. Radujemo se vašoj poruci!',
})
</script>
