<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4"
      @click.self="close"
    >
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-5 rounded-t-2xl">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold">Dobrodošli na Popust.ba!</h2>
              <p class="text-purple-200 text-sm mt-1">Evo kako da uštedite</p>
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
        <div class="p-5 space-y-4">
          <!-- Step 1: Search -->
          <div class="flex gap-4 items-start p-4 bg-blue-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center flex-shrink-0">
              <!-- Search icon -->
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Pretražite pametno</h3>
              <p class="text-sm text-gray-600 mt-1">
                Na početnoj stranici koristite <strong>pametnu pretragu</strong> za brzo pronalaženje proizvoda po najnižim cijenama.
              </p>
            </div>
          </div>

          <!-- Step 2: Proizvodi -->
          <div class="flex gap-4 items-start p-4 bg-green-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-green-500 text-white flex items-center justify-center flex-shrink-0">
              <!-- Grid/Products icon -->
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Istražujte Proizvode</h3>
              <p class="text-sm text-gray-600 mt-1">
                Posjetite stranicu <strong>Proizvodi</strong> za istraživanje svih akcija i popusta. Filtrirajte po kategorijama i trgovinama.
              </p>
            </div>
          </div>

          <!-- Step 3: Favorites -->
          <div class="flex gap-4 items-start p-4 bg-red-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-red-500 text-white flex items-center justify-center flex-shrink-0">
              <!-- Heart icon -->
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Sačuvajte favorite</h3>
              <p class="text-sm text-gray-600 mt-1">
                Kliknite na <span class="text-red-500 font-medium">❤️ srce</span> da sačuvate omiljene proizvode i pratite njihove cijene.
              </p>
            </div>
          </div>

          <!-- Step 4: Earn Credits -->
          <div class="flex gap-4 items-start p-4 bg-yellow-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-yellow-500 text-white flex items-center justify-center flex-shrink-0">
              <!-- Thumbs up icon -->
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M2 20h2c.55 0 1-.45 1-1v-9c0-.55-.45-1-1-1H2v11zm19.83-7.12c.11-.25.17-.52.17-.8V11c0-1.1-.9-2-2-2h-5.5l.92-4.65c.05-.22.02-.46-.08-.66-.23-.45-.52-.86-.88-1.22L14 2 7.59 8.41C7.21 8.79 7 9.3 7 9.83v7.84C7 18.95 8.05 20 9.34 20h8.11c.7 0 1.36-.37 1.72-.97l2.66-6.15z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Zaradite kredite</h3>
              <p class="text-sm text-gray-600 mt-1">
                Glasajte <span class="text-green-600 font-medium">👍 lajk</span> i <span class="text-blue-600 font-medium">💬 komentarišite</span> proizvode da zaradite dodatne kredite za pretraživanje.
              </p>
            </div>
          </div>

          <!-- Step 5: Shopping List -->
          <div class="flex gap-4 items-start p-4 bg-purple-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-purple-500 text-white flex items-center justify-center flex-shrink-0">
              <!-- Shopping list icon -->
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Kreirajte listu za kupovinu</h3>
              <p class="text-sm text-gray-600 mt-1">
                Koristite dugme <span class="text-purple-600 font-medium">🛒 "Dodaj u listu"</span> da kreirate svoju listu za kupovinu i ne zaboravite ništa u prodavnici.
              </p>
            </div>
          </div>

          <!-- Credits Info -->
          <div class="mt-4 p-4 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-xl border border-purple-200">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span class="font-semibold text-purple-800">Imate 40 besplatnih kredita sedmično!</span>
            </div>
            <p class="text-sm text-purple-700">
              Krediti se koriste za pretraživanje. Zaradite više glasanjem i komentarisanjem.
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div class="sticky bottom-0 bg-gray-50 p-4 border-t border-gray-200 rounded-b-2xl">
          <button
            @click="getStarted"
            class="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg"
          >
            Počnimo!
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const { post } = useApi()

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits(['close', 'started'])

function close() {
  emit('close')
}

async function getStarted() {
  try {
    // Mark welcome guide as seen on backend
    await post('/auth/user/welcome-guide-seen', {})
  } catch (error) {
    console.error('Error marking welcome guide as seen:', error)
  }
  emit('started')
  close()
}
</script>
