<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  head: {
    title: 'Authorized',
  },
  mounted() {
    window.location.href = 'https://discord.com/oauth2/authorized'
  },
}
</script>
