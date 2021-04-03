<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  head: {
    title: 'Premium',
  },
  mounted() {
    window.location.href = 'https://www.youtube.com/watch/dQw4w9WgXcQ'
  },
}
</script>
