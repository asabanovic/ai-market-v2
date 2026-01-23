<template>
  <div class="min-h-screen bg-gray-50 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <NuxtLink to="/admin" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </NuxtLink>
            <div>
              <h1 class="text-2xl font-semibold text-gray-900">Korisnicke prijave proizvoda</h1>
              <p class="mt-1 text-sm text-gray-600">Pregled i odobravanje korisnickih fotografija proizvoda</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Summary -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="text-sm text-gray-500">Ukupno</div>
          <div class="text-2xl font-bold text-gray-900">{{ stats.total }}</div>
        </div>
        <div class="bg-white rounded-lg border border-yellow-200 p-4 bg-yellow-50">
          <div class="text-sm text-yellow-700">Na cekanju</div>
          <div class="text-2xl font-bold text-yellow-600">{{ stats.pending }}</div>
        </div>
        <div class="bg-white rounded-lg border border-blue-200 p-4 bg-blue-50">
          <div class="text-sm text-blue-700">U obradi</div>
          <div class="text-2xl font-bold text-blue-600">{{ stats.processing }}</div>
        </div>
        <div class="bg-white rounded-lg border border-green-200 p-4 bg-green-50">
          <div class="text-sm text-green-700">Odobreno</div>
          <div class="text-2xl font-bold text-green-600">{{ stats.approved }}</div>
        </div>
        <div class="bg-white rounded-lg border border-red-200 p-4 bg-red-50">
          <div class="text-sm text-red-700">Odbijeno</div>
          <div class="text-2xl font-bold text-red-600">{{ stats.rejected }}</div>
        </div>
      </div>

      <!-- Filter Buttons -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button
          @click="setFilter(null)"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            !statusFilter
              ? 'bg-indigo-600 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          Svi
        </button>
        <button
          @click="setFilter('pending')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            statusFilter === 'pending'
              ? 'bg-yellow-600 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          Na cekanju
        </button>
        <button
          @click="setFilter('processing')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            statusFilter === 'processing'
              ? 'bg-blue-600 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          U obradi
        </button>
        <button
          @click="setFilter('approved')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            statusFilter === 'approved'
              ? 'bg-green-600 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          Odobreno
        </button>
        <button
          @click="setFilter('rejected')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            statusFilter === 'rejected'
              ? 'bg-red-600 text-white'
              : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          Odbijeno
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center text-indigo-600">
          <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="ml-3 text-lg">Ucitavanje...</span>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="submissions.length === 0" class="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">Nema prijava</h3>
        <p class="mt-2 text-gray-600">Trenutno nema korisnickih prijava za pregled.</p>
      </div>

      <!-- Table View -->
      <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slika</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Korisnik</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Biznis</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ekstrahirano</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Datum</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Akcije</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="submission in submissions" :key="submission.id" class="hover:bg-gray-50">
                <!-- Image -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div
                    class="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden cursor-pointer"
                    @click="openViewModal(submission)"
                  >
                    <img
                      :src="submission.image_url"
                      :alt="`Submission ${submission.id}`"
                      class="w-full h-full object-cover"
                    />
                  </div>
                </td>

                <!-- User -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                      <span class="text-sm font-medium text-indigo-600">
                        {{ submission.user_name?.charAt(0) || submission.user_email?.charAt(0) || '?' }}
                      </span>
                    </div>
                    <div class="max-w-[120px]">
                      <p class="text-sm font-medium text-gray-900 truncate">
                        {{ submission.user_name || submission.user_email }}
                      </p>
                    </div>
                  </div>
                </td>

                <!-- Business -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <span class="text-sm text-gray-900">{{ submission.business_name }}</span>
                </td>

                <!-- Extracted Data -->
                <td class="px-4 py-3">
                  <div v-if="submission.extracted_title" class="max-w-[200px]">
                    <p class="text-sm font-medium text-gray-900 truncate">{{ submission.extracted_title }}</p>
                    <p v-if="submission.extracted_old_price || submission.extracted_new_price" class="text-xs text-gray-500">
                      <span v-if="submission.extracted_old_price">{{ submission.extracted_old_price }} KM</span>
                      <span v-if="submission.extracted_new_price" class="text-green-600 ml-1">
                        &rarr; {{ submission.extracted_new_price }} KM
                      </span>
                    </p>
                  </div>
                  <span v-else class="text-xs text-gray-400">Nije obradeno</span>
                </td>

                <!-- Status -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <span
                    :class="[
                      'px-2 py-1 text-xs font-medium rounded-full',
                      getStatusClass(submission.status)
                    ]"
                  >
                    {{ getStatusLabel(submission.status) }}
                  </span>
                </td>

                <!-- Date -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <span class="text-sm text-gray-500">{{ formatDate(submission.created_at) }}</span>
                </td>

                <!-- Actions -->
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="flex gap-2">
                    <button
                      @click="openViewModal(submission)"
                      class="px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded hover:bg-indigo-200 transition-colors"
                    >
                      Pregledaj
                    </button>
                    <button
                      v-if="submission.status === 'pending'"
                      @click="openApproveModal(submission)"
                      class="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded hover:bg-green-200 transition-colors"
                    >
                      Odobri
                    </button>
                    <button
                      v-if="submission.status === 'pending'"
                      @click="openRejectModal(submission)"
                      class="px-3 py-1 bg-red-100 text-red-700 text-xs font-medium rounded hover:bg-red-200 transition-colors"
                    >
                      Odbij
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-6 flex justify-center gap-2">
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 text-gray-700"
        >
          Prethodna
        </button>
        <span class="px-4 py-2 text-gray-600">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button
          @click="goToPage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 text-gray-700"
        >
          Sljedeca
        </button>
      </div>
    </div>

    <!-- View/Process Modal -->
    <Teleport to="body">
      <div
        v-if="viewingSubmission"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="viewingSubmission = null"
      >
        <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
          <!-- Header -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Prijava #{{ viewingSubmission.id }}</h3>
              <button @click="viewingSubmission = null" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            <div class="flex gap-6">
              <!-- Image Preview -->
              <div class="flex-shrink-0 w-80">
                <div class="bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    :src="viewingSubmission.image_url"
                    :alt="`Submission ${viewingSubmission.id}`"
                    class="w-full h-auto"
                  />
                </div>
                <!-- User info -->
                <div class="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p class="text-sm font-medium text-gray-900">{{ viewingSubmission.user_name || viewingSubmission.user_email }}</p>
                  <p class="text-xs text-gray-500">{{ viewingSubmission.business_name }}</p>
                  <p class="text-xs text-gray-400 mt-1">{{ formatDate(viewingSubmission.created_at) }}</p>
                </div>
              </div>

              <!-- AI Extraction Panel -->
              <div class="flex-1">
                <!-- Process with AI Button -->
                <div class="mb-6">
                  <button
                    @click="processWithAI"
                    :disabled="isProcessingAI"
                    class="w-full px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
                  >
                    <svg v-if="isProcessingAI" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    {{ isProcessingAI ? 'Obrada u toku...' : 'Pokreni AI obradu' }}
                  </button>
                  <p v-if="aiProcessError" class="mt-2 text-sm text-red-600">{{ aiProcessError }}</p>
                </div>

                <!-- Extracted Data Display/Edit -->
                <div class="space-y-4">
                  <h4 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">Ekstrahirani podaci</h4>

                  <div v-if="extractedData || viewingSubmission.extracted_title">
                    <div class="space-y-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda</label>
                        <input
                          v-model="editableData.title"
                          type="text"
                          class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                          placeholder="Naziv proizvoda"
                        />
                      </div>

                      <div class="grid grid-cols-2 gap-4">
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Stara cijena (KM)</label>
                          <input
                            v-model="editableData.base_price"
                            type="number"
                            step="0.01"
                            class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                            placeholder="0.00"
                          />
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Nova cijena (KM)</label>
                          <input
                            v-model="editableData.discount_price"
                            type="number"
                            step="0.01"
                            class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                            placeholder="0.00"
                          />
                        </div>
                      </div>

                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Vazi do</label>
                        <input
                          v-model="editableData.expires"
                          type="date"
                          class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                        />
                      </div>

                      <!-- Additional extracted info (read-only display) -->
                      <div v-if="extractedData" class="bg-gray-50 rounded-lg p-3">
                        <h5 class="text-xs font-medium text-gray-500 mb-2">Dodatni podaci iz AI</h5>
                        <div class="flex flex-wrap gap-2">
                          <span v-if="extractedData.brand" class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{{ extractedData.brand }}</span>
                          <span v-if="extractedData.product_type" class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">{{ extractedData.product_type }}</span>
                          <span v-if="extractedData.category" class="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">{{ extractedData.category }}</span>
                          <span v-if="extractedData.weight_volume" class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">{{ extractedData.weight_volume }}</span>
                        </div>
                        <p v-if="extractedData.description" class="text-xs text-gray-600 mt-2">{{ extractedData.description }}</p>
                      </div>
                    </div>
                  </div>

                  <div v-else class="text-center py-8 bg-gray-50 rounded-lg">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <p class="mt-2 text-sm text-gray-500">Klikni "Pokreni AI obradu" za ekstrahiranje podataka sa slike</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
            <button
              @click="viewingSubmission = null"
              class="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100"
            >
              Zatvori
            </button>
            <div v-if="viewingSubmission.status === 'pending' || viewingSubmission.status === 'processing'" class="flex gap-2">
              <button
                @click="openRejectFromView"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Odbij
              </button>
              <button
                @click="approveFromView"
                :disabled="!editableData.title || !editableData.base_price"
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Odobri i kreiraj proizvod
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Approve Modal (simple) -->
    <Teleport to="body">
      <div
        v-if="approvingSubmission"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="approvingSubmission = null"
      >
        <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Odobri prijavu</h3>

          <!-- Preview image -->
          <div class="mb-4">
            <img :src="approvingSubmission.image_url" class="w-full h-48 object-cover rounded-lg" />
          </div>

          <!-- Form -->
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Naziv proizvoda *</label>
              <input
                v-model="approveForm.title"
                type="text"
                class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                placeholder="Unesite naziv proizvoda"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Stara cijena (KM) *</label>
                <input
                  v-model="approveForm.base_price"
                  type="number"
                  step="0.01"
                  class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Nova cijena (KM)</label>
                <input
                  v-model="approveForm.discount_price"
                  type="number"
                  step="0.01"
                  class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
                  placeholder="0.00"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Vazi do</label>
              <input
                v-model="approveForm.expires"
                type="date"
                class="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900"
              />
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <button
              @click="approvingSubmission = null"
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Odustani
            </button>
            <button
              @click="confirmApprove"
              :disabled="!approveForm.title || !approveForm.base_price"
              class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Odobri i kreiraj
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Reject Modal -->
    <Teleport to="body">
      <div
        v-if="rejectingSubmission"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="rejectingSubmission = null"
      >
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Odbij prijavu</h3>
          <p class="text-sm text-gray-600 mb-4">Unesite razlog odbijanja (opcionalno):</p>
          <textarea
            v-model="rejectionReason"
            class="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none text-gray-900"
            rows="3"
            placeholder="Razlog odbijanja..."
          ></textarea>
          <div class="flex gap-3 mt-4">
            <button
              @click="rejectingSubmission = null"
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Odustani
            </button>
            <button
              @click="confirmReject"
              class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Odbij
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'admin'
})

const { get, post } = useApi()

interface Submission {
  id: number
  user_id: string
  business_id: number
  business_name: string
  image_url: string
  status: string
  user_email?: string
  user_name?: string
  extracted_title?: string
  extracted_old_price?: number
  extracted_new_price?: number
  extracted_valid_until?: string
  created_at: string
}

const submissions = ref<Submission[]>([])
const isLoading = ref(true)
const statusFilter = ref<string | null>(null)
const currentPage = ref(1)
const totalPages = ref(1)
const total = ref(0)

const stats = ref({
  total: 0,
  pending: 0,
  processing: 0,
  approved: 0,
  rejected: 0
})

// View/Process modal
const viewingSubmission = ref<Submission | null>(null)
const isProcessingAI = ref(false)
const aiProcessError = ref('')
const extractedData = ref<any>(null)
const editableData = ref({
  title: '',
  base_price: null as number | null,
  discount_price: null as number | null,
  expires: ''
})

// Approve modal (standalone)
const approvingSubmission = ref<Submission | null>(null)
const approveForm = ref({
  title: '',
  base_price: '',
  discount_price: '',
  expires: ''
})

// Reject modal
const rejectingSubmission = ref<Submission | null>(null)
const rejectionReason = ref('')

// Fetch submissions
async function fetchSubmissions() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', currentPage.value.toString())
    params.append('per_page', '20')
    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }

    const response = await get(`/api/admin/submissions?${params.toString()}`)
    submissions.value = response.submissions || []
    totalPages.value = response.pages || 1
    total.value = response.total || 0
  } catch (error) {
    console.error('Error fetching submissions:', error)
  } finally {
    isLoading.value = false
  }
}

// Fetch stats
async function fetchStats() {
  try {
    const [pendingRes, processingRes, approvedRes, rejectedRes] = await Promise.all([
      get('/api/admin/submissions?status=pending&per_page=1'),
      get('/api/admin/submissions?status=processing&per_page=1'),
      get('/api/admin/submissions?status=approved&per_page=1'),
      get('/api/admin/submissions?status=rejected&per_page=1')
    ])

    stats.value = {
      total: (pendingRes.total || 0) + (processingRes.total || 0) + (approvedRes.total || 0) + (rejectedRes.total || 0),
      pending: pendingRes.total || 0,
      processing: processingRes.total || 0,
      approved: approvedRes.total || 0,
      rejected: rejectedRes.total || 0
    }
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

function setFilter(status: string | null) {
  statusFilter.value = status
  currentPage.value = 1
  fetchSubmissions()
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchSubmissions()
  }
}

function getStatusClass(status: string) {
  switch (status) {
    case 'pending': return 'bg-yellow-100 text-yellow-800'
    case 'processing': return 'bg-blue-100 text-blue-800'
    case 'approved': return 'bg-green-100 text-green-800'
    case 'rejected': return 'bg-red-100 text-red-800'
    case 'duplicate': return 'bg-orange-100 text-orange-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'pending': return 'Na cekanju'
    case 'processing': return 'U obradi'
    case 'approved': return 'Odobreno'
    case 'rejected': return 'Odbijeno'
    case 'duplicate': return 'Duplikat'
    default: return status
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('bs-BA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// View Modal
function openViewModal(submission: Submission) {
  viewingSubmission.value = submission
  extractedData.value = null
  aiProcessError.value = ''

  // Pre-fill with existing extracted data if any
  editableData.value = {
    title: submission.extracted_title || '',
    base_price: submission.extracted_old_price || null,
    discount_price: submission.extracted_new_price || null,
    expires: submission.extracted_valid_until || ''
  }
}

async function processWithAI() {
  if (!viewingSubmission.value) return

  isProcessingAI.value = true
  aiProcessError.value = ''

  try {
    const response = await post(`/api/admin/submissions/${viewingSubmission.value.id}/process`, {})

    if (response.extracted_data) {
      extractedData.value = response.extracted_data

      // Update editable fields with AI results
      editableData.value = {
        title: response.extracted_data.title || editableData.value.title,
        base_price: response.extracted_data.base_price || editableData.value.base_price,
        discount_price: response.extracted_data.discount_price || editableData.value.discount_price,
        expires: response.extracted_data.expires || editableData.value.expires
      }

      // Update the submission in the list
      if (response.submission) {
        const idx = submissions.value.findIndex(s => s.id === viewingSubmission.value?.id)
        if (idx !== -1) {
          submissions.value[idx] = { ...submissions.value[idx], ...response.submission }
        }
        viewingSubmission.value = { ...viewingSubmission.value, ...response.submission }
      }
    }
  } catch (error: any) {
    console.error('Error processing with AI:', error)
    aiProcessError.value = error.response?.data?.error || 'Greska pri AI obradi'
  } finally {
    isProcessingAI.value = false
  }
}

function openRejectFromView() {
  if (!viewingSubmission.value) return
  rejectingSubmission.value = viewingSubmission.value
  rejectionReason.value = ''
  viewingSubmission.value = null
}

async function approveFromView() {
  if (!viewingSubmission.value) return
  if (!editableData.value.title || !editableData.value.base_price) return

  try {
    await post(`/api/admin/submissions/${viewingSubmission.value.id}/approve`, {
      title: editableData.value.title,
      base_price: parseFloat(String(editableData.value.base_price)),
      discount_price: editableData.value.discount_price ? parseFloat(String(editableData.value.discount_price)) : null,
      expires: editableData.value.expires || null
    })

    viewingSubmission.value = null
    fetchSubmissions()
    fetchStats()
  } catch (error: any) {
    console.error('Error approving submission:', error)
    alert('Greska pri odobravanju: ' + (error.response?.data?.error || 'Unknown error'))
  }
}

// Approve Modal (standalone)
function openApproveModal(submission: Submission) {
  approvingSubmission.value = submission
  approveForm.value = {
    title: submission.extracted_title || '',
    base_price: submission.extracted_old_price?.toString() || '',
    discount_price: submission.extracted_new_price?.toString() || '',
    expires: submission.extracted_valid_until || ''
  }
}

async function confirmApprove() {
  if (!approvingSubmission.value) return
  if (!approveForm.value.title || !approveForm.value.base_price) return

  try {
    await post(`/api/admin/submissions/${approvingSubmission.value.id}/approve`, {
      title: approveForm.value.title,
      base_price: parseFloat(approveForm.value.base_price),
      discount_price: approveForm.value.discount_price ? parseFloat(approveForm.value.discount_price) : null,
      expires: approveForm.value.expires || null
    })
    approvingSubmission.value = null
    fetchSubmissions()
    fetchStats()
  } catch (error: any) {
    console.error('Error approving submission:', error)
    alert('Greska pri odobravanju: ' + (error.response?.data?.error || 'Unknown error'))
  }
}

// Reject Modal
function openRejectModal(submission: Submission) {
  rejectingSubmission.value = submission
  rejectionReason.value = ''
}

async function confirmReject() {
  if (!rejectingSubmission.value) return

  try {
    await post(`/api/admin/submissions/${rejectingSubmission.value.id}/reject`, {
      reason: rejectionReason.value || null
    })
    rejectingSubmission.value = null
    fetchSubmissions()
    fetchStats()
  } catch (error: any) {
    console.error('Error rejecting submission:', error)
    alert('Greska pri odbijanju')
  }
}

onMounted(() => {
  fetchSubmissions()
  fetchStats()
})
</script>
