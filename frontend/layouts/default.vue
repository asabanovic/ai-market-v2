<template>
  <div class="min-h-screen flex flex-col">
    <LayoutHeader />
    <ClientOnly>
      <PhoneBanner />
    </ClientOnly>
    <main class="flex-1">
      <slot />
    </main>
    <LayoutFooter />
    <ClientOnly>
      <NotificationOptInPopup />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
// Default layout with header and footer
</script>
