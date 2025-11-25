<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :class="className"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path :d="iconPath" fill="currentColor" />
  </svg>
</template>

<script setup lang="ts">
import {
  mdiHeart,
  mdiHeartOutline,
  mdiCart,
  mdiPlaylistPlus,
  mdiInformationOutline,
  mdiChevronDown,
  mdiClose,
  mdiMagnify,
  mdiAccount,
  mdiLogout,
  mdiCog,
  mdiChevronUp,
  mdiPlus,
  mdiMinus,
  mdiDelete,
  mdiCheckCircle,
  mdiAlertCircle,
  mdiCloseCircle,
  mdiInformation
} from '@mdi/js'

const props = defineProps<{
  name: string
  size?: string | number
  class?: string
}>()

const className = computed(() => props.class || '')
const size = computed(() => {
  if (!props.size) return '24'
  return typeof props.size === 'number' ? props.size.toString() : props.size.replace('px', '')
})

// Map icon names to MDI paths
const iconMap: Record<string, string> = {
  'mdi:heart': mdiHeart,
  'mdi:heart-outline': mdiHeartOutline,
  'mdi:cart': mdiCart,
  'mdi:playlist-plus': mdiPlaylistPlus,
  'mdi:information-outline': mdiInformationOutline,
  'mdi:chevron-down': mdiChevronDown,
  'mdi:close': mdiClose,
  'mdi:magnify': mdiMagnify,
  'mdi:account': mdiAccount,
  'mdi:logout': mdiLogout,
  'mdi:cog': mdiCog,
  'mdi:chevron-up': mdiChevronUp,
  'mdi:plus': mdiPlus,
  'mdi:minus': mdiMinus,
  'mdi:delete': mdiDelete,
  'mdi:check-circle': mdiCheckCircle,
  'mdi:alert-circle': mdiAlertCircle,
  'mdi:close-circle': mdiCloseCircle,
  'mdi:information': mdiInformation
}

const iconPath = computed(() => {
  const path = iconMap[props.name]
  if (!path) {
    console.warn(`Icon "${props.name}" not found in icon map`)
    return ''
  }
  return path
})
</script>
