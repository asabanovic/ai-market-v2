<template>
  <div v-if="stores.length > 0" class="discount-ticker bg-gradient-to-r from-purple-900 to-indigo-900 text-white py-2 overflow-hidden">
    <div class="ticker-wrapper">
      <div class="ticker-content animate-ticker">
        <!-- Repeat stores for seamless loop -->
        <template v-for="repeat in 3" :key="'repeat-' + repeat">
          <div v-for="store in stores" :key="repeat + '-' + store.id" class="ticker-item">
            <div v-if="store.logo" class="logo-wrapper">
              <img
                :src="store.logo"
                :alt="store.name"
                class="store-logo"
                @error="(e) => (e.target as HTMLImageElement).parentElement!.style.display = 'none'"
              />
            </div>
            <span v-else class="store-name">{{ store.name }}</span>
            <span class="countdown">
              <span class="countdown-label">ističe za</span>
              <span class="countdown-value">{{ formatCountdown(store.latest_expires) }}</span>
            </span>
            <span class="discount-count">({{ store.discount_count }} {{ store.discount_count === 1 ? 'akcija' : 'akcija' }})</span>
            <span class="separator">|</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Store {
  id: number
  name: string
  logo?: string
  latest_expires: string
  discount_count: number
}

const props = defineProps<{
  stores: Store[]
}>()

function formatCountdown(expiresDate: string): string {
  if (!expiresDate) return ''

  const now = new Date()
  const expires = new Date(expiresDate + 'T23:59:59')
  const diff = expires.getTime() - now.getTime()

  if (diff <= 0) return 'isteklo'

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))

  if (days > 0) {
    return `${days}d ${hours}h`
  }
  return `${hours}h`
}
</script>

<style scoped>
.discount-ticker {
  position: relative;
}

.ticker-wrapper {
  display: flex;
  width: 100%;
}

.ticker-content {
  display: flex;
  white-space: nowrap;
}

.ticker-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 1rem;
  font-size: 0.875rem;
}

.logo-wrapper {
  background: white;
  border-radius: 4px;
  padding: 2px 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.store-logo {
  height: 20px;
  width: auto;
  max-width: 60px;
  object-fit: contain;
}

.store-name {
  font-weight: 600;
}

.countdown {
  display: inline-flex;
  gap: 0.25rem;
}

.countdown-label {
  opacity: 0.7;
}

.countdown-value {
  font-weight: 700;
  color: #fbbf24;
}

.discount-count {
  opacity: 0.6;
  font-size: 0.75rem;
}

.separator {
  opacity: 0.3;
  margin: 0 0.5rem;
}

.animate-ticker {
  animation: ticker 30s linear infinite;
}

.animate-ticker:hover {
  animation-play-state: paused;
}

@keyframes ticker {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-33.33%);
  }
}
</style>
