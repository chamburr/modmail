<template>
  <div class="pb-4">
    <h1 class="display-2">{{ title }}</h1>
    <p class="heading-description"><slot></slot></p>
  </div>
</template>

<script>
export default {
  name: 'Heading',
  props: {
    title: {
      type: String,
      default: '',
    },
  },
}
</script>

<style scoped>
.heading-description {
  font-size: 1.15em;
}
</style>
