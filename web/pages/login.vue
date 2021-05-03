<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  async mounted() {
    await this.$axios
      .$get('/login', {
        params: {
          redirect: this.$route.query.redirect
            ? encodeURIComponent(this.$route.query.redirect.toString())
            : null,
        },
      })
      .then(res => {
        window.location.href = res.uri
      })
      .catch(this.$fatal)
  },
}
</script>
