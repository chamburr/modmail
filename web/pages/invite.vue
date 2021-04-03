<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  head: {
    title: 'Invite',
  },
  async mounted() {
    await this.$axios
      .$get('/invite', { params: { guild: this.$route.query.guild } })
      .then(res => {
        window.location.href = res.uri
      })
      .catch(this.$fatal)
  },
}
</script>
