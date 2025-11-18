export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.directive('click-outside', {
    mounted(el, binding) {
      el.clickOutsideEvent = function (event: MouseEvent) {
        // Check if the click was outside the element and its children
        if (!(el === event.target || el.contains(event.target as Node))) {
          // Call the provided method
          binding.value(event)
        }
      }
      document.addEventListener('click', el.clickOutsideEvent)
    },
    unmounted(el) {
      document.removeEventListener('click', el.clickOutsideEvent)
    },
  })
})
