<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
      @click.self="close"
    >
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 bg-gradient-to-r from-purple-600 to-purple-700 text-white p-5 rounded-t-2xl">
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
        </div>

        <!-- Content -->
        <div class="p-5 space-y-5">
          <!-- Rating -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Kako vam se sviđa aplikacija?
            </label>
            <div class="flex justify-center gap-2">
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
              Šta biste poboljšali u aplikaciji?
            </label>
            <textarea
              v-model="whatToImprove"
              rows="2"
              maxlength="500"
              class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white"
              placeholder="npr. Dodajte više prodavnica, brža pretraga..."
            />
          </div>

          <!-- Question 2 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Kako vam možemo biti od veće pomoći?
            </label>
            <textarea
              v-model="howToHelp"
              rows="2"
              maxlength="500"
              class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white"
              placeholder="npr. Obavještenja o popustima, praćenje cijena..."
            />
          </div>

          <!-- Question 3 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Šta bi vas natjeralo da koristite ovu aplikaciju svaki put kad kupujete?
            </label>
            <textarea
              v-model="whatWouldMakeYouUse"
              rows="2"
              maxlength="500"
              class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white"
              placeholder="npr. Lista za kupovinu, uporedba cijena..."
            />
          </div>

          <!-- Additional Comments -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Dodatni komentari (opciono)
            </label>
            <textarea
              v-model="comments"
              rows="2"
              maxlength="1000"
              class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none text-sm text-gray-900 bg-white"
              placeholder="Bilo šta drugo što želite podijeliti..."
            />
          </div>
        </div>

        <!-- Footer -->
        <div class="sticky bottom-0 bg-gray-50 p-4 border-t border-gray-200 rounded-b-2xl">
          <div class="flex gap-3">
            <button
              @click="close"
              class="flex-1 py-3 px-4 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Kasnije
            </button>
            <button
              @click="submit"
              :disabled="isSubmitting || !hasAnyInput"
              class="flex-1 py-3 px-4 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isSubmitting ? 'Šaljem...' : 'Pošalji' }}
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

const hasAnyInput = computed(() => {
  return rating.value > 0 ||
         whatToImprove.value.trim() ||
         howToHelp.value.trim() ||
         whatWouldMakeYouUse.value.trim() ||
         comments.value.trim()
})

function close() {
  emit('close')
}

async function submit() {
  if (!hasAnyInput.value || isSubmitting.value) return

  isSubmitting.value = true

  try {
    await post('/api/feedback', {
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
