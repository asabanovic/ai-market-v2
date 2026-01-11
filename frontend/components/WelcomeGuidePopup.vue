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
              <h2 class="text-xl font-bold">Dobro nam došli!</h2>
              <p class="text-purple-200 text-sm mt-1">Kratki vodič kroz Popust.ba</p>
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
          <!-- Intro text -->
          <p class="text-gray-600 text-sm">
            Napravili smo Popust.ba da Vam olakšamo kupovinu. Evo kako da izvučete maksimum:
          </p>

          <!-- Step 1: Moji Proizvodi -->
          <div class="flex gap-4 items-start p-4 bg-purple-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-purple-500 text-white flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Moji Proizvodi</h3>
              <p class="text-sm text-gray-600 mt-1">
                Ovdje pratimo cijene proizvoda koje ste odabrali. Svratite svaki dan — ako nešto padne na akciju, vidjet ćete odmah.
              </p>
            </div>
          </div>

          <!-- Step 2: Pretraga -->
          <div class="flex gap-4 items-start p-4 bg-blue-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Pretraga</h3>
              <p class="text-sm text-gray-600 mt-1">
                Tražite nešto konkretno? Upišite na početnoj stranici i uporedite cijene u svim trgovinama. Pretražujte koliko god želite.
              </p>
            </div>
          </div>

          <!-- Step 3: Proizvodi -->
          <div class="flex gap-4 items-start p-4 bg-green-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-green-500 text-white flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Svi proizvodi</h3>
              <p class="text-sm text-gray-600 mt-1">
                Nemate ideju šta kupiti? Pregledajte sve akcije na stranici "Proizvodi" — možda Vam nešto zapadne za oko.
              </p>
            </div>
          </div>

          <!-- Step 4: Lista za kupovinu -->
          <div class="flex gap-4 items-start p-4 bg-orange-50 rounded-xl">
            <div class="w-10 h-10 rounded-full bg-orange-500 text-white flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900">Korpa za poređenje cijena</h3>
              <p class="text-sm text-gray-600 mt-1">
                Dodajte proizvode u korpu klikom na "Dodaj u korpu". Tako ćete vidjeti u kojem marketu možete sve kupiti najpovoljnije.
              </p>
            </div>
          </div>

          <!-- Tip box -->
          <div class="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
            <p class="text-sm text-gray-600">
              <span class="font-medium text-gray-800">Mali savjet:</span> Dodajte proizvode koje često kupujete u "Moji Proizvodi". Mi ćemo ih pratiti i obavijestiti Vas kad budu na akciji.
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div class="sticky bottom-0 bg-gray-50 p-4 border-t border-gray-200 rounded-b-2xl">
          <button
            @click="getStarted"
            class="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg"
          >
            Razumijem, idemo!
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
