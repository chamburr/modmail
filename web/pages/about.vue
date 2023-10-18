<template>
  <div>
    <Heading title="About Us">
      These are the awesome people who have contributed to the bot!
    </Heading>
    <div class="row">
      <div
        v-for="element in people"
        :key="element.name"
        class="about-card col-12 col-md-6 col-lg-4 mt-4 mt-md-0 pb-4"
      >
        <Card class="h-100" body-classes="d-flex flex-column text-center">
          <div class="pb-4">
            <img
              class="about-icon mw-100 mh-100 rounded-circle"
              :src="element.image"
              alt="Icon"
            />
          </div>
          <div class="flex-grow-1 d-flex flex-column">
            <p class="font-weight-bold h4">
              {{ element.name }}
            </p>
            <p class="about-description mb-0">{{ element.description.replace(', ', '\n') }}</p>
            <div class="flex-grow-1 d-flex flex-column justify-content-end">
              <hr
                v-if="
                  element.website ||
                  element.github ||
                  element.twitter ||
                  element.reddit ||
                  element.linkedin
                "
                class="my-3"
              />
              <div>
                <a v-if="element.website" target="_blank" :href="element.website">
                  <BaseIcon name="fas globe" class="big" />
                </a>
                <a v-if="element.github" target="_blank" :href="element.github">
                  <BaseIcon name="fab github" class="big" />
                </a>
                <a v-if="element.twitter" target="_blank" :href="element.twitter">
                  <BaseIcon name="fab twitter" class="big" />
                </a>
                <a v-if="element.reddit" target="_blank" :href="element.reddit">
                  <BaseIcon name="fab reddit" class="big" />
                </a>
                <a v-if="element.linkedin" target="_blank" :href="element.linkedin">
                  <BaseIcon name="fab linkedin" class="big" />
                </a>
              </div>
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
      people: await $getContent('about'),
    }
  },
  head: {
    title: 'About Us',
  },
}
</script>

<style scoped lang="scss">
.about-description {
  white-space: pre;
}

.about-card {
  box-sizing: border-box;
}

.about-icon {
  width: 160px;
  height: 160px;
}
</style>
