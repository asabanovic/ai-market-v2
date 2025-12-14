<template>
  <div class="category-selector">
    <!-- Left arrow button (mobile) -->
    <button
      v-if="showLeftGradient"
      @click="scrollLeft"
      class="md:hidden absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white/90 shadow-md rounded-full p-1.5 text-gray-600 hover:bg-gray-100 active:bg-gray-200"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>

    <!-- Right arrow button (mobile) -->
    <button
      v-if="showRightGradient"
      @click="scrollRight"
      class="md:hidden absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-white/90 shadow-md rounded-full p-1.5 text-gray-600 hover:bg-gray-100 active:bg-gray-200"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>

    <!-- Scroll hint gradient on left -->
    <div
      v-if="showLeftGradient"
      class="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none"
    ></div>

    <!-- Scroll hint gradient on right -->
    <div
      v-if="showRightGradient"
      class="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none"
    ></div>

    <div
      ref="scrollContainer"
      class="flex gap-2 overflow-x-auto pb-2 scrollbar-hide px-6 md:px-1"
      @scroll="updateGradients"
    >
      <!-- All categories button -->
      <button
        @click="selectCategory(null)"
        :disabled="disabled"
        :class="[
          'flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 min-w-[72px]',
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : '',
          selectedCategory === null
            ? 'bg-purple-600 text-white shadow-md'
            : disabled
              ? 'bg-gray-100 text-gray-400'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        <span class="text-xl">🏪</span>
        <span class="text-xs font-medium whitespace-nowrap">Sve</span>
      </button>

      <!-- Category buttons -->
      <button
        v-for="category in categories"
        :key="category.id"
        @click="selectCategory(category.id)"
        :disabled="disabled"
        :class="[
          'flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 min-w-[72px]',
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : '',
          selectedCategory === category.id
            ? 'bg-purple-600 text-white shadow-md'
            : disabled
              ? 'bg-gray-100 text-gray-400'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        <span class="text-xl">{{ category.icon }}</span>
        <span class="text-xs font-medium whitespace-nowrap">{{ category.name }}</span>
        <span
          v-if="category.count"
          :class="[
            'text-[10px] px-1.5 rounded-full',
            selectedCategory === category.id
              ? 'bg-purple-500 text-purple-100'
              : 'bg-gray-200 text-gray-600'
          ]"
        >
          {{ category.count }}
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Category {
  id: string
  name: string
  icon: string
  count?: number
}

const props = defineProps<{
  modelValue: string | null
  categoryCounts?: Record<string, number>
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

const scrollContainer = ref<HTMLElement | null>(null)
const showLeftGradient = ref(false)
const showRightGradient = ref(true)

// Hardcoded categories with icons
const baseCategories: Omit<Category, 'count'>[] = [
  { id: 'meso', name: 'Meso', icon: '🥩' },
  { id: 'mlijeko', name: 'Mlijeko', icon: '🥛' },
  { id: 'pica', name: 'Pića', icon: '🥤' },
  { id: 'voce_povrce', name: 'Voće/Povrće', icon: '🥬' },
  { id: 'kuhinja', name: 'Za kuhinju', icon: '🍳' },
  { id: 'ves', name: 'Za veš', icon: '🧺' },
  { id: 'ciscenje', name: 'Čišćenje', icon: '🧹' },
  { id: 'higijena', name: 'Higijena', icon: '🧴' },
  { id: 'slatkisi', name: 'Slatkiši', icon: '🍫' },
  { id: 'kafa', name: 'Kafa/Čaj', icon: '☕' },
  { id: 'smrznuto', name: 'Smrznuto', icon: '🧊' },
  { id: 'pekara', name: 'Pekara', icon: '🥖' },
  { id: 'ljubimci', name: 'Ljubimci', icon: '🐕' },
  { id: 'bebe', name: 'Za bebe', icon: '👶' },
]

const categories = computed<Category[]>(() => {
  return baseCategories.map(cat => ({
    ...cat,
    count: props.categoryCounts?.[cat.id] || 0
  })).filter(cat => !props.categoryCounts || cat.count > 0)
})

const selectedCategory = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function selectCategory(categoryId: string | null) {
  if (props.disabled) return
  selectedCategory.value = categoryId
}

function updateGradients() {
  if (!scrollContainer.value) return

  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
  showLeftGradient.value = scrollLeft > 10
  showRightGradient.value = scrollLeft < scrollWidth - clientWidth - 10
}

function scrollLeft() {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({ left: -150, behavior: 'smooth' })
}

function scrollRight() {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({ left: 150, behavior: 'smooth' })
}

onMounted(() => {
  updateGradients()
  // Check gradients after render
  nextTick(updateGradients)
})
</script>

<style scoped>
.category-selector {
  position: relative;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
