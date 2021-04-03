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
      .then(() => {
        this.$store.commit('user/reset')
        this.$router.push('/')
      })
      .catch(this.$fatal)
  },
}
</script>
