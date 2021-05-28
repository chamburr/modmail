<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  async mounted() {
    await this.$axios
      .post('/users/@me/logout')
      .then(async () => {
        this.$store.commit('user/reset')
        await this.$router.push('/')
      })
      .catch(this.$fatal)
  },
}
</script>
