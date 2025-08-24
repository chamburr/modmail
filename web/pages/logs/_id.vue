<template>
  <div>
    <Heading title="Logs">
      The beautiful ModMail chat log viewer. All timestamps represent UTC time zone.
    </Heading>
    <Card>
      <Card
        v-for="(element, index) in logs"
        :key="index"
        class="my-2 border-0"
        body-classes="px-0 pt-2 pb-3"
        header-classes="border-0 p-0"
      >
        <template #header>
          <span :class="`log-${element.role.toLowerCase()}`">
            {{ element.username }}{{ element.discriminator ? `#${element.discriminator}` : '' }}
          </span>
          <span class="text-muted">{{ element.timestamp }}</span>
        </template>
        {{ element.message }}
        <div v-if="element.attachments.length !== 0" class="row mt-2">
          <div
            v-for="(attachment, index2) in supportedAttachments(element.attachments)"
            :key="`${index}-1-${index2}`"
            class="col flex-grow-0"
          >
            <a :href="attachment" target="_blank">
              <img :src="attachment" alt="Attachment" class="log-attachment" />
            </a>
          </div>
          <div
            v-for="(attachment, index2) in unsupportedAttachments(element.attachments)"
            :key="`${index}-2-${index2}`"
            class="col-12"
          >
            <a :href="attachment" target="_blank" rel="noopener">
              {{ attachment }}
            </a>
          </div>
        </div>
      </Card>
    </Card>
  </div>
</template>

<script>
export default {
  async asyncData({ $axios, $fatal, route }) {
    return {
      logs: await $axios.$get(`/logs/${route.params.id}`).catch($fatal),
    }
  },
  head: {
    title: 'Logs',
  },
  methods: {
    supportedAttachments(elements) {
      const supported = ['bmp', 'gif', 'jpg', 'jpeg', 'png']
      return elements.filter(element =>
        supported.includes(element.split('?')[0].split('.').pop().toLowerCase())
      )
    },
    unsupportedAttachments(elements) {
      const supported = this.supportedAttachments(elements)
      return elements.filter(element => !supported.includes(element))
    },
  },
}
</script>

<style scoped lang="scss">
.log-attachment {
  max-width: 300px;
}

.log-staff {
  font-weight: bold;
  color: #ff4500;
}

.log-user {
  font-weight: bold;
  color: #0f0;
}

.log-comment {
  font-weight: bold;
  color: #6c757d;
}
</style>
