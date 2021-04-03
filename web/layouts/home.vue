<template>
  <div>
    <TheHeader :transparent="windowTop <= 5" />
    <Nuxt />
    <TheFooter />
  </div>
</template>

<script>
export default {
  data() {
    return {
      windowTop: 0,
    }
  },
  mounted() {
    window.addEventListener('scroll', this.onScroll)
  },
  beforeDestroy() {
    window.removeEventListener('scroll', this.onScroll)
  },
  methods: {
    onScroll() {
      this.windowTop = window.top.scrollY
    },
  },
}
</script>
