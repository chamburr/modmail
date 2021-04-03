<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  async mounted() {
    await this.$axios
      .$post('/authorize', {
        code: this.$route.query.code,
        state: this.$route.query.state,
      })
      .then(async res => {
        const user = await this.$axios.$get('/users/@me').catch(this.$fatal)
        this.$store.commit('user/set', user)
      })
      .catch(this.$fatal)
  },
}
</script>
