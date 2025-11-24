<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto">
      <!-- Back button -->
      <NuxtLink to="/" class="inline-flex items-center text-purple-600 hover:text-purple-800 mb-8">
        <Icon name="mdi:arrow-left" class="w-5 h-5 mr-2" />
        Nazad na početnu
      </NuxtLink>

      <!-- Main content card -->
      <div class="bg-white rounded-2xl shadow-xl overflow-hidden">
        <!-- Header with gradient -->
        <div class="bg-gradient-to-r from-purple-600 to-purple-800 px-8 py-12 text-center">
          <div class="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto mb-6">
            <Icon name="mdi:rocket-launch" class="w-12 h-12 text-purple-600" />
          </div>
          <h1 class="text-4xl font-bold text-white mb-4">Dodatni Krediti - Uskoro!</h1>
          <p class="text-purple-100 text-lg">Radimo na uzbudljivom sistemu kredita koji će vam omogućiti još više pretraga</p>
        </div>

        <!-- Body -->
        <div class="px-8 py-10">
          <!-- Current status -->
          <div class="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-6 mb-8">
            <div class="flex items-start">
              <Icon name="mdi:information" class="w-6 h-6 text-blue-600 mt-1 mr-3 flex-shrink-0" />
              <div>
                <h3 class="font-semibold text-blue-900 mb-2">Trenutno stanje:</h3>
                <p class="text-blue-800">
                  Svi registrovani korisnici dobijaju <strong class="text-blue-900">10 BESPLATNIH kredita sedmično</strong>.
                  Svaki proizvod koji pretražite troši 1 kredit. Krediti se automatski obnavljaju svakog ponedjeljka!
                </p>
              </div>
            </div>
          </div>

          <!-- Coming soon features -->
          <h2 class="text-2xl font-bold text-gray-900 mb-6">Šta planiramo? 🎯</h2>

          <div class="space-y-4 mb-10">
            <div class="flex items-start space-x-4 p-4 bg-purple-50 rounded-lg">
              <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="mdi:gift" class="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 mb-1">Bonus Krediti za Aktivne Korisnike</h3>
                <p class="text-gray-600 text-sm">Podijelite ponude sa prijateljima i zaradite dodatne kredite!</p>
              </div>
            </div>

            <div class="flex items-start space-x-4 p-4 bg-green-50 rounded-lg">
              <div class="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="mdi:account-multiple" class="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 mb-1">Referal Program</h3>
                <p class="text-gray-600 text-sm">Pozovite prijatelje i dobijte bonus kredite za svakog novog korisnika!</p>
              </div>
            </div>

            <div class="flex items-start space-x-4 p-4 bg-yellow-50 rounded-lg">
              <div class="w-10 h-10 bg-yellow-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="mdi:star" class="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 mb-1">Premium Paketi</h3>
                <p class="text-gray-600 text-sm">Neograničene pretrage i ekskluzivne funkcije za najaktivnije korisnike</p>
              </div>
            </div>

            <div class="flex items-start space-x-4 p-4 bg-blue-50 rounded-lg">
              <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="mdi:trophy" class="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 mb-1">Nagrade za Uštede</h3>
                <p class="text-gray-600 text-sm">Što više uštedite koristeći naše ponude, više kredita zaradite!</p>
              </div>
            </div>
          </div>

          <!-- Interest gauge -->
          <div class="bg-gradient-to-r from-purple-100 to-blue-100 rounded-xl p-8 mb-8">
            <div class="text-center">
              <Icon name="mdi:chart-line" class="w-16 h-16 mx-auto mb-4 text-purple-600" />
              <h3 class="text-xl font-bold text-gray-900 mb-3">Hvala vam na interesovanju!</h3>
              <p class="text-gray-700 mb-4">
                Vaš klik nam je zabilježen i pomaže nam da prioritiziramo razvoj ove funkcije.
                Što više korisnika pokaže interesovanje, brže ćemo implementirati sistem dodatnih kredita!
              </p>
              <div class="inline-flex items-center space-x-2 bg-white px-6 py-3 rounded-full shadow-md">
                <Icon name="mdi:check-circle" class="w-6 h-6 text-green-500" />
                <span class="font-semibold text-gray-900">Vaš glas je zabilježen!</span>
              </div>
            </div>
          </div>

          <!-- Newsletter signup (future) -->
          <div class="bg-gray-50 rounded-xl p-6 text-center">
            <Icon name="mdi:email-newsletter" class="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 class="font-semibold text-gray-900 mb-2">Želite biti prvi koji saznaju?</h3>
            <p class="text-gray-600 mb-4 text-sm">
              Ne brinite! Svi registrovani korisnici će automatski biti obavješteni kada ova funkcija bude dostupna.
            </p>
            <div class="inline-flex items-center space-x-2 text-purple-600">
              <Icon name="mdi:bell-ring" class="w-5 h-5" />
              <span class="font-medium text-sm">Obavijestit ćemo vas putem email-a</span>
            </div>
          </div>
        </div>

        <!-- Footer CTA -->
        <div class="bg-gray-50 px-8 py-6 border-t border-gray-200">
          <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="text-center sm:text-left">
              <p class="text-sm text-gray-600">U međuvremenu, iskoristite vaših 10 sedmičnih kredita!</p>
            </div>
            <NuxtLink
              to="/"
              class="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 transition-colors inline-flex items-center space-x-2"
            >
              <Icon name="mdi:magnify" class="w-5 h-5" />
              <span>Pretražite proizvode</span>
            </NuxtLink>
          </div>
        </div>
      </div>

      <!-- FAQ Section -->
      <div class="mt-8 bg-white rounded-xl shadow-lg p-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Često Postavljana Pitanja</h2>

        <div class="space-y-6">
          <div>
            <h3 class="font-semibold text-gray-900 mb-2 flex items-center">
              <Icon name="mdi:help-circle" class="w-5 h-5 text-purple-600 mr-2" />
              Koliko kredita imam trenutno?
            </h3>
            <p class="text-gray-600 text-sm ml-7">
              Svi korisnici imaju 10 kredita sedmično. Možete vidjeti koliko vam je preostalo nakon svake pretrage, a krediti se obnavljaju svakog ponedjeljka.
            </p>
          </div>

          <div>
            <h3 class="font-semibold text-gray-900 mb-2 flex items-center">
              <Icon name="mdi:help-circle" class="w-5 h-5 text-purple-600 mr-2" />
              Kako se troše krediti?
            </h3>
            <p class="text-gray-600 text-sm ml-7">
              Svaki proizvod koji pretražite troši 1 kredit. Na primjer, ako pretražite "brasno, cokolada, mlijeko" (3 proizvoda), potroš ite 3 kredita.
            </p>
          </div>

          <div>
            <h3 class="font-semibold text-gray-900 mb-2 flex items-center">
              <Icon name="mdi:help-circle" class="w-5 h-5 text-purple-600 mr-2" />
              Kada se obnavljaju krediti?
            </h3>
            <p class="text-gray-600 text-sm ml-7">
              Krediti se automatski resetuju svakog dana u ponoć. Svi korisnici ponovo dobijaju punih 10 kredita.
            </p>
          </div>

          <div>
            <h3 class="font-semibold text-gray-900 mb-2 flex items-center">
              <Icon name="mdi:help-circle" class="w-5 h-5 text-purple-600 mr-2" />
              Kada će biti dostupni dodatni krediti?
            </h3>
            <p class="text-gray-600 text-sm ml-7">
              Radimo na tome! Hvala što ste pokazali interesovanje - to nam pomaže da prioritiziramo ovu funkciju. Obavijestit ćemo sve korisnike čim bude spremno.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
useSeoMeta({
  title: 'Dodatni Krediti - Uskoro! - Rabat.ba',
  description: 'Saznajte više o našem nadolazećem sistemu dodatnih kredita i kako možete dobiti više pretraga',
})

// Log interest in credits feature
onMounted(async () => {
  try {
    // This could be logged to analytics in the future
    console.log('User showed interest in additional credits feature')
  } catch (error) {
    console.error('Failed to log interest:', error)
  }
})
</script>
