<template>
  <div>
    <Heading title="Terms of Service">
      These Terms of Service govern your access to and use of Wyvor's website and services. Please
      make sure to fully read and understand these terms prior to using our website and services.
    </Heading>
    <NuxtContent :document="terms" />
  </div>
</template>

<script>
export default {
  async asyncData({ $getContent }) {
    return {
      terms: await $getContent('terms', false),
    }
  },
  head: {
    title: 'Terms of Service',
  },
}
</script>
