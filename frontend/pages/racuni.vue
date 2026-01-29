<template>
  <div class="bg-gray-50 min-h-screen py-6 pb-24">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-4">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          Moji računi
        </h1>
        <p class="text-gray-600 text-sm">
          Skenirajte račune i pratite potrošnju
        </p>
      </div>

      <!-- Tips Banner - Collapsible -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl mb-6 overflow-hidden">
        <button
          @click="showTips = !showTips"
          class="w-full p-4 flex items-center justify-between text-left"
        >
          <div class="flex items-center gap-3">
            <div class="text-2xl">💡</div>
            <div>
              <p class="text-blue-900 font-medium">
                Savjeti za skeniranje računa
              </p>
              <p class="text-blue-700 text-sm">
                Kako najbolje fotografisati račune za precizno očitavanje
              </p>
            </div>
          </div>
          <svg
            class="w-5 h-5 text-blue-600 transition-transform duration-200"
            :class="{ 'rotate-180': showTips }"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <Transition name="collapse">
          <div v-show="showTips" class="px-4 pb-4 border-t border-blue-200">
            <div class="grid md:grid-cols-2 gap-4 pt-4">
              <!-- Tip 1: Short receipts -->
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-gray-900 text-sm">Kratki računi</p>
                  <p class="text-gray-600 text-xs">Slikajte cijeli račun odjednom, od vrha do dna.</p>
                </div>
              </div>

              <!-- Tip 2: Long receipts -->
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-gray-900 text-sm">Dugački računi</p>
                  <p class="text-gray-600 text-xs">Možete slikati u dijelovima - svaki dio se zasebno očita i artikli se sakupe.</p>
                </div>
              </div>

              <!-- Tip 3: Focus on items -->
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-gray-900 text-sm">Fokusirajte se na artikle</p>
                  <p class="text-gray-600 text-xs">Najvažnije je da se vide nazivi proizvoda i cijene. Ukupan iznos se računa automatski.</p>
                </div>
              </div>

              <!-- Tip 4: Good lighting -->
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-gray-900 text-sm">Dobro osvjetljenje</p>
                  <p class="text-gray-600 text-xs">Fotografišite na ravnoj podlozi sa dobrim osvjetljenjem, bez sjena.</p>
                </div>
              </div>
            </div>

            <!-- Summary message -->
            <div class="mt-4 p-3 bg-white/50 rounded-lg">
              <p class="text-sm text-gray-700">
                <span class="font-medium">Cilj:</span> Pratite potrošnju kroz artikle koje kupujete. Vremenom ćete vidjeti na šta trošite najviše!
              </p>
            </div>

            <!-- Beta notice -->
            <div class="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
              <span class="text-amber-500 flex-shrink-0">⚠️</span>
              <p class="text-sm text-amber-800">
                <span class="font-semibold">BETA:</span> Ova funkcija je trenutno u testnoj fazi. Moguće su greške pri očitavanju, ali stalno unapređujemo preciznost!
              </p>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Tab Navigation -->
      <div class="flex border-b border-gray-200 mb-6">
        <button
          @click="activeTab = 'receipts'"
          :class="[
            'flex-1 py-3 px-2 md:px-4 font-medium transition-colors flex flex-col md:flex-row items-center justify-center gap-1 md:gap-2',
            activeTab === 'receipts'
              ? 'text-purple-600 border-b-2 border-purple-600'
              : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          <svg class="w-6 h-6 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="text-sm md:text-base">Računi</span>
        </button>
        <button
          @click="activeTab = 'stats'"
          :class="[
            'flex-1 py-3 px-2 md:px-4 font-medium transition-colors flex flex-col md:flex-row items-center justify-center gap-1 md:gap-2',
            activeTab === 'stats'
              ? 'text-purple-600 border-b-2 border-purple-600'
              : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          <svg class="w-6 h-6 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span class="text-sm md:text-base">Statistika</span>
        </button>
      </div>

      <!-- Receipts Tab -->
      <div v-show="activeTab === 'receipts'">
        <!-- Upload Section -->
        <div class="bg-white rounded-xl shadow-md p-6 mb-6">
          <div class="text-center">
            <div class="w-20 h-20 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full mx-auto mb-4 flex items-center justify-center text-white">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">Slikajte račun</h3>
            <p class="text-gray-600 text-sm mb-4">
              Fotografišite račun iz radnje i automatski ćemo očitati proizvode
            </p>

            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              capture="environment"
              class="hidden"
              @change="handleFileSelect"
            />

            <div class="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                @click="openCamera"
                :disabled="isUploading"
                class="flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50"
              >
                <svg v-if="isUploading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {{ isUploading ? 'Učitavanje...' : 'Slikaj račun' }}
              </button>

              <button
                @click="openFileSelect"
                :disabled="isUploading"
                class="flex items-center justify-center gap-2 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-all disabled:opacity-50"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Odaberi sliku
              </button>
            </div>
          </div>
        </div>

        <!-- Image Preview -->
        <div v-if="previewUrl" class="bg-white rounded-xl shadow-md p-4 mb-6">
          <div class="relative">
            <img :src="previewUrl" alt="Preview" class="w-full max-h-80 object-contain rounded-lg" />
            <button
              @click="clearPreview"
              class="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="text-center py-8">
          <svg class="w-10 h-10 text-purple-600 animate-spin mx-auto" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="mt-4 text-gray-600">Učitavanje računa...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p class="text-red-700">{{ error }}</p>
        </div>

        <!-- Receipts List -->
        <div v-else>
          <div v-if="receipts.length === 0" class="text-center py-12">
            <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-gray-500">Nemate učitanih računa</p>
            <p class="text-gray-400 text-sm mt-1">Slikajte prvi račun da počnete pratiti potrošnju</p>
          </div>

          <template v-else>
          <!-- Mobile Cards View -->
          <div class="space-y-4 md:hidden">
            <div
              v-for="receipt in sortedReceipts"
              :key="receipt.id"
              :class="[
                'rounded-xl shadow-md overflow-hidden',
                receipt.processing_status === 'processing' || receipt.processing_status === 'pending'
                  ? 'animate-shimmer'
                  : receipt.processing_status === 'duplicate'
                    ? 'bg-red-50 border-2 border-red-200'
                    : 'bg-white'
              ]"
            >
              <!-- Card Header - New Layout -->
              <div class="p-4" @click="toggleExpand(receipt.id)">
                <div class="flex items-start gap-3">
                  <!-- Receipt Image Thumbnail -->
                  <div
                    v-if="receipt.receipt_image_url"
                    class="relative flex-shrink-0"
                    @click.stop="openImageLightbox(receipt.receipt_image_url)"
                  >
                    <img
                      :src="receipt.receipt_image_url"
                      alt="Račun"
                      class="w-14 h-14 rounded-lg object-cover"
                    />
                    <div class="absolute inset-0 bg-black/20 rounded-lg flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                      <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                      </svg>
                    </div>
                  </div>
                  <div v-else class="w-14 h-14 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg class="w-7 h-7 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>

                  <!-- Receipt Info - New Layout -->
                  <div class="flex-1 min-w-0">
                    <!-- Top Row: Amount + Articles -->
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span class="text-xl font-bold text-gray-900">
                          {{ receipt.total_amount ? receipt.total_amount.toFixed(2) : '0.00' }} KM
                        </span>
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                          {{ receipt.item_count || 0 }} artikala
                        </span>
                      </div>
                      <svg
                        class="w-5 h-5 text-gray-400 transition-transform duration-200 flex-shrink-0"
                        :class="{ 'rotate-90': expandedReceipts.has(receipt.id) }"
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </div>

                    <!-- Second Row: Store + Timestamp + Status -->
                    <div class="flex items-center gap-2 mt-1.5">
                      <span class="font-medium text-gray-700 truncate">
                        {{ receipt.store_name || 'Nepoznata radnja' }}
                      </span>
                      <span class="text-gray-400">•</span>
                      <span class="text-sm text-gray-500 whitespace-nowrap">
                        {{ formatDateShort(receipt.receipt_date || receipt.created_at) }}
                        {{ formatTime(receipt.receipt_date || receipt.created_at) }}
                      </span>
                    </div>

                    <!-- Status badge (for non-completed) -->
                    <div v-if="receipt.processing_status !== 'completed'" class="mt-1.5">
                      <span
                        :class="[
                          'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                          receipt.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                          receipt.processing_status === 'failed' ? 'bg-red-100 text-red-700' :
                          receipt.processing_status === 'duplicate' ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-100 text-gray-700'
                        ]"
                      >
                        {{ getStatusText(receipt.processing_status) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Expanded Items -->
              <div v-if="expandedReceipts.has(receipt.id)" class="border-t bg-gray-50 p-4">
                <!-- Loading -->
                <div v-if="loadingItems.has(receipt.id)" class="flex items-center gap-2 text-gray-500 py-4 justify-center">
                  <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="text-sm">Učitavanje...</span>
                </div>

                <!-- Items List -->
                <div v-else-if="receiptItems[receipt.id]?.length > 0" class="space-y-2">
                  <div
                    v-for="(item, idx) in receiptItems[receipt.id]"
                    :key="item.id"
                    class="flex items-center justify-between bg-white rounded-lg p-3"
                  >
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-gray-900 text-sm truncate">{{ item.parsed_name || item.raw_name }}</p>
                      <p class="text-xs text-gray-500">
                        <span v-if="item.brand && item.brand !== 'UNKNOWN'">{{ item.brand }}</span>
                        <span v-if="isFuelItem(item) && item.quantity"> • {{ item.quantity.toFixed(2) }} l × {{ getUnitPrice(item).toFixed(2) }} KM/l</span>
                        <span v-else-if="item.pack_size"> • {{ item.pack_size }}</span>
                        <span v-if="!isFuelItem(item) && item.quantity > 1"> • x{{ item.quantity }}</span>
                      </p>
                    </div>
                    <span class="font-semibold text-gray-900 text-sm ml-2">{{ item.line_total?.toFixed(2) || '-' }} KM</span>
                  </div>
                </div>

                <div v-else class="text-sm text-gray-500 py-4 text-center">
                  Nema artikala
                </div>

                <!-- Actions -->
                <div class="flex gap-2 mt-4 pt-4 border-t">
                  <button
                    @click.stop="openSidebar(receipt)"
                    class="flex-1 flex items-center justify-center gap-2 bg-purple-100 text-purple-700 py-2 rounded-lg font-medium"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    Detalji
                  </button>
                  <button
                    @click.stop="deleteReceipt(receipt)"
                    class="flex items-center justify-center gap-2 bg-red-100 text-red-700 px-4 py-2 rounded-lg font-medium"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Desktop Table View -->
          <div class="hidden md:block bg-white rounded-xl shadow-md overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="w-10 px-4 py-3"></th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Datum
                  </th>
                  <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Radnja
                  </th>
                  <th scope="col" class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Artikli
                  </th>
                  <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Ukupno
                  </th>
                  <th scope="col" class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Akcije
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <template v-for="receipt in sortedReceipts" :key="receipt.id">
                  <!-- Main Row -->
                  <tr
                    class="hover:bg-gray-50 cursor-pointer transition-colors"
                    @click="toggleExpand(receipt.id)"
                  >
                    <!-- Expand Icon -->
                    <td class="px-4 py-4">
                      <svg
                        class="w-5 h-5 text-gray-400 transition-transform duration-200"
                        :class="{ 'rotate-90': expandedReceipts.has(receipt.id) }"
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </td>
                    <!-- Date -->
                    <td class="px-4 py-4 whitespace-nowrap">
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatDateShort(receipt.receipt_date || receipt.created_at) }}
                      </div>
                      <div class="text-xs text-gray-500">
                        {{ formatTime(receipt.receipt_date || receipt.created_at) }}
                      </div>
                    </td>
                    <!-- Store -->
                    <td class="px-4 py-4">
                      <div class="flex items-center gap-3">
                        <img
                          v-if="receipt.receipt_image_url"
                          :src="receipt.receipt_image_url"
                          alt="Račun"
                          class="w-10 h-10 rounded-lg object-cover flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
                          @click.stop="openImageLightbox(receipt.receipt_image_url)"
                        />
                        <div class="min-w-0">
                          <div class="text-sm font-medium text-gray-900 truncate">
                            {{ receipt.store_name || 'Nepoznata radnja' }}
                          </div>
                          <div v-if="receipt.store_address" class="text-xs text-gray-500 truncate max-w-[200px]">
                            {{ receipt.store_address }}
                          </div>
                        </div>
                      </div>
                    </td>
                    <!-- Item Count -->
                    <td class="px-4 py-4 text-center">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {{ receipt.item_count || 0 }}
                      </span>
                    </td>
                    <!-- Total -->
                    <td class="px-4 py-4 text-right">
                      <span class="text-sm font-bold text-gray-900">
                        {{ receipt.total_amount ? receipt.total_amount.toFixed(2) : '0.00' }} KM
                      </span>
                    </td>
                    <!-- Status -->
                    <td class="px-4 py-4 text-center">
                      <span
                        :class="[
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          receipt.processing_status === 'completed' ? 'bg-green-100 text-green-700' :
                          receipt.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                          receipt.processing_status === 'failed' ? 'bg-red-100 text-red-700' :
                          receipt.processing_status === 'duplicate' ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-100 text-gray-700'
                        ]"
                      >
                        {{ getStatusText(receipt.processing_status) }}
                      </span>
                    </td>
                    <!-- Actions -->
                    <td class="px-4 py-4 text-right" @click.stop>
                      <div class="flex justify-end gap-1">
                        <button
                          @click="openSidebar(receipt)"
                          class="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                          title="Pogledaj račun"
                        >
                          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                        <button
                          @click="deleteReceipt(receipt)"
                          class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title="Obriši račun"
                        >
                          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>

                  <!-- Expanded Items Row -->
                  <tr v-if="expandedReceipts.has(receipt.id)" class="bg-gray-50">
                    <td colspan="7" class="px-4 py-4">
                      <div class="ml-9">
                        <!-- Loading items -->
                        <div v-if="loadingItems.has(receipt.id)" class="flex items-center gap-2 text-gray-500 py-4">
                          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span class="text-sm">Učitavanje artikala...</span>
                        </div>

                        <!-- Items table -->
                        <div v-else-if="receiptItems[receipt.id]?.length > 0" class="bg-white rounded-lg border border-gray-200 overflow-hidden">
                          <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-100">
                              <tr>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Naziv</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Brend</th>
                                <th class="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Količina</th>
                                <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Cijena</th>
                                <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Ukupno</th>
                              </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100">
                              <tr v-for="(item, idx) in receiptItems[receipt.id]" :key="item.id" class="hover:bg-gray-50">
                                <td class="px-4 py-2 text-sm text-gray-500">{{ idx + 1 }}</td>
                                <td class="px-4 py-2">
                                  <div class="text-sm font-medium text-gray-900">{{ item.parsed_name || item.raw_name }}</div>
                                  <div v-if="isFuelItem(item) && item.quantity" class="text-xs text-gray-500">{{ item.quantity.toFixed(2) }} l</div>
                                  <div v-else-if="item.pack_size" class="text-xs text-gray-500">{{ item.pack_size }}</div>
                                </td>
                                <td class="px-4 py-2 text-sm text-gray-600">
                                  {{ item.brand !== 'UNKNOWN' ? item.brand : '-' }}
                                </td>
                                <td class="px-4 py-2 text-sm text-gray-900 text-center">{{ item.quantity || 1 }}</td>
                                <td class="px-4 py-2 text-sm text-gray-600 text-right">
                                  {{ item.unit_price ? item.unit_price.toFixed(2) : '-' }} KM
                                </td>
                                <td class="px-4 py-2 text-sm font-medium text-gray-900 text-right">
                                  {{ item.line_total ? item.line_total.toFixed(2) : '-' }} KM
                                </td>
                              </tr>
                            </tbody>
                            <tfoot class="bg-gray-50">
                              <tr>
                                <td colspan="5" class="px-4 py-2 text-sm font-semibold text-gray-900 text-right">Ukupno:</td>
                                <td class="px-4 py-2 text-sm font-bold text-purple-600 text-right">
                                  {{ receipt.total_amount ? receipt.total_amount.toFixed(2) : '0.00' }} KM
                                </td>
                              </tr>
                            </tfoot>
                          </table>
                        </div>

                        <!-- No items -->
                        <div v-else class="text-sm text-gray-500 py-4">
                          Nema artikala za ovaj račun
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <!-- Load More -->
          <div v-if="hasMore" class="text-center mt-6">
            <button
              @click="loadMore"
              :disabled="isLoadingMore"
              class="bg-gray-100 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-200 transition-all disabled:opacity-50"
            >
              {{ isLoadingMore ? 'Učitavanje...' : 'Učitaj još' }}
            </button>
          </div>
          </template>
        </div>
      </div>

      <!-- Statistics Tab - Charts -->
      <div v-show="activeTab === 'stats'">
        <div v-if="isLoadingStats" class="text-center py-12">
          <svg class="w-10 h-10 text-purple-600 animate-spin mx-auto" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="mt-4 text-gray-600">Učitavanje statistike...</p>
        </div>

        <div v-else-if="chartData.length > 0">
          <!-- Period Filter -->
          <div class="flex gap-2 mb-6">
            <button
              v-for="period in chartPeriods"
              :key="period.value"
              @click="chartPeriod = period.value"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                chartPeriod === period.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              ]"
            >
              {{ period.label }}
            </button>
          </div>

          <!-- Bar Chart (at the top) -->
          <div class="bg-white rounded-xl shadow-md p-6 mb-6">
            <h3 class="font-semibold text-gray-900 mb-4">Dnevna potrošnja</h3>
            <div class="relative h-64 w-full">
              <Bar :data="barChartData" :options="barChartOptions" />
            </div>
          </div>

          <!-- Summary Cards -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div class="bg-white rounded-lg shadow-md p-3">
              <p class="text-xs text-gray-500 mb-1">Ukupno ({{ chartPeriodLabel }})</p>
              <p class="text-lg font-bold text-gray-900">{{ chartTotals.total.toFixed(2) }} KM</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-3">
              <p class="text-xs text-gray-500 mb-1">Prosječno dnevno</p>
              <p class="text-lg font-bold text-purple-600">{{ chartTotals.average.toFixed(2) }} KM</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-3">
              <p class="text-xs text-gray-500 mb-1">Najviši dan</p>
              <p class="text-lg font-bold text-red-600">{{ chartTotals.max.toFixed(2) }} KM</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-3">
              <p class="text-xs text-gray-500 mb-1">Broj računa</p>
              <p class="text-lg font-bold text-blue-600">{{ chartTotals.receipts }}</p>
            </div>
          </div>

          <!-- Top categories by spending -->
          <div class="grid md:grid-cols-2 gap-6 mt-6">
            <!-- Top Brands -->
            <div class="bg-white rounded-xl shadow-md p-4">
              <h3 class="font-semibold text-gray-900 mb-4">Top brendovi</h3>
              <div class="space-y-3">
                <div
                  v-for="(brand, idx) in topBrands"
                  :key="brand.name"
                  class="flex items-center gap-3"
                >
                  <span class="w-6 h-6 flex items-center justify-center bg-purple-100 text-purple-600 rounded text-xs font-bold">
                    {{ idx + 1 }}
                  </span>
                  <div class="flex-1">
                    <div class="flex justify-between items-center">
                      <span class="font-medium text-gray-900 text-sm">{{ brand.name }}</span>
                      <span class="font-semibold text-gray-900 text-sm">{{ brand.total.toFixed(2) }} KM</span>
                    </div>
                    <div class="mt-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        class="h-full bg-gradient-to-r from-purple-500 to-purple-300 rounded-full"
                        :style="{ width: `${(brand.total / topBrands[0]?.total) * 100}%` }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Products -->
            <div class="bg-white rounded-xl shadow-md p-4">
              <h3 class="font-semibold text-gray-900 mb-4">Top proizvodi</h3>
              <div class="space-y-3">
                <div
                  v-for="(product, idx) in topProducts"
                  :key="product.name"
                  class="flex items-center gap-3"
                >
                  <span class="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-600 rounded text-xs font-bold">
                    {{ idx + 1 }}
                  </span>
                  <div class="flex-1">
                    <div class="flex justify-between items-center">
                      <span class="font-medium text-gray-900 text-sm truncate">{{ product.name }}</span>
                      <span class="font-semibold text-gray-900 text-sm">{{ product.total.toFixed(2) }} KM</span>
                    </div>
                    <div class="mt-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        class="h-full bg-gradient-to-r from-blue-500 to-blue-300 rounded-full"
                        :style="{ width: `${(product.total / topProducts[0]?.total) * 100}%` }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-12">
          <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p class="text-gray-500">Nema dovoljno podataka za statistiku</p>
          <p class="text-gray-400 text-sm mt-1">Učitajte račune da vidite grafikon potrošnje</p>
        </div>
      </div>
    </div>

    <!-- Receipt Detail Sidebar -->
    <Teleport to="body">
      <!-- Backdrop -->
      <Transition name="fade">
        <div
          v-if="isSidebarOpen"
          class="fixed inset-0 z-40 bg-black/50"
          @click="closeSidebar"
        ></div>
      </Transition>

      <!-- Sidebar -->
      <Transition name="slide">
        <div
          v-if="isSidebarOpen && selectedReceipt"
          class="fixed right-0 top-0 z-50 h-full w-full max-w-md bg-white shadow-2xl overflow-hidden flex flex-col"
        >
          <!-- Header -->
          <div class="flex-shrink-0 border-b bg-gradient-to-r from-purple-600 to-blue-600 px-4 py-4">
            <div class="flex justify-between items-center">
              <div class="text-white">
                <h3 class="font-semibold text-lg">
                  {{ selectedReceipt.store_name || 'Račun' }}
                </h3>
                <p v-if="selectedReceipt.receipt_date" class="text-purple-100 text-sm">
                  {{ formatDate(selectedReceipt.receipt_date) }}
                </p>
              </div>
              <button @click="closeSidebar" class="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Content - Scrollable -->
          <div class="flex-1 overflow-y-auto">
            <!-- Receipt Image -->
            <div class="p-4 border-b bg-gray-50">
              <a
                v-if="selectedReceipt.receipt_image_url"
                :href="selectedReceipt.receipt_image_url"
                target="_blank"
                class="block"
              >
                <img
                  :src="selectedReceipt.receipt_image_url"
                  alt="Račun"
                  class="w-full rounded-lg shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
                />
              </a>
            </div>

            <!-- Info Cards -->
            <div class="p-4 space-y-3">
              <div v-if="selectedReceipt.store_address" class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div class="w-8 h-8 flex items-center justify-center bg-purple-100 rounded-lg flex-shrink-0">
                  <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase font-medium">Adresa</p>
                  <p class="text-sm text-gray-800">{{ selectedReceipt.store_address }}</p>
                </div>
              </div>

              <div v-if="selectedReceipt.jib" class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div class="w-8 h-8 flex items-center justify-center bg-blue-100 rounded-lg flex-shrink-0">
                  <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
                  </svg>
                </div>
                <div>
                  <p class="text-xs text-gray-500 uppercase font-medium">JIB</p>
                  <p class="text-sm text-gray-800 font-mono">{{ selectedReceipt.jib }}</p>
                </div>
              </div>
            </div>

            <!-- Items Section -->
            <div class="p-4 border-t">
              <div class="flex items-center justify-between mb-4">
                <h4 class="font-semibold text-gray-900">Artikli</h4>
                <span class="bg-purple-100 text-purple-700 text-xs font-medium px-2 py-1 rounded-full">
                  {{ selectedReceipt.items?.length || 0 }} stavki
                </span>
              </div>

              <div v-if="selectedReceipt.items && selectedReceipt.items.length > 0" class="space-y-2">
                <div
                  v-for="(item, idx) in selectedReceipt.items"
                  :key="item.id"
                  class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div class="flex items-start gap-3">
                    <span class="text-xs text-gray-400 font-medium w-5 flex-shrink-0 pt-0.5">{{ idx + 1 }}</span>
                    <div class="flex-1 min-w-0">
                      <!-- Parsed name (main) -->
                      <p class="font-medium text-gray-900 text-sm leading-tight">{{ item.parsed_name || item.raw_name }}</p>

                      <!-- Raw receipt text (if different from parsed) -->
                      <p
                        v-if="item.raw_name && item.parsed_name && cleanRawName(item.raw_name) !== item.parsed_name"
                        class="text-xs text-gray-500 mt-0.5 font-mono truncate"
                        :title="item.raw_name"
                      >
                        {{ cleanRawName(item.raw_name) }}
                      </p>

                      <!-- Tags row -->
                      <div class="flex flex-wrap gap-2 mt-1.5">
                        <span v-if="item.brand && item.brand !== 'UNKNOWN'" class="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
                          {{ item.brand }}
                        </span>
                        <!-- For fuel items, show quantity in liters instead of misleading pack_size -->
                        <span v-if="isFuelItem(item) && item.quantity" class="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">
                          {{ item.quantity.toFixed(2) }} l
                        </span>
                        <span v-else-if="item.pack_size" class="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">
                          {{ item.pack_size }}
                        </span>
                      </div>
                    </div>

                    <!-- Price column -->
                    <div class="flex-shrink-0 text-right">
                      <span class="font-semibold text-gray-900 text-sm">{{ item.line_total?.toFixed(2) }} KM</span>
                      <!-- Show quantity breakdown if more than 1 -->
                      <p v-if="item.quantity > 1" class="text-xs text-gray-500 mt-0.5">
                        {{ item.quantity }} x {{ getUnitPrice(item).toFixed(2) }} KM
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="text-center py-8 text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p class="text-sm">Nema očitanih artikala</p>
              </div>
            </div>
          </div>

          <!-- Footer - Total -->
          <div v-if="selectedReceipt.total_amount" class="flex-shrink-0 border-t bg-gradient-to-r from-purple-50 to-blue-50 p-4">
            <div class="flex justify-between items-center">
              <span class="font-medium text-gray-700">Ukupno</span>
              <span class="text-2xl font-bold text-purple-600">{{ selectedReceipt.total_amount.toFixed(2) }} KM</span>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Image Lightbox -->
      <Transition name="fade">
        <div
          v-if="lightboxUrl"
          class="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4"
          @click="closeImageLightbox"
        >
          <button
            class="absolute top-4 right-4 text-white/80 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors"
            @click="closeImageLightbox"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <img
            :src="lightboxUrl"
            alt="Račun"
            class="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            @click.stop
          />
        </div>
      </Transition>

      <!-- Delete Confirmation Modal -->
      <Transition name="fade">
        <div v-if="showDeleteModal" class="fixed inset-0 z-[60] overflow-y-auto">
          <div class="flex items-center justify-center min-h-screen px-4">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="cancelDelete"></div>
            <div class="relative bg-white rounded-xl max-w-md w-full shadow-2xl p-6">
              <div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
                <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 text-center mb-2">Obrisati račun?</h3>
              <p class="text-gray-600 text-center mb-6">
                Da li ste sigurni da želite obrisati račun iz radnje
                <strong>{{ receiptToDelete?.store_name || 'Nepoznata radnja' }}</strong>
                <span v-if="receiptToDelete?.total_amount"> u iznosu od {{ receiptToDelete.total_amount.toFixed(2) }} KM</span>?
                Ova akcija se ne može poništiti.
              </p>
              <div class="flex gap-3">
                <button
                  @click="cancelDelete"
                  :disabled="isDeleting"
                  class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-100 disabled:opacity-50"
                >
                  Otkaži
                </button>
                <button
                  @click="confirmDelete"
                  :disabled="isDeleting"
                  class="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <svg v-if="isDeleting" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {{ isDeleting ? 'Brisanje...' : 'Obriši' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Confetti Canvas -->
      <canvas
        v-show="showConfetti"
        ref="confettiCanvas"
        class="fixed inset-0 z-[70] pointer-events-none"
      ></canvas>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import ChartDataLabels from 'chartjs-plugin-datalabels'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ChartDataLabels)

definePageMeta({
  middleware: ['auth']
})

const { get, post, del } = useApi()
const config = useRuntimeConfig()
const { token } = useAuth()

const activeTab = ref('receipts')
const fileInput = ref<HTMLInputElement | null>(null)
const previewUrl = ref<string | null>(null)
const selectedFile = ref<File | null>(null)

// Receipts state
const receipts = ref<any[]>([])
const isLoading = ref(true)
const isUploading = ref(false)
const isLoadingMore = ref(false)
const error = ref<string | null>(null)
const currentPage = ref(1)
const hasMore = ref(false)

// Stats state
const stats = ref<any>(null)
const isLoadingStats = ref(false)
const allItems = ref<any[]>([])

// Chart state (Statistika tab)
const chartPeriod = ref('week')
const chartPeriods = [
  { value: 'week', label: '7 dana' },
  { value: 'day', label: '30 dana' },
  { value: 'month', label: '6 mjeseci' }
]

// Selected receipt for sidebar
const selectedReceipt = ref<any>(null)
const isSidebarOpen = ref(false)

// Image lightbox state
const lightboxUrl = ref<string | null>(null)

// Confetti state
const confettiCanvas = ref<HTMLCanvasElement | null>(null)
const showConfetti = ref(false)
const showTips = ref(true)

// Delete confirmation modal state
const showDeleteModal = ref(false)
const receiptToDelete = ref<any>(null)
const isDeleting = ref(false)

// Expandable table state
const expandedReceipts = ref(new Set<number>())
const loadingItems = ref(new Set<number>())
const receiptItems = ref<Record<number, any[]>>({})

// Sorted receipts by date descending (newest first)
const sortedReceipts = computed(() => {
  return [...receipts.value].sort((a, b) => {
    const dateA = new Date(a.receipt_date || a.created_at).getTime()
    const dateB = new Date(b.receipt_date || b.created_at).getTime()
    return dateB - dateA
  })
})

// Filter items by selected chart period for stats
const filteredItems = computed(() => {
  const now = new Date()
  let cutoff: Date

  switch (chartPeriod.value) {
    case 'day':
      cutoff = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      break
    case 'week':
      cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case 'month':
      cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    default:
      cutoff = new Date(0)
  }

  return allItems.value.filter(item => {
    const itemDate = new Date(item.receipt_date || item.created_at)
    return itemDate >= cutoff
  })
})

// Chart data - varies by period
const chartData = computed(() => {
  const now = new Date()
  now.setHours(23, 59, 59, 999)

  // For "1 mjesec" - show last 6 months aggregated by month
  if (chartPeriod.value === 'month') {
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
    const monthlyData: { year: number; month: number; amount: number; receipts: number }[] = []

    // Create 6 months of data
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now)
      date.setMonth(date.getMonth() - i)
      monthlyData.push({ year: date.getFullYear(), month: date.getMonth(), amount: 0, receipts: 0 })
    }

    // Aggregate receipts by month
    for (const receipt of receipts.value) {
      const receiptDate = new Date(receipt.receipt_date || receipt.created_at)
      const monthData = monthlyData.find(m => m.year === receiptDate.getFullYear() && m.month === receiptDate.getMonth())
      if (monthData) {
        monthData.amount += receipt.total_amount || 0
        monthData.receipts += 1
      }
    }

    return monthlyData.map(m => ({
      date: new Date(m.year, m.month, 1),
      amount: m.amount,
      receipts: m.receipts,
      label: `${monthNames[m.month]} ${m.year}`,
      shortLabel: monthNames[m.month]
    }))
  }

  // For "1 dan" - show last 30 days
  if (chartPeriod.value === 'day') {
    const dailyData: { date: Date; amount: number; receipts: number }[] = []

    for (let i = 29; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      date.setHours(0, 0, 0, 0)
      dailyData.push({ date, amount: 0, receipts: 0 })
    }

    // Aggregate receipts by day
    for (const receipt of receipts.value) {
      const receiptDate = new Date(receipt.receipt_date || receipt.created_at)
      receiptDate.setHours(0, 0, 0, 0)

      const dayData = dailyData.find(d => d.date.getTime() === receiptDate.getTime())
      if (dayData) {
        dayData.amount += receipt.total_amount || 0
        dayData.receipts += 1
      }
    }

    return dailyData.map(d => ({
      date: d.date,
      amount: d.amount,
      receipts: d.receipts,
      label: d.date.toLocaleDateString('bs-BA', { weekday: 'short', day: 'numeric', month: 'short' }),
      shortLabel: String(d.date.getDate())
    }))
  }

  // For "1 sedmica" - show last 7 days
  const dailyData: { date: Date; amount: number; receipts: number }[] = []

  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    date.setHours(0, 0, 0, 0)
    dailyData.push({ date, amount: 0, receipts: 0 })
  }

  // Aggregate receipts by day
  for (const receipt of receipts.value) {
    const receiptDate = new Date(receipt.receipt_date || receipt.created_at)
    receiptDate.setHours(0, 0, 0, 0)

    const dayData = dailyData.find(d => d.date.getTime() === receiptDate.getTime())
    if (dayData) {
      dayData.amount += receipt.total_amount || 0
      dayData.receipts += 1
    }
  }

  return dailyData.map(d => ({
    date: d.date,
    amount: d.amount,
    receipts: d.receipts,
    label: d.date.toLocaleDateString('bs-BA', { weekday: 'short', day: 'numeric', month: 'short' }),
    shortLabel: String(d.date.getDate())
  }))
})

// Chart max value - use highest actual value from data
const chartMaxValue = computed(() => {
  return Math.max(...chartData.value.map(d => d.amount), 1)
})

// Bar chart data for Chart.js
const barChartData = computed(() => ({
  labels: chartData.value.map(d => d.shortLabel),
  datasets: [{
    label: 'Potrošeno (KM)',
    data: chartData.value.map(d => d.amount),
    backgroundColor: 'rgba(147, 51, 234, 0.8)',
    borderColor: 'rgb(147, 51, 234)',
    borderWidth: 2,
    borderRadius: 6,
  }]
}))

// Bar chart options for Chart.js
const barChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        title: (items: any) => {
          const idx = items[0]?.dataIndex
          if (idx !== undefined && chartData.value[idx]) {
            const date = chartData.value[idx].date
            // Format as dd/mm/yyyy
            const day = String(date.getDate()).padStart(2, '0')
            const month = String(date.getMonth() + 1).padStart(2, '0')
            const year = date.getFullYear()
            return `${day}/${month}/${year}`
          }
          return ''
        },
        label: (item: any) => {
          const idx = item.dataIndex
          const data = chartData.value[idx]
          if (data) {
            return [`${data.amount.toFixed(2)} KM`, `${data.receipts} računa`]
          }
          return ''
        }
      }
    },
    datalabels: {
      anchor: 'end',
      align: 'top',
      offset: 4,
      color: '#374151', // gray-700 for good contrast
      font: {
        weight: 'bold',
        size: 11
      },
      formatter: (value: number) => value > 0 ? `${value.toFixed(0)}` : ''
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: chartMaxValue.value * 1.15, // Add 15% padding for labels above bars
      ticks: {
        callback: (value: number) => `${value.toFixed(0)} KM`
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      }
    },
    x: {
      grid: {
        display: false
      }
    }
  }
}))

// Chart totals
const chartTotals = computed(() => {
  const total = chartData.value.reduce((sum, d) => sum + d.amount, 0)
  const receipts = chartData.value.reduce((sum, d) => sum + d.receipts, 0)
  const daysWithData = chartData.value.filter(d => d.amount > 0).length
  const average = daysWithData > 0 ? total / daysWithData : 0
  const max = Math.max(...chartData.value.map(d => d.amount))

  return { total, average, max, receipts }
})

// Chart period label
const chartPeriodLabel = computed(() => {
  switch (chartPeriod.value) {
    case 'day': return '30 dana'
    case 'week': return '7 dana'
    case 'month': return '6 mjeseci'
    default: return ''
  }
})

// Top brands from all items
const topBrands = computed(() => {
  const brandMap = new Map<string, { name: string; total: number; count: number }>()

  for (const item of filteredItems.value) {
    const brand = item.brand && item.brand !== 'UNKNOWN' ? item.brand : null
    if (!brand) continue

    if (!brandMap.has(brand)) {
      brandMap.set(brand, { name: brand, total: 0, count: 0 })
    }
    const data = brandMap.get(brand)!
    data.total += item.line_total || 0
    data.count += 1
  }

  return Array.from(brandMap.values())
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
})

// Top products from all items
const topProducts = computed(() => {
  const productMap = new Map<string, { name: string; total: number; count: number }>()

  for (const item of filteredItems.value) {
    const name = item.parsed_name || item.raw_name || 'Nepoznato'

    if (!productMap.has(name)) {
      productMap.set(name, { name, total: 0, count: 0 })
    }
    const data = productMap.get(name)!
    data.total += item.line_total || 0
    data.count += 1
  }

  return Array.from(productMap.values())
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
})

const route = useRoute()
const router = useRouter()

// Load receipts on mount
onMounted(async () => {
  await loadReceipts()
  // Check if we need to poll for a new receipt (came from FAB upload)
  handleRefreshParam()
})

// Watch for refresh query param (when navigating from FAB upload)
watch(() => route.query.refresh, (newVal) => {
  if (newVal) {
    handleRefreshParam()
  }
})

// Handle refresh parameter - reload receipts and clear the param
async function handleRefreshParam() {
  if (route.query.refresh) {
    await loadReceipts()
    // Remove the refresh param from URL without navigation
    router.replace({ path: '/racuni', query: {} })
    // Start polling for the newest receipt if it's still processing
    // Use sortedReceipts to ensure we get the most recent one
    await nextTick()
    const newest = sortedReceipts.value[0]
    if (newest && (newest.processing_status === 'pending' || newest.processing_status === 'processing')) {
      pollReceiptStatus(newest.id)
    }
  }
}

// Load stats data when switching to stats tab
watch(activeTab, async (newTab) => {
  if (newTab === 'stats') {
    if (allItems.value.length === 0) {
      await loadAllItems()
    }
    if (!stats.value) {
      await loadStats()
    }
  }
})

// Load all items for stats (top brands/products)
async function loadAllItems() {
  try {
    const response = await get('/api/receipts/items', {
      per_page: 1000
    })
    allItems.value = response.items || []
  } catch (e: any) {
    console.error('Error loading items:', e)
    allItems.value = []
  }
}

async function loadReceipts() {
  isLoading.value = true
  error.value = null

  try {
    const response = await get('/api/receipts', {
      page: 1,
      per_page: 20
    })
    receipts.value = response.receipts || []
    currentPage.value = 1
    hasMore.value = response.pages > 1
  } catch (e: any) {
    error.value = e.message || 'Greška prilikom učitavanja računa'
  } finally {
    isLoading.value = false
  }
}

async function loadMore() {
  isLoadingMore.value = true

  try {
    const response = await get('/api/receipts', {
      page: currentPage.value + 1,
      per_page: 20
    })
    receipts.value = [...receipts.value, ...(response.receipts || [])]
    currentPage.value++
    hasMore.value = response.pages > currentPage.value
  } catch (e: any) {
    console.error('Error loading more receipts:', e)
  } finally {
    isLoadingMore.value = false
  }
}

async function loadStats() {
  isLoadingStats.value = true

  try {
    const response = await get('/api/receipts/statistics', {
      period: 'monthly',
      months: 3
    })
    stats.value = response
  } catch (e: any) {
    console.error('Error loading stats:', e)
  } finally {
    isLoadingStats.value = false
  }
}

function openCamera() {
  if (fileInput.value) {
    fileInput.value.setAttribute('capture', 'environment')
    fileInput.value.click()
  }
}

function openFileSelect() {
  if (fileInput.value) {
    fileInput.value.removeAttribute('capture')
    fileInput.value.click()
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
    uploadReceipt(file)
  }
}

function clearPreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = null
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function uploadReceipt(file: File) {
  isUploading.value = true
  error.value = null

  try {
    const formData = new FormData()
    formData.append('image', file)

    const response = await fetch(`${config.public.apiBase}/api/receipts/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token.value}`
      },
      body: formData
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || 'Upload failed')
    }

    const data = await response.json()

    // Add to top of list
    if (data.receipt) {
      receipts.value = [data.receipt, ...receipts.value]
      // Trigger confetti animation on successful upload
      nextTick(() => {
        startConfetti()
      })
    }

    clearPreview()

    // Poll for processing completion
    if (data.receipt?.id) {
      pollReceiptStatus(data.receipt.id)
    }
  } catch (e: any) {
    error.value = e.message || 'Greška prilikom učitavanja računa'
  } finally {
    isUploading.value = false
  }
}

async function pollReceiptStatus(receiptId: number) {
  let attempts = 0
  const maxAttempts = 30 // 30 seconds max

  const poll = async () => {
    attempts++
    if (attempts > maxAttempts) {
      console.log('Polling stopped: max attempts reached')
      return
    }

    try {
      const response = await get(`/api/receipts/${receiptId}`)
      const receipt = response?.receipt

      // Stop polling if no receipt found
      if (!receipt) {
        console.log('Polling stopped: no receipt in response')
        return
      }

      // Update in list
      const index = receipts.value.findIndex(r => r.id === receiptId)
      if (index !== -1) {
        receipts.value[index] = receipt
      }

      // If still processing, poll again (with longer interval)
      if (receipt.processing_status === 'pending' || receipt.processing_status === 'processing') {
        setTimeout(poll, 2000) // 2 seconds between polls
      } else {
        console.log('Polling complete:', receipt.processing_status)
        // Refresh stats if on stats tab
        if (activeTab.value === 'stats') {
          loadStats()
        }
      }
    } catch (e) {
      console.error('Error polling receipt status, stopping:', e)
      // Stop polling on error
      return
    }
  }

  poll()
}

function deleteReceipt(receipt: any) {
  receiptToDelete.value = receipt
  showDeleteModal.value = true
}

function cancelDelete() {
  showDeleteModal.value = false
  receiptToDelete.value = null
}

async function confirmDelete() {
  if (!receiptToDelete.value) return

  isDeleting.value = true
  try {
    await del(`/api/receipts/${receiptToDelete.value.id}`)
    receipts.value = receipts.value.filter(r => r.id !== receiptToDelete.value.id)

    // Refresh stats
    if (stats.value) {
      loadStats()
    }

    showDeleteModal.value = false
    receiptToDelete.value = null
  } catch (e: any) {
    error.value = e.message || 'Greška prilikom brisanja računa'
  } finally {
    isDeleting.value = false
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('bs-BA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getStatusText(status: string): string {
  switch (status) {
    case 'completed': return 'Obrađeno'
    case 'processing': return 'Obrada...'
    case 'failed': return 'Greška'
    case 'pending': return 'Čeka'
    case 'duplicate': return 'Duplikat'
    default: return status
  }
}

// Toggle expand receipt row and load items
async function toggleExpand(receiptId: number) {
  if (expandedReceipts.value.has(receiptId)) {
    expandedReceipts.value.delete(receiptId)
    // Trigger reactivity
    expandedReceipts.value = new Set(expandedReceipts.value)
  } else {
    expandedReceipts.value.add(receiptId)
    expandedReceipts.value = new Set(expandedReceipts.value)

    // Load items if not already loaded
    if (!receiptItems.value[receiptId]) {
      loadingItems.value.add(receiptId)
      loadingItems.value = new Set(loadingItems.value)

      try {
        const response = await get(`/api/receipts/${receiptId}`)
        if (response?.receipt?.items) {
          receiptItems.value[receiptId] = response.receipt.items
        } else {
          receiptItems.value[receiptId] = []
        }
      } catch (e) {
        console.error('Error loading receipt items:', e)
        receiptItems.value[receiptId] = []
      } finally {
        loadingItems.value.delete(receiptId)
        loadingItems.value = new Set(loadingItems.value)
      }
    }
  }
}

// Clean raw name by removing leading product codes (e.g., "123456 PRODUCT NAME" -> "PRODUCT NAME")
function cleanRawName(rawName: string | null): string {
  if (!rawName) return ''
  // Remove leading codes: numbers, alphanumeric codes like "A123", barcodes, etc.
  // Pattern: start of string, optional whitespace, code (letters/numbers), whitespace, then the actual name
  return rawName.replace(/^[\s]*[A-Za-z0-9]{4,15}[\s]+/, '').trim()
}

// Get unit price - use stored value or calculate from line_total / quantity
function getUnitPrice(item: any): number {
  if (item.unit_price) return item.unit_price
  if (item.line_total && item.quantity > 0) {
    return item.line_total / item.quantity
  }
  return 0
}

// Check if item is fuel (benzin, dizel, gorivo, etc.) - measured in liters
function isFuelItem(item: any): boolean {
  // Use LLM classification if available (new receipts)
  if (typeof item.is_fuel === 'boolean') {
    return item.is_fuel
  }

  // Fallback for old receipts without is_fuel field
  const name = (item.parsed_name || item.raw_name || '').toLowerCase()
  const productType = (item.product_type || '').toLowerCase()

  // Exclude tax/fee lines
  const excludeKeywords = ['taksa', 'naknada', 'porez', 'tax', 'fee']
  if (excludeKeywords.some(keyword => name.includes(keyword))) return false

  // Check product_type
  if (productType === 'gorivo' || productType === 'fuel') return true

  // Check name for fuel keywords
  const fuelKeywords = ['benzin', 'dizel', 'diesel', 'eurosuper', 'euro super', 'premium bezolovni']
  return fuelKeywords.some(keyword => name.includes(keyword))
}

// Short date format (dd.mm.yyyy)
function formatDateShort(dateStr: string | null): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('bs-BA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

// Time format (HH:mm)
function formatTime(dateStr: string | null): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleTimeString('bs-BA', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Open sidebar with receipt details
function openSidebar(receipt: any) {
  selectedReceipt.value = receipt
  isSidebarOpen.value = true
  // Load full details if needed
  if (!receipt.items) {
    get(`/api/receipts/${receipt.id}`).then(response => {
      if (response?.receipt) {
        selectedReceipt.value = response.receipt
      }
    }).catch(e => console.error('Error loading receipt:', e))
  }
}

// Close sidebar
function closeSidebar() {
  isSidebarOpen.value = false
  setTimeout(() => {
    selectedReceipt.value = null
  }, 300)
}

// Open image lightbox
function openImageLightbox(url: string) {
  lightboxUrl.value = url
}

// Close image lightbox
function closeImageLightbox() {
  lightboxUrl.value = null
}

// Confetti animation
function startConfetti() {
  showConfetti.value = true
  const canvas = confettiCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  interface Particle {
    x: number
    y: number
    vx: number
    vy: number
    color: string
    size: number
    rotation: number
    rotationSpeed: number
  }

  const particles: Particle[] = []
  const colors = ['#10B981', '#34D399', '#6EE7B7', '#FBBF24', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#3B82F6']

  // Create particles
  for (let i = 0; i < 200; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      vx: (Math.random() - 0.5) * 4,
      vy: Math.random() * 3 + 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 8 + 4,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.2
    })
  }

  let frame = 0
  const maxFrames = 180 // 3 seconds at 60fps

  function animate() {
    if (frame >= maxFrames) {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      showConfetti.value = false
      return
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    particles.forEach(p => {
      p.x += p.vx
      p.y += p.vy
      p.vy += 0.1 // gravity
      p.rotation += p.rotationSpeed

      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(p.rotation)
      ctx.fillStyle = p.color
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6)
      ctx.restore()
    })

    frame++
    requestAnimationFrame(animate)
  }

  animate()
}
</script>

<style scoped>
/* Fade transition for backdrop */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide transition for sidebar */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* Collapse transition for tips banner */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* Shimmer animation for processing receipts */
@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.animate-shimmer {
  background: linear-gradient(
    90deg,
    #ffffff 0%,
    #ffffff 25%,
    #f3e8ff 35%,
    #e9d5ff 50%,
    #f3e8ff 65%,
    #ffffff 75%,
    #ffffff 100%
  );
  background-size: 300% 100%;
  animation: shimmer 1.5s linear infinite;
}
</style>
