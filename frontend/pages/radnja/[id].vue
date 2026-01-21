<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center min-h-screen p-4">
      <div class="text-6xl mb-4">:(</div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">Radnja nije pronađena</h1>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <NuxtLink to="/" class="text-purple-600 hover:text-purple-800">
        ← Nazad na početnu
      </NuxtLink>
    </div>

    <!-- Business Page -->
    <div v-else-if="business">
      <!-- Full Width Map Section -->
      <div class="relative h-56 md:h-80 w-full">
        <!-- Leaflet Map Container -->
        <div
          v-if="hasLocations"
          ref="mapContainer"
          class="w-full h-full z-0 bg-gray-200"
        ></div>
        <!-- Fallback gradient if no locations -->
        <div
          v-else
          class="w-full h-full bg-gradient-to-r from-purple-600 to-blue-600"
        >
          <img
            v-if="business.cover_image_path"
            :src="getImageUrl(business.cover_image_path)"
            :alt="business.name"
            class="w-full h-full object-cover"
          />
        </div>
      </div>

      <!-- Content Container -->
      <div class="max-w-7xl mx-auto pb-8">
        <!-- Profile Section (Facebook-style: logo overlapping cover) -->
        <div class="bg-white shadow-sm relative mx-4 md:mx-6 rounded-b-lg -mt-10 pt-0 pb-4 px-5">
        <!-- Logo + Name Row -->
        <div class="flex items-end gap-4">
          <!-- Logo (overlapping the cover) -->
          <div class="flex-shrink-0 -mt-8">
            <div class="w-24 h-24 md:w-32 md:h-32 rounded-xl bg-white shadow-lg border-4 border-white overflow-hidden">
              <img
                v-if="business.logo_path"
                :src="getImageUrl(business.logo_path)"
                :alt="business.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full bg-gray-200 flex items-center justify-center">
                <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Business Name + Rating -->
          <div class="flex-1 pt-14 md:pt-16">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h1 class="text-2xl md:text-3xl font-bold text-gray-900">{{ business.name }}</h1>
              <!-- Rating Display -->
              <div v-if="business.average_rating > 0" class="flex items-center gap-1 bg-amber-50 px-3 py-1 rounded-full">
                <svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <span class="font-bold text-amber-700">{{ business.average_rating.toFixed(1) }}</span>
                <span class="text-amber-600 text-sm">({{ business.total_reviews }})</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats Row -->
        <div class="flex flex-wrap items-center gap-4 mt-4 text-sm">
          <!-- Total Products -->
          <div class="flex items-center gap-1.5 text-gray-600">
            <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <span><strong class="text-gray-800">{{ totalProductsCount }}</strong> proizvoda</span>
          </div>

          <!-- On Discount -->
          <div class="flex items-center gap-1.5 text-gray-600">
            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <span><strong class="text-gray-800">{{ discountedProductsCount }}</strong> na popustu</span>
          </div>

          <!-- Expiry Countdown/Days -->
          <div v-if="soonestExpiry && daysUntilExpiry !== null && daysUntilExpiry > 0" class="flex items-center gap-1.5">
            <!-- Within 24 hours - show countdown -->
            <template v-if="isWithin24Hours">
              <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-red-600 font-medium">Ističe za <strong class="font-mono">{{ countdownText }}</strong></span>
            </template>
            <!-- More than 24 hours - show days -->
            <template v-else>
              <svg class="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span class="text-gray-600">Popust ističe za <strong class="text-gray-800">{{ daysUntilExpiry }}</strong> {{ daysUntilExpiry === 1 ? 'dan' : 'dana' }}</span>
            </template>
          </div>
        </div>

        <!-- Description -->
        <p v-if="business.description" class="text-gray-600 mt-4">{{ business.description }}</p>

        <!-- Social Media Links -->
        <div v-if="hasSocialLinks" class="flex flex-wrap gap-3 mt-4">
              <a v-if="business.website_url" :href="business.website_url" target="_blank" rel="noopener noreferrer"
                 class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-gray-700">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                <span class="text-sm">Web</span>
              </a>
              <a v-if="business.facebook_url" :href="business.facebook_url" target="_blank" rel="noopener noreferrer"
                 class="flex items-center gap-2 px-3 py-2 bg-blue-100 rounded-lg hover:bg-blue-200 transition-colors text-blue-700">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                <span class="text-sm">Facebook</span>
              </a>
              <a v-if="business.instagram_url" :href="business.instagram_url" target="_blank" rel="noopener noreferrer"
                 class="flex items-center gap-2 px-3 py-2 bg-pink-100 rounded-lg hover:bg-pink-200 transition-colors text-pink-700">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
                <span class="text-sm">Instagram</span>
              </a>
              <a v-if="business.viber_contact" :href="'viber://chat?number=' + business.viber_contact.replace(/[^0-9]/g, '')"
                 class="flex items-center gap-2 px-3 py-2 bg-purple-100 rounded-lg hover:bg-purple-200 transition-colors text-purple-700">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M11.398.002C9.473.028 5.331.344 3.014 2.467 1.294 4.182.518 6.793.39 10.061c-.128 3.268-.298 9.395 5.754 11.103l.007.003v2.563s-.038.976.606 1.173c.779.239 1.236-.502 1.981-1.304.407-.439.971-1.081 1.396-1.573 3.846.322 6.806-.416 7.142-.528.773-.258 5.145-.811 5.856-6.619.733-5.988-.353-9.772-2.293-11.47l-.001-.001c-.559-.508-2.773-2.157-8.093-2.38-.213-.009-.429-.013-.647-.012l.3-.016zM11.431 1.4h.547c4.721.205 6.678 1.632 7.13 2.043l.003.002c1.658 1.452 2.539 4.87 1.891 10.161-.596 4.869-4.212 5.271-4.869 5.491-.277.092-2.915.748-6.212.54 0 0-2.464 2.97-3.232 3.742-.12.12-.26.167-.354.145-.132-.031-.169-.182-.166-.401l.02-4.06-.007-.004c-5.125-1.448-4.82-6.625-4.712-9.378.108-2.753.756-5.006 2.213-6.453 1.932-1.773 5.362-2.058 7.748-1.828zm.162 2.315v.006c-.032 0-.063.003-.094.006-.695.046-1.301.156-1.878.368a5.15 5.15 0 00-1.566.891c-.87.723-1.373 1.618-1.486 2.692-.08.762.089 1.481.477 2.147.34.585.825 1.059 1.418 1.45.065.043.063.088.058.156l-.24 1.538c-.044.28.083.395.337.259l1.69-.908c.086-.047.161-.07.253-.063.312.024.623.07.932.107.088.01.148-.006.207-.077.585-.695 1.174-1.386 1.758-2.082.083-.099.089-.163.012-.26-.499-.628-.993-1.26-1.49-1.89-.062-.078-.071-.137-.004-.22.566-.69 1.128-1.386 1.691-2.079.066-.081.054-.123-.036-.17-.556-.287-1.133-.516-1.751-.626-.305-.054-.615-.082-.91-.116-.125-.015-.25-.023-.376-.028l-.002-.001zm-.07.868c.246.003.497.028.755.067.511.078 1.001.26 1.472.504l.014.007c.07.037.074.05.026.109-.528.648-1.057 1.296-1.585 1.944-.07.086-.067.135.005.21.467.594.935 1.188 1.399 1.784.052.067.053.109-.01.168-.547.65-1.094 1.301-1.641 1.951-.057.067-.1.08-.173.041a4.46 4.46 0 01-.779-.358c-.524-.306-.962-.705-1.254-1.248-.242-.45-.365-.925-.306-1.435.082-.708.446-1.276 1.003-1.739a3.835 3.835 0 011.184-.675 4.7 4.7 0 011.89-.33zm3.358 1.418c.088 0 .176.007.263.022.505.088.938.31 1.31.643.447.401.717.9.86 1.47.098.39.119.786.086 1.186-.043.528-.212 1.019-.494 1.471-.34.545-.794.98-1.354 1.302-.24.138-.5.235-.767.31a3.18 3.18 0 01-.795.099c-.043-.001-.087-.002-.128-.005-.084-.006-.11-.033-.107-.118.02-.595.039-1.19.059-1.785.002-.058.02-.089.077-.104.38-.101.716-.275 1-.527.337-.299.552-.671.609-1.115.053-.408-.018-.796-.221-1.154-.186-.328-.456-.576-.786-.757-.17-.094-.352-.157-.544-.189a1.46 1.46 0 00-.313-.018c-.076.004-.1-.019-.105-.094a11.17 11.17 0 01-.066-.857c-.007-.115.03-.156.145-.168.089-.009.18-.015.27-.016l.001.004zm-3.183.578c.043 0 .087.003.13.007.348.035.67.149.958.34.413.275.678.654.785 1.14.068.307.055.614-.04.916a1.84 1.84 0 01-.59.89c-.256.216-.557.355-.882.444-.067.018-.088.054-.086.12.012.388.02.775.03 1.163.002.058-.015.084-.073.096-.465.097-.893.06-1.297-.157a1.878 1.878 0 01-.754-.74 1.67 1.67 0 01-.199-.912c.03-.406.18-.765.442-1.077.258-.308.584-.528.953-.686.32-.137.658-.22 1.006-.257.076-.008.153-.012.23-.013l.387.026zm-.07.846a2.127 2.127 0 00-.765.288c-.244.145-.438.338-.554.594-.097.213-.123.437-.087.667.05.319.205.582.452.791.193.163.418.275.663.346.052.015.075.044.073.1-.011.324-.02.648-.029.971-.001.042-.012.064-.055.074-.371.083-.724.055-1.058-.124-.25-.134-.438-.332-.553-.592-.124-.28-.147-.571-.078-.867.068-.292.217-.544.429-.756.261-.26.574-.435.922-.545.2-.064.408-.098.621-.109l.019.162zm2.64.003l.018-.161c.276.017.543.074.796.178.356.147.641.376.857.68.18.253.285.537.314.846.033.352-.037.686-.206.998-.155.287-.375.522-.647.702-.103.068-.154.057-.21-.054-.112-.223-.256-.425-.426-.607-.074-.08-.088-.145-.04-.247.107-.229.156-.471.123-.725-.038-.298-.159-.556-.364-.774a1.54 1.54 0 00-.736-.457c-.111-.032-.227-.051-.345-.056-.078-.003-.107-.029-.109-.108-.007-.208-.017-.416-.025-.625v-.59z"/>
                </svg>
                <span class="text-sm">Viber</span>
              </a>
              <a v-if="business.contact_email" :href="'mailto:' + business.contact_email"
                 class="flex items-center gap-2 px-3 py-2 bg-red-100 rounded-lg hover:bg-red-200 transition-colors text-red-700">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span class="text-sm">Email</span>
              </a>
            </div>

        <!-- Google Maps Link -->
        <div v-if="business.google_link" class="mt-4">
          <a :href="business.google_link" target="_blank" rel="noopener noreferrer"
             class="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            Pogledaj na Google Maps
          </a>
        </div>
      </div>

      <!-- Featured Products Section -->
      <div v-if="featuredProducts.length > 0" class="mx-4 mt-6">
        <div class="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg p-6">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-6 h-6 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <h2 class="text-xl font-bold text-gray-900">Istaknuti proizvodi</h2>
          </div>
          <!-- Mobile: horizontal scroll carousel, Desktop: 4-column grid -->
          <div class="flex md:grid md:grid-cols-4 gap-4 overflow-x-auto md:overflow-visible pb-2 md:pb-0 snap-x snap-mandatory md:snap-none -mx-2 px-2 md:mx-0 md:px-0">
            <div v-for="product in featuredProducts.slice(0, 4)" :key="product.id" class="flex-shrink-0 w-[70vw] sm:w-[45vw] md:w-auto snap-start">
              <ProductCard :product="product" />
            </div>
          </div>
        </div>
      </div>

      <!-- Products Section -->
      <div id="products-section" ref="productsSection" class="mx-4 mt-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <h2 class="text-xl font-bold text-gray-900">
            Svi proizvodi
            <span v-if="business.product_count" class="text-gray-500 font-normal text-base">({{ business.product_count }})</span>
          </h2>

          <!-- Filters Row -->
          <div class="flex flex-wrap gap-2">
            <!-- Category Filter -->
            <select
              v-if="business.categories && business.categories.length > 0"
              v-model="selectedCategory"
              @change="onFilterChange"
              class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="">Sve kategorije</option>
              <option v-for="cat in business.categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>

            <!-- Sort Dropdown -->
            <select
              v-model="sortBy"
              @change="onFilterChange"
              class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="discount">Najveći popust</option>
              <option value="price_asc">Cijena: niska → visoka</option>
              <option value="price_desc">Cijena: visoka → niska</option>
              <option value="name">Naziv A-Z</option>
            </select>
          </div>
        </div>

        <!-- Search -->
        <div class="mb-4">
          <div class="relative">
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text"
              placeholder="Pretraži proizvode..."
              class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900 bg-white"
            />
            <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <!-- Active Filters -->
        <div v-if="selectedCategory" class="mb-4 flex flex-wrap gap-2">
          <span class="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
            {{ selectedCategory }}
            <button @click="clearCategory" class="hover:text-purple-900">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </span>
        </div>

        <!-- Loading Products -->
        <div v-if="loadingProducts" class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>

        <!-- Products Grid - full width on mobile, then 2-4 columns on larger screens -->
        <div v-else-if="products.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          <ProductCard v-for="product in products" :key="product.id" :product="product" />
        </div>

        <!-- No Products -->
        <div v-else class="bg-white rounded-lg shadow-sm p-8 text-center">
          <p class="text-gray-600">Nema proizvoda za prikaz</p>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1 && !loadingProducts" class="flex flex-col items-center space-y-3 mt-6">
          <div class="flex justify-center items-center space-x-2">
            <button
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
              class="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Prije
            </button>

            <div class="flex space-x-1">
              <template v-for="(page, index) in visiblePages" :key="index">
                <!-- Ellipsis (not clickable) -->
                <span
                  v-if="page === '...'"
                  class="px-2 py-2 text-gray-500"
                >
                  ...
                </span>
                <!-- Page number button -->
                <button
                  v-else
                  @click="goToPage(page as number)"
                  :class="[
                    'px-3 py-2 border rounded-md text-sm',
                    page === currentPage
                      ? 'bg-purple-600 text-white border-purple-600'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  ]"
                >
                  {{ page }}
                </button>
              </template>
            </div>

            <button
              :disabled="currentPage === totalPages"
              @click="goToPage(currentPage + 1)"
              class="px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Dalje
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

const loading = ref(true)
const error = ref('')
const business = ref<any>(null)
const products = ref<any[]>([])
const featuredProducts = ref<any[]>([])
const loadingProducts = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const mapContainer = ref<HTMLElement | null>(null)
const productsSection = ref<HTMLElement | null>(null)
const selectedCategory = ref('')
const sortBy = ref('discount')
let mapInstance: any = null

// Stats
const totalProductsCount = ref(0)
const discountedProductsCount = ref(0)
const soonestExpiry = ref<Date | null>(null)
const countdownText = ref('')
let countdownInterval: any = null

// Check if we have locations with valid coordinates
const hasLocations = computed(() => {
  if (!business.value?.locations || business.value.locations.length === 0) return false
  // Check if at least one location has valid lat/lng
  return business.value.locations.some((loc: any) => loc.latitude && loc.longitude)
})

// Smart pagination with ellipsis (like /proizvodi page)
const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 5) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)
    if (current > 3) {
      pages.push('...')
    }
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    if (current < total - 2) {
      pages.push('...')
    }
    pages.push(total)
  }
  return pages
})

// Check if business has any social links
const hasSocialLinks = computed(() => {
  if (!business.value) return false
  return business.value.website_url ||
         business.value.facebook_url ||
         business.value.instagram_url ||
         business.value.viber_contact ||
         business.value.contact_email
})

// Computed: days until soonest expiry (for display when > 24 hours)
const daysUntilExpiry = computed(() => {
  if (!soonestExpiry.value) return null
  const now = new Date()
  const diff = soonestExpiry.value.getTime() - now.getTime()
  if (diff <= 0) return 0
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
})

// Check if within 24 hours (show countdown)
const isWithin24Hours = computed(() => {
  if (!soonestExpiry.value) return false
  const now = new Date()
  const diff = soonestExpiry.value.getTime() - now.getTime()
  return diff > 0 && diff <= 24 * 60 * 60 * 1000
})

// Update countdown text
function updateCountdown() {
  if (!soonestExpiry.value) {
    countdownText.value = ''
    return
  }

  const now = new Date()
  const diff = soonestExpiry.value.getTime() - now.getTime()

  if (diff <= 0) {
    countdownText.value = 'Isteklo'
    return
  }

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  countdownText.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// Start countdown timer
function startCountdown() {
  if (countdownInterval) clearInterval(countdownInterval)
  updateCountdown()
  countdownInterval = setInterval(updateCountdown, 1000)
}

function getApiUrl() {
  return config.public.apiBase || 'http://localhost:5001'
}

function getImageUrl(path: string) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  // S3 paths (popust/, assets/, etc.) go to S3
  if (path.startsWith('popust/') || path.startsWith('assets/')) {
    return `https://aipijaca.s3.eu-central-1.amazonaws.com/${path}`
  }
  // Local paths go to API server
  if (path.startsWith('/static/') || path.startsWith('uploads/')) {
    return `${getApiUrl()}${path.startsWith('/') ? '' : '/static/'}${path}`
  }
  // Default to S3 for unknown paths
  return `https://aipijaca.s3.eu-central-1.amazonaws.com/${path}`
}

function getToken() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token')
  }
  return null
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

function clearCategory() {
  selectedCategory.value = ''
  onFilterChange()
}

function onFilterChange() {
  currentPage.value = 1
  fetchProducts()
}

// Load Leaflet dynamically
async function loadLeaflet(): Promise<any> {
  if (typeof window === 'undefined') return null

  // Check if already loaded
  if ((window as any).L) return (window as any).L

  return new Promise((resolve) => {
    // Load CSS
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link)
    }

    // Load JS
    const existingScript = document.querySelector('script[src*="leaflet"]')
    if (existingScript) {
      const checkLoaded = setInterval(() => {
        if ((window as any).L) {
          clearInterval(checkLoaded)
          resolve((window as any).L)
        }
      }, 100)
      return
    }

    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = () => resolve((window as any).L)
    script.onerror = () => resolve(null)
    document.head.appendChild(script)
  })
}

// Initialize Leaflet map with all locations
async function initMap() {
  try {
    if (!hasLocations.value || !mapContainer.value) return

    const L = await loadLeaflet()
    if (!L) return

    const locations = business.value.locations.filter((loc: any) => loc.latitude && loc.longitude)
    if (locations.length === 0) return

    // Ensure container has dimensions
    const container = mapContainer.value
    if (container.clientWidth === 0 || container.clientHeight === 0) {
      await new Promise(resolve => setTimeout(resolve, 300))
    }

    // Calculate center from all locations
    const lats = locations.map((loc: any) => loc.latitude)
    const lngs = locations.map((loc: any) => loc.longitude)
    const centerLat = lats.reduce((a: number, b: number) => a + b, 0) / lats.length
    const centerLng = lngs.reduce((a: number, b: number) => a + b, 0) / lngs.length

    // Create map
    mapInstance = L.map(container, {
      zoomControl: true,
      attributionControl: false
    }).setView([centerLat, centerLng], 15)

    // Add OpenStreetMap tiles (standard map style)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19
    }).addTo(mapInstance)

    // Add markers for each location
    const markers: any[] = []
    locations.forEach((loc: any) => {
      const marker = L.marker([loc.latitude, loc.longitude]).addTo(mapInstance)

      // Add popup with location details
      const popupContent = `
        <div style="min-width: 150px;">
          <strong style="color: #1f2937;">${loc.name || business.value.name}</strong>
          ${loc.address ? `<br><span style="color: #6b7280; font-size: 13px;">${loc.address}</span>` : ''}
          ${loc.city ? `<br><span style="color: #6b7280; font-size: 13px;">${loc.city}</span>` : ''}
        </div>
      `
      marker.bindPopup(popupContent)
      markers.push(marker)
    })

    // Fit bounds if multiple locations
    if (markers.length > 1) {
      const group = L.featureGroup(markers)
      mapInstance.fitBounds(group.getBounds().pad(0.1))
    }

  } catch (err) {
    console.error('Error initializing Leaflet map:', err)
  }
}

async function fetchBusiness() {
  try {
    const businessId = route.params.id as string
    const token = getToken()

    if (!token) {
      error.value = 'Morate biti prijavljeni da vidite ovu stranicu'
      loading.value = false
      return
    }

    const response = await fetch(`${getApiUrl()}/api/radnja/${businessId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()

    if (!response.ok) {
      error.value = data.error || 'Radnja nije pronađena'
      return
    }

    business.value = data.business
    featuredProducts.value = data.featured_products || []
    products.value = data.products || []

    // Calculate total pages from total_products
    const totalProducts = data.total_products || 0
    totalPages.value = Math.max(1, Math.ceil(totalProducts / 28))

    // Set stats - use business.product_count which includes all products (featured + regular)
    totalProductsCount.value = data.business?.product_count || totalProducts
    discountedProductsCount.value = data.discounted_products_count || data.business?.discounted_products_count || totalProductsCount.value

    // Find soonest expiry date from all products (featured + regular)
    const allProducts = [...(data.featured_products || []), ...(data.products || [])]
    let soonestDate: Date | null = null

    allProducts.forEach((product: any) => {
      const expiryField = product.expires || product.discount_valid_until || product.discount_end_date || product.valid_until
      if (expiryField) {
        const expiry = new Date(expiryField)
        // Only consider future dates
        if (expiry > new Date() && (!soonestDate || expiry < soonestDate)) {
          soonestDate = expiry
        }
      }
    })

    // Also check business-level soonest_expiry if provided
    if (data.business?.soonest_expiry || data.soonest_expiry) {
      const businessExpiry = new Date(data.business?.soonest_expiry || data.soonest_expiry)
      if (!soonestDate || businessExpiry < soonestDate) {
        soonestDate = businessExpiry
      }
    }

    soonestExpiry.value = soonestDate

    // Start countdown if within 24 hours
    if (soonestDate) {
      startCountdown()
    }

    // Initialize map after data is loaded
    await nextTick()
    initMap()
  } catch (e) {
    error.value = 'Greška pri učitavanju radnje'
  } finally {
    loading.value = false
  }
}

async function fetchProducts() {
  loadingProducts.value = true
  try {
    const businessId = route.params.id as string
    const token = getToken()
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      per_page: '28',
      exclude_featured: 'true',
      sort: sortBy.value,
      ...(searchQuery.value && { search: searchQuery.value }),
      ...(selectedCategory.value && { category: selectedCategory.value })
    })

    const response = await fetch(`${getApiUrl()}/api/radnja/${businessId}/products?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      products.value = data.products || []
      totalPages.value = data.pages || 1
    }
  } catch (e) {
    console.error('Error fetching products:', e)
  } finally {
    loadingProducts.value = false
  }
}

let searchTimeout: any = null
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchProducts()
  }, 300)
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchProducts()
    // Scroll to products section
    nextTick(() => {
      if (productsSection.value) {
        productsSection.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    })
  }
}

onMounted(async () => {
  await fetchBusiness()
})

// Watch for mapContainer to become available
watch(mapContainer, (newContainer) => {
  if (newContainer && hasLocations.value && !mapInstance) {
    initMap()
  }
})

onUnmounted(() => {
  // Clean up Leaflet map instance
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
  // Clean up countdown interval
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
})

// SEO
useSeoMeta({
  title: () => business.value ? `${business.value.name} - Popust.ba` : 'Radnja - Popust.ba',
  description: () => business.value?.description || 'Pogledajte proizvode i popuste ove radnje',
})
</script>
