<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
      @click.self="close"
    >
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 bg-gradient-to-r from-purple-600 to-purple-700 text-white p-5 rounded-t-2xl z-10">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold">Vaše mišljenje nam je važno!</h2>
              <p class="text-purple-200 text-sm mt-1">Pomozite nam da budemo bolji</p>
            </div>
            <button
              @click="close"
              class="text-white/80 hover:text-white p-1"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <!-- Credit Incentive Banner -->
          <div class="mt-3 bg-yellow-400 text-yellow-900 rounded-lg px-3 py-2 flex items-center gap-2 relative overflow-hidden">
            <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span class="text-sm font-medium flex-1">Kao zahvalu za Vaše vrijeme, poklanjamo Vam <strong>+5 kredita</strong></span>
            <!-- Decorative star on right - contained within banner -->
            <svg class="w-8 h-8 text-yellow-500/40 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </div>
        </div>

        <!-- Content -->
        <div class="p-5 space-y-5">
          <!-- Rating -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Kako vam se sviđa aplikacija? <span class="text-red-500">*</span>
            </label>
            <div class="flex justify-center gap-2 relative z-0">
              <button
                v-for="star in 5"
                :key="star"
                @click="rating = star"
                class="p-1 transition-transform hover:scale-110"
              >
                <svg
                  class="w-10 h-10"
                  :class="star <= rating ? 'text-yellow-400' : 'text-gray-300'"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Question 1 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Šta biste poboljšali u aplikaciji? <span class="text-red-500">*</span>
              <span class="text-xs text-gray-500 font-normal">(min. {{ MIN_CHARS_PER_FIELD }} znakova)</span>
            </label>
            <textarea
              v-model="whatToImprove"
              rows="3"
              maxlength="500"
              :class="[
                'w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white',
                whatToImprove.trim().length > 0 && whatToImprove.trim().length < MIN_CHARS_PER_FIELD ? 'border-red-300' : 'border-gray-300'
              ]"
              placeholder="Opišite šta bi trebalo biti bolje..."
            />
            <div v-if="whatToImprove.trim().length > 0 && whatToImprove.trim().length < MIN_CHARS_PER_FIELD" class="text-xs text-red-500 mt-1">
              Još {{ MIN_CHARS_PER_FIELD - whatToImprove.trim().length }} znakova
            </div>
          </div>

          <!-- Question 2 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Kako vam možemo biti od veće pomoći? <span class="text-red-500">*</span>
              <span class="text-xs text-gray-500 font-normal">(min. {{ MIN_CHARS_PER_FIELD }} znakova)</span>
            </label>
            <textarea
              v-model="howToHelp"
              rows="3"
              maxlength="500"
              :class="[
                'w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white',
                howToHelp.trim().length > 0 && howToHelp.trim().length < MIN_CHARS_PER_FIELD ? 'border-red-300' : 'border-gray-300'
              ]"
              placeholder="Šta bi vam olakšalo korištenje..."
            />
            <div v-if="howToHelp.trim().length > 0 && howToHelp.trim().length < MIN_CHARS_PER_FIELD" class="text-xs text-red-500 mt-1">
              Još {{ MIN_CHARS_PER_FIELD - howToHelp.trim().length }} znakova
            </div>
          </div>

          <!-- Question 3 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Šta bi vas potaklo da koristite ovu aplikaciju svaki put kad kupujete? <span class="text-red-500">*</span>
              <span class="text-xs text-gray-500 font-normal">(min. {{ MIN_CHARS_PER_FIELD }} znakova)</span>
            </label>
            <textarea
              v-model="whatWouldMakeYouUse"
              rows="3"
              maxlength="500"
              :class="[
                'w-full p-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white',
                whatWouldMakeYouUse.trim().length > 0 && whatWouldMakeYouUse.trim().length < MIN_CHARS_PER_FIELD ? 'border-red-300' : 'border-gray-300'
              ]"
              placeholder="Šta vam nedostaje da biste koristili aplikaciju redovno..."
            />
            <div v-if="whatWouldMakeYouUse.trim().length > 0 && whatWouldMakeYouUse.trim().length < MIN_CHARS_PER_FIELD" class="text-xs text-red-500 mt-1">
              Još {{ MIN_CHARS_PER_FIELD - whatWouldMakeYouUse.trim().length }} znakova
            </div>
          </div>

          <!-- Additional Comments -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Dodatni komentari (opciono)
            </label>
            <textarea
              v-model="comments"
              rows="3"
              maxlength="1000"
              class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white"
              placeholder="Bilo šta dodatno što želite podijeliti s nama..."
            />
          </div>
        </div>

        <!-- Footer -->
        <div class="sticky bottom-0 bg-gray-50 p-4 border-t border-gray-200 rounded-b-2xl">
          <!-- Progress indicator -->
          <div v-if="!canSubmit" class="mb-3 text-center">
            <div class="text-sm text-gray-600">
              Popunite sva obavezna polja <span class="font-bold text-purple-600">({{ completedFieldsCount }}/4)</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div
                class="bg-purple-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: (completedFieldsCount / 4) * 100 + '%' }"
              />
            </div>
          </div>
          <div v-else class="mb-3 text-center">
            <div class="text-sm text-green-600 font-medium flex items-center justify-center gap-1">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              Spremno za slanje - dobićete +5 kredita!
            </div>
          </div>

          <div class="flex gap-3">
            <button
              @click="close"
              class="flex-1 py-3 px-4 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Kasnije
            </button>
            <button
              @click="submit"
              :disabled="isSubmitting || !canSubmit"
              class="flex-1 py-3 px-4 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isSubmitting ? 'Šaljem...' : 'Pošalji (+5 kredita)' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const { post } = useApi()

const props = defineProps<{
  show: boolean
  triggerType?: string
}>()

const emit = defineEmits(['close', 'submitted'])

const rating = ref(0)
const whatToImprove = ref('')
const howToHelp = ref('')
const whatWouldMakeYouUse = ref('')
const comments = ref('')
const isSubmitting = ref(false)

// Minimum characters required per field
const MIN_CHARS_PER_FIELD = 15

// All 3 required fields must meet the minimum
const canSubmit = computed(() => {
  return rating.value > 0 &&
         whatToImprove.value.trim().length >= MIN_CHARS_PER_FIELD &&
         howToHelp.value.trim().length >= MIN_CHARS_PER_FIELD &&
         whatWouldMakeYouUse.value.trim().length >= MIN_CHARS_PER_FIELD
})

// Count how many fields are complete
const completedFieldsCount = computed(() => {
  let count = 0
  if (rating.value > 0) count++
  if (whatToImprove.value.trim().length >= MIN_CHARS_PER_FIELD) count++
  if (howToHelp.value.trim().length >= MIN_CHARS_PER_FIELD) count++
  if (whatWouldMakeYouUse.value.trim().length >= MIN_CHARS_PER_FIELD) count++
  return count
})

function close() {
  emit('close')
}

async function submit() {
  if (!canSubmit.value || isSubmitting.value) return

  isSubmitting.value = true
  const { showSuccess } = useCreditsToast()

  try {
    const response = await post('/api/feedback', {
      rating: rating.value || null,
      what_to_improve: whatToImprove.value.trim() || null,
      how_to_help: howToHelp.value.trim() || null,
      what_would_make_you_use: whatWouldMakeYouUse.value.trim() || null,
      comments: comments.value.trim() || null,
      trigger_type: props.triggerType || 'manual',
      page_url: window.location.href
    })

    emit('submitted')
    close()

    // Show success message with credit bonus info
    if (response.credits_awarded) {
      showSuccess('Hvala na povratnim informacijama! Dobili ste +5 kredita!', 'Bonus krediti!')
    } else {
      showSuccess('Hvala na povratnim informacijama!')
    }

    // Reset form
    rating.value = 0
    whatToImprove.value = ''
    howToHelp.value = ''
    whatWouldMakeYouUse.value = ''
    comments.value = ''
  } catch (error) {
    console.error('Error submitting feedback:', error)
  } finally {
    isSubmitting.value = false
  }
}
</script>
