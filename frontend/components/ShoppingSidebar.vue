<template>
  <!-- Overlay -->
  <Transition name="fade">
    <div
      v-if="isOpen"
      @click="$emit('close')"
      class="fixed inset-0 bg-black/50 z-40"
    ></div>
  </Transition>

  <!-- Sidebar -->
  <Transition name="slide">
    <div
      v-if="isOpen"
      class="fixed top-0 right-0 h-full w-full max-w-md bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col"
    >
      <!-- Header -->
      <div class="px-4 py-3 border-b dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-bold text-gray-900 dark:text-white">
                {{ todoMode ? 'TODO Lista' : 'Vaša Lista' }}
              </h2>
              <!-- TODO Mode Toggle -->
              <button
                v-if="!todoMode"
                @click="enableTodoMode"
                class="p-1.5 rounded-lg bg-green-100 hover:bg-green-200 text-green-700 transition-colors"
                title="Aktiviraj TODO mode"
              >
                <Icon name="mdi:check-circle" class="w-5 h-5" />
              </button>
              <button
                v-else
                @click="disableTodoMode"
                class="p-1.5 rounded-lg bg-red-100 hover:bg-red-200 text-red-700 transition-colors"
                title="Zatvori TODO mode"
              >
                <Icon name="mdi:close-circle" class="w-5 h-5" />
              </button>
            </div>
            <!-- Enhanced countdown with urgency indicators (green theme) -->
            <div v-if="cartStore.isActive && !todoMode" class="mt-1.5 flex items-center gap-1.5">
              <span class="text-xs text-gray-600 dark:text-gray-400">Ističe za: </span>
              <span
                :class="[
                  'text-sm font-mono font-bold',
                  isTimeCritical ? 'text-red-600 dark:text-red-400' : isTimeWarning ? 'text-orange-600 dark:text-orange-400' : 'text-green-600 dark:text-green-400'
                ]"
              >
                {{ cartStore.ttlFormatted }}
              </span>
            </div>
          </div>
          <button
            @click="$emit('close')"
            class="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <Icon name="mdi:close" class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-3 py-2">
        <!-- Loading State -->
        <div v-if="cartStore.loading" class="flex items-center justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="!cartStore.sidebar || cartStore.sidebar.groups.length === 0"
          class="flex flex-col items-center justify-center py-8 text-center"
        >
          <Icon name="mdi:cart" class="w-12 h-12 text-gray-400 mb-3" />
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1">
            Lista je prazna
          </h3>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Dodajte proizvode u listu za kupovinu
          </p>
        </div>

        <!-- Shopping List Groups -->
        <div v-else class="space-y-2">
          <!-- Group by Store (Sorted by spend) -->
          <div
            v-for="group in sortedGroups"
            :key="group.store.id"
            class="border dark:border-gray-700 rounded-md overflow-hidden"
          >
            <!-- Store Header (Collapsible) -->
            <button
              @click="toggleGroup(group.store.id)"
              class="w-full bg-gray-50 dark:bg-gray-800 px-2.5 py-2 flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <!-- Collapse Icon -->
              <Icon
                :name="expandedGroups.has(group.store.id) ? 'mdi:chevron-down' : 'mdi:chevron-up'"
                class="w-4 h-4 text-gray-600 dark:text-gray-400 transition-transform"
              />

              <!-- Store Logo -->
              <img
                v-if="group.store.logo"
                :src="group.store.logo"
                :alt="group.store.name"
                class="w-6 h-6 object-contain rounded"
              />

              <!-- Store Info -->
              <div class="flex-1 text-left">
                <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                  {{ group.store.name }}
                </h3>
                <div class="flex items-center gap-2 text-[10px] text-gray-600 dark:text-gray-400">
                  <span>{{ group.items.length }} {{ group.items.length === 1 ? 'artikal' : 'artikala' }}</span>
                  <span class="text-gray-400">•</span>
                  <span class="font-semibold text-gray-900 dark:text-white">{{ group.group_subtotal.toFixed(2) }} KM</span>
                  <span v-if="group.group_saving > 0 && !todoMode" class="text-green-600 dark:text-green-400">
                    -{{ group.group_saving.toFixed(2) }} KM
                  </span>
                </div>
              </div>
            </button>

            <!-- Items (Collapsible) -->
            <div v-if="expandedGroups.has(group.store.id)" class="divide-y dark:divide-gray-700">
              <div
                v-for="item in group.items"
                :key="item.item_id"
                :class="[
                  'p-2 transition-colors',
                  todoMode && checkedItems.has(item.item_id) ? 'bg-green-50 dark:bg-green-900/10' : ''
                ]"
              >
                <div class="flex items-center gap-2">
                  <!-- TODO Mode Checkbox -->
                  <button
                    v-if="todoMode"
                    @click="toggleCheck(item.item_id)"
                    class="flex-shrink-0"
                  >
                    <Icon
                      :name="checkedItems.has(item.item_id) ? 'mdi:check-circle' : 'mdi:circle'"
                      :class="[
                        'w-5 h-5 transition-colors',
                        checkedItems.has(item.item_id) ? 'text-green-600' : 'text-gray-300'
                      ]"
                    />
                  </button>

                  <!-- Item Info -->
                  <div class="flex-1 min-w-0">
                    <h4
                      :class="[
                        'text-xs font-medium truncate',
                        todoMode && checkedItems.has(item.item_id)
                          ? 'line-through text-gray-500 dark:text-gray-400'
                          : 'text-gray-900 dark:text-white'
                      ]"
                    >
                      {{ item.name }}
                    </h4>

                    <!-- Price -->
                    <div class="flex items-center gap-1.5 mt-0.5">
                      <span class="text-xs font-semibold text-gray-900 dark:text-white">
                        {{ item.unit_price.toFixed(2) }} KM
                      </span>
                      <span
                        v-if="item.old_price && !todoMode"
                        class="text-[10px] text-gray-500 dark:text-gray-400 line-through"
                      >
                        {{ item.old_price.toFixed(2) }} KM
                      </span>
                      <span
                        v-if="item.estimated_saving > 0 && !todoMode"
                        class="text-[10px] text-green-600 dark:text-green-400"
                      >
                        -{{ item.estimated_saving.toFixed(2) }} KM
                      </span>
                    </div>
                  </div>

                  <!-- Quantity Stepper (hidden in TODO mode) -->
                  <div v-if="!todoMode" class="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded px-1 py-0.5">
                    <button
                      @click="decrementQty(item)"
                      class="p-0.5 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                    >
                      <Icon name="mdi:minus" class="w-3 h-3" />
                    </button>
                    <span class="text-xs font-semibold text-gray-900 dark:text-white w-6 text-center">
                      {{ item.qty }}
                    </span>
                    <button
                      @click="incrementQty(item)"
                      class="p-0.5 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                    >
                      <Icon name="mdi:plus" class="w-3 h-3" />
                    </button>
                  </div>

                  <!-- Quantity display in TODO mode -->
                  <div v-else class="text-xs text-gray-600 dark:text-gray-400">
                    x{{ item.qty }}
                  </div>

                  <!-- Subtotal -->
                  <div class="text-right">
                    <p class="text-xs font-bold text-gray-900 dark:text-white">
                      {{ item.subtotal.toFixed(2) }} KM
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div
        v-if="cartStore.sidebar && cartStore.sidebar.groups.length > 0"
        class="border-t dark:border-gray-700 px-3 py-2"
      >
        <!-- Grand Totals -->
        <div class="space-y-1">
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-600 dark:text-gray-400">
              Ukupno artikala: {{ cartStore.sidebar.total_items }}
            </span>
          </div>
          <div
            v-if="cartStore.sidebar.grand_saving > 0 && !todoMode"
            class="flex items-center justify-between text-xs"
          >
            <span class="text-gray-600 dark:text-gray-400">Ukupna ušteda:</span>
            <span class="font-semibold text-green-600 dark:text-green-400">
              {{ cartStore.sidebar.grand_saving.toFixed(2) }} KM
            </span>
          </div>
          <div class="flex items-center justify-between text-base font-bold">
            <span class="text-gray-900 dark:text-white">UKUPNO:</span>
            <span class="text-primary-600 dark:text-primary-400">
              {{ cartStore.sidebar.grand_total.toFixed(2) }} KM
            </span>
          </div>

          <!-- TODO Mode Summary -->
          <div v-if="todoMode" class="pt-2 mt-2 border-t dark:border-gray-600">
            <div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
              <span>Označeno:</span>
              <span class="font-semibold">{{ checkedItems.size }} / {{ totalItems }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useCartStore } from '~/stores/cart'
import type { ShoppingListItem, ShoppingListGroup } from '~/stores/cart'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  'close': []
}>()

const cartStore = useCartStore()
const { handleApiError, showSuccess } = useCreditsToast()

// TODO Mode state
const todoMode = ref(false)
const checkedItems = ref<Set<number>>(new Set())

// Collapsible groups state (expanded by default)
const expandedGroups = ref<Set<number>>(new Set())

// Sort groups by amount spent (highest first)
const sortedGroups = computed(() => {
  if (!cartStore.sidebar?.groups) return []
  return [...cartStore.sidebar.groups].sort((a, b) => b.group_subtotal - a.group_subtotal)
})

// Time warning states
const isTimeCritical = computed(() => {
  return cartStore.ttlSeconds !== null && cartStore.ttlSeconds < 1800 // Less than 30 minutes
})

const isTimeWarning = computed(() => {
  return cartStore.ttlSeconds !== null && cartStore.ttlSeconds < 3600 && cartStore.ttlSeconds >= 1800 // Between 30min and 1 hour
})

// Total items count for TODO mode
const totalItems = computed(() => {
  if (!cartStore.sidebar?.groups) return 0
  return cartStore.sidebar.groups.reduce((sum, group) => sum + group.items.length, 0)
})

// TODO Mode functions
function enableTodoMode() {
  todoMode.value = true
  // Expand all groups in TODO mode for easier checking
  if (cartStore.sidebar?.groups) {
    cartStore.sidebar.groups.forEach(group => {
      expandedGroups.value.add(group.store.id)
    })
  }
}

function disableTodoMode() {
  todoMode.value = false
  checkedItems.value.clear()
}

function toggleCheck(itemId: number) {
  if (checkedItems.value.has(itemId)) {
    checkedItems.value.delete(itemId)
  } else {
    checkedItems.value.add(itemId)
  }
}

// Toggle group expansion
function toggleGroup(storeId: number) {
  if (expandedGroups.value.has(storeId)) {
    expandedGroups.value.delete(storeId)
  } else {
    expandedGroups.value.add(storeId)
  }
}

// Fetch sidebar data when opened
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    await cartStore.fetchSidebar()

    // Collapse all stores by default, unless there's only one store
    if (cartStore.sidebar?.groups) {
      expandedGroups.value.clear()

      // If only one store, keep it expanded
      if (sortedGroups.value.length === 1) {
        expandedGroups.value.add(sortedGroups.value[0].store.id)
      }
      // Otherwise, all stores are collapsed by default
    }

    // Poll for updates every 30 seconds while open
    const interval = setInterval(async () => {
      if (props.isOpen && cartStore.isActive) {
        await cartStore.fetchSidebar()
      } else {
        clearInterval(interval)
      }
    }, 30000)
  } else {
    // Reset TODO mode when closing
    if (todoMode.value) {
      disableTodoMode()
    }
  }
})

async function incrementQty(item: ShoppingListItem) {
  const result = await cartStore.updateQty(item.item_id, item.qty + 1)
  if (!result.success && result.error) {
    handleApiError(result.error)
  }
}

async function decrementQty(item: ShoppingListItem) {
  if (item.qty > 1) {
    const result = await cartStore.updateQty(item.item_id, item.qty - 1)
    if (!result.success && result.error) {
      handleApiError(result.error)
    }
  } else {
    // Remove item
    const result = await cartStore.removeItem(item.item_id)
    if (!result.success && result.error) {
      handleApiError(result.error)
    }
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
