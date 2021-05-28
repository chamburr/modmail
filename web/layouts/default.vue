<template>
  <div>
    <TheHeader />
    <div id="app-flex-wrapper">
      <div class="container py-5 px-4">
        <Nuxt />
      </div>
      <TheFooter />
    </div>
  </div>
</template>

<script>
export default {}
</script>

<style scoped>
#app-flex-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: calc(100vh - 75px);
}
</style>
