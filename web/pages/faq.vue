<template>
  <div>
    <Heading title="FAQs">
      The frequently asked questions. If you don't find what you are looking for, please join our
      support server.
    </Heading>
    <Card
      v-for="(element, index) in questions"
      :key="element.name"
      class="faq-card mb-4"
      body-classes="py-0"
      header-classes="border-0 p-0"
    >
      <template #header>
        <div v-b-toggle="`faq-question-${index}`" class="font-weight-bolder px-4 py-3">
          {{ element.name }}
        </div>
      </template>
      <BCollapse :id="`faq-question-${index}`" role="tabpanel">
        <p class="mt-0 mb-3 faq-description">{{ element.description }}</p>
      </BCollapse>
    </Card>
  </div>
</template>

<script>
export default {
  async asyncData({ $getContent }) {
    return {
      questions: await $getContent('faq'),
    }
  },
  head: {
    title: 'FAQ',
  },
}
</script>

<style scoped lang="scss">
.faq-card {
  ::v-deep div:focus {
    outline: none;
  }
}

.faq-description {
  white-space: pre-line;
}
</style>
