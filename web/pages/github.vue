<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  head: {
    title: 'GitHub',
  },
  mounted() {
    window.location.href = 'https://github.com/chamburr/modmail'
  },
}
</script>
