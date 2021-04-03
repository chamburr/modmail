<template>
  <div>
    <Heading title="Partners">
      Cool things and services which we have partnered with. Contact us if you are interested in
      partnership!
    </Heading>
    <div class="row">
      <div
        v-for="element in partners"
        :key="element.name"
        class="partner-card text-center text-lg-left col-12 col-md-6 mt-4 mt-md-0 pb-4"
      >
        <Card class="bg-dark h-100">
          <div class="row h-100">
            <div class="col-12 col-lg-4 pb-4 px-3 pb-lg-0">
              <img
                class="partner-icon mw-100 mh-100 rounded-circle"
                :src="`${element.image}?size=512`"
                alt="Icon"
              />
            </div>
            <div class="col-12 col-lg-8 h-100">
              <p class="font-weight-bold h4">
                {{ element.name }}
              </p>
              <p>{{ element.description }}</p>
              <a :href="element.link">Learn more</a>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  async asyncData({ $getContent }) {
    return {
      partners: await $getContent('partners'),
    }
  },
  head: {
    title: 'Partners',
  },
}
</script>

<style scoped lang="scss">
@include media-breakpoint-down(md) {
  .partner-icon {
    width: 160px;
    height: 160px;
  }
}

.partner-card {
  box-sizing: border-box;
}
</style>
