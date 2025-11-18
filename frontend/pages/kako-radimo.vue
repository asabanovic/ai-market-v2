<template>
  <div class="bg-gray-50 py-16">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center mb-16">
        <h1 class="text-4xl font-bold text-gray-900 mb-6">Kako radimo</h1>
        <p class="text-xl text-gray-600 max-w-3xl mx-auto">
          Naša platforma povezuje kupce sa lokalnim radnjama i njihovim aktuelnim popustima.
          Uz pomoć AI asistenta, pronalaženje najboljih akcija nikada nije bilo lakše.
        </p>
      </div>

      <!-- How Users Search -->
      <div class="mb-20">
        <h2 class="text-3xl font-bold text-gray-900 text-center mb-12">Za kupce</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="bg-indigo-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">1. Pitajte AI asistenta</h3>
            <p class="text-gray-600">
              Jednostavno ukucajte šta tražite, npr. "Gdje kupiti junetinu ispod 20 KM u Tuzli?"
              ili "Trebam nove gume za auto". Naš AI će razumjeti vaš upit.
            </p>
          </div>

          <div class="text-center">
            <div class="bg-indigo-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">2. Dobijte personalizirane rezultate</h3>
            <p class="text-gray-600">
              AI analizira vaš zahtev i pronalazi najbolje trenutne ponude iz naše baze podataka.
              Rezultati su prilagođeni vašem gradu i preferencijama.
            </p>
          </div>

          <div class="text-center">
            <div class="bg-indigo-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 7H19M7 13L5.4 5M7 13l-2.293 2.293a1 1 0 001.414 1.414L9 14h6m0 0v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6m8 0V9a2 2 0 00-2-2H9a2 2 0 00-2 2v5z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">3. Kupujte pametno</h3>
            <p class="text-gray-600">
              Dobijate kompletne informacije - cijene, popuste, lokacije radnji, kontakte i datume isteka akcija.
              Sve što trebate da uštedite novac.
            </p>
          </div>
        </div>
      </div>

      <!-- Credits System -->
      <div class="bg-gradient-to-br from-green-50 to-blue-50 rounded-xl p-8 mb-20">
        <h2 class="text-3xl font-bold text-gray-900 text-center mb-8">Kako funkcionišu krediti</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">💝 Besplatne pretrage bez rezultata</h3>
            <p class="text-gray-600">
              Ako vaša pretraga ne vrati rezultate, častimo vas ovim kreditom! Krediti se troše samo kada pronađemo proizvode koji vas zanimaju.
            </p>
          </div>

          <div class="text-center">
            <div class="bg-blue-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Dnevni krediti</h3>
            <p class="text-gray-600">
              Neregistrovani korisnici imaju 3 kredita dnevno. Registrovani korisnici dobijaju 10 kredita i mogućnost nadogradnje paketa za više pretraga.
            </p>
          </div>

          <div class="text-center">
            <div class="bg-purple-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Pametan sistem</h3>
            <p class="text-gray-600">
              Sistem je dizajniran da bude fer - plaćate samo za uspješne pretrage koje vam stvarno pomažu da pronađete ono što tražite.
            </p>
          </div>
        </div>

        <div v-if="!isAuthenticated" class="text-center mt-8">
          <NuxtLink to="/registracija"
             class="bg-green-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-green-700 transition duration-200 inline-block">
            Registrujte se za više kredita
          </NuxtLink>
        </div>
      </div>

      <!-- How Businesses Add Products -->
      <div class="mb-20">
        <h2 class="text-3xl font-bold text-gray-900 text-center mb-12">Za radnje</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">1. Dodajte proizvode</h3>
            <p class="text-gray-600">
              Unosite proizvode kroz jednostavan obrazac, CSV fajl ili običan tekst.
              Naš AI će automatski organizovati informacije.
            </p>
          </div>

          <div class="text-center">
            <div class="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM9 17H4l5 5v-5zM21 7h-5V2l5 5zM3 7h5V2L3 7z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">2. Automatska kategorizacija</h3>
            <p class="text-gray-600">
              Sistem automatski kategoriše vaše proizvode i priprema ih za pretraživanje.
              Kupci će lakše pronaći ono što traže.
            </p>
          </div>

          <div class="text-center">
            <div class="bg-green-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">3. Povećajte prodaju</h3>
            <p class="text-gray-600">
              Vaši proizvodi postaju vidljivi kupcima koji aktivno traže baš ono što nudite.
              Pratite statistike i optimizujte ponudu.
            </p>
          </div>
        </div>
      </div>

      <!-- Why Register -->
      <div class="bg-indigo-50 rounded-xl p-8 mb-20">
        <h2 class="text-3xl font-bold text-gray-900 text-center mb-8">Zašto se registrovati?</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="flex items-start">
            <div class="bg-indigo-100 w-12 h-12 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 mb-2">Brži pronalazak</h3>
              <p class="text-gray-600">Napredna pretraga koja razumije šta tražite i pronalazi najbolje ponude</p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="bg-indigo-100 w-12 h-12 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 mb-2">Ekskluzivni popusti</h3>
              <p class="text-gray-600">Pristup specijalnim akcijama dostupnim samo registrovanim korisnicima</p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="bg-indigo-100 w-12 h-12 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 mb-2">Brže pretraživanje</h3>
              <p class="text-gray-600">Sačuvane preferencije omogućavaju bržu i precizniju pretragu</p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="bg-indigo-100 w-12 h-12 rounded-lg flex items-center justify-center mr-4 flex-shrink-0">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 mb-2">Praćenje historije</h3>
              <p class="text-gray-600">Vodite evidenciju o svojim pretragama i omiljenim proizvodima</p>
            </div>
          </div>
        </div>

        <div v-if="!isAuthenticated" class="text-center mt-8">
          <NuxtLink to="/registracija"
             class="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 transition duration-200 inline-block">
            Registrujte se besplatno
          </NuxtLink>
        </div>
      </div>

      <!-- Technology -->
      <div class="text-center">
        <h2 class="text-3xl font-bold text-gray-900 mb-8">Napredna AI tehnologija</h2>
        <p class="text-lg text-gray-600 max-w-4xl mx-auto mb-8">
          Koristimo najnovije AI modele za razumijevanje prirodnog jezika i inteligentno povezivanje
          kupaca sa proizvodima. Naš sistem kontinuirano uči i poboljšava se kako bi vam pružio
          što bolje rezultate.
        </p>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
          <div>
            <div class="text-2xl font-bold text-indigo-600 mb-2">AI</div>
            <p class="text-sm text-gray-600">Pametan pretraživač</p>
          </div>
          <div>
            <div class="text-2xl font-bold text-indigo-600 mb-2">24/7</div>
            <p class="text-sm text-gray-600">Dostupnost</p>
          </div>
          <div>
            <div class="text-2xl font-bold text-indigo-600 mb-2">U Realnom vremenu</div>
            <p class="text-sm text-gray-600">Ažurni podaci</p>
          </div>
          <div>
            <div class="text-2xl font-bold text-indigo-600 mb-2">Besplatno</div>
            <p class="text-sm text-gray-600">Besplatna usluga</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { isAuthenticated } = useAuth()

useSeoMeta({
  title: 'Kako radimo - AI Pijaca',
  description: 'Saznajte kako AI Pijaca koristi naprednu AI tehnologiju da poveže kupce sa najboljim lokalnim popustima i akcijama',
})
</script>
