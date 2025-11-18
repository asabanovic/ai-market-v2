<template>
  <div class="min-h-screen flex flex-col">
    <LayoutHeader />
    <PhoneBanner />
    <main class="flex-1">
      <slot />
    </main>
    <LayoutFooter />
    <NotificationOptInPopup />
  </div>
</template>

<script setup lang="ts">
// Default layout with header and footer
</script>
