<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  hover?: boolean
  padding?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  hover: true,
  padding: 'md'
})

const cardClasses = computed(() => {
  const baseClasses = 'glass rounded-xl shadow-lg transition-all duration-300'
  const hoverClass = props.hover ? 'hover:shadow-xl hover:scale-105' : ''

  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  }

  return [baseClasses, hoverClass, paddingClasses[props.padding]]
})
</script>
