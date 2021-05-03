<template>
  <div>
    <Heading title="Privacy Policy">
      This Privacy Policy describes our policies and procedures on the collection, use, and
      disclosure of your personal information when you access or use ModMail's website and services.
    </Heading>
    <NuxtContent :document="privacy" />
  </div>
</template>

<script>
export default {
  async asyncData({ $getContent }) {
    return {
      privacy: await $getContent('privacy', false),
    }
  },
  head: {
    title: 'Privacy Policy',
  },
}
</script>
