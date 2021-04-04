<template></template>

<script>
export default {
  head: {
    title: 'logs',
  },
  async mounted() {
    await this.$axios.$get(`/logs`)
  },
}
</script>
